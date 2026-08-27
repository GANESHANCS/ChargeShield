"""
Authoritative Constants and Enums for ChargeShield Data Governance, Security, and Workflows.
"""

from enum import Enum


class DataState(str, Enum):
    """Authoritative Data State governance enum. Prevents cross-contamination."""
    PRODUCTION = "PRODUCTION"
    SIMULATION = "SIMULATION"
    HISTORICAL = "HISTORICAL"


class UserRole(str, Enum):
    """Authoritative Role-Based Access Control (RBAC) roles."""
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    REVIEWER = "REVIEWER"
    AUDITOR = "AUDITOR"


class ReviewStatus(str, Enum):
    """Authoritative case workflow review status states."""
    PENDING_REVIEW = "PENDING_REVIEW"
    IN_REVIEW = "IN_REVIEW"
    DECIDED = "DECIDED"
    ESCALATED = "ESCALATED"


class DecisionType(str, Enum):
    """Authoritative human reviewer decision choices."""
    CONTEST = "CONTEST"
    DO_NOT_CONTEST = "DO_NOT_CONTEST"
    ESCALATE = "ESCALATE"


class OutcomeType(str, Enum):
    """Authoritative ground-truth dispute outcomes."""
    WON = "WON"
    LOST = "LOST"
    EXPIRED = "EXPIRED"
