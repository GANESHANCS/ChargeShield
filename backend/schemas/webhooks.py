"""
Pydantic API Schemas for Payment Gateway Webhook ingestion and responses.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class CustomerWebhookData(BaseModel):
    customer_id: str = Field(..., description="Unique customer identification code")
    account_creation_date: Optional[str] = Field(None, description="ISO timestamp of account creation")
    tenure_days: Optional[float] = Field(365.0, description="Customer tenure in days")
    country: Optional[str] = Field("IN", description="Two-letter country code")
    total_order_count: Optional[float] = Field(10.0, description="Historical total order count")
    successful_order_count: Optional[float] = Field(9.0, description="Historical successful order count")
    previous_dispute_count: Optional[float] = Field(0.0, description="Previous dispute count")
    previous_chargeback_count: Optional[float] = Field(0.0, description="Previous chargeback count")
    refund_count: Optional[float] = Field(0.0, description="Historical refund count")
    account_status: Optional[str] = Field("ACTIVE", description="Account status e.g. ACTIVE")
    customer_segment: Optional[str] = Field("REGULAR", description="Customer segment tier e.g. REGULAR, VIP")


class OrderWebhookData(BaseModel):
    order_id: str = Field(..., description="Unique order identification code")
    customer_id: Optional[str] = Field(None, description="Linked customer ID")
    product_category: Optional[str] = Field("GENERAL", description="Product category e.g. ELECTRONICS")
    order_amount: Optional[float] = Field(0.0, description="Order total value")
    currency: Optional[str] = Field("INR", description="Three-letter ISO currency code")
    fulfillment_status: Optional[str] = Field("DELIVERED", description="Order fulfillment status")
    cancellation_status: Optional[str] = Field("NONE", description="Cancellation status")
    order_timestamp: Optional[str] = Field(None, description="ISO timestamp of order placement")


class TransactionWebhookData(BaseModel):
    transaction_id: str = Field(..., description="Unique payment transaction ID")
    order_id: Optional[str] = Field(None, description="Linked order ID")
    payment_method: Optional[str] = Field("CREDIT_CARD", description="Payment method e.g. CREDIT_CARD, UPI")
    payment_gateway: Optional[str] = Field("STRIPE", description="Payment gateway e.g. STRIPE, RAZORPAY")
    transaction_status: Optional[str] = Field("CAPTURED", description="Transaction status")
    payment_success: Optional[float] = Field(1.0, description="1.0 for success, 0.0 for failure")
    auth_risk_score: Optional[float] = Field(0.1, description="Authorization risk score")
    velocity_24h: Optional[float] = Field(1.0, description="24h transaction velocity")
    transaction_timestamp: Optional[str] = Field(None, description="ISO timestamp of transaction processing")
    amount: Optional[float] = Field(0.0, description="Transaction amount")


class DisputeWebhookData(BaseModel):
    dispute_id: str = Field(..., description="Unique dispute identification code")
    transaction_id: str = Field(..., description="Associated transaction ID")
    order_id: str = Field(..., description="Associated order ID")
    customer_id: str = Field(..., description="Associated customer ID")
    disputed_amount: float = Field(..., description="Disputed amount")
    currency: str = Field("INR", description="Three-letter ISO currency code")
    dispute_reason_code: str = Field(..., description="Chargeback reason code e.g. 13.1_MERCH_NOT_RECEIVED")
    dispute_category: Optional[str] = Field("FRAUD", description="Dispute category e.g. FRAUD, SERVICE")
    dispute_status: Optional[str] = Field("PENDING_REVIEW", description="Current dispute status")
    dispute_stage: Optional[str] = Field("FIRST_CHARGEBACK", description="Dispute stage")
    dispute_creation_timestamp: Optional[str] = Field(None, description="ISO timestamp when dispute was filed")
    response_deadline: Optional[str] = Field(None, description="ISO deadline for representment response")
    evidence_deadline: Optional[str] = Field(None, description="ISO deadline for submitting evidence")


class DisputeWebhookRequest(BaseModel):
    event_id: str = Field(..., description="Unique gateway event ID used for idempotency")
    event_type: str = Field(..., description="Type of event e.g. dispute.created")
    timestamp: str = Field(..., description="ISO timestamp of webhook generation")
    data_state: Optional[str] = Field("PRODUCTION", description="Data state governance tracking")
    customer: CustomerWebhookData
    order: OrderWebhookData
    transaction: TransactionWebhookData
    dispute: DisputeWebhookData

    @field_validator("data_state")
    @classmethod
    def validate_data_state(cls, v: Optional[str]) -> str:
        return "PRODUCTION"


class WebhookResponseEnvelope(BaseModel):
    status: str = Field(..., description="Outcome status e.g. SUCCESS, IDEMPOTENT_SUCCESS, ERROR, CONFLICT")
    event_id: str = Field(..., description="Gateway event ID")
    dispute_id: Optional[str] = Field(None, description="Created or matched dispute ID")
    message: str = Field(..., description="Human-readable processing message")
    correlation_id: str = Field(..., description="Correlation ID for audit tracing")
    timestamp: str = Field(..., description="ISO response timestamp")
    detail: Optional[Dict[str, Any]] = Field(None, description="Optional payload metadata")
