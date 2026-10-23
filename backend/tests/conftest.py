import sys
from pathlib import Path

# Add src to path so imports work
backend_root = Path(__file__).parent.parent
src_path = backend_root / 'src'
sys.path.insert(0, str(src_path))

pytest_plugins = ('pytest_asyncio',)

# E2E Test Fixtures
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

@pytest.fixture
def client():
    from app.main import create_app
    app = create_app()
    return TestClient(app)

@pytest.fixture
def mock_aws_services():
    return {}

@pytest.fixture
def sample_scan_data():
    return {'scan_id': 'test-001'}
