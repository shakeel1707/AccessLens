"""
DynamoDB data models using Pydantic for validation.
All models are designed for AWS DynamoDB with proper key schemas.
"""

from datetime import datetime
from typing import Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class ScanStatus(str, Enum):
    """Status enum for scans."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Severity(str, Enum):
    """Accessibility violation severity levels (WCAG axe-core)."""
    CRITICAL = "critical"
    SERIOUS = "serious"
    MODERATE = "moderate"
    MINOR = "minor"


class ReviewStatus(str, Enum):
    """Status of repair proposal review."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# ============================================================================
# Scan Table Model
# ============================================================================

class ScanModel(BaseModel):
    """
    Scan table model.
    
    PK: scan_id (UUID)
    SK: timestamp (ISO 8601)
    
    Represents a website accessibility scan request and its status.
    """
    scan_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique scan identifier")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Timestamp (ISO 8601)")
    
    url: str = Field(..., description="Target website URL (validated)")
    user_id: str = Field(default="demo-user", description="User who initiated scan")
    status: ScanStatus = Field(default=ScanStatus.PENDING, description="Current scan status")
    finding_count: int = Field(default=0, description="Number of findings detected")
    error_message: Optional[str] = Field(None, description="Error message if scan failed")
    
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    class Config:
        use_enum_values = True  # Serialize enums as strings
    
    def to_dynamodb_item(self) -> dict[str, Any]:
        """Convert to DynamoDB item format."""
        return {
            "scan_id": self.scan_id,
            "timestamp": self.timestamp,
            "url": self.url,
            "user_id": self.user_id,
            "status": self.status,
            "finding_count": self.finding_count,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dynamodb_item(cls, item: dict[str, Any]) -> "ScanModel":
        """Create from DynamoDB item."""
        return cls(**item)


# ============================================================================
# Findings Table Model
# ============================================================================

class FindingModel(BaseModel):
    """
    Findings table model.
    
    PK: scan_id
    SK: finding_id (SHA256 hash)
    
    Represents an individual accessibility violation.
    """
    scan_id: str = Field(..., description="Associated scan ID")
    finding_id: str = Field(..., description="Unique finding ID (SHA256)")
    
    rule_id: str = Field(..., description="axe-core rule ID (e.g., 'image-alt')")
    severity: Severity = Field(..., description="Violation severity")
    selector: str = Field(..., description="CSS selector of affected element")
    html_snippet: Optional[str] = Field(None, description="Affected HTML snippet")
    description: str = Field(..., description="Violation description")
    
    explanation: Optional[str] = Field(None, description="AI-generated explanation (max 500 chars)")
    cached_at: Optional[str] = Field(None, description="Timestamp when explanation was cached")
    
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    class Config:
        use_enum_values = True
    
    def to_dynamodb_item(self) -> dict[str, Any]:
        """Convert to DynamoDB item."""
        return {
            "scan_id": self.scan_id,
            "finding_id": self.finding_id,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "selector": self.selector,
            "html_snippet": self.html_snippet,
            "description": self.description,
            "explanation": self.explanation,
            "cached_at": self.cached_at,
            "created_at": self.created_at,
        }
    
    @classmethod
    def from_dynamodb_item(cls, item: dict[str, Any]) -> "FindingModel":
        """Create from DynamoDB item."""
        return cls(**item)


# ============================================================================
# Repairs Table Model
# ============================================================================

class RepairModel(BaseModel):
    """
    Repairs table model.
    
    PK: scan_id
    SK: finding_id (composite: repair_id or finding_id-repair_index)
    
    Represents an AI-generated repair proposal.
    """
    scan_id: str = Field(..., description="Associated scan ID")
    repair_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique repair ID")
    finding_id: str = Field(..., description="Associated finding ID")
    
    rule_id: str = Field(..., description="Rule being fixed")
    file_type: str = Field(..., description="Target file type (html|css|js)")
    proposed_patch: str = Field(..., description="Proposed code patch/modification")
    confidence: str = Field(..., description="Confidence level (high|medium|low)")
    assumptions: Optional[str] = Field(None, description="Assumptions about the fix")
    warnings: Optional[str] = Field(None, description="Potential warnings or side effects")
    
    review_status: ReviewStatus = Field(default=ReviewStatus.PENDING, description="Review status")
    reviewer_comment: Optional[str] = Field(None, description="User's comment on the repair")
    
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    reviewed_at: Optional[str] = Field(None, description="Timestamp when reviewed")
    
    class Config:
        use_enum_values = True
    
    def to_dynamodb_item(self) -> dict[str, Any]:
        """Convert to DynamoDB item."""
        return {
            "scan_id": self.scan_id,
            "repair_id": self.repair_id,
            "finding_id": self.finding_id,
            "rule_id": self.rule_id,
            "file_type": self.file_type,
            "proposed_patch": self.proposed_patch,
            "confidence": self.confidence,
            "assumptions": self.assumptions,
            "warnings": self.warnings,
            "review_status": self.review_status,
            "reviewer_comment": self.reviewer_comment,
            "created_at": self.created_at,
            "reviewed_at": self.reviewed_at,
        }
    
    @classmethod
    def from_dynamodb_item(cls, item: dict[str, Any]) -> "RepairModel":
        """Create from DynamoDB item."""
        return cls(**item)


# ============================================================================
# Verification Results Table Model
# ============================================================================

class VerificationResultModel(BaseModel):
    """
    Verification Results table model.
    
    PK: scan_id
    SK: verification_id (UUID)
    
    Represents results after patches are applied and re-scan is performed.
    """
    scan_id: str = Field(..., description="Associated scan ID")
    verification_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique verification ID")
    
    fixed_count: int = Field(default=0, description="Number of violations fixed")
    new_violations_count: int = Field(default=0, description="Number of new violations introduced")
    unresolved_count: int = Field(default=0, description="Number of violations still present")
    
    before_findings: list[str] = Field(default_factory=list, description="List of before finding IDs")
    after_findings: list[str] = Field(default_factory=list, description="List of after finding IDs")
    
    comparison_result: dict[str, Any] = Field(default_factory=dict, description="Detailed comparison data")
    
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    class Config:
        use_enum_values = True
    
    def to_dynamodb_item(self) -> dict[str, Any]:
        """Convert to DynamoDB item."""
        return {
            "scan_id": self.scan_id,
            "verification_id": self.verification_id,
            "fixed_count": self.fixed_count,
            "new_violations_count": self.new_violations_count,
            "unresolved_count": self.unresolved_count,
            "before_findings": self.before_findings,
            "after_findings": self.after_findings,
            "comparison_result": self.comparison_result,
            "created_at": self.created_at,
        }
    
    @classmethod
    def from_dynamodb_item(cls, item: dict[str, Any]) -> "VerificationResultModel":
        """Create from DynamoDB item."""
        return cls(**item)