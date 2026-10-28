"""Asynchronous PvP: shields, attack orders and battle reports

Additive. Existing commanders keep the 72 h newbie shield counted from sign-up,
so anyone who joined more than three days ago is attackable right away.
"""
from alembic import op
import sqlalchemy as sa

revision = 'c6e8a0b2d4f6'
down_revision = 'b4d6f8a0c2e3'
branch_labels = None
depends_on = None

NEWBIE = 72 * 3600


def upgrade():
    op.add_column('users', sa.Column('shield_until', sa.BigInteger(), server_default='0', nullable=False))
    op.execute(f"UPDATE users SET shield_until = created_at + {NEWBIE}")
    op.drop_constraint('army_orders_action_check', 'army_orders', type_='check')
    op.create_check_constraint('army_orders_action_check', 'army_orders', "action IN ('move', 'capture', 'attack')")
    op.create_table('pvp_reports',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('battle_id', sa.String(), nullable=False),
    sa.Column('attacker_id', sa.String(), nullable=False),
    sa.Column('defender_id', sa.String(), nullable=False),
    sa.Column('target', sa.String(), nullable=False),
    sa.Column('q', sa.Integer(), nullable=False),
    sa.Column('r', sa.Integer(), nullable=False),
    sa.Column('outcome', sa.String(), nullable=False),
    sa.Column('loot', sa.JSON(), nullable=False),
    sa.Column('losses', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.BigInteger(), nullable=False),
    sa.CheckConstraint("target IN ('base', 'territory', 'mine')", name='ck_pvp_reports_target'),
    sa.CheckConstraint("outcome IN ('victory', 'defeat')", name='ck_pvp_reports_outcome'),
    sa.ForeignKeyConstraint(['attacker_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['battle_id'], ['battles.id'], ),
    sa.ForeignKeyConstraint(['defender_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('battle_id')
    )
    op.create_index('ix_pvp_reports_pair', 'pvp_reports', ['attacker_id', 'defender_id', 'created_at'])
    op.create_index('ix_pvp_reports_defender', 'pvp_reports', ['defender_id', 'created_at'])


def downgrade():
    # Drops PvP history. Attack orders become plain moves so the old constraint holds.
    op.drop_index('ix_pvp_reports_defender', table_name='pvp_reports')
    op.drop_index('ix_pvp_reports_pair', table_name='pvp_reports')
    op.drop_table('pvp_reports')
    op.execute("UPDATE army_orders SET action = 'move' WHERE action = 'attack'")
    op.drop_constraint('army_orders_action_check', 'army_orders', type_='check')
    op.create_check_constraint('army_orders_action_check', 'army_orders', "action IN ('move', 'capture')")
    op.drop_column('users', 'shield_until')
