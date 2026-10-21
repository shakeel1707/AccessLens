"""Integration tests for Task 15: Patch Application Endpoint"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from app.main import app
from app.models.schemas import PatchApplyRequest

client = TestClient(app)


class TestPatchEndpoint:
    """Tests for POST /api/patch/apply endpoint"""
    
    def test_apply_patches_success(self):
        """Test successful patch application dispatch"""
        request_body = {
            "scan_id": "test-scan-123",
            "repair_ids": ["repair-1", "repair-2", "repair-3"]
        }
        
        response = client.post("/api/patch/apply", json=request_body)
        
        assert response.status_code == 202
        data = response.json()
        assert data["scan_id"] == "test-scan-123"
        assert data["application_status"] == "in_progress"
        assert "message" in data
    
    def test_apply_patches_empty_repairs(self):
        """Test error when repair_ids is empty"""
        request_body = {
            "scan_id": "test-scan-123",
            "repair_ids": []
        }
        
        response = client.post("/api/patch/apply", json=request_body)
        
        assert response.status_code == 422
    
    def test_apply_patches_too_many_repairs(self):
        """Test error when repair_ids exceeds max"""
        request_body = {
            "scan_id": "test-scan-123",
            "repair_ids": [f"repair-{i}" for i in range(101)]
        }
        
        response = client.post("/api/patch/apply", json=request_body)
        
        assert response.status_code == 422
    
    def test_apply_patches_duplicate_repairs(self):
        """Test error when repair_ids contain duplicates"""
        request_body = {
            "scan_id": "test-scan-123",
            "repair_ids": ["repair-1", "repair-1", "repair-2"]
        }
        
        response = client.post("/api/patch/apply", json=request_body)
        
        assert response.status_code == 422
    
    def test_apply_patches_response_schema(self):
        """Test response matches PatchApplyResponse schema"""
        request_body = {
            "scan_id": "test-scan-123",
            "repair_ids": ["repair-1"]
        }
        
        response = client.post("/api/patch/apply", json=request_body)
        
        assert response.status_code == 202
        data = response.json()
        assert "scan_id" in data
        assert "applied_count" in data
        assert "failed_count" in data
        assert "application_status" in data
        assert "message" in data
    
    def test_apply_patches_single_repair(self):
        """Test with single repair"""
        request_body = {
            "scan_id": "scan-001",
            "repair_ids": ["repair-single"]
        }
        
        response = client.post("/api/patch/apply", json=request_body)
        
        assert response.status_code == 202
        data = response.json()
        assert data["scan_id"] == "scan-001"
    
    def test_apply_patches_max_repairs(self):
        """Test with maximum allowed repairs"""
        request_body = {
            "scan_id": "scan-max",
            "repair_ids": [f"repair-{i}" for i in range(100)]
        }
        
        response = client.post("/api/patch/apply", json=request_body)
        
        assert response.status_code == 202
    
    def test_apply_patches_missing_scan_id(self):
        """Test error when scan_id is missing"""
        request_body = {
            "repair_ids": ["repair-1"]
        }
        
        response = client.post("/api/patch/apply", json=request_body)
        
        assert response.status_code == 422
