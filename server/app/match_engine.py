"""Polytopia-style match engine for IRON FRONT rooms.

Pure and deterministic: every function takes the match state (a JSON-able dict)
and either returns information or mutates a deep copy via apply(). Rules:

* Hex map (axial q, r), terrain field / forest / mountain / water, resources.
* One currency: supply (★). Cities pay their income at the start of the owner's turn.
* Neutral villages are captured by a unit that starts its turn on them; the captor
  chooses the city's specialization. Cities grow from improvements built on their
  territory and offer a reward choice at every new level.
* Units move, then may attack (Polytopia combat formula). Melee killers advance.
  Three kills make a unit eligible for a promotion along one of two branches.
* Tech tree unlocks units and improvements. Last player holding cities wins.
"""
import copy, math, random

DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]
SIZES = {"small": 11, "medium": 15, "large": 19}
START_STARS = 5
VISION = 2

# Fictional balance, Polytopia-like scale. Roles map to the faction's unit art.
ROLES = {
    "rifles":    {"name": "Стрелки",       "cost": 2,  "hp": 10, "atk": 2.0, "def": 2.0, "mv": 1, "rng": 1, "tech": None},
    "scouts":    {"name": "Разведчики",    "cost": 3,  "hp": 10, "atk": 1.0, "def": 1.0, "mv": 2, "rng": 1, "tech": "motors", "escape": True},
    "artillery": {"name": "Артиллерия",    "cost": 6,  "hp": 10, "atk": 3.0, "def": 1.0, "mv": 1, "rng": 2, "tech": "ballistics"},
    "assault":   {"name": "Штурмовики",    "cost": 5,  "hp": 15, "atk": 3.0, "def": 3.0, "mv": 1, "rng": 1, "tech": "assault"},
    "armor":     {"name": "Бронетехника",  "cost": 10, "hp": 20, "atk": 3.5, "def": 1.0, "mv": 3, "rng": 1, "tech": "armor", "factory": True},
}
PROMOTION_KILLS = 3
BRANCHES = {   # two promotion branches per role: (key, name, stat bonuses)
    "rifles":    [("bayonets", "Штыки", {"atk": 1}), ("trenches", "Окопы", {"def": 1})],
    "scouts":    [("raid", "Рейд", {"mv": 1}), ("mg", "Пулемёт", {"atk": 1})],
    "artillery": [("long", "Дальнобой", {"rng": 1}), ("calibre", "Калибр", {"atk": 1})],
    "assault":   [("grenades", "Гранаты", {"atk": 1}), ("plates", "Бронежилеты", {"def": 1})],
    "armor":     [("ram", "Таран", {"atk": 1}), ("crew", "Экипаж", {"def": 1, "hp": 5})],
}
TECHS = {   # key: (name, tier, prerequisite, unlocks)
    "farming":    ("Земледелие", 1, None, "Ферма на поле с урожаем"),
    "forestry":   ("Лесное дело", 1, None, "Лесопилка в лесу"),
    "mining":     ("Горное дело", 1, None, "Шахты; горы проходимы"),
    "motors":     ("Моторы", 1, None, "Разведчики"),
    "ballistics": ("Баллистика", 1, None, "Артиллерия"),
    "assault":    ("Штурм", 2, "mining", "Штурмовики"),
    "fortify":    ("Фортификация", 2, "forestry", "Стены в любом городе"),
    "armor":      ("Бронетехника", 3, "motors", "Бронетехника (в заводских городах)"),
}
IMPROVEMENTS = {   # key: (name, cost, pop, tech, terrain, resource)
    "gather": ("Сбор урожая", 2, 1, None, None, "fruit"),
    "farm":   ("Ферма", 5, 2, "farming", "field", "crop"),
    "lumber": ("Лесопилка", 3, 1, "forestry", "forest", None),
    "mine":   ("Шахта", 5, 2, "mining", "mountain", "ore"),
}
SPECS = {   # chosen when a city is captured
    "factory": ("Завод", "+1 ★ за ход, здесь нанимают бронетехнику"),
    "fort":    ("Форт", "Стены сразу, +1 место для отрядов"),
    "market":  ("Рынок", "+2 ★ за ход"),
    "outpost": ("Штаб связи", "Территория и обзор шире на 1"),
}
REWARDS = {   # by new level (5 = every level from 5 up)
    2: [("workshop", "Мастерская: +1 ★ за ход"), ("recruit", "Ополчение: бесплатные стрелки")],
    3: [("walls", "Стены: защита в городе ×2,5"), ("cache", "Склад: +5 ★ сразу")],
    4: [("borders", "Границы шире"), ("growth", "Приток жителей: +3 населения")],
    5: [("park", "Парк: +1 ★ за ход"), ("guard", "Гвардия: бесплатные штурмовики")],
}
CITY_NAMES = ["Ржавец", "Котлоград", "Медный Брод", "Шестерня", "Дымов", "Заклёпск", "Паровск", "Болтин",
              "Тигельск", "Литейка", "Поршнев", "Кривошип", "Угольный Яр", "Маховик", "Сварогорск", "Окалина",
              "Броневка", "Клапанск", "Медь-на-Реке", "Гайкин Луг", "Фланец", "Цилиндров", "Штамповка", "Кузнецк",
              "Вольтов", "Свинцовка", "Чугунов", "Котельня", "Рессорск", "Шплинт"]


class Illegal(ValueError):
    """An action the rules do not allow; the message is shown to the player."""


# ---- geometry ----------------------------------------------------------------

def key(q, r):
    return f"{q},{r}"


def unkey(k):
    q, r = k.split(",")
    return int(q), int(r)


def distance(a, b):
    dq, dr = a[0] - b[0], a[1] - b[1]
    return max(abs(dq), abs(dr), abs(dq + dr))


def neighbors(q, r):
    return [(q + dq, r + dr) for dq, dr in DIRS]


def within(q, r, radius):
    return [(q + dq, r + dr) for dq in range(-radius, radius + 1) for dr in range(-radius, radius + 1)
            if abs(dq + dr) <= radius]


# ---- map generation ------------------------------------------------------------

def generate(size_name, seats, seed, factions):
    """New match state for `seats` (list of seat numbers) on a seeded map."""
    size = SIZES[size_name]
    rng = random.Random(f"iron-match:{seed}")
    coords = [(c - r // 2, r) for r in range(size) for c in range(size)]
    terrain = {}
    for q, r in coords:
        x = rng.random()
        terrain[(q, r)] = "water" if x < .14 else "mountain" if x < .26 else "forest" if x < .52 else "field"
    for _ in range(2):   # smooth: tiles drift toward their neighbours' majority
        nxt = {}
        for (q, r), t in terrain.items():
            around = [terrain[n] for n in neighbors(q, r) if n in terrain]
            top = max(set(around), key=around.count) if around else t
            nxt[(q, r)] = top if around.count(top) >= 4 and rng.random() < .7 else t
        terrain = nxt
    # Capitals in opposite corners (inset), with a passable ring around them.
    inset = 2
    corners = [(inset - (inset // 2), inset), (size - 1 - inset - ((size - 1 - inset) // 2), size - 1 - inset),
               (size - 1 - inset - inset // 2, inset), (inset - (size - 1 - inset) // 2, size - 1 - inset)]
    spots = corners[:len(seats)]
    for q, r in spots:
        for n in within(q, r, 1):
            if n in terrain:
                terrain[n] = "field" if terrain[n] in ("water", "mountain") else terrain[n]
        terrain[(q, r)] = "field"
    for a, b in zip(spots, spots[1:] + spots[:1]):   # carve a land route between capitals
        steps = distance(a, b)
        for i in range(steps + 1):
            q = round(a[0] + (b[0] - a[0]) * i / steps); r = round(a[1] + (b[1] - a[1]) * i / steps)
            if (q, r) in terrain and terrain[(q, r)] in ("water", "mountain"):
                terrain[(q, r)] = "field"
    tiles = {}
    for (q, r), t in terrain.items():
        res = None
        x = rng.random()
        if t == "field":
            res = "crop" if x < .2 else "fruit" if x < .32 else None
        elif t == "forest":
            res = "fruit" if x < .14 else None
        elif t == "mountain":
            res = "ore" if x < .5 else None
        tiles[key(q, r)] = {"t": t, "res": res, "imp": None, "city": None}
    state = {"size": size, "size_name": size_name, "seed": seed, "turn": 1, "order": list(seats), "current": seats[0],
             "tiles": tiles, "cities": {}, "units": {}, "players": {}, "next_id": 1, "winner": None, "log": []}
    names = CITY_NAMES[:]
    rng.shuffle(names)
    for seat, (q, r) in zip(seats, spots):
        state["players"][str(seat)] = {"seat": seat, "stars": START_STARS, "techs": [], "explored": [],
                                       "eliminated": False, "faction": factions.get(seat, "raven")}
        cid = _new_city(state, q, r, names.pop(), seat, capital=True)
        state["cities"][cid]["spec"] = "capital"
        _spawn(state, "rifles", q, r, seat, cid, ready=True)
    # Villages: on land, at least 2 hexes from any other settlement, reachable from capitals.
    reach = _reachable(state, spots[0])
    candidates = [unkey(k) for k, t in tiles.items() if t["t"] in ("field", "forest") and unkey(k) in reach]
    rng.shuffle(candidates)
    wanted = max(len(seats) * 3, size * size // 13)
    for q, r in candidates:
        if wanted <= 0:
            break
        if all(distance((q, r), (c["q"], c["r"])) >= 3 for c in state["cities"].values()):
            _new_city(state, q, r, names.pop() if names else f"Посёлок {state['next_id']}", None)
            wanted -= 1
    for seat in seats:
        _reveal(state, seat)
    _start_turn(state, seats[0], pay=False)
    return state


def _reachable(state, start):
    seen, todo = {start}, [start]
    while todo:
        q, r = todo.pop()
        for n in neighbors(q, r):
            t = state["tiles"].get(key(*n))
            if t and t["t"] in ("field", "forest") and n not in seen:
                seen.add(n); todo.append(n)
    return seen


def _new_city(state, q, r, name, owner, capital=False):
    cid = f"c{state['next_id']}"; state["next_id"] += 1
    state["cities"][cid] = {"id": cid, "name": name, "q": q, "r": r, "owner": owner, "level": 1, "pop": 0,
                            "spec": None, "capital": capital, "radius": 1, "walls": False, "bonus": 0,
                            "reward": None}
    state["tiles"][key(q, r)]["t"] = "field" if state["tiles"][key(q, r)]["t"] in ("water", "mountain") else state["tiles"][key(q, r)]["t"]
    state["tiles"][key(q, r)]["res"] = None
    if owner is not None:
        _claim(state, cid)
    return cid


def _claim(state, cid):
    c = state["cities"][cid]
    for q, r in within(c["q"], c["r"], c["radius"]):
        t = state["tiles"].get(key(q, r))
        if t and (t["city"] is None or t["city"] == cid):
            t["city"] = cid


def _spawn(state, role, q, r, seat, home, ready=False):
    uid = f"u{state['next_id']}"; state["next_id"] += 1
    spec = ROLES[role]
    state["units"][uid] = {"id": uid, "role": role, "q": q, "r": r, "owner": seat, "home": home,
                           "hp": spec["hp"], "moved": not ready, "attacked": not ready, "kills": 0, "branch": None}
    return uid


# ---- derived values ------------------------------------------------------------

def stat(unit, name):
    base = ROLES[unit["role"]][name]
    if unit.get("branch"):
        for k, n, bonus in BRANCHES[unit["role"]]:
            if k == unit["branch"]:
                base += bonus.get(name, 0)
    return base


def max_hp(unit):
    return stat(unit, "hp") + (5 if unit.get("branch") else 0)


def income(state, cid):
    c = state["cities"][cid]
    return c["level"] + (1 if c["capital"] else 0) + {"factory": 1, "market": 2}.get(c["spec"], 0) + c["bonus"]


def tech_cost(state, seat, tech):
    cities = sum(1 for c in state["cities"].values() if c["owner"] == seat)
    return TECHS[tech][1] * max(1, cities) + 4


def unit_cap(state, cid):
    c = state["cities"][cid]
    return c["level"] + 1 + (1 if c["spec"] == "fort" else 0)


def unit_at(state, q, r):
    return next((u for u in state["units"].values() if u["q"] == q and u["r"] == r), None)


def city_at(state, q, r):
    return next((c for c in state["cities"].values() if c["q"] == q and c["r"] == r), None)


def passable(state, seat, q, r):
    t = state["tiles"].get(key(q, r))
    if not t or t["t"] == "water":
        return False
    return t["t"] != "mountain" or "mining" in state["players"][str(seat)]["techs"]


def visible(state, seat):
    seen = set()
    for u in state["units"].values():
        if u["owner"] == seat:
            seen.update(within(u["q"], u["r"], VISION))
    for c in state["cities"].values():
        if c["owner"] == seat:
            seen.update(within(c["q"], c["r"], c["radius"] + (1 if c["spec"] == "outpost" else 0) + 1))
    return {key(q, r) for q, r in seen if key(q, r) in state["tiles"]}


def _reveal(state, seat):
    p = state["players"][str(seat)]
    p["explored"] = sorted(set(p["explored"]) | visible(state, seat))


def moves(state, unit):
    """Tiles the unit can reach this turn. Forest, mountain and enemy contact (ZOC) end the move."""
    if unit["moved"]:
        return set()
    seat = unit["owner"]
    enemy = {(u["q"], u["r"]) for u in state["units"].values() if u["owner"] != seat}
    zoc = {n for e in enemy for n in neighbors(*e)}
    start = (unit["q"], unit["r"])
    left_at, todo = {start: stat(unit, "mv")}, [start]
    while todo:
        cur = todo.pop(0)
        left = left_at[cur]
        if left <= 0:
            continue
        for n in neighbors(*cur):
            if n in enemy or not passable(state, seat, *n):
                continue
            rest = 0 if state["tiles"][key(*n)]["t"] in ("forest", "mountain") or n in zoc else left - 1
            if rest > left_at.get(n, -1):
                left_at[n] = rest
                todo.append(n)
    del left_at[start]
    return {key(*n) for n in left_at if not unit_at(state, *n)}


def targets(state, unit):
    if unit["attacked"]:
        return []
    seen = visible(state, unit["owner"])
    return [u["id"] for u in state["units"].values() if u["owner"] != unit["owner"] and key(u["q"], u["r"]) in seen
            and distance((unit["q"], unit["r"]), (u["q"], u["r"])) <= stat(unit, "rng")]


def defense_bonus(state, unit):
    t = state["tiles"][key(unit["q"], unit["r"])]
    city = city_at(state, unit["q"], unit["r"])
    bonus = 1.0
    if t["t"] in ("forest", "mountain"):
        bonus = 1.5
    if city and city["owner"] == unit["owner"]:
        bonus = max(bonus, 2.5 if city["walls"] else 1.5)
    return bonus


def forecast(state, attacker, defender):
    """(damage to defender, retaliation to attacker) with the Polytopia formula."""
    a_force = stat(attacker, "atk") * attacker["hp"] / max_hp(attacker)
    d_force = stat(defender, "def") * defender["hp"] / max_hp(defender) * defense_bonus(state, defender)
    total = a_force + d_force
    dmg = round(a_force / total * stat(attacker, "atk") * 4.5)
    back = 0
    if dmg < defender["hp"] and distance((attacker["q"], attacker["r"]), (defender["q"], defender["r"])) <= stat(defender, "rng"):
        back = round(d_force / total * stat(defender, "def") * 4.5)
    return dmg, back


def can_promote(unit):
    return unit["kills"] >= PROMOTION_KILLS and not unit.get("branch")


def available_roles(state, seat, cid):
    techs = state["players"][str(seat)]["techs"]
    spec = state["cities"][cid]["spec"]
    return [r for r, s in ROLES.items() if (s["tech"] is None or s["tech"] in techs) and (not s.get("factory") or spec == "factory")]


def improvement_options(state, seat, q, r):
    t = state["tiles"].get(key(q, r))
    if not t or t["imp"] or not t["city"] or state["cities"][t["city"]]["owner"] != seat or city_at(state, q, r):
        return []
    techs = state["players"][str(seat)]["techs"]
    out = []
    for k, (name, cost, pop, tech, terrain, res) in IMPROVEMENTS.items():
        if (tech is None or tech in techs) and (terrain is None or terrain == t["t"]) and (res is None or res == t["res"]):
            out.append(k)
    return out


# ---- actions ---------------------------------------------------------------------

def apply(state, seat, action):
    """Validate and apply one action for `seat`. Returns (new_state, events)."""
    if state["winner"] is not None:
        raise Illegal("Партия завершена")
    if state["current"] != seat:
        raise Illegal("Сейчас ход другого игрока")
    s = copy.deepcopy(state)
    events = []
    kind = action.get("type")
    handler = {"move": _move, "attack": _attack, "capture": _capture, "recover": _recover, "train": _train,
               "build": _build, "research": _research, "promote": _promote, "spec": _spec, "reward": _reward,
               "walls": _walls, "end_turn": _end_turn, "resign": _resign}.get(kind)
    if not handler:
        raise Illegal("Неизвестное действие")
    handler(s, seat, action, events)
    _reveal(s, seat)
    s["log"] = (s["log"] + [{"turn": s["turn"], "seat": seat, **e} for e in events])[-40:]
    return s, events


def _own_unit(s, seat, action):
    u = s["units"].get(action.get("unit"))
    if not u or u["owner"] != seat:
        raise Illegal("Отряд не найден")
    return u


def _own_city(s, seat, action):
    c = s["cities"].get(action.get("city"))
    if not c or c["owner"] != seat:
        raise Illegal("Город не найден")
    return c


def _pay(s, seat, cost):
    p = s["players"][str(seat)]
    if p["stars"] < cost:
        raise Illegal(f"Нужно {cost} ★")
    p["stars"] -= cost


def _move(s, seat, a, ev):
    u = _own_unit(s, seat, a)
    k = key(a["q"], a["r"])
    reach = moves(s, u)
    if k not in reach:
        raise Illegal("Туда не дойти")
    u["q"], u["r"], u["moved"] = a["q"], a["r"], True
    ev.append({"type": "move", "unit": u["id"], "q": a["q"], "r": a["r"]})


def _attack(s, seat, a, ev):
    u = _own_unit(s, seat, a)
    t = s["units"].get(a.get("target"))
    if not t or t["id"] not in targets(s, u):
        raise Illegal("Цель вне досягаемости")
    dmg, back = forecast(s, u, t)
    t["hp"] -= dmg
    ev.append({"type": "attack", "unit": u["id"], "target": t["id"], "damage": dmg})
    escape = ROLES[u["role"]].get("escape") and not u["moved"]
    u["attacked"] = True
    u["moved"] = u["moved"] or not escape   # scouts may still move if they attacked first
    if t["hp"] <= 0:
        u["kills"] += 1
        ev.append({"type": "destroyed", "unit": t["id"], "by": u["id"]})
        tq, tr = t["q"], t["r"]
        del s["units"][t["id"]]
        if stat(u, "rng") == 1:   # melee advances into the cleared tile
            u["q"], u["r"] = tq, tr
    elif back:
        u["hp"] -= back
        ev.append({"type": "retaliate", "unit": t["id"], "target": u["id"], "damage": back})
        if u["hp"] <= 0:
            t["kills"] += 1
            ev.append({"type": "destroyed", "unit": u["id"], "by": t["id"]})
            del s["units"][u["id"]]


def _capture(s, seat, a, ev):
    u = _own_unit(s, seat, a)
    c = city_at(s, u["q"], u["r"])
    if not c or c["owner"] == seat:
        raise Illegal("Здесь нечего захватывать")
    if u["moved"] or u["attacked"]:
        raise Illegal("Захват возможен, только если отряд начал ход в поселении")
    prev = c["owner"]
    c["owner"], c["reward"] = seat, None
    if prev is None:
        c["spec"] = None   # the captor chooses a specialization next
    if c["capital"] and prev is not None:
        c["capital"] = False
    for t in s["tiles"].values():
        if t["city"] == c["id"]:
            t["city"] = None
    _claim(s, c["id"])
    for x in s["units"].values():   # units based in a lost city lose their home
        if x["home"] == c["id"] and x["owner"] != seat:
            x["home"] = None
    u["moved"] = u["attacked"] = True
    ev.append({"type": "capture", "unit": u["id"], "city": c["id"], "from": prev})
    _check_elimination(s, ev)


def _recover(s, seat, a, ev):
    u = _own_unit(s, seat, a)
    if u["moved"] or u["attacked"]:
        raise Illegal("Отряд уже действовал")
    t = s["tiles"][key(u["q"], u["r"])]
    own = t["city"] and s["cities"][t["city"]]["owner"] == seat
    healed = min(max_hp(u), u["hp"] + (8 if own else 4)) - u["hp"]
    u["hp"] += healed
    u["moved"] = u["attacked"] = True
    ev.append({"type": "recover", "unit": u["id"], "amount": healed})


def _train(s, seat, a, ev):
    c = _own_city(s, seat, a)
    role = a.get("role")
    if role not in available_roles(s, seat, c["id"]):
        raise Illegal("Этот отряд пока недоступен")
    if unit_at(s, c["q"], c["r"]):
        raise Illegal("Клетка города занята")
    if sum(1 for u in s["units"].values() if u["home"] == c["id"]) >= unit_cap(s, c["id"]):
        raise Illegal("Город содержит максимум отрядов: развивайте его")
    _pay(s, seat, ROLES[role]["cost"])
    uid = _spawn(s, role, c["q"], c["r"], seat, c["id"])
    ev.append({"type": "train", "unit": uid, "role": role, "city": c["id"]})


def _build(s, seat, a, ev):
    q, r, imp = a["q"], a["r"], a.get("improvement")
    if imp not in improvement_options(s, seat, q, r):
        raise Illegal("Здесь это не построить")
    enemy = unit_at(s, q, r)
    if enemy and enemy["owner"] != seat:
        raise Illegal("Клетку занял противник")
    name, cost, pop, *_ = IMPROVEMENTS[imp]
    _pay(s, seat, cost)
    t = s["tiles"][key(q, r)]
    t["imp"] = imp
    if imp == "gather":
        t["imp"], t["res"] = None, None   # one-off harvest
    ev.append({"type": "build", "improvement": imp, "q": q, "r": r})
    _grow(s, t["city"], pop, ev)


def _grow(s, cid, pop, ev):
    c = s["cities"][cid]
    c["pop"] += pop
    while c["pop"] >= c["level"] + 1:
        c["pop"] -= c["level"] + 1
        c["level"] += 1
        c["reward"] = min(c["level"], 5)
        ev.append({"type": "level", "city": cid, "level": c["level"]})


def _research(s, seat, a, ev):
    tech = a.get("tech")
    p = s["players"][str(seat)]
    if tech not in TECHS or tech in p["techs"]:
        raise Illegal("Технология недоступна")
    need = TECHS[tech][2]
    if need and need not in p["techs"]:
        raise Illegal(f"Сначала изучите «{TECHS[need][0]}»")
    _pay(s, seat, tech_cost(s, seat, tech))
    p["techs"].append(tech)
    ev.append({"type": "research", "tech": tech})


def _promote(s, seat, a, ev):
    u = _own_unit(s, seat, a)
    if not can_promote(u):
        raise Illegal(f"Повышение после {PROMOTION_KILLS} побед")
    if a.get("branch") not in [b[0] for b in BRANCHES[u["role"]]]:
        raise Illegal("Неизвестная ветка")
    u["branch"] = a["branch"]
    u["hp"] = max_hp(u)
    ev.append({"type": "promote", "unit": u["id"], "branch": u["branch"]})


def _spec(s, seat, a, ev):
    c = _own_city(s, seat, a)
    if c["spec"] is not None:
        raise Illegal("Специализация уже выбрана")
    if a.get("spec") not in SPECS:
        raise Illegal("Неизвестная специализация")
    c["spec"] = a["spec"]
    if c["spec"] == "fort":
        c["walls"] = True
    if c["spec"] == "outpost":
        c["radius"] = 2
        _claim(s, c["id"])
    ev.append({"type": "spec", "city": c["id"], "spec": c["spec"]})


def _reward(s, seat, a, ev):
    c = _own_city(s, seat, a)
    if not c["reward"]:
        raise Illegal("Награда уже получена")
    options = [k for k, _ in REWARDS[c["reward"]]]
    pick = a.get("reward")
    if pick not in options:
        raise Illegal("Неизвестная награда")
    c["reward"] = None
    if pick in ("workshop", "park"):
        c["bonus"] += 1
    elif pick == "walls":
        c["walls"] = True
    elif pick == "cache":
        s["players"][str(seat)]["stars"] += 5
    elif pick == "borders":
        c["radius"] = 2
        _claim(s, c["id"])
    elif pick == "growth":
        _grow(s, c["id"], 3, ev)
    elif pick in ("recruit", "guard"):
        spot = next(((q, r) for q, r in [(c["q"], c["r"])] + neighbors(c["q"], c["r"])
                     if passable(s, seat, q, r) and not unit_at(s, q, r)), None)
        if spot:
            _spawn(s, "rifles" if pick == "recruit" else "assault", spot[0], spot[1], seat, c["id"])
    ev.append({"type": "reward", "city": c["id"], "reward": pick})


def _walls(s, seat, a, ev):
    c = _own_city(s, seat, a)
    if "fortify" not in s["players"][str(seat)]["techs"]:
        raise Illegal("Нужна «Фортификация»")
    if c["walls"]:
        raise Illegal("Стены уже есть")
    _pay(s, seat, 5)
    c["walls"] = True
    ev.append({"type": "walls", "city": c["id"]})


def _end_turn(s, seat, a, ev):
    for u in s["units"].values():
        if u["owner"] == seat:
            u["moved"] = u["attacked"] = False
    alive = [x for x in s["order"] if not s["players"][str(x)]["eliminated"]]
    i = alive.index(seat)
    nxt = alive[(i + 1) % len(alive)]
    if (i + 1) >= len(alive):
        s["turn"] += 1
    s["current"] = nxt
    ev.append({"type": "end_turn", "next": nxt})
    _start_turn(s, nxt)


def _resign(s, seat, a, ev):
    for c in s["cities"].values():
        if c["owner"] == seat:
            c["owner"] = None
            c["capital"] = False
    ev.append({"type": "resign"})
    _check_elimination(s, ev)
    if s["winner"] is None and s["current"] == seat:
        alive = [x for x in s["order"] if not s["players"][str(x)]["eliminated"]]
        nxt = alive[0]
        for x in s["order"][s["order"].index(seat) + 1:] + s["order"]:
            if x in alive:
                nxt = x
                break
        s["current"] = nxt
        _start_turn(s, nxt)


def _start_turn(s, seat, pay=True):
    if pay:
        p = s["players"][str(seat)]
        p["stars"] += sum(income(s, cid) for cid, c in s["cities"].items() if c["owner"] == seat)
    for u in s["units"].values():
        if u["owner"] == seat:
            u["moved"] = u["attacked"] = False


def _check_elimination(s, ev):
    for p in s["players"].values():
        if p["eliminated"]:
            continue
        if not any(c["owner"] == p["seat"] for c in s["cities"].values()):
            p["eliminated"] = True
            for uid in [u["id"] for u in s["units"].values() if u["owner"] == p["seat"]]:
                del s["units"][uid]
            ev.append({"type": "eliminated", "seat": p["seat"]})
    alive = [p["seat"] for p in s["players"].values() if not p["eliminated"]]
    if len(alive) == 1:
        s["winner"] = alive[0]
        ev.append({"type": "victory", "seat": alive[0]})


# ---- per-player view -------------------------------------------------------------------

def view(state, seat):
    """What `seat` may see: explored terrain, cities on explored tiles, units in sight."""
    me = state["players"].get(str(seat))
    seen = visible(state, seat) if me else set(state["tiles"])
    explored = set(me["explored"]) if me else set(state["tiles"])
    tiles = [{"q": unkey(k)[0], "r": unkey(k)[1], "t": t["t"], "res": t["res"], "imp": t["imp"],
              "owner": state["cities"][t["city"]]["owner"] if t["city"] else None, "city": t["city"], "fog": k not in seen}
             for k, t in state["tiles"].items() if k in explored]
    cities = [{**c, "income": income(state, c["id"]) if c["owner"] is not None else 0,
               "units": sum(1 for u in state["units"].values() if u["home"] == c["id"]), "cap": unit_cap(state, c["id"])}
              for c in state["cities"].values() if key(c["q"], c["r"]) in explored]
    units = []
    for u in state["units"].values():
        if key(u["q"], u["r"]) not in seen:
            continue
        item = {**u, "max_hp": max_hp(u), "atk": stat(u, "atk"), "def": stat(u, "def"), "mv": stat(u, "mv"), "rng": stat(u, "rng"),
                "promote": can_promote(u)}
        if u["owner"] == seat and state["current"] == seat:
            item["moves"] = sorted(moves(state, u))
            item["targets"] = [{"id": t, "forecast": forecast(state, u, state["units"][t])} for t in targets(state, u)]
            c = city_at(state, u["q"], u["r"])
            item["can_capture"] = bool(c and c["owner"] != seat and not u["moved"] and not u["attacked"])
        units.append(item)
    players = [{"seat": p["seat"], "faction": p["faction"], "eliminated": p["eliminated"],
                "cities": sum(1 for c in state["cities"].values() if c["owner"] == p["seat"]),
                **({"stars": p["stars"], "techs": p["techs"]} if p["seat"] == seat else {})}
               for p in state["players"].values()]
    out = {"size": state["size"], "turn": state["turn"], "current": state["current"], "winner": state["winner"],
           "tiles": tiles, "cities": cities, "units": units, "players": players,
           "log": state["log"][-12:]}
    if me:
        out["income"] = sum(income(state, c["id"]) for c in state["cities"].values() if c["owner"] == seat)
        out["tech_costs"] = {t: tech_cost(state, seat, t) for t in TECHS}
        out["build"] = {k: improvement_options(state, seat, *unkey(k)) for k in state["tiles"]
                        if improvement_options(state, seat, *unkey(k))} if state["current"] == seat else {}
        out["train"] = {c["id"]: available_roles(state, seat, c["id"]) for c in state["cities"].values() if c["owner"] == seat}
    return out
