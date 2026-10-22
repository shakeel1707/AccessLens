import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState } from "react";
import { useApp } from "../context/AppContext";
const generateDiff = (original, proposed) => {
    const originalLines = original.split("\n");
    const proposedLines = proposed.split("\n");
    const diff = [];
    const maxLines = Math.max(originalLines.length, proposedLines.length);
    for (let i = 0; i < maxLines; i++) {
        const origLine = originalLines[i];
        const propLine = proposedLines[i];
        if (origLine !== propLine) {
            if (origLine)
                diff.push({ type: "remove", content: origLine });
            if (propLine)
                diff.push({ type: "add", content: propLine });
        }
        else if (origLine) {
            diff.push({ type: "context", content: origLine });
        }
    }
    return diff;
};
const getConfidenceLevel = (confidence) => {
    const levels = {
        high: { label: "High", color: "#10b981", percentage: 90 },
        medium: { label: "Medium", color: "#f59e0b", percentage: 60 },
        low: { label: "Low", color: "#ef4444", percentage: 30 },
    };
    return levels[confidence] || levels.low;
};
export const RepairReview = () => {
    const { repairs, setRepairs } = useApp();
    const [expanded, setExpanded] = useState({});
    if (!repairs || repairs.length === 0) {
        return (_jsx("div", { className: "repairs-empty", role: "status", "aria-label": "No repairs to review", children: _jsx("p", { children: "No repairs to review" }) }));
    }
    const toggleExpand = (repairId) => {
        setExpanded((prev) => ({
            ...prev,
            [repairId]: !prev[repairId],
        }));
    };
    const handleApprove = (repairId) => {
        setRepairs(repairs.map((r) => r.repair_id === repairId ? { ...r, status: "approved" } : r));
    };
    const handleReject = (repairId) => {
        setRepairs(repairs.map((r) => r.repair_id === repairId ? { ...r, status: "rejected" } : r));
    };
    const handleRegenerate = (repairId) => {
        setRepairs(repairs.map((r) => r.repair_id === repairId ? { ...r, status: "pending" } : r));
    };
    return (_jsxs("div", { className: "repair-review", role: "region", "aria-label": "Repair proposals", children: [_jsxs("h2", { className: "repair-review-title", children: ["Repair Proposals ", _jsxs("span", { className: "repair-count", children: ["(", repairs.length, ")"] })] }), repairs.map((repair) => {
                const confidenceInfo = getConfidenceLevel(repair.confidence);
                const diff = generateDiff(repair.original_code, repair.proposed_code);
                return (_jsxs("div", { className: `repair-card repair-status-${repair.status}`, role: "article", "aria-label": `Repair ${repair.repair_id} - ${repair.status}`, children: [_jsxs("div", { className: "repair-header", children: [_jsxs("button", { className: "repair-toggle-button", onClick: () => toggleExpand(repair.repair_id), "aria-expanded": expanded[repair.repair_id] ?? false, "aria-controls": `repair-details-${repair.repair_id}`, children: [_jsx("span", { className: "toggle-icon", children: expanded[repair.repair_id] ? "▼" : "▶" }), _jsxs("div", { className: "repair-header-content", children: [_jsx("span", { className: "repair-id", children: repair.repair_id }), _jsx("span", { className: "file-type", title: `File type: ${repair.file_type}`, children: repair.file_type.toUpperCase() }), _jsx("code", { className: "selector", title: repair.selector, children: repair.selector })] })] }), _jsxs("div", { className: "repair-meta", children: [_jsxs("div", { className: "confidence-badge", style: { backgroundColor: confidenceInfo.color }, role: "status", "aria-label": `${confidenceInfo.label} confidence`, children: [_jsx("span", { className: "confidence-text", children: confidenceInfo.label }), _jsx("div", { className: "confidence-bar", children: _jsx("div", { className: "confidence-fill", style: {
                                                            width: `${confidenceInfo.percentage}%`,
                                                            backgroundColor: confidenceInfo.color,
                                                        }, "aria-hidden": "true" }) })] }), _jsx("span", { className: `status-badge status-${repair.status}`, role: "status", children: repair.status.charAt(0).toUpperCase() + repair.status.slice(1) })] })] }), expanded[repair.repair_id] && (_jsxs("div", { id: `repair-details-${repair.repair_id}`, className: "repair-details", role: "region", "aria-label": "Repair details", children: [_jsxs("div", { className: "repair-section", children: [_jsx("h4", { children: "Code Changes" }), _jsx("div", { className: "code-diff", children: _jsx("div", { className: "diff-container", children: diff.map((line, idx) => (_jsxs("div", { className: `diff-line diff-${line.type}`, role: "doc-line", children: [_jsx("span", { className: "diff-marker", children: line.type === "add" ? "+" : line.type === "remove" ? "−" : " " }), _jsx("code", { children: line.content })] }, idx))) }) })] }), repair.assumptions.length > 0 && (_jsxs("div", { className: "repair-section", children: [_jsx("h4", { children: "Assumptions" }), _jsx("ul", { className: "assumptions-list", role: "list", children: repair.assumptions.map((assumption, idx) => (_jsx("li", { role: "listitem", children: assumption }, idx))) })] })), repair.warnings.length > 0 && (_jsxs("div", { className: "repair-section warnings-section", children: [_jsx("h4", { children: "\u26A0\uFE0F Warnings" }), _jsx("ul", { className: "warnings-list", role: "list", children: repair.warnings.map((warning, idx) => (_jsx("li", { className: "warning-item", role: "listitem", children: warning }, idx))) })] })), _jsxs("div", { className: "repair-actions", children: [repair.status === "pending" && (_jsxs(_Fragment, { children: [_jsx("button", { onClick: () => handleApprove(repair.repair_id), className: "btn btn-approve", "aria-label": `Approve repair ${repair.repair_id}`, children: "\u2713 Approve" }), _jsx("button", { onClick: () => handleReject(repair.repair_id), className: "btn btn-reject", "aria-label": `Reject repair ${repair.repair_id}`, children: "\u2717 Reject" }), _jsx("button", { onClick: () => handleRegenerate(repair.repair_id), className: "btn btn-regenerate", "aria-label": `Regenerate repair ${repair.repair_id}`, children: "\u21BB Regenerate" })] })), repair.status === "approved" && (_jsx("span", { className: "status-message approved", children: "\u2713 Approved" })), repair.status === "rejected" && (_jsx("span", { className: "status-message rejected", children: "\u2717 Rejected" }))] })] }))] }, repair.repair_id));
            })] }));
};
export default RepairReview;
//# sourceMappingURL=RepairReview.js.map