"""
Webhook Service for ChargeShield Payment Gateway Ingestion.
Handles HMAC-SHA256 authentication, replay protection, payload validation,
idempotency checks, atomic relational DB transactions, audit logging,
and production event stream publishing.
"""

import hmac
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional

from backend.core.config import settings
from backend.core.logging import logger
from backend.db.database import get_db_session
from backend.db.models import (
    CustomerModel,
    OrderModel,
    TransactionModel,
    DisputeModel,
    WebhookEventModel,
)
from backend.schemas.webhooks import DisputeWebhookRequest
from backend.services.event_service import event_service
from backend.services.case_service import case_service


class WebhookAuthenticationError(Exception):
    """Raised when signature verification or authentication fails."""
    pass


class ReplayProtectionError(Exception):
    """Raised when timestamp is outside allowed clock skew window."""
    pass


class DuplicateConflictError(Exception):
    """Raised when an existing event_id is received with conflicting payload data."""
    pass


class WebhookService:
    """Service managing payment gateway dispute webhooks with HMAC security and atomic persistence."""

    def __init__(self, secret: str = settings.WEBHOOK_SECRET, skew_seconds: int = settings.WEBHOOK_MAX_CLOCK_SKEW_SECONDS):
        self.secret = secret
        self.skew_seconds = skew_seconds

    def verify_signature_and_timestamp(
        self,
        raw_body: bytes,
        signature_header: Optional[str],
        timestamp_header: Optional[str]
    ) -> bool:
        """
        Validates HMAC-SHA256 signature and checks timestamp for replay protection.
        Does NOT log secrets, signatures, or sensitive body contents.
        """
        if not signature_header:
            raise WebhookAuthenticationError("Missing required webhook signature header ('X-ChargeShield-Signature').")

        if not timestamp_header:
            raise WebhookAuthenticationError("Missing required webhook timestamp header ('X-ChargeShield-Timestamp').")

        # 1. Verify Clock Skew / Replay Protection
        now_ts = datetime.now(timezone.utc).timestamp()
        try:
            # Handle ISO string or numeric epoch timestamp
            if "T" in timestamp_header:
                ts_dt = datetime.fromisoformat(timestamp_header.replace("Z", "+00:00"))
                event_ts = ts_dt.timestamp()
            else:
                event_ts = float(timestamp_header)
                if event_ts > 1e11:  # Epoch milliseconds
                    event_ts = event_ts / 1000.0
        except Exception:
            raise ReplayProtectionError("Malformed or unparseable webhook timestamp header.")

        skew = abs(now_ts - event_ts)
        if skew > self.skew_seconds:
            raise ReplayProtectionError(
                f"Webhook timestamp skew ({skew:.1f}s) exceeds maximum allowed threshold ({self.skew_seconds}s)."
            )

        # 2. Compute Expected Signature over (timestamp_header + "." + raw_body) and raw_body
        clean_sig = signature_header.strip()
        if clean_sig.startswith("v1="):
            clean_sig = clean_sig[3:]

        # Support signature generated over 'timestamp.raw_body' or 'raw_body'
        msg_payload_ts = f"{timestamp_header}.".encode("utf-8") + raw_body
        expected_sig_ts = hmac.new(self.secret.encode("utf-8"), msg_payload_ts, hashlib.sha256).hexdigest()
        expected_sig_raw = hmac.new(self.secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

        match_ts = hmac.compare_digest(expected_sig_ts.lower(), clean_sig.lower())
        match_raw = hmac.compare_digest(expected_sig_raw.lower(), clean_sig.lower())

        if not (match_ts or match_raw):
            raise WebhookAuthenticationError("Invalid webhook signature verification failed.")

        return True

    def process_dispute_webhook(
        self,
        payload: DisputeWebhookRequest,
        raw_body: bytes,
        correlation_id: str
    ) -> Tuple[Dict[str, Any], int]:
        """
        Atomically processes valid webhook:
        1. Calculates payload SHA-256 hash
        2. Idempotency & conflict checks against WebhookEventModel
        3. Single SQL transaction persistence (Customer -> Order -> Transaction -> Dispute -> WebhookEvent)
        4. Event stream publication
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        payload_hash = hashlib.sha256(raw_body).hexdigest()
        event_id = payload.event_id
        disp = payload.dispute
        cust = payload.customer
        ord_data = payload.order
        txn = payload.transaction

        # 1. Idempotency & Conflict Check
        with get_db_session() as session:
            existing_event = session.query(WebhookEventModel).filter_by(event_id=event_id).first()
            if existing_event:
                if existing_event.payload_hash == payload_hash:
                    logger.info(f"Idempotent webhook received for event_id '{event_id}'. Returning 200 OK.")
                    return {
                        "status": "IDEMPOTENT_SUCCESS",
                        "event_id": event_id,
                        "dispute_id": existing_event.dispute_id or disp.dispute_id,
                        "message": "Webhook event previously processed successfully.",
                        "correlation_id": correlation_id,
                        "timestamp": now_iso
                    }, 200
                else:
                    logger.warning(
                        f"Conflicting webhook payload received for existing event_id '{event_id}'. Rejecting with 409."
                    )
                    # Record audit trail of conflict attempt
                    raise DuplicateConflictError(
                        f"Event ID '{event_id}' already exists with different payload content. Duplicate rejected."
                    )

        # 2. Atomic SQL Transaction Multi-Entity Persistence
        try:
            with get_db_session() as session:
                # 2a. Customer
                c_obj = session.query(CustomerModel).filter_by(customer_id=cust.customer_id).first()
                if not c_obj:
                    c_obj = CustomerModel(
                        customer_id=cust.customer_id,
                        account_creation_date=cust.account_creation_date,
                        tenure_days=cust.tenure_days,
                        country=cust.country,
                        total_order_count=cust.total_order_count,
                        successful_order_count=cust.successful_order_count,
                        previous_dispute_count=cust.previous_dispute_count,
                        previous_chargeback_count=cust.previous_chargeback_count,
                        refund_count=cust.refund_count,
                        account_status=cust.account_status or "ACTIVE",
                        customer_segment=cust.customer_segment,
                        data_state="PRODUCTION",
                        created_at=now_iso,
                        updated_at=now_iso,
                    )
                    session.add(c_obj)
                else:
                    c_obj.data_state = "PRODUCTION"
                    c_obj.updated_at = now_iso

                # 2b. Order
                o_obj = session.query(OrderModel).filter_by(order_id=ord_data.order_id).first()
                if not o_obj:
                    o_obj = OrderModel(
                        order_id=ord_data.order_id,
                        customer_id=cust.customer_id,
                        product_category=ord_data.product_category,
                        order_amount=float(ord_data.order_amount or disp.disputed_amount),
                        currency=ord_data.currency or "INR",
                        fulfillment_status=ord_data.fulfillment_status or "DELIVERED",
                        cancellation_status=ord_data.cancellation_status or "NONE",
                        order_timestamp=ord_data.order_timestamp or now_iso,
                        data_state="PRODUCTION",
                        created_at=now_iso,
                        updated_at=now_iso,
                    )
                    session.add(o_obj)
                else:
                    o_obj.data_state = "PRODUCTION"
                    o_obj.updated_at = now_iso

                # 2c. Transaction
                t_obj = session.query(TransactionModel).filter_by(transaction_id=txn.transaction_id).first()
                if not t_obj:
                    t_obj = TransactionModel(
                        transaction_id=txn.transaction_id,
                        order_id=ord_data.order_id,
                        payment_method=txn.payment_method or "CREDIT_CARD",
                        payment_gateway=txn.payment_gateway or "STRIPE",
                        transaction_status=txn.transaction_status or "CAPTURED",
                        payment_success=float(txn.payment_success if txn.payment_success is not None else 1.0),
                        auth_risk_score=txn.auth_risk_score,
                        velocity_24h=txn.velocity_24h,
                        transaction_timestamp=txn.transaction_timestamp or now_iso,
                        amount=float(txn.amount or disp.disputed_amount),
                        data_state="PRODUCTION",
                        created_at=now_iso,
                        updated_at=now_iso,
                    )
                    session.add(t_obj)
                else:
                    t_obj.data_state = "PRODUCTION"
                    t_obj.updated_at = now_iso

                # 2d. Dispute
                d_obj = session.query(DisputeModel).filter_by(dispute_id=disp.dispute_id).first()
                if not d_obj:
                    d_obj = DisputeModel(
                        dispute_id=disp.dispute_id,
                        transaction_id=txn.transaction_id,
                        order_id=ord_data.order_id,
                        customer_id=cust.customer_id,
                        disputed_amount=float(disp.disputed_amount),
                        currency=disp.currency or "INR",
                        dispute_reason_code=disp.dispute_reason_code,
                        dispute_category=disp.dispute_category or "FRAUD",
                        dispute_status=disp.dispute_status or "PENDING_REVIEW",
                        dispute_stage=disp.dispute_stage or "FIRST_CHARGEBACK",
                        dispute_creation_timestamp=disp.dispute_creation_timestamp or now_iso,
                        response_deadline=disp.response_deadline or now_iso,
                        evidence_deadline=disp.evidence_deadline or now_iso,
                        data_state="PRODUCTION",
                        created_at=now_iso,
                        updated_at=now_iso,
                    )
                    session.add(d_obj)
                else:
                    d_obj.dispute_status = disp.dispute_status or d_obj.dispute_status
                    d_obj.data_state = "PRODUCTION"
                    d_obj.updated_at = now_iso

                # 2e. Webhook Audit Record
                we_obj = WebhookEventModel(
                    event_id=event_id,
                    event_type=payload.event_type,
                    dispute_id=disp.dispute_id,
                    correlation_id=correlation_id,
                    data_state="PRODUCTION",
                    processing_status="PROCESSED",
                    payload_hash=payload_hash,
                    failure_reason=None,
                    received_timestamp=now_iso,
                )
                session.add(we_obj)

                session.commit()
        except Exception as e:
            logger.error(f"Atomic database transaction failed for webhook event '{event_id}': {str(e)}")
            # Record failed event audit attempt if possible
            try:
                with get_db_session() as fail_session:
                    fail_we = WebhookEventModel(
                        event_id=event_id,
                        event_type=payload.event_type,
                        dispute_id=disp.dispute_id,
                        correlation_id=correlation_id,
                        data_state="PRODUCTION",
                        processing_status="REJECTED",
                        payload_hash=payload_hash,
                        failure_reason=str(e)[:1024],
                        received_timestamp=now_iso,
                    )
                    fail_session.add(fail_we)
                    fail_session.commit()
            except Exception:
                pass
            raise RuntimeError(f"Database transaction failure processing webhook: {str(e)}")

        # 3. Real-Time Event Feed Publication
        try:
            event_service.publish_event(
                event_type="DISPUTE_RECEIVED",
                message=f"Production Dispute Webhook received: {disp.dispute_id} ({disp.dispute_reason_code}) - {disp.currency} {disp.disputed_amount:.2f}",
                data_state="PRODUCTION",
                dispute_id=disp.dispute_id,
                transaction_id=txn.transaction_id,
                source="PAYMENT_GATEWAY_WEBHOOK",
                status="COMPLETED",
                metadata={
                    "gateway_event_id": event_id,
                    "event_type": payload.event_type,
                    "disputed_amount": disp.disputed_amount,
                    "currency": disp.currency,
                    "dispute_reason_code": disp.dispute_reason_code
                }
            )
        except Exception as pub_err:
            logger.warning(f"Failed to publish event to live stream: {str(pub_err)}")

        return {
            "status": "SUCCESS",
            "event_id": event_id,
            "dispute_id": disp.dispute_id,
            "message": "Dispute webhook successfully ingested and persisted into relational case queue.",
            "correlation_id": correlation_id,
            "timestamp": now_iso
        }, 200


webhook_service = WebhookService()
