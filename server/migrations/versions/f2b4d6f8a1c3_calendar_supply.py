"""Seasons table and upkeep clock

Additive. Inserts season 1 for the current world (seed iron-world-2), starting
now and lasting 14 days. users.upkeep_at starts at the migration time, so no
retroactive upkeep is charged.
"""
import time
from alembic import op
import sqlalchemy as sa

revision = 'f2b4d6f8a1c3'
down_revision = 'e1a3c5e7f9b2'
branch_labels = None
depends_on = None


def upgrade():
    now = int(time.time())
    op.create_table('seasons',
    sa.Column('number', sa.Integer(), nullable=False),
    sa.Column('seed', sa.String(), nullable=False),
    sa.Column('started_at', sa.BigInteger(), nullable=False),
    sa.Column('ends_at', sa.BigInteger(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('results', sa.JSON(), nullable=True),
    sa.CheckConstraint("status IN ('active', 'finished')", name='ck_seasons_status'),
    sa.CheckConstraint('ends_at > started_at', name='ck_seasons_span'),
    sa.PrimaryKeyConstraint('number')
    )
    op.execute(f"INSERT INTO seasons (number, seed, started_at, ends_at, status) VALUES (1, 'iron-world-2', {now}, {now + 14 * 24 * 3600}, 'active')")
    op.add_column('users', sa.Column('upkeep_at', sa.BigInteger(), server_default='0', nullable=False))
    op.execute(f"UPDATE users SET upkeep_at = {now}")


def downgrade():
    op.drop_column('users', 'upkeep_at')
    op.drop_table('seasons')
