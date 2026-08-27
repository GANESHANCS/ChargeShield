"""
Pydantic Schemas for Phase 4 Read-Only AI Risk Investigation Agent.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class InvestigationRecommendation(BaseModel):
    action: str = Field(description="CONTEST, MANUAL_REVIEW, or DO_NOT_CONTEST")
    win_probability: float = Field(ge=0.0, le=1.0)
    confidence_level: str = Field(description="HIGH, MEDIUM, or LOW based on probability cutoff")
    reason: str

class TimelineEvent(BaseModel):
    timestamp: str
    event_type: str = Field(description="ORDER_CREATED, PAYMENT_CAPTURED, SHIPMENT_DISPATCHED, DELIVERY_COMPLETED, SUPPORT_INTERACTION, DISPUTE_FILED")
    description: str
    source_id: str

class FactorItem(BaseModel):
    title: str
    explanation: str
    source_id: str
    type: str = Field(description="FACT or MODEL_SIGNAL")

class EvidenceItem(BaseModel):
    evidence_id: str
    source_type: str = Field(description="DISPUTE, CUSTOMER, TRANSACTION, ORDER, DELIVERY, COMMUNICATION")
    source_id: str
    source_field: Optional[str] = Field(default=None, description="Specific field on source entity being claimed")
    claim: str
    value: str = Field(description="Alias for claimed_value for backward compatibility")
    claimed_value: Optional[str] = Field(default=None, description="Structured value being claimed")
    timestamp: Optional[str] = None
    verification_status: str = Field(default="UNVERIFIED", description="UNVERIFIED (Verification executed in Phase 5)")

class MLAssessmentPayload(BaseModel):
    win_probability: float
    win_probability_percent: str
    recommendation: str
    model_version: str
    decision_threshold: float

class InvestigationReport(BaseModel):
    dispute_id: str
    investigation_status: str = Field(default="COMPLETED")
    executive_summary: str
    recommendation: InvestigationRecommendation
    case_facts: List[str]
    timeline: List[TimelineEvent]
    supporting_factors: List[FactorItem]
    risk_factors: List[FactorItem]
    ml_assessment: MLAssessmentPayload
    evidence: List[EvidenceItem]
    open_questions: List[str]
    human_review_items: List[str]
    investigation_timestamp: str
    is_synthetic_data: bool = True
    disclaimer: str = "READ-ONLY DECISION SUPPORT. Final financial actions require human authorization."
