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


def new_battle(player_stacks, npc_stacks, cover, seed, hero, bonus):
    state = {"turn": 1, "round": 1, "stacks": player_stacks + npc_stacks, "cover": cover,
             "ability_used": False, "active": None, "order": []}
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
    elif action == "ability":
        if s["ability_used"]:
            raise ValueError("Способность командира уже использована в этом бою")
        extra = _ability(s, me, command, seed, hero, bonus, events)
        s["ability_used"] = True
    else:
        raise ValueError("Неизвестный приказ")
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


def _damage(s, attacker, target, seed, hero, bonus, factor, tag):
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
    elif hero == "titan":
        value *= 0.95
    if not a["melee"] and a.get("trait") != "marksman" and any(distance(attacker["pos"], e["pos"]) == 1
                              for e in _living(s, "npc" if attacker["side"] == "player" else "player")):
        value *= 0.5   # shooters fire badly with an enemy in their face
    value *= factor * roll(seed, s["turn"], f"{tag}:{attacker['id']}") / 100
    return max(1, round(value))


def _hit(s, attacker, target, seed, hero, bonus, events, factor, kind):
    before = alive(target)
    dmg = _damage(s, attacker, target, seed, hero, bonus, factor, kind)
    target["hp"] = max(0, target["hp"] - dmg)
    events.append({"type": kind, "actor": attacker["id"], "target": target["id"], "damage": dmg,
                   "kills": before - alive(target)})
    if not alive(target):
        events.append({"type": "destroyed", "actor": target["id"]})


def _attack(s, me, target, seed, hero, bonus, events, ranged_any, factor):
    spec = UNITS[me["kind"]]
    if spec["melee"]:
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
            and spec.get("trait") != "first_strike":
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


def _new_round(s):
    for x in s["stacks"]:
        x["acted"] = x["retaliated"] = False
        x["defending"] = False
    s["order"] = [x["id"] for x in sorted(_living(s), key=lambda x: (
        -UNITS[x["kind"]]["initiative"], 0 if x["side"] == "player" else 1, x["id"]))]


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
