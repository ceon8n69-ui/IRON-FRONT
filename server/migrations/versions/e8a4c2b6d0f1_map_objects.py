"""Adventure-map objects: one-time pickups and mine ownership

Additive: creates map_pickups and map_mines. Object placement itself is
derived from coordinates, so no seeding is needed.
"""
from alembic import op
import sqlalchemy as sa

revision = 'e8a4c2b6d0f1'
down_revision = 'd5e2f9a7c1b3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('map_pickups',
    sa.Column('world_id', sa.Integer(), nullable=False),
    sa.Column('q', sa.Integer(), nullable=False),
    sa.Column('r', sa.Integer(), nullable=False),
    sa.Column('kind', sa.String(), nullable=False),
    sa.Column('player_id', sa.String(), nullable=False),
    sa.Column('taken_at', sa.BigInteger(), nullable=False),
    sa.Column('choice', sa.String(), nullable=True),
    sa.CheckConstraint("kind IN ('pile', 'chest')", name='ck_map_pickups_kind'),
    sa.CheckConstraint("choice IS NULL OR choice IN ('resources', 'xp')", name='ck_map_pickups_choice'),
    sa.ForeignKeyConstraint(['player_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['world_id', 'q', 'r'], ['hex_tiles.world_id', 'hex_tiles.q', 'hex_tiles.r'], ),
    sa.PrimaryKeyConstraint('world_id', 'q', 'r')
    )
    op.create_index(op.f('ix_map_pickups_player_id'), 'map_pickups', ['player_id'], unique=False)
    op.create_table('map_mines',
    sa.Column('world_id', sa.Integer(), nullable=False),
    sa.Column('q', sa.Integer(), nullable=False),
    sa.Column('r', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.String(), nullable=False),
    sa.Column('resource', sa.String(), nullable=False),
    sa.Column('rate', sa.Integer(), nullable=False),
    sa.Column('acquired_at', sa.BigInteger(), nullable=False),
    sa.CheckConstraint('rate > 0', name='ck_map_mines_rate'),
    sa.ForeignKeyConstraint(['player_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['world_id', 'q', 'r'], ['hex_tiles.world_id', 'hex_tiles.q', 'hex_tiles.r'], ),
    sa.PrimaryKeyConstraint('world_id', 'q', 'r')
    )
    op.create_index(op.f('ix_map_mines_player_id'), 'map_mines', ['player_id'], unique=False)


def downgrade():
    # Destroys pickups and mine ownership. Never on production without backup and approval.
    op.drop_index(op.f('ix_map_mines_player_id'), table_name='map_mines')
    op.drop_table('map_mines')
    op.drop_index(op.f('ix_map_pickups_player_id'), table_name='map_pickups')
    op.drop_table('map_pickups')
