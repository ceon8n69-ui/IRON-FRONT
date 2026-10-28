"""Level-based building effects. Pure functions over the BUILDINGS baseline."""
from .config import BUILDINGS, MAX_LEVEL, BASE_STORAGE, GROWTH


def upgrade_cost(kind, level):
    """Cost to raise a building from `level` to `level + 1`."""
    base = BUILDINGS[kind]["cost"] or {"metal": 100}
    return {k: round(v * GROWTH["cost"] ** level) for k, v in base.items()}


def upgrade_seconds(kind, level):
    return min(4 * 3600, round(max(BUILDINGS[kind]["seconds"], 30) * GROWTH["time"] ** level))


def output(kind, level):
    factor = 1 + GROWTH["output"] * (level - 1)
    return {k: round(v * factor) for k, v in BUILDINGS[kind].get("output", {}).items()}


def inputs(kind, level):
    factor = 1 + GROWTH["output"] * (level - 1)
    return {k: round(v * factor) for k, v in BUILDINGS[kind].get("input", {}).items()}


def power(kind, level):
    base = BUILDINGS[kind]["power"]
    growth = GROWTH["power_gen"] if base > 0 else GROWTH["power_use"]
    return round(base * (1 + growth * (level - 1)))


def storage(levels):
    """levels: mapping kind -> active level (0 when absent)."""
    return BASE_STORAGE + BUILDINGS["warehouse"]["storage"] * levels.get("warehouse", 0)


def vision_bonus(levels):
    level = levels.get("watchtower", 0)
    return 0 if not level else 1 if level < 6 else 2


def repair_rate(levels):
    return BUILDINGS["repair"]["repair"] * levels.get("repair", 0)


def max_level(kind, hq_level):
    return MAX_LEVEL if kind == "hq" else min(MAX_LEVEL, hq_level)


def describe(kind, level):
    """Effects shown to the client for the current and next level."""
    def at(n):
        return {"output": output(kind, n), "input": inputs(kind, n), "power": power(kind, n),
                "storage": BUILDINGS[kind].get("storage", 0) * n,
                "vision": vision_bonus({kind: n}) if kind == "watchtower" else 0,
                "repair": repair_rate({kind: n}) if kind == "repair" else 0}
    return {"current": at(level), "next": at(level + 1) if level < MAX_LEVEL else None}
