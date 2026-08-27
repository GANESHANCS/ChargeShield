# ChargeShield Read-Only AI Risk Investigation Agent Specification

> **Project:** ChargeShield — AI-Powered Chargeback Defense & Recovery Platform  
> **Track:** Razorpay AI Buildathon 2026 — Track 02: AI Risk Manager  
> **Status:** Phase 4 Read-Only AI Risk Investigation Agent Completed  

---

## 1. Executive Summary & Agent Purpose

The **ChargeShield AI Risk Investigation Agent** acts as an automated, evidence-grounded risk investigator for chargeback disputes. It synthesizes relational merchant records (customer tenure, payment risk scores, delivery manifests, customer support logs) and ML Win-Probability signals into a structured `InvestigationReport`.

> [!IMPORTANT]
> **READ-ONLY DECISION SUPPORT POLICY:**  
> The agent is strictly **read-only**. It does not perform autonomous financial transactions, auto-submit chargeback responses, issue refunds, or close disputes. All output serves as decision-support recommendations for human risk analysts.

---

## 2. Agent Architecture & Flow

```
┌─────────────────────────────────────────────────────────────┐
│                 POST /api/v1/cases/{id}/investigate        │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
     ┌───────────────────┐           ┌───────────────────┐
     │    CaseService    │           │ PredictionService │
     └─────────┬─────────┘           └─────────┬─────────┘
               │                               │
               └───────────────┬───────────────┘
                               ▼
            ┌────────────────────────────────────┐
            │       RiskInvestigationAgent       │
            └──────────────────┬─────────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
     ┌─────────────────────┐       ┌──────────────────────┐
     │ Anthropic Provider  │       │ Deterministic Engine │
     │  (Sonnet 3.5 synthesis)│    │  (Zero Hallucination)│
     └─────────────────────┘       └──────────────────────┘
                               │
                               ▼
            ┌────────────────────────────────────┐
            │        InvestigationReport         │
            └────────────────────────────────────┘
```

---

## 3. Fact vs. Inference Policy

To prevent AI hallucinations, the agent enforces a strict partitioning policy:
1. **Facts (`FACT`):** Grounded exclusively in database/CSV record values (e.g., carrier tracking status, customer order count, device fingerprint match).
2. **Model Signals (`MODEL_SIGNAL`):** Derived directly from Phase 2 LightGBM model predictions (`chargeshield_ml_v1`) and SHAP TreeExplainer attributions.
3. **Inferences (`INFERENCE`):** Explicitly categorized interpretations synthesized from factual signals.
4. **Unverified Evidence:** All evidence items are assigned `verification_status: "UNVERIFIED"`.

> [!NOTE]
> **Phase 5 Deferral:** Programmatic evidence validation and cryptographic hash/citation verification are intentionally deferred to Phase 5.

---

## 4. Investigation API Endpoint

- **Endpoint:** `POST /api/v1/cases/{dispute_id}/investigate`
- **Response Schema:** `InvestigationReport`
- **Example Response:**
```json
{
  "dispute_id": "DSP_000001",
  "investigation_status": "COMPLETED",
  "executive_summary": "Dispute DSP_000001 was filed on 2025-10-27 for 1797.72 INR under reason code '13.1_MERCH_NOT_RECEIVED'...",
  "recommendation": {
    "action": "CONTEST",
    "win_probability": 0.6816,
    "confidence_level": "MEDIUM",
    "reason": "Model win probability of 68.2% exceeds optimal decision threshold of 0.29 with supporting delivery evidence."
  },
  "case_facts": [
    "FACT: Chargeback dispute DSP_000001 filed for 1797.72 INR on reason 13.1_MERCH_NOT_RECEIVED.",
    "FACT: Customer CUS_002528 account tenure is 642 days with 31 successful orders."
  ],
  "timeline": [
    {
      "timestamp": "2025-10-13T15:00:00",
      "event_type": "ORDER_CREATED",
      "description": "Order ORD_002528 placed for 1797.72 INR (Electronics).",
      "source_id": "ORD_002528"
    }
  ],
  "supporting_factors": [
    {
      "title": "Calibrated High Win Probability Signal",
      "explanation": "Phase 2 LightGBM model estimates a 68.2% probability of successful dispute contestation.",
      "source_id": "DSP_000001",
      "type": "MODEL_SIGNAL"
    }
  ],
  "ml_assessment": {
    "win_probability": 0.6816,
    "win_probability_percent": "68.2%",
    "recommendation": "CONTEST",
    "model_version": "chargeshield_ml_v1",
    "decision_threshold": 0.29
  },
  "evidence": [
    {
      "evidence_id": "EVID_DSP_000001_1",
      "source_type": "DELIVERY",
      "source_id": "DEL_002528",
      "claim": "Carrier delivery status confirmation",
      "value": "FULFILLED",
      "verification_status": "UNVERIFIED"
    }
  ],
  "open_questions": [
    "Delivery completion timestamp is unavailable in carrier record."
  ],
  "human_review_items": [
    "Verify carrier tracking receipt and POD signature for Delivery DEL_002528.",
    "Confirm merchant response deadline (2025-11-03T15:01:00) before submitting rebuttal packet."
  ],
  "disclaimer": "READ-ONLY DECISION SUPPORT. Final financial actions require human authorization."
}
```

---

## 5. Limitations & Future Integration Points

1. **Read-Only Scope:** The agent cannot execute financial decisions or auto-submit rebuttal documentation to card networks.
2. **Evidence Validation:** Evidence verification against external API endpoints or hashes is deferred to Phase 5.
3. **Synthetic Context:** All case data originates from synthetic merchant datasets (`data/generator.py`).
