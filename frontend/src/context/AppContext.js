import { jsx as _jsx } from "react/jsx-runtime";
import { createContext, useContext, useState } from "react";
const AppContext = createContext(undefined);
export const AppProvider = ({ children }) => {
    const [scanId, setScanId] = useState(null);
    const [scanStatus, setScanStatus] = useState("idle");
    const [findings, setFindings] = useState([]);
    const [repairs, setRepairs] = useState([]);
    const [error, setError] = useState(null);
    const [report, setReport] = useState(null);
    return (_jsx(AppContext.Provider, { value: {
            scanId,
            setScanId,
            scanStatus,
            setScanStatus,
            findings,
            setFindings,
            repairs,
            setRepairs,
            error,
            setError,
            report,
            setReport,
        }, children: children }));
};
export const useApp = () => {
    const context = useContext(AppContext);
    if (context === undefined) {
        throw new Error("useApp must be used within AppProvider");
    }
    return context;
};
//# sourceMappingURL=AppContext.js.map