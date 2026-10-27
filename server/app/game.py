import hashlib, json, time, uuid
from fastapi import HTTPException
from sqlalchemy import select
from .models import (
    Player,
    Resource,
    Building,
    Job,
    Unit,
    Hero,
    Item,
    Ownership,
    Battle,
    BattleTurn,
    Reward,
    Ledger,
    Command,
    Event,
)
from .config import BUILDINGS, HEROES, INITIAL, VERSION, EXPEDITIONS
from . import expeditions, garrisons
from .combat import resolve


def uid():
    return str(uuid.uuid4())


def now():
    return int(time.time())


def rows(db, model, pid):
    return list(db.scalars(select(model).where(model.player_id == pid)))


def fail(message):
    raise HTTPException(409, message)


def notify(db, p, kind):
    p.revision += 1
    db.add(Event(player_id=p.id, revision=p.revision, kind=kind, created_at=now()))


def change(db, p, delta, operation):
    balances = {r.kind: r for r in rows(db, Resource, p.id)}
    for kind, n in delta.items():
        if balances[kind].amount + n < 0:
            fail("Недостаточно ресурсов")
    for kind, n in delta.items():
        resource = balances[kind]
        actual = min(n, 5000 - resource.amount) if n > 0 else n
        if not actual:
            continue
        resource.amount += actual
        db.add(
            Ledger(
                id=uid(),
                player_id=p.id,
                kind=kind,
                delta=actual,
                after=resource.amount,
                operation=operation,
                created_at=now(),
            )
        )


def settle(db, p, at=None):
    at = now() if at is None else at
    marched = expeditions.settle_orders(db, p, at)
    territories = expeditions.state(db, p.id)["territories"]
    buildings = rows(db, Building, p.id)
    # Each whole minute is simulated with the buildings actually ready at its start.
    # Bounded offline accrual: 24h. Fractional final minute remains in settled_at.
    ticks = min(max(0, (at - p.settled_at) // 60), 1440)
    cursor = max(p.settled_at, at - 86400)
    hero = db.get(Hero, p.id)
    totals = {k: 0 for k in INITIAL}
    balances = {r.kind: r.amount for r in rows(db, Resource, p.id)}
    for i in range(ticks):
        start = cursor + i * 60
        for territory in territories:
            if territory["acquired_at"] <= start:
                for kind, amount in territory["yield"].items():
                    gained = min(amount, 5000 - balances[kind])
                    balances[kind] += gained
                    totals[kind] += gained
        active = [b for b in buildings if b.ready_at <= start]
        power = sum(BUILDINGS[b.kind]["power"] for b in active)
        if power < 0:
            continue
        for b in sorted(active, key=lambda b: b.id):
            spec = BUILDINGS[b.kind]
            inputs = spec.get("input", {})
            outputs = dict(spec.get("output", {}))
            if b.kind == "quarry" and hero and hero.kind == "ghost":
                outputs["metal"] += 1
            if (
                not outputs
                or any(balances[k] < v for k, v in inputs.items())
                or any(balances[k] + v > 5000 for k, v in outputs.items())
            ):
                continue
            for k, v in inputs.items():
                balances[k] -= v
                totals[k] -= v
            for k, v in outputs.items():
                balances[k] += v
                totals[k] += v
    if ticks:
        change(db, p, totals, "production")
        p.settled_at = cursor + ticks * 60
    completed = False
    for b in buildings:
        if b.status == "building" and b.ready_at <= at:
            b.status = "ready"
            completed = True
    for job in rows(db, Job, p.id):
        if job.status == "queued" and job.ready_at <= at:
            db.add(
                Unit(id=job.id, player_id=p.id, kind=job.kind, hp=100, status="reserve")
            )
            job.status = "complete"
            completed = True
    if completed or marched or any(totals.values()):
        notify(db, p, "settled")
    db.flush()


def snapshot(db, p):
    hero = db.get(Hero, p.id)
    serialize = lambda o, keys: {k: getattr(o, k) for k in keys.split()}
    return {
        "player": {"id": p.id, "name": p.name},
        "revision": p.revision,
        "server_time": now(),
        "resources": {r.kind: r.amount for r in rows(db, Resource, p.id)},
        "buildings": [
            serialize(b, "id kind q r level status ready_at")
            for b in rows(db, Building, p.id)
        ],
        "jobs": [
            serialize(j, "id kind status ready_at")
            for j in rows(db, Job, p.id)
            if j.status == "queued"
        ],
        "units": [serialize(u, "id kind hp status") for u in rows(db, Unit, p.id)],
        "hero": serialize(hero, "kind xp") if hero else None,
        "inventory": [
            serialize(i, "id definition_id source_id equipped created_at")
            for i in db.scalars(select(Item).where(Item.owner_id == p.id))
        ],
        "battles": [
            serialize(b, "id status state balance_version")
            for b in rows(db, Battle, p.id)
        ],
        "first_victory": db.get(Reward, (p.id, "first-patrol")) is not None,
        **expeditions.state(db, p.id),
    }


def execute(db, p, op, data, key):
    fingerprint = hashlib.sha256(
        json.dumps([op, data], sort_keys=True).encode()
    ).hexdigest()
    old = db.get(Command, (p.id, key))
    if old:
        if old.fingerprint != fingerprint:
            fail("Ключ запроса уже использован для другой команды")
        return old.result
    settle(db, p)
    result = dispatch(db, p, op, data)
    notify(db, p, op)
    db.flush()
    response = {"result": result, "state": snapshot(db, p)}
    db.add(Command(player_id=p.id, key=key, fingerprint=fingerprint, result=response))
    return response


def dispatch(db, p, op, data):
    hero = db.get(Hero, p.id)
    buildings = rows(db, Building, p.id)
    if op == "hero":
        if hero:
            fail("Стартовый командир уже выбран")
        if data["kind"] not in HEROES:
            fail("Неизвестный командир")
        db.add(Hero(player_id=p.id, kind=data["kind"], xp=0))
        return {"selected": data["kind"]}
    if not hero:
        fail("Сначала выберите командира")
    if op in ("army_create", "army_order"):
        return expeditions.dispatch(db, p, op, data, now(), uid, change)
    if op == "build":
        kind = data["kind"]
        q = data["q"]
        r = data["r"]
        if kind not in BUILDINGS or kind == "hq":
            fail("Недоступное здание")
        if max(abs(q), abs(r), abs(q + r)) > 4:
            fail("Клетка вне базы")
        if any(b.q == q and b.r == r for b in buildings):
            fail("Клетка занята")
        if any(b.status == "building" for b in buildings):
            fail("Строительная очередь занята")
        if any(b.kind == kind for b in buildings):
            fail("В первом срезе доступно одно здание каждого типа")
        spec = BUILDINGS[kind]
        if kind != "power" and not any(
            b.kind == "power" and b.status == "ready" for b in buildings
        ):
            fail("Сначала завершите электростанцию")
        change(db, p, {k: -v for k, v in spec["cost"].items()}, "construction")
        obj = Building(
            id=uid(),
            player_id=p.id,
            kind=kind,
            q=q,
            r=r,
            level=1,
            status="building",
            ready_at=now() + spec["seconds"],
        )
        db.add(obj)
        return {"id": obj.id}
    if op == "train":
        if not any(b.kind == "barracks" and b.status == "ready" for b in buildings):
            fail("Необходимы готовые казармы")
        if (
            sum(BUILDINGS[b.kind]["power"] for b in buildings if b.status == "ready")
            < 0
        ):
            fail("Недостаточно энергии")
        if any(j.status == "queued" for j in rows(db, Job, p.id)):
            fail("Очередь подготовки занята")
        change(db, p, {"metal": -60, "food": -40}, "training")
        job = Job(
            id=uid(),
            player_id=p.id,
            kind="rifles",
            ready_at=now() + 45,
            status="queued",
        )
        db.add(job)
        return {"id": job.id}
    if op == "battle":
        if db.get(Reward, (p.id, "first-patrol")):
            fail("Учебная операция уже завершена")
        if any(b.status == "active" for b in rows(db, Battle, p.id)):
            fail("У вас уже есть активный бой")
        unit = db.get(Unit, data["unit_id"])
        if not unit or unit.player_id != p.id or unit.status != "reserve":
            fail("Отряд недоступен")
        unit.status = "battle"
        battle = Battle(
            id=uid(),
            player_id=p.id,
            unit_id=unit.id,
            status="active",
            seed=uid(),
            balance_version=VERSION,
            state={
                "turn": 1,
                "player": {"pos": [2, 4], "hp": unit.hp},
                "npc": {"pos": [6, 4], "hp": 70},
                "cover": [[3, 4], [4, 2], [5, 5]],
            },
        )
        db.add(battle)
        return {"id": battle.id}
    if op == "turn":
        battle = db.get(Battle, data["battle_id"])
        if not battle or battle.player_id != p.id:
            raise HTTPException(404, "Бой не найден")
        if battle.status != "active":
            fail("Бой уже завершён")
        if data["turn"] != battle.state["turn"]:
            fail("Раунд устарел: обновите состояние")
        bonus = (
            0.03
            if db.scalar(
                select(Item).where(Item.owner_id == p.id, Item.equipped == True)
            )
            else 0
        )
        try:
            state, events, outcome = resolve(
                battle.state, data, battle.seed, hero.kind, bonus
            )
        except ValueError as exc:
            fail(str(exc))
        db.add(
            BattleTurn(
                battle_id=battle.id, turn=data["turn"], command=data, events=events
            )
        )
        battle.state = state
        battle.status = outcome
        if outcome != "active" and 'expedition' in state:
            captured=garrisons.finish(db,p,battle,outcome,now())
            if captured:
                hero.xp += 50
            return {"events":events,"outcome":outcome,"captured":captured}
        if outcome != "active":
            unit = db.get(Unit, battle.unit_id)
            unit.status = "reserve"
            unit.hp = max(50, state["player"]["hp"])
            if hero.kind == "phoenix":
                unit.hp = min(100, unit.hp + 10)
            if outcome == "victory":
                db.add(
                    Reward(player_id=p.id, mission="first-patrol", battle_id=battle.id)
                )
                change(db, p, {"metal": 150, "food": 60}, "first-patrol")
                hero.xp += 100
                item = Item(
                    id=uid(),
                    owner_id=p.id,
                    definition_id="field-module",
                    source_id=battle.id,
                    equipped=False,
                    created_at=now(),
                )
                db.add(item)
                db.flush()
                db.add(
                    Ownership(
                        id=uid(),
                        item_id=item.id,
                        owner_id=p.id,
                        reason="first-patrol",
                        created_at=now(),
                    )
                )
        return {"events": events, "outcome": outcome}
    if op == "equip":
        item = db.get(Item, data["item_id"])
        if not item or item.owner_id != p.id:
            raise HTTPException(404, "Предмет не найден")
        if any(b.status == "active" for b in rows(db, Battle, p.id)):
            fail("Нельзя менять экипировку во время боя")
        if data["equipped"]:
            for other in db.scalars(select(Item).where(Item.owner_id == p.id)):
                other.equipped = False
        item.equipped = data["equipped"]
        return {"id": item.id}
    raise HTTPException(404, "Неизвестная команда")
