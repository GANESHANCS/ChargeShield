"""
Comprehensive Test Suite for ChargeShield Phase 14 Milestone 3 - Evidence Document Management.
Validates file upload, SHA-256 integrity, RBAC, path traversal protection, duplicate detection,
atomic rollback cleanup, data-state isolation, and API response envelope contracts.
"""

import io
import os
import shutil
import pytest
import hashlib
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.core.config import settings
from backend.db.database import Base, get_db
from backend.db.models import (
    CustomerModel, OrderModel, TransactionModel, DisputeModel,
    EvidenceDocumentModel, UserModel
)
from backend.services.evidence_storage_service import evidence_storage_service
from backend.services.auth_service import create_access_token, hash_password

# Use isolated SQLite test database
TEST_DB_URL = "sqlite:///./test_phase14_evidence.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

TEST_STORAGE_DIR = "storage/test_evidence"


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_environment():
    """Sets up test database tables, storage directory, and seed users/disputes."""
    Base.metadata.create_all(bind=engine)
    
    # Configure test storage dir
    evidence_storage_service.base_storage_path = TEST_STORAGE_DIR
    os.makedirs(TEST_STORAGE_DIR, exist_ok=True)

    db = TestingSessionLocal()

    # Create Seed Users for RBAC testing
    users = [
        UserModel(user_id="usr_admin", email="admin@chargeshield.com", username="admin_user", full_name="Admin User", hashed_password=hash_password("pass"), role="ADMIN", is_active=1.0, created_at="2026-08-27T00:00:00Z"),
        UserModel(user_id="usr_reviewer", email="reviewer@chargeshield.com", username="reviewer_user", full_name="Reviewer User", hashed_password=hash_password("pass"), role="REVIEWER", is_active=1.0, created_at="2026-08-27T00:00:00Z"),
        UserModel(user_id="usr_analyst", email="analyst@chargeshield.com", username="analyst_user", full_name="Analyst User", hashed_password=hash_password("pass"), role="ANALYST", is_active=1.0, created_at="2026-08-27T00:00:00Z"),
        UserModel(user_id="usr_auditor", email="auditor@chargeshield.com", username="auditor_user", full_name="Auditor User", hashed_password=hash_password("pass"), role="AUDITOR", is_active=1.0, created_at="2026-08-27T00:00:00Z"),
    ]
    for u in users:
        if not db.query(UserModel).filter_by(username=u.username).first():
            db.add(u)

    # Seed Relational Dispute Hierarchy
    cust = CustomerModel(customer_id="CUST_EV_01", tenure_days=100.0, previous_chargeback_count=0.0, successful_order_count=5.0, customer_segment="VIP", data_state="PRODUCTION", created_at="2026-08-27T00:00:00Z", updated_at="2026-08-27T00:00:00Z")
    ord_m = OrderModel(order_id="ORD_EV_01", customer_id="CUST_EV_01", order_amount=150.0, order_timestamp="2026-08-27T00:00:00Z", product_category="ELECTRONICS", fulfillment_status="DELIVERED", data_state="PRODUCTION", created_at="2026-08-27T00:00:00Z", updated_at="2026-08-27T00:00:00Z")
    tx_m = TransactionModel(transaction_id="TX_EV_01", order_id="ORD_EV_01", amount=150.0, payment_method="CREDIT_CARD", auth_risk_score=15.0, data_state="PRODUCTION", created_at="2026-08-27T00:00:00Z", updated_at="2026-08-27T00:00:00Z")
    disp_prod = DisputeModel(dispute_id="DSP_EV_PROD_01", transaction_id="TX_EV_01", order_id="ORD_EV_01", customer_id="CUST_EV_01", disputed_amount=150.0, currency="INR", dispute_reason_code="FRAUDULENT", dispute_status="PENDING_REVIEW", data_state="PRODUCTION", created_at="2026-08-27T00:00:00Z", updated_at="2026-08-27T00:00:00Z")

    disp_sim = DisputeModel(dispute_id="DSP_EV_SIM_01", transaction_id="TX_EV_01", order_id="ORD_EV_01", customer_id="CUST_EV_01", disputed_amount=200.0, currency="INR", dispute_reason_code="PRODUCT_NOT_RECEIVED", dispute_status="PENDING_REVIEW", data_state="SIMULATION", created_at="2026-08-27T00:00:00Z", updated_at="2026-08-27T00:00:00Z")

    db.add_all([cust, ord_m, tx_m, disp_prod, disp_sim])
    db.commit()
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)

    # Cleanup after tests
    Base.metadata.drop_all(bind=engine)
    if os.path.exists(TEST_STORAGE_DIR):
        shutil.rmtree(TEST_STORAGE_DIR, ignore_errors=True)
    if os.path.exists("test_phase14_evidence.db"):
        try:
            os.remove("test_phase14_evidence.db")
        except Exception:
            pass


def get_token(username: str) -> str:
    user_map = {
        "admin_user": ("usr_admin", "admin_user", "ADMIN"),
        "reviewer_user": ("usr_reviewer", "reviewer_user", "REVIEWER"),
        "analyst_user": ("usr_analyst", "analyst_user", "ANALYST"),
        "auditor_user": ("usr_auditor", "auditor_user", "AUDITOR"),
    }
    uid, uname, role = user_map[username]
    return create_access_token(data={"sub": uid, "username": uname, "role": role})


# -----------------------------------------------------------------------------
# TEST CASES
# -----------------------------------------------------------------------------

def test_upload_valid_pdf():
    token = get_token("reviewer_user")
    pdf_content = b"%PDF-1.4 Test Evidence Document Content"
    files = {"file": ("proof_delivery.pdf", io.BytesIO(pdf_content), "application/pdf")}
    
    res = client.post(
        "/api/v1/cases/DSP_EV_PROD_01/evidence-upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["data"]["original_filename"] == "proof_delivery.pdf"
    assert data["data"]["content_type"] == "application/pdf"
    assert data["data"]["data_state"] == "PRODUCTION"


def test_upload_valid_image_png():
    token = get_token("admin_user")
    png_content = b"\x89PNG\r\n\x1a\nFake PNG Bytes"
    files = {"file": ("receipt.png", io.BytesIO(png_content), "image/png")}
    
    res = client.post(
        "/api/v1/cases/DSP_EV_PROD_01/evidence-upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert res.json()["data"]["original_filename"] == "receipt.png"


def test_upload_valid_image_jpg():
    token = get_token("reviewer_user")
    jpg_content = b"\xff\xd8\xffFake JPG Bytes"
    files = {"file": ("id_proof.jpg", io.BytesIO(jpg_content), "image/jpeg")}
    
    res = client.post(
        "/api/v1/cases/DSP_EV_PROD_01/evidence-upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert res.json()["data"]["original_filename"] == "id_proof.jpg"


def test_upload_valid_csv():
    token = get_token("admin_user")
    csv_content = b"order_id,item,price\nORD_EV_01,Laptop,150.0"
    files = {"file": ("order_items.csv", io.BytesIO(csv_content), "text/csv")}
    
    res = client.post(
        "/api/v1/cases/DSP_EV_PROD_01/evidence-upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert res.json()["data"]["original_filename"] == "order_items.csv"


def test_upload_valid_txt():
    token = get_token("reviewer_user")
    txt_content = b"Customer support log transcript notes."
    files = {"file": ("chat_log.txt", io.BytesIO(txt_content), "text/plain")}
    
    res = client.post(
        "/api/v1/cases/DSP_EV_PROD_01/evidence-upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert res.json()["data"]["original_filename"] == "chat_log.txt"


def test_upload_unsupported_file_extension():
    token = get_token("admin_user")
    exe_content = b"MZExecutableContent"
    files = {"file": ("malicious.exe", io.BytesIO(exe_content), "application/x-msdownload")}
    
    res = client.post(
        "/api/v1/cases/DSP_EV_PROD_01/evidence-upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 400
    assert "Forbidden file extension" in res.json()["detail"]


def test_upload_oversized_file():
    token = get_token("admin_user")
    # Simulate oversized file (>10MB)
    large_content = b"X" * (11 * 1024 * 1024)
    files = {"file": ("huge_document.pdf", io.BytesIO(large_content), "application/pdf")}
    
    res = client.post(
        "/api/v1/cases/DSP_EV_PROD_01/evidence-upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code in (400, 413)


def test_upload_missing_dispute():
    token = get_token("admin_user")
    pdf_content = b"%PDF-1.4 Valid File"
    files = {"file": ("doc.pdf", io.BytesIO(pdf_content), "application/pdf")}
    
    res = client.post(
        "/api/v1/cases/DSP_NON_EXISTENT_99/evidence-upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 404
    assert "does not exist" in res.json()["detail"]


def test_upload_unauthenticated():
    pdf_content = b"%PDF-1.4 Valid File"
    files = {"file": ("doc.pdf", io.BytesIO(pdf_content), "application/pdf")}
    
    orig_env = settings.ENVIRONMENT
    try:
        settings.ENVIRONMENT = "production"
        res = client.post("/api/v1/cases/DSP_EV_PROD_01/evidence-upload", files=files)
        assert res.status_code == 401
    finally:
        settings.ENVIRONMENT = orig_env


def test_upload_analyst_rejected():
    token = get_token("analyst_user")
    pdf_content = b"%PDF-1.4 Valid File"
    files = {"file": ("doc.pdf", io.BytesIO(pdf_content), "application/pdf")}
    
    res = client.post(
        "/api/v1/cases/DSP_EV_PROD_01/evidence-upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403


def test_upload_auditor_rejected():
    token = get_token("auditor_user")
    pdf_content = b"%PDF-1.4 Valid File"
    files = {"file": ("doc.pdf", io.BytesIO(pdf_content), "application/pdf")}
    
    res = client.post(
        "/api/v1/cases/DSP_EV_PROD_01/evidence-upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403


def test_evidence_metadata_persistence_and_sha256():
    token = get_token("admin_user")
    content = b"%PDF-1.4 Persistent Verification Content"
    expected_hash = hashlib.sha256(content).hexdigest()
    files = {"file": ("unique_verify.pdf", io.BytesIO(content), "application/pdf")}
    
    res = client.post(
        "/api/v1/cases/DSP_EV_PROD_01/evidence-upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    ev_data = res.json()["data"]
    assert ev_data["sha256_hash"] == expected_hash
    assert ev_data["safe_filename"] == "unique_verify.pdf"
    assert ev_data["uploaded_by"] == "admin_user"


def test_filename_sanitization_and_path_traversal():
    token = get_token("admin_user")
    content = b"%PDF-1.4 Path Traversal Test"
    files = {"file": ("../../etc/passwd_evil.pdf", io.BytesIO(content), "application/pdf")}
    
    res = client.post(
        "/api/v1/cases/DSP_EV_PROD_01/evidence-upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    safe_name = res.json()["data"]["safe_filename"]
    assert ".." not in safe_name
    assert "/" not in safe_name
    assert "\\" not in safe_name
    assert safe_name == "passwd_evil.pdf"


def test_duplicate_evidence_detection():
    token = get_token("admin_user")
    content = b"%PDF-1.4 Exact Duplicate Content String"
    files1 = {"file": ("first_upload.pdf", io.BytesIO(content), "application/pdf")}
    files2 = {"file": ("second_upload.pdf", io.BytesIO(content), "application/pdf")}
    
    res1 = client.post(
        "/api/v1/cases/DSP_EV_PROD_01/evidence-upload",
        files=files1,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res1.status_code == 200
    ev_id1 = res1.json()["data"]["evidence_id"]

    # Duplicate upload attempt
    res2 = client.post(
        "/api/v1/cases/DSP_EV_PROD_01/evidence-upload",
        files=files2,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["meta"]["upload_status"] == "DUPLICATE_IDEMPOTENT"
    assert data2["data"]["evidence_id"] == ev_id1


def test_production_vs_simulation_data_state_isolation():
    token = get_token("admin_user")
    content_prod = b"%PDF-1.4 Production Doc"
    content_sim = b"%PDF-1.4 Simulation Doc"
    
    res_prod = client.post(
        "/api/v1/cases/DSP_EV_PROD_01/evidence-upload",
        files={"file": ("prod.pdf", io.BytesIO(content_prod), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_prod.status_code == 200
    assert res_prod.json()["data"]["data_state"] == "PRODUCTION"

    res_sim = client.post(
        "/api/v1/cases/DSP_EV_SIM_01/evidence-upload",
        files={"file": ("sim.pdf", io.BytesIO(content_sim), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_sim.status_code == 200
    assert res_sim.json()["data"]["data_state"] == "SIMULATION"


def test_list_evidence_rbac():
    # Analyst role can list evidence
    token_analyst = get_token("analyst_user")
    res = client.get("/api/v1/cases/DSP_EV_PROD_01/evidence", headers={"Authorization": f"Bearer {token_analyst}"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert "evidence_documents" in data
    assert data["total_count"] >= 1

    # Unauthenticated rejected
    orig_env = settings.ENVIRONMENT
    try:
        settings.ENVIRONMENT = "production"
        assert client.get("/api/v1/cases/DSP_EV_PROD_01/evidence").status_code == 401
    finally:
        settings.ENVIRONMENT = orig_env


def test_secure_retrieval_and_download():
    token = get_token("reviewer_user")
    content = b"%PDF-1.4 Downloadable File Content"
    upload_res = client.post(
        "/api/v1/cases/DSP_EV_PROD_01/evidence-upload",
        files={"file": ("download_test.pdf", io.BytesIO(content), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"}
    )
    ev_id = upload_res.json()["data"]["evidence_id"]

    # Stream file download
    dl_res = client.get(
        f"/api/v1/cases/DSP_EV_PROD_01/evidence/{ev_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert dl_res.status_code == 200
    assert dl_res.content == content
    assert dl_res.headers["content-type"] == "application/pdf"


def test_cross_dispute_retrieval_rejection():
    token = get_token("admin_user")
    content = b"%PDF-1.4 Dispute A Doc"
    upload_res = client.post(
        "/api/v1/cases/DSP_EV_PROD_01/evidence-upload",
        files={"file": ("disp_a.pdf", io.BytesIO(content), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"}
    )
    ev_id = upload_res.json()["data"]["evidence_id"]

    # Attempt to retrieve under wrong dispute_id
    res = client.get(
        f"/api/v1/cases/DSP_EV_SIM_01/evidence/{ev_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 404


def test_revoke_evidence_rbac():
    token_admin = get_token("admin_user")
    token_reviewer = get_token("reviewer_user")
    
    # Upload doc to revoke
    content = b"%PDF-1.4 Document to Revoke"
    upload_res = client.post(
        "/api/v1/cases/DSP_EV_PROD_01/evidence-upload",
        files={"file": ("to_revoke.pdf", io.BytesIO(content), "application/pdf")},
        headers={"Authorization": f"Bearer {token_admin}"}
    )
    ev_id = upload_res.json()["data"]["evidence_id"]

    # Reviewer role cannot revoke (403)
    res_rev_rev = client.delete(
        f"/api/v1/cases/DSP_EV_PROD_01/evidence/{ev_id}",
        headers={"Authorization": f"Bearer {token_reviewer}"}
    )
    assert res_rev_rev.status_code == 403

    # Admin role can revoke (200)
    res_admin_rev = client.delete(
        f"/api/v1/cases/DSP_EV_PROD_01/evidence/{ev_id}",
        headers={"Authorization": f"Bearer {token_admin}"}
    )
    assert res_admin_rev.status_code == 200
    assert res_admin_rev.json()["data"]["status"] == "REVOKED"

    # Subsequent download fails (404)
    assert client.get(f"/api/v1/cases/DSP_EV_PROD_01/evidence/{ev_id}", headers={"Authorization": f"Bearer {token_admin}"}).status_code == 404


def test_failed_db_operation_cleans_physical_file():
    db = TestingSessionLocal()
    content = b"%PDF-1.4 Trigger DB Failure"
    
    # Mock db.commit to simulate database exception
    with patch.object(db, "commit", side_effect=Exception("Database Connection Failure")):
        with pytest.raises(Exception):
            evidence_storage_service.store_evidence_document(
                db=db,
                dispute_id="DSP_EV_PROD_01",
                file_bytes=content,
                original_filename="db_fail_test.pdf",
                content_type="application/pdf",
                uploaded_by="admin_user"
            )
            
    db.close()
    
    # Verify no physical file left behind in dispute directory
    dispute_dir = os.path.join(TEST_STORAGE_DIR, "DSP_EV_PROD_01")
    if os.path.exists(dispute_dir):
        files_left = os.listdir(dispute_dir)
        for f in files_left:
            assert "db_fail_test.pdf" not in f
