"""Season scoring and the Capital

Additive: users.vp, users.tutorial_done, season_results. The legacy shared
staging hex 64:64 becomes the Capital, a capturable territory, so the
tile_ownership constraint that excluded it is dropped. Land is forced in a
radius of 2 around it so the Capital is always reachable.
"""
from alembic import op
import sqlalchemy as sa

revision = 'a3c5e7a9b1d2'
down_revision = 'f2b4d6f8a1c3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('vp', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('tutorial_done', sa.Boolean(), server_default=sa.false(), nullable=False))
    op.execute("UPDATE users SET tutorial_done = true WHERE id IN (SELECT player_id FROM mission_rewards WHERE mission = 'first-patrol')")
    op.create_table('season_results',
    sa.Column('season', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.String(), nullable=False),
    sa.Column('rank', sa.Integer(), nullable=False),
    sa.Column('vp', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('hero', sa.String(), nullable=True),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.ForeignKeyConstraint(['player_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['season'], ['seasons.number'], ),
    sa.PrimaryKeyConstraint('season', 'player_id')
    )
    op.drop_constraint('tile_ownership_check', 'tile_ownership', type_='check')
    op.execute("""UPDATE hex_tiles SET biome = 'plain' WHERE world_id = 1
        AND greatest(abs(q - 64), abs(r - 64), abs(q + r - 128)) <= 2
        AND biome IN ('sea', 'lake', 'river', 'mountain')""")


def downgrade():
    # Terrain forced around the Capital stays (harmless). A captured Capital is released.
    op.execute("DELETE FROM tile_ownership WHERE q = 64 AND r = 64")
    op.create_check_constraint('tile_ownership_check', 'tile_ownership', 'NOT (q = 64 AND r = 64)')
    op.drop_table('season_results')
    op.drop_column('users', 'tutorial_done')
    op.drop_column('users', 'vp')
