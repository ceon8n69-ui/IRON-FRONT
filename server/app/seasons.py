"""Seasons and the in-game calendar.

A season lasts two real weeks. Inside it, Heroes-style time runs fast:
one in-game day = 4 real hours (every army refills its movement points at
dawn), one in-game week = 6 days = one real day, with a weekly event.
"""
import hashlib
from sqlalchemy import select
from .models import Season

DAY = 4 * 3600
DAYS_PER_WEEK = 6
SEASON_SECONDS = 14 * 24 * 3600

# Weekly events (fictional). Effects are read by economy, training, movement and upkeep.
EVENTS = [
    {"key": "infantry", "name": "Неделя пехоты", "about": "Подготовка пехоты дешевле на 25 %",
     "effects": {"infantry_cost": 0.75}},
    {"key": "armor", "name": "Неделя брони", "about": "Техника готовится на 40 % быстрее",
     "effects": {"vehicle_time": 0.6}},
    {"key": "harvest", "name": "Неделя изобилия", "about": "Производство базы +20 %",
     "effects": {"production": 1.2}},
    {"key": "fog", "name": "Туман войны", "about": "Обзор соединений −1",
     "effects": {"army_vision": -1}},
    {"key": "mud", "name": "Распутица", "about": "Лес, холмы и броды стоят на 1 очко хода дороже",
     "effects": {"rough_cost": 1}},
    {"key": "supply", "name": "Неделя снабжения", "about": "Содержание войск вдвое дешевле",
     "effects": {"upkeep": 0.5}},
    {"key": "spoils", "name": "Неделя трофеев", "about": "Находки на карте +50 %",
     "effects": {"pickups": 1.5}},
]


def current(db):
    """The active season (the latest one), cached for the session's lifetime."""
    if "season" not in db.info:
        db.info["season"] = db.scalar(select(Season).order_by(Season.number.desc()).limit(1))
    return db.info["season"]


def calendar(season, at):
    if not season:
        return None
    elapsed = max(0, at - season.started_at)
    day_index = elapsed // DAY
    week = day_index // DAYS_PER_WEEK + 1
    return {
        "season": season.number,
        "day": day_index % DAYS_PER_WEEK + 1,
        "week": week,
        "day_index": day_index,
        "day_started_at": season.started_at + day_index * DAY,
        "next_day_at": season.started_at + (day_index + 1) * DAY,
        "ends_at": season.ends_at,
        "event": event(season, week),
    }


def event(season, week):
    roll = int(hashlib.sha256(f"week-event-1:{season.seed}:{week}".encode()).hexdigest()[:8], 16)
    return EVENTS[roll % len(EVENTS)]


def effect(db, key, at, default=1):
    """Current weekly modifier, or `default` when this week has no such effect."""
    season = current(db)
    cal = calendar(season, at)
    return cal["event"]["effects"].get(key, default) if cal else default


def day_start(db, at):
    season = current(db)
    if not season:
        return None
    return calendar(season, at)["day_started_at"]


# ---- scoring ----------------------------------------------------------------

VP_EVENTS = {"garrison": 10, "fortress": 40, "capital": 100, "pvp_attack": 25, "pvp_defence": 15}
TITLES = [(1, "Маршал сезона"), (3, "Генерал сезона"), (10, "Полковник сезона")]


def award(p, reason):
    p.vp += VP_EVENTS[reason]


def accrue(db, p, ticks, at):
    """Victory points for supplied nodes held during the settled minutes."""
    if ticks <= 0:
        return 0
    from .models import TileOwnership
    from . import logistics, nodes
    supply = logistics.supplied(db, p.id)
    gained = 0
    for t in db.scalars(select(TileOwnership).where(TileOwnership.player_id == p.id)):
        if (t.q, t.r) not in supply:
            continue
        kind = logistics.node_kind(db, t.q, t.r)
        if kind:
            held = max(0, min(ticks, (at - t.acquired_at) // 60))
            gained += held * nodes.VP_PER_MINUTE[kind]
    p.vp += gained
    return gained


def title_for(rank):
    return next((t for limit, t in TITLES if rank <= limit), "Ветеран сезона")


def leaderboard(db, pid, limit=20):
    from sqlalchemy import func
    from . import alliances
    from .models import Player, Hero, SeasonResult
    season = current(db)
    rows = list(db.execute(select(Player.id, Player.name, Player.vp, Hero.kind)
                           .join(Hero, Hero.player_id == Player.id)
                           .order_by(Player.vp.desc(), Player.created_at, Player.id).limit(limit)))
    me = db.get(Player, pid)
    rank = (db.scalar(select(func.count()).select_from(Player).join(Hero, Hero.player_id == Player.id)
                      .where(Player.vp > me.vp)) or 0) + 1
    last = None
    if season and season.number > 1:
        prev = db.get(Season, season.number - 1)
        last = {"season": prev.number, "top": (prev.results or {}).get("top", [])[:3]} if prev else None
    medals = [{"season": r.season, "rank": r.rank, "title": r.title, "vp": r.vp}
              for r in db.scalars(select(SeasonResult).where(SeasonResult.player_id == pid).order_by(SeasonResult.season.desc()))]
    return {
        "calendar": calendar(season, _now()),
        "top": [{"rank": i + 1, "name": n, "vp": vp, "hero": h, "me": i_d == pid} for i, (i_d, n, vp, h) in enumerate(rows)],
        "me": {"rank": rank, "vp": me.vp},
        "rules": {"node_vp_per_hour": 60, "capital_vp_per_hour": 300, **VP_EVENTS},
        "last": last,
        "medals": medals,
        "alliances": alliances.ranking(db),
        "alliance": alliances.view(db, pid),
    }


def _now():
    import time
    return int(time.time())


# ---- rollover -----------------------------------------------------------------

LOCK = (1717, 2)
STARTER_BUILDINGS = [("power", 1, 0), ("barracks", 0, 1), ("quarry", -1, 1), ("farm", -1, 0)]


def due(db, at):
    season = current(db)
    return bool(season and season.status == "active" and season.ends_at <= at)


def rollover(db, at, seed=None):
    """Finish the current season and start the next one on a fresh map.

    Runs in one transaction from the worker. Final standings are archived in
    seasons.results and season_results (kept forever); every season-scoped row
    is wiped; each commander keeps their account, chosen commander and medals,
    and starts with a small kit. Returns the new season number, or None.
    """
    import os, secrets, uuid
    from sqlalchemy import text, delete, update
    from .models import (Player, Hero, SeasonResult, Resource, Ledger, Building, Unit, Reward, Battle, BattleTurn,
                         PvpReport, Army, ArmyUnit, ArmyOrder, Item, Ownership, Job, MapPickup, MapMine,
                         ClearedSite, TileOwnership, Discovery, WorldBase, Command, Tile, Event, Doctrine, Raid)
    from .config import INITIAL, FACTIONS, UNITS
    from . import worldgen, nodes
    db.execute(text("SELECT pg_advisory_xact_lock(:a, :b)"), {"a": LOCK[0], "b": LOCK[1]})
    db.info.pop("season", None)
    season = current(db)
    if not season or season.status != "active" or season.ends_at > at:
        return None
    # Stop the world: requests take ROW SHARE on users; this waits for them and holds new ones.
    db.execute(text(f"LOCK TABLE {_qualified(db, 'users')} IN SHARE ROW EXCLUSIVE MODE"))
    standings = list(db.execute(select(Player.id, Player.name, Player.vp, Hero.kind)
                                .join(Hero, Hero.player_id == Player.id)
                                .order_by(Player.vp.desc(), Player.created_at, Player.id)))
    top = []
    for i, (pid, name, vp, hero) in enumerate(standings):
        rank = i + 1
        db.add(SeasonResult(season=season.number, player_id=pid, rank=rank, vp=vp, title=title_for(rank), hero=hero, name=name))
        if rank <= 100:
            top.append({"rank": rank, "name": name, "vp": vp, "hero": hero, "title": title_for(rank)})
    season.results = {"top": top, "players": len(standings), "finished_at": at}
    season.status = "finished"
    db.flush()
    # Wipe season-scoped state (children first).
    for model in (BattleTurn, PvpReport, Reward, Ownership):
        db.execute(delete(model))
    db.execute(delete(Battle))
    for model in (ArmyOrder, ArmyUnit):
        db.execute(delete(model))
    db.execute(delete(Army))
    for model in (Item, Job, Unit, Building, MapPickup, MapMine, ClearedSite, TileOwnership, Discovery, WorldBase, Command,
                  Doctrine, Raid):
        db.execute(delete(model))
    # New map.
    new_seed = seed or f"season-{season.number + 1}-{secrets.token_hex(4)}"
    world = dict(worldgen.generate(new_seed))
    cq, cr = nodes.CAPITAL
    for (q, r), b in list(world.items()):
        if max(abs(q - cq), abs(r - cr), abs(q + r - cq - cr)) <= 2 and b in ("sea", "lake", "river", "mountain"):
            world[(q, r)] = "plain"
    from sqlalchemy import bindparam
    stmt = update(Tile).where(Tile.world_id == 1, Tile.q == bindparam("tq"), Tile.r == bindparam("tr")) \
        .values(biome=bindparam("tb")).execution_options(synchronize_session=False)
    rows = [{"tq": q, "tr": r, "tb": b} for (q, r), b in world.items()]
    for start in range(0, len(rows), 4000):
        db.connection().execute(stmt, rows[start:start + 4000])
    nxt = Season(number=season.number + 1, seed=new_seed, started_at=at, ends_at=at + SEASON_SECONDS, status="active")
    db.add(nxt)
    db.flush()
    db.info["season"] = nxt
    # Fresh start for every commander.
    heroes = {h.player_id: h for h in db.scalars(select(Hero))}
    for p in db.scalars(select(Player)):
        p.vp, p.settled_at, p.upkeep_at = 0, at, at
        p.shield_until = at + 24 * 3600          # everyone gets a day to set up
        p.tutorial_done = p.tutorial_done or p.id in heroes
        for res in db.scalars(select(Resource).where(Resource.player_id == p.id)):
            delta = INITIAL[res.kind] - res.amount
            res.amount = INITIAL[res.kind]
            if delta:
                db.add(Ledger(id=str(uuid.uuid4()), player_id=p.id, kind=res.kind, delta=delta, after=res.amount,
                              operation="season_reset", created_at=at))
        db.add(Building(id=str(uuid.uuid4()), player_id=p.id, kind="hq", q=0, r=0, level=1, ready_at=at, status="ready"))
        hero = heroes.get(p.id)
        if hero:
            hero.xp, hero.skills = 0, {}
            for kind, q, r in STARTER_BUILDINGS:
                db.add(Building(id=str(uuid.uuid4()), player_id=p.id, kind=kind, q=q, r=r, level=1, ready_at=at, status="ready"))
            roster = {v["role"]: v["key"] for v in FACTIONS[hero.kind]["units"]}
            for role in ("rifles", "scouts"):
                key = roster[role]
                db.add(Unit(id=str(uuid.uuid4()), player_id=p.id, kind=key, hp=100, count=UNITS[key]["count"], status="reserve"))
        p.revision += 1
        db.add(Event(player_id=p.id, revision=p.revision, kind="season", created_at=at))
    db.flush()
    return nxt.number


def _qualified(db, table):
    """Table name honouring a schema_translate_map (used by the isolated test schemas)."""
    schema = (db.connection().get_execution_options().get("schema_translate_map") or {}).get(None)
    return f'"{schema}".{table}' if schema else table
