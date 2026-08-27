# ChargeShield Deployment Guide

## Overview
This deployment guide provides instructions for launching ChargeShield across LOCAL development, STAGING validation, and PRODUCTION environments.

---

## Environment Matrix

| Environment | Database | Auth / JWT | Background Worker | Static Assets |
| :--- | :--- | :--- | :--- | :--- |
| **LOCAL** | SQLite (`chargeshield.db`) | Local Secret (`dev-secret`) | In-Memory `BackgroundTasks` | Vite Dev Server (`localhost:5173`) |
| **STAGING** | PostgreSQL 15 | Signed Staging JWT | Async Worker Thread | Compiled Static Assets / Nginx |
| **PRODUCTION** | Managed PostgreSQL (RDS/Cloud SQL) | HSM / Vault JWT Secret | Distributed Queue (Celery/Redis) | CDN + Nginx / Reverse Proxy |

---

## 1. Local Development Setup
```bash
# 1. Start FastAPI Backend
cd backend
python -m uvicorn main:app --reload --port 8000

# 2. Start Vite Frontend
cd frontend
npm run dev
```

---

## 2. Production Docker Deployment
```bash
# Build and run backend with PostgreSQL using Docker Compose
docker-compose up --build -d

# Verify Container Health
docker-compose ps
curl http://localhost:8000/health
```

---

## 3. Database Migration Execution
```bash
# Apply database migrations to PostgreSQL
alembic upgrade head
```

---

## 4. Operational Monitoring & Health Verification
- **Live Health Probe:** `GET /health`
- **Container Readiness:** `GET /ready`
- **Background Jobs Polling:** `GET /api/v1/jobs/{job_id}`
- **OpenAPI Documentation:** `http://localhost:8000/docs`
