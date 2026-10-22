import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { useApp } from "../context/AppContext";
const SEVERITY_COLORS = {
    critical: "#dc2626",
    serious: "#f97316",
    moderate: "#d97706",
    minor: "#3b82f6",
};
export const ReportDisplay = () => {
    const { report, scanId } = useApp();
    const [isPrinting, setIsPrinting] = useState(false);
    const downloadReport = async (format) => {
        if (!scanId)
            return;
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
        }
        catch (err) {
            console.error("Failed to download report", err);
        }
    };
    const handlePrint = () => {
        setIsPrinting(true);
        window.print();
        setIsPrinting(false);
    };
    if (!report) {
        return (_jsx("div", { className: "report-empty", role: "status", "aria-label": "No report available", children: _jsx("p", { children: "No report available. Run a scan to generate a compliance report." }) }));
    }
    const improvementClass = report.improvement_percentage >= 50 ? "improvement-high" :
        report.improvement_percentage >= 20 ? "improvement-medium" : "improvement-low";
    return (_jsxs("div", { className: "report-display", role: "region", "aria-label": "Compliance report", children: [_jsxs("div", { className: "report-header print:bg-white", children: [_jsx("h1", { className: "report-title", children: "Accessibility Compliance Report" }), _jsxs("div", { className: "report-meta", children: [_jsxs("p", { children: [_jsx("strong", { children: "URL:" }), " ", _jsx("a", { href: report.url, target: "_blank", rel: "noopener noreferrer", children: report.url })] }), _jsxs("p", { children: [_jsx("strong", { children: "Scan Date:" }), " ", new Date(report.scan_date).toLocaleDateString(), " at ", new Date(report.scan_date).toLocaleTimeString()] }), _jsxs("p", { children: [_jsx("strong", { children: "WCAG Version:" }), " ", report.wcag_version] }), _jsxs("p", { children: [_jsx("strong", { children: "Scan ID:" }), " ", _jsx("code", { className: "scan-id", children: report.scan_id })] })] })] }), _jsxs("div", { className: "report-summary", children: [_jsx("h2", { children: "Summary" }), _jsxs("div", { className: "metrics-grid", children: [_jsxs("div", { className: "metric-card metric-improvement", role: "status", "aria-label": `${report.improvement_percentage}% improvement`, children: [_jsx("div", { className: "metric-label", children: "Improvement" }), _jsxs("div", { className: `metric-value ${improvementClass}`, children: [report.improvement_percentage, "%"] }), _jsx("div", { className: "metric-description", children: "violations improved" })] }), _jsxs("div", { className: "metric-card metric-fixed", role: "status", "aria-label": `${report.fixed_count} violations fixed`, children: [_jsx("div", { className: "metric-label", children: "\u2713 Fixed" }), _jsx("div", { className: "metric-value metric-fixed-value", children: report.fixed_count }), _jsx("div", { className: "metric-description", children: "issues resolved" })] }), _jsxs("div", { className: "metric-card metric-unresolved", role: "status", "aria-label": `${report.unresolved_count} violations unresolved`, children: [_jsx("div", { className: "metric-label", children: "Unresolved" }), _jsx("div", { className: "metric-value metric-unresolved-value", children: report.unresolved_count }), _jsx("div", { className: "metric-description", children: "still pending" })] }), _jsxs("div", { className: "metric-card metric-new", role: "status", "aria-label": `${report.new_violations_count} new violations`, children: [_jsx("div", { className: "metric-label", children: "New Issues" }), _jsx("div", { className: "metric-value metric-new-value", children: report.new_violations_count }), _jsx("div", { className: "metric-description", children: "introduced" })] })] })] }), _jsxs("div", { className: "report-comparison", children: [_jsx("h2", { children: "Violations: Before & After" }), _jsxs("div", { className: "comparison-grid", children: [_jsxs("div", { className: "comparison-card before-violations", children: [_jsx("h3", { children: "Before Scan" }), _jsxs("div", { className: "violation-count total-before", role: "status", children: [_jsx("span", { className: "count", children: report.before_violations.total }), _jsx("span", { className: "label", children: "Total Violations" })] }), _jsx("div", { className: "violation-breakdown", children: Object.entries(report.before_violations)
                                            .filter(([key]) => key !== "total")
                                            .map(([severity, count]) => (_jsxs("div", { className: "breakdown-item", role: "listitem", children: [_jsx("span", { className: "severity-dot", style: { backgroundColor: SEVERITY_COLORS[severity] }, "aria-hidden": "true" }), _jsx("span", { className: "severity-label", children: severity.charAt(0).toUpperCase() + severity.slice(1) }), _jsx("span", { className: "severity-count", children: count })] }, severity))) })] }), _jsxs("div", { className: "comparison-card after-violations", children: [_jsx("h3", { children: "After Repairs" }), _jsxs("div", { className: "violation-count total-after", role: "status", children: [_jsx("span", { className: "count", children: report.after_violations.total }), _jsx("span", { className: "label", children: "Total Violations" })] }), _jsx("div", { className: "violation-breakdown", children: Object.entries(report.after_violations)
                                            .filter(([key]) => key !== "total")
                                            .map(([severity, count]) => (_jsxs("div", { className: "breakdown-item", role: "listitem", children: [_jsx("span", { className: "severity-dot", style: { backgroundColor: SEVERITY_COLORS[severity] }, "aria-hidden": "true" }), _jsx("span", { className: "severity-label", children: severity.charAt(0).toUpperCase() + severity.slice(1) }), _jsx("span", { className: "severity-count", children: count })] }, severity))) })] })] })] }), _jsxs("div", { className: "report-chart", children: [_jsx("h2", { children: "Violation Breakdown by Severity" }), _jsx("div", { className: "severity-chart", children: ["critical", "serious", "moderate", "minor"].map((severity) => {
                            const beforeCount = report.before_violations[severity];
                            const afterCount = report.after_violations[severity];
                            const maxCount = Math.max(beforeCount, afterCount, 5);
                            const beforePercent = (beforeCount / maxCount) * 100;
                            const afterPercent = (afterCount / maxCount) * 100;
                            return (_jsxs("div", { className: "chart-row", children: [_jsx("label", { className: "chart-label", children: severity.charAt(0).toUpperCase() + severity.slice(1) }), _jsxs("div", { className: "chart-bars", children: [_jsxs("div", { className: "bar-group", children: [_jsx("div", { className: "bar before-bar", style: {
                                                            width: `${beforePercent}%`,
                                                            backgroundColor: SEVERITY_COLORS[severity],
                                                        }, role: "progressbar", "aria-valuenow": beforeCount, "aria-valuemin": 0, "aria-valuemax": maxCount, "aria-label": `${severity}: ${beforeCount} before repairs` }), _jsx("span", { className: "bar-value", children: beforeCount })] }), _jsxs("div", { className: "bar-group", children: [_jsx("div", { className: "bar after-bar", style: {
                                                            width: `${afterPercent}%`,
                                                            backgroundColor: SEVERITY_COLORS[severity],
                                                            opacity: 0.5,
                                                        }, role: "progressbar", "aria-valuenow": afterCount, "aria-valuemin": 0, "aria-valuemax": maxCount, "aria-label": `${severity}: ${afterCount} after repairs` }), _jsx("span", { className: "bar-value", children: afterCount })] })] })] }, severity));
                        }) }), _jsxs("div", { className: "chart-legend", children: [_jsxs("span", { className: "legend-item", children: [_jsx("span", { className: "legend-box", style: { opacity: 1 } }), " Before Repairs"] }), _jsxs("span", { className: "legend-item", children: [_jsx("span", { className: "legend-box", style: { opacity: 0.5 } }), " After Repairs"] })] })] }), _jsxs("div", { className: "report-actions print:hidden", children: [_jsx("h2", { children: "Export Report" }), _jsxs("div", { className: "action-buttons", children: [_jsx("button", { onClick: () => downloadReport("json"), className: "btn btn-download-json", "aria-label": "Download report as JSON", children: "\u2193 Download JSON" }), _jsx("button", { onClick: () => downloadReport("html"), className: "btn btn-download-html", "aria-label": "Download report as HTML", children: "\u2193 Download HTML" }), _jsx("button", { onClick: handlePrint, className: "btn btn-print", "aria-label": "Print report", disabled: isPrinting, children: "\uD83D\uDDA8\uFE0F Print Report" })] })] }), _jsx("div", { className: "report-footer print:block hidden", children: _jsxs("p", { className: "print-notice", children: ["This report was generated by AccessLens on ", new Date().toLocaleString()] }) })] }));
};
export default ReportDisplay;
//# sourceMappingURL=ReportDisplay.js.map