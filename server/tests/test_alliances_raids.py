from sqlalchemy import select
from app import raids, game
from app.models import Player, TileOwnership, Raid, Unit
from conftest import post, login
from test_expeditions import commander, create, order, home, player_id
from test_movement import at_time


def me(c, h):
    return c.get('/api/v1/player/me', headers=h).json()


def test_alliance_create_join_leave_and_kick(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); h2, u2 = commander(c, monkeypatch, 456)
    made = post(c, '/alliance/create', {'name': 'Стальной клин', 'tag': 'stk'}, h)
    assert made.status_code == 200, made.text
    ally = made.json()['state']['alliance']
    assert ally['tag'] == 'STK' and ally['owner'] and len(ally['members']) == 1
    assert post(c, '/alliance/create', {'name': 'Другой', 'tag': 'STK'}, h2).status_code == 409   # tag taken
    joined = post(c, '/alliance/join', {'code': ally['code'].lower()}, h2)
    assert joined.status_code == 200 and len(joined.json()['state']['alliance']['members']) == 2
    board = c.get('/api/v1/season', headers=h).json()
    assert board['alliances'][0]['tag'] == 'STK' and board['alliances'][0]['members'] == 2
    assert post(c, '/alliance/kick', {'player_id': player_id(c, 123)}, h2).status_code == 403
    assert post(c, '/alliance/kick', {'player_id': player_id(c, 456)}, h).status_code == 200
    assert me(c, h2)['alliance'] is None
    assert post(c, '/alliance/leave', {}, h).status_code == 200
    assert me(c, h)['alliance'] is None and c.get('/api/v1/season', headers=h).json()['alliances'] == []


def test_allies_cannot_attack_and_may_pass(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); h2, u2 = commander(c, monkeypatch, 456)
    a = create(c, h, u); Q, R = home(c, h)
    code = post(c, '/alliance/create', {'name': 'Северный фронт', 'tag': 'NF'}, h).json()['state']['alliance']['code']
    post(c, '/alliance/join', {'code': code}, h2)
    with c.factory.begin() as db:
        for q in (Q+1, Q+2):
            db.add(TileOwnership(world_id=1, q=q, r=R, player_id=player_id(c, 456), acquired_at=0))
        for pid in (player_id(c, 123), player_id(c, 456)):
            db.get(Player, pid).shield_until = 0
    assert order(c, h, a, Q+1, R, 'attack').status_code == 409
    tiles = c.get(f'/api/v1/world/tiles?q={Q}&r={R}&radius=2', headers=h).json()['tiles']
    assert next(t for t in tiles if (t['q'], t['r']) == (Q+1, R))['control'] == 'ally'
    route = c.get(f'/api/v1/army/route?q={Q+3}&r={R}', headers=h).json()
    assert [Q+1, R] in [p[:2] for p in route['path']] or [Q+2, R] in [p[:2] for p in route['path']]
    res = order(c, h, a, Q+2, R, 'move')
    assert res.status_code == 200, res.text
    at_time(monkeypatch, res.json()['state']['armies'][0]['orders'][0]['ready_at'] + 1)
    assert (me(c, h)['armies'][0]['q'], me(c, h)['armies'][0]['r']) == (Q+2, R)


def test_raid_spawns_next_to_weak_land_and_burns_it(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); Q, R = home(c, h)
    monkeypatch.setattr(raids, 'CHANCE', 100)
    with c.factory.begin() as db:
        for cell in [(Q+1, R), (Q+2, R), (Q+3, R), (Q+7, R)]:
            db.add(TileOwnership(world_id=1, q=cell[0], r=cell[1], player_id=player_id(c, 123), acquired_at=0))
    s = me(c, h)
    raid = next(x for x in s['raids'] if x['status'] == 'active')
    assert (raid['target_q'], raid['target_r']) == (Q+7, R)            # cut-off land is hit first
    assert max(abs(raid['q'] - Q - 7), abs(raid['r'] - R), abs(raid['q'] + raid['r'] - Q - 7 - R)) == 1
    tiles = c.get(f"/api/v1/world/tiles?q={raid['q']}&r={raid['r']}&radius=1", headers=h).json()['tiles']
    spot = next(t for t in tiles if (t['q'], t['r']) == (raid['q'], raid['r']))
    assert spot['garrison'] and spot['garrison_strength']['name'] == 'Мародёры' and spot['raid']['mine']
    me(c, h)
    assert len([x for x in me(c, h)['raids'] if x['status'] == 'active']) == 1   # one per day
    at_time(monkeypatch, raid['strikes_at'] + 1)
    s = me(c, h)
    assert not any((t['q'], t['r']) == (Q+7, R) for t in s['territories'])
    assert any(x['status'] == 'struck' and 'сожгли' in x['result'] for x in s['raids'])


def test_beating_the_raiders_saves_the_land(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    monkeypatch.setattr(raids, 'CHANCE', 100)
    with c.factory.begin() as db:
        for cell in [(Q+1, R), (Q+2, R), (Q+1, R-1), (Q+2, R-1)]:
            db.add(TileOwnership(world_id=1, q=cell[0], r=cell[1], player_id=player_id(c, 123), acquired_at=0))
        db.get(Unit, u).count = 60
    raid = next(x for x in me(c, h)['raids'] if x['status'] == 'active')
    res = order(c, h, a, raid['q'], raid['r'], 'move')
    assert res.status_code == 200, res.text
    at_time(monkeypatch, res.json()['state']['armies'][0]['orders'][0]['ready_at'] + 1)
    battle = next(b for b in me(c, h)['battles'] if b['status'] == 'active')
    assert battle['state']['npc_tier']['name'] == 'Мародёры'
    from test_pvp import finish
    assert finish(c, h, battle)['result']['outcome'] == 'victory'
    s = me(c, h)
    assert any(x['status'] == 'defeated' for x in s['raids'])
    at_time(monkeypatch, raid['strikes_at'] + 1)
    assert len(me(c, h)['territories']) >= 4
