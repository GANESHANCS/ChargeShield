"""
API v1 Controller for Case Work Management, SLA, Evidence Confidence & Outcome Operations.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status

from backend.schemas.case_workflow import (
    AssignmentRequest,
    StatusUpdateRequest,
    NoteCreateRequest,
    NoteResponse,
    ActivityItemResponse,
    CaseWorkflowStateResponse,
    SLABreakdownResponse,
    EvidenceConfidenceResponse,
    OutcomeOverviewResponse
)
from backend.services.case_workflow_service import case_workflow_service
from backend.services.case_service import CaseService
from backend.services.sla_service import sla_service
from backend.services.evidence_confidence_service import evidence_confidence_service
from backend.services.outcome_service import outcome_service
from backend.services.outcome_feedback_service import outcome_feedback_service

router = APIRouter(tags=["case-workflow"])
case_service_inst = CaseService()

@router.patch("/api/v1/cases/{dispute_id}/assignment", response_model=Dict[str, Any])
def assign_case(dispute_id: str, req: AssignmentRequest):
    """Assigns a reviewer to a dispute and logs action lineage."""
    try:
        res = case_workflow_service.assign_case(
            dispute_id=dispute_id,
            reviewer_id=req.reviewer_id,
            actor_id=req.actor_id
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/api/v1/cases/{dispute_id}/status", response_model=Dict[str, Any])
def update_case_status(dispute_id: str, req: StatusUpdateRequest):
    """Updates case workflow status with transition validation."""
    try:
        res = case_workflow_service.update_status(
            dispute_id=dispute_id,
            new_status=req.status,
            actor_id=req.actor_id or "SYSTEM",
            reason=req.reason
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/cases/{dispute_id}/notes", response_model=Dict[str, Any])
def add_case_note(dispute_id: str, req: NoteCreateRequest):
    """Adds a review note to a case and logs activity trace."""
    try:
        res = case_workflow_service.add_note(
            dispute_id=dispute_id,
            author_id=req.author_id,
            note_text=req.note_text
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/cases/{dispute_id}/notes", response_model=List[NoteResponse])
def get_case_notes(dispute_id: str):
    """Retrieves all review notes for a case."""
    notes = case_workflow_service.get_notes(dispute_id)
    return notes

@router.get("/api/v1/cases/{dispute_id}/activity", response_model=List[ActivityItemResponse])
def get_case_activity(dispute_id: str):
    """Retrieves complete action lineage activity trace for a dispute."""
    trace = case_workflow_service.get_activity_trace(dispute_id)
    return trace

@router.get("/api/v1/cases/{dispute_id}/sla", response_model=SLABreakdownResponse)
def get_case_sla(dispute_id: str):
    """Calculates SLA deadline status, time remaining, and review priority."""
    try:
        detail = case_service_inst.get_case_detail(dispute_id)
        if not detail:
            raise HTTPException(status_code=404, detail=f"Dispute {dispute_id} not found")
        dispute = detail.get("dispute", {})
        financial = detail.get("financial", {})
        risk = detail.get("risk", {})
        
        sla_info = sla_service.calculate_sla(
            response_deadline_iso=dispute.get("response_deadline"),
            disputed_amount=dispute.get("disputed_amount", 0.0),
            win_probability=financial.get("win_probability", 0.5),
            risk_score=risk.get("auth_risk_score", 0.5),
            evidence_confidence=0.75
        )
        return sla_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/cases/{dispute_id}/evidence-confidence", response_model=EvidenceConfidenceResponse)
def get_evidence_confidence(dispute_id: str):
    """Calculates evidence confidence score and verification summary."""
    try:
        detail = case_service_inst.get_case_detail(dispute_id)
        if not detail:
            raise HTTPException(status_code=404, detail=f"Dispute {dispute_id} not found")
        res = evidence_confidence_service.evaluate_evidence(detail)
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/outcomes/overview", response_model=OutcomeOverviewResponse)
def get_outcome_overview():
    """Retrieves outcome intelligence and recorded human decision metrics."""
    res = outcome_service.get_outcome_metrics()
    return res

@router.get("/api/v1/outcomes/feedback", response_model=Dict[str, Any])
def get_outcome_feedback():
    """Retrieves model feedback metrics against actual adjudicated bank outcomes."""
    res = outcome_feedback_service.evaluate_model_feedback()
    return res
