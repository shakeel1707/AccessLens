"""
Patch router: POST /api/patch/apply (Task 15)
"""

import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.config import get_config
from app.models.schemas import PatchApplyRequest, PatchApplyResponse
from app.services.patch_applier import PatchApplicationService

logger = logging.getLogger("accesslens.patch")
router = APIRouter()


@router.post("/patch/apply", status_code=status.HTTP_202_ACCEPTED, response_model=PatchApplyResponse)
async def apply_patches(request: PatchApplyRequest):
    """Apply approved patches to an isolated website copy.
    
    Task 15: Patch Application Endpoint
    
    Args:
        scan_id: Scan identifier
        repair_ids: List of approved repair IDs to apply (1-100)
    
    Returns:
        202 ACCEPTED with job status
    """
    config = get_config()
    
    try:
        if not request.repair_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="repair_ids must not be empty"
            )
        
        service = PatchApplicationService()
        job_info = await service.apply_patches_async(request)
        
        logger.info(f"Patch application started: job_id={job_info['job_id']}, repairs={len(request.repair_ids)}")
        
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "scan_id": request.scan_id,
                "applied_count": 0,
                "failed_count": 0,
                "application_status": "in_progress",
                "message": f"Patch application job {job_info['job_id']} started"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying patches: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start patch application"
        )
