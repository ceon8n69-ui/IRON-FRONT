"""Exclusive world base per player

Additive: creates player_bases only. Existing players receive a base lazily on
their next authenticated request; no existing rows are rewritten.
"""
from alembic import op
import sqlalchemy as sa

revision = 'b7c41e2d9f05'
down_revision = '9a3feb768692'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('player_bases',
    sa.Column('player_id', sa.String(), nullable=False),
    sa.Column('world_id', sa.Integer(), nullable=False),
    sa.Column('q', sa.Integer(), nullable=False),
    sa.Column('r', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.BigInteger(), nullable=False),
    sa.CheckConstraint('NOT (q = 64 AND r = 64)', name='ck_player_bases_not_staging'),
    sa.ForeignKeyConstraint(['player_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['world_id', 'q', 'r'], ['hex_tiles.world_id', 'hex_tiles.q', 'hex_tiles.r'], ),
    sa.PrimaryKeyConstraint('player_id'),
    sa.UniqueConstraint('world_id', 'q', 'r', name='uq_player_bases_site')
    )


def downgrade():
    # Destroys base assignments. Never run against production without backup and approval.
    op.drop_table('player_bases')
