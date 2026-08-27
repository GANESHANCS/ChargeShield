"""
Pydantic Schemas for Phase 8 Real-Time Fraud Operations & Model Monitoring.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class MetricValue(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "HEALTHY"})
    value: Optional[Any] = Field(None, json_schema_extra={"example": 42})
    unit: Optional[str] = Field(None, json_schema_extra={"example": "INR"})
    note: Optional[str] = Field(None, json_schema_extra={"example": "Calculated from real DB records"})


class OperationsOverviewResponse(BaseModel):
    total_active_disputes: int
    pending_human_reviews: int
    high_risk_cases: int
    critical_risk_cases: int
    total_disputed_value: float
    estimated_recoverable_value: float
    decisions_today: int
    contest_rate: float
    do_not_contest_rate: float
    escalation_rate: float
    average_review_time: MetricValue
    evidence_verification_status: str
    data_quality_status: str
    model_status: str
    audit_system_status: str
    currency: str = "INR"
    last_updated: str


class OperationalAlert(BaseModel):
    alert_id: str
    severity: str  # INFO, WARNING, HIGH, CRITICAL
    category: str  # HIGH_RISK_VOLUME, CRITICAL_VALUE_EXPOSURE, REVIEW_BACKLOG, DATA_QUALITY_DEGRADATION, MODEL_DRIFT, EVIDENCE_QUALITY_DEGRADATION, HIGH_CONTEST_DISAGREEMENT, SYSTEM_HEALTH, AUDIT_ANOMALY
    title: str
    description: str
    detected_at: str
    related_metric: Optional[str] = None
    recommended_action: str
    status: str = "ACTIVE"  # ACTIVE, ACKNOWLEDGED, RESOLVED


class ModelMonitoringResponse(BaseModel):
    current_model: str
    model_version: str
    prediction_count: int
    average_predicted_probability: float
    prediction_distribution: Dict[str, int]
    positive_prediction_rate: float
    threshold_in_use: float
    baseline_availability: bool
    drift_status: str  # HEALTHY, WARNING, DRIFT_DETECTED, AWAITING_BASELINE, INSUFFICIENT_DATA
    performance_status: str
    data_state_label: str  # PRODUCTION, HISTORICAL, SIMULATION, INSUFFICIENT_DATA, AWAITING_BASELINE
    last_evaluated: str


class DisagreementCase(BaseModel):
    dispute_id: str
    disputed_amount: float
    ai_recommendation: str
    ai_win_probability: float
    human_decision: str
    reviewer_id: str
    justification: str
    created_at: str


class ModelFeedbackResponse(BaseModel):
    total_human_decisions: int
    agreement_count: int
    disagreement_count: int
    agreement_rate: float
    disagreement_rate: float
    override_rate: float
    escalation_rate: float
    disagreement_cases: List[DisagreementCase]
    data_state_label: str


class TimelineEvent(BaseModel):
    event_id: str
    stage: str
    title: str
    description: str
    timestamp: Optional[str] = None
    status: str  # COMPLETED, IN_PROGRESS, PENDING
    actor: str  # SYSTEM, MODEL, HUMAN_AGENT
    metadata: Optional[Dict[str, Any]] = None


class CaseTimelineResponse(BaseModel):
    dispute_id: str
    events: List[TimelineEvent]
    current_stage: str
    overall_status: str
