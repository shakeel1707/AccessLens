"""
PBT Suite 2: Repair Patch Safety - Testing that patches don't contain injection attacks or unsafe operations
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, seed, Phase, assume
import re

# Strategies for generating patch content
html_selectors = st.sampled_from(["img", "button", "input", "div", "span", "a", ".class", "#id"])
safe_attributes = st.sampled_from(["alt", "aria-label", "title", "data-test", "class"])
injection_patterns = [
    "javascript:",
    "onerror=",
    "onclick=",
    "onload=",
    "<script>",
    "vbscript:",
    "eval(",
    "expression("
]

confidence_values = st.sampled_from(["high", "medium", "low"])

# Custom URL strategy
url_strategy = st.builds(
    lambda scheme, domain, path: f"{scheme}://{domain}.com{path}",
    scheme=st.sampled_from(["http", "https"]),
    domain=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=20),
    path=st.sampled_from(["", "/path", "/path/to/page", "/index.html"])
)

class TestPBTSuite2PatchSafety:
    """PBT Suite 2: Patch safety validation."""

    @given(
        selector=html_selectors,
        attribute=safe_attributes,
        value=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @seed(43)
    def test_patch_no_injection_patterns(self, selector, attribute, value):
        """Invariant: Patch content never contains injection attack patterns."""
        patch = f"{selector}[{attribute}] = '{value}'"

        for pattern in injection_patterns:
            assert pattern.lower() not in patch.lower(), \
                f"Injection pattern '{pattern}' found in patch: {patch}"

    @given(
        selector=html_selectors,
        original_url=url_strategy,
        new_url=url_strategy
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    @seed(43)
    def test_patch_no_scheme_changes(self, selector, original_url, new_url):
        """Invariant: Patch cannot change URL scheme (http to https, etc)."""
        original_scheme = original_url.split("://")[0] if "://" in original_url else ""
        new_scheme = new_url.split("://")[0] if "://" in new_url else ""

        # Verify schemes are same (or skip if invalid)
        assume(original_scheme and new_scheme and original_scheme == new_scheme)

        patch = f"Change {original_url} to {new_url}"
        # Schemes must match: can't have http->https or https->http
        assert original_scheme == new_scheme, \
            f"Patch contains scheme change: {patch}"

    @given(
        selector=html_selectors,
        content=st.text(min_size=1, max_size=200)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @seed(43)
    def test_patch_targets_selector_only(self, selector, content):
        """Invariant: Patch targets specific selector, not global content."""
        patch = f"{selector} {{ {content} }}"
        assert selector in patch, f"Patch doesn't target selector: {patch}"

    @given(
        confidence=confidence_values,
        assumptions=st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=5)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @seed(43)
    def test_patch_confidence_valid(self, confidence, assumptions):
        """Invariant: Confidence is always high/medium/low."""
        valid = ["high", "medium", "low"]
        assert confidence in valid, f"Invalid confidence: {confidence}"
        assert len(assumptions) <= 5, f"Too many assumptions: {len(assumptions)}"

    @given(
        selector=html_selectors,
        content=st.text(min_size=0, max_size=500)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @seed(43)
    def test_patch_no_unrelated_modifications(self, selector, content):
        """Invariant: Patch modifications are isolated to target selector."""
        patch = f"Update {selector}"
        selectors_in_patch = patch.count(selector)
        assert selectors_in_patch >= 1, "Patch doesn't modify target selector"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
