"""Doctrines, ruins and mercenary camps

Additive: player_doctrines, camp_hires; map_pickups may hold one-time ruins.
"""
from alembic import op
import sqlalchemy as sa

revision = 'b5d7f9b1c3e4'
down_revision = 'a3c5e7a9b1d2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('player_doctrines',
    sa.Column('player_id', sa.String(), nullable=False),
    sa.Column('key', sa.String(), nullable=False),
    sa.Column('started_at', sa.BigInteger(), nullable=False),
    sa.Column('ready_at', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['player_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('player_id', 'key')
    )
    op.create_table('camp_hires',
    sa.Column('world_id', sa.Integer(), nullable=False),
    sa.Column('q', sa.Integer(), nullable=False),
    sa.Column('r', sa.Integer(), nullable=False),
    sa.Column('season', sa.Integer(), nullable=False),
    sa.Column('week', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.String(), nullable=False),
    sa.Column('kind', sa.String(), nullable=False),
    sa.Column('hired_at', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['player_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('world_id', 'q', 'r', 'season', 'week')
    )
    op.drop_constraint('ck_map_pickups_kind', 'map_pickups', type_='check')
    op.create_check_constraint('ck_map_pickups_kind', 'map_pickups', "kind IN ('pile', 'chest', 'ruin')")


def downgrade():
    op.execute("DELETE FROM map_pickups WHERE kind = 'ruin'")
    op.drop_constraint('ck_map_pickups_kind', 'map_pickups', type_='check')
    op.create_check_constraint('ck_map_pickups_kind', 'map_pickups', "kind IN ('pile', 'chest')")
    op.drop_table('camp_hires')
    op.drop_table('player_doctrines')
