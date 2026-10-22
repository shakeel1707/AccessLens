import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { useApp } from "../context/AppContext";
const SEVERITY_COLORS = {
    critical: { bg: "#fee2e2", text: "#dc2626" },
    serious: { bg: "#fed7aa", text: "#f97316" },
    moderate: { bg: "#fef3c7", text: "#d97706" },
    minor: { bg: "#dbeafe", text: "#3b82f6" },
};
const SEVERITY_ORDER = {
    critical: 0,
    serious: 1,
    moderate: 2,
    minor: 3,
};
export const FindingsList = () => {
    const { findings } = useApp();
    const [expanded, setExpanded] = useState({});
    if (!findings || findings.length === 0) {
        return (_jsx("div", { className: "findings-empty", role: "status", "aria-label": "No accessibility findings", children: _jsx("p", { children: "No accessibility findings to display" }) }));
    }
    const sortedFindings = [...findings].sort((a, b) => (SEVERITY_ORDER[a.severity] ?? 999) - (SEVERITY_ORDER[b.severity] ?? 999));
    const groupedBySeverity = sortedFindings.reduce((acc, finding) => {
        if (!acc[finding.severity]) {
            acc[finding.severity] = [];
        }
        acc[finding.severity].push(finding);
        return acc;
    }, {});
    const toggleExpand = (findingId) => {
        setExpanded((prev) => ({
            ...prev,
            [findingId]: !prev[findingId],
        }));
    };
    const handleKeyDown = (e, findingId) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            toggleExpand(findingId);
        }
    };
    return (_jsxs("div", { className: "findings-list", role: "region", "aria-label": "Accessibility findings", children: [_jsxs("h2", { className: "findings-title", children: ["Accessibility Findings ", _jsxs("span", { className: "finding-count", children: ["(", findings.length, ")"] })] }), Object.entries(groupedBySeverity).map(([severity, items]) => (_jsxs("div", { className: "findings-severity-group", children: [_jsxs("h3", { className: "severity-section-title", children: [severity.charAt(0).toUpperCase() + severity.slice(1), " (", items.length, ")"] }), _jsx("div", { className: "findings-group", children: items.map((finding) => (_jsxs("div", { className: "finding-item-wrapper", children: [_jsxs("button", { className: "finding-item-button", onClick: () => toggleExpand(finding.finding_id), onKeyDown: (e) => handleKeyDown(e, finding.finding_id), "aria-expanded": expanded[finding.finding_id] ?? false, "aria-controls": `finding-details-${finding.finding_id}`, children: [_jsxs("div", { className: "finding-header", style: {
                                                borderLeft: `4px solid ${SEVERITY_COLORS[severity].text}`,
                                            }, children: [_jsx("span", { className: "severity-badge", style: {
                                                        backgroundColor: SEVERITY_COLORS[severity].bg,
                                                        color: SEVERITY_COLORS[severity].text,
                                                    }, role: "status", "aria-label": `${severity} severity`, children: severity.toUpperCase() }), _jsx("code", { className: "selector", title: finding.selector, "aria-label": `CSS selector: ${finding.selector}`, children: finding.selector }), _jsx("span", { className: "expand-icon", "aria-hidden": "true", children: expanded[finding.finding_id] ? "▼" : "▶" })] }), _jsx("p", { className: "description", children: finding.description })] }), expanded[finding.finding_id] && (_jsxs("div", { id: `finding-details-${finding.finding_id}`, className: "finding-details", role: "region", "aria-label": "Finding details", children: [finding.explanation && (_jsxs("div", { className: "detail-section", children: [_jsx("h4", { children: "Explanation" }), _jsx("p", { children: finding.explanation })] })), finding.html && (_jsxs("div", { className: "detail-section", children: [_jsx("h4", { children: "HTML" }), _jsx("pre", { children: _jsx("code", { children: finding.html }) })] })), _jsxs("div", { className: "detail-section", children: [_jsx("h4", { children: "Rule ID" }), _jsx("code", { className: "rule-id", children: finding.rule_id })] })] }))] }, finding.finding_id))) })] }, severity)))] }));
};
export default FindingsList;
//# sourceMappingURL=FindingsList.js.map