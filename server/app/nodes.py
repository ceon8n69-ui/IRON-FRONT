"""Strategic nodes: rare, heavily guarded hexes worth fighting over.

Placement is a pure function of coordinates (like garrisons and map objects).
A node is captured like any guarded territory (win the battle, own the tile)
and only works while supplied (see app.logistics).
"""
import hashlib
from . import bases

KINDS = {
    "oil_field": {"name": "Нефтяная вышка", "yield": {"oil": 10}, "vision": 0,
                  "about": "+10 нефти в минуту, пока узел снабжается"},
    "plant": {"name": "Завод электроники", "yield": {"electronics": 3}, "vision": 0,
              "about": "+3 электроники в минуту, пока узел снабжается"},
    "radar": {"name": "Радарная станция", "yield": {}, "vision": 4,
              "about": "Видит на 4 гекса вокруг, пока узел снабжается"},
}
ORDER = ["oil_field", "plant", "radar"]
CAPITAL = (64, 64)
KINDS["capital"] = {"name": "Столица", "yield": {"metal": 8, "oil": 4, "electronics": 2}, "vision": 3,
                    "about": "Главная цель сезона: 5 очков победы в минуту, доход и обзор, пока Столица снабжается"}
VP_PER_MINUTE = {"oil_field": 1, "plant": 1, "radar": 1, "capital": 5}
CAPITAL_TIER = {"name": "Гвардия Столицы", "xp": 400,
                "stacks": [["rifles", 20], ["assault", 12], ["artillery", 6], ["armor", 4], ["scouts", 10]]}
TIER = {"name": "Укрепрайон", "xp": 180,
        "stacks": [["rifles", 12], ["assault", 8], ["artillery", 3], ["armor", 2]]}
DENSITY = 14            # per mille of eligible land hexes
CLEARANCE = bases.SAFE_RADIUS + 2   # same window every caller passes as nearby sites
NO_NODE = {"sea", "lake", "river", "mountain"}


def _roll(q, r):
    return int(hashlib.sha256(f"iron-node-1:{q}:{r}".encode()).hexdigest()[:8], 16)


def at(q, r, biome, sites):
    """Node kind at a hex or None. `sites` = nearby base sites."""
    if (q, r) == CAPITAL:
        return "capital"
    if biome in NO_NODE:
        return None
    if any(abs(q - b[0]) + abs(r - b[1]) <= CLEARANCE for b in sites):
        return None
    roll = _roll(q, r)
    if roll % 1000 >= DENSITY or max(abs(q - CAPITAL[0]), abs(r - CAPITAL[1]), abs(q + r - sum(CAPITAL))) <= 3:
        return None
    return ORDER[(roll // 1000) % len(ORDER)]


def tier(kind):
    return CAPITAL_TIER if kind == "capital" else TIER


def view(kind):
    return {"kind": kind, **KINDS[kind]} if kind else None
