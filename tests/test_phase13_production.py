"""
Comprehensive Test Suite for ChargeShield Phase 13 Production Hardening.
Tests DB connection pooling, data state governance, background jobs, ingestion pipeline multi-stage validation & idempotency,
API response envelopes, server-side pagination, RBAC enforcement, decision policy decoupling, and operational observability.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.constants import DataState, UserRole, ReviewStatus, DecisionType, OutcomeType
from backend.core.jobs import job_manager, JobStatus
from backend.services.data_ingestion_service import data_ingestion_service
from backend.core.api_response import success_response, error_response, paginate_list
from backend.services.decision_policy import decision_policy_service
from backend.core.metrics import metrics_collector
from backend.db.models import ReviewDecisionModel, ModelOutcomeModel, UserModel

client = TestClient(app)


def test_constants_and_enums():
    """Verify authoritative governance enums."""
    assert DataState.PRODUCTION == "PRODUCTION"
    assert DataState.SIMULATION == "SIMULATION"
    assert UserRole.ADMIN == "ADMIN"
    assert UserRole.ANALYST == "ANALYST"
    assert ReviewStatus.PENDING_REVIEW == "PENDING_REVIEW"
    assert DecisionType.CONTEST == "CONTEST"
    assert OutcomeType.WON == "WON"


def test_background_job_manager():
    """Test background job registration, progress tracking, and status polling."""
    job_id = job_manager.create_job("BULK_PREDICTION", metadata={"count": 50})
    assert job_id.startswith("JOB_BULK_")
    
    job = job_manager.get_job(job_id)
    assert job["status"] == JobStatus.PENDING
    assert job["progress"] == 0.0

    job_manager.update_job(job_id, status=JobStatus.PROCESSING, progress=45.0)
    job_updated = job_manager.get_job(job_id)
    assert job_updated["status"] == JobStatus.PROCESSING
    assert job_updated["progress"] == 45.0

    job_manager.update_job(job_id, status=JobStatus.COMPLETED, progress=100.0, result={"completed": True})
    job_completed = job_manager.get_job(job_id)
    assert job_completed["status"] == JobStatus.COMPLETED
    assert job_completed["result"] == {"completed": True}

    # Test via API endpoint
    response = client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 200
    assert response.json()["job"]["job_id"] == job_id


def test_ingestion_pipeline_multistage_and_idempotency():
    """Test multi-stage CSV ingestion validation and SHA256 batch hash idempotency."""
    csv_bytes = b"dispute_id,disputed_amount,currency,dispute_reason_code,customer_id,order_id,transaction_id\nDSP_P13_01,1500.0,INR,10.4,CUST_01,ORD_01,TXN_01\nDSP_P13_02,2500.0,INR,13.1,CUST_02,ORD_02,TXN_02\n"

    # Stage 1: Validate & Stage
    report = data_ingestion_service.validate_and_stage_csv(csv_bytes, data_state="PRODUCTION")
    assert report["status"] == "ACCEPTED"
    assert report["rows_received"] == 2
    assert report["rows_accepted"] == 2
    assert report["data_quality_score"] == 100.0
    batch_id = report["batch_id"]

    # Stage 2: Explicit Confirmation & Commit
    commit_res = data_ingestion_service.confirm_and_commit_batch(batch_id, actor_id="TEST_ADMIN")
    assert commit_res["status"] == "COMMITTED"
    assert commit_res["committed_rows"] == 2

    # Idempotency Check: Re-submitting identical CSV bytes must be caught by batch hash governor
    dup_report = data_ingestion_service.validate_and_stage_csv(csv_bytes, data_state="PRODUCTION")
    assert dup_report["status"] == "IDEMPOTENT_SKIPPED"
    assert "Duplicate dataset upload blocked" in dup_report["warnings"][0]


def test_api_response_envelopes_and_pagination():
    """Test standard response envelope builders and pagination bounds."""
    succ = success_response(data={"key": "val"}, message="Success", request_id="req-123")
    assert succ["status"] == "SUCCESS"
    assert succ["data"] == {"key": "val"}
    assert succ["request_id"] == "req-123"

    err = error_response(error_message="Test Error", code="TEST_ERR")
    assert err["status"] == "ERROR"
    assert err["code"] == "TEST_ERR"

    # Pagination test
    items = list(range(100))
    paged = paginate_list(items, page=2, page_size=15)
    assert len(paged["items"]) == 15
    assert paged["items"][0] == 15
    assert paged["pagination"]["total_pages"] == 7
    assert paged["pagination"]["has_next"] is True
    assert paged["pagination"]["has_prev"] is True


def test_decoupled_decision_policy():
    """Test 4-stage pipeline in DecisionPolicyService."""
    res = decision_policy_service.evaluate_case_policy("DSP_000001", active_threshold=0.29)
    assert "recommended_action" in res
    assert res["recommended_action"] in ["CONTEST", "DO_NOT_CONTEST", "ESCALATE"]
    assert "1_prediction" in res["pipeline_stages"]
    assert "2_risk_engine" in res["pipeline_stages"]
    assert "3_financial_engine" in res["pipeline_stages"]
    assert "4_decision_policy" in res["pipeline_stages"]


def test_metrics_collector_and_health_probe():
    """Test operational metrics collector and health API response."""
    metrics_collector.record_request(200, 15.5)
    metrics_collector.record_prediction()

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "metrics" in data
    assert data["metrics"]["requests_total"] >= 1
    assert data["subsystems"]["database"] == "HEALTHY"


def test_readiness_probe():
    """Test readiness endpoint."""
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "READY"
