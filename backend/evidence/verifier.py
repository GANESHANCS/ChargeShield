"""
Evidence Verifier Orchestrator for ChargeShield Phase 5.
Executes automated claim verification against Phase 3 service records and Phase 2 ML outputs.
"""

from typing import List, Dict, Any, Optional
from backend.agent.schemas import InvestigationReport, EvidenceItem
from backend.evidence.schemas import (
    VerificationResult, VerificationSummary, VerifiedInvestigationResponse, SourceReference
)
from backend.evidence.sources import get_source_record
from backend.evidence.comparator import compare_values
from backend.evidence.citations import generate_citation
from backend.services.prediction_service import prediction_service
from backend.core.logging import logger

class EvidenceVerifier:
    """Read-only automated evidence verifier and citation engine."""

    def verify_investigation(self, dispute_id: str, report: InvestigationReport) -> VerifiedInvestigationResponse:
        """
        Iterates over all evidence items in an InvestigationReport and verifies each claim
        against authoritative Phase 3 relational records and Phase 2 ML predictions.
        """
        logger.info(f"Starting evidence verification for dispute {dispute_id}...")
        
        results: List[VerificationResult] = []
        
        # 1. Field-Level Evidence Items Verification
        for item in report.evidence:
            res = self._verify_evidence_item(dispute_id, item)
            results.append(res)

        # 2. ML Prediction Verification (Model Output Verification)
        ml_res = self._verify_ml_assessment(dispute_id, report)
        results.append(ml_res)

        # 3. Calculate Verification Summary
        total = len(results)
        verified_count = sum(1 for r in results if r.verification_status == "VERIFIED")
        mismatched_count = sum(1 for r in results if r.verification_status == "MISMATCH")
        missing_count = sum(1 for r in results if r.verification_status == "MISSING_SOURCE")
        unsupported_count = sum(1 for r in results if r.verification_status == "UNSUPPORTED")
        unverifiable_count = sum(1 for r in results if r.verification_status == "UNVERIFIABLE")
        
        rate = round(verified_count / total, 4) if total > 0 else 1.0

        summary = VerificationSummary(
            total_evidence=total,
            verified=verified_count,
            mismatched=mismatched_count,
            missing_source=missing_count,
            unsupported=unsupported_count,
            unverifiable=unverifiable_count,
            verification_rate=rate
        )

        logger.info(f"Verification completed for {dispute_id}. Rate: {rate * 100:.1f}% ({verified_count}/{total} verified).")

        return VerifiedInvestigationResponse(
            dispute_id=dispute_id,
            investigation=report,
            verification_summary=summary,
            verification_results=results,
            is_synthetic_data=True,
            disclaimer="READ-ONLY DECISION SUPPORT. Final financial actions require human authorization."
        )

    def _verify_evidence_item(self, dispute_id: str, item: EvidenceItem) -> VerificationResult:
        source_rec = get_source_record(dispute_id, item.source_type, item.source_id)
        ref, citation_label = generate_citation(item.source_type, item.source_id, item.source_field)

        # Handle Missing Source
        if source_rec is None:
            return VerificationResult(
                evidence_id=item.evidence_id,
                source_type=item.source_type,
                source_id=item.source_id,
                source_field=item.source_field,
                claim=item.claim,
                claimed_value=item.claimed_value or item.value,
                actual_source_value=None,
                verification_status="MISSING_SOURCE",
                match_type="MISMATCH",
                verification_reason=f"Authoritative source record '{item.source_id}' ({item.source_type}) could not be located.",
                citation_label=citation_label,
                source_reference=ref
            )

        # Field-level comparison
        target_field = item.source_field
        claimed_val = item.claimed_value or item.value

        if target_field and target_field in source_rec:
            actual_val = source_rec[target_field]
            status, match_type, reason = compare_values(claimed_val, actual_val)
            actual_str = str(actual_val)
        else:
            # Fallback when specific field is unmapped or missing
            status = "UNVERIFIABLE"
            match_type = "NOT_APPLICABLE"
            reason = f"Field '{target_field}' is not directly mapped on entity '{item.source_type}'."
            actual_str = None

        return VerificationResult(
            evidence_id=item.evidence_id,
            source_type=item.source_type,
            source_id=item.source_id,
            source_field=target_field,
            claim=item.claim,
            claimed_value=claimed_val,
            actual_source_value=actual_str,
            verification_status=status,
            match_type=match_type,
            verification_reason=reason,
            citation_label=citation_label,
            source_reference=ref
        )

    def _verify_ml_assessment(self, dispute_id: str, report: InvestigationReport) -> VerificationResult:
        """Verifies ML win probability and model version against Phase 2 prediction service."""
        ref, citation_label = generate_citation("ML_MODEL", dispute_id, "win_probability")
        
        try:
            pred = prediction_service.predict_dispute(dispute_id)
            actual_prob = pred["win_probability"]
            claimed_prob = report.ml_assessment.win_probability
            
            if round(claimed_prob, 4) == round(actual_prob, 4):
                status = "VERIFIED"
                match_type = "EXACT"
                reason = f"Investigation ML win probability {claimed_prob} matches Phase 2 model prediction ({actual_prob})."
            else:
                status = "MISMATCH"
                match_type = "MISMATCH"
                reason = f"ML win probability mismatch: claimed {claimed_prob} vs actual prediction {actual_prob}."
                
            actual_str = f"Prob: {actual_prob}, Rec: {pred['recommendation']}, Model: {pred['model_version']}"
        except Exception as e:
            status = "UNVERIFIABLE"
            match_type = "NOT_APPLICABLE"
            reason = f"ML prediction verification failed: {str(e)}"
            actual_str = None

        return VerificationResult(
            evidence_id=f"EVID_{dispute_id}_ML",
            source_type="ML_MODEL",
            source_id=dispute_id,
            source_field="win_probability",
            claim="Phase 2 ML Model Win Probability Assessment",
            claimed_value=str(report.ml_assessment.win_probability),
            actual_source_value=actual_str,
            verification_status=status,
            match_type=match_type,
            verification_reason=reason,
            citation_label=citation_label,
            source_reference=ref
        )

evidence_verifier = EvidenceVerifier()
