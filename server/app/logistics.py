"""Supply lines and army upkeep.

Supply: a territory works only if a chain of your own hexes connects it to
your base. Cut-off territory yields nothing, a cut-off node gives no bonus and
cut-off land is defended by half the militia. A mine works when it touches the
base or a supplied territory.

Upkeep: every stack eats or burns fuel each hour. Charged in whole hours in
settle; if the stores run dry, each unfed stack loses one member per hour
(never below one).
"""
import math
from collections import deque
from sqlalchemy import select
from .models import TileOwnership, Unit, Tile, Player
from .config import UNITS, UPKEEP
from .combat import distance
from . import bases, nodes

DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]


def supplied(db, pid):
    """Owned hexes connected to the base through owned hexes."""
    owned = {(t.q, t.r) for t in db.scalars(select(TileOwnership).where(TileOwnership.player_id == pid))}
    home = tuple(bases.home(db, pid))
    frontier = deque(c for c in owned if distance(home, c) == 1)
    seen = set(frontier)
    while frontier:
        q, r = frontier.popleft()
        for dq, dr in DIRS:
            c = (q + dq, r + dr)
            if c in owned and c not in seen:
                seen.add(c)
                frontier.append(c)
    return seen


def mine_supplied(home, supply, q, r):
    return distance(home, (q, r)) <= 1 or any((q + dq, r + dr) in supply for dq, dr in DIRS)


def node_kind(db, q, r):
    tile = db.get(Tile, (1, q, r))
    return nodes.at(q, r, tile.biome if tile else "plain", bases.near(db, q, r, nodes.CLEARANCE + 1))


def owned_nodes(db, pid, supply=None):
    """[(q, r, kind, is_supplied)] for every node tile the player owns."""
    supply = supplied(db, pid) if supply is None else supply
    out = []
    for t in db.scalars(select(TileOwnership).where(TileOwnership.player_id == pid)):
        kind = node_kind(db, t.q, t.r)
        if kind:
            out.append((t.q, t.r, kind, (t.q, t.r) in supply))
    return out


def radars(db, pid):
    return [(q, r, nodes.KINDS[k]["vision"]) for q, r, k, ok in owned_nodes(db, pid) if ok and nodes.KINDS[k]["vision"]]


def unit_upkeep(kind, count):
    spec = UNITS.get(kind, {})
    if spec.get("naval"):
        return {"fuel": UPKEEP["naval_fuel"] * count}
    if spec.get("infantry"):
        return {"food": UPKEEP["infantry_food"] * count}
    return {"fuel": UPKEEP["vehicle_fuel"] * count}


def per_hour(db, pid, factor=1.0):
    import time
    from . import doctrines
    total = {"food": 0, "fuel": 0}
    for u in db.scalars(select(Unit).where(Unit.player_id == pid)):
        for k, v in unit_upkeep(u.kind, u.count).items():
            total[k] += v
    eff = doctrines.effects(db, pid, int(time.time()))
    scale = {"food": eff.get("food_upkeep", 1), "fuel": eff.get("fuel_upkeep", 1)}
    return {k: math.ceil(v * factor * scale[k]) for k, v in total.items()}


def charge(db, p, at, change, factor=1.0):
    """Charge whole hours of upkeep since p.upkeep_at. Returns True if anyone deserted."""
    if not p.upkeep_at:
        p.upkeep_at = at
        return False
    elapsed = (at - p.upkeep_at) // 3600
    if elapsed <= 0:
        return False
    p.upkeep_at += elapsed * 3600
    hours = min(24, elapsed)          # bounded like offline production
    from .models import Resource
    balances = {r.kind: r.amount for r in db.scalars(select(Resource).where(Resource.player_id == p.id))}
    units = list(db.scalars(select(Unit).where(Unit.player_id == p.id).order_by(Unit.id)))
    deserted = False
    for _ in range(hours):
        due = per_hour(db, p.id, factor)
        short = {k for k, v in due.items() if v and balances.get(k, 0) < v}
        pay = {k: -min(v, balances.get(k, 0)) for k, v in due.items() if v}
        for k, v in pay.items():
            balances[k] += v
        pay = {k: v for k, v in pay.items() if v}
        if pay:
            change(db, p, pay, "upkeep")
        for u in units:
            needs = set(unit_upkeep(u.kind, 1))
            if needs & short and u.count > 1:
                u.count -= 1
                deserted = True
    return deserted
