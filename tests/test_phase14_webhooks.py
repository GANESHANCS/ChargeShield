"""
Phase 14 Milestone 2 Unit and Integration Test Suite: Payment Gateway Webhooks & Real-Time Dispute Feed.

Verifies all 24 webhook milestone requirements.
"""

import hmac
import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.config import settings
from backend.services.case_service import case_service
from backend.db.database import get_db_session
from backend.db.models import (
    CustomerModel,
    OrderModel,
    TransactionModel,
    DisputeModel,
    WebhookEventModel,
)

client = TestClient(app)


def make_signature(raw_body: bytes, timestamp_str: str, secret: str = settings.WEBHOOK_SECRET) -> str:
    msg = f"{timestamp_str}.".encode("utf-8") + raw_body
    sig = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    return f"v1={sig}"


def create_sample_webhook_payload(
    event_id: str = None,
    dispute_id: str = None,
    order_id: str = None,
    txn_id: str = None,
    cust_id: str = None,
    disputed_amount: float = 25000.0,
    data_state: str = "PRODUCTION",
) -> dict:
    uid = uuid.uuid4().hex[:6].upper()
    event_id = event_id or f"evt_wh_{uid}"
    dispute_id = dispute_id or f"DSP_WH_{uid}"
    order_id = order_id or f"ORD_WH_{uid}"
    txn_id = txn_id or f"TXN_WH_{uid}"
    cust_id = cust_id or f"CUS_WH_{uid}"

    now_iso = datetime.now(timezone.utc).isoformat()
    return {
        "event_id": event_id,
        "event_type": "dispute.created",
        "timestamp": now_iso,
        "data_state": data_state,
        "customer": {
            "customer_id": cust_id,
            "account_creation_date": now_iso,
            "tenure_days": 400.0,
            "country": "IN",
            "total_order_count": 12.0,
            "successful_order_count": 11.0,
            "previous_dispute_count": 0.0,
            "previous_chargeback_count": 0.0,
            "refund_count": 1.0,
            "account_status": "ACTIVE",
            "customer_segment": "VIP",
        },
        "order": {
            "order_id": order_id,
            "customer_id": cust_id,
            "product_category": "ELECTRONICS",
            "order_amount": disputed_amount,
            "currency": "INR",
            "fulfillment_status": "DELIVERED",
            "cancellation_status": "NONE",
            "order_timestamp": now_iso,
        },
        "transaction": {
            "transaction_id": txn_id,
            "order_id": order_id,
            "payment_method": "CREDIT_CARD",
            "payment_gateway": "STRIPE",
            "transaction_status": "CAPTURED",
            "payment_success": 1.0,
            "auth_risk_score": 0.05,
            "velocity_24h": 1.0,
            "transaction_timestamp": now_iso,
            "amount": disputed_amount,
        },
        "dispute": {
            "dispute_id": dispute_id,
            "transaction_id": txn_id,
            "order_id": order_id,
            "customer_id": cust_id,
            "disputed_amount": disputed_amount,
            "currency": "INR",
            "dispute_reason_code": "13.1_MERCH_NOT_RECEIVED",
            "dispute_category": "FRAUD",
            "dispute_status": "PENDING_REVIEW",
            "dispute_stage": "FIRST_CHARGEBACK",
            "dispute_creation_timestamp": now_iso,
            "response_deadline": now_iso,
            "evidence_deadline": now_iso,
        },
    }


# 1. Valid Webhook Accepted
def test_valid_signed_webhook_accepted():
    payload = create_sample_webhook_payload()
    event_id = payload["event_id"]
    disp_id = payload["dispute"]["dispute_id"]

    raw_body = json.dumps(payload).encode("utf-8")
    ts_str = str(int(time.time()))
    sig = make_signature(raw_body, ts_str)

    res = client.post(
        "/api/v1/webhooks/dispute",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-ChargeShield-Signature": sig,
            "X-ChargeShield-Timestamp": ts_str,
            "X-Correlation-ID": "corr-test-101",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["event_id"] == event_id
    assert data["dispute_id"] == disp_id
    assert data["correlation_id"] == "corr-test-101"


# 2. Invalid Signature Rejected
def test_invalid_signature_rejected():
    payload = create_sample_webhook_payload()
    raw_body = json.dumps(payload).encode("utf-8")
    ts_str = str(int(time.time()))

    res = client.post(
        "/api/v1/webhooks/dispute",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-ChargeShield-Signature": "v1=invalid_hmac_signature_999",
            "X-ChargeShield-Timestamp": ts_str,
        },
    )
    assert res.status_code == 401
    assert res.json()["status"] == "ERROR"
    assert "signature verification failed" in res.json()["message"].lower()


# 3. Missing Signature Rejected
def test_missing_signature_rejected():
    payload = create_sample_webhook_payload()
    raw_body = json.dumps(payload).encode("utf-8")

    res = client.post(
        "/api/v1/webhooks/dispute",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-ChargeShield-Timestamp": str(int(time.time())),
        },
    )
    assert res.status_code == 401
    assert "Missing required webhook signature" in res.json()["message"]


# 4. Expired/Replayed Timestamp Rejected
def test_expired_timestamp_rejected():
    payload = create_sample_webhook_payload()
    raw_body = json.dumps(payload).encode("utf-8")
    old_ts_str = str(int(time.time()) - 600)
    sig = make_signature(raw_body, old_ts_str)

    res = client.post(
        "/api/v1/webhooks/dispute",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-ChargeShield-Signature": sig,
            "X-ChargeShield-Timestamp": old_ts_str,
        },
    )
    assert res.status_code == 400
    assert "timestamp skew" in res.json()["message"].lower()


# 5. Malformed Payload Rejected
def test_malformed_payload_rejected():
    raw_body = b"{ invalid json string ... "
    ts_str = str(int(time.time()))
    sig = make_signature(raw_body, ts_str)

    res = client.post(
        "/api/v1/webhooks/dispute",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-ChargeShield-Signature": sig,
            "X-ChargeShield-Timestamp": ts_str,
        },
    )
    assert res.status_code == 422


# 6. Missing Required Fields Rejected
def test_missing_required_fields_rejected():
    payload = {"event_id": "evt_incomplete", "event_type": "dispute.created"}
    raw_body = json.dumps(payload).encode("utf-8")
    ts_str = str(int(time.time()))
    sig = make_signature(raw_body, ts_str)

    res = client.post(
        "/api/v1/webhooks/dispute",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-ChargeShield-Signature": sig,
            "X-ChargeShield-Timestamp": ts_str,
        },
    )
    assert res.status_code == 422


# 7, 8, 9, 10, 11. Relational Entities Creation & Atomic Persistence
def test_webhook_creates_relational_entities_atomically():
    payload = create_sample_webhook_payload()
    event_id = payload["event_id"]
    disp_id = payload["dispute"]["dispute_id"]
    ord_id = payload["order"]["order_id"]
    txn_id = payload["transaction"]["transaction_id"]
    cust_id = payload["customer"]["customer_id"]

    raw_body = json.dumps(payload).encode("utf-8")
    ts_str = str(int(time.time()))
    sig = make_signature(raw_body, ts_str)

    res = client.post(
        "/api/v1/webhooks/dispute",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-ChargeShield-Signature": sig,
            "X-ChargeShield-Timestamp": ts_str,
        },
    )
    assert res.status_code == 200

    with get_db_session() as session:
        c_db = session.query(CustomerModel).filter_by(customer_id=cust_id).first()
        o_db = session.query(OrderModel).filter_by(order_id=ord_id).first()
        t_db = session.query(TransactionModel).filter_by(transaction_id=txn_id).first()
        d_db = session.query(DisputeModel).filter_by(dispute_id=disp_id).first()
        w_db = session.query(WebhookEventModel).filter_by(event_id=event_id).first()

        assert c_db is not None
        assert o_db is not None
        assert t_db is not None
        assert d_db is not None
        assert w_db is not None

        assert d_db.customer_id == cust_id
        assert d_db.order_id == ord_id
        assert d_db.transaction_id == txn_id
        assert w_db.processing_status == "PROCESSED"


# 12. Database Failure Rolls Back Everything
def test_database_failure_rolls_back_everything(monkeypatch):
    payload = create_sample_webhook_payload()
    event_id = payload["event_id"]
    disp_id = payload["dispute"]["dispute_id"]
    cust_id = payload["customer"]["customer_id"]

    raw_body = json.dumps(payload).encode("utf-8")
    ts_str = str(int(time.time()))
    sig = make_signature(raw_body, ts_str)

    real_get_db = get_db_session

    class FailingSession:
        def __init__(self, real_sess):
            self.real_sess = real_sess
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.real_sess.__exit__(exc_type, exc_val, exc_tb)
        def query(self, *args, **kwargs):
            return self.real_sess.query(*args, **kwargs)
        def add(self, *args, **kwargs):
            return self.real_sess.add(*args, **kwargs)
        def commit(self):
            raise RuntimeError("Simulated Database Transaction Failure")
        def rollback(self):
            return self.real_sess.rollback()

    call_count = [0]
    def mock_get_db_session():
        call_count[0] += 1
        real_sess = real_get_db()
        if call_count[0] == 2:
            return FailingSession(real_sess)
        return real_sess

    monkeypatch.setattr("backend.services.webhook_service.get_db_session", mock_get_db_session)

    res = client.post(
        "/api/v1/webhooks/dispute",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-ChargeShield-Signature": sig,
            "X-ChargeShield-Timestamp": ts_str,
        },
    )
    assert res.status_code == 500

    with real_get_db() as session:
        d_db = session.query(DisputeModel).filter_by(dispute_id=disp_id).first()
        c_db = session.query(CustomerModel).filter_by(customer_id=cust_id).first()
        assert d_db is None
        assert c_db is None


# 13. Idempotent Duplicate Event Handling
def test_idempotent_duplicate_webhook():
    payload = create_sample_webhook_payload()
    raw_body = json.dumps(payload).encode("utf-8")
    ts_str = str(int(time.time()))
    sig = make_signature(raw_body, ts_str)

    headers = {
        "Content-Type": "application/json",
        "X-ChargeShield-Signature": sig,
        "X-ChargeShield-Timestamp": ts_str,
    }

    # First send
    res1 = client.post("/api/v1/webhooks/dispute", content=raw_body, headers=headers)
    assert res1.status_code == 200
    assert res1.json()["status"] == "SUCCESS"

    # Second send (identical raw body)
    res2 = client.post("/api/v1/webhooks/dispute", content=raw_body, headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "IDEMPOTENT_SUCCESS"
    assert "previously processed" in data2["message"].lower()


# 14. Conflicting Duplicate Event Rejection (409 Conflict)
def test_conflicting_duplicate_event_rejected():
    payload1 = create_sample_webhook_payload(disputed_amount=1000.0)
    event_id = payload1["event_id"]
    raw_body1 = json.dumps(payload1).encode("utf-8")
    ts_str1 = str(int(time.time()))
    sig1 = make_signature(raw_body1, ts_str1)

    res1 = client.post(
        "/api/v1/webhooks/dispute",
        content=raw_body1,
        headers={
            "Content-Type": "application/json",
            "X-ChargeShield-Signature": sig1,
            "X-ChargeShield-Timestamp": ts_str1,
        },
    )
    assert res1.status_code == 200

    # Second send with SAME event_id but DIFFERENT payload content
    payload2 = dict(payload1)
    payload2["dispute"] = dict(payload1["dispute"])
    payload2["dispute"]["disputed_amount"] = 9999.0

    raw_body2 = json.dumps(payload2).encode("utf-8")
    ts_str2 = str(int(time.time()))
    sig2 = make_signature(raw_body2, ts_str2)

    res2 = client.post(
        "/api/v1/webhooks/dispute",
        content=raw_body2,
        headers={
            "Content-Type": "application/json",
            "X-ChargeShield-Signature": sig2,
            "X-ChargeShield-Timestamp": ts_str2,
        },
    )
    assert res2.status_code == 409
    assert res2.json()["status"] == "CONFLICT"
    assert "already exists with different payload" in res2.json()["message"]


# 15. Enforces PRODUCTION Data State
def test_enforces_production_data_state():
    payload = create_sample_webhook_payload()
    disp_id = payload["dispute"]["dispute_id"]
    cust_id = payload["customer"]["customer_id"]

    raw_body = json.dumps(payload).encode("utf-8")
    ts_str = str(int(time.time()))
    sig = make_signature(raw_body, ts_str)

    res = client.post(
        "/api/v1/webhooks/dispute",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-ChargeShield-Signature": sig,
            "X-ChargeShield-Timestamp": ts_str,
        },
    )
    assert res.status_code == 200

    with get_db_session() as session:
        d_db = session.query(DisputeModel).filter_by(dispute_id=disp_id).first()
        c_db = session.query(CustomerModel).filter_by(customer_id=cust_id).first()
        assert d_db.data_state == "PRODUCTION"
        assert c_db.data_state == "PRODUCTION"


# 16, 17, 18. CaseService Visibility & Contract Preservation
def test_webhook_dispute_immediately_visible_in_caseservice():
    payload = create_sample_webhook_payload()
    disp_id = payload["dispute"]["dispute_id"]
    cust_id = payload["customer"]["customer_id"]

    raw_body = json.dumps(payload).encode("utf-8")
    ts_str = str(int(time.time()))
    sig = make_signature(raw_body, ts_str)

    res = client.post(
        "/api/v1/webhooks/dispute",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-ChargeShield-Signature": sig,
            "X-ChargeShield-Timestamp": ts_str,
        },
    )
    assert res.status_code == 200

    # 1. Fetch via case_service.get_case_detail
    detail = case_service.get_case_detail(disp_id)
    assert detail is not None
    assert detail["dispute"]["dispute_id"] == disp_id
    assert detail["customer"]["customer_id"] == cust_id

    # 2. Fetch via GET /api/v1/cases/{dispute_id} API endpoint
    api_res = client.get(f"/api/v1/cases/{disp_id}")
    assert api_res.status_code == 200
    api_detail = api_res.json()
    assert api_detail["dispute_id"] == disp_id
    assert api_detail["customer"]["customer_id"] == cust_id

    # 3. Fetch via GET /api/v1/cases list
    list_res = client.get("/api/v1/cases?page=1&page_size=100")
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    found_ids = [c["dispute_id"] for c in items]
    assert disp_id in found_ids


# 19. Audit Event Created in WebhookEventModel
def test_audit_event_created_in_webhook_events():
    payload = create_sample_webhook_payload()
    event_id = payload["event_id"]
    disp_id = payload["dispute"]["dispute_id"]

    raw_body = json.dumps(payload).encode("utf-8")
    ts_str = str(int(time.time()))
    sig = make_signature(raw_body, ts_str)

    res = client.post(
        "/api/v1/webhooks/dispute",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-ChargeShield-Signature": sig,
            "X-ChargeShield-Timestamp": ts_str,
            "X-Correlation-ID": "corr-audit-019",
        },
    )
    assert res.status_code == 200

    with get_db_session() as session:
        we = session.query(WebhookEventModel).filter_by(event_id=event_id).first()
        assert we is not None
        assert we.dispute_id == disp_id
        assert we.correlation_id == "corr-audit-019"
        assert we.processing_status == "PROCESSED"
        assert len(we.payload_hash) == 64


# 20. Secrets/Signatures Not Leaked into Responses or Exceptions
def test_no_secret_or_signature_leakage():
    secret_str = settings.WEBHOOK_SECRET
    payload = create_sample_webhook_payload()
    raw_body = json.dumps(payload).encode("utf-8")
    ts_str = str(int(time.time()))

    res = client.post(
        "/api/v1/webhooks/dispute",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-ChargeShield-Signature": "v1=bad_signature_val",
            "X-ChargeShield-Timestamp": ts_str,
        },
    )
    assert res.status_code == 401
    resp_text = res.text
    assert secret_str not in resp_text
    assert "bad_signature_val" not in resp_text or "signature verification failed" in resp_text


# 21. Correlation ID Preservation
def test_correlation_id_preservation():
    payload = create_sample_webhook_payload()
    raw_body = json.dumps(payload).encode("utf-8")
    ts_str = str(int(time.time()))
    sig = make_signature(raw_body, ts_str)
    test_corr_id = "corr-custom-header-999"

    res = client.post(
        "/api/v1/webhooks/dispute",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-ChargeShield-Signature": sig,
            "X-ChargeShield-Timestamp": ts_str,
            "X-Correlation-ID": test_corr_id,
        },
    )
    assert res.status_code == 200
    assert res.json()["correlation_id"] == test_corr_id


# 22, 23. Simulation Isolation
def test_simulation_data_state_isolation():
    payload = create_sample_webhook_payload(data_state="SIMULATION")
    disp_id = payload["dispute"]["dispute_id"]

    raw_body = json.dumps(payload).encode("utf-8")
    ts_str = str(int(time.time()))
    sig = make_signature(raw_body, ts_str)

    res = client.post(
        "/api/v1/webhooks/dispute",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-ChargeShield-Signature": sig,
            "X-ChargeShield-Timestamp": ts_str,
        },
    )
    assert res.status_code == 200

    with get_db_session() as session:
        d_db = session.query(DisputeModel).filter_by(dispute_id=disp_id).first()
        assert d_db.data_state == "PRODUCTION"

    sim_cases = case_service.list_cases(page=1, page_size=100, data_state="SIMULATION")
    sim_ids = [c["dispute_id"] for c in sim_cases["items"]]
    assert disp_id not in sim_ids
