# Requirements Document

## Introduction

The conftest.py file in `backend/tests/e2e/` was accidentally deleted, causing the GitHub Actions CI pipeline to fail with 28 test errors. The root cause is that boto3 mocking setup is not applied before the Flask application is imported in test modules, resulting in real AWS credential lookups during tests.

This specification defines requirements to restore and properly document the test infrastructure, ensuring boto3 mocking happens before app import, and guaranteeing the CI/CD pipeline passes reliably.

## Glossary

- **E2E_Tests**: End-to-End tests in `backend/tests/e2e/` that validate complete workflows
- **conftest.py**: Pytest configuration file that defines shared fixtures and setup logic
- **boto3**: AWS SDK for Python
- **Mocking**: Replacing real AWS service calls with fake implementations
- **CI_Pipeline**: GitHub Actions workflow that runs automated tests
- **App_Import**: The line that imports the FastAPI application (e.g., `from app.main import app`)
- **Fixture**: A pytest function that provides test data or setup/teardown logic
- **Monkeypatch**: Pytest mechanism to replace functions/modules with mocks at test time

## Requirements

### Requirement 1: Restore conftest.py in E2E Test Directory

**User Story:** As a CI/CD operator, I want the conftest.py file restored to the e2e test directory, so that pytest can discover and apply shared fixtures and setup.

#### Acceptance Criteria

1. THE conftest.py file SHALL exist at the absolute path `backend/tests/e2e/conftest.py`
2. WHEN pytest discovers e2e tests, THE conftest.py file SHALL be loaded before any test module execution
3. WHEN pytest loads conftest.py, ALL fixtures defined in conftest.py (mock_boto3, client, sample_scan_data, sample_findings_data, sample_repair_data) SHALL be registered and available to test modules
4. THE conftest.py file SHALL contain fixture definitions that follow the pytest fixture protocol (functions decorated with @pytest.fixture)
5. WHEN `git status` is run, THE conftest.py file SHALL appear in the tracked files (not in .gitignore, not untracked)
6. WHEN `git diff HEAD` is run after conftest.py is restored, THE file content SHALL be verifiable as restored (not corrupted)

---

### Requirement 2: Mock boto3 Before App Import

**User Story:** As a test infrastructure maintainer, I want boto3 to be mocked before the app is imported, so that tests never attempt to access real AWS credentials or services.

#### Acceptance Criteria

1. WHEN the test session starts (before any test module executes), boto3 mocking SHALL be applied via the mock_boto3 fixture
2. THE mock_boto3 fixture SHALL initialize boto3 mocks using the moto library (@mock_aws decorator or context manager)
3. WHEN the mock_boto3 fixture is applied, THE sys.modules dictionary SHALL be cleared of boto3-related imports to force fresh imports with mocking active
4. THE mock_boto3 fixture SHALL verify that boto3 module reloading succeeds (using importlib.reload) before proceeding
5. WHEN a test module imports the application (app.main), boto3 SHALL already be mocked (verified by checking mock state)
6. IF boto3 import fails or mocking fails to initialize, THE fixture SHALL raise a pytest error with a descriptive message identifying the failure point
7. WHEN mocking is active, ALL calls to boto3.client() and boto3.resource() within the application SHALL return mock objects (not real AWS clients)
8. WHEN the test completes, boto3 mocking SHALL remain active for all subsequent tests in the session (session-scoped fixture behavior)

---

### Requirement 3: Provide Mocked AWS Service Fixtures

**User Story:** As a test writer, I want pre-configured mock fixtures for AWS services, so that I can write tests without managing mock setup.

#### Acceptance Criteria

1. THE conftest.py file SHALL provide a `mock_aws_services` fixture (function-scoped, depends on mock_boto3)
2. WHEN a test requests the `mock_aws_services` fixture, THE fixture SHALL return a dict with keys: 'dynamodb', 's3', 'bedrock'
3. THE 'dynamodb' value SHALL be a moto mock client with the following error handling:
   - WHEN mock_dynamodb.get_item() is called with a valid params dict (TableName, Key), THE mock SHALL return {'Item': {...}} or {'Item': None} if key not found
   - WHEN mock_dynamodb.scan() is called, THE mock SHALL return {'Items': [], 'Count': 0} for empty table or {'Items': [...], 'Count': N} for populated table
   - IF mock_dynamodb.get_item() receives invalid params, THE mock SHALL raise botocore.exceptions.ParamValidationError
4. THE 's3' value SHALL be a moto mock resource with the following error handling:
   - WHEN mock_s3.put_object() is called with valid params (Bucket, Key, Body), THE mock SHALL return {'ResponseMetadata': {'HTTPStatusCode': 200}}
   - WHEN mock_s3.get_object() is called with valid params (Bucket, Key), THE mock SHALL return {'Body': <StreamingBody>, 'ResponseMetadata': {...}}
   - WHEN mock_s3.get_object() is called with non-existent Bucket, THE mock SHALL raise botocore.exceptions.NoSuchBucket
   - WHEN mock_s3.get_object() is called with non-existent Key, THE mock SHALL raise botocore.exceptions.NoSuchKey
5. THE 'bedrock' value SHALL be a moto mock client with the following behavior:
   - WHEN mock_bedrock.invoke_model() is called, THE mock SHALL return {'body': <mock response body>} without accessing real Bedrock
   - IF an error occurs during bedrock mock initialization, THE fixture SHALL catch it and raise a descriptive error
6. ALL mock responses SHALL use realistic AWS response structures (not simplified stubs)

---

### Requirement 4: Provide Test Client Fixture

**User Story:** As a test writer, I want a FastAPI test client that connects to a mocked app with mocked AWS services, so that I can test endpoints without real AWS calls.

#### Acceptance Criteria

1. THE conftest.py file SHALL provide a `client` fixture (function-scoped, depends on mock_boto3 fixture)
2. THE client fixture SHALL be implemented as a pytest fixture that:
   a. Imports sys and inspects sys.modules to verify boto3 is already mocked (mock_boto3 dependency ensures this)
   b. Imports the FastAPI application from app.main AFTER mocking is verified active
   c. Returns a TestClient instance from fastapi.testclient
3. WHEN the client fixture executes, sys.modules['boto3'] SHALL already be patched by moto before app.main import
4. WHEN a test uses the client to make HTTP requests (e.g., `client.get('/endpoint')`), boto3 calls inside request handlers SHALL use moto mocks
5. THE client fixture SHALL set environment variables BEFORE app import:
   - AWS_ACCESS_KEY_ID=testing
   - AWS_SECRET_ACCESS_KEY=testing
   - AWS_SECURITY_TOKEN=testing
6. IF the application fails to import after mocking is applied, THE fixture SHALL raise a descriptive pytest error with the import traceback
7. WHEN tests complete, THE TestClient SHALL be cleaned up (no connection leaks)

---

### Requirement 5: Provide Sample Data Fixtures

**User Story:** As a test writer, I want pre-defined sample data for common test objects, so that I can write tests consistently without creating test data.

#### Acceptance Criteria

1. THE conftest.py file SHALL provide a `sample_scan_data` fixture that returns a dict with the following fields:
   - scan_id: string (UUID format, e.g., "550e8400-e29b-41d4-a716-446655440000")
   - user_id: string (e.g., "user_123")
   - url: string (valid URL, e.g., "https://example.com/page")
   - status: string (value in ["pending", "completed", "failed"])
   - timestamp: string (ISO 8601 format, e.g., "2024-01-15T10:30:00Z")
2. THE conftest.py file SHALL provide a `sample_findings_data` fixture that returns a list (minimum length 3, maximum 10 for realistic test data) of findings dicts, each containing:
   - finding_id: string (UUID format)
   - wcag_rule_id: string (value from set: ["1.1.1", "1.4.3", "2.1.1", "2.4.3", "3.2.1", "4.1.2"])
   - severity: string (value in ["critical", "major", "minor"])
   - description: string (non-empty, 10-100 characters)
   - affected_element: string (CSS selector or HTML identifier)
3. THE conftest.py file SHALL provide a `sample_repair_data` fixture that returns a list (minimum length 2, maximum 8) of repair proposal dicts, each containing:
   - repair_id: string (UUID format)
   - finding_id: string (UUID format, matching a finding_id in sample_findings_data)
   - suggested_fix: string (non-empty, 10-200 characters)
   - confidence_score: float (value between 0.0 and 1.0, inclusive)
   - status: string (value in ["proposed", "accepted", "rejected", "applied"])
4. EACH sample fixture SHALL return new instances on each call (not singletons that could be mutated)
5. ALL sample data values SHALL be realistic and match the application's domain model requirements

---

### Requirement 6: All E2E Tests Pass in GitHub Actions

**User Story:** As a developer, I want all 28 E2E tests to pass in the GitHub Actions CI pipeline, so that I can be confident the code is production-ready.

#### Acceptance Criteria

1. WHEN the GitHub Actions CI pipeline runs the e2e test suite, ALL 28 tests in `backend/tests/e2e/` SHALL pass (zero test failures)
2. THE test environment MUST use Python 3.8 or later (Python version requirement for moto and boto3 compatibility)
3. WHEN pytest executes, THE exit code SHALL be 0 (success, no errors)
4. WHEN a test fails, THE pytest output SHALL clearly indicate the failure reason (e.g., assertion failure, fixture error, or boto3 error) - NOT a conftest.py loading failure
5. WHEN the CI pipeline completes, THE job artifact SHALL include a test results report with:
   - Total test count: 28
   - Passed count: 28
   - Failed count: 0
   - Test duration (in seconds)
6. THE artifact format SHALL be parseable (e.g., JUnit XML or pytest JSON format)
7. IF pytest fails to load conftest.py, THE CI job SHALL fail with error output containing "conftest.py" and a clear error message (not silently skip)

---

### Requirement 7: Document Test Infrastructure Setup

**User Story:** As a new team member, I want clear documentation of how the test infrastructure works, so that I can understand and maintain the tests.

#### Acceptance Criteria

1. THE conftest.py file SHALL contain inline comments following this format:
   - Each fixture definition SHALL have a docstring explaining its purpose (one sentence minimum)
   - Each fixture's first 3 lines SHALL include a comment block explaining what it does and why
   - Comments SHALL explain the mocking strategy (e.g., "Uses moto to mock DynamoDB without real AWS access")
2. THE conftest.py file SHALL contain a comment block at the top (before imports) explaining:
   - Why boto3 mocking must happen before app import (to prevent real credential lookups)
   - What happens if mocking is not applied (e.g., "boto3 will attempt to load credentials from ~/.aws/credentials or environment variables")
   - How the mocking works (e.g., "moto patches sys.modules['boto3'] before app.main is imported")
3. WITHIN the e2e test directory (`backend/tests/e2e/`), A file named TESTING.md OR README.md SHALL exist with sections:
   - **Overview**: One paragraph explaining the e2e test purpose and scope
   - **Running Tests Locally**: Step-by-step instructions (e.g., "1. cd backend 2. pytest tests/e2e/ -v")
   - **Adding New Tests**: Guide to using provided fixtures (sample_scan_data, client, mock_aws_services)
   - **Adding New AWS Service Mocks**: Instructions (e.g., "1. Import the service in mock_boto3 fixture 2. Add to mock_aws_services dict 3. Update this README")
   - **Troubleshooting**: Common issues and solutions (e.g., "If boto3 import fails, check conftest.py is present")
4. THE documentation SHALL include code examples showing how to use fixtures (e.g., a sample test using `client` fixture)

---

### Requirement 8: Avoid Credential Errors During Local Test Execution

**User Story:** As a developer running tests locally, I want the test suite to run without AWS credential warnings or errors, so that I can run tests on any machine.

#### Acceptance Criteria

1. WHEN a developer runs `pytest backend/tests/e2e/ -v` on a local machine (without ~/.aws/credentials configured), ALL tests SHALL execute successfully (zero credential-related errors)
2. BEFORE app import, conftest.py SHALL set these environment variables:
   - AWS_ACCESS_KEY_ID=testing
   - AWS_SECRET_ACCESS_KEY=testing
   - AWS_SECURITY_TOKEN=testing
3. WHEN boto3 module code attempts to load credentials (during import or client instantiation), boto3 SHALL use the "testing" environment variable values (not attempt to load from ~/.aws/credentials or IAM metadata)
4. IF credentials cannot be found in the environment, boto3 SHALL use the moto-provided mocks (no fallback to real AWS, no credential errors)
5. WHEN running tests in GitHub Actions, environment variables SHALL NOT require AWS credentials in the GitHub Actions secrets - the testing values SHALL be sufficient
6. WHEN tests complete, environment variables MAY revert to their pre-test state (no side effects on developer's machine)

---

## Verification

This specification will be verified through:

1. **Manual Code Review**: Verify conftest.py matches the original implementation and all fixtures are present
2. **Local Test Execution**: Run `pytest backend/tests/e2e/ -v` and confirm all tests pass
3. **GitHub Actions CI Run**: Trigger the CI pipeline and confirm all 28 tests pass
4. **Boto3 Mock Verification**: Inspect test logs to confirm boto3 mocking is applied before app import
5. **Documentation Review**: Verify that conftest.py has inline comments and test README is clear

---

## Next Steps

Once these requirements are approved, the implementation will:

1. Restore conftest.py with all boto3 mocking setup
2. Verify all fixtures are properly configured
3. Run local tests to confirm they pass
4. Trigger GitHub Actions to validate CI passes
5. Document any lessons learned in the test infrastructure
