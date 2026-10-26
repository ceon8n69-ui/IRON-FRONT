"""Fictional balance: deterministic simultaneous attacks, no real weapon data."""

import copy, hashlib


def distance(a, b):
    q = a[0] - b[0]
    r = a[1] - b[1]
    return max(abs(q), abs(r), abs(q + r))


def roll(seed, turn, actor):
    return (
        90
        + int(hashlib.sha256(f"{seed}:{turn}:{actor}".encode()).hexdigest()[:8], 16)
        % 21
    )


def resolve(state, command, seed, hero, bonus):
    s = copy.deepcopy(state)
    events = []
    p = s["player"]
    n = s["npc"]
    t = s["turn"]
    if command["action"] == "move":
        target = [command["q"], command["r"]]
        if (
            not all(0 <= v < 9 for v in target)
            or target == n["pos"]
            or distance(p["pos"], target) > (2 if hero == "storm" else 1)
        ):
            raise ValueError("Недоступное перемещение")
        p["pos"] = target
        events.append({"type": "move", "actor": "player", "pos": target})
    elif command["action"] == "attack" and distance(p["pos"], n["pos"]) > 3:
        raise ValueError("Цель вне дальности: подойдите ближе")
    if distance(p["pos"], n["pos"]) > 2:
        q, r = n["pos"]
        candidates = [
            [q + 1, r],
            [q - 1, r],
            [q, r + 1],
            [q, r - 1],
            [q + 1, r - 1],
            [q - 1, r + 1],
        ]
        candidates = [
            c for c in candidates if all(0 <= v < 9 for v in c) and c != p["pos"]
        ]
        n["pos"] = min(candidates, key=lambda c: distance(c, p["pos"]))
        events.append({"type": "move", "actor": "npc", "pos": n["pos"]})
    pd = nd = 0
    if command["action"] == "attack" and distance(p["pos"], n["pos"]) <= 3:
        pd = round(
            24
            * (1.05 if hero == "raven" else 1)
            * (1 + min(bonus, 0.10))
            * roll(seed, t, "player")
            / 100
        )
    if distance(p["pos"], n["pos"]) <= 2:
        cover = 0.8 if p["pos"] in s["cover"] else 1
        nd = round(
            13
            * cover
            * (0.95 if hero == "titan" else 1)
            * (0.6 if command["action"] == "defend" else 1)
            * roll(seed, t, "npc")
            / 100
        )
    p["hp"] = max(0, p["hp"] - nd)
    n["hp"] = max(0, n["hp"] - pd)
    events.extend(
        [
            {"type": "damage", "actor": "npc", "amount": pd},
            {"type": "damage", "actor": "player", "amount": nd},
        ]
    )
    s["turn"] += 1
    outcome = "active"
    if p["hp"] == 0:
        outcome = "defeat"
    elif n["hp"] == 0:
        outcome = "victory"
    elif s["turn"] > 50:
        outcome = "defeat"
    return s, events, outcome
