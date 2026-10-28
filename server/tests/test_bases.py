import concurrent.futures
import pytest
from sqlalchemy import select, func
from app import bases, garrisons
from app.combat import distance
from app.models import WorldBase, TileOwnership
from conftest import login, signed
from test_expeditions import commander, create, order, home, player_id
from test_integration import advance


def test_candidate_grid_is_spaced_and_avoids_staging():
    sites = bases.candidates()
    assert len(sites) >= 100
    assert all(distance(bases.STAGING, s) > bases.STAGING_CLEARANCE for s in sites)
    assert all(bases.MARGIN <= v < 128 - bases.MARGIN for s in sites for v in s)
    assert min(distance(a, b) for i, a in enumerate(sites) for b in sites[i+1:]) >= bases.SPACING


def test_garrison_rule_is_relative_to_each_base():
    sites = {(30, 30): 'p'}
    assert garrisons.guarded(30, 31, sites)            # tutorial garrison south
    assert not garrisons.guarded(31, 30, sites)        # first eastward hex open
    assert not any(garrisons.guarded(30+dq, 30+dr, sites)
                   for dq in range(-4, 5) for dr in range(-4, 5)
                   if abs(dq)+abs(dr) <= 4 and (dq, dr) != (0, 1))
    assert garrisons.guarded(64, 65, {bases.STAGING: None})  # legacy staging unchanged


def test_each_player_gets_distinct_persistent_base(client):
    c = client
    first = c.get('/api/v1/player/me', headers=login(c, 1)).json()['base']
    again = c.get('/api/v1/player/me', headers=login(c, 1)).json()['base']
    second = c.get('/api/v1/player/me', headers=login(c, 2)).json()['base']
    assert first == again
    assert (first['q'], first['r']) == bases.candidates()[0]
    assert distance((first['q'], first['r']), (second['q'], second['r'])) >= bases.SPACING


def test_concurrent_first_logins_never_share_a_site(client):
    c = client
    uids = list(range(1000, 1008))
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        codes = list(pool.map(lambda u: c.post('/api/v1/auth/telegram', json={'init_data': signed(u)}).status_code, uids))
    assert codes == [200] * len(uids)
    with c.factory() as db:
        rows = list(db.scalars(select(WorldBase)))
    sites = {(b.q, b.r) for b in rows}
    assert len(rows) == len(uids) == len(sites)


def test_legacy_player_without_base_is_assigned_lazily(client):
    c = client
    h = login(c, 7)
    with c.factory.begin() as db:
        db.query(WorldBase).delete()
    base = c.get('/api/v1/player/me', headers=h).json()['base']
    assert base is not None
    with c.factory() as db:
        assert db.scalar(select(func.count()).select_from(WorldBase)) == 1


def test_bases_avoid_existing_holdings(client):
    c = client
    login(c, 8)
    q, r = bases.candidates()[1]
    with c.factory.begin() as db:
        db.add(TileOwnership(world_id=1, q=q+2, r=r, player_id=player_id(c, 8), acquired_at=0))
    second = c.get('/api/v1/player/me', headers=login(c, 9)).json()['base']
    assert (second['q'], second['r']) not in (bases.candidates()[0], (q, r))


def test_world_full_returns_clear_error(client, monkeypatch):
    c = client
    monkeypatch.setattr(bases, 'candidates', lambda: [(20, 20)])
    login(c, 10)
    r = c.post('/api/v1/auth/telegram', json={'init_data': signed(11)})
    assert r.status_code == 503 and 'секторы' in r.json()['detail']


def test_world_tiles_mark_bases_and_block_foreign_base(client, monkeypatch):
    c = client
    h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    other = login(c, 456); oq, orr = home(c, other)
    tiles = c.get(f'/api/v1/world/tiles?q={Q}&r={R}&radius=1', headers=h).json()['tiles']
    own = next(t for t in tiles if (t['q'], t['r']) == (Q, R))
    assert own['home'] and own['base'] == 'self' and own['visibility'] == 'visible'
    assert next(t for t in tiles if (t['q'], t['r']) == (Q, R+1))['garrison']
    assert not next(t for t in tiles if (t['q'], t['r']) == (Q+1, R))['garrison']
    # Hidden foreign base is not disclosed.
    far = c.get(f'/api/v1/world/tiles?q={oq}&r={orr}&radius=1', headers=h).json()['tiles']
    assert next(t for t in far if (t['q'], t['r']) == (oq, orr))['base'] is None
    # Even when adjacent, a foreign base can't be entered or captured, only attacked.
    from app.models import Army
    with c.factory.begin() as db:
        army = db.get(Army, a['id']); army.q, army.r = oq - 1, orr
    near = c.get(f'/api/v1/world/tiles?q={oq}&r={orr}&radius=1', headers=h).json()['tiles']
    assert next(t for t in near if (t['q'], t['r']) == (oq, orr))['base'] == 'other'
    for action in ('move', 'capture'):
        response = order(c, h, a, oq, orr, action)
        assert response.status_code == 409 and 'атаковать' in response.json()['detail'].lower()


def test_foreign_base_appearing_mid_march_blocks_arrival(client, monkeypatch):
    c = client
    h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    assert order(c, h, a, Q+1, R, 'move').status_code == 200
    login(c, 457)
    with c.factory.begin() as db:
        base = db.get(WorldBase, player_id(c, 457)); base.q, base.r = Q+1, R
    advance(c, monkeypatch, 31)
    s = c.get('/api/v1/player/me', headers=h).json()
    assert (s['armies'][0]['q'], s['armies'][0]['r']) == (Q, R)
    assert s['armies'][0]['orders'][0]['status'] == 'blocked'
