# End-to-End Testing Documentation

## Overview

The AccessLens end-to-end (E2E) test suite validates the complete accessibility scanning and repair workflow from start to finish. These 28 comprehensive tests verify that URL submissions are correctly processed, websites are scanned for accessibility violations, repairs are generated and approved, patches are applied, and reports are successfully generated. By using moto-based AWS service mocking, tests execute without requiring real AWS credentials or making actual API calls to Amazon services, making them ideal for both local development and CI/CD environments.

## Quick Start

To run the complete E2E test suite locally:

```bash
pytest backend/tests/e2e/ -v
```

This command will execute all 28 tests and display verbose output showing each test name and result.

## Test Structure

### Fixture Architecture

The E2E test suite is built on a layered fixture architecture that ensures proper AWS service mocking before any application code is imported:

**Core Fixtures:**
- **`mock_boto3`**: Activates moto's `@mock_aws` decorator to patch boto3 before any app imports. This is the foundation that prevents real AWS calls.
- **`client`**: Creates a FastAPI TestClient wrapping the application. Depends on `mock_boto3` to ensure mocking is active during app initialization.
- **`mock_aws_services`**: Returns a registry of mocked AWS service references for test assertions (DynamoDB, S3, Bedrock).

**Test Data Fixtures:**
- **`sample_scan_data`**: Provides realistic scan submission data (scan_id, url, user_id, status, timestamps).
- **`sample_findings`**: Returns a list of mock accessibility violation findings (2+ findings with violation types, WCAG criteria, impact levels).
- **`sample_repairs`**: Provides mock repair proposals showing code before/after for accessibility fixes.

**Auto-Use Fixtures:**
- **`mock_dynamodb_tables`**: Automatically applied to all tests (via `autouse=True`). Ensures DynamoDB access is always mocked, preventing accidental real AWS calls even if tests forget to include the fixture explicitly.

### Mocking Strategy

The critical design principle is that **boto3 mocking must occur BEFORE the FastAPI app imports boto3**. Here's why:

1. When Python imports `app.main`, it immediately executes code that calls `boto3.client('dynamodb')` and similar
2. If boto3 isn't mocked yet, boto3 immediately begins credential resolution (checking `~/.aws/credentials`, environment variables, IAM metadata, etc.)
3. Without dummy credentials set, this raises `NoCredentialsError` and the import fails
4. Even if credentials exist, boto3 would make real HTTP calls to AWS

The moto library patches `sys.modules['boto3']` and `botocore` at the module level. By applying the `@mock_aws` decorator to `mock_boto3` and making `client` depend on it, mocking is guaranteed to be active when `create_app()` executes:

```
1. Test requests 'client' fixture
2. client fixture declares mock_boto3 dependency → mock_boto3 runs first
3. @mock_aws decorator activates (patches sys.modules['boto3'])
4. Environment variables (AWS_ACCESS_KEY_ID='testing') are set
5. from app.main import create_app executes with moto active
6. create_app() calls boto3.client() → receives moto mock objects
7. Test runs with all boto3 calls intercepted in-memory
8. @mock_aws context exits, mocks reset
9. Next test starts fresh
```

### Why Fixtures Matter

- **Isolation**: Each test gets a fresh mock state with empty databases and clean service state
- **Speed**: Mocked operations complete in milliseconds vs. seconds for real AWS API calls
- **Reliability**: No credential errors, no network timeouts, no AWS service unavailability
- **Safety**: Zero risk of modifying real infrastructure; tests never leave any trace in AWS
- **Consistency**: Tests produce identical results every run, every machine, every CI pipeline

## Running Tests

### Local Execution - All Tests

```bash
cd backend
pytest tests/e2e/ -v
```

Expected output (28 tests pass):
```
tests/e2e/test_complete_workflow.py::TestE2ECompleteWorkflow::test_e2e_workflow_success_happy_path XFAIL
tests/e2e/test_complete_workflow.py::TestE2ECompleteWorkflow::test_e2e_workflow_invalid_url PASSED
tests/e2e/test_complete_workflow.py::TestE2ECompleteWorkflow::test_e2e_workflow_ssrf_prevention PASSED
...
===================== 28 passed in 3.45s =====================
```

### Local Execution - With Coverage Report

```bash
pytest backend/tests/e2e/ --cov=app --cov-report=term-missing
```

This generates a coverage report showing which app code paths are exercised by the E2E tests. Lines not executed by any test are marked with "missing".

### Local Execution - Single Test

To run a specific test (useful for debugging):

```bash
pytest backend/tests/e2e/test_complete_workflow.py::TestE2ECompleteWorkflow::test_e2e_workflow_success_happy_path -v
```

This runs only the named test with verbose output and full traceback on failure.

### Local Execution - Specific Test Class

```bash
pytest backend/tests/e2e/test_complete_workflow.py::TestE2EErrorScenarios -v
```

This runs all tests within the `TestE2EErrorScenarios` class.

### Test Execution Time

Expect total execution time of **30-60 seconds locally** (depending on machine). Moto operations are extremely fast (in-memory), so tests complete quickly.

## Using Fixtures

### Example 1: Using the `client` Fixture to Make HTTP Requests

The `client` fixture provides a TestClient that can make HTTP requests to your FastAPI application exactly as external clients would:

```python
def test_scan_submission(client):
    """
    Test that users can submit a URL for accessibility scanning.
    The client fixture provides a TestClient with mocked AWS services.
    """
    response = client.post(
        "/api/scan",
        json={
            "url": "https://example.com",
            "user_id": "test-user-001"
        }
    )
    
    # Assertions verify the response
    assert response.status_code == 202, "Should accept scan and return 202 Accepted"
    data = response.json()
    assert "scan_id" in data, "Response should include scan ID"
    assert data["status"] == "queued", "New scan should have queued status"
```

### Example 2: Using `sample_scan_data` Fixture to Prepare Test Data

The `sample_scan_data` fixture provides realistic data that matches your application's expected schema:

```python
def test_scan_retrieval(client, sample_scan_data):
    """
    Test that submitted scans can be retrieved by their ID.
    The sample_scan_data fixture provides realistic scan submission data.
    """
    # Submit a scan
    submit_response = client.post(
        "/api/scan",
        json=sample_scan_data
    )
    assert submit_response.status_code == 202
    scan_id = submit_response.json()["scan_id"]
    
    # Retrieve the scan
    get_response = client.get(f"/api/verification/{scan_id}")
    
    # Verify we can fetch what we submitted
    assert get_response.status_code in [200, 404]  # 404 if async not ready yet
    if get_response.status_code == 200:
        retrieved = get_response.json()
        assert retrieved["scan_id"] == scan_id
```

### Example 3: Using `mock_aws_services` and `sample_findings` Fixtures

The `mock_aws_services` fixture provides references to mocked AWS services, and `sample_findings` provides realistic accessibility violation data:

```python
def test_repair_generation_with_findings(
    client,
    mock_aws_services,
    sample_findings
):
    """
    Test that repairs are generated from accessibility findings.
    mock_aws_services lets us verify AWS operations.
    sample_findings provides realistic violation data.
    """
    # Simulate scan with findings
    repair_response = client.post(
        "/api/repair/generate",
        json={
            "scan_id": "test-scan-001",
            "findings": sample_findings  # Use fixture data
        }
    )
    
    # Verify repair generation
    assert repair_response.status_code == 202
    repairs = repair_response.json()
    assert len(repairs.get("repair_ids", [])) > 0
    
    # If needed, verify AWS was called (for advanced testing)
    # assert mock_aws_services['bedrock'].invoke_model.called
    # (This would require additional instrumentation in your app)
```

## Adding New Tests

Follow these steps to write new E2E tests:

### Step 1: Create Test File

Create a new test file in `backend/tests/e2e/test_*.py` (e.g., `test_custom_workflow.py`). Using the `test_` prefix ensures pytest discovers it.

### Step 2: Import Dependencies

```python
import pytest
from fastapi.testclient import TestClient
```

### Step 3: Define Test Class

Organize related tests in a class:

```python
class TestNewWorkflow:
    """Group of tests for custom workflow features."""
```

### Step 4: Write Test Function

```python
def test_custom_feature(self, client, sample_scan_data):
    """
    Docstring explaining what this test validates.
    
    List fixtures used as parameters (pytest injects them automatically):
    - client: FastAPI TestClient with mocked AWS
    - sample_scan_data: Realistic scan data
    """
    # Arrange: Set up test data
    data = sample_scan_data.copy()
    data["url"] = "https://specific-test-site.com"
    
    # Act: Call API under test
    response = client.post("/api/scan", json=data)
    
    # Assert: Verify expected behavior
    assert response.status_code == 202
    assert response.json()["status"] == "queued"
```

### Step 5: Follow Naming Conventions

- **File names**: `test_*.py` (e.g., `test_workflow.py`)
- **Class names**: `Test*` (e.g., `TestWorkflow`)
- **Function names**: `test_*` (e.g., `test_feature_behavior`)

### Example: Complete New Test

```python
# backend/tests/e2e/test_batch_scanning.py
import pytest

class TestBatchScanning:
    """Tests for submitting multiple scans in batch."""
    
    def test_batch_scan_submission(self, client, sample_scan_data):
        """Verify multiple scans can be submitted in one batch."""
        scan_ids = []
        
        # Submit 5 scans
        for i in range(5):
            data = sample_scan_data.copy()
            data["url"] = f"https://example-{i}.com"
            
            response = client.post("/api/scan", json=data)
            assert response.status_code == 202
            scan_ids.append(response.json()["scan_id"])
        
        # Verify all IDs are unique
        assert len(scan_ids) == len(set(scan_ids))
```

## Adding New AWS Service Mocks

The `mock_aws_services` fixture currently provides DynamoDB, S3, and Bedrock mocks. To add mocking for additional AWS services:

### Step 1: Identify Required Service

Determine which AWS service you need (SNS, SQS, Lambda, etc.). Check [moto documentation](https://docs.getmoto.org/) to verify it's supported.

### Step 2: Update conftest.py

Edit `backend/tests/e2e/conftest.py` and modify the `mock_aws_services` fixture:

```python
@pytest.fixture(scope='function')
def mock_aws_services(mock_boto3):
    """Registry of mocked AWS services for test assertions."""
    return {
        'dynamodb': MagicMock(),
        's3': MagicMock(),
        'bedrock': MagicMock(),
        'sns': MagicMock(),        # NEW SERVICE
        'sqs': MagicMock(),        # NEW SERVICE
    }
```

### Step 3: Update Documentation

Add a section in this file documenting the new service and example usage.

### Step 4: Test the Mock

Create a test to verify the new service mock works:

```python
def test_sns_publish(client, mock_aws_services):
    """Verify SNS publishing works with mocked service."""
    response = client.post(
        "/api/notify",
        json={"message": "Test notification"}
    )
    assert response.status_code == 200
    # Verify SNS was used
    # assert mock_aws_services['sns'].publish.called
```

### Reference: Common AWS Services in moto

Moto supports these services commonly used in web applications:

- **DynamoDB**: NoSQL database (fully supported)
- **S3**: Object storage (fully supported)
- **Lambda**: Serverless compute (fully supported)
- **SNS**: Publish/subscribe notifications (fully supported)
- **SQS**: Message queuing (fully supported)
- **Bedrock**: AI/ML models (supported)
- **CloudWatch**: Monitoring/logging (fully supported)

[View complete moto service list →](https://docs.getmoto.org/en/latest/docs/services/index.html)

## Troubleshooting

### Issue: "boto3 import fails" or "ModuleNotFoundError: No module named 'boto3'"

**Root Cause:** conftest.py not found or `@mock_aws` decorator not applied to mock_boto3 fixture.

**Solution:**
1. Verify `backend/tests/e2e/conftest.py` exists (should be present from task 1)
2. Verify mock_boto3 fixture has `@mock_aws` decorator before the function definition:
   ```python
   @pytest.fixture(scope='function')
   @mock_aws
   def mock_boto3():
   ```
3. Verify client fixture depends on mock_boto3: `def client(mock_boto3):`
4. Run fixture discovery: `pytest backend/tests/e2e/conftest.py --fixtures`

### Issue: "NoCredentialsError" or "InvalidClientTokenId"

**Root Cause:** AWS credentials aren't being mocked properly. The app is attempting to use real AWS credentials.

**Solution:**
1. Verify conftest.py sets environment variables at module level:
   ```python
   os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
   os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
   os.environ['AWS_SECURITY_TOKEN'] = 'testing'
   os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
   ```
2. These must be set BEFORE boto3 is imported
3. Check that moto is imported: `import moto` should succeed (verify in requirements.txt)
4. Try running with verbose output to see where error occurs: `pytest backend/tests/e2e/ -vv`

### Issue: "DynamoDB table not found" or "ResourceNotFound"

**Root Cause:** Mock DynamoDB tables aren't being created for the test.

**Solution:**
1. Ensure `mock_dynamodb_tables` fixture is present and auto-use (should be present from task 8)
2. Verify the fixture creates any tables your app expects:
   ```python
   @pytest.fixture(autouse=True, scope='function')
   def mock_dynamodb_tables(mock_boto3):
       # Tables should be created here
       yield
   ```
3. If your app creates tables dynamically, ensure that happens within the @mock_aws context
4. Alternative: Create tables in individual tests as needed:
   ```python
   def test_with_table(client, mock_boto3):
       import boto3
       dynamodb = boto3.resource('dynamodb')
       dynamodb.create_table(
           TableName='MyTable',
           KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
           AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
           BillingMode='PAY_PER_REQUEST'
       )
       # Now test with table
   ```

### Issue: "Tests timeout" or "Test takes 30+ seconds"

**Root Cause:** Real AWS API calls are happening (mocking not active), or test logic is stuck in a loop.

**Solution:**
1. Verify mocking is active by adding debug output:
   ```python
   def test_check_mocking(client):
       import boto3
       # This should return a moto mock, not real AWS client
       s3 = boto3.client('s3')
       print(f"S3 client type: {type(s3)}")  # Should be moto.s3.models.s3_backends
   ```
2. Check if real AWS credentials are configured (~/.aws/credentials or env vars)
   - If they are, boto3 might bypass the test fixtures
   - Temporarily move/remove ~/.aws/credentials to test this
3. Look for infinite loops or blocking calls in test code
4. Use a timeout decorator for tests that might hang:
   ```python
   import pytest
   
   @pytest.mark.timeout(5)  # 5 second timeout
   def test_something(client):
       # Test code
   ```

### Issue: "Import error for app.main" or "Cannot import create_app"

**Root Cause:** sys.path isn't configured correctly in conftest.py.

**Solution:**
1. Verify conftest.py includes sys.path setup:
   ```python
   import sys
   from pathlib import Path
   
   backend_root = Path(__file__).parent.parent.parent
   src_path = backend_root / 'src'
   sys.path.insert(0, str(src_path))
   ```
2. Verify structure: if conftest.py is in `backend/tests/e2e/`, then `backend/src` should exist
3. Verify app code is in `backend/src/app/main.py` (or adjust path accordingly)
4. Test import manually: 
   ```bash
   cd backend
   python -c "import sys; sys.path.insert(0, 'src'); from app.main import create_app; print(create_app)"
   ```

### Issue: "Tests pass locally but fail in CI/GitHub Actions"

**Root Cause:** Environment differences between local and CI (Python version, installed packages, missing dependencies).

**Solution:**
1. Check Python version matches: `python --version` should match CI matrix (3.10, 3.11)
2. Verify all dependencies installed: `pip install -r backend/requirements.txt`
3. Verify test environment variable setup is identical in CI
4. Check CI logs for full error messages: GitHub Actions provides detailed job logs
5. Replicate CI environment locally: 
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r backend/requirements.txt
   pytest backend/tests/e2e/ -v
   ```

### Issue: "Test order matters" or "Tests fail when run together but pass individually"

**Root Cause:** Test state leaking between tests (fixtures aren't properly isolated).

**Solution:**
1. Verify all fixtures have `scope='function'` (not 'module' or 'session')
2. Check that sample data fixtures return fresh instances, not singletons:
   ```python
   @pytest.fixture(scope='function')
   def sample_scan_data():
       # Correct: new dict each call
       return {'scan_id': ..., 'url': ...}
       
       # Wrong: shared dict across tests
       # data = {'scan_id': ...}
       # return data
   ```
3. Add fixture that clears state between tests:
   ```python
   @pytest.fixture(autouse=True)
   def clear_state():
       yield
       # Cleanup here if needed
   ```
4. Run tests with random order to detect ordering issues:
   ```bash
   pytest backend/tests/e2e/ --random-order
   ```

## CI/CD Integration

### GitHub Actions Workflow

Tests are automatically run by GitHub Actions when code is pushed. The CI pipeline is configured in `.github/workflows/e2e-tests.yml`:

**Workflow Features:**
- **Trigger:** Runs on every push and pull request
- **Matrix:** Tests run on Python 3.10 and Python 3.11
- **Duration:** Completes in < 2 minutes per Python version
- **No secrets needed:** Uses only dummy AWS credentials (AWS_ACCESS_KEY_ID='testing', etc.)
- **Artifact:** Test results are saved as JUnit XML artifact
- **Exit code:** Job fails if any test fails, succeeds if all pass

### No Real AWS Credentials in CI

The test fixtures use dummy credentials that don't require secret management:

```python
# These are set in conftest.py (NOT secrets)
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'      # Dummy value
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'  # Dummy value
os.environ['AWS_SECURITY_TOKEN'] = 'testing'     # Dummy value
```

These values are NOT secrets because:
- They don't grant access to any real AWS account
- They don't need to be hidden from version control
- Moto intercepts boto3 calls before credential validation
- Real AWS account IDs and credentials are never used

### Matrix Testing: Python 3.10 and 3.11

The CI workflow tests against multiple Python versions to ensure compatibility:

```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11']
```

Each Python version gets its own job:
- Tests run independently per version
- All dependencies are fresh-installed for each version
- Results are reported separately per version

### Test Artifacts in CI

After the workflow completes, test results are available:

1. **JUnit XML report**: `test-results.xml` (if configured)
   - Machine-readable format for CI systems
   - Can be viewed in GitHub Actions UI
   - Contains individual test results, timings, failures

2. **GitHub Actions summary**: Visible in PR checks
   - Green checkmark if all tests pass
   - Red X if any test fails
   - Link to full job log

3. **Coverage report** (if enabled):
   - Shows which code paths are tested
   - Can identify untested edge cases

### Running CI Tests Locally

To replicate the CI environment:

```bash
# Use exact Python version from CI matrix
python3.10 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r backend/requirements.txt
pip install pytest pytest-cov

# Run tests exactly as CI does
cd backend
pytest tests/e2e/ -v --tb=short
```

## Key Design Principles

Understanding these principles will help you work effectively with the E2E test infrastructure:

### 1. boto3 Mocking Happens BEFORE App Import

The most critical principle: if boto3 mocking isn't active when `app.main` imports boto3 clients, the import will fail with credential errors.

**Why this matters:**
- boto3 credential resolution happens at import time (not call time)
- The `@mock_aws` decorator patches `sys.modules['boto3']` at function call time
- By making `client` fixture depend on `mock_boto3` (with @mock_aws), we guarantee mocking is active first
- Then `from app.main import create_app` runs with mocking active

**The pattern:**
```
mock_boto3 fixture runs first (@mock_aws decorator activates)
                ↓
boto3 is now mocked in sys.modules
                ↓
client fixture imports create_app (with mocking active)
                ↓
create_app calls boto3.client() → gets moto mocks
                ↓
Test runs with all boto3 calls intercepted
```

### 2. Each Test Gets Fresh Mock State (Function-Scoped Fixtures)

All fixtures use `scope='function'` to ensure isolation:

```python
@pytest.fixture(scope='function')  # Fresh for each test
def client(mock_boto3):
```

**Benefits:**
- One test's database mutations don't affect another test
- One test's API responses don't pollute another test
- Tests can run in any order with identical results
- Parallel test execution is safe (different processes each get fresh mocks)

### 3. No Real AWS Calls Ever Happen

Even if mocking failed, the dummy credentials couldn't grant access to real AWS. Moto ensures:

- All boto3 calls are intercepted before network
- No HTTP requests leave your machine during tests
- No real resources are created, modified, or billed

### 4. Tests Are Fast (Moto Operations In-Memory)

Moto doesn't make HTTP calls; it simulates AWS services in-memory:

- DynamoDB operations: ~1ms (vs. ~100ms over network)
- S3 operations: ~1ms (vs. ~200ms over network)
- Complete test suite: ~30-60 seconds (vs. 5-10 minutes with real AWS)

### 5. Supports Local Dev and CI Execution

Same test code runs identically in:
- **Local machine** without AWS credentials configured
- **CI pipeline** without secret management
- **Different operating systems** (Linux, macOS, Windows)
- **Any Python 3.10+ installation**

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [FastAPI testing guide](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [moto documentation](https://docs.getmoto.org/) - AWS service mocking library
- [boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) - AWS SDK for Python
- [WCAG 2.1 accessibility standards](https://www.w3.org/WAI/WCAG21/quickref/)

## Questions or Issues?

If you encounter issues not covered here:

1. Check the conftest.py file at `backend/tests/e2e/conftest.py`
2. Review the top-level comment block explaining boto3 mocking strategy
3. Check pytest fixture discovery: `pytest backend/tests/e2e/ --fixtures`
4. Run tests with maximum verbosity: `pytest backend/tests/e2e/ -vv --tb=long`
5. Review GitHub Actions CI logs in `.github/workflows/e2e-tests.yml`
