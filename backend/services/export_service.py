"""
Report Export Service for ChargeShield.
Generates CSV and JSON operational report exports with explicit data provenance metadata.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.services.case_service import case_service
from backend.db.models import ReviewDecisionModel

class ExportService:
    def get_data_provenance(self) -> Dict[str, str]:
        """Returns immutable data provenance header for exports."""
        return {
            "DATA_STATE": "SIMULATION" if settings.SIMULATION_MODE else "PRODUCTION",
            "GENERATED_AT": datetime.now(timezone.utc).isoformat(),
            "SOURCE": "ChargeShield Risk Intelligence Operational Platform",
            "DISCLAIMER": settings.FINANCIAL_ASSUMPTIONS if hasattr(settings, "FINANCIAL_ASSUMPTIONS") else "Base Filing Fee = ₹1,500; Contest Multiplier = 0.25"
        }

    def export_cases_json(self, db: Session) -> Dict[str, Any]:
        """Exports all case summaries with provenance header in JSON format."""
        cases = case_service.list_cases(page=1, page_size=500)
        items = cases.get("items", []) if isinstance(cases, dict) else getattr(cases, "items", [])
        total = cases.get("total", len(items)) if isinstance(cases, dict) else getattr(cases, "total", len(items))
        return {
            "provenance": self.get_data_provenance(),
            "total_cases": total,
            "cases": items
        }

    def export_cases_csv(self, db: Session) -> str:
        """Exports case summaries in CSV format with provenance header."""
        cases = case_service.list_cases(page=1, page_size=500)
        items = cases.get("items", []) if isinstance(cases, dict) else getattr(cases, "items", [])
        prov = self.get_data_provenance()
        lines = [
            f"# DATA STATE: {prov['DATA_STATE']}",
            f"# GENERATED AT: {prov['GENERATED_AT']}",
            f"# SOURCE: {prov['SOURCE']}",
            "dispute_id,disputed_amount,currency,dispute_reason_code,dispute_status,customer_id,auth_risk_score"
        ]

        for item in items:
            disp_id = item.get("dispute_id") if isinstance(item, dict) else getattr(item, "dispute_id", "")
            amt = item.get("disputed_amount") if isinstance(item, dict) else getattr(item, "disputed_amount", 0)
            curr = item.get("currency", "INR") if isinstance(item, dict) else getattr(item, "currency", "INR")
            reason = item.get("dispute_reason_code") if isinstance(item, dict) else getattr(item, "dispute_reason_code", "")
            status_val = item.get("dispute_status", "OPEN") if isinstance(item, dict) else getattr(item, "dispute_status", "OPEN")
            cust_id = item.get("customer_id") if isinstance(item, dict) else getattr(item, "customer_id", "")
            risk_score = item.get("auth_risk_score", 0.0) if isinstance(item, dict) else getattr(item, "auth_risk_score", 0.0)

            lines.append(
                f"{disp_id},{amt},{curr},{reason},{status_val},{cust_id},{risk_score}"
            )
        return "\n".join(lines)

    def export_audit_log_json(self, db: Session) -> Dict[str, Any]:
        """Exports review decision audit logs with provenance header in JSON format."""
        decisions = db.query(ReviewDecisionModel).order_by(ReviewDecisionModel.created_at.desc()).all()
        return {
            "provenance": self.get_data_provenance(),
            "total_audit_events": len(decisions),
            "audit_events": [
                {
                    "decision_id": d.decision_id,
                    "dispute_id": d.dispute_id,
                    "reviewer_id": d.reviewer_id,
                    "decision": d.decision,
                    "reason": d.reason,
                    "ai_recommendation": d.ai_recommendation,
                    "ai_win_probability": d.ai_win_probability,
                    "created_at": d.created_at
                } for d in decisions
            ]
        }

    def export_audit_log_csv(self, db: Session) -> str:
        """Exports review decision audit logs in CSV format."""
        decisions = db.query(ReviewDecisionModel).order_by(ReviewDecisionModel.created_at.desc()).all()
        prov = self.get_data_provenance()
        lines = [
            f"# DATA STATE: {prov['DATA_STATE']}",
            f"# GENERATED AT: {prov['GENERATED_AT']}",
            f"# SOURCE: {prov['SOURCE']}",
            "decision_id,dispute_id,reviewer_id,decision,ai_recommendation,ai_win_probability,created_at,reason"
        ]

        for d in decisions:
            # Escape quotes in reason
            reason_clean = d.reason.replace('"', '""')
            lines.append(
                f"{d.decision_id},{d.dispute_id},{d.reviewer_id},{d.decision},"
                f"{d.ai_recommendation},{d.ai_win_probability},{d.created_at},\"{reason_clean}\""
            )
        return "\n".join(lines)

export_service = ExportService()
