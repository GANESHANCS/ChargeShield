"""
SQLAlchemy ORM models for ChargeShield persistent review workflow and decision audit log.
"""

from sqlalchemy import Column, String, Float, Integer, Index, ForeignKey
from sqlalchemy.orm import relationship
from backend.db.database import Base

class ReviewStateModel(Base):
    """Stores current review state for each dispute case (survives server restart)."""
    __tablename__ = "review_states"

    dispute_id = Column(String(64), primary_key=True, index=True)
    review_status = Column(String(32), nullable=False, default="PENDING_REVIEW")
    updated_at = Column(String(64), nullable=False)

    def __repr__(self):
        return f"<ReviewStateModel(dispute_id='{self.dispute_id}', status='{self.review_status}')>"


class ReviewDecisionModel(Base):
    """Append-only audit table storing authorized human reviewer decisions."""
    __tablename__ = "review_decisions"
    __table_args__ = (
        Index("ix_decisions_dispute_created", "dispute_id", "created_at"),
        Index("ix_decisions_reviewer_decision", "reviewer_id", "decision"),
    )

    decision_id = Column(String(64), primary_key=True)
    dispute_id = Column(String(64), nullable=False, index=True)
    reviewer_id = Column(String(64), nullable=False, index=True)
    decision = Column(String(32), nullable=False, index=True)
    reason = Column(String(2048), nullable=False)
    ai_recommendation = Column(String(32), nullable=False)
    ai_win_probability = Column(Float, nullable=False)
    verification_rate = Column(Float, nullable=False, default=1.0)
    created_at = Column(String(64), nullable=False, index=True)

    def __repr__(self):
        return f"<ReviewDecisionModel(id='{self.decision_id}', dispute='{self.dispute_id}', decision='{self.decision}')>"


class UserModel(Base):
    """User account table for authentication and RBAC governance."""
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_role_active", "role", "is_active"),
    )

    user_id = Column(String(64), primary_key=True, index=True)
    email = Column(String(128), unique=True, nullable=False, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    hashed_password = Column(String(256), nullable=False)
    role = Column(String(32), nullable=False, default="REVIEWER", index=True)  # ADMIN, ANALYST, REVIEWER, AUDITOR
    full_name = Column(String(128), nullable=False)
    is_active = Column(Float, nullable=False, default=1.0) # 1.0 for active, 0.0 for inactive
    created_at = Column(String(64), nullable=False)

    def __repr__(self):
        return f"<UserModel(user_id='{self.user_id}', username='{self.username}', role='{self.role}')>"

# Alias for backwards compatibility
UserRecord = UserModel


class ModelVersionModel(Base):
    """Registry table tracking ML model version lifecycles."""
    __tablename__ = "model_versions"

    id = Column(String(64), primary_key=True)
    version = Column(String(32), unique=True, nullable=False, index=True)
    algorithm = Column(String(64), nullable=False)
    feature_count = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    lifecycle_status = Column(String(32), nullable=False, index=True)  # DEVELOPMENT, VALIDATION, STAGED, PRODUCTION, RETIRED
    training_timestamp = Column(String(64), nullable=False)
    created_at = Column(String(64), nullable=False)

    def __repr__(self):
        return f"<ModelVersionModel(version='{self.version}', status='{self.lifecycle_status}')>"


class ModelOutcomeModel(Base):
    """Ground-truth dispute outcome records provided by authorized reviewers/admins."""
    __tablename__ = "model_outcomes"
    __table_args__ = (
        Index("ix_outcomes_dispute_state", "dispute_id", "data_state"),
        Index("ix_outcomes_state_created", "data_state", "created_at"),
    )

    outcome_id = Column(String(64), primary_key=True)
    dispute_id = Column(String(64), nullable=False, index=True)
    actual_outcome = Column(String(32), nullable=False, index=True)  # WON, LOST, EXPIRED
    resolution_timestamp = Column(String(64), nullable=False)
    financial_recovery_amount = Column(Float, nullable=True)
    reviewer_id = Column(String(64), nullable=False, index=True)
    justification = Column(String(2048), nullable=False)
    data_state = Column(String(32), nullable=False, default="PRODUCTION", index=True)
    created_at = Column(String(64), nullable=False, index=True)

    def __repr__(self):
        return f"<ModelOutcomeModel(dispute='{self.dispute_id}', outcome='{self.actual_outcome}')>"



class LearningFeedbackModel(Base):
    """Links predictions, human review decisions, and ground-truth outcomes for learning audit."""
    __tablename__ = "learning_feedback"

    feedback_id = Column(String(64), primary_key=True)
    dispute_id = Column(String(64), nullable=False, index=True)
    prediction = Column(String(32), nullable=False)
    human_decision = Column(String(32), nullable=False)
    actual_outcome = Column(String(32), nullable=False)
    eligibility = Column(String(32), nullable=False, index=True)  # ELIGIBLE, INELIGIBLE
    eligibility_reason = Column(String(512), nullable=False)
    created_at = Column(String(64), nullable=False)

    def __repr__(self):
        return f"<LearningFeedbackModel(dispute='{self.dispute_id}', eligibility='{self.eligibility}')>"


class ThresholdEvaluationModel(Base):
    """Stores comparative threshold optimization analysis snapshots."""
    __tablename__ = "threshold_evaluations"

    eval_id = Column(String(64), primary_key=True)
    threshold = Column(Float, nullable=False, index=True)
    precision = Column(Float, nullable=False)
    recall = Column(Float, nullable=False)
    f1_score = Column(Float, nullable=False)
    false_positive_rate = Column(Float, nullable=False)
    false_negative_rate = Column(Float, nullable=False)
    predicted_contests = Column(Float, nullable=False)
    predicted_accepts = Column(Float, nullable=False)
    expected_recovery = Column(Float, nullable=False)
    operational_cost = Column(Float, nullable=False)
    net_financial_advantage = Column(Float, nullable=False)
    created_at = Column(String(64), nullable=False)

    def __repr__(self):
        return f"<ThresholdEvaluationModel(threshold={self.threshold}, net_advantage={self.net_financial_advantage})>"


class ThresholdAuditModel(Base):
    """Immutable audit record for production decision threshold modifications."""
    __tablename__ = "threshold_audits"

    audit_id = Column(String(64), primary_key=True)
    previous_threshold = Column(Float, nullable=False)
    proposed_threshold = Column(Float, nullable=False)
    approved_threshold = Column(Float, nullable=False)
    admin_id = Column(String(64), nullable=False, index=True)
    timestamp = Column(String(64), nullable=False, index=True)
    reason = Column(String(2048), nullable=False)
    evidence_metrics_json = Column(String(4096), nullable=False)

    def __repr__(self):
        return f"<ThresholdAuditModel(audit_id='{self.audit_id}', approved_threshold={self.approved_threshold})>"


class CustomerModel(Base):
    """Stores customer profile, historical order stats, and risk tiering."""
    __tablename__ = "customers"

    customer_id = Column(String(64), primary_key=True, index=True)
    account_creation_date = Column(String(64), nullable=True)
    tenure_days = Column(Float, nullable=True)
    country = Column(String(32), nullable=True)
    total_order_count = Column(Float, nullable=True, default=0.0)
    successful_order_count = Column(Float, nullable=True, default=0.0)
    previous_dispute_count = Column(Float, nullable=True, default=0.0)
    previous_chargeback_count = Column(Float, nullable=True, default=0.0)
    refund_count = Column(Float, nullable=True, default=0.0)
    account_status = Column(String(32), nullable=True, default="ACTIVE")
    customer_segment = Column(String(32), nullable=True)
    data_state = Column(String(32), nullable=False, default="PRODUCTION", index=True)
    created_at = Column(String(64), nullable=False)
    updated_at = Column(String(64), nullable=False)

    orders = relationship("OrderModel", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CustomerModel(id='{self.customer_id}', segment='{self.customer_segment}')>"


class OrderModel(Base):
    """Stores e-commerce order details linked to customer."""
    __tablename__ = "orders"

    order_id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), ForeignKey("customers.customer_id"), nullable=False, index=True)
    product_category = Column(String(64), nullable=True)
    order_amount = Column(Float, nullable=False, default=0.0)
    currency = Column(String(16), nullable=False, default="INR")
    fulfillment_status = Column(String(32), nullable=True)
    cancellation_status = Column(String(32), nullable=True)
    order_timestamp = Column(String(64), nullable=True)
    data_state = Column(String(32), nullable=False, default="PRODUCTION", index=True)
    created_at = Column(String(64), nullable=False)
    updated_at = Column(String(64), nullable=False)

    customer = relationship("CustomerModel", back_populates="orders")
    transactions = relationship("TransactionModel", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<OrderModel(id='{self.order_id}', amount={self.order_amount})>"


class TransactionModel(Base):
    """Stores payment transaction details linked to order."""
    __tablename__ = "transactions"

    transaction_id = Column(String(64), primary_key=True, index=True)
    order_id = Column(String(64), ForeignKey("orders.order_id"), nullable=False, index=True)
    payment_method = Column(String(64), nullable=True)
    payment_gateway = Column(String(64), nullable=True)
    transaction_status = Column(String(32), nullable=True)
    payment_success = Column(Float, nullable=True, default=1.0)
    auth_risk_score = Column(Float, nullable=True)
    velocity_24h = Column(Float, nullable=True)
    transaction_timestamp = Column(String(64), nullable=True)
    amount = Column(Float, nullable=True)
    data_state = Column(String(32), nullable=False, default="PRODUCTION", index=True)
    created_at = Column(String(64), nullable=False)
    updated_at = Column(String(64), nullable=False)

    order = relationship("OrderModel", back_populates="transactions")
    disputes = relationship("DisputeModel", back_populates="transaction", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TransactionModel(id='{self.transaction_id}', gateway='{self.payment_gateway}')>"


class DisputeModel(Base):
    """Authoritative relational dispute/case table."""
    __tablename__ = "disputes"
    __table_args__ = (
        Index("ix_disputes_state_status", "data_state", "dispute_status"),
        Index("ix_disputes_status_created", "dispute_status", "created_at"),
        Index("ix_disputes_state_created", "data_state", "created_at"),
    )

    dispute_id = Column(String(64), primary_key=True, index=True)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    order_id = Column(String(64), ForeignKey("orders.order_id"), nullable=False, index=True)
    customer_id = Column(String(64), ForeignKey("customers.customer_id"), nullable=False, index=True)
    disputed_amount = Column(Float, nullable=False)
    currency = Column(String(16), nullable=False, default="INR")
    dispute_reason_code = Column(String(64), nullable=False)
    dispute_category = Column(String(64), nullable=True)
    dispute_status = Column(String(32), nullable=False, default="PENDING_REVIEW", index=True)
    dispute_stage = Column(String(32), nullable=True)
    dispute_creation_timestamp = Column(String(64), nullable=True)
    response_deadline = Column(String(64), nullable=True)
    evidence_deadline = Column(String(64), nullable=True)
    contest_success = Column(Float, nullable=True)
    final_outcome = Column(String(32), nullable=True)
    settlement_date = Column(String(64), nullable=True)
    data_state = Column(String(32), nullable=False, default="PRODUCTION", index=True)
    created_at = Column(String(64), nullable=False, index=True)
    updated_at = Column(String(64), nullable=False)

    transaction = relationship("TransactionModel", back_populates="disputes")
    order = relationship("OrderModel", foreign_keys=[order_id])
    customer = relationship("CustomerModel", foreign_keys=[customer_id])

    def __repr__(self):
        return f"<DisputeModel(id='{self.dispute_id}', status='{self.dispute_status}')>"


class WebhookEventModel(Base):
    """Audit and idempotency log for payment gateway webhook events."""
    __tablename__ = "webhook_events"
    __table_args__ = (
        Index("ix_webhooks_dispute_state", "dispute_id", "data_state"),
        Index("ix_webhooks_event_received", "event_id", "received_timestamp"),
    )

    event_id = Column(String(128), primary_key=True, index=True)
    event_type = Column(String(64), nullable=False)
    dispute_id = Column(String(64), nullable=True, index=True)
    correlation_id = Column(String(64), nullable=True)
    data_state = Column(String(32), nullable=False, default="PRODUCTION", index=True)
    processing_status = Column(String(32), nullable=False, index=True)  # PROCESSED, DUPLICATE, REJECTED
    payload_hash = Column(String(64), nullable=False)  # SHA-256 hash of payload body
    failure_reason = Column(String(1024), nullable=True)
    received_timestamp = Column(String(64), nullable=False, index=True)

    def __repr__(self):
        return f"<WebhookEventModel(event_id='{self.event_id}', status='{self.processing_status}')>"


class EvidenceDocumentModel(Base):
    """Metadata repository for dispute evidence documents."""
    __tablename__ = "evidence_documents"
    __table_args__ = (
        Index("ix_evidence_dispute_state", "dispute_id", "data_state"),
        Index("ix_evidence_dispute_status", "dispute_id", "status"),
        Index("ix_evidence_hash", "sha256_hash"),
    )

    evidence_id = Column(String(64), primary_key=True, index=True)
    dispute_id = Column(String(64), ForeignKey("disputes.dispute_id"), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    safe_filename = Column(String(255), nullable=False)
    content_type = Column(String(128), nullable=False)
    file_size = Column(Integer, nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    storage_key = Column(String(512), nullable=False)
    uploaded_by = Column(String(128), nullable=False)
    uploaded_at = Column(String(64), nullable=False)
    data_state = Column(String(32), nullable=False, default="PRODUCTION", index=True)
    status = Column(String(32), nullable=False, default="ACTIVE", index=True)
    created_at = Column(String(64), nullable=False)
    updated_at = Column(String(64), nullable=False)

    dispute = relationship("DisputeModel", foreign_keys=[dispute_id])

    def __repr__(self):
        return f"<EvidenceDocumentModel(id='{self.evidence_id}', filename='{self.original_filename}', status='{self.status}')>"

