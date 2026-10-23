"""
Shared fixtures for E2E tests with AWS mocking setup.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import json

# Add src to path
backend_root = Path(__file__).parent.parent.parent
src_path = backend_root / 'src'
sys.path.insert(0, str(src_path))

from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import (
    ScanModel, FindingModel, RepairModel, PatchModel, ReportModel
)


@pytest.fixture(scope="session")
def anyio_backend():
    """Set async backend for pytest-asyncio"""
    return "asyncio"


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_aws_services(monkeypatch):
    """Mock AWS services (DynamoDB, S3, Bedrock)"""
    
    # Mock DynamoDB responses
    mock_dynamodb = MagicMock()
    mock_dynamodb.get_item.return_value = {
        'Item': {
            'scan_id': {'S': 'test-scan-001'},
            'user_id': {'S': 'test-user'},
            'url': {'S': 'https://example.com'},
            'status': {'S': 'completed'},
            'findings': {'SS': ['finding-1', 'finding-2']},
            'timestamp': {'N': '1700000000'}
        }
    }
    mock_dynamodb.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
    mock_dynamodb.update_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
    mock_dynamodb.query.return_value = {'Items': []}
    
    # Mock S3 responses
    mock_s3 = MagicMock()
    mock_s3.put_object.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
    mock_s3.get_object.return_value = {
        'Body': MagicMock(read=lambda: b'{"report": "data"}')
    }
    
    # Mock Bedrock responses
    mock_bedrock = MagicMock()
    mock_bedrock.invoke_model.return_value = {
        'body': MagicMock(read=lambda: json.dumps({
            'content': [{
                'text': json.dumps({
                    'repairs': [
                        {
                            'finding_id': 'finding-1',
                            'repair_id': 'repair-1',
                            'description': 'Add alt text to image',
                            'confidence': 0.95,
                            'patch': '<img src="test.jpg" alt="Test image" />'
                        }
                    ]
                })
            }]
        }).encode())
    }
    
    # Patch boto3 clients
    monkeypatch.setattr(
        'boto3.client',
        lambda service, **kwargs: {
            'dynamodb': mock_dynamodb,
            's3': mock_s3,
            'bedrock-runtime': mock_bedrock
        }.get(service, MagicMock())
    )
    
    return {
        'dynamodb': mock_dynamodb,
        's3': mock_s3,
        'bedrock': mock_bedrock
    }


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
            "repair_code": "<img src='test.jpg' alt='Sample image showing accessibility guidelines' />",
            "confidence": 0.95,
            "explanation": "Added descriptive alt text that conveys the image's purpose",
            "status": "pending_review"
        },
        {
            "repair_id": "repair-2",
            "finding_id": "finding-2",
            "scan_id": "scan-e2e-001",
            "description": "Increase text contrast",
            "repair_code": "<p style='color: #333; background: #fff;'>Text</p>",
            "confidence": 0.88,
            "explanation": "Changed text color from #888 to #333 to meet WCAG 4.5:1 ratio",
            "status": "pending_review"
        }
    ]


@pytest.fixture
def mock_playwright_scanner(monkeypatch):
    """Mock Playwright browser scanner"""
    
    async def mock_scan_website(url: str):
        return [
            {
                "type": "missing_alt_text",
                "element": "<img src='test.jpg' />",
                "severity": "high",
                "wcag_criteria": "1.1.1",
                "message": "Image missing alt text"
            },
            {
                "type": "low_contrast",
                "element": "<p style='color: #888; background: #fff;'>Text</p>",
                "severity": "medium",
                "wcag_criteria": "1.4.3",
                "message": "Text contrast ratio is 4.48:1, needs to be at least 4.5:1"
            }
        ]
    
    monkeypatch.setattr(
        'app.services.scanner.scan_website',
        mock_scan_website
    )


@pytest.fixture
def mock_bedrock_repair_generator(monkeypatch):
    """Mock Bedrock repair generation"""
    
    async def mock_generate_repairs(findings: list):
        return [
            {
                "repair_id": f"repair-{i}",
                "finding_id": finding.get("finding_id"),
                "description": f"Repair for {finding.get('type')}",
                "repair_code": "<repair>fixed</repair>",
                "confidence": 0.90,
                "explanation": "Auto-generated repair using Bedrock"
            }
            for i, finding in enumerate(findings)
        ]
    
    monkeypatch.setattr(
        'app.services.repair_generator.generate_repairs',
        mock_generate_repairs
    )
