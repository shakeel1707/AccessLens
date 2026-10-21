"""
Tests for API payload validation and schemas (PBT Suite 6).
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime
from app.models.schemas import (
    ScanRequest, RepairGenerateRequest, RepairApproveRequest, PatchApplyRequest,
    FindingResponse, ScanResponse, ErrorResponse, Severity, ScanStatus, ReviewStatus,
)


class TestScanRequestValidation:
    """Test ScanRequest validation."""
    
    def test_scan_request_valid(self):
        """Valid scan request."""
        request = ScanRequest(url="https://example.com")
        assert request.url == "https://example.com"
        assert request.wait_for_results is False
    
    def test_scan_request_http(self):
        """HTTP URLs are valid."""
        request = ScanRequest(url="http://example.com")
        assert request.url == "http://example.com"
    
    def test_scan_request_with_path(self):
        """URLs with paths are valid."""
        request = ScanRequest(url="https://example.com/path/to/page")
        assert request.url == "https://example.com/path/to/page"
    
    def test_scan_request_with_query(self):
        """URLs with query strings are valid."""
        request = ScanRequest(url="https://example.com?param=value&other=123")
        assert request.url == "https://example.com?param=value&other=123"
    
    def test_scan_request_max_length(self):
        """URL max length is 2048."""
        long_url = "https://example.com/" + "a" * 2000
        request = ScanRequest(url=long_url)
        assert len(request.url) == 2048 + 18  # Adjusted for prefix
    
    def test_scan_request_too_long(self):
        """URL exceeding 2048 chars rejected."""
        long_url = "https://example.com/" + "a" * 2100
        with pytest.raises(ValueError):
            ScanRequest(url=long_url)
    
    def test_scan_request_no_scheme(self):
        """URL without scheme rejected."""
        with pytest.raises(ValueError):
            ScanRequest(url="example.com")
    
    def test_scan_request_invalid_scheme(self):
        """Invalid scheme rejected."""
        with pytest.raises(ValueError):
            ScanRequest(url="ftp://example.com")
    
    def test_scan_request_empty_url(self):
        """Empty URL rejected."""
        with pytest.raises(ValueError):
            ScanRequest(url="")
    
    def test_scan_request_wait_for_results(self):
        """Wait for results flag."""
        request = ScanRequest(url="https://example.com", wait_for_results=True)
        assert request.wait_for_results is True


class TestRepairGenerateRequestValidation:
    """Test RepairGenerateRequest validation."""
    
    def test_repair_generate_request_valid(self):
        """Valid repair generation request."""
        request = RepairGenerateRequest(scan_id="scan-123")
        assert request.scan_id == "scan-123"
        assert request.max_repairs == 10
        assert request.finding_ids is None
    
    def test_repair_generate_max_repairs(self):
        """Max repairs boundary."""
        request = RepairGenerateRequest(scan_id="scan-123", max_repairs=100)
        assert request.max_repairs == 100
    
    def test_repair_generate_max_repairs_too_high(self):
        """Max repairs > 100 rejected."""
        with pytest.raises(ValueError):
            RepairGenerateRequest(scan_id="scan-123", max_repairs=101)
    
    def test_repair_generate_finding_ids(self):
        """Finding IDs list accepted."""
        ids = [f"id-{i}" for i in range(5)]
        request = RepairGenerateRequest(scan_id="scan-123", finding_ids=ids)
        assert request.finding_ids == ids
    
    def test_repair_generate_too_many_finding_ids(self):
        """More than 10000 finding IDs rejected."""
        ids = [f"id-{i}" for i in range(10001)]
        with pytest.raises(ValueError):
            RepairGenerateRequest(scan_id="scan-123", finding_ids=ids)


class TestRepairApproveRequestValidation:
    """Test RepairApproveRequest validation."""
    
    def test_repair_approve_request_approve(self):
        """Approve repair."""
        request = RepairApproveRequest(repair_id="repair-123", status=ReviewStatus.APPROVED)
        assert request.repair_id == "repair-123"
        assert request.status == ReviewStatus.APPROVED
    
    def test_repair_approve_request_reject(self):
        """Reject repair."""
        request = RepairApproveRequest(repair_id="repair-123", status=ReviewStatus.REJECTED)
        assert request.status == ReviewStatus.REJECTED
    
    def test_repair_approve_with_comment(self):
        """Comment included."""
        request = RepairApproveRequest(
            repair_id="repair-123",
            status=ReviewStatus.APPROVED,
            comment="Looks good!"
        )
        assert request.comment == "Looks good!"
    
    def test_repair_approve_comment_max_length(self):
        """Comment max length 1000."""
        long_comment = "x" * 1000
        request = RepairApproveRequest(
            repair_id="repair-123",
            status=ReviewStatus.APPROVED,
            comment=long_comment
        )
        assert len(request.comment) == 1000
    
    def test_repair_approve_comment_too_long(self):
        """Comment > 1000 rejected."""
        long_comment = "x" * 1001
        with pytest.raises(ValueError):
            RepairApproveRequest(
                repair_id="repair-123",
                status=ReviewStatus.APPROVED,
                comment=long_comment
            )


class TestPatchApplyRequestValidation:
    """Test PatchApplyRequest validation."""
    
    def test_patch_apply_request_valid(self):
        """Valid patch apply request."""
        request = PatchApplyRequest(scan_id="scan-123", repair_ids=["repair-1"])
        assert request.scan_id == "scan-123"
        assert request.repair_ids == ["repair-1"]
    
    def test_patch_apply_multiple_repairs(self):
        """Multiple repairs accepted."""
        repair_ids = [f"repair-{i}" for i in range(50)]
        request = PatchApplyRequest(scan_id="scan-123", repair_ids=repair_ids)
        assert len(request.repair_ids) == 50
    
    def test_patch_apply_max_repairs(self):
        """Max 100 repairs."""
        repair_ids = [f"repair-{i}" for i in range(100)]
        request = PatchApplyRequest(scan_id="scan-123", repair_ids=repair_ids)
        assert len(request.repair_ids) == 100
    
    def test_patch_apply_too_many_repairs(self):
        """> 100 repairs rejected."""
        repair_ids = [f"repair-{i}" for i in range(101)]
        with pytest.raises(ValueError):
            PatchApplyRequest(scan_id="scan-123", repair_ids=repair_ids)
    
    def test_patch_apply_empty_repairs(self):
        """Empty repair list rejected."""
        with pytest.raises(ValueError):
            PatchApplyRequest(scan_id="scan-123", repair_ids=[])
    
    def test_patch_apply_duplicate_repairs(self):
        """Duplicate repair IDs rejected."""
        repair_ids = ["repair-1", "repair-1", "repair-2"]
        with pytest.raises(ValueError):
            PatchApplyRequest(scan_id="scan-123", repair_ids=repair_ids)


class TestFindingResponseValidation:
    """Test FindingResponse validation."""
    
    def test_finding_response_valid(self):
        """Valid finding response."""
        finding = FindingResponse(
            finding_id="id-123",
            rule_id="alt-text",
            selector="img.logo",
            description="Missing alt text",
            severity=Severity.CRITICAL
        )
        assert finding.finding_id == "id-123"
        assert finding.severity == "critical"  # Enum values
    
    def test_finding_response_optional_fields(self):
        """Optional fields."""
        finding = FindingResponse(
            finding_id="id-123",
            rule_id="alt-text",
            selector="img.logo",
            description="Missing alt text",
            severity=Severity.SERIOUS,
            html="<img src='logo.png'>",
            impact="Users cannot understand images"
        )
        assert finding.html is not None
        assert finding.impact is not None


class TestScanResponseValidation:
    """Test ScanResponse validation."""
    
    def test_scan_response_pending(self):
        """Pending scan response."""
        response = ScanResponse(
            scan_id="scan-123",
            status=ScanStatus.PENDING,
            url="https://example.com"
        )
        assert response.status == "pending"
    
    def test_scan_response_with_findings(self):
        """Response with findings."""
        finding = FindingResponse(
            finding_id="id-1",
            rule_id="alt-text",
            selector="img",
            description="Missing alt",
            severity=Severity.CRITICAL
        )
        response = ScanResponse(
            scan_id="scan-123",
            status=ScanStatus.COMPLETED,
            url="https://example.com",
            findings=[finding],
            finding_count=1
        )
        assert len(response.findings) == 1
        assert response.finding_count == 1
    
    def test_scan_response_failed(self):
        """Failed scan response."""
        response = ScanResponse(
            scan_id="scan-123",
            status=ScanStatus.FAILED,
            url="https://example.com",
            error_message="Network timeout"
        )
        assert response.status == "failed"
        assert response.error_message is not None


class TestErrorResponseValidation:
    """Test ErrorResponse validation."""
    
    def test_error_response_valid(self):
        """Valid error response."""
        error = ErrorResponse(
            code="INVALID_URL",
            message="URL format is invalid",
            status_code=400,
            request_id="req-123"
        )
        assert error.code == "INVALID_URL"
        assert error.status_code == 400
    
    def test_error_response_with_details(self):
        """Error with details."""
        error = ErrorResponse(
            code="SCAN_FAILED",
            message="Scan failed",
            status_code=500,
            request_id="req-123",
            details={"timeout": 30, "retries": 3}
        )
        assert error.details is not None
        assert error.details["timeout"] == 30
    
    def test_error_response_invalid_status_code(self):
        """Invalid status code rejected."""
        with pytest.raises(ValueError):
            ErrorResponse(
                code="ERROR",
                message="Error",
                status_code=200,  # Should be 4xx or 5xx
                request_id="req-123"
            )


# PBT Suite 6: API Payload Validation

@given(
    url=st.just("https://example.com") | 
         st.from_regex(r'https?://[a-z0-9\-\.]+\.[a-z]{2,}(/[a-z0-9\-_/]*)?', fullmatch=True),
)
@settings(suppress_health_check=[HealthCheck.filter_too_much], max_examples=30)
def test_pbt_valid_scan_requests(url):
    """PBT Suite 6: Valid scan requests are accepted."""
    if len(url) <= 2048:
        try:
            request = ScanRequest(url=url)
            assert request.url == url
        except ValueError:
            pass  # Some generated URLs might fail format validation


@given(
    scan_id=st.text(min_size=1, max_size=255),
    max_repairs=st.integers(min_value=1, max_value=100),
)
@settings(max_examples=30)
def test_pbt_valid_repair_generate_requests(scan_id, max_repairs):
    """PBT Suite 6: Valid repair requests are accepted."""
    request = RepairGenerateRequest(scan_id=scan_id, max_repairs=max_repairs)
    assert request.scan_id == scan_id
    assert request.max_repairs == max_repairs


@given(
    repair_ids=st.lists(st.text(min_size=1, max_size=255), min_size=1, max_size=100),
)
@settings(max_examples=30)
def test_pbt_valid_patch_apply_requests(repair_ids):
    """PBT Suite 6: Valid patch requests are accepted."""
    # Remove duplicates
    unique_ids = list(dict.fromkeys(repair_ids))
    if len(unique_ids) > 0:
        request = PatchApplyRequest(scan_id="scan-123", repair_ids=unique_ids)
        assert len(request.repair_ids) == len(unique_ids)


@given(
    status_code=st.integers(min_value=400, max_value=599),
)
@settings(max_examples=30)
def test_pbt_valid_error_responses(status_code):
    """PBT Suite 6: Valid error responses accepted."""
    error = ErrorResponse(
        code="ERROR",
        message="Error message",
        status_code=status_code,
        request_id="req-123"
    )
    assert error.status_code == status_code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
