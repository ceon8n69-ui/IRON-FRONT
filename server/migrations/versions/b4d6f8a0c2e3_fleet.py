"""Fleet: cleared sea-raider sites

Additive: creates map_cleared. Ships are ordinary player_units rows.
"""
from alembic import op
import sqlalchemy as sa

revision = 'b4d6f8a0c2e3'
down_revision = 'a2c4e6f8b0d1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('map_cleared',
    sa.Column('world_id', sa.Integer(), nullable=False),
    sa.Column('q', sa.Integer(), nullable=False),
    sa.Column('r', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.String(), nullable=False),
    sa.Column('cleared_at', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['player_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['world_id', 'q', 'r'], ['hex_tiles.world_id', 'hex_tiles.q', 'hex_tiles.r'], ),
    sa.PrimaryKeyConstraint('world_id', 'q', 'r')
    )


def downgrade():
    # Drops raider clearance history. Never on production without backup and approval.
    op.drop_table('map_cleared')
