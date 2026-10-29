"""Stack growth: veterancy ranks, barracks-sized stacks, reinforcement and merging.

A stack earns experience in every battle it fights (more for a win and for the
damage it dealt). Ranks add damage and cut damage taken; the Elite rank may use
its ability twice per battle. Recruits added by reinforcement or merging dilute
the stack's experience by head count, so veterans are worth keeping alive.
"""
import math
from .config import UNITS

RANKS = [(0, "Новобранцы"), (100, "Бывалые"), (300, "Ветераны"), (700, "Элита")]
DAMAGE_PER_RANK = 0.05      # +5 % damage per rank
GUARD_PER_RANK = 0.04       # -4 % damage taken per rank
CAP_PER_LEVEL = 0.25        # stack size +25 % of the base per barracks level above 1
REFILL_PRICE = 0.6          # a reinforcement costs 60 % of a recruit's share of a new stack
REFILL_TIME = 0.5           # and half its training time


def rank(xp):
    return max(i for i, (need, _) in enumerate(RANKS) if xp >= need)


def view(unit, levels):
    r = rank(unit.xp)
    return {"xp": unit.xp, "rank": r, "rank_name": RANKS[r][1],
            "next_xp": RANKS[r + 1][0] if r + 1 < len(RANKS) else None, "cap": cap(unit.kind, levels)}


def cap(kind, levels):
    """Largest stack the base can field: barracks (shipyard for ships) level grows it."""
    spec = UNITS[kind]
    level = max(1, levels.get("shipyard" if spec.get("naval") else "barracks", 1))
    return math.ceil(spec["count"] * (1 + CAP_PER_LEVEL * (level - 1)))


def refill_cost(kind, missing, discount=0.0):
    spec = UNITS[kind]
    share = missing / spec["count"] * REFILL_PRICE * max(0.5, 1 - discount)
    return {k: max(1, math.ceil(v * share)) for k, v in spec["cost"].items()}


def refill_seconds(kind, missing):
    spec = UNITS[kind]
    return max(10, round(spec["seconds"] * REFILL_TIME * missing / spec["count"]))


def blend(xp_a, count_a, xp_b, count_b):
    """Experience after mixing two groups (recruits come with 0)."""
    total = count_a + count_b
    return (xp_a * count_a + xp_b * count_b) // total if total else 0


def battle_xp(outcome, dealt, boost=0.0):
    return round(((20 if outcome == "victory" else 8) + dealt // 4) * (1 + boost))
