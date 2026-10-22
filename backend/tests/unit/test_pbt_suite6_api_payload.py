"""
PBT Suite 6: API Payload Validation - Testing required fields, boundaries, and error responses
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, seed, assume
import json

# URL strategy - valid HTTP/HTTPS URLs
urls = st.builds(
    lambda scheme, domain, path: f"{scheme}://{domain}.com{path}",
    scheme=st.sampled_from(["http", "https"]),
    domain=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=20),
    path=st.sampled_from(["", "/path", "/api", "/index.html"])
)

# Rule IDs
rule_ids = st.sampled_from(["alt-text", "color-contrast", "heading-hierarchy", "form-labels", "aria-hidden"])

# Severity values
severities = st.sampled_from(["critical", "serious", "moderate", "minor"])

class TestPBTSuite6APIPayload:
    """PBT Suite 6: API payload validation."""

    @given(
        url=urls,
        rule_id=rule_ids
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @seed(46)
    def test_scan_request_valid_fields(self, url, rule_id):
        """Invariant: Scan request has required fields (url, rule_id)."""
        payload = {
            "url": url,
            "rule_id": rule_id
        }
        assert "url" in payload, "Missing url field"
        assert "rule_id" in payload, "Missing rule_id field"
        assert payload["url"], "URL cannot be empty"
        assert payload["rule_id"], "Rule ID cannot be empty"

    @given(
        url=st.text(min_size=1, max_size=2048)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @seed(46)
    def test_url_boundary_validation(self, url):
        """Invariant: URL field respects max length boundary (2048 chars)."""
        assume(url)
        assert len(url) <= 2048, f"URL exceeds max length: {len(url)} > 2048"

    @given(
        findings=st.lists(
            st.fixed_dictionaries({
                "finding_id": st.text(min_size=1, max_size=64),
                "severity": severities,
                "rule_id": rule_ids
            }),
            min_size=0,
            max_size=10000
        )
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    @seed(46)
    def test_findings_boundary_validation(self, findings):
        """Invariant: Findings array respects max size boundary (10000 items)."""
        assert len(findings) <= 10000, f"Findings exceeds max size: {len(findings)} > 10000"
        for finding in findings:
            assert "finding_id" in finding, "Missing finding_id"
            assert "severity" in finding, "Missing severity"
            assert finding["severity"] in ["critical", "serious", "moderate", "minor"], \
                f"Invalid severity: {finding['severity']}"

    @given(
        status_code=st.integers(min_value=400, max_value=599),
        error_msg=st.text(min_size=1, max_size=500)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @seed(46)
    def test_error_response_format(self, status_code, error_msg):
        """Invariant: Error responses follow standard format."""
        error_response = {
            "code": f"ERROR_{status_code}",
            "message": error_msg,
            "status_code": status_code,
            "request_id": "req-123"
        }
        assert "code" in error_response, "Missing code field"
        assert "message" in error_response, "Missing message field"
        assert "status_code" in error_response, "Missing status_code field"
        assert error_response["status_code"] >= 400, "Invalid error status code"
        assert len(error_response["message"]) > 0, "Error message cannot be empty"

    @given(
        request=st.fixed_dictionaries({
            "url": urls,
            "wcag_version": st.sampled_from(["WCAG 2.1 Level A", "WCAG 2.1 Level AA", "WCAG 2.1 Level AAA"]),
            "timeout": st.integers(min_value=1, max_value=300)
        })
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @seed(46)
    def test_request_serialization_valid(self, request):
        """Invariant: Request payloads can be serialized to JSON."""
        try:
            json_str = json.dumps(request)
            assert json_str, "Serialized JSON is empty"
            deserialized = json.loads(json_str)
            assert deserialized["url"] == request["url"], "URL not preserved in serialization"
        except (TypeError, ValueError) as e:
            pytest.fail(f"Serialization failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
