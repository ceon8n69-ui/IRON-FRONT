"""Greedy AI seat for match rooms. Plays through match_engine.apply, so it obeys every rule
and sees only what its seat could see (explored cities, units in sight)."""
from . import match_engine as E

TECH_ORDER = ["motors", "forestry", "farming", "mining", "ballistics", "assault", "fortify", "armor"]
ROLE_ORDER = ["armor", "assault", "artillery", "scouts", "rifles"]


def _try(state, seat, action, log):
    try:
        state, events = E.apply(state, seat, action)
        log.extend(events)
        return state, True
    except E.Illegal:
        return state, False


def play_turn(state, seat):
    """Play one full turn for `seat` and end it. Returns (state, events)."""
    log = []
    s = state
    p = s["players"][str(seat)]
    # Cities: specialization and level rewards.
    for c in list(s["cities"].values()):
        if c["owner"] != seat:
            continue
        if c["spec"] is None:
            mine = sum(1 for x in s["cities"].values() if x["owner"] == seat)
            s, _ = _try(s, seat, {"type": "spec", "city": c["id"], "spec": "factory" if mine % 2 else "market"}, log)
        if s["cities"][c["id"]]["reward"]:
            opts = E.REWARDS[s["cities"][c["id"]]["reward"]]
            s, _ = _try(s, seat, {"type": "reward", "city": c["id"], "reward": opts[0][0]}, log)
    # Units: capture, fight, advance.
    for uid in list(s["units"]):
        u = s["units"].get(uid)
        if not u or u["owner"] != seat:
            continue
        if E.can_promote(u):
            s, _ = _try(s, seat, {"type": "promote", "unit": uid, "branch": E.BRANCHES[u["role"]][0][0]}, log)
        s = _unit_turn(s, seat, uid, log)
        if s["winner"] is not None:
            return s, log
    # Economy: research, improvements, recruits.
    for tech in TECH_ORDER:
        p = s["players"][str(seat)]
        if tech not in p["techs"] and p["stars"] >= E.tech_cost(s, seat, tech) + 2:
            s, done = _try(s, seat, {"type": "research", "tech": tech}, log)
            if done:
                break
    for k in sorted(s["tiles"]):
        q, r = E.unkey(k)
        for imp in E.improvement_options(s, seat, q, r):
            if s["players"][str(seat)]["stars"] >= E.IMPROVEMENTS[imp][1] + 2:
                s, _ = _try(s, seat, {"type": "build", "q": q, "r": r, "improvement": imp}, log)
                break
    for c in list(s["cities"].values()):
        if c["owner"] != seat:
            continue
        roles = E.available_roles(s, seat, c["id"])
        for role in ROLE_ORDER:
            if role in roles and s["players"][str(seat)]["stars"] >= E.ROLES[role]["cost"]:
                s, done = _try(s, seat, {"type": "train", "city": c["id"], "role": role}, log)
                if done:
                    break
    s, _ = _try(s, seat, {"type": "end_turn"}, log)
    return s, log


def _goal(s, seat, u):
    """Nearest known city we do not own, else nearest visible enemy."""
    explored = set(s["players"][str(seat)]["explored"])
    seen = E.visible(s, seat)
    spots = [(c["q"], c["r"]) for c in s["cities"].values() if c["owner"] != seat and E.key(c["q"], c["r"]) in explored]
    spots += [(x["q"], x["r"]) for x in s["units"].values() if x["owner"] != seat and E.key(x["q"], x["r"]) in seen]
    if not spots:   # explore: head for the far side of the map
        size = s["size"]
        spots = [E.unkey(k) for k in s["tiles"] if k not in explored] or [(size // 2 - size // 4, size // 2)]
    here = (u["q"], u["r"])
    return min(spots, key=lambda p: (E.distance(here, p), p))


def _attack_best(s, seat, uid, log):
    u = s["units"].get(uid)
    if not u:
        return s, False
    best, score = None, None
    for t in E.targets(s, u):
        dmg, back = E.forecast(s, u, s["units"][t])
        kill = dmg >= s["units"][t]["hp"]
        value = (10 if kill else 0) + dmg - back
        if (kill or dmg >= back) and (score is None or value > score):
            best, score = t, value
    if best:
        return _try(s, seat, {"type": "attack", "unit": uid, "target": best}, log)
    return s, False


def _unit_turn(s, seat, uid, log):
    u = s["units"][uid]
    city = E.city_at(s, u["q"], u["r"])
    if city and city["owner"] != seat and not u["moved"]:
        s, done = _try(s, seat, {"type": "capture", "unit": uid}, log)
        if done:
            return s
    s, attacked = _attack_best(s, seat, uid, log)
    u = s["units"].get(uid)
    if not u:
        return s
    if u["hp"] < E.max_hp(u) * .4 and not u["moved"] and not attacked:
        s, _ = _try(s, seat, {"type": "recover", "unit": uid}, log)
        return s
    reach = E.moves(s, u)
    if reach:
        goal = _goal(s, seat, u)
        here = E.distance((u["q"], u["r"]), goal)
        best = min(reach, key=lambda k: (E.distance(E.unkey(k), goal), k))
        if E.distance(E.unkey(best), goal) < here:
            q, r = E.unkey(best)
            s, _ = _try(s, seat, {"type": "move", "unit": uid, "q": q, "r": r}, log)
    if not attacked:
        s, _ = _attack_best(s, seat, uid, log)
    return s
