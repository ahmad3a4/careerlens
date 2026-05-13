"""Initial migration - Create users and seen_jobs tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-05-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
# from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('job_query', sa.String(length=255), nullable=False),
        sa.Column('alert_interval_hours', sa.Integer(), nullable=True, server_default='6'),
        sa.Column('candidate_summary', sa.JSON(), nullable=False),
        sa.Column('best_score', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    
    # Create index on email for faster lookups
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create seen_jobs table
    op.create_table(
        'seen_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('job_link', sa.Text(), nullable=False),
        sa.Column('job_score', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('seen_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on user_id for faster lookups
    op.create_index(op.f('ix_seen_jobs_id'), 'seen_jobs', ['id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_seen_jobs_id'), table_name='seen_jobs')
    
    # Drop tables
    op.drop_table('seen_jobs')
    
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
