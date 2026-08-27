"""
FastAPI Router for Phase 6 & Phase 8 Persistent Human Review Workflow & Audit Log.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.review.schemas import (
    ReviewQueueResponse, ReviewCasePackage, DecisionRequest, DecisionRecord, AuditLogResponse
)
from backend.review.service import review_service, DuplicateDecisionError

router = APIRouter(prefix="/api/v1/review", tags=["Human Review Workflow"])

@router.get("/queue", response_model=ReviewQueueResponse, summary="Get Ordered Review Queue")
async def get_review_queue(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by review status (PENDING_REVIEW, IN_REVIEW, DECIDED, ESCALATED)"),
    recommendation: Optional[str] = Query(None, description="Filter by AI recommendation (CONTEST, DO_NOT_CONTEST)"),
    min_prob: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum AI win probability"),
    max_prob: Optional[float] = Query(None, ge=0.0, le=1.0, description="Maximum AI win probability"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size limit")
):
    """
    Returns paginated, ordered review queue of pending/decided cases for human risk analysts.
    Cases are prioritized based on threshold proximity, verification status, and disputed amount.
    """
    try:
        queue_resp = review_service.get_queue(
            status=status_filter,
            recommendation=recommendation,
            min_prob=min_prob,
            max_prob=max_prob,
            page=page,
            page_size=page_size
        )
        return queue_resp
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve review queue: {str(e)}"
        )

@router.get("/audit", response_model=AuditLogResponse, summary="Get Persistent Human Review Decision Audit Log")
async def get_review_audit_log(
    dispute_id: Optional[str] = Query(None, description="Filter by dispute ID"),
    reviewer_id: Optional[str] = Query(None, description="Filter by human reviewer ID"),
    decision: Optional[str] = Query(None, description="Filter by human decision (CONTEST, DO_NOT_CONTEST, ESCALATE)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size limit")
):
    """
    Returns paginated audit log of persistent human reviewer decisions stored in SQLite (chargeshield.db).
    """
    try:
        audit_resp = review_service.get_audit_log(
            dispute_id=dispute_id,
            reviewer_id=reviewer_id,
            decision=decision,
            page=page,
            page_size=page_size
        )
        return audit_resp
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit log: {str(e)}"
        )

@router.get("/cases/{dispute_id}", response_model=ReviewCasePackage, summary="Get Complete Reviewer Package")
async def get_review_case_package(dispute_id: str):
    """
    Returns complete reviewer package aggregating Case Detail, ML Prediction, Phase 4 Investigation,
    Phase 5 Evidence Verification, and Decision History.
    """
    try:
        package = review_service.get_review_package(dispute_id)
        return package
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assemble review package: {str(e)}"
        )

@router.post("/cases/{dispute_id}/decision", response_model=DecisionRecord, summary="Submit Human Reviewer Decision")
async def submit_human_decision(dispute_id: str, request: DecisionRequest):
    """
    Submits a human reviewer decision (CONTEST, DO_NOT_CONTEST, or ESCALATE) with mandatory justification reason.
    Records decision immutably into SQLite database and updates case review state.
    """
    try:
        record = review_service.submit_decision(dispute_id, request)
        return record
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        else:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)
    except DuplicateDecisionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record decision: {str(e)}"
        )
