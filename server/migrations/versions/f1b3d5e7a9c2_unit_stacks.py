"""Unit stacks: member count per player unit

Additive: player_units.count (existing squads become 10 riflemen).
"""
from alembic import op
import sqlalchemy as sa

revision = 'f1b3d5e7a9c2'
down_revision = 'e8a4c2b6d0f1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('player_units', sa.Column('count', sa.Integer(), server_default='10', nullable=False))
    op.create_check_constraint('ck_player_units_count', 'player_units', 'count >= 1')


def downgrade():
    # Drops stack sizes. Never on production without backup and approval.
    op.drop_constraint('ck_player_units_count', 'player_units')
    op.drop_column('player_units', 'count')
