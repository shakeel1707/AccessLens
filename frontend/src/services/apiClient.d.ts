/**
 * API client for AccessLens backend.
 */
export interface ScanRequest {
    url: string;
}
export interface ScanResponse {
    scan_id: string;
    status: string;
    url: string;
    created_at: string;
}
export interface ApiError {
    code: string;
    message: string;
    status_code: number;
    request_id?: string;
}
export declare class ApiClient {
    static submitScan(url: string): Promise<ScanResponse>;
    static getFindings(scanId: string): Promise<any>;
    static getReport(scanId: string, format?: 'json' | 'html'): Promise<any>;
}
export default ApiClient;
//# sourceMappingURL=apiClient.d.ts.map