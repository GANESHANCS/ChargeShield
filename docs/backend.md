# ChargeShield Risk Case Backend & API Layer Specification

> **Project:** ChargeShield — AI-Powered Chargeback Defense & Recovery Platform  
> **Track:** Razorpay AI Buildathon 2026 — Track 02: AI Risk Manager  
> **Status:** Phase 3 Backend + API Layer Completed  

---

## 1. Executive Summary & Backend Architecture

The **ChargeShield Backend** acts as the central orchestration engine for Risk Operations. Built with **FastAPI**, it bridges the synthetic relational merchant datasets (`data/generated/`) and the verified ML Win-Probability Engine (`ml/artifacts/model.joblib`), serving structured APIs to future frontend dashboards and read-only AI investigation agents.

```
┌─────────────────────────────────────────────────────────────┐
│                       FastAPI Router                        │
│                 (/api/v1/cases, /health)                    │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
     ┌───────────────────┐           ┌───────────────────┐
     │    CaseService    │           │ PredictionService │
     └─────────┬─────────┘           └─────────┬─────────┘
               │                               │
               ▼                               ▼
     ┌───────────────────┐           ┌───────────────────┐
     │ Synthetic Data    │           │ ML Win Engine     │
     │  (data/generated) │           │ (LightGBM v1.0)   │
     └───────────────────┘           └───────────────────┘
```

---

## 2. API Endpoints Reference

### A. System Health Check
- **Endpoint:** `GET /health`
- **Description:** Verifies backend health and synthetic environment safety flags.

### B. List Risk Cases (Paginated & Filtered)
- **Endpoint:** `GET /api/v1/cases`
- **Query Parameters:**
  - `page` (int, default=1): Page number
  - `page_size` (int, default=20, max=100): Cases per page
  - `status` (string, optional): Dispute status filter (e.g. `CLOSED`, `NEW`)
  - `reason` (string, optional): Dispute reason code filter (e.g. `13.1_MERCH_NOT_RECEIVED`, `10.4_UNAUTHORIZED`)
  - `min_prob` / `max_prob` (float, optional): Win probability range filter
  - `sort_by` (string, default=`newest`): `newest`, `oldest`, `amount_desc`, `amount_asc`, `prob_desc`, `prob_asc`

### C. Get Single Case Detail
- **Endpoint:** `GET /api/v1/cases/{dispute_id}`
- **Description:** Returns full relational graph: dispute, customer history, transaction risk metrics, order details, delivery tracking, support communications, and ML win prediction.

### D. Get Case ML Prediction
- **Endpoint:** `GET /api/v1/cases/{dispute_id}/prediction`
- **Description:** Executes ML inference using the trained `chargeshield_ml_v1` model artifact to return calibrated probability and decision recommendation (`CONTEST`, `MANUAL_REVIEW`, `DO_NOT_CONTEST`).

### E. Get Case SHAP Model Explanation
- **Endpoint:** `GET /api/v1/cases/{dispute_id}/explanation`
- **Description:** Returns top positive and negative SHAP attribution factors explaining *why* the model assigned a specific win probability.

---

## 3. Data & Prediction Flows

1. **Relational Join Flow:** `dispute_id` $\rightarrow$ `CaseService` $\rightarrow$ joins `disputes`, `transactions`, `orders`, `deliveries`, `customers`, `communications`, `previous_disputes`.
2. **Prediction Flow:** `dispute_id` $\rightarrow$ `PredictionService` $\rightarrow$ `ChargebackPredictor` (cached model) $\rightarrow$ preprocessor pipeline $\rightarrow$ LightGBM probability $\rightarrow$ cost-sensitive threshold cutoff ($t=0.29$).
3. **Explanation Flow:** `raw_features` $\rightarrow$ `DisputeExplainer` $\rightarrow$ SHAP `TreeExplainer` $\rightarrow$ top positive/negative risk factor attributions.

---

## 4. Running the Server & Test Suite

### Run Backend Server (Development Mode)
```powershell
python -m backend.main
```
Server opens at `http://127.0.0.1:8000`. Interactive OpenAPI documentation available at `http://127.0.0.1:8000/docs`.

### Run Test Suite (Phases 0 - 3)
```powershell
python -m pytest tests/
```

---

## 5. Security & Synthetic Data Disclaimer

> [!IMPORTANT]
> **SYNTHETIC DATA & NON-AUTONOMOUS DISCLAIMER:**  
> All endpoints return synthetically generated evaluation data. ChargeShield does not access Razorpay production databases, live card networks, or financial gateways. The ML predictions and API recommendations represent **human decision support** and do not automatically submit chargeback responses or initiate financial transactions.
