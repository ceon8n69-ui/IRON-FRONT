"""Alliances and marauder raids

Additive: alliances, users.alliance_id, raids.
"""
from alembic import op
import sqlalchemy as sa

revision = 'c7e9b1d3f5a6'
down_revision = 'b5d7f9b1c3e4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('alliances',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(length=24), nullable=False),
    sa.Column('tag', sa.String(length=5), nullable=False),
    sa.Column('code', sa.String(length=8), nullable=False),
    sa.Column('owner_id', sa.String(), nullable=False),
    sa.Column('created_at', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code'),
    sa.UniqueConstraint('tag')
    )
    op.add_column('users', sa.Column('alliance_id', sa.String(), nullable=True))
    op.create_foreign_key('fk_users_alliance', 'users', 'alliances', ['alliance_id'], ['id'])
    op.create_index('ix_users_alliance_id', 'users', ['alliance_id'])
    op.create_table('raids',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('player_id', sa.String(), nullable=False),
    sa.Column('q', sa.Integer(), nullable=False),
    sa.Column('r', sa.Integer(), nullable=False),
    sa.Column('target_q', sa.Integer(), nullable=False),
    sa.Column('target_r', sa.Integer(), nullable=False),
    sa.Column('season', sa.Integer(), nullable=False),
    sa.Column('day', sa.Integer(), nullable=False),
    sa.Column('stacks', sa.JSON(), nullable=False),
    sa.Column('strikes_at', sa.BigInteger(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('result', sa.String(), nullable=True),
    sa.CheckConstraint("status IN ('active', 'defeated', 'struck')", name='ck_raids_status'),
    sa.ForeignKeyConstraint(['player_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('player_id', 'season', 'day', name='uq_raids_player_day')
    )
    op.create_index('ix_raids_player_id', 'raids', ['player_id'])
    op.create_index('uq_raids_active_hex', 'raids', ['q', 'r'], unique=True, postgresql_where=sa.text("status = 'active'"))


def downgrade():
    op.drop_index('uq_raids_active_hex', table_name='raids')
    op.drop_index('ix_raids_player_id', table_name='raids')
    op.drop_table('raids')
    op.drop_index('ix_users_alliance_id', table_name='users')
    op.drop_constraint('fk_users_alliance', 'users', type_='foreignkey')
    op.drop_column('users', 'alliance_id')
    op.drop_table('alliances')
