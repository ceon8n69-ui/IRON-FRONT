from sqlalchemy import select
from app import garrisons, bases
from app.models import Building, Unit, Army, ArmyUnit, Tile, ClearedSite, Player
from conftest import post
from test_expeditions import commander, create, order, home, player_id
from test_movement import at_time
from test_stacks import finish


def me(c, h):
    return c.get('/api/v1/player/me', headers=h).json()


def shipyard(c, level=1):
    with c.factory.begin() as db:
        pid = db.scalar(select(Player.id).where(Player.telegram_id == 123))
        db.scalar(select(Building).where(Building.kind == 'hq')).level = 3
        db.add(Building(id='yard', player_id=pid, kind='shipyard', q=2, r=0, level=level, ready_at=0, status='ready'))


def give_ship(c, army_id, kind, count=2, uid='ship1'):
    with c.factory.begin() as db:
        pid = db.scalar(select(Player.id).where(Player.telegram_id == 123))
        db.add(Unit(id=uid, player_id=pid, kind=kind, count=count, hp=100, status='army'))
        db.flush()
        db.add(ArmyUnit(army_id=army_id, unit_id=uid))


def flood(c, cells, biome='sea'):
    with c.factory.begin() as db:
        for q, r in cells:
            db.get(Tile, (1, q, r)).biome = biome


def test_shipyard_gates_ships(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch)
    r = post(c, '/army/train', {'kind': 'transport'}, h)
    assert r.status_code == 409 and 'Верфь' in r.json()['detail']
    r = post(c, '/construction/start', {'kind': 'shipyard', 'q': 2, 'r': 0}, h)
    assert r.status_code == 409 and '2 уровня' in r.json()['detail']
    shipyard(c, 1)
    assert post(c, '/army/train', {'kind': 'gunboat'}, h).status_code == 409   # needs yard level 2
    r = post(c, '/army/train', {'kind': 'transport'}, h)
    assert r.status_code == 200, r.text
    at_time(monkeypatch, r.json()['state']['jobs'][0]['ready_at'] + 1)
    assert any(x['kind'] == 'transport' and x['count'] == 2 for x in me(c, h)['units'])


def test_fleet_crosses_water_and_pays_to_land(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    flood(c, [(Q + 2, R + d) for d in range(-4, 5)])            # a strait east of the base
    blocked = c.get(f'/api/v1/army/route?q={Q+3}&r={R}', headers=h)
    assert blocked.status_code == 409 and 'флот' in blocked.json()['detail']
    give_ship(c, a['id'], 'transport')
    preview = c.get(f'/api/v1/army/route?q={Q+3}&r={R}', headers=h).json()
    assert [p[:2] for p in preview['path']] == [[Q+1, R], [Q+2, R], [Q+3, R]]
    assert [p[2] for p in preview['path']] == [1, 3, 3]          # embark +2, go ashore +2
    r = order(c, h, a, Q+2, R, 'capture')
    assert r.status_code == 409 and 'Водные' in r.json()['detail']


def pirate_site(sites):
    from app.objects import strength
    for q in range(20, 110):
        for r in range(20, 110):
            if garrisons.pirates(q, r, sites) and strength(q, r, 'sea')[0] == 'Пиратский дозор':
                return q, r


def test_pirates_fight_ships_only_and_stay_cleared(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    with c.factory() as db:
        sites = bases.near(db, 64, 64, 64)
    pq, pr = pirate_site(sites)
    flood(c, [(pq + dq, pr + dr) for dq in range(-2, 3) for dr in range(-2, 3)])
    with c.factory.begin() as db:
        army = db.get(Army, a['id']); army.q, army.r = pq - 1, pr
    # Land troops alone cannot engage raiders at sea.
    r = order(c, h, a, pq, pr, 'move')
    assert r.status_code == 409 and ('корабли' in r.json()['detail'] or 'флот' in r.json()['detail'])
    give_ship(c, a['id'], 'gunboat', 3)
    tiles = c.get(f'/api/v1/world/tiles?q={pq}&r={pr}&radius=1', headers=h).json()['tiles']
    target = next(t for t in tiles if (t['q'], t['r']) == (pq, pr))
    assert target['garrison'] and target['garrison_strength']['name'].startswith('Пират')
    metal = me(c, h)['resources']['metal']
    r = order(c, h, a, pq, pr, 'move'); assert r.status_code == 200, r.text
    at_time(monkeypatch, r.json()['state']['armies'][0]['orders'][0]['ready_at'] + 1)
    battle = next(b for b in me(c, h)['battles'] if b['status'] == 'active')
    assert battle['state']['terrain'] == 'sea' and battle['state']['cover'] == []
    assert [x['kind'] for x in battle['state']['stacks'] if x['side'] == 'player'] == ['gunboat']
    result = finish(c, h, battle)
    assert result['result']['outcome'] == 'victory' and result['result']['captured']
    s = result['state']
    assert s['resources']['metal'] > metal and (s['armies'][0]['q'], s['armies'][0]['r']) == (pq, pr)
    with c.factory() as db:
        assert db.get(ClearedSite, (1, pq, pr)).player_id == player_id(c, 123)
    tiles = c.get(f'/api/v1/world/tiles?q={pq}&r={pr}&radius=1', headers=h).json()['tiles']
    assert not next(t for t in tiles if (t['q'], t['r']) == (pq, pr))['garrison']


def test_ships_do_not_fight_on_land(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    give_ship(c, a['id'], 'transport')
    res = order(c, h, a, Q, R + 1, 'capture')      # tutorial land garrison
    at_time(monkeypatch, res.json()['state']['armies'][0]['orders'][0]['ready_at'] + 1)
    battle = next(b for b in me(c, h)['battles'] if b['status'] == 'active')
    assert all(x['kind'] != 'transport' for x in battle['state']['stacks'] if x['side'] == 'player')
