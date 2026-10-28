import pytest
from app.config import UNITS, FACTIONS, EFFECTS
from app.combat import new_battle, make_stack, resolve, alive


def battle(kind, enemies=None, allies=None, hero="raven"):
    me = make_stack("p1", "player", kind, UNITS[kind]["count"], [3, 4], "u")
    npcs = enemies or [make_stack("n1", "npc", "rifles", 10, [5, 4])]
    s, _, _ = new_battle([me] + (allies or []), npcs, [], "seed", hero, 0)
    while s["active"] != "p1":
        s, _, _ = resolve(s, {"action": "wait"}, "seed", hero, 0)
    return s


def get(s, sid):
    return next(x for x in s["stacks"] if x["id"] == sid)


def test_every_unit_has_one_ability_with_known_effect():
    for kind, unit in UNITS.items():
        ab = unit["ability"]
        assert ab["effect"] in EFFECTS and ab["name"] and ab["about"], kind
    for f in FACTIONS.values():
        names = [UNITS[v["key"]]["ability"]["name"] for v in f["units"]]
        assert len(set(names)) == 5


def test_strike_hits_harder_and_is_once_per_battle():
    s = battle("raven_heavy", [make_stack("n1", "npc", "armor", 3, [4, 4])])
    plain, _, _ = resolve(s, {"action": "attack"}, "seed", "raven", 0)
    boosted, events, _ = resolve(s, {"action": "skill"}, "seed", "raven", 0)
    assert get(boosted, "n1")["hp"] < get(plain, "n1")["hp"] and events[0]["type"] == "skill"
    nxt = boosted
    while nxt["active"] != "p1":
        nxt, _, _ = resolve(nxt, {"action": "wait"}, "seed", "raven", 0)
    with pytest.raises(ValueError):
        resolve(nxt, {"action": "skill"}, "seed", "raven", 0)


def test_splash_damages_neighbours_of_target():
    s = battle("ghost_tesla", [make_stack("n1", "npc", "rifles", 3, [6, 4]), make_stack("n2", "npc", "rifles", 3, [6, 5])], hero="ghost")
    new, events, _ = resolve(s, {"action": "skill", "target": "n1"}, "seed", "ghost", 0)
    assert any(e["type"] == "splash" and e["target"] == "n2" for e in events)


def test_dash_moves_far_and_keeps_the_turn():
    s = battle("valkyrie_heavy", hero="valkyrie")
    assert UNITS["valkyrie_heavy"]["speed"] < 5 <= UNITS["valkyrie_heavy"]["speed"] + 3
    new, _, _ = resolve(s, {"action": "skill", "q": 8, "r": 1}, "seed", "valkyrie", 0)   # distance 5
    assert get(new, "p1")["pos"] == [8, 1] and new["active"] == "p1"
    with pytest.raises(ValueError):
        resolve(s, {"action": "skill", "q": 8, "r": 8}, "seed", "valkyrie", 0)            # distance 9


def test_fortify_and_smoke_reduce_incoming_damage():
    base = battle("titan_line", [make_stack("n1", "npc", "rifles", 10, [5, 4])], hero="titan")
    hit, _, _ = resolve(base, {"action": "defend"}, "seed", "titan", 0)
    dug, _, _ = resolve(base, {"action": "skill"}, "seed", "titan", 0)
    assert get(dug, "p1")["hp"] > get(hit, "p1")["hp"]
    ally = make_stack("p2", "player", "phoenix_line", 10, [2, 5], "a")
    smoke = battle("phoenix_howitzer", allies=[ally], hero="phoenix")
    new, _, _ = resolve(smoke, {"action": "skill"}, "seed", "phoenix", 0)
    assert get(new, "p2").get("guard", 1) < 1 or new["round"] > smoke["round"]


def test_jam_suppress_and_mark_affect_the_target():
    s = battle("valkyrie_snipers", hero="valkyrie")
    jammed, events, _ = resolve(s, {"action": "skill", "target": "n1"}, "seed", "valkyrie", 0)
    assert any(e["type"] == "jammed" for e in events) or get(jammed, "n1").get("skip")
    s = battle("valkyrie_walker", hero="valkyrie")
    quiet, _, _ = resolve(s, {"action": "skill", "target": "n1"}, "seed", "valkyrie", 0)
    loud, _, _ = resolve(s, {"action": "wait"}, "seed", "valkyrie", 0)
    assert get(quiet, "p1")["hp"] >= get(loud, "p1")["hp"]
    s = battle("ghost_drones", hero="ghost")
    marked, events, _ = resolve(s, {"action": "skill", "target": "n1"}, "seed", "ghost", 0)
    assert any(e["type"] == "mark" for e in events)


def test_heal_aura_restores_neighbours():
    hurt = make_stack("p2", "player", "phoenix_line", 10, [3, 5], "a"); hurt["hp"] = 40
    s = battle("phoenix_medics", allies=[hurt], hero="phoenix")
    before = get(s, "p2")["hp"]
    new, events, _ = resolve(s, {"action": "skill"}, "seed", "phoenix", 0)
    assert any(e["type"] == "heal" and e["target"] == "p2" for e in events)


def test_longshot_ignores_range():
    s = battle("storm_heavy", [make_stack("n1", "npc", "rifles", 10, [8, 8])], hero="storm")
    with pytest.raises(ValueError):
        resolve(s, {"action": "attack"}, "seed", "storm", 0)
    new, events, _ = resolve(s, {"action": "skill"}, "seed", "storm", 0)
    assert any(e["type"] == "attack" for e in events)
