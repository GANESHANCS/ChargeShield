"""
Risk Scoring Engine for ChargeShield Phase 7.

Calculates multi-dimensional risk classification, priority scores, confidence metrics,
and transparent priority reasoning strings for risk operations.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Configurable risk thresholds
RISK_THRESHOLDS: Dict[str, Any] = {
    "critical_amount": 50000.0,
    "high_amount": 20000.0,
    "low_win_prob": 0.35,
    "high_win_prob": 0.65,
    "critical_win_prob": 0.25
}

class RiskEngine:
    """Derives risk tier classification, priority score, and priority reasoning."""

    def __init__(self, thresholds: Optional[Dict[str, Any]] = None):
        self.thresholds = thresholds or RISK_THRESHOLDS

    def assess_risk(
        self,
        dispute_id: str,
        transaction_id: str,
        amount: float,
        dispute_reason: str,
        win_probability: float,
        model_version: str = "chargeshield_ml_v1",
        decision_threshold: float = 0.29
    ) -> Dict[str, Any]:
        """
        Assesses a dispute case and returns structured risk classification,
        priority score, confidence, and human-readable priority reasoning.
        """
        amt = max(0.0, float(amount))
        win_prob = max(0.0, min(1.0, float(win_probability)))
        risk_score = round(1.0 - win_prob, 4)

        # Calculate Confidence Score (0.5 to 1.0)
        # Distance from 0.5 uncertainty threshold scaled to 0.5 - 1.0 range
        dist_from_center = abs(win_prob - 0.50)
        confidence = round(0.50 + dist_from_center, 4)

        # Risk Classification Tiers: CRITICAL, HIGH, MEDIUM, LOW
        crit_amt = self.thresholds["critical_amount"]
        high_amt = self.thresholds["high_amount"]
        low_prob = self.thresholds["low_win_prob"]
        high_prob = self.thresholds["high_win_prob"]
        crit_prob = self.thresholds["critical_win_prob"]

        if amt >= crit_amt or (win_prob < crit_prob and amt >= (crit_amt / 2.0)):
            risk_tier = "CRITICAL"
        elif amt >= high_amt or win_prob < low_prob:
            risk_tier = "HIGH"
        elif low_prob <= win_prob <= high_prob:
            risk_tier = "MEDIUM"
        else:
            risk_tier = "LOW"

        # Calculate Priority Score (0.0 to 100.0)
        # Combines amount scale (40%), win probability potential (40%), and risk score (20%)
        amt_score = min(40.0, (amt / crit_amt) * 40.0)
        prob_score = win_prob * 40.0
        risk_part = risk_score * 20.0
        priority_score = round(min(100.0, amt_score + prob_score + risk_part), 2)

        # Recommended Action
        if win_prob >= decision_threshold:
            recommended_action = "CONTEST"
        elif win_prob >= max(0.15, decision_threshold - 0.15):
            recommended_action = "MANUAL_REVIEW"
        else:
            recommended_action = "DO_NOT_CONTEST"

        # Priority Reasoning Generation
        win_pct = f"{win_prob * 100:.1f}%"
        amt_formatted = f"₹{amt:,.0f}"

        reasons = [f"{risk_tier}"]
        reasons.append(f"{amt_formatted} at stake")
        reasons.append(f"{win_pct} predicted win probability")

        if amt >= crit_amt:
            reasons.append("Critical financial exposure")
        elif win_prob >= 0.70:
            reasons.append("High recovery potential")
        elif win_prob < crit_prob:
            reasons.append("High loss risk")
        else:
            reasons.append("Standard triage case")

        priority_reasoning = " | ".join(reasons)

        now_iso = datetime.now(timezone.utc).isoformat()

        return {
            "dispute_id": dispute_id,
            "transaction_id": transaction_id,
            "amount": amt,
            "currency": "INR",
            "dispute_reason": dispute_reason,
            "risk_score": risk_score,
            "win_probability": win_prob,
            "priority": risk_tier,
            "priority_score": priority_score,
            "priority_reasoning": priority_reasoning,
            "recommended_action": recommended_action,
            "confidence": confidence,
            "model_version": model_version,
            "prediction_timestamp": now_iso,
            "thresholds": self.thresholds
        }

risk_engine = RiskEngine()
