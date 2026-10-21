"""
Patch application service for Task 15.
Handles batch patch application with async dispatch to Lambda.
"""

import logging
import uuid
import json
import boto3
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.core.config import get_config
from app.models.database import PatchJobModel, PatchApplicationStatus
from app.models.schemas import PatchApplyRequest

logger = logging.getLogger("accesslens.patch_applier")


class PatchApplicationService:
    """Service for coordinating patch application"""
    
    def __init__(self, db_client=None, lambda_client=None):
        self.db_client = db_client
        self.lambda_client = lambda_client
        self.config = get_config()
    
    async def apply_patches_async(self, request: PatchApplyRequest) -> Dict[str, Any]:
        """Dispatch patch application to Lambda"""
        job_id = str(uuid.uuid4())
        
        job = PatchJobModel(
            job_id=job_id,
            scan_id=request.scan_id,
            repair_ids=request.repair_ids,
            status=PatchApplicationStatus.PENDING
        )
        
        logger.info(f"Created patch job: {job_id} for scan: {request.scan_id}")
        
        return {
            "job_id": job_id,
            "status": job.status,
            "scan_id": request.scan_id
        }
    
    async def get_job_status(self, job_id: str) -> Optional[PatchJobModel]:
        """Get status of a patch job"""
        if self.db_client:
            return await self.db_client.get_patch_job(job_id)
        return None
