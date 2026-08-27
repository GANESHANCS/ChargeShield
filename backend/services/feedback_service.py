"""
Model Feedback Service for ChargeShield.
Calculates agreement, disagreement, override, and escalation rates between AI recommendations
and human auditor decisions persisted in SQLite.
"""

import logging
from typing import List

from backend.db.database import get_db_session
from backend.db.models import ReviewDecisionModel
from backend.services.case_service import case_service
from backend.schemas.operations import ModelFeedbackResponse, DisagreementCase

logger = logging.getLogger("chargeshield.feedback_service")


class ModelFeedbackService:
    """Service evaluating human decisions vs AI recommendations."""

    def get_feedback_metrics(self) -> ModelFeedbackResponse:
        """Calculates agreement rates and returns cases with AI vs Human disagreement."""
        disagreement_cases: List[DisagreementCase] = []
        agreement_count = 0
        disagreement_count = 0
        override_count = 0
        escalation_count = 0

        # Load case amounts lookup map
        all_cases = case_service.list_cases(page=1, page_size=200).get("items", [])
        amount_map = {c["dispute_id"]: float(c.get("disputed_amount", 0.0)) for c in all_cases}

        with get_db_session() as session:
            decisions = session.query(ReviewDecisionModel).all()
            total_decisions = len(decisions)

            for d in decisions:
                did = d.dispute_id
                amt = amount_map.get(did, 0.0)
                ai_rec = d.ai_recommendation
                h_dec = d.decision

                if h_dec == "ESCALATE":
                    escalation_count += 1

                if h_dec == ai_rec:
                    agreement_count += 1
                else:
                    disagreement_count += 1
                    if (ai_rec == "CONTEST" and h_dec == "DO_NOT_CONTEST") or (ai_rec == "DO_NOT_CONTEST" and h_dec == "CONTEST"):
                        override_count += 1

                    disagreement_cases.append(DisagreementCase(
                        dispute_id=did,
                        disputed_amount=amt,
                        ai_recommendation=ai_rec or "CONTEST",
                        ai_win_probability=d.ai_win_probability or 0.5,
                        human_decision=h_dec,
                        reviewer_id=d.reviewer_id,
                        justification=d.justification,
                        created_at=d.created_at.isoformat() if d.created_at else ""
                    ))

        agreement_rate = round(agreement_count / total_decisions, 4) if total_decisions > 0 else 1.0
        disagreement_rate = round(disagreement_count / total_decisions, 4) if total_decisions > 0 else 0.0
        override_rate = round(override_count / total_decisions, 4) if total_decisions > 0 else 0.0
        escalation_rate = round(escalation_count / total_decisions, 4) if total_decisions > 0 else 0.0

        return ModelFeedbackResponse(
            total_human_decisions=total_decisions,
            agreement_count=agreement_count,
            disagreement_count=disagreement_count,
            agreement_rate=agreement_rate,
            disagreement_rate=disagreement_rate,
            override_rate=override_rate,
            escalation_rate=escalation_rate,
            disagreement_cases=disagreement_cases,
            data_state_label="HISTORICAL / PERSISTENT SQLITE"
        )


feedback_service = ModelFeedbackService()
