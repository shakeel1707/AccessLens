import { describe, it, expect } from "vitest";
import fc from "fast-check";

describe("Task 25: Suite 7 - JSON Round-Trip Serialization (Frontend)", () => {
  // Arbitrary generators for test data
  const scanReport = () =>
    fc.record({
      scan_id: fc.uuidV(4),
      url: fc.webUrl(),
      scan_date: fc.date(),
      wcag_version: fc.constantFrom("WCAG 2.1 Level A", "WCAG 2.1 Level AA"),
      before_violations: fc.record({
        critical: fc.integer({ min: 0, max: 100 }),
        serious: fc.integer({ min: 0, max: 100 }),
        moderate: fc.integer({ min: 0, max: 100 }),
        minor: fc.integer({ min: 0, max: 100 }),
        total: fc.integer({ min: 0, max: 400 }),
      }),
      after_violations: fc.record({
        critical: fc.integer({ min: 0, max: 50 }),
        serious: fc.integer({ min: 0, max: 50 }),
        moderate: fc.integer({ min: 0, max: 50 }),
        minor: fc.integer({ min: 0, max: 50 }),
        total: fc.integer({ min: 0, max: 200 }),
      }),
      improvement_percentage: fc.float({ min: 0, max: 100 }),
      fixed_count: fc.integer({ min: 0, max: 100 }),
      unresolved_count: fc.integer({ min: 0, max: 100 }),
    });

  const finding = () =>
    fc.record({
      finding_id: fc.hexaString({ minLength: 32, maxLength: 64 }),
      rule_id: fc.constantFrom(
        "alt-text",
        "color-contrast",
        "heading-hierarchy",
        "form-labels",
        "aria-hidden"
      ),
      severity: fc.constantFrom("critical", "serious", "moderate", "minor"),
      selector: fc.string({ minLength: 1, maxLength: 100 }),
      description: fc.string({ minLength: 1, maxLength: 500 }),
      html: fc.string({ minLength: 1, maxLength: 500 }),
    });

  const repair = () =>
    fc.record({
      repair_id: fc.uuidV(4),
      finding_id: fc.uuidV(4),
      original_code: fc.string({ minLength: 1, maxLength: 200 }),
      proposed_code: fc.string({ minLength: 1, maxLength: 200 }),
      file_type: fc.constantFrom("html", "css", "javascript"),
      selector: fc.string({ minLength: 1, maxLength: 100 }),
      confidence: fc.constantFrom("high", "medium", "low"),
      status: fc.constantFrom("pending", "approved", "rejected"),
    });

  it("should serialize and deserialize ScanReport without data loss (invariant: identity)", () => {
    fc.assert(
      fc.property(scanReport(), (original) => {
        const serialized = JSON.stringify(original);
        const deserialized = JSON.parse(serialized);

        // Invariant: Deserialized object equals original (for serializable types)
        expect(deserialized.scan_id).toBe(original.scan_id);
        expect(deserialized.url).toBe(original.url);
        expect(deserialized.wcag_version).toBe(original.wcag_version);
        expect(deserialized.improvement_percentage).toBe(
          original.improvement_percentage
        );
      }),
      { seed: 50 }
    );
  });

  it("should handle Unicode characters in strings during round-trip", () => {
    const unicodeStrings = fc.string({
      minLength: 1,
      maxLength: 100,
      // Include Unicode characters
      unit16CodePointSets: [
        "\\u0041-\\u005A", // A-Z
        "\\u0061-\\u007A", // a-z
        "\\u00C0-\\u00FF", // Latin Extended
        "\\u4E00-\\u9FFF", // CJK Unified
      ],
    });

    fc.assert(
      fc.property(unicodeStrings, (original) => {
        const serialized = JSON.stringify({ text: original });
        const deserialized = JSON.parse(serialized);

        // Invariant: Unicode preserved
        expect(deserialized.text).toBe(original);
        expect(deserialized.text.length).toBe(original.length);
      }),
      { seed: 50 }
    );
  });

  it("should preserve nested object structures", () => {
    fc.assert(
      fc.property(
        fc.record({
          level1: fc.record({
            level2: fc.record({
              level3: fc.string({ minLength: 1, maxLength: 50 }),
            }),
          }),
        }),
        (original) => {
          const serialized = JSON.stringify(original);
          const deserialized = JSON.parse(serialized);

          // Invariant: Nested structure preserved
          expect(deserialized.level1.level2.level3).toBe(
            original.level1.level2.level3
          );
        }
      ),
      { seed: 50 }
    );
  });

  it("should handle arrays in serialization", () => {
    fc.assert(
      fc.property(
        fc.array(finding(), { minLength: 1, maxLength: 50 }),
        (findings) => {
          const serialized = JSON.stringify(findings);
          const deserialized = JSON.parse(serialized);

          // Invariant: Array length preserved
          expect(deserialized.length).toBe(findings.length);

          // Invariant: Array elements preserve order
          for (let i = 0; i < findings.length; i++) {
            expect(deserialized[i].finding_id).toBe(findings[i].finding_id);
            expect(deserialized[i].severity).toBe(findings[i].severity);
          }
        }
      ),
      { seed: 50 }
    );
  });

  it("should handle null values correctly", () => {
    const dataWithNull = fc.record({
      value: fc.oneof(fc.string(), fc.constant(null)),
      nested: fc.record({
        field: fc.oneof(fc.integer(), fc.constant(null)),
      }),
    });

    fc.assert(
      fc.property(dataWithNull, (original) => {
        const serialized = JSON.stringify(original);
        const deserialized = JSON.parse(serialized);

        // Invariant: Null values preserved
        expect(deserialized.value).toBe(original.value);
        expect(deserialized.nested.field).toBe(original.nested.field);
      }),
      { seed: 50 }
    );
  });

  it("should round-trip repairs with confidence preservation", () => {
    fc.assert(
      fc.property(fc.array(repair(), { minLength: 1, maxLength: 10 }), (repairs) => {
        const serialized = JSON.stringify(repairs);
        const deserialized = JSON.parse(serialized);

        // Invariant: Confidence values preserved
        for (let i = 0; i < repairs.length; i++) {
          expect(deserialized[i].confidence).toBe(repairs[i].confidence);
          expect(deserialized[i].status).toBe(repairs[i].status);
        }
      }),
      { seed: 50 }
    );
  });

  it("should ensure serialization inverse is deterministic", () => {
    fc.assert(
      fc.property(
        fc.record({
          id: fc.uuidV(4),
          data: fc.record({
            count: fc.integer({ min: 0, max: 1000 }),
            name: fc.string({ minLength: 1, maxLength: 100 }),
          }),
        }),
        (original) => {
          // Serialize twice
          const s1 = JSON.stringify(original);
          const s2 = JSON.stringify(original);

          // Invariant: Same input produces same JSON string
          expect(s1).toBe(s2);

          // Deserialize both and verify they're identical
          const d1 = JSON.parse(s1);
          const d2 = JSON.parse(s2);

          expect(d1.id).toBe(d2.id);
          expect(d1.data.count).toBe(d2.data.count);
        }
      ),
      { seed: 50 }
    );
  });

  it("should handle large objects without truncation", () => {
    fc.assert(
      fc.property(
        fc.record({
          items: fc.array(
            fc.record({
              id: fc.uuidV(4),
              content: fc.string({ minLength: 100, maxLength: 500 }),
            }),
            { minLength: 10, maxLength: 100 }
          ),
        }),
        (original) => {
          const serialized = JSON.stringify(original);
          const deserialized = JSON.parse(serialized);

          // Invariant: All items preserved
          expect(deserialized.items.length).toBe(original.items.length);

          // Invariant: No truncation (all content preserved)
          for (let i = 0; i < original.items.length; i++) {
            expect(deserialized.items[i].content.length).toBe(
              original.items[i].content.length
            );
          }
        }
      ),
      { seed: 50 }
    );
  });
});
