"""Integration tests for Task 17: Report Generation Logic"""

import json
from app.services.report import ReportGenerationService, ComplianceReport, ReportFormat


class TestComplianceReport:
    """Tests for ComplianceReport"""
    
    def test_report_initialization(self):
        """Test ComplianceReport creation"""
        before = [{"rule_id": "image-alt", "severity": "serious"}]
        after = []
        
        report = ComplianceReport(
            scan_id="test-001",
            url="https://example.com",
            before_violations=before,
            after_violations=after,
            fixed_count=1,
            new_count=0,
            unresolved_count=0,
        )
        
        assert report.scan_id == "test-001"
        assert report.url == "https://example.com"
        assert report.fixed_count == 1
        assert report.wcag_version == "WCAG 2.1"
    
    def test_json_export(self):
        """Test JSON export format"""
        before = [{"rule_id": "image-alt", "severity": "serious"}]
        after = []
        
        report = ComplianceReport(
            scan_id="test-001",
            url="https://example.com",
            before_violations=before,
            after_violations=after,
            fixed_count=1,
            new_count=0,
            unresolved_count=0,
        )
        
        json_output = report.to_json()
        data = json.loads(json_output)
        
        assert data["scan_id"] == "test-001"
        assert data["url"] == "https://example.com"
        assert data["metrics"]["fixed_count"] == 1
        assert data["wcag_version"] == "WCAG 2.1"
    
    def test_html_export(self):
        """Test HTML export format"""
        before = [{"rule_id": "image-alt", "severity": "serious"}]
        after = []
        
        report = ComplianceReport(
            scan_id="test-001",
            url="https://example.com",
            before_violations=before,
            after_violations=after,
            fixed_count=1,
            new_count=0,
            unresolved_count=0,
        )
        
        html_output = report.to_html()
        
        assert "<!DOCTYPE html>" in html_output
        assert "test-001" in html_output
        assert "https://example.com" in html_output
        assert "AccessLens Compliance Report" in html_output
    
    def test_improvement_calculation(self):
        """Test improvement percentage calculation"""
        before = [
            {"rule_id": "image-alt", "severity": "serious"},
            {"rule_id": "color-contrast", "severity": "serious"},
        ]
        after = [{"rule_id": "color-contrast", "severity": "serious"}]
        
        report = ComplianceReport(
            scan_id="test-001",
            url="https://example.com",
            before_violations=before,
            after_violations=after,
            fixed_count=1,
            new_count=0,
            unresolved_count=1,
        )
        
        assert report.improvement_percentage == 50.0
    
    def test_severity_breakdown(self):
        """Test severity breakdown calculation"""
        before = [
            {"rule_id": "rule1", "severity": "critical"},
            {"rule_id": "rule2", "severity": "serious"},
            {"rule_id": "rule3", "severity": "serious"},
            {"rule_id": "rule4", "severity": "moderate"},
        ]
        
        report = ComplianceReport(
            scan_id="test-001",
            url="https://example.com",
            before_violations=before,
            after_violations=[],
            fixed_count=4,
            new_count=0,
            unresolved_count=0,
        )
        
        json_output = report.to_json()
        data = json.loads(json_output)
        
        assert data["severity_breakdown"]["before"]["critical"] == 1
        assert data["severity_breakdown"]["before"]["serious"] == 2
        assert data["severity_breakdown"]["before"]["moderate"] == 1


class TestReportGenerationService:
    """Tests for ReportGenerationService"""
    
    def test_generate_json_report(self):
        """Test JSON report generation"""
        before = [{"rule_id": "image-alt", "severity": "serious"}]
        after = []
        
        json_report = ReportGenerationService.generate_report(
            scan_id="test-001",
            url="https://example.com",
            before_violations=before,
            after_violations=after,
            fixed_count=1,
            new_count=0,
            unresolved_count=0,
            report_format=ReportFormat.JSON,
        )
        
        data = json.loads(json_report)
        assert data["scan_id"] == "test-001"
        assert "metrics" in data
    
    def test_generate_html_report(self):
        """Test HTML report generation"""
        before = [{"rule_id": "image-alt", "severity": "serious"}]
        after = []
        
        html_report = ReportGenerationService.generate_report(
            scan_id="test-001",
            url="https://example.com",
            before_violations=before,
            after_violations=after,
            fixed_count=1,
            new_count=0,
            unresolved_count=0,
            report_format=ReportFormat.HTML,
        )
        
        assert "<!DOCTYPE html>" in html_report
        assert "AccessLens Compliance Report" in html_report
    
    def test_report_with_recommendations(self):
        """Test that report includes recommendations"""
        before = [
            {"rule_id": "rule1", "severity": "critical"},
            {"rule_id": "rule2", "severity": "serious"},
        ]
        after = [{"rule_id": "rule2", "severity": "serious"}]
        
        json_report = ReportGenerationService.generate_report(
            scan_id="test-001",
            url="https://example.com",
            before_violations=before,
            after_violations=after,
            fixed_count=1,
            new_count=0,
            unresolved_count=1,
            report_format=ReportFormat.JSON,
        )
        
        data = json.loads(json_report)
        assert "recommendations" in data
        assert len(data["recommendations"]) > 0
    
    def test_report_with_timestamp(self):
        """Test that report includes timestamp"""
        json_report = ReportGenerationService.generate_report(
            scan_id="test-001",
            url="https://example.com",
            before_violations=[],
            after_violations=[],
            report_format=ReportFormat.JSON,
        )
        
        data = json.loads(json_report)
        assert "report_date" in data
        assert len(data["report_date"]) > 0
    
    def test_report_default_format_is_json(self):
        """Test that default format is JSON"""
        report = ReportGenerationService.generate_report(
            scan_id="test-001",
            url="https://example.com",
            before_violations=[],
            after_violations=[],
        )
        
        # Should not raise exception when parsing as JSON
        data = json.loads(report)
        assert "scan_id" in data
