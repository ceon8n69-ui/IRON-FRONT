from sqlalchemy import select
from app import economy, game
from app.models import Building, Resource, Unit, Player
from conftest import login, post
from test_integration import advance


def me(c, h):
    return c.get('/api/v1/player/me', headers=h).json()


def rich(c, amount=4000):
    with c.factory.begin() as db:
        for r in db.scalars(select(Resource)):
            r.amount = amount


def building(state, kind):
    return next(b for b in state['buildings'] if b['kind'] == kind)


def start(c, monkeypatch, uid=123):
    h = login(c, uid)
    assert post(c, '/heroes/choose', {'kind': 'titan'}, h).status_code == 200
    assert post(c, '/construction/start', {'kind': 'power', 'q': 1, 'r': 0}, h).status_code == 200
    advance(c, monkeypatch, 31)
    return h


def upgrade(c, h, b, key=None):
    return post(c, '/construction/upgrade', {'building_id': b['id']}, h, key)


def test_economy_curves_are_bounded_and_monotonic():
    assert economy.output('quarry', 1) == {'metal': 12}
    assert economy.power('power', 1) == 20 and economy.power('quarry', 1) == -4
    for kind in ('quarry', 'power', 'hq'):
        costs = [economy.upgrade_cost(kind, n)['metal'] for n in range(1, 10)]
        times = [economy.upgrade_seconds(kind, n) for n in range(1, 10)]
        assert costs == sorted(costs) and times == sorted(times)
        assert max(times) <= 4 * 3600
    assert economy.output('quarry', 10)['metal'] < 12 * 4
    assert economy.max_level('quarry', 3) == 3 and economy.max_level('hq', 1) == 10


def test_headquarters_level_caps_other_buildings(client, monkeypatch):
    c = client; h = start(c, monkeypatch); rich(c)
    s = me(c, h); power = building(s, 'power')
    assert power['max_level'] == 1 and power['upgrade'] is None
    r = upgrade(c, h, power)
    assert r.status_code == 409 and 'штаб' in r.json()['detail']
    hq = building(s, 'hq')
    r = upgrade(c, h, hq, 'hq-upgrade-1')
    assert r.status_code == 200, r.text
    assert upgrade(c, h, hq, 'hq-upgrade-1').json() == r.json()       # idempotent replay
    cost = economy.upgrade_cost('hq', 1)
    assert r.json()['state']['resources']['metal'] == 4000 - cost['metal']
    assert building(r.json()['state'], 'hq')['level'] == 1
    # Queue is shared between construction and upgrades.
    busy = post(c, '/construction/start', {'kind': 'quarry', 'q': 0, 'r': 1}, h)
    assert busy.status_code == 409 and 'очередь' in busy.json()['detail'].lower()
    advance(c, monkeypatch, economy.upgrade_seconds('hq', 1) + 1)
    s = me(c, h)
    assert building(s, 'hq')['level'] == 2 and building(s, 'hq')['upgrade_ready_at'] is None
    assert building(s, 'power')['max_level'] == 2
    assert upgrade(c, h, building(s, 'power')).status_code == 200


def test_new_buildings_require_headquarters_level(client, monkeypatch):
    c = client; h = start(c, monkeypatch); rich(c)
    r = post(c, '/construction/start', {'kind': 'warehouse', 'q': 0, 'r': 1}, h)
    assert r.status_code == 409 and '2 уровня' in r.json()['detail']
    assert post(c, '/construction/start', {'kind': 'farm', 'q': 0, 'r': 1}, h).status_code == 200
    advance(c, monkeypatch, 41)
    assert post(c, '/construction/start', {'kind': 'oil_well', 'q': -1, 'r': 1}, h).status_code == 200


def test_warehouse_raises_storage_cap(client, monkeypatch):
    c = client; h = start(c, monkeypatch)
    assert me(c, h)['storage_cap'] == 5000
    with c.factory.begin() as db:
        pid = db.scalar(select(Player.id))
        db.scalar(select(Building).where(Building.kind == 'hq')).level = 2
        db.add(Building(id='w1', player_id=pid, kind='warehouse', q=2, r=0, level=2, ready_at=0, status='ready'))
    assert me(c, h)['storage_cap'] == 10000


def test_upgrade_keeps_producing_old_level_until_complete(client, monkeypatch):
    c = client; h = start(c, monkeypatch)
    with c.factory.begin() as db:
        pid = db.scalar(select(Player.id))
        db.scalar(select(Building).where(Building.kind == 'hq')).level = 3
        db.add(Building(id='q1', player_id=pid, kind='quarry', q=0, r=1, level=1, ready_at=0, status='ready'))
    me(c, h)
    rich(c, 1000)
    with c.factory.begin() as db:
        db.get(Player, pid).settled_at = game.now()
    r = upgrade(c, h, {'id': 'q1'})
    assert r.status_code == 200, r.text
    after_cost = r.json()['state']['resources']['metal']
    seconds = economy.upgrade_seconds('quarry', 1)
    # One minute before completion every minute yields level-1 output (12).
    advance(c, monkeypatch, seconds - 60)
    s = me(c, h)
    minutes = (seconds - 60) // 60
    assert s['resources']['metal'] == after_cost + 12 * minutes
    assert building(s, 'quarry')['level'] == 1
    advance(c, monkeypatch, seconds + 200)
    s = me(c, h)
    assert building(s, 'quarry')['level'] == 2
    assert building(s, 'quarry')['effects']['current']['output'] == {'metal': 15}


def test_upgrade_rules_and_foreign_building(client, monkeypatch):
    c = client; h = start(c, monkeypatch); rich(c)
    other = login(c, 456)
    assert post(c, '/heroes/choose', {'kind': 'raven'}, other).status_code == 200
    s = me(c, h); hq = building(s, 'hq')
    assert upgrade(c, other, hq).status_code == 404
    assert post(c, '/construction/start', {'kind': 'quarry', 'q': 0, 'r': 1}, h).status_code == 200
    building_quarry = building(me(c, h), 'quarry')
    r = upgrade(c, h, building_quarry)
    assert r.status_code == 409 and 'строительства' in r.json()['detail']
    with c.factory.begin() as db:
        for res in db.scalars(select(Resource)):
            res.amount = 0
    advance(c, monkeypatch, 46)
    r = upgrade(c, h, hq)
    assert r.status_code == 409 and 'ресурс' in r.json()['detail'].lower()


def test_repair_center_heals_units_outside_battle(client, monkeypatch):
    c = client; h = start(c, monkeypatch)
    with c.factory.begin() as db:
        pid = db.scalar(select(Player.id))
        db.add(Building(id='r1', player_id=pid, kind='repair', q=2, r=0, level=2, ready_at=0, status='ready'))
        db.add(Unit(id='u1', player_id=pid, kind='rifles', hp=60, status='reserve'))
        db.add(Unit(id='u2', player_id=pid, kind='rifles', hp=60, status='battle'))
        db.get(Player, pid).settled_at = game.now()
    advance(c, monkeypatch, 3 * 60 + 5)
    units = {u['id']: u for u in me(c, h)['units']}
    assert units['u1']['hp'] == 60 + 3 * 4 and units['u2']['hp'] == 60


def test_watchtower_extends_world_vision(client, monkeypatch):
    c = client; h = start(c, monkeypatch)
    q, r = me(c, h)['base'].values()
    def far_visible():
        tiles = c.get(f'/api/v1/world/tiles?q={q+4}&r={r}&radius=1', headers=h).json()['tiles']
        return next(t for t in tiles if (t['q'], t['r']) == (q+4, r))['visibility'] == 'visible'
    assert not far_visible()
    with c.factory.begin() as db:
        pid = db.scalar(select(Player.id))
        db.add(Building(id='t1', player_id=pid, kind='watchtower', q=2, r=0, level=1, ready_at=0, status='ready'))
    assert far_visible()
