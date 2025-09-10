"""add document sharing and version control

Revision ID: 1234567890ab
Revises: 
Create Date: 2025-09-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1234567890ab'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create document_shares table
    op.create_table('document_shares',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('shared_by', sa.Integer(), nullable=False),
        sa.Column('share_token', sa.String(length=100), nullable=False),
        sa.Column('share_password', sa.String(length=255), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('max_views', sa.Integer(), nullable=True),
        sa.Column('current_views', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_accessed', sa.DateTime(), nullable=True),
        sa.Column('access_log', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['shared_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_shares_document_id'), 'document_shares', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_shares_share_token'), 'document_shares', ['share_token'], unique=True)
    op.create_index(op.f('ix_document_shares_shared_by'), 'document_shares', ['shared_by'], unique=False)
    op.create_index(op.f('ix_document_shares_expires_at'), 'document_shares', ['expires_at'], unique=False)

    # Create document_versions table
    op.create_table('document_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('placeholder_data', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('changed_by', sa.Integer(), nullable=False),
        sa.Column('change_type', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('generation_time', sa.Integer(), nullable=True),
        sa.Column('estimated_time_saved', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_versions_document_id'), 'document_versions', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_versions_changed_by'), 'document_versions', ['changed_by'], unique=False)
    op.create_index(op.f('ix_document_versions_version_number'), 'document_versions', ['version_number'], unique=False)
    op.create_index(op.f('ix_document_versions_created_at'), 'document_versions', ['created_at'], unique=False)
    op.create_index(op.f('ix_document_versions_is_current'), 'document_versions', ['is_current'], unique=False)


def downgrade() -> None:
    # Drop document_versions table
    op.drop_index(op.f('ix_document_versions_is_current'), table_name='document_versions')
    op.drop_index(op.f('ix_document_versions_created_at'), table_name='document_versions')
    op.drop_index(op.f('ix_document_versions_version_number'), table_name='document_versions')
    op.drop_index(op.f('ix_document_versions_changed_by'), table_name='document_versions')
    op.drop_index(op.f('ix_document_versions_document_id'), table_name='document_versions')
    op.drop_table('document_versions')

    # Drop document_shares table
    op.drop_index(op.f('ix_document_shares_expires_at'), table_name='document_shares')
    op.drop_index(op.f('ix_document_shares_shared_by'), table_name='document_shares')
    op.drop_index(op.f('ix_document_shares_share_token'), table_name='document_shares')
    op.drop_index(op.f('ix_document_shares_document_id'), table_name='document_shares')
    op.drop_table('document_shares')
