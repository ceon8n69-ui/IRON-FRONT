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
from .config import NPC_TIERS, NPC_SEA_TIERS, UNITS, FACTIONS
# Mercenaries: any faction's line, scout or assault unit (one stack per camp per in-game week).
CAMP_UNITS = sorted(v["key"] for f in FACTIONS.values() for v in f["units"] if v["role"] in ("rifles", "scouts", "assault"))
CAMP_PREMIUM = 1.25
RUIN_OUTCOMES = ["cache", "xp", "artifact", "recruits", "maps"]
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
    if n < 11:
        return {"kind": "ruin"}
    if n < 12:
        return {"kind": "camp", "unit": CAMP_UNITS[_roll(q, r, "camp") % len(CAMP_UNITS)]}
    return None


def at(db, q, r):
    tile = db.get(Tile, (1, q, r))
    return placed(q, r, bases.near(db, q, r, bases.SAFE_RADIUS + 2), tile.biome if tile else "plain")


def strength(q, r, biome="plain", sites=()):
    """Visible neutral stack strength: (label, hp, xp)."""
    if biome == "sea":
        return SEA_TIERS[_roll(q, r, "sea-tier") % 3]
    from . import nodes
    node = nodes.at(q, r, biome, sites)
    if node:
        t = nodes.tier(node)
        return (t["name"], sum(UNITS[k]["hp"] * n for k, n in t["stacks"]), t["xp"])
    if (q, r - 1) in set(sites) or _is_tutorial(q, r):
        return TIERS[0]
    return TIERS[_roll(q, r, "tier") % 3]


def tier_definition(name):
    from . import nodes
    return next(t for t in NPC_TIERS + NPC_SEA_TIERS + [nodes.TIER, nodes.CAPITAL_TIER] if t["name"] == name)


def _is_tutorial(q, r):
    # Tutorial garrisons sit directly south of a base on the spaced grid.
    return (q, r - 1) in set(bases.candidates())


def blocks_path(db, c, pid, sites, biome="plain"):
    """Untaken pickups and ruins, unowned/foreign mines can only be a destination; camps never block."""
    obj = placed(c[0], c[1], sites, biome)
    if not obj or obj["kind"] == "camp":
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
    if obj["kind"] == "camp":
        return camp_view(db, q, r, obj)
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
    if obj["kind"] == "camp":
        view = camp_view(db, q, r, obj)
        return f"Лагерь наёмников: {view['name']} · {view['count']}" + ("" if view["available"] else " (на этой неделе уже наняты)")
    if obj["kind"] == "mine":
        mine = db.get(MapMine, (1, q, r))
        if mine and mine.player_id != p.id:
            return "Шахта принадлежит другому командиру."
        if not mine:
            db.add(MapMine(world_id=1, q=q, r=r, player_id=p.id, resource=obj["resource"], rate=obj["rate"], acquired_at=at_time))
            return f"Шахта захвачена: +{obj['rate']} в минуту"
        return None
    won = db.execute(insert(MapPickup).values(world_id=1, q=q, r=r, kind=obj["kind"], player_id=p.id,
        taken_at=at_time, choice=None if obj["kind"] == "chest" else "resources")
        .on_conflict_do_nothing().returning(MapPickup.q)).scalar()
    if won is None:
        return "Здесь уже побывал другой отряд."
    if obj["kind"] == "ruin":
        return explore_ruin(db, p, q, r, at_time, change)
    if obj["kind"] == "pile":
        from . import commander
        from . import seasons
        amount = round(obj["amount"] * (1 + commander.perk(db, p.id, "plunder")) * seasons.effect(db, "pickups", at_time))
        change(db, p, {obj["resource"]: amount}, "map_pile")
        return f"Найдено: +{amount} ({obj['resource']})"
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


# ---- ruins and camps --------------------------------------------------------

def explore_ruin(db, p, q, r, at_time, change):
    """One-time Polytopia-style ruin: a fixed outcome per hex for whoever arrives first."""
    import uuid
    from .models import Unit, Item, Ownership, Army, ArmyUnit
    from . import equipment
    outcome = RUIN_OUTCOMES[_roll(q, r, "ruin-outcome") % len(RUIN_OUTCOMES)]
    if outcome == "cache":
        change(db, p, {"metal": 400, "electronics": 100, "fuel": 100}, "ruin_cache")
        return "Руины: тайник со снабжением (+400 металла, +100 электроники, +100 топлива)"
    if outcome == "xp":
        db.get(Hero, p.id).xp += 150
        return "Руины: архив штаба. Командир получает 150 опыта"
    if outcome == "artifact":
        key, roll = equipment.loot(f"ruin:{q}:{r}", 1)
        item = Item(id=str(uuid.uuid4()), owner_id=p.id, definition_id=key, source_id=f"ruin:{q}:{r}", equipped=False, created_at=at_time)
        db.add(item); db.flush()
        db.add(Ownership(id=str(uuid.uuid4()), item_id=item.id, owner_id=p.id, reason="ruin", created_at=at_time))
        return f"Руины: найден артефакт «{equipment.DEFINITIONS[key]['name']}»"
    if outcome == "recruits":
        hero = db.get(Hero, p.id)
        key = next(v["key"] for v in FACTIONS[hero.kind]["units"] if v["role"] == "rifles")
        db.add(Unit(id=str(uuid.uuid4()), player_id=p.id, kind=key, hp=100, count=6, status="reserve"))
        return f"Руины: уцелевшие бойцы присоединяются ({UNITS[key]['name']} · 6, в резерве на базе)"
    from .models import Tile, Discovery
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    tiles = db.scalars(select(Tile).where(Tile.world_id == 1, Tile.q.between(q - 6, q + 6), Tile.r.between(r - 6, r + 6)))
    values = [dict(player_id=p.id, world_id=1, q=t.q, r=t.r, discovered_at=at_time) for t in tiles
              if max(abs(t.q - q), abs(t.r - r), abs(t.q + t.r - q - r)) <= 6]
    if values:
        db.execute(pg_insert(Discovery).values(values).on_conflict_do_nothing())
    return "Руины: старые карты. Открыта местность на 6 гексов вокруг"


def camp_view(db, q, r, obj=None):
    import time
    from .models import CampHire
    from . import seasons
    obj = obj or at(db, q, r)
    kind = obj["unit"]
    cal = seasons.calendar(seasons.current(db), int(time.time()))
    week, season = (cal["week"], cal["season"]) if cal else (0, 0)
    hired = db.get(CampHire, (1, q, r, season, week))
    spec = UNITS[kind]
    return {"kind": "camp", "unit": kind, "name": spec["name"], "count": spec["count"], "faction": spec.get("faction"),
            "cost": {k: round(v * CAMP_PREMIUM) for k, v in spec["cost"].items()}, "available": hired is None,
            "week": week}


def hire(db, p, army_id, at_time, change):
    """Hire the camp's weekly stack with an army standing on the camp."""
    import uuid
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from .models import Army, ArmyUnit, Unit, CampHire
    from .config import ARMY_STACKS
    army = db.get(Army, army_id)
    if not army or army.player_id != p.id:
        raise HTTPException(404, "Соединение не найдено")
    if army.status != "idle":
        raise HTTPException(409, "Соединение в пути")
    obj = at(db, army.q, army.r)
    if not obj or obj["kind"] != "camp":
        raise HTTPException(409, "Здесь нет лагеря наёмников")
    view = camp_view(db, army.q, army.r, obj)
    db.scalar(select(Tile).where(Tile.world_id == 1, Tile.q == army.q, Tile.r == army.r).with_for_update())
    from . import seasons
    season = seasons.current(db)
    won = db.execute(pg_insert(CampHire).values(world_id=1, q=army.q, r=army.r, season=season.number if season else 0,
                     week=view["week"], player_id=p.id, kind=view["unit"], hired_at=at_time)
                     .on_conflict_do_nothing().returning(CampHire.q)).scalar()
    if won is None:
        raise HTTPException(409, "На этой неделе наёмников уже наняли. Новые придут через игровую неделю")
    change(db, p, {k: -v for k, v in view["cost"].items()}, "mercenaries")
    unit = Unit(id=str(uuid.uuid4()), player_id=p.id, kind=view["unit"], hp=100, count=view["count"], status="reserve")
    db.add(unit); db.flush()
    stacks = db.scalars(select(ArmyUnit).where(ArmyUnit.army_id == army.id)).all()
    if len(stacks) < ARMY_STACKS:
        db.add(ArmyUnit(army_id=army.id, unit_id=unit.id)); unit.status = "army"
    return {"unit_id": unit.id, "kind": unit.kind, "joined": unit.status == "army"}
