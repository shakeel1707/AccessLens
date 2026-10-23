"""SSRF Prevention Security Tests - Unit Tests"""

import pytest
import sys
from pathlib import Path

backend_root = Path(__file__).parent.parent.parent
src_path = backend_root / 'src'
sys.path.insert(0, str(src_path))

from app.core.validators import URLValidator

@pytest.fixture
def validator():
    """Create URLValidator instance with test config"""
    return URLValidator(
        allowed_domains=["example.com", "google.com"],
        max_redirects=5,
        redirect_timeout=5.0
    )

class TestSSRFLocalhost:
    """Test rejection of localhost addresses"""
    
    def test_localhost_direct(self, validator):
        """Reject direct localhost access"""
        result = validator.validate("http://localhost:8000/admin")
        assert not result.is_valid

    def test_localhost_127_0_0_1(self, validator):
        """Reject 127.0.0.1 loopback"""
        result = validator.validate("http://127.0.0.1:8000/")
        assert not result.is_valid

    def test_localhost_0_0_0_0(self, validator):
        """Reject 0.0.0.0 address"""
        result = validator.validate("http://0.0.0.0:8080/")
        assert not result.is_valid

class TestSSRFPrivateNetworks:
    """Test rejection of private IP ranges"""
    
    def test_private_10_network(self, validator):
        """Reject 10.0.0.0/8 private range"""
        result = validator.validate("http://10.0.0.1/")
        assert not result.is_valid

    def test_private_172_network(self, validator):
        """Reject 172.16.0.0/12 private range"""
        result = validator.validate("http://172.16.0.1/")
        assert not result.is_valid

    def test_private_192_network(self, validator):
        """Reject 192.168.0.0/16 private range"""
        result = validator.validate("http://192.168.0.1/")
        assert not result.is_valid

class TestSSRFAllowlist:
    """Test allowlist enforcement"""
    
    def test_allowed_domain_accepted(self, validator):
        """Accept URLs from allowlist"""
        result = validator.validate("http://example.com/page")
        assert result.is_valid

    def test_non_allowlist_rejected(self, validator):
        """Reject URLs not on allowlist"""
        result = validator.validate("http://evil.com/")
        assert not result.is_valid