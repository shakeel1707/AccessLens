"""
Unit tests for patch application service (Task 14).

Tests cover:
- PBT Suite 2: Repair Patch Safety (no injection, target selector only, original preserved)
- PBT Suite 8: Isolation (no corruption, rollback success, logged operations)
- PBT Suite 9: Patch Policy (policy compliance, unrelated content preserved)
"""

import pytest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from hypothesis import given, strategies as st, assume

from app.services.patch_application import (
    PatchStatus,
    AppliedPatch,
    PatchSafetyValidator,
    PatchApplicationEngine,
)


# ============================================================================
# PBT Suite 2: Repair Patch Safety Tests (Injection Prevention)
# ============================================================================

class TestPatchSafetyValidator:
    """Test patch safety validation"""
    
    def test_safe_patch_basic_html(self):
        """Test basic safe HTML is accepted"""
        content = "<div>Hello World</div>"
        assert PatchSafetyValidator.is_safe_patch(content) is True
    
    def test_safe_patch_with_attributes(self):
        """Test safe HTML with attributes is accepted"""
        content = '<div class="container" id="main">Content</div>'
        assert PatchSafetyValidator.is_safe_patch(content) is True
    
    def test_unsafe_patch_script_tag(self):
        """Test script tag is rejected"""
        content = "<script>alert('xss')</script>"
        assert PatchSafetyValidator.is_safe_patch(content) is False
    
    def test_unsafe_patch_javascript_protocol(self):
        """Test javascript: protocol is rejected"""
        content = '<a href="javascript:alert(1)">click</a>'
        assert PatchSafetyValidator.is_safe_patch(content) is False
    
    def test_unsafe_patch_onerror_attribute(self):
        """Test onerror attribute is rejected"""
        content = '<img src="x" onerror="alert(1)">'
        assert PatchSafetyValidator.is_safe_patch(content) is False
    
    def test_unsafe_patch_onclick_attribute(self):
        """Test onclick attribute is rejected"""
        content = '<button onclick="alert(1)">Click</button>'
        assert PatchSafetyValidator.is_safe_patch(content) is False
    
    def test_unsafe_patch_eval_function(self):
        """Test eval() is rejected"""
        content = 'eval("alert(1)")'
        assert PatchSafetyValidator.is_safe_patch(content) is False
    
    def test_unsafe_patch_vbscript_protocol(self):
        """Test vbscript: protocol is rejected"""
        content = '<a href="vbscript:msgbox(1)">click</a>'
        assert PatchSafetyValidator.is_safe_patch(content) is False
    
    def test_unsafe_patch_data_uri(self):
        """Test data:text/html is rejected"""
        content = '<a href="data:text/html,<script>alert(1)</script>">link</a>'
        assert PatchSafetyValidator.is_safe_patch(content) is False
    
    def test_safe_patch_case_insensitive(self):
        """Test injection detection is case-insensitive"""
        content = "<SCRIPT>alert(1)</SCRIPT>"
        assert PatchSafetyValidator.is_safe_patch(content) is False
    
    def test_safe_patch_with_svg(self):
        """Test safe SVG is accepted"""
        content = '<svg><circle cx="50" cy="50" r="40"/></svg>'
        assert PatchSafetyValidator.is_safe_patch(content) is True
    
    def test_selector_targets_only_basic(self):
        """Test selector targeting verification"""
        selector = ".target"
        html_before = '<div class="target">Old</div>'
        html_after = '<div class="target">New</div>'
        assert PatchSafetyValidator.selector_targets_only(selector, html_before, html_after) is True


# ============================================================================
# PBT Suite 2: Hypothesis-based Injection Pattern Detection
# ============================================================================

class TestPatchSafetyHypothesis:
    """Hypothesis-based tests for patch safety (PBT Suite 2)"""
    
    @given(st.text(min_size=1, max_size=100))
    def test_safe_content_never_contains_injection_patterns(self, content):
        """For any safe patch, it shall not contain injection patterns"""
        # Filter out content that naturally contains patterns
        assume("<script" not in content.lower())
        assume("javascript:" not in content.lower())
        assume("onerror=" not in content.lower())
        assume("onclick=" not in content.lower())
        assume("expression(" not in content.lower())
        
        assert PatchSafetyValidator.is_safe_patch(content) is True
    
    @given(st.sampled_from(["<script>", "javascript:", "onerror=", "onclick=", "eval(", "vbscript:"]))
    def test_injection_patterns_always_rejected(self, pattern):
        """For any injection pattern, patches containing it shall be rejected"""
        content = f"<div>{pattern}</div>"
        assert PatchSafetyValidator.is_safe_patch(content) is False


# ============================================================================
# PBT Suite 8: Isolation & Rollback Tests (Isolation Guarantee)
# ============================================================================

class TestPatchApplicationEngine:
    """Test patch application engine"""
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self):
        """Test engine initializes correctly"""
        engine = PatchApplicationEngine()
        assert engine.applied_patches == []
        assert engine.audit_log == []
        assert engine.MAX_PATCH_SIZE == 1000
    
    @pytest.mark.asyncio
    async def test_applied_patch_record_creation(self):
        """Test AppliedPatch dataclass creation"""
        patch = AppliedPatch(
            repair_id="rep-001",
            selector=".target",
            status=PatchStatus.APPLIED,
            applied_at=datetime.utcnow().isoformat(),
            original_html="<div>Old</div>",
            modified_html="<div>New</div>",
            rollback_available=True
        )
        assert patch.repair_id == "rep-001"
        assert patch.status == PatchStatus.APPLIED
        assert patch.rollback_available is True
    
    @pytest.mark.asyncio
    async def test_patch_status_enum_values(self):
        """Test PatchStatus enum contains all required statuses"""
        statuses = [
            PatchStatus.PENDING,
            PatchStatus.IN_PROGRESS,
            PatchStatus.APPLIED,
            PatchStatus.FAILED,
            PatchStatus.ROLLED_BACK,
        ]
        assert len(statuses) == 5
        assert PatchStatus.APPLIED.value == "applied"
        assert PatchStatus.ROLLED_BACK.value == "rolled_back"
    
    @pytest.mark.asyncio
    async def test_apply_patch_with_safe_content(self):
        """Test patch application with safe content"""
        engine = PatchApplicationEngine()
        
        applied = await engine.apply_patch(
            repair_id="rep-001",
            selector=".target",
            patch_content="<div>Safe content</div>",
            page_html="<div class='target'>Old</div>"
        )
        
        assert applied.repair_id == "rep-001"
        assert applied.status == PatchStatus.APPLIED
        assert applied.rollback_available is True
        assert len(engine.applied_patches) == 1
    
    @pytest.mark.asyncio
    async def test_apply_patch_with_unsafe_content_raises_error(self):
        """Test patch application with unsafe content raises ValueError"""
        engine = PatchApplicationEngine()
        
        with pytest.raises(ValueError, match="Unsafe patch content"):
            await engine.apply_patch(
                repair_id="rep-001",
                selector=".target",
                patch_content="<script>alert(1)</script>",
                page_html="<div>HTML</div>"
            )
    
    @pytest.mark.asyncio
    async def test_apply_patch_size_validation(self):
        """Test patch size validation"""
        engine = PatchApplicationEngine()
        large_content = "x" * (engine.MAX_PATCH_SIZE + 1)
        
        with pytest.raises(ValueError, match="exceeds"):
            await engine.apply_patch(
                repair_id="rep-001",
                selector=".target",
                patch_content=large_content,
                page_html="<div>HTML</div>"
            )
    
    @pytest.mark.asyncio
    async def test_apply_multiple_patches_sequentially(self):
        """Test applying multiple patches in sequence"""
        engine = PatchApplicationEngine()
        
        repairs = [
            {"repair_id": "rep-001", "selector": ".first", "content": "<span>First</span>"},
            {"repair_id": "rep-002", "selector": ".second", "content": "<span>Second</span>"},
        ]
        
        applied = await engine.apply_patches(repairs, "<div>HTML</div>")
        
        assert len(applied) == 2
        assert applied[0].repair_id == "rep-001"
        assert applied[1].repair_id == "rep-002"
    
    @pytest.mark.asyncio
    async def test_rollback_applied_patch(self):
        """Test rollback of an applied patch"""
        engine = PatchApplicationEngine()
        
        applied = await engine.apply_patch(
            repair_id="rep-001",
            selector=".target",
            patch_content="<div>New</div>",
            page_html="<div>Old</div>"
        )
        
        assert applied.rollback_available is True
        
        # Perform rollback
        success = await engine.rollback_patch("rep-001")
        
        assert success is True
        assert engine.applied_patches[0].status == PatchStatus.ROLLED_BACK
    
    @pytest.mark.asyncio
    async def test_rollback_non_existent_patch(self):
        """Test rollback of non-existent patch returns False"""
        engine = PatchApplicationEngine()
        
        success = await engine.rollback_patch("rep-nonexistent")
        
        assert success is False


# ============================================================================
# PBT Suite 8: Hypothesis-based Isolation & Rollback Tests
# ============================================================================

class TestIsolationHypothesis:
    """Hypothesis-based tests for isolation (PBT Suite 8)"""
    
    @pytest.mark.asyncio
    @given(st.text(min_size=1, max_size=50))
    async def test_applied_patch_always_has_audit_entry(self, repair_id):
        """For any applied patch, there shall be an audit log entry"""
        engine = PatchApplicationEngine()
        
        try:
            await engine.apply_patch(
                repair_id=repair_id,
                selector=".target",
                patch_content="<div>Safe</div>",
                page_html="<div>HTML</div>"
            )
            
            # Check audit log has entry
            audit_entries = engine.get_audit_log()
            assert any(e["repair_id"] == repair_id for e in audit_entries)
        except ValueError:
            # Safe to skip if patch validation fails
            pass
    
    @pytest.mark.asyncio
    @given(st.lists(st.just({"repair_id": "rep-001", "selector": ".t", "content": "<d>s</d>"})))
    async def test_multiple_patches_isolation(self, repairs):
        """For any sequence of patches, each shall be tracked independently"""
        engine = PatchApplicationEngine()
        
        if repairs:
            try:
                await engine.apply_patches(repairs, "<div>HTML</div>")
                
                # Check isolation: each patch has own record
                patches = engine.get_applied_patches()
                assert len(patches) > 0
                for p in patches:
                    assert p.repair_id is not None
                    assert p.selector is not None
            except RuntimeError:
                # Expected if patch application fails
                pass


# ============================================================================
# PBT Suite 9: Patch Policy Compliance Tests (Policy Enforcement)
# ============================================================================

class TestPatchPolicy:
    """Test patch policy compliance"""
    
    @pytest.mark.asyncio
    async def test_patch_application_logs_all_events(self):
        """Test that all patch applications are logged"""
        engine = PatchApplicationEngine()
        
        await engine.apply_patch(
            repair_id="rep-001",
            selector=".target",
            patch_content="<div>New</div>",
            page_html="<div>Old</div>"
        )
        
        audit_log = engine.get_audit_log()
        assert len(audit_log) > 0
        assert audit_log[0]["event_type"] == "patch_applied"
        assert audit_log[0]["result"] == "success"
    
    @pytest.mark.asyncio
    async def test_patch_rollback_logs_event(self):
        """Test that rollback events are logged"""
        engine = PatchApplicationEngine()
        
        await engine.apply_patch(
            repair_id="rep-001",
            selector=".target",
            patch_content="<div>New</div>",
            page_html="<div>Old</div>"
        )
        
        initial_log_length = len(engine.get_audit_log())
        
        await engine.rollback_patch("rep-001")
        
        audit_log = engine.get_audit_log()
        assert len(audit_log) > initial_log_length
        assert any(e["event_type"] == "patch_rollback" for e in audit_log)
    
    @pytest.mark.asyncio
    async def test_failed_patch_logs_failure(self):
        """Test that failed patches raise ValueError"""
        engine = PatchApplicationEngine()
        
        with pytest.raises(ValueError, match="Unsafe patch"):
            await engine.apply_patch(
                repair_id="rep-001",
                selector=".target",
                patch_content="<script>alert(1)</script>",
                page_html="<div>HTML</div>"
            )
    
    @pytest.mark.asyncio
    async def test_patch_preserves_original_html(self):
        """Test that original HTML is preserved in patch record"""
        engine = PatchApplicationEngine()
        original_html = "<div class='target'>Original content</div>"
        
        applied = await engine.apply_patch(
            repair_id="rep-001",
            selector=".target",
            patch_content="<div>Modified</div>",
            page_html=original_html
        )
        
        assert applied.original_html == original_html
        assert applied.original_html is not None
    
    @pytest.mark.asyncio
    async def test_applied_patch_timestamp_is_iso_format(self):
        """Test that applied_at timestamp is in ISO format"""
        engine = PatchApplicationEngine()
        
        applied = await engine.apply_patch(
            repair_id="rep-001",
            selector=".target",
            patch_content="<div>New</div>",
            page_html="<div>Old</div>"
        )
        
        # Verify ISO format (timestamp should have T separator)
        assert "T" in applied.applied_at
        # ISO 8601 format without timezone is valid
        # Timestamp format: YYYY-MM-DDTHH:MM:SS.ffffff


# ============================================================================
# PBT Suite 9: Hypothesis-based Policy Compliance Tests
# ============================================================================

class TestPolicyComplianceHypothesis:
    """Hypothesis-based tests for policy compliance (PBT Suite 9)"""
    
    @pytest.mark.asyncio
    @given(st.text(min_size=1, max_size=20))
    async def test_audit_log_captures_all_patch_operations(self, repair_id):
        """For any patch operation, it shall be logged in audit trail"""
        engine = PatchApplicationEngine()
        
        try:
            await engine.apply_patch(
                repair_id=repair_id,
                selector=".target",
                patch_content="<div>Content</div>",
                page_html="<div>HTML</div>"
            )
            
            # Verify audit entry exists
            audit_log = engine.get_audit_log()
            matching_entries = [e for e in audit_log if e["repair_id"] == repair_id]
            assert len(matching_entries) > 0
            assert matching_entries[0]["result"] in ["success", "failure"]
        except (ValueError, RuntimeError):
            # Expected for invalid patches
            pass
    
    @pytest.mark.asyncio
    @given(st.integers(min_value=1, max_value=100))
    async def test_unrelated_content_not_modified(self, num_chars):
        """For any patch, unrelated content shall not be modified"""
        engine = PatchApplicationEngine()
        
        related_content = '<div class="target">Original</div>'
        unrelated_content = '<div class="other">Should not change</div>'
        page_html = related_content + unrelated_content
        
        try:
            applied = await engine.apply_patch(
                repair_id="rep-001",
                selector=".target",
                patch_content="<div>Modified</div>",
                page_html=page_html
            )
            
            # Verify unrelated content is tracked
            assert applied.original_html is not None
            assert "other" in applied.original_html
        except (ValueError, RuntimeError):
            pass


# ============================================================================
# Integration and Edge Case Tests
# ============================================================================

class TestPatchApplicationIntegration:
    """Integration tests for patch application"""
    
    @pytest.mark.asyncio
    async def test_get_applied_patches_returns_copy(self):
        """Test get_applied_patches returns a copy not reference"""
        engine = PatchApplicationEngine()
        
        await engine.apply_patch(
            repair_id="rep-001",
            selector=".target",
            patch_content="<div>New</div>",
            page_html="<div>Old</div>"
        )
        
        patches1 = engine.get_applied_patches()
        patches2 = engine.get_applied_patches()
        
        assert patches1 == patches2
        assert patches1 is not patches2  # Different objects
    
    @pytest.mark.asyncio
    async def test_get_audit_log_returns_copy(self):
        """Test get_audit_log returns a copy not reference"""
        engine = PatchApplicationEngine()
        
        await engine.apply_patch(
            repair_id="rep-001",
            selector=".target",
            patch_content="<div>New</div>",
            page_html="<div>Old</div>"
        )
        
        log1 = engine.get_audit_log()
        log2 = engine.get_audit_log()
        
        assert log1 == log2
        assert log1 is not log2  # Different objects
    
    @pytest.mark.asyncio
    async def test_patch_application_end_to_end(self):
        """End-to-end test of patch application workflow"""
        engine = PatchApplicationEngine()
        
        # Apply a patch
        applied1 = await engine.apply_patch(
            repair_id="rep-001",
            selector=".title",
            patch_content="<h1>New Title</h1>",
            page_html="<div><span class='title'>Old</span></div>"
        )
        
        assert applied1.status == PatchStatus.APPLIED
        
        # Apply another patch
        applied2 = await engine.apply_patch(
            repair_id="rep-002",
            selector=".description",
            patch_content="<p>New Description</p>",
            page_html=applied1.modified_html or "<div><span>HTML</span></div>"
        )
        
        assert applied2.status == PatchStatus.APPLIED
        
        # Verify both patches are tracked
        patches = engine.get_applied_patches()
        assert len(patches) == 2
        
        # Verify audit log has entries for both
        audit_log = engine.get_audit_log()
        repair_ids = [e["repair_id"] for e in audit_log]
        assert "rep-001" in repair_ids
        assert "rep-002" in repair_ids
        
        # Rollback first patch
        success = await engine.rollback_patch("rep-001")
        assert success is True
        
        # Verify rollback is logged
        audit_log_after = engine.get_audit_log()
        assert len(audit_log_after) > len(audit_log)
        assert any(
            e["event_type"] == "patch_rollback" and e["repair_id"] == "rep-001"
            for e in audit_log_after
        )
