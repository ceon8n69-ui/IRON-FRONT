"""Commander growth, Heroes-style: levels from XP, a skill choice on every level, artifacts.

Levels are derived from XP, so nothing extra is stored for them. Every level
above 1 grants one pick; the three offers for the next pick are a pure function
of (player, picks made), so they never change on reload and can't be rerolled.

Perks are merged from level, skills and equipped artifacts. Army perks only work
for the army the commander leads; economy perks work everywhere.
"""
import hashlib
from fastapi import HTTPException
from sqlalchemy import select
from .models import Hero, Item
from . import equipment

LEVELS = [0, 100, 250, 450, 700, 1000, 1400, 1900, 2500, 3200, 4000, 4900, 5900, 7000, 8200]
MAX_SKILLS = 6
MAX_RANK = 3
LEVEL_PERKS = {"attack": 0.01, "defense": 0.01}     # per level above 1
ARMY_PERKS = {"attack", "defense", "ranged", "initiative", "morale", "luck", "movement", "vision", "first_aid"}
CAPS = {"attack": 0.5, "defense": 0.4, "ranged": 0.45, "initiative": 4, "morale": 0.3, "luck": 0.3,
        "movement": 8, "vision": 3, "first_aid": 0.4, "plunder": 0.6, "supply": 0.3, "engineering": 0.4}

# Fictional balance. value[rank-1] per perk.
SKILLS = {
    "offense": {"name": "Натиск", "icon": "⚔", "perks": {"attack": (0.05, 0.10, 0.15)},
                "about": "Урон ваших стеков +{attack}%"},
    "armorer": {"name": "Стойкость", "icon": "🛡", "perks": {"defense": (0.05, 0.10, 0.15)},
                "about": "Получаемый урон −{defense}%"},
    "artillery": {"name": "Артиллерия", "icon": "🎯", "perks": {"ranged": (0.10, 0.20, 0.30)},
                  "about": "Урон стрелков и орудий +{ranged}%"},
    "tactics": {"name": "Тактика", "icon": "♟", "perks": {"initiative": (1, 2, 3)},
                "about": "Инициатива ваших стеков +{initiative}"},
    "leadership": {"name": "Боевой дух", "icon": "🎺", "perks": {"morale": (0.08, 0.14, 0.20)},
                   "about": "Шанс {morale}% на дополнительное действие после хода"},
    "luck": {"name": "Удача", "icon": "🍀", "perks": {"luck": (0.08, 0.14, 0.20)},
             "about": "Шанс {luck}% на удачный удар ×1.5"},
    "logistics": {"name": "Логистика", "icon": "🧭", "perks": {"movement": (2, 4, 6)},
                  "about": "Очки хода соединения командира +{movement}"},
    "scouting": {"name": "Разведка", "icon": "🔭", "perks": {"vision": (1, 2, 3)},
                 "about": "Обзор соединения командира +{vision}"},
    "first_aid": {"name": "Полевая медицина", "icon": "✚", "perks": {"first_aid": (0.10, 0.20, 0.30)},
                  "about": "После боя возвращается {first_aid}% павших"},
    "plunder": {"name": "Мародёрство", "icon": "💰", "perks": {"plunder": (0.15, 0.30, 0.45)},
                "about": "Трофеи с карты, моря и налётов +{plunder}%"},
    "supply": {"name": "Снабжение", "icon": "🏭", "perks": {"supply": (0.05, 0.10, 0.15)},
               "about": "Производство базы +{supply}%"},
    "engineering": {"name": "Инженерия", "icon": "🔧", "perks": {"engineering": (0.10, 0.20, 0.30)},
                    "about": "Строительство и улучшения быстрее на {engineering}%"},
}
PERCENT = {"attack", "defense", "ranged", "morale", "luck", "first_aid", "plunder", "supply", "engineering"}


def level(xp):
    return sum(1 for need in LEVELS if xp >= need)


def describe(key, rank):
    spec = SKILLS[key]
    values = {k: (round(v[rank - 1] * 100) if k in PERCENT else v[rank - 1]) for k, v in spec["perks"].items()}
    return spec["about"].format(**values)


def picks(hero):
    return sum((hero.skills or {}).values())


def pending(hero):
    return max(0, level(hero.xp) - 1 - picks(hero))


def offers(hero):
    """Three options for the next pick: new skills while slots remain, otherwise upgrades."""
    have = dict(hero.skills or {})
    pool = [k for k in SKILLS if have.get(k, 0) < MAX_RANK and (k in have or len(have) < MAX_SKILLS)]
    seed = f"cmd-skill-1:{hero.player_id}:{picks(hero)}"
    pool.sort(key=lambda k: hashlib.sha256(f"{seed}:{k}".encode()).hexdigest())
    return pool[:3]


def choose(db, p, key):
    hero = db.get(Hero, p.id)
    if not hero:
        raise HTTPException(409, "Сначала выберите командира")
    if not pending(hero):
        raise HTTPException(409, "Нет свободных очков навыков: побеждайте, чтобы получить уровень")
    if key not in offers(hero):
        raise HTTPException(409, "Этот навык сейчас не предлагается")
    skills = dict(hero.skills or {})
    skills[key] = skills.get(key, 0) + 1
    hero.skills = skills
    return {"skill": key, "rank": skills[key]}


def perks(db, pid):
    """All perks, capped. Callers pick army or economy ones."""
    hero = db.get(Hero, pid)
    out = {}
    if hero:
        for k, v in LEVEL_PERKS.items():
            out[k] = out.get(k, 0) + v * (level(hero.xp) - 1)
        for key, rank in (hero.skills or {}).items():
            for k, values in SKILLS.get(key, {}).get("perks", {}).items():
                out[k] = out.get(k, 0) + values[min(rank, MAX_RANK) - 1]
    items = db.scalars(select(Item).where(Item.owner_id == pid, Item.equipped.is_(True)))
    for k, v in equipment.artifact_perks(items).items():
        out[k] = out.get(k, 0) + v
    return {k: round(min(v, CAPS.get(k, v)), 4) for k, v in out.items() if v}


def army_perks(db, pid):
    return {k: v for k, v in perks(db, pid).items() if k in ARMY_PERKS}


DOCTRINE_COMBAT = {"inf_attack", "inf_defense", "veh_attack", "veh_defense", "gun_attack"}


def battle_perks(db, pid, led, at=None):
    """Perks snapshotted into a battle: the commander's (only if he leads) plus combat doctrines (always)."""
    import time
    from . import doctrines
    out = dict(army_perks(db, pid)) if led else {}
    for k, v in doctrines.effects(db, pid, at or int(time.time())).items():
        if k in DOCTRINE_COMBAT:
            out[k] = round(out.get(k, 0) + v, 4)
    return out


def perk(db, pid, key):
    return perks(db, pid).get(key, 0)


def view(db, pid):
    hero = db.get(Hero, pid)
    if not hero:
        return None
    lv = level(hero.xp)
    skills = hero.skills or {}
    return {
        "level": lv, "xp": hero.xp,
        "level_xp": LEVELS[lv - 1], "next_xp": LEVELS[lv] if lv < len(LEVELS) else None,
        "pending": pending(hero),
        "offers": [{"key": k, "name": SKILLS[k]["name"], "icon": SKILLS[k]["icon"], "rank": skills.get(k, 0) + 1,
                    "about": describe(k, skills.get(k, 0) + 1)} for k in (offers(hero) if pending(hero) else [])],
        "skills": [{"key": k, "name": SKILLS[k]["name"], "icon": SKILLS[k]["icon"], "rank": r, "about": describe(k, r)}
                   for k, r in skills.items() if k in SKILLS],
        "perks": perks(db, pid),
        "max_skills": MAX_SKILLS,
    }
