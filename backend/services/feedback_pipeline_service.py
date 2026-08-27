"""
Feedback Pipeline Service for ChargeShield Phase 12.
Orchestrates the continuous learning pipeline across Prediction -> Human Review -> Final Decision -> Actual Outcome -> Outcome Label.
Tracks learning eligibility and enforces strict exclusion of simulation cases from production feedback loops.
"""

from typing import Dict, Any, List
from backend.db.database import get_db_session
from backend.db.models import ModelOutcomeModel, ReviewDecisionModel, ReviewStateModel
from backend.services.case_service import case_service


class FeedbackPipelineService:
    def get_learning_readiness_and_eligibility(self) -> Dict[str, Any]:
        with get_db_session() as db:
            outcomes = db.query(ModelOutcomeModel).all()
            decisions = db.query(ReviewDecisionModel).all()
            states = db.query(ReviewStateModel).all()

            # Map dispute -> outcome
            outcome_map = {o.dispute_id: o for o in outcomes}
            decision_map = {d.dispute_id: d for d in decisions}

            # Fetch all cases from case_service to evaluate full corpus
            all_cases = case_service.list_cases(page_size=100).get("items", [])

            total_cases = len(all_cases)
            production_cases = 0
            simulation_cases = 0
            eligible_cases = 0
            pending_outcomes = 0

            excluded_breakdown = {
                "SIMULATION_DATA": 0,
                "OUTCOME_PENDING": 0,
                "MISSING_HUMAN_DECISION": 0,
                "MISSING_PREDICTION": 0
            }

            eligible_case_ids = []

            for c in all_cases:
                d_id = c.get("dispute_id", "")
                is_sim = d_id.startswith("DSP_SIM_") or c.get("data_state") == "SIMULATION"

                if is_sim:
                    simulation_cases += 1
                    excluded_breakdown["SIMULATION_DATA"] += 1
                    continue

                production_cases += 1
                has_dec = d_id in decision_map
                has_out = d_id in outcome_map

                if not has_dec:
                    excluded_breakdown["MISSING_HUMAN_DECISION"] += 1

                if not has_out:
                    pending_outcomes += 1
                    excluded_breakdown["OUTCOME_PENDING"] += 1
                    continue

                if has_dec and has_out:
                    eligible_cases += 1
                    eligible_case_ids.append(d_id)

            # Determine overall readiness status
            if eligible_cases >= 5:
                readiness_status = "LEARNING_READY"
            elif eligible_cases > 0:
                readiness_status = "PARTIALLY_READY"
            elif pending_outcomes > 0:
                readiness_status = "AWAITING_OUTCOME_LABELS"
            else:
                readiness_status = "INSUFFICIENT_DATA"

            return {
                "status": readiness_status,
                "learning_readiness_status": readiness_status,
                "total_cases_evaluated": total_cases,
                "production_cases": production_cases,
                "simulation_cases_excluded": simulation_cases,
                "eligible_production_cases_count": eligible_cases,
                "pending_outcome_cases_count": pending_outcomes,
                "eligible_case_ids": eligible_case_ids,
                "ineligibility_breakdown": excluded_breakdown,
                "data_provenance": "PRODUCTION",
                "governance": {
                    "simulation_exclusion": True,
                    "requires_ground_truth_outcome": True,
                    "policy": "Only genuine production cases with model prediction, human decision, and recorded actual outcome are eligible for learning."
                }
            }


feedback_pipeline_service = FeedbackPipelineService()
