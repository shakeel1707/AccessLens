import React, { useState } from "react";
import { useApp } from "../context/AppContext";
import { URLValidator } from "../services/urlValidator";
import { ApiClient } from "../services/apiClient";

export const ScanForm: React.FC = () => {
  const [url, setUrl] = useState("");
  const [isValid, setIsValid] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const { setScanId, setScanStatus, setError } = useApp();
  const validator = new URLValidator();

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
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

  const handleSubmit = async (e: React.FormEvent) => {
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
      setScanStatus((response.status as any) || "completed");
      setError(null);
      setUrl("");
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to start scan";
      setError(errorMsg);
      setScanStatus("error");
      setValidationError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="scan-form">
      <div className="form-group">
        <label htmlFor="url">Website URL</label>
        <input
          id="url"
          type="text"
          value={url}
          onChange={handleUrlChange}
          placeholder="https://example.com"
          disabled={isLoading}
          className={`url-input ${isValid ? "valid" : ""} ${validationError ? "invalid" : ""}`}
          aria-label="Website URL for scanning"
          aria-invalid={!!validationError}
          aria-describedby={validationError ? "url-error" : undefined}
        />
        {validationError && (
          <p id="url-error" className="error" role="alert">
            {validationError}
          </p>
        )}
      </div>
      <button
        type="submit"
        disabled={!isValid || isLoading}
        className="submit-button"
        aria-busy={isLoading}
      >
        {isLoading ? "Scanning..." : "Start Scan"}
      </button>
    </form>
  );
};
