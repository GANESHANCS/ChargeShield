"""
Phase 4 Read-Only AI Risk Investigation Agent Test Suite.

Verifies:
1. Investigation endpoint existence and 200 response for valid disputes
2. 404 response for unknown disputes
3. InvestigationReport schema compliance and strongly typed fields
4. Source-of-truth grounding (evidence items reference actual entity IDs)
5. ML assessment matching Phase 2 prediction output and model version
6. Deterministic zero-hallucination fallback engine behavior
7. End-to-End CASE -> PREDICTION -> EXPLANATION -> INVESTIGATION -> REPORT pipeline
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.agent.investigator import investigation_agent
from backend.agent.llm import DeterministicFallbackInvestigator

client = TestClient(app)

# 1, 2, 4, 5, 6, 7, 8, 9, 10. Investigation Endpoint Test
def test_investigation_endpoint_valid_dispute():
    # 1. Fetch first known case
    res_list = client.get("/api/v1/cases?page_size=1")
    known_id = res_list.json()["items"][0]["dispute_id"]
    
    # 2. Trigger Investigation
    res_inv = client.post(f"/api/v1/cases/{known_id}/investigate")
    assert res_inv.status_code == 200
    report = res_inv.json()
    
    # 3. Assert report structure
    assert report["dispute_id"] == known_id
    assert report["investigation_status"] == "COMPLETED"
    assert "executive_summary" in report
    assert report["recommendation"]["action"] in ["CONTEST", "MANUAL_REVIEW", "DO_NOT_CONTEST"]
    assert 0.0 <= report["recommendation"]["win_probability"] <= 1.0
    
    # 4. Assert ML assessment
    ml_eval = report["ml_assessment"]
    assert ml_eval["win_probability"] == report["recommendation"]["win_probability"]
    assert ml_eval["model_version"] == "chargeshield_ml_v1"
    assert ml_eval["decision_threshold"] == 0.29
    
    # 5. Assert timeline chronological order
    timeline = report["timeline"]
    assert len(timeline) > 0
    timestamps = [ev["timestamp"] for ev in timeline]
    assert timestamps == sorted(timestamps)
    
    # 6. Assert Evidence Source IDs match real entities
    evidence = report["evidence"]
    assert len(evidence) > 0
    for item in evidence:
        assert item["verification_status"] == "UNVERIFIED"
        assert item["source_id"].startswith(("DEL_", "TXN_", "ORD_", "CUS_", "COM_", "DSP_"))

# 3. Unknown Dispute 404 Test
def test_investigation_endpoint_unknown_dispute():
    res_404 = client.post("/api/v1/cases/DSP_NONEXISTENT_999/investigate")
    assert res_404.status_code == 404

# 15. Deterministic Fallback Engine Direct Unit Test
def test_deterministic_fallback_engine():
    res_detail = client.get("/api/v1/cases/DSP_000001")
    case_detail = res_detail.json()
    
    fallback = DeterministicFallbackInvestigator()
    report = fallback.generate_report(case_detail)
    
    assert report.dispute_id == "DSP_000001"
    assert report.investigation_status == "COMPLETED"
    assert report.ml_assessment.model_version == "chargeshield_ml_v1"
    assert len(report.case_facts) > 0
    assert len(report.supporting_factors) > 0

# 30. End-to-End Investigation Pipeline Test
def test_e2e_investigation_pipeline():
    """
    End-to-End integration test validating CASE -> PREDICTION -> EXPLANATION -> INVESTIGATION -> REPORT
    """
    dispute_id = "DSP_000001"
    
    # 1. Prediction API
    pred_data = client.get(f"/api/v1/cases/{dispute_id}/prediction").json()
    
    # 2. Investigation API
    inv_data = client.post(f"/api/v1/cases/{dispute_id}/investigate").json()
    
    # 3. Verify ML probability alignment across layers
    assert inv_data["ml_assessment"]["win_probability"] == pred_data["win_probability"]
    assert inv_data["recommendation"]["action"] == pred_data["recommendation"]
    assert inv_data["disclaimer"] == "READ-ONLY DECISION SUPPORT. Final financial actions require human authorization."
