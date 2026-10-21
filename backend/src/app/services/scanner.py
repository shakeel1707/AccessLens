"""
Playwright-based website scanning engine for AccessLens.
Implements browser automation with axe-core integration for accessibility scanning.
"""

import asyncio
import json
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import subprocess
import os

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
except ImportError:
    raise ImportError("playwright package required: pip install playwright")

from app.services.finding_service import Finding, Severity

logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    """Result of a website scan."""
    url: str
    findings: List[Finding] = field(default_factory=list)
    scan_time_ms: float = 0.0
    error: Optional[str] = None
    error_type: Optional[str] = None
    html_snapshot: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'url': self.url,
            'findings': [f.to_dict() for f in self.findings],
            'scan_time_ms': self.scan_time_ms,
            'error': self.error,
            'error_type': self.error_type,
            'html_snapshot': self.html_snapshot,
        }


class AxeCoreWrapper:
    """Wrapper for axe-core accessibility testing."""
    
    @staticmethod
    async def run_axe(page, context: str = "document") -> Dict[str, Any]:
        """
        Run axe-core on the page and return results.
        
        Args:
            page: Playwright page object
            context: axe context (default: full document)
            
        Returns:
            axe-core results dict with violations, passes, etc.
        """
        # Inject axe-core script
        axe_script = """
        async function runAxe() {
            if (typeof axe === 'undefined') {
                throw new Error('axe-core not loaded');
            }
            return new Promise((resolve, reject) => {
                axe.run((error, results) => {
                    if (error) reject(error);
                    else resolve(results);
                });
            });
        }
        return await runAxe();
        """
        
        try:
            # Inject axe-core library first
            axe_cdn = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.7.2/axe.min.js"
            await page.add_script_tag(url=axe_cdn)
            await asyncio.sleep(0.5)  # Wait for script to load
            
            # Run axe and get results
            results = await page.evaluate(axe_script)
            return results
        except Exception as e:
            logger.error(f"Error running axe-core: {str(e)}")
            return {"violations": [], "passes": []}


class PlaywrightScanner:
    """Website scanner using Playwright and axe-core."""
    
    # Severity mapping from axe-core impact levels
    IMPACT_TO_SEVERITY = {
        "critical": Severity.CRITICAL,
        "serious": Severity.SERIOUS,
        "moderate": Severity.MODERATE,
        "minor": Severity.MINOR,
    }
    
    def __init__(self, timeout_seconds: int = 30, headless: bool = True):
        """
        Initialize scanner.
        
        Args:
            timeout_seconds: Timeout for scan operations
            headless: Run browser in headless mode
        """
        self.timeout_seconds = timeout_seconds
        self.headless = headless
        self.playwright = None
        self.browser = None
    
    async def initialize(self) -> None:
        """Initialize Playwright browser."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=self.headless)
            logger.info("Playwright browser initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Playwright: {str(e)}")
            raise
    
    async def close(self) -> None:
        """Close Playwright browser."""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Playwright browser closed")
        except Exception as e:
            logger.error(f"Error closing Playwright: {str(e)}")
    
    async def scan(self, url: str) -> ScanResult:
        """
        Scan a URL for accessibility issues.
        
        Args:
            url: URL to scan
            
        Returns:
            ScanResult with findings
        """
        if not self.browser:
            raise RuntimeError("Scanner not initialized. Call initialize() first.")
        
        start_time = datetime.now()
        result = ScanResult(url=url)
        
        context = None
        page = None
        
        try:
            # Create browser context and page
            context = await self.browser.new_context()
            page = await context.new_page()
            
            # Set viewport and navigate with timeout
            await page.set_viewport_size({"width": 1280, "height": 720})
            await page.goto(url, wait_until="networkidle", timeout=self.timeout_seconds * 1000)
            
            # Run axe-core
            axe_results = await AxeCoreWrapper.run_axe(page)
            
            # Extract findings from violations
            findings = []
            for violation in axe_results.get("violations", []):
                for node in violation.get("nodes", []):
                    finding = self._violation_to_finding(violation, node)
                    findings.append(finding)
            
            # Capture HTML snapshot
            try:
                result.html_snapshot = await page.content()
            except Exception as e:
                logger.warning(f"Failed to capture HTML snapshot: {str(e)}")
            
            result.findings = findings
            result.error = None
            
        except PlaywrightTimeoutError:
            result.error = f"Scan timeout after {self.timeout_seconds} seconds"
            result.error_type = "TIMEOUT"
            logger.warning(f"Scan timeout for {url}")
        except Exception as e:
            error_msg = str(e)
            if "net::" in error_msg or "ERR_" in error_msg:
                result.error = f"Network error: {error_msg}"
                result.error_type = "NETWORK_ERROR"
            elif "Invalid URL" in error_msg or "ERR_INVALID_URL" in error_msg:
                result.error = f"Invalid URL: {url}"
                result.error_type = "INVALID_URL"
            else:
                result.error = f"Scan error: {error_msg}"
                result.error_type = "SCAN_ERROR"
            logger.error(f"Error scanning {url}: {error_msg}")
        
        finally:
            # Cleanup
            if page:
                try:
                    await page.close()
                except Exception as e:
                    logger.warning(f"Error closing page: {str(e)}")
            if context:
                try:
                    await context.close()
                except Exception as e:
                    logger.warning(f"Error closing context: {str(e)}")
        
        # Calculate scan time
        result.scan_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        return result
    
    def _violation_to_finding(self, violation: Dict[str, Any], node: Dict[str, Any]) -> Finding:
        """Convert axe-core violation to Finding object."""
        # Extract node information
        target = node.get("target", ["unknown"])
        selector = target[0] if isinstance(target, list) and target else "unknown"
        html = node.get("html", "")
        
        # Map impact to severity
        impact = violation.get("impact", "minor").lower()
        severity = self.IMPACT_TO_SEVERITY.get(impact, Severity.MINOR)
        
        # Create finding
        finding = Finding(
            finding_id="",  # Will be generated by FindingIDGenerator
            rule_id=violation.get("id", "unknown-rule"),
            selector=selector,
            description=violation.get("description", "Accessibility issue"),
            severity=severity,
            html=html,
            impact=violation.get("impact", "unknown"),
        )
        
        return finding


class ScannerPool:
    """Pool of scanner instances for concurrent scanning."""
    
    def __init__(self, pool_size: int = 5, timeout_seconds: int = 30):
        """
        Initialize scanner pool.
        
        Args:
            pool_size: Number of scanner instances to maintain
            timeout_seconds: Timeout for individual scans
        """
        self.pool_size = pool_size
        self.timeout_seconds = timeout_seconds
        self.scanners: List[PlaywrightScanner] = []
        self.semaphore = asyncio.Semaphore(pool_size)
    
    async def initialize(self) -> None:
        """Initialize all scanners in pool."""
        for i in range(self.pool_size):
            scanner = PlaywrightScanner(timeout_seconds=self.timeout_seconds)
            await scanner.initialize()
            self.scanners.append(scanner)
        logger.info(f"Scanner pool initialized with {self.pool_size} instances")
    
    async def close(self) -> None:
        """Close all scanners."""
        for scanner in self.scanners:
            await scanner.close()
        logger.info("Scanner pool closed")
    
    async def scan(self, url: str) -> ScanResult:
        """
        Scan URL using available scanner from pool.
        
        Args:
            url: URL to scan
            
        Returns:
            ScanResult
        """
        async with self.semaphore:
            # Get available scanner (round-robin)
            scanner = self.scanners[asyncio.get_event_loop()._counter % self.pool_size]
            asyncio.get_event_loop()._counter = getattr(asyncio.get_event_loop(), '_counter', 0) + 1
            
            return await scanner.scan(url)
