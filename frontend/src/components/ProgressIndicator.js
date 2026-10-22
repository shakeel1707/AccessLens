import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useApp } from "../context/AppContext";
export const ProgressIndicator = () => {
    const { scanStatus, error } = useApp();
    const steps = [
        { name: "Scan", status: scanStatus !== "idle" ? "active" : "pending" },
        { name: "Review", status: scanStatus === "completed" ? "active" : "pending" },
        { name: "Report", status: scanStatus === "completed" ? "active" : "pending" },
    ];
    return (_jsxs("div", { className: "progress-indicator", children: [_jsx("div", { className: "steps", children: steps.map((step, index) => (_jsxs("div", { className: "step", children: [_jsx("div", { className: `step-circle step-${step.status}`, children: _jsx("span", { children: index + 1 }) }), _jsx("div", { className: "step-label", children: step.name }), index < steps.length - 1 && (_jsx("div", { className: `step-line step-${step.status}` }))] }, step.name))) }), scanStatus === "scanning" && (_jsxs("div", { className: "status-message", children: [_jsx("div", { className: "spinner" }), _jsx("p", { children: "Scanning website for accessibility issues..." })] })), scanStatus === "completed" && (_jsx("div", { className: "status-message success", children: _jsx("p", { children: "\u2713 Scan completed successfully" }) })), scanStatus === "error" && error && (_jsx("div", { className: "status-message error", children: _jsxs("p", { children: ["\u2717 ", error] }) }))] }));
};
//# sourceMappingURL=ProgressIndicator.js.map