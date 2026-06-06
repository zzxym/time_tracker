"""Add teams and team_members tables.

Revision ID: 002
Revises: 001
Create Date: 2026-06-06
"""

from alembic import op
import sqlalchemy as sa


revision = '002_add_teams'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create teams table
    op.create_table(
        'teams',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(500), nullable=False, default=''),
        sa.Column('owner_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_teams_owner_id', 'teams', ['owner_id'], unique=False)

    # Create team_members table
    op.create_table(
        'team_members',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('team_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, default='member'),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_team_members_team_id', 'team_members', ['team_id'], unique=False)
    op.create_index('ix_team_members_user_id', 'team_members', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('team_members')
    op.drop_table('teams')
