"""Add evidence_documents table for document upload and storage metadata

Revision ID: 005_evidence_documents
Revises: 004_webhook_events
Create Date: 2026-08-27 23:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '005_evidence_documents'
down_revision: Union[str, None] = '004_webhook_events'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if 'evidence_documents' not in existing_tables:
        op.create_table(
            'evidence_documents',
            sa.Column('evidence_id', sa.String(length=64), nullable=False),
            sa.Column('dispute_id', sa.String(length=64), nullable=False),
            sa.Column('original_filename', sa.String(length=255), nullable=False),
            sa.Column('safe_filename', sa.String(length=255), nullable=False),
            sa.Column('content_type', sa.String(length=128), nullable=False),
            sa.Column('file_size', sa.Integer(), nullable=False),
            sa.Column('sha256_hash', sa.String(length=64), nullable=False),
            sa.Column('storage_key', sa.String(length=512), nullable=False),
            sa.Column('uploaded_by', sa.String(length=128), nullable=False),
            sa.Column('uploaded_at', sa.String(length=64), nullable=False),
            sa.Column('data_state', sa.String(length=32), nullable=False, server_default='PRODUCTION'),
            sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
            sa.Column('created_at', sa.String(length=64), nullable=False),
            sa.Column('updated_at', sa.String(length=64), nullable=False),
            sa.ForeignKeyConstraint(['dispute_id'], ['disputes.dispute_id'], name='fk_evidence_disputes_dispute_id'),
            sa.PrimaryKeyConstraint('evidence_id')
        )
        op.create_index(op.f('ix_evidence_documents_evidence_id'), 'evidence_documents', ['evidence_id'], unique=False)
        op.create_index(op.f('ix_evidence_documents_dispute_id'), 'evidence_documents', ['dispute_id'], unique=False)
        op.create_index(op.f('ix_evidence_documents_sha256_hash'), 'evidence_documents', ['sha256_hash'], unique=False)
        op.create_index(op.f('ix_evidence_documents_data_state'), 'evidence_documents', ['data_state'], unique=False)
        op.create_index(op.f('ix_evidence_documents_status'), 'evidence_documents', ['status'], unique=False)
        op.create_index('ix_evidence_dispute_state', 'evidence_documents', ['dispute_id', 'data_state'], unique=False)
        op.create_index('ix_evidence_dispute_status', 'evidence_documents', ['dispute_id', 'status'], unique=False)
        op.create_index('ix_evidence_hash', 'evidence_documents', ['sha256_hash'], unique=False)

def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if 'evidence_documents' in existing_tables:
        try:
            op.drop_index('ix_evidence_hash', table_name='evidence_documents')
            op.drop_index('ix_evidence_dispute_status', table_name='evidence_documents')
            op.drop_index('ix_evidence_dispute_state', table_name='evidence_documents')
            op.drop_index(op.f('ix_evidence_documents_status'), table_name='evidence_documents')
            op.drop_index(op.f('ix_evidence_documents_data_state'), table_name='evidence_documents')
            op.drop_index(op.f('ix_evidence_documents_sha256_hash'), table_name='evidence_documents')
            op.drop_index(op.f('ix_evidence_documents_dispute_id'), table_name='evidence_documents')
            op.drop_index(op.f('ix_evidence_documents_evidence_id'), table_name='evidence_documents')
        except Exception:
            pass
        op.drop_table('evidence_documents')
