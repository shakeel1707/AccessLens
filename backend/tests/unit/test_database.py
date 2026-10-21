"""
Unit tests for DynamoDB models and access layer.
"""

import pytest
from app.models.database import (
    ScanModel, ScanStatus, FindingModel, Severity, RepairModel, 
    ReviewStatus, VerificationResultModel
)


def test_scan_model_creation():
    """Test ScanModel creation with defaults."""
    scan = ScanModel(url="https://example.com", user_id="test-user")
    assert scan.url == "https://example.com"
    assert scan.user_id == "test-user"
    assert scan.status == ScanStatus.PENDING
    assert scan.finding_count == 0
    assert scan.scan_id is not None


def test_scan_model_to_dynamodb():
    """Test ScanModel conversion to DynamoDB format."""
    scan = ScanModel(url="https://example.com")
    item = scan.to_dynamodb_item()
    assert "scan_id" in item
    assert "url" in item
    assert item["status"] == "pending"


def test_scan_model_status_enum():
    """Test ScanStatus enum values."""
    assert ScanStatus.PENDING.value == "pending"
    assert ScanStatus.IN_PROGRESS.value == "in_progress"
    assert ScanStatus.COMPLETED.value == "completed"
    assert ScanStatus.FAILED.value == "failed"


def test_finding_model_creation():
    """Test FindingModel creation."""
    finding = FindingModel(
        scan_id="scan-123",
        finding_id="finding-456",
        rule_id="image-alt",
        severity=Severity.CRITICAL,
        selector="img#logo",
        description="Missing alt text"
    )
    assert finding.scan_id == "scan-123"
    assert finding.rule_id == "image-alt"
    assert finding.severity == Severity.CRITICAL


def test_finding_model_to_dynamodb():
    """Test FindingModel conversion to DynamoDB."""
    finding = FindingModel(
        scan_id="scan-123",
        finding_id="finding-456",
        rule_id="image-alt",
        severity=Severity.SERIOUS,
        selector="img",
        description="Missing alt"
    )
    item = finding.to_dynamodb_item()
    assert item["rule_id"] == "image-alt"
    assert item["severity"] == "serious"


def test_severity_enum():
    """Test Severity enum values."""
    assert Severity.CRITICAL.value == "critical"
    assert Severity.SERIOUS.value == "serious"
    assert Severity.MODERATE.value == "moderate"
    assert Severity.MINOR.value == "minor"


def test_repair_model_creation():
    """Test RepairModel creation."""
    repair = RepairModel(
        scan_id="scan-123",
        finding_id="finding-456",
        rule_id="image-alt",
        file_type="html",
        proposed_patch="<img alt=\"Logo\" src=\"/logo.png\">",
        confidence="high"
    )
    assert repair.scan_id == "scan-123"
    assert repair.file_type == "html"
    assert repair.confidence == "high"
    assert repair.review_status == ReviewStatus.PENDING


def test_repair_model_to_dynamodb():
    """Test RepairModel conversion."""
    repair = RepairModel(
        scan_id="scan-123",
        finding_id="finding-456",
        rule_id="image-alt",
        file_type="html",
        proposed_patch="fix",
        confidence="medium"
    )
    item = repair.to_dynamodb_item()
    assert item["review_status"] == "pending"
    assert item["confidence"] == "medium"


def test_verification_model_creation():
    """Test VerificationResultModel creation."""
    result = VerificationResultModel(
        scan_id="scan-123",
        fixed_count=3,
        new_violations_count=1,
        unresolved_count=2
    )
    assert result.scan_id == "scan-123"
    assert result.fixed_count == 3
    assert result.new_violations_count == 1
    assert result.unresolved_count == 2


def test_verification_model_to_dynamodb():
    """Test VerificationResultModel conversion."""
    result = VerificationResultModel(
        scan_id="scan-123",
        fixed_count=5,
        new_violations_count=0,
        unresolved_count=1,
        before_findings=["f1", "f2"],
        after_findings=["f1", "f2", "f3"]
    )
    item = result.to_dynamodb_item()
    assert item["fixed_count"] == 5
    assert len(item["before_findings"]) == 2