/**
 * Client-side URL validation matching backend URLValidator logic.
 */

export interface ValidationResult {
  isValid: boolean;
  errorMessage?: string;
  finalUrl?: string;
  redirectCount?: number;
}

const PRIVATE_IPV4_RANGES = [
  { start: '10.0.0.0', end: '10.255.255.255' },
  { start: '172.16.0.0', end: '172.31.255.255' },
  { start: '192.168.0.0', end: '192.168.255.255' },
  { start: '127.0.0.0', end: '127.255.255.255' },
  { start: '169.254.0.0', end: '169.254.255.255' },
];

const BLOCKED_HOSTNAMES = [
  'localhost',
  'localhost.localdomain',
  '169.254.169.254',
  'metadata.google.internal',
  'metadata',
];

export class URLValidator {
  private allowedDomains: string[] = [];

  constructor(allowedDomains?: string[]) {
    if (allowedDomains) {
      this.allowedDomains = allowedDomains;
    }
  }

  validate(url: string): ValidationResult {
    if (!url) {
      return { isValid: false, errorMessage: 'URL cannot be empty' };
    }

    if (url.length > 2048) {
      return { isValid: false, errorMessage: 'URL exceeds maximum length of 2048 characters' };
    }

    let parsed: URL;
    try {
      parsed = new URL(url);
    } catch (e) {
      return { isValid: false, errorMessage: 'Invalid URL format' };
    }

    const scheme = parsed.protocol.replace(':', '');
    if (!['http', 'https'].includes(scheme)) {
      return { isValid: false, errorMessage: 'Only HTTP and HTTPS schemes are allowed' };
    }

    const ssrfCheck = this.checkSSRF(parsed);
    if (!ssrfCheck.isValid) {
      return ssrfCheck;
    }

    if (this.allowedDomains.length > 0) {
      if (!this.checkAllowlist(parsed.hostname)) {
        return { isValid: false, errorMessage: 'Domain is not in the allowed list' };
      }
    }

    return {
      isValid: true,
      finalUrl: url,
      redirectCount: 0,
    };
  }

  private checkSSRF(parsed: URL): ValidationResult {
    const hostname = parsed.hostname || '';

    if (!hostname) {
      return { isValid: false, errorMessage: 'URL has no hostname' };
    }

    if (BLOCKED_HOSTNAMES.includes(hostname.toLowerCase())) {
      return { isValid: false, errorMessage: 'Hostname is not allowed' };
    }

    const ip = this.parseIP(hostname);
    if (ip && this.isPrivateIP(ip)) {
      return { isValid: false, errorMessage: 'Private IP addresses are not allowed' };
    }

    return { isValid: true };
  }

  private checkAllowlist(hostname: string | null): boolean {
    if (!hostname) return false;

    for (const allowed of this.allowedDomains) {
      if (allowed === hostname) return true;
      if (allowed.startsWith('*.')) {
        const suffix = allowed.slice(2);
        if (hostname.endsWith('.' + suffix) || hostname === suffix) return true;
      }
    }
    return false;
  }

  private parseIP(hostname: string): number[] | null {
    const parts = hostname.split('.');
    if (parts.length !== 4) return null;
    const nums: number[] = [];
    for (const part of parts) {
      const num = parseInt(part, 10);
      if (isNaN(num) || num < 0 || num > 255) return null;
      nums.push(num);
    }
    return nums;
  }

  private isPrivateIP(ip: number[]): boolean {
    const ipNum = (ip[0] << 24) | (ip[1] << 16) | (ip[2] << 8) | ip[3];
    for (const range of PRIVATE_IPV4_RANGES) {
      const start = this.ipStringToNum(range.start);
      const end = this.ipStringToNum(range.end);
      if (ipNum >= start && ipNum <= end) return true;
    }
    return false;
  }

  private ipStringToNum(ipStr: string): number {
    const parts = ipStr.split('.').map(Number);
    return (parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3];
  }
}

export const validateUrl = (url: string, allowedDomains?: string[]): ValidationResult => {
  const validator = new URLValidator(allowedDomains);
  return validator.validate(url);
};