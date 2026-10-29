"""Match rooms: Polytopia-style matches, seats and a Telegram notice outbox

Additive: three new tables, nothing existing changes.
"""
from alembic import op
import sqlalchemy as sa

revision = 'e3f5a7b9c1d2'
down_revision = 'd9e1f3a5b7c8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'matches',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('code', sa.String(6), nullable=False, unique=True),
        sa.Column('name', sa.String(40), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('size', sa.String(), nullable=False),
        sa.Column('seats', sa.Integer(), nullable=False),
        sa.Column('turn_limit', sa.Integer(), nullable=False),
        sa.Column('private', sa.Boolean(), nullable=False),
        sa.Column('host_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('state', sa.JSON(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('turn_started_at', sa.BigInteger(), nullable=True),
        sa.Column('winner_seat', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        sa.CheckConstraint('seats >= 2 AND seats <= 4', name='ck_matches_seats'),
    )
    op.create_index('ix_matches_status', 'matches', ['status'])
    op.create_table(
        'match_seats',
        sa.Column('match_id', sa.String(), sa.ForeignKey('matches.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('seat', sa.Integer(), primary_key=True),
        sa.Column('player_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('ai', sa.Boolean(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('faction', sa.String(), nullable=False),
        sa.Column('joined_at', sa.BigInteger(), nullable=False),
        sa.UniqueConstraint('match_id', 'player_id', name='uq_match_seats_player'),
    )
    op.create_index('ix_match_seats_player_id', 'match_seats', ['player_id'])
    op.create_table(
        'match_notices',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('player_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('match_id', sa.String(), sa.ForeignKey('matches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('text', sa.String(300), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('sent_at', sa.BigInteger(), nullable=True),
    )
    op.create_index('ix_match_notices_pending', 'match_notices', ['sent_at'])


def downgrade():
    # Drops every match. Never on production without backup and approval.
    op.drop_table('match_notices')
    op.drop_table('match_seats')
    op.drop_table('matches')
