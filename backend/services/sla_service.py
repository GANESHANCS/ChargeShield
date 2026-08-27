"""
SLA & Review Prioritization Engine for ChargeShield.

Calculates SLA urgency, remaining response time, overdue status, review priority,
and generates a human-readable transparent priority explanation string.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional

class SLAService:
    """Service layer calculating SLA deadline pressure and review priorities."""

    def calculate_sla(
        self,
        response_deadline_iso: Optional[str],
        disputed_amount: float = 0.0,
        win_probability: float = 0.5,
        risk_score: float = 0.5,
        evidence_confidence: float = 0.5
    ) -> Dict[str, Any]:
        """
        Calculates SLA deadline status, time remaining, urgency score,
        review priority tier, and transparent priority explanation string.
        """
        now = datetime.now(timezone.utc)

        if not response_deadline_iso:
            return {
                "sla_status": "NO_DEADLINE",
                "hours_remaining": None,
                "is_overdue": False,
                "urgency_score": 20.0,
                "review_priority": "LOW",
                "priority_explanation": f"LOW | ₹{disputed_amount:,.0f} exposure | NO DEADLINE SET"
            }

        try:
            # Parse deadline ISO timestamp
            deadline_clean = response_deadline_iso.replace('Z', '+00:00')
            deadline_dt = datetime.fromisoformat(deadline_clean)
            if deadline_dt.tzinfo is None:
                deadline_dt = deadline_dt.replace(tzinfo=timezone.utc)
        except Exception:
            deadline_dt = now

        delta = deadline_dt - now
        hours_remaining = delta.total_seconds() / 3600.0

        # Determine SLA Status
        if hours_remaining < 0:
            sla_status = "OVERDUE"
            is_overdue = True
        elif hours_remaining <= 24:
            sla_status = "AT_RISK"
            is_overdue = False
        elif hours_remaining <= 48:
            sla_status = "DUE_SOON"
            is_overdue = False
        else:
            sla_status = "ON_TRACK"
            is_overdue = False

        # Calculate Urgency Score (0 - 100)
        # Factor 1: Deadline proximity (0-40 pts)
        if hours_remaining <= 0:
            time_score = 40.0
        elif hours_remaining <= 12:
            time_score = 38.0
        elif hours_remaining <= 24:
            time_score = 32.0
        elif hours_remaining <= 48:
            time_score = 22.0
        elif hours_remaining <= 96:
            time_score = 12.0
        else:
            time_score = 5.0

        # Factor 2: Financial Exposure (0-30 pts)
        if disputed_amount >= 50000:
            amount_score = 30.0
        elif disputed_amount >= 20000:
            amount_score = 24.0
        elif disputed_amount >= 10000:
            amount_score = 18.0
        elif disputed_amount >= 5000:
            amount_score = 12.0
        else:
            amount_score = 6.0

        # Factor 3: Win Probability & Risk Score (0-20 pts)
        risk_score_pt = min(20.0, risk_score * 20.0)

        # Factor 4: Evidence Confidence (0-10 pts)
        evidence_score_pt = min(10.0, evidence_confidence * 10.0)

        urgency_score = round(time_score + amount_score + risk_score_pt + evidence_score_pt, 1)

        # Derive Review Priority Tier
        if urgency_score >= 75 or hours_remaining <= 12 or (disputed_amount >= 40000 and hours_remaining <= 36):
            review_priority = "CRITICAL"
        elif urgency_score >= 55 or hours_remaining <= 36:
            review_priority = "HIGH"
        elif urgency_score >= 35 or hours_remaining <= 72:
            review_priority = "MEDIUM"
        else:
            review_priority = "LOW"

        # Generate Transparent Priority Explanation String
        time_str = (
            f"{abs(hours_remaining):.0f}h OVERDUE" if is_overdue
            else f"{hours_remaining:.0f}h remaining"
        )
        conf_label = (
            "HIGH" if evidence_confidence >= 0.75
            else "MODERATE" if evidence_confidence >= 0.50
            else "LOW"
        )
        
        explanation = f"{review_priority} | ₹{disputed_amount:,.0f} exposure | {time_str} | {conf_label} evidence confidence"

        return {
            "sla_status": sla_status,
            "hours_remaining": round(hours_remaining, 1),
            "is_overdue": is_overdue,
            "urgency_score": urgency_score,
            "review_priority": review_priority,
            "priority_explanation": explanation,
            "deadline": response_deadline_iso,
            "data_state": "PRODUCTION"
        }

sla_service = SLAService()
