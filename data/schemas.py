"""
ChargeShield Synthetic Data Schemas & Data Dictionary Definitions.

Categorizes all entity fields into:
- PRE_TRIAGE: Available at prediction time for ML feature engineering
- POST_OUTCOME: Known only after resolution (BARRED from ML features to prevent leakage)
- TARGET: The dispute contestability outcome label (contest_success)
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

class FieldCategory(str, Enum):
    PRE_TRIAGE = "pre_triage"       # Allowed ML feature
    POST_OUTCOME = "post_outcome"   # Post-resolution field (Leakage risk!)
    TARGET = "target"               # Outcome label (contest_success)
    IDENTIFIER = "identifier"       # Entity ID / FK

class CustomerSchema(BaseModel):
    customer_id: str = Field(description="Unique synthetic customer identifier")
    account_creation_date: str = Field(description="Customer signup timestamp (ISO 8601)")
    tenure_days: int = Field(description="Customer account tenure in days at time of order")
    country: str = Field(description="Customer primary country code (e.g. IN, US, AE)")
    total_order_count: int = Field(description="Total historical orders placed by customer")
    successful_order_count: int = Field(description="Total completed orders without disputes/returns")
    previous_dispute_count: int = Field(description="Total chargebacks/disputes previously filed by customer")
    previous_chargeback_count: int = Field(description="Total chargebacks lost by merchant for this customer")
    refund_count: int = Field(description="Total voluntary merchant refunds issued to customer")
    account_status: str = Field(description="Customer account standing: ACTIVE, DORMANT, FLAGGED")
    customer_segment: str = Field(description="Merchant customer tier: VIP, REGULAR, NEW, HIGH_RISK")

class OrderSchema(BaseModel):
    order_id: str = Field(description="Unique synthetic order identifier")
    customer_id: str = Field(description="FK referencing customers.customer_id")
    order_timestamp: str = Field(description="Order placement timestamp (ISO 8601)")
    product_category: str = Field(description="Product category: ELECTRONICS, FASHION, DIGITAL_GOODS, HOME, BEAUTY")
    order_amount: float = Field(description="Order monetary value in INR (₹)")
    fulfillment_status: str = Field(description="Order fulfillment status: FULFILLED, PENDING, CANCELLED, PARTIAL")
    cancellation_status: str = Field(description="Cancellation state: NONE, CUSTOMER_CANCELLED, MERCHANT_CANCELLED")
    refund_status: str = Field(description="Refund status: NONE, FULL_REFUND, PARTIAL_REFUND")
    is_digital_item: bool = Field(description="Whether order contains non-physical digital goods")

class TransactionSchema(BaseModel):
    transaction_id: str = Field(description="Unique synthetic payment transaction identifier")
    customer_id: str = Field(description="FK referencing customers.customer_id")
    order_id: str = Field(description="FK referencing orders.order_id")
    transaction_timestamp: str = Field(description="Payment processing timestamp (ISO 8601)")
    amount: float = Field(description="Transaction amount in INR (₹)")
    currency: str = Field(description="Currency code: INR")
    payment_method: str = Field(description="Payment category: UPI, CREDIT_CARD, DEBIT_CARD, NET_BANKING, WALLET")
    transaction_status: str = Field(description="Gateway transaction state: CAPTURED, FAILED, PENDING")
    payment_success: bool = Field(description="Whether transaction was successfully captured")
    auth_risk_score: float = Field(description="Gateway payment risk score (0-100)")
    velocity_24h: int = Field(description="Number of transactions by customer in past 24 hours")
    device_fingerprint_match: bool = Field(description="Whether transaction device matches customer history")
    ip_country_match: bool = Field(description="Whether IP country matches billing address country")

class DeliverySchema(BaseModel):
    delivery_id: str = Field(description="Unique synthetic delivery tracking record ID")
    order_id: str = Field(description="FK referencing orders.order_id")
    shipment_timestamp: Optional[str] = Field(None, description="Package dispatch timestamp (ISO 8601)")
    delivery_timestamp: Optional[str] = Field(None, description="Package delivery timestamp (ISO 8601)")
    delivery_status: str = Field(description="Delivery state: DELIVERED, IN_TRANSIT, RETURNED, FAILED, NOT_APPLICABLE")
    carrier: str = Field(description="Logistics carrier: BLUEDART, DELHIVERY, FEDEX, EKART, NONE")
    tracking_available: bool = Field(description="Whether active tracking number exists")
    pod_signature_present: bool = Field(description="Whether Proof of Delivery signature was captured")
    delivery_location_match: bool = Field(description="Whether delivery address matched billing address")
    fulfillment_anomaly: bool = Field(description="Whether shipping exception occurred (e.g. wrong address)")

class DisputeSchema(BaseModel):
    dispute_id: str = Field(description="Unique synthetic dispute record ID")
    transaction_id: str = Field(description="FK referencing transactions.transaction_id")
    order_id: str = Field(description="FK referencing orders.order_id")
    customer_id: str = Field(description="FK referencing customers.customer_id")
    dispute_creation_timestamp: str = Field(description="Dispute filing timestamp by card issuer (ISO 8601)")
    dispute_reason_code: str = Field(description="Reason code: 13.1_MERCH_NOT_RECEIVED, 10.4_UNAUTHORIZED, 13.3_NOT_AS_DESCRIBED, 12.6_DUPLICATE, 13.6_CREDIT_NOT_PROCESSED")
    dispute_category: str = Field(description="Dispute category: NON_RECEIPT, FRAUD, QUALITY, PROCESSING, CREDIT")
    disputed_amount: float = Field(description="Disputed monetary value in INR (₹)")
    dispute_status: str = Field(description="Current dispute stage: NEW, UNDER_REVIEW, CLOSED")
    response_deadline: str = Field(description="Merchant evidence submission deadline (ISO 8601)")
    evidence_deadline: str = Field(description="Internal evidence gathering target deadline (ISO 8601)")
    dispute_stage: str = Field(description="Dispute stage: FIRST_DISPUTE, PRE_ARBITRATION")
    
    # Target variable (Ground truth contestability label)
    contest_success: int = Field(description="TARGET: 1 if merchant won dispute contest, 0 if lost")
    
    # Post-outcome fields (BARRED from pre-triage ML features)
    final_outcome: str = Field(description="POST_OUTCOME: Final resolution state: WON, LOST")
    settlement_date: Optional[str] = Field(None, description="POST_OUTCOME: Bank settlement timestamp")

class CommunicationSchema(BaseModel):
    communication_id: str = Field(description="Unique synthetic support communication ID")
    customer_id: str = Field(description="FK referencing customers.customer_id")
    order_id: str = Field(description="FK referencing orders.order_id")
    dispute_id: Optional[str] = Field(None, description="FK referencing disputes.dispute_id if linked")
    timestamp: str = Field(description="Communication timestamp (ISO 8601)")
    channel: str = Field(description="Communication channel: EMAIL, CHAT, PHONE, TICKET")
    category: str = Field(description="Support topic: ORDER_INQUIRY, REFUND_REQUEST, DELIVERY_UPDATE, COMPLAINT")
    resolution_status: str = Field(description="Ticket resolution status: RESOLVED, OPEN, ESCALATED")
    summary_text: str = Field(description="Synthetic communication summary for evidence retrieval")

class PreviousDisputeSchema(BaseModel):
    previous_dispute_id: str = Field(description="Unique historical dispute record ID")
    customer_id: str = Field(description="FK referencing customers.customer_id")
    current_dispute_id: str = Field(description="FK referencing current disputes.dispute_id")
    historical_reason_code: str = Field(description="Historical dispute reason code")
    historical_outcome: str = Field(description="Historical outcome: WON, LOST")
    resolution_days: int = Field(description="Number of days taken to resolve historical dispute")

# Feature Availability Mapping for Leakage Prevention
DATA_DICTIONARY: Dict[str, Dict[str, FieldCategory]] = {
    "customers": {
        "customer_id": FieldCategory.IDENTIFIER,
        "account_creation_date": FieldCategory.PRE_TRIAGE,
        "tenure_days": FieldCategory.PRE_TRIAGE,
        "country": FieldCategory.PRE_TRIAGE,
        "total_order_count": FieldCategory.PRE_TRIAGE,
        "successful_order_count": FieldCategory.PRE_TRIAGE,
        "previous_dispute_count": FieldCategory.PRE_TRIAGE,
        "previous_chargeback_count": FieldCategory.PRE_TRIAGE,
        "refund_count": FieldCategory.PRE_TRIAGE,
        "account_status": FieldCategory.PRE_TRIAGE,
        "customer_segment": FieldCategory.PRE_TRIAGE,
    },
    "orders": {
        "order_id": FieldCategory.IDENTIFIER,
        "customer_id": FieldCategory.IDENTIFIER,
        "order_timestamp": FieldCategory.PRE_TRIAGE,
        "product_category": FieldCategory.PRE_TRIAGE,
        "order_amount": FieldCategory.PRE_TRIAGE,
        "fulfillment_status": FieldCategory.PRE_TRIAGE,
        "cancellation_status": FieldCategory.PRE_TRIAGE,
        "refund_status": FieldCategory.PRE_TRIAGE,
        "is_digital_item": FieldCategory.PRE_TRIAGE,
    },
    "transactions": {
        "transaction_id": FieldCategory.IDENTIFIER,
        "customer_id": FieldCategory.IDENTIFIER,
        "order_id": FieldCategory.IDENTIFIER,
        "transaction_timestamp": FieldCategory.PRE_TRIAGE,
        "amount": FieldCategory.PRE_TRIAGE,
        "currency": FieldCategory.PRE_TRIAGE,
        "payment_method": FieldCategory.PRE_TRIAGE,
        "transaction_status": FieldCategory.PRE_TRIAGE,
        "payment_success": FieldCategory.PRE_TRIAGE,
        "auth_risk_score": FieldCategory.PRE_TRIAGE,
        "velocity_24h": FieldCategory.PRE_TRIAGE,
        "device_fingerprint_match": FieldCategory.PRE_TRIAGE,
        "ip_country_match": FieldCategory.PRE_TRIAGE,
    },
    "deliveries": {
        "delivery_id": FieldCategory.IDENTIFIER,
        "order_id": FieldCategory.IDENTIFIER,
        "shipment_timestamp": FieldCategory.PRE_TRIAGE,
        "delivery_timestamp": FieldCategory.PRE_TRIAGE,
        "delivery_status": FieldCategory.PRE_TRIAGE,
        "carrier": FieldCategory.PRE_TRIAGE,
        "tracking_available": FieldCategory.PRE_TRIAGE,
        "pod_signature_present": FieldCategory.PRE_TRIAGE,
        "delivery_location_match": FieldCategory.PRE_TRIAGE,
        "fulfillment_anomaly": FieldCategory.PRE_TRIAGE,
    },
    "disputes": {
        "dispute_id": FieldCategory.IDENTIFIER,
        "transaction_id": FieldCategory.IDENTIFIER,
        "order_id": FieldCategory.IDENTIFIER,
        "customer_id": FieldCategory.IDENTIFIER,
        "dispute_creation_timestamp": FieldCategory.PRE_TRIAGE,
        "dispute_reason_code": FieldCategory.PRE_TRIAGE,
        "dispute_category": FieldCategory.PRE_TRIAGE,
        "disputed_amount": FieldCategory.PRE_TRIAGE,
        "dispute_status": FieldCategory.PRE_TRIAGE,
        "response_deadline": FieldCategory.PRE_TRIAGE,
        "evidence_deadline": FieldCategory.PRE_TRIAGE,
        "dispute_stage": FieldCategory.PRE_TRIAGE,
        "contest_success": FieldCategory.TARGET,
        "final_outcome": FieldCategory.POST_OUTCOME,
        "settlement_date": FieldCategory.POST_OUTCOME,
    },
    "communications": {
        "communication_id": FieldCategory.IDENTIFIER,
        "customer_id": FieldCategory.IDENTIFIER,
        "order_id": FieldCategory.IDENTIFIER,
        "dispute_id": FieldCategory.IDENTIFIER,
        "timestamp": FieldCategory.PRE_TRIAGE,
        "channel": FieldCategory.PRE_TRIAGE,
        "category": FieldCategory.PRE_TRIAGE,
        "resolution_status": FieldCategory.PRE_TRIAGE,
        "summary_text": FieldCategory.PRE_TRIAGE,
    },
    "previous_disputes": {
        "previous_dispute_id": FieldCategory.IDENTIFIER,
        "customer_id": FieldCategory.IDENTIFIER,
        "current_dispute_id": FieldCategory.IDENTIFIER,
        "historical_reason_code": FieldCategory.PRE_TRIAGE,
        "historical_outcome": FieldCategory.PRE_TRIAGE,
        "resolution_days": FieldCategory.PRE_TRIAGE,
    }
}
