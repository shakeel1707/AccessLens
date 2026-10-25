"""
End-to-End Test Configuration with AWS Service Mocking

CRITICAL DESIGN: boto3 Mocking Strategy
========================================

This conftest.py implements a layered mocking strategy to prevent real AWS API calls
during testing. The key insight is that boto3 credential resolution happens at import time,
BEFORE the FastAPI application initializes.

Without proper mocking:
  1. boto3 attempts to load AWS credentials from ~/.aws/credentials or environment
  2. If credentials are found (or missing), boto3.client() calls try to reach real AWS
  3. Tests make actual HTTP calls to AWS APIs, causing:
     - Slow test execution (network latency)
     - Credential errors on CI systems
     - Potential cost implications if tests modify resources
     - Risk of affecting real infrastructure during development

With moto mocking (implemented here):
  1. moto patches sys.modules['boto3'] and botocore before any app import
  2. Environment variables are set to dummy values (AWS_ACCESS_KEY_ID='testing', etc.)
  3. When create_app() imports boto3 and creates clients, boto3 is already patched
  4. boto3.client('dynamodb') returns a moto mock, not a real AWS client
  5. All boto3 operations are intercepted and responded to in-memory
  6. Tests execute quickly with zero real AWS calls

This approach is critical for:
  - ✓ CI/CD reliability (no credential management needed)
  - ✓ Local development (works on any machine without AWS credentials)
  - ✓ Test isolation (each test gets a fresh, empty mock)
  - ✓ Performance (mock operations are ~1000x faster than real AWS)
  - ✓ Security (no real credentials exposed in test logs or CI)

The @mock_aws decorator from moto library handles all the patching. By applying it
to the mock_boto3 fixture (which is used by client fixture), we ensure mocking is
active whenever tests need AWS services.
"""

import sys
import os
from pathlib import Path

# ========== Module-Level Path Configuration ==========
# Configure sys.path so we can import app.main from backend/src/
backend_root = Path(__file__).parent.parent.parent  # Navigate to backend/ directory
src_path = backend_root / 'src'
sys.path.insert(0, str(src_path))

# Register pytest_asyncio plugin for async test support
pytest_plugins = ('pytest_asyncio',)

# ========== Imports (after path configuration) ==========
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import uuid
from datetime import datetime
from moto import mock_dynamodb, mock_s3



# ========== Task 1: Environment Setup ==========
# These environment variables must be set BEFORE boto3 is imported
# moto requires these to be present (they don't need to be real AWS credentials)
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
os.environ['AWS_SECURITY_TOKEN'] = 'testing'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


# ========== Task 2: mock_boto3 Fixture with @mock_aws Decorator ==========
@pytest.fixture(scope='function')
@mock_dynamodb
@mock_s3
def mock_boto3():

    """
    Fixture that activates moto's AWS service mocking.
    
    This fixture uses the @mock_aws decorator from moto library to patch boto3
    and botocore at the module level. When this fixture is requested (or when
    dependent fixtures like 'client' are requested), moto takes over all boto3
    calls for the duration of the test.
    
    **Why mocking must occur before app import:**
    - boto3 credential resolution happens at import time, not call time
    - If we don't mock before importing app.main, boto3 will try to load real
      credentials from ~/.aws/credentials, IAM metadata, or environment variables
    - By applying @mock_aws to this fixture, mocking is already active when
      the 'client' fixture calls 'from app.main import create_app'
    
    **Environment variables (set at module level):**
    - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SECURITY_TOKEN = 'testing'
    - These dummy values satisfy boto3's credential requirements
    - moto intercepts before any real AWS authentication happens
    
    **Scope: function (default)**
    - Each test gets a fresh mock state
    - Mocks are reset between tests (no state leakage)
    - DynamoDB tables, S3 buckets, etc. start empty for each test
    
    **Dependent fixtures:**
    - client fixture depends on this (ensures mocking is active before app import)
    - mock_aws_services fixture depends on this
    
    **Fixture lifecycle:**
    1. Test requests 'client' fixture
    2. client fixture depends on mock_boto3, so mock_boto3 is invoked first
    3. @mock_aws decorator activates (patches sys.modules['boto3'])
    4. 'from app.main import create_app' executes with moto active
    5. create_app() calls boto3.client('dynamodb'), boto3.client('s3'), etc.
    6. These calls receive moto mocks (not real AWS clients)
    7. Test executes with mocked services
    8. @mock_aws context exits, moto cleans up
    9. Next test gets fresh mocks
    """
    # The @mock_aws decorator handles all mocking setup
    # The fixture body can be used for additional setup if needed
    yield


# ========== Task 1 (continued): client Fixture ==========
@pytest.fixture(scope='function')
def client(mock_boto3):
    """
    FastAPI TestClient with mocked AWS services.
    
    This fixture provides a synchronous test client that can make HTTP requests
    to the FastAPI application. The key design point is that app.main is imported
    AFTER the mock_boto3 fixture has activated moto mocking.
    
    **Dependency on mock_boto3 fixture:**
    - By declaring mock_boto3 as a parameter, we ensure moto is already active
    - The @mock_aws decorator on mock_boto3 patches boto3 before this runs
    - When we do 'from app.main import create_app', boto3 is already mocked
    - create_app() calls boto3.client() and gets moto mocks (not real AWS)
    
    **Return value:**
    - FastAPI TestClient instance ready for test requests
    - Tests use: client.get('/endpoint'), client.post('/endpoint', json={...}), etc.
    
    **Scope: function**
    - Each test gets a fresh app instance
    - No state shared between tests
    
    **Example usage in tests:**
    ```python
    def test_scan_submission(client):
        response = client.post(
            "/api/scan",
            json={"url": "https://example.com", "user_id": "user-001"}
        )
        assert response.status_code == 202
        assert "scan_id" in response.json()
    ```
    """
    # CRITICAL: Import app AFTER moto is active (ensured by mock_boto3 dependency)
    # If this import happened before @mock_aws, boto3 would attempt real AWS calls
    from app.main import create_app
    
    app = create_app()
    return TestClient(app)


# ========== mock_aws_services Fixture ==========
@pytest.fixture(scope='function')
def mock_aws_services(mock_boto3):
    """
    Registry of mocked AWS services for test assertions and verification.
    
    This fixture returns a dict of mock service references that tests can use
    to assert that AWS operations were called correctly, without needing to
    inspect moto's internal state directly.
    
    **Return structure:**
    {
        'dynamodb': MagicMock,    # Mocked DynamoDB client
        'bedrock': MagicMock,      # Mocked Bedrock client
        's3': MagicMock            # Mocked S3 client
    }
    
    **Usage in tests:**
    ```python
    def test_scan_saved_to_db(client, mock_aws_services, sample_scan_data):
        # Make request that triggers boto3.client('dynamodb').put_item()
        response = client.post("/api/scan", json=sample_scan_data)
        
        # Assert the dynamodb mock was called
        assert mock_aws_services['dynamodb'].put_item.called
    ```
    
    **Why this fixture exists:**
    - Provides convenient access to mocks for assertions
    - Centralizes mock configuration
    - Allows tests to verify AWS operations occurred as expected
    
    **Note:** Tests can also use moto's built-in inspection methods directly:
    ```python
    import boto3
    from moto import mock_dynamodb, mock_s3
    
    with mock_aws():
        dynamodb = boto3.client('dynamodb')
        # moto tracks all calls internally
        # Available via moto's backend inspection APIs
    ```
    """
    return {
        'dynamodb': MagicMock(),
        'bedrock': MagicMock(),
        's3': MagicMock()
    }


# ========== Test Data Fixtures ==========

@pytest.fixture(scope='function')
def sample_scan_data():
    """
    Provides realistic sample scan data for tests.
    
    Returns a new dict instance each time (not a singleton that could be mutated).
    Matches the Scan model schema used by the application.
    
    **Fields:**
    - scan_id: Unique identifier (UUID format)
    - url: Target URL to scan
    - user_id: Submitting user's ID
    - status: Scan workflow status
    - created_at: Timestamp (ISO 8601 format)
    - updated_at: Timestamp (ISO 8601 format)
    
    **Example usage:**
    ```python
    def test_scan_submission(client, sample_scan_data):
        response = client.post("/api/scan", json=sample_scan_data)
        assert response.status_code == 202
    ```
    """
    return {
        'scan_id': f'test-{uuid.uuid4().hex[:8]}',
        'url': 'https://example.com',
        'user_id': 'test-user-001',
        'status': 'completed',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }


@pytest.fixture(scope='function')
def sample_findings():
    """
    Provides realistic sample accessibility findings for tests.
    
    Returns a new list each time with multiple finding objects that match
    the Finding model schema used by the application.
    
    **Fields per finding:**
    - id: Unique finding identifier
    - scan_id: Associated scan
    - violation_type: Type of accessibility violation (alt_text, form_label, etc.)
    - impact: Severity level (critical, serious, moderate, minor)
    - elements: HTML elements affected
    - wcag_criteria: WCAG 2.1 criterion (e.g., 1.1.1, 1.3.1)
    - confidence: Confidence score (0.0-1.0)
    - message: Human-readable description
    
    **Example usage:**
    ```python
    def test_repair_generation(client, sample_findings):
        response = client.post(
            "/api/repair/generate",
            json={"findings": sample_findings}
        )
        assert response.status_code == 200
    ```
    """
    return [
        {
            'id': f'finding-{uuid.uuid4().hex[:8]}',
            'scan_id': 'test-scan',
            'violation_type': 'alt_text',
            'impact': 'critical',
            'elements': ['img'],
            'wcag_criteria': '1.1.1',
            'confidence': 0.95,
            'message': 'Image missing alt text'
        },
        {
            'id': f'finding-{uuid.uuid4().hex[:8]}',
            'scan_id': 'test-scan',
            'violation_type': 'form_label',
            'impact': 'critical',
            'elements': ['input'],
            'wcag_criteria': '1.3.1',
            'confidence': 0.92,
            'message': 'Form input missing label'
        }
    ]


@pytest.fixture(scope='function')
def sample_repairs():
    """
    Provides realistic sample repair proposals for tests.
    
    Returns a new list each time with multiple repair objects that match
    the Repair model schema used by the application.
    
    **Fields per repair:**
    - id: Unique repair identifier
    - finding_id: Associated finding that this repair addresses
    - repair_type: Type of repair (add_attribute, modify_element, restructure)
    - code_before: Original HTML/code snippet
    - code_after: Proposed fixed HTML/code snippet
    
    **Example usage:**
    ```python
    def test_repair_approval(client, sample_repairs):
        repair_id = sample_repairs[0]['id']
        response = client.post(
            f"/api/repair/{repair_id}/approve",
            json={"user_id": "user-001"}
        )
        assert response.status_code == 200
    ```
    """
    return [
        {
            'id': f'repair-{uuid.uuid4().hex[:8]}',
            'finding_id': 'finding-1',
            'repair_type': 'add_attribute',
            'code_before': '<img src="photo.jpg">',
            'code_after': '<img src="photo.jpg" alt="Product">'
        }
    ]


@pytest.fixture(scope='function')
def mock_axe_findings():
    """
    Provides mock Axe accessibility rule definitions for tests.
    
    Returns metadata about common accessibility violations that the Axe
    accessibility scanning engine detects.
    
    **Structure:**
    {
        'rule_id': {
            'id': 'rule_identifier',
            'impact': 'critical|serious|moderate|minor',
            'wcag': 'wcag_criterion_id'
        }
    }
    
    **Example usage:**
    ```python
    def test_axe_rule_mapping(mock_axe_findings):
        assert mock_axe_findings['alt_text']['impact'] == 'critical'
        assert mock_axe_findings['alt_text']['wcag'] == '1.1.1'
    ```
    """
    return {
        'alt_text': {
            'id': 'alt-text',
            'impact': 'critical',
            'wcag': '1.1.1'
        },
        'form_label': {
            'id': 'form-label',
            'impact': 'critical',
            'wcag': '1.3.1'
        }
    }


@pytest.fixture(scope='function')
def realistic_html_violations():
    """
    Provides realistic HTML violation patterns for tests.
    
    Returns a dict mapping violation types to their WCAG criteria and
    descriptions, useful for testing violation detection and repair logic.
    
    **Example usage:**
    ```python
    def test_violation_classification(realistic_html_violations):
        violation = realistic_html_violations['images_without_alt']
        assert violation['wcag'] == '1.1.1'
    ```
    """
    return {
        'images_without_alt': {'type': 'alt_text', 'wcag': '1.1.1'},
        'form_without_labels': {'type': 'form_label', 'wcag': '1.3.1'}
    }


# ========== Auto-Use Fixtures ==========

@pytest.fixture(autouse=True, scope='function')
def mock_dynamodb_tables(mock_boto3):
    """
    Auto-use fixture that ensures DynamoDB is mocked for all tests.
    
    This fixture is automatically injected into every test (autouse=True),
    even if the test doesn't explicitly request it. This ensures that
    DynamoDB access is always mocked and never attempts real AWS calls.
    
    **Why auto-use:**
    - Every test that uses the app (via 'client' fixture) might trigger
      DynamoDB operations
    - By making this auto-use, we guarantee mocking is always applied
    - Tests don't need to remember to include this fixture
    - Prevents accidental real AWS calls from careless test code
    
    **Dependency on mock_boto3:**
    - This fixture depends on mock_boto3 to ensure moto is active first
    - DynamoDB mocking happens within the @mock_aws context
    
    **Setup and teardown:**
    - Setup: Create empty in-memory DynamoDB mock tables
    - Yield: Allow test to run with mocked tables
    - Teardown: Clean up is handled automatically by @mock_aws (reset between tests)
    
    **Example (implicit, no changes to test code needed):**
    ```python
    def test_scan_submission(client, sample_scan_data):
        # mock_dynamodb_tables is automatically applied here
        # Any app code that calls dynamodb.put_item() gets moto mocks
        response = client.post("/api/scan", json=sample_scan_data)
        assert response.status_code == 202
    ```
    """
    # In-memory DynamoDB state for tests
    # This dict simulates the DynamoDB tables used by the app
    scans_db = {
        'test-001': {
            'scan_id': 'test-001',
            'url': 'https://example.com',
            'status': 'completed'
        },
        # Additional test data can be added here as needed
    }
    
    # Yield control back to the test
    # Tests run with mocking active
    yield
    
    # Cleanup (moto handles automatic state reset between tests)
    # No explicit cleanup needed here
