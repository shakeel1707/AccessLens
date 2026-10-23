import sys
from pathlib import Path

backend_root = Path(__file__).parent.parent
src_path = backend_root / 'src'
sys.path.insert(0, str(src_path))

pytest_plugins = ('pytest_asyncio',)

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import uuid
from datetime import datetime

@pytest.fixture
def client():
    from app.main import create_app
    app = create_app()
    return TestClient(app)

@pytest.fixture
def mock_aws_services():
    return {
        'dynamodb': MagicMock(),
        'bedrock': MagicMock(),
        's3': MagicMock()
    }

@pytest.fixture
def sample_scan_data():
    return {
        'scan_id': f'test-{uuid.uuid4().hex[:8]}',
        'url': 'https://example.com',
        'user_id': 'test-user-001',
        'status': 'completed',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }

@pytest.fixture
def sample_findings():
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

@pytest.fixture
def sample_repairs():
    return [
        {
            'id': f'repair-{uuid.uuid4().hex[:8]}',
            'finding_id': 'finding-1',
            'repair_type': 'add_attribute',
            'code_before': '<img src="photo.jpg">',
            'code_after': '<img src="photo.jpg" alt="Product">'
        }
    ]

@pytest.fixture
def mock_axe_findings():
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

@pytest.fixture
def realistic_html_violations():
    return {
        'images_without_alt': {'type': 'alt_text', 'wcag': '1.1.1'},
        'form_without_labels': {'type': 'form_label', 'wcag': '1.3.1'}
    }

    
@pytest.fixture(autouse=True)
def mock_dynamodb_tables(monkeypatch):
    scans_db = {
        'test-001': {'scan_id': 'test-001', 'url': 'https://example.com', 'status': 'completed'},
        # ... (all scan IDs)
    }

    yield
