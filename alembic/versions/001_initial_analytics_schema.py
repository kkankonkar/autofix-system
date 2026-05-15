"""Initial analytics schema

Revision ID: 001
Revises: 
Create Date: 2026-05-14 15:52:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create analytics_events table
    op.create_table(
        'analytics_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.Enum('review', 'updatedocs', 'analyzeimpact', 'implementfix', name='eventtype'), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('github_type', sa.String(length=20), nullable=False),
        sa.Column('github_number', sa.Integer(), nullable=False),
        sa.Column('github_title', sa.String(length=500), nullable=False),
        sa.Column('github_url', sa.String(length=500), nullable=False),
        sa.Column('github_repository', sa.String(length=200), nullable=False),
        sa.Column('github_author', sa.String(length=100), nullable=False),
        sa.Column('github_labels', sa.JSON(), nullable=True),
        sa.Column('cost_coins_used', sa.Float(), nullable=False),
        sa.Column('cost_dollars_used', sa.Float(), nullable=False),
        sa.Column('cost_operation', sa.String(length=100), nullable=False),
        sa.Column('metadata_triggered_by', sa.String(length=100), nullable=False),
        sa.Column('metadata_duration', sa.Integer(), nullable=True),
        sa.Column('metadata_status', sa.Enum('success', 'failure', 'partial', name='status'), nullable=False),
        sa.Column('metadata_workflow_run_id', sa.String(length=100), nullable=True),
        sa.Column('metadata_workflow_run_url', sa.String(length=500), nullable=True),
        sa.Column('metadata_fixium_version', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4'
    )
    op.create_index('idx_event_type', 'analytics_events', ['event_type'])
    op.create_index('idx_timestamp', 'analytics_events', ['timestamp'])
    op.create_index('idx_repository', 'analytics_events', ['github_repository'])
    op.create_index('idx_github_number', 'analytics_events', ['github_number'])

    # Create review_details table
    op.create_table(
        'review_details',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('total_findings', sa.Integer(), nullable=False),
        sa.Column('critical_count', sa.Integer(), nullable=False),
        sa.Column('high_count', sa.Integer(), nullable=False),
        sa.Column('medium_count', sa.Integer(), nullable=False),
        sa.Column('low_count', sa.Integer(), nullable=False),
        sa.Column('findings_by_severity', sa.JSON(), nullable=True),
        sa.Column('files_reviewed', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['analytics_events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4'
    )
    op.create_index('idx_review_event_id', 'review_details', ['event_id'])

    # Create documentation_details table
    op.create_table(
        'documentation_details',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('files_analyzed', sa.Integer(), nullable=False),
        sa.Column('suggestions_count', sa.Integer(), nullable=False),
        sa.Column('high_priority_count', sa.Integer(), nullable=False),
        sa.Column('medium_priority_count', sa.Integer(), nullable=False),
        sa.Column('low_priority_count', sa.Integer(), nullable=False),
        sa.Column('documentation_files', sa.JSON(), nullable=True),
        sa.Column('suggestions', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['analytics_events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4'
    )
    op.create_index('idx_doc_event_id', 'documentation_details', ['event_id'])

    # Create impact_details table
    op.create_table(
        'impact_details',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.Enum('low', 'medium', 'medium-high', 'high', 'critical', name='risklevel'), nullable=False),
        sa.Column('direct_dependencies', sa.Integer(), nullable=False),
        sa.Column('downstream_impact', sa.Integer(), nullable=False),
        sa.Column('test_coverage_status', sa.String(length=50), nullable=True),
        sa.Column('test_coverage_files_found', sa.Integer(), nullable=True),
        sa.Column('test_coverage_needs_update', sa.Integer(), nullable=True),
        sa.Column('api_endpoints_total', sa.Integer(), nullable=True),
        sa.Column('api_endpoints_new', sa.Integer(), nullable=True),
        sa.Column('api_endpoints_modified', sa.Integer(), nullable=True),
        sa.Column('api_endpoints_breaking', sa.Integer(), nullable=True),
        sa.Column('database_tables_affected', sa.Integer(), nullable=True),
        sa.Column('database_schema_changes', sa.Integer(), nullable=True),
        sa.Column('recommendations_count', sa.Integer(), nullable=False),
        sa.Column('high_priority_recommendations', sa.Integer(), nullable=False),
        sa.Column('affected_components', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['analytics_events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4'
    )
    op.create_index('idx_impact_event_id', 'impact_details', ['event_id'])
    op.create_index('idx_risk_level', 'impact_details', ['risk_level'])

    # Create fix_details table
    op.create_table(
        'fix_details',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('total_fixes', sa.Integer(), nullable=False),
        sa.Column('successful_fixes', sa.Integer(), nullable=False),
        sa.Column('failed_fixes', sa.Integer(), nullable=False),
        sa.Column('files_modified', sa.JSON(), nullable=True),
        sa.Column('tests_added', sa.Integer(), nullable=True),
        sa.Column('tests_updated', sa.Integer(), nullable=True),
        sa.Column('pr_created', sa.Boolean(), nullable=False),
        sa.Column('pr_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['analytics_events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4'
    )
    op.create_index('idx_fix_event_id', 'fix_details', ['event_id'])


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('fix_details')
    op.drop_table('impact_details')
    op.drop_table('documentation_details')
    op.drop_table('review_details')
    op.drop_table('analytics_events')
    
    # Drop ENUMs
    op.execute('DROP TYPE IF EXISTS eventtype')
    op.execute('DROP TYPE IF EXISTS status')
    op.execute('DROP TYPE IF EXISTS risklevel')

# Made with Bob
