# ChargeShield Multi-Tenant Architecture Roadmap

## Executive Summary
This document defines the architectural blueprint for transitioning ChargeShield into a enterprise multi-tenant SaaS platform. It details organizational tenancy models, schema isolation strategies, RBAC scoping, and model versioning per tenant.

---

## 1. Tenancy Model Strategy

### Tenant Hierarchy
```
Organization (Tenant)
 ├── Users & Roles (ADMIN, ANALYST, REVIEWER, AUDITOR)
 ├── Merchant Profiles & Gateways (Stripe, Razorpay, Adyen)
 ├── Dispute Cases & Transactions
 ├── Custom Risk & Decision Policies
 └── Tenant ML Models & Threshold Configurations
```

### Database Isolation Options
1. **Discriminator Column Isolation (Shared DB, Shared Schema):**
   - Add indexed `org_id` column to all primary tables (`review_states`, `review_decisions`, `model_outcomes`, `learning_feedback`, `threshold_evaluations`).
   - Row-Level Security (RLS) policies in PostgreSQL enforce `WHERE org_id = current_tenant_id()`.
   - *Recommended Phase 14 approach due to operational simplicity and efficiency.*

2. **Schema-Per-Tenant Isolation (Shared DB, Separate Schemas):**
   - Each tenant receives an isolated PostgreSQL schema (`tenant_org_01`, `tenant_org_02`).
   - Connection pool dynamically switches `search_path` per incoming tenant JWT request.

---

## 2. Security & RBAC Tenant Boundaries
- **JWT Claims:** Include `org_id` in the signed JWT bearer token payload.
- **Tenant Scope Enforcement:** Middleware extracts `org_id` and sets thread-local or contextvar tenant scope for all DB queries.
- **Cross-Tenant Prevention:** Attempting to query or mutate a resource belonging to a different `org_id` returns HTTP 404 / 403.

---

## 3. Custom Model & Threshold Governance
- **Tenant Baseline Thresholds:** Each organization maintains its own decision threshold calibration based on tenant-specific dispute reason distributions and financial fee structures.
- **Tenant Model Version Registry:** Model versions (`model_versions`) are scoped by `org_id`, enabling custom retrained XGBoost/LightGBM models for enterprise tenants.
