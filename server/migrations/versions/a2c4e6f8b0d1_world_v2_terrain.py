"""World v2: seas, islands, lakes, rivers and mountains

Data migration on hex_tiles.biome. The previous biome of every tile is copied
to hex_tiles_biome_v1 first, so downgrade restores the old world exactly.
Tiles players already use keep their old biome when the new one would be
water or mountain: bases and two rings around them, owned territories,
mines, pickups, armies, march paths and the legacy staging point 64:64.
"""
from alembic import op
import sqlalchemy as sa

revision = 'a2c4e6f8b0d1'
down_revision = 'f1b3d5e7a9c2'
branch_labels = None
depends_on = None

BLOCKED = {"sea", "lake", "river", "mountain"}


def _protected(conn):
    keep = set()
    def ring(q, r, d):
        for dq in range(-d, d + 1):
            for dr in range(-d, d + 1):
                if max(abs(dq), abs(dr), abs(dq + dr)) <= d:
                    keep.add((q + dq, r + dr))
    for q, r in conn.execute(sa.text("SELECT q, r FROM player_bases WHERE world_id = 1")):
        ring(q, r, 2)
    ring(64, 64, 2)
    for table in ("tile_ownership", "armies", "map_mines", "map_pickups"):
        keep.update(conn.execute(sa.text(f"SELECT q, r FROM {table} WHERE world_id = 1")).all())
    for (path,) in conn.execute(sa.text("SELECT path FROM army_orders WHERE path IS NOT NULL")):
        keep.update((p[0], p[1]) for p in (path or []))
    for q, r in conn.execute(sa.text("SELECT q, r FROM army_orders")):
        keep.add((q, r))
    return keep


def upgrade():
    from app import worldgen  # generator lives with the application code
    conn = op.get_bind()
    op.create_table('hex_tiles_biome_v1',
        sa.Column('world_id', sa.Integer(), nullable=False),
        sa.Column('q', sa.Integer(), nullable=False),
        sa.Column('r', sa.Integer(), nullable=False),
        sa.Column('biome', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('world_id', 'q', 'r'))
    conn.execute(sa.text("INSERT INTO hex_tiles_biome_v1 SELECT world_id, q, r, biome FROM hex_tiles WHERE world_id = 1"))
    old = {(q, r): b for q, r, b in conn.execute(sa.text("SELECT q, r, biome FROM hex_tiles WHERE world_id = 1"))}
    if not old:
        return  # fresh database: bootstrap seeds the new world directly
    keep = _protected(conn)
    rows = []
    for (q, r), biome in worldgen.generate().items():
        if (q, r) not in old:
            continue
        if (q, r) in keep and biome in BLOCKED:
            biome = old[(q, r)]
        if biome != old[(q, r)]:
            rows.append({"q": q, "r": r, "b": biome})
    for i in range(0, len(rows), 1000):
        conn.execute(sa.text("UPDATE hex_tiles SET biome = :b WHERE world_id = 1 AND q = :q AND r = :r"), rows[i:i + 1000])


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE hex_tiles t SET biome = b.biome FROM hex_tiles_biome_v1 b "
                         "WHERE t.world_id = b.world_id AND t.q = b.q AND t.r = b.r"))
    op.drop_table('hex_tiles_biome_v1')
