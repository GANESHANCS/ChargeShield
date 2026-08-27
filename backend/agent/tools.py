"""
Read-Only Agent Tools for ChargeShield Risk Investigation Agent.
Enforces read-only data retrieval from Phase 3 Case & Prediction services.
"""

from typing import Dict, Any, Optional
from backend.services.case_service import case_service
from backend.services.prediction_service import prediction_service

def get_case_detail_tool(dispute_id: str) -> Optional[Dict[str, Any]]:
    """Read-only tool: Retrieves complete relational case details."""
    return case_service.get_case_detail(dispute_id)

def get_prediction_tool(dispute_id: str) -> Dict[str, Any]:
    """Read-only tool: Retrieves ML win probability and decision recommendation."""
    return prediction_service.predict_dispute(dispute_id)

def get_explanation_tool(dispute_id: str) -> Dict[str, Any]:
    """Read-only tool: Retrieves SHAP model explanation risk factors."""
    return prediction_service.explain_dispute(dispute_id)

def get_customer_history_tool(dispute_id: str) -> Optional[Dict[str, Any]]:
    """Read-only tool: Retrieves customer tenure, order count, and dispute history."""
    detail = case_service.get_case_detail(dispute_id)
    if not detail:
        return None
    return {
        "customer": detail["customer"],
        "previous_disputes": detail["previous_disputes"]
    }

def get_delivery_evidence_tool(dispute_id: str) -> Optional[Dict[str, Any]]:
    """Read-only tool: Retrieves delivery logistics status and POD signature presence."""
    detail = case_service.get_case_detail(dispute_id)
    if not detail:
        return None
    return detail["delivery"]

def get_transaction_risk_tool(dispute_id: str) -> Optional[Dict[str, Any]]:
    """Read-only tool: Retrieves transaction risk scores, payment method, and fingerprint match."""
    detail = case_service.get_case_detail(dispute_id)
    if not detail:
        return None
    return detail["transaction"]
