"""Heroes-style movement points and multi-hex routes

Additive: armies.movement / movement_at with defaults (existing armies start
full), nullable army_orders.path. Legacy single-hex orders keep working.
"""
from alembic import op
import sqlalchemy as sa

revision = 'd5e2f9a7c1b3'
down_revision = 'c3d8a1f6e2b4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('armies', sa.Column('movement', sa.Integer(), server_default='12', nullable=False))
    op.add_column('armies', sa.Column('movement_at', sa.BigInteger(), server_default='0', nullable=False))
    op.create_check_constraint('ck_armies_movement', 'armies', 'movement >= 0')
    op.add_column('army_orders', sa.Column('path', sa.JSON(), nullable=True))


def downgrade():
    # Drops routes and movement state. Never on production without backup and approval.
    op.drop_column('army_orders', 'path')
    op.drop_constraint('ck_armies_movement', 'armies')
    op.drop_column('armies', 'movement_at')
    op.drop_column('armies', 'movement')
