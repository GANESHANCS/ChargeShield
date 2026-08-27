# ChargeShield Evidence Verification & Citation Engine Specification

> **Project:** ChargeShield — AI-Powered Chargeback Defense & Recovery Platform  
> **Track:** Razorpay AI Buildathon 2026 — Track 02: AI Risk Manager  
> **Status:** Phase 5 Evidence Verification Engine Completed & Fully Tested  

---

## 1. Executive Summary & Purpose

The **ChargeShield Evidence Verification & Citation Engine** provides automated, deterministic claim verification for investigation reports generated in Phase 4. It verifies AI-generated evidence claims against Phase 3 authoritative relational records and Phase 2 ML outputs.

> [!CRITICAL]
> **SOURCE-OF-TRUTH POLICY:**  
> The system **never** marks an evidence item as `VERIFIED` merely because an LLM or fallback investigator generated it. Verification requires an explicit field-level comparison between the claimed value and the authoritative record retrieved from Phase 3 services. AI claims are never silently overwritten to force a match.

---

## 2. Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                 POST /api/v1/cases/{id}/verify              │
└──────────────────────────────┬──────────────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
┌──────────────────────┐              ┌────────────────────────┐
│  InvestigationAgent  │              │    EvidenceVerifier    │
│  (Phase 4 Report)    │              │ (Read-Only Orchestrator)│
└───────────┬──────────┘              └───────────┬────────────┘
            │                                     │
            └──────────────────┬──────────────────┘
                               ▼
                ┌──────────────────────────────┐
                │        Source Retriever      │
                │(CaseService & PredService)   │
                └──────────────┬───────────────┘
                               │
                               ▼
                ┌──────────────────────────────┐
                │      Value Comparator        │
                │(Exact, Normalized, Numeric)  │
                └──────────────┬───────────────┘
                               │
                               ▼
                ┌──────────────────────────────┐
                │ VerifiedInvestigationResponse│
                └──────────────────────────────┘
```

---

## 3. Verification Statuses & Match Types

### Explicit Verification Statuses:
- **`VERIFIED`:** Claimed value matches authoritative source record.
- **`MISMATCH`:** Source record exists but claimed value conflicts with actual source value.
- **`MISSING_SOURCE`:** Referenced entity (e.g. `DEL_999999`) cannot be found in database.
- **`UNSUPPORTED`:** Factual assertion cannot be supported by available source fields.
- **`UNVERIFIABLE`:** Source record exists but data is unpopulated or missing.

### Comparison Match Types:
- **`EXACT`:** Literal identity match after trimming.
- **`NORMALIZED_MATCH`:** Case-insensitive string match, boolean normalization (`"true"` vs `True`), or numeric precision equality.
- **`PARTIAL_MATCH`:** Substring match.
- **`MISMATCH`:** Direct value conflict.
- **`NOT_APPLICABLE`:** Missing or unmappable source field.

---

## 4. Source Field Mappings

Authoritative source fields verified against Phase 1/3 entities:
- **`DELIVERY`:** `delivery_status`, `pod_signature_present`, `shipment_timestamp`, `delivery_timestamp`, `carrier`.
- **`TRANSACTION`:** `amount`, `payment_method`, `transaction_status`, `auth_risk_score`, `device_fingerprint_match`, `ip_country_match`.
- **`ORDER`:** `order_amount`, `fulfillment_status`, `is_digital_item`, `product_category`, `order_timestamp`.
- **`CUSTOMER`:** `tenure_days`, `successful_order_count`, `previous_chargeback_count`, `account_status`.
- **`DISPUTE`:** `disputed_amount`, `dispute_reason_code`, `dispute_status`, `response_deadline`.
- **`ML_MODEL`:** `win_probability`, `recommendation`, `model_version`, `decision_threshold`.

---

## 5. Citations & References

Every verified evidence item produces:
1. **Machine-Readable Citation (`SourceReference`):** `entity_type`, `entity_id`, `field`.
2. **Human-Readable Citation (`citation_label`):** e.g., `"Delivery DEL_002528 → delivery_status"`.

---

## 6. API Endpoint

- **Endpoint:** `POST /api/v1/cases/{dispute_id}/verify`
- **Response Schema:** `VerifiedInvestigationResponse`
- **Example Verification Output (`DSP_000001`):**
```json
{
  "dispute_id": "DSP_000001",
  "verification_summary": {
    "total_evidence": 5,
    "verified": 5,
    "mismatched": 0,
    "missing_source": 0,
    "unsupported": 0,
    "unverifiable": 0,
    "verification_rate": 1.0
  },
  "verification_results": [
    {
      "evidence_id": "EVID_DSP_000001_1",
      "source_type": "DELIVERY",
      "source_id": "DEL_002528",
      "source_field": "delivery_status",
      "claim": "Carrier delivery status confirmation",
      "claimed_value": "NOT_APPLICABLE",
      "actual_source_value": "NOT_APPLICABLE",
      "verification_status": "VERIFIED",
      "match_type": "EXACT",
      "verification_reason": "Claimed value 'NOT_APPLICABLE' exactly matches authoritative source value 'NOT_APPLICABLE'.",
      "citation_label": "Delivery DEL_002528 \u2192 delivery_status",
      "source_reference": {
        "entity_type": "DELIVERY",
        "entity_id": "DEL_002528",
        "field": "delivery_status"
      }
    }
  ]
}
```

---

## 7. Future Integration & Limitations

1. **Read-Only Scope:** Verifier retrieves data without mutating any records.
2. **Phase 6 Readiness:** Output format is structured for UI side-by-side claim vs source display and human reviewer approvals.
