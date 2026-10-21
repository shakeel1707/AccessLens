"""
Unit tests and PBT for finding ID generation and deduplication service.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from app.services.finding_service import (
    Finding,
    Severity,
    FindingIDGenerator,
    FindingDeduplicator,
    FindingSortingService,
    FindingProcessingPipeline,
)


class TestFindingIDGenerator:
    """Test SHA256-based finding ID generation."""
    
    def test_generate_id_basic(self):
        """Basic ID generation."""
        finding_id = FindingIDGenerator.generate_id("alt-text", "img.logo", "Missing alt text")
        assert finding_id is not None
        assert len(finding_id) == 64  # SHA256 hex is 64 chars
        assert all(c in "0123456789abcdef" for c in finding_id)
    
    def test_generate_id_deterministic(self):
        """Same input produces same ID (deterministic)."""
        id1 = FindingIDGenerator.generate_id("alt-text", "img.logo", "Missing alt text")
        id2 = FindingIDGenerator.generate_id("alt-text", "img.logo", "Missing alt text")
        assert id1 == id2
    
    def test_generate_id_different_inputs(self):
        """Different inputs produce different IDs."""
        id1 = FindingIDGenerator.generate_id("alt-text", "img.logo", "Missing alt text")
        id2 = FindingIDGenerator.generate_id("alt-text", "img.other", "Missing alt text")
        assert id1 != id2
    
    def test_generate_id_unicode(self):
        """Unicode characters handled correctly."""
        finding_id = FindingIDGenerator.generate_id("règle", "élément", "Description français")
        assert len(finding_id) == 64
        assert all(c in "0123456789abcdef" for c in finding_id)
    
    def test_generate_id_empty_fields(self):
        """Empty or None fields handled gracefully."""
        id1 = FindingIDGenerator.generate_id("", "img.logo", "Missing")
        id2 = FindingIDGenerator.generate_id(None, "img.logo", "Missing")
        assert id1 == id2  # None and "" should be treated the same
    
    def test_generate_id_all_empty(self):
        """All empty fields."""
        finding_id = FindingIDGenerator.generate_id("", "", "")
        assert len(finding_id) == 64
    
    def test_generate_from_finding(self):
        """Generate ID from Finding object."""
        finding = Finding(
            finding_id="",
            rule_id="alt-text",
            selector="img.logo",
            description="Missing alt text",
            severity=Severity.CRITICAL
        )
        finding_id = FindingIDGenerator.generate_from_finding(finding)
        expected = FindingIDGenerator.generate_id("alt-text", "img.logo", "Missing alt text")
        assert finding_id == expected


class TestDeduplication:
    """Test finding deduplication."""
    
    def test_deduplicate_no_duplicates(self):
        """No duplicates in list."""
        findings = [
            Finding("id1", "rule1", "sel1", "desc1", Severity.CRITICAL),
            Finding("id2", "rule2", "sel2", "desc2", Severity.SERIOUS),
        ]
        result = FindingDeduplicator.deduplicate(findings)
        assert len(result) == 2
        assert result == findings
    
    def test_deduplicate_exact_duplicates(self):
        """Remove exact duplicate IDs."""
        findings = [
            Finding("id1", "rule1", "sel1", "desc1", Severity.CRITICAL),
            Finding("id1", "rule1", "sel1", "desc1", Severity.CRITICAL),
            Finding("id2", "rule2", "sel2", "desc2", Severity.SERIOUS),
        ]
        result = FindingDeduplicator.deduplicate(findings)
        assert len(result) == 2
        assert result[0].finding_id == "id1"
        assert result[1].finding_id == "id2"
    
    def test_deduplicate_preserves_first_occurrence(self):
        """Keep first occurrence, discard later ones."""
        findings = [
            Finding("id1", "rule1", "sel1", "desc1", Severity.CRITICAL),
            Finding("id2", "rule2", "sel2", "desc2", Severity.SERIOUS),
            Finding("id1", "rule1", "sel1", "desc1", Severity.CRITICAL),
        ]
        result = FindingDeduplicator.deduplicate(findings)
        assert len(result) == 2
        assert result[0].finding_id == "id1"
        assert result[1].finding_id == "id2"
    
    def test_deduplicate_empty_list(self):
        """Handle empty list."""
        result = FindingDeduplicator.deduplicate([])
        assert result == []
    
    def test_deduplicate_single_finding(self):
        """Single finding returns as is."""
        findings = [Finding("id1", "rule1", "sel1", "desc1", Severity.CRITICAL)]
        result = FindingDeduplicator.deduplicate(findings)
        assert result == findings


class TestSeveritySorting:
    """Test sorting findings by severity."""
    
    def test_sort_all_severities(self):
        """Sort all severity levels correctly."""
        findings = [
            Finding("id1", "rule1", "sel1", "desc1", Severity.MINOR),
            Finding("id2", "rule2", "sel2", "desc2", Severity.CRITICAL),
            Finding("id3", "rule3", "sel3", "desc3", Severity.MODERATE),
            Finding("id4", "rule4", "sel4", "desc4", Severity.SERIOUS),
        ]
        result = FindingSortingService.sort_by_severity(findings)
        assert result[0].severity == Severity.CRITICAL
        assert result[1].severity == Severity.SERIOUS
        assert result[2].severity == Severity.MODERATE
        assert result[3].severity == Severity.MINOR
    
    def test_sort_stable_within_severity(self):
        """Stable sort preserves order within same severity."""
        findings = [
            Finding("id1", "rule1", "sel1", "desc1", Severity.CRITICAL),
            Finding("id2", "rule2", "sel2", "desc2", Severity.CRITICAL),
            Finding("id3", "rule3", "sel3", "desc3", "CRITICAL"),
        ]
        result = FindingSortingService.sort_by_severity(findings)
        assert result[0].finding_id == "id1"
        assert result[1].finding_id == "id2"
    
    def test_sort_empty_list(self):
        """Handle empty list."""
        result = FindingSortingService.sort_by_severity([])
        assert result == []
    
    def test_sort_single_finding(self):
        """Single finding returns as is."""
        findings = [Finding("id1", "rule1", "sel1", "desc1", Severity.CRITICAL)]
        result = FindingSortingService.sort_by_severity(findings)
        assert result == findings
    
    def test_sort_by_severity_then_selector(self):
        """Sort by severity first, then selector."""
        findings = [
            Finding("id1", "rule1", "zzz", "desc1", Severity.SERIOUS),
            Finding("id2", "rule2", "aaa", "desc2", Severity.SERIOUS),
            Finding("id3", "rule3", "bbb", "desc3", Severity.CRITICAL),
        ]
        result = FindingSortingService.sort_by_severity_then_selector(findings)
        assert result[0].severity == Severity.CRITICAL
        assert result[1].selector == "aaa"  # Before "zzz"
        assert result[2].selector == "zzz"


class TestFindingProcessingPipeline:
    """Test complete processing pipeline."""
    
    def test_process_generates_ids(self):
        """Pipeline generates missing IDs."""
        findings = [
            Finding("", "alt-text", "img.logo", "Missing alt", Severity.CRITICAL),
        ]
        result = FindingProcessingPipeline.process(findings)
        assert result[0].finding_id != ""
        assert len(result[0].finding_id) == 64
    
    def test_process_deduplicates(self):
        """Pipeline deduplicates."""
        findings = [
            Finding("id1", "rule1", "sel1", "desc1", Severity.CRITICAL),
            Finding("id1", "rule1", "sel1", "desc1", Severity.CRITICAL),
        ]
        result = FindingProcessingPipeline.process(findings)
        assert len(result) == 1
    
    def test_process_sorts(self):
        """Pipeline sorts by severity."""
        findings = [
            Finding("id1", "rule1", "sel1", "desc1", Severity.MINOR),
            Finding("id2", "rule2", "sel2", "desc2", Severity.CRITICAL),
        ]
        result = FindingProcessingPipeline.process(findings)
        assert result[0].severity == Severity.CRITICAL
        assert result[1].severity == Severity.MINOR
    
    def test_process_full_pipeline(self):
        """Full pipeline: generate, deduplicate, sort."""
        findings = [
            Finding("", "rule1", "sel1", "desc1", Severity.MINOR),
            Finding("", "rule1", "sel1", "desc1", Severity.MINOR),
            Finding("id2", "rule2", "sel2", "desc2", Severity.CRITICAL),
        ]
        result = FindingProcessingPipeline.process(findings)
        # 1. Generate IDs for first two (same content = same ID)
        # 2. Deduplicate (keeps one)
        # 3. Sort (critical first)
        assert len(result) == 2
        assert result[0].severity == Severity.CRITICAL
        assert result[1].severity == Severity.MINOR


# PBT Suite 1: Finding Structure
@given(
    rule_id=st.text(min_size=1, max_size=50),
    selector=st.text(min_size=1, max_size=100),
    description=st.text(min_size=1, max_size=200),
)
@settings(suppress_health_check=[HealthCheck.filter_too_much], max_examples=50)
def test_pbt_finding_id_deterministic(rule_id, selector, description):
    """PBT Suite 1: ID generation is deterministic."""
    id1 = FindingIDGenerator.generate_id(rule_id, selector, description)
    id2 = FindingIDGenerator.generate_id(rule_id, selector, description)
    assert id1 == id2


@given(
    rule_id1=st.text(min_size=1),
    selector1=st.text(min_size=1),
    description1=st.text(min_size=1),
    rule_id2=st.text(min_size=1),
    selector2=st.text(min_size=1),
    description2=st.text(min_size=1),
)
@settings(suppress_health_check=[HealthCheck.filter_too_much], max_examples=50)
def test_pbt_finding_id_uniqueness(rule_id1, selector1, description1, rule_id2, selector2, description2):
    """PBT Suite 1: Different inputs produce different IDs (with high probability)."""
    combined1 = f"{rule_id1}||{selector1}||{description1}"
    combined2 = f"{rule_id2}||{selector2}||{description2}"
    assume(combined1 != combined2)
    
    id1 = FindingIDGenerator.generate_id(rule_id1, selector1, description1)
    id2 = FindingIDGenerator.generate_id(rule_id2, selector2, description2)
    assert id1 != id2


# PBT Suite 5: Deduplication
@given(st.lists(
    st.builds(
        Finding,
        finding_id=st.text(min_size=1, max_size=64),
        rule_id=st.text(min_size=1),
        selector=st.text(min_size=1),
        description=st.text(min_size=1),
        severity=st.sampled_from(list(Severity)),
    ),
    min_size=0,
    max_size=10,
))
@settings(max_examples=50)
def test_pbt_deduplication_is_idempotent(findings):
    """PBT Suite 5: Deduplication is idempotent."""
    deduplicated_once = FindingDeduplicator.deduplicate(findings)
    deduplicated_twice = FindingDeduplicator.deduplicate(deduplicated_once)
    assert deduplicated_once == deduplicated_twice


@given(st.lists(
    st.builds(
        Finding,
        finding_id=st.text(min_size=1, max_size=64),
        rule_id=st.text(min_size=1),
        selector=st.text(min_size=1),
        description=st.text(min_size=1),
        severity=st.sampled_from(list(Severity)),
    ),
    min_size=0,
    max_size=10,
))
@settings(max_examples=50)
def test_pbt_deduplication_preserves_unique(findings):
    """PBT Suite 5: All unique findings preserved."""
    unique_findings = {f.finding_id: f for f in findings}
    if len(unique_findings) < len(findings):
        assume(False)  # Skip if no duplicates
    
    deduplicated = FindingDeduplicator.deduplicate(findings)
    assert len(deduplicated) == len(unique_findings)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
