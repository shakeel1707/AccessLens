"""
Unit tests for URL validation and SSRF prevention.
"""

import pytest
from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, settings, HealthCheck
import re

from app.core.validators import URLValidator, ValidationResult, validate_url


class TestURLValidation:
    """Test URL validation logic."""
    
    def test_empty_url(self):
        """Empty URLs should be rejected."""
        validator = URLValidator()
        result = validator.validate("")
        assert result.is_valid is False
        assert "empty" in result.error_message.lower()
    
    def test_url_too_long(self):
        """URLs exceeding 2048 characters should be rejected."""
        validator = URLValidator()
        long_url = "https://example.com/" + "a" * 2100
        result = validator.validate(long_url)
        assert result.is_valid is False
        assert "exceeds maximum length" in result.error_message.lower()
    
    def test_valid_https_url(self):
        """Valid HTTPS URLs should be accepted (without network check for test)."""
        validator = URLValidator()
        with patch('requests.head') as mock_head:
            mock_head.return_value.status_code = 200
            mock_head.return_value.headers = {}
            result = validator.validate("https://example.com")
            assert result.is_valid is True
            assert result.final_url == "https://example.com"
    
    def test_valid_http_url(self):
        """Valid HTTP URLs should be accepted."""
        validator = URLValidator()
        with patch('requests.head') as mock_head:
            mock_head.return_value.status_code = 200
            mock_head.return_value.headers = {}
            result = validator.validate("http://example.com")
            assert result.is_valid is True
    
    def test_invalid_scheme(self):
        """URLs with invalid schemes should be rejected."""
        validator = URLValidator()
        result = validator.validate("ftp://example.com")
        assert result.is_valid is False
        assert "scheme" in result.error_message.lower()
    
    def test_no_scheme(self):
        """URLs without scheme should be rejected."""
        validator = URLValidator()
        result = validator.validate("example.com")
        assert result.is_valid is False
        assert "scheme" in result.error_message.lower()
    
    def test_no_hostname(self):
        """URLs without hostname should be rejected."""
        validator = URLValidator()
        result = validator.validate("https://")
        assert result.is_valid is False
    
    def test_localhost_rejected(self):
        """localhost URLs should be rejected."""
        validator = URLValidator()
        result = validator.validate("http://localhost")
        assert result.is_valid is False
        assert "localhost" in result.error_message.lower()
    
    def test_localhost_dot_localdomain_rejected(self):
        """localhost.localdomain should be rejected."""
        validator = URLValidator()
        result = validator.validate("http://localhost.localdomain")
        assert result.is_valid is False
    
    def test_private_network_127_rejected(self):
        """127.x.x.x addresses should be rejected."""
        validator = URLValidator()
        result = validator.validate("http://127.0.0.1")
        assert result.is_valid is False
        assert "private" in result.error_message.lower()
    
    def test_private_network_10_rejected(self):
        """10.x.x.x addresses should be rejected."""
        validator = URLValidator()
        result = validator.validate("http://10.0.0.1")
        assert result.is_valid is False
        assert "private" in result.error_message.lower()
    
    def test_private_network_172_rejected(self):
        """172.16-31.x.x addresses should be rejected."""
        validator = URLValidator()
        result = validator.validate("http://172.16.0.1")
        assert result.is_valid is False
        assert "private" in result.error_message.lower()
    
    def test_private_network_192_168_rejected(self):
        """192.168.x.x addresses should be rejected."""
        validator = URLValidator()
        result = validator.validate("http://192.168.1.1")
        assert result.is_valid is False
        assert "private" in result.error_message.lower()
    
    def test_ipv6_loopback_rejected(self):
        """IPv6 loopback (::1) should be rejected."""
        validator = URLValidator()
        result = validator.validate("http://[::1]")
        assert result.is_valid is False
        assert "private" in result.error_message.lower()
    
    def test_ipv6_private_rejected(self):
        """IPv6 private addresses should be rejected."""
        validator = URLValidator()
        result = validator.validate("http://[fc00::1]")
        assert result.is_valid is False
        assert "private" in result.error_message.lower()
    
    def test_metadata_endpoint_rejected(self):
        """AWS metadata endpoint should be rejected."""
        validator = URLValidator()
        result = validator.validate("http://169.254.169.254")
        assert result.is_valid is False
        assert "metadata" in result.error_message.lower()
    
    def test_google_metadata_rejected(self):
        """Google Cloud metadata endpoint should be rejected."""
        validator = URLValidator()
        result = validator.validate("http://metadata.google.internal")
        assert result.is_valid is False
        assert "metadata" in result.error_message.lower()


class TestURLRedirects:
    """Test redirect handling."""
    
    def test_no_redirects(self):
        """URLs with no redirects should be validated correctly."""
        validator = URLValidator()
        with patch('requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_head.return_value = mock_response
            
            result = validator.validate("https://example.com")
            assert result.is_valid is True
            assert result.redirect_count == 0
    
    def test_single_redirect(self):
        """URLs with single redirect should be followed."""
        validator = URLValidator()
        with patch('requests.head') as mock_head:
            # First request: redirect
            redirect_response = MagicMock()
            redirect_response.status_code = 301
            redirect_response.headers = {'Location': 'https://example.com/new'}
            
            # Second request: final response
            final_response = MagicMock()
            final_response.status_code = 200
            final_response.headers = {}
            
            mock_head.side_effect = [redirect_response, final_response]
            
            result = validator.validate("https://example.com")
            assert result.is_valid is True
            assert result.redirect_count == 1
            assert result.final_url == "https://example.com/new"
    
    def test_max_redirects_enforced(self):
        """Exceeding max redirects should fail."""
        validator = URLValidator(max_redirects=2)
        with patch('requests.head') as mock_head:
            redirect_response = MagicMock()
            redirect_response.status_code = 301
            redirect_response.headers = {'Location': 'https://example.com/redirect'}
            mock_head.return_value = redirect_response
            
            result = validator.validate("https://example.com")
            assert result.is_valid is False
            assert "too many redirects" in result.error_message.lower()
    
    def test_redirect_loop_detection(self):
        """Redirect loops should be detected."""
        validator = URLValidator()
        with patch('requests.head') as mock_head:
            redirect_response = MagicMock()
            redirect_response.status_code = 301
            redirect_response.headers = {'Location': 'https://example.com'}  # Loop back
            mock_head.return_value = redirect_response
            
            result = validator.validate("https://example.com")
            assert result.is_valid is False
            assert "loop" in result.error_message.lower()
    
    def test_relative_redirect_handling(self):
        """Relative redirects should be handled correctly."""
        validator = URLValidator()
        with patch('requests.head') as mock_head:
            redirect_response = MagicMock()
            redirect_response.status_code = 301
            redirect_response.headers = {'Location': '/new-path'}  # Relative
            
            final_response = MagicMock()
            final_response.status_code = 200
            final_response.headers = {}
            
            mock_head.side_effect = [redirect_response, final_response]
            
            result = validator.validate("https://example.com/old")
            assert result.is_valid is True
            assert "/new-path" in result.final_url
    
    def test_redirect_to_private_network_blocked(self):
        """Redirects to private networks should be blocked."""
        validator = URLValidator()
        with patch('requests.head') as mock_head:
            redirect_response = MagicMock()
            redirect_response.status_code = 301
            redirect_response.headers = {'Location': 'http://192.168.1.1/'}
            mock_head.return_value = redirect_response
            
            result = validator.validate("https://example.com")
            assert result.is_valid is False
            assert "blocked" in result.error_message.lower() or "private" in result.error_message.lower()


class TestAllowlist:
    """Test allowlist functionality."""
    
    def test_empty_allowlist_uses_blocklist(self):
        """Empty allowlist should use SSRF blocklist."""
        validator = URLValidator(allowed_domains=[])
        result = validator.validate("http://localhost")
        assert result.is_valid is False
    
    def test_allowlist_exact_match(self):
        """URLs matching allowlist should be accepted."""
        validator = URLValidator(allowed_domains=["example.com"])
        with patch('requests.head') as mock_head:
            mock_head.return_value.status_code = 200
            mock_head.return_value.headers = {}
            result = validator.validate("https://example.com")
            assert result.is_valid is True
    
    def test_allowlist_rejects_non_matching(self):
        """URLs not in allowlist should be rejected."""
        validator = URLValidator(allowed_domains=["example.com"])
        result = validator.validate("https://other.com")
        assert result.is_valid is False
        assert "not in the allowed list" in result.error_message
    
    def test_allowlist_wildcard_subdomain(self):
        """Wildcard subdomains should be supported."""
        validator = URLValidator(allowed_domains=["*.example.com"])
        with patch('requests.head') as mock_head:
            mock_head.return_value.status_code = 200
            mock_head.return_value.headers = {}
            
            result = validator.validate("https://api.example.com")
            assert result.is_valid is True
    
    def test_allowlist_wildcard_deep_subdomain(self):
        """Wildcards should support deep subdomains."""
        validator = URLValidator(allowed_domains=["*.example.com"])
        with patch('requests.head') as mock_head:
            mock_head.return_value.status_code = 200
            mock_head.return_value.headers = {}
            
            result = validator.validate("https://deep.api.example.com")
            assert result.is_valid is True
    
    def test_allowlist_with_port(self):
        """Allowlist should work with ports."""
        validator = URLValidator(allowed_domains=["example.com"])
        with patch('requests.head') as mock_head:
            mock_head.return_value.status_code = 200
            mock_head.return_value.headers = {}
            
            result = validator.validate("https://example.com:8443/path")
            assert result.is_valid is True


class TestEdgeCases:
    """Test edge cases."""
    
    def test_url_with_authentication(self):
        """URLs with authentication should be handled."""
        validator = URLValidator()
        with patch('requests.head') as mock_head:
            mock_head.return_value.status_code = 200
            mock_head.return_value.headers = {}
            result = validator.validate("https://user:pass@example.com")
            assert result.is_valid is True
    
    def test_url_with_port(self):
        """URLs with explicit ports should be handled."""
        validator = URLValidator()
        with patch('requests.head') as mock_head:
            mock_head.return_value.status_code = 200
            mock_head.return_value.headers = {}
            result = validator.validate("https://example.com:8443")
            assert result.is_valid is True
    
    def test_url_with_path(self):
        """URLs with paths should be handled."""
        validator = URLValidator()
        with patch('requests.head') as mock_head:
            mock_head.return_value.status_code = 200
            mock_head.return_value.headers = {}
            result = validator.validate("https://example.com/api/v1/endpoint")
            assert result.is_valid is True
    
    def test_url_with_query_string(self):
        """URLs with query strings should be handled."""
        validator = URLValidator()
        with patch('requests.head') as mock_head:
            mock_head.return_value.status_code = 200
            mock_head.return_value.headers = {}
            result = validator.validate("https://example.com?param=value&other=123")
            assert result.is_valid is True
    
    def test_url_with_fragment(self):
        """URLs with fragments should be handled."""
        validator = URLValidator()
        with patch('requests.head') as mock_head:
            mock_head.return_value.status_code = 200
            mock_head.return_value.headers = {}
            result = validator.validate("https://example.com#section")
            assert result.is_valid is True
    
    def test_connection_error_handling(self):
        """Connection errors should not cause validation to fail."""
        validator = URLValidator()
        with patch('requests.head') as mock_head:
            import requests
            mock_head.side_effect = requests.exceptions.ConnectionError("Connection refused")
            
            result = validator.validate("https://unreachable.example.com")
            # Should still be valid (domain itself is not blocked)
            assert result.is_valid is True
    
    def test_timeout_handling(self):
        """Request timeouts should be handled gracefully."""
        validator = URLValidator(redirect_timeout=1.0)
        with patch('requests.head') as mock_head:
            import requests
            mock_head.side_effect = requests.exceptions.Timeout()
            
            result = validator.validate("https://slow.example.com")
            assert result.is_valid is False
            assert "timed out" in result.error_message.lower()


@given(
    url_host=st.just("example.com") | st.sampled_from(["api.example.com", "test.example.com"]),
    scheme=st.just("https") | st.just("http"),
)
@settings(suppress_health_check=[HealthCheck.filter_too_much], max_examples=20)
def test_pbt_valid_urls(url_host, scheme):
    """Property-based test: valid public URLs should pass validation."""
    validator = URLValidator()
    url = f"{scheme}://{url_host}/path?query=1"
    
    with patch('requests.head') as mock_head:
        mock_head.return_value.status_code = 200
        mock_head.return_value.headers = {}
        
        result = validator.validate(url)
        assert result.is_valid is True


@given(
    private_ip=st.sampled_from([
        "127.0.0.1", "192.168.1.1", "10.0.0.1", "172.16.0.1"
    ])
)
@settings(max_examples=20)
def test_pbt_private_ips_rejected(private_ip):
    """Property-based test: private IPs should always be rejected."""
    validator = URLValidator()
    url = f"http://{private_ip}/path"
    
    result = validator.validate(url)
    assert result.is_valid is False
    assert "private" in result.error_message.lower()


# Convenience function tests
def test_validate_url_convenience_function():
    """Test the convenience validate_url function."""
    with patch('requests.head') as mock_head:
        mock_head.return_value.status_code = 200
        mock_head.return_value.headers = {}
        
        result = validate_url("https://example.com")
        assert result.is_valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
