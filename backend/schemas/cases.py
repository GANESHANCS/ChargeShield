"""
Pydantic API Schemas for Risk Case list, detail, and nested operational entities.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DisputeMetadata(BaseModel):
    dispute_id: str
    transaction_id: str
    order_id: str
    customer_id: str
    dispute_creation_timestamp: str
    dispute_reason_code: str
    dispute_category: str
    disputed_amount: float
    currency: str = "INR"
    dispute_status: str
    response_deadline: str
    evidence_deadline: str
    dispute_stage: str

class CustomerMetadata(BaseModel):
    customer_id: str
    account_creation_date: str
    tenure_days: int
    country: str
    total_order_count: int
    successful_order_count: int
    previous_dispute_count: int
    previous_chargeback_count: int
    refund_count: int
    account_status: str
    customer_segment: str

class TransactionMetadata(BaseModel):
    transaction_id: str
    customer_id: str
    order_id: str
    transaction_timestamp: str
    amount: float
    currency: str = "INR"
    payment_method: str
    transaction_status: str
    payment_success: bool
    auth_risk_score: float
    velocity_24h: int
    device_fingerprint_match: bool
    ip_country_match: bool

class OrderMetadata(BaseModel):
    order_id: str
    customer_id: str
    order_timestamp: str
    product_category: str
    order_amount: float
    fulfillment_status: str
    cancellation_status: str
    refund_status: str
    is_digital_item: bool

class DeliveryMetadata(BaseModel):
    delivery_id: str
    order_id: str
    shipment_timestamp: Optional[str] = None
    delivery_timestamp: Optional[str] = None
    delivery_status: str
    carrier: str
    tracking_available: bool
    pod_signature_present: bool
    delivery_location_match: bool
    fulfillment_anomaly: bool

class CommunicationItem(BaseModel):
    communication_id: str
    customer_id: str
    order_id: str
    dispute_id: Optional[str] = None
    timestamp: str
    channel: str
    category: str
    resolution_status: str
    summary_text: str

class PreviousDisputeItem(BaseModel):
    previous_dispute_id: str
    customer_id: str
    current_dispute_id: str
    historical_reason_code: str
    historical_outcome: str
    resolution_days: int

class CaseSummary(BaseModel):
    dispute_id: str
    customer_id: str
    order_id: str
    transaction_id: str
    disputed_amount: float
    currency: str = "INR"
    dispute_reason_code: str
    dispute_category: str
    dispute_status: str
    dispute_creation_timestamp: str
    response_deadline: str
    win_probability: float
    recommendation: str
    priority: str = Field(description="CRITICAL, HIGH, MEDIUM, or LOW derived operational priority")
    priority_reasoning: Optional[str] = None
    financial_impact: Optional[Dict[str, Any]] = None
    risk_classification: Optional[Dict[str, Any]] = None

class CaseListResponse(BaseModel):
    items: List[CaseSummary]
    page: int
    page_size: int
    total: int
    total_pages: int

class CaseDetailResponse(BaseModel):
    dispute_id: str
    dispute: DisputeMetadata
    customer: CustomerMetadata
    transaction: TransactionMetadata
    order: OrderMetadata
    delivery: DeliveryMetadata
    communications: List[CommunicationItem]
    previous_disputes: List[PreviousDisputeItem]
    prediction: Dict[str, Any]
    priority: str
    priority_reasoning: Optional[str] = None
    financial_impact: Optional[Dict[str, Any]] = None
    risk_classification: Optional[Dict[str, Any]] = None
    executive_explanation: Optional[str] = None
    technical_shap: Optional[Dict[str, Any]] = None
    decision_simulation: Optional[Dict[str, Any]] = None
    data_quality_info: Optional[Dict[str, Any]] = None
    is_synthetic_data: bool = True

