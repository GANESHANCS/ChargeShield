"""Add customers, orders, transactions, and disputes entity tables

Revision ID: 003_dispute_entities
Revises: 002_phase13_hardening
Create Date: 2026-08-27 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_dispute_entities'
down_revision: Union[str, None] = '002_phase13_hardening'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # 1. customers table
    if 'customers' not in existing_tables:
        op.create_table(
            'customers',
            sa.Column('customer_id', sa.String(length=64), nullable=False),
            sa.Column('account_creation_date', sa.String(length=64), nullable=True),
            sa.Column('tenure_days', sa.Float(), nullable=True),
            sa.Column('country', sa.String(length=32), nullable=True),
            sa.Column('total_order_count', sa.Float(), nullable=True, server_default='0.0'),
            sa.Column('successful_order_count', sa.Float(), nullable=True, server_default='0.0'),
            sa.Column('previous_dispute_count', sa.Float(), nullable=True, server_default='0.0'),
            sa.Column('previous_chargeback_count', sa.Float(), nullable=True, server_default='0.0'),
            sa.Column('refund_count', sa.Float(), nullable=True, server_default='0.0'),
            sa.Column('account_status', sa.String(length=32), nullable=True, server_default='ACTIVE'),
            sa.Column('customer_segment', sa.String(length=32), nullable=True),
            sa.Column('data_state', sa.String(length=32), nullable=False, server_default='PRODUCTION'),
            sa.Column('created_at', sa.String(length=64), nullable=False),
            sa.Column('updated_at', sa.String(length=64), nullable=False),
            sa.PrimaryKeyConstraint('customer_id')
        )
        op.create_index(op.f('ix_customers_customer_id'), 'customers', ['customer_id'], unique=False)
        op.create_index(op.f('ix_customers_data_state'), 'customers', ['data_state'], unique=False)

    # 2. orders table
    if 'orders' not in existing_tables:
        op.create_table(
            'orders',
            sa.Column('order_id', sa.String(length=64), nullable=False),
            sa.Column('customer_id', sa.String(length=64), nullable=False),
            sa.Column('product_category', sa.String(length=64), nullable=True),
            sa.Column('order_amount', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('currency', sa.String(length=16), nullable=False, server_default='INR'),
            sa.Column('fulfillment_status', sa.String(length=32), nullable=True),
            sa.Column('cancellation_status', sa.String(length=32), nullable=True),
            sa.Column('order_timestamp', sa.String(length=64), nullable=True),
            sa.Column('data_state', sa.String(length=32), nullable=False, server_default='PRODUCTION'),
            sa.Column('created_at', sa.String(length=64), nullable=False),
            sa.Column('updated_at', sa.String(length=64), nullable=False),
            sa.ForeignKeyConstraint(['customer_id'], ['customers.customer_id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('order_id')
        )
        op.create_index(op.f('ix_orders_order_id'), 'orders', ['order_id'], unique=False)
        op.create_index(op.f('ix_orders_customer_id'), 'orders', ['customer_id'], unique=False)
        op.create_index(op.f('ix_orders_data_state'), 'orders', ['data_state'], unique=False)

    # 3. transactions table
    if 'transactions' not in existing_tables:
        op.create_table(
            'transactions',
            sa.Column('transaction_id', sa.String(length=64), nullable=False),
            sa.Column('order_id', sa.String(length=64), nullable=False),
            sa.Column('payment_method', sa.String(length=64), nullable=True),
            sa.Column('payment_gateway', sa.String(length=64), nullable=True),
            sa.Column('transaction_status', sa.String(length=32), nullable=True),
            sa.Column('payment_success', sa.Float(), nullable=True, server_default='1.0'),
            sa.Column('auth_risk_score', sa.Float(), nullable=True),
            sa.Column('velocity_24h', sa.Float(), nullable=True),
            sa.Column('transaction_timestamp', sa.String(length=64), nullable=True),
            sa.Column('amount', sa.Float(), nullable=True),
            sa.Column('data_state', sa.String(length=32), nullable=False, server_default='PRODUCTION'),
            sa.Column('created_at', sa.String(length=64), nullable=False),
            sa.Column('updated_at', sa.String(length=64), nullable=False),
            sa.ForeignKeyConstraint(['order_id'], ['orders.order_id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('transaction_id')
        )
        op.create_index(op.f('ix_transactions_transaction_id'), 'transactions', ['transaction_id'], unique=False)
        op.create_index(op.f('ix_transactions_order_id'), 'transactions', ['order_id'], unique=False)
        op.create_index(op.f('ix_transactions_data_state'), 'transactions', ['data_state'], unique=False)

    # 4. disputes table
    if 'disputes' not in existing_tables:
        op.create_table(
            'disputes',
            sa.Column('dispute_id', sa.String(length=64), nullable=False),
            sa.Column('transaction_id', sa.String(length=64), nullable=False),
            sa.Column('order_id', sa.String(length=64), nullable=False),
            sa.Column('customer_id', sa.String(length=64), nullable=False),
            sa.Column('disputed_amount', sa.Float(), nullable=False),
            sa.Column('currency', sa.String(length=16), nullable=False, server_default='INR'),
            sa.Column('dispute_reason_code', sa.String(length=64), nullable=False),
            sa.Column('dispute_category', sa.String(length=64), nullable=True),
            sa.Column('dispute_status', sa.String(length=32), nullable=False, server_default='PENDING_REVIEW'),
            sa.Column('dispute_stage', sa.String(length=32), nullable=True),
            sa.Column('dispute_creation_timestamp', sa.String(length=64), nullable=True),
            sa.Column('response_deadline', sa.String(length=64), nullable=True),
            sa.Column('evidence_deadline', sa.String(length=64), nullable=True),
            sa.Column('contest_success', sa.Float(), nullable=True),
            sa.Column('final_outcome', sa.String(length=32), nullable=True),
            sa.Column('settlement_date', sa.String(length=64), nullable=True),
            sa.Column('data_state', sa.String(length=32), nullable=False, server_default='PRODUCTION'),
            sa.Column('created_at', sa.String(length=64), nullable=False),
            sa.Column('updated_at', sa.String(length=64), nullable=False),
            sa.ForeignKeyConstraint(['transaction_id'], ['transactions.transaction_id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['order_id'], ['orders.order_id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['customer_id'], ['customers.customer_id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('dispute_id')
        )
        op.create_index(op.f('ix_disputes_dispute_id'), 'disputes', ['dispute_id'], unique=False)
        op.create_index(op.f('ix_disputes_transaction_id'), 'disputes', ['transaction_id'], unique=False)
        op.create_index(op.f('ix_disputes_order_id'), 'disputes', ['order_id'], unique=False)
        op.create_index(op.f('ix_disputes_customer_id'), 'disputes', ['customer_id'], unique=False)
        op.create_index(op.f('ix_disputes_dispute_status'), 'disputes', ['dispute_status'], unique=False)
        op.create_index(op.f('ix_disputes_data_state'), 'disputes', ['data_state'], unique=False)
        op.create_index(op.f('ix_disputes_created_at'), 'disputes', ['created_at'], unique=False)
        op.create_index('ix_disputes_state_status', 'disputes', ['data_state', 'dispute_status'], unique=False)
        op.create_index('ix_disputes_status_created', 'disputes', ['dispute_status', 'created_at'], unique=False)
        op.create_index('ix_disputes_state_created', 'disputes', ['data_state', 'created_at'], unique=False)

def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if 'disputes' in existing_tables:
        try:
            op.drop_index('ix_disputes_state_created', table_name='disputes')
            op.drop_index('ix_disputes_status_created', table_name='disputes')
            op.drop_index('ix_disputes_state_status', table_name='disputes')
            op.drop_index(op.f('ix_disputes_created_at'), table_name='disputes')
            op.drop_index(op.f('ix_disputes_data_state'), table_name='disputes')
            op.drop_index(op.f('ix_disputes_dispute_status'), table_name='disputes')
            op.drop_index(op.f('ix_disputes_customer_id'), table_name='disputes')
            op.drop_index(op.f('ix_disputes_order_id'), table_name='disputes')
            op.drop_index(op.f('ix_disputes_transaction_id'), table_name='disputes')
            op.drop_index(op.f('ix_disputes_dispute_id'), table_name='disputes')
        except Exception:
            pass
        op.drop_table('disputes')

    if 'transactions' in existing_tables:
        try:
            op.drop_index(op.f('ix_transactions_data_state'), table_name='transactions')
            op.drop_index(op.f('ix_transactions_order_id'), table_name='transactions')
            op.drop_index(op.f('ix_transactions_transaction_id'), table_name='transactions')
        except Exception:
            pass
        op.drop_table('transactions')

    if 'orders' in existing_tables:
        try:
            op.drop_index(op.f('ix_orders_data_state'), table_name='orders')
            op.drop_index(op.f('ix_orders_customer_id'), table_name='orders')
            op.drop_index(op.f('ix_orders_order_id'), table_name='orders')
        except Exception:
            pass
        op.drop_table('orders')

    if 'customers' in existing_tables:
        try:
            op.drop_index(op.f('ix_customers_data_state'), table_name='customers')
            op.drop_index(op.f('ix_customers_customer_id'), table_name='customers')
        except Exception:
            pass
        op.drop_table('customers')
