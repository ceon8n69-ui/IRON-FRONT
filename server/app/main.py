import mimetypes
import asyncio, json, os, secrets, time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
import redis
from redis.backoff import NoBackoff
from redis.retry import Retry
from fastapi import (
    FastAPI,
    HTTPException,
    Header,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from . import config, expeditions, garrisons, bases, objects, pvp, commander, equipment
from .db import SessionLocal
from .models import Player, Session, Resource, Building, Hero, Tile, BattleTurn, Ledger, TileOwnership, Discovery, Army
from .auth import validate_init_data, token_hash
from .game import uid, now, settle, snapshot, execute

cache = redis.Redis.from_url(
    config.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
    retry=Retry(NoBackoff(), 0),
)
app = FastAPI(title="IRON FRONT", version="0.17.0")
# Map windows are large, repetitive JSON: compress responses for mobile networks.
app.add_middleware(GZipMiddleware, minimum_size=1024)


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Login(Strict):
    init_data: str = Field(max_length=8192)


class Choose(Strict):
    kind: str = Field(max_length=30)


class Build(Choose):
    q: int = Field(ge=-4, le=4)
    r: int = Field(ge=-4, le=4)


class Chest(Strict):
    q: int = Field(ge=0, le=127)
    r: int = Field(ge=0, le=127)
    choice: Literal["resources", "xp"]


class Upgrade(Strict):
    building_id: str = Field(max_length=40)


class StartBattle(Strict):
    unit_id: str = Field(max_length=40)


class March(Strict):
    army_id: str = Field(max_length=40)
    action: Literal["move", "capture", "attack"]
    q: int = Field(ge=0, le=127)
    r: int = Field(ge=0, le=127)


class Turn(Strict):
    battle_id: str = Field(max_length=40)
    turn: int = Field(ge=1, le=50)
    action: Literal["move", "attack", "defend", "wait", "ability", "skill"]
    q: int = Field(default=0, ge=0, le=8)
    r: int = Field(default=0, ge=0, le=8)
    target: str | None = Field(default=None, max_length=20)


class Train(Strict):
    kind: str = Field(default="rifles", max_length=20)


class Compose(Strict):
    unit_id: str = Field(max_length=40)
    army_id: str | None = Field(default=None, max_length=40)


class SkillPick(Strict):
    key: str = Field(max_length=40)


class BattleRef(Strict):
    battle_id: str = Field(max_length=40)


class ArmyRef(Strict):
    army_id: str = Field(max_length=40)


class Equip(Strict):
    item_id: str = Field(max_length=40)
    equipped: bool


# Redis handles shared rate limits; PostgreSQL remains authoritative.
def rate_limit(key, limit=120):
    try:
        # INCR and EXPIRE together, so a crash cannot leave an immortal key.
        value = cache.eval(
            "local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],60) end; return n",
            1,
            "rate:" + key,
        )
        if value > limit:
            raise HTTPException(429, "Слишком много запросов")
    except redis.RedisError:
        if config.ENV == "production":
            raise HTTPException(503, "Сервис временно недоступен")


def identify(db, authorization):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Требуется вход")
    session = db.get(Session, token_hash(authorization[7:]))
    if not session or session.expires_at <= now():
        raise HTTPException(401, "Сессия истекла")
    return session.player_id


def locked(db, pid):
    return db.scalar(select(Player).where(Player.id == pid).with_for_update())


@app.get("/health")
def health():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        cache.ping()
    except Exception:
        raise HTTPException(503, "Dependencies unavailable")
    return {"status": "ok", "version": config.VERSION}


@app.post("/api/v1/auth/telegram")
def login(body: Login, request: Request):
    rate_limit("auth:" + request.client.host, 30)
    user = validate_init_data(body.init_data, config.BOT_TOKEN)
    with SessionLocal.begin() as db:
        # Serialize concurrent first logins for the same Telegram account.
        db.execute(text("SELECT pg_advisory_xact_lock(:id)"), {"id": user["id"]})
        player = db.scalar(select(Player).where(Player.telegram_id == user["id"]))
        if not player:
            player = Player(
                id=uid(),
                telegram_id=user["id"],
                name=str(user.get("first_name", "Командир"))[:100],
                created_at=now(),
                settled_at=now(),
                revision=0,
                shield_until=now() + config.PVP["newbie_seconds"],
                upkeep_at=now(),
            )
            db.add(player)
            db.flush()
            db.add_all(
                [
                    Resource(player_id=player.id, kind=k, amount=v)
                    for k, v in config.INITIAL.items()
                ]
            )
            db.add_all(
                [
                    Ledger(
                        id=uid(),
                        player_id=player.id,
                        kind=k,
                        delta=v,
                        after=v,
                        operation="initial_grant",
                        created_at=now(),
                    )
                    for k, v in config.INITIAL.items()
                ]
            )
            db.add(
                Building(
                    id=uid(),
                    player_id=player.id,
                    kind="hq",
                    q=0,
                    r=0,
                    level=1,
                    ready_at=now(),
                    status="ready",
                )
            )
            bases.ensure(db, player, now())
        token = secrets.token_urlsafe(32)
        db.add(
            Session(
                token_hash=token_hash(token),
                player_id=player.id,
                expires_at=now() + 86400,
            )
        )
    return {"token": token, "expires_at": now() + 86400}


@app.get("/api/v1/config")
def definitions():
    return {
        "buildings": config.BUILDINGS,
        "heroes": config.HEROES,
        "units": config.UNITS,
        "abilities": config.ABILITIES,
        "skills": {k: {"name": v["name"], "icon": v["icon"]} for k, v in commander.SKILLS.items()},
        "artifacts": equipment.DEFINITIONS,
        "artifact_slots": equipment.SLOTS,
        "factions": config.FACTIONS,
        "traits": config.TRAITS,
        "army_stacks": config.ARMY_STACKS,
        "expeditions": config.EXPEDITIONS,
        "balance_version": config.VERSION,
        "offline_hours": 24,
        "storage_cap": config.BASE_STORAGE,
        "max_level": config.MAX_LEVEL,
    }


@app.get("/api/v1/player/me")
def me(authorization: str | None = Header(default=None)):
    with SessionLocal.begin() as db:
        pid = identify(db, authorization)
        rate_limit(pid)
        p = locked(db, pid)
        settle(db, p)
        return snapshot(db, p)


def mutate(op, body, authorization, key):
    if not key or not 8 <= len(key) <= 100:
        raise HTTPException(400, "Нужен Idempotency-Key длиной 8–100 символов")
    with SessionLocal.begin() as db:
        pid = identify(db, authorization)
        rate_limit(pid)
        return execute(db, locked(db, pid), op, body, key)


@app.post("/api/v1/heroes/choose")
def choose(
    body: Choose,
    authorization: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None),
):
    return mutate("hero", body.model_dump(), authorization, idempotency_key)


@app.post("/api/v1/construction/start")
def build(
    body: Build,
    authorization: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None),
):
    return mutate("build", body.model_dump(), authorization, idempotency_key)


@app.post("/api/v1/world/chest")
def chest(
    body: Chest,
    authorization: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None),
):
    return mutate("chest", body.model_dump(), authorization, idempotency_key)


@app.post("/api/v1/construction/upgrade")
def upgrade(
    body: Upgrade,
    authorization: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None),
):
    return mutate("upgrade", body.model_dump(), authorization, idempotency_key)


@app.post("/api/v1/army/train")
def train(
    body: Train | None = None,
    authorization: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None),
):
    return mutate("train", (body or Train()).model_dump(), authorization, idempotency_key)


@app.post("/api/v1/army/assign")
def army_assign(body: Compose, authorization: str | None = Header(default=None),
                idempotency_key: str | None = Header(default=None)):
    return mutate("army_assign", body.model_dump(), authorization, idempotency_key)


@app.post("/api/v1/army/release")
def army_release(body: Compose, authorization: str | None = Header(default=None),
                 idempotency_key: str | None = Header(default=None)):
    return mutate("army_release", body.model_dump(), authorization, idempotency_key)


@app.post("/api/v1/battles/auto")
def battle_auto(body: BattleRef, authorization: str | None = Header(default=None),
                idempotency_key: str | None = Header(default=None)):
    return mutate("auto", body.model_dump(), authorization, idempotency_key)


class DoctrineRef(Strict):
    key: str = Field(max_length=40)


class AllianceCreate(Strict):
    name: str = Field(min_length=3, max_length=24)
    tag: str = Field(min_length=2, max_length=5)


class AllianceJoin(Strict):
    code: str = Field(min_length=4, max_length=12)


class AllianceKick(Strict):
    player_id: str = Field(max_length=40)


class Empty(Strict):
    pass


@app.post("/api/v1/alliance/create")
def alliance_create(body: AllianceCreate, authorization: str | None = Header(default=None),
                    idempotency_key: str | None = Header(default=None)):
    return mutate("alliance_create", body.model_dump(), authorization, idempotency_key)


@app.post("/api/v1/alliance/join")
def alliance_join(body: AllianceJoin, authorization: str | None = Header(default=None),
                  idempotency_key: str | None = Header(default=None)):
    return mutate("alliance_join", body.model_dump(), authorization, idempotency_key)


@app.post("/api/v1/alliance/leave")
def alliance_leave(body: Empty, authorization: str | None = Header(default=None),
                   idempotency_key: str | None = Header(default=None)):
    return mutate("alliance_leave", body.model_dump(), authorization, idempotency_key)


@app.post("/api/v1/alliance/kick")
def alliance_kick(body: AllianceKick, authorization: str | None = Header(default=None),
                  idempotency_key: str | None = Header(default=None)):
    return mutate("alliance_kick", body.model_dump(), authorization, idempotency_key)


@app.post("/api/v1/doctrines/research")
def doctrine_research(body: DoctrineRef, authorization: str | None = Header(default=None),
                      idempotency_key: str | None = Header(default=None)):
    return mutate("doctrine", body.model_dump(), authorization, idempotency_key)


@app.post("/api/v1/world/hire")
def world_hire(body: ArmyRef, authorization: str | None = Header(default=None),
               idempotency_key: str | None = Header(default=None)):
    return mutate("hire", body.model_dump(), authorization, idempotency_key)


@app.post("/api/v1/commander/skill")
def commander_skill(body: SkillPick, authorization: str | None = Header(default=None),
                    idempotency_key: str | None = Header(default=None)):
    return mutate("skill_pick", body.model_dump(), authorization, idempotency_key)


@app.post("/api/v1/army/disband")
def army_disband(body: ArmyRef, authorization: str | None = Header(default=None),
                 idempotency_key: str | None = Header(default=None)):
    return mutate("army_disband", body.model_dump(), authorization, idempotency_key)


@app.post("/api/v1/army/lead")
def army_lead(body: ArmyRef, authorization: str | None = Header(default=None),
              idempotency_key: str | None = Header(default=None)):
    return mutate("army_lead", body.model_dump(), authorization, idempotency_key)


@app.post("/api/v1/army/create")
def create_army(body: StartBattle, authorization: str | None = Header(default=None),
                idempotency_key: str | None = Header(default=None)):
    return mutate("army_create", body.model_dump(), authorization, idempotency_key)


@app.post("/api/v1/army/orders")
def army_order(body: March, authorization: str | None = Header(default=None),
               idempotency_key: str | None = Header(default=None)):
    return mutate("army_order", body.model_dump(), authorization, idempotency_key)


@app.post("/api/v1/battles")
def battle(
    body: StartBattle,
    authorization: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None),
):
    return mutate("battle", body.model_dump(), authorization, idempotency_key)


@app.post("/api/v1/battles/commands")
def turn(
    body: Turn,
    authorization: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None),
):
    return mutate("turn", body.model_dump(), authorization, idempotency_key)


@app.post("/api/v1/equipment/equip")
def equip(
    body: Equip,
    authorization: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None),
):
    return mutate("equip", body.model_dump(), authorization, idempotency_key)


@app.get("/api/v1/battles/{battle_id}/replay")
def replay(battle_id: str, authorization: str | None = Header(default=None)):
    from .models import Battle

    with SessionLocal() as db:
        pid = identify(db, authorization)
        b = db.get(Battle, battle_id)
        if not b or b.player_id != pid:
            raise HTTPException(404, "Бой не найден")
        return {
            "seed": b.seed if b.status != "active" else None,
            "balance_version": b.balance_version,
            "turns": [
                {"turn": t.turn, "command": t.command, "events": t.events}
                for t in db.scalars(
                    select(BattleTurn)
                    .where(BattleTurn.battle_id == b.id)
                    .order_by(BattleTurn.turn)
                )
            ],
        }


@app.get("/api/v1/army/route")
def army_route(q: int, r: int, army_id: str | None = None, authorization: str | None = Header(default=None)):
    """Read-only preview of the cheapest route for the player's army."""
    if not 0 <= q < 128 or not 0 <= r < 128:
        raise HTTPException(422, "Недопустимые координаты")
    with SessionLocal.begin() as db:
        pid = identify(db, authorization)
        rate_limit(pid)
        p = locked(db, pid)
        settle(db, p)
        mine = expeditions.armies(db, pid)
        army = next((a for a in mine if a.id == army_id), None) if army_id else next((a for a in mine if a.commander), mine[0] if mine else None)
        if not army:
            raise HTTPException(409, "Сформируйте соединение в разделе «Армия»")
        if (q, r) == (army.q, army.r):
            raise HTTPException(409, "Соединение уже на этом гексе")
        steps, cost = expeditions.route(db, p, army, (q, r), now())
        rules = config.EXPEDITIONS
        return {"path": [[sq, sr, c] for sq, sr, c in steps], "cost": cost,
                "fuel": rules["fuel"] * len(steps), "seconds": cost * rules["step_seconds"],
                "movement": army.movement, "affordable": cost <= army.movement}


@app.get("/api/v1/season")
def season(authorization: str | None = Header(default=None)):
    """Season standings, calendar, scoring rules, last winners and the player's medals."""
    from . import seasons
    with SessionLocal.begin() as db:
        pid = identify(db, authorization)
        rate_limit(pid)
        p = locked(db, pid)
        settle(db, p)
        return seasons.leaderboard(db, pid)


@app.get("/api/v1/world/target")
def world_target(q: int, r: int, authorization: str | None = Header(default=None)):
    """Scout report on another commander's holding within your sight."""
    if not 0 <= q < 128 or not 0 <= r < 128:
        raise HTTPException(422, "Недопустимые координаты")
    with SessionLocal.begin() as db:
        pid = identify(db, authorization)
        rate_limit(pid)
        p = locked(db, pid)
        settle(db, p)
        if not expeditions.visible(db, pid, q, r):
            raise HTTPException(404, "Цель вне зоны видимости")
        info = pvp.preview(db, pid, q, r, now())
        if not info:
            raise HTTPException(404, "Здесь нет владений другого командира")
        return info


@app.get("/api/v1/world/tiles")
def tiles(
    q: int = 64,
    r: int = 64,
    radius: int = 4,
    hw: float | None = None,
    hh: float | None = None,
    authorization: str | None = Header(default=None),
):
    """Tiles around (q, r): an axial square of `radius`, or — with hw/hh, the half-width and
    half-height of the viewport in hexes — just the screen-shaped window the camera sees."""
    if not 0 <= q < 128 or not 0 <= r < 128 or not 1 <= radius <= 8:
        raise HTTPException(422, "Недопустимый чанк")
    view = None
    if hw is not None or hh is not None:
        if hw is None or hh is None or not 0 < hw <= 14 or not 0 < hh <= 26:
            raise HTTPException(422, "Недопустимое окно карты")
        view = (int(hw) + 1, int(hh) + 1)
        radius = view[0] + (view[1] + 1) // 2
    with SessionLocal.begin() as db:
        pid = identify(db, authorization)
        rate_limit(pid)
        p = locked(db,pid)
        settle(db,p)
        ts = list(db.scalars(select(Tile).where(Tile.world_id == 1,
            Tile.q.between(q-radius,q+radius),Tile.r.between(r-radius,r+radius))))
        if view:
            ts = [t for t in ts if abs(t.r-r) <= view[1] and abs((t.q-q)+(t.r-r)/2) <= view[0]]
        discovered = {(t.q,t.r) for t in db.scalars(select(Discovery).where(
            Discovery.player_id == pid, Discovery.world_id == 1,
            Discovery.q.between(q-radius,q+radius), Discovery.r.between(r-radius,r+radius)))}
        owners = {(t.q,t.r):t.player_id for t in db.scalars(select(TileOwnership).where(
            TileOwnership.world_id==1,TileOwnership.q.between(q-radius,q+radius),TileOwnership.r.between(r-radius,r+radius)))}
        home = bases.home(db,pid)
        sites = bases.near(db,q,r,radius+bases.SAFE_RADIUS+2)
        cleared = garrisons.cleared_in(db,q,r,radius)
        army_state = expeditions.state(db,pid)["armies"]
        home_vision = expeditions.home_vision(db,pid)
        from .combat import distance
        from . import logistics, nodes
        radar = logistics.radars(db,pid)
        from . import raids as raid_mod, alliances
        raid_hexes = raid_mod.active_in(db,q,r,radius)
        friends = alliances.ally_ids(db,pid)
        supply = logistics.supplied(db,pid)
        result=[]
        for t in ts:
            in_view = distance(home,[t.q,t.r]) <= home_vision or any(distance([a["q"],a["r"]],[t.q,t.r]) <= a.get("vision", config.EXPEDITIONS["army_vision"]) for a in army_state) \
                or any(distance([rq,rr],[t.q,t.r]) <= rv for rq,rr,rv in radar)
            known = in_view or (t.q,t.r) in discovered
            owner = owners.get((t.q,t.r)) if in_view else None
            site = (t.q,t.r) in sites
            raid = raid_hexes.get((t.q,t.r))
            if raid and not in_view and raid.player_id != pid:
                raid = None   # the threatened commander always sees the band; others need sight
            guarded = bool(raid) or bool(in_view and not owner and not site and (t.q,t.r) not in cleared and garrisons.guarded(t.q,t.r,sites,t.biome))
            tier = raid_mod.strength(raid) if raid else objects.strength(t.q,t.r,t.biome,sites) if guarded else None
            base = None
            if site and in_view:
                base = "self" if sites[(t.q,t.r)] == pid else "ally" if sites[(t.q,t.r)] in friends else "other"
            if not known and not raid:
                # Unscouted hex: geography only, kept tiny since zoomed-out windows hold ~1000 of them.
                result.append({"id":f"1:{t.q}:{t.r}","q":t.q,"r":t.r,"biome":"unknown","terrain":t.biome,"visibility":"unknown","home":False,"control":None,"base":None})
                continue
            result.append({"id":f"1:{t.q}:{t.r}","q":t.q,"r":t.r,
                "biome":t.biome if known else "unknown",
                "terrain":None if known else t.biome,   # geography only: contents stay hidden until scouted
                "garrison":guarded,
                "garrison_strength":{"name":tier[0],"hp":tier[1],"xp":tier[2]} if tier else None,
                "object":objects.view(db,pid,t.q,t.r,sites,t.biome) if in_view and not site else None,
                "visibility":"visible" if in_view else "explored" if known else "unknown",
                "control":("self" if owner == pid else "ally" if owner in friends else "other" if owner else "neutral") if in_view else None,
                "raid":{"strikes_at":raid.strikes_at,"target":[raid.target_q,raid.target_r],"mine":raid.player_id == pid} if raid else None,
                "home":[t.q,t.r] == home,
                "node":nodes.view(nodes.at(t.q,t.r,t.biome,sites)) if known else None,
                "supplied":((t.q,t.r) in supply) if owner == pid else None,
                "base":base})
        return {"tiles":result}


@app.websocket("/api/v1/ws")
async def ws(socket: WebSocket):
    await socket.accept()
    try:
        message = await asyncio.wait_for(socket.receive_json(), timeout=5)
        with SessionLocal() as db:
            pid = identify(db, "Bearer " + str(message.get("token", "")))
        rate_limit("ws:" + pid, 20)
        last = -1
        while True:
            # Snapshot protocol: reconnect always sends complete authorized state.
            # Blocking SQL runs in a thread; per-player locks coordinate with worker.
            def read():
                with SessionLocal.begin() as db:
                    identify(db, "Bearer " + str(message["token"]))
                    p = locked(db, pid)
                    settle(db, p)
                    return snapshot(db, p)

            state = await asyncio.to_thread(read)
            if state["revision"] != last:
                await socket.send_json({"type": "snapshot", "state": state})
                last = state["revision"]
            else:
                await socket.send_json({"type": "heartbeat", "server_time": now()})
            await asyncio.sleep(2)
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    except HTTPException:
        await socket.close(code=4401)


# Debian slim may lack the system MIME database used on CI runners.
mimetypes.add_type("image/webp", ".webp")

# Repository layout: server/app -> repo/client.
static = Path(__file__).resolve().parents[2] / "client" / "dist"
if static.exists():
    app.mount("/assets", StaticFiles(directory=static / "assets"), name="assets")
    if (static / "art").is_dir():
        app.mount("/art", StaticFiles(directory=static / "art"), name="art")

    @app.get("/")
    def index():
        return FileResponse(static / "index.html")
