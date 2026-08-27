"""
SQLAlchemy ORM models for ChargeShield persistent review workflow and decision audit log.
"""

from sqlalchemy import Column, String, Float, Index
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

