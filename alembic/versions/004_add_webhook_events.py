"""Add webhook_events table for idempotency and audit tracking

Revision ID: 004_webhook_events
Revises: 003_dispute_entities
Create Date: 2026-08-27 23:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004_webhook_events'
down_revision: Union[str, None] = '003_dispute_entities'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if 'webhook_events' not in existing_tables:
        op.create_table(
            'webhook_events',
            sa.Column('event_id', sa.String(length=128), nullable=False),
            sa.Column('event_type', sa.String(length=64), nullable=False),
            sa.Column('dispute_id', sa.String(length=64), nullable=True),
            sa.Column('correlation_id', sa.String(length=64), nullable=True),
            sa.Column('data_state', sa.String(length=32), nullable=False, server_default='PRODUCTION'),
            sa.Column('processing_status', sa.String(length=32), nullable=False),
            sa.Column('payload_hash', sa.String(length=64), nullable=False),
            sa.Column('failure_reason', sa.String(length=1024), nullable=True),
            sa.Column('received_timestamp', sa.String(length=64), nullable=False),
            sa.PrimaryKeyConstraint('event_id')
        )
        op.create_index(op.f('ix_webhook_events_event_id'), 'webhook_events', ['event_id'], unique=False)
        op.create_index(op.f('ix_webhook_events_dispute_id'), 'webhook_events', ['dispute_id'], unique=False)
        op.create_index(op.f('ix_webhook_events_data_state'), 'webhook_events', ['data_state'], unique=False)
        op.create_index(op.f('ix_webhook_events_processing_status'), 'webhook_events', ['processing_status'], unique=False)
        op.create_index(op.f('ix_webhook_events_received_timestamp'), 'webhook_events', ['received_timestamp'], unique=False)
        op.create_index('ix_webhooks_dispute_state', 'webhook_events', ['dispute_id', 'data_state'], unique=False)
        op.create_index('ix_webhooks_event_received', 'webhook_events', ['event_id', 'received_timestamp'], unique=False)

def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if 'webhook_events' in existing_tables:
        try:
            op.drop_index('ix_webhooks_event_received', table_name='webhook_events')
            op.drop_index('ix_webhooks_dispute_state', table_name='webhook_events')
            op.drop_index(op.f('ix_webhook_events_received_timestamp'), table_name='webhook_events')
            op.drop_index(op.f('ix_webhook_events_processing_status'), table_name='webhook_events')
            op.drop_index(op.f('ix_webhook_events_data_state'), table_name='webhook_events')
            op.drop_index(op.f('ix_webhook_events_dispute_id'), table_name='webhook_events')
            op.drop_index(op.f('ix_webhook_events_event_id'), table_name='webhook_events')
        except Exception:
            pass
        op.drop_table('webhook_events')
