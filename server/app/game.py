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
from . import expeditions, garrisons, equipment, bases, economy
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


def levels(buildings, at):
    """Effective level per kind for buildings operating at time `at`."""
    result = {}
    for b in buildings:
        if b.ready_at > at:
            continue
        level = b.level + (1 if b.upgrade_ready_at and b.upgrade_ready_at <= at else 0)
        result[b.kind] = max(result.get(b.kind, 0), level)
    return result


def storage_cap(db, p, at=None):
    return economy.storage(levels(rows(db, Building, p.id), now() if at is None else at))


def change(db, p, delta, operation):
    cap = storage_cap(db, p)
    balances = {r.kind: r for r in rows(db, Resource, p.id)}
    for kind, n in delta.items():
        if balances[kind].amount + n < 0:
            fail("Недостаточно ресурсов")
    for kind, n in delta.items():
        resource = balances[kind]
        actual = max(0, min(n, cap - resource.amount)) if n > 0 else n
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
    bases.ensure(db, p, at)
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
    repair_minutes = 0
    for i in range(ticks):
        start = cursor + i * 60
        active = levels(buildings, start)
        cap = economy.storage(active)
        for territory in territories:
            if territory["acquired_at"] <= start:
                for kind, amount in territory["yield"].items():
                    gained = max(0, min(amount, cap - balances[kind]))
                    balances[kind] += gained
                    totals[kind] += gained
        if sum(economy.power(k, n) for k, n in active.items()) < 0:
            continue
        repair_minutes += economy.repair_rate(active)
        for kind in sorted(active):
            inputs = economy.inputs(kind, active[kind])
            outputs = economy.output(kind, active[kind])
            if kind == "quarry" and hero and hero.kind == "ghost":
                outputs["metal"] += 1
            if (
                not outputs
                or any(balances[k] < v for k, v in inputs.items())
                or any(balances[k] + v > cap for k, v in outputs.items())
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
    if repair_minutes:
        for unit in rows(db, Unit, p.id):
            if unit.status in ("reserve", "army") and unit.hp < 100:
                unit.hp = min(100, unit.hp + repair_minutes)
                completed = True
    for b in buildings:
        if b.status == "building" and b.ready_at <= at:
            b.status = "ready"
            completed = True
        if b.upgrade_ready_at and b.upgrade_ready_at <= at:
            b.level += 1
            b.upgrade_ready_at = None
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
        "base": {"q": base.q, "r": base.r} if (base := bases.get(db, p.id)) else None,
        "revision": p.revision,
        "server_time": now(),
        "resources": {r.kind: r.amount for r in rows(db, Resource, p.id)},
        "buildings": [building_view(b, hq_level(db, p.id)) for b in rows(db, Building, p.id)],
        "storage_cap": storage_cap(db, p),
        "jobs": [
            serialize(j, "id kind status ready_at")
            for j in rows(db, Job, p.id)
            if j.status == "queued"
        ],
        "units": [serialize(u, "id kind hp status") for u in rows(db, Unit, p.id)],
        "hero": serialize(hero, "kind xp") if hero else None,
        "inventory": [
            {**serialize(i, "id definition_id source_id equipped created_at"), "definition":equipment.DEFINITIONS.get(i.definition_id), "source": "first-patrol" if i.definition_id=="field-module" else "garrison"}
            for i in db.scalars(select(Item).where(Item.owner_id == p.id))
        ],
        "battles": [
            serialize(b, "id status state balance_version")
            for b in rows(db, Battle, p.id)
        ],
        "first_victory": db.get(Reward, (p.id, "first-patrol")) is not None,
        **expeditions.state(db, p.id),
    }


def hq_level(db, pid):
    hq = db.scalar(select(Building).where(Building.player_id == pid, Building.kind == "hq"))
    return hq.level if hq else 1


def building_view(b, hq):
    limit = economy.max_level(b.kind, hq)
    can = b.level < limit
    return {
        "id": b.id, "kind": b.kind, "q": b.q, "r": b.r, "level": b.level,
        "status": b.status, "ready_at": b.ready_at, "upgrade_ready_at": b.upgrade_ready_at,
        "max_level": limit,
        "upgrade": {"cost": economy.upgrade_cost(b.kind, b.level),
                    "seconds": economy.upgrade_seconds(b.kind, b.level)} if can else None,
        "effects": economy.describe(b.kind, b.level),
    }


def busy_queue(buildings):
    return any(b.status == "building" or b.upgrade_ready_at for b in buildings)


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
        if busy_queue(buildings):
            fail("Строительная очередь занята")
        if any(b.kind == kind for b in buildings):
            fail("Доступно одно здание каждого типа: улучшайте существующее")
        spec = BUILDINGS[kind]
        if hq_level(db, p.id) < spec["hq"]:
            fail(f"Требуется штаб {spec['hq']} уровня")
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
    if op == "upgrade":
        b = db.get(Building, data["building_id"])
        if not b or b.player_id != p.id:
            raise HTTPException(404, "Здание не найдено")
        if b.status != "ready":
            fail("Дождитесь завершения строительства")
        if busy_queue(buildings):
            fail("Строительная очередь занята")
        limit = economy.max_level(b.kind, hq_level(db, p.id))
        if b.level >= limit:
            fail("Достигнут максимальный уровень" if b.level >= economy.MAX_LEVEL else "Сначала улучшите штаб")
        change(db, p, {k: -v for k, v in economy.upgrade_cost(b.kind, b.level).items()}, "upgrade")
        b.upgrade_ready_at = now() + economy.upgrade_seconds(b.kind, b.level)
        return {"id": b.id, "level": b.level + 1, "ready_at": b.upgrade_ready_at}
    if op == "train":
        if not any(b.kind == "barracks" and b.status == "ready" for b in buildings):
            fail("Необходимы готовые казармы")
        if sum(economy.power(k, n) for k, n in levels(buildings, now()).items()) < 0:
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
        bonus = equipment.damage_bonus(db.scalars(select(Item).where(Item.owner_id==p.id)))
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
                definition_id, roll = equipment.loot(battle.seed)
                item=Item(id=uid(),owner_id=p.id,definition_id=definition_id,source_id=battle.id,equipped=False,created_at=now())
                db.add(item);db.flush()
                db.add(Ownership(id=uid(),item_id=item.id,owner_id=p.id,reason='garrison-loot-v1',created_at=now()))
                battle.state={**battle.state,'loot':{'item_id':item.id,'definition_id':definition_id,'table_version':'gar-loot-v1','roll':roll},'captured':True}
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
