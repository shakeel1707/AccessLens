"""
Finding ID generation and deduplication service for AccessLens.
Implements SHA256-based finding IDs, deduplication, and severity-based sorting.
"""

import hashlib
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    """Finding severity levels from axe-core."""
    CRITICAL = "critical"
    SERIOUS = "serious"
    MODERATE = "moderate"
    MINOR = "minor"


@dataclass
class Finding:
    """Represents an accessibility finding."""
    finding_id: str
    rule_id: str
    selector: str
    description: str
    severity: Severity
    html: Optional[str] = None
    impact: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary for storage."""
        return {
            'finding_id': self.finding_id,
            'rule_id': self.rule_id,
            'selector': self.selector,
            'description': self.description,
            'severity': self.severity.value,
            'html': self.html,
            'impact': self.impact,
        }


class FindingIDGenerator:
    """Generates deterministic SHA256-based IDs for accessibility findings."""
    
    SEPARATOR = "||"
    
    @staticmethod
    def generate_id(rule_id: str, selector: str, description: str) -> str:
        """Generate a deterministic SHA256-based ID for a finding."""
        rule_id = rule_id or ""
        selector = selector or ""
        description = description or ""
        combined = f"{rule_id}{FindingIDGenerator.SEPARATOR}{selector}{FindingIDGenerator.SEPARATOR}{description}"
        hash_object = hashlib.sha256(combined.encode('utf-8'))
        return hash_object.hexdigest()
    
    @staticmethod
    def generate_from_finding(finding: Finding) -> str:
        """Generate ID from a Finding object."""
        return FindingIDGenerator.generate_id(
            finding.rule_id,
            finding.selector,
            finding.description
        )


class FindingDeduplicator:
    """Deduplicates findings based on ID."""
    
    @staticmethod
    def deduplicate(findings: List[Finding]) -> List[Finding]:
        """Remove duplicate findings, keeping the first occurrence."""
        seen_ids = set()
        deduplicated = []
        for finding in findings:
            if finding.finding_id not in seen_ids:
                seen_ids.add(finding.finding_id)
                deduplicated.append(finding)
        return deduplicated


class FindingSortingService:
    """Sorts findings by severity and other criteria."""
    
    SEVERITY_ORDER = {
        Severity.CRITICAL: 0,
        Severity.SERIOUS: 1,
        Severity.MODERATE: 2,
        Severity.MINOR: 3,
    }
    
    @staticmethod
    def sort_by_severity(findings: List[Finding]) -> List[Finding]:
        """Sort findings by severity (critical → serious → moderate → minor)."""
        return sorted(
            findings,
            key=lambda f: FindingSortingService.SEVERITY_ORDER.get(f.severity, 999)
        )
    
    @staticmethod
    def sort_by_severity_then_selector(findings: List[Finding]) -> List[Finding]:
        """Sort by severity first, then by selector."""
        return sorted(
            findings,
            key=lambda f: (
                FindingSortingService.SEVERITY_ORDER.get(f.severity, 999),
                f.selector
            )
        )


class FindingProcessingPipeline:
    """Complete pipeline for processing findings: ID generation, deduplication, sorting."""
    
    @staticmethod
    def process(findings: List[Finding], sort_by_selector: bool = False) -> List[Finding]:
        """Process findings through complete pipeline."""
        for finding in findings:
            if not finding.finding_id:
                finding.finding_id = FindingIDGenerator.generate_from_finding(finding)
        deduplicated = FindingDeduplicator.deduplicate(findings)
        if sort_by_selector:
            sorted_findings = FindingSortingService.sort_by_severity_then_selector(deduplicated)
        else:
            sorted_findings = FindingSortingService.sort_by_severity(deduplicated)
        return sorted_findings
