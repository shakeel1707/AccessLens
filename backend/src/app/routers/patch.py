"""
Patch router: POST /patch/apply
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post("/patch/apply", status_code=status.HTTP_202_ACCEPTED)
async def apply_patches(scan_id: str, repair_ids: list[str]):
    """Apply approved patches to an isolated website copy.
    
    Args:
        scan_id: Scan identifier
        repair_ids: List of approved repair IDs to apply
    
    Returns:
        { scan_id, application_status, message }
    """
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "scan_id": scan_id,
            "application_status": "in_progress",
            "message": "Patch application started in isolated environment",
        }
    )