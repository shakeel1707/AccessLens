"""
Tests for Playwright scanning engine and axe-core integration.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.scanner import (
    ScanResult, PlaywrightScanner, AxeCoreWrapper, ScannerPool
)
from app.services.finding_service import Severity


class TestScanResult:
    """Test ScanResult dataclass."""
    
    def test_scan_result_creation(self):
        """Create scan result."""
        result = ScanResult(url="https://example.com")
        assert result.url == "https://example.com"
        assert result.findings == []
        assert result.error is None
    
    def test_scan_result_to_dict(self):
        """Convert to dictionary."""
        result = ScanResult(
            url="https://example.com",
            scan_time_ms=250.5,
            error="Network error"
        )
        result_dict = result.to_dict()
        assert result_dict["url"] == "https://example.com"
        assert result_dict["scan_time_ms"] == 250.5
        assert result_dict["error"] == "Network error"


class TestAxeCoreWrapper:
    """Test axe-core wrapper."""
    
    @pytest.mark.asyncio
    async def test_run_axe_mock(self):
        """Test axe-core execution with mock."""
        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value={
            "violations": [],
            "passes": []
        })
        
        # In real tests, would need Playwright running
        # This is a placeholder for the structure
        result = await AxeCoreWrapper.run_axe(mock_page)
        assert result is not None


class TestPlaywrightScannerStructure:
    """Test PlaywrightScanner structure and methods."""
    
    def test_scanner_initialization(self):
        """Scanner initializes correctly."""
        scanner = PlaywrightScanner(timeout_seconds=30, headless=True)
        assert scanner.timeout_seconds == 30
        assert scanner.headless is True
        assert scanner.browser is None
    
    def test_impact_to_severity_mapping(self):
        """Impact levels map to severities."""
        mapping = PlaywrightScanner.IMPACT_TO_SEVERITY
        assert mapping["critical"] == Severity.CRITICAL
        assert mapping["serious"] == Severity.SERIOUS
        assert mapping["moderate"] == Severity.MODERATE
        assert mapping["minor"] == Severity.MINOR
    
    def test_violation_to_finding_conversion(self):
        """Convert violation to finding."""
        scanner = PlaywrightScanner()
        
        violation = {
            "id": "alt-text",
            "description": "Missing alt text",
            "impact": "critical",
        }
        
        node = {
            "target": ["img.logo"],
            "html": "<img src='logo.png'>",
        }
        
        finding = scanner._violation_to_finding(violation, node)
        assert finding.rule_id == "alt-text"
        assert finding.selector == "img.logo"
        assert finding.severity == Severity.CRITICAL
        assert finding.html == "<img src='logo.png'>"
    
    def test_violation_to_finding_edge_cases(self):
        """Handle edge cases in violation conversion."""
        scanner = PlaywrightScanner()
        
        violation = {
            "id": "rule",
            "description": "Issue",
            "impact": "minor",
        }
        
        node = {
            "target": [],  # Empty target
            "html": "",
        }
        
        finding = scanner._violation_to_finding(violation, node)
        assert finding.selector == "unknown"
        assert finding.severity == Severity.MINOR


class TestScannerPoolStructure:
    """Test ScannerPool structure."""
    
    def test_pool_initialization(self):
        """Pool initializes correctly."""
        pool = ScannerPool(pool_size=3, timeout_seconds=30)
        assert pool.pool_size == 3
        assert pool.timeout_seconds == 30
        assert pool.scanners == []
    
    def test_pool_semaphore(self):
        """Pool semaphore controls concurrency."""
        pool = ScannerPool(pool_size=5)
        assert pool.semaphore._value == 5
    
    def test_pool_timeout_setting(self):
        """Pool passes timeout to scanners."""
        pool = ScannerPool(pool_size=2, timeout_seconds=45)
        # Scanners created during initialize would have this timeout
        assert pool.timeout_seconds == 45


class TestScanResultTypes:
    """Test various scan result scenarios."""
    
    def test_successful_scan_result(self):
        """Successful scan result."""
        result = ScanResult(
            url="https://example.com",
            findings=[],
            scan_time_ms=100,
            error=None
        )
        assert result.error is None
        assert len(result.findings) == 0
    
    def test_scan_with_timeout_error(self):
        """Scan with timeout error."""
        result = ScanResult(
            url="https://slow.com",
            findings=[],
            error="Scan timeout after 30 seconds",
            error_type="TIMEOUT"
        )
        assert result.error_type == "TIMEOUT"
    
    def test_scan_with_network_error(self):
        """Scan with network error."""
        result = ScanResult(
            url="https://unreachable.com",
            findings=[],
            error="Network error: ERR_CONNECTION_REFUSED",
            error_type="NETWORK_ERROR"
        )
        assert result.error_type == "NETWORK_ERROR"
    
    def test_scan_with_invalid_url_error(self):
        """Scan with invalid URL error."""
        result = ScanResult(
            url="invalid://url",
            findings=[],
            error="Invalid URL: invalid://url",
            error_type="INVALID_URL"
        )
        assert result.error_type == "INVALID_URL"


class TestViolationConversion:
    """Test violation to finding conversion edge cases."""
    
    def test_severe_violation_conversion(self):
        """Convert critical violation."""
        scanner = PlaywrightScanner()
        
        violation = {
            "id": "heading-order",
            "description": "Heading order is not sequential",
            "impact": "serious",
        }
        
        node = {
            "target": ["h3"],
            "html": "<h3>Section</h3>",
        }
        
        finding = scanner._violation_to_finding(violation, node)
        assert finding.severity == Severity.SERIOUS
    
    def test_multiple_selectors(self):
        """Handle multiple CSS selectors."""
        scanner = PlaywrightScanner()
        
        violation = {"id": "rule", "description": "Issue", "impact": "moderate"}
        node = {
            "target": ["div > button", ".primary-btn"],
            "html": "<button>Click</button>",
        }
        
        finding = scanner._violation_to_finding(violation, node)
        # Should use first selector
        assert finding.selector == "div > button"
    
    def test_unknown_impact_defaults_to_minor(self):
        """Unknown impact level defaults to minor."""
        scanner = PlaywrightScanner()
        
        violation = {
            "id": "rule",
            "description": "Issue",
            "impact": "unknown_severity",
        }
        
        node = {"target": ["div"], "html": "<div></div>"}
        
        finding = scanner._violation_to_finding(violation, node)
        assert finding.severity == Severity.MINOR


# Integration-style tests (would need real Playwright to run)

@pytest.mark.asyncio
async def test_scanner_initialization_structure():
    """Test scanner initialization structure."""
    scanner = PlaywrightScanner(timeout_seconds=30)
    assert scanner.timeout_seconds == 30
    assert scanner.browser is None
    # Actual initialization would require Playwright installation


def test_scan_result_serialization():
    """Test scan result can be serialized."""
    result = ScanResult(
        url="https://example.com",
        findings=[],
        scan_time_ms=150,
        error=None
    )
    result_dict = result.to_dict()
    
    assert isinstance(result_dict, dict)
    assert "url" in result_dict
    assert "findings" in result_dict
    assert "scan_time_ms" in result_dict
    assert "error" in result_dict


def test_pool_concurrent_limit():
    """Pool respects concurrent scan limit."""
    pool = ScannerPool(pool_size=4)
    assert pool.semaphore._value == 4
    
    # After acquiring once, should have 3 remaining
    # (In real async code)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
