"""
Verification router: GET /verification/{scan_id}
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/verification/{scan_id}")
async def get_verification_results(scan_id: str):
    """Get verification results after patch application.
    
    Args:
        scan_id: Scan identifier
    
    Returns:
        { scan_id, fixed_count, new_violations, unresolved, comparison, message }
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "scan_id": scan_id,
            "fixed_count": 0,
            "new_violations_count": 0,
            "unresolved_count": 0,
            "comparison": {},
            "message": "Verification not yet available",
        }
    )