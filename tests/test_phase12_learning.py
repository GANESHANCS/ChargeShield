"""
Phase 12 Continuous Learning, Outcome Feedback, Threshold Governance & Security Test Suite.
Verifies ground-truth outcome ingestion, RBAC access control, simulation isolation, immutability,
calibration, multi-threshold optimization, Admin threshold approval audit, and pipeline eligibility.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db.database import get_db_session, init_db
from backend.db.models import ModelOutcomeModel, ThresholdAuditModel, ModelVersionModel
from backend.services.user_service import seed_dev_users, create_user

from backend.services.user_service import seed_dev_users, create_user, get_user_by_username

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_phase12_environment():
    init_db()
    with get_db_session() as db:
        seed_dev_users(db, admin_username="admin_p12", admin_password="AdminPass123!")
        
        if not get_user_by_username(db, "reviewer_p12"):
            create_user(db, username="reviewer_p12", email="reviewer_p12@chargeshield.io", password="ReviewerPass123!", role="REVIEWER")
        if not get_user_by_username(db, "auditor_p12"):
            create_user(db, username="auditor_p12", email="auditor_p12@chargeshield.io", password="AuditorPass123!", role="AUDITOR")
        if not get_user_by_username(db, "analyst_p12"):
            create_user(db, username="analyst_p12", email="analyst_p12@chargeshield.io", password="AnalystPass123!", role="ANALYST")

        # Clean outcomes and audits for test isolation
        db.query(ModelOutcomeModel).delete()
        db.query(ThresholdAuditModel).delete()
        prod_m = db.query(ModelVersionModel).filter(ModelVersionModel.lifecycle_status == "PRODUCTION").first()
        if prod_m:
            prod_m.threshold = 0.29
        db.commit()



def get_token(username: str, password: str = "AdminPass123!") -> str:
    res = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


# 1. Outcome Ingestion Authorization Tests
def test_authorized_outcome_recording_reviewer_and_admin():
    rev_token = get_token("reviewer_p12", "ReviewerPass123!")
    headers = {"Authorization": f"Bearer {rev_token}"}

    payload = {
        "dispute_id": "DSP_000093",
        "actual_outcome": "WON",
        "resolution_timestamp": "2026-08-24T12:00:00Z",
        "financial_recovery_amount": 1500.0,
        "justification": "Verified carrier delivery receipt and signed POD."
    }

    res = client.post("/api/v1/model/outcomes", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "RECORDED"
    assert data["dispute_id"] == "DSP_000093"
    assert data["actual_outcome"] == "WON"
    assert data["financial_status"] == "EXPLICIT_RECOVERY"
    assert data["data_state"] == "PRODUCTION"


def test_unauthorized_outcome_recording_auditor_analyst_unauthenticated():
    aud_token = get_token("auditor_p12", "AuditorPass123!")
    headers = {"Authorization": f"Bearer {aud_token}"}

    payload = {
        "dispute_id": "DSP_000080",
        "actual_outcome": "LOST",
        "justification": "Attempting auditor outcome creation."
    }

    # Auditor denied
    res_aud = client.post("/api/v1/model/outcomes", json=payload, headers=headers)
    assert res_aud.status_code == 403

    # Analyst denied
    an_token = get_token("analyst_p12", "AnalystPass123!")
    res_an = client.post("/api/v1/model/outcomes", json=payload, headers={"Authorization": f"Bearer {an_token}"})
    assert res_an.status_code == 403

    # Unauthenticated in production environment mode denied (401)
    from backend.core.config import settings
    orig_env = settings.ENVIRONMENT
    try:
        settings.ENVIRONMENT = "production"
        res_unauth = client.post("/api/v1/model/outcomes", json=payload)
        assert res_unauth.status_code == 401
    finally:
        settings.ENVIRONMENT = orig_env



# 2. Simulation Outcome Rejection Test
def test_simulation_outcome_rejection():
    adm_token = get_token("admin_p12")
    headers = {"Authorization": f"Bearer {adm_token}"}

    payload = {
        "dispute_id": "DSP_SIM_000001",
        "actual_outcome": "WON",
        "justification": "Attempting simulation case outcome labeling."
    }

    res = client.post("/api/v1/model/outcomes", json=payload, headers=headers)
    assert res.status_code == 400
    assert "SIMULATION cases cannot receive production outcome labels" in res.json()["detail"]


# 3. Outcome Immutability and Conflict Protection
def test_duplicate_and_conflicting_outcome_rejection():
    adm_token = get_token("admin_p12")
    headers = {"Authorization": f"Bearer {adm_token}"}

    payload1 = {
        "dispute_id": "DSP_000373",
        "actual_outcome": "WON",
        "justification": "First valid outcome label entry."
    }
    res1 = client.post("/api/v1/model/outcomes", json=payload1, headers=headers)
    assert res1.status_code == 200

    # Second entry on same dispute rejected
    payload2 = {
        "dispute_id": "DSP_000373",
        "actual_outcome": "LOST",
        "justification": "Conflicting duplicate outcome entry attempt."
    }
    res2 = client.post("/api/v1/model/outcomes", json=payload2, headers=headers)
    assert res2.status_code == 409
    assert "immutable" in res2.json()["detail"].lower()


# 4. Missing Financial Recovery Handling
def test_missing_financial_recovery_returns_insufficient_data_status():
    adm_token = get_token("admin_p12")
    headers = {"Authorization": f"Bearer {adm_token}"}

    payload = {
        "dispute_id": "DSP_000260",
        "actual_outcome": "EXPIRED",
        "financial_recovery_amount": None,
        "justification": "Case expired without explicit financial recovery statement."
    }

    res = client.post("/api/v1/model/outcomes", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["financial_recovery_amount"] is None
    assert data["financial_status"] == "INSUFFICIENT_DATA"



# 5. Calibration & Threshold API Fallbacks
def test_calibration_and_threshold_insufficient_data_fallbacks():
    token = get_token("admin_p12")
    headers = {"Authorization": f"Bearer {token}"}

    # Calibration endpoint
    res_cal = client.get("/api/v1/model/calibration", headers=headers)
    assert res_cal.status_code == 200
    cal_data = res_cal.json()
    assert cal_data["calibration_status"] == "INSUFFICIENT_DATA"
    assert cal_data["data_provenance"] == "INSUFFICIENT_DATA"

    # Thresholds endpoint
    res_thresh = client.get("/api/v1/model/thresholds", headers=headers)
    assert res_thresh.status_code == 200
    thresh_data = res_thresh.json()
    assert thresh_data["recommendation_status"] == "AWAITING_BASELINE"
    assert thresh_data["current_threshold"] == 0.29
    assert thresh_data["recommended_threshold"] is None


# 6. Admin Threshold Approval & Immutable Audit
def test_admin_threshold_approval_governance_and_audit():
    adm_token = get_token("admin_p12")
    adm_headers = {"Authorization": f"Bearer {adm_token}"}

    approval_payload = {
        "proposed_threshold": 0.35,
        "reason": "Analytical review demonstrates higher net financial recovery at 0.35 threshold.",
        "evidence_metrics": {"eval_f1": 0.82, "expected_recovery": 145000.0}
    }

    # Non-Admin (Reviewer) denied
    rev_token = get_token("reviewer_p12", "ReviewerPass123!")
    res_rev = client.post("/api/v1/model/thresholds/approve", json=approval_payload, headers={"Authorization": f"Bearer {rev_token}"})
    assert res_rev.status_code == 403

    # Admin approved
    res_adm = client.post("/api/v1/model/thresholds/approve", json=approval_payload, headers=adm_headers)
    assert res_adm.status_code == 200
    adm_data = res_adm.json()
    assert adm_data["status"] == "APPROVED"
    assert adm_data["approved_threshold"] == 0.35
    assert adm_data["admin_id"] == "admin_p12"
    assert "audit_id" in adm_data

    # Verify audit record created in DB
    with get_db_session() as db:
        audit = db.query(ThresholdAuditModel).filter(ThresholdAuditModel.audit_id == adm_data["audit_id"]).first()
        assert audit is not None
        assert audit.approved_threshold == 0.35
        assert audit.admin_id == "admin_p12"


# 7. Model Version Registry & Learning Eligibility
def test_model_registry_and_learning_readiness():
    token = get_token("admin_p12")
    headers = {"Authorization": f"Bearer {token}"}

    # Model Registry
    res_reg = client.get("/api/v1/model/registry", headers=headers)
    assert res_reg.status_code == 200
    reg_data = res_reg.json()
    assert "versions" in reg_data
    assert reg_data["active_production_model"]["lifecycle_status"] == "PRODUCTION"

    # Learning Readiness
    res_learn = client.get("/api/v1/model/learning", headers=headers)
    assert res_learn.status_code == 200
    learn_data = res_learn.json()
    assert "pipeline_readiness" in learn_data
    assert learn_data["pipeline_readiness"]["governance"]["simulation_exclusion"] is True
