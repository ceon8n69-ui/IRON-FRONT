"""Marauder raids: the map fights back.

Once per in-game day (4 h), a commander holding at least four territories may
be raided (35 % chance, deterministic per player and day). A marauder band
camps on a neutral hex next to one of their weakest territories: cut-off land
first, then the most exposed. Anyone may attack the band like a garrison. If
it is still there when its timer runs out (one in-game day), the target
territory is burned and becomes neutral again.
"""
import hashlib, uuid
from sqlalchemy import select
from .models import Raid, TileOwnership, Tile
from .combat import distance

MIN_TERRITORIES = 4
CHANCE = 35
NAME = "Мародёры"
BLOCKED = {"sea", "lake", "river", "mountain"}
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]


def stacks_for(territories):
    n = territories
    out = [["rifles", 6 + n], ["assault", 4 + n // 2]]
    if n >= 8:
        out.append(["armor", 1 + (n - 8) // 4])
    return out


def active_at(db, q, r):
    return db.scalar(select(Raid).where(Raid.q == q, Raid.r == r, Raid.status == "active"))


def active_in(db, q, r, radius):
    return {(x.q, x.r): x for x in db.scalars(select(Raid).where(
        Raid.status == "active", Raid.q.between(q - radius, q + radius), Raid.r.between(r - radius, r + radius)))}


def strength(raid):
    from .config import UNITS
    return NAME, sum(UNITS[k]["hp"] * n for k, n in raid.stacks), 60


def tick(db, p, at):
    """Strike overdue raids, then maybe spawn today's. Returns True if anything changed."""
    from . import seasons, logistics, bases, garrisons, objects
    changed = False
    for raid in db.scalars(select(Raid).where(Raid.player_id == p.id, Raid.status == "active", Raid.strikes_at <= at)):
        tile = db.get(TileOwnership, (1, raid.target_q, raid.target_r))
        if tile and tile.player_id == p.id:
            db.delete(tile)
            raid.result = f"Мародёры сожгли территорию {raid.target_q}:{raid.target_r}"
        else:
            raid.result = "Мародёры ушли ни с чем"
        raid.status = "struck"
        changed = True
    season = seasons.current(db)
    cal = seasons.calendar(season, at)
    if not cal:
        return changed
    if db.scalar(select(Raid).where(Raid.player_id == p.id, Raid.status == "active")):
        return changed
    if db.scalar(select(Raid).where(Raid.player_id == p.id, Raid.season == cal["season"], Raid.day == cal["day_index"])):
        return changed
    owned = {(t.q, t.r) for t in db.scalars(select(TileOwnership).where(TileOwnership.player_id == p.id))}
    if len(owned) < MIN_TERRITORIES:
        return changed
    roll = int(hashlib.sha256(f"raid-1:{season.seed}:{p.id}:{cal['day_index']}".encode()).hexdigest()[:8], 16)
    if roll % 100 >= CHANCE:
        return changed
    supply = logistics.supplied(db, p.id)
    exposed = lambda c: sum((c[0] + dq, c[1] + dr) in owned for dq, dr in DIRS)
    for target in sorted(owned, key=lambda c: (c in supply, exposed(c), c)):
        spot = _camp_spot(db, target, owned)
        if spot:
            db.add(Raid(id=str(uuid.uuid4()), player_id=p.id, q=spot[0], r=spot[1], target_q=target[0], target_r=target[1],
                        season=cal["season"], day=cal["day_index"], stacks=stacks_for(len(owned)),
                        strikes_at=at + seasons.DAY, status="active"))
            db.flush()
            return True
    return changed


def _camp_spot(db, target, owned):
    from . import bases, garrisons, objects
    for dq, dr in DIRS:
        c = (target[0] + dq, target[1] + dr)
        tile = db.get(Tile, (1, c[0], c[1]))
        if not tile or tile.biome in BLOCKED or c in owned or db.get(TileOwnership, (1, c[0], c[1])):
            continue
        if bases.at(db, c[0], c[1])[0] or garrisons.guarded_at(db, c[0], c[1]) or objects.at(db, c[0], c[1]):
            continue
        return c
    return None


def defeat(db, q, r):
    raid = active_at(db, q, r)
    if raid:
        raid.status, raid.result = "defeated", "Мародёры разбиты"
    return raid


def state(db, pid, at):
    rows = list(db.scalars(select(Raid).where(Raid.player_id == pid).order_by(Raid.strikes_at.desc()).limit(5)))
    return [{"q": x.q, "r": x.r, "target_q": x.target_q, "target_r": x.target_r, "strikes_at": x.strikes_at,
             "status": x.status, "result": x.result} for x in rows]
