"""
Phase 8 Backend Tests for ChargeShield Real-Time Fraud Operations, Model Monitoring & Production Intelligence.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.operations_monitor import operations_monitor
from backend.services.alert_engine import alert_engine
from backend.services.model_monitor import model_monitor
from backend.services.feedback_service import feedback_service
from backend.services.case_service import case_service

client = TestClient(app)


def test_operations_monitor_service():
    """Test real operations monitor service calculations and honest INSUFFICIENT_DATA structures."""
    ops = operations_monitor.get_operations_overview()
    assert ops.total_active_disputes > 0
    assert ops.total_disputed_value > 0.0
    assert ops.average_review_time.status == "INSUFFICIENT_DATA"
    assert ops.currency == "INR"
    assert "INTEGRITY SCORE" in ops.data_quality_status


def test_alert_engine_service():
    """Test rule-driven operational alerts output."""
    alerts = alert_engine.get_active_alerts()
    assert isinstance(alerts, list)
    assert len(alerts) >= 1
    # Check that each alert has required fields
    for a in alerts:
        assert a.alert_id is not None
        assert a.severity in ["INFO", "WARNING", "HIGH", "CRITICAL"]
        assert a.category is not None
        assert a.title is not None
        assert a.recommended_action is not None


def test_model_monitor_service():
    """Test model monitoring foundation and honest AWAITING_BASELINE status."""
    mon = model_monitor.get_monitoring_status()
    assert mon.current_model == "LightGBM Classifier"
    assert mon.prediction_count > 0
    assert abs(mon.threshold_in_use - 0.29) < 0.01
    assert mon.drift_status == "AWAITING_BASELINE"
    assert mon.data_state_label == "HISTORICAL / PRODUCTION"
    assert "0-20%" in mon.prediction_distribution


def test_feedback_service_metrics():
    """Test model feedback agreement rate and disagreement case collection."""
    fb = feedback_service.get_feedback_metrics()
    assert fb.total_human_decisions >= 0
    assert 0.0 <= fb.agreement_rate <= 1.0
    assert isinstance(fb.disagreement_cases, list)


def test_case_timeline_generation():
    """Test case chronological investigation timeline construction."""
    timeline = case_service.get_case_timeline("DSP_000001")
    assert timeline is not None
    assert timeline["dispute_id"] == "DSP_000001"
    events = timeline["events"]
    assert len(events) >= 5
    stages = [e["stage"] for e in events]
    assert "TRANSACTION_CREATED" in stages
    assert "DISPUTE_RECEIVED" in stages
    assert "MODEL_PREDICTION" in stages
    assert "EVIDENCE_VERIFIED" in stages
    assert "CASE_PRIORITIZED" in stages


def test_operations_api_overview():
    """Test GET /api/v1/operations/overview endpoint."""
    response = client.get("/api/v1/operations/overview")
    assert response.status_code == 200
    data = response.json()
    assert "total_active_disputes" in data
    assert "estimated_recoverable_value" in data
    assert data["currency"] == "INR"


def test_operations_api_alerts():
    """Test GET /api/v1/operations/alerts endpoint."""
    response = client.get("/api/v1/operations/alerts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_operations_api_health():
    """Test GET /api/v1/operations/health endpoint."""
    response = client.get("/api/v1/operations/health")
    assert response.status_code == 200
    data = response.json()
    assert data["api"] == "HEALTHY"
    assert data["database"] == "HEALTHY"


def test_model_api_monitoring():
    """Test GET /api/v1/model/monitoring endpoint."""
    response = client.get("/api/v1/model/monitoring")
    assert response.status_code == 200
    data = response.json()
    assert data["current_model"] == "LightGBM Classifier"
    assert data["drift_status"] == "AWAITING_BASELINE"


def test_model_api_feedback():
    """Test GET /api/v1/model/feedback endpoint."""
    response = client.get("/api/v1/model/feedback")
    assert response.status_code == 200
    data = response.json()
    assert "agreement_rate" in data
    assert "disagreement_cases" in data


def test_case_timeline_api():
    """Test GET /api/v1/cases/DSP_000001/timeline endpoint."""
    response = client.get("/api/v1/cases/DSP_000001/timeline")
    assert response.status_code == 200
    data = response.json()
    assert data["dispute_id"] == "DSP_000001"
    assert len(data["events"]) >= 5
