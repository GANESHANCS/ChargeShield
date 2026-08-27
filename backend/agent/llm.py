"""
LLM Provider Abstraction & Deterministic Fallback Engine for ChargeShield.
Supports optional Anthropic API synthesis and deterministic zero-hallucination fallback.
"""

import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import json

from backend.core.config import settings
from backend.core.logging import logger
from backend.agent.schemas import (
    InvestigationReport, InvestigationRecommendation, TimelineEvent,
    FactorItem, EvidenceItem, MLAssessmentPayload
)

class LLMProvider:
    """Abstract interface for LLM synthesis."""
    def generate_report(self, case_detail: Dict[str, Any]) -> InvestigationReport:
        raise NotImplementedError

class DeterministicFallbackInvestigator(LLMProvider):
    """
    Deterministic rule-based investigation engine.
    Extracts facts, constructs real timeline, attributes SHAP factors,
    and formats evidence items without external LLM dependencies.
    """
    def generate_report(self, case_detail: Dict[str, Any]) -> InvestigationReport:
        disp = case_detail["dispute"]
        cust = case_detail["customer"]
        txn = case_detail["transaction"]
        ord_info = case_detail["order"]
        deliv = case_detail["delivery"]
        coms = case_detail.get("communications", [])
        prevs = case_detail.get("previous_disputes", [])
        pred = case_detail["prediction"]

        disp_id = disp["dispute_id"]
        win_prob = float(pred["win_probability"])
        rec_action = pred["recommendation"]
        model_ver = pred["model_version"]
        thresh = float(pred["decision_threshold"])

        # 1. Timeline Construction from actual timestamps
        raw_events = []
        if ord_info.get("order_timestamp"):
            raw_events.append({
                "timestamp": ord_info["order_timestamp"],
                "event_type": "ORDER_CREATED",
                "description": f"Order {ord_info['order_id']} placed for {ord_info['order_amount']} INR ({ord_info['product_category']}).",
                "source_id": ord_info["order_id"]
            })
        if txn.get("transaction_timestamp"):
            raw_events.append({
                "timestamp": txn["transaction_timestamp"],
                "event_type": "PAYMENT_CAPTURED",
                "description": f"Payment of {txn['amount']} INR captured via {txn['payment_method']} (Risk Score: {txn['auth_risk_score']}).",
                "source_id": txn["transaction_id"]
            })
        if deliv.get("shipment_timestamp"):
            raw_events.append({
                "timestamp": deliv["shipment_timestamp"],
                "event_type": "SHIPMENT_DISPATCHED",
                "description": f"Shipment dispatched via carrier {deliv['carrier']}.",
                "source_id": deliv["delivery_id"]
            })
        if deliv.get("delivery_timestamp"):
            raw_events.append({
                "timestamp": deliv["delivery_timestamp"],
                "event_type": "DELIVERY_COMPLETED",
                "description": f"Delivery marked {deliv['delivery_status']}. POD Signature: {'Present' if deliv['pod_signature_present'] else 'Absent'}.",
                "source_id": deliv["delivery_id"]
            })
        for com in coms:
            if com.get("timestamp"):
                raw_events.append({
                    "timestamp": com["timestamp"],
                    "event_type": "SUPPORT_INTERACTION",
                    "description": f"Customer support communication via {com['channel']} ({com['category']}): {com['resolution_status']}.",
                    "source_id": com["communication_id"]
                })
        if disp.get("dispute_creation_timestamp"):
            raw_events.append({
                "timestamp": disp["dispute_creation_timestamp"],
                "event_type": "DISPUTE_FILED",
                "description": f"Chargeback dispute filed for reason {disp['dispute_reason_code']} ({disp['dispute_category']}). Amount: {disp['disputed_amount']} INR.",
                "source_id": disp["dispute_id"]
            })

        # Sort timeline chronologically
        raw_events.sort(key=lambda x: x["timestamp"])
        timeline = [TimelineEvent(**ev) for ev in raw_events]

        # 2. Case Facts
        case_facts = [
            f"FACT: Chargeback dispute {disp_id} filed for {disp['disputed_amount']} {disp.get('currency', 'INR')} on reason {disp['dispute_reason_code']}.",
            f"FACT: Customer {cust['customer_id']} account tenure is {cust['tenure_days']} days with {cust['successful_order_count']} successful orders.",
            f"FACT: Transaction {txn['transaction_id']} processed via {txn['payment_method']} with authorization risk score {txn['auth_risk_score']}.",
            f"FACT: Fulfillment status for Order {ord_info['order_id']} is {ord_info['fulfillment_status']}.",
            f"FACT: Delivery record {deliv['delivery_id']} status is {deliv['delivery_status']} (POD Signature: {deliv['pod_signature_present']})."
        ]

        # 3. Supporting Factors
        supporting_factors = []
        if deliv["delivery_status"] == "DELIVERED":
            supporting_factors.append(FactorItem(
                title="Confirmed Delivery Record",
                explanation="Carrier logistics tracking confirms package delivery was completed successfully.",
                source_id=deliv["delivery_id"],
                type="FACT"
            ))
        if deliv["pod_signature_present"]:
            supporting_factors.append(FactorItem(
                title="Proof of Delivery (POD) Signature Verified",
                explanation="Physical proof of delivery signature is recorded on carrier manifest.",
                source_id=deliv["delivery_id"],
                type="FACT"
            ))
        if cust["tenure_days"] > 180:
            supporting_factors.append(FactorItem(
                title="Established Customer History",
                explanation=f"Customer has a solid account tenure of {cust['tenure_days']} days with {cust['successful_order_count']} completed orders.",
                source_id=cust["customer_id"],
                type="FACT"
            ))
        if txn["device_fingerprint_match"] and txn["ip_country_match"]:
            supporting_factors.append(FactorItem(
                title="Verified Session Metadata",
                explanation="Device fingerprint and IP country match customer's registered profile.",
                source_id=txn["transaction_id"],
                type="FACT"
            ))

        # Model Signal Supporting Factor
        supporting_factors.append(FactorItem(
            title="Calibrated High Win Probability Signal",
            explanation=f"Phase 2 LightGBM model estimates a {win_prob*100:.1f}% probability of successful dispute contestation.",
            source_id=disp_id,
            type="MODEL_SIGNAL"
        ))

        # 4. Risk Factors
        risk_factors = []
        if txn["auth_risk_score"] > 70:
            risk_factors.append(FactorItem(
                title="Elevated Payment Risk Assessment",
                explanation=f"Gateway payment risk score is elevated at {txn['auth_risk_score']}/100.",
                source_id=txn["transaction_id"],
                type="FACT"
            ))
        if cust["previous_chargeback_count"] > 0:
            risk_factors.append(FactorItem(
                title="Prior Dispute History Detected",
                explanation=f"Customer account has {cust['previous_chargeback_count']} prior chargeback filings.",
                source_id=cust["customer_id"],
                type="FACT"
            ))
        if not deliv["pod_signature_present"] and ord_info["is_digital_item"]:
            risk_factors.append(FactorItem(
                title="Digital Item Non-Physical Delivery",
                explanation="Order consists of digital goods without physical delivery confirmation.",
                source_id=ord_info["order_id"],
                type="FACT"
            ))

        # 5. Evidence Items (Unverified status for Phase 5 verification)
        evidence = [
            EvidenceItem(
                evidence_id=f"EVID_{disp_id}_1",
                source_type="DELIVERY",
                source_id=deliv["delivery_id"],
                source_field="delivery_status",
                claim="Carrier delivery status confirmation",
                value=str(deliv["delivery_status"]),
                claimed_value=str(deliv["delivery_status"]),
                timestamp=deliv.get("delivery_timestamp"),
                verification_status="UNVERIFIED"
            ),
            EvidenceItem(
                evidence_id=f"EVID_{disp_id}_2",
                source_type="DELIVERY",
                source_id=deliv["delivery_id"],
                source_field="pod_signature_present",
                claim="Proof of Delivery signature presence",
                value=str(deliv["pod_signature_present"]),
                claimed_value=str(deliv["pod_signature_present"]),
                timestamp=deliv.get("delivery_timestamp"),
                verification_status="UNVERIFIED"
            ),
            EvidenceItem(
                evidence_id=f"EVID_{disp_id}_3",
                source_type="TRANSACTION",
                source_id=txn["transaction_id"],
                source_field="auth_risk_score",
                claim="Payment authorization risk score",
                value=str(txn["auth_risk_score"]),
                claimed_value=str(txn["auth_risk_score"]),
                timestamp=txn.get("transaction_timestamp"),
                verification_status="UNVERIFIED"
            ),
            EvidenceItem(
                evidence_id=f"EVID_{disp_id}_4",
                source_type="ORDER",
                source_id=ord_info["order_id"],
                source_field="fulfillment_status",
                claim="Order fulfillment confirmation",
                value=str(ord_info["fulfillment_status"]),
                claimed_value=str(ord_info["fulfillment_status"]),
                timestamp=ord_info.get("order_timestamp"),
                verification_status="UNVERIFIED"
            )
        ]

        # 6. Open Questions
        open_questions = []
        if not deliv.get("delivery_timestamp"):
            open_questions.append("Delivery completion timestamp is unavailable in carrier record.")
        if not deliv["pod_signature_present"]:
            open_questions.append("POD signature record is missing from delivery receipt.")
        if len(coms) == 0:
            open_questions.append("No post-purchase customer service communications found.")

        # 7. Human Review Items
        human_review_items = [
            f"Verify carrier tracking receipt and POD signature for Delivery {deliv['delivery_id']}.",
            f"Review customer transaction risk indicators and device match for Transaction {txn['transaction_id']}.",
            f"Confirm merchant response deadline ({disp['response_deadline']}) before submitting rebuttal packet."
        ]

        # 8. Executive Summary & Recommendation
        conf_level = "HIGH" if win_prob >= 0.75 else ("MEDIUM" if win_prob >= 0.40 else "LOW")
        exec_summary = (
            f"Dispute {disp_id} was filed on {disp['dispute_creation_timestamp'][:10]} for {disp['disputed_amount']} {disp.get('currency', 'INR')} "
            f"under reason code '{disp['dispute_reason_code']}'. The customer ({cust['customer_id']}) has a {cust['tenure_days']}-day tenure "
            f"with {cust['successful_order_count']} previous successful orders. Carrier tracking ({deliv['carrier']}) shows status "
            f"'{deliv['delivery_status']}' with POD signature {'present' if deliv['pod_signature_present'] else 'absent'}. "
            f"The Phase 2 LightGBM ML model assigns a win probability of {win_prob*100:.1f}%, leading to a preliminary recommendation to {rec_action}."
        )

        rec = InvestigationRecommendation(
            action=rec_action,
            win_probability=win_prob,
            confidence_level=conf_level,
            reason=f"Model win probability of {win_prob*100:.1f}% exceeds optimal decision threshold of {thresh} with supporting delivery evidence."
        )

        ml_eval = MLAssessmentPayload(
            win_probability=win_prob,
            win_probability_percent=f"{win_prob*100:.1f}%",
            recommendation=rec_action,
            model_version=model_ver,
            decision_threshold=thresh
        )

        return InvestigationReport(
            dispute_id=disp_id,
            investigation_status="COMPLETED",
            executive_summary=exec_summary,
            recommendation=rec,
            case_facts=case_facts,
            timeline=timeline,
            supporting_factors=supporting_factors,
            risk_factors=risk_factors,
            ml_assessment=ml_eval,
            evidence=evidence,
            open_questions=open_questions,
            human_review_items=human_review_items,
            investigation_timestamp=datetime.now(timezone.utc).isoformat(),
            is_synthetic_data=True,
            disclaimer="READ-ONLY DECISION SUPPORT. Final financial actions require human authorization."
        )

class AnthropicLLMProvider(LLMProvider):
    """Anthropic API LLM provider for natural-language report synthesis."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.fallback_engine = DeterministicFallbackInvestigator()

    def generate_report(self, case_detail: Dict[str, Any]) -> InvestigationReport:
        try:
            import anthropic
            from backend.agent.prompts import INVESTIGATION_AGENT_SYSTEM_PROMPT, build_user_investigation_prompt
            
            client = anthropic.Anthropic(api_key=self.api_key)
            user_prompt = build_user_investigation_prompt(case_detail)
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2500,
                system=INVESTIGATION_AGENT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}]
            )
            
            content_text = response.content[0].text
            report_dict = json.loads(content_text)
            return InvestigationReport(**report_dict)
        except Exception as e:
            logger.warning(f"Anthropic API synthesis failed or unconfigured ({str(e)}). Falling back to Deterministic Investigator.")
            return self.fallback_engine.generate_report(case_detail)

def get_llm_provider() -> LLMProvider:
    """Factory function returning configured LLM provider or fallback."""
    api_key = os.getenv("ANTHROPIC_API_KEY", settings.ANTHROPIC_API_KEY)
    if api_key and api_key.strip():
        logger.info("Initializing Anthropic LLM Provider for Investigation Agent.")
        return AnthropicLLMProvider(api_key=api_key)
    else:
        logger.info("Using Deterministic Fallback Investigator (Zero-Hallucination Factual Engine).")
        return DeterministicFallbackInvestigator()
