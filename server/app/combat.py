"""Heroes-style stack combat on a 9x9 hex field.

Fictional balance only, no real weapon data. Each stack is N members of one
unit type sharing a health pool. Stacks act one at a time by initiative;
the server resolves the player's command for the active stack, then runs NPC
stacks until a player stack is active again or the battle ends. Everything
is deterministic for a given seed, and the input state is never mutated.
"""
import copy, hashlib, math
from .config import UNITS, ABILITIES

SIZE = 9
MAX_TURNS = 50
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]


def distance(a, b):
    q = a[0] - b[0]
    r = a[1] - b[1]
    return max(abs(q), abs(r), abs(q + r))


def roll(seed, turn, actor):
    return 90 + int(hashlib.sha256(f"{seed}:{turn}:{actor}".encode()).hexdigest()[:8], 16) % 21


def chance(seed, turn, tag):
    """Deterministic 0..99 roll for morale and luck."""
    return int(hashlib.sha256(f"{seed}:{turn}:{tag}".encode()).hexdigest()[8:16], 16) % 100


def _perks(s):
    return s.get("perks") or {}


def make_stack(sid, side, kind, count, pos, unit_id=None, hp_pct=100):
    each = UNITS[kind]["hp"]
    hp = max(1, (count - 1) * each + round(each * hp_pct / 100))
    spec = UNITS[kind]
    stack = {"id": sid, "side": side, "kind": kind, "count": count, "start": count, "hp": hp,
             "each": each, "art": spec.get("art"), "trait": spec.get("trait"), "faction": spec.get("faction"),
             "pos": list(pos), "acted": False, "retaliated": False, "defending": False, "skip": False}
    if unit_id:
        stack["unit_id"] = unit_id
    return stack


def alive(stack):
    return max(0, math.ceil(stack["hp"] / UNITS[stack["kind"]]["hp"]))


def new_battle(player_stacks, npc_stacks, cover, seed, hero, bonus, perks=None):
    state = {"turn": 1, "round": 1, "stacks": player_stacks + npc_stacks, "cover": cover,
             "ability_used": False, "active": None, "order": []}
    if perks is not None:
        state["perks"] = perks
    _new_round(state)
    events = []
    outcome = _advance(state, seed, hero, bonus, events)
    return state, events, outcome


def resolve(state, command, seed, hero, bonus):
    s = copy.deepcopy(state)
    events = []
    me = _get(s, s["active"])
    if not me or me["side"] != "player":
        raise ValueError("Сейчас ход противника")
    action = command["action"]
    if action == "ability" and not hero:
        raise ValueError("Командира нет в этом соединении: его способность недоступна")
    extra = False
    if action == "move":
        _move(s, me, [command["q"], command["r"]], hero)
        events.append({"type": "move", "actor": me["id"], "pos": me["pos"]})
    elif action == "attack":
        target = _target(s, me, command.get("target"))
        _attack(s, me, target, seed, hero, bonus, events, ranged_any=False, factor=1.0)
    elif action == "defend":
        me["defending"] = True
        events.append({"type": "defend", "actor": me["id"]})
    elif action == "wait":
        events.append({"type": "wait", "actor": me["id"]})
    elif action == "skill":
        extra = _skill(s, me, command, seed, hero, bonus, events)
    elif action == "ability":
        if s["ability_used"]:
            raise ValueError("Способность командира уже использована в этом бою")
        extra = _ability(s, me, command, seed, hero, bonus, events)
        s["ability_used"] = True
    else:
        raise ValueError("Неизвестный приказ")
    if not extra and action not in ("wait", "defend") and alive(me) and not me.get("morale") \
            and chance(seed, s["turn"], f"morale:{me['id']}") < 100 * _perks(s).get("morale", 0) and _living(s, "npc"):
        me["morale"] = True          # once per round per stack
        extra = True
        events.append({"type": "morale", "actor": me["id"]})
    if not extra:
        me["acted"] = True
        _after_turn(s, me, events)
    s["turn"] += 1
    outcome = _advance(s, seed, hero, bonus, events)
    if outcome == "active" and s["turn"] > MAX_TURNS:
        outcome = "defeat"
    return s, events, outcome


def from_legacy(state, unit_id):
    """Convert a pre-0.7 single-squad battle (player/npc HP) into stacks."""
    s = {k: v for k, v in state.items() if k not in ("player", "npc")}
    p, n = state["player"], state["npc"]
    player = make_stack("p1", "player", "rifles", 10, p["pos"], unit_id)
    player["hp"] = max(1, p["hp"])
    npc = make_stack("n1", "npc", "rifles", max(1, math.ceil(n["hp"] / UNITS["rifles"]["hp"])), n["pos"])
    npc["hp"] = max(1, n["hp"])
    s.update({"stacks": [player, npc], "round": 1, "ability_used": False, "active": "p1", "order": []})
    _new_round(s)
    s["active"] = "p1"
    return s


def summary(state):
    """Per player stack: survivors and top-member health after a battle."""
    result = {}
    for st in state["stacks"]:
        if st["side"] != "player":
            continue
        each = UNITS[st["kind"]]["hp"]
        n = alive(st)
        top = st["hp"] - (n - 1) * each if n else 0
        result[st["unit_id"]] = {"alive": n, "start": st["start"], "hp_pct": max(1, round(100 * top / each)) if n else 0}
    return result


# ---- internals -------------------------------------------------------------

def _get(s, sid):
    return next((x for x in s["stacks"] if x["id"] == sid and alive(x)), None)


def _living(s, side=None):
    return [x for x in s["stacks"] if alive(x) and (side is None or x["side"] == side)]


def _occupied(s, pos, ignore=None):
    return any(x["pos"] == pos and x is not ignore for x in _living(s))


def _speed(stack, hero):
    return UNITS[stack["kind"]]["speed"] + (1 if hero == "storm" and stack["side"] == "player" else 0)


def _inside(pos):
    return 0 <= pos[0] < SIZE and 0 <= pos[1] < SIZE


def _move(s, stack, target, hero):
    if not _inside(target) or _occupied(s, target, stack) or distance(stack["pos"], target) > _speed(stack, hero) \
            or target == stack["pos"]:
        raise ValueError("Недоступное перемещение")
    stack["pos"] = list(target)


def _target(s, me, sid):
    enemies = _living(s, "npc" if me["side"] == "player" else "player")
    if sid:
        target = next((x for x in enemies if x["id"] == sid), None)
        if not target:
            raise ValueError("Цель недоступна")
        return target
    return min(enemies, key=lambda x: (distance(me["pos"], x["pos"]), x["id"]))


def _approach(s, me, target, hero):
    """Free hex adjacent to target within reach, nearest to the attacker."""
    if distance(me["pos"], target["pos"]) == 1:
        return me["pos"]
    spots = [[target["pos"][0] + dq, target["pos"][1] + dr] for dq, dr in DIRS]
    spots = [p for p in spots if _inside(p) and not _occupied(s, p, me) and distance(me["pos"], p) <= _speed(me, hero)]
    return min(spots, key=lambda p: (distance(me["pos"], p), p)) if spots else None


def _damage(s, attacker, target, seed, hero, bonus, factor, tag, fixed_roll=None):
    a, d = UNITS[attacker["kind"]], UNITS[target["kind"]]
    value = alive(attacker) * a["damage"]
    if a.get("trait") != "pierce":
        value *= max(0.6, 1 - 0.05 * d["defense"])
    if d.get("trait") == "shield" and not a["melee"]:
        value *= 0.6
    if target["defending"]:
        value *= 0.6
    if d["infantry"] and target["pos"] in s["cover"] and a.get("trait") != "marksman":
        value *= 0.8
    if attacker["side"] == "player":
        if hero == "raven" and a["infantry"]:
            value *= 1.05
        value *= 1 + min(max(bonus, 0), 0.10)
        perks = _perks(s)
        value *= 1 + perks.get("attack", 0) + (0 if a["melee"] else perks.get("ranged", 0))
    elif hero == "titan":
        value *= 0.95
    if target["side"] == "player":
        value *= 1 - _perks(s).get("defense", 0)
    if not a["melee"] and a.get("trait") != "marksman" and any(distance(attacker["pos"], e["pos"]) == 1
                              for e in _living(s, "npc" if attacker["side"] == "player" else "player")):
        value *= 0.5   # shooters fire badly with an enemy in their face
    value *= attacker.get("buff", 1) * attacker.get("weak", 1) * target.get("guard", 1)
    value *= factor * (fixed_roll or roll(seed, s["turn"], f"{tag}:{attacker['id']}")) / 100
    return max(1, round(value))


def _hit(s, attacker, target, seed, hero, bonus, events, factor, kind):
    before = alive(target)
    lucky = attacker["side"] == "player" and kind != "retaliate" and \
        chance(seed, s["turn"], f"luck:{kind}:{attacker['id']}") < 100 * _perks(s).get("luck", 0)
    if lucky:
        factor *= 1.5
        events.append({"type": "luck", "actor": attacker["id"]})
    dmg = _damage(s, attacker, target, seed, hero, bonus, factor, kind)
    target["hp"] = max(0, target["hp"] - dmg)
    events.append({"type": kind, "actor": attacker["id"], "target": target["id"], "damage": dmg,
                   "kills": before - alive(target)})
    if not alive(target):
        events.append({"type": "destroyed", "actor": target["id"]})


def _attack(s, me, target, seed, hero, bonus, events, ranged_any, factor):
    spec = UNITS[me["kind"]]
    if spec["melee"] and not ranged_any:
        spot = _approach(s, me, target, hero)
        if spot is None:
            raise ValueError("Цель вне досягаемости: подойдите ближе")
        if spot != me["pos"]:
            me["pos"] = list(spot)
            events.append({"type": "move", "actor": me["id"], "pos": me["pos"]})
            if spec.get("trait") == "charge":
                factor *= 1.3
    elif not ranged_any and distance(me["pos"], target["pos"]) > spec["range"]:
        raise ValueError("Цель вне дальности: подойдите ближе")
    _hit(s, me, target, seed, hero, bonus, events, factor, "attack")
    # One retaliation per round when struck at close quarters.
    if alive(target) and not target["retaliated"] and distance(me["pos"], target["pos"]) == 1 \
            and spec.get("trait") != "first_strike" and not target.get("mute"):
        target["retaliated"] = True
        t = UNITS[target["kind"]]
        _hit(s, target, me, seed, hero, bonus, events,
             1.0 if t["melee"] or t.get("trait") == "bayonet" else 0.5, "retaliate")


def _after_turn(s, me, events):
    """Passive traits that trigger once the stack has acted."""
    trait = UNITS[me["kind"]].get("trait")
    if not alive(me) or trait not in ("medic", "self_repair"):
        return
    targets = [me] if trait == "self_repair" else [x for x in _living(s, me["side"])
                                                   if x is not me and distance(x["pos"], me["pos"]) == 1]
    share = 0.10 if trait == "self_repair" else 0.15
    for x in targets:
        top = x["start"] * UNITS[x["kind"]]["hp"]
        healed = min(top, x["hp"] + math.ceil(share * top)) - x["hp"]
        if healed > 0:
            x["hp"] += healed
            events.append({"type": "heal", "actor": me["id"], "target": x["id"], "amount": healed})


def _ability(s, me, command, seed, hero, bonus, events):
    events.append({"type": "ability", "actor": me["id"], "name": ABILITIES[hero]["name"]})
    if hero == "raven":
        _attack(s, me, _target(s, me, command.get("target")), seed, hero, bonus, events, False, 1.5)
    elif hero == "valkyrie":
        _attack(s, me, _target(s, me, command.get("target")), seed, hero, bonus, events, True, 1.0)
    elif hero == "titan":
        for x in _living(s, "player"):
            x["defending"] = True
    elif hero == "phoenix":
        each = UNITS[me["kind"]]["hp"]
        me["hp"] = min(me["start"] * each, me["hp"] + math.ceil(0.3 * me["start"] * each))
    elif hero == "ghost":
        target = _target(s, me, command.get("target"))
        target["skip"] = True
    elif hero == "storm":
        return True   # same stack acts again
    return False


def _skill(s, me, command, seed, hero, bonus, events):
    """The stack's own once-per-battle ability. Returns True when the stack may act again."""
    spec = UNITS[me["kind"]].get("ability")
    if not spec:
        raise ValueError("У этого отряда нет способности")
    if me.get("skill_used"):
        raise ValueError("Способность отряда уже использована в этом бою")
    effect, v = spec["effect"], spec["value"]
    events.append({"type": "skill", "actor": me["id"], "name": spec["name"]})
    allies = _living(s, me["side"])
    near = lambda radius: [x for x in allies if distance(x["pos"], me["pos"]) <= radius]
    extra = False
    if effect in ("strike", "longshot", "splash", "suppress_attack"):
        target = _target(s, me, command.get("target"))
        _attack(s, me, target, seed, hero, bonus, events, effect == "longshot",
                v if effect in ("strike", "longshot", "suppress_attack") else 1.0)
        if effect == "splash":
            for x in _living(s, target["side"]):
                if x is not target and distance(x["pos"], target["pos"]) == 1:
                    _hit(s, me, x, seed, hero, bonus, events, v, "splash")
        if effect == "suppress_attack" and alive(target):
            target["weak"], target["mute"] = 0.7, True
    elif effect in ("suppress", "jam", "mark"):
        target = _target(s, me, command.get("target"))
        if effect == "suppress":
            target["weak"], target["mute"] = v, True
        elif effect == "jam":
            target["skip"] = True
        else:
            target["guard"] = v
        events.append({"type": effect, "actor": me["id"], "target": target["id"]})
    elif effect == "dash":
        target = [command.get("q", -1), command.get("r", -1)]
        if not _inside(target) or _occupied(s, target, me) or target == me["pos"] \
                or distance(me["pos"], target) > _speed(me, hero) + v:
            raise ValueError("Выберите свободный гекс в пределах рывка")
        me["pos"] = list(target)
        events.append({"type": "move", "actor": me["id"], "pos": me["pos"]})
        extra = True
    elif effect == "fortify":
        me["defending"], me["guard"] = True, v
    elif effect in ("guard_aura", "smoke"):
        for x in near(1 if effect == "guard_aura" else 2):
            x["guard"] = min(x.get("guard", 1), v)
    elif effect in ("heal", "heal_aura"):
        for x in ([me] if effect == "heal" else near(1)):
            top = x["start"] * UNITS[x["kind"]]["hp"]
            healed = min(top, x["hp"] + math.ceil(v * top)) - x["hp"]
            if healed > 0:
                x["hp"] += healed
                events.append({"type": "heal", "actor": me["id"], "target": x["id"], "amount": healed})
    me["skill_used"] = True
    return extra


def _new_round(s):
    for x in s["stacks"]:
        x["acted"] = x["retaliated"] = False
        x["defending"] = False
        for flag in ("buff", "weak", "guard", "mute", "morale"):
            x.pop(flag, None)
    bonus = _perks(s).get("initiative", 0)
    s["order"] = [x["id"] for x in sorted(_living(s), key=lambda x: (
        -UNITS[x["kind"]]["initiative"] - (bonus if x["side"] == "player" else 0),
        0 if x["side"] == "player" else 1, x["id"]))]


def _next(s):
    return next((sid for sid in s["order"] if (x := _get(s, sid)) and not x["acted"]), None)


def _outcome(s):
    if not _living(s, "npc"):
        return "victory"
    if not _living(s, "player"):
        return "defeat"
    return "active"


def _advance(s, seed, hero, bonus, events):
    guard = 0
    while True:
        outcome = _outcome(s)
        if outcome != "active":
            s["active"] = None
            return outcome
        sid = _next(s)
        if sid is None:
            s["round"] += 1
            _new_round(s)
            events.append({"type": "round", "round": s["round"]})
            continue
        stack = _get(s, sid)
        if stack["side"] == "player":
            s["active"] = sid
            return "active"
        stack["acted"] = True
        if stack.get("skip"):
            stack["skip"] = False
            events.append({"type": "jammed", "actor": sid})
            continue
        _npc_turn(s, stack, seed, hero, bonus, events)
        _after_turn(s, stack, events)
        guard += 1
        if guard > 200:
            raise RuntimeError("combat loop guard")


def _npc_turn(s, me, seed, hero, bonus, events):
    spec = UNITS[me["kind"]]
    enemies = _living(s, "player")
    target = min(enemies, key=lambda x: (distance(me["pos"], x["pos"]), x["hp"], x["id"]))
    if spec["melee"]:
        spot = _approach(s, me, target, hero)
        if spot is not None:
            _attack(s, me, target, seed, hero, bonus, events, False, 1.0)
            return
    elif distance(me["pos"], target["pos"]) <= spec["range"]:
        _attack(s, me, target, seed, hero, bonus, events, False, 1.0)
        return
    # Close the distance as far as speed allows.
    best, reach = me["pos"], _speed(me, hero)
    for q in range(SIZE):
        for r in range(SIZE):
            p = [q, r]
            if distance(me["pos"], p) <= reach and not _occupied(s, p, me) and \
                    (distance(p, target["pos"]), p) < (distance(best, target["pos"]), best):
                best = p
    if best != me["pos"]:
        me["pos"] = best
        events.append({"type": "move", "actor": me["id"], "pos": best})


# ---- previews and quick combat ---------------------------------------------

def preview(state, seed, hero, bonus):
    """For the active player stack: expected damage, kills and retaliation per enemy stack."""
    s = copy.deepcopy(state)
    me = _get(s, s.get("active"))
    if not me or me["side"] != "player":
        return {}
    spec = UNITS[me["kind"]]
    out = {}
    for target in _living(s, "npc"):
        sim = copy.deepcopy(s)
        a, t = _get(sim, me["id"]), _get(sim, target["id"])
        factor, reach = 1.0, True
        if spec["melee"]:
            spot = _approach(sim, a, t, hero)
            if spot is None:
                reach = False
            else:
                if spot != a["pos"] and spec.get("trait") == "charge":
                    factor *= 1.3
                a["pos"] = list(spot)
        elif distance(a["pos"], t["pos"]) > spec["range"]:
            reach = False
        lo = _damage(sim, a, t, seed, hero, bonus, factor, "attack", 90)
        hi = _damage(sim, a, t, seed, hero, bonus, factor, "attack", 110)
        each = UNITS[t["kind"]]["hp"]
        left = lambda d: max(0, math.ceil((t["hp"] - d) / each))
        info = {"reach": reach, "damage": [lo, hi], "kills": [alive(t) - left(lo), alive(t) - left(hi)], "retaliation": None}
        if reach and left(lo) and not t["retaliated"] and not t.get("mute") and distance(a["pos"], t["pos"]) == 1 \
                and spec.get("trait") != "first_strike":
            tt = UNITS[t["kind"]]
            rf = 1.0 if tt["melee"] or tt.get("trait") == "bayonet" else 0.5
            r_lo, r_hi = [], []
            for d, bucket in ((hi, r_lo), (lo, r_hi)):
                t2 = dict(t, hp=t["hp"] - d)
                if alive(t2):
                    bucket.append(_damage(sim, t2, a, seed, hero, bonus, rf, "retaliate", 90 if bucket is r_lo else 110))
            if r_hi:
                r_lo = r_lo or [0]
                me_each = UNITS[a["kind"]]["hp"]
                info["retaliation"] = {"damage": [r_lo[0], r_hi[0]],
                                       "kills": [alive(a) - max(0, math.ceil((a["hp"] - r_lo[0]) / me_each)),
                                                 alive(a) - max(0, math.ceil((a["hp"] - r_hi[0]) / me_each))]}
        out[target["id"]] = info
    return out


def ai_command(state, hero):
    """Quick combat: the server plays the active player stack like a sensible NPC."""
    me = _get(state, state["active"])
    spec = UNITS[me["kind"]]
    enemies = _living(state, "npc")
    target = min(enemies, key=lambda x: (distance(me["pos"], x["pos"]), x["hp"], x["id"]))
    if spec["melee"]:
        if _approach(state, me, target, hero) is not None:
            return {"action": "attack", "target": target["id"]}
    elif distance(me["pos"], target["pos"]) <= spec["range"]:
        # Ranged: shoot the weakest enemy in range.
        in_range = [x for x in enemies if distance(me["pos"], x["pos"]) <= spec["range"]]
        return {"action": "attack", "target": min(in_range, key=lambda x: (x["hp"], x["id"]))["id"]}
    best, reach = me["pos"], _speed(me, hero)
    for q in range(SIZE):
        for r in range(SIZE):
            p = [q, r]
            if distance(me["pos"], p) <= reach and not _occupied(state, p, me) and \
                    (distance(p, target["pos"]), p) < (distance(best, target["pos"]), best):
                best = p
    if best != me["pos"]:
        return {"action": "move", "q": best[0], "r": best[1]}
    return {"action": "defend"}
