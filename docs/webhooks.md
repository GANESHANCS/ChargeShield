# ChargeShield Payment Gateway Webhooks Integration Guide

## Overview

ChargeShield provides an enterprise-grade Payment Gateway Webhook API (`POST /api/v1/webhooks/dispute`) for real-time ingestion of chargeback and dispute events from external processors (e.g., Stripe, Razorpay, Adyen, PayPal).

All webhook events are authenticated using HMAC-SHA256 signatures, protected against replay attacks, processed idempotently, and persisted atomically into ChargeShield's relational database.

---

## Endpoint Details

- **Method**: `POST`
- **Path**: `/api/v1/webhooks/dispute`
- **Content-Type**: `application/json`
- **Authentication**: HMAC-SHA256 Signature (does not require browser JWT)

---

## Required Request Headers

| Header | Format / Type | Description |
| :--- | :--- | :--- |
| `X-ChargeShield-Signature` | String (`v1=<hex_signature>`) | HMAC-SHA256 signature calculated over timestamp and raw request body. |
| `X-ChargeShield-Timestamp` | String (ISO 8601 or Epoch seconds) | Timestamp when webhook was generated at source gateway. |
| `X-Correlation-ID` | String (UUID / String, Optional) | Correlation tracking ID preserved across processing logs. |

---

## HMAC-SHA256 Signature Generation

External payment gateways must sign the payload using the shared secret configured in `CHARGESHIELD_WEBHOOK_SECRET`.

### Signature Construction Algorithm

1. Construct the signature payload string by concatenating the timestamp header value, a dot `.`, and the exact raw UTF-8 request body bytes:
   ```text
   msg_to_sign = "<X-ChargeShield-Timestamp>." + raw_request_body_bytes
   ```
2. Compute the HMAC-SHA256 digest using `CHARGESHIELD_WEBHOOK_SECRET`:
   ```python
   signature = hmac.new(
       key=secret.encode('utf-8'),
       msg=msg_to_sign.encode('utf-8'),
       digestmod=hashlib.sha256
   ).hexdigest()
   ```
3. Attach the signature to the header:
   ```text
   X-ChargeShield-Signature: v1=<signature>
   ```

---

## Replay Protection Window

To prevent replay attacks:
- The server compares `X-ChargeShield-Timestamp` against the current UTC server time.
- If the difference (`abs(now - timestamp)`) exceeds **300 seconds (5 minutes)**, the request is rejected with `HTTP 400 Bad Request`.

---

## Idempotency & Conflict Semantics

- **Primary Idempotency Key**: `event_id` (gateway's unique event identifier).
- **Exact Retry**: If a webhook with an existing `event_id` and an **identical SHA-256 payload hash** is re-sent, ChargeShield returns `HTTP 200 OK` with status `IDEMPOTENT_SUCCESS` without duplicating database entities.
- **Conflicting Retry**: If an existing `event_id` is re-sent with **materially different payload data**, ChargeShield rejects the request with `HTTP 409 Conflict` and records a security audit entry.

---

## Sample Request Payload

```json
{
  "event_id": "evt_wh_live_998822",
  "event_type": "dispute.created",
  "timestamp": "2026-08-27T23:10:00Z",
  "data_state": "PRODUCTION",
  "customer": {
    "customer_id": "CUS_WH_001",
    "account_creation_date": "2025-01-15T08:00:00Z",
    "tenure_days": 590,
    "country": "IN",
    "total_order_count": 14,
    "successful_order_count": 13,
    "previous_dispute_count": 0,
    "previous_chargeback_count": 0,
    "refund_count": 1,
    "account_status": "ACTIVE",
    "customer_segment": "REGULAR"
  },
  "order": {
    "order_id": "ORD_WH_001",
    "customer_id": "CUS_WH_001",
    "product_category": "ELECTRONICS",
    "order_amount": 14999.00,
    "currency": "INR",
    "fulfillment_status": "DELIVERED",
    "cancellation_status": "NONE",
    "order_timestamp": "2026-08-20T14:30:00Z"
  },
  "transaction": {
    "transaction_id": "TXN_WH_001",
    "order_id": "ORD_WH_001",
    "payment_method": "CREDIT_CARD",
    "payment_gateway": "STRIPE",
    "transaction_status": "CAPTURED",
    "payment_success": 1.0,
    "auth_risk_score": 0.08,
    "velocity_24h": 1.0,
    "transaction_timestamp": "2026-08-20T14:31:05Z",
    "amount": 14999.00
  },
  "dispute": {
    "dispute_id": "DSP_WH_001",
    "transaction_id": "TXN_WH_001",
    "order_id": "ORD_WH_001",
    "customer_id": "CUS_WH_001",
    "disputed_amount": 14999.00,
    "currency": "INR",
    "dispute_reason_code": "13.1_MERCH_NOT_RECEIVED",
    "dispute_category": "FRAUD",
    "dispute_status": "PENDING_REVIEW",
    "dispute_stage": "FIRST_CHARGEBACK",
    "dispute_creation_timestamp": "2026-08-27T23:05:00Z",
    "response_deadline": "2026-09-10T23:59:59Z",
    "evidence_deadline": "2026-09-08T23:59:59Z"
  }
}
```

---

## Expected API Responses

### 1. Success Response (200 OK)
```json
{
  "status": "SUCCESS",
  "event_id": "evt_wh_live_998822",
  "dispute_id": "DSP_WH_001",
  "message": "Dispute webhook successfully ingested and persisted into relational case queue.",
  "correlation_id": "corr-a1b2c3d4",
  "timestamp": "2026-08-27T23:10:01Z"
}
```

### 2. Idempotent Retry Response (200 OK)
```json
{
  "status": "IDEMPOTENT_SUCCESS",
  "event_id": "evt_wh_live_998822",
  "dispute_id": "DSP_WH_001",
  "message": "Webhook event previously processed successfully.",
  "correlation_id": "corr-a1b2c3d4",
  "timestamp": "2026-08-27T23:10:02Z"
}
```

### 3. Authentication Failure (401 Unauthorized)
```json
{
  "status": "ERROR",
  "event_id": "UNKNOWN",
  "dispute_id": null,
  "message": "Invalid webhook signature verification failed.",
  "correlation_id": "corr-a1b2c3d4",
  "timestamp": "2026-08-27T23:10:01Z"
}
```

### 4. Conflicting Retry (409 Conflict)
```json
{
  "status": "CONFLICT",
  "event_id": "evt_wh_live_998822",
  "dispute_id": "DSP_WH_001",
  "message": "Event ID 'evt_wh_live_998822' already exists with different payload content. Duplicate rejected.",
  "correlation_id": "corr-a1b2c3d4",
  "timestamp": "2026-08-27T23:10:01Z"
}
```

---

## Production Security Considerations

1. **Environment Secret**: Always set a high-entropy secret for `CHARGESHIELD_WEBHOOK_SECRET` in production `.env`.
2. **TLS / HTTPS**: Ensure production webhooks are served exclusively over TLS 1.3 / HTTPS.
3. **No Secret Logging**: Secrets, raw signatures, and authentication credentials are strictly excluded from server logs and exception payloads.
