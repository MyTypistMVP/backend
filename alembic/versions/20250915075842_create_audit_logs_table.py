"""create_audit_logs_table

Revision ID: 20250915075842
Revises: d1f848efafdf
Create Date: 2025-09-15 07:58:42.514427

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250915075842'
down_revision = 'd1f848efafdf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create audit_logs table"""
    # Create audit event type enum
    op.execute("CREATE TYPE auditeventtype AS ENUM (" +
              "'login', 'logout', 'login_failed', 'password_change', 'password_reset', " +
              "'registration_successful', 'registration_failed', 'user_registered', " +
              "'user_login', 'user_logout', 'password_changed', 'password_change_failed', " +
              "'password_reset_requested', 'email_verified', 'verification_resent', " +
              "'user_created', 'user_updated', 'user_deleted', 'user_suspended', " +
              "'user_activated', 'profile_updated', 'settings_updated', " +
              "'user_status_changed', 'user_role_changed', 'user_hard_deleted', " +
              "'user_soft_deleted', 'document_created', 'document_viewed', " +
              "'document_updated', 'document_deleted', 'document_shared', " +
              "'document_downloaded', 'document_generated', 'document_generation_failed', " +
              "'batch_generated', 'batch_generation_completed', 'batch_generation_failed', " +
              "'shared_document_accessed', 'document_auto_deleted', " +
              "'thumbnail_generation_failed', 'template_created', 'template_updated', " +
              "'template_deleted', 'template_used', 'template_downloaded', " +
              "'template_rated', 'template_status_changed', 'template_visibility_changed', " +
              "'signature_added', 'signature_verified', 'signature_rejected', " +
              "'signature_updated', 'system_startup', 'system_shutdown', " +
              "'unhandled_exception', 'slow_request', 'webhook_processed', " +
              "'webhook_processing_failed', 'webhook_processing_error', " +
              "'system_health_check', 'database_optimized', 'database_optimization_failed', " +
              "'database_backup_created', 'database_backup_failed', " +
              "'database_backup_error', 'maintenance_mode_changed', " +
              "'orphaned_files_cleanup', 'system_backup_created', " +
              "'audit_logs_cleaned', 'audit_log_cleanup_failed', " +
              "'expired_documents_cleaned', 'expired_document_cleanup_failed', " +
              "'unused_files_cleaned', 'unused_file_cleanup_failed', " +
              "'old_visits_cleaned', 'visit_cleanup_failed', 'old_backups_cleaned', " +
              "'backup_cleanup_failed', 'temporary_files_cleaned', " +
              "'cleanup_failed', 'storage_optimized', 'storage_optimization_failed', " +
              "'analytics_exported', 'visit_deleted', 'analytics_anonymized', " +
              "'gdpr_request', 'data_export', 'data_deletion', " +
              "'consent_given', 'consent_withdrawn'" +
              ")")
    
    # Create audit level enum  
    op.execute("CREATE TYPE auditlevel AS ENUM ('info', 'warning', 'error', 'critical')")
    
    # Create the audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        
        # Event information
        sa.Column('event_type', sa.Enum('auditeventtype', name='auditeventtype'), nullable=False, index=True),
        sa.Column('event_level', sa.Enum('auditlevel', name='auditlevel'), nullable=False, server_default='info'),
        sa.Column('event_message', sa.Text(), nullable=False),
        sa.Column('event_details', sa.JSON(), nullable=True),
        
        # User and session information
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True, index=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('request_id', sa.String(100), nullable=True),
        
        # Request information
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_method', sa.String(10), nullable=True),
        sa.Column('request_path', sa.String(500), nullable=True),
        sa.Column('request_params', sa.JSON(), nullable=True),
        sa.Column('response_status', sa.Integer(), nullable=True),
        
        # Resource information
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('resource_name', sa.String(255), nullable=True),
        
        # Geographic information
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('latitude', sa.String(20), nullable=True),
        sa.Column('longitude', sa.String(20), nullable=True),
        
        # Compliance and security
        sa.Column('gdpr_relevant', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('pii_accessed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sensitive_operation', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('requires_retention', sa.Boolean(), nullable=False, server_default='true'),
        
        # Risk assessment
        sa.Column('risk_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('anomaly_detected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('automated_response', sa.String(100), nullable=True),
        
        # Processing information
        sa.Column('processing_time', sa.Float(), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        
        # Metadata
        sa.Column('environment', sa.String(20), nullable=False, server_default="'development'"),
        sa.Column('service_version', sa.String(20), nullable=True),
        sa.Column('correlation_id', sa.String(100), nullable=True),
        
        # Timestamps
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )


def downgrade() -> None:
    """Drop audit_logs table"""
    op.drop_table('audit_logs')
    op.execute("DROP TYPE IF EXISTS auditeventtype")
    op.execute("DROP TYPE IF EXISTS auditlevel")
