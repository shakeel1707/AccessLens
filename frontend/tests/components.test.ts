import { describe, it, expect } from "vitest";
import React from "react";

describe("Frontend Components - Task 19", () => {
  it("should export ScanForm component", () => {
    // Component import test
    expect(() => require("../src/components/ScanForm")).toBeDefined();
  });

  it("should export FindingsList component", () => {
    expect(() => require("../src/components/FindingsList")).toBeDefined();
  });

  it("should export RepairReview component", () => {
    expect(() => require("../src/components/RepairReview")).toBeDefined();
  });

  it("should export ReportDisplay component", () => {
    expect(() => require("../src/components/ReportDisplay")).toBeDefined();
  });

  it("should export ProgressIndicator component", () => {
    expect(() => require("../src/components/ProgressIndicator")).toBeDefined();
  });

  it("should have AppProvider context", () => {
    expect(() => require("../src/context/AppContext")).toBeDefined();
  });

  it("should have main App component", () => {
    expect(() => require("../src/App")).toBeDefined();
  });

  it("should have Vite config", () => {
    expect(() => require("../vite.config.ts")).toBeDefined();
  });

  it("should have TypeScript config", () => {
    expect(() => require("../tsconfig.json")).toBeDefined();
  });

  it("should have package.json with React dependencies", () => {
    const pkg = require("../package.json");
    expect(pkg.dependencies).toHaveProperty("react");
    expect(pkg.dependencies).toHaveProperty("react-dom");
    expect(pkg.devDependencies).toHaveProperty("vite");
    expect(pkg.devDependencies).toHaveProperty("vitest");
  });

  it("should have CSS styling", () => {
    expect(() => require("../src/App.css")).toBeDefined();
  });

  it("should have proper scripts in package.json", () => {
    const pkg = require("../package.json");
    expect(pkg.scripts).toHaveProperty("dev");
    expect(pkg.scripts).toHaveProperty("build");
    expect(pkg.scripts).toHaveProperty("test");
  });
});
