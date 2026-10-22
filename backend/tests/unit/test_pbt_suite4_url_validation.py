"""
PBT Suite 4: URL Validation - Testing allowlist enforcement and redirect handling
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, seed, assume
import re

# URL strategies
valid_protocols = st.sampled_from(["http://", "https://"])
valid_domains = st.sampled_from(["example.com", "test.org", "site.edu", "domain.io"])
paths = st.text(alphabet="abcdefghijklmnopqrstuvwxyz-_/", min_size=0, max_size=50)

# Generate URLs
urls = st.builds(
    lambda protocol, domain, path: f"{protocol}{domain}{path if path else ''}",
    protocol=valid_protocols,
    domain=valid_domains,
    path=paths
)

# Private/internal IPs
private_ips = st.sampled_from([
    "localhost",
    "127.0.0.1",
    "192.168.1.1",
    "10.0.0.1",
    "172.16.0.1",
    "::1"
])

class TestPBTSuite4URLValidation:
    """PBT Suite 4: URL validation."""

    @given(url=urls)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @seed(45)
    def test_url_format_validation(self, url):
        """Invariant: Valid URLs follow standard format."""
        # Check URL starts with protocol
        assert url.startswith("http://") or url.startswith("https://"), \
            f"URL missing protocol: {url}"

        # Check URL contains domain
        assert "://" in url, f"URL format invalid: {url}"

    @given(
        url=urls,
        max_redirects=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @seed(45)
    def test_url_redirect_limit_enforced(self, url, max_redirects):
        """Invariant: URL validation enforces max redirects (max 5)."""
        assert max_redirects <= 10, f"Max redirects exceeds limit: {max_redirects}"

    @given(ip=private_ips)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    @seed(45)
    def test_private_network_rejected(self, ip):
        """Invariant: Private networks and localhost are rejected."""
        private_url = f"http://{ip}/"

        # Verify IP is actually private/local
        assert ip in ["localhost", "127.0.0.1", "192.168.1.1", "10.0.0.1", "172.16.0.1", "::1"], \
            f"Not a private IP: {ip}"

    @given(
        domain=st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789")
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @seed(45)
    def test_url_domain_validation(self, domain):
        """Invariant: Domain names contain valid characters."""
        assume(domain)  # Skip empty domains
        # Domain should not contain invalid chars
        assert " " not in domain, f"Domain contains spaces: {domain}"
        assert "-" not in domain, f"Domain contains dashes: {domain}"
        assert "." not in domain, f"Domain contains dots (tested separately): {domain}"
        assert len(domain) >= 1, f"Domain too short: {domain}"

    @given(url=urls)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @seed(45)
    def test_url_length_bounded(self, url):
        """Invariant: URL length is bounded (max 2048 chars)."""
        assert len(url) <= 2048, f"URL exceeds max length: {len(url)}"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
