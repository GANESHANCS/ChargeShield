# ChargeShield Human Review & Decision Workflow Specification

> **Project:** ChargeShield — AI-Powered Chargeback Defense & Recovery Platform  
> **Track:** Razorpay AI Buildathon 2026 — Track 02: AI Risk Manager  
> **Status:** Phase 6 Human Review Workflow Completed & Verified  

---

## 1. Executive Summary & Purpose

The **ChargeShield Human Review & Decision Workflow** implements a human-in-the-loop decision-support framework. The central core principle is: **AI recommends. Evidence verifies. Human authorizes.** 

> [!CRITICAL]
> **NO AUTONOMOUS FINANCIAL EXECUTION:**  
> AI predictions and investigation reports are purely advisory. The ChargeShield platform **never** executes payment reversals, bank refunds, or autonomous network chargeback submissions. Every contestation or escalation requires explicit authorization by a human reviewer.

---

## 2. Architecture & Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                       Case Selection                        │
│                   GET /api/v1/review/queue                  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Reviewer Case Package                    │
│             GET /api/v1/review/cases/{dispute_id}           │
│  (Case Detail + ML Prediction + AI Report + Evidence)       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Human Review Decision                    │
│        POST /api/v1/review/cases/{dispute_id}/decision      │
│     (CONTEST / DO_NOT_CONTEST / ESCALATE + Mandatory Reason) │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  Append-Only Decision Record                │
│                   DEC_DSP_000001_001 (Audit)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Case Review States & Decision Enum

### Case Review States (`ReviewStateEnum`):
- **`PENDING_REVIEW`:** Case is queued awaiting analyst inspection.
- **`IN_REVIEW`:** Analyst has opened the reviewer package.
- **`DECIDED`:** Analyst has submitted a final decision (`CONTEST` or `DO_NOT_CONTEST`).
- **`ESCALATED`:** Analyst escalated case for higher-authority review.

### Human Decisions (`DecisionEnum`):
- **`CONTEST`:** Human approves contesting the chargeback (authorizes rebuttal packet generation).
- **`DO_NOT_CONTEST`:** Human accepts chargeback / decides not to contest.
- **`ESCALATE`:** Human escalates complex case for senior management sign-off.

---

## 4. API Endpoints

1. `GET /api/v1/review/queue`
   - Returns prioritized review queue ordered by transparent score (threshold proximity, verification risk, disputed amount).
   - Supports filtering by `status`, `recommendation`, `min_prob`, and `max_prob`.

2. `GET /api/v1/review/cases/{dispute_id}`
   - Returns complete `ReviewCasePackage` aggregating Case Detail, ML Prediction, Phase 4 Report, Phase 5 Verification, and Decision History.

3. `POST /api/v1/review/cases/{dispute_id}/decision`
   - Records human decision immutably. Returns `DecisionRecord`.

---

## 5. Demonstration Output (`DSP_000001`)

```json
{
  "decision_id": "DEC_DSP_000001_001",
  "dispute_id": "DSP_000001",
  "reviewer_id": "analyst_sarah_01",
  "decision": "CONTEST",
  "reason": "Verified carrier tracking and delivery confirmation supports contesting this chargeback.",
  "ai_recommendation": "CONTEST",
  "ai_win_probability": 0.6816,
  "verification_rate": 1.0,
  "created_at": "2026-08-22T17:41:54.962224+00:00"
}
```

---

## 6. Duplicate Protection & AI/Human Disagreement

- **Duplicate Decision Protection:** Submitting a second decision on a case already in `DECIDED` status returns HTTP 409 Conflict.
- **AI/Human Disagreement Support:** System preserves AI recommendation alongside human decision, allowing analysts to override AI recommendations (e.g. AI recommends `CONTEST`, human chooses `DO_NOT_CONTEST`).

---

## 7. Limitations & Future Integration

1. **No Financial Execution:** Human decision is an audit record only.
2. **Phase 7 Integration:** Decision records will feed into Phase 7 Audit & Compliance System.
