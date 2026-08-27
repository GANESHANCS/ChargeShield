# ChargeShield Architecture & System Specifications

## 1. System Vision & Core Division of Labor
ChargeShield is an AI-powered chargeback defense and recovery platform designed with cost-sensitive ML decisioning, grounded evidence investigation, and human-in-the-loop financial controls.

| Layer | Function | Primary Output |
|---|---|---|
| ML Model (LightGBM) | Win probability estimation & risk ranking | Calibrated `win_probability` (0–100%) + SHAP feature attributions |
| AI Agent (Claude Tool-Calling) | Structured evidence retrieval & missing evidence flagging | Grounded evidence packet & recommendation |
| Programmatic Evidence Validator | Claim verification against retrieved tool records | `verified: true/false` status per claim |
| Human Reviewer | Consequential financial action authorization | Final decision: `APPROVED`, `REJECTED`, `EDITED` |

## 2. End-to-End State Machine
```
NEW → ML SCORED → INVESTIGATION → RECOMMENDATION → HUMAN REVIEW
→ APPROVED / REJECTED / EDITED → SUBMITTED / CONCEDED → OUTCOME
```

## 3. Safety Guarantees
1. No autonomous financial execution.
2. Programmatic validation of all agent claims against database sources.
3. Immutable append-only audit trail.
4. Transparent labeling of synthetic data across UI and API.
