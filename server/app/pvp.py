"""Asynchronous PvP (ТЗ 8.7–8.8).

The attacker marches with an explicit "attack" order onto another commander's
base, territory or mine. On arrival the server snapshots the defender's forces
into an ordinary stack battle where the defender's side is played by the server
AI, so the defender never has to be online.

Protection rules:
- 72 h newbie shield from sign-up, lost on the first voluntary attack;
- an 8 h shield after a lost base raid;
- at most PAIR_LIMIT attacks on the same commander per 24 h;
- no attacks on commanders below half of your strength;
- defending stacks never drop below half; a base is never captured;
- 30 % of storage (at least 1000) of every resource is never raidable.

Locking: the attacker's row is held by the request. The defender's row is only
taken when the battle ends, under a short lock timeout inside a savepoint, so a
mutual finish can't deadlock; the request then fails with 409 and is retried.
"""
import math, uuid
from fastapi import HTTPException
from sqlalchemy import select, func, text
from sqlalchemy.exc import OperationalError
from .models import (Player, Unit, Army, ArmyUnit, ArmyOrder, Battle, Building, Hero, Item, Resource,
                     TileOwnership, MapMine, WorldBase, Tile, PvpReport)
from .config import PVP, UNITS, FACTIONS, VERSION, EXPEDITIONS
from . import bases, combat

TARGET_NAMES = {"base": "база", "territory": "территория", "mine": "шахта"}
BASE_COVER = [[5, 4], [6, 3], [6, 5]]
FIELD_COVER = [[3, 4], [4, 2], [5, 5]]


# ---- targets ---------------------------------------------------------------

def target(db, pid, q, r):
    """Hostile holding at a hex: {'kind', 'defender_id'} or None."""
    is_base, owner = bases.at(db, q, r)
    if is_base:
        return {"kind": "base", "defender_id": owner} if owner and owner != pid else None
    mine = db.get(MapMine, (1, q, r))
    if mine and mine.player_id != pid:
        return {"kind": "mine", "defender_id": mine.player_id}
    tile = db.get(TileOwnership, (1, q, r))
    if tile and tile.player_id != pid:
        return {"kind": "territory", "defender_id": tile.player_id}
    return None


def power(db, pid):
    """Rough military strength used only for the 'much weaker' rule."""
    total = 0
    for u in db.scalars(select(Unit).where(Unit.player_id == pid)):
        spec = UNITS.get(u.kind)
        if spec:
            total += u.count * (spec["hp"] + 3 * spec["damage"])
    return total + 50 * hq_level(db, pid)


def hq_level(db, pid):
    hq = db.scalar(select(Building).where(Building.player_id == pid, Building.kind == "hq"))
    return hq.level if hq else 1


def recent_attacks(db, attacker_id, defender_id, at):
    return db.scalar(select(func.count()).select_from(PvpReport).where(
        PvpReport.attacker_id == attacker_id, PvpReport.defender_id == defender_id,
        PvpReport.created_at > at - PVP["pair_window"])) or 0


def blocked_reason(db, p, tgt, at):
    """Why this attack is not allowed right now, or None. Never raises."""
    defender = db.get(Player, tgt["defender_id"])
    if not defender:
        return "Командир не найден"
    if defender.shield_until > at:
        hours = math.ceil((defender.shield_until - at) / 3600)
        return f"{defender.name} под защитой ещё {hours} ч"
    if recent_attacks(db, p.id, defender.id, at) >= PVP["pair_limit"]:
        return f"Лимит: не больше {PVP['pair_limit']} нападений на одного командира за сутки"
    if power(db, defender.id) < PVP["weaker_ratio"] * power(db, p.id):
        return "Противник намного слабее вас: такие нападения запрещены"
    return None


# ---- forces ----------------------------------------------------------------

def _militia(db, defender_id, kind):
    """Virtual home guard of the defender's faction; takes no persistent losses."""
    hero = db.get(Hero, defender_id)
    roster = {v["role"]: v["key"] for v in FACTIONS[hero.kind]["units"]} if hero else {}
    hq = hq_level(db, defender_id)
    line = roster.get("rifles", "rifles")
    out = [(line, (6 + 3 * hq) if kind == "base" else (4 + 2 * hq))]
    if kind == "base":
        out.append((roster.get("artillery", "artillery"), 1 + hq // 2))
    return out[:PVP["militia"][kind]]


def defenders(db, tgt, q, r):
    """Defender's stacks for this target: [(kind, count, unit_id or None, hp)], max 5.

    Real stacks: the defender's idle armies standing on the hex, plus reserve
    units for a base. Militia fills the remaining slots.
    """
    did, kind = tgt["defender_id"], tgt["kind"]
    real = []
    for army in db.scalars(select(Army).where(Army.player_id == did, Army.status == "idle", Army.q == q, Army.r == r)):
        ids = list(db.scalars(select(ArmyUnit.unit_id).where(ArmyUnit.army_id == army.id).order_by(ArmyUnit.unit_id)))
        real += [u for u in (db.get(Unit, i) for i in ids) if u and u.status == "army"]
    if kind == "base":
        real += list(db.scalars(select(Unit).where(Unit.player_id == did, Unit.status == "reserve").order_by(Unit.id)))
    real = [u for u in real if not UNITS[u.kind].get("naval")]
    real.sort(key=lambda u: -u.count * UNITS[u.kind]["hp"])
    forces = [(u.kind, u.count, u.id, u.hp) for u in real[:5]]
    cut_off = False
    if kind != "base":
        from . import logistics
        supply = logistics.supplied(db, did)
        cut_off = (q, r) not in supply if kind == "territory" else \
            not logistics.mine_supplied(tuple(bases.home(db, did)), supply, q, r)
    militia = _militia(db, did, kind)
    if kind == "territory":
        from . import logistics as _l
        if _l.node_kind(db, q, r) == "capital":
            # The Capital's own guard turns out for whoever holds it.
            militia = [(k, n * 3) for k, n in militia] + [(k2, 2 + hq_level(db, did)) for k2 in
                       [next((v["key"] for v in FACTIONS[db.get(Hero, did).kind]["units"] if v["role"] == "artillery"), "artillery")]]
    for k, n in militia:
        if len(forces) < 5:
            forces.append((k, max(1, n // 2) if cut_off else n, None, 100))
    return forces


def preview(db, pid, q, r, at):
    """What a scout sees: owner, protection and rounded enemy forces."""
    tgt = target(db, pid, q, r)
    if not tgt:
        return None
    defender = db.get(Player, tgt["defender_id"])
    hero = db.get(Hero, defender.id)
    me = db.get(Player, pid)
    reason = blocked_reason(db, me, tgt, at)
    forces = [{"kind": k, "name": UNITS[k]["name"], "count": n if n < 5 else 5 * round(n / 5), "approx": n >= 5,
               "militia": uid is None} for k, n, uid, _ in defenders(db, tgt, q, r)]
    return {"kind": tgt["kind"], "title": TARGET_NAMES[tgt["kind"]], "defender": defender.name,
            "hero": hero.kind if hero else None, "shield_until": defender.shield_until,
            "allowed": reason is None, "reason": reason, "forces": forces,
            "my_shield_until": me.shield_until,
            "loses_shield": me.shield_until > at,
            "attacks_left": max(0, PVP["pair_limit"] - recent_attacks(db, pid, defender.id, at))}


# ---- battle ----------------------------------------------------------------

def begin(db, p, army, order, tgt, at):
    from .game import PLAYER_SPOTS, NPC_SPOTS
    from .garrisons import fighting_units
    from . import equipment
    units = fighting_units(db, army, False)[:len(PLAYER_SPOTS)]
    if not units:
        order.status, order.result = "blocked", "Нет сухопутных отрядов для боя"
        army.status = "idle"
        return
    stacks = []
    for i, u in enumerate(units):
        u.status = "battle"
        stacks.append(combat.make_stack(f"p{i+1}", "player", u.kind, u.count, PLAYER_SPOTS[i], u.id, u.hp))
    enemy = []
    for i, (kind, count, unit_id, hp) in enumerate(defenders(db, tgt, order.q, order.r)):
        st = combat.make_stack(f"n{i+1}", "npc", kind, count, NPC_SPOTS[i], hp_pct=hp)
        st["owner_unit"] = unit_id
        enemy.append(st)
    defender = db.get(Player, tgt["defender_id"])
    hero = db.get(Hero, p.id)
    led = bool(army.commander)
    from . import commander
    seed = str(uuid.uuid4())
    cover = BASE_COVER if tgt["kind"] == "base" else FIELD_COVER
    state, _, _ = combat.new_battle(stacks, enemy, cover, seed, hero.kind if led else None, 0,
                                    commander.battle_perks(db, p.id, led))
    state["led"] = led
    tile = db.get(Tile, (1, order.q, order.r))
    state["expedition"] = {"army_id": army.id, "order_id": order.id, "q": order.q, "r": order.r}
    state["pvp"] = {"target": tgt["kind"], "defender_id": defender.id, "defender": defender.name}
    state["npc_tier"] = {"name": defender.name, "hp": sum(x["hp"] for x in enemy), "xp": PVP["xp"]}
    state["terrain"] = tile.biome
    db.add(Battle(id=str(uuid.uuid4()), player_id=p.id, unit_id=units[0].id, status="active",
                  seed=seed, balance_version=VERSION, state=state))
    order.status, order.result = "complete", f"Атака: {TARGET_NAMES[tgt['kind']]} командира {defender.name}"
    army.status = "idle"


def _lock_defender(db, did):
    try:
        with db.begin_nested():
            db.execute(text("SET LOCAL lock_timeout = '3s'"))
            row = db.scalar(select(Player).where(Player.id == did).with_for_update())
            db.execute(text("SET LOCAL lock_timeout = 0"))
            return row
    except OperationalError:
        raise HTTPException(409, "Противник сейчас занят. Повторите приказ через пару секунд")


def _loot(db, defender, at):
    from .game import storage_cap
    cap = storage_cap(db, defender, at)
    safe = max(PVP["protected_min"], round(cap * PVP["protected_share"]))
    loot = {}
    for res in db.scalars(select(Resource).where(Resource.player_id == defender.id).order_by(Resource.kind)):
        n = min(PVP["loot_max"], int(max(0, res.amount - safe) * PVP["loot_share"]))
        if n > 0:
            loot[res.kind] = n
    return loot


def finish(db, p, battle, outcome, at):
    """Apply both sides' results. Attacker losses are already applied by the caller."""
    from .game import battle_units, change, settle, notify
    from .expeditions import owned, discover, control_limit
    s = battle.state
    ctx, info = s["expedition"], s["pvp"]
    army, order = db.get(Army, ctx["army_id"]), db.get(ArmyOrder, ctx["order_id"])
    for unit in battle_units(db, battle):
        unit.status = "army"
    defender = _lock_defender(db, info["defender_id"])
    settle(db, defender, at)
    # Defender: real stacks lose what died, but never below half of what fought.
    lost_def = {}
    for st in s["stacks"]:
        if st["side"] != "npc" or not st.get("owner_unit"):
            continue
        unit = db.get(Unit, st["owner_unit"])
        if not unit or unit.player_id != defender.id:
            continue
        dead = st["start"] - combat.alive(st)
        allowed = st["start"] - math.ceil(st["start"] * PVP["defender_floor"])
        dead = max(0, min(dead, allowed, unit.count - 1))
        if dead:
            unit.count -= dead
            lost_def[unit.kind] = lost_def.get(unit.kind, 0) + dead
    lost_att = {x["kind"]: x["start"] - combat.alive(x) for x in s["stacks"] if x["side"] == "player"}
    loot, result = {}, None
    db.scalar(select(Tile).where(Tile.world_id == 1, Tile.q == ctx["q"], Tile.r == ctx["r"]).with_for_update())
    from . import seasons
    if outcome == "victory":
        db.get(Hero, p.id).xp += PVP["xp"]
        seasons.award(p, "pvp_attack")
        kind = info["target"]
        if kind == "base":
            from . import commander
            loot = _loot(db, defender, at)
            bonus = commander.perk(db, p.id, "plunder")
            gained = {k: round(v * (1 + bonus)) for k, v in loot.items()}
            if loot:
                change(db, defender, {k: -v for k, v in loot.items()}, "pvp_raid_loss")
                change(db, p, gained, "pvp_raid")
            defender.shield_until = max(defender.shield_until, at + PVP["raid_shield_seconds"])
            result = "Налёт удался: трофеи доставлены на базу" if loot else "Налёт удался, но склады противника пусты"
        elif kind == "mine":
            mine = db.get(MapMine, (1, ctx["q"], ctx["r"]))
            if mine and mine.player_id == defender.id:
                mine.player_id, mine.acquired_at = p.id, at
                army.q, army.r = ctx["q"], ctx["r"]
                discover(db, army, at)
                result = f"Шахта отбита: +{mine.rate} в минуту"
            else:
                result = "Победа, но шахта уже сменила владельца"
        else:
            tile = db.get(TileOwnership, (1, ctx["q"], ctx["r"]))
            if not tile or tile.player_id != defender.id:
                result = "Победа, но территория уже сменила владельца"
            elif len(owned(db, p.id)) >= control_limit(db, p.id):
                result = "Победа, но достигнут лимит контроля: территория осталась за противником"
            else:
                tile.player_id, tile.acquired_at = p.id, at
                army.q, army.r = ctx["q"], ctx["r"]
                discover(db, army, at)
                result = "Территория захвачена"
    else:
        seasons.award(defender, "pvp_defence")
        result = "Поражение. Соединение отступило"
    order.result = result
    db.add(PvpReport(id=str(uuid.uuid4()), battle_id=battle.id, attacker_id=p.id, defender_id=defender.id,
                     target=info["target"], q=ctx["q"], r=ctx["r"], outcome=outcome, loot=loot,
                     losses={"attacker": lost_att, "defender": lost_def}, created_at=at))
    battle.state = {**s, "pvp": {**info, "result": result, "loot": loot}}
    notify(db, defender, "pvp")
    db.flush()
    return outcome == "victory"


# ---- player view -----------------------------------------------------------

def holdings(db, pid):
    found = {(t.q, t.r): "territory" for t in db.scalars(select(TileOwnership).where(TileOwnership.player_id == pid))}
    found.update({(m.q, m.r): "mine" for m in db.scalars(select(MapMine).where(MapMine.player_id == pid))})
    base = bases.get(db, pid)
    if base:
        found[(base.q, base.r)] = "base"
    return found


def state(db, p, at):
    names = {}

    def name(pid):
        if pid not in names:
            other = db.get(Player, pid)
            names[pid] = other.name if other else "?"
        return names[pid]
    reports = db.scalars(select(PvpReport).where(
        (PvpReport.attacker_id == p.id) | (PvpReport.defender_id == p.id)).order_by(PvpReport.created_at.desc()).limit(10))
    mine = holdings(db, p.id)
    incoming = []
    for order, army in db.execute(select(ArmyOrder, Army).join(Army, Army.id == ArmyOrder.army_id).where(
            ArmyOrder.status == "moving", ArmyOrder.action == "attack", Army.player_id != p.id)):
        if (order.q, order.r) in mine:
            incoming.append({"q": order.q, "r": order.r, "target": mine[(order.q, order.r)],
                             "attacker": name(army.player_id), "arrive_at": order.ready_at})
    return {
        "shield_until": p.shield_until,
        "newbie": p.shield_until > at and p.created_at + PVP["newbie_seconds"] >= p.shield_until,
        "incoming": sorted(incoming, key=lambda x: x["arrive_at"]),
        "reports": [{"id": r.id, "role": "attacker" if r.attacker_id == p.id else "defender",
                     "enemy": name(r.defender_id if r.attacker_id == p.id else r.attacker_id),
                     "target": r.target, "q": r.q, "r": r.r,
                     "outcome": r.outcome if r.attacker_id == p.id else ("defeat" if r.outcome == "victory" else "victory"),
                     "loot": r.loot, "losses": r.losses, "created_at": r.created_at} for r in reports],
    }
