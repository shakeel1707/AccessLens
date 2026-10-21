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

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export class ApiClient {
  static async submitScan(url: string): Promise<ScanResponse> {
    const request: ScanRequest = { url };

    try {
      const response = await fetch(API_BASE_URL + '/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = (await response.json()) as ApiError;
        throw new Error(error.message || 'HTTP ' + response.status);
      }

      return (await response.json()) as ScanResponse;
    } catch (error) {
      if (error instanceof Error) throw error;
      throw new Error('Failed to submit scan');
    }
  }

  static async getFindings(scanId: string) {
    const response = await fetch(API_BASE_URL + '/scan/' + scanId + '/findings');
    if (!response.ok) throw new Error('HTTP ' + response.status);
    return await response.json();
  }

  static async getReport(scanId: string, format: 'json' | 'html' = 'json') {
    const response = await fetch(API_BASE_URL + '/report/' + scanId + '?format=' + format);
    if (!response.ok) throw new Error('HTTP ' + response.status);
    return format === 'html' ? await response.text() : await response.json();
  }
}

export default ApiClient;