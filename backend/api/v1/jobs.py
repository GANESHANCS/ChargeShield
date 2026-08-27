"""
API Router for Background Job Execution Status & Polling.
Exposes endpoints to query the status of asynchronous background tasks (ingestion, bulk processing, reports).
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends

from backend.core.jobs import job_manager
from backend.api.dependencies import get_current_user
from backend.db.models import UserModel

router = APIRouter(prefix="/api/v1/jobs", tags=["Background Jobs Architecture"])


@router.get("/{job_id}", summary="Get Background Job Status & Result")
async def get_job_status(
    job_id: str,
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Returns live background job status, progress percentage, execution result or error.
    """
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Background job '{job_id}' not found."
        )
    return {
        "status": "SUCCESS",
        "job": job
    }
