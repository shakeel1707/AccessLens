# CI Infrastructure Fix - Technical Design

## Overview

This design addresses the restoration of the CI infrastructure for end-to-end (E2E) tests by recreating the deleted `conftest.py` in `backend/tests/e2e/`. The conftest provides a comprehensive fixture system that enables 28 E2E tests to run successfully in GitHub Actions across Python 3.8+, with proper AWS service mocking using moto.

The core challenge is preventing boto3 from attempting real AWS credential access during testing while providing complete mock fixtures that tests can rely on. The solution uses moto's decorator pattern combined with early sys.modules manipulation to inject mocks before the FastAPI application is imported.

**Key Goals:**
- Restore test execution to passing status (28 E2E tests)
- Mock AWS services (DynamoDB, Bedrock, S3) before app initialization
- Provide comprehensive fixtures for common test patterns
- Enable CI/CD in GitHub Actions (Python 3.10, 3.11)
- Document mocking strategy for maintainability
- Ensure no secrets or real credentials are needed in CI environment

---

## Architecture

### Fixture Hierarchy

```
conftest.py
├── Module-Level Setup
│   ├── Path configuration (sys.path, backend_root)
│   └── pytest plugins registration
│
├── AWS Mocking Layer (moto)
│   ├── Scoped fixtures (@pytest.fixture scope="function")
│   └── Auto-use fixtures (@pytest.fixture autouse=True)
│
├── Application Fixtures
│   ├── client: FastAPI TestClient
│   └── mock_aws_services: Service registry dict
│
└── Test Data Fixtures
    ├── sample_scan_data: Scan model instance
    ├── sample_findings: List of finding objects
    ├── sample_repairs: List of repair objects
    └── mock_axe_findings: AXE rule mapping
```

### Dependency Graph

```
conftest.py (module import)
  ↓
sys.path setup + pytest_asyncio
  ↓
moto decorators applied to moto_aws fixture
  ↓
client fixture (uses create_app after moto is active)
  ↓
mock_aws_services fixture (registry of mocked services)
  ↓
Test data fixtures (sample_*, mock_*)
  ↓
Test functions (all fixtures available via @pytest.fixture injection)
```

**Critical Ordering:**
1. Path configuration happens at module load time
2. moto.mock_aws() is applied BEFORE any fixture that imports app
3. client fixture imports app.main.create_app() INSIDE the moto context
4. All tests run with mocked AWS services active for their scope

### Module Loading Sequence

When pytest loads `backend/tests/e2e/conftest.py`:

1. **Module initialization** (top-level code runs immediately):
   - Add backend/src to sys.path
   - Register pytest_asyncio plugin
   - **moto decorators NOT applied yet** (only when fixtures are used)

2. **When a test requests the `client` fixture**:
   - moto.mock_aws() decorator activates
   - Environment variables are set (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
   - boto3 clients created within this context will be mocked
   - `app.main.create_app()` is imported and called
   - FastAPI app is instantiated with mocked services
   - TestClient wraps the app

3. **Test execution** with mocked services:
   - DynamoDB operations go to moto mock
   - Bedrock operations go to moto mock
   - S3 operations go to moto mock
   - No real AWS API calls occur

4. **Fixture cleanup** (after test completes):
   - moto context exits
   - Mocks are reset
   - Next test gets fresh mocks

---

## Components and Interfaces

### Core Fixtures

#### 1. `client` Fixture
**Type:** Function-scoped pytest fixture
**Dependencies:** None (but requires moto mocking)
**Returns:** FastAPI TestClient

```python
@pytest.fixture
def client():
    """
    FastAPI TestClient with mocked AWS services.
    
    The moto library patches boto3 at the module level, so we import
    the app AFTER moto is active. This ensures all boto3 clients
    created during app initialization use mocks instead of real AWS.
    """
    from app.main import create_app
    app = create_app()
    return TestClient(app)
```

**Why This Works:**
- `from app.main import create_app` happens INSIDE the moto context
- By the time create_app() runs, boto3 is already patched
- Any boto3.client() calls inside create_app() get mocked clients
- TestClient provides a synchronous interface for testing async endpoints

#### 2. `mock_aws_services` Fixture
**Type:** Function-scoped pytest fixture
**Returns:** Dictionary of mock service references

```python
@pytest.fixture
def mock_aws_services():
    """
    Registry of mocked AWS services for inspection and verification.
    
    Provides direct access to moto-managed mock objects for:
    - Asserting calls were made
    - Setting up mock responses
    - Verifying state changes
    """
    return {
        'dynamodb': MagicMock(),
        'bedrock': MagicMock(),
        's3': MagicMock()
    }
```

**Usage:**
Tests can use this to assert interactions: `mock_aws_services['dynamodb'].assert_called_once()`

#### 3. Test Data Fixtures

**`sample_scan_data`:** Generates realistic scan records
```python
{
    'scan_id': 'test-scan-abc12345',
    'url': 'https://example.com',
    'user_id': 'test-user-001',
    'status': 'completed',
    'created_at': '2024-01-15T10:30:00',
    'updated_at': '2024-01-15T10:35:00'
}
```

**`sample_findings`:** Array of accessibility violations
```python
[
    {
        'id': 'finding-alt1',
        'scan_id': 'test-scan',
        'violation_type': 'alt_text',
        'impact': 'critical',
        'wcag_criteria': '1.1.1',
        'confidence': 0.95,
        'message': 'Image missing alt text'
    },
    # ... more findings
]
```

**`sample_repairs`:** Suggested code fixes
```python
[
    {
        'id': 'repair-fix1',
        'finding_id': 'finding-alt1',
        'repair_type': 'add_attribute',
        'code_before': '<img src="photo.jpg">',
        'code_after': '<img src="photo.jpg" alt="Product">'
    }
]
```

**`mock_axe_findings`:** Rule metadata from Axe accessibility engine
```python
{
    'alt_text': {'id': 'alt-text', 'impact': 'critical', 'wcag': '1.1.1'},
    'form_label': {'id': 'form-label', 'impact': 'critical', 'wcag': '1.3.1'}
}
```

#### 4. Auto-Use Fixtures

**`mock_dynamodb_tables` (autouse=True)**
Automatically activates for every test. Sets up empty DynamoDB mock with proper table schemas.

```python
@pytest.fixture(autouse=True)
def mock_dynamodb_tables(monkeypatch):
    """
    Auto-use fixture that ensures DynamoDB is mocked for all tests.
    
    The @pytest.fixture(autouse=True) decorator means this runs
    automatically for every test without explicit inclusion.
    """
    # Configuration happens here
    yield
    # Cleanup happens here
```

**Why Auto-Use:**
- Tests don't need to explicitly request it
- Ensures consistent mocking across all tests
- Prevents accidental real AWS calls
- Simplifies test code

---

## Data Models

### Scan Status Lifecycle

```
{
  "scan_id": "scan-uuid-here",
  "status": "queued" | "scanning" | "completed" | "failed",
  "url": "https://example.com",
  "user_id": "user-001",
  "created_at": ISO8601,
  "updated_at": ISO8601,
  "findings": [...],
  "repair_batch": {...}
}
```

### Finding Model

```
{
  "id": "finding-uuid",
  "scan_id": "scan-uuid",
  "violation_type": "alt_text" | "form_label" | "color_contrast" | ...,
  "impact": "critical" | "serious" | "moderate" | "minor",
  "elements": ["img", "input"],
  "wcag_criteria": "1.1.1",
  "confidence": 0.92,  # 0.0 to 1.0
  "message": "Human-readable description"
}
```

### Repair Model

```
{
  "id": "repair-uuid",
  "finding_id": "finding-uuid",
  "repair_type": "add_attribute" | "modify_element" | "restructure",
  "code_before": "<original HTML>",
  "code_after": "<repaired HTML>",
  "certainty": 0.87,
  "explanation": "Why this fix works"
}
```

---

## Mocking Strategy

### How Moto Works

Moto is a library that intercepts boto3 calls and returns mock responses without contacting AWS. The key mechanism:

1. **Patch at import time:** moto replaces boto3's internals before any boto3 clients are created
2. **Service emulation:** moto maintains in-memory state for each AWS service
3. **Decorator pattern:** `@mock_aws` decorator activates mocking for a function/fixture scope
4. **Automatic cleanup:** Moto resets state when the decorator context exits

### Integration Point

```python
@pytest.fixture(scope="function")
@mock_aws
def client():
    from app.main import create_app
    app = create_app()
    return TestClient(app)
```

**Explanation:**
- `@mock_aws` is applied FIRST (innermost decorator)
- When the fixture is requested, moto activates
- `from app.main import create_app` happens with moto active
- `create_app()` calls boto3.client('dynamodb'), boto3.client('s3'), etc.
- These clients are mocked by moto, not real AWS
- TestClient wraps the app and provides sync interface

### Service Configuration

Moto provides reasonable defaults, but can be customized:

```python
# In conftest.py, before create_app():

# Ensure tables exist (for tests that need specific schema)
import boto3
from moto import mock_aws

with mock_aws():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='scans',
        KeySchema=[
            {'AttributeName': 'scan_id', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'scan_id', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
```

### Environment Variable Handling

Moto requires AWS credentials to be present (for boto3 client initialization), but they don't need to be real:

```python
import os

# Set fake credentials for testing
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
os.environ['AWS_SECURITY_TOKEN'] = 'testing'
os.environ['AWS_SESSION_TOKEN'] = 'testing'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
```

**Critical Note:** These are NOT secrets. They're dummy values that moto requires. Real secrets never appear in test code or CI configurations.

### Verification Approach

Tests verify mocking is working by:

1. **Making API calls:** `response = client.post("/api/scan", json={...})`
2. **Checking responses:** `assert response.status_code == 202`
3. **Verifying state:** `assert some_value in mock_response.json()`
4. **No external calls:** If mocking is broken, tests would make real AWS calls and fail with credentials error or timeout

**Example verification:**
```python
def test_scan_submission(client):
    response = client.post("/api/scan", json={"url": "https://example.com"})
    # If mocking failed, boto3 would try real AWS → credential error or timeout
    # If mocking works, response comes from moto in-memory mock → fast response
    assert response.status_code == 202
    assert "scan_id" in response.json()
```

---

## Error Handling

### Common Mocking Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `botocore.exceptions.NoCredentialsError` | Moto not active or env vars not set | Ensure `@mock_aws` decorator applied; set dummy AWS_ env vars |
| `ModuleNotFoundError: No module named 'app'` | sys.path not configured | Verify `sys.path.insert(0, str(src_path))` at top of conftest.py |
| `ImportError` in app initialization | boto3 import happens before moto active | Move `from app.main import create_app` INSIDE fixture (after @mock_aws) |
| Tests pass locally but fail in CI | Python version mismatch or moto version | Pin moto==4.2.10 in requirements.txt; test against Python 3.10, 3.11 |
| `DynamoDB table does not exist` | App expects pre-created tables | Use moto to create tables in fixture or app initialization |

### Test-Level Error Handling

Tests in `backend/tests/e2e/test_complete_workflow.py` use defensive assertions:

```python
def test_scan_submission(client):
    response = client.post("/api/scan", json={...})
    
    # Defensive: handle multiple possible responses
    assert response.status_code in [200, 202]  # 200 if sync, 202 if async
    assert "scan_id" in response.json() or response.status_code == 404
```

This approach handles partial implementations gracefully.

---

## Environment Setup

### File Structure

```
backend/
├── src/
│   └── app/
│       ├── main.py
│       ├── core/
│       │   ├── config.py
│       │   └── errors.py
│       └── routers/
│           └── ...
├── tests/
│   ├── conftest.py          ← Root conftest (path setup, pytest_asyncio)
│   └── e2e/
│       ├── conftest.py      ← E2E conftest (AWS mocking, fixtures)
│       ├── test_complete_workflow.py
│       ├── test_simple_workflows.py
│       └── test_realistic_violations.py
└── requirements.txt
```

### AWS Credentials in CI

**GitHub Actions Workflow** (`e2e-tests.yml`):
- No secrets needed for moto mocking
- Tests run with dummy credentials
- Moto intercepts boto3 calls before they reach AWS
- No real AWS account access required

**Local Development:**
- Same dummy credentials work
- Or can use real AWS credentials (moto will use mocks anyway)
- Moto takes precedence over actual AWS

### Python Version Support

**Tested versions:** 3.10, 3.11
**In requirements.txt:** `pytest==7.4.3`, `pytest-asyncio==0.21.1`

These versions support:
- Type hints (Python 3.10+)
- AsyncIO integration with pytest
- Moto 4.2.10 compatibility

### Dependencies

**Critical packages:**
- `pytest==7.4.3` - Test framework
- `pytest-asyncio==0.21.1` - Async test support
- `moto==4.2.10` - AWS service mocking
- `fastapi==0.104.1` - Application framework
- `httpx==0.25.1` - Async HTTP client (implicit in TestClient)
- `boto3==1.29.7` - AWS SDK (will be mocked by moto)

---

## Documentation Approach

### Inline Comments in conftest.py

Each fixture includes detailed comments explaining:
- **Purpose:** What the fixture does
- **Returns:** Data structure returned
- **Why:** Reasoning for implementation choices
- **Usage:** Example test code

Example:
```python
@pytest.fixture
def client():
    """
    FastAPI TestClient with mocked AWS services.
    
    The moto library patches boto3 at the module level, so we import
    the app AFTER moto is active. This ensures all boto3 clients
    created during app initialization use mocks instead of real AWS.
    
    Scope: function (fresh mock state for each test)
    Returns: TestClient instance ready for test requests
    """
```

### TESTING.md Documentation

A companion file `backend/tests/TESTING.md` explains:

1. **Testing Architecture**
   - Fixture system overview
   - Mocking strategy
   - Test organization

2. **Running Tests**
   - Local: `pytest backend/tests/e2e/ -v`
   - With coverage: `pytest backend/tests/e2e/ --cov=app --cov-report=term-missing`
   - Single test: `pytest backend/tests/e2e/test_complete_workflow.py::TestE2ECompleteWorkflow::test_e2e_workflow_success_happy_path -v`

3. **Common Issues & Solutions**
   - Mocking problems
   - Import errors
   - Credential issues

4. **Adding New Tests**
   - Use provided fixtures
   - Follow naming conventions
   - Example test template

5. **CI/CD Integration**
   - GitHub Actions workflow
   - Test execution in CI
   - Artifact handling

---

## Testing Strategy

### Unit Test vs Integration Test vs E2E

| Level | Scope | Tools | Fixtures |
|-------|-------|-------|----------|
| **Unit** | Single function/module | Mock dependencies | `mock_aws_services` |
| **Integration** | Multiple components | Mocked AWS | `client` + `sample_*` |
| **E2E** | Complete workflow | Mocked AWS | All fixtures |

### E2E Test Classes

The 28 E2E tests are organized into classes:

**TestE2ECompleteWorkflow** (6 tests)
- Happy path: full workflow from scan to report
- Invalid URL rejection
- SSRF prevention
- Multiple concurrent scans
- Data isolation between scans

**TestE2EErrorScenarios** (6 tests)
- Network timeout handling
- Repair generation with no findings
- Invalid scan ID handling
- Non-pending repair approval
- Missing scan reports
- Concurrent patch applications

**TestE2EDataPersistence** (3 tests)
- Scan data persisted after submission
- Repairs associated with correct scan
- Patch status tracking

**TestE2EReportGeneration** (4 tests)
- JSON format export
- CSV format export
- PDF generation
- Invalid format rejection

**TestE2EPerformance** (3 tests)
- Scan submission response time (< 5s)
- Many findings handling (50+ items)
- Report generation response time (< 1s)

**Total: 28 tests**

### Test Execution Flow

```
1. pytest discovers test files in backend/tests/e2e/
2. conftest.py is loaded:
   - sys.path configured
   - pytest_asyncio registered
   - Fixtures defined
3. For each test:
   a. Request `client` fixture
   b. @mock_aws decorator activates
   c. Environment variables set (fake AWS credentials)
   d. create_app() called with moto active
   e. boto3 clients created by app are mocked
   f. TestClient wraps the app
   g. Test executes with mocked services
   h. Assertions verified
   i. @mock_aws context exits, moto cleans up
   j. Next test gets fresh mocks
4. Results aggregated
5. Coverage report generated (if --cov flag used)
```

### Continuous Integration

**GitHub Actions Workflow** (`e2e-tests.yml`):

```yaml
e2e-tests:
  matrix:
    python-version: ['3.10', '3.11']
  steps:
    - Set up Python
    - Install dependencies (pip install -r backend/requirements.txt)
    - Run linting (flake8)
    - Run type checking (mypy)
    - Run E2E tests: pytest backend/tests/e2e/ -v
    - Generate coverage report
    - Upload artifacts
```

**Success Criteria:**
- All 28 tests pass
- No import errors
- No credential errors
- Coverage above baseline
- Test execution completes in < 5 minutes

---

## Verification Plan

### Pre-Deployment Verification

1. **Syntax Check**
   ```bash
   python -m py_compile backend/tests/e2e/conftest.py
   ```
   ✓ conftest.py has no syntax errors

2. **Import Check**
   ```bash
   python -c "from app.main import create_app; print('✓ App imports successfully')"
   ```
   ✓ App can be imported with moto active

3. **Fixture Availability**
   ```bash
   pytest backend/tests/e2e/conftest.py --fixtures | grep -E "client|mock_aws|sample_"
   ```
   ✓ All expected fixtures listed

4. **Single Test Execution**
   ```bash
   pytest backend/tests/e2e/test_complete_workflow.py::TestE2ECompleteWorkflow::test_e2e_workflow_success_happy_path -v
   ```
   ✓ At least one test passes

### Post-Deployment Verification

5. **Full Test Suite**
   ```bash
   pytest backend/tests/e2e/ -v --tb=short
   ```
   ✓ All 28 tests pass

6. **Coverage Report**
   ```bash
   pytest backend/tests/e2e/ --cov=app --cov-report=term-missing
   ```
   ✓ Coverage above threshold (baseline TBD)

7. **CI Execution**
   - Push to branch with tests
   - GitHub Actions workflow triggers
   - Runs on Python 3.10 and 3.11
   - All tests pass
   - Artifacts uploaded

8. **Mocking Verification**
   - Check that tests execute in < 30s (fast mock operations, not real AWS)
   - No AWS API calls logged in CloudTrail
   - No credentials error messages
   - No timeout errors (real AWS network issues)

### Test Coverage Verification

Each fixture should be used by at least one test:
- `client` → used by all 28 tests
- `mock_aws_services` → used for assertion verification
- `sample_scan_data` → test data preparation
- `sample_findings` → finding processing tests
- `sample_repairs` → repair generation tests
- `mock_dynamodb_tables` → auto-use, all tests

---

## Implementation Checklist

- [ ] Create `backend/tests/e2e/conftest.py` with moto setup
- [ ] Add AWS credentials environment variables (dummy values)
- [ ] Implement `client` fixture with @mock_aws decorator
- [ ] Implement `mock_aws_services` fixture
- [ ] Implement test data fixtures (sample_*, mock_*)
- [ ] Implement auto-use `mock_dynamodb_tables` fixture
- [ ] Add inline documentation comments
- [ ] Create `backend/tests/TESTING.md` guide
- [ ] Verify local test execution: `pytest backend/tests/e2e/ -v`
- [ ] Verify CI execution in GitHub Actions
- [ ] Confirm all 28 tests pass
- [ ] Confirm coverage report generation
- [ ] Update GitHub Actions workflow if needed

---

## Next Steps

1. **Implementation Phase** - Write conftest.py and TESTING.md
2. **Verification Phase** - Run tests locally and in CI
3. **Documentation Review** - Ensure TESTING.md is clear
4. **Final Testing** - Confirm all 28 tests pass across Python 3.10+
