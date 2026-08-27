"""
Read-Only Source Record Retrieval for Evidence Verification.
Retrieves authoritative entity dicts from Phase 3 Case Service.
"""

from typing import Dict, Any, Optional
from backend.services.case_service import case_service

def get_source_record(dispute_id: str, source_type: str, source_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves authoritative source record from Phase 3 CaseService.
    Supports source types: DISPUTE, CUSTOMER, TRANSACTION, ORDER, DELIVERY, COMMUNICATION, PREVIOUS_DISPUTE.
    """
    detail = case_service.get_case_detail(dispute_id)
    if not detail:
        return None

    src_upper = source_type.upper()

    if src_upper == "DISPUTE":
        disp = detail["dispute"]
        if disp.get("dispute_id") == source_id:
            return disp
    elif src_upper == "CUSTOMER":
        cust = detail["customer"]
        if cust.get("customer_id") == source_id:
            return cust
    elif src_upper == "TRANSACTION":
        txn = detail["transaction"]
        if txn.get("transaction_id") == source_id:
            return txn
    elif src_upper == "ORDER":
        ord_info = detail["order"]
        if ord_info.get("order_id") == source_id:
            return ord_info
    elif src_upper == "DELIVERY":
        deliv = detail["delivery"]
        if deliv.get("delivery_id") == source_id:
            return deliv
    elif src_upper == "COMMUNICATION":
        for com in detail.get("communications", []):
            if com.get("communication_id") == source_id:
                return com
    elif src_upper in ["PREVIOUS_DISPUTE", "HISTORICAL_DISPUTE"]:
        for prev in detail.get("previous_disputes", []):
            if prev.get("dispute_id") == source_id:
                return prev

    return None
