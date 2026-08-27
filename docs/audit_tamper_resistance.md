# ChargeShield Audit & Event Integrity Architecture

## Overview
ChargeShield enforces an immutable, audit-ready operational record for all automated AI triages, risk evaluations, and human reviewer decisions. This document outlines the architectural safeguards and tamper-resistance mechanisms embedded in the system.

---

## Key Principles & Technical Controls

### 1. Append-Only Persistence
- Human review decisions are persisted to the `review_decisions` relational table.
- No `UPDATE` or `DELETE` API endpoints are exposed for decision or outcome audit logs.
- Audit records contain the reviewer ID, timestamp (`datetime.now(timezone.utc)`), decision (`CONTEST`, `DO_NOT_CONTEST`, `ESCALATE`), AI model recommendation, AI win probability, verification rate, and mandatory human justification.

### 2. Explicit Data Provenance Isolation
- Every record and event in the system carries an authoritative `data_state` attribute (`PRODUCTION`, `SIMULATION`, `HISTORICAL`).
- Simulation events are partitioned and explicitly isolated from production outcome metrics, threshold evaluations, and learning feedback loops.

### 3. Credential & Sensitive Data Filtering
- Middleware and structured loggers sanitize incoming request and header data.
- Passwords, JWT secrets, bearer tokens, and full primary account numbers (PAN) are strictly scrubbed prior to writing to application logs or event streams.

### 4. Correlation ID Propagation
- Every HTTP request generates or propagates an `X-Correlation-ID` header.
- Correlation IDs link API invocation, database operations, background tasks, and audit logs into a unified, traceable execution trace.

### 5. Multi-Stage Ingestion Fingerprinting
- CSV dataset batch uploads generate SHA-256 content hashes (`batch_hash`).
- Re-submitting an identical payload triggers idempotency protection, preventing duplicate record creation or audit log pollution.
