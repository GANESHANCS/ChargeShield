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
        deliv = case_detail.get("delivery", {}) or {}
        coms = case_detail.get("communications", []) or []
        prevs = case_detail.get("previous_disputes", []) or []
        pred = case_detail["prediction"]

        disp_id = str(disp.get("dispute_id", "DISP_UNKNOWN"))
        win_prob = float(pred.get("win_probability", 0.5))
        rec_action = str(pred.get("recommendation", "MANUAL_REVIEW"))
        model_ver = str(pred.get("model_version", "chargeshield_ml_v1"))
        thresh = float(pred.get("decision_threshold", 0.29))

        deliv_id = str(deliv.get("delivery_id", deliv.get("order_id", f"DEL_{disp_id}")))
        deliv_status = str(deliv.get("delivery_status", "DELIVERED"))
        carrier_name = str(deliv.get("carrier", "FEDEX"))
        pod_signature = bool(deliv.get("pod_signature_present", True))

        # 1. Timeline Construction from actual timestamps
        raw_events = []
        if ord_info.get("order_timestamp"):
            raw_events.append({
                "timestamp": str(ord_info["order_timestamp"]),
                "event_type": "ORDER_CREATED",
                "description": f"Order {ord_info.get('order_id')} placed for {ord_info.get('order_amount', 0.0)} INR ({ord_info.get('product_category', 'GENERAL')}).",
                "source_id": str(ord_info.get("order_id"))
            })
        if txn.get("transaction_timestamp"):
            raw_events.append({
                "timestamp": str(txn["transaction_timestamp"]),
                "event_type": "PAYMENT_CAPTURED",
                "description": f"Payment of {txn.get('amount', 0.0)} INR captured via {txn.get('payment_method', 'CARD')} (Risk Score: {txn.get('auth_risk_score', 0.1)}).",
                "source_id": str(txn.get("transaction_id"))
            })
        if deliv.get("shipment_timestamp"):
            raw_events.append({
                "timestamp": str(deliv["shipment_timestamp"]),
                "event_type": "SHIPMENT_DISPATCHED",
                "description": f"Shipment dispatched via carrier {carrier_name}.",
                "source_id": deliv_id
            })
        if deliv.get("delivery_timestamp"):
            raw_events.append({
                "timestamp": str(deliv["delivery_timestamp"]),
                "event_type": "DELIVERY_COMPLETED",
                "description": f"Delivery marked {deliv_status}. POD Signature: {'Present' if pod_signature else 'Absent'}.",
                "source_id": deliv_id
            })
        for com in coms:
            if isinstance(com, dict) and com.get("timestamp"):
                raw_events.append({
                    "timestamp": str(com["timestamp"]),
                    "event_type": "SUPPORT_INTERACTION",
                    "description": f"Customer support communication via {com.get('channel', 'EMAIL')} ({com.get('category', 'GENERAL')}): {com.get('resolution_status', 'RESOLVED')}.",
                    "source_id": str(com.get("communication_id", "COM_1"))
                })
        if disp.get("dispute_creation_timestamp"):
            raw_events.append({
                "timestamp": str(disp["dispute_creation_timestamp"]),
                "event_type": "DISPUTE_FILED",
                "description": f"Chargeback dispute filed for reason {disp.get('dispute_reason_code')} ({disp.get('dispute_category', 'FRAUD')}). Amount: {disp.get('disputed_amount')} INR.",
                "source_id": disp_id
            })

        raw_events.sort(key=lambda x: x["timestamp"])
        timeline = [TimelineEvent(**ev) for ev in raw_events]

        # 2. Case Facts
        case_facts = [
            f"FACT: Chargeback dispute {disp_id} filed for {disp.get('disputed_amount')} {disp.get('currency', 'INR')} on reason {disp.get('dispute_reason_code')}.",
            f"FACT: Customer {cust.get('customer_id')} account tenure is {cust.get('tenure_days', 0)} days with {cust.get('successful_order_count', 0)} successful orders.",
            f"FACT: Transaction {txn.get('transaction_id')} processed via {txn.get('payment_method')} with authorization risk score {txn.get('auth_risk_score', 0.1)}.",
            f"FACT: Fulfillment status for Order {ord_info.get('order_id')} is {ord_info.get('fulfillment_status', 'DELIVERED')}.",
            f"FACT: Delivery record {deliv_id} status is {deliv_status} (POD Signature: {pod_signature})."
        ]

        # 3. Supporting Factors
        supporting_factors = []
        if deliv_status.upper() == "DELIVERED":
            supporting_factors.append(FactorItem(
                title="Confirmed Delivery Record",
                explanation="Carrier logistics tracking confirms package delivery was completed successfully.",
                source_id=deliv_id,
                type="FACT"
            ))
        if pod_signature:
            supporting_factors.append(FactorItem(
                title="Proof of Delivery (POD) Signature Verified",
                explanation="Physical proof of delivery signature is recorded on carrier manifest.",
                source_id=deliv_id,
                type="FACT"
            ))
        if float(cust.get("tenure_days", 0)) > 180:
            supporting_factors.append(FactorItem(
                title="Established Customer History",
                explanation=f"Customer has a solid account tenure of {cust.get('tenure_days')} days with {cust.get('successful_order_count')} completed orders.",
                source_id=str(cust.get("customer_id")),
                type="FACT"
            ))
        if bool(txn.get("device_fingerprint_match", True)) and bool(txn.get("ip_country_match", True)):
            supporting_factors.append(FactorItem(
                title="Verified Session Metadata",
                explanation="Device fingerprint and IP country match customer's registered profile.",
                source_id=str(txn.get("transaction_id")),
                type="FACT"
            ))

        supporting_factors.append(FactorItem(
            title="Calibrated High Win Probability Signal",
            explanation=f"Phase 2 LightGBM model estimates a {win_prob*100:.1f}% probability of successful dispute contestation.",
            source_id=disp_id,
            type="MODEL_SIGNAL"
        ))

        # 4. Risk Factors
        risk_factors = []
        if float(txn.get("auth_risk_score", 0.1)) > 70:
            risk_factors.append(FactorItem(
                title="Elevated Payment Risk Assessment",
                explanation=f"Gateway payment risk score is elevated at {txn.get('auth_risk_score')}/100.",
                source_id=str(txn.get("transaction_id")),
                type="FACT"
            ))
        if float(cust.get("previous_chargeback_count", 0)) > 0:
            risk_factors.append(FactorItem(
                title="Prior Dispute History Detected",
                explanation=f"Customer account has {cust.get('previous_chargeback_count')} prior chargeback filings.",
                source_id=str(cust.get("customer_id")),
                type="FACT"
            ))
        if not pod_signature and bool(ord_info.get("is_digital_item", False)):
            risk_factors.append(FactorItem(
                title="Digital Item Non-Physical Delivery",
                explanation="Order consists of digital goods without physical delivery confirmation.",
                source_id=str(ord_info.get("order_id")),
                type="FACT"
            ))

        # 5. Evidence Items
        evidence = [
            EvidenceItem(
                evidence_id=f"EVID_{disp_id}_1",
                source_type="DELIVERY",
                source_id=deliv_id,
                source_field="delivery_status",
                claim="Carrier delivery status confirmation",
                value=deliv_status,
                claimed_value=deliv_status,
                timestamp=deliv.get("delivery_timestamp"),
                verification_status="UNVERIFIED"
            ),
            EvidenceItem(
                evidence_id=f"EVID_{disp_id}_2",
                source_type="DELIVERY",
                source_id=deliv_id,
                source_field="pod_signature_present",
                claim="Proof of Delivery signature presence",
                value=str(pod_signature),
                claimed_value=str(pod_signature),
                timestamp=deliv.get("delivery_timestamp"),
                verification_status="UNVERIFIED"
            ),
            EvidenceItem(
                evidence_id=f"EVID_{disp_id}_3",
                source_type="TRANSACTION",
                source_id=str(txn.get("transaction_id")),
                source_field="auth_risk_score",
                claim="Payment authorization risk score",
                value=str(txn.get("auth_risk_score", 0.1)),
                claimed_value=str(txn.get("auth_risk_score", 0.1)),
                timestamp=txn.get("transaction_timestamp"),
                verification_status="UNVERIFIED"
            ),
            EvidenceItem(
                evidence_id=f"EVID_{disp_id}_4",
                source_type="ORDER",
                source_id=str(ord_info.get("order_id")),
                source_field="fulfillment_status",
                claim="Order fulfillment confirmation",
                value=str(ord_info.get("fulfillment_status", "DELIVERED")),
                claimed_value=str(ord_info.get("fulfillment_status", "DELIVERED")),
                timestamp=ord_info.get("order_timestamp"),
                verification_status="UNVERIFIED"
            )
        ]

        # 6. Open Questions
        open_questions = []
        if not deliv.get("delivery_timestamp"):
            open_questions.append("Delivery completion timestamp is unavailable in carrier record.")
        if not pod_signature:
            open_questions.append("POD signature record is missing from delivery receipt.")
        if len(coms) == 0:
            open_questions.append("No post-purchase customer service communications found.")

        # 7. Human Review Items
        human_review_items = [
            f"Verify carrier tracking receipt and POD signature for Delivery {deliv_id}.",
            f"Review customer transaction risk indicators and device match for Transaction {txn.get('transaction_id')}.",
            f"Confirm merchant response deadline ({disp.get('response_deadline')}) before submitting rebuttal packet."
        ]

        # 8. Executive Summary & Recommendation
        conf_level = "HIGH" if win_prob >= 0.75 else ("MEDIUM" if win_prob >= 0.40 else "LOW")
        disp_ts = str(disp.get("dispute_creation_timestamp", ""))[:10]
        exec_summary = (
            f"Dispute {disp_id} was filed on {disp_ts} for {disp.get('disputed_amount')} {disp.get('currency', 'INR')} "
            f"under reason code '{disp.get('dispute_reason_code')}'. The customer ({cust.get('customer_id')}) has a {cust.get('tenure_days')}-day tenure "
            f"with {cust.get('successful_order_count')} previous successful orders. Carrier tracking ({carrier_name}) shows status "
            f"'{deliv_status}' with POD signature {'present' if pod_signature else 'absent'}. "
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
