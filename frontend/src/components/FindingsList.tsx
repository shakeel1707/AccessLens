import React, { useState } from "react";
import { useApp } from "../context/AppContext";

interface Finding {
  finding_id: string;
  rule_id: string;
  severity: "critical" | "serious" | "moderate" | "minor";
  selector: string;
  description: string;
  html?: string;
  explanation?: string;
}

const SEVERITY_COLORS: Record<string, { bg: string; text: string }> = {
  critical: { bg: "#fee2e2", text: "#dc2626" },
  serious: { bg: "#fed7aa", text: "#f97316" },
  moderate: { bg: "#fef3c7", text: "#d97706" },
  minor: { bg: "#dbeafe", text: "#3b82f6" },
};

const SEVERITY_ORDER: Record<string, number> = {
  critical: 0,
  serious: 1,
  moderate: 2,
  minor: 3,
};

interface ExpandedState {
  [key: string]: boolean;
}

export const FindingsList: React.FC = () => {
  const { findings } = useApp();
  const [expanded, setExpanded] = useState<ExpandedState>({});

  if (!findings || findings.length === 0) {
    return (
      <div
        className="findings-empty"
        role="status"
        aria-label="No accessibility findings"
      >
        <p>No accessibility findings to display</p>
      </div>
    );
  }

  const sortedFindings = [...findings].sort(
    (a, b) =>
      (SEVERITY_ORDER[a.severity] ?? 999) - (SEVERITY_ORDER[b.severity] ?? 999)
  );

  const groupedBySeverity = sortedFindings.reduce(
    (acc, finding) => {
      if (!acc[finding.severity]) {
        acc[finding.severity] = [];
      }
      acc[finding.severity].push(finding);
      return acc;
    },
    {} as Record<string, Finding[]>
  );

  const toggleExpand = (findingId: string) => {
    setExpanded((prev) => ({
      ...prev,
      [findingId]: !prev[findingId],
    }));
  };

  const handleKeyDown = (
    e: React.KeyboardEvent,
    findingId: string
  ) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      toggleExpand(findingId);
    }
  };

  return (
    <div className="findings-list" role="region" aria-label="Accessibility findings">
      <h2 className="findings-title">
        Accessibility Findings <span className="finding-count">({findings.length})</span>
      </h2>

      {Object.entries(groupedBySeverity).map(([severity, items]) => (
        <div key={severity} className="findings-severity-group">
          <h3 className="severity-section-title">
            {severity.charAt(0).toUpperCase() + severity.slice(1)} ({items.length})
          </h3>
          <div className="findings-group">
            {items.map((finding) => (
              <div key={finding.finding_id} className="finding-item-wrapper">
                <button
                  className="finding-item-button"
                  onClick={() => toggleExpand(finding.finding_id)}
                  onKeyDown={(e) => handleKeyDown(e, finding.finding_id)}
                  aria-expanded={expanded[finding.finding_id] ?? false}
                  aria-controls={`finding-details-${finding.finding_id}`}
                >
                  <div
                    className="finding-header"
                    style={{
                      borderLeft: `4px solid ${SEVERITY_COLORS[severity].text}`,
                    }}
                  >
                    <span
                      className="severity-badge"
                      style={{
                        backgroundColor: SEVERITY_COLORS[severity].bg,
                        color: SEVERITY_COLORS[severity].text,
                      }}
                      role="status"
                      aria-label={`${severity} severity`}
                    >
                      {severity.toUpperCase()}
                    </span>
                    <code
                      className="selector"
                      title={finding.selector}
                      aria-label={`CSS selector: ${finding.selector}`}
                    >
                      {finding.selector}
                    </code>
                    <span
                      className="expand-icon"
                      aria-hidden="true"
                    >
                      {expanded[finding.finding_id] ? "▼" : "▶"}
                    </span>
                  </div>
                  <p className="description">{finding.description}</p>
                </button>

                {expanded[finding.finding_id] && (
                  <div
                    id={`finding-details-${finding.finding_id}`}
                    className="finding-details"
                    role="region"
                    aria-label="Finding details"
                  >
                    {finding.explanation && (
                      <div className="detail-section">
                        <h4>Explanation</h4>
                        <p>{finding.explanation}</p>
                      </div>
                    )}
                    {finding.html && (
                      <div className="detail-section">
                        <h4>HTML</h4>
                        <pre>
                          <code>{finding.html}</code>
                        </pre>
                      </div>
                    )}
                    <div className="detail-section">
                      <h4>Rule ID</h4>
                      <code className="rule-id">{finding.rule_id}</code>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default FindingsList;
