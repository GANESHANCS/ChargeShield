"""
Decision Simulation Engine for ChargeShield Phase 7.

Simulates financial and operational outcomes across decision paths (CONTEST, DO_NOT_CONTEST, ESCALATE)
and explicitly distinguishes Model Estimates from Actual Historical Outcomes.
"""

from typing import Dict, Any, Optional
from backend.services.financial_engine import financial_engine
from backend.db.database import get_db_session
from backend.db.models import ReviewDecisionModel

class SimulationService:
    """Calculates what-if decision scenario outcomes for risk investigators."""

    def simulate_decision_scenarios(
        self,
        dispute_id: str,
        disputed_amount: float,
        win_probability: float
    ) -> Dict[str, Any]:
        """
        Simulates financial outcomes for:
          1. CONTEST (Filing fee + contest cost applied, expected recovery based on win prob)
          2. DO_NOT_CONTEST (100% loss of disputed amount, zero operational contest cost)
          3. ESCALATE (Pends case for senior risk officer review)
        """
        impact = financial_engine.calculate_impact(disputed_amount, win_probability)
        amt = impact["disputed_amount"]

        # 1. CONTEST Scenario Projection
        contest_scenario = {
            "action": "CONTEST",
            "label": "Contest Dispute",
            "expected_recovery": impact["expected_recovery"],
            "operational_cost": impact["estimated_operational_cost"],
            "net_financial_outcome": impact["expected_net_contest_value"],
            "risk_impact": "Recovers funds if successful; incurs non-refundable filing fee if lost.",
            "type": "MODEL_ESTIMATE"
        }

        # 2. DO NOT CONTEST Scenario Projection
        do_not_contest_scenario = {
            "action": "DO_NOT_CONTEST",
            "label": "Accept Chargeback",
            "expected_recovery": 0.0,
            "operational_cost": 0.0,
            "net_financial_outcome": impact["expected_net_accept_value"],
            "risk_impact": "Guarantees 100% financial loss; avoids operational contest fees.",
            "type": "MODEL_ESTIMATE"
        }

        # 3. ESCALATE Scenario Projection
        escalate_scenario = {
            "action": "ESCALATE",
            "label": "Escalate to Senior Committee",
            "expected_recovery": impact["expected_recovery"],
            "operational_cost": impact["estimated_operational_cost"],
            "net_financial_outcome": impact["expected_net_contest_value"],
            "risk_impact": "Defers action for executive review; holds deadline countdown.",
            "type": "MODEL_ESTIMATE"
        }

        # Check for Actual Historical Decision Outcome in SQLite database
        actual_outcome = None
        try:
            with get_db_session() as session:
                dec = session.query(ReviewDecisionModel).filter(
                    ReviewDecisionModel.dispute_id == dispute_id
                ).first()
                if dec:
                    actual_outcome = {
                        "decision_id": dec.decision_id,
                        "reviewer_id": dec.reviewer_id,
                        "decision": dec.decision,
                        "reason": dec.reason,
                        "recorded_at": dec.created_at,
                        "type": "ACTUAL_OUTCOME"
                    }
        except Exception:
            pass

        return {
            "dispute_id": dispute_id,
            "disputed_amount": amt,
            "win_probability": win_probability,
            "scenarios": {
                "CONTEST": contest_scenario,
                "DO_NOT_CONTEST": do_not_contest_scenario,
                "ESCALATE": escalate_scenario
            },
            "recommended_scenario": "CONTEST" if impact["is_financially_viable"] else "DO_NOT_CONTEST",
            "net_financial_advantage": impact["net_financial_advantage"],
            "actual_outcome": actual_outcome,
            "assumptions": impact["assumptions"],
            "disclaimer": "SIMULATION MODEL ONLY — Explicitly distinguishes Model Estimate from Recorded Actual Outcome."
        }

simulation_service = SimulationService()
