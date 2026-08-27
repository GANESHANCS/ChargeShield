"""Initial Phase 8 review_states and review_decisions tables

Revision ID: 001_initial_phase8
Revises: 
Create Date: 2026-08-22 18:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_phase8'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'review_states',
        sa.Column('dispute_id', sa.String(length=64), nullable=False),
        sa.Column('review_status', sa.String(length=32), nullable=False, server_default='PENDING_REVIEW'),
        sa.Column('updated_at', sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint('dispute_id')
    )
    op.create_index(op.f('ix_review_states_dispute_id'), 'review_states', ['dispute_id'], unique=False)

    op.create_table(
        'review_decisions',
        sa.Column('decision_id', sa.String(length=64), nullable=False),
        sa.Column('dispute_id', sa.String(length=64), nullable=False),
        sa.Column('reviewer_id', sa.String(length=64), nullable=False),
        sa.Column('decision', sa.String(length=32), nullable=False),
        sa.Column('reason', sa.String(length=2048), nullable=False),
        sa.Column('ai_recommendation', sa.String(length=32), nullable=False),
        sa.Column('ai_win_probability', sa.Float(), nullable=False),
        sa.Column('verification_rate', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint('decision_id')
    )
    op.create_index(op.f('ix_review_decisions_dispute_id'), 'review_decisions', ['dispute_id'], unique=False)
    op.create_index(op.f('ix_review_decisions_reviewer_id'), 'review_decisions', ['reviewer_id'], unique=False)
    op.create_index(op.f('ix_review_decisions_decision'), 'review_decisions', ['decision'], unique=False)
    op.create_index(op.f('ix_review_decisions_created_at'), 'review_decisions', ['created_at'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_review_decisions_created_at'), table_name='review_decisions')
    op.drop_index(op.f('ix_review_decisions_decision'), table_name='review_decisions')
    op.drop_index(op.f('ix_review_decisions_reviewer_id'), table_name='review_decisions')
    op.drop_index(op.f('ix_review_decisions_dispute_id'), table_name='review_decisions')
    op.drop_table('review_decisions')
    op.drop_index(op.f('ix_review_states_dispute_id'), table_name='review_states')
    op.drop_table('review_states')
