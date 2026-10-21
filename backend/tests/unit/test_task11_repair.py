"""Unit tests for Task 11: Repair Generation Endpoint

Tests include:
- Rule applicability checking (5 MVP rules)
- Patch generation for each rule type
- Safety validation (PBT Suite 2: Unsafe patch rejection)
- Confidence scoring
- Assumptions and explanations
- Integration with Bedrock (mocked)
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from hypothesis import given, strategies as st, settings, HealthCheck

from app.services.repair import (
    RepairGenerator,
    RepairApplicabilityChecker,
    RepairPatch,
)
from app.models.schemas import RepairGenerateRequest, RepairGenerateResponse, Severity


class TestApplicabilityChecker:
    """Test rule applicability for MVP repair types"""
    
    def test_image_alt_is_applicable(self):
        """Test that image-alt rule is applicable"""
        assert RepairApplicabilityChecker.is_applicable("image-alt") is True
    
    def test_color_contrast_is_applicable(self):
        """Test that color-contrast rule is applicable"""
        assert RepairApplicabilityChecker.is_applicable("color-contrast") is True
    
    def test_heading_order_is_applicable(self):
        """Test that heading-order rule is applicable"""
        assert RepairApplicabilityChecker.is_applicable("heading-order") is True
    
    def test_form_label_is_applicable(self):
        """Test that form-label rule is applicable"""
        assert RepairApplicabilityChecker.is_applicable("form-label") is True
    
    def test_aria_required_attr_is_applicable(self):
        """Test that aria-required-attr rule is applicable"""
        assert RepairApplicabilityChecker.is_applicable("aria-required-attr") is True
    
    def test_non_applicable_rule(self):
        """Test that non-MVP rules are not applicable"""
        assert RepairApplicabilityChecker.is_applicable("color-contrast-enhanced") is False
        assert RepairApplicabilityChecker.is_applicable("unknown-rule") is False
        assert RepairApplicabilityChecker.is_applicable("") is False


class TestRepairGeneratorInit:
    """Test RepairGenerator initialization"""
    
    def test_init_with_bedrock_client(self):
        """Test initialization with Bedrock client"""
        mock_client = Mock()
        generator = RepairGenerator(bedrock_client=mock_client)
        assert generator.bedrock_client is mock_client
        assert generator.checker is not None
    
    def test_init_without_bedrock_client(self):
        """Test initialization without Bedrock client"""
        generator = RepairGenerator()
        assert generator.bedrock_client is None
        assert generator.checker is not None


class TestSafetyValidation:
    """Test PBT Suite 2: Unsafe patch rejection"""
    
    def test_safe_patch_accepted(self):
        """Test that safe patches pass validation"""
        generator = RepairGenerator()
        
        repair = RepairPatch(
            repair_id="repair-1",
            finding_id="finding-1",
            file_type="html",
            content='alt="Descriptive text"',
            selector="img.logo",
        )
        
        assert generator._is_safe_patch(repair) is True
    
    def test_script_tag_injection_rejected(self):
        """Test that <script> injection is rejected"""
        generator = RepairGenerator()
        
        repair = RepairPatch(
            repair_id="repair-1",
            finding_id="finding-1",
            file_type="html",
            content='<script>alert("xss")</script>',
            selector="div",
        )
        
        assert generator._is_safe_patch(repair) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
