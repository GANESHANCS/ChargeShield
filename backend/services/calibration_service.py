"""
Calibration Service for ChargeShield Phase 12.
Evaluates model win probability calibration against ground-truth outcomes across 10 probability buckets.
Returns explicit INSUFFICIENT_DATA / AWAITING_OUTCOME_LABELS status when ground-truth outcomes are absent.
"""

from typing import Dict, Any, List
from backend.db.database import get_db_session
from backend.db.models import ModelOutcomeModel, ReviewDecisionModel
from backend.services.case_service import case_service

MIN_SAMPLES_FOR_CALIBRATION = 5


class CalibrationService:
    def evaluate_calibration(self) -> Dict[str, Any]:
        with get_db_session() as db:
            outcomes = db.query(ModelOutcomeModel).filter(ModelOutcomeModel.data_state == "PRODUCTION").all()

            if not outcomes:
                return {
                    "status": "AWAITING_OUTCOME_LABELS",
                    "calibration_status": "INSUFFICIENT_DATA",
                    "is_sufficient": False,
                    "total_labeled_outcomes": 0,
                    "min_required_outcomes": MIN_SAMPLES_FOR_CALIBRATION,
                    "buckets": self._empty_buckets(),
                    "mean_calibration_gap": None,
                    "data_provenance": "INSUFFICIENT_DATA",
                    "message": "AWAITING OUTCOME LABELS. Insufficient ground-truth production outcomes to compute calibration curve."
                }

            # Map dispute_id to win probability
            dispute_ids = [o.dispute_id for o in outcomes]
            prob_map = {}
            decisions = db.query(ReviewDecisionModel).filter(ReviewDecisionModel.dispute_id.in_(dispute_ids)).all()
            for d in decisions:
                prob_map[d.dispute_id] = d.ai_win_probability

            # Also check prediction service or case detail if not in decisions
            for o in outcomes:
                if o.dispute_id not in prob_map:
                    cd = case_service.get_case_detail(o.dispute_id)
                    if cd and "prediction" in cd and cd["prediction"]:
                        prob_map[o.dispute_id] = cd["prediction"].get("win_probability", 0.5)
                    else:
                        prob_map[o.dispute_id] = 0.5

            # Group into 10 buckets (0.0-0.1, 0.1-0.2, ..., 0.9-1.0)
            bucket_bins = [
                (0.0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.4), (0.4, 0.5),
                (0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0)
            ]

            bucket_data = {f"{low:.1f} - {high:.1f}": {"low": low, "high": high, "probs": [], "wins": 0} for low, high in bucket_bins}

            valid_samples = 0
            for o in outcomes:
                p = prob_map.get(o.dispute_id, 0.5)
                is_win = 1 if o.actual_outcome == "WON" else 0
                valid_samples += 1

                for b_key, b_info in bucket_data.items():
                    if b_info["low"] <= p < b_info["high"] or (b_info["high"] == 1.0 and p == 1.0):
                        b_info["probs"].append(p)
                        b_info["wins"] += is_win
                        break

            if valid_samples < MIN_SAMPLES_FOR_CALIBRATION:
                return {
                    "status": "INSUFFICIENT_DATA",
                    "calibration_status": "INSUFFICIENT_DATA",
                    "is_sufficient": False,
                    "total_labeled_outcomes": valid_samples,
                    "min_required_outcomes": MIN_SAMPLES_FOR_CALIBRATION,
                    "buckets": self._empty_buckets(),
                    "mean_calibration_gap": None,
                    "data_provenance": "INSUFFICIENT_DATA",
                    "message": f"INSUFFICIENT DATA ({valid_samples}/{MIN_SAMPLES_FOR_CALIBRATION} required production labels)."
                }

            result_buckets = []
            total_gap = 0.0
            active_buckets = 0

            for b_key, b_info in bucket_data.items():
                count = len(b_info["probs"])
                avg_prob = sum(b_info["probs"]) / count if count > 0 else (b_info["low"] + b_info["high"]) / 2.0
                obs_win_rate = b_info["wins"] / count if count > 0 else 0.0
                gap = abs(obs_win_rate - avg_prob) if count > 0 else 0.0

                if count > 0:
                    total_gap += gap
                    active_buckets += 1

                result_buckets.append({
                    "bucket_range": b_key,
                    "sample_count": count,
                    "average_predicted_probability": round(avg_prob, 4),
                    "observed_win_rate": round(obs_win_rate, 4),
                    "calibration_gap": round(gap, 4)
                })

            mean_gap = total_gap / active_buckets if active_buckets > 0 else 0.0

            if mean_gap <= 0.05:
                cal_status = "CALIBRATED"
            elif mean_gap <= 0.15:
                cal_status = "PARTIALLY_CALIBRATED"
            else:
                cal_status = "POORLY_CALIBRATED"

            return {
                "status": "EVALUATED",
                "calibration_status": cal_status,
                "is_sufficient": True,
                "total_labeled_outcomes": valid_samples,
                "mean_calibration_gap": round(mean_gap, 4),
                "buckets": result_buckets,
                "data_provenance": "PRODUCTION",
                "message": f"Model probability calibration is {cal_status} (mean gap: {round(mean_gap*100, 1)}%)."
            }

    def _empty_buckets(self) -> List[Dict[str, Any]]:
        bucket_bins = [
            (0.0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.4), (0.4, 0.5),
            (0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0)
        ]
        return [
            {
                "bucket_range": f"{low:.1f} - {high:.1f}",
                "sample_count": 0,
                "average_predicted_probability": round((low + high) / 2.0, 2),
                "observed_win_rate": 0.0,
                "calibration_gap": 0.0
            }
            for low, high in bucket_bins
        ]


calibration_service = CalibrationService()
