"""
Pydantic Schemas for ChargeShield Phase 6 & Phase 8 Persistent Human Review Workflow.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from backend.schemas.cases import CaseDetailResponse
from backend.schemas.predictions import PredictionResponse
from backend.agent.schemas import InvestigationReport
from backend.evidence.schemas import VerifiedInvestigationResponse

class DecisionEnum(str, Enum):
    CONTEST = "CONTEST"
    DO_NOT_CONTEST = "DO_NOT_CONTEST"
    ESCALATE = "ESCALATE"

class ReviewStateEnum(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    IN_REVIEW = "IN_REVIEW"
    DECIDED = "DECIDED"
    ESCALATED = "ESCALATED"

class ReviewQueueItem(BaseModel):
    dispute_id: str
    disputed_amount: float
    currency: str = "INR"
    dispute_reason: str
    win_probability: float
    ai_recommendation: str
    verification_rate: float
    review_status: ReviewStateEnum
    priority_score: float
    created_at: str

class ReviewQueueResponse(BaseModel):
    items: List[ReviewQueueItem]
    total: int
    pending_count: int
    decided_count: int
    escalated_count: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 1

class DecisionRequest(BaseModel):
    reviewer_id: str = Field(description="Identifier of human reviewer")
    decision: DecisionEnum
    reason: str = Field(description="Mandatory justification for human review decision")

    @field_validator("reviewer_id")
    def validate_reviewer_id(cls, v: str) -> str:
        clean = v.strip()
        if not clean or clean.lower() in ["none", "null", "undefined"]:
            raise ValueError("Reviewer ID cannot be empty.")
        return clean

    @field_validator("reason")
    def validate_reason(cls, v: str) -> str:
        clean = v.strip()
        if not clean or len(clean) < 5 or clean.lower() in ["test", "abc", "asdf", "123", "none"]:
            raise ValueError("A meaningful decision reason (at least 5 characters) is required.")
        return clean

class DecisionRecord(BaseModel):
    decision_id: str
    dispute_id: str
    reviewer_id: str
    decision: DecisionEnum
    reason: str
    ai_recommendation: str
    ai_win_probability: float
    verification_rate: float
    created_at: str

class AuditLogResponse(BaseModel):
    items: List[DecisionRecord]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 1
    is_synthetic_data: bool = True
    disclaimer: str = "HUMAN AUTHORIZATION REQUIRED. AI output is advisory only."

class ReviewCasePackage(BaseModel):
    dispute_id: str
    case: CaseDetailResponse
    prediction: PredictionResponse
    investigation: InvestigationReport
    verification: VerifiedInvestigationResponse
    review_status: ReviewStateEnum
    decisions: List[DecisionRecord]
    is_synthetic_data: bool = True
    disclaimer: str = "HUMAN AUTHORIZATION REQUIRED. AI output is advisory only."
