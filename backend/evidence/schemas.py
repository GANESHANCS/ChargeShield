"""
Pydantic Schemas for Phase 5 Evidence Verification & Citation Engine.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.agent.schemas import InvestigationReport

class SourceReference(BaseModel):
    entity_type: str = Field(description="DISPUTE, CUSTOMER, TRANSACTION, ORDER, DELIVERY, COMMUNICATION, ML_MODEL")
    entity_id: str
    field: Optional[str] = Field(default=None, description="Field name on source entity")

class VerificationResult(BaseModel):
    evidence_id: str
    source_type: str
    source_id: str
    source_field: Optional[str] = None
    claim: str
    claimed_value: Optional[str] = None
    actual_source_value: Optional[str] = None
    verification_status: str = Field(description="VERIFIED, MISMATCH, MISSING_SOURCE, UNSUPPORTED, UNVERIFIABLE")
    match_type: str = Field(description="EXACT, NORMALIZED_MATCH, PARTIAL_MATCH, MISMATCH, NOT_APPLICABLE")
    verification_reason: str
    citation_label: str = Field(description="Human-readable citation label, e.g. Delivery DEL_002528 -> delivery_status")
    source_reference: SourceReference

class VerificationSummary(BaseModel):
    total_evidence: int
    verified: int
    mismatched: int
    missing_source: int
    unsupported: int
    unverifiable: int
    verification_rate: float = Field(ge=0.0, le=1.0)

class VerifiedInvestigationResponse(BaseModel):
    dispute_id: str
    investigation: InvestigationReport
    verification_summary: VerificationSummary
    verification_results: List[VerificationResult]
    is_synthetic_data: bool = True
    disclaimer: str = "READ-ONLY DECISION SUPPORT. Final financial actions require human authorization."
