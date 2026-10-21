# AccessLens Requirements

**Project:** AccessLens AI-powered website accessibility detection and repair platform
**Team:** 1-2 developers
**Target Users:** Developers, students, website owners, accessibility testers
**Scope:** Software-only MVP

## 1. Introduction

AccessLens provides a complete workflow: Scan → Detect → Explain → Generate Repair → Review → Apply to Isolated Copy → Verify → Report

### 1.1 Core Workflow

- Scan: Submit target website URL for analysis
- Detect: Run axe-core to identify accessibility violations
- Explain: Use Bedrock to generate human-readable explanations
- Generate Repair: AI generates code patches for common fixes
- Review: User reviews and approves/rejects repair proposals
- Apply to Isolated Copy: Apply patches in container-based browser environment
- Verify: Re-run axe-core to confirm violations resolved
- Report: Generate detailed compliance report with before/after metrics

### 1.2 MVP Scope

Complete core workflow for common WCAG 2.1 Level A/AA violations. Out of scope: bulk scanning, advanced reporting, third-party integrations.

## 2. Glossary

- Accessibility Violation: WCAG 2.1 failure detected by axe-core
- Finding: Detected violation with rule ID, severity, selector, description
- Repair Proposal: AI-generated code patch
- Isolated Copy: Container-based browser environment for patch testing
- Patch: Approved code modification
- WCAG 2.1: Web Content Accessibility Guidelines Level A and AA
- axe-core: Accessibility testing engine
- Bedrock: Amazon generative AI service

## 3. Functional Requirements

### 3.1 Website Submission and Scanning

#### Requirement 1: Accept Website URL Input
As a user, I want to submit a website URL for accessibility analysis.
- UI text input for website URL
- URL validation: HTTP/HTTPS only; reject localhost, private networks, data URIs
- SSRF prevention: allowlist and redirect detection
- Immediate validation feedback
- Submit button triggers scan
- Loading state during scanning

#### Requirement 2: Execute Accessibility Scanning
As the system, I need to run accessibility scans on submitted URLs.
- Use axe-core for scanning
- Include WCAG 2.1 Level A and AA rules
- Playwright headless Chrome environment
- Complete within 30 seconds
- Network error handling
- Persist to DynamoDB: scan_id, URL, timestamp, findings
- Findings: rule ID, severity, selector, HTML snippet, message

### 3.2 Violation Detection and Explanation

#### Requirement 3: Process and Validate Findings
As the system, I need to validate and deduplicate findings.
- Deduplicate findings: same rule_id + selector
- Exclude malformed findings
- Deterministic IDs: SHA256(rule_id || selector || description)
- Sort by severity
- Display counts in reports

#### Requirement 4: Generate AI Explanations
As a user, I want violations explained in plain language.
- Bedrock generates explanation (max 500 chars)
- Include violation type, WCAG criterion, impact, recommended action
- Cache by finding ID
- Fallback explanation if Bedrock fails
- Include in results and reports

### 3.3 Repair Generation and Review

#### Requirement 5: Generate Repair Proposals
As a user, I want AI-generated code repairs for common violations.
- Evaluate repair applicability (alt-text, headings, contrast, form labels, ARIA)
- Bedrock generates patch (HTML, CSS, JavaScript)
- Include: content, rule type, confidence, assumptions, warnings
- Patch schema: file_type, content, selector, line_numbers, explanation
- Max 10 repairs per scan (most severe first)
- 20-second timeout per repair

#### Requirement 6: Review and Approve Repairs
As a user, I want to review and approve/reject repairs before application.
- Display: original code, proposed patch, confidence, assumptions
- User can approve, reject, or regenerate
- Persist: review_status, user_id
- Mark rejected with reason
- Preserve history
- Persist to DynamoDB

### 3.4 Isolated Application and Verification

#### Requirement 7: Apply Patches in Isolated Environment
As the system, I need to apply patches safely to isolated copy.
- Create container-based browser environment
- Fetch and render target website
- Apply patches in sequence
- Prevent: unsafe injection, scheme changes, unrelated modifications
- Log all changes with timestamps
- Automatic rollback on failure
- Destroy environment after verification

#### Requirement 8: Verify Fixes
As the system, I need to re-scan and verify violations resolved.
- Run axe-core scan after patches
- Same configuration as original
- Compare: resolved, new, unresolved
- Results: fixed_count, new_violations_count, unresolved_count
- User notification on failure
- Persist to DynamoDB linked to scan_id

### 3.5 Reporting and Data Persistence

#### Requirement 9: Generate Compliance Reports
As a user, I want before/after metrics in reports.
- Include: URL, date, WCAG version, violations, severity, fixed, unresolved
- Display: violations, explanations, repairs, status, recommendations
- Export JSON or HTML
- Downloadable with timestamp and scan_id
- Compliance documentation detail

#### Requirement 10: Persist and Retrieve Scan Results
As the system, I need to store results durably.
- Persist to DynamoDB
- Data: scan_id, URL, timestamp, user_id, findings, repairs, verification_results
- Retrieve by scan_id (MVP)
- Retention: 90 days; auto-delete
- Scan history accessible in UI

## 4. Non-Functional Requirements

### 4.1 Performance
- Scan latency: <30 seconds
- Repair generation: <20 seconds
- API response: <500ms non-scan
- DB query: <100ms

### 4.2 Scalability
- Concurrent scans: 5-10
- DynamoDB on-demand
- Playwright containers: max 10

### 4.3 Reliability
- 99.5% uptime target
- All failures logged and notified
- Timeout handling for external calls
- Orphaned cleanup: 5 minutes

### 4.4 Security
- URL allowlist, SSRF prevention
- Repair content filtering
- Bedrock IAM roles
- Encryption: at rest and in transit (TLS 1.2+)
- Input validation and escaping

### 4.5 Accessibility
- WCAG 2.1 Level AA compliance
- Screen reader support
- Keyboard navigation

## 5. Business Rules

### 5.1 Repair Applicability
- MVP supported: alt-text, headings, contrast, form labels, ARIA
- Unsupported: user notified
- Confidence level guides decisions

### 5.2 Finding Identity
- ID = SHA256(rule_id || selector || description)
- Linked across scans
- Duplicates removed

### 5.3 Patch Safety
- Never original files
- Logged modifications
- Explicit user approval
- Unsafe patches rejected

### 5.4 Verification
- Fixed: absent in post-patch scan
- New violations flagged
- Unresolved included

### 5.5 Data Retention
- 90 days retained
- URL and findings only, not page source
- Anonymized user_id

## 6. Property-Based Testing Requirements

### 6.1 Philosophy
PBT verifies invariants systematically. Complements scenario tests. Tests deterministic and reproducible.

### 6.2 PBT Suite 1: Finding Structure
Invariants: rule_id, severity (critical|serious|moderate|minor), selector, HTML, description. IDs deterministic. Counts <= DOM elements. Severity from allowed set.

### 6.3 PBT Suite 2: Repair Patch Schema
Invariants: file_type (html|css|js), content, confidence (high|medium|low), explanation. No unsafe schemes. Target selector only. Original preserved.

### 6.4 PBT Suite 3: Finding Identity and Comparison
Invariants: ID stable. Correctly identifies: fixed, new, unresolved. Fixed = ID absent post-patch. Unresolved retained.

### 6.5 PBT Suite 4: URL Validation
Invariants: Valid = http/https + external host. Invalid = localhost, private networks, non-HTTP, data URIs. SSRF prevented. Consistent.

### 6.6 PBT Suite 5: Empty and Duplicates
Invariants: Empty valid. Duplicates removed. Report deterministic.

### 6.7 PBT Suite 6: API Payload
Invariants: Valid payloads include required fields. Errors include code, message, status. JSON responses. Boundaries: URL 2048 chars, findings 10000 items.

### 6.8 PBT Suite 7: JSON Round-Trip
Invariants: Serialization/deserialization inverse. Unicode preserved. Empty collections preserved. Optional fields consistent.

### 6.9 PBT Suite 8: Isolation and Patches
Invariants: Isolated environment unaffected. Patches sequential. Failures don't corrupt (rollback). Operations logged.

### 6.10 PBT Suite 9: Patch Policy
Invariants: Policy compliant (allowed types/selectors). No unrelated modifications. Original preserved. Non-destructive.

## 7. Testing Strategy
- PBT: fast-check (TypeScript), Hypothesis (Python)
- Unit: validation, ID generation, deduplication, patch safety
- Integration: workflows
- Component: React components
- E2E: full workflows
- Security: SSRF, content validation, unsafe patches
- Accessibility: AccessLens UI
- Scenario-based: realistic user scenarios

## 8. Deployment and Infrastructure

### 8.1 AWS Services
- API Gateway: REST endpoints
- Lambda: scan handler, repair generator, verifier, reporter
- DynamoDB: results, findings, repairs, verification (on-demand)
- S3: report exports
- CloudWatch: logging, monitoring, errors
- IAM: role-based access, Bedrock credentials

### 8.2 Local Development
- Frontend: React + Vite, TypeScript
- Backend: FastAPI + Python
- Testing: Playwright, axe-core
- Isolation: Docker (optional)

### 8.3 Continuous Integration
- Pre-commit: lint, type check
- CI: build, test (unit, integration, PBT, E2E), coverage
- Deployment: auto to AWS (dev/test/prod)

## 9. Out of Scope
- Bulk scanning
- Advanced reporting
- Third-party integrations
- Mobile app
- Custom rulesets
- Multi-tenant
- Real-time scanning
- Standards beyond WCAG 2.1

## 10. Success Criteria
- MVP: all core steps functional
- Performance: <30s scans, <500ms API
- Reliability: 99.5% uptime, zero unhandled errors
- User satisfaction: clear explanations, accurate repairs
- Testing: >80% coverage, all PBT pass, all security tests pass
- Accessibility: WCAG 2.1 Level AA