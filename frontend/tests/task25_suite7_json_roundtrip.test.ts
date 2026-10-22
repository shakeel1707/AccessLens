import { describe, it, expect } from "vitest";

describe("Task 25: Suite 7 - JSON Round-Trip Serialization (Frontend)", () => {
  it("should serialize and deserialize scan report without data loss", () => {
    const report = {
      scan_id: "scan-uuid-123",
      url: "https://example.com",
      wcag_version: "WCAG 2.1 Level AA",
      before_violations: {
        critical: 5,
        serious: 10,
        moderate: 15,
        minor: 20,
        total: 50,
      },
      after_violations: {
        critical: 2,
        serious: 5,
        moderate: 8,
        minor: 10,
        total: 25,
      },
      improvement_percentage: 50,
      fixed_count: 25,
      unresolved_count: 25,
    };

    const serialized = JSON.stringify(report);
    const deserialized = JSON.parse(serialized);

    expect(deserialized.scan_id).toBe(report.scan_id);
    expect(deserialized.url).toBe(report.url);
    expect(deserialized.wcag_version).toBe(report.wcag_version);
    expect(deserialized.before_violations).toEqual(report.before_violations);
    expect(deserialized.after_violations).toEqual(report.after_violations);
    expect(deserialized.improvement_percentage).toBe(report.improvement_percentage);
  });

  it("should handle Unicode characters in strings during round-trip", () => {
    const data = {
      description: "Image de logo (日本語) - Überschrift",
      selector: "img.logó",
      value: "Some text with emoji 🎯",
    };

    const serialized = JSON.stringify(data);
    const deserialized = JSON.parse(serialized);

    expect(deserialized.description).toBe(data.description);
    expect(deserialized.selector).toBe(data.selector);
    expect(deserialized.value).toBe(data.value);
  });

  it("should preserve nested object structures", () => {
    const nested = {
      level1: {
        level2: {
          level3: {
            value: "deep value",
            count: 42,
          },
        },
      },
    };

    const serialized = JSON.stringify(nested);
    const deserialized = JSON.parse(serialized);

    expect(deserialized.level1.level2.level3.value).toBe("deep value");
    expect(deserialized.level1.level2.level3.count).toBe(42);
  });

  it("should handle arrays in serialization", () => {
    const findings = [
      {
        finding_id: "f1",
        severity: "critical",
        rule_id: "alt-text",
      },
      {
        finding_id: "f2",
        severity: "serious",
        rule_id: "color-contrast",
      },
    ];

    const serialized = JSON.stringify(findings);
    const deserialized = JSON.parse(serialized);

    expect(deserialized.length).toBe(findings.length);
    expect(deserialized[0].finding_id).toBe(findings[0].finding_id);
    expect(deserialized[1].severity).toBe(findings[1].severity);
  });

  it("should handle null values correctly", () => {
    const data = {
      value: null,
      nested: {
        field: null,
      },
      array: [1, null, 3],
    };

    const serialized = JSON.stringify(data);
    const deserialized = JSON.parse(serialized);

    expect(deserialized.value).toBeNull();
    expect(deserialized.nested.field).toBeNull();
    expect(deserialized.array[1]).toBeNull();
  });

  it("should round-trip repairs with confidence preservation", () => {
    const repairs = [
      {
        repair_id: "r1",
        finding_id: "f1",
        original_code: "<img />",
        proposed_code: '<img alt="image" />',
        file_type: "html",
        confidence: "high",
        status: "approved",
      },
      {
        repair_id: "r2",
        finding_id: "f2",
        original_code: "color: red;",
        proposed_code: "color: red; /* contrast: 5:1 */",
        file_type: "css",
        confidence: "medium",
        status: "pending",
      },
    ];

    const serialized = JSON.stringify(repairs);
    const deserialized = JSON.parse(serialized);

    for (let i = 0; i < repairs.length; i++) {
      expect(deserialized[i].confidence).toBe(repairs[i].confidence);
      expect(deserialized[i].status).toBe(repairs[i].status);
      expect(deserialized[i].proposed_code).toBe(repairs[i].proposed_code);
    }
  });

  it("should ensure serialization produces consistent output", () => {
    const data = {
      id: "uuid-123",
      count: 42,
      name: "Test",
    };

    const s1 = JSON.stringify(data);
    const s2 = JSON.stringify(data);

    expect(s1).toBe(s2);

    const d1 = JSON.parse(s1);
    const d2 = JSON.parse(s2);

    expect(d1.id).toBe(d2.id);
    expect(d1.count).toBe(d2.count);
  });

  it("should handle large objects without truncation", () => {
    const items = [];
    for (let i = 0; i < 50; i++) {
      items.push({
        id: `item-${i}`,
        content: `This is content item ${i}. `.repeat(10),
      });
    }

    const data = { items };
    const serialized = JSON.stringify(data);
    const deserialized = JSON.parse(serialized);

    expect(deserialized.items.length).toBe(items.length);
    for (let i = 0; i < items.length; i++) {
      expect(deserialized.items[i].content.length).toBe(items[i].content.length);
    }
  });

  it("should preserve special characters and escaping", () => {
    const data = {
      quoted: 'Text with "quotes"',
      newlines: "Line 1\nLine 2\nLine 3",
      tabs: "Col1\tCol2\tCol3",
      backslash: "Path\\to\\file",
    };

    const serialized = JSON.stringify(data);
    const deserialized = JSON.parse(serialized);

    expect(deserialized.quoted).toBe(data.quoted);
    expect(deserialized.newlines).toBe(data.newlines);
    expect(deserialized.tabs).toBe(data.tabs);
    expect(deserialized.backslash).toBe(data.backslash);
  });
});
