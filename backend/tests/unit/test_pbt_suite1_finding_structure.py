"""
PBT Suite 1: Finding Structure - Testing ID generation determinism and severity validation
Uses Hypothesis to generate diverse finding inputs and verify invariants.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, seed, Phase
from app.services.finding_service import FindingIDGenerator, Severity

# Strategy for generating valid finding data
finding_rule_id = st.sampled_from(["alt-text", "color-contrast", "heading-hierarchy", "form-labels", "aria-hidden"])
finding_selector = st.sampled_from(["img.logo", "button#submit", ".container", "h1", "input[type=text]"])
finding_description = st.text(min_size=1, max_size=200)

# Strategy for severity values
severity_strategy = st.sampled_from([Severity.CRITICAL, Severity.SERIOUS, Severity.MODERATE, Severity.MINOR])

class TestPBTSuite1FindingStructure:
    """PBT Suite 1: Finding Structure validation."""

    @given(
        rule_id=finding_rule_id,
        selector=finding_selector,
        description=finding_description
    )
    @settings(
        max_examples=100,
        phases=[Phase.generate, Phase.shrink],
        suppress_health_check=[HealthCheck.too_slow]
    )
    @seed(42)  # Reproducible seed
    def test_finding_id_deterministic(self, rule_id, selector, description):
        """Invariant: Same input always produces same ID (deterministic)."""
        id1 = FindingIDGenerator.generate_id(rule_id, selector, description)
        id2 = FindingIDGenerator.generate_id(rule_id, selector, description)
        assert id1 == id2, f"ID generation not deterministic for ({rule_id}, {selector}, {description})"

    @given(
        rule_id=finding_rule_id,
        selector=finding_selector,
        description=finding_description
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @seed(42)
    def test_finding_id_format(self, rule_id, selector, description):
        """Invariant: ID is always 64-char SHA256 hex string."""
        finding_id = FindingIDGenerator.generate_id(rule_id, selector, description)
        assert len(finding_id) == 64, f"ID length not 64: {finding_id}"
        assert all(c in "0123456789abcdef" for c in finding_id), f"ID contains non-hex chars: {finding_id}"

    @given(
        rule_id1=finding_rule_id,
        selector1=finding_selector,
        description1=finding_description,
        rule_id2=finding_rule_id,
        selector2=finding_selector,
        description2=finding_description
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    @seed(42)
    def test_finding_id_collision_resistance(self, rule_id1, selector1, description1, rule_id2, selector2, description2):
        """Invariant: Different inputs produce different IDs (collision resistance)."""
        if (rule_id1, selector1, description1) != (rule_id2, selector2, description2):
            id1 = FindingIDGenerator.generate_id(rule_id1, selector1, description1)
            id2 = FindingIDGenerator.generate_id(rule_id2, selector2, description2)
            assert id1 != id2, f"Collision detected: {(rule_id1, selector1, description1)} vs {(rule_id2, selector2, description2)}"

    @given(severity=severity_strategy)
    @settings(max_examples=100)
    @seed(42)
    def test_severity_valid_values(self, severity):
        """Invariant: Severity is always one of 4 valid values."""
        valid_severities = [Severity.CRITICAL, Severity.SERIOUS, Severity.MODERATE, Severity.MINOR]
        assert severity in valid_severities, f"Invalid severity: {severity}"

    @given(
        rule_id=finding_rule_id,
        selector=finding_selector,
        description=st.text(min_size=0, max_size=500)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @seed(42)
    def test_finding_id_length_invariant(self, rule_id, selector, description):
        """Invariant: ID length is always 64 regardless of input length."""
        finding_id = FindingIDGenerator.generate_id(rule_id, selector, description)
        assert len(finding_id) == 64, f"ID length varies with input: {len(finding_id)}"

# Test execution with reproducible seed
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
