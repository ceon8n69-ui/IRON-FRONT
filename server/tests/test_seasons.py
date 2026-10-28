from sqlalchemy import select, func
from app import seasons, nodes, garrisons, objects, game
from app.models import (Season, SeasonResult, Player, Unit, Building, TileOwnership, Tile, Hero, Resource,
                        Army, Battle, Item)
from app.config import INITIAL
from conftest import post, login
from test_expeditions import commander, create, order, home, player_id
from test_movement import at_time


def me(c, h):
    return c.get('/api/v1/player/me', headers=h).json()


def test_capital_is_a_guarded_node_at_the_centre():
    assert nodes.at(64, 64, 'plain', {}) == 'capital'
    assert garrisons.guarded(64, 64, {}, 'plain')
    name, hp, xp = objects.strength(64, 64, 'plain', {})
    assert name == nodes.CAPITAL_TIER['name'] and xp == 400 and hp > objects.strength(0, 0, 'plain', {})[1]
    assert all(nodes.at(64 + dq, 64 + dr, 'plain', {}) in (None, 'capital') for dq in range(-3, 4) for dr in range(-3, 4)
               if max(abs(dq), abs(dr), abs(dq + dr)) <= 3)


def test_victory_points_from_supplied_nodes_and_battles(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    res = order(c, h, a, Q, R+1)                          # tutorial garrison: +10 VP
    at_time(monkeypatch, res.json()['state']['armies'][0]['orders'][0]['ready_at'] + 1)
    from test_pvp import finish
    battle = next(b for b in me(c, h)['battles'] if b['status'] == 'active')
    with c.factory.begin() as db:
        db.get(Unit, u).count = 40
    assert finish(c, h, battle)['result']['outcome'] == 'victory'
    assert me(c, h)['vp'] == 10
    monkeypatch.setattr(nodes, 'at', lambda q, r, biome, sites: 'plant' if (q, r) == (Q+1, R) else None)
    with c.factory.begin() as db:
        db.add(TileOwnership(world_id=1, q=Q+1, r=R, player_id=player_id(c, 123), acquired_at=game.now()))
    at_time(monkeypatch, game.now() + 10 * 60 + 2)
    assert 10 + 8 <= me(c, h)['vp'] <= 10 + 10


def test_leaderboard_ranks_commanders(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); h2, u2 = commander(c, monkeypatch, 456)
    with c.factory.begin() as db:
        db.get(Player, player_id(c, 456)).vp = 500
        db.get(Player, player_id(c, 123)).vp = 120
    board = c.get('/api/v1/season', headers=h).json()
    assert [r['vp'] for r in board['top']] == [500, 120] and board['top'][1]['me']
    assert board['me'] == {'rank': 2, 'vp': 120}
    assert board['calendar']['season'] == 1 and board['rules']['capital_vp_per_hour'] == 300


def test_rollover_archives_results_and_starts_a_fresh_map(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); h2, u2 = commander(c, monkeypatch, 456)
    a = create(c, h, u); Q, R = home(c, h)
    with c.factory.begin() as db:
        db.add(TileOwnership(world_id=1, q=Q+1, r=R, player_id=player_id(c, 123), acquired_at=0))
        db.get(Player, player_id(c, 123)).vp = 300
        db.get(Player, player_id(c, 456)).vp = 900
        db.get(Hero, player_id(c, 123)).xp = 2000
        season = db.get(Season, 1); season.ends_at = game.now() - 1
    with c.factory() as db:
        assert seasons.due(db, game.now())
    with c.factory.begin() as db:
        assert seasons.rollover(db, game.now(), seed='season-test-2') == 2
    with c.factory.begin() as db:                          # second call is a no-op
        assert seasons.rollover(db, game.now()) is None
    with c.factory() as db:
        old, new = db.get(Season, 1), db.get(Season, 2)
        assert old.status == 'finished' and [t['vp'] for t in old.results['top']] == [900, 300]
        assert new.status == 'active' and new.ends_at - new.started_at == seasons.SEASON_SECONDS
        ranks = {r.player_id: (r.rank, r.title) for r in db.scalars(select(SeasonResult))}
        assert ranks[player_id(c, 456)] == (1, 'Маршал сезона')
        assert db.scalar(select(func.count()).select_from(TileOwnership)) == 0
        assert db.scalar(select(func.count()).select_from(Army)) == 0
        assert db.scalar(select(func.count()).select_from(Battle)) == 0
        biomes = {t.biome for t in db.scalars(select(Tile))}
        assert len(biomes) > 3                               # the all-plain test world was regenerated
        capital = [db.get(Tile, (1, 64 + dq, 64 + dr)).biome for dq in (-1, 0, 1) for dr in (-1, 0, 1)]
        assert all(b not in ('sea', 'lake', 'river', 'mountain') for b in capital)
    s = me(c, h)
    assert s['vp'] == 0 and s['resources'] == INITIAL and s['territories'] == [] and s['armies'] == []
    assert s['first_victory'] and s['commander']['level'] == 1 and s['commander']['skills'] == []
    kinds = sorted(x['kind'] for x in s['units'])
    assert kinds == ['raven_line', 'raven_scouts']
    assert {b['kind'] for b in s['buildings']} == {'hq', 'power', 'barracks', 'quarry', 'farm'}
    assert s['base'] is not None and s['calendar']['season'] == 2 and s['pvp']['shield_until'] > game.now()
    assert post(c, '/army/create', {'unit_id': s['units'][0]['id']}, h).status_code == 200   # straight back into play
    board = c.get('/api/v1/season', headers=h).json()
    assert board['last']['season'] == 1 and board['last']['top'][0]['vp'] == 900
    assert board['medals'] == [{'season': 1, 'rank': 2, 'title': 'Генерал сезона', 'vp': 300}]
