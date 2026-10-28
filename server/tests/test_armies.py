from sqlalchemy import select
from app.models import Unit, Army, Building
from conftest import post
from test_expeditions import commander, create, order, home, player_id
from test_movement import at_time


def me(c, h):
    return c.get('/api/v1/player/me', headers=h).json()


def extra_unit(c, uid=123, kind='raven_line', count=10):
    with c.factory.begin() as db:
        unit = Unit(id=f'extra-{kind}-{count}', player_id=player_id(c, uid), kind=kind, hp=100, count=count, status='reserve')
        db.add(unit)
    return unit.id


def test_two_armies_march_in_different_directions(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); Q, R = home(c, h)
    a1 = create(c, h, u)
    u2 = extra_unit(c)
    second = post(c, '/army/create', {'unit_id': u2}, h)
    assert second.status_code == 200, second.text
    armies = second.json()['state']['armies']
    assert [a['number'] for a in armies] == [1, 2] and [a['commander'] for a in armies] == [True, False]
    assert second.json()['state']['armies_max'] == 2
    third = post(c, '/army/create', {'unit_id': extra_unit(c, count=7)}, h)
    assert third.status_code == 409 and 'Максимум соединений' in third.json()['detail']
    a2 = armies[1]
    r1 = order(c, h, a1, Q+2, R, 'move'); r2 = order(c, h, a2, Q-2, R, 'move')
    assert r1.status_code == r2.status_code == 200, r2.text
    s = r2.json()['state']
    assert all(a['status'] == 'moving' for a in s['armies'])
    at_time(monkeypatch, max(o['ready_at'] for a in s['armies'] for o in a['orders']) + 1)
    s = me(c, h)
    assert {(a['q'], a['r']) for a in s['armies']} == {(Q+2, R), (Q-2, R)}
    assert all(a['movement'] < a['movement_max'] for a in s['armies'])       # each army spends its own points


def test_hq_raises_army_limit(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch)
    with c.factory.begin() as db:
        db.scalar(select(Building).where(Building.player_id == player_id(c, 123), Building.kind == 'hq')).level = 5
    assert me(c, h)['armies_max'] == 4


def test_only_the_commanders_army_uses_his_ability(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); Q, R = home(c, h)
    create(c, h, u)
    second = post(c, '/army/create', {'unit_id': extra_unit(c, count=12)}, h).json()['state']['armies'][1]
    res = order(c, h, second, Q, R+1, 'capture')            # tutorial garrison south of the base
    assert res.status_code == 200, res.text
    at_time(monkeypatch, next(a for a in res.json()['state']['armies'] if a['id'] == second['id'])['orders'][0]['ready_at'] + 1)
    battle = next(b for b in me(c, h)['battles'] if b['status'] == 'active')
    assert battle['state']['led'] is False
    hit = post(c, '/battles/commands', {'battle_id': battle['id'], 'turn': battle['state']['turn'], 'action': 'ability'}, h)
    assert hit.status_code == 409 and 'Командира нет' in hit.json()['detail']


def test_second_army_waits_while_another_battle_runs(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); Q, R = home(c, h)
    a1 = create(c, h, u)
    a2 = post(c, '/army/create', {'unit_id': extra_unit(c, count=12)}, h).json()['state']['armies'][1]
    r1 = order(c, h, a1, Q, R+1, 'capture')
    assert r1.status_code == 200
    at_time(monkeypatch, r1.json()['state']['armies'][0]['orders'][0]['ready_at'] + 1)
    assert any(b['status'] == 'active' for b in me(c, h)['battles'])
    from app import garrisons                              # a second guarded hex west of the base
    real = garrisons.guarded
    if True:
        monkeypatch.setattr(garrisons, 'guarded', lambda q, r, sites, biome='plain': (q, r) == (Q-1, R) or real(q, r, sites, biome))
    r2 = order(c, h, a2, Q-1, R, 'capture')
    assert r2.status_code == 200, r2.text                    # other armies still take orders mid-battle
    ready = next(a for a in r2.json()['state']['armies'] if a['id'] == a2['id'])['orders'][0]['ready_at']
    at_time(monkeypatch, ready + 5)
    s = me(c, h)
    assert sum(b['status'] == 'active' for b in s['battles']) == 1
    waiting = next(a for a in s['armies'] if a['id'] == a2['id'])
    assert waiting['status'] == 'moving' and waiting['orders'][0]['status'] == 'moving'
    from test_pvp import finish
    first = next(b for b in s['battles'] if b['status'] == 'active')
    assert finish(c, h, first)['result']['outcome'] in ('victory', 'defeat')
    s = me(c, h)
    nxt = next(b for b in s['battles'] if b['status'] == 'active')
    assert (nxt['state']['expedition']['q'], nxt['state']['expedition']['r']) == (Q-1, R)
    assert nxt['state']['expedition']['army_id'] == a2['id']


def test_lead_transfer_and_disband(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch)
    create(c, h, u)
    a2 = post(c, '/army/create', {'unit_id': extra_unit(c)}, h).json()['state']['armies'][1]
    first = me(c, h)['armies'][0]
    assert post(c, '/army/disband', {'army_id': first['id']}, h).status_code == 409   # commander must move first
    s = post(c, '/army/lead', {'army_id': a2['id']}, h).json()['state']
    assert [a['commander'] for a in s['armies']] == [False, True]
    s = post(c, '/army/disband', {'army_id': first['id']}, h).json()['state']
    assert [a['id'] for a in s['armies']] == [a2['id']]
    assert next(x for x in s['units'] if x['id'] == u)['status'] == 'reserve'
    again = post(c, '/army/create', {'unit_id': u}, h).json()['state']['armies']
    assert sorted(a['number'] for a in again) == [1, 2]
