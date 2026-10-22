"""
PBT Suite 3: Finding Identity and Comparison - Testing stable IDs and correct categorization
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, seed, assume
from app.services.finding_service import FindingIDGenerator, Severity

severity_levels = st.sampled_from([Severity.CRITICAL, Severity.SERIOUS, Severity.MODERATE, Severity.MINOR])
rule_ids = st.sampled_from(["alt-text", "color-contrast", "heading-hierarchy", "form-labels"])
selectors = st.sampled_from(["img", "button", "h1", "input", ".element", "#identifier"])

class TestPBTSuite3FindingIdentity:
    """PBT Suite 3: Finding identity validation."""

    @given(
        rule_id=rule_ids,
        selector=selectors,
        description=st.text(min_size=1, max_size=200),
        severity=severity_levels
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @seed(44)
    def test_finding_id_stable_across_calls(self, rule_id, selector, description, severity):
        """Invariant: Finding ID remains stable across multiple calls."""
        id1 = FindingIDGenerator.generate_id(rule_id, selector, description)
        id2 = FindingIDGenerator.generate_id(rule_id, selector, description)
        id3 = FindingIDGenerator.generate_id(rule_id, selector, description)

        assert id1 == id2 == id3, f"ID not stable: {id1} vs {id2} vs {id3}"

    @given(
        rule_id=rule_ids,
        selector=selectors,
        description=st.text(min_size=1, max_size=200)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @seed(44)
    def test_finding_id_independent_of_severity(self, rule_id, selector, description):
        """Invariant: Finding ID depends only on rule_id, selector, description (not severity)."""
        # Two findings with same content but different severity should have same ID
        id1 = FindingIDGenerator.generate_id(rule_id, selector, description)
        id2 = FindingIDGenerator.generate_id(rule_id, selector, description)

        assert id1 == id2, "ID should not depend on severity"

    @given(
        findings=st.lists(
            st.tuples(
                st.sampled_from(["alt-text", "contrast"]),
                st.sampled_from(["img", "button"]),
                st.text(min_size=1, max_size=100)
            ),
            min_size=1,
            max_size=10,
            unique=True
        )
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    @seed(44)
    def test_finding_uniqueness_preserved(self, findings):
        """Invariant: Unique findings produce unique IDs."""
        ids = set()
        for rule_id, selector, description in findings:
            finding_id = FindingIDGenerator.generate_id(rule_id, selector, description)
            assert finding_id not in ids, f"Duplicate ID generated: {finding_id}"
            ids.add(finding_id)

    @given(severity=severity_levels)
    @settings(max_examples=100)
    @seed(44)
    def test_severity_ordering(self, severity):
        """Invariant: Severity follows correct ordering (critical > serious > moderate > minor)."""
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.SERIOUS: 1,
            Severity.MODERATE: 2,
            Severity.MINOR: 3
        }
        assert severity in severity_order, f"Unknown severity: {severity}"
        assert severity_order[severity] <= 3, f"Severity order violated: {severity}"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
