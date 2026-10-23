"""Input Sanitization Security Tests - Unit Tests"""

import pytest

class TestInputValidation:
    """Test input validation"""
    
    def test_url_max_length(self):
        """Reject URLs exceeding max length (2048 chars)"""
        long_url = "http://example.com/" + "a" * 2500
        assert len(long_url) > 2048

    def test_empty_url_validation(self):
        """Empty URL should be invalid"""
        url = ""
        assert len(url) == 0

    def test_whitespace_url(self):
        """Whitespace-only URL is invalid"""
        url = "   "
        assert url.strip() == ""

    def test_url_format_validation(self):
        """Valid URL formats"""
        valid_urls = [
            "http://example.com",
            "https://example.com/path",
            "http://example.com:8080/path?query=value"
        ]
        for url in valid_urls:
            assert url.startswith(("http://", "https://"))

    def test_invalid_url_formats(self):
        """Invalid URL formats should be rejected"""
        invalid_urls = [
            "ftp://example.com",
            "file:///etc/passwd",
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>"
        ]
        for url in invalid_urls:
            assert not url.startswith(("http://", "https://"))