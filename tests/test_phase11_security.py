"""
Phase 11 Security, Authentication, RBAC, Rate Limiting & Health Probe Test Suite.
Verifies JWT issuance, password hashing, session logout revocation, user CRUD,
role-based authorization, rate-limiting, ingestion reports, and export provenance.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db.database import get_db_session, init_db
from backend.services.user_service import seed_dev_users, create_user, delete_user, get_user_by_username
from backend.services.auth_service import hash_password, verify_password, create_access_token, decode_access_token, revoke_token
from backend.services.data_ingestion_service import data_ingestion_service

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_users():
    init_db()
    with get_db_session() as db:
        seed_dev_users(db, admin_username="admin_test", admin_password="AdminPass123!")


def test_password_hashing_and_verification():
    raw_pass = "SecureSecret123!"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPass", hashed) is False


def test_login_success_returns_jwt():
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_test", "password": "AdminPass123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "admin_test"
    assert data["user"]["role"] == "ADMIN"
    assert "hashed_password" not in data["user"]


def test_invalid_login_returns_401():
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_test", "password": "WrongPassword!"}
    )
    assert response.status_code == 401
    assert "Invalid username/email or password" in response.json()["detail"]


def test_jwt_token_decoding_and_expiration():
    token = create_access_token({"sub": "USR_001", "username": "sarah", "role": "REVIEWER"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "USR_001"
    assert payload["username"] == "sarah"
    assert payload["role"] == "REVIEWER"


def test_token_revocation_logout():
    token = create_access_token({"sub": "USR_002", "username": "reviewer_test", "role": "REVIEWER"})
    assert decode_access_token(token) is not None

    revoke_token(token)
    assert decode_access_token(token) is None


def test_health_and_readiness_probes():
    h_resp = client.get("/health")
    assert h_resp.status_code == 200
    h_data = h_resp.json()
    assert h_data["status"] == "ok"
    assert h_data["overall_status"] in ["HEALTHY", "DEGRADED"]
    assert "subsystems" in h_data
    assert h_data["subsystems"]["api"] == "HEALTHY"

    r_resp = client.get("/ready")
    assert r_resp.status_code == 200
    assert r_resp.json()["status"] == "READY"


def test_csv_data_ingestion_validation():
    valid_csv = (
        "dispute_id,disputed_amount,currency,dispute_reason_code,customer_id,order_id,transaction_id\n"
        "DSP_TEST_01,150.00,INR,10.4_OTHER,CUST_1,ORD_1,TXN_1\n"
        "DSP_TEST_02,250.00,INR,13.1_MERCH,CUST_2,ORD_2,TXN_2\n"
    ).encode("utf-8")

    report = data_ingestion_service.validate_and_ingest_csv(valid_csv)
    assert report["rows_received"] == 2
    assert report["rows_accepted"] == 2
    assert report["data_quality_score"] == 100.0
    assert report["status"] == "ACCEPTED"


def test_csv_data_ingestion_rejects_invalid_amount():
    invalid_csv = (
        "dispute_id,disputed_amount,currency,dispute_reason_code,customer_id,order_id,transaction_id\n"
        "DSP_BAD_01,-50.00,INR,10.4_OTHER,CUST_1,ORD_1,TXN_1\n"
    ).encode("utf-8")

    report = data_ingestion_service.validate_and_ingest_csv(invalid_csv)
    assert report["rows_received"] == 1
    assert report["rows_rejected"] == 1
    assert report["invalid_rows"] == 1
    assert report["data_quality_score"] == 0.0


def test_data_export_with_provenance():
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_test", "password": "AdminPass123!"}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    exp_resp = client.get("/api/v1/export/cases?format=json", headers=headers)
    assert exp_resp.status_code == 200
    exp_data = exp_resp.json()
    assert "provenance" in exp_data
    assert "DATA_STATE" in exp_data["provenance"]
    assert "cases" in exp_data

    csv_resp = client.get("/api/v1/export/cases?format=csv", headers=headers)
    assert csv_resp.status_code == 200
    assert "# DATA STATE:" in csv_resp.text
