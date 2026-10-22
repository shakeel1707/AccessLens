import React, { useState } from "react";
import { useApp } from "../context/AppContext";



const SEVERITY_COLORS: Record<string, string> = {
  critical: "#dc2626",
  serious: "#f97316",
  moderate: "#d97706",
  minor: "#3b82f6",
};

export const ReportDisplay: React.FC = () => {
  const { report, scanId } = useApp();
  const [isPrinting, setIsPrinting] = useState(false);

  const downloadReport = async (format: "json" | "html") => {
    if (!scanId) return;
    try {
      const response = await fetch(`/api/report/${scanId}?format=${format}`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `report-${scanId}-${new Date().toISOString().split("T")[0]}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to download report", err);
    }
  };

  const handlePrint = () => {
    setIsPrinting(true);
    window.print();
    setIsPrinting(false);
  };

  if (!report) {
    return (
      <div className="report-empty" role="status" aria-label="No report available">
        <p>No report available. Run a scan to generate a compliance report.</p>
      </div>
    );
  }

  const improvementClass =
    report.improvement_percentage >= 50 ? "improvement-high" :
    report.improvement_percentage >= 20 ? "improvement-medium" : "improvement-low";

  return (
    <div className="report-display" role="region" aria-label="Compliance report">
      {/* Header */}
      <div className="report-header print:bg-white">
        <h1 className="report-title">Accessibility Compliance Report</h1>
        <div className="report-meta">
          <p><strong>URL:</strong> <a href={report.url} target="_blank" rel="noopener noreferrer">{report.url}</a></p>
          <p><strong>Scan Date:</strong> {new Date(report.scan_date).toLocaleDateString()} at {new Date(report.scan_date).toLocaleTimeString()}</p>
          <p><strong>WCAG Version:</strong> {report.wcag_version}</p>
          <p><strong>Scan ID:</strong> <code className="scan-id">{report.scan_id}</code></p>
        </div>
      </div>

      {/* Summary Metrics */}
      <div className="report-summary">
        <h2>Summary</h2>
        <div className="metrics-grid">
          <div className="metric-card metric-improvement" role="status" aria-label={`${report.improvement_percentage}% improvement`}>
            <div className="metric-label">Improvement</div>
            <div className={`metric-value ${improvementClass}`}>
              {report.improvement_percentage}%
            </div>
            <div className="metric-description">violations improved</div>
          </div>

          <div className="metric-card metric-fixed" role="status" aria-label={`${report.fixed_count} violations fixed`}>
            <div className="metric-label">✓ Fixed</div>
            <div className="metric-value metric-fixed-value">{report.fixed_count}</div>
            <div className="metric-description">issues resolved</div>
          </div>

          <div className="metric-card metric-unresolved" role="status" aria-label={`${report.unresolved_count} violations unresolved`}>
            <div className="metric-label">Unresolved</div>
            <div className="metric-value metric-unresolved-value">{report.unresolved_count}</div>
            <div className="metric-description">still pending</div>
          </div>

          <div className="metric-card metric-new" role="status" aria-label={`${report.new_violations_count} new violations`}>
            <div className="metric-label">New Issues</div>
            <div className="metric-value metric-new-value">{report.new_violations_count}</div>
            <div className="metric-description">introduced</div>
          </div>
        </div>
      </div>

      {/* Before/After Comparison */}
      <div className="report-comparison">
        <h2>Violations: Before & After</h2>
        <div className="comparison-grid">
          <div className="comparison-card before-violations">
            <h3>Before Scan</h3>
            <div className="violation-count total-before" role="status">
              <span className="count">{report.before_violations.total}</span>
              <span className="label">Total Violations</span>
            </div>
            <div className="violation-breakdown">
              {Object.entries(report.before_violations)
                .filter(([key]) => key !== "total")
                .map(([severity, count]) => (
                  <div key={severity} className="breakdown-item" role="listitem">
                    <span
                      className="severity-dot"
                      style={{ backgroundColor: SEVERITY_COLORS[severity] }}
                      aria-hidden="true"
                    />
                    <span className="severity-label">{severity.charAt(0).toUpperCase() + severity.slice(1)}</span>
                    <span className="severity-count">{count}</span>
                  </div>
                ))}
            </div>
          </div>

          <div className="comparison-card after-violations">
            <h3>After Repairs</h3>
            <div className="violation-count total-after" role="status">
              <span className="count">{report.after_violations.total}</span>
              <span className="label">Total Violations</span>
            </div>
            <div className="violation-breakdown">
              {Object.entries(report.after_violations)
                .filter(([key]) => key !== "total")
                .map(([severity, count]) => (
                  <div key={severity} className="breakdown-item" role="listitem">
                    <span
                      className="severity-dot"
                      style={{ backgroundColor: SEVERITY_COLORS[severity] }}
                      aria-hidden="true"
                    />
                    <span className="severity-label">{severity.charAt(0).toUpperCase() + severity.slice(1)}</span>
                    <span className="severity-count">{count}</span>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </div>

      {/* Severity Breakdown Chart */}
      <div className="report-chart">
        <h2>Violation Breakdown by Severity</h2>
        <div className="severity-chart">
          {["critical", "serious", "moderate", "minor"].map((severity) => {
            const beforeCount = report.before_violations[severity as keyof typeof report.before_violations];
            const afterCount = report.after_violations[severity as keyof typeof report.after_violations];
            const maxCount = Math.max(beforeCount, afterCount, 5);
            const beforePercent = (beforeCount / maxCount) * 100;
            const afterPercent = (afterCount / maxCount) * 100;

            return (
              <div key={severity} className="chart-row">
                <label className="chart-label">{severity.charAt(0).toUpperCase() + severity.slice(1)}</label>
                <div className="chart-bars">
                  <div className="bar-group">
                    <div
                      className="bar before-bar"
                      style={{
                        width: `${beforePercent}%`,
                        backgroundColor: SEVERITY_COLORS[severity],
                      }}
                      role="progressbar"
                      aria-valuenow={beforeCount}
                      aria-valuemin={0}
                      aria-valuemax={maxCount}
                      aria-label={`${severity}: ${beforeCount} before repairs`}
                    />
                    <span className="bar-value">{beforeCount}</span>
                  </div>
                  <div className="bar-group">
                    <div
                      className="bar after-bar"
                      style={{
                        width: `${afterPercent}%`,
                        backgroundColor: SEVERITY_COLORS[severity],
                        opacity: 0.5,
                      }}
                      role="progressbar"
                      aria-valuenow={afterCount}
                      aria-valuemin={0}
                      aria-valuemax={maxCount}
                      aria-label={`${severity}: ${afterCount} after repairs`}
                    />
                    <span className="bar-value">{afterCount}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        <div className="chart-legend">
          <span className="legend-item"><span className="legend-box" style={{ opacity: 1 }} /> Before Repairs</span>
          <span className="legend-item"><span className="legend-box" style={{ opacity: 0.5 }} /> After Repairs</span>
        </div>
      </div>

      {/* Download Section */}
      <div className="report-actions print:hidden">
        <h2>Export Report</h2>
        <div className="action-buttons">
          <button
            onClick={() => downloadReport("json")}
            className="btn btn-download-json"
            aria-label="Download report as JSON"
          >
            ↓ Download JSON
          </button>
          <button
            onClick={() => downloadReport("html")}
            className="btn btn-download-html"
            aria-label="Download report as HTML"
          >
            ↓ Download HTML
          </button>
          <button
            onClick={handlePrint}
            className="btn btn-print"
            aria-label="Print report"
            disabled={isPrinting}
          >
            🖨️ Print Report
          </button>
        </div>
      </div>

      {/* Print-only footer */}
      <div className="report-footer print:block hidden">
        <p className="print-notice">This report was generated by AccessLens on {new Date().toLocaleString()}</p>
      </div>
    </div>
  );
};

export default ReportDisplay;
