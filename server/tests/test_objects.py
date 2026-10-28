import concurrent.futures
from sqlalchemy import select, func
from app import objects, bases, garrisons, game
from app.models import MapPickup, MapMine, Army, TileOwnership
from conftest import login, post
from test_expeditions import commander, create, order, home, player_id
from test_movement import at_time


def me(c, h):
    return c.get('/api/v1/player/me', headers=h).json()


def place(monkeypatch, layout):
    real = objects.placed
    monkeypatch.setattr(objects, 'placed', lambda q, r, sites: layout.get((q, r)))
    return real


def go(c, h, a, monkeypatch, q, r):
    res = order(c, h, a, q, r, 'move')
    assert res.status_code == 200, res.text
    at_time(monkeypatch, res.json()['state']['armies'][0]['orders'][0]['ready_at'] + 1)
    return me(c, h)


def test_real_placement_rules():
    sites = {(30, 30): 'p'}
    found = [objects.placed(q, r, sites) for q in range(10, 120) for r in range(10, 120)]
    share = sum(1 for o in found if o) / len(found)
    assert 0.05 < share < 0.15
    assert all(objects.placed(30+dq, 30+dr, sites) is None for dq, dr in
               [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)])
    assert all(not (objects.placed(q, r, sites) and garrisons.guarded(q, r, sites))
               for q in range(20, 60) for r in range(20, 60))
    assert objects.strength(56, 77) == objects.TIERS[0]   # tutorial garrison south of a base


def test_resource_pile_is_taken_once(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    place(monkeypatch, {(Q+2, R): {'kind': 'pile', 'resource': 'metal', 'amount': 200}})
    tiles = c.get(f'/api/v1/world/tiles?q={Q}&r={R}&radius=3', headers=h).json()['tiles']
    assert next(t for t in tiles if (t['q'], t['r']) == (Q+2, R))['object']['kind'] == 'pile'
    metal = me(c, h)['resources']['metal']
    s = go(c, h, a, monkeypatch, Q+2, R)
    assert s['resources']['metal'] == metal + 200 and 'Найдено' in s['armies'][0]['orders'][0]['result']
    tiles = c.get(f'/api/v1/world/tiles?q={Q}&r={R}&radius=3', headers=h).json()['tiles']
    assert next(t for t in tiles if (t['q'], t['r']) == (Q+2, R))['object'] is None
    s = go(c, h, a, monkeypatch, Q+1, R); s = go(c, h, a, monkeypatch, Q+2, R)
    assert 'другой отряд' in s['armies'][0]['orders'][0]['result']
    assert s['resources']['metal'] == metal + 200
    with c.factory() as db:
        assert db.scalar(select(func.count()).select_from(MapPickup)) == 1


def test_untaken_object_blocks_route_until_taken(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    place(monkeypatch, {(Q+1, R): {'kind': 'pile', 'resource': 'food', 'amount': 100}})
    preview = c.get(f'/api/v1/army/route?q={Q+2}&r={R}', headers=h).json()
    assert [Q+1, R] not in [p[:2] for p in preview['path']] and preview['cost'] == 3
    s = go(c, h, a, monkeypatch, Q+1, R); go(c, h, a, monkeypatch, Q, R)
    preview = c.get(f'/api/v1/army/route?q={Q+2}&r={R}', headers=h).json()
    assert [p[:2] for p in preview['path']] == [[Q+1, R], [Q+2, R]]


def test_chest_offers_one_choice(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    place(monkeypatch, {(Q+2, R): {'kind': 'chest'}})
    s = go(c, h, a, monkeypatch, Q+2, R)
    assert s['pending_chests'] == [{'q': Q+2, 'r': R, 'options': objects.CHEST}]
    other = login(c, 456); post(c, '/heroes/choose', {'kind': 'ghost'}, other)
    assert post(c, '/world/chest', {'q': Q+2, 'r': R, 'choice': 'xp'}, other).status_code == 404
    xp = s['hero']['xp']
    r = post(c, '/world/chest', {'q': Q+2, 'r': R, 'choice': 'xp'}, h, 'chest-key')
    assert r.status_code == 200 and r.json()['state']['hero']['xp'] == xp + objects.CHEST['xp']
    assert post(c, '/world/chest', {'q': Q+2, 'r': R, 'choice': 'xp'}, h, 'chest-key').json() == r.json()
    again = post(c, '/world/chest', {'q': Q+2, 'r': R, 'choice': 'resources'}, h)
    assert again.status_code == 409 and r.json()['state']['pending_chests'] == []


def test_mine_is_flagged_and_pays_every_minute(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    place(monkeypatch, {(Q+2, R): {'kind': 'mine', 'resource': 'oil', 'rate': 4}})
    s = go(c, h, a, monkeypatch, Q+2, R)
    assert s['mines'] == [{'q': Q+2, 'r': R, 'resource': 'oil', 'rate': 4}]
    t0 = game.now(); oil = s['resources']['oil']
    at_time(monkeypatch, t0 + 5 * 60 + 2)
    assert me(c, h)['resources']['oil'] >= oil + 4 * 4
    # A second commander cannot take it before PvP.
    h2, u2 = commander(c, monkeypatch, 456); a2 = create(c, h2, u2)
    with c.factory.begin() as db:
        army = db.get(Army, a2['id']); army.q, army.r = Q+3, R
    res = order(c, h2, a2, Q+2, R, 'move'); assert res.status_code == 200
    at_time(monkeypatch, res.json()['state']['armies'][0]['orders'][0]['ready_at'] + 1)
    assert 'другому командиру' in me(c, h2)['armies'][0]['orders'][0]['result']
    with c.factory() as db:
        assert db.get(MapMine, (1, Q+2, R)).player_id == player_id(c, 123)


def test_two_armies_race_for_one_pile(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); h2, u2 = commander(c, monkeypatch, 456)
    a = create(c, h, u); a2 = create(c, h2, u2); Q, R = home(c, h)
    place(monkeypatch, {(Q+2, R): {'kind': 'pile', 'resource': 'metal', 'amount': 200}})
    with c.factory.begin() as db:
        db.add(TileOwnership(world_id=1, q=Q+3, r=R, player_id=player_id(c, 456), acquired_at=0))
        army = db.get(Army, a2['id']); army.q, army.r = Q+3, R
    r1 = order(c, h, a, Q+2, R, 'move'); r2 = order(c, h2, a2, Q+2, R, 'move')
    assert r1.status_code == r2.status_code == 200
    at_time(monkeypatch, max(r1.json()['state']['armies'][0]['orders'][0]['ready_at'],
                             r2.json()['state']['armies'][0]['orders'][0]['ready_at']) + 1)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda auth: me(c, auth), [h, h2]))
    with c.factory() as db:
        assert db.scalar(select(func.count()).select_from(MapPickup)) == 1


def test_neutral_strength_is_visible_and_used_in_battle(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    tiles = c.get(f'/api/v1/world/tiles?q={Q}&r={R}&radius=2', headers=h).json()['tiles']
    tutorial = next(t for t in tiles if (t['q'], t['r']) == (Q, R+1))
    assert tutorial['garrison_strength'] == {'name': 'Патруль', 'hp': 60, 'xp': 50}
    res = order(c, h, a, Q, R+1, 'capture'); assert res.status_code == 200
    at_time(monkeypatch, res.json()['state']['armies'][0]['orders'][0]['ready_at'] + 1)
    battle = next(b for b in me(c, h)['battles'] if b['status'] == 'active')
    npc = [x for x in battle['state']['stacks'] if x['side'] == 'npc']
    assert [(x['kind'], x['count'], x['hp']) for x in npc] == [('rifles', 6, 60)]
    assert battle['state']['npc_tier']['name'] == 'Патруль'
