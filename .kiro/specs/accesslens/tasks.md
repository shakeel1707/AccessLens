# AccessLens Tasks

## Task Overview

The AccessLens MVP consists of 25 implementation tasks organized by workflow phase. All tasks require property-based testing (PBT) where applicable.

## Phase 1: Backend Infrastructure (Tasks 1–5)

### Task 1: Set Up FastAPI Backend Project
**Dependencies:** None
**Priority:** Required
**Effort:** 2 hours
**Description:** Initialize FastAPI project with project structure, configuration management, dependency injection, logging, and error handling middleware.
**Definition of Done:**
- FastAPI app initialized with routers for /scan, /repair, /patch, /verification
- Configuration loaded from environment variables (dev/test/prod)
- Logging configured with CloudWatch integration
- Error middleware for graceful failure handling
- Async request handlers ready
- Unit tests pass for configuration loading

### Task 2: Implement DynamoDB Schema and Access Layer
**Dependencies:** Task 1
**Priority:** Required
**Effort:** 3 hours
**Description:** Define DynamoDB tables (Scans, Findings, Repairs, VerificationResults) and create Boto3 access layer with CRUD operations, error handling, and TTL policies.
**Definition of Done:**
- All 4 DynamoDB tables created with correct primary keys
- CRUD operations implemented and tested
- Connection pooling configured
- TTL policies set (90-day auto-delete)
- Unit tests pass for all CRUD operations
- Mock DynamoDB fixtures for testing

### Task 3: Implement URL Validation and SSRF Prevention
**Dependencies:** Task 1
**Priority:** Required
**Effort:** 3 hours
**Description:** Implement URL validation logic with allowlist enforcement, private network blocking, redirect detection (up to 5 hops), and loop detection. Include PBT Suite 4 (URL Validation).
**Definition of Done:**
- URL parser implemented with allowlist logic
- Localhost and private networks rejected
- Redirect following implemented (max 5 hops)
- Loop detection working
- PBT Suite 4 passes (fast-check URL generator)
- Unit tests cover edge cases (IPv6, ports, fragments)
- Security tests for common SSRF patterns

### Task 4: Implement Finding ID Generation and Deduplication
**Dependencies:** Task 2
**Priority:** Required
**Effort:** 2 hours
**Description:** Implement SHA256-based finding ID generation, deduplication logic, and deterministic sorting by severity. Include PBT Suite 1 (Finding Structure) and Suite 5 (Deduplication).
**Definition of Done:**
- SHA256 ID generation: ID = SHA256(rule_id || selector || description)
- Deduplication algorithm removes exact duplicates
- Findings sorted by severity (critical → minor)
- PBT Suite 1 passes (Hypothesis finding generator)
- PBT Suite 5 passes (Hypothesis deduplication)
- Unit tests cover edge cases (Unicode, empty fields)

### Task 5: Implement API Payload Validation and Error Responses
**Dependencies:** Task 1
**Priority:** Required
**Effort:** 2 hours
**Description:** Implement request/response validation, error response formatting, and boundary checking. Include PBT Suite 6 (API Payload).
**Definition of Done:**
- Pydantic models for all API requests/responses
- Boundary validation: URL max 2048 chars, findings max 10000 items
- Error response format: { code, message, status_code, request_id }
- PBT Suite 6 passes (Hypothesis payload generator)
- Unit tests for valid/invalid payloads
- Rate limiting configured (10 req/min per user)

## Phase 2: Scanning Engine (Tasks 6–9)

### Task 6: Implement Playwright Scanning Engine
**Dependencies:** Task 2, Task 4
**Priority:** Required
**Effort:** 4 hours
**Description:** Implement Playwright-based browser automation for website scanning, axe-core integration, and finding extraction with proper error handling.
**Definition of Done:**
- Playwright browser context created and managed
- axe-core run via Node.js or Python wrapper
- Findings extracted and normalized
- Scan timeout: 30 seconds
- Error handling for network timeouts, invalid HTML, browser crashes
- Unit tests for findings extraction
- Integration tests with mock websites

### Task 7: Implement Scan API Endpoint
**Dependencies:** Task 2, Task 3, Task 5, Task 6
**Priority:** Required
**Effort:** 2 hours
**Description:** Implement POST /api/scan endpoint with async scan job dispatch to Lambda, result persistence, and user-facing status updates.
**Definition of Done:**
- POST /api/scan endpoint implemented
- URL validation called before Lambda invocation
- Async job dispatch (background task or Lambda invoke)
- Scan status persisted to DynamoDB
- GET /api/scan/{scan_id} returns status and findings
- Error responses for invalid URLs
- Integration tests for scan workflow

### Task 8: Implement Finding Caching and Retrieval
**Dependencies:** Task 2, Task 4, Task 7
**Priority:** Required
**Effort:** 2 hours
**Description:** Implement finding retrieval from DynamoDB, deduplication, and caching layer for findings within a scan.
**Definition of Done:**
- GET /api/scan/{scan_id}/findings returns deduplicated findings
- Findings include all required fields (rule_id, severity, selector, HTML)
- Sorting by severity applied
- Finding count metadata included
- Unit tests for retrieval and deduplication

### Task 9: Implement Scan Error Handling and Retry Logic
**Dependencies:** Task 6, Task 7
**Priority:** Required
**Effort:** 2 hours
**Description:** Implement error handling for scan failures (network timeouts, invalid HTML, browser crashes) with exponential backoff retry logic (max 2 retries).
**Definition of Done:**
- Retry logic implemented with exponential backoff
- Failed scans marked with error status and message
- Error logs include details for debugging
- User notified of failures
- Unit tests for retry scenarios
- Integration tests for network failure simulation

## Phase 3: AI Integration (Tasks 10–12)

### Task 10: Implement Bedrock Integration for Explanations
**Dependencies:** Task 1, Task 2
**Priority:** Required
**Effort:** 3 hours
**Description:** Implement Bedrock API calls for generating accessibility violation explanations, caching logic (24-hour TTL), and fallback text. Include PBT Suite 7 (JSON Round-Trip).
**Definition of Done:**
- Bedrock API calls implemented with boto3
- Prompt engineering for clear explanations (max 500 chars)
- Caching by finding_id in DynamoDB
- Fallback explanation provided on Bedrock failure
- Exponential backoff for quota handling
- PBT Suite 7 passes (JSON serialization integrity)
- Unit tests for caching logic
- Integration tests with mock Bedrock responses

### Task 11: Implement Repair Generation Endpoint
**Dependencies:** Task 1, Task 2, Task 5, Task 10
**Priority:** Required
**Effort:** 3 hours
**Description:** Implement POST /api/repair/generate endpoint with Bedrock-based patch generation for applicable rule types, confidence scoring, and max 10 repairs per scan. Include PBT Suite 2 (Repair Patch Schema).
**Definition of Done:**
- POST /api/repair/generate endpoint implemented
- Rule applicability check (MVP: alt-text, headings, contrast, form labels, ARIA)
- Bedrock generates patches (HTML, CSS, JavaScript targets)
- Patch schema includes: file_type, content, selector, line_numbers, confidence, assumptions, explanation
- Max 10 repairs per scan (most severe first)
- Timeout: 20 seconds per repair
- PBT Suite 2 passes (unsafe patch rejection)
- Unit tests for rule applicability
- Integration tests with mock Bedrock

### Task 12: Implement Repair Review Endpoint
**Dependencies:** Task 2, Task 5, Task 11
**Priority:** Required
**Effort:** 2 hours
**Description:** Implement POST /api/repair/approve endpoint for user approval/rejection of repairs with persistence, history tracking, and regeneration requests.
**Definition of Done:**
- POST /api/repair/approve endpoint implemented
- Repair persisted with review_status (approved|rejected|pending)
- User comments/reasons captured
- Regeneration supported via separate request
- History preserved (no data loss on regeneration)
- Unit tests for approval/rejection logic
- Integration tests for full repair lifecycle

## Phase 4: Patch Application and Verification (Tasks 13–16)

### Task 13: Implement Isolated Environment Setup
**Dependencies:** Task 2, Task 6
**Priority:** Required
**Effort:** 3 hours
**Description:** Implement ephemeral isolated Playwright environments for patch application, including container lifecycle management, original file protection, and cleanup.
**Definition of Done:**
- Isolated Playwright context created per patch operation
- Target website fetched and rendered
- Original files never modified (read-only copy or separate environment)
- Environment cleanup on completion or timeout (5-minute auto-cleanup)
- Logging of all environment creation and destruction
- Unit tests for environment setup/teardown

### Task 14: Implement Patch Application Logic
**Dependencies:** Task 2, Task 13
**Priority:** Required
**Effort:** 4 hours
**Description:** Implement patch application to DOM/HTML in isolated environment with safety checks (no injection, no scheme changes, target selector only). Include PBT Suites 2, 8, 9 (Patch Safety, Isolation, Policy).
**Definition of Done:**
- Patch application logic implemented (DOM manipulation)
- Safety checks: no injection patterns, no scheme changes, target selector only
- Rollback on failure (automatic)
- Audit trail: all modifications logged with timestamp
- Unrelated content preservation verified
- PBT Suite 2 passes (unsafe patch rejection)
- PBT Suite 8 passes (rollback on failure)
- PBT Suite 9 passes (policy compliance)
- Unit tests for patch application
- Integration tests for conflict detection

### Task 15: Implement Patch Application Endpoint
**Dependencies:** Task 2, Task 5, Task 12, Task 14
**Priority:** Required
**Effort:** 2 hours
**Description:** Implement POST /api/patch/apply endpoint for batch patch application in isolated environment with async dispatch and status tracking.
**Definition of Done:**
- POST /api/patch/apply endpoint implemented
- Async dispatch to Lambda for patch application
- Patches applied in sequence to single isolated environment
- Status tracking: pending → in_progress → completed|failed
- Error details captured for failed patches
- Integration tests for patch workflow

### Task 16: Implement Verification and Before/After Comparison
**Dependencies:** Task 2, Task 6, Task 15
**Priority:** Required
**Effort:** 3 hours
**Description:** Implement re-scanning in isolated environment after patches, before/after finding comparison (fixed, new, unresolved), and result persistence. Include PBT Suite 3 (Finding Identity and Comparison).
**Definition of Done:**
- Re-scan logic after patches in isolated environment
- Same axe-core configuration as original scan
- Before/after comparison: identifies fixed (removed), new (added), unresolved (still present)
- Counts: fixed_count, new_violations_count, unresolved_count
- Results persisted to DynamoDB
- PBT Suite 3 passes (Hypothesis comparison generator)
- Unit tests for comparison logic
- Integration tests for full verification workflow

## Phase 5: Reporting and Frontend (Tasks 17–20)

### Task 17: Implement Report Generation Logic
**Dependencies:** Task 2, Task 16
**Priority:** Required
**Effort:** 2 hours
**Description:** Generate compliance reports with before/after metrics, violation details, repair status, and recommendations in JSON and HTML formats.
**Definition of Done:**
- Report JSON structure: URL, date, WCAG version, violations (before/after), breakdown by severity, fixed count, unresolved count
- Report includes: violations with explanations, approved repairs, verification status, recommendations
- JSON export implemented
- HTML export template implemented
- Report downloadable with timestamp and scan_id
- Unit tests for report generation

### Task 18: Implement Report Download Endpoint
**Dependencies:** Task 2, Task 17
**Priority:** Required
**Effort:** 1 hour
**Description:** Implement GET /api/report/{scan_id} endpoint with format negotiation (JSON|HTML) and S3 upload for long-term storage.
**Definition of Done:**
- GET /api/report/{scan_id} endpoint implemented
- Format parameter: json or html
- Report generated from DynamoDB data
- S3 signed URL provided for download
- Report cached in S3 for 30 days
- Unit tests for endpoint

### Task 19: Implement Frontend React Project with Vite
**Dependencies:** None (parallel with backend)
**Priority:** Required
**Effort:** 2 hours
**Description:** Initialize React + TypeScript + Vite project with component structure (ScanForm, FindingsList, RepairReview, ReportDisplay, ProgressIndicator), state management via Context API, and styling.
**Definition of Done:**
- Vite project initialized with React + TypeScript
- Component files created (ScanForm, FindingsList, RepairReview, ReportDisplay, ProgressIndicator)
- React Context API setup for global state (scan status, findings, repairs)
- Styling framework chosen (Tailwind, CSS-in-JS, etc.)
- Build and dev server configured
- Unit tests for components (Vitest)

### Task 20: Implement Frontend URL Submission and Validation
**Dependencies:** Task 3, Task 19
**Priority:** Required
**Effort:** 2 hours
**Description:** Implement ScanForm component with URL input field, client-side URL validation (matching server-side logic), loading state, and error feedback.
**Definition of Done:**
- ScanForm component with URL input field
- Client-side URL validation (allowlist, SSRF prevention)
- Immediate feedback: valid (green) / invalid (red)
- Submit button enabled only for valid URLs
- Loading state during scan
- Error messages displayed to user
- Component tests with Vitest
- PBT via fast-check for URL validation round-trip

## Phase 6: Frontend UI and Workflows (Tasks 21–23)

### Task 21: Implement Findings Display Component
**Dependencies:** Task 20
**Priority:** Required
**Effort:** 2 hours
**Description:** Implement FindingsList component to display findings with explanations, severity badges, and organization by category.
**Definition of Done:**
- FindingsList component displays findings with explanations
- Severity badges (critical, serious, moderate, minor) with color coding
- Findings organized by severity or category
- Click to expand for full details
- Accessibility: semantic HTML, ARIA labels, keyboard navigation
- Component tests

### Task 22: Implement Repair Review Component
**Dependencies:** Task 21
**Priority:** Required
**Effort:** 2 hours
**Description:** Implement RepairReview component for displaying repair proposals with code diff, confidence score, assumptions, and user controls (approve/reject/regenerate).
**Definition of Done:**
- RepairReview component displays each repair proposal
- Original code vs. proposed patch visible (side-by-side or diff format)
- Confidence score displayed (high/medium/low)
- Assumptions and warnings shown
- User can approve, reject, or request regeneration
- State tracked: pending → approved|rejected
- Component tests

### Task 23: Implement Report Display Component
**Dependencies:** Task 17
**Priority:** Required
**Effort:** 2 hours
**Description:** Implement ReportDisplay component showing before/after metrics, violation breakdown, fixed count, unresolved count, and download button for JSON/HTML export.
**Definition of Done:**
- ReportDisplay shows URL, scan date, WCAG version
- Before/after violation counts displayed
- Breakdown by severity shown (chart or table)
- Fixed/unresolved counts highlighted
- Download buttons for JSON and HTML
- Print-friendly styling
- Component tests

## Phase 7: Property-Based Testing Suites (Tasks 24–25)

### Task 24: Implement PBT Suites 1–5 (Backend)
**Dependencies:** Tasks 1–8, Task 11, Task 12, Task 14, Task 16
**Priority:** Required
**Effort:** 6 hours
**Description:** Implement and execute PBT Suites 1–5 (Finding Structure, Repair Patch Schema, Finding Identity, URL Validation, Deduplication) using Hypothesis + pytest with reproducible seeds and failure reporting.
**Definition of Done:**
- Suite 1: test_finding_structure.py passes (ID determinism, severity validation)
- Suite 2: test_patch_safety.py passes (no injection, target selector only)
- Suite 3: test_finding_identity.py passes (stable IDs, correct categorization)
- Suite 4: test_url_validation.py passes (allowlist enforcement, redirect handling)
- Suite 5: test_deduplication.py passes (duplicates removed, deterministic output)
- All suites with reproducible seeds recorded
- Failure reporting includes seed, input, expected vs. actual
- CI/CD integration for automated runs

### Task 25: Implement PBT Suites 6–9 (Backend) and Suite 7 (Frontend)
**Dependencies:** Task 24, Task 19
**Priority:** Required
**Effort:** 6 hours
**Description:** Implement and execute PBT Suites 6–9 (API Payload, JSON Round-Trip, Isolation, Patch Policy) using Hypothesis + pytest (backend) and fast-check (frontend Suite 7) with reproducible seeds.
**Definition of Done:**
- Suite 6: test_api_payload.py passes (required fields, boundaries, error responses)
- Suite 7 (Frontend): test_json_roundtrip.test.ts passes (serialization inverse, Unicode)
- Suite 8: test_isolation.py passes (no corruption, rollback success)
- Suite 9: test_patch_policy.py passes (policy compliance, unrelated content preserved)
- All suites with reproducible seeds recorded
- Failure reporting includes seed, input, expected vs. actual
- CI/CD integration for automated runs
- Coverage report: >80% including all PBT suites

## Integration and Final Tasks (Tasks 26–28)

### Task 26: End-to-End Testing and Integration
**Dependencies:** All previous tasks
**Priority:** Required
**Effort:** 4 hours
**Description:** Implement E2E tests covering full workflow (URL submission → scan → repair → verification → report download) using test environment with mock AWS services or localstack.
**Definition of Done:**
- E2E tests for complete workflow (submission to report)
- Test with realistic accessibility violations
- Verify all data persisted correctly
- Test error scenarios (network failures, invalid URLs)
- E2E tests pass consistently
- Documentation of test scenarios

### Task 27: Security and Compliance Testing
**Dependencies:** All previous tasks
**Priority:** Required
**Effort:** 3 hours
**Description:** Implement security tests for SSRF prevention, unsafe patch rejection, input sanitization, and data encryption. Document WCAG 2.1 Level AA compliance of UI.
**Definition of Done:**
- SSRF attack tests (redirects, private networks)
- Unsafe patch injection tests
- Input sanitization tests
- Rate limiting tests
- Data encryption verification (TLS, DynamoDB)
- Accessibility audit of AccessLens UI (WCAG 2.1 Level AA)
- Security test report documented

### Task 28: Deployment Configuration and CI/CD
**Dependencies:** All previous tasks
**Priority:** Required
**Effort:** 3 hours
**Description:** Set up CloudFormation/SAM for AWS infrastructure (Lambda, API Gateway, DynamoDB, S3, CloudWatch), configure CI/CD pipeline for build/test/deploy, and document deployment procedures.
**Definition of Done:**
- CloudFormation/SAM template for infrastructure
- Lambda functions packaged and ready
- API Gateway configured
- DynamoDB tables and policies defined
- S3 buckets configured (Lambda code, reports, frontend)
- GitHub Actions workflow (build, test, deploy)
- Environment-specific configurations (dev/test/prod)
- Deployment documentation
- Local development setup documented

## Task Dependency Graph

`
Task 1 (FastAPI) → Task 2 (DynamoDB) → Task 4 (Finding ID) → Task 7 (Scan Endpoint)
                ↓
                Task 3 (URL Validation) → Task 7
                Task 5 (API Validation) → Task 7
                Task 6 (Playwright) → Task 7
                ↓
                Task 8 (Finding Caching) → Task 9 (Error Handling)
                ↓
                Task 10 (Bedrock Explanations) → Task 11 (Repair Generation)
                Task 11 → Task 12 (Repair Review)
                ↓
                Task 13 (Isolated Environment) → Task 14 (Patch Application)
                Task 14 → Task 15 (Patch Endpoint)
                ↓
                Task 16 (Verification) → Task 17 (Report Generation)
                Task 17 → Task 18 (Report Endpoint)
                ↓
                Task 19 (React Project) → Task 20 (URL Submission)
                Task 20 → Task 21 (Findings Display)
                Task 21 → Task 22 (Repair Review UI)
                Task 22 → Task 23 (Report Display)
                ↓
                Task 24 (PBT Suites 1–5) → Task 25 (PBT Suites 6–9)
                ↓
                Task 26 (E2E Tests) → Task 27 (Security Tests)
                Task 27 → Task 28 (Deployment)
`

## Testing Summary

- **Unit Tests:** Each task includes unit tests for critical functions
- **Integration Tests:** Workflows tested across API layers
- **Component Tests (Frontend):** React components tested with Vitest
- **PBT Suites:** 9 suites covering all major invariants; runs in CI/CD
- **E2E Tests:** Full workflow simulation with test environment
- **Security Tests:** SSRF, injection, sanitization, encryption verified
- **Accessibility Tests:** AccessLens UI verified for WCAG 2.1 Level AA compliance

## Success Criteria

- All 28 tasks completed and passing tests
- All 9 PBT suites passing with reproducible seeds
- E2E tests passing for complete workflow
- Security tests passing (zero vulnerabilities)
- Code coverage >80% including all PBT suites
- AccessLens UI fully accessible (WCAG 2.1 Level AA)
- Deployment procedures documented and tested
