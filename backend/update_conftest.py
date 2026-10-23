import_code = '''"""
Shared fixtures for E2E tests with AWS mocking setup using Moto.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import json
from moto import mock_dynamodb, mock_s3, mock_bedrock_runtime

# Add src to path
backend_root = Path(__file__).parent.parent.parent
src_path = backend_root / 'src'
sys.path.insert(0, str(src_path))

from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="session")
def anyio_backend():
    """Set async backend for pytest-asyncio"""
    return "asyncio"

@pytest.fixture
@mock_dynamodb
@mock_s3
@mock_bedrock_runtime
def client():
    """FastAPI test client with mocked AWS services"""
    return TestClient(app)

@pytest.fixture
def mock_aws_services(monkeypatch):
    """Mock AWS services (DynamoDB, S3, Bedrock)"""
    
    # Mock DynamoDB responses
    mock_dynamodb_obj = MagicMock()
    mock_dynamodb_obj.get_item.return_value = {
        'Item': {
            'scan_id': {'S': 'test-scan-001'},
            'user_id': {'S': 'test-user'},
            'url': {'S': 'https://example.com'},
            'status': {'S': 'completed'},
            'findings': {'SS': ['finding-1', 'finding-2']},
            'timestamp': {'N': '1700000000'}
        }
    }
    mock_dynamodb_obj.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
    mock_dynamodb_obj.update_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
    mock_dynamodb_obj.query.return_value = {'Items': []}
    
    # Mock S3 responses
    mock_s3_obj = MagicMock()
    mock_s3_obj.put_object.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
    mock_s3_obj.get_object.return_value = {
        'Body': MagicMock(read=lambda: b'{"report": "data"}')
    }
    
    # Mock Bedrock responses
    mock_bedrock_obj = MagicMock()
    mock_bedrock_obj.invoke_model.return_value = {
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
    
    return {
        'dynamodb': mock_dynamodb_obj,
        's3': mock_s3_obj,
        'bedrock': mock_bedrock_obj
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
'''

# Read original file
with open("tests/e2e/conftest.py", "r") as f:
    content = f.read()

# Find where to cut off (before the fixtures) and replace imports and early fixtures
import re
match = re.search(r"(@pytest\.fixture\(scope=\"session\"\))", content)
if match:
    pos = content.rfind("\n", 0, match.start()) + 1
    new_content = import_code + content[pos:]
    
    with open("tests/e2e/conftest.py", "w") as f:
        f.write(new_content)
    print("Updated conftest.py with moto decorators")
else:
    print("Could not find fixtures in conftest")
