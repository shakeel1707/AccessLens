"""
PBT Suite 5: Deduplication - Testing that duplicates are removed and output is deterministic
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, seed
from app.services.finding_service import FindingIDGenerator

# Finding data generators
finding_data = st.tuples(
    st.sampled_from(["alt-text", "contrast", "heading", "labels"]),
    st.sampled_from(["img", "button", "h1", "input"]),
    st.text(min_size=1, max_size=100)
)

class FindingDeduplicator:
    """Simple deduplicator for testing."""

    @staticmethod
    def deduplicate(findings):
        """Remove duplicates and return sorted results."""
        seen = {}
        for finding in findings:
            finding_id = FindingIDGenerator.generate_id(
                finding[0], finding[1], finding[2]
            )
            seen[finding_id] = finding
        return sorted(seen.values(), key=lambda x: FindingIDGenerator.generate_id(x[0], x[1], x[2]))

class TestPBTSuite5Deduplication:
    """PBT Suite 5: Deduplication validation."""

    @given(
        findings=st.lists(finding_data, min_size=1, max_size=20)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @seed(46)
    def test_deduplication_removes_duplicates(self, findings):
        """Invariant: Deduplication removes exact duplicates."""
        # Create findings with intentional duplicates
        findings_with_dupes = findings + findings[:len(findings)//2]

        deduplicated = FindingDeduplicator.deduplicate(findings_with_dupes)

        # Check all results are unique
        unique_ids = set()
        for finding in deduplicated:
            finding_id = FindingIDGenerator.generate_id(finding[0], finding[1], finding[2])
            assert finding_id not in unique_ids, f"Duplicate not removed: {finding_id}"
            unique_ids.add(finding_id)

    @given(
        findings=st.lists(finding_data, min_size=1, max_size=20)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @seed(46)
    def test_deduplication_deterministic(self, findings):
        """Invariant: Deduplication produces same output for same input."""
        deduplicated1 = FindingDeduplicator.deduplicate(findings)
        deduplicated2 = FindingDeduplicator.deduplicate(findings)
        deduplicated3 = FindingDeduplicator.deduplicate(findings)

        # Convert to IDs for comparison
        ids1 = [FindingIDGenerator.generate_id(f[0], f[1], f[2]) for f in deduplicated1]
        ids2 = [FindingIDGenerator.generate_id(f[0], f[1], f[2]) for f in deduplicated2]
        ids3 = [FindingIDGenerator.generate_id(f[0], f[1], f[2]) for f in deduplicated3]

        assert ids1 == ids2 == ids3, "Deduplication output not deterministic"

    @given(
        findings=st.lists(finding_data, min_size=0, max_size=20)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @seed(46)
    def test_deduplication_preserves_originals(self, findings):
        """Invariant: Deduplication preserves original findings (no data loss)."""
        deduplicated = FindingDeduplicator.deduplicate(findings)

        # All unique findings should still be present
        original_ids = set()
        for finding in findings:
            finding_id = FindingIDGenerator.generate_id(finding[0], finding[1], finding[2])
            original_ids.add(finding_id)

        result_ids = set()
        for finding in deduplicated:
            finding_id = FindingIDGenerator.generate_id(finding[0], finding[1], finding[2])
            result_ids.add(finding_id)

        assert original_ids == result_ids, "Deduplication lost data"

    @given(
        findings=st.lists(finding_data, min_size=1, max_size=20)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @seed(46)
    def test_deduplication_output_sorted(self, findings):
        """Invariant: Deduplication output is deterministically sorted."""
        deduplicated = FindingDeduplicator.deduplicate(findings)

        # Verify output is sorted by ID
        ids = [FindingIDGenerator.generate_id(f[0], f[1], f[2]) for f in deduplicated]
        assert ids == sorted(ids), "Deduplication output not sorted"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
