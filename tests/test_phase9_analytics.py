"""
Phase 9 Automated Tests for ChargeShield Production Observability & Operational Intelligence.
Verifies read-only analytics service, API router endpoints, live subsystem health checks,
risk/decision distributions, financial simulated recovery, and exportable operational report generation.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.db.database import get_db_session, init_db
from backend.analytics.service import analytics_service

client = TestClient(app)

@pytest.fixture(autouse=True)
def ensure_db():
    """Ensures database tables are initialized before tests."""
    init_db()

def test_analytics_overview_endpoint():
    """Verify GET /api/v1/analytics/overview returns aggregated operational metrics."""
    resp = client.get("/api/v1/analytics/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert "operational" in data
    assert "financial" in data
    assert "decisions" in data
    assert "risk" in data
    assert "evidence" in data
    assert "health" in data
    assert "generated_at" in data

    ops = data["operational"]
    assert ops["total_cases"] >= 1
    assert "pending_review" in ops
    assert "decided" in ops

def test_analytics_decisions_endpoint():
    """Verify GET /api/v1/analytics/decisions returns decision distributions and agreement metrics."""
    resp = client.get("/api/v1/analytics/decisions")
    assert resp.status_code == 200
    data = resp.json()
    assert "ai_recommendation_distribution" in data
    assert "human_decision_distribution" in data
    assert "agreement_rate" in data
    assert "disagreement_count" in data
    assert 0.0 <= data["agreement_rate"] <= 1.0

def test_analytics_risk_distribution_endpoint():
    """Verify GET /api/v1/analytics/risk-distribution returns win probability buckets and dispute reasons."""
    resp = client.get("/api/v1/analytics/risk-distribution")
    assert resp.status_code == 200
    data = resp.json()
    assert "win_probability_buckets" in data
    assert "dispute_reason_distribution" in data
    assert "disputed_amount_distribution" in data
    assert "0–20%" in data["win_probability_buckets"]
    assert "80–100%" in data["win_probability_buckets"]

def test_analytics_financial_endpoint():
    """Verify GET /api/v1/analytics/financial returns disputed values and simulated recoverable amount."""
    resp = client.get("/api/v1/analytics/financial")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_disputed_value" in data
    assert "contest_value" in data
    assert "simulated_recoverable_value" in data
    assert data["total_disputed_value"] > 0
    assert "disclaimer" in data

def test_analytics_evidence_endpoint():
    """Verify GET /api/v1/analytics/evidence returns evidence verification summary."""
    resp = client.get("/api/v1/analytics/evidence")
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_verification_rate" in data
    assert "verified_evidence_count" in data
    assert data["overall_verification_rate"] >= 0.0

def test_analytics_subsystem_health_endpoint():
    """Verify GET /api/v1/analytics/health performs real subsystem status checks."""
    resp = client.get("/api/v1/analytics/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["api"] == "HEALTHY"
    assert data["database"] in ["HEALTHY", "DEGRADED"]
    assert data["ml_engine"] in ["READY", "UNAVAILABLE"]
    assert data["evidence_engine"] in ["READY", "UNAVAILABLE"]
    assert data["review_engine"] in ["READY", "UNAVAILABLE"]
    assert data["dataset"] in ["AVAILABLE", "MISSING"]

def test_analytics_operational_report_endpoint():
    """Verify GET /api/v1/analytics/report generates exportable structured JSON report."""
    resp = client.get("/api/v1/analytics/report")
    assert resp.status_code == 200
    data = resp.json()
    assert "report_id" in data
    assert data["report_id"].startswith("RPT_")
    assert "model_version" in data
    assert "disclaimer" in data
    assert "operational_metrics" in data
    assert "financial_analytics" in data

def test_analytics_service_direct_execution():
    """Verify AnalyticsService methods directly."""
    overview = analytics_service.get_overview()
    assert overview.operational.total_cases > 0
    health = analytics_service.check_health()
    assert health.api == "HEALTHY"
