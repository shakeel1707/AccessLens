import React, { useState } from "react";
import { useApp } from "../context/AppContext";

interface Report {
  scan_id: string;
  url: string;
  report_date: string;
  wcag_version: string;
  metrics: {
    before_violations: number;
    after_violations: number;
    improvement_percentage: number;
  };
}

export const ReportDisplay: React.FC = () => {
  const { scanId, findings } = useApp();
  const [_report, _setReport] = useState<Report | null>(null);

  const downloadReport = async (format: "json" | "html") => {
    if (!scanId) return;
    try {
      const response = await fetch(`/api/report/${scanId}?format=${format}`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `report-${scanId}.${format}`;
      a.click();
    } catch (err) {
      console.error("Failed to download report", err);
    }
  };

  if (!scanId) {
    return <div className="report-empty">No scan to report on</div>;
  }

  return (
    <div className="report-display">
      <h2>Compliance Report</h2>
      <div className="report-info">
        <p>Scan ID: <code>{scanId}</code></p>
        <p>Violations Before: <strong>{findings.length}</strong></p>
        <p>Violations After: <strong>0</strong></p>
        <p>Improvement: <strong>0%</strong></p>
      </div>
      <div className="download-actions">
        <button onClick={() => downloadReport("json")} className="btn-download">
          Download JSON
        </button>
        <button onClick={() => downloadReport("html")} className="btn-download">
          Download HTML
        </button>
        <button onClick={() => window.print()} className="btn-print">
          Print Report
        </button>
      </div>
    </div>
  );
};
