import concurrent.futures, uuid
from sqlalchemy import select, func
from app import game, main
from app.models import Player, Resource, Building, Unit, Item, Ledger, Reward
from conftest import login, post


def advance(c, monkeypatch, seconds):
    value = game.now() + seconds
    monkeypatch.setattr(game, "now", lambda: value)
    monkeypatch.setattr(main, "now", lambda: value)
    return value


def prepare(c, monkeypatch):
    h = login(c)
    assert post(c, "/heroes/choose", {"kind": "raven"}, h).status_code == 200
    for kind, q, r, seconds in [
        ("power", 1, 0, 31),
        ("quarry", 0, 1, 46),
        ("barracks", -1, 1, 61),
    ]:
        result = post(c, "/construction/start", {"kind": kind, "q": q, "r": r}, h)
        assert result.status_code == 200, result.text
        advance(c, monkeypatch, seconds)
        c.get("/api/v1/player/me", headers=h)
    assert post(c, "/army/train", {}, h).status_code == 200
    advance(c, monkeypatch, 46)
    state = c.get("/api/v1/player/me", headers=h).json()
    return h, state


def test_vertical_cycle_persistence_rewards(client, monkeypatch):
    c = client
    h, state = prepare(c, monkeypatch)
    assert len(state["units"]) == 1
    b = post(c, "/battles", {"unit_id": state["units"][0]["id"]}, h).json()["state"][
        "battles"
    ][0]
    assert (
        post(
            c,
            "/battles/commands",
            {"battle_id": b["id"], "turn": 1, "action": "move", "q": 3, "r": 4},
            h,
        ).status_code
        == 200
    )
    key = None
    body = None
    for turn in range(2, 10):
        key = str(uuid.uuid4())
        body = {"battle_id": b["id"], "turn": turn, "action": "attack"}
        result = post(c, "/battles/commands", body, h, key)
        assert result.status_code == 200, result.text
        b = result.json()["state"]["battles"][0]
        if b["status"] != "active":
            break
    assert b["status"] == "victory"
    first = post(c, "/battles/commands", body, h, key)
    assert first.json() == result.json()
    assert post(c, "/battles/commands", body, h).status_code == 409
    item = result.json()["state"]["inventory"][0]
    assert (
        post(
            c, "/equipment/equip", {"item_id": item["id"], "equipped": True}, h
        ).status_code
        == 200
    )
    # New session + new connection pool represents a fresh application instance.
    c.factory.kw["bind"].dispose()
    again = login(c)
    loaded = c.get("/api/v1/player/me", headers=again).json()
    assert loaded["inventory"][0]["equipped"]
    assert loaded["first_victory"] and loaded["hero"]["xp"] == 100
    assert len(loaded["units"]) == 1 and len(loaded["buildings"]) == 4
    with c.factory() as db:
        assert db.scalar(select(func.count()).select_from(Item)) == 1
        assert db.scalar(select(func.count()).select_from(Reward)) == 1


def test_duplicate_build_and_payload_conflict(client):
    h = login(client)
    post(client, "/heroes/choose", {"kind": "titan"}, h)
    body = {"kind": "power", "q": 1, "r": 0}
    key = "same-request-1"
    a = post(client, "/construction/start", body, h, key)
    b = post(client, "/construction/start", body, h, key)
    assert a.status_code == 200 and a.json() == b.json()
    assert (
        post(client, "/construction/start", {**body, "q": 2}, h, key).status_code == 409
    )
    state = client.get("/api/v1/player/me", headers=h).json()
    assert state["resources"]["metal"] == 900 and len(state["buildings"]) == 2


def test_concurrent_requests(client):
    h = login(client)
    post(client, "/heroes/choose", {"kind": "titan"}, h)

    def build(_):
        return post(
            client,
            "/construction/start",
            {"kind": "power", "q": 1, "r": 0},
            h,
            "parallel-key",
        ).status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(build, range(4))) == [200] * 4
    with client.factory() as db:
        assert db.scalar(select(func.count()).select_from(Building)) == 2


def test_foreign_units_items_and_battles(client, monkeypatch):
    h, s = prepare(client, monkeypatch)
    other = login(client, 456)
    post(client, "/heroes/choose", {"kind": "ghost"}, other)
    assert (
        post(client, "/battles", {"unit_id": s["units"][0]["id"]}, other).status_code
        == 409
    )
    battle = post(client, "/battles", {"unit_id": s["units"][0]["id"]}, h).json()[
        "result"
    ]["id"]
    assert (
        post(
            client,
            "/battles/commands",
            {"battle_id": battle, "turn": 1, "action": "attack"},
            other,
        ).status_code
        == 404
    )
    assert (
        client.get("/api/v1/battles/" + battle + "/replay", headers=other).status_code
        == 404
    )
    assert (
        post(
            client,
            "/equipment/equip",
            {"item_id": "nonexistent", "equipped": True},
            other,
        ).status_code
        == 404
    )


def test_production_restart_no_double_credit(client, monkeypatch):
    h, s = prepare(client, monkeypatch)
    before = s["resources"]["metal"]
    advance(client, monkeypatch, 600)
    first = client.get("/api/v1/player/me", headers=h).json()
    client.factory.kw["bind"].dispose()
    second = client.get("/api/v1/player/me", headers=h).json()
    assert first["resources"] == second["resources"]
    assert first["resources"]["metal"] >= before + 120


def test_no_negative_or_overlap(client):
    h = login(client)
    post(client, "/heroes/choose", {"kind": "raven"}, h)
    assert (
        post(
            client, "/construction/start", {"kind": "power", "q": 0, "r": 0}, h
        ).status_code
        == 409
    )
    with client.factory.begin() as db:
        metal = db.scalar(select(Resource).where(Resource.kind == "metal"))
        metal.amount = 1
    assert (
        post(
            client, "/construction/start", {"kind": "power", "q": 1, "r": 0}, h
        ).status_code
        == 409
    )
    assert client.get("/api/v1/player/me", headers=h).json()["resources"]["metal"] == 1


def test_bad_signature_and_no_session(client):
    assert (
        client.post("/api/v1/auth/telegram", json={"init_data": "hash=bad"}).status_code
        == 401
    )
    assert client.get("/api/v1/player/me").status_code == 401


def test_queue_requirements_and_out_of_bounds(client):
    h = login(client)
    post(client, "/heroes/choose", {"kind": "ghost"}, h)
    assert post(client, "/army/train", {}, h).status_code == 409
    assert (
        post(
            client, "/construction/start", {"kind": "quarry", "q": 1, "r": 0}, h
        ).status_code
        == 409
    )
    assert (
        post(
            client, "/construction/start", {"kind": "power", "q": 4, "r": 4}, h
        ).status_code
        == 409
    )
    assert (
        post(
            client, "/construction/start", {"kind": "power", "q": 1, "r": 0}, h
        ).status_code
        == 200
    )
    assert (
        post(
            client, "/construction/start", {"kind": "quarry", "q": 0, "r": 1}, h
        ).status_code
        == 409
    )


def test_storage_cap_and_offline_settlement(client, monkeypatch):
    h, state = prepare(client, monkeypatch)
    with client.factory.begin() as db:
        resource = db.scalar(select(Resource).where(Resource.kind == "metal"))
        resource.amount = 4995
    advance(client, monkeypatch, 60 * 60 * 48)
    # Session lasts 24h; refresh login through real signed test auth.
    from conftest import signed
    from app.auth import token_hash
    from app.models import Session

    with client.factory.begin() as db:
        session = db.get(Session, token_hash(h["Authorization"][7:]))
        session.expires_at = game.now() + 3600
    first = client.get("/api/v1/player/me", headers=h).json()
    second = client.get("/api/v1/player/me", headers=h).json()
    assert first["resources"]["metal"] <= 5000
    assert first["resources"] == second["resources"]


def test_expired_session(client):
    from app.models import Session
    from app.auth import token_hash

    h = login(client)
    with client.factory.begin() as db:
        db.get(Session, token_hash(h["Authorization"][7:])).expires_at = 1
    assert client.get("/api/v1/player/me", headers=h).status_code == 401
