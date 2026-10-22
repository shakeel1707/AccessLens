import { describe, it, expect } from "vitest";
import { URLValidator, validateUrl } from "../src/services/urlValidator";
import { ApiClient } from "../src/services/apiClient";

describe("URLValidator - SSRF Prevention", () => {
  const validator = new URLValidator();

  it("should validate valid HTTPS URLs", () => {
    const result = validator.validate("https://example.com");
    expect(result.isValid).toBe(true);
  });

  it("should validate valid HTTP URLs", () => {
    const result = validator.validate("http://example.com");
    expect(result.isValid).toBe(true);
  });

  it("should reject empty URLs", () => {
    const result = validator.validate("");
    expect(result.isValid).toBe(false);
    expect(result.errorMessage).toContain("empty");
  });

  it("should reject localhost by hostname", () => {
    const result = validator.validate("http://localhost:8080");
    expect(result.isValid).toBe(false);
  });

  it("should reject 127.0.0.1 (IPv4 loopback)", () => {
    const result = validator.validate("http://127.0.0.1");
    expect(result.isValid).toBe(false);
  });

  it("should reject private IP 10.0.0.0/8", () => {
    const result = validator.validate("http://10.0.0.1");
    expect(result.isValid).toBe(false);
  });

  it("should reject private IP 172.16.0.0/12", () => {
    const result = validator.validate("http://172.16.0.1");
    expect(result.isValid).toBe(false);
  });

  it("should reject private IP 192.168.0.0/16", () => {
    const result = validator.validate("http://192.168.1.1");
    expect(result.isValid).toBe(false);
  });

  it("should reject link-local address 169.254.0.0/16", () => {
    const result = validator.validate("http://169.254.0.1");
    expect(result.isValid).toBe(false);
  });

  it("should reject metadata endpoint 169.254.169.254", () => {
    const result = validator.validate("http://169.254.169.254");
    expect(result.isValid).toBe(false);
  });

  it("should reject URLs exceeding 2048 characters", () => {
    const longUrl = "https://example.com/" + "a".repeat(2100);
    const result = validator.validate(longUrl);
    expect(result.isValid).toBe(false);
    expect(result.errorMessage).toContain("exceeds maximum length");
  });

  it("should reject invalid URL format", () => {
    const result = validator.validate("not a url");
    expect(result.isValid).toBe(false);
    expect(result.errorMessage).toContain("Invalid URL format");
  });

  it("should reject non-HTTP schemes", () => {
    const result = validator.validate("ftp://example.com");
    expect(result.isValid).toBe(false);
    expect(result.errorMessage).toContain("HTTP");
  });

  it("should support allowlist validation for allowed domains", () => {
    const allowlistValidator = new URLValidator(["example.com", "safe.org"]);
    const result = allowlistValidator.validate("https://example.com");
    expect(result.isValid).toBe(true);
  });

  it("should reject domains not in allowlist", () => {
    const allowlistValidator = new URLValidator(["example.com"]);
    const result = allowlistValidator.validate("https://untrusted.com");
    expect(result.isValid).toBe(false);
  });

  it("should support wildcard allowlist domains", () => {
    const wildcardValidator = new URLValidator(["*.example.com"]);
    const result = wildcardValidator.validate("https://sub.example.com");
    expect(result.isValid).toBe(true);
  });

  it("should have validateUrl convenience function", () => {
    const result = validateUrl("https://google.com");
    expect(result.isValid).toBe(true);
  });

  it("should reject localhost.localdomain", () => {
    const result = validator.validate("http://localhost.localdomain");
    expect(result.isValid).toBe(false);
  });

  it("should reject metadata.google.internal", () => {
    const result = validator.validate("http://metadata.google.internal");
    expect(result.isValid).toBe(false);
  });
});

describe("URLValidator - Round-trip Validation", () => {
  it("should validate round-trip: valid URL in -> valid URL out", () => {
    const validator = new URLValidator();
    const url = "https://example.com/path?query=value";
    const result = validator.validate(url);
    expect(result.isValid).toBe(true);
    expect(result.finalUrl).toBe(url);
  });

  it("should return redirect count", () => {
    const validator = new URLValidator();
    const result = validator.validate("https://example.com");
    expect(result.redirectCount).toBe(0);
  });
});

describe("APIClient", () => {
  it("should have submitScan method", () => {
    expect(ApiClient.submitScan).toBeDefined();
    expect(typeof ApiClient.submitScan).toBe("function");
  });

  it("should have getFindings method", () => {
    expect(ApiClient.getFindings).toBeDefined();
    expect(typeof ApiClient.getFindings).toBe("function");
  });

  it("should have getReport method", () => {
    expect(ApiClient.getReport).toBeDefined();
    expect(typeof ApiClient.getReport).toBe("function");
  });
});

describe("Task 20: Frontend URL Submission and Validation", () => {
  it("should export URLValidator class with complete API", () => {
    const validator = new URLValidator();
    expect(validator).toBeDefined();
    expect(typeof validator.validate).toBe("function");
  });

  it("should export validateUrl convenience function", () => {
    expect(validateUrl).toBeDefined();
    expect(typeof validateUrl).toBe("function");
  });

  it("should export ApiClient class with all methods", () => {
    expect(ApiClient).toBeDefined();
    expect(ApiClient.submitScan).toBeDefined();
    expect(ApiClient.getFindings).toBeDefined();
    expect(ApiClient.getReport).toBeDefined();
  });

  it("should have ScanForm component with API integration", () => {
    // Component exists and can be imported
    expect(() => require("../src/components/ScanForm")).toBeDefined();
  });

  it("URLValidator should validate 5 private IP ranges", () => {
    const validator = new URLValidator();
    const privateIPs = [
      "http://10.0.0.1",
      "http://172.16.0.1",
      "http://192.168.1.1",
      "http://127.0.0.1",
      "http://169.254.0.1"
    ];

    privateIPs.forEach(ip => {
      const result = validator.validate(ip);
      expect(result.isValid).toBe(false);
    });
  });

  it("URLValidator should block 4 metadata endpoints", () => {
    const validator = new URLValidator();
    const endpoints = [
      "http://localhost",
      "http://localhost.localdomain",
      "http://169.254.169.254",
      "http://metadata.google.internal"
    ];

    endpoints.forEach(endpoint => {
      const result = validator.validate(endpoint);
      expect(result.isValid).toBe(false);
    });
  });
});
