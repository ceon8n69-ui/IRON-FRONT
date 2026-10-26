import os

# Integration tests must explicitly target a disposable database.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("BOT_TOKEN", "123456:test-only-not-a-real-token")
import hashlib, hmac, json, time, uuid
from urllib.parse import urlencode
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.models import Base
from app import main, game


def signed(uid=123):
    data = {
        "user": json.dumps({"id": uid, "first_name": "Tester"}),
        "auth_date": str(int(time.time())),
    }
    secret = hmac.new(
        b"WebAppData", os.environ["BOT_TOKEN"].encode(), hashlib.sha256
    ).digest()
    data["hash"] = hmac.new(
        secret,
        "\n".join(f"{k}={v}" for k, v in sorted(data.items())).encode(),
        hashlib.sha256,
    ).hexdigest()
    return urlencode(data)


@pytest.fixture
def client(monkeypatch):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL must point to disposable PostgreSQL")
    engine = create_engine(
        url, pool_pre_ping=True, connect_args={"prepare_threshold": None}
    )
    schema = "test_" + uuid.uuid4().hex
    with engine.begin() as c:
        c.exec_driver_sql(f"CREATE SCHEMA {schema}")
    scoped = create_engine(
        url, connect_args={"prepare_threshold": None}
    ).execution_options(schema_translate_map={None: schema})
    Base.metadata.create_all(scoped)
    factory = sessionmaker(scoped, expire_on_commit=False)
    monkeypatch.setattr(main, "SessionLocal", factory)
    monkeypatch.setattr(main, "rate_limit", lambda *args, **kw: None)
    with TestClient(main.app) as c:
        c.factory = factory
        yield c
    scoped.dispose()
    with engine.begin() as c:
        c.exec_driver_sql(f"DROP SCHEMA {schema} CASCADE")
    engine.dispose()


def login(client, uid=123):
    r = client.post("/api/v1/auth/telegram", json={"init_data": signed(uid)})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["token"]}


def post(c, path, data, headers, key=None):
    return c.post(
        "/api/v1" + path,
        json=data,
        headers={**headers, "Idempotency-Key": key or str(uuid.uuid4())},
    )
