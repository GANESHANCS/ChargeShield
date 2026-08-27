"""
Package Init for ChargeShield Evidence Verification Subsystem.
"""

from backend.evidence.verifier import EvidenceVerifier, evidence_verifier
from backend.evidence.schemas import (
    SourceReference, VerificationResult, VerificationSummary, VerifiedInvestigationResponse
)

__all__ = [
    "EvidenceVerifier",
    "evidence_verifier",
    "SourceReference",
    "VerificationResult",
    "VerificationSummary",
    "VerifiedInvestigationResponse"
]
