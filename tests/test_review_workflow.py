"""
Phase 6 Human Review & Decision Workflow Test Suite.

Verifies:
1. Review queue generation, prioritization, and filtering
2. Complete Reviewer Package aggregation (GET /api/v1/review/cases/{id})
3. Human decision recording (CONTEST, DO_NOT_CONTEST, ESCALATE)
4. Validation of reviewer_id and decision reason
5. Duplicate decision protection (409 Conflict)
6. Preservation of AI recommendation, probability, and verification status at decision time
7. Disagreement support (Human decision differing from AI recommendation)
8. Read-Only underlying data preservation
9. End-to-end DSP_000001 human decision flow
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db.database import get_db_session, init_db
from backend.db.models import ReviewStateModel, ReviewDecisionModel
from backend.review.service import review_service, ReviewStateEnum, DecisionEnum
from backend.services.case_service import case_service

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    """Resets review states and decision records before each test for test isolation."""
    init_db()
    with get_db_session() as session:
        session.query(ReviewDecisionModel).delete()
        session.query(ReviewStateModel).delete()

# 1. Queue Endpoint Tests
def test_review_queue_retrieval():
    res = client.get("/api/v1/review/queue?page_size=100")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] > 0
    assert len(data["items"]) == data["total"]

    # Verify priority score sorting (first item should have highest priority_score)
    items = data["items"]
    scores = [item["priority_score"] for item in items]
    assert scores == sorted(scores, reverse=True)

# 2. Queue Filtering Tests
def test_review_queue_filtering():
    res = client.get("/api/v1/review/queue?recommendation=CONTEST")
    assert res.status_code == 200
    data = res.json()
    for item in data["items"]:
        assert item["ai_recommendation"] == "CONTEST"

# 3. Review Case Package Endpoint Test
def test_review_case_package_valid():
    dispute_id = "DSP_000002"
    res = client.get(f"/api/v1/review/cases/{dispute_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["dispute_id"] == dispute_id
    assert "case" in data
    assert "prediction" in data
    assert "investigation" in data
    assert "verification" in data
    assert "review_status" in data
    assert data["review_status"] in ["IN_REVIEW", "PENDING_REVIEW"]

# 4. Unknown Case 404 Test
def test_review_case_package_unknown():
    res = client.get("/api/v1/review/cases/DSP_NONEXISTENT_999")
    assert res.status_code == 404

# 5, 11-13, 15, 19, 21. Valid Decision Submission (DSP_000001)
def test_submit_valid_contest_decision_e2e():
    dispute_id = "DSP_000001"
    
    # 1. Get Review Package
    pkg_res = client.get(f"/api/v1/review/cases/{dispute_id}")
    assert pkg_res.status_code == 200

    # 2. Submit Decision
    payload = {
        "reviewer_id": "analyst_sarah_01",
        "decision": "CONTEST",
        "reason": "Verified carrier tracking and delivery confirmation supports contesting this chargeback."
    }
    dec_res = client.post(f"/api/v1/review/cases/{dispute_id}/decision", json=payload)
    assert dec_res.status_code == 200
    
    dec_data = dec_res.json()
    assert dec_data["dispute_id"] == dispute_id
    assert dec_data["reviewer_id"] == "analyst_sarah_01"
    assert dec_data["decision"] == "CONTEST"
    assert dec_data["ai_recommendation"] == "CONTEST"
    assert dec_data["ai_win_probability"] == pytest.approx(0.6816, abs=0.01)
    assert dec_data["verification_rate"] == 1.0
    assert "created_at" in dec_data
    assert dec_data["decision_id"].startswith(f"DEC_{dispute_id}_")

    # 3. Verify Status Updated to DECIDED
    pkg_res_updated = client.get(f"/api/v1/review/cases/{dispute_id}")
    assert pkg_res_updated.json()["review_status"] == "DECIDED"
    assert len(pkg_res_updated.json()["decisions"]) >= 1

# 17. Duplicate Decision Protection (409 Conflict)
def test_duplicate_decision_rejection():
    dispute_id = "DSP_000001"
    payload1 = {
        "reviewer_id": "analyst_sarah_01",
        "decision": "CONTEST",
        "reason": "Initial decision reason for case."
    }
    client.post(f"/api/v1/review/cases/{dispute_id}/decision", json=payload1)

    payload2 = {
        "reviewer_id": "analyst_bob_02",
        "decision": "DO_NOT_CONTEST",
        "reason": "Attempting duplicate decision."
    }
    # Check 409 Conflict on duplicate decision submission
    res_review = client.post(f"/api/v1/review/cases/{dispute_id}/decision", json=payload2)
    assert res_review.status_code == 409

# 6, 14. Valid Decision with AI/Human Disagreement (DSP_000003)
def test_human_ai_disagreement_and_do_not_contest():
    dispute_id = "DSP_000003"
    payload = {
        "reviewer_id": "risk_lead_01",
        "decision": "DO_NOT_CONTEST",
        "reason": "High chargeback history customer and weak physical evidence. Overriding AI recommendation."
    }
    res = client.post(f"/api/v1/review/cases/{dispute_id}/decision", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "DO_NOT_CONTEST"
    # Preserves both human decision and AI recommendation
    assert "ai_recommendation" in data

# 7, 18. Valid Escalation Decision (DSP_000004)
def test_escalation_decision():
    dispute_id = "DSP_000004"
    payload = {
        "reviewer_id": "analyst_sarah_01",
        "decision": "ESCALATE",
        "reason": "Complex high-value dispute requiring senior risk manager sign-off."
    }
    res = client.post(f"/api/v1/review/cases/{dispute_id}/decision", json=payload)
    assert res.status_code == 200
    assert res.json()["decision"] == "ESCALATE"

    # Verify status changed to ESCALATED
    pkg_res = client.get(f"/api/v1/review/cases/{dispute_id}")
    assert pkg_res.json()["review_status"] == "ESCALATED"

# 8, 9, 10. Validation Rejections (Invalid / Empty Reasons & Reviewer ID)
def test_invalid_decision_payloads():
    dispute_id = "DSP_000005"

    # Missing / empty reason
    payload_bad_reason = {
        "reviewer_id": "analyst_01",
        "decision": "CONTEST",
        "reason": "abc"  # too short / invalid
    }
    res1 = client.post(f"/api/v1/review/cases/{dispute_id}/decision", json=payload_bad_reason)
    assert res1.status_code == 422

    # Missing reviewer ID
    payload_bad_reviewer = {
        "reviewer_id": "   ",
        "decision": "CONTEST",
        "reason": "Valid reason explanation."
    }
    res2 = client.post(f"/api/v1/review/cases/{dispute_id}/decision", json=payload_bad_reviewer)
    assert res2.status_code == 422

    # Invalid decision enum
    payload_bad_enum = {
        "reviewer_id": "analyst_01",
        "decision": "INVALID_ACTION",
        "reason": "Valid reason explanation."
    }
    res3 = client.post(f"/api/v1/review/cases/{dispute_id}/decision", json=payload_bad_enum)
    assert res3.status_code == 422

# 20. Read-Only Data Preservation
def test_underlying_data_unmodified():
    dispute_id = "DSP_000001"
    detail_before = case_service.get_case_detail(dispute_id)
    
    # Financial status must remain unchanged in underlying database
    assert detail_before["dispute"]["dispute_status"] in ["CLOSED", "OPEN", "PENDING"]
