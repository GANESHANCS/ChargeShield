"""
Simulation Engine for ChargeShield Phase 9 Real-Time Event Intelligence.
Executes controlled, deterministic scenario simulations through the full risk & decision pipeline.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import threading
import uuid

from backend.services.event_service import event_service
from backend.services.financial_engine import financial_engine
from backend.services.risk_engine import risk_engine
from backend.services.case_service import case_service

SCENARIO_PROFILES = {
    "NORMAL_TRANSACTION": {
        "scenario_id": "NORMAL_TRANSACTION",
        "name": "Normal Transaction Triage",
        "description": "Low risk standard transaction with verified fulfillment and established tenure.",
        "amount": 2500.0,
        "auth_risk_score": 12,
        "tenure_days": 180,
        "dispute_history": 0,
        "pod_signature": True,
        "win_probability": 0.88,
        "dispute_reason_code": "10.4",
        "priority": "LOW"
    },
    "LOW_RISK_CHARGEBACK": {
        "scenario_id": "LOW_RISK_CHARGEBACK",
        "name": "Low Risk Chargeback",
        "description": "Minor dispute with high probability of successful contestation.",
        "amount": 4500.0,
        "auth_risk_score": 22,
        "tenure_days": 120,
        "dispute_history": 0,
        "pod_signature": True,
        "win_probability": 0.78,
        "dispute_reason_code": "10.4",
        "priority": "LOW"
    },
    "HIGH_RISK_CHARGEBACK": {
        "scenario_id": "HIGH_RISK_CHARGEBACK",
        "name": "High Risk Chargeback",
        "description": "Elevated transaction amount with unverified carrier delivery signature.",
        "amount": 18000.0,
        "auth_risk_score": 82,
        "tenure_days": 14,
        "dispute_history": 1,
        "pod_signature": False,
        "win_probability": 0.32,
        "dispute_reason_code": "13.1",
        "priority": "HIGH"
    },
    "CRITICAL_VALUE_DISPUTE": {
        "scenario_id": "CRITICAL_VALUE_DISPUTE",
        "name": "Critical Value Exposure Dispute",
        "description": "High monetary exposure requiring immediate operational escalation.",
        "amount": 75000.0,
        "auth_risk_score": 94,
        "tenure_days": 5,
        "dispute_history": 3,
        "pod_signature": False,
        "win_probability": 0.18,
        "dispute_reason_code": "10.4",
        "priority": "CRITICAL"
    },
    "EVIDENCE_MISMATCH": {
        "scenario_id": "EVIDENCE_MISMATCH",
        "name": "Evidence Citation Inconsistency",
        "description": "Carrier tracking shows delivered but IP geolocation and signature mismatch.",
        "amount": 12000.0,
        "auth_risk_score": 65,
        "tenure_days": 45,
        "dispute_history": 0,
        "pod_signature": False,
        "win_probability": 0.42,
        "dispute_reason_code": "13.1",
        "priority": "MEDIUM"
    },
    "LOW_WIN_PROBABILITY_CASE": {
        "scenario_id": "LOW_WIN_PROBABILITY_CASE",
        "name": "Low Win Probability (Unviable)",
        "description": "High chargeback history customer where contestation filing fee exceeds expected recovery.",
        "amount": 22000.0,
        "auth_risk_score": 88,
        "tenure_days": 10,
        "dispute_history": 4,
        "pod_signature": False,
        "win_probability": 0.15,
        "dispute_reason_code": "10.4",
        "priority": "HIGH"
    },
    "HIGH_WIN_PROBABILITY_CASE": {
        "scenario_id": "HIGH_WIN_PROBABILITY_CASE",
        "name": "High Win Probability (Strong Defense)",
        "description": "100% verified POD signature, matching AVS/CVV, and 300+ day customer tenure.",
        "amount": 3500.0,
        "auth_risk_score": 8,
        "tenure_days": 320,
        "dispute_history": 0,
        "pod_signature": True,
        "win_probability": 0.94,
        "dispute_reason_code": "10.4",
        "priority": "LOW"
    },
    "REPEAT_DISPUTE_CUSTOMER": {
        "scenario_id": "REPEAT_DISPUTE_CUSTOMER",
        "name": "Repeat Dispute Fraud Cluster",
        "description": "Customer account with multiple historical chargeback claims within 30 days.",
        "amount": 14000.0,
        "auth_risk_score": 79,
        "tenure_days": 28,
        "dispute_history": 4,
        "pod_signature": False,
        "win_probability": 0.28,
        "dispute_reason_code": "10.4",
        "priority": "HIGH"
    }
}

class SimulationEngine:
    def __init__(self):
        self._running = False
        self._scenario = "NORMAL_TRANSACTION"
        self._events_processed = 0
        self._transactions_processed = 0
        self._cases_created = 0
        self._last_event_time: Optional[str] = None
        self._lock = threading.Lock()
        self._sim_counter = 100

    def start_simulation(self, scenario: str = "NORMAL_TRANSACTION") -> Dict[str, Any]:
        """Start or reconfigure simulation mode."""
        if scenario not in SCENARIO_PROFILES:
            scenario = "NORMAL_TRANSACTION"

        with self._lock:
            self._running = True
            self._scenario = scenario
            self._last_event_time = datetime.now(timezone.utc).isoformat()

        event_service.publish_event(
            event_type="SIMULATION_STARTED",
            message=f"Simulation mode initialized with scenario profile '{scenario}'.",
            data_state="SIMULATION",
            source="SIMULATION_ENGINE",
            metadata={"scenario": scenario}
        )

        return self.get_status()

    def stop_simulation(self) -> Dict[str, Any]:
        """Stop active simulation mode."""
        with self._lock:
            self._running = False
            self._last_event_time = datetime.now(timezone.utc).isoformat()

        event_service.publish_event(
            event_type="SIMULATION_STOPPED",
            message="Simulation mode deactivated by user request.",
            data_state="SIMULATION",
            source="SIMULATION_ENGINE"
        )

        return self.get_status()

    def get_status(self) -> Dict[str, Any]:
        """Return current simulation engine status and counter metrics."""
        with self._lock:
            return {
                "running": self._running,
                "scenario": self._scenario,
                "events_processed": self._events_processed,
                "transactions_processed": self._transactions_processed,
                "cases_created": self._cases_created,
                "last_event_time": self._last_event_time or datetime.now(timezone.utc).isoformat(),
                "data_state": "SIMULATION"
            }

    def generate_transaction(self, scenario_override: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate ONE controlled simulated transaction and process it through the full pipeline.
        """
        target_scenario = scenario_override or self._scenario
        profile = SCENARIO_PROFILES.get(target_scenario, SCENARIO_PROFILES["NORMAL_TRANSACTION"])

        with self._lock:
            self._sim_counter += 1
            seq = self._sim_counter

        txn_id = f"TXN_SIM_{seq:05d}"
        dispute_id = f"DSP_SIM_{seq:05d}"
        cust_id = f"CUST_SIM_{seq:04d}"
        ord_id = f"ORD_SIM_{seq:05d}"
        del_id = f"DEL_SIM_{seq:05d}"

        amount = profile["amount"]
        win_prob = profile["win_probability"]
        auth_risk = profile["auth_risk_score"]
        priority = profile["priority"]
        r_code = profile["dispute_reason_code"]

        # Step 1: TRANSACTION_RECEIVED
        event_service.publish_event(
            event_type="TRANSACTION_RECEIVED",
            message=f"Simulated transaction {txn_id} received for ₹{amount:,.0f} INR.",
            data_state="SIMULATION",
            transaction_id=txn_id,
            metadata={"amount": amount, "currency": "INR", "payment_method": "CREDIT_CARD"}
        )

        # Step 2: TRANSACTION_VALIDATED
        event_service.publish_event(
            event_type="TRANSACTION_VALIDATED",
            message=f"Transaction {txn_id} passed schema validation & security integrity checks.",
            data_state="SIMULATION",
            transaction_id=txn_id
        )

        # Step 3: MODEL_PREDICTION_CREATED & RISK_EVALUATED
        rec = "CONTEST" if win_prob >= 0.29 else "DO_NOT_CONTEST"
        if 0.25 <= win_prob < 0.35:
            rec = "MANUAL_REVIEW"

        event_service.publish_event(
            event_type="MODEL_PREDICTION_CREATED",
            message=f"LightGBM classifier scored win probability at {(win_prob * 100):.1f}%. Recommendation: {rec}.",
            data_state="SIMULATION",
            transaction_id=txn_id,
            metadata={"win_probability": win_prob, "recommendation": rec}
        )

        risk_assessment = risk_engine.assess_risk(
            dispute_id=dispute_id,
            transaction_id=txn_id,
            amount=amount,
            dispute_reason=r_code,
            win_probability=win_prob,
            decision_threshold=0.29
        )

        event_service.publish_event(
            event_type="RISK_EVALUATED",
            message=f"Risk engine classified case exposure as {risk_assessment['priority']} priority.",
            data_state="SIMULATION",
            transaction_id=txn_id,
            metadata=risk_assessment
        )

        # Step 4: FINANCIAL_IMPACT_CALCULATED
        fin_impact = financial_engine.calculate_impact(amount, win_prob)
        event_service.publish_event(
            event_type="FINANCIAL_IMPACT_CALCULATED",
            message=f"Financial impact calculated: Net contest advantage ₹{fin_impact['net_financial_advantage']:,.0f} INR.",
            data_state="SIMULATION",
            transaction_id=txn_id,
            metadata=fin_impact
        )

        # Step 5: Inject case record into CaseService
        case_data = {
            "dispute_id": dispute_id,
            "transaction_id": txn_id,
            "customer_id": cust_id,
            "order_id": ord_id,
            "disputed_amount": amount,
            "currency": "INR",
            "dispute_reason_code": r_code,
            "dispute_category": "FRAUD" if r_code == "10.4" else "PRODUCT",
            "dispute_status": "UNDER_REVIEW",
            "dispute_creation_timestamp": datetime.now(timezone.utc).isoformat(),
            "response_deadline": datetime.now(timezone.utc).isoformat(),
            "data_state": "SIMULATION"
        }

        cust_data = {
            "customer_id": cust_id,
            "tenure_days": profile["tenure_days"],
            "historical_chargeback_count": profile["dispute_history"],
            "successful_order_count": 15 if profile["tenure_days"] > 30 else 2,
            "customer_segment": "REGULAR" if profile["tenure_days"] > 60 else "NEW"
        }

        ord_data = {
            "order_id": ord_id,
            "order_amount": amount,
            "order_timestamp": datetime.now(timezone.utc).isoformat(),
            "product_category": "ELECTRONICS",
            "fulfillment_status": "DELIVERED"
        }

        txn_data = {
            "transaction_id": txn_id,
            "payment_method": "CREDIT_CARD",
            "auth_risk_score": auth_risk,
            "cvv_match": "M",
            "avs_match": "Y",
            "ip_country": "IN"
        }

        del_data = {
            "delivery_id": del_id,
            "order_id": ord_id,
            "carrier": "BLUE_DART",
            "delivery_status": "DELIVERED",
            "pod_signature_present": profile["pod_signature"],
            "pod_match_status": "MATCHED" if profile["pod_signature"] else "UNVERIFIED",
            "shipment_timestamp": datetime.now(timezone.utc).isoformat(),
            "delivery_timestamp": datetime.now(timezone.utc).isoformat()
        }

        case_service.add_simulated_case(
            dispute=case_data,
            customer=cust_data,
            order=ord_data,
            transaction=txn_data,
            delivery=del_data
        )

        event_service.publish_event(
            event_type="CASE_CREATED",
            message=f"Dispute case {dispute_id} created for transaction {txn_id}.",
            data_state="SIMULATION",
            dispute_id=dispute_id,
            transaction_id=txn_id
        )

        event_service.publish_event(
            event_type="CASE_PRIORITIZED",
            message=f"Case {dispute_id} placed in review queue with priority {priority}.",
            data_state="SIMULATION",
            dispute_id=dispute_id
        )

        # Step 6: EVIDENCE_ANALYSIS
        event_service.publish_event(
            event_type="EVIDENCE_ANALYSIS_STARTED",
            message=f"Cross-verifying evidence citations for dispute {dispute_id}.",
            data_state="SIMULATION",
            dispute_id=dispute_id
        )

        ver_score = 1.0 if profile["pod_signature"] else 0.5
        event_service.publish_event(
            event_type="EVIDENCE_ANALYSIS_COMPLETED",
            message=f"Evidence verification complete for dispute {dispute_id} (Score: {ver_score*100:.0f}%).",
            data_state="SIMULATION",
            dispute_id=dispute_id,
            metadata={"verification_score": ver_score}
        )

        with self._lock:
            self._transactions_processed += 1
            self._cases_created += 1
            self._events_processed += 8
            self._last_event_time = datetime.now(timezone.utc).isoformat()

        return {
            "dispute_id": dispute_id,
            "transaction_id": txn_id,
            "scenario": target_scenario,
            "disputed_amount": amount,
            "win_probability": win_prob,
            "recommendation": rec,
            "priority": priority,
            "data_state": "SIMULATION"
        }

# Global singleton instance
simulation_engine = SimulationEngine()
