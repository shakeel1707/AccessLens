import React, { useState } from "react";
import { useApp } from "../context/AppContext";

export const ScanForm: React.FC = () => {
  const [url, setUrl] = useState("");
  const [isValid, setIsValid] = useState(false);
  const { setScanId, setScanStatus, setError } = useApp();

  const validateUrl = (input: string): boolean => {
    try {
      new URL(input);
      // Check for private networks and localhost
      const hostname = new URL(input).hostname;
      if (hostname === "localhost" || hostname === "127.0.0.1") {
        return false;
      }
      return true;
    } catch {
      return false;
    }
  };

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setUrl(value);
    setIsValid(validateUrl(value));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid) {
      setError("Invalid URL");
      return;
    }

    try {
      setScanStatus("scanning");
      setScanId("scan-" + Date.now());
      // API call would go here
      setError(null);
    } catch (err) {
      setError("Failed to start scan");
      setScanStatus("error");
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
          className={`url-input ${isValid ? "valid" : "invalid"}`}
        />
        {!isValid && url && <p className="error">Invalid URL</p>}
      </div>
      <button type="submit" disabled={!isValid} className="submit-button">
        Start Scan
      </button>
    </form>
  );
};
