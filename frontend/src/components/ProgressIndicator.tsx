import React from "react";
import { useApp } from "../context/AppContext";

export const ProgressIndicator: React.FC = () => {
  const { scanStatus, error } = useApp();

  const steps = [
    { name: "Scan", status: scanStatus !== "idle" ? "active" : "pending" },
    { name: "Review", status: scanStatus === "completed" ? "active" : "pending" },
    { name: "Report", status: scanStatus === "completed" ? "active" : "pending" },
  ];

  return (
    <div className="progress-indicator">
      <div className="steps">
        {steps.map((step, index) => (
          <div key={step.name} className="step">
            <div className={`step-circle step-${step.status}`}>
              <span>{index + 1}</span>
            </div>
            <div className="step-label">{step.name}</div>
            {index < steps.length - 1 && (
              <div className={`step-line step-${step.status}`} />
            )}
          </div>
        ))}
      </div>
      {scanStatus === "scanning" && (
        <div className="status-message">
          <div className="spinner" />
          <p>Scanning website for accessibility issues...</p>
        </div>
      )}
      {scanStatus === "completed" && (
        <div className="status-message success">
          <p>✓ Scan completed successfully</p>
        </div>
      )}
      {scanStatus === "error" && error && (
        <div className="status-message error">
          <p>✗ {error}</p>
        </div>
      )}
    </div>
  );
};
