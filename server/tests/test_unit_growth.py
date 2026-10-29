"""Stack growth: veterancy from battles, barracks-sized stacks, reinforcement and merging."""
from sqlalchemy import select
from app import combat, veterancy
from app.models import Unit, Building, Resource, Item
from conftest import post
from test_expeditions import commander, create, player_id
from test_integration import advance


def me(c, h):
    return c.get('/api/v1/player/me', headers=h).json()


def first_unit(c, h):
    return me(c, h)['units'][0]


def set_unit(c, unit_id, **values):
    with c.factory.begin() as db:
        u = db.get(Unit, unit_id)
        for k, v in values.items():
            setattr(u, k, v)


def set_building(c, kind, level, uid=123):
    with c.factory.begin() as db:
        db.scalar(select(Building).where(Building.player_id == player_id(c, uid), Building.kind == kind)).level = level


def rich(c, uid=123):
    with c.factory.begin() as db:
        for r in db.scalars(select(Resource).where(Resource.player_id == player_id(c, uid))):
            r.amount = 4000


def test_first_battle_gives_the_stack_experience(client, monkeypatch):
    c = client; h, _ = commander(c, monkeypatch)
    u = first_unit(c, h)
    assert u['xp'] >= 20 and u['rank'] == 0 and u['rank_name'] == 'Новобранцы'
    assert u['next_xp'] == 100 and u['cap'] == 10


def test_ranks_and_their_combat_bonus():
    assert [veterancy.rank(x) for x in (0, 99, 100, 299, 300, 700, 5000)] == [0, 0, 1, 1, 2, 3, 3]
    s = {'stacks': [], 'cover': [], 'turn': 1}
    green = combat.make_stack('p1', 'player', 'rifles', 10, [0, 0])
    elite = combat.make_stack('p2', 'player', 'rifles', 10, [0, 1], rank=3)
    foe = combat.make_stack('n1', 'npc', 'rifles', 10, [5, 5])
    hit = lambda a, t: combat._damage(s, a, t, 'seed', 'raven', 0, 1, 't', fixed_roll=100)
    assert hit(elite, foe) > hit(green, foe)
    tough = combat.make_stack('n2', 'npc', 'rifles', 10, [5, 6], rank=3)
    assert hit(green, tough) < hit(green, foe)


def test_elite_uses_its_ability_twice():
    def use(rank):
        me = combat.make_stack('p1', 'player', 'rifles', 10, [3, 3], rank=rank)
        foe = combat.make_stack('n1', 'npc', 'rifles', 30, [3, 6])
        s = {'stacks': [me, foe], 'cover': [], 'turn': 1}
        combat._skill(s, me, {'target': 'n1'}, 'seed', 'raven', 0, [])
        try:
            combat._skill(s, me, {'target': 'n1'}, 'seed', 'raven', 0, [])
            return 2
        except ValueError:
            return 1
    assert use(0) == 1 and use(3) == 2


def test_refill_restores_losses_and_dilutes_experience(client, monkeypatch):
    c = client; h, _ = commander(c, monkeypatch); rich(c)
    u = first_unit(c, h)
    set_unit(c, u['id'], count=5, xp=400)
    r = post(c, '/units/refill', {'unit_id': u['id']}, h)
    assert r.status_code == 200, r.text
    body = r.json()['result']
    assert body['added'] == 5 and all(v > 0 for v in body['cost'].values())
    assert post(c, '/army/train', {}, h).status_code == 409      # the barracks queue is busy
    advance(c, monkeypatch, body['ready_at'] - __import__('app.game', fromlist=['now']).now() + 1)
    u = first_unit(c, h)
    assert u['count'] == 10 and u['xp'] == 200 and u['rank_name'] == 'Бывалые'
    full = post(c, '/units/refill', {'unit_id': u['id']}, h)
    assert full.status_code == 409 and 'полон' in full.json()['detail']


def test_refill_needs_the_stack_at_the_base(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); rich(c)
    army = create(c, h, u)
    set_unit(c, u, count=4)
    from app.models import Army
    with c.factory.begin() as db:
        db.get(Army, army['id']).q += 3
    r = post(c, '/units/refill', {'unit_id': u}, h)
    assert r.status_code == 409 and 'базе' in r.json()['detail']


def test_barracks_level_grows_the_cap_and_merge_pours_stacks(client, monkeypatch):
    c = client; h, _ = commander(c, monkeypatch)
    u = first_unit(c, h)
    set_building(c, 'barracks', 3)
    set_unit(c, u['id'], xp=300, count=10)
    with c.factory.begin() as db:
        db.add(Unit(id='extra-1', player_id=player_id(c, 123), kind=u['kind'], hp=100, count=8, xp=0, status='reserve'))
        db.add(Unit(id='other-kind', player_id=player_id(c, 123), kind='raven_scouts', hp=100, count=6, xp=0, status='reserve'))
    assert first_unit(c, h)['cap'] == 15
    r = post(c, '/units/merge', {'unit_id': 'extra-1', 'into_id': u['id']}, h)
    assert r.status_code == 200, r.text
    assert r.json()['result'] == {'moved': 5, 'left': 3}
    units = {x['id']: x for x in me(c, h)['units']}
    assert units[u['id']]['count'] == 15 and units[u['id']]['xp'] == 200 and units['extra-1']['count'] == 3
    assert post(c, '/units/merge', {'unit_id': 'extra-1', 'into_id': u['id']}, h).status_code == 409   # full
    assert post(c, '/units/merge', {'unit_id': 'other-kind', 'into_id': 'extra-1'}, h).status_code == 409
    # Pouring a whole stack removes it.
    r = post(c, '/units/merge', {'unit_id': u['id'], 'into_id': 'extra-1'}, h)
    assert r.json()['result'] == {'moved': 12, 'left': 3}


def test_full_merge_deletes_the_source_even_with_battle_history(client, monkeypatch):
    c = client; h, _ = commander(c, monkeypatch)
    u = first_unit(c, h)                       # fought the tutorial battle
    set_building(c, 'barracks', 3)
    with c.factory.begin() as db:
        db.add(Unit(id='big', player_id=player_id(c, 123), kind=u['kind'], hp=100, count=2, status='reserve'))
    r = post(c, '/units/merge', {'unit_id': u['id'], 'into_id': 'big'}, h)
    assert r.status_code == 200 and r.json()['result']['left'] == 0, r.text
    assert [x['id'] for x in me(c, h)['units']] == ['big']


def test_artifacts_for_unit_growth_drop_and_apply():
    from app import equipment
    keys = {equipment.loot(f'seed-{i}', 3)[0] for i in range(400)}
    assert {'drill-manual', 'regiment-banner'} <= keys
    assert equipment.DEFINITIONS['recruit-poster']['perks'] == {'refill_cost': 0.2}
    assert veterancy.refill_cost('rifles', 5, 0.2)['metal'] < veterancy.refill_cost('rifles', 5)['metal']
