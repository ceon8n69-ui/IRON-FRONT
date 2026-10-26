import copy, hashlib, hmac, json
from urllib.parse import urlencode
import pytest
from fastapi import HTTPException
from app.auth import validate_init_data
from app.combat import resolve, distance


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


def initial():
    return {
        "turn": 1,
        "player": {"pos": [3, 4], "hp": 100},
        "npc": {"pos": [5, 4], "hp": 70},
        "cover": [[3, 4]],
    }


def test_combat_deterministic_immutable():
    state = initial()
    saved = copy.deepcopy(state)
    cmd = {"action": "attack"}
    assert resolve(state, cmd, "seed", "raven", 0) == resolve(
        state, cmd, "seed", "raven", 0
    )
    assert state == saved


def test_equipment_effect_and_cap():
    base = resolve(initial(), {"action": "attack"}, "seed", "raven", 0)[0]["npc"]["hp"]
    bonus = resolve(initial(), {"action": "attack"}, "seed", "raven", 0.1)[0]["npc"][
        "hp"
    ]
    assert bonus < base
    assert resolve(initial(), {"action": "attack"}, "seed", "raven", 100) == resolve(
        initial(), {"action": "attack"}, "seed", "raven", 0.1
    )


def test_invalid_movement():
    with pytest.raises(ValueError):
        resolve(initial(), {"action": "move", "q": 8, "r": 8}, "seed", "raven", 0)


def test_simultaneous_attacks():
    state = initial()
    state["npc"]["hp"] = 1
    new, events, outcome = resolve(state, {"action": "attack"}, "seed", "raven", 0)
    assert outcome == "victory" and new["player"]["hp"] < 100


def test_defend_reduces_damage():
    attack = resolve(initial(), {"action": "attack"}, "seed", "raven", 0)[0]["player"][
        "hp"
    ]
    defend = resolve(initial(), {"action": "defend"}, "seed", "raven", 0)[0]["player"][
        "hp"
    ]
    assert defend > attack


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
