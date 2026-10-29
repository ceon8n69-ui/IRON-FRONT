"""Rules of the Polytopia-style match engine (pure, no database)."""
import pytest
from app import match_engine as E, match_ai as A


def new(seats=(0, 1), size='small', seed='t'):
    return E.generate(size, list(seats), seed, {0: 'raven', 1: 'titan', 2: 'storm', 3: 'ghost'})


def put_unit(s, role, q, r, seat, ready=True):
    return E._spawn(s, role, q, r, seat, None, ready=ready)


def free_tile(s, near, terrain='field'):
    for q, r in sorted(E.within(*near, 4), key=lambda p: E.distance(p, near)):
        t = s['tiles'].get(E.key(q, r))
        if t and t['t'] == terrain and not E.unit_at(s, q, r) and not E.city_at(s, q, r):
            return q, r


def test_generation_is_deterministic_and_fair():
    a, b = new(seed='x'), new(seed='x')
    assert a == b
    caps = [c for c in a['cities'].values() if c['capital']]
    assert {c['owner'] for c in caps} == {0, 1} and len(a['cities']) > 4
    assert all(p['stars'] == E.START_STARS for p in a['players'].values())
    reach = E._reachable(a, (caps[0]['q'], caps[0]['r']))
    assert (caps[1]['q'], caps[1]['r']) in reach                  # capitals connected by land


def test_turns_pass_immediately_and_pay_income():
    s = new()
    with pytest.raises(E.Illegal):
        E.apply(s, 1, {'type': 'end_turn'})
    s, _ = E.apply(s, 0, {'type': 'end_turn'})
    assert s['current'] == 1 and s['players']['1']['stars'] == E.START_STARS + 2   # capital: level 1 + 1
    s, _ = E.apply(s, 1, {'type': 'end_turn'})
    assert s['current'] == 0 and s['turn'] == 2


def test_village_capture_needs_a_unit_that_started_there_then_choose_spec():
    s = new()
    village = next(c for c in s['cities'].values() if c['owner'] is None)
    uid = put_unit(s, 'rifles', village['q'], village['r'], 0, ready=False)
    with pytest.raises(E.Illegal):
        E.apply(s, 0, {'type': 'capture', 'unit': uid})              # just arrived
    s['units'][uid]['moved'] = s['units'][uid]['attacked'] = False
    s, ev = E.apply(s, 0, {'type': 'capture', 'unit': uid})
    c = s['cities'][village['id']]
    assert c['owner'] == 0 and c['spec'] is None and ev[0]['type'] == 'capture'
    s, _ = E.apply(s, 0, {'type': 'spec', 'city': c['id'], 'spec': 'outpost'})
    assert s['cities'][c['id']]['radius'] == 2
    with pytest.raises(E.Illegal):
        E.apply(s, 0, {'type': 'spec', 'city': c['id'], 'spec': 'market'})


def test_improvements_grow_the_city_and_levels_offer_rewards():
    s = new()
    cap = next(c for c in s['cities'].values() if c['owner'] == 0)
    s['players']['0']['stars'] = 50
    s['players']['0']['techs'] = ['farming', 'forestry']
    q, r = free_tile(s, (cap['q'], cap['r']))
    s['tiles'][E.key(q, r)].update(res='crop', city=cap['id'])
    s, ev = E.apply(s, 0, {'type': 'build', 'q': q, 'r': r, 'improvement': 'farm'})
    c = s['cities'][cap['id']]
    assert c['level'] == 2 and c['reward'] == 2 and s['players']['0']['stars'] == 45
    s, _ = E.apply(s, 0, {'type': 'reward', 'city': c['id'], 'reward': 'workshop'})
    assert E.income(s, c['id']) == 2 + 1 + 1                     # level + capital + workshop


def test_combat_formula_retaliation_and_melee_advance():
    s = new()
    a = put_unit(s, 'assault', 0, 5, 0)
    d = put_unit(s, 'rifles', 1, 5, 1)
    s['tiles'][E.key(1, 5)]['t'] = 'field'; s['tiles'][E.key(0, 5)]['t'] = 'field'
    dmg, back = E.forecast(s, s['units'][a], s['units'][d])
    assert dmg == round(3 / (3 + 2) * 3 * 4.5) and back > 0
    s['units'][d]['hp'] = 2
    s, ev = E.apply(s, 0, {'type': 'attack', 'unit': a, 'target': d})
    assert d not in s['units'] and (s['units'][a]['q'], s['units'][a]['r']) == (1, 5) and s['units'][a]['kills'] == 1


def test_three_kills_unlock_a_promotion_branch():
    s = new()
    uid = put_unit(s, 'rifles', 0, 5, 0)
    s['units'][uid]['kills'] = 3
    s, _ = E.apply(s, 0, {'type': 'promote', 'unit': uid, 'branch': 'bayonets'})
    u = s['units'][uid]
    assert E.stat(u, 'atk') == 3 and u['hp'] == E.max_hp(u) == 15
    with pytest.raises(E.Illegal):
        E.apply(s, 0, {'type': 'promote', 'unit': uid, 'branch': 'trenches'})


def test_techs_unlock_units_and_cost_more_with_more_cities():
    s = new()
    cap = next(c for c in s['cities'].values() if c['owner'] == 0)
    assert E.available_roles(s, 0, cap['id']) == ['rifles']
    assert E.tech_cost(s, 0, 'motors') == 5
    s['players']['0']['stars'] = 20
    with pytest.raises(E.Illegal):
        E.apply(s, 0, {'type': 'research', 'tech': 'armor'})       # needs motors first
    s, _ = E.apply(s, 0, {'type': 'research', 'tech': 'motors'})
    assert 'scouts' in E.available_roles(s, 0, cap['id'])
    s['players']['0']['techs'] += ['armor']
    assert 'armor' not in E.available_roles(s, 0, cap['id'])        # only in factory cities


def test_training_respects_city_capacity():
    s = new()
    cap = next(c for c in s['cities'].values() if c['owner'] == 0)
    s['players']['0']['stars'] = 30
    for u in list(s['units'].values()):
        if u['owner'] == 0:
            u['q'], u['r'] = free_tile(s, (cap['q'], cap['r']))
    s, _ = E.apply(s, 0, {'type': 'train', 'city': cap['id'], 'role': 'rifles'})
    new_unit = next(u for u in s['units'].values() if u['home'] == cap['id'] and u['moved'])
    new_unit['q'], new_unit['r'] = free_tile(s, (cap['q'], cap['r']))
    with pytest.raises(E.Illegal):                                    # capital level 1: 2 units
        E.apply(s, 0, {'type': 'train', 'city': cap['id'], 'role': 'rifles'})


def test_losing_every_city_eliminates_and_the_last_player_wins():
    s = new()
    enemy_cap = next(c for c in s['cities'].values() if c['owner'] == 1)
    for u in [u for u in s['units'].values() if u['owner'] == 1]:
        del s['units'][u['id']]
    uid = put_unit(s, 'rifles', enemy_cap['q'], enemy_cap['r'], 0)
    s, ev = E.apply(s, 0, {'type': 'capture', 'unit': uid})
    assert s['players']['1']['eliminated'] and s['winner'] == 0
    with pytest.raises(E.Illegal):
        E.apply(s, 0, {'type': 'end_turn'})


def test_view_hides_unseen_enemies_and_private_numbers():
    s = new()
    v = E.view(s, 0)
    assert all(u['owner'] == 0 for u in v['units'])
    assert len(v['tiles']) < len(s['tiles'])
    other = next(p for p in v['players'] if p['seat'] == 1)
    assert 'stars' not in other and 'techs' not in other


def test_ai_games_finish():
    for seed in ('a', 'c'):
        s = new(seed=seed)
        while s['winner'] is None and s['turn'] < 120:
            s, _ = A.play_turn(s, s['current'])
        assert s['winner'] in (0, 1)
