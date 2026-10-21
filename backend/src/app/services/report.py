"""
Report generation service for Task 17.
Generates compliance reports with before/after metrics, violation details, and recommendations.
Supports JSON and HTML export formats.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger("accesslens.report")


class ReportFormat(str, Enum):
    """Report export format options."""
    JSON = "json"
    HTML = "html"


class ComplianceReport:
    """Represents a compliance report with before/after metrics."""
    
    def __init__(
        self,
        scan_id: str,
        url: str,
        before_violations: List[Dict[str, Any]],
        after_violations: List[Dict[str, Any]],
        fixed_count: int = 0,
        new_count: int = 0,
        unresolved_count: int = 0,
    ):
        self.scan_id = scan_id
        self.url = url
        self.before_violations = before_violations
        self.after_violations = after_violations
        self.fixed_count = fixed_count
        self.new_count = new_count
        self.unresolved_count = unresolved_count
        self.report_date = datetime.utcnow().isoformat()
        self.wcag_version = "WCAG 2.1"
        self.improvement_percentage = self._calculate_improvement()
    
    def _calculate_improvement(self) -> float:
        """Calculate percentage improvement from before to after."""
        if not self.before_violations:
            return 100.0 if not self.after_violations else 0.0
        
        improvement = (self.fixed_count / len(self.before_violations)) * 100
        return min(100.0, max(0.0, improvement))
    
    def _get_severity_breakdown(self, violations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get count of violations by severity level."""
        breakdown = {
            "critical": 0,
            "serious": 0,
            "moderate": 0,
            "minor": 0,
        }
        for violation in violations:
            severity = violation.get("severity", "minor").lower()
            if severity in breakdown:
                breakdown[severity] += 1
        return breakdown
    
    def to_json(self) -> str:
        """Export report as JSON string."""
        report_data = {
            "scan_id": self.scan_id,
            "url": self.url,
            "report_date": self.report_date,
            "wcag_version": self.wcag_version,
            "metrics": {
                "before_total": len(self.before_violations),
                "after_total": len(self.after_violations),
                "fixed_count": self.fixed_count,
                "new_count": self.new_count,
                "unresolved_count": self.unresolved_count,
                "improvement_percentage": self.improvement_percentage,
            },
            "severity_breakdown": {
                "before": self._get_severity_breakdown(self.before_violations),
                "after": self._get_severity_breakdown(self.after_violations),
            },
            "violations": {
                "before": self.before_violations,
                "after": self.after_violations,
            },
            "recommendations": self._generate_recommendations(),
        }
        return json.dumps(report_data, indent=2)
    
    def to_html(self) -> str:
        """Export report as HTML string."""
        severity_before = self._get_severity_breakdown(self.before_violations)
        severity_after = self._get_severity_breakdown(self.after_violations)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AccessLens Compliance Report - {self.scan_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 20px; color: #333; }}
        .header {{ border-bottom: 3px solid #007bff; padding-bottom: 20px; margin-bottom: 30px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric {{ background: #f5f5f5; padding: 15px; border-radius: 8px; }}
        .metric-value {{ font-size: 28px; font-weight: bold; color: #007bff; }}
        .metric-label {{ font-size: 14px; color: #666; margin-top: 5px; }}
        .success {{ color: #28a745; }}
        .warning {{ color: #ffc107; }}
        .danger {{ color: #dc3545; }}
        .section {{ margin: 30px 0; }}
        .section-title {{ font-size: 20px; font-weight: bold; border-left: 4px solid #007bff; padding-left: 10px; margin-bottom: 15px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #007bff; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
        .recommendation {{ background: #e7f3ff; border-left: 4px solid #2196F3; padding: 15px; margin: 10px 0; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #999; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>AccessLens Compliance Report</h1>
        <p><strong>URL:</strong> {self.url}</p>
        <p><strong>Scan ID:</strong> {self.scan_id}</p>
        <p><strong>Report Date:</strong> {self.report_date}</p>
        <p><strong>WCAG Version:</strong> {self.wcag_version}</p>
    </div>
    
    <div class="section">
        <div class="section-title">Summary Metrics</div>
        <div class="metrics">
            <div class="metric">
                <div class="metric-value success">{self.fixed_count}</div>
                <div class="metric-label">Violations Fixed</div>
            </div>
            <div class="metric">
                <div class="metric-value warning">{self.new_count}</div>
                <div class="metric-label">New Violations</div>
            </div>
            <div class="metric">
                <div class="metric-value danger">{self.unresolved_count}</div>
                <div class="metric-label">Unresolved Issues</div>
            </div>
            <div class="metric">
                <div class="metric-value">{self.improvement_percentage:.1f}%</div>
                <div class="metric-label">Improvement</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <div class="section-title">Severity Breakdown</div>
        <table>
            <tr>
                <th>Severity</th>
                <th>Before</th>
                <th>After</th>
                <th>Fixed</th>
            </tr>
            <tr>
                <td><strong>Critical</strong></td>
                <td>{severity_before["critical"]}</td>
                <td>{severity_after["critical"]}</td>
                <td>{severity_before["critical"] - severity_after["critical"]}</td>
            </tr>
            <tr>
                <td><strong>Serious</strong></td>
                <td>{severity_before["serious"]}</td>
                <td>{severity_after["serious"]}</td>
                <td>{severity_before["serious"] - severity_after["serious"]}</td>
            </tr>
            <tr>
                <td><strong>Moderate</strong></td>
                <td>{severity_before["moderate"]}</td>
                <td>{severity_after["moderate"]}</td>
                <td>{severity_before["moderate"] - severity_after["moderate"]}</td>
            </tr>
            <tr>
                <td><strong>Minor</strong></td>
                <td>{severity_before["minor"]}</td>
                <td>{severity_after["minor"]}</td>
                <td>{severity_before["minor"] - severity_after["minor"]}</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <div class="section-title">Recommendations</div>
        {self._generate_html_recommendations()}
    </div>
    
    <div class="footer">
        <p>Generated by AccessLens on {self.report_date}</p>
    </div>
</body>
</html>"""
        return html
    
    def _generate_recommendations(self) -> List[Dict[str, str]]:
        """Generate recommendations based on violations."""
        recommendations = []
        
        if self.new_count > 0:
            recommendations.append({
                "type": "warning",
                "title": "New Violations Detected",
                "description": f"{self.new_count} new violations were introduced during repairs. Review and address these issues.",
            })
        
        if self.unresolved_count > 0:
            recommendations.append({
                "type": "alert",
                "title": "Unresolved Issues Remain",
                "description": f"{self.unresolved_count} violations could not be automatically fixed. Manual review required.",
            })
        
        if self.improvement_percentage >= 90:
            recommendations.append({
                "type": "success",
                "title": "Excellent Progress",
                "description": f"Your website accessibility has improved by {self.improvement_percentage:.1f}%. Continue working on remaining issues.",
            })
        
        if self.improvement_percentage >= 50 and self.improvement_percentage < 90:
            recommendations.append({
                "type": "info",
                "title": "Good Progress",
                "description": f"You've achieved {self.improvement_percentage:.1f}% improvement. More work needed to reach full compliance.",
            })
        
        return recommendations
    
    def _generate_html_recommendations(self) -> str:
        """Generate HTML for recommendations."""
        html = ""
        for rec in self._generate_recommendations():
            html += f'<div class="recommendation">'
            html += f'<strong>{rec["title"]}</strong><br>'
            html += f'{rec["description"]}'
            html += f'</div>'
        return html


class ReportGenerationService:
    """Service for generating compliance reports."""
    
    @staticmethod
    def generate_report(
        scan_id: str,
        url: str,
        before_violations: List[Dict[str, Any]],
        after_violations: List[Dict[str, Any]],
        fixed_count: int = 0,
        new_count: int = 0,
        unresolved_count: int = 0,
        report_format: ReportFormat = ReportFormat.JSON,
    ) -> str:
        """
        Generate a compliance report in specified format.
        
        Args:
            scan_id: Unique scan identifier
            url: Website URL that was scanned
            before_violations: Violations before repairs
            after_violations: Violations after repairs
            fixed_count: Number of violations fixed
            new_count: Number of new violations introduced
            unresolved_count: Number of unresolved violations
            report_format: Output format (JSON or HTML)
        
        Returns:
            Report as string in specified format
        """
        report = ComplianceReport(
            scan_id=scan_id,
            url=url,
            before_violations=before_violations,
            after_violations=after_violations,
            fixed_count=fixed_count,
            new_count=new_count,
            unresolved_count=unresolved_count,
        )
        
        if report_format == ReportFormat.JSON:
            return report.to_json()
        elif report_format == ReportFormat.HTML:
            return report.to_html()
        else:
            return report.to_json()  # Default to JSON
