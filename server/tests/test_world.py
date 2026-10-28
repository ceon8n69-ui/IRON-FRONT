from sqlalchemy import select
from app import worldgen, bases, garrisons, objects
from app.models import Tile, Army
from conftest import login, post
from test_expeditions import commander, create, order, home
from test_movement import at_time


def test_generated_world_has_varied_terrain():
    world = worldgen.generate()
    counts = worldgen.stats()
    assert len(world) == 128 * 128 and worldgen.generate() is world      # deterministic, cached
    assert 0.3 < counts['sea'] / len(world) < 0.5
    for kind in ('lake', 'river', 'mountain', 'beach', 'forest', 'hills', 'plain', 'desert'):
        assert counts.get(kind, 0) > 50, kind
    assert all(world[(q, r)] == 'sea' for q in range(128) for r in (0, 127))   # ocean rim
    # Several separate landmasses (continents and islands).
    land = {c for c, b in world.items() if b not in ('sea', 'lake')}
    islands, seen = 0, set()
    for c in land:
        if c in seen:
            continue
        islands += 1
        stack = [c]
        while stack:
            x = stack.pop()
            if x in seen or x not in land:
                continue
            seen.add(x)
            stack.extend(worldgen._neighbours(*x))
    assert islands >= 5


def test_water_and_mountains_block_land_armies(client, monkeypatch):
    c = client; h, u = commander(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    with c.factory.begin() as db:
        db.get(Tile, (1, Q+3, R)).biome = 'sea'
        db.get(Tile, (1, Q+3, R-1)).biome = 'mountain'
        db.get(Tile, (1, Q+2, R+1)).biome = 'river'
    r = order(c, h, a, Q+3, R, 'move')
    assert r.status_code == 409 and 'флот' in r.json()['detail']
    r = order(c, h, a, Q+3, R-1, 'move')
    assert r.status_code == 409 and 'горы' in r.json()['detail']
    preview = c.get(f'/api/v1/army/route?q={Q+2}&r={R+1}', headers=h).json()
    assert preview['path'][-1][2] == 3          # fording a river costs 3


def test_bases_only_on_land_with_walkable_ring(client):
    c = client
    q, r = bases.candidates()[0]
    with c.factory.begin() as db:
        db.get(Tile, (1, q + 1, r)).biome = 'sea'
    base = c.get('/api/v1/player/me', headers=login(c, 77)).json()['base']
    assert (base['q'], base['r']) != (q, r)
    with c.factory() as db:
        ring = [db.get(Tile, (1, base['q'] + dq, base['r'] + dr)).biome for dq in range(-2, 3) for dr in range(-2, 3)
                if max(abs(dq), abs(dr), abs(dq + dr)) <= 2]
    assert not set(ring) & bases.BAD_GROUND


def test_no_land_garrisons_or_objects_on_water():
    sites = {(30, 30): 'p'}
    for q in range(40, 90):
        for r in range(40, 90):
            assert not garrisons.guarded(q, r, sites, 'lake')
            assert not garrisons.guarded(q, r, sites, 'mountain')
            assert objects.placed(q, r, sites, 'river') is None
            obj = objects.placed(q, r, sites, 'sea')
            assert obj is None or obj.get('wreck')
