# AccessLens E2E Test Scenarios

This document describes the end-to-end test scenarios and their objectives.

## Overview

The E2E test suite covers the complete AccessLens workflow from URL submission through report generation. Tests are organized by scenario type and validate both happy-path and error-path behavior.

## Test Structure

```
backend/tests/e2e/
├── __init__.py                    # E2E test module initialization
├── conftest.py                    # Shared fixtures and AWS mocking setup
├── test_complete_workflow.py      # Full workflow E2E tests
├── test_realistic_violations.py   # Tests with realistic WCAG violations
└── TEST_SCENARIOS.md              # This file
```

## Workflow Steps Tested

### 1. URL Submission & Scan Initiation
**Endpoint:** `POST /api/scan`
**Purpose:** User submits a website URL for accessibility scanning

**Test Scenarios:**
- ✅ Valid URL submission returns `202 Accepted` with scan_id
- ❌ Invalid URLs (malformed, missing protocol) return `400/422`
- ❌ SSRF prevention: private network URLs rejected (localhost, 192.168.x.x, AWS metadata endpoint)
- ✅ Multiple concurrent scans maintain isolation

**Test Class:** `TestE2ECompleteWorkflow.test_e2e_workflow_*`

### 2. Website Scanning (Playwright)
**Internal:** Playwright browser automation scans website for accessibility issues

**Validates:**
- Detection of missing alt text on images
- Identification of low contrast text
- Finding of missing form labels
- Detection of heading hierarchy issues
- Identification of missing page titles
- Finding of missing video captions

**Test Class:** `TestE2ERealisticViolations`

### 3. Finding Detection & Categorization
**Purpose:** Categorize and prioritize accessibility violations

**Test Scenarios:**
- ✅ Findings categorized by WCAG criteria (1.1.1, 1.4.3, 2.4.2, etc.)
- ✅ Findings include severity levels (high, medium, low)
- ✅ Findings provide detailed context (element, impact, affected users)
- ✅ False positives minimized (decorative images with role="presentation" not flagged)

**Test Class:** `TestE2ERealisticViolations.TestE2EViolationDetectionAccuracy`

### 4. Repair Generation (Bedrock AI)
**Endpoint:** `POST /api/repair/generate`
**Purpose:** Generate AI-powered accessibility repairs for findings

**Test Scenarios:**
- ✅ Repairs generated for typical violations (alt text, contrast, labels)
- ✅ Repairs include confidence scores (0.0-1.0)
- ✅ Multiple repairs can be generated in batch
- ✅ Repairs maintain code functionality (don't break existing code)
- ✅ Repairs follow accessibility best practices
- ✅ Each repair includes clear explanation of why change was made
- ❌ Empty finding list rejected (422)
- ❌ Non-existent findings handled gracefully

**Test Class:** `TestE2ECompleteWorkflow` + `TestE2ERealisticViolations`

### 5. Repair Review & Approval
**Endpoint:** `POST /api/repair/approve`
**Purpose:** User reviews and approves proposed repairs

**Test Scenarios:**
- ✅ Repairs moved to "approved" state when approved
- ✅ User can select subset of repairs (partial approval)
- ✅ Approved repairs logged for audit trail
- ❌ Attempting to approve already-approved repair handled gracefully
- ❌ Non-existent repair_ids handled gracefully

**Test Class:** `TestE2ECompleteWorkflow`

### 6. Patch Application
**Endpoint:** `POST /api/patch/apply`
**Purpose:** Apply approved repairs to website code

**Test Scenarios:**
- ✅ Patch application queued with `202 Accepted`
- ✅ Application status tracked (in_progress → completed/failed)
- ✅ Concurrent patch applications handled (no race conditions)
- ✅ Failed patches reported with error details
- ❌ Application with invalid scan_id handled gracefully
- ❌ Non-existent repairs handled gracefully

**Test Class:** `TestE2ECompleteWorkflow.TestE2EErrorScenarios`

### 7. Verification (Re-scan & Comparison)
**Endpoint:** `GET /api/verification/{scan_id}`
**Purpose:** Re-scan website after repairs and compare results

**Test Scenarios:**
- ✅ Post-repair scan shows reduced violation count
- ✅ Specific violations marked as "resolved"
- ✅ Before/after violation counts compared
- ✅ New violations detected (if repairs introduced issues)
- ✅ Verification results cached for performance

**Test Class:** `TestE2ECompleteWorkflow`

### 8. Report Generation & Download
**Endpoint:** `GET /api/report/{scan_id}`
**Purpose:** Generate accessibility report in multiple formats

**Formats Supported:**
- JSON: Machine-readable, includes all metadata
- CSV: Spreadsheet format for analysis
- PDF: Print-friendly, downloadable report

**Test Scenarios:**
- ✅ Report generated successfully after repairs applied
- ✅ JSON format returns complete violation data
- ✅ CSV format suitable for spreadsheet import
- ✅ PDF format includes visual styling and branding
- ✅ Report includes before/after metrics
- ✅ Invalid format parameter rejected (400/422)
- ✅ Report generation for non-existent scan returns 404
- ✅ Report generation responds within 1 second (response time SLA)

**Test Class:** `TestE2ECompleteWorkflow.TestE2EReportGeneration`

## Test Categories

### Happy Path Tests
Tests the ideal scenario where everything works correctly:
- Valid inputs accepted
- Scans complete successfully
- Repairs generated with high confidence
- Patches applied without errors
- Reports generated in requested format

**Entry Point:** `TestE2ECompleteWorkflow.test_e2e_workflow_success_happy_path()`

### Error Scenario Tests
Tests error handling and edge cases:
- Invalid URLs and SSRF prevention
- Network timeouts and service unavailability
- Missing or malformed data
- Non-existent resources
- Concurrent modifications
- Rate limiting

**Test Class:** `TestE2ECompleteWorkflow.TestE2EErrorScenarios`

### Data Persistence Tests
Validates that data survives across workflow steps:
- Scan metadata persisted after submission
- Findings associated with correct scan
- Repairs linked to findings
- Patches tracked to scan
- Reports retrievable after completion

**Test Class:** `TestE2ECompleteWorkflow.TestE2EDataPersistence`

### Realistic Violation Tests
Tests with actual WCAG violations and repairs:
- Images without alt text
- Form inputs without labels
- Low contrast text
- Missing page titles
- Improper heading hierarchy
- Links without clear purpose
- Buttons without accessible names
- Videos without captions
- Color-only information conveyance
- Improper ARIA usage

**Test Class:** `TestE2ERealisticViolations`

### Performance Tests
Validates API performance and response times:
- Scan submission responds in < 2 seconds
- Report retrieval responds in < 1 second
- Handling of many findings (50+) without degradation
- Concurrent requests handled efficiently

**Test Class:** `TestE2ECompleteWorkflow.TestE2EPerformance`

## Running the E2E Tests

### Prerequisites
```bash
# Install test dependencies
pip install -r requirements.txt
pip install moto[dynamodb,s3,bedrock]  # For AWS mocking
```

### Run All E2E Tests
```bash
# Run all E2E tests
pytest backend/tests/e2e/ -v

# Run with coverage report
pytest backend/tests/e2e/ --cov=app --cov-report=html

# Run specific test class
pytest backend/tests/e2e/test_complete_workflow.py::TestE2ECompleteWorkflow -v
```

### Run Specific Scenarios
```bash
# Run happy path only
pytest backend/tests/e2e/test_complete_workflow.py::TestE2ECompleteWorkflow::test_e2e_workflow_success_happy_path -v

# Run error scenarios
pytest backend/tests/e2e/test_complete_workflow.py::TestE2EErrorScenarios -v

# Run realistic violations
pytest backend/tests/e2e/test_realistic_violations.py -v
```

### Run with Markers
```bash
# Run only slow tests
pytest backend/tests/e2e/ -v -m slow

# Run only fast tests (excludes API calls)
pytest backend/tests/e2e/ -v -m fast
```

## AWS Mocking Setup

The test suite uses **moto** for AWS service mocking. No real AWS credentials needed.

### Mocked Services
- **DynamoDB**: Scan metadata, findings, repairs stored here
- **S3**: Reports cached and exported from S3
- **Bedrock**: AI model invocations mocked to return realistic repairs

### Mock Configuration
See `conftest.py` for:
- `mock_aws_services` fixture: Configures moto mocks
- `mock_playwright_scanner` fixture: Mocks browser scanning
- `mock_bedrock_repair_generator` fixture: Mocks AI repairs

## Test Data

### Sample Data Fixtures
Located in `conftest.py`:

**`sample_scan_data`**: Basic scan submission data
```python
{
    "scan_id": "scan-e2e-001",
    "user_id": "user-e2e-001",
    "url": "https://example.com",
    "status": "completed"
}
```

**`sample_findings_data`**: Realistic accessibility findings
```python
{
    "finding_id": "finding-1",
    "type": "missing_alt_text",
    "severity": "high",
    "wcag_criteria": "1.1.1"
}
```

**`sample_repair_data`**: AI-generated repairs
```python
{
    "repair_id": "repair-1",
    "description": "Add descriptive alt text",
    "confidence": 0.95,
    "status": "pending_review"
}
```

### Realistic Violations
Located in `test_realistic_violations.py`:
- Images without alt text
- Form inputs without labels
- Low contrast text
- Missing page titles
- Improper heading hierarchy
- Links without clear purpose
- Buttons without accessible names
- Videos without captions
- Color-only information

## Expected Test Results

### All Tests Pass When:
- ✅ API endpoints respond with correct status codes
- ✅ Data persisted across workflow steps
- ✅ Repairs generated for all violation types
- ✅ Error scenarios handled gracefully
- ✅ Response times meet performance SLAs
- ✅ SSRF prevention working correctly
- ✅ Concurrent operations don't cause data corruption

### Common Test Failures & Debugging

**Timeout on Scan Submission**
- Check that backend is running
- Verify Playwright browsers are available
- Check network connectivity to test URL (if not mocked)

**AWS Service Not Found**
- Verify `moto` installed: `pip list | grep moto`
- Check AWS mocking fixtures in `conftest.py`
- Ensure `@mock_*` decorators applied to test functions

**False Positive on SSRF Test**
- Check SSRF validation logic in `app.services.validators.py`
- Verify private IP ranges in allowlist are correct

**Report Generation Timeout**
- Check PDF generation (slow operation)
- Verify S3 mock is configured correctly
- Consider disabling PDF tests if S3 unavailable

## Continuous Integration

### GitHub Actions Workflow
See `.github/workflows/e2e-tests.yml`:

```yaml
- name: Run E2E Tests
  run: |
    pytest backend/tests/e2e/ -v --cov=app --junitxml=test-results.xml
```

### CI Constraints
- Tests should complete in < 5 minutes
- No external network calls (all mocked)
- No real AWS credentials in CI environment
- Results saved to JUnit XML for reporting

## Next Steps: Browser E2E Tests

Future phase can add full browser-based E2E tests:
- Use **Playwright** or **Cypress** for browser automation
- Test complete React UI → Backend workflow
- Validate user interactions (form submission, repair approval, report download)
- Include visual regression testing

**Estimated effort:** 8-12 hours for comprehensive browser E2E suite

## References

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Playwright Documentation](https://playwright.dev/)
- [Moto AWS Mocking](https://docs.getmoto.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-databases/)
