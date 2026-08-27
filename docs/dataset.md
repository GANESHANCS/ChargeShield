# ChargeShield Synthetic Dataset Documentation & Specification

> **Project:** ChargeShield — AI-Powered Chargeback Defense & Recovery Platform  
> **Track:** Razorpay AI Buildathon 2026 — Track 02: AI Risk Manager  
> **Status:** Phase 1 Data Foundation Specification

---

> [!IMPORTANT]
> **SYNTHETIC DATA SAFETY DISCLAIMER:**  
> All entity records, customer profiles, payment transactions, delivery logs, support communications, and dispute resolution outcomes documented here are generated **100% synthetically** using deterministic seeds (`data/generator.py`). No real cardholder, merchant, card network, or Razorpay proprietary data is present or accessed.

---

## 1. Entity Relational Architecture

The synthetic dataset represents a full-stack merchant operating environment:

```
[ Customers ] ──1:N──> [ Orders ] ──1:1──> [ Transactions ]
                           │                     │
                           1:1                   1:1
                           ▼                     ▼
                     [ Deliveries ]        [ Disputes ]
                                                 │
                                                 ├──1:N──> [ Communications ]
                                                 └──1:N──> [ Previous Disputes ]
```

---

## 2. Target Variable & Latent Process

### Prediction Target: `contest_success`
- **Definition:** Binary indicator ($1$ or $0$) representing whether the merchant successfully contests the chargeback.
- **Latent Process Formulation:**
  $$\text{logit}(z) = \beta_0 + \sum_{i} \beta_i X_i + \epsilon$$
  where $X_i$ represents pre-triage observable factors:
  - **Delivery & POD Proof:** $+2.5$ logit boost if package delivered with Proof of Delivery (POD) signature.
  - **Device & IP Consistency:** $+2.0$ logit boost if device fingerprint and IP country match customer history (for fraud disputes).
  - **Support Resolution:** $+1.5$ logit boost if customer support ticket was resolved prior to chargeback.
  - **Serial Disputer Penalty:** $-2.0$ logit penalty if customer has $>1$ lost historical chargeback.
  - **In-Transit Non-Delivery:** $-3.5$ logit penalty for `13.1_MERCH_NOT_RECEIVED` disputes where carrier tracking confirms non-delivery.
  - **Noise Term:** $\epsilon \sim \mathcal{N}(0, 0.85)$ modeling card issuer adjudication variance.
- **Probability & Label:**
  $$P(\text{win}) = \sigma(z) = \frac{1}{1 + e^{-z}}$$
  $$\text{contest\_success} = \begin{cases} 1 & \text{if } P(\text{win}) \ge 0.5 \\ 0 & \text{otherwise} \end{cases}$$

---

## 3. Strict Target Leakage Prevention Policy

To prevent artificial accuracy inflated by data leakage, fields are strictly segregated:

| Category | Description | Permitted in ML Features? | Example Fields |
|---|---|---|---|
| **PRE_TRIAGE** | Known at dispute filing time | **YES** | `dispute_reason_code`, `order_amount`, `pod_signature_present`, `auth_risk_score`, `tenure_days` |
| **TARGET** | Ground truth label | **NO (Prediction Target)** | `contest_success` |
| **POST_OUTCOME** | Known only after dispute resolution | **STRICTLY BARRED** | `final_outcome` (`WON`/`LOST`), `settlement_date`, adjudication notes |

---

## 4. Complete Data Dictionary

### A. Customers Entity (`customers.csv`)
| Field Name | Type | Category | Nullable | Description |
|---|---|---|---|---|
| `customer_id` | String | IDENTIFIER | No | Unique synthetic customer ID |
| `account_creation_date` | ISO String | PRE_TRIAGE | No | Customer signup timestamp |
| `tenure_days` | Integer | PRE_TRIAGE | No | Account tenure in days at order time |
| `country` | String | PRE_TRIAGE | No | Billing country code (IN, US, AE, etc.) |
| `total_order_count` | Integer | PRE_TRIAGE | No | Historical order count |
| `successful_order_count` | Integer | PRE_TRIAGE | No | Completed orders without disputes |
| `previous_dispute_count` | Integer | PRE_TRIAGE | No | Total prior disputes filed |
| `previous_chargeback_count` | Integer | PRE_TRIAGE | No | Total prior chargebacks lost |
| `refund_count` | Integer | PRE_TRIAGE | No | Voluntary refunds issued |
| `account_status` | String | PRE_TRIAGE | No | ACTIVE, DORMANT, FLAGGED |
| `customer_segment` | String | PRE_TRIAGE | No | VIP, REGULAR, NEW, HIGH_RISK |

### B. Disputes Entity (`disputes.csv`)
| Field Name | Type | Category | Nullable | Description |
|---|---|---|---|---|
| `dispute_id` | String | IDENTIFIER | No | Unique synthetic dispute ID |
| `transaction_id` | String | IDENTIFIER | No | FK to transactions |
| `order_id` | String | IDENTIFIER | No | FK to orders |
| `customer_id` | String | IDENTIFIER | No | FK to customers |
| `dispute_creation_timestamp` | ISO String | PRE_TRIAGE | No | Issuer filing timestamp |
| `dispute_reason_code` | String | PRE_TRIAGE | No | Standard reason code (e.g. `13.1_MERCH_NOT_RECEIVED`, `10.4_UNAUTHORIZED`) |
| `dispute_category` | String | PRE_TRIAGE | No | Category (NON_RECEIPT, FRAUD, QUALITY) |
| `disputed_amount` | Float | PRE_TRIAGE | No | Disputed monetary value in INR (₹) |
| `dispute_status` | String | PRE_TRIAGE | No | Stage: NEW, UNDER_REVIEW, CLOSED |
| `response_deadline` | ISO String | PRE_TRIAGE | No | Card network submission deadline |
| `evidence_deadline` | ISO String | PRE_TRIAGE | No | Internal target gathering deadline |
| `dispute_stage` | String | PRE_TRIAGE | No | FIRST_DISPUTE, PRE_ARBITRATION |
| `contest_success` | Integer | TARGET | No | **TARGET (1=Won, 0=Lost)** |
| `final_outcome` | String | POST_OUTCOME | No | **BARRED FROM ML (WON/LOST)** |
| `settlement_date` | ISO String | POST_OUTCOME | Yes | **BARRED FROM ML (Bank timestamp)** |

---

## 5. Dataset Generation & Verification Commands

### Generate Standard Dataset (Seed 42)
```powershell
python -m data.generator
```

### Run Phase 1 Data Quality & Leakage Test Suite
```powershell
python -m pytest tests/test_dataset_generator.py
```
