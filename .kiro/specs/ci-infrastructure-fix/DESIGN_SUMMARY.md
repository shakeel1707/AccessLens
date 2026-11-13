# Design Summary: CI Infrastructure Fix

## Problem Statement

The E2E test suite in `backend/tests/e2e/` cannot run because `conftest.py` was deleted. This causes:
- 28 E2E tests to fail with import errors
- Missing fixtures that tests depend on
- CI pipeline failures in GitHub Actions
- Broken mocking of AWS services (boto3 attempts real connections)

## Solution Overview

Restore `backend/tests/e2e/conftest.py` with:
1. **Moto-based AWS mocking** - Intercept boto3 before app initialization
2. **Comprehensive fixtures** - client, mock_aws_services, sample_* data fixtures
3. **Proper test infrastructure** - Auto-use fixtures, environment setup, documentation
4. **CI/CD compatibility** - Works in GitHub Actions (Python 3.10+)

## Architecture Decisions

### 1. Early Mocking (Before App Import)
**Decision:** Apply `@mock_aws` decorator at fixture level, import app INSIDE the decorator

```python
@pytest.fixture(scope="function")
@mock_aws
def client():
    from app.main import create_app  # Import AFTER moto is active
    app = create_app()
    return TestClient(app)
```

**Why:** Ensures boto3 is patched before any boto3.client() calls in app initialization.

### 2. Dummy AWS Credentials (Non-Secret)
**Decision:** Use test credentials that are NOT secrets

```python
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
```

**Why:** Moto requires credentials but they don't need to be real. These are public test values, not secrets.

### 3. Function-Scoped Fixtures
**Decision:** All fixtures have `scope="function"` (not `scope="session"`)

**Why:** Fresh mock state for each test prevents test pollution and interdependencies.

### 4. Auto-Use Mocking Fixture
**Decision:** Include `@pytest.fixture(autouse=True)` for DynamoDB setup

**Why:** Tests automatically get consistent mocking without explicit fixture requests.

### 5. Separate conftest.py for E2E
**Decision:** Keep existing `backend/tests/conftest.py` (root) and create new `backend/tests/e2e/conftest.py` (E2E-specific)

**Why:** Root conftest has general setup; E2E conftest has AWS mocking specific to E2E tests.

## Key Components

### Fixtures Provided

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `client` | function | FastAPI TestClient with mocked AWS |
| `mock_aws_services` | function | Registry of mocked services |
| `sample_scan_data` | function | Realistic scan test data |
| `sample_findings` | function | Array of accessibility violations |
| `sample_repairs` | function | Array of suggested fixes |
| `mock_axe_findings` | function | Rule metadata from Axe engine |
| `mock_dynamodb_tables` | function | Auto-use DynamoDB setup |

### Test Data Models

**Scan:**
```json
{
  "scan_id": "test-scan-abc",
  "url": "https://example.com",
  "user_id": "test-user-001",
  "status": "completed",
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

**Finding:**
```json
{
  "id": "finding-1",
  "scan_id": "test-scan",
  "violation_type": "alt_text",
  "impact": "critical",
  "wcag_criteria": "1.1.1",
  "confidence": 0.95,
  "message": "Image missing alt text"
}
```

**Repair:**
```json
{
  "id": "repair-1",
  "finding_id": "finding-1",
  "repair_type": "add_attribute",
  "code_before": "<img src=\"photo.jpg\">",
  "code_after": "<img src=\"photo.jpg\" alt=\"Product\">"
}
```

## Testing Organization

### 28 E2E Tests across 5 test classes

1. **TestE2ECompleteWorkflow** (6 tests)
   - Happy path workflow
   - URL validation (SSRF prevention)
   - Concurrent scan isolation

2. **TestE2EErrorScenarios** (6 tests)
   - Network timeouts
   - Invalid IDs
   - State constraint violations

3. **TestE2EDataPersistence** (3 tests)
   - Scan data saved
   - Repairs linked correctly
   - Status tracked

4. **TestE2EReportGeneration** (4 tests)
   - JSON, CSV, PDF export
   - Invalid format rejection

5. **TestE2EPerformance** (3 tests)
   - Response time assertions
   - High-volume input handling

## Critical Implementation Details

### Moto Integration

```
Test Execution Flow:
1. pytest discovers test_*.py files
2. conftest.py loads
3. Test requests `client` fixture
4. @mock_aws decorator activates
5. Environment variables set (fake AWS creds)
6. create_app() called with moto active
7. boto3.client() calls are intercepted by moto
8. TestClient wraps the app
9. Test executes with all AWS calls mocked
10. Fixture cleans up, moto resets state
```

### Environment Setup

**File Structure:**
```
backend/
├── src/app/ (source code)
├── tests/
│   ├── conftest.py (root - general setup)
│   └── e2e/
│       ├── conftest.py (E2E - AWS mocking)
│       └── test_*.py (28 E2E tests)
└── requirements.txt (includes moto==4.2.10)
```

**Python Versions:** 3.10, 3.11
**Key Dependencies:**
- pytest==7.4.3
- pytest-asyncio==0.21.1
- moto==4.2.10
- fastapi==0.104.1
- boto3==1.29.7

## Verification Strategy

### Pre-Deployment
- ✓ Syntax check: `python -m py_compile backend/tests/e2e/conftest.py`
- ✓ Import check: Verify app loads with moto active
- ✓ Fixture availability: List all fixtures via pytest
- ✓ Single test: Run one test successfully

### Post-Deployment
- ✓ Full suite: All 28 tests pass
- ✓ Coverage: Generate and verify coverage report
- ✓ CI execution: GitHub Actions workflow completes successfully
- ✓ Mocking verification: Tests execute fast (not hitting real AWS)

## Documentation

### Inline Comments
Every fixture includes detailed comments explaining:
- Purpose and return values
- Why the implementation works
- Example usage patterns

### TESTING.md Guide
Comprehensive documentation covering:
- Testing architecture overview
- Running tests locally and in CI
- Common issues and solutions
- Adding new tests
- CI/CD integration

## Success Criteria

✓ All 28 E2E tests pass locally
✓ All 28 E2E tests pass in GitHub Actions (Python 3.10, 3.11)
✓ No import errors or credential errors
✓ No real AWS API calls made
✓ Test execution completes in < 5 minutes
✓ Coverage report generated
✓ Documentation is clear and maintainable

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Moto version incompatibility | Pin moto==4.2.10 in requirements.txt |
| Python version issues | Test on 3.10 and 3.11 in GitHub Actions matrix |
| boto3 import order issues | Import app INSIDE @mock_aws decorator |
| Test interdependencies | Use function scope for all fixtures |
| Missing AWS service mocks | Document which services are mocked |
| Credential issues in CI | Use dummy credentials, not real secrets |

## Files Created

1. `backend/tests/e2e/conftest.py` - Main fixture file
2. `backend/tests/TESTING.md` - Comprehensive testing guide
3. `.kiro/specs/ci-infrastructure-fix/design.md` - This design document

## Implementation Timeline

1. **Create conftest.py** (1-2 hours)
   - Copy structure from root conftest.py
   - Add moto decorators and mocking setup
   - Implement all 7 fixtures
   - Add inline documentation

2. **Create TESTING.md** (30-45 min)
   - Overview and architecture
   - Running tests locally
   - Common issues and solutions
   - CI/CD integration guide

3. **Local Verification** (30-45 min)
   - Run full test suite locally
   - Verify coverage
   - Check documentation clarity

4. **CI/CD Verification** (15-30 min)
   - Push to branch
   - Wait for GitHub Actions
   - Confirm all tests pass
   - Review artifacts

**Total Estimated Time:** 3-4 hours

## Next Phase

After design approval:
1. Implement conftest.py with all fixtures
2. Create TESTING.md documentation
3. Run local verification
4. Commit and push to trigger CI
5. Verify all tests pass in GitHub Actions
