import hashlib, json, math, time, uuid
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
from .config import BUILDINGS, HEROES, INITIAL, VERSION, EXPEDITIONS, UNITS, TUTORIAL_NPC, FACTIONS
from . import expeditions, garrisons, equipment, bases, economy, objects, pvp, commander, logistics, seasons, nodes, doctrines
from . import combat


def uid():
    return str(uuid.uuid4())


def now():
    return int(time.time())


def rows(db, model, pid):
    return list(db.scalars(select(model).where(model.player_id == pid)))


def fail(message):
    raise HTTPException(409, message)


def tutorial_done(db, p):
    """The first patrol is fought once per account; seasons keep it done."""
    return bool(p.tutorial_done) or db.get(Reward, (p.id, "first-patrol")) is not None


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
    from . import doctrines
    at = now() if at is None else at
    return round(economy.storage(levels(rows(db, Building, p.id), at)) * doctrines.effect(db, p.id, "storage", at))


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
    marched = expeditions.settle_orders(db, p, at, change)
    # Only supplied land works: territories chained to the base, mines touching them.
    supply = logistics.supplied(db, p.id)
    home = tuple(bases.home(db, p.id))
    territories = [t for t in expeditions.state(db, p.id)["territories"] if t["supplied"]] + [
        {"acquired_at": m.acquired_at, "yield": {m.resource: m.rate}} for m in objects.mines(db, p.id)
        if logistics.mine_supplied(home, supply, m.q, m.r)]
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
        from . import doctrines
        boost = (1 + commander.perk(db, p.id, "supply")) * seasons.effect(db, "production", at) * doctrines.effect(db, p.id, "production", at)
        if boost != 1:
            totals = {k: round(v * boost) if v > 0 else v for k, v in totals.items()}
        change(db, p, totals, "production")
        seasons.accrue(db, p, ticks, at)
        p.settled_at = cursor + ticks * 60
    completed = logistics.charge(db, p, at, change, seasons.effect(db, "upkeep", at))
    for battle in rows(db, Battle, p.id):
        if battle.status == "active" and "stacks" not in battle.state:
            battle.state = combat.from_legacy(battle.state, battle.unit_id)
            completed = True
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
            db.add(Unit(id=job.id, player_id=p.id, kind=job.kind, hp=100,
                        count=UNITS.get(job.kind, UNITS["rifles"])["count"], status="reserve"))
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
        "units": [serialize(u, "id kind hp count status") for u in rows(db, Unit, p.id)],
        "hero": serialize(hero, "kind xp") if hero else None,
        "inventory": [
            {**serialize(i, "id definition_id source_id equipped created_at"), "definition":equipment.DEFINITIONS.get(i.definition_id), "source": "first-patrol" if i.definition_id=="field-module" else "garrison"}
            for i in db.scalars(select(Item).where(Item.owner_id == p.id))
        ],
        "battles": [
            {**serialize(b, "id status state balance_version"), **({"preview": battle_preview(db, p, b)} if b.status == "active" else {})}
            for b in rows(db, Battle, p.id)
        ],
        "commander": commander.view(db, p.id),
        "doctrines": doctrines.view(db, p.id, now()),
        "first_victory": tutorial_done(db, p),
        "vp": p.vp,
        **expeditions.state(db, p.id),
        "mines": [{"q": m.q, "r": m.r, "resource": m.resource, "rate": m.rate,
                   "supplied": logistics.mine_supplied(tuple(bases.home(db, p.id)), logistics.supplied(db, p.id), m.q, m.r)}
                  for m in objects.mines(db, p.id)],
        "pending_chests": objects.pending_chests(db, p.id),
        "pvp": pvp.state(db, p, now()),
        "calendar": seasons.calendar(seasons.current(db), now()),
        "upkeep": logistics.per_hour(db, p.id, seasons.effect(db, "upkeep", now())),
        "control_limit": expeditions.control_limit(db, p.id),
        "nodes": [{"q": q, "r": r, "kind": k, "name": nodes.KINDS[k]["name"], "supplied": ok}
                  for q, r, k, ok in logistics.owned_nodes(db, p.id)],
    }


def faction_unit(hero_kind, requested):
    """Resolve a hire request to this commander's own unit (role names map to the faction variant)."""
    roster = {v["key"]: v for v in FACTIONS[hero_kind]["units"]}
    if requested in roster or UNITS.get(requested, {}).get("naval"):
        return requested
    by_role = {v["role"]: v["key"] for v in roster.values()}
    if requested in by_role:
        return by_role[requested]
    if requested in UNITS and UNITS[requested].get("faction"):
        fail("Этот отряд нанимает другой командир")
    fail("Неизвестный тип войск")


PLAYER_SPOTS = [[2, 4], [1, 3], [1, 5], [2, 2], [2, 6]]
NPC_SPOTS = [[6, 4], [7, 3], [7, 5], [6, 2], [6, 6]]


def npc_stacks(composition):
    return [combat.make_stack(f"n{i+1}", "npc", kind, count, NPC_SPOTS[i])
            for i, (kind, count) in enumerate(composition)]


def battle_units(db, battle):
    ids = [x["unit_id"] for x in battle.state["stacks"] if x["side"] == "player"]
    return [db.get(Unit, i) for i in ids]


def battle_preview(db, p, battle):
    try:
        hero = db.get(Hero, p.id)
        led = battle.state.get("led", True)
        return combat.preview(battle.state, battle.seed, hero.kind if hero and led else None, legacy_bonus(db, p, battle))
    except Exception:
        return {}


def legacy_bonus(db, p, battle):
    """Battles started before perks keep the old equipment bonus; new ones carry perks in their state."""
    if "perks" in battle.state or not battle.state.get("led", True):
        return 0
    return equipment.damage_bonus(db.scalars(select(Item).where(Item.owner_id == p.id)))


def apply_losses(db, battle, outcome, hero):
    """Casualties persist. Defeat keeps at least half of each stack; Phoenix recovers 10% of the fallen,
    Field medicine (commander skill) a further share."""
    aid = (battle.state.get("perks") or {}).get("first_aid", 0)
    for unit_id, r in combat.summary(battle.state).items():
        unit = db.get(Unit, unit_id)
        survivors, hp = r["alive"], r["hp_pct"]
        if outcome != "victory" and survivors < math.ceil(r["start"] / 2):
            survivors, hp = math.ceil(r["start"] / 2), 50
        fallen = r["start"] - survivors
        if hero.kind == "phoenix" and fallen:
            survivors = min(r["start"], survivors + max(1, math.ceil(0.1 * fallen)))
        if aid and fallen:
            survivors = min(r["start"], survivors + math.floor(aid * fallen))
        unit.count, unit.hp = max(1, survivors), max(1, min(100, hp or 50))


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
    if op in ("army_create", "army_order", "army_assign", "army_release", "army_disband", "army_lead"):
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
            ready_at=now() + round(spec["seconds"] * (1 - commander.perk(db, p.id, "engineering"))),
        )
        db.add(obj)
        return {"id": obj.id}
    if op == "chest":
        return objects.choose(db, p, data["q"], data["r"], data["choice"], change)
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
        b.upgrade_ready_at = now() + max(1, round(economy.upgrade_seconds(b.kind, b.level) * (1 - commander.perk(db, p.id, "engineering"))))
        return {"id": b.id, "level": b.level + 1, "ready_at": b.upgrade_ready_at}
    if op == "train":
        kind = faction_unit(hero.kind, data.get("kind") or "rifles")
        spec = UNITS[kind]
        lv = levels(buildings, now())
        if not spec.get("naval") and not lv.get("barracks"):
            fail("Необходимы готовые казармы")
        for need, level in spec["requires"].items():
            if lv.get(need, 0) < level:
                fail(f"Требуется: {BUILDINGS[need]['name']} {level} уровня")
        if sum(economy.power(k, n) for k, n in lv.items()) < 0:
            fail("Недостаточно энергии")
        if any(j.status == "queued" for j in rows(db, Job, p.id)):
            fail("Очередь подготовки занята")
        from . import doctrines
        cost_factor = seasons.effect(db, "infantry_cost", now()) * doctrines.effect(db, p.id, "inf_cost", now()) if spec.get("infantry") else 1
        time_factor = seasons.effect(db, "vehicle_time", now()) * doctrines.effect(db, p.id, "veh_time", now()) \
            if not spec.get("infantry") and not spec.get("naval") else 1
        change(db, p, {k: -max(1, round(v * cost_factor)) for k, v in spec["cost"].items()}, "training")
        job = Job(id=uid(), player_id=p.id, kind=kind, ready_at=now() + max(1, round(spec["seconds"] * time_factor)), status="queued")
        db.add(job)
        return {"id": job.id}
    if op == "battle":
        if tutorial_done(db, p):
            fail("Учебная операция уже завершена")
        if any(b.status == "active" for b in rows(db, Battle, p.id)):
            fail("У вас уже есть активный бой")
        unit = db.get(Unit, data["unit_id"])
        if not unit or unit.player_id != p.id or unit.status != "reserve":
            fail("Отряд недоступен")
        unit.status = "battle"
        seed = uid()
        state, _, _ = combat.new_battle(
            [combat.make_stack("p1", "player", unit.kind, unit.count, PLAYER_SPOTS[0], unit.id, unit.hp)],
            npc_stacks(TUTORIAL_NPC), [[3, 4], [4, 2], [5, 5]], seed, hero.kind, 0, commander.battle_perks(db, p.id, True))
        battle = Battle(id=uid(), player_id=p.id, unit_id=unit.id, status="active", seed=seed,
                        balance_version=VERSION, state=state)
        db.add(battle)
        return {"id": battle.id}
    if op in ("turn", "auto"):
        battle = db.get(Battle, data["battle_id"])
        if not battle or battle.player_id != p.id:
            raise HTTPException(404, "Бой не найден")
        if battle.status != "active":
            fail("Бой уже завершён")
        led = battle.state.get("led", True)
        kind = hero.kind if led else None
        bonus = legacy_bonus(db, p, battle)
        state, events, outcome = battle.state, [], "active"
        try:
            if op == "turn":
                if data["turn"] != battle.state["turn"]:
                    fail("Раунд устарел: обновите состояние")
                state, events, outcome = combat.resolve(battle.state, data, battle.seed, kind, bonus)
                db.add(BattleTurn(battle_id=battle.id, turn=data["turn"], command=data, events=events))
            else:
                # Quick combat: the server plays every remaining player turn.
                while outcome == "active":
                    cmd = {**combat.ai_command(state, kind), "battle_id": battle.id, "turn": state["turn"], "auto": True}
                    turn = state["turn"]
                    try:
                        state, step, outcome = combat.resolve(state, cmd, battle.seed, kind, bonus)
                    except ValueError:
                        cmd = {"action": "defend", "battle_id": battle.id, "turn": turn, "auto": True}
                        state, step, outcome = combat.resolve(state, cmd, battle.seed, kind, bonus)
                    db.add(BattleTurn(battle_id=battle.id, turn=turn, command=cmd, events=step))
                    events += step
        except ValueError as exc:
            fail(str(exc))
        battle.state = state
        battle.status = outcome
        if outcome == "active":
            return {"events": events, "outcome": outcome}
        return conclude(db, p, battle, hero, events, outcome)
    if op == "doctrine":
        from . import doctrines
        return doctrines.start(db, p, data["key"], now(), change)
    if op == "hire":
        return objects.hire(db, p, data["army_id"], now(), change)
    if op == "skill_pick":
        return commander.choose(db, p, data["key"])
    if op == "equip":
        item = db.get(Item, data["item_id"])
        if not item or item.owner_id != p.id:
            raise HTTPException(404, "Предмет не найден")
        if any(b.status == "active" for b in rows(db, Battle, p.id)):
            fail("Нельзя менять экипировку во время боя")
        if data["equipped"]:
            slot = equipment.DEFINITIONS.get(item.definition_id, {}).get("slot")
            for other in db.scalars(select(Item).where(Item.owner_id == p.id)):
                if equipment.DEFINITIONS.get(other.definition_id, {}).get("slot") == slot:
                    other.equipped = False
        item.equipped = data["equipped"]
        return {"id": item.id}
    raise HTTPException(404, "Неизвестная команда")


def conclude(db, p, battle, hero, events, outcome):
    """Shared end of a battle: losses, rewards and world effects."""
    state = battle.state
    apply_losses(db, battle, outcome, hero)
    if 'pvp' in state:
        won = pvp.finish(db, p, battle, outcome, now())
        return {"events": events, "outcome": outcome, "captured": won}
    if 'expedition' in state:
        captured = garrisons.finish(db, p, battle, outcome, now())
        if captured:
            hero.xp += battle.state.get('npc_tier', {}).get('xp', 50)
            from .config import NPC_TIERS
            name = battle.state.get('npc_tier', {}).get('name')
            fortress = name in (nodes.TIER['name'], nodes.CAPITAL_TIER['name'])
            tier = 3 if fortress else next((i for i, t in enumerate(NPC_TIERS) if t['name'] == name), 0)
            seasons.award(p, 'capital' if name == nodes.CAPITAL_TIER['name'] else 'fortress' if fortress else 'garrison')
            definition_id, roll = equipment.loot(battle.seed, tier)
            item = Item(id=uid(), owner_id=p.id, definition_id=definition_id, source_id=battle.id, equipped=False, created_at=now())
            db.add(item); db.flush()
            db.add(Ownership(id=uid(), item_id=item.id, owner_id=p.id, reason=equipment.LOOT_VERSION, created_at=now()))
            battle.state = {**battle.state, 'loot': {'item_id': item.id, 'definition_id': definition_id,
                                                     'table_version': equipment.LOOT_VERSION, 'roll': roll}, 'captured': True}
        return {"events": events, "outcome": outcome, "captured": captured}
    for unit in battle_units(db, battle):
        unit.status = "reserve"
    if outcome == "victory":
        p.tutorial_done = True
        db.add(Reward(player_id=p.id, mission="first-patrol", battle_id=battle.id))
        change(db, p, {"metal": 150, "food": 60}, "first-patrol")
        hero.xp += 100
        item = Item(id=uid(), owner_id=p.id, definition_id="field-module", source_id=battle.id,
                    equipped=False, created_at=now())
        db.add(item)
        db.flush()
        db.add(Ownership(id=uid(), item_id=item.id, owner_id=p.id, reason="first-patrol", created_at=now()))
    return {"events": events, "outcome": outcome}
