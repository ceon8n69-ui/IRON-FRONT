import pytest
from app import combat
from app.config import FACTIONS, UNITS, TRAITS, HEROES
from app.combat import new_battle, make_stack, resolve
from conftest import login, post
from test_expeditions import commander, player_id
from test_movement import at_time


def test_every_commander_has_five_unique_units_covering_all_roles():
    assert set(FACTIONS) == set(HEROES)
    keys = [v['key'] for f in FACTIONS.values() for v in f['units']]
    assert len(keys) == len(set(keys)) == 30
    for f in FACTIONS.values():
        assert sorted(v['role'] for v in f['units']) == sorted(['rifles', 'scouts', 'assault', 'artillery', 'armor'])
        for v in f['units']:
            u = UNITS[v['key']]
            assert u['hp'] >= 1 and u['speed'] >= 1 and u['damage'] >= 0 and u['range'] >= 1
            assert u.get('trait') is None or u['trait'] in TRAITS


def test_faction_power_stays_close_to_baseline():
    def power(u):
        return u['count'] * u['hp'] * (u['damage'] + 1) * (1 + 0.05 * u['defense'])
    for f in FACTIONS.values():
        for v in f['units']:
            assert 0.6 < power(UNITS[v['key']]) / power(UNITS[v['role']]) < 1.35, v['key']  # medics trade damage for healing


def test_hiring_uses_own_faction_and_maps_roles(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch)          # Raven
    r = post(c, '/army/train', {'kind': 'titan_line'}, h)
    assert r.status_code == 409 and 'другой командир' in r.json()['detail']
    r = post(c, '/army/train', {'kind': 'rifles'}, h)
    assert r.status_code == 200
    at_time(monkeypatch, r.json()['state']['jobs'][0]['ready_at'] + 1)
    kinds = [x['kind'] for x in c.get('/api/v1/player/me', headers=h).json()['units']]
    assert kinds.count('raven_line') == 2       # tutorial squad + this one
    cfg = c.get('/api/v1/config').json()
    assert cfg['factions']['raven']['units'][0]['name'] == 'Стрелки легиона' and 'charge' in cfg['traits']


def duel(attacker, defender, cmd=None, hero='raven'):
    s, _, _ = new_battle([make_stack('p1', 'player', attacker, UNITS[attacker]['count'], [3, 4], 'u')],
                         [make_stack('n1', 'npc', defender, UNITS[defender]['count'], [4, 4])], [], 'seed', hero, 0)
    return resolve(s, cmd or {'action': 'attack'}, 'seed', hero, 0)


def test_first_strike_prevents_retaliation():
    for kind, expect in (('raven_assault', False), ('assault', True)):
        _, events, _ = duel(kind, 'assault')
        first = events.index(next(e for e in events if e['type'] == 'attack' and e['actor'] == 'p1'))
        answered = len(events) > first + 1 and events[first + 1]['type'] == 'retaliate' and events[first + 1]['actor'] == 'n1'
        assert answered is expect, kind


def test_pierce_ignores_defense_and_shield_blocks_shots():
    plain = combat._damage({'cover': [], 'stacks': [], 'turn': 1}, make_stack('a', 'player', 'artillery', 4, [0, 0], 'u'),
                           make_stack('b', 'npc', 'armor', 3, [5, 5]), 's', None, 0, 1, 't')
    pierce = combat._damage({'cover': [], 'stacks': [], 'turn': 1}, make_stack('a', 'player', 'ghost_tesla', 4, [0, 0], 'u'),
                            make_stack('b', 'npc', 'armor', 3, [5, 5]), 's', None, 0, 1, 't')
    assert pierce > plain
    vs_shield = combat._damage({'cover': [], 'stacks': [], 'turn': 1}, make_stack('a', 'player', 'rifles', 10, [0, 0], 'u'),
                               make_stack('b', 'npc', 'titan_shields', 8, [5, 5]), 's', None, 0, 1, 't')
    vs_plain = combat._damage({'cover': [], 'stacks': [], 'turn': 1}, make_stack('a', 'player', 'rifles', 10, [0, 0], 'u'),
                              make_stack('b', 'npc', 'assault', 8, [5, 5]), 's', None, 0, 1, 't')
    assert vs_shield < vs_plain


def test_medics_heal_neighbours_after_acting():
    medic = make_stack('p1', 'player', 'phoenix_medics', 6, [2, 4], 'm')
    hurt = make_stack('p2', 'player', 'phoenix_line', 10, [2, 5], 'r'); hurt['hp'] = 50
    s, _, _ = new_battle([medic, hurt], [make_stack('n1', 'npc', 'rifles', 1, [8, 0])], [], 'seed', 'phoenix', 0)
    if s['active'] != 'p1':
        s, _, _ = resolve(s, {'action': 'wait'}, 'seed', 'phoenix', 0)
    before = next(x for x in s['stacks'] if x['id'] == 'p2')['hp']
    s, events, _ = resolve(s, {'action': 'defend'}, 'seed', 'phoenix', 0)
    assert any(e['type'] == 'heal' and e['target'] == 'p2' for e in events)
    assert next(x for x in s['stacks'] if x['id'] == 'p2')['hp'] > before


def test_stack_state_carries_art_for_client():
    st = make_stack('p1', 'player', 'valkyrie_walker', 6, [1, 1], 'u')
    assert st['art'] == 'walker' and st['faction'] == 'valkyrie' and st['each'] == UNITS['valkyrie_walker']['hp']
