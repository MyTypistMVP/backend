"""enhance template model with preview and metrics

Revision ID: 202509120002
Revises: 1234567890ab
Create Date: 2025-09-12 00:02:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '202509120002'
down_revision = '1234567890ab'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to templates table
    op.add_column('templates', sa.Column('preview_file_path', sa.String(500), nullable=True))
    op.add_column('templates', sa.Column('token_cost', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('templates', sa.Column('preview_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('templates', sa.Column('preview_to_download_rate', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('templates', sa.Column('average_generation_time', sa.Float(), nullable=True))
    op.add_column('templates', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('templates', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))


def downgrade() -> None:
    # Remove new columns from templates table
    op.drop_column('templates', 'preview_file_path')
    op.drop_column('templates', 'token_cost')
    op.drop_column('templates', 'preview_count')
    op.drop_column('templates', 'preview_to_download_rate')
    op.drop_column('templates', 'average_generation_time')
    op.drop_column('templates', 'created_at')
    op.drop_column('templates', 'updated_at')