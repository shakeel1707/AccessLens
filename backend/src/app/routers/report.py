"""
Report Download router: GET /api/report/{scan_id}
Implements report download endpoint with format negotiation and S3 integration.
"""

import logging
import json
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import JSONResponse, StreamingResponse
import boto3
from app.services.report import ReportGenerationService, ReportFormat
from app.services.database import DynamoDBClient, ScansRepository, FindingsRepository, VerificationRepository
from app.core.config import get_config

logger = logging.getLogger("accesslens.report")
router = APIRouter()

# Initialize AWS clients - lazy load to avoid circular imports
s3_client = None

def get_s3_client():
    """Get or create S3 client."""
    global s3_client
    if s3_client is None:
        s3_client = boto3.client("s3")
    return s3_client


class ReportDownloadService:
    """Service for generating, caching, and downloading reports."""
    
    def __init__(self, s3_bucket: str = None):
        config = get_config()
        self.s3_bucket = s3_bucket or config.S3_REPORTS_BUCKET
        self.cache_ttl_days = 30
        self.s3_client = get_s3_client()
    
    def get_report_s3_key(self, scan_id: str, format: str) -> str:
        """Generate S3 key for report caching."""
        return f"reports/{scan_id}/report.{format}"
    
    def generate_and_cache_report(
        self,
        scan_id: str,
        url: str,
        before_violations: list,
        after_violations: list,
        fixed_count: int,
        new_count: int,
        unresolved_count: int,
        format: str
    ) -> tuple:
        """Generate report and cache in S3, return (report_content, s3_url)."""
        
        # Generate report
        report_format = ReportFormat.JSON if format == "json" else ReportFormat.HTML
        report_content = ReportGenerationService.generate_report(
            scan_id=scan_id,
            url=url,
            before_violations=before_violations,
            after_violations=after_violations,
            fixed_count=fixed_count,
            new_count=new_count,
            unresolved_count=unresolved_count,
            report_format=report_format
        )
        
        # Upload to S3
        s3_key = self.get_report_s3_key(scan_id, format)
        content_type = "application/json" if format == "json" else "text/html"
        
        try:
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=report_content.encode("utf-8") if isinstance(report_content, str) else report_content,
                ContentType=content_type,
                Metadata={
                    "scan_id": scan_id,
                    "generated_at": datetime.utcnow().isoformat(),
                    "format": format
                }
            )
            logger.info(f"Cached report in S3: s3://{self.s3_bucket}/{s3_key}")
        except Exception as e:
            logger.warning(f"Failed to cache report in S3: {str(e)}")
        
        # Generate signed URL
        try:
            signed_url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.s3_bucket,
                    "Key": s3_key
                },
                ExpiresIn=int(self.cache_ttl_days * 24 * 3600)  # 30 days
            )
        except Exception as e:
            logger.warning(f"Failed to generate signed URL: {str(e)}")
            signed_url = None
        
        return report_content, signed_url
    
    def get_cached_report_from_s3(self, scan_id: str, format: str) -> Optional[str]:
        """Try to retrieve cached report from S3."""
        s3_key = self.get_report_s3_key(scan_id, format)
        
        try:
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=s3_key)
            report_content = response["Body"].read().decode("utf-8")
            logger.info(f"Retrieved cached report from S3: {s3_key}")
            return report_content
        except self.s3_client.exceptions.NoSuchKey:
            logger.debug(f"Cached report not found in S3: {s3_key}")
            return None
        except Exception as e:
            logger.warning(f"Error retrieving cached report from S3: {str(e)}")
            return None


@router.get("/report/{scan_id}")
async def download_report(
    scan_id: str,
    format: str = Query("json", pattern="^(json|html)$")
):
    """Download compliance report for a scan.
    
    Retrieves report from cache or generates new one from DynamoDB data.
    Supports JSON and HTML formats with 30-day S3 caching.
    
    Args:
        scan_id: Scan identifier
        format: Report format ('json' or 'html')
    
    Returns:
        Report content with appropriate content-type headers
        or S3 signed URL for download
    
    Status Codes:
        200: Report generated/retrieved successfully
        404: Scan not found
        500: Internal error
    """
    
    try:
        config = get_config()
        logger.info(f"Downloading report for scan_id={scan_id}, format={format}")
        
        # Initialize services
        db_client = DynamoDBClient(config)
        scans_repo = ScansRepository(db_client, config)
        findings_repo = FindingsRepository(db_client, config)
        verification_repo = VerificationRepository(db_client, config)
        report_service = ReportDownloadService()
        
        # Verify scan exists
        scan = scans_repo.get(scan_id)
        if not scan:
            logger.error(f"Scan not found: {scan_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scan {scan_id} not found"
            )
        
        # Try to get cached report first
        cached_report = report_service.get_cached_report_from_s3(scan_id, format)
        if cached_report:
            content_type = "application/json" if format == "json" else "text/html"
            return StreamingResponse(
                iter([cached_report]),
                media_type=content_type,
                headers={
                    "Content-Disposition": f"attachment; filename=report-{scan_id}.{format}",
                    "X-Report-Source": "cache"
                }
            )
        
        # Get findings data from DynamoDB
        findings = findings_repo.get_by_scan_id(scan_id)
        before_violations = [f.to_dict() for f in findings] if findings else []
        
        # Get verification results
        verification = verification_repo.get_by_scan_id(scan_id)
        after_violations = []
        fixed_count = 0
        new_count = 0
        unresolved_count = 0
        
        if verification:
            # Parse verification data to get after_violations and counts
            verification_dict = verification.to_dict() if hasattr(verification, 'to_dict') else verification
            after_violations = verification_dict.get("after_violations", [])
            fixed_count = verification_dict.get("fixed_count", 0)
            new_count = verification_dict.get("new_violations_count", 0)
            unresolved_count = verification_dict.get("unresolved_count", 0)
        
        # Generate report and cache
        report_content, signed_url = report_service.generate_and_cache_report(
            scan_id=scan_id,
            url=scan.url,
            before_violations=before_violations,
            after_violations=after_violations,
            fixed_count=fixed_count,
            new_count=new_count,
            unresolved_count=unresolved_count,
            format=format
        )
        
        # Return report content
        content_type = "application/json" if format == "json" else "text/html"
        
        return StreamingResponse(
            iter([report_content]),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename=report-{scan_id}.{format}",
                "X-Report-Generated": datetime.utcnow().isoformat(),
                "X-S3-Signed-URL": signed_url or "Not available"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download report"
        )


