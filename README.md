# ChargeShield 🛡️
> **AI-Powered Chargeback Defense & Recovery Platform**  
> *Razorpay AI Buildathon 2026 — Track 02: AI Risk Manager*

> [!IMPORTANT]
> **SAFETY & SYNTHETIC DATA DISCLAIMER:**  
> All data (transactions, disputes, customer profiles, delivery traces) used by ChargeShield is generated synthetically using deterministic seeds. No real customer, merchant, card network, or Razorpay proprietary data is used. ChargeShield NEVER executes autonomous financial submissions or dispute settlements; all consequential financial actions require human authorization.

---

## 1. Product Summary & Central Question

**Central Product Question:**
> *"Should this merchant spend resources contesting this chargeback, and if so, can ChargeShield automatically assemble the evidence needed for a strong case?"*

### Core Division of Labor

| Layer | Responsibility | Safety Control |
|---|---|---|
| **ML Model (LightGBM)** | Calculates calibrated `win_probability` (0–100%) and SHAP risk factors | Evaluated strictly on held-out test data with cost-sensitive threshold selection |
| **AI Agent (Claude)** | Conducts structured evidence investigation via read-only tools | Programmatic evidence validator verifies claims against DB records |
| **Human Reviewer** | Reviews case recommendation, edits packet, and authorizes action | **Only layer allowed to trigger financial state transitions** |

---

## 2. End-to-End State Machine

```
NEW → ML SCORED → INVESTIGATION → RECOMMENDATION → HUMAN REVIEW
→ APPROVED / REJECTED / EDITED → SUBMITTED / CONCEDED → OUTCOME
```

---

## 3. Project Structure

```
chargeshield/
├── frontend/           # React + TypeScript + Vite + Tailwind CSS
├── backend/            # FastAPI REST API
│   ├── api/            # API Route handlers
│   ├── services/       # Core business logic
│   ├── db/             # SQLAlchemy ORM schemas and DB connection
│   └── core/           # Config, JSON logging, safety settings
├── ml/                 # Win probability model, SHAP explainability, pipeline
├── agent/              # Read-only tool orchestration & evidence validator
├── data/               # Reproducible synthetic data generator
├── docs/               # Architecture documents and phase reports
├── tests/              # Pytest suite
├── .env.example        # Environment variable template
├── .gitignore
└── README.md
```

---

## 4. Local Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### Backend Setup
1. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   # macOS/Linux:
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure Environment Variables:
   ```bash
   cp .env.example .env
   ```

4. Run the Backend API:
   ```bash
   python -m uvicorn backend.main:app --reload --port 8000
   ```
   API docs will be accessible at: `http://127.0.0.1:8000/docs`  
   Health check endpoint: `http://127.0.0.1:8000/health`

### Frontend Setup
1. Navigate to the `frontend/` folder:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the Development Server:
   ```bash
   npm run dev
   ```
   App will be accessible at: `http://localhost:3000`

---

---

## 5. Verification & Testing

### Running the Full Pytest Suite (194/194 Tests Passing)
```bash
python -m pytest
```

### Running the Golden-Path End-to-End Test
```bash
python -m pytest tests/test_golden_path_e2e.py -v
```

### Building Frontend Bundle
```bash
cd frontend
npm run build
```

---

## 6. Key Production Features & Architectural Safeguards

1. **LightGBM ML Win Probability Model & SHAP Explainer:** Calibrated Platt-scaled probability predictions with feature importance drivers.
2. **Deterministic & Anthropic Hybrid Risk Investigator:** Deep investigative agent with structured JSON output and fallback safety.
3. **Evidence SHA-256 Verification & Storage:** Secure upload engine with checksum integrity validation and mime-type enforcement.
4. **Representment Evidence Package PDF Export:** ReportLab automated legal document generation for chargeback defense (`GET /api/v1/cases/{id}/representment-package`).
5. **HMAC Webhook Ingestion:** Webhook endpoint with HMAC-SHA256 signature verification and idempotency protection.
6. **Strict Simulation Isolation:** Production records (`PRODUCTION`) and simulation experiments (`SIMULATION`) are strictly isolated to prevent metric pollution.
7. **Append-Only Decision Audit Log:** Human reviewer decisions (`CONTEST`, `DO_NOT_CONTEST`, `ESCALATE`) are recorded immutably into SQLite/PostgreSQL.
