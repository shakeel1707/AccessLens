import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { ScanForm } from "./components/ScanForm";
import { FindingsList } from "./components/FindingsList";
import { RepairReview } from "./components/RepairReview";
import { ReportDisplay } from "./components/ReportDisplay";
import { ProgressIndicator } from "./components/ProgressIndicator";
import "./App.css";
export const App = () => {
    return (_jsxs("div", { className: "app", children: [_jsxs("header", { className: "header", children: [_jsx("h1", { children: "AccessLens" }), _jsx("p", { children: "AI-powered website accessibility detection and repair" })] }), _jsxs("main", { className: "main", children: [_jsx("section", { className: "section", children: _jsx(ProgressIndicator, {}) }), _jsx("section", { className: "section", children: _jsx(ScanForm, {}) }), _jsx("section", { className: "section", children: _jsx(FindingsList, {}) }), _jsx("section", { className: "section", children: _jsx(RepairReview, {}) }), _jsx("section", { className: "section", children: _jsx(ReportDisplay, {}) })] }), _jsx("footer", { className: "footer", children: _jsx("p", { children: "\u00A9 2024 AccessLens. All rights reserved." }) })] }));
};
export default App;
//# sourceMappingURL=App.js.map