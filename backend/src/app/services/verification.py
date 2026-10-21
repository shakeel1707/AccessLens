"""
Verification service for Task 16: Before/after comparison and finding reconciliation.
Handles re-scanning after patches and comparing findings to identify fixed/new/unresolved violations.
"""

import logging
import uuid
from typing import List, Dict, Any
from datetime import datetime
from app.models.database import VerificationResultModel

logger = logging.getLogger("accesslens.verification")


class ComparisonResult:
    """Represents the result of before/after finding comparison."""
    
    def __init__(self, before_findings: List[Dict[str, Any]], after_findings: List[Dict[str, Any]]):
        self.before_findings = before_findings
        self.after_findings = after_findings
        self.fixed: List[Dict[str, Any]] = []
        self.new: List[Dict[str, Any]] = []
        self.unresolved: List[Dict[str, Any]] = []
        self._compute_comparison()
    
    def _compute_comparison(self):
        """Compute fixed, new, and unresolved violations."""
        # Get sets of rule IDs for comparison
        before_rules = {f.get("rule_id"): f for f in self.before_findings}
        after_rules = {f.get("rule_id"): f for f in self.after_findings}
        
        before_rule_ids = set(before_rules.keys())
        after_rule_ids = set(after_rules.keys())
        
        # Fixed: in before but not after
        fixed_ids = before_rule_ids - after_rule_ids
        self.fixed = [before_rules[rid] for rid in fixed_ids]
        
        # New: in after but not before
        new_ids = after_rule_ids - before_rule_ids
        self.new = [after_rules[rid] for rid in new_ids]
        
        # Unresolved: in both before and after
        unresolved_ids = before_rule_ids & after_rule_ids
        self.unresolved = [before_rules[rid] for rid in unresolved_ids]
        
        logger.info(
            f"Comparison complete: fixed={len(self.fixed)}, "
            f"new={len(self.new)}, unresolved={len(self.unresolved)}"
        )
    
    @property
    def fixed_count(self) -> int:
        return len(self.fixed)
    
    @property
    def new_count(self) -> int:
        return len(self.new)
    
    @property
    def unresolved_count(self) -> int:
        return len(self.unresolved)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fixed": self.fixed,
            "new": self.new,
            "unresolved": self.unresolved,
            "fixed_count": self.fixed_count,
            "new_count": self.new_count,
            "unresolved_count": self.unresolved_count,
        }


class VerificationService:
    """Service for verification and before/after comparison."""
    
    def __init__(self, db_client=None, scanner=None):
        self.db_client = db_client
        self.scanner = scanner
    
    async def verify_patches(
        self,
        scan_id: str,
        before_findings: List[Dict[str, Any]],
        after_findings: List[Dict[str, Any]] = None,
    ) -> VerificationResultModel:
        """
        Verify patches by comparing before and after findings.
        
        Args:
            scan_id: Original scan ID
            before_findings: Findings from original scan
            after_findings: Findings after patches (optional, will re-scan if not provided)
        
        Returns:
            VerificationResultModel with comparison results
        """
        if after_findings is None:
            logger.info(f"Re-scanning environment for scan_id={scan_id}")
            after_findings = await self._re_scan(scan_id)
        
        # Perform comparison
        comparison = ComparisonResult(before_findings, after_findings)
        
        # Create verification result
        result = VerificationResultModel(
            scan_id=scan_id,
            verification_id=str(uuid.uuid4()),
            fixed_count=comparison.fixed_count,
            new_violations_count=comparison.new_count,
            unresolved_count=comparison.unresolved_count,
            before_findings=[f.get("finding_id", str(uuid.uuid4())) for f in before_findings],
            after_findings=[f.get("finding_id", str(uuid.uuid4())) for f in after_findings],
            comparison_result=comparison.to_dict(),
            created_at=datetime.utcnow().isoformat(),
        )
        
        # Persist to DynamoDB
        if self.db_client:
            await self.db_client.save_verification_result(result)
            logger.info(f"Verification result persisted: scan_id={scan_id}, verification_id={result.verification_id}")
        
        return result
    
    async def _re_scan(self, scan_id: str) -> List[Dict[str, Any]]:
        """
        Re-scan in isolated environment after patches applied.
        Uses same axe-core configuration as original scan.
        
        Args:
            scan_id: Original scan ID to re-scan
        
        Returns:
            List of findings from re-scan
        """
        if not self.scanner:
            logger.warning("Scanner not available, returning empty findings")
            return []
        
        try:
            # Re-scan the same environment
            findings = await self.scanner.scan(scan_id)
            logger.info(f"Re-scan complete: scan_id={scan_id}, findings_count={len(findings)}")
            return findings
        except Exception as e:
            logger.error(f"Re-scan failed: scan_id={scan_id}, error={str(e)}")
            raise
    
    def compare_findings(
        self,
        before: List[Dict[str, Any]],
        after: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Compare two finding lists.
        
        Args:
            before: Findings before patches
            after: Findings after patches
        
        Returns:
            Comparison result with fixed, new, and unresolved counts
        """
        comparison = ComparisonResult(before, after)
        return comparison.to_dict()
