"""
Decision Policy Service for ChargeShield.
Decouples Machine Learning Model Inference (probabilities) from Operational Business Policies.
Determines operational actions (CONTEST, DO_NOT_CONTEST, ESCALATE) based on explicit rules, risk tiers, and financial advantage without mutating production threshold configuration.
"""

from typing import Dict, Any
from backend.core.logging import logger
from backend.services.prediction_service import prediction_service
from backend.services.risk_engine import risk_engine
from backend.services.financial_engine import financial_engine


class DecisionPolicyService:
    """
    Decoupled business decision policy controller.
    Executes clear 4-stage pipeline:
      PredictionService -> RiskEngine -> FinancialEngine -> DecisionPolicy
    """
    def evaluate_case_policy(
        self,
        dispute_id: str,
        active_threshold: float = 0.29
    ) -> Dict[str, Any]:
        """
        Evaluates operational decision policy for a dispute case.
        """
        # 1. Model Inference Stage (Probability outputs only)
        pred = prediction_service.predict_dispute(dispute_id)
        win_prob = pred["win_probability"]

        # 2. Risk Engine Stage (Priority and Risk Tiering)
        dispute_amt = pred.get("disputed_amount", 0.0)
        reason_code = pred.get("dispute_reason_code", "10.4")
        txn_id = pred.get("transaction_id", "")

        risk_assessment = risk_engine.assess_risk(
            dispute_id=dispute_id,
            transaction_id=txn_id,
            amount=dispute_amt,
            dispute_reason=reason_code,
            win_probability=win_prob,
            decision_threshold=active_threshold
        )

        # 3. Financial Engine Stage (Cost-Benefit & Advantage)
        financial_assessment = financial_engine.calculate_impact(
            disputed_amount=dispute_amt,
            win_probability=win_prob
        )

        # 4. Business Decision Policy Stage
        # Policy logic determines recommended operational action:
        net_advantage = financial_assessment.get("net_financial_advantage", 0.0)

        if win_prob >= active_threshold and net_advantage > 0:
            recommended_action = "CONTEST"
            policy_reason = (
                f"Calibrated win probability ({(win_prob * 100):.1f}%) meets or exceeds active threshold "
                f"({active_threshold}) with positive net financial advantage (₹{net_advantage:,.2f})."
            )
        elif dispute_amt >= 50000.0 or risk_assessment.get("priority") == "CRITICAL":
            recommended_action = "ESCALATE"
            policy_reason = (
                f"Disputed amount (₹{dispute_amt:,.2f}) or CRITICAL risk exposure requires senior operational review."
            )
        else:
            recommended_action = "DO_NOT_CONTEST"
            policy_reason = (
                f"Calibrated win probability ({(win_prob * 100):.1f}%) is below active threshold ({active_threshold}) "
                f"or expected recovery does not justify contestation costs."
            )

        return {
            "dispute_id": dispute_id,
            "pipeline_stages": {
                "1_prediction": pred,
                "2_risk_engine": risk_assessment,
                "3_financial_engine": financial_assessment,
                "4_decision_policy": {
                    "recommended_action": recommended_action,
                    "policy_reason": policy_reason,
                    "active_threshold": active_threshold
                }
            },
            "recommended_action": recommended_action,
            "policy_reason": policy_reason
        }


decision_policy_service = DecisionPolicyService()
