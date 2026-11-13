# Implementation Plan: CI Infrastructure Fix

## Overview

This plan restores the CI infrastructure for end-to-end testing by implementing boto3 mocking fixtures, restoring conftest.py, and ensuring all 28 E2E tests pass in both local and GitHub Actions environments. The implementation follows a critical path approach: establish mocking infrastructure first, then test data fixtures, then verify all tests pass.

**Key Implementation Sequence:**
1. Create e2e/conftest.py with moto-based AWS mocking
2. Implement client fixture (FastAPI TestClient with mocked AWS)
3. Implement test data fixtures (sample_scan_data, sample_findings, sample_repairs)
4. Create TESTING.md documentation
5. Verify all 28 tests pass locally
6. Verify all 28 tests pass in GitHub Actions CI

**No Production Changes:** This spec is infrastructure-only. No application code is modified.

---

## Tasks

### Phase 1: AWS Mocking Infrastructure

- [x] 1. Create backend/tests/e2e/conftest.py with moto setup
  - Copy existing fixture patterns from backend/tests/conftest.py
  - Add sys.path configuration for importing app.main
  - Add comment block explaining boto3 mocking strategy before imports
  - Register pytest_asyncio plugin with pytest_plugins
  - _Requirements: 1.1, 2.1, 7.1, 8.1_

- [x] 2. Implement mock_boto3 fixture with @mock_aws decorator
  - Create fixture with @pytest.fixture and @mock_aws decorators
  - Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SECURITY_TOKEN env vars to "testing"
  - Set AWS_DEFAULT_REGION to "us-east-1"
  - Add docstring explaining boto3 mocking happens before app import
  - Add inline comments explaining why mocking must occur before app initialization
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 7.2, 8.2_

- [ ] 3. Implement client fixture with moto mocking context
  - Create fixture with @pytest.fixture(scope="function") decorator
  - Apply @mock_aws decorator to ensure moto patches boto3 before app import
  - Import create_app from app.main INSIDE the moto context (after decorator applies)
  - Create FastAPI TestClient wrapping the app instance
  - Add docstring explaining fixture purpose and mocking strategy
  - Add 3-line comment block explaining why app import happens inside @mock_aws context
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 7.2_

- [ ]* 3.1 Write property test for client fixture mocking
  - **Property 1: Boto3 Isolation**
  - **Validates: Requirements 4.3, 4.4**
  - Test that boto3.client() calls within app initialization return moto mock objects
  - Verify boto3 does NOT attempt real AWS credential lookup

- [ ] 4. Implement mock_aws_services fixture
  - Create fixture with @pytest.fixture(scope="function") decorator and mock_boto3 dependency
  - Return dict with keys: 'dynamodb', 's3', 'bedrock'
  - For 'dynamodb': Create moto mock client for DynamoDB service
  - For 's3': Create moto mock resource for S3 service
  - For 'bedrock': Create moto mock client for Bedrock service
  - Add docstring explaining fixture returns service references for test assertions
  - Add inline comment explaining error handling for each service
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 7.2_

- [ ]* 4.1 Write unit test for mock_aws_services fixture
  - Test that all three services ('dynamodb', 's3', 'bedrock') are present in returned dict
  - Test that each service is a valid moto mock object (has expected methods)
  - Verify no real AWS calls occur when services are accessed

---

### Phase 2: Test Data Fixtures

- [ ] 5. Implement sample_scan_data fixture
  - Create fixture with @pytest.fixture(scope="function") decorator
  - Return dict with fields: scan_id, user_id, url, status, timestamp
  - Use uuid.uuid4() for scan_id (realistic format)
  - Use realistic values: user_id="test-user-001", url="https://example.com"
  - Set status to one of: ["pending", "completed", "failed"]
  - Use datetime.utcnow().isoformat() for timestamp (ISO 8601 format)
  - Add docstring explaining sample data purpose
  - Ensure new dict instance returned each call (no mutation issues)
  - _Requirements: 5.1_

- [ ]* 5.1 Write unit test for sample_scan_data fixture
  - Verify all required fields present (scan_id, user_id, url, status, timestamp)
  - Verify scan_id has UUID format
  - Verify status is valid value from ["pending", "completed", "failed"]
  - Verify timestamp is ISO 8601 format

- [ ] 6. Implement sample_findings_data fixture
  - Create fixture with @pytest.fixture(scope="function") decorator
  - Return list of 3-10 finding dicts (realistic count)
  - Each finding dict contains: finding_id, wcag_rule_id, severity, description, affected_element
  - finding_id: UUID format string
  - wcag_rule_id: One of ["1.1.1", "1.4.3", "2.1.1", "2.4.3", "3.2.1", "4.1.2"]
  - severity: One of ["critical", "major", "minor"]
  - description: Non-empty string, 10-100 characters
  - affected_element: CSS selector or HTML identifier string
  - Add docstring explaining sample findings structure
  - Ensure new list instance returned each call
  - _Requirements: 5.2_

- [ ]* 6.1 Write unit test for sample_findings_data fixture
  - Verify list has 3-10 items
  - Verify each finding has all required fields
  - Verify wcag_rule_id values are valid
  - Verify severity values are valid
  - Verify descriptions are 10-100 characters

- [ ] 7. Implement sample_repair_data fixture
  - Create fixture with @pytest.fixture(scope="function") decorator
  - Return list of 2-8 repair proposal dicts (realistic count)
  - Each repair dict contains: repair_id, finding_id, suggested_fix, confidence_score, status
  - repair_id: UUID format string
  - finding_id: UUID format string
  - suggested_fix: Non-empty string, 10-200 characters
  - confidence_score: Float between 0.0 and 1.0 (inclusive)
  - status: One of ["proposed", "accepted", "rejected", "applied"]
  - Add docstring explaining repair fixture purpose
  - Ensure new list instance returned each call
  - _Requirements: 5.3_

- [ ]* 7.1 Write unit test for sample_repair_data fixture
  - Verify list has 2-8 items
  - Verify each repair has all required fields
  - Verify confidence_score is float between 0.0-1.0
  - Verify status values are valid

---

### Phase 3: Auto-Use and Integration Fixtures

- [ ] 8. Implement mock_dynamodb_tables auto-use fixture
  - Create fixture with @pytest.fixture(autouse=True, scope="function") decorator
  - Ensure DynamoDB tables are mocked for all tests automatically
  - Create mock tables that tests expect (table names from app/core/config.py or design)
  - Set up proper table schemas (HASH keys, RANGE keys as needed)
  - Add docstring explaining auto-use behavior
  - Add inline comment explaining why autouse=True (prevents accidental real AWS calls)
  - _Requirements: 1.2, 1.3, 1.4_

- [ ]* 8.1 Write unit test for mock_dynamodb_tables fixture
  - Verify tables are created in moto mock (not real DynamoDB)
  - Test table operations (put_item, get_item, scan) return moto responses
  - Verify error handling for invalid table operations

- [ ] 9. Add top-level comment block to conftest.py
  - Add comment block BEFORE imports explaining:
    - Why boto3 mocking must happen before app import
    - What happens if mocking is not applied (boto3 tries real credentials)
    - How mocking works (moto patches sys.modules['boto3'] before app.main import)
    - Reference to TESTING.md for detailed documentation
  - Ensure comments are clear and maintainable
  - _Requirements: 7.1, 7.2_

---

### Phase 4: Documentation

- [x] 10. Create backend/tests/TESTING.md documentation file
  - Create file at absolute path: backend/tests/TESTING.md
  - Include sections:
    - **Overview**: One paragraph explaining e2e test purpose and scope
    - **Quick Start**: How to run tests locally (command: `pytest backend/tests/e2e/ -v`)
    - **Test Structure**: Description of fixture architecture and mocking strategy
    - **Running Tests**:
      - Local execution: `pytest backend/tests/e2e/ -v`
      - With coverage: `pytest backend/tests/e2e/ --cov=app --cov-report=term-missing`
      - Single test: `pytest backend/tests/e2e/test_complete_workflow.py::TestE2ECompleteWorkflow::test_e2e_workflow_success_happy_path -v`
    - **Using Fixtures**: Example test showing how to use client, sample_scan_data, mock_aws_services
    - **Adding New Tests**: Step-by-step guide for writing new tests with provided fixtures
    - **Adding New AWS Service Mocks**: Instructions for extending mock_aws_services
    - **Troubleshooting**:
      - "boto3 import fails" → check conftest.py present and @mock_aws decorator applied
      - "Credential errors" → verify AWS_ env vars set in conftest.py
      - "DynamoDB table not found" → use mock_dynamodb_tables fixture
    - **CI/CD Integration**: How tests run in GitHub Actions, no secrets needed
  - Include 2-3 code examples showing fixture usage
  - _Requirements: 7.3, 7.4_

- [ ]* 10.1 Review TESTING.md for clarity and completeness
  - Verify all sections present and well-organized
  - Verify code examples are accurate and runnable
  - Verify troubleshooting covers common issues
  - Get feedback from team member (optional)

---

### Phase 5: Verification and Testing

- [x] 11. Checkpoint - Verify conftest.py syntax and imports
  - Run `python -m py_compile backend/tests/e2e/conftest.py` to verify no syntax errors
  - Verify file imports successfully: `python -c "import sys; sys.path.insert(0, 'backend/src'); from tests.e2e import conftest"`
  - Check that all fixtures are registered: `pytest backend/tests/e2e/conftest.py --fixtures | grep -E "client|mock_aws|sample_"`
  - Ensure all expected fixtures appear in output
  - Document any issues found and fixes applied
  - _Requirements: 1.5, 1.6_

- [x] 12. Run local E2E test suite - Verify all 28 tests pass
  - Execute: `cd backend && pytest tests/e2e/ -v --tb=short`
  - Verify exit code is 0 (success)
  - Verify exactly 28 tests executed
  - Verify 28 tests passed, 0 tests failed
  - Check test execution completes in < 60 seconds (moto mocks are fast)
  - Document test results
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ]* 12.1 Generate and review local test coverage report
  - Execute: `pytest backend/tests/e2e/ --cov=app --cov-report=term-missing`
  - Review coverage percentage for app modules
  - Identify any major gaps in test coverage
  - Document coverage results (informational, not blocking)

- [x] 13. Verify boto3 mocking is active - No credential errors locally
  - Run tests on machine without ~/.aws/credentials file configured
  - Or temporarily rename ~/.aws directory
  - Execute: `pytest backend/tests/e2e/ -v` 
  - Verify tests pass WITHOUT credential errors
  - Verify no "NoCredentialsError" messages in output
  - Confirm env vars prevent boto3 fallback to real credentials
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.6_

- [x] 14. Trigger GitHub Actions CI pipeline
  - Push branch with conftest.py and TESTING.md to GitHub
  - GitHub Actions e2e-tests.yml workflow should trigger automatically
  - Verify workflow runs on matrix: Python 3.10, 3.11
  - Wait for workflow to complete
  - Check all jobs pass (no failures)
  - _Requirements: 6.1, 6.5, 6.6, 6.7_

- [x] 15. Verify CI test results meet requirements
  - Confirm all 28 tests executed in CI
  - Confirm all 28 tests passed (0 failures)
  - Verify test exit code is 0
  - Verify test results include duration (in CI logs)
  - Check for conftest.py loading errors (should be none)
  - Download and review JUnit XML or pytest JSON artifact
  - _Requirements: 6.1, 6.4, 6.5, 6.6_

- [x] 16. Final verification - No AWS credential errors in CI
  - Review CI job logs for "NoCredentialsError" messages (should be none)
  - Verify CI uses dummy AWS_ACCESS_KEY_ID/SECRET values only
  - Confirm no real AWS secrets exposed in CI configuration
  - Confirm CI environment does not have ~/.aws/credentials file
  - Verify tests execute in < 2 minutes in CI (moto mocks perform well)
  - _Requirements: 8.5, 8.6_

---

### Phase 6: Final Checkpoint

- [x] 17. Final checkpoint - All requirements verified
  - Ensure all tests pass locally: `pytest backend/tests/e2e/ -v` → 28 pass, 0 fail
  - Ensure all tests pass in CI: GitHub Actions shows all green
  - Ensure conftest.py contains all fixtures: client, mock_boto3, mock_aws_services, sample_scan_data, sample_findings_data, sample_repair_data, mock_dynamodb_tables
  - Ensure conftest.py has documentation comments (top-level comment block + fixture docstrings)
  - Ensure TESTING.md exists with all required sections
  - Ensure no credential errors occur (locally or in CI)
  - Ask: "Are all requirements met? Any questions or concerns before declaring complete?"

---

## Notes

### Task Types and Ordering

**REQUIRED Tasks (Critical Path):**
- Tasks 1-9: Infrastructure setup (conftest.py and fixtures)
- Tasks 11-17: Verification and testing (proving everything works)
- All top-level tasks (without decimal) are REQUIRED

**OPTIONAL Tasks (Nice-to-Haves):**
- 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 10.1, 12.1
- These are marked with `*` suffix
- Can be skipped for faster MVP (though property tests catch more bugs)
- Should be included for production readiness

### File References

- **Backend root:** `backend/`
- **Spec directory:** `.kiro/specs/ci-infrastructure-fix/`
- **E2E conftest:** `backend/tests/e2e/conftest.py` (NEW FILE)
- **Testing docs:** `backend/tests/TESTING.md` (NEW FILE)
- **Test files:** `backend/tests/e2e/test_*.py` (28 tests total)
- **Parent conftest:** `backend/tests/conftest.py` (reference for patterns)
- **App main:** `backend/src/app/main.py` (imported by fixtures)

### Dependencies and Constraints

**Python Version:** 3.10+ (pytest-asyncio compatibility)

**Key Packages (from requirements.txt):**
- `pytest==7.4.3` - Test framework
- `pytest-asyncio==0.21.1` - Async test support
- `moto==4.2.10` - AWS service mocking
- `fastapi==0.104.1` - Application framework
- `boto3==1.29.7` - AWS SDK (mocked by moto)

**Environment Variables (set in conftest.py, not CI secrets):**
```
AWS_ACCESS_KEY_ID=testing
AWS_SECRET_ACCESS_KEY=testing
AWS_SECURITY_TOKEN=testing
AWS_DEFAULT_REGION=us-east-1
```

These are NOT secrets. They're dummy values required by boto3 initialization.

### Testing Strategy

**All 28 E2E Tests:**
- Located in `backend/tests/e2e/test_*.py` (3 files)
- Require: client fixture, mock_aws_services, sample data fixtures
- Should pass in < 60 seconds total (local) and < 2 minutes (CI)
- Verify complete workflows from scan submission to report generation

**Test Organization:**
- `test_complete_workflow.py` - Full workflow scenarios (happy path, error cases)
- `test_simple_workflows.py` - Individual endpoint tests
- `test_realistic_violations.py` - Complex accessibility violation scenarios

### Verification Checkpoints

**Pre-Implementation:**
- ✓ Spec requirements reviewed
- ✓ Design document reviewed
- ✓ Existing fixtures in `backend/tests/conftest.py` reviewed

**During Implementation:**
- Checkpoint at task 11: conftest.py syntax and fixture registration
- Checkpoint at task 12: 28 tests pass locally
- Checkpoint at task 15: 28 tests pass in GitHub Actions CI
- Checkpoint at task 17: All requirements verified

**Post-Implementation:**
- Document any deviations from design
- Update this plan if issues found
- Archive CI logs for reference

### References to Requirements

Each task references specific requirements it addresses. Mapping:
- Requirement 1: Task 1, 11
- Requirement 2: Tasks 2, 3
- Requirement 3: Task 4
- Requirement 4: Tasks 3, 9
- Requirement 5: Tasks 5, 6, 7
- Requirement 6: Tasks 12, 14, 15, 16
- Requirement 7: Tasks 2, 9, 10
- Requirement 8: Tasks 2, 13, 16

All 8 requirements have implementation coverage across the 17 tasks.

---

## Task Dependency Graph

```json
{
  "waves": [
    {
      "id": 0,
      "tasks": ["1", "2"]
    },
    {
      "id": 1,
      "tasks": ["3", "4"]
    },
    {
      "id": 2,
      "tasks": ["5", "6", "7"]
    },
    {
      "id": 3,
      "tasks": ["8", "9"]
    },
    {
      "id": 4,
      "tasks": ["10"]
    },
    {
      "id": 5,
      "tasks": ["11"]
    },
    {
      "id": 6,
      "tasks": ["12"]
    },
    {
      "id": 7,
      "tasks": ["13"]
    },
    {
      "id": 8,
      "tasks": ["14"]
    },
    {
      "id": 9,
      "tasks": ["15", "16"]
    },
    {
      "id": 10,
      "tasks": ["17"]
    }
  ]
}
```

### Wave Explanation

- **Wave 0:** Core AWS mocking setup (mock_boto3 and client fixtures)
- **Wave 1:** Integration of fixtures (mock_aws_services, @mock_aws context)
- **Wave 2:** Test data fixtures (sample_scan_data, findings, repairs)
- **Wave 3:** Auto-use fixtures and documentation setup
- **Wave 4:** Documentation creation (TESTING.md)
- **Wave 5:** Syntax and import verification checkpoint
- **Wave 6:** Local testing verification
- **Wave 7:** Local credential error verification
- **Wave 8:** CI pipeline trigger
- **Wave 9:** CI results verification
- **Wave 10:** Final checkpoint and sign-off

**Wave Sequencing Rationale:**
- Waves 0-3 establish infrastructure (no dependencies on each other within each wave, but later waves depend on earlier ones)
- Wave 4 documents the infrastructure
- Wave 5 verifies syntax before testing
- Waves 6-9 perform testing verification (sequential, each depends on previous)
- Wave 10 is final verification

This sequential ordering ensures the critical path (infrastructure → documentation → verification) completes before declaring success.

---

## Workflow Completion

This specification is complete when:

1. ✓ All REQUIRED tasks (1-9, 11-17) are implemented
2. ✓ All 28 E2E tests pass locally
3. ✓ All 28 E2E tests pass in GitHub Actions CI
4. ✓ No credential errors occur in any environment
5. ✓ conftest.py contains inline documentation
6. ✓ TESTING.md is clear and complete
7. ✓ Team has confirmed all requirements are met

Once tasks.md is created, implementation can begin by:
1. Opening this tasks.md file
2. Clicking "Start task" next to task items
3. Following task instructions sequentially
4. Verifying checkpoints before proceeding to next phase

**This workflow is infrastructure-only and does NOT modify application code.**

