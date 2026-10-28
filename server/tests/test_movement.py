from sqlalchemy import select
from app import game
from app.models import Army, Tile, TileOwnership
from conftest import login, post
from test_expeditions import commander, create, order, home, player_id
from test_integration import advance


def me(c, h):
    return c.get('/api/v1/player/me', headers=h).json()


def at_time(monkeypatch, t):
    from app import main
    monkeypatch.setattr(game, 'now', lambda: t)
    monkeypatch.setattr(main, 'now', lambda: t)


def biome(c, q, r, kind):
    with c.factory.begin() as db:
        db.get(Tile, (1, q, r)).biome = kind


def test_multi_hex_route_spends_points_fuel_and_walks_step_by_step(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    assert a['movement'] == a['movement_max'] == 12 and a['movement_next_at'] is None
    r = order(c, h, a, Q+3, R, 'move')
    assert r.status_code == 200, r.text
    s = r.json()['state']; army = s['armies'][0]; o = army['orders'][0]
    assert army['movement'] == 9 and s['resources']['fuel'] == 197
    assert [p[:2] for p in o['path']] == [[Q+1, R], [Q+2, R], [Q+3, R]]
    assert [p[2] - o['started_at'] for p in o['path']] == [10, 20, 30]
    assert army['movement_next_at'] == o['started_at'] + 2400
    t0 = o['started_at']
    at_time(monkeypatch, t0 + 15)
    assert (me(c, h)['armies'][0]['q'], me(c, h)['armies'][0]['status']) == (Q+1, 'moving')
    at_time(monkeypatch, t0 + 25)
    assert me(c, h)['armies'][0]['q'] == Q+2
    at_time(monkeypatch, t0 + 31)
    army = me(c, h)['armies'][0]
    assert (army['q'], army['r'], army['status']) == (Q+3, R, 'idle')


def test_terrain_costs_and_not_enough_points(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    biome(c, Q+1, R, 'hills')
    r = order(c, h, a, Q+1, R, 'move')
    assert r.status_code == 200 and r.json()['state']['armies'][0]['movement'] == 9
    assert r.json()['state']['armies'][0]['orders'][0]['ready_at'] - r.json()['state']['armies'][0]['orders'][0]['started_at'] == 30
    at_time(monkeypatch, r.json()['state']['armies'][0]['orders'][0]['ready_at'] + 1); me(c, h)
    with c.factory.begin() as db:
        db.get(Army, a['id']).movement = 1
    fuel = me(c, h)['resources']['fuel']
    r = order(c, h, a, Q+3, R, 'move')
    assert r.status_code == 409 and 'очков хода' in r.json()['detail']
    assert me(c, h)['resources']['fuel'] == fuel


def test_movement_regenerates_in_real_time_up_to_cap(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); a = create(c, h, u)
    with c.factory.begin() as db:
        army = db.get(Army, a['id']); army.movement, army.movement_at = 0, game.now()
    t0 = game.now()
    at_time(monkeypatch, t0 + 3 * 2400 + 5)
    army = me(c, h)['armies'][0]
    assert army['movement'] == 3 and army['movement_next_at'] is not None
    at_time(monkeypatch, t0 + 20 * 2400)
    army = me(c, h)['armies'][0]
    assert army['movement'] == 12 and army['movement_next_at'] is None


def test_route_avoids_garrisons_and_rejects_unknown_land(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    r = order(c, h, a, Q, R+2, 'move')            # tutorial garrison sits on (Q, R+1)
    assert r.status_code == 200, r.text
    path = [p[:2] for p in r.json()['state']['armies'][0]['orders'][0]['path']]
    assert [Q, R+1] not in path and path[-1] == [Q, R+2] and len(path) == 3
    at_time(monkeypatch, r.json()['state']['armies'][0]['orders'][0]['ready_at'] + 1); me(c, h)
    r = order(c, h, a, Q+9, R+2, 'move')
    assert r.status_code == 409 and 'неразведан' in r.json()['detail']


def test_storm_commander_has_more_movement(client, monkeypatch):
    c = client
    h = login(c, 321)
    assert post(c, '/heroes/choose', {'kind': 'storm'}, h).status_code == 200
    from app import expeditions
    with c.factory() as db:
        assert expeditions.movement_max(db, player_id(c, 321)) == 14


def test_blocked_final_hex_stops_army_on_previous_step(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    other = login(c, 456)
    r = order(c, h, a, Q+2, R, 'move'); assert r.status_code == 200
    t0 = r.json()['state']['armies'][0]['orders'][0]['started_at']
    with c.factory.begin() as db:
        db.add(TileOwnership(world_id=1, q=Q+2, r=R, player_id=player_id(c, 456), acquired_at=0))
    at_time(monkeypatch, t0 + 25)
    army = me(c, h)['armies'][0]
    assert (army['q'], army['r'], army['status']) == (Q+1, R, 'idle')
    assert army['orders'][0]['status'] == 'blocked'


def test_route_preview_matches_order_and_changes_nothing(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    biome(c, Q+2, R, 'forest')
    before = me(c, h)
    preview = c.get(f'/api/v1/army/route?q={Q+2}&r={R}', headers=h).json()
    assert preview['cost'] == 3 and preview['fuel'] == 2 and preview['seconds'] == 30 and preview['affordable']
    assert me(c, h)['resources'] == before['resources'] and me(c, h)['armies'][0]['movement'] == 12
    r = order(c, h, a, Q+2, R, 'move')
    assert [p[:2] for p in r.json()['state']['armies'][0]['orders'][0]['path']] == [p[:2] for p in preview['path']]
    blocked = c.get(f'/api/v1/army/route?q={Q+9}&r={R}', headers=h)
    assert blocked.status_code == 409
