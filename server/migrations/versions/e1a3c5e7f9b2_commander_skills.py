"""Commander skills

Additive: player_heroes.skills (JSON, skill -> rank). Levels come from XP.
"""
from alembic import op
import sqlalchemy as sa

revision = 'e1a3c5e7f9b2'
down_revision = 'd8f0a2c4e6b8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('player_heroes', sa.Column('skills', sa.JSON(), server_default='{}', nullable=False))


def downgrade():
    op.drop_column('player_heroes', 'skills')
