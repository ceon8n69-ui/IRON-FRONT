from types import SimpleNamespace
from sqlalchemy import select
from app import logistics, nodes, seasons, garrisons, objects, game
from app.models import TileOwnership, Resource, Unit, Building, Player
from conftest import post
from test_expeditions import commander, create, order, home, player_id
from test_movement import at_time


def me(c, h):
    return c.get('/api/v1/player/me', headers=h).json()


def own(c, cells, uid=123):
    with c.factory.begin() as db:
        for q, r in cells:
            db.add(TileOwnership(world_id=1, q=q, r=r, player_id=player_id(c, uid), acquired_at=game.now()))


def test_supply_chain_and_cut_off_land_yields_nothing(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); Q, R = home(c, h)
    own(c, [(Q+1, R), (Q+2, R), (Q+3, R), (Q+6, R)])
    s = me(c, h)
    supplied = {(t['q'], t['r']): t['supplied'] for t in s['territories']}
    assert supplied == {(Q+1, R): True, (Q+2, R): True, (Q+3, R): True, (Q+6, R): False}
    tiles = c.get(f'/api/v1/world/tiles?q={Q}&r={R}&radius=4', headers=h).json()['tiles']
    assert next(t for t in tiles if (t['q'], t['r']) == (Q+2, R))['supplied'] is True
    with c.factory.begin() as db:                        # cut the chain in the middle
        db.delete(db.get(TileOwnership, (1, Q+2, R)))
    s = me(c, h)
    assert {(t['q'], t['r']): t['supplied'] for t in s['territories']}[(Q+3, R)] is False
    with c.factory() as db:
        assert logistics.supplied(db, player_id(c, 123)) == {(Q+1, R)}


def test_upkeep_is_charged_hourly_and_hunger_makes_units_desert(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch)
    s = me(c, h)
    unit = next(x for x in s['units'] if x['id'] == u)
    assert s['upkeep']['food'] == 2 * unit['count'] and s['upkeep']['fuel'] == 0
    food = s['resources']['food']
    at_time(monkeypatch, game.now() + 3600 + 5)
    s = me(c, h)
    assert s['resources']['food'] <= food - 2 * unit['count'] + 200      # farm-less base: upkeep dominates
    with c.factory.begin() as db:
        db.scalar(select(Resource).where(Resource.player_id == player_id(c, 123), Resource.kind == 'food')).amount = 0
    count = next(x for x in me(c, h)['units'] if x['id'] == u)['count']
    at_time(monkeypatch, game.now() + 2 * 3600 + 5)
    after = next(x for x in me(c, h)['units'] if x['id'] == u)['count']
    assert after == count - 2                                           # one deserter per hungry hour


def test_nodes_are_rare_guarded_and_strong():
    sites = {(10, 10): 'p'}
    found = [(q, r) for q in range(20, 120) for r in range(20, 120) if nodes.at(q, r, 'plain', sites)]
    assert 0.008 < len(found) / 10000 < 0.02
    q, r = found[0]
    assert garrisons.guarded(q, r, sites, 'plain')
    assert objects.placed(q, r, sites, 'plain') is None
    name, hp, xp = objects.strength(q, r, 'plain', sites)
    assert name == nodes.TIER['name'] and xp == nodes.TIER['xp'] and hp > objects.TIERS[2][1]
    assert nodes.at(q, r, 'sea', sites) is None
    assert all(not nodes.at(10 + dq, 10 + dr, 'plain', sites) for dq in range(-3, 4) for dr in range(-3, 4))


def test_owned_supplied_node_adds_its_yield(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); Q, R = home(c, h)
    monkeypatch.setattr(nodes, 'at', lambda q, r, biome, sites: 'plant' if (q, r) == (Q+2, R) else None)
    own(c, [(Q+2, R)])
    s = me(c, h)
    node = next(t for t in s['territories'] if (t['q'], t['r']) == (Q+2, R))
    assert node['node'] == 'plant' and node['yield']['electronics'] == 3 and not node['supplied']
    assert s['nodes'] == [{'q': Q+2, 'r': R, 'kind': 'plant', 'name': 'Завод электроники', 'supplied': False}]
    own(c, [(Q+1, R)])
    s = me(c, h)
    assert s['nodes'][0]['supplied'] is True
    e0 = s['resources']['electronics']
    at_time(monkeypatch, game.now() + 10 * 60 + 2)
    assert me(c, h)['resources']['electronics'] >= e0 + 24          # ~3 per minute


def test_calendar_days_weeks_and_events():
    season = SimpleNamespace(number=1, seed='s', started_at=1000, ends_at=1000 + seasons.SEASON_SECONDS)
    cal = seasons.calendar(season, 1000 + seasons.DAY * 7 + 5)
    assert (cal['week'], cal['day'], cal['day_index']) == (2, 2, 7)
    assert cal['next_day_at'] == 1000 + seasons.DAY * 8
    weeks = {seasons.event(season, w)['key'] for w in range(1, 15)}
    assert len(weeks) >= 4 and seasons.event(season, 3) == seasons.event(season, 3)


def test_mud_week_makes_rough_ground_dearer(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    from test_movement import biome
    biome(c, Q+1, R, 'forest')
    plain = c.get(f'/api/v1/army/route?q={Q+1}&r={R}', headers=h).json()['cost']
    monkeypatch.setattr(seasons, 'effect', lambda db, key, at, default=1: 1 if key == 'rough_cost' else default)
    assert c.get(f'/api/v1/army/route?q={Q+1}&r={R}', headers=h).json()['cost'] == plain + 1


def test_control_limit_grows_with_hq_and_isolated_capture_is_allowed(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    assert me(c, h)['control_limit'] == 12
    with c.factory.begin() as db:
        db.scalar(select(Building).where(Building.player_id == player_id(c, 123), Building.kind == 'hq')).level = 4
    assert me(c, h)['control_limit'] == 18
    res = order(c, h, a, Q+3, R, 'capture')
    assert res.status_code == 200, res.text
    at_time(monkeypatch, res.json()['state']['armies'][0]['orders'][0]['ready_at'] + 1)
    terr = next(t for t in me(c, h)['territories'] if (t['q'], t['r']) == (Q+3, R))
    assert terr['supplied'] is False
