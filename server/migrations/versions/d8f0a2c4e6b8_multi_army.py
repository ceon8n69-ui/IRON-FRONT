"""Several armies per commander

Additive: drops the one-army-per-player constraint, numbers armies and marks the
one the commander leads. Every existing army becomes army no. 1 with the commander.
"""
from alembic import op
import sqlalchemy as sa

revision = 'd8f0a2c4e6b8'
down_revision = 'c6e8a0b2d4f6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('armies', sa.Column('number', sa.Integer(), server_default='1', nullable=False))
    op.add_column('armies', sa.Column('commander', sa.Boolean(), server_default=sa.false(), nullable=False))
    op.execute("UPDATE armies SET commander = true")
    op.drop_constraint('armies_player_id_key', 'armies', type_='unique')
    op.create_index('ix_armies_player_id', 'armies', ['player_id'])
    op.create_unique_constraint('uq_armies_player_number', 'armies', ['player_id', 'number'])
    op.create_index('uq_armies_commander', 'armies', ['player_id'], unique=True, postgresql_where=sa.text('commander'))


def downgrade():
    # Keeps each commander's own army; extra armies are disbanded into reserve first.
    op.execute("""UPDATE player_units SET status = 'reserve' WHERE id IN (
        SELECT au.unit_id FROM army_units au JOIN armies a ON a.id = au.army_id WHERE NOT a.commander)""")
    op.execute("DELETE FROM army_units WHERE army_id IN (SELECT id FROM armies WHERE NOT commander)")
    op.execute("DELETE FROM army_orders WHERE army_id IN (SELECT id FROM armies WHERE NOT commander)")
    op.execute("DELETE FROM armies WHERE NOT commander")
    op.drop_index('uq_armies_commander', table_name='armies')
    op.drop_constraint('uq_armies_player_number', 'armies', type_='unique')
    op.drop_index('ix_armies_player_id', table_name='armies')
    op.create_unique_constraint('armies_player_id_key', 'armies', ['player_id'])
    op.drop_column('armies', 'commander')
    op.drop_column('armies', 'number')
