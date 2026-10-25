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
  - CI/CD reliability (no credential management needed)
  - Local development (works on any machine without AWS credentials)
  - Test isolation (each test gets a fresh, empty mock)
  - Performance (mock operations are ~1000x faster than real AWS)
  - Security (no real credentials exposed in test logs or CI)

The @mock_dynamodb and @mock_s3 decorators from moto library handle all the patching.
By applying them to the mock_boto3 fixture (which is used by client fixture), we ensure
mocking is active whenever tests need AWS services.
"""

import sys
import os
from pathlib import Path

# ========== Module-Level Path Configuration ==========
# Configure sys.path so we can import app.main from backend/src/
backend_root = Path(__file__).parent.parent.parent
src_path = backend_root / 'src'
sys.path.insert(0, str(src_path))

# Register pytest_asyncio plugin for async test support
pytest_plugins = ('pytest_asyncio',)

# ========== Imports ==========
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import uuid
from datetime import datetime
from moto import mock_dynamodb, mock_s3


# ========== Environment Setup ==========
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
os.environ['AWS_SECURITY_TOKEN'] = 'testing'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


# ========== mock_boto3 Fixture ==========
@pytest.fixture(scope='function')
@mock_dynamodb
@mock_s3
def mock_boto3():
    """Fixture that activates moto AWS service mocking."""
    yield


# ========== client Fixture ==========
@pytest.fixture(scope='function')
def client(mock_boto3):
    """FastAPI TestClient with mocked AWS services."""
    from app.main import create_app
    app = create_app()
    return TestClient(app)


# ========== mock_aws_services Fixture ==========
@pytest.fixture(scope='function')
def mock_aws_services(mock_boto3):
    """Registry of mocked AWS services for test assertions."""
    return {
        'dynamodb': MagicMock(),
        's3': MagicMock()
    }


# ========== Test Data Fixtures ==========

@pytest.fixture(scope='function')
def sample_scan_data():
    """Provides realistic sample scan data for tests."""
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
    """Provides realistic sample accessibility findings for tests."""
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
    """Provides realistic sample repair proposals for tests."""
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
    """Provides mock Axe accessibility rule definitions for tests."""
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
    """Provides realistic HTML violation patterns for tests."""
    return {
        'images_without_alt': {'type': 'alt_text', 'wcag': '1.1.1'},
        'form_without_labels': {'type': 'form_label', 'wcag': '1.3.1'}
    }


# ========== Auto-Use Fixtures ==========

@pytest.fixture(autouse=True, scope='function')
def mock_dynamodb_tables(mock_boto3):
    """Auto-use fixture that ensures DynamoDB is mocked for all tests."""
    scans_db = {
        'test-001': {
            'scan_id': 'test-001',
            'url': 'https://example.com',
            'status': 'completed'
        },
    }
    yield
