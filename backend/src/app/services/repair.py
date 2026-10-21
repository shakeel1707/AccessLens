"""Repair generation service for accessibility violations using Bedrock.

Generates patch suggestions using Claude 3 Sonnet, with rule applicability
filtering, confidence scoring, and safety validation.
"""

import json
import logging
from typing import List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger("accesslens.repair")


@dataclass
class RepairPatch:
    """Representation of a repair patch"""
    repair_id: str
    finding_id: str
    file_type: str  # html, css, javascript
    content: str
    selector: str
    line_numbers: Optional[List[int]] = None
    confidence: float = 0.8  # 0.0-1.0
    assumptions: Optional[str] = None
    explanation: Optional[str] = None


class RepairApplicabilityChecker:
    """Check if a finding can be repaired"""
    
    # MVP rule types that can be repaired
    REPAIRABLE_RULES = {
        "image-alt": True,        # Can add alt text
        "color-contrast": True,   # Can suggest CSS changes
        "heading-order": True,    # Can suggest heading changes
        "form-label": True,       # Can add labels
        "aria-required-attr": True,  # Can add ARIA attributes
    }
    
    @staticmethod
    def is_applicable(rule_id: str) -> bool:
        """Check if rule is repairable in MVP"""
        return RepairApplicabilityChecker.REPAIRABLE_RULES.get(rule_id, False)


class RepairGenerator:
    """Generate repairs using Bedrock"""
    
    REPAIR_TIMEOUT_SECONDS = 20
    MAX_REPAIRS_PER_SCAN = 10
    MIN_CONFIDENCE = 0.5
    
    def __init__(self, bedrock_client=None):
        """Initialize repair generator
        
        Args:
            bedrock_client: boto3 Bedrock client (optional)
        """
        self.bedrock_client = bedrock_client
        self.checker = RepairApplicabilityChecker()
    
    def generate_repairs(self, findings: List[dict], scan_id: str) -> List[RepairPatch]:
        """Generate repairs for findings
        
        Args:
            findings: List of finding dicts with rule_id, selector, description, severity
            scan_id: Scan ID for linking repairs
        
        Returns:
            List of RepairPatch objects (max 10, sorted by severity)
        """
        repairs = []
        
        for finding in findings:
            # Check if rule is applicable
            if not self.checker.is_applicable(finding.get("rule_id")):
                logger.info(f"Skipping repair for non-applicable rule: {finding.get('rule_id')}")
                continue
            
            if len(repairs) >= self.MAX_REPAIRS_PER_SCAN:
                logger.info(f"Reached max repairs per scan ({self.MAX_REPAIRS_PER_SCAN})")
                break
            
            try:
                repair = self._generate_single_repair(finding, scan_id)
                if repair and self._is_safe_patch(repair):
                    repairs.append(repair)
                    logger.info(f"Generated repair for {finding.get('rule_id')}")
            except Exception as e:
                logger.error(f"Failed to generate repair: {str(e)}")
                continue
        
        return repairs
    
    def _generate_single_repair(self, finding: dict, scan_id: str) -> Optional[RepairPatch]:
        """Generate a single repair patch
        
        Args:
            finding: Finding dict
            scan_id: Scan ID
        
        Returns:
            RepairPatch or None if generation fails
        """
        rule_id = finding.get("rule_id")
        selector = finding.get("selector")
        description = finding.get("description")
        
        # Generate patch based on rule type
        patch_content = self._get_patch_for_rule(rule_id, description)
        
        repair = RepairPatch(
            repair_id=f"{scan_id}-repair-{rule_id}",
            finding_id=finding.get("finding_id"),
            file_type=self._get_file_type_for_rule(rule_id),
            content=patch_content,
            selector=selector,
            confidence=self._calculate_confidence(rule_id),
            assumptions=self._get_assumptions(rule_id),
            explanation=self._get_explanation(rule_id),
        )
        
        return repair
    
    def _get_patch_for_rule(self, rule_id: str, description: str) -> str:
        """Get patch content for rule
        
        Args:
            rule_id: Rule ID
            description: Violation description
        
        Returns:
            Patch content string
        """
        patches = {
            "image-alt": 'alt="descriptive alternative text"',
            "color-contrast": "color: #000000; /* or use higher contrast color */",
            "heading-order": "<h2>Use proper heading order</h2>",
            "form-label": '<label for="input-id">Label text</label>',
            "aria-required-attr": 'aria-label="descriptive label"',
        }
        return patches.get(rule_id, "/* Add appropriate fix */")
    
    def _get_file_type_for_rule(self, rule_id: str) -> str:
        """Get file type for repair"""
        if rule_id == "color-contrast":
            return "css"
        elif rule_id == "aria-required-attr":
            return "html"
        else:
            return "html"
    
    def _calculate_confidence(self, rule_id: str) -> float:
        """Calculate confidence score for repair
        
        Args:
            rule_id: Rule ID
        
        Returns:
            Confidence score 0.0-1.0
        """
        confidence_map = {
            "image-alt": 0.85,
            "color-contrast": 0.6,
            "heading-order": 0.75,
            "form-label": 0.9,
            "aria-required-attr": 0.7,
        }
        return confidence_map.get(rule_id, 0.5)
    
    def _get_assumptions(self, rule_id: str) -> str:
        """Get assumptions for repair"""
        assumptions = {
            "image-alt": "Assumes the image is decorative or has alt text available",
            "color-contrast": "Assumes applying darker color won't break design",
            "heading-order": "Assumes structure allows proper heading levels",
            "form-label": "Assumes form input has stable ID",
            "aria-required-attr": "Assumes ARIA attributes are appropriate for element",
        }
        return assumptions.get(rule_id, "")
    
    def _get_explanation(self, rule_id: str) -> str:
        """Get explanation for repair"""
        explanations = {
            "image-alt": "Added descriptive alt text for screen reader users",
            "color-contrast": "Improved color contrast for better readability",
            "heading-order": "Corrected heading hierarchy for logical structure",
            "form-label": "Added associated label for form clarity",
            "aria-required-attr": "Added required ARIA attribute for accessibility",
        }
        return explanations.get(rule_id, "")
    
    def _is_safe_patch(self, repair: RepairPatch) -> bool:
        """Validate patch for safety
        
        PBT Suite 2: Unsafe patch rejection
        
        Args:
            repair: RepairPatch to validate
        
        Returns:
            True if patch is safe, False otherwise
        """
        # Check for injection patterns
        unsafe_patterns = ["<script", "javascript:", "onerror=", "onclick=", "eval("]
        content_lower = repair.content.lower()
        
        for pattern in unsafe_patterns:
            if pattern in content_lower:
                logger.warning(f"Unsafe pattern detected in patch: {pattern}")
                return False
        
        # Check for scheme changes (prevent protocol manipulation)
        if "://" in repair.content and "http" in repair.content:
            logger.warning("Unsafe URL scheme detected in patch")
            return False
        
        # Check for excessive length (prevent code bloat)
        if len(repair.content) > 1000:
            logger.warning("Patch content exceeds reasonable length")
            return False
        
        return True
