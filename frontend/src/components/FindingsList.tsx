import React from "react";
import { useApp } from "../context/AppContext";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#dc2626",
  serious: "#f97316",
  moderate: "#eab308",
  minor: "#3b82f6",
};

export const FindingsList: React.FC = () => {
  const { findings } = useApp();

  if (findings.length === 0) {
    return <div className="findings-empty">No findings to display</div>;
  }

  const groupedByRule = findings.reduce(
    (acc, finding) => {
      if (!acc[finding.rule_id]) {
        acc[finding.rule_id] = [];
      }
      acc[finding.rule_id].push(finding);
      return acc;
    },
    {} as Record<string, typeof findings>
  );

  return (
    <div className="findings-list">
      <h2>Accessibility Findings ({findings.length})</h2>
      {Object.entries(groupedByRule).map(([rule, items]) => (
        <div key={rule} className="finding-group">
          <h3>{rule}</h3>
          {items.map((finding) => (
            <div
              key={finding.finding_id}
              className="finding-item"
              style={{
                borderLeft: `4px solid ${SEVERITY_COLORS[finding.severity]}`,
              }}
            >
              <div className="finding-header">
                <span
                  className="severity-badge"
                  style={{ backgroundColor: SEVERITY_COLORS[finding.severity] }}
                >
                  {finding.severity}
                </span>
                <code className="selector">{finding.selector}</code>
              </div>
              <p className="description">{finding.description}</p>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
};
