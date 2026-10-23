"""
Shared fixtures for E2E tests with simple mocking.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import os
import json

# Add src to path
backend_root = Path(__file__).parent.parent.parent
src_path = backend_root / 'src'
sys.path.insert(0, str(src_path))

# Set dummy AWS credentials to avoid credential errors
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"

from fastapi.testclient import TestClient

@pytest.fixture(scope="session")
def anyio_backend():
    """Set async backend for pytest-asyncio"""
    return "asyncio"

@pytest.fixture
def mock_aws_services(monkeypatch):
    """Mock AWS services for E2E tests"""
    mock_dynamodb = MagicMock()
    mock_s3 = MagicMock()
    mock_bedrock = MagicMock()
    
    mock_dynamodb.get_item.return_value = {
        'Item': {'scan_id': 'test-scan-001', 'status': 'completed'}
    }
    mock_dynamodb.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
    
    mock_s3.put_object.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
    mock_s3.get_object.return_value = {'Body': MagicMock(read=lambda: b'test')}
    
    return {'dynamodb': mock_dynamodb, 's3': mock_s3, 'bedrock': mock_bedrock}

@pytest.fixture
def client(monkeypatch):
    """FastAPI test client with mocked database"""
    # Mock boto3 to avoid real AWS calls
    mock_boto3 = MagicMock()
    mock_dynamodb_client = MagicMock()
    mock_s3_client = MagicMock()
    
    mock_boto3.client.side_effect = lambda service, **kwargs: {
        'dynamodb': mock_dynamodb_client,
        's3': mock_s3_client
    }.get(service, MagicMock())
    
    mock_boto3.resource.side_effect = lambda service, **kwargs: {
        'dynamodb': MagicMock(Table=lambda name: MagicMock()),
        's3': MagicMock()
    }.get(service, MagicMock())
    
    monkeypatch.setitem(__import__('sys').modules, 'boto3', mock_boto3)
    
    from app.main import app
    return TestClient(app)

@pytest.fixture
def sample_scan_data():
    """Sample scan data for E2E tests"""
    return {
        "scan_id": "scan-e2e-001",
        "user_id": "user-e2e-001",
        "url": "https://example.com",
        "status": "completed",
        "findings_count": 2,
        "timestamp": 1700000000
    }

@pytest.fixture
def sample_findings_data():
    """Sample accessibility findings"""
    return [
        {
            "finding_id": "finding-1",
            "scan_id": "scan-e2e-001",
            "type": "missing_alt_text",
            "element": "<img src='test.jpg' />",
            "severity": "high",
            "wcag_criteria": "1.1.1",
            "message": "Image missing alt text",
            "impact": "Users with visual impairments cannot understand image content"
        },
        {
            "finding_id": "finding-2",
            "scan_id": "scan-e2e-001",
            "type": "low_contrast",
            "element": "<p style='color: #888; background: #fff;'>Text</p>",
            "severity": "medium",
            "wcag_criteria": "1.4.3",
            "message": "Text contrast ratio is 4.48:1, needs to be at least 4.5:1",
            "impact": "Users with low vision may struggle to read the text"
        }
    ]

@pytest.fixture
def sample_repair_data():
    """Sample repair proposals"""
    return [
        {
            "repair_id": "repair-1",
            "finding_id": "finding-1",
            "scan_id": "scan-e2e-001",
            "description": "Add descriptive alt text",
            "repair_code": "<img src='test.jpg' alt='Sample image' />",
            "confidence": 0.95,
            "explanation": "Added descriptive alt text",
            "status": "pending_review"
        }
    ]
