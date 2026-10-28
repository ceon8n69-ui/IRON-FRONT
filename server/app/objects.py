"""Heroes-style adventure-map objects: resource piles, chests, mines.

Placement is a pure function of coordinates (like garrisons), so the world
needs no seeding. Only state is persisted: a one-time pickup row per hex
(first transaction wins under the tile row lock) and mine ownership.
Object hexes are interacted with on arrival; until taken they can only be
a route's destination, never a hex walked through.
"""
import hashlib
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from .models import MapPickup, MapMine, Tile, Hero
from . import bases, garrisons

PILES = {"metal": 180, "oil": 120, "fuel": 60, "food": 150}
CHEST = {"resources": {"metal": 250, "electronics": 60}, "xp": 120}
MINES = {"metal": 6, "oil": 4}          # per minute, like territory yield
from .config import NPC_TIERS, NPC_SEA_TIERS, UNITS
TIERS = [(t["name"], sum(UNITS[k]["hp"] * n for k, n in t["stacks"]), t["xp"]) for t in NPC_TIERS]
SEA_TIERS = [(t["name"], sum(UNITS[k]["hp"] * n for k, n in t["stacks"]), t["xp"]) for t in NPC_SEA_TIERS]


def _roll(q, r, salt):
    return int(hashlib.sha256(f"iron-obj-1:{salt}:{q}:{r}".encode()).hexdigest()[:8], 16)


def placed(q, r, sites, biome="plain"):
    """Static object at a hex, or None. `sites` = nearby base sites, `biome` = the tile's terrain."""
    if garrisons.guarded(q, r, sites, biome) or biome in ("mountain", "river", "lake"):
        return None
    if biome == "sea":
        # Shipwrecks: salvage for fleets.
        if _roll(q, r, "wreck") % 100 < 3 and not any(abs(q - b[0]) + abs(r - b[1]) <= 2 for b in sites):
            kind = ("metal", "fuel", "electronics")[_roll(q, r, "wres") % 3]
            return {"kind": "pile", "resource": kind, "amount": 200 if kind != "electronics" else 80, "wreck": True}
        return None
    # The base and its first ring stay clear, so the opening moves are clean.
    if any(max(abs(q - b[0]), abs(r - b[1]), abs(q + r - b[0] - b[1])) <= 1 for b in sites):
        return None
    n = _roll(q, r, "kind") % 100
    if n < 6:
        kind = list(PILES)[_roll(q, r, "res") % len(PILES)]
        amount = round(PILES[kind] * (1 + (_roll(q, r, "amt") % 51) / 100))
        return {"kind": "pile", "resource": kind, "amount": amount}
    if n < 8:
        return {"kind": "chest"}
    if n < 10:
        kind = list(MINES)[_roll(q, r, "mine") % len(MINES)]
        return {"kind": "mine", "resource": kind, "rate": MINES[kind]}
    return None


def at(db, q, r):
    tile = db.get(Tile, (1, q, r))
    return placed(q, r, bases.near(db, q, r, bases.SAFE_RADIUS + 2), tile.biome if tile else "plain")


def strength(q, r, biome="plain", sites=()):
    """Visible neutral stack strength: (label, hp, xp)."""
    if biome == "sea":
        return SEA_TIERS[_roll(q, r, "sea-tier") % 3]
    if (q, r - 1) in set(sites) or _is_tutorial(q, r):
        return TIERS[0]
    return TIERS[_roll(q, r, "tier") % 3]


def tier_definition(name):
    return next(t for t in NPC_TIERS + NPC_SEA_TIERS if t["name"] == name)


def _is_tutorial(q, r):
    # Tutorial garrisons sit directly south of a base on the spaced grid.
    return (q, r - 1) in set(bases.candidates()) or (q, r - 1) == bases.STAGING


def blocks_path(db, c, pid, sites, biome="plain"):
    """Untaken pickups and unowned/foreign mines can only be a destination."""
    obj = placed(c[0], c[1], sites, biome)
    if not obj:
        return False
    if obj["kind"] == "mine":
        mine = db.get(MapMine, (1, c[0], c[1]))
        return not (mine and mine.player_id == pid)
    return db.get(MapPickup, (1, c[0], c[1])) is None


def view(db, pid, q, r, sites, biome="plain"):
    obj = placed(q, r, sites, biome)
    if not obj:
        return None
    if obj["kind"] == "mine":
        mine = db.get(MapMine, (1, q, r))
        owner = None if not mine else "self" if mine.player_id == pid else "other"
        return {**obj, "owner": owner}
    taken = db.get(MapPickup, (1, q, r))
    if taken and not (obj["kind"] == "chest" and taken.player_id == pid and taken.choice is None):
        return None
    return {**obj, "pending": bool(taken)}


def arrive(db, p, q, r, at_time, change):
    """Interact with the object on the army's arrival hex. Returns a result line or None."""
    obj = at(db, q, r)
    if not obj:
        return None
    db.scalar(select(Tile).where(Tile.world_id == 1, Tile.q == q, Tile.r == r).with_for_update())
    if obj["kind"] == "mine":
        mine = db.get(MapMine, (1, q, r))
        if mine and mine.player_id != p.id:
            return "Шахта принадлежит другому командиру. PvP пока не включён."
        if not mine:
            db.add(MapMine(world_id=1, q=q, r=r, player_id=p.id, resource=obj["resource"], rate=obj["rate"], acquired_at=at_time))
            return f"Шахта захвачена: +{obj['rate']} в минуту"
        return None
    won = db.execute(insert(MapPickup).values(world_id=1, q=q, r=r, kind=obj["kind"], player_id=p.id,
        taken_at=at_time, choice=None if obj["kind"] == "chest" else "resources")
        .on_conflict_do_nothing().returning(MapPickup.q)).scalar()
    if won is None:
        return "Здесь уже побывал другой отряд."
    if obj["kind"] == "pile":
        change(db, p, {obj["resource"]: obj["amount"]}, "map_pile")
        return f"Найдено: +{obj['amount']} ({obj['resource']})"
    return "Найден сундук: выберите награду"


def choose(db, p, q, r, choice, change):
    pick = db.get(MapPickup, (1, q, r))
    if not pick or pick.player_id != p.id or pick.kind != "chest":
        raise HTTPException(404, "Сундук не найден")
    if pick.choice is not None:
        raise HTTPException(409, "Награда из сундука уже получена")
    if choice == "resources":
        change(db, p, CHEST["resources"], "map_chest")
    else:
        hero = db.get(Hero, p.id)
        hero.xp += CHEST["xp"]
    pick.choice = choice
    return {"choice": choice}


def pending_chests(db, pid):
    return [{"q": c.q, "r": c.r, "options": CHEST} for c in db.scalars(select(MapPickup).where(
        MapPickup.player_id == pid, MapPickup.kind == "chest", MapPickup.choice.is_(None)))]


def mines(db, pid):
    return list(db.scalars(select(MapMine).where(MapMine.player_id == pid)))
