"""Seeded procedural world for the 128x128 hex map.

Layered value noise gives elevation and moisture. An edge falloff plus a few
continent "plates" make a sea with islands of varied size; mountains rise on
ridges, lakes fill basins, and rivers walk downhill from high ground to the
nearest water. Deterministic for a given seed, pure Python, ~0.3 s.
"""
import hashlib
import math
from functools import lru_cache

SIZE = 128
SEED = "iron-world-2"
WATER = {"sea", "lake", "river"}
IMPASSABLE_LAND = {"sea", "lake", "mountain"}
NEIGHBOURS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]


def _h(*parts):
    return int(hashlib.blake2b(":".join(map(str, parts)).encode(), digest_size=8).hexdigest(), 16) / 2**64


def _lattice(seed, octave, cell):
    n = cell + 2
    return [[_h(seed, octave, i, j) for j in range(n)] for i in range(n)]


def _fbm(seed, octaves=5, base_cell=32):
    """Fractal value noise sampled on axial (q, r) mapped to a square grid."""
    out = [[0.0] * SIZE for _ in range(SIZE)]
    amp, total = 1.0, 0.0
    cell = base_cell
    for o in range(octaves):
        grid = _lattice(seed, o, SIZE // cell + 2)
        for q in range(SIZE):
            fx = q / cell
            ix, tx = int(fx), fx - int(fx)
            sx = tx * tx * (3 - 2 * tx)
            for r in range(SIZE):
                fy = r / cell
                iy, ty = int(fy), fy - int(fy)
                sy = ty * ty * (3 - 2 * ty)
                a = grid[ix][iy] + (grid[ix + 1][iy] - grid[ix][iy]) * sx
                b = grid[ix][iy + 1] + (grid[ix + 1][iy + 1] - grid[ix][iy + 1]) * sx
                out[q][r] += (a + (b - a) * sy) * amp
        total += amp
        amp *= 0.5
        cell = max(2, cell // 2)
    return [[v / total for v in row] for row in out]


def _neighbours(q, r):
    for dq, dr in NEIGHBOURS:
        a, b = q + dq, r + dr
        if 0 <= a < SIZE and 0 <= b < SIZE:
            yield a, b


@lru_cache(maxsize=4)
def generate(seed=SEED):
    """Return {(q, r): biome}."""
    elev = _fbm(seed + ":elev", 5, 24)
    wet = _fbm(seed + ":wet", 4, 20)
    ridge = _fbm(seed + ":ridge", 3, 12)
    # Many soft plates of different size: big continents, mid islands, islets.
    plates = [(_h(seed, "p", i, 0) * 108 + 10, _h(seed, "p", i, 1) * 108 + 10,
               6 + _h(seed, "p", i, 2) ** 2 * 26) for i in range(16)]
    height = {}
    for q in range(SIZE):
        for r in range(SIZE):
            lift = max(math.exp(-((q - px) ** 2 + (r - py) ** 2) / (2 * pr * pr)) for px, py, pr in plates)
            falloff = min(1.0, min(q, r, SIZE - 1 - q, SIZE - 1 - r) / 10)
            height[(q, r)] = (0.6 * elev[q][r] + 0.4 * lift + 0.18 * ridge[q][r] * lift) * (0.25 + 0.75 * falloff)
    # Percentile thresholds keep proportions stable for any seed.
    ordered = sorted(height.values())
    pct = lambda p: ordered[min(len(ordered) - 1, int(p * len(ordered)))]
    sea_level, hill_level, peak_level = pct(0.40), pct(0.80), pct(0.94)
    biome = {}
    for (q, r), e in height.items():
        m = wet[q][r]
        if e < sea_level:
            biome[(q, r)] = "sea"
        elif e >= peak_level:
            biome[(q, r)] = "mountain"
        elif e >= hill_level:
            biome[(q, r)] = "hills"
        elif m > 0.53:
            biome[(q, r)] = "forest"
        elif m < 0.42 and _h(seed, "dry", q // 10, r // 10) < 0.45:
            biome[(q, r)] = "desert"
        else:
            biome[(q, r)] = "plain"
    # Water not connected to the map edge is an inland lake.
    ocean, stack = set(), [(q, r) for q in range(SIZE) for r in (0, SIZE - 1)] + [(q, r) for r in range(SIZE) for q in (0, SIZE - 1)]
    while stack:
        c = stack.pop()
        if c in ocean or biome[c] != "sea":
            continue
        ocean.add(c)
        stack.extend(_neighbours(*c))
    for c, b in biome.items():
        if b == "sea" and c not in ocean:
            biome[c] = "lake"
    # Lakes: a dozen small basins in wet lowland.
    lowland = [c for c, b in biome.items() if b in ("plain", "forest") and wet[c[0]][c[1]] > 0.5
               and min(c[0], c[1], SIZE - 1 - c[0], SIZE - 1 - c[1]) > 6]
    for i, c in enumerate(sorted(lowland, key=lambda c: _h(seed, "lk", *c))[:12]):
        radius = 1 + int(_h(seed, "lr", i) * 2)
        for q in range(c[0] - radius, c[0] + radius + 1):
            for r in range(c[1] - radius, c[1] + radius + 1):
                if (q, r) in biome and max(abs(q - c[0]), abs(r - c[1]), abs(q + r - c[0] - c[1])) <= radius \
                        and biome[(q, r)] in ("plain", "forest"):
                    biome[(q, r)] = "lake"
    # Islets: scattered specks of land in open sea.
    for i in range(40):
        q, r = int(_h(seed, "is", i, 0) * 108) + 10, int(_h(seed, "is", i, 1) * 108) + 10
        if biome[(q, r)] == "sea" and all(biome[n] == "sea" for n in _neighbours(q, r)):
            biome[(q, r)] = "forest" if i % 3 == 0 else "plain"
            for n in list(_neighbours(q, r))[: 1 + i % 3]:
                biome[n] = "plain"
    # Beaches: low land touching the sea.
    for (q, r), b in list(biome.items()):
        if b in ("plain", "forest", "desert") and (height[(q, r)] < sea_level + 0.025 or _h(seed, "bch", q, r) < 0.3) \
                and any(biome[n] == "sea" for n in _neighbours(q, r)):
            biome[(q, r)] = "beach"
    # Rivers: start on high ground, walk downhill to water.
    sources = sorted((c for c, e in height.items() if hill_level <= e < peak_level),
                     key=lambda c: _h(seed, "src", *c))[:40]
    for c in sources:
        path, seen = [], set()
        cur = c
        for _ in range(70):
            seen.add(cur)
            if biome[cur] in ("sea", "lake") or (biome[cur] == "river" and cur != c):
                break
            path.append(cur)
            options = [n for n in _neighbours(*cur) if n not in seen]
            if not options:
                break
            cur = min(options, key=lambda n: (height[n] + _h(seed, "jit", *n) * 0.01))
        if len(path) >= 5 and biome[cur] in ("sea", "lake", "river"):
            for p in path[1:]:
                if biome[p] != "mountain":
                    biome[p] = "river"
    return biome


def stats(seed=SEED):
    counts = {}
    for b in generate(seed).values():
        counts[b] = counts.get(b, 0) + 1
    return counts
