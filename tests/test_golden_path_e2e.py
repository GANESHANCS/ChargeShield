"""
Golden-Path End-to-End Integration Test for ChargeShield.

Exercises the complete dispute lifecycle:
1. Webhook Ingestion (dispute.created) with HMAC verification & atomic DB persistence
2. Case Retrieval via CaseService and Case API
3. ML Risk Prediction & Recommendation
4. Review Queue Retrieval
5. Evidence Document Upload & SHA-256 integrity verification
6. Human Decision Authorization (CONTEST decision with justification)
7. Audit / Activity Log recording
8. Representment Evidence Package PDF export verification:
   - Starts with %PDF- magic header
   - Non-empty document structure
   - Contains dispute metadata, evidence file/SHA-256 hash, and reviewer decision
   - Displays '[ OUTCOME PENDING ]' (ground truth outcome not fabricated)
   - Enforces PRODUCTION vs SIMULATION isolation boundaries
"""

import io
import json
import time
import hmac
import hashlib
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.core.config import settings
from backend.db.database import get_db_session, init_db
from backend.services.user_service import seed_dev_users
from backend.services.auth_service import create_access_token
from backend.db.models import DisputeModel

client = TestClient(app)


def make_signature(raw_body: bytes, timestamp_str: str, secret: str = settings.WEBHOOK_SECRET) -> str:
    msg = f"{timestamp_str}.".encode("utf-8") + raw_body
    sig = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    return f"v1={sig}"


def get_auth_headers(username: str = "reviewer", role: str = "REVIEWER") -> dict:
    token = create_access_token({"sub": "USR_E2E_001", "username": username, "role": role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def setup_e2e_environment():
    init_db()
    with get_db_session() as db:
        seed_dev_users(db, admin_username="admin_e2e", admin_password="AdminPass123!")


def test_golden_path_end_to_end_dispute_lifecycle():
    import uuid
    uid = uuid.uuid4().hex[:6].upper()
    # Deterministic Test Data Identifiers
    dispute_id = f"DSP_GOLDEN_{uid}"
    event_id = f"EVT_GOLDEN_{uid}"
    order_id = f"ORD_GOLDEN_{uid}"
    txn_id = f"TXN_GOLDEN_{uid}"
    cust_id = f"CUS_GOLDEN_{uid}"
    now_iso = "2026-09-04T00:00:00Z"

    # Step 1: Webhook Ingestion
    webhook_payload = {
        "event_id": event_id,
        "event_type": "dispute.created",
        "timestamp": now_iso,
        "data_state": "PRODUCTION",
        "customer": {
            "customer_id": cust_id,
            "account_creation_date": now_iso,
            "tenure_days": 365.0,
            "country": "IN",
            "total_order_count": 15.0,
            "successful_order_count": 14.0,
            "previous_dispute_count": 0.0,
            "previous_chargeback_count": 0.0,
            "refund_count": 1.0,
            "account_status": "ACTIVE",
            "customer_segment": "REGULAR"
        },
        "order": {
            "order_id": order_id,
            "customer_id": cust_id,
            "product_category": "ELECTRONICS",
            "order_amount": 18500.0,
            "currency": "INR",
            "fulfillment_status": "DELIVERED",
            "cancellation_status": "NONE",
            "order_timestamp": now_iso
        },
        "transaction": {
            "transaction_id": txn_id,
            "order_id": order_id,
            "payment_method": "CREDIT_CARD",
            "payment_gateway": "STRIPE",
            "transaction_status": "CAPTURED",
            "payment_success": 1.0,
            "auth_risk_score": 0.02,
            "velocity_24h": 1.0,
            "transaction_timestamp": now_iso,
            "amount": 18500.0
        },
        "dispute": {
            "dispute_id": dispute_id,
            "transaction_id": txn_id,
            "order_id": order_id,
            "customer_id": cust_id,
            "disputed_amount": 18500.0,
            "currency": "INR",
            "dispute_reason_code": "13.1_MERCH_NOT_RECEIVED",
            "dispute_category": "FRAUD",
            "dispute_status": "PENDING_REVIEW",
            "dispute_stage": "FIRST_CHARGEBACK",
            "dispute_creation_timestamp": now_iso,
            "response_deadline": "2026-09-20T00:00:00Z",
            "evidence_deadline": "2026-09-18T00:00:00Z"
        }
    }

    raw_body = json.dumps(webhook_payload).encode("utf-8")
    ts_str = str(int(time.time()))
    sig = make_signature(raw_body, ts_str)

    wh_response = client.post(
        "/api/v1/webhooks/dispute",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-ChargeShield-Signature": sig,
            "X-ChargeShield-Timestamp": ts_str,
            "X-Correlation-ID": "golden-corr-e2e-001"
        }
    )
    assert wh_response.status_code == 200
    wh_data = wh_response.json()
    assert wh_data["status"] == "SUCCESS"
    assert wh_data["dispute_id"] == dispute_id

    # Verify Relational Persistence & PRODUCTION Data State
    with get_db_session() as session:
        disp_db = session.query(DisputeModel).filter_by(dispute_id=dispute_id).first()
        assert disp_db is not None
        assert disp_db.data_state == "PRODUCTION"
        assert disp_db.disputed_amount == 18500.0

    # Step 2: Case Retrieval via API
    auth_headers = get_auth_headers(username="reviewer", role="REVIEWER")
    case_res = client.get(f"/api/v1/cases/{dispute_id}", headers=auth_headers)
    assert case_res.status_code == 200
    case_json = case_res.json()
    assert case_json["dispute_id"] == dispute_id
    assert case_json["customer"]["customer_id"] == cust_id

    # Step 3: ML Risk Prediction
    pred_res = client.get(f"/api/v1/cases/{dispute_id}/prediction", headers=auth_headers)
    assert pred_res.status_code == 200
    pred_json = pred_res.json()
    assert "win_probability" in pred_json
    assert "recommendation" in pred_json

    # Step 4: Review Workflow Package Retrieval & Queue
    review_res = client.get(f"/api/v1/review/cases/{dispute_id}", headers=auth_headers)
    assert review_res.status_code == 200
    rev_pkg = review_res.json()
    assert rev_pkg["dispute_id"] == dispute_id
    assert rev_pkg["review_status"] in ["PENDING_REVIEW", "IN_REVIEW"]

    queue_res = client.get("/api/v1/review/queue?page_size=100", headers=auth_headers)
    assert queue_res.status_code == 200

    # Step 5: Evidence Document Upload & SHA-256 Verification
    evidence_content = b"E2E Golden Path Proof of Delivery PDF text content"
    files = {"file": ("pod_proof_e2e.pdf", io.BytesIO(evidence_content), "application/pdf")}
    upload_res = client.post(
        f"/api/v1/cases/{dispute_id}/evidence-upload",
        files=files,
        headers=auth_headers
    )
    assert upload_res.status_code == 200
    upload_data = upload_res.json()["data"]
    assert upload_data["dispute_id"] == dispute_id
    sha256_expected = hashlib.sha256(evidence_content).hexdigest()
    assert upload_data["sha256_hash"] == sha256_expected

    # Step 6: Human Decision Authorization
    decision_payload = {
        "reviewer_id": "reviewer",
        "decision": "CONTEST",
        "reason": "Verified carrier tracking and delivery receipt signature match customer shipping address."
    }
    dec_res = client.post(
        f"/api/v1/review/cases/{dispute_id}/decision",
        json=decision_payload,
        headers=auth_headers
    )
    assert dec_res.status_code == 200
    dec_json = dec_res.json()
    assert dec_json["decision"] == "CONTEST"

    # Step 7: Audit / Activity Log Verification
    audit_res = client.get(f"/api/v1/review/audit?dispute_id={dispute_id}", headers=auth_headers)
    assert audit_res.status_code == 200
    audit_items = audit_res.json()["items"]
    assert len(audit_items) >= 1
    assert audit_items[0]["decision"] == "CONTEST"

    # Step 8: Representment Evidence Package PDF Export
    pdf_res = client.get(f"/api/v1/cases/{dispute_id}/representment-package", headers=auth_headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert f"attachment; filename=\"chargeshield_representment_{dispute_id}.pdf\"" in pdf_res.headers["content-disposition"]
    pdf_bytes = pdf_res.content
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 500

    pdf_text = pdf_bytes.decode("latin1")
    assert dispute_id in pdf_text
    assert "[ OUTCOME PENDING ]" in pdf_text
    assert sha256_expected[:12] in pdf_text or "pod_proof_e2e.pdf" in pdf_text
    assert "CONTEST" in pdf_text

    # Step 9: Simulation Data Boundary Isolation
    sim_cases_res = client.get("/api/v1/cases?data_state=SIMULATION", headers=auth_headers)
    assert sim_cases_res.status_code == 200
    sim_items = sim_cases_res.json()["items"]
    sim_ids = [item["dispute_id"] for item in sim_items]
    assert dispute_id not in sim_ids
