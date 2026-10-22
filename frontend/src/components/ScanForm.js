import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { useApp } from "../context/AppContext";
import { URLValidator } from "../services/urlValidator";
import { ApiClient } from "../services/apiClient";
export const ScanForm = () => {
    const [url, setUrl] = useState("");
    const [isValid, setIsValid] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [validationError, setValidationError] = useState(null);
    const { setScanId, setScanStatus, setError } = useApp();
    const validator = new URLValidator();
    const handleUrlChange = (e) => {
        const value = e.target.value;
        setUrl(value);
        setValidationError(null);
        if (!value) {
            setIsValid(false);
            return;
        }
        const result = validator.validate(value);
        setIsValid(result.isValid);
        if (!result.isValid) {
            setValidationError(result.errorMessage || "Invalid URL");
        }
    };
    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!isValid) {
            setValidationError("Please enter a valid URL");
            return;
        }
        setIsLoading(true);
        setScanStatus("scanning");
        try {
            const response = await ApiClient.submitScan(url);
            setScanId(response.scan_id);
            setScanStatus(response.status || "completed");
            setError(null);
            setUrl("");
        }
        catch (err) {
            const errorMsg = err instanceof Error ? err.message : "Failed to start scan";
            setError(errorMsg);
            setScanStatus("error");
            setValidationError(errorMsg);
        }
        finally {
            setIsLoading(false);
        }
    };
    return (_jsxs("form", { onSubmit: handleSubmit, className: "scan-form", children: [_jsxs("div", { className: "form-group", children: [_jsx("label", { htmlFor: "url", children: "Website URL" }), _jsx("input", { id: "url", type: "text", value: url, onChange: handleUrlChange, placeholder: "https://example.com", disabled: isLoading, className: `url-input ${isValid ? "valid" : ""} ${validationError ? "invalid" : ""}`, "aria-label": "Website URL for scanning", "aria-invalid": !!validationError, "aria-describedby": validationError ? "url-error" : undefined }), validationError && (_jsx("p", { id: "url-error", className: "error", role: "alert", children: validationError }))] }), _jsx("button", { type: "submit", disabled: !isValid || isLoading, className: "submit-button", "aria-busy": isLoading, children: isLoading ? "Scanning..." : "Start Scan" })] }));
};
//# sourceMappingURL=ScanForm.js.map