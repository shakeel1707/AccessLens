import React, { useState } from "react";
import { useApp } from "../context/AppContext";

interface DiffLine {
  type: "add" | "remove" | "context";
  content: string;
}

const generateDiff = (original: string, proposed: string): DiffLine[] => {
  const originalLines = original.split("\n");
  const proposedLines = proposed.split("\n");
  const diff: DiffLine[] = [];

  const maxLines = Math.max(originalLines.length, proposedLines.length);

  for (let i = 0; i < maxLines; i++) {
    const origLine = originalLines[i];
    const propLine = proposedLines[i];

    if (origLine !== propLine) {
      if (origLine) diff.push({ type: "remove", content: origLine });
      if (propLine) diff.push({ type: "add", content: propLine });
    } else if (origLine) {
      diff.push({ type: "context", content: origLine });
    }
  }

  return diff;
};

const getConfidenceLevel = (confidence: string): { label: string; color: string; percentage: number } => {
  const levels = {
    high: { label: "High", color: "#10b981", percentage: 90 },
    medium: { label: "Medium", color: "#f59e0b", percentage: 60 },
    low: { label: "Low", color: "#ef4444", percentage: 30 },
  };
  return levels[confidence as keyof typeof levels] || levels.low;
};

interface ExpandedState {
  [key: string]: boolean;
}

export const RepairReview: React.FC = () => {
  const { repairs, setRepairs } = useApp();
  const [expanded, setExpanded] = useState<ExpandedState>({});

  if (!repairs || repairs.length === 0) {
    return (
      <div className="repairs-empty" role="status" aria-label="No repairs to review">
        <p>No repairs to review</p>
      </div>
    );
  }

  const toggleExpand = (repairId: string) => {
    setExpanded((prev) => ({
      ...prev,
      [repairId]: !prev[repairId],
    }));
  };

  const handleApprove = (repairId: string) => {
    setRepairs(
      repairs.map((r) =>
        r.repair_id === repairId ? { ...r, status: "approved" } : r
      )
    );
  };

  const handleReject = (repairId: string) => {
    setRepairs(
      repairs.map((r) =>
        r.repair_id === repairId ? { ...r, status: "rejected" } : r
      )
    );
  };

  const handleRegenerate = (repairId: string) => {
    setRepairs(
      repairs.map((r) =>
        r.repair_id === repairId ? { ...r, status: "pending" } : r
      )
    );
  };

  return (
    <div className="repair-review" role="region" aria-label="Repair proposals">
      <h2 className="repair-review-title">
        Repair Proposals <span className="repair-count">({repairs.length})</span>
      </h2>

      {repairs.map((repair) => {
        const confidenceInfo = getConfidenceLevel(repair.confidence);
        const diff = generateDiff(repair.original_code, repair.proposed_code);

        return (
          <div
            key={repair.repair_id}
            className={`repair-card repair-status-${repair.status}`}
            role="article"
            aria-label={`Repair ${repair.repair_id} - ${repair.status}`}
          >
            <div className="repair-header">
              <button
                className="repair-toggle-button"
                onClick={() => toggleExpand(repair.repair_id)}
                aria-expanded={expanded[repair.repair_id] ?? false}
                aria-controls={`repair-details-${repair.repair_id}`}
              >
                <span className="toggle-icon">
                  {expanded[repair.repair_id] ? "▼" : "▶"}
                </span>
                <div className="repair-header-content">
                  <span className="repair-id">{repair.repair_id}</span>
                  <span className="file-type" title={`File type: ${repair.file_type}`}>
                    {repair.file_type.toUpperCase()}
                  </span>
                  <code className="selector" title={repair.selector}>
                    {repair.selector}
                  </code>
                </div>
              </button>

              <div className="repair-meta">
                <div
                  className="confidence-badge"
                  style={{ backgroundColor: confidenceInfo.color }}
                  role="status"
                  aria-label={`${confidenceInfo.label} confidence`}
                >
                  <span className="confidence-text">{confidenceInfo.label}</span>
                  <div className="confidence-bar">
                    <div
                      className="confidence-fill"
                      style={{
                        width: `${confidenceInfo.percentage}%`,
                        backgroundColor: confidenceInfo.color,
                      }}
                      aria-hidden="true"
                    />
                  </div>
                </div>

                <span className={`status-badge status-${repair.status}`} role="status">
                  {repair.status.charAt(0).toUpperCase() + repair.status.slice(1)}
                </span>
              </div>
            </div>

            {expanded[repair.repair_id] && (
              <div
                id={`repair-details-${repair.repair_id}`}
                className="repair-details"
                role="region"
                aria-label="Repair details"
              >
                {/* Code Diff Section */}
                <div className="repair-section">
                  <h4>Code Changes</h4>
                  <div className="code-diff">
                    <div className="diff-container">
                      {diff.map((line, idx) => (
                        <div
                          key={idx}
                          className={`diff-line diff-${line.type}`}
                          role="doc-line"
                        >
                          <span className="diff-marker">
                            {line.type === "add" ? "+" : line.type === "remove" ? "−" : " "}
                          </span>
                          <code>{line.content}</code>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Assumptions Section */}
                {repair.assumptions.length > 0 && (
                  <div className="repair-section">
                    <h4>Assumptions</h4>
                    <ul className="assumptions-list" role="list">
                      {repair.assumptions.map((assumption, idx) => (
                        <li key={idx} role="listitem">
                          {assumption}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Warnings Section */}
                {repair.warnings.length > 0 && (
                  <div className="repair-section warnings-section">
                    <h4>⚠️ Warnings</h4>
                    <ul className="warnings-list" role="list">
                      {repair.warnings.map((warning, idx) => (
                        <li key={idx} className="warning-item" role="listitem">
                          {warning}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="repair-actions">
                  {repair.status === "pending" && (
                    <>
                      <button
                        onClick={() => handleApprove(repair.repair_id)}
                        className="btn btn-approve"
                        aria-label={`Approve repair ${repair.repair_id}`}
                      >
                        ✓ Approve
                      </button>
                      <button
                        onClick={() => handleReject(repair.repair_id)}
                        className="btn btn-reject"
                        aria-label={`Reject repair ${repair.repair_id}`}
                      >
                        ✗ Reject
                      </button>
                      <button
                        onClick={() => handleRegenerate(repair.repair_id)}
                        className="btn btn-regenerate"
                        aria-label={`Regenerate repair ${repair.repair_id}`}
                      >
                        ↻ Regenerate
                      </button>
                    </>
                  )}
                  {repair.status === "approved" && (
                    <span className="status-message approved">✓ Approved</span>
                  )}
                  {repair.status === "rejected" && (
                    <span className="status-message rejected">✗ Rejected</span>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default RepairReview;
