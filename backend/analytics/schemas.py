from typing import Dict, Optional
from pydantic import BaseModel, Field

class OperationalMetrics(BaseModel):
    total_cases: int = Field(..., description="Total dispute cases in platform")
    pending_review: int = Field(..., description="Cases pending review")
    in_review: int = Field(..., description="Cases in active review")
    decided: int = Field(..., description="Cases with human decisions")
    escalated: int = Field(..., description="Escalated cases")
    contest_decisions: int = Field(..., description="Human CONTEST decisions")
    do_not_contest_decisions: int = Field(..., description="Human DO_NOT_CONTEST decisions")
    escalations: int = Field(..., description="Human ESCALATE decisions")
    avg_review_activity: str = Field(..., description="Average review activity metric")

class FinancialAnalytics(BaseModel):
    total_disputed_value: float = Field(..., description="Total value of all disputes")
    contest_value: float = Field(..., description="Total value associated with CONTEST decisions")
    do_not_contest_value: float = Field(..., description="Total value associated with DO_NOT_CONTEST decisions")
    escalate_value: float = Field(..., description="Total value associated with ESCALATE decisions")
    simulated_recoverable_value: float = Field(..., description="Model-derived recoverable value (win_prob * amount for contest decisions)")
    currency: str = Field("INR", description="Currency symbol")
    disclaimer: str = Field(
        "Synthetic / simulated data derived from LightGBM win probability and dispute amounts.",
        description="Synthetic data disclaimer"
    )

class DecisionAnalytics(BaseModel):
    ai_recommendation_distribution: Dict[str, int] = Field(..., description="Distribution of AI recommendations")
    human_decision_distribution: Dict[str, int] = Field(..., description="Distribution of human decisions")
    agreement_rate: float = Field(..., description="Rate of agreement between AI recommendation and human decision")
    disagreement_count: int = Field(..., description="Count of cases where human decision differed from AI recommendation")
    total_human_decisions: int = Field(..., description="Total recorded human decisions")
    escalation_rate: float = Field(..., description="Ratio of escalations to total human decisions")

class RiskAnalytics(BaseModel):
    win_probability_buckets: Dict[str, int] = Field(..., description="Cases grouped by win probability range")
    dispute_reason_distribution: Dict[str, int] = Field(..., description="Cases grouped by dispute reason code")
    disputed_amount_distribution: Dict[str, int] = Field(..., description="Cases grouped by disputed amount brackets")
    high_priority_count: int = Field(..., description="Cases flagged as high priority")

class EvidenceAnalytics(BaseModel):
    total_cases_analyzed: int = Field(..., description="Total cases with evidence analyzed")
    verified_evidence_count: int = Field(..., description="Total verified evidence items")
    mismatched_evidence_count: int = Field(..., description="Total mismatched evidence items")
    unverifiable_evidence_count: int = Field(..., description="Total unverifiable evidence items")
    overall_verification_rate: float = Field(..., description="Overall verification rate across evidence claims")
    has_historical_persistence: bool = Field(True, description="Whether evidence verification is persisted")
    note: str = Field("Live backend evidence verification engine cross-referencing authoritative relational dataset.", description="Notes on evidence history")

class SubsystemStatus(BaseModel):
    api: str = Field(..., description="API subsystem health status")
    database: str = Field(..., description="SQLite database connectivity status")
    ml_engine: str = Field(..., description="ML Win-Probability engine readiness")
    evidence_engine: str = Field(..., description="Evidence verification engine status")
    review_engine: str = Field(..., description="Review workflow engine status")
    dataset: str = Field(..., description="Synthetic relational dataset availability")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of status check")

class AnalyticsOverviewResponse(BaseModel):
    operational: OperationalMetrics
    financial: FinancialAnalytics
    decisions: DecisionAnalytics
    risk: RiskAnalytics
    evidence: EvidenceAnalytics
    health: SubsystemStatus
    generated_at: str

class OperationalReportResponse(BaseModel):
    report_id: str
    generated_at: str
    disclaimer: str
    model_version: str
    operational_metrics: OperationalMetrics
    financial_analytics: FinancialAnalytics
    decision_analytics: DecisionAnalytics
    risk_analytics: RiskAnalytics
    evidence_analytics: EvidenceAnalytics
    subsystem_health: SubsystemStatus
