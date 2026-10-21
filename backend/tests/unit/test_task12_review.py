"""Unit tests for Task 12: Repair Review Endpoint"""
import pytest
from app.models.schemas import RepairApproveRequest, RepairApproveResponse, ReviewStatus
from app.models.database import RepairModel
from datetime import datetime

class TestRepairReviewRequest:
    def test_approve_repair_request_valid(self):
        request = RepairApproveRequest(
            repair_id="repair-123",
            status=ReviewStatus.APPROVED,
            comment="Looks good"
        )
        assert request.repair_id == "repair-123"
        assert request.status == ReviewStatus.APPROVED
    
    def test_reject_repair_request_valid(self):
        request = RepairApproveRequest(
            repair_id="repair-456",
            status=ReviewStatus.REJECTED,
            comment="Needs review"
        )
        assert request.repair_id == "repair-456"
        assert request.status == ReviewStatus.REJECTED
    
    def test_pending_status_request_valid(self):
        request = RepairApproveRequest(
            repair_id="repair-789",
            status=ReviewStatus.PENDING
        )
        assert request.status == ReviewStatus.PENDING

class TestRepairApproveResponse:
    def test_approve_response_format(self):
        response = RepairApproveResponse(
            repair_id="repair-123",
            status=ReviewStatus.APPROVED,
            message="Repair approved"
        )
        assert response.repair_id == "repair-123"
        assert response.status == ReviewStatus.APPROVED
    
    def test_reject_response_format(self):
        response = RepairApproveResponse(
            repair_id="repair-456",
            status=ReviewStatus.REJECTED,
            message="Repair rejected"
        )
        assert response.status == ReviewStatus.REJECTED

class TestRepairModel:
    def test_repair_model_review_status(self):
        repair = RepairModel(
            scan_id="scan-123",
            repair_id="repair-123",
            finding_id="finding-456",
            rule_id="image-alt",
            file_type="html",
            proposed_patch="alt='desc'",
            confidence="high",
            review_status=ReviewStatus.PENDING
        )
        assert repair.review_status == ReviewStatus.PENDING
    
    def test_repair_model_comment_field(self):
        repair = RepairModel(
            scan_id="scan-123",
            repair_id="repair-123",
            finding_id="finding-456",
            rule_id="color-contrast",
            file_type="css",
            proposed_patch="color: #000",
            confidence="medium",
            review_status=ReviewStatus.APPROVED,
            reviewer_comment="Approved"
        )
        assert repair.reviewer_comment == "Approved"

class TestCommentCapture:
    def test_approval_comment_captured(self):
        request = RepairApproveRequest(
            repair_id="repair-123",
            status=ReviewStatus.APPROVED,
            comment="Works great"
        )
        assert "Works" in request.comment
    
    def test_rejection_comment_captured(self):
        request = RepairApproveRequest(
            repair_id="repair-456",
            status=ReviewStatus.REJECTED,
            comment="Needs change"
        )
        assert "change" in request.comment

class TestAuditTrail:
    def test_approval_timestamp_recorded(self):
        now = datetime.utcnow().isoformat()
        repair = RepairModel(
            scan_id="scan-123",
            repair_id="repair-123",
            finding_id="finding-456",
            rule_id="aria-required-attr",
            file_type="html",
            proposed_patch='aria-label="btn"',
            confidence="high",
            review_status=ReviewStatus.APPROVED,
            created_at=now,
            reviewed_at=now
        )
        assert repair.reviewed_at is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
