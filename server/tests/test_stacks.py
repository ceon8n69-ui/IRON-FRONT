import math
from sqlalchemy import select
from app import game
from app.models import Building, Unit, Army, Battle, Player
from conftest import login, post
from test_expeditions import commander, create, order, home, player_id
from test_movement import at_time


def finish(c, h, battle, action='attack'):
    """Drive a battle: ranged stacks out of range step forward, others act."""
    for _ in range(60):
        state = me(c, h)
        b = next(x for x in state['battles'] if x['id'] == battle['id'])
        if b['status'] != 'active':
            return last
        s = b['state']; active = next(x for x in s['stacks'] if x['id'] == s['active'])
        cmd = {'battle_id': b['id'], 'turn': s['turn'], 'action': action}
        last = post(c, '/battles/commands', cmd, h)
        if last.status_code == 409 and 'дальности' in last.json()['detail']:
            q, r = active['pos']
            for nq, nr in [(q+1, r), (q+1, r-1), (q, r+1), (q, r-1)]:
                last = post(c, '/battles/commands', {**cmd, 'action': 'move', 'q': nq, 'r': nr}, h)
                if last.status_code == 200:
                    break
        assert last.status_code == 200, last.text
        last = last.json()
        if last['result']['outcome'] != 'active':
            return last
    raise AssertionError('battle did not finish')


def me(c, h):
    return c.get('/api/v1/player/me', headers=h).json()


def barracks(c, level):
    with c.factory.begin() as db:
        db.scalar(select(Building).where(Building.kind == 'barracks')).level = level
        db.scalar(select(Building).where(Building.kind == 'hq')).level = max(level, 1)


def reserve(c, pid, kind, count, uid):
    with c.factory.begin() as db:
        db.add(Unit(id=uid, player_id=pid, kind=kind, count=count, hp=100, status='reserve'))


def test_unit_types_need_barracks_level_and_train_as_stacks(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch)
    r = post(c, '/army/train', {'kind': 'assault'}, h)
    assert r.status_code == 409 and 'Казармы 2' in r.json()['detail']
    assert post(c, '/army/train', {'kind': 'tanks'}, h).status_code == 409
    barracks(c, 2)
    r = post(c, '/army/train', {'kind': 'assault'}, h)
    assert r.status_code == 200, r.text
    at_time(monkeypatch, r.json()['state']['jobs'][0]['ready_at'] + 1)
    assault = next(x for x in me(c, h)['units'] if x['kind'] == 'assault')
    assert assault['count'] == 8 and assault['hp'] == 100


def test_army_composition_changes_only_at_base(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    pid = player_id(c, 123)
    for i in range(5):
        reserve(c, pid, 'rifles', 5, f'extra{i}')
    for i in range(4):
        assert post(c, '/army/assign', {'unit_id': f'extra{i}'}, h).status_code == 200
    full = post(c, '/army/assign', {'unit_id': 'extra4'}, h)
    assert full.status_code == 409 and 'максимум 5' in full.json()['detail']
    assert len(me(c, h)['armies'][0]['unit_ids']) == 5
    assert post(c, '/army/release', {'unit_id': 'extra0'}, h).status_code == 200
    res = order(c, h, a, Q+1, R, 'move'); at_time(monkeypatch, res.json()['state']['armies'][0]['orders'][0]['ready_at'] + 1)
    me(c, h)  # settle arrival; a rejected command below rolls back its own transaction
    away = post(c, '/army/assign', {'unit_id': 'extra0'}, h)
    assert away.status_code == 409 and 'базе' in away.json()['detail']
    with c.factory.begin() as db:
        army = db.get(Army, a['id']); army.q, army.r = Q, R
    for i in range(1, 4):
        r = post(c, '/army/release', {'unit_id': f'extra{i}'}, h)
        assert r.status_code == 200, r.text
    last = post(c, '/army/release', {'unit_id': u}, h)
    assert last.status_code == 409 and 'хотя бы один' in last.json()['detail']


def test_multi_stack_garrison_battle_persists_casualties(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    reserve(c, player_id(c, 123), 'rifles', 10, 'second')
    assert post(c, '/army/assign', {'unit_id': 'second'}, h).status_code == 200
    res = order(c, h, a, Q, R+1, 'capture')
    at_time(monkeypatch, res.json()['state']['armies'][0]['orders'][0]['ready_at'] + 1)
    battle = next(b for b in me(c, h)['battles'] if b['status'] == 'active')
    players = [x for x in battle['state']['stacks'] if x['side'] == 'player']
    assert {x['unit_id'] for x in players} == {u, 'second'}
    result = finish(c, h, battle)
    assert result['result']['outcome'] == 'victory' and result['result']['captured']
    units = {x['id']: x for x in result['state']['units']}
    assert all(units[i]['status'] == 'army' for i in (u, 'second'))
    assert all(1 <= units[i]['count'] <= 10 for i in (u, 'second'))
    with c.factory() as db:
        final = db.get(Battle, battle['id']).state
    for x in final['stacks']:
        if x['side'] == 'player':
            survivors = math.ceil(x['hp'] / 10)
            assert units[x['unit_id']]['count'] == max(1, survivors)


def test_defeat_keeps_half_of_each_stack(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    res = order(c, h, a, Q, R+1, 'capture')
    at_time(monkeypatch, res.json()['state']['armies'][0]['orders'][0]['ready_at'] + 1)
    battle = next(b for b in me(c, h)['battles'] if b['status'] == 'active')
    start = next(x for x in battle['state']['stacks'] if x['side'] == 'player')['count']
    result = finish(c, h, battle, 'defend')
    assert result['result']['outcome'] == 'defeat'
    unit = next(x for x in result['state']['units'] if x['id'] == u)
    assert unit['count'] >= math.ceil(start / 2) and unit['status'] == 'army'


def test_active_legacy_battle_is_converted_on_read(client, monkeypatch):
    c = client; h = login(c)
    post(c, '/heroes/choose', {'kind': 'raven'}, h)
    pid = player_id(c, 123)
    reserve(c, pid, 'rifles', 10, 'old-squad')
    with c.factory.begin() as db:
        db.get(Unit, 'old-squad').status = 'battle'
        db.add(Battle(id='legacy', player_id=pid, unit_id='old-squad', status='active', seed='s', balance_version='slice-6',
                      state={'turn': 2, 'player': {'pos': [3, 4], 'hp': 90}, 'npc': {'pos': [6, 4], 'hp': 40}, 'cover': []}))
    battle = next(b for b in me(c, h)['battles'] if b['id'] == 'legacy')
    assert [x['side'] for x in battle['state']['stacks']] == ['player', 'npc']
    r = post(c, '/battles/commands', {'battle_id': 'legacy', 'turn': 2, 'action': 'attack'}, h)
    assert r.status_code == 200, r.text
