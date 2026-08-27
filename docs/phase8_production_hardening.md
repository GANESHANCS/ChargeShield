# ChargeShield — Phase 8: Persistent Audit, Security & Production Hardening

## Overview
Phase 8 hardens ChargeShield by transitioning in-memory review states and decisions into durable SQLite database storage (`chargeshield.db`) managed via **SQLAlchemy ORM** and **Alembic migrations**.

---

## 1. Database Architecture & Schema

### Database Configuration
- **Engine**: SQLite via SQLAlchemy (`sqlite:///./chargeshield.db`)
- **Connection Management**: Scoped session context manager (`get_db_session()`) with auto-commit on success and auto-rollback on exception.

### Table Definitions

#### `review_states` Table
Tracks the lifecycle status of dispute cases during human risk review.
- `dispute_id` (VARCHAR(64), Primary Key, Indexed): Unique identifier of the dispute case.
- `review_status` (VARCHAR(32), Default `'PENDING_REVIEW'`): State of the case (`PENDING_REVIEW`, `IN_REVIEW`, `DECIDED`, `ESCALATED`).
- `updated_at` (VARCHAR(64)): ISO 8601 UTC timestamp of last status update.

#### `review_decisions` Table
Immutable, append-only audit trail recording authorized human decisions.
- `decision_id` (VARCHAR(64), Primary Key): Formatted decision ID (`DEC_{dispute_id}_{index}`).
- `dispute_id` (VARCHAR(64), Indexed): Associated dispute case ID.
- `reviewer_id` (VARCHAR(64), Indexed): Identifier of human analyst authorizing the decision.
- `decision` (VARCHAR(32), Indexed): Authorized human action (`CONTEST`, `DO_NOT_CONTEST`, `ESCALATE`).
- `reason` (VARCHAR(2048)): Mandatory human justification reason.
- `ai_recommendation` (VARCHAR(32)): Advisory recommendation from ML engine at decision time.
- `ai_win_probability` (FLOAT): ML win probability score at decision time.
- `verification_rate` (FLOAT, Default `1.0`): Evidence verification rate at decision time.
- `created_at` (VARCHAR(64), Indexed): ISO 8601 UTC timestamp when decision was committed.

---

## 2. Alembic Migrations

Alembic manages database schema evolution.

### Migration Environment Setup
- `alembic.ini`: Database migration configuration referencing `chargeshield.db`.
- `alembic/versions/001_initial_phase8_tables.py`: Initial schema creation script.

### Executing Migrations Manually
```bash
# Apply migrations to latest schema
alembic upgrade head

# Roll back migration if needed
alembic downgrade -1
```

---

## 3. Paginated API Endpoints

### 1. `GET /api/v1/review/queue`
Retrieves paginated review queue ordered by transparent priority score.
- **Query Parameters**:
  - `status` (string, optional): Filter by `PENDING_REVIEW`, `IN_REVIEW`, `DECIDED`, `ESCALATED`.
  - `recommendation` (string, optional): Filter by `CONTEST`, `DO_NOT_CONTEST`.
  - `min_prob` (float, optional): Filter minimum win probability.
  - `max_prob` (float, optional): Filter maximum win probability.
  - `page` (int, default `1`): Current page number.
  - `page_size` (int, default `20`): Number of items per page.
- **Response**: `ReviewQueueResponse` with `items`, `total`, `pending_count`, `decided_count`, `escalated_count`, `page`, `page_size`, `total_pages`.

### 2. `GET /api/v1/review/audit`
Retrieves paginated decision audit log from SQLite.
- **Query Parameters**:
  - `dispute_id` (string, optional): Search by dispute ID.
  - `reviewer_id` (string, optional): Search by reviewer ID.
  - `decision` (string, optional): Filter by `CONTEST`, `DO_NOT_CONTEST`, `ESCALATE`.
  - `page` (int, default `1`): Current page number.
  - `page_size` (int, default `20`): Number of items per page.
- **Response**: `AuditLogResponse` containing append-only decision records with pagination metadata.

---

## 4. Security Hardening & CORS Strategy

### Response Headers Middleware
All API responses automatically include defense-in-depth security response headers:
- `X-Content-Type-Options: nosniff`: Prevents MIME type sniffing.
- `X-Frame-Options: DENY`: Protects against clickjacking.
- `X-XSS-Protection: 1; mode=block`: Enables browser XSS filtering.

### CORS Configuration
Configured in `backend/core/config.py` via `ALLOWED_ORIGINS` restricting API access to authorized frontend origin domains (`http://localhost:5173`, `http://127.0.0.1:5173`, `http://127.0.0.1:8000`).

### Sanitized Exception Handler
Unhandled exceptions are intercepted by a global exception handler in `backend/main.py`. User-facing HTTP 500 responses return a sanitized JSON error payload preventing stack trace, file path, or database credential leaks.

---

## 5. Duplicate Decision Protection & Human Boundary

- **HTTP 409 Conflict**: Submitting a decision for a case with `review_status == 'DECIDED'` returns a `409 Conflict` error, preventing duplicate or conflicting decisions.
- **Mandatory Rationale**: Decisions require a non-empty `reviewer_id` and a `reason` of at least 5 characters (enforced via Pydantic validators and returning `422 Unprocessable Entity` on violation).
- **Human Authorization Boundary**: AI recommendations remain advisory. No autonomous payment processor submission or financial execution occurs without explicit human authorization.

---

## 6. System Verification Commands

### Run Full Test Suite (54 Tests)
```bash
python -m pytest tests/
```

### Build Production Frontend
```bash
cd frontend
npm run build
```
