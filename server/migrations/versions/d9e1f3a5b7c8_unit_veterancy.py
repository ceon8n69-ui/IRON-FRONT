"""Unit veterancy: experience per stack

Additive: player_units.xp (existing stacks start as recruits).
"""
from alembic import op
import sqlalchemy as sa

revision = 'd9e1f3a5b7c8'
down_revision = 'c7e9b1d3f5a6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('player_units', sa.Column('xp', sa.Integer(), server_default='0', nullable=False))


def downgrade():
    # Drops stack experience. Never on production without backup and approval.
    op.drop_column('player_units', 'xp')
