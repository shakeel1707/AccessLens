/**
 * Client-side URL validation matching backend URLValidator logic.
 */
export interface ValidationResult {
    isValid: boolean;
    errorMessage?: string;
    finalUrl?: string;
    redirectCount?: number;
}
export declare class URLValidator {
    private allowedDomains;
    constructor(allowedDomains?: string[]);
    validate(url: string): ValidationResult;
    private checkSSRF;
    private checkAllowlist;
    private parseIP;
    private isPrivateIP;
    private ipStringToNum;
}
export declare const validateUrl: (url: string, allowedDomains?: string[]) => ValidationResult;
//# sourceMappingURL=urlValidator.d.ts.map