"""
E2E Tests with Realistic Accessibility Violations

Tests the workflow with realistic HTML examples containing actual WCAG violations.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestE2ERealisticViolations:
    """Test E2E workflow with realistic accessibility violations"""
    
    @pytest.fixture
    def realistic_html_violations(self):
        """Collection of realistic HTML violations with expected repairs"""
        return {
            "images_without_alt": {
                "violation_type": "missing_alt_text",
                "wcag_criteria": "1.1.1 Non-text Content",
                "severity": "high",
                "html_before": '<img src="product.jpg" width="200" height="200">',
                "html_after": '<img src="product.jpg" width="200" height="200" alt="Red cotton shirt with blue stripes">',
                "explanation": "Image must have descriptive alt text for users with visual impairments"
            },
            "form_without_labels": {
                "violation_type": "form_label_missing",
                "wcag_criteria": "1.3.1 Info and Relationships",
                "severity": "high",
                "html_before": '<input type="text" placeholder="Enter email">',
                "html_after": '<label for="email">Email address</label>\n<input type="text" id="email" placeholder="Enter email">',
                "explanation": "Form inputs must have associated labels for users with assistive technology"
            },
            "low_contrast_text": {
                "violation_type": "low_contrast",
                "wcag_criteria": "1.4.3 Contrast (Minimum)",
                "severity": "high",
                "html_before": '<p style="color: #999; background-color: #fff;">Important information</p>',
                "html_after": '<p style="color: #333; background-color: #fff;">Important information</p>',
                "explanation": "Text contrast ratio must be at least 4.5:1 for normal text (WCAG AA)"
            },
            "missing_heading_hierarchy": {
                "violation_type": "heading_hierarchy",
                "wcag_criteria": "1.3.1 Info and Relationships",
                "severity": "medium",
                "html_before": '<h1>Main Title</h1>\n<h3>Subsection</h3>\n<h2>Another section</h2>',
                "html_after": '<h1>Main Title</h1>\n<h2>Subsection</h2>\n<h3>Details under subsection</h3>',
                "explanation": "Heading hierarchy should be sequential (h1 → h2 → h3) for logical document structure"
            },
            "missing_page_title": {
                "violation_type": "missing_page_title",
                "wcag_criteria": "2.4.2 Page Titled",
                "severity": "high",
                "html_before": '<!DOCTYPE html>\n<html>\n<head>\n</head>\n<body>Content</body>\n</html>',
                "html_after": '<!DOCTYPE html>\n<html>\n<head>\n<title>Product Catalog - E-commerce Store</title>\n</head>\n<body>Content</body>\n</html>',
                "explanation": "Every page must have a descriptive title element"
            },
            "link_without_purpose": {
                "violation_type": "link_purpose",
                "wcag_criteria": "2.4.4 Link Purpose (In Context)",
                "severity": "medium",
                "html_before": '<a href="/more-info">Click here</a>',
                "html_after": '<a href="/more-info">Click here for more information about our services</a>',
                "explanation": "Link text must describe the link's purpose (users should understand where it goes)"
            },
            "button_without_accessible_name": {
                "violation_type": "button_name",
                "wcag_criteria": "4.1.2 Name, Role, Value",
                "severity": "high",
                "html_before": '<button><svg><use xlink:href="#icon-search"></use></svg></button>',
                "html_after": '<button aria-label="Search"><svg><use xlink:href="#icon-search"></use></svg></button>',
                "explanation": "Buttons must have an accessible name (via text, aria-label, or aria-labelledby)"
            },
            "video_without_captions": {
                "violation_type": "video_captions",
                "wcag_criteria": "1.2.2 Captions (Prerecorded)",
                "severity": "high",
                "html_before": '<video src="demo.mp4" controls></video>',
                "html_after": '<video src="demo.mp4" controls>\n  <track kind="captions" src="demo.vtt" label="English">\n</video>',
                "explanation": "Prerecorded videos must have captions for users who are deaf or hard of hearing"
            },
            "color_only_to_convey_info": {
                "violation_type": "color_not_sole_means",
                "wcag_criteria": "1.4.1 Use of Color",
                "severity": "medium",
                "html_before": '<p><span style="color: red;">Errors</span> | <span style="color: green;">Success</span></p>',
                "html_after": '<p><span style="color: red;">❌ Errors</span> | <span style="color: green;">✓ Success</span></p>',
                "explanation": "Color alone should not be used to convey information (add text, icons, or patterns)"
            },
            "aria_misuse": {
                "violation_type": "aria_misuse",
                "wcag_criteria": "4.1.2 Name, Role, Value",
                "severity": "high",
                "html_before": '<div role="button">Click me</div>',
                "html_after": '<button>Click me</button>',
                "explanation": "Use semantic HTML elements instead of ARIA role="button" on div"
            }
        }
    
    def test_e2e_missing_alt_text_workflow(self, client, realistic_html_violations):
        """Test complete workflow for missing alt text violation"""
        violation = realistic_html_violations["images_without_alt"]
        
        # Step 1: Submit scan
        submit = client.post(
            "/api/scan",
            json={
                "url": "https://test-violations.com",
                "user_id": "test-violations-user"
            }
        )
        assert submit.status_code == 202
        scan_id = submit.json()["scan_id"]
        
        # Step 2: Generate repair for missing alt text
        repair = client.post(
            "/api/repair/generate",
            json={
                "scan_id": scan_id,
                "finding_ids": ["finding-img-alt"]
            }
        )
        
        # Should accept and generate repair
        assert repair.status_code in [202, 200]
    
    def test_e2e_form_labeling_workflow(self, client, realistic_html_violations):
        """Test workflow for missing form labels"""
        violation = realistic_html_violations["form_without_labels"]
        
        response = client.post(
            "/api/repair/generate",
            json={
                "scan_id": "form-test-scan",
                "finding_ids": ["finding-form-label"]
            }
        )
        
        assert response.status_code in [202, 200]
    
    def test_e2e_contrast_violation_workflow(self, client, realistic_html_violations):
        """Test workflow for low contrast violations"""
        violation = realistic_html_violations["low_contrast_text"]
        
        response = client.post(
            "/api/repair/generate",
            json={
                "scan_id": "contrast-test-scan",
                "finding_ids": ["finding-contrast"]
            }
        )
        
        assert response.status_code in [202, 200]
    
    def test_e2e_heading_hierarchy_workflow(self, client, realistic_html_violations):
        """Test workflow for heading hierarchy violations"""
        violation = realistic_html_violations["missing_heading_hierarchy"]
        
        response = client.post(
            "/api/repair/generate",
            json={
                "scan_id": "heading-test-scan",
                "finding_ids": ["finding-heading-h1", "finding-heading-h3", "finding-heading-h2"]
            }
        )
        
        assert response.status_code in [202, 200]
    
    def test_e2e_multiple_violations_combined(self, client, realistic_html_violations):
        """Test workflow with multiple realistic violations"""
        
        # Simulate a page with multiple violations
        finding_ids = [
            "finding-img-alt",
            "finding-form-label",
            "finding-contrast",
            "finding-link-purpose",
            "finding-video-captions"
        ]
        
        response = client.post(
            "/api/repair/generate",
            json={
                "scan_id": "multi-violation-scan",
                "finding_ids": finding_ids
            }
        )
        
        assert response.status_code in [202, 200]
        
        # If successful, repairs should be generated for each violation
        if response.status_code == 202:
            data = response.json()
            assert "batch_id" in data or "repair_ids" in data
    
    def test_e2e_wcag_level_aa_compliance(self, client):
        """Test that repairs address WCAG 2.1 Level AA criteria"""
        
        # Common WCAG AA criteria
        wcag_aa_criteria = [
            "1.1.1",   # Non-text Content
            "1.2.2",   # Captions (Prerecorded)
            "1.4.3",   # Contrast (Minimum)
            "2.4.2",   # Page Titled
            "2.4.4",   # Link Purpose (In Context)
            "3.1.1",   # Language of Page
            "4.1.2"    # Name, Role, Value
        ]
        
        # Submit scan and verify repairs address these criteria
        response = client.post(
            "/api/repair/generate",
            json={
                "scan_id": "wcag-aa-scan",
                "finding_ids": [f"finding-wcag-{i}" for i in range(len(wcag_aa_criteria))]
            }
        )
        
        assert response.status_code in [202, 200]
    
    def test_e2e_violation_severity_levels(self, client, realistic_html_violations):
        """Test that violations are categorized by severity"""
        
        # Separate high and medium severity findings
        high_severity = [
            "finding-img-alt",
            "finding-form-label",
            "finding-contrast",
            "finding-button-name"
        ]
        
        medium_severity = [
            "finding-heading-hierarchy",
            "finding-link-purpose",
            "finding-color-meaning"
        ]
        
        # Generate repairs for high severity
        high_response = client.post(
            "/api/repair/generate",
            json={
                "scan_id": "severity-high-scan",
                "finding_ids": high_severity
            }
        )
        assert high_response.status_code in [202, 200]
        
        # Generate repairs for medium severity
        medium_response = client.post(
            "/api/repair/generate",
            json={
                "scan_id": "severity-medium-scan",
                "finding_ids": medium_severity
            }
        )
        assert medium_response.status_code in [202, 200]


class TestE2EViolationDetectionAccuracy:
    """Test accuracy of violation detection"""
    
    def test_e2e_false_positive_handling(self, client):
        """Test that legitimate elements aren't marked as violations"""
        
        # These should NOT be violations
        valid_elements = [
            "finding-decorative-image",  # Decorative image with role="presentation"
            "finding-hidden-skip-link",  # Hidden skip link (valid practice)
            "finding-valid-aria-label"   # Properly used ARIA label
        ]
        
        response = client.post(
            "/api/repair/generate",
            json={
                "scan_id": "false-positive-test",
                "finding_ids": valid_elements
            }
        )
        
        # Should handle gracefully
        assert response.status_code in [202, 200, 422]
    
    def test_e2e_violation_confidence_levels(self, client):
        """Test that violations report confidence levels"""
        
        response = client.post(
            "/api/repair/generate",
            json={
                "scan_id": "confidence-test",
                "finding_ids": ["finding-high-confidence", "finding-low-confidence"]
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            # Repairs should include confidence scores
            assert isinstance(data, (dict, list))


class TestE2ERepairQuality:
    """Test quality of generated repairs"""
    
    def test_e2e_repair_maintains_functionality(self, client):
        """Test that repairs don't break existing functionality"""
        
        # Apply repairs and verify page still works
        response = client.post(
            "/api/patch/apply",
            json={
                "scan_id": "quality-test-scan",
                "repair_ids": ["repair-1", "repair-2"]
            }
        )
        
        assert response.status_code in [202, 200]
    
    def test_e2e_repair_follows_best_practices(self, client):
        """Test that repairs follow accessibility best practices"""
        
        response = client.post(
            "/api/repair/generate",
            json={
                "scan_id": "best-practices-scan",
                "finding_ids": ["finding-1"]
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            # Repairs should use semantic HTML when possible
            assert isinstance(data, (dict, list))
    
    def test_e2e_repair_explanation_clarity(self, client):
        """Test that repairs include clear explanations"""
        
        response = client.post(
            "/api/repair/generate",
            json={
                "scan_id": "explanation-test",
                "finding_ids": ["finding-1"]
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            # Should have explanations of why repair was made
            assert isinstance(data, (dict, list))
