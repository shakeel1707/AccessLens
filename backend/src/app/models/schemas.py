"""
API request/response models and validation for AccessLens.
Implements Pydantic models for all API endpoints with boundary checking.
"""

from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import re


class ScanStatus(str, Enum):
    """Status of a scan."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Severity(str, Enum):
    """Finding severity levels."""
    CRITICAL = "critical"
    SERIOUS = "serious"
    MODERATE = "moderate"
    MINOR = "minor"


class ReviewStatus(str, Enum):
    """Repair review status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# Request Models

class ScanRequest(BaseModel):
    """Request to scan a URL for accessibility issues."""
    url: str = Field(..., min_length=1, max_length=2048, description="URL to scan")
    wait_for_results: bool = Field(default=False, description="Wait for scan to complete before returning")
    
    @validator("url")
    def validate_url_format(cls, v):
        """Validate URL format (basic check, detailed validation in service)."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class RepairGenerateRequest(BaseModel):
    """Request to generate repairs for accessibility findings."""
    scan_id: str = Field(..., min_length=1, max_length=255, description="Scan ID")
    finding_ids: Optional[List[str]] = Field(default=None, description="Specific findings to repair (null = all)")
    max_repairs: int = Field(default=10, ge=1, le=100, description="Maximum repairs to generate")
    
    @validator("finding_ids")
    def validate_finding_ids_count(cls, v):
        """Validate number of finding IDs."""
        if v is not None and len(v) > 10000:
            raise ValueError("Cannot request repairs for more than 10000 findings")
        return v


class RepairApproveRequest(BaseModel):
    """Request to approve or reject a repair."""
    repair_id: str = Field(..., min_length=1, max_length=255, description="Repair ID")
    status: ReviewStatus = Field(..., description="Approval status")
    comment: Optional[str] = Field(default=None, max_length=1000, description="User comment")


class PatchApplyRequest(BaseModel):
    """Request to apply patches to a website."""
    scan_id: str = Field(..., min_length=1, max_length=255, description="Scan ID")
    repair_ids: List[str] = Field(..., min_items=1, max_items=100, description="Repair IDs to apply")
    
    @validator("repair_ids")
    def validate_repair_ids_uniqueness(cls, v):
        """Ensure no duplicate repair IDs."""
        if len(v) != len(set(v)):
            raise ValueError("Duplicate repair IDs in request")
        return v


# Response Models

class FindingResponse(BaseModel):
    """Representation of an accessibility finding."""
    finding_id: str
    rule_id: str
    selector: str
    description: str
    severity: Severity
    html: Optional[str] = None
    impact: Optional[str] = None
    
    class Config:
        use_enum_values = True


class ScanResponse(BaseModel):
    """Response for scan status."""
    scan_id: str
    status: ScanStatus
    url: str
    findings: Optional[List[FindingResponse]] = None
    finding_count: Optional[int] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class RepairPatchResponse(BaseModel):
    """Representation of a repair patch."""
    repair_id: str
    finding_id: str
    file_type: str  # html, css, javascript
    content: str
    selector: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    assumptions: Optional[str] = None
    explanation: Optional[str] = None


class RepairGenerateResponse(BaseModel):
    """Response for repair generation."""
    scan_id: str
    repairs: List[RepairPatchResponse]
    generation_timestamp: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RepairApproveResponse(BaseModel):
    """Response for repair approval."""
    repair_id: str
    status: ReviewStatus
    message: str
    
    class Config:
        use_enum_values = True


class PatchApplyResponse(BaseModel):
    """Response for patch application."""
    scan_id: str
    applied_count: int
    failed_count: int
    application_status: str  # success, partial, failed
    message: str
    
    class Config:
        use_enum_values = True


class VerificationResponse(BaseModel):
    """Response for verification results."""
    scan_id: str
    fixed_count: int
    new_violations_count: int
    unresolved_count: int
    before_total: int
    after_total: int
    improvement_percentage: float
    verification_timestamp: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """Standardized error response."""
    code: str = Field(..., description="Error code (e.g., INVALID_URL, SCAN_NOT_FOUND)")
    message: str = Field(..., description="Human-readable error message")
    status_code: int = Field(..., ge=400, le=599, description="HTTP status code")
    request_id: str = Field(..., description="Request ID for tracking")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(default="healthy", description="Health status")
    environment: str
    version: str
    timestamp: datetime


class InfoResponse(BaseModel):
    """API info response."""
    name: str = "AccessLens"
    version: str
    description: str = "AI-powered website accessibility detection and repair platform"
    endpoints: Dict[str, str] = Field(
        default={
            "scan": "POST /api/scan",
            "scan_status": "GET /api/scan/{scan_id}",
            "repair_generate": "POST /api/repair/generate",
            "repair_approve": "POST /api/repair/approve",
            "patch_apply": "POST /api/patch/apply",
            "verification": "GET /api/verification/{scan_id}",
            "report": "GET /api/report/{scan_id}",
        }
    )


# Batch response models

class BatchScanResponse(BaseModel):
    """Response for batch scan queries."""
    scans: List[ScanResponse]
    total: int
    page: int
    per_page: int


class BatchFindingResponse(BaseModel):
    """Response for batch finding queries."""
    findings: List[FindingResponse]
    total: int
    page: int
    per_page: int


# Validation helper functions

def validate_url_length(url: str, max_length: int = 2048) -> bool:
    """Validate URL length."""
    return len(url) <= max_length


def validate_findings_count(findings: List[Any], max_count: int = 10000) -> bool:
    """Validate findings count."""
    return len(findings) <= max_count


def validate_severity(severity: str) -> bool:
    """Validate severity value."""
    return severity in [s.value for s in Severity]


def validate_pagination(page: int = 1, per_page: int = 20, max_per_page: int = 100) -> bool:
    """Validate pagination parameters."""
    return page >= 1 and 1 <= per_page <= max_per_page
