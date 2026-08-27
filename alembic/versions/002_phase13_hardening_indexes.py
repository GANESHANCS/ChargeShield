"""Phase 13 production hardening indexes and table governance

Revision ID: 002_phase13_hardening
Revises: 001_initial_phase8
Create Date: 2026-08-27 21:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_phase13_hardening'
down_revision: Union[str, None] = '001_initial_phase8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add compound indexes to review_decisions
    op.create_index('ix_decisions_dispute_created', 'review_decisions', ['dispute_id', 'created_at'], unique=False)
    op.create_index('ix_decisions_reviewer_decision', 'review_decisions', ['reviewer_id', 'decision'], unique=False)

    # Add compound indexes to users table if exists
    try:
        op.create_index('ix_users_role_active', 'users', ['role', 'is_active'], unique=False)
    except Exception:
        pass

    # Add compound indexes to model_outcomes if exists
    try:
        op.create_index('ix_outcomes_dispute_state', 'model_outcomes', ['dispute_id', 'data_state'], unique=False)
        op.create_index('ix_outcomes_state_created', 'model_outcomes', ['data_state', 'created_at'], unique=False)
    except Exception:
        pass

def downgrade() -> None:
    try:
        op.drop_index('ix_outcomes_state_created', table_name='model_outcomes')
        op.drop_index('ix_outcomes_dispute_state', table_name='model_outcomes')
    except Exception:
        pass

    try:
        op.drop_index('ix_users_role_active', table_name='users')
    except Exception:
        pass

    op.drop_index('ix_decisions_reviewer_decision', table_name='review_decisions')
    op.drop_index('ix_decisions_dispute_created', table_name='review_decisions')
