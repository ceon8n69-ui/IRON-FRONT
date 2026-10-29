from sqlalchemy import select
from app import objects, doctrines, commander, game
from app.models import Resource, Doctrine, Army, Hero
from conftest import post
from test_expeditions import commander as setup, create, order, home, player_id
from test_movement import at_time


def me(c, h):
    return c.get('/api/v1/player/me', headers=h).json()


def rich(c, uid=123):
    with c.factory.begin() as db:
        for res in db.scalars(select(Resource).where(Resource.player_id == player_id(c, uid))):
            res.amount = 5000


def test_research_tree_tiers_and_exclusive_picks(client, monkeypatch):
    c = client; h, u = setup(c, monkeypatch); rich(c)
    r = post(c, '/doctrines/research', {'key': 'bayonets'}, h)
    assert r.status_code == 200, r.text
    s = r.json()['state']
    assert s['resources']['metal'] == 5000 - 400
    assert next(d for d in s['doctrines']['doctrines'] if d['key'] == 'bayonets')['state'] == 'research'
    assert post(c, '/doctrines/research', {'key': 'roads'}, h).status_code == 409          # one at a time
    assert post(c, '/doctrines/research', {'key': 'veterans'}, h).status_code == 409       # tier 1 not done
    at_time(monkeypatch, game.now() + 601)
    assert post(c, '/doctrines/research', {'key': 'trenches'}, h).status_code == 409       # rival in tier 1
    assert post(c, '/doctrines/research', {'key': 'veterans'}, h).status_code == 200
    assert me(c, h)['doctrines']['effects']['inf_attack'] == 0.10


def test_doctrines_reach_combat_movement_and_limits(client, monkeypatch):
    c = client; h, u = setup(c, monkeypatch); a = create(c, h, u)
    pid = player_id(c, 123)
    with c.factory.begin() as db:
        for key in ('bayonets', 'roads', 'depots', 'front_hq', 'factories'):
            db.add(Doctrine(player_id=pid, key=key, started_at=0, ready_at=1))
    s = me(c, h)
    assert s['armies'][0]['movement_max'] == 34 and s['armies_max'] == 4
    assert s['storage_cap'] == round(5000 * 1.25)
    with c.factory() as db:
        assert commander.battle_perks(db, pid, False)['inf_attack'] == 0.10
        assert 'attack' not in commander.battle_perks(db, pid, False)


def test_ruin_gives_one_fixed_outcome_to_the_first_visitor(client, monkeypatch):
    c = client; h, u = setup(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    real = objects.placed
    monkeypatch.setattr(objects, 'placed', lambda q, r, sites, biome='plain': {'kind': 'ruin'} if (q, r) == (Q+2, R) else None)
    res = order(c, h, a, Q+2, R, 'move')
    at_time(monkeypatch, res.json()['state']['armies'][0]['orders'][0]['ready_at'] + 1)
    s = me(c, h)
    assert s['armies'][0]['orders'][0]['result'].startswith('Армия прибыла. Руины:')
    for q in (Q+1, Q+2):
        res = order(c, h, a, q, R, 'move')
        at_time(monkeypatch, res.json()['state']['armies'][0]['orders'][0]['ready_at'] + 1)
    assert 'уже побывал' in me(c, h)['armies'][0]['orders'][0]['result']


def test_camp_sells_one_stack_per_week(client, monkeypatch):
    c = client; h, u = setup(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h); rich(c)
    camp = {'kind': 'camp', 'unit': 'titan_shields'}
    monkeypatch.setattr(objects, 'placed', lambda q, r, sites, biome='plain': camp if (q, r) == (Q+1, R) else None)
    res = order(c, h, a, Q+1, R, 'move')
    at_time(monkeypatch, res.json()['state']['armies'][0]['orders'][0]['ready_at'] + 1)
    tiles = c.get(f'/api/v1/world/tiles?q={Q}&r={R}&radius=2', headers=h).json()['tiles']
    view = next(t for t in tiles if (t['q'], t['r']) == (Q+1, R))['object']
    assert view['available'] and view['unit'] == 'titan_shields'
    hired = post(c, '/world/hire', {'army_id': a['id']}, h)
    assert hired.status_code == 200, hired.text
    s = hired.json()['state']
    assert hired.json()['result']['joined'] and len(s['armies'][0]['unit_ids']) == 2
    assert s['resources']['metal'] == 5000 - view['cost']['metal']
    again = post(c, '/world/hire', {'army_id': a['id']}, h)
    assert again.status_code == 409 and 'уже наняли' in again.json()['detail']
