"""
Integration and Unit Test Suite for ChargeShield Phase 10:
Case Operations, SLA Prioritization, Evidence Confidence, Outcome Intelligence,
and Workflow APIs.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.case_workflow_service import case_workflow_service
from backend.services.sla_service import sla_service
from backend.services.evidence_confidence_service import evidence_confidence_service
from backend.services.outcome_service import outcome_service
from backend.services.outcome_feedback_service import outcome_feedback_service

client = TestClient(app)

def test_case_assignment_service():
    """Test assigning reviewer to dispute."""
    dispute_id = "DSP_P10_001"
    res = case_workflow_service.assign_case(dispute_id=dispute_id, reviewer_id="RVR_101", actor_id="MGR_001")
    
    assert res["dispute_id"] == dispute_id
    assert res["assigned_reviewer_id"] == "RVR_101"
    assert res["status"] == "IN_REVIEW"
    assert res["activity"]["event_type"] == "CASE_ASSIGNMENT"

def test_case_status_transitions():
    """Test valid case workflow state transitions."""
    dispute_id = "DSP_P10_002"
    
    # Valid transition to IN_REVIEW
    st1 = case_workflow_service.update_status(dispute_id, "IN_REVIEW")
    assert st1["status"] == "IN_REVIEW"
    
    # Valid transition to ESCALATED
    st2 = case_workflow_service.update_status(dispute_id, "ESCALATED")
    assert st2["status"] == "ESCALATED"
    
    # Valid transition to RESOLVED
    st3 = case_workflow_service.update_status(dispute_id, "RESOLVED")
    assert st3["status"] == "RESOLVED"

def test_invalid_status_transition():
    """Test handling of invalid status values."""
    dispute_id = "DSP_P10_003"
    with pytest.raises(ValueError):
        case_workflow_service.update_status(dispute_id, "INVALID_STATE_XYZ")

from backend.services.case_service import CaseService

def test_review_notes_and_activity_trace():
    """Test adding notes and building action lineage activity trace."""
    dispute_id = "DSP_P10_004"
    
    n1 = case_workflow_service.add_note(dispute_id, "RVR_001", "Verified carrier delivery receipt with customer signature.")
    assert n1["note"]["author_id"] == "RVR_001"
    assert "carrier delivery receipt" in n1["note"]["note_text"].lower()
    
    notes = case_workflow_service.get_notes(dispute_id)
    assert len(notes) >= 1
    
    activity = case_workflow_service.get_activity_trace(dispute_id)
    assert len(activity) >= 1
    assert any(a["event_type"] == "NOTE_ADDED" for a in activity)

def test_sla_service_calculations():
    """Test SLA status, remaining time, priority tier, and transparent priority string."""
    # Test ON_TRACK case
    sla1 = sla_service.calculate_sla(
        response_deadline_iso="2030-01-01T00:00:00Z",
        disputed_amount=12000.0,
        win_probability=0.8,
        risk_score=0.3,
        evidence_confidence=0.9
    )
    assert sla1["sla_status"] in ["ON_TRACK", "DUE_SOON"]
    assert "exposure" in sla1["priority_explanation"]
    
    # Test OVERDUE case
    sla2 = sla_service.calculate_sla(
        response_deadline_iso="2020-01-01T00:00:00Z",
        disputed_amount=48200.0,
        win_probability=0.9,
        risk_score=0.8,
        evidence_confidence=0.85
    )
    assert sla2["sla_status"] == "OVERDUE"
    assert sla2["is_overdue"] is True
    assert sla2["review_priority"] == "CRITICAL"
    assert "OVERDUE" in sla2["priority_explanation"]

def test_evidence_confidence_service():
    """Test evidence confidence scoring across complete vs missing evidence."""
    mock_case_detail = {
        "delivery": {
            "pod_signature_present": True,
            "pod_match_status": "EXACT_MATCH",
            "delivery_status": "DELIVERED"
        },
        "transaction": {
            "cvv_match": "MATCH",
            "avs_match": "MATCH"
        },
        "customer": {
            "tenure_days": 200,
            "successful_order_count": 8,
            "historical_chargeback_count": 0
        },
        "order": {
            "fulfillment_status": "FULFILLED"
        }
    }
    
    conf = evidence_confidence_service.evaluate_evidence(mock_case_detail)
    assert conf["evidence_confidence_score"] >= 0.85
    assert conf["evidence_status"] == "VERIFIED"
    assert len(conf["missing_evidence"]) == 0

def test_outcome_intelligence_service():
    """Test outcome metrics calculation."""
    metrics = outcome_service.get_outcome_metrics()
    assert "total_reviewed" in metrics
    assert "contest_count" in metrics
    assert "actual_outcome_status" in metrics
    assert "INSUFFICIENT_DATA" in metrics["actual_outcome_status"]

def test_outcome_feedback_service():
    """Test outcome feedback returns non-synthetic status."""
    fb = outcome_feedback_service.evaluate_model_feedback()
    assert fb["status"] == "AWAITING_ADJUDICATION_DATA"
    assert fb["precision"] is None

def test_phase10_api_endpoints():
    """Test Phase 10 REST API endpoints."""
    valid_id = CaseService().list_cases()['items'][0]['dispute_id']

    # Test assignment endpoint
    resp = client.patch(f"/api/v1/cases/{valid_id}/assignment", json={"reviewer_id": "RVR_888", "actor_id": "ADM_001"})
    assert resp.status_code == 200
    assert resp.json()["assigned_reviewer_id"] == "RVR_888"

    # Test status endpoint
    resp_st = client.patch(f"/api/v1/cases/{valid_id}/status", json={"status": "ESCALATED", "actor_id": "RVR_888", "reason": "Requires manager approval"})
    assert resp_st.status_code == 200
    assert resp_st.json()["status"] == "ESCALATED"

    # Test note creation endpoint
    resp_n = client.post(f"/api/v1/cases/{valid_id}/notes", json={"author_id": "RVR_888", "note_text": "Customer signature matches on carrier receipt."})
    assert resp_n.status_code == 200

    # Test activity endpoint
    resp_act = client.get(f"/api/v1/cases/{valid_id}/activity")
    assert resp_act.status_code == 200
    assert isinstance(resp_act.json(), list)

    # Test SLA endpoint
    resp_sla = client.get(f"/api/v1/cases/{valid_id}/sla")
    assert resp_sla.status_code == 200
    assert "sla_status" in resp_sla.json()

    # Test Evidence Confidence endpoint
    resp_ev = client.get(f"/api/v1/cases/{valid_id}/evidence-confidence")
    assert resp_ev.status_code == 200
    assert "evidence_confidence_score" in resp_ev.json()

    # Test Outcomes Overview endpoint
    resp_out = client.get("/api/v1/outcomes/overview")
    assert resp_out.status_code == 200
    assert "actual_outcome_status" in resp_out.json()

    # Test Outcomes Feedback endpoint
    resp_fb = client.get("/api/v1/outcomes/feedback")
    assert resp_fb.status_code == 200
    assert resp_fb.json()["status"] == "AWAITING_ADJUDICATION_DATA"
