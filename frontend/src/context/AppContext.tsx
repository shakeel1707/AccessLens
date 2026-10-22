import React, { createContext, useContext, useState, ReactNode } from "react";

export interface Finding {
  finding_id: string;
  rule_id: string;
  severity: "critical" | "serious" | "moderate" | "minor";
  description: string;
  selector: string;
  html?: string;
  explanation?: string;
}

export interface Repair {
  repair_id: string;
  finding_id: string;
  status: "pending" | "approved" | "rejected";
  patch: string;
  confidence: "high" | "medium" | "low";
  original_code: string;
  proposed_code: string;
  assumptions: string[];
  warnings: string[];
  file_type: "html" | "css" | "javascript";
  selector: string;
}


export interface AppContextType {
  scanId: string | null;
  setScanId: (id: string) => void;
  scanStatus: "idle" | "scanning" | "completed" | "error";
  setScanStatus: (status: "idle" | "scanning" | "completed" | "error") => void;
  findings: Finding[];
  setFindings: (findings: Finding[]) => void;
  repairs: Repair[];
  setRepairs: (repairs: Repair[]) => void;
  error: string | null;
  setError: (error: string | null) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [scanId, setScanId] = useState<string | null>(null);
  const [scanStatus, setScanStatus] = useState<"idle" | "scanning" | "completed" | "error">("idle");
  const [findings, setFindings] = useState<Finding[]>([]);
  const [repairs, setRepairs] = useState<Repair[]>([]);
  const [error, setError] = useState<string | null>(null);

  return (
    <AppContext.Provider
      value={{
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
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error("useApp must be used within AppProvider");
  }
  return context;
};
