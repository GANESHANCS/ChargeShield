"""
Pydantic Schemas for Case Workflow, SLA, Evidence Confidence & Outcome Operations.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class AssignmentRequest(BaseModel):
    reviewer_id: str = Field(..., description="ID of the assigned reviewer (e.g., RVR_001)")
    actor_id: Optional[str] = Field(None, description="ID of the actor performing the assignment")

class StatusUpdateRequest(BaseModel):
    status: str = Field(..., description="New workflow status (NEW, IN_REVIEW, ESCALATED, DECISION_PENDING, RESOLVED, CLOSED)")
    actor_id: Optional[str] = Field("SYSTEM", description="ID of actor performing status change")
    reason: Optional[str] = Field(None, description="Reason for status change or administrative override")

class NoteCreateRequest(BaseModel):
    author_id: str = Field(..., description="Author ID of the review note")
    note_text: str = Field(..., description="Content of the review note")

class NoteResponse(BaseModel):
    note_id: str
    dispute_id: str
    author_id: str
    note_text: str
    timestamp: str

class ActivityItemResponse(BaseModel):
    activity_id: str
    dispute_id: str
    event_type: str
    actor: str
    timestamp: str
    action: str
    previous_state: str
    new_state: str
    reason: str

class CaseWorkflowStateResponse(BaseModel):
    dispute_id: str
    status: str
    assigned_reviewer_id: str
    notes_count: int
    last_activity_at: str
    data_state: str = "PRODUCTION"

class SLABreakdownResponse(BaseModel):
    sla_status: str
    hours_remaining: Optional[float] = None
    is_overdue: bool
    urgency_score: float
    review_priority: str
    priority_explanation: str
    deadline: Optional[str] = None
    data_state: str = "PRODUCTION"

class EvidenceConfidenceResponse(BaseModel):
    evidence_confidence_score: float
    evidence_status: str
    verification_summary: str
    missing_evidence: List[str]
    conflicting_evidence: List[str]
    pod_signature_present: bool
    cvv_match: str
    avs_match: str
    delivery_status: str
    data_state: str = "PRODUCTION"

class OutcomeOverviewResponse(BaseModel):
    total_reviewed: int
    contest_count: int
    do_not_contest_count: int
    escalate_count: int
    contest_percentage: float = 0.0
    do_not_contest_percentage: float = 0.0
    escalate_percentage: float = 0.0
    agreement_rate: float
    disagreement_rate: float
    total_disputed_exposure: float
    average_disputed_amount: float
    estimated_recoverable_value: float
    model_estimate_status: str
    human_decision_status: str
    actual_outcome_status: str
    actual_outcome_message: str
    data_state: str = "PRODUCTION"
