"""
FastAPI Router for Payment Gateway Webhooks (/api/v1/webhooks/dispute).
Handles HMAC verification, request body parsing, error mapping, and correlation tracking.
"""

import uuid
import time
import json
from typing import Dict, Any
from fastapi import APIRouter, Request, Header, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from backend.schemas.webhooks import DisputeWebhookRequest, WebhookResponseEnvelope
from backend.services.webhook_service import (
    webhook_service,
    WebhookAuthenticationError,
    ReplayProtectionError,
    DuplicateConflictError,
)
from backend.core.logging import logger

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])


@router.post("/dispute", response_model=WebhookResponseEnvelope, status_code=status.HTTP_200_OK)
async def ingest_dispute_webhook(
    request: Request,
    x_chargeshield_signature: str = Header(None, alias="X-ChargeShield-Signature"),
    x_chargeshield_timestamp: str = Header(None, alias="X-ChargeShield-Timestamp"),
    x_correlation_id: str = Header(None, alias="X-Correlation-ID"),
):
    """
    Ingests, authenticates, validates, and persists external payment gateway dispute webhooks.
    Applies HMAC-SHA256 signature verification and clock skew replay protection.
    Atomically creates relational Customer, Order, Transaction, Dispute, and Webhook Audit entities.
    Enforces PRODUCTION data-state governance and idempotency.
    """
    raw_body = await request.body()
    correlation_id = x_correlation_id or getattr(request.state, "request_id", None) or f"corr-{uuid.uuid4().hex[:8]}"
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Fallback to alternate header names if X-ChargeShield-* not present
    sig_header = x_chargeshield_signature or request.headers.get("x-signature") or request.headers.get("X-Signature")
    ts_header = x_chargeshield_timestamp or request.headers.get("x-timestamp") or request.headers.get("X-Timestamp")

    # 1. Webhook Authentication & Replay Verification
    try:
        webhook_service.verify_signature_and_timestamp(
            raw_body=raw_body,
            signature_header=sig_header,
            timestamp_header=ts_header
        )
    except WebhookAuthenticationError as auth_err:
        logger.warning(f"Webhook authentication failed: {str(auth_err)}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "status": "ERROR",
                "event_id": "UNKNOWN",
                "dispute_id": None,
                "message": str(auth_err),
                "correlation_id": correlation_id,
                "timestamp": now_iso,
            }
        )
    except ReplayProtectionError as replay_err:
        logger.warning(f"Webhook replay protection triggered: {str(replay_err)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status": "ERROR",
                "event_id": "UNKNOWN",
                "dispute_id": None,
                "message": str(replay_err),
                "correlation_id": correlation_id,
                "timestamp": now_iso,
            }
        )

    # 2. Payload Parsing & Schema Validation
    try:
        json_data = json.loads(raw_body.decode("utf-8"))
        payload = DisputeWebhookRequest.model_validate(json_data)
    except (json.JSONDecodeError, ValidationError) as val_err:
        logger.warning(f"Malformed webhook payload: {str(val_err)}")
        err_msg = "Invalid or malformed dispute webhook JSON payload."
        if isinstance(val_err, ValidationError):
            first_err = val_err.errors()[0]
            loc_str = " -> ".join([str(x) for x in first_err.get("loc", [])])
            err_msg = f"Validation error at {loc_str}: {first_err.get('msg', '')}"
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "ERROR",
                "event_id": "UNKNOWN",
                "dispute_id": None,
                "message": err_msg,
                "correlation_id": correlation_id,
                "timestamp": now_iso,
            }
        )

    # 3. Processing & Persistence
    try:
        response_data, status_code = webhook_service.process_dispute_webhook(
            payload=payload,
            raw_body=raw_body,
            correlation_id=correlation_id
        )
        return JSONResponse(status_code=status_code, content=response_data)
    except DuplicateConflictError as conflict_err:
        logger.warning(f"Webhook duplicate conflict: {str(conflict_err)}")
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "status": "CONFLICT",
                "event_id": payload.event_id,
                "dispute_id": payload.dispute.dispute_id,
                "message": str(conflict_err),
                "correlation_id": correlation_id,
                "timestamp": now_iso,
            }
        )
    except Exception as exc:
        logger.error(f"Internal error during webhook processing: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "ERROR",
                "event_id": payload.event_id if 'payload' in locals() else "UNKNOWN",
                "dispute_id": payload.dispute.dispute_id if 'payload' in locals() else None,
                "message": "Internal database or server error processing dispute webhook.",
                "correlation_id": correlation_id,
                "timestamp": now_iso,
            }
        )
