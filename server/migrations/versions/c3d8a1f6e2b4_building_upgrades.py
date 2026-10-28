"""Building upgrades: in-progress upgrade completion time

Additive nullable column; existing buildings keep their level and status.
"""
from alembic import op
import sqlalchemy as sa

revision = 'c3d8a1f6e2b4'
down_revision = 'b7c41e2d9f05'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('player_buildings', sa.Column('upgrade_ready_at', sa.BigInteger(), nullable=True))


def downgrade():
    # Drops pending upgrades. Never run against production without backup and approval.
    op.drop_column('player_buildings', 'upgrade_ready_at')
