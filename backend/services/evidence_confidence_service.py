"""
Evidence Confidence Engine for ChargeShield.

Calculates evidence completeness, proof strength, verification status,
missing items, and conflicting indicators from actual transaction, delivery,
and customer signals.
"""

from typing import Dict, List, Any

class EvidenceConfidenceService:
    """Evaluates grounding confidence of evidence for dispute defense."""

    def evaluate_evidence(self, case_detail: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates evidence completeness and consistency across delivery,
        transaction authentication, customer tenure, and communications.
        """
        delivery = case_detail.get("delivery", {})
        txn = case_detail.get("transaction", {})
        customer = case_detail.get("customer", {})
        order = case_detail.get("order", {})

        points = 0.0
        max_points = 100.0

        missing_evidence: List[str] = []
        conflicting_evidence: List[str] = []

        # 1. Delivery & Proof of Delivery (40 pts)
        if delivery.get("pod_signature_present"):
            points += 20.0
        else:
            missing_evidence.append("POD_SIGNATURE_MISSING")

        if delivery.get("pod_match_status") == "EXACT_MATCH":
            points += 10.0
        elif delivery.get("pod_match_status") == "MISMATCH":
            conflicting_evidence.append("POD_LOCATION_MISMATCH")

        if delivery.get("delivery_status") == "DELIVERED":
            points += 10.0
        elif delivery.get("delivery_status") in ["RETURNED", "FAILED"]:
            conflicting_evidence.append(f"DELIVERY_{delivery.get('delivery_status')}")

        # 2. Transaction Verification & Authentication (30 pts)
        if txn.get("cvv_match") in ["MATCH", "Y", "M"]:
            points += 15.0
        else:
            missing_evidence.append("CVV_MATCH_ABSENT")
            conflicting_evidence.append("CVV_CHECK_FAILED")

        if txn.get("avs_match") in ["MATCH", "Y", "M", "Z"]:
            points += 15.0
        else:
            missing_evidence.append("AVS_MATCH_ABSENT")

        # 3. Customer Tenure & Order History (20 pts)
        tenure = customer.get("tenure_days", 0)
        successful_orders = customer.get("successful_order_count", 0)
        
        if tenure >= 180 or successful_orders >= 5:
            points += 15.0
        elif tenure >= 30 or successful_orders >= 1:
            points += 8.0
        else:
            missing_evidence.append("ESTABLISHED_CUSTOMER_TENURE_ABSENT")

        if customer.get("historical_chargeback_count", 0) > 0:
            conflicting_evidence.append("PRIOR_CHARGEBACK_HISTORY_DETECTED")

        # 4. Fulfillment Status (10 pts)
        if order.get("fulfillment_status") == "FULFILLED":
            points += 10.0
        else:
            missing_evidence.append("FULFILLMENT_CONFIRMATION_PENDING")

        score = round(min(1.0, max(0.0, points / max_points)), 2)

        # Determine Evidence Status
        if len(conflicting_evidence) >= 2:
            evidence_status = "CONFLICTING"
        elif score >= 0.85:
            evidence_status = "VERIFIED"
        elif score >= 0.70:
            evidence_status = "HIGH_CONFIDENCE"
        elif score >= 0.45:
            evidence_status = "PARTIAL"
        elif score >= 0.20:
            evidence_status = "INSUFFICIENT_DATA"
        else:
            evidence_status = "INSUFFICIENT_DATA"

        summary = (
            f"Evidence confidence score {score:.2f} ({evidence_status}). "
            f"{len(missing_evidence)} missing item(s), {len(conflicting_evidence)} conflicting indicator(s)."
        )

        return {
            "evidence_confidence_score": score,
            "evidence_status": evidence_status,
            "verification_summary": summary,
            "missing_evidence": missing_evidence,
            "conflicting_evidence": conflicting_evidence,
            "pod_signature_present": bool(delivery.get("pod_signature_present")),
            "cvv_match": str(txn.get("cvv_match", "N/A")),
            "avs_match": str(txn.get("avs_match", "N/A")),
            "delivery_status": str(delivery.get("delivery_status", "N/A")),
            "data_state": "PRODUCTION"
        }

evidence_confidence_service = EvidenceConfidenceService()
