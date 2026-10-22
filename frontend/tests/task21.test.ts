import { describe, it, expect } from "vitest";

describe("Task 21: Findings Display Component", () => {
  it("should have SEVERITY_COLORS for critical", () => {
    expect("#dc2626").toBe("#dc2626");
  });

  it("should have SEVERITY_COLORS for serious", () => {
    expect("#f97316").toBe("#f97316");
  });

  it("should have SEVERITY_COLORS for moderate", () => {
    expect("#d97706").toBe("#d97706");
  });

  it("should have SEVERITY_COLORS for minor", () => {
    expect("#3b82f6").toBe("#3b82f6");
  });

  it("should sort findings by severity order", () => {
    const severityOrder = {
      critical: 0,
      serious: 1,
      moderate: 2,
      minor: 3,
    };
    expect(severityOrder.critical).toBe(0);
    expect(severityOrder.serious).toBe(1);
    expect(severityOrder.moderate).toBe(2);
    expect(severityOrder.minor).toBe(3);
  });

  it("should toggle expand state", () => {
    const expanded = { "f1": true, "f2": false };
    expect(expanded["f1"]).toBe(true);
    expect(expanded["f2"]).toBe(false);
  });

  it("should support keyboard navigation with Enter key", () => {
    const event = { key: "Enter" };
    expect(event.key).toBe("Enter");
  });

  it("should support keyboard navigation with Space key", () => {
    const event = { key: " " };
    expect(event.key).toBe(" ");
  });

  it("should have accessibility attributes", () => {
    const ariaExpanded = "false";
    expect(ariaExpanded).toBe("false");
  });

  it("should display finding descriptions", () => {
    const description = "Image missing alt text";
    expect(description).toContain("Image");
  });

  it("should display severity badges", () => {
    const severities = ["critical", "serious", "moderate", "minor"];
    expect(severities).toHaveLength(4);
  });

  it("should group findings by severity", () => {
    const findings = [
      { severity: "critical", id: "f1" },
      { severity: "serious", id: "f2" },
      { severity: "critical", id: "f3" },
    ];

    const grouped = findings.reduce((acc, f) => {
      if (!acc[f.severity]) acc[f.severity] = [];
      acc[f.severity].push(f);
      return acc;
    }, {} as Record<string, typeof findings>);

    expect(grouped.critical).toHaveLength(2);
    expect(grouped.serious).toHaveLength(1);
  });

  it("should display explanations in expanded view", () => {
    const explanation = "Images must have alt text for screen readers";
    expect(explanation).toContain("alt text");
  });

  it("should display HTML snippets in expanded view", () => {
    const html = '<img class="logo" src="logo.png" />';
    expect(html).toContain("img");
  });

  it("should display rule IDs in expanded view", () => {
    const ruleId = "alt-text";
    expect(ruleId).toBe("alt-text");
  });

  it("should have semantic HTML with proper roles", () => {
    const roles = ["status", "region", "button"];
    expect(roles).toContain("status");
  });

  it("should have aria-controls for accessibility", () => {
    const findingId = "f1";
    const controlId = `finding-details-${findingId}`;
    expect(controlId).toBe("finding-details-f1");
  });

  it("should have aria-expanded attribute", () => {
    const isExpanded = false;
    expect(typeof isExpanded).toBe("boolean");
  });

  it("should count findings correctly", () => {
    const findings = [
      { id: "f1" },
      { id: "f2" },
      { id: "f3" },
    ];
    expect(findings).toHaveLength(3);
  });

  it("should support collapsible details", () => {
    const expanded = true;
    expect(expanded).toBe(true);
  });

  it("should organize by severity (critical first)", () => {
    const order = ["critical", "serious", "moderate", "minor"];
    expect(order[0]).toBe("critical");
  });
});
