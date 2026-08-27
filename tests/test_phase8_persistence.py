"""
Phase 8 Automated Tests for ChargeShield Persistent Audit, Security & Production Hardening.
Verifies database persistence, restart survival, audit API, pagination, duplicate decision protection,
security headers, sanitized error handling, and audit filtering capabilities.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.db.database import get_db_session, init_db
from backend.db.models import ReviewStateModel, ReviewDecisionModel
from backend.review.service import ReviewService, DuplicateDecisionError
from backend.review.schemas import DecisionRequest, DecisionEnum

client = TestClient(app)

@pytest.fixture(autouse=True)
def ensure_db():
    """Ensures DB tables exist before each test."""
    init_db()

def test_database_table_creation():
    """Verify that review_states and review_decisions tables are initialized."""
    with get_db_session() as session:
        state_count = session.query(ReviewStateModel).count()
        decision_count = session.query(ReviewDecisionModel).count()
        assert isinstance(state_count, int)
        assert isinstance(decision_count, int)

def test_decision_persistence_and_restart_survival():
    """Verify human review decisions persist in SQLite across service recreation."""
    service_a = ReviewService()
    test_dispute = "DSP_000001"

    with get_db_session() as session:
        session.query(ReviewDecisionModel).filter(ReviewDecisionModel.dispute_id == test_dispute).delete()
        session.query(ReviewStateModel).filter(ReviewStateModel.dispute_id == test_dispute).delete()

    req = DecisionRequest(
        reviewer_id="analyst_test_01",
        decision=DecisionEnum.CONTEST,
        reason="Verified carrier signature and order delivery logs."
    )
    rec = service_a.submit_decision(test_dispute, req)
    assert rec.dispute_id == test_dispute
    assert rec.decision == DecisionEnum.CONTEST

    service_b = ReviewService()
    status = service_b.get_review_status(test_dispute)
    assert status.value == "DECIDED"

    pkg = service_b.get_review_package(test_dispute)
    assert pkg.review_status.value == "DECIDED"
    assert len(pkg.decisions) >= 1
    assert pkg.decisions[-1].decision == DecisionEnum.CONTEST
    assert pkg.decisions[-1].reviewer_id == "analyst_test_01"

def test_duplicate_decision_protection_http_409():
    """Verify attempting to submit a second decision on a DECIDED case returns 409 Conflict."""
    test_dispute = "DSP_000002"

    with get_db_session() as session:
        session.query(ReviewDecisionModel).filter(ReviewDecisionModel.dispute_id == test_dispute).delete()
        session.query(ReviewStateModel).filter(ReviewStateModel.dispute_id == test_dispute).delete()

    resp1 = client.post(
        f"/api/v1/review/cases/{test_dispute}/decision",
        json={"reviewer_id": "analyst_sarah_01", "decision": "CONTEST", "reason": "First valid decision."}
    )
    assert resp1.status_code == 200

    resp2 = client.post(
        f"/api/v1/review/cases/{test_dispute}/decision",
        json={"reviewer_id": "analyst_sarah_01", "decision": "DO_NOT_CONTEST", "reason": "Second duplicate attempt."}
    )
    assert resp2.status_code == 409
    assert "already been DECIDED" in resp2.json()["detail"]

def test_audit_log_endpoint_filtering_and_pagination():
    """Verify GET /api/v1/review/audit supports filters and structured pagination."""
    resp = client.get("/api/v1/review/audit?page=1&page_size=5")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "total_pages" in data
    assert data["page"] == 1
    assert data["page_size"] == 5

# --- Dedicated Audit Filter Tests ---

def test_audit_api_dispute_id_filtering():
    """Verify filtering GET /api/v1/review/audit by dispute_id returns matching records only."""
    with get_db_session() as session:
        session.query(ReviewDecisionModel).filter(ReviewDecisionModel.dispute_id.in_(["DSP_000010", "DSP_000011"])).delete()
        session.query(ReviewStateModel).filter(ReviewStateModel.dispute_id.in_(["DSP_000010", "DSP_000011"])).delete()

    client.post("/api/v1/review/cases/DSP_000010/decision", json={
        "reviewer_id": "analyst_a",
        "decision": "CONTEST",
        "reason": "Carrier proof confirmed."
    })
    client.post("/api/v1/review/cases/DSP_000011/decision", json={
        "reviewer_id": "analyst_b",
        "decision": "DO_NOT_CONTEST",
        "reason": "Non-contestable chargeback."
    })

    resp = client.get("/api/v1/review/audit?dispute_id=DSP_000010")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["dispute_id"] == "DSP_000010"

def test_audit_api_reviewer_id_filtering():
    """Verify filtering GET /api/v1/review/audit by reviewer_id returns matching records only."""
    resp = client.get("/api/v1/review/audit?reviewer_id=analyst_a")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["reviewer_id"] == "analyst_a"

def test_audit_api_decision_filtering():
    """Verify filtering GET /api/v1/review/audit by decision enum value returns matching records only."""
    resp = client.get("/api/v1/review/audit?decision=DO_NOT_CONTEST")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["decision"] == "DO_NOT_CONTEST"

def test_audit_api_combined_filtering():
    """Verify combining dispute_id, reviewer_id, and decision query filters."""
    resp = client.get("/api/v1/review/audit?dispute_id=DSP_000010&reviewer_id=analyst_a&decision=CONTEST")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["dispute_id"] == "DSP_000010"
    assert data["items"][0]["reviewer_id"] == "analyst_a"
    assert data["items"][0]["decision"] == "CONTEST"

def test_audit_api_empty_result_filtering():
    """Verify filtering by non-existent dispute_id returns zero items and valid total_pages."""
    resp = client.get("/api/v1/review/audit?dispute_id=DSP_NON_EXISTENT_999999")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["total_pages"] == 1

def test_queue_pagination():
    """Verify GET /api/v1/review/queue supports page and page_size query parameters."""
    resp = client.get("/api/v1/review/queue?page=1&page_size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert len(data["items"]) <= 10
    assert "total_pages" in data

def test_mandatory_reason_validation():
    """Verify submission fails with 422 if reason is too short or empty."""
    resp_short = client.post(
        "/api/v1/review/cases/DSP_000003/decision",
        json={"reviewer_id": "analyst_sarah_01", "decision": "CONTEST", "reason": "abc"}
    )
    assert resp_short.status_code == 422

    resp_empty_reviewer = client.post(
        "/api/v1/review/cases/DSP_000003/decision",
        json={"reviewer_id": "", "decision": "CONTEST", "reason": "Valid reason provided."}
    )
    assert resp_empty_reviewer.status_code == 422

def test_security_response_headers():
    """Verify mandatory security response headers are present on all responses."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("X-XSS-Protection") == "1; mode=block"

def test_sanitized_exception_responses():
    """Verify internal server errors return sanitized JSON without leaking stack traces."""
    resp = client.get("/api/v1/cases/DSP_NON_EXISTENT")
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data
    assert "Traceback" not in data["detail"]
    assert "d:\\" not in data["detail"].lower()
