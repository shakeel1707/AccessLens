"""
End-to-End Test Configuration with AWS Service Mocking
"""

import sys
import os
from pathlib import Path

backend_root = Path(__file__).parent.parent.parent
src_path = backend_root / 'src'
sys.path.insert(0, str(src_path))

os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
os.environ['AWS_SECURITY_TOKEN'] = 'testing'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import uuid
from datetime import datetime
from moto import mock_dynamodb, mock_s3

# Start mocks at session level BEFORE any imports
@pytest.fixture(scope='session', autouse=True)
def setup_moto_mocks():
    """Session-level setup: Start moto mocks before app import."""
    with mock_dynamodb(), mock_s3():
        yield

@pytest.fixture(scope='function')
def client():
    """FastAPI TestClient with mocked AWS services (DynamoDB and S3)."""
    # Apply mocks at function level
    with mock_dynamodb(), mock_s3():
        from app.main import create_app
        app = create_app()
        yield TestClient(app)

@pytest.fixture(scope='function')
def mock_aws_services(client):
    """Registry of mocked AWS services for test assertions."""
    return {'dynamodb': MagicMock(), 's3': MagicMock()}

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
        'alt_text': {'id': 'alt-text', 'impact': 'critical', 'wcag': '1.1.1'},
        'form_label': {'id': 'form-label', 'impact': 'critical', 'wcag': '1.3.1'}
    }

@pytest.fixture(scope='function')
def realistic_html_violations():
    """Provides realistic HTML violation patterns for tests."""
    return {
        'images_without_alt': {
            'explanation': 'Decorative image or missing alt text',
            'html_before': '<img src="decorative.jpg">',
            'html_after': '<img src="decorative.jpg" alt="">',
            'severity': 'high'
        },
        'form_without_labels': {
            'explanation': 'Use semantic HTML elements instead of ARIA role="button" on div',
            'html_before': '<input type="text" placeholder="Enter email">',
            'html_after': '<label>Email<input type="text"></label>',
            'severity': 'high'
        },
        'low_contrast_text': {
            'explanation': 'Color contrast too low',
            'html_before': '<p style="color: #999">Low contrast</p>',
            'html_after': '<p style="color: #000">High contrast</p>',
            'severity': 'high'
        },
        'missing_heading_hierarchy': {
            'explanation': 'Heading hierarchy violated',
            'html_before': '<h1>Title</h1><h3>Subtitle</h3>',
            'html_after': '<h1>Title</h1><h2>Subtitle</h2>',
            'severity': 'medium'
        },
        'aria_misuse': {
            'explanation': 'Use semantic HTML elements instead of ARIA role="button" on div',
            'html_before': '<div role="button">Click</div>',
            'html_after': '<button>Click</button>',
            'severity': 'high'
        }
    }

@pytest.fixture(autouse=True, scope='function')
def mock_dynamodb_tables():
    """Auto-use fixture that ensures DynamoDB is mocked for all tests."""
    scans_db = {
        'test-001': {
            'scan_id': 'test-001',
            'url': 'https://example.com',
            'status': 'completed'
        },
    }
    yield
