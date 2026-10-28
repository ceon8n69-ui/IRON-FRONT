import math
from sqlalchemy import select, func
from app import game
from app.config import PVP
from app.models import Army, ArmyUnit, Unit, Player, Resource, TileOwnership, MapMine, PvpReport, WorldBase, Discovery
from conftest import post
from test_expeditions import commander, create, order, home, player_id
from test_movement import at_time


def dist(a, b):
    q, r = a[0] - b[0], a[1] - b[1]
    return max(abs(q), abs(r), abs(q + r))


def finish(c, h, b, action='attack'):
    """Play the attacker: attack the nearest enemy, walking closer when out of range."""
    from app.config import UNITS
    for turn in range(1, 51):
        battle = next(x for x in me(c, h)['battles'] if x['id'] == b['id'])
        st = battle['state']
        if battle['status'] != 'active':
            break
        mine = next(x for x in st['stacks'] if x['id'] == st['active'])
        foes = [x for x in st['stacks'] if x['side'] == 'npc' and x['hp'] > 0]
        target = min(foes, key=lambda x: dist(mine['pos'], x['pos']))
        cmd = {'battle_id': b['id'], 'turn': st['turn'], 'action': action}
        spec = UNITS[mine['kind']]
        if action == 'attack' and not spec['melee'] and dist(mine['pos'], target['pos']) > spec['range']:
            taken = {tuple(x['pos']) for x in st['stacks'] if x['hp'] > 0}
            cells = [(q, r) for q in range(9) for r in range(9) if (q, r) not in taken
                     and dist(mine['pos'], (q, r)) <= spec['speed']]
            q, r = min(cells, key=lambda p: dist(p, target['pos']))
            cmd.update(action='move', q=q, r=r)
        res = post(c, '/battles/commands', cmd, h)
        assert res.status_code == 200, res.text
        if res.json()['result']['outcome'] != 'active':
            return res.json()
    raise AssertionError('Battle did not finish')


def me(c, h):
    return c.get('/api/v1/player/me', headers=h).json()


def duel(c, monkeypatch, strong=40):
    """Two commanders; shields off; the attacker's only stack is beefed up."""
    h, u = commander(c, monkeypatch); h2, u2 = commander(c, monkeypatch, 456)
    a = create(c, h, u); a2 = create(c, h2, u2)
    with c.factory.begin() as db:
        for pid in (player_id(c, 123), player_id(c, 456)):
            db.get(Player, pid).shield_until = 0
        db.get(Unit, u).count = strong
    return h, u, a, h2, u2, a2


def run(c, monkeypatch, h, a, q, r):
    res = order(c, h, a, q, r, 'attack')
    assert res.status_code == 200, res.text
    at_time(monkeypatch, res.json()['state']['armies'][0]['orders'][0]['ready_at'] + 1)
    battle = next(b for b in me(c, h)['battles'] if b['status'] == 'active')
    assert battle['state']['pvp']['target'] in ('base', 'territory', 'mine')
    return battle


def test_newbie_shield_blocks_and_a_voluntary_attack_drops_your_own(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); h2, u2 = commander(c, monkeypatch, 456)
    a = create(c, h, u); Q, R = home(c, h)
    assert me(c, h)['pvp']['newbie'] and me(c, h)['pvp']['shield_until'] > game.now()
    with c.factory.begin() as db:
        db.add(TileOwnership(world_id=1, q=Q+1, r=R, player_id=player_id(c, 456), acquired_at=0))
    assert order(c, h, a, Q+1, R, 'move').status_code == 409          # must say "attack"
    blocked = order(c, h, a, Q+1, R, 'attack')
    assert blocked.status_code == 409 and 'под защитой' in blocked.json()['detail']
    with c.factory.begin() as db:
        db.get(Player, player_id(c, 456)).shield_until = 0
    monkeypatch.setitem(PVP, 'weaker_ratio', 0)
    ok = order(c, h, a, Q+1, R, 'attack')
    assert ok.status_code == 200, ok.text
    assert ok.json()['state']['pvp']['shield_until'] == 0 and not ok.json()['state']['pvp']['newbie']
    assert order(c, h, a, Q+2, R, 'attack').status_code == 409         # nothing hostile there


def test_territory_victory_transfers_tile_and_defender_keeps_half(client, monkeypatch):
    c = client; h, u, a, h2, u2, a2 = duel(c, monkeypatch); Q, R = home(c, h)
    monkeypatch.setitem(PVP, 'weaker_ratio', 0)
    enemy = player_id(c, 456)
    with c.factory.begin() as db:
        db.add(TileOwnership(world_id=1, q=Q+1, r=R, player_id=enemy, acquired_at=0))
        army = db.get(Army, a2['id']); army.q, army.r = Q+1, R
        start = db.get(Unit, u2).count
    preview = c.get(f'/api/v1/world/target?q={Q+1}&r={R}', headers=h).json()
    assert preview['kind'] == 'territory' and preview['allowed'] and len(preview['forces']) == 2
    assert not preview['forces'][0]['militia'] and preview['forces'][1]['militia']
    incoming_before = me(c, h2)['pvp']['incoming']
    assert incoming_before == []
    b = run(c, monkeypatch, h, a, Q+1, R)
    npc = [x for x in b['state']['stacks'] if x['side'] == 'npc']
    # Real stack + militia (4 + 2*HQ1 = 6), halved: this tile is cut off from the defender's base.
    assert npc[0]['count'] == start and npc[1]['count'] == 3
    result = finish(c, h, b)
    assert result['result']['outcome'] == 'victory'
    s = result['state']
    assert any((t['q'], t['r']) == (Q+1, R) for t in s['territories'])
    assert (s['armies'][0]['q'], s['armies'][0]['r']) == (Q+1, R)
    assert s['pvp']['reports'][0]['outcome'] == 'victory' and s['pvp']['reports'][0]['role'] == 'attacker'
    d = me(c, h2)
    assert not any((t['q'], t['r']) == (Q+1, R) for t in d['territories'])
    assert d['pvp']['reports'][0]['outcome'] == 'defeat' and d['pvp']['reports'][0]['role'] == 'defender'
    left = next(x for x in d['units'] if x['id'] == u2)['count']
    assert math.ceil(start / 2) <= left <= start


def test_base_raid_takes_only_unprotected_share_and_shields_defender(client, monkeypatch):
    c = client; h, u, a, h2, u2, a2 = duel(c, monkeypatch, strong=80)
    monkeypatch.setitem(PVP, 'weaker_ratio', 0)
    enemy = player_id(c, 456); EQ, ER = home(c, h2)
    with c.factory.begin() as db:
        army = db.get(Army, a['id']); army.q, army.r = EQ - 2, ER
        db.add_all([Discovery(player_id=player_id(c, 123), world_id=1, q=EQ + dq, r=ER + dr, discovered_at=0)
                    for dq in range(-3, 2) for dr in range(-2, 3)])
        for res in db.scalars(select(Resource).where(Resource.player_id == enemy)):
            res.amount = 5000 if res.kind == 'metal' else 900
        for res in db.scalars(select(Resource).where(Resource.player_id == player_id(c, 123))):
            res.amount = 100
    b = run(c, monkeypatch, h, a, EQ, ER)
    kinds = [x['kind'] for x in b['state']['stacks'] if x['side'] == 'npc']
    assert kinds[-2:] == ['raven_line', 'raven_artillery']                  # base militia after real reserve
    result = finish(c, h, b)
    assert result['result']['outcome'] == 'victory'
    # Storage 5000 -> safe 1500; 25 % of the 3500 surplus = 875. Food/oil below the safe line stay.
    report = result['state']['pvp']['reports'][0]
    assert report['loot'] == {'metal': 875}
    assert result['state']['resources']['metal'] >= 100 + 875 - 5
    d = me(c, h2)
    assert d['resources']['metal'] <= 5000 - 875 + 50 and d['base'] == {'q': EQ, 'r': ER}
    assert d['pvp']['shield_until'] >= game.now() + PVP['raid_shield_seconds'] - 5
    again = c.get(f'/api/v1/world/target?q={EQ}&r={ER}', headers=h).json()
    assert not again['allowed'] and 'под защитой' in again['reason']


def test_defeat_leaves_holdings_and_attacker_keeps_half(client, monkeypatch):
    c = client; h, u, a, h2, u2, a2 = duel(c, monkeypatch, strong=2); Q, R = home(c, h)
    monkeypatch.setitem(PVP, 'weaker_ratio', 0)
    enemy = player_id(c, 456)
    with c.factory.begin() as db:
        db.add(MapMine(world_id=1, q=Q+1, r=R, player_id=enemy, resource='metal', rate=6, acquired_at=0))
        db.get(Unit, u2).count = 30
        army = db.get(Army, a2['id']); army.q, army.r = Q+1, R
    b = run(c, monkeypatch, h, a, Q+1, R)
    result = finish(c, h, b, action='defend')
    assert result['result']['outcome'] == 'defeat'
    assert next(x for x in result['state']['units'] if x['id'] == u)['count'] >= 1
    with c.factory() as db:
        assert db.get(MapMine, (1, Q+1, R)).player_id == enemy
        assert db.scalar(select(func.count()).select_from(PvpReport)) == 1
    assert me(c, h2)['pvp']['reports'][0]['outcome'] == 'victory'


def test_repeat_and_weaker_limits(client, monkeypatch):
    c = client; h, u, a, h2, u2, a2 = duel(c, monkeypatch, strong=10); Q, R = home(c, h)
    enemy, mine_id = player_id(c, 456), player_id(c, 123)
    with c.factory.begin() as db:
        db.add(TileOwnership(world_id=1, q=Q+1, r=R, player_id=enemy, acquired_at=0))
    assert c.get(f'/api/v1/world/target?q={Q+1}&r={R}', headers=h).json()['allowed']
    with c.factory.begin() as db:
        db.get(Unit, u).count = 200                                         # now far stronger
    weak = order(c, h, a, Q+1, R, 'attack')
    assert weak.status_code == 409 and 'слабее' in weak.json()['detail']
    with c.factory.begin() as db:
        db.get(Unit, u).count = 10
        from app.models import Battle
        for i in range(PVP['pair_limit']):
            db.add(Battle(id=f'b{i}', player_id=mine_id, unit_id=u, status='victory', seed='s',
                          balance_version='t', state={}))
            db.flush()
            db.add(PvpReport(id=f'r{i}', battle_id=f'b{i}', attacker_id=mine_id, defender_id=enemy, target='territory',
                             q=Q+1, r=R, outcome='defeat', loot={}, losses={}, created_at=game.now() - 60))
    limited = order(c, h, a, Q+1, R, 'attack')
    assert limited.status_code == 409 and 'Лимит' in limited.json()['detail']


def test_incoming_attack_is_visible_to_defender_and_paths_avoid_enemy_land(client, monkeypatch):
    c = client; h, u, a, h2, u2, a2 = duel(c, monkeypatch); Q, R = home(c, h)
    monkeypatch.setitem(PVP, 'weaker_ratio', 0)
    enemy = player_id(c, 456)
    with c.factory.begin() as db:
        db.add_all([TileOwnership(world_id=1, q=Q+1, r=R, player_id=enemy, acquired_at=0),
                    TileOwnership(world_id=1, q=Q+2, r=R, player_id=enemy, acquired_at=0)])
    preview = c.get(f'/api/v1/army/route?q={Q+3}&r={R}', headers=h).json()
    assert all(tuple(p[:2]) not in ((Q+1, R), (Q+2, R)) for p in preview['path'])
    assert order(c, h, a, Q+1, R, 'attack').status_code == 200
    incoming = me(c, h2)['pvp']['incoming']
    assert incoming and incoming[0]['target'] == 'territory' and incoming[0]['attacker'] == 'Tester'
