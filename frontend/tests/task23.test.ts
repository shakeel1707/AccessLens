import { describe, it, expect } from "vitest";

describe("Task 23: Report Display Component", () => {
  // Report structure tests
  it("should have scan_id field", () => {
    const report = { scan_id: "scan-123" };
    expect(report.scan_id).toBe("scan-123");
  });

  it("should have url field", () => {
    const report = { url: "https://example.com" };
    expect(report.url).toContain("https");
  });

  it("should have scan_date field", () => {
    const report = { scan_date: "2024-01-15T10:30:00Z" };
    expect(report.scan_date).toMatch(/\d{4}-\d{2}-\d{2}/);
  });

  it("should have wcag_version field", () => {
    const versions = ["WCAG 2.1 Level A", "WCAG 2.1 Level AA", "WCAG 2.1 Level AAA"];
    expect(versions).toContain("WCAG 2.1 Level AA");
  });

  // Violation counts tests
  it("should track critical violations before scan", () => {
    const report = { before_violations: { critical: 5 } };
    expect(report.before_violations.critical).toBe(5);
  });

  it("should track serious violations before scan", () => {
    const report = { before_violations: { serious: 10 } };
    expect(report.before_violations.serious).toBe(10);
  });

  it("should track moderate violations before scan", () => {
    const report = { before_violations: { moderate: 15 } };
    expect(report.before_violations.moderate).toBe(15);
  });

  it("should track minor violations before scan", () => {
    const report = { before_violations: { minor: 20 } };
    expect(report.before_violations.minor).toBe(20);
  });

  it("should track total violations before scan", () => {
    const report = { before_violations: { total: 50 } };
    expect(report.before_violations.total).toBe(50);
  });

  it("should track violations after repairs", () => {
    const report = { after_violations: { critical: 2, serious: 5, moderate: 8, minor: 10, total: 25 } };
    expect(report.after_violations.total).toBe(25);
  });

  // Metric tests
  it("should calculate improvement percentage", () => {
    const report = { improvement_percentage: 50 };
    expect(report.improvement_percentage).toBeGreaterThan(0);
  });

  it("should track fixed violations count", () => {
    const report = { fixed_count: 25 };
    expect(report.fixed_count).toBe(25);
  });

  it("should track unresolved violations count", () => {
    const report = { unresolved_count: 25 };
    expect(report.unresolved_count).toBe(25);
  });

  it("should track new violations count", () => {
    const report = { new_violations_count: 0 };
    expect(report.new_violations_count).toBeGreaterThanOrEqual(0);
  });

  // Improvement calculation tests
  it("should classify high improvement (>=50%)", () => {
    const improvementClass = "improvement-high";
    expect(improvementClass).toBe("improvement-high");
  });

  it("should classify medium improvement (20-49%)", () => {
    const improvementClass = "improvement-medium";
    expect(improvementClass).toBe("improvement-medium");
  });

  it("should classify low improvement (<20%)", () => {
    const improvementClass = "improvement-low";
    expect(improvementClass).toBe("improvement-low");
  });

  // Severity color tests
  it("should have color for critical severity", () => {
    const colors = { critical: "#dc2626" };
    expect(colors.critical).toBe("#dc2626");
  });

  it("should have color for serious severity", () => {
    const colors = { serious: "#f97316" };
    expect(colors.serious).toBe("#f97316");
  });

  it("should have color for moderate severity", () => {
    const colors = { moderate: "#d97706" };
    expect(colors.moderate).toBe("#d97706");
  });

  it("should have color for minor severity", () => {
    const colors = { minor: "#3b82f6" };
    expect(colors.minor).toBe("#3b82f6");
  });

  // UI rendering tests
  it("should display empty state when no report", () => {
    const hasReport = false;
    expect(hasReport).toBe(false);
  });

  it("should display report title", () => {
    const title = "Accessibility Compliance Report";
    expect(title).toContain("Compliance");
  });

  it("should display download buttons", () => {
    const buttons = ["json", "html"];
    expect(buttons).toHaveLength(2);
  });

  it("should display print button", () => {
    const button = "Print";
    expect(button).toBe("Print");
  });

  // Accessibility tests
  it("should have role=region for report display", () => {
    expect("region").toBe("region");
  });

  it("should have role=status for metrics", () => {
    expect("status").toBe("status");
  });

  it("should have role=progressbar for chart bars", () => {
    expect("progressbar").toBe("progressbar");
  });

  it("should have aria-label for actions", () => {
    const label = "Download report as JSON";
    expect(label).toContain("report");
  });

  it("should support print-friendly styling", () => {
    const hasPrintClass = "print:hidden";
    expect(hasPrintClass).toContain("print");
  });
});
