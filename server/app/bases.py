"""Per-player world bases.

Every commander gets one exclusive base hex on the world map. Sites come from
a fixed spaced grid ordered by distance from the map centre, so assignment is
deterministic and neighbouring bases never share a safe zone. The legacy shared
staging hex 64:64 is never assigned and keeps acting as a protected point for
territories captured before this release.

Caller must hold the player's row lock. Assignment additionally takes one
transaction-scoped advisory lock (two-int key space, separate from the login
lock) so concurrent first logins can never pick the same site; the unique
(world_id, q, r) constraint is the database backstop.
"""
from fastapi import HTTPException
from sqlalchemy import select, text
from .models import WorldBase, Tile, TileOwnership, Army
from .combat import distance

STAGING = (64, 64)
SPACING = 10        # grid step = minimum hex distance between bases
MARGIN = 6          # keep every base away from the map edge
SAFE_RADIUS = 4     # no NPC garrisons this close to a base (except tutorial)
STAGING_CLEARANCE = 10
OWNED_CLEARANCE = 5
ARMY_CLEARANCE = 3
LOCK_KEY = (1717, 1)


def candidates():
    sites = [(q, r) for q in range(MARGIN, 128 - MARGIN, SPACING)
             for r in range(MARGIN, 128 - MARGIN, SPACING)
             if distance(STAGING, (q, r)) > STAGING_CLEARANCE]
    return sorted(sites, key=lambda s: (distance(STAGING, s), s))


def get(db, pid):
    return db.get(WorldBase, pid)


def home(db, pid):
    """Base coordinates as [q, r]; staging only for a player not yet assigned."""
    base = get(db, pid)
    return [base.q, base.r] if base else list(STAGING)


def near(db, q, r, radius):
    """Base sites (plus the legacy staging point) within a square window."""
    found = {(b.q, b.r): b.player_id for b in db.scalars(select(WorldBase).where(
        WorldBase.world_id == 1,
        WorldBase.q.between(q - radius, q + radius),
        WorldBase.r.between(r - radius, r + radius)))}
    if abs(STAGING[0] - q) <= radius and abs(STAGING[1] - r) <= radius:
        found.setdefault(STAGING, None)
    return found


def at(db, q, r):
    """(is_base, owner_id) for one hex. Staging is a base with no owner."""
    if (q, r) == STAGING:
        return True, None
    base = db.scalar(select(WorldBase).where(
        WorldBase.world_id == 1, WorldBase.q == q, WorldBase.r == r))
    return (True, base.player_id) if base else (False, None)


def _free(db, q, r):
    if not db.get(Tile, (1, q, r)) or not db.get(Tile, (1, q, r + 1)):
        return False
    window = max(SPACING, OWNED_CLEARANCE, ARMY_CLEARANCE)

    def box(model):
        return select(model).where(model.world_id == 1,
            model.q.between(q - window, q + window),
            model.r.between(r - window, r + window))

    if any(distance((b.q, b.r), (q, r)) < SPACING for b in db.scalars(box(WorldBase))):
        return False
    if any(distance((t.q, t.r), (q, r)) <= OWNED_CLEARANCE for t in db.scalars(box(TileOwnership))):
        return False
    if any(distance((a.q, a.r), (q, r)) <= ARMY_CLEARANCE for a in db.scalars(box(Army))):
        return False
    return True


def ensure(db, p, now):
    base = get(db, p.id)
    if base:
        return base
    db.execute(text("SELECT pg_advisory_xact_lock(:a, :b)"), {"a": LOCK_KEY[0], "b": LOCK_KEY[1]})
    for q, r in candidates():
        if _free(db, q, r):
            base = WorldBase(player_id=p.id, world_id=1, q=q, r=r, created_at=now)
            db.add(base)
            db.flush()
            return base
    raise HTTPException(503, "Свободные секторы мира закончились. Попробуйте позже.")
