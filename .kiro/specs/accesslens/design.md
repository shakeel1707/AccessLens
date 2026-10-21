# AccessLens Design

## 1. System Architecture

### 1.1 High-Level Components

- Frontend: React + Vite + TypeScript
- Backend API: FastAPI + Python
- Scan Engine: Lambda + Playwright + axe-core
- AI Service: Amazon Bedrock
- Data Store: DynamoDB
- File Storage: S3
- Monitoring: CloudWatch

### 1.2 Data Flow

1. User submits URL via Frontend
2. Frontend validates URL (SSRF prevention)
3. Frontend sends scan request to Backend API
4. Backend invokes Lambda scan function
5. Lambda spawns Playwright container, runs axe-core
6. Findings persisted to DynamoDB
7. Backend calls Bedrock for explanations
8. Findings + explanations returned to Frontend
9. User reviews repairs (Bedrock-generated)
10. User approves repairs; persisted to DynamoDB
11. Backend invokes Lambda patch-application
12. Lambda spawns isolated Playwright environment
13. Lambda re-runs axe-core in isolated environment
14. Verification results persisted to DynamoDB
15. Report generated and exported to S3
16. Frontend displays report

### 1.3 Isolation Strategy

- Scan Isolation: Each scan in dedicated Playwright process
- Patch Isolation: Ephemeral isolated environment (separate from original)
- Container Lifecycle: Spun up per operation, destroyed after completion
- Original Protection: Original files never modified
- Cleanup: Auto-destroyed containers; DynamoDB cleanup after 90 days

## 2. Database Schema (DynamoDB)

### 2.1 Scans Table

- PK: scan_id (UUID)
- SK: timestamp (ISO 8601)
- Attributes: URL, user_id, status, finding_count, creation_date

### 2.2 Findings Table

- PK: scan_id
- SK: finding_id (SHA256)
- Attributes: rule_id, severity, selector, html_snippet, description, explanation, cached_at

### 2.3 Repairs Table

- PK: scan_id
- SK: finding_id
- Attributes: rule_id, proposed_patch, confidence, assumptions, review_status, reviewer_comment, created_at

### 2.4 VerificationResults Table

- PK: scan_id
- SK: verification_id
- Attributes: fixed_count, new_violations_count, unresolved_count, before_findings, after_findings, comparison_result, created_at

## 3. API Endpoints

### 3.1 POST /api/scan
- Request: { url, user_id }
- Response: { scan_id, status, message }
- Validation: URL allowlist, SSRF prevention
- Async: Returns immediately

### 3.2 GET /api/scan/{scan_id}
- Response: { scan_id, status, findings, explanation_cache, message }

### 3.3 POST /api/repair/generate
- Request: { scan_id, finding_ids[] }
- Response: { scan_id, repairs[] }

### 3.4 POST /api/repair/approve
- Request: { scan_id, repair_id, approved, comment }
- Response: { repair_id, status }

### 3.5 POST /api/patch/apply
- Request: { scan_id, repair_ids[] }
- Response: { scan_id, application_status, message }
- Async: Spawns isolated environment

### 3.6 GET /api/verification/{scan_id}
- Response: { scan_id, fixed_count, new_violations, unresolved, comparison, message }

### 3.7 GET /api/report/{scan_id}
- Query params: format (json|html)
- Response: Report content or S3 signed URL

## 4. Property-Based Testing Strategy

### 4.1 PBT Frameworks

- Frontend: fast-check (TypeScript)
- Backend: Hypothesis (Python) + pytest

### 4.2 PBT Suites Implementation

#### Suite 1: Finding Structure (Backend)
- test_finding_structure.py using Hypothesis
- Generator: valid/invalid findings
- Invariants: ID determinism, severity validation, field presence

#### Suite 2: Repair Patch Safety (Backend)
- test_patch_safety.py using Hypothesis
- Generator: safe/unsafe patches
- Invariants: no injection, target selector only, original preserved

#### Suite 3: Finding Identity (Backend)
- test_finding_identity.py using Hypothesis
- Invariants: stable IDs, correct categorization

#### Suite 4: URL Validation (Backend)
- test_url_validation.py using Hypothesis
- Invariants: allowlist enforcement, redirect handling, consistency

#### Suite 5: Deduplication (Backend)
- test_deduplication.py using Hypothesis
- Invariants: duplicates removed, deterministic output

#### Suite 6: API Payload (Backend)
- test_api_payload.py using Hypothesis
- Invariants: required fields, boundaries, error responses

#### Suite 7: JSON Round-Trip (Frontend + Backend)
- test_json_roundtrip.test.ts using fast-check
- Invariants: serialization inverse, Unicode preserved

#### Suite 8: Isolation (Backend)
- test_isolation.py using Hypothesis
- Invariants: no corruption, rollback success, logged operations

#### Suite 9: Patch Policy (Backend)
- test_patch_policy.py using Hypothesis
- Invariants: policy compliance, unrelated content preserved

### 4.3 Test Execution

- Local: Run all PBT suites before commit
- CI/CD: GitHub Actions with reproducible seeds
- Failure Reporting: Include seed, input, expected vs. actual
- Coverage: 80%+ including all PBT suites

## 5. Security Design

### 5.1 URL Validation

- Allowlist: http/https only, external IPs
- Blocklist: localhost, 127.x, 10.x, 172.16-31.x, 192.168.x, 0.0.0.0, ::1
- Redirects: Follow up to 5 hops; detect loops
- Validation: Client-side and server-side

### 5.2 Content Filtering

- Patch Content: Scan for unsafe patterns
- Rejection: Unsafe patches rejected with reason
- Logging: All rejections logged

### 5.3 API Security

- Authentication: JWT tokens
- CORS: Single domain (configurable)
- Rate Limiting: 10 requests/minute per user
- Input Validation: All parameters validated

### 5.4 Data Security

- Encryption: TLS 1.2+; AES-256 at rest
- Bedrock: IAM role with least-privilege
- Secrets: AWS Secrets Manager

## 6. Error Handling

### 6.1 Scan Failures
- Timeout: Retry 2x with exponential backoff
- Invalid HTML: Log and skip
- Crash: Rollback and notify

### 6.2 Bedrock Failures
- Timeout: Fallback explanation
- Quota: Queue and retry
- Invalid: Log and fallback

### 6.3 Database Failures
- Write timeout: Retry max 3x
- Read timeout: Return cached if available
- Corruption: Auto-cleanup after TTL

### 6.4 Patch Application Failures
- Selector mismatch: Log; mark failed
- Write conflict: Rollback and notify
- Verification failure: Mark unverified; manual review

## 7. Frontend Architecture

### 7.1 State Management
- React Context API for global state
- Local state for forms
- No external state library (MVP simple)

### 7.2 Component Structure
- ScanForm: URL input, submission
- FindingsList: Display with explanations
- RepairReview: Display and approve
- ReportDisplay: Before/after metrics
- ProgressIndicator: Status tracking

### 7.3 Accessibility
- Semantic HTML, ARIA labels
- Keyboard navigation
- Screen reader support
- WCAG 2.1 Level AA

## 8. Backend Architecture

### 8.1 Project Structure
- FastAPI routers: /scan, /repair, /patch, /verification
- Dependency injection for DB and services
- Async handlers for long operations
- Background workers (APScheduler)

### 8.2 Integration Points
- axe-core: Playwright integration
- Bedrock: Boto3 with exponential backoff
- DynamoDB: Boto3 with connection pooling
- S3: Boto3 for report uploads

### 8.3 Testing
- Unit tests for endpoints and services
- Fixtures for mock DynamoDB, Bedrock, S3
- PBT suites for critical logic
- Integration tests for workflows

## 9. Deployment

### 9.1 Infrastructure
- Frontend: S3 + CloudFront
- Backend: Lambda + API Gateway
- Database: DynamoDB (on-demand)
- Scanning: Lambda with ECR containers
- Monitoring: CloudWatch

### 9.2 CI/CD Pipeline
- Trigger: Commits to main
- Build: Docker images, React build
- Test: Unit, integration, PBT, E2E
- Deploy: CloudFormation/SAM

### 9.3 Configuration
- Environment variables for API keys, URLs, timeouts
- Separate configs for dev/test/prod
- Secrets in AWS Secrets Manager

## 10. Performance Optimization

### 10.1 Caching
- Bedrock explanations: 24-hour TTL
- Scan results: DynamoDB
- Frontend: Browser local storage

### 10.2 Async Operations
- Scan and patch: async; user gets immediate response
- Background jobs update DynamoDB
- Frontend polls for status

### 10.3 Resource Limits
- Scan timeout: 30s
- Playwright memory: 512MB
- Repair timeout: 20s per repair
- API response: 500ms non-scan
- DynamoDB: on-demand

## 11. Future Enhancements
- Bulk scanning
- Custom violation rulesets
- Advanced reporting
- Third-party integrations
- WebSocket for real-time updates
- Webhook support
