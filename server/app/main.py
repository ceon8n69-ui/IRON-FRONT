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
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from . import config
from .db import SessionLocal
from .models import Player, Session, Resource, Building, Hero, Tile, BattleTurn, Ledger
from .auth import validate_init_data, token_hash
from .game import uid, now, settle, snapshot, execute

cache = redis.Redis.from_url(
    config.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
    retry=Retry(NoBackoff(), 0),
)
app = FastAPI(title="IRON FRONT", version="0.1.0")


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Login(Strict):
    init_data: str = Field(max_length=8192)


class Choose(Strict):
    kind: str = Field(max_length=30)


class Build(Choose):
    q: int = Field(ge=-4, le=4)
    r: int = Field(ge=-4, le=4)


class StartBattle(Strict):
    unit_id: str = Field(max_length=40)


class Turn(Strict):
    battle_id: str = Field(max_length=40)
    turn: int = Field(ge=1, le=50)
    action: Literal["move", "attack", "defend"]
    q: int = Field(default=0, ge=0, le=8)
    r: int = Field(default=0, ge=0, le=8)


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
        "balance_version": config.VERSION,
        "offline_hours": 24,
        "storage_cap": 5000,
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


@app.post("/api/v1/army/train")
def train(
    authorization: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None),
):
    return mutate("train", {}, authorization, idempotency_key)


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


@app.get("/api/v1/world/tiles")
def tiles(
    q: int = 64,
    r: int = 64,
    radius: int = 4,
    authorization: str | None = Header(default=None),
):
    if not 0 <= q < 128 or not 0 <= r < 128 or not 1 <= radius <= 8:
        raise HTTPException(422, "Недопустимый чанк")
    from .combat import distance

    with SessionLocal() as db:
        pid = identify(db, authorization)
        hero = db.get(Hero, pid)
        vision = 4 if hero and hero.kind == "valkyrie" else 3
        ts = db.scalars(
            select(Tile).where(
                Tile.q.between(q - radius, q + radius),
                Tile.r.between(r - radius, r + radius),
            )
        )
        return {
            "tiles": [
                {
                    "id": f"1:{t.q}:{t.r}",
                    "q": t.q,
                    "r": t.r,
                    "biome": (
                        t.biome
                        if distance([64, 64], [t.q, t.r]) <= vision
                        else "unknown"
                    ),
                }
                for t in ts
            ]
        }


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


# Repository layout: server/app -> repo/client.
static = Path(__file__).resolve().parents[2] / "client" / "dist"
if static.exists():
    app.mount("/assets", StaticFiles(directory=static / "assets"), name="assets")

    @app.get("/")
    def index():
        return FileResponse(static / "index.html")
