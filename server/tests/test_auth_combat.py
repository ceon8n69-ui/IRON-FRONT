import copy, hashlib, hmac, json
from urllib.parse import urlencode
import pytest
from fastapi import HTTPException
from app.auth import validate_init_data
from app.combat import resolve, distance, new_battle, make_stack, from_legacy


def valid(now=1000):
    data = {"auth_date": str(now), "user": json.dumps({"id": 12})}
    secret = hmac.new(b"WebAppData", b"test", hashlib.sha256).digest()
    data["hash"] = hmac.new(
        secret,
        "\n".join(f"{k}={v}" for k, v in sorted(data.items())).encode(),
        hashlib.sha256,
    ).hexdigest()
    return urlencode(data)


def test_auth_valid():
    assert validate_init_data(valid(), "test", 1000)["id"] == 12


@pytest.mark.parametrize(
    "raw,token,now",
    [
        (valid() + "&user=bad", "test", 1000),
        (valid(), "wrong", 1000),
        (valid(), "test", 1301),
        (valid(), "test", 900),
        ("hash=bad", "test", 1000),
    ],
)
def test_auth_rejects(raw, token, now):
    with pytest.raises(HTTPException) as exc:
        validate_init_data(raw, token, now)
    assert exc.value.status_code == 401


def initial(hero="raven", bonus=0, npc=None):
    state, _, _ = new_battle([make_stack("p1", "player", "rifles", 10, [3, 4], "u1")],
                             npc or [make_stack("n1", "npc", "rifles", 7, [5, 4])], [[3, 4]], "seed", hero, bonus)
    return state


def npc(state):
    return next(x for x in state["stacks"] if x["side"] == "npc")


def me(state):
    return next(x for x in state["stacks"] if x["side"] == "player")


def test_combat_deterministic_immutable():
    state = initial()
    saved = copy.deepcopy(state)
    cmd = {"action": "attack"}
    assert resolve(state, cmd, "seed", "raven", 0) == resolve(state, cmd, "seed", "raven", 0)
    assert state == saved


def test_equipment_effect_and_cap():
    base = npc(resolve(initial(), {"action": "attack"}, "seed", "raven", 0)[0])["hp"]
    bonus = npc(resolve(initial(), {"action": "attack"}, "seed", "raven", 0.1)[0])["hp"]
    assert bonus < base
    assert resolve(initial(), {"action": "attack"}, "seed", "raven", 100) == resolve(
        initial(), {"action": "attack"}, "seed", "raven", 0.1)


def test_invalid_movement():
    with pytest.raises(ValueError):
        resolve(initial(), {"action": "move", "q": 8, "r": 8}, "seed", "raven", 0)
    with pytest.raises(ValueError):   # occupied by the enemy stack
        resolve(initial(), {"action": "move", "q": 5, "r": 4}, "seed", "raven", 0)


def test_kills_and_victory_when_enemy_pool_is_empty():
    state = initial(); npc(state)["hp"] = 1
    new, events, outcome = resolve(state, {"action": "attack"}, "seed", "raven", 0)
    assert outcome == "victory" and any(e["type"] == "destroyed" for e in events)


def test_defend_reduces_damage():
    attack = me(resolve(initial(), {"action": "attack"}, "seed", "raven", 0)[0])["hp"]
    defend = me(resolve(initial(), {"action": "defend"}, "seed", "raven", 0)[0])["hp"]
    assert defend > attack


def test_initiative_order_and_npc_acts_between_player_turns():
    state = initial(npc=[make_stack("n1", "npc", "scouts", 6, [6, 4])])
    assert state["order"] == ["n1", "p1"] and state["active"] == "p1"
    assert state["round"] == 1 and npc(state)["acted"]


def test_melee_approaches_and_target_retaliates_once():
    state, _, _ = new_battle([make_stack("p1", "player", "assault", 8, [2, 4], "u1")],
                             [make_stack("n1", "npc", "assault", 4, [5, 4])], [], "seed", "titan", 0)
    new, events, _ = resolve(state, {"action": "attack"}, "seed", "titan", 0)
    kinds = [e["type"] for e in events]
    assert "move" in kinds and kinds.count("retaliate") >= 1
    assert distance(me(new)["pos"], npc(new)["pos"]) == 1


def test_ranged_out_of_range_and_hero_abilities():
    far = initial(npc=[make_stack("n1", "npc", "artillery", 2, [8, 0])])
    with pytest.raises(ValueError):
        resolve(far, {"action": "attack"}, "seed", "valkyrie", 0)
    shot, events, _ = resolve(far, {"action": "ability"}, "seed", "valkyrie", 0)
    assert any(e["type"] == "attack" for e in events) and shot["ability_used"]
    with pytest.raises(ValueError):
        resolve(shot, {"action": "ability"}, "seed", "valkyrie", 0)
    storm = initial("storm")
    again, _, _ = resolve(storm, {"action": "ability"}, "seed", "storm", 0)
    assert again["active"] == "p1" and not me(again)["acted"]
    healed = initial("phoenix"); me(healed)["hp"] = 30
    assert me(resolve(healed, {"action": "ability"}, "seed", "phoenix", 0)[0])["hp"] > 30


def test_legacy_single_squad_state_converts():
    legacy = {"turn": 3, "player": {"pos": [3, 4], "hp": 80}, "npc": {"pos": [6, 4], "hp": 35}, "cover": []}
    s = from_legacy(legacy, "u1")
    assert me(s)["hp"] == 80 and npc(s)["count"] == 4 and s["active"] == "p1" and s["turn"] == 3
    resolve(s, {"action": "attack"}, "seed", "raven", 0)


def test_rate_limit_fails_closed_in_production(monkeypatch):
    import redis
    from app import main, config

    monkeypatch.setattr(config, "ENV", "production")

    def unavailable(*args):
        raise redis.ConnectionError("test unavailable")

    monkeypatch.setattr(main.cache, "eval", unavailable)
    with pytest.raises(HTTPException) as exc:
        main.rate_limit("test")
    assert exc.value.status_code == 503


def test_rate_limit_threshold(monkeypatch):
    from app import main

    monkeypatch.setattr(main.cache, "eval", lambda *args: 121)
    with pytest.raises(HTTPException) as exc:
        main.rate_limit("test")
    assert exc.value.status_code == 429
