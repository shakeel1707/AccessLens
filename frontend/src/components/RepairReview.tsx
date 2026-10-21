import React from "react";
import { useApp } from "../context/AppContext";

export const RepairReview: React.FC = () => {
  const { repairs, setRepairs } = useApp();

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

  if (repairs.length === 0) {
    return <div className="repairs-empty">No repairs to review</div>;
  }

  return (
    <div className="repair-review">
      <h2>Repair Proposals ({repairs.length})</h2>
      {repairs.map((repair) => (
        <div key={repair.repair_id} className="repair-card">
          <div className="repair-header">
            <span className="repair-id">{repair.repair_id}</span>
            <span className={`confidence confidence-${Math.round(repair.confidence * 100)}`}>
              {Math.round(repair.confidence * 100)}% confidence
            </span>
            <span className={`status status-${repair.status}`}>{repair.status}</span>
          </div>
          <div className="repair-patch">
            <h4>Proposed Patch:</h4>
            <pre><code>{repair.patch}</code></pre>
          </div>
          <div className="repair-actions">
            {repair.status === "pending" && (
              <>
                <button onClick={() => handleApprove(repair.repair_id)} className="btn-approve">
                  Approve
                </button>
                <button onClick={() => handleReject(repair.repair_id)} className="btn-reject">
                  Reject
                </button>
              </>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
