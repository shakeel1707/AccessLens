import React, { ReactNode } from "react";
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
export interface Report {
    scan_id: string;
    url: string;
    scan_date: string;
    wcag_version: "WCAG 2.1 Level A" | "WCAG 2.1 Level AA" | "WCAG 2.1 Level AAA";
    before_violations: {
        critical: number;
        serious: number;
        moderate: number;
        minor: number;
        total: number;
    };
    after_violations: {
        critical: number;
        serious: number;
        moderate: number;
        minor: number;
        total: number;
    };
    fixed_count: number;
    new_violations_count: number;
    unresolved_count: number;
    improvement_percentage: number;
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
    report: Report | null;
    setReport: (report: Report | null) => void;
}
export declare const AppProvider: React.FC<{
    children: ReactNode;
}>;
export declare const useApp: () => AppContextType;
//# sourceMappingURL=AppContext.d.ts.map