"""Integration tests for Task 16: Verification and Before/After Comparison"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.verification import VerificationService, ComparisonResult

client = TestClient(app)


class TestComparisonResult:
    """Tests for ComparisonResult before/after comparison logic"""
    
    def test_fixed_violations_detection(self):
        before = [
            {"finding_id": "f1", "rule_id": "image-alt"},
            {"finding_id": "f2", "rule_id": "color-contrast"},
        ]
        after = [
            {"finding_id": "f2", "rule_id": "color-contrast"},
        ]
        
        comparison = ComparisonResult(before, after)
        assert comparison.fixed_count == 1
        assert comparison.unresolved_count == 1
        assert comparison.new_count == 0
    
    def test_new_violations_detection(self):
        before = [
            {"finding_id": "f1", "rule_id": "image-alt"},
        ]
        after = [
            {"finding_id": "f1", "rule_id": "image-alt"},
            {"finding_id": "f2", "rule_id": "form-label"},
        ]
        
        comparison = ComparisonResult(before, after)
        assert comparison.new_count == 1
        assert comparison.fixed_count == 0
        assert comparison.unresolved_count == 1
    
    def test_all_violations_fixed(self):
        before = [
            {"finding_id": "f1", "rule_id": "image-alt"},
            {"finding_id": "f2", "rule_id": "color-contrast"},
        ]
        after = []
        
        comparison = ComparisonResult(before, after)
        assert comparison.fixed_count == 2
        assert comparison.new_count == 0
        assert comparison.unresolved_count == 0


class TestVerificationService:
    """Tests for VerificationService"""
    
    def test_service_initialization(self):
        service = VerificationService()
        assert service is not None
        assert service.db_client is None
        assert service.scanner is None
    
    def test_compare_findings_method(self):
        service = VerificationService()
        before = [
            {"finding_id": "f1", "rule_id": "image-alt"},
            {"finding_id": "f2", "rule_id": "color-contrast"},
        ]
        after = [
            {"finding_id": "f2", "rule_id": "color-contrast"},
        ]
        
        result = service.compare_findings(before, after)
        assert result["fixed_count"] == 1
        assert result["new_count"] == 0
        assert result["unresolved_count"] == 1


class TestVerificationEndpoint:
    """Tests for GET /api/verification/{scan_id} endpoint"""
    
    def test_get_verification_success(self):
        response = client.get("/api/verification/test-scan-123")
        assert response.status_code == 200
        data = response.json()
        assert "scan_id" in data
        assert data["scan_id"] == "test-scan-123"
    
    def test_get_verification_has_metrics(self):
        response = client.get("/api/verification/test-scan-456")
        assert response.status_code == 200
        data = response.json()
        
        assert "fixed_count" in data
        assert "new_violations_count" in data
        assert "unresolved_count" in data
        assert "comparison" in data
    
    def test_get_verification_counts_are_integers(self):
        response = client.get("/api/verification/test-scan-789")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data["fixed_count"], int)
        assert isinstance(data["new_violations_count"], int)
        assert isinstance(data["unresolved_count"], int)
