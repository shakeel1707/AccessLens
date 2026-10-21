"""Scanning router with error handling and retry logic"""
import logging
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
import uuid
from app.core.validators import URLValidator
from app.core.config import get_config
from app.models.schemas import ScanRequest, ScanResponse, FindingResponse, ScanStatus
from app.models.database import ScanModel, FindingModel, Severity
from app.services.database import DynamoDBClient, ScansRepository, FindingsRepository
from app.services.scanner import PlaywrightScanner
from app.services.finding_service import FindingIDGenerator, FindingDeduplicator, FindingSortingService

logger = logging.getLogger("accesslens.scan")
router = APIRouter()

_scanner_instance = None

async def get_scanner():
    global _scanner_instance
    if _scanner_instance is None:
        config = get_config()
        _scanner_instance = PlaywrightScanner(timeout_seconds=config.SCAN_TIMEOUT_SECONDS, headless=True)
        await _scanner_instance.initialize()
    return _scanner_instance

async def perform_scan(scan_id: str, url: str, user_id: str, db_client, config):
    """Perform accessibility scan with exponential backoff retry logic.
    
    Implements max 2 retries with exponential backoff (1s, 2s delays).
    Handles network timeouts, invalid HTML, and browser crashes gracefully.
    """
    scans_repo = ScansRepository(db_client, config)
    findings_repo = FindingsRepository(db_client, config)
    
    max_retries = 2
    base_delay = 1  # seconds
    
    for attempt in range(max_retries + 1):
        try:
            # Update scan status to in_progress
            scan = _get_scan_by_id_sync(scan_id, db_client, config)
            if scan:
                scan.status = ScanStatus.IN_PROGRESS
                scan.updated_at = datetime.utcnow().isoformat()
                scans_repo.update(scan)
                logger.info(f"Scan {scan_id} in_progress (attempt {attempt + 1}/{max_retries + 1})")
            
            # Get scanner instance
            scanner = await get_scanner()
            
            # Perform scan
            logger.info(f"Starting scan for URL: {url}")
            scan_result = await scanner.scan(url)
            logger.info(f"Scan completed for {url}. Found {len(scan_result.findings)} violations.")
            
            # Extract findings from scan result
            findings = []
            for violation in scan_result.findings:
                # Generate deterministic ID
                finding_id = FindingIDGenerator.generate_id(
                    rule_id=violation.rule_id,
                    selector=violation.selector,
                    description=violation.description,
                )
                
                # Map severity
                severity = Severity(violation.severity) if hasattr(Severity, violation.severity.upper()) else Severity.MODERATE
                
                finding = FindingModel(
                    scan_id=scan_id,
                    finding_id=finding_id,
                    rule_id=violation.rule_id,
                    severity=severity,
                    selector=violation.selector,
                    html_snippet=violation.html,
                    description=violation.description,
                    created_at=datetime.utcnow().isoformat(),
                )
                findings.append(finding)
            
            # Deduplicate findings
            unique_findings = FindingDeduplicator.deduplicate(findings)
            logger.info(f"After deduplication: {len(unique_findings)} unique findings")
            
            # Sort by severity
            sorted_findings = FindingSortingService.sort_by_severity(unique_findings)
            
            # Persist findings to DynamoDB
            for finding in sorted_findings:
                findings_repo.create(finding)
            
            # Update scan status to completed
            scan = _get_scan_by_id_sync(scan_id, db_client, config)
            if scan:
                scan.status = ScanStatus.COMPLETED
                scan.finding_count = len(sorted_findings)
                scan.updated_at = datetime.utcnow().isoformat()
                scans_repo.update(scan)
                logger.info(f"Scan {scan_id} completed successfully with {len(sorted_findings)} findings")
            
            return  # Success - exit retry loop
        
        except asyncio.TimeoutError as e:
            logger.warning(f"Scan {scan_id} timeout (attempt {attempt + 1}/{max_retries + 1}): {str(e)}")
            error_msg = f"Scan timed out after {config.SCAN_TIMEOUT_SECONDS}s"
            
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)  # Exponential backoff: 1s, 2s
                logger.info(f"Retrying scan {scan_id} in {delay}s...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"Scan {scan_id} failed after {max_retries + 1} attempts: {error_msg}")
                _mark_scan_failed(scan_id, db_client, config, error_msg)
                return
        
        except Exception as e:
            error_type = type(e).__name__
            error_msg_base = f"{error_type}: {str(e)}"
            logger.warning(f"Scan {scan_id} failed (attempt {attempt + 1}/{max_retries + 1}): {error_msg_base}")
            
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)  # Exponential backoff: 1s, 2s
                logger.info(f"Retrying scan {scan_id} in {delay}s...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"Scan {scan_id} failed after {max_retries + 1} attempts: {error_msg_base}")
                _mark_scan_failed(scan_id, db_client, config, error_msg_base)
                return


def _mark_scan_failed(scan_id: str, db_client, config, error_message: str):
    """Mark scan as failed and persist error message."""
    try:
        scans_repo = ScansRepository(db_client, config)
        scan = scans_repo.get(scan_id)
        if scan:
            scan.status = ScanStatus.FAILED
            scan.error_message = error_message
            scan.updated_at = datetime.utcnow().isoformat()
            scans_repo.update(scan)
            logger.info(f"Scan {scan_id} marked as failed: {error_message}")
    except Exception as update_error:
        logger.error(f"Failed to update scan status for {scan_id}: {str(update_error)}")


def _get_scan_by_id_sync(scan_id: str, db_client, config) -> Optional[ScanModel]:
    """Synchronous helper to get scan by ID."""
    scans_repo = ScansRepository(db_client, config)
    return scans_repo.get(scan_id)


@router.post("/scan", status_code=status.HTTP_202_ACCEPTED, response_model=ScanResponse)
async def submit_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
):
    """Submit a website for accessibility scanning.
    
    Validates URL, creates scan record, and dispatches async background task.
    Returns immediately with scan_id and status='pending'.
    """
    config = get_config()
    
    try:
        # Validate URL using URLValidator
        validator = URLValidator(
            allowed_domains=config.ALLOWED_DOMAINS,
            max_redirects=5,
            redirect_timeout=5.0,
        )
        validation_result = validator.validate(request.url)
        
        if not validation_result.is_valid:
            logger.warning(f"URL validation failed: {validation_result.error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid URL: {validation_result.error}",
            )
        
        # Initialize DynamoDB client and repository
        db_client = DynamoDBClient(config)
        scans_repo = ScansRepository(db_client, config)
        
        # Create scan record
        scan = ScanModel(
            scan_id=str(uuid.uuid4()),
            url=request.url,
            user_id="demo-user",
            status=ScanStatus.PENDING,
            timestamp=datetime.utcnow().isoformat(),
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )
        
        # Persist to DynamoDB
        scans_repo.create(scan)
        logger.info(f"Scan created: {scan.scan_id}")
        
        # Dispatch async background task with retry support
        background_tasks.add_task(
            perform_scan,
            scan_id=scan.scan_id,
            url=request.url,
            user_id=scan.user_id,
            db_client=db_client,
            config=config,
        )
        
        # Return response
        return ScanResponse(
            scan_id=scan.scan_id,
            status=ScanStatus.PENDING,
            url=request.url,
            findings=None,
            finding_count=0,
            created_at=scan.created_at,
            completed_at=None,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting scan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit scan",
        )


@router.get("/scan/{scan_id}", response_model=ScanResponse)
async def get_scan_status(scan_id: str):
    """Get scan status and findings.
    
    Returns scan status from DynamoDB with findings if completed.
    Includes error_message if scan failed.
    """
    config = get_config()
    
    try:
        # Get scan from DynamoDB
        db_client = DynamoDBClient(config)
        scans_repo = ScansRepository(db_client, config)
        scan = scans_repo.get(scan_id)
        
        if not scan:
            logger.warning(f"Scan not found: {scan_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scan {scan_id} not found",
            )
        
        # Get findings if scan is completed
        findings_data = None
        if scan.status == ScanStatus.COMPLETED:
            findings_repo = FindingsRepository(db_client, config)
            finding_models = findings_repo.query_by_scan(scan_id)
            
            # Convert to response format
            findings_data = [
                FindingResponse(
                    finding_id=f.finding_id,
                    rule_id=f.rule_id,
                    selector=f.selector,
                    description=f.description,
                    severity=f.severity,
                    html=f.html_snippet,
                    impact=None,
                )
                for f in finding_models
            ]
        
        # Build response
        return ScanResponse(
            scan_id=scan.scan_id,
            status=scan.status,
            url=scan.url,
            findings=findings_data,
            finding_count=scan.finding_count,
            error_message=scan.error_message,
            created_at=scan.created_at,
            completed_at=scan.updated_at if scan.status == ScanStatus.COMPLETED else None,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving scan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve scan",
        )


@router.get("/scan/{scan_id}/findings", response_model=list[FindingResponse])
async def get_scan_findings(scan_id: str):
    """Get deduplicated findings for a scan, sorted by severity.
    
    Retrieves all findings for a completed scan from DynamoDB.
    Findings are returned sorted by severity (critical ? minor).
    """
    config = get_config()
    
    try:
        # Get scan from DynamoDB
        db_client = DynamoDBClient(config)
        scans_repo = ScansRepository(db_client, config)
        scan = scans_repo.get(scan_id)
        
        if not scan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Scan {scan_id} not found")
        
        # Check if scan is completed
        if scan.status != ScanStatus.COMPLETED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Scan status is {scan.status}, not completed")
        
        # Get findings
        findings_repo = FindingsRepository(db_client, config)
        finding_models = findings_repo.query_by_scan(scan_id)
        
        # Convert to response format and return
        findings_data = [
            FindingResponse(
                finding_id=f.finding_id,
                rule_id=f.rule_id,
                selector=f.selector,
                description=f.description,
                severity=f.severity,
                html=f.html_snippet,
                impact=None,
            )
            for f in finding_models
        ]
        
        return findings_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving findings: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve findings")
