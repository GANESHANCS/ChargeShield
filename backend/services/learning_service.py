"""
Learning Service for ChargeShield Phase 12.
Analyzes ground-truth outcomes vs AI predictions and human reviewer decisions.
Calculates agreement rates, AI/Human correctness against ground truth, FPR/FNR, precision, recall,
and financial impacts of overrides. Enforces strict production-only filtering and explicit status returns.
"""

from typing import Dict, Any, List
from backend.db.database import get_db_session
from backend.db.models import ModelOutcomeModel, ReviewDecisionModel
from backend.services.case_service import case_service

MIN_LEARNING_SAMPLES = 1


class LearningService:
    def get_learning_metrics(self) -> Dict[str, Any]:
        with get_db_session() as db:
            # Query PRODUCTION outcomes only
            outcomes = db.query(ModelOutcomeModel).filter(ModelOutcomeModel.data_state == "PRODUCTION").all()

            if not outcomes or len(outcomes) < MIN_LEARNING_SAMPLES:
                return {
                    "status": "AWAITING_OUTCOME_LABELS",
                    "learning_status": "INSUFFICIENT_DATA",
                    "total_eligible_production_cases": 0,
                    "total_labeled_outcomes": 0,
                    "ai_vs_human_agreement_rate": 0.0,
                    "ai_vs_outcome_accuracy": 0.0,
                    "human_vs_outcome_accuracy": 0.0,
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1_score": 0.0,
                    "false_positive_rate": 0.0,
                    "false_negative_rate": 0.0,
                    "outcome_recovery_rate": 0.0,
                    "override_rate": 0.0,
                    "financial_impact_incorrect_predictions": 0.0,
                    "financial_impact_human_overrides": 0.0,
                    "data_provenance": "INSUFFICIENT_DATA",
                    "message": "AWAITING OUTCOME LABELS. Ground-truth dispute outcomes are required for feedback learning calculations."
                }

            # Map dispute_id -> ReviewDecisionModel
            dispute_ids = [o.dispute_id for o in outcomes]
            dec_map = {}
            decisions = db.query(ReviewDecisionModel).filter(ReviewDecisionModel.dispute_id.in_(dispute_ids)).all()
            for d in decisions:
                dec_map[d.dispute_id] = d

            ai_human_agreements = 0
            ai_correct_count = 0
            human_correct_count = 0
            overrides = 0
            tp, fp, tn, fn = 0, 0, 0, 0
            total_recovery = 0.0
            total_cases = len(outcomes)

            for o in outcomes:
                dec = dec_map.get(o.dispute_id)
                ai_rec = dec.ai_recommendation if dec else "CONTEST"
                human_dec = dec.decision if dec else "CONTEST"
                actual = o.actual_outcome  # WON, LOST, EXPIRED

                # Agreement
                if ai_rec == human_dec:
                    ai_human_agreements += 1
                else:
                    overrides += 1

                # Correctness (WIN considered positive outcome for CONTEST action)
                actual_win = (actual == "WON")
                ai_contested = (ai_rec in ["CONTEST", "HIGH_RISK_CONTEST"])
                human_contested = (human_dec in ["CONTEST", "HIGH_RISK_CONTEST"])

                if ai_contested == actual_win:
                    ai_correct_count += 1
                if human_contested == actual_win:
                    human_correct_count += 1

                # Contingency for AI
                if ai_contested and actual_win:
                    tp += 1
                    total_recovery += (o.financial_recovery_amount or 1500.0)
                elif ai_contested and not actual_win:
                    fp += 1
                elif not ai_contested and actual_win:
                    fn += 1
                else:
                    tn += 1

            agreement_rate = ai_human_agreements / total_cases if total_cases > 0 else 0.0
            ai_acc = ai_correct_count / total_cases if total_cases > 0 else 0.0
            human_acc = human_correct_count / total_cases if total_cases > 0 else 0.0
            override_rate = overrides / total_cases if total_cases > 0 else 0.0

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
            recovery_rate = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0

            # Financial impacts
            fin_incorrect = fp * 375.0  # Lost contest fees (₹375 per false contest)
            fin_overrides = (human_correct_count - ai_correct_count) * 1125.0  # Net recovery gained by human overrides

            return {
                "status": "EVALUATED",
                "learning_status": "LEARNING_READY",
                "total_eligible_production_cases": total_cases,
                "total_labeled_outcomes": total_cases,
                "ai_vs_human_agreement_rate": round(agreement_rate, 4),
                "ai_vs_outcome_accuracy": round(ai_acc, 4),
                "human_vs_outcome_accuracy": round(human_acc, 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
                "false_positive_rate": round(fpr, 4),
                "false_negative_rate": round(fnr, 4),
                "outcome_recovery_rate": round(recovery_rate, 4),
                "override_rate": round(override_rate, 4),
                "financial_impact_incorrect_predictions": round(fin_incorrect, 2),
                "financial_impact_human_overrides": round(fin_overrides, 2),
                "data_provenance": "PRODUCTION",
                "message": f"Evaluated feedback across {total_cases} ground-truth production outcomes. AI accuracy: {round(ai_acc*100, 1)}%."
            }


learning_service = LearningService()
