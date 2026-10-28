"""Versioned server-owned artifact definitions and deterministic loot.

Five slots, one equipped artifact per slot. Perks merge into the commander's
perks (app.commander). The pre-0.12 modules live on in the "gear" slot, and
damage_bonus() is kept for battles started before perks existed.
"""
import hashlib

SLOTS = {"weapon": "Оружие", "armor": "Броня", "badge": "Знак отличия", "gear": "Модуль", "optics": "Снаряжение"}

DEFINITIONS = {
    # gear (the original modules)
    'field-module': {'name': 'Полевой модуль', 'rarity': 'uncommon', 'slot': 'gear', 'perks': {'attack': 0.03}},
    'garrison-module-v1': {'name': 'Трофейный модуль', 'rarity': 'uncommon', 'slot': 'gear', 'perks': {'attack': 0.03}},
    'precision-module-v1': {'name': 'Модуль точности', 'rarity': 'rare', 'slot': 'gear', 'perks': {'ranged': 0.06}},
    'vanguard-module-v1': {'name': 'Модуль «Авангард»', 'rarity': 'epic', 'slot': 'gear', 'perks': {'attack': 0.05, 'initiative': 1}},
    # weapon
    'service-pistol': {'name': 'Наградной пистолет', 'rarity': 'uncommon', 'slot': 'weapon', 'perks': {'attack': 0.03}},
    'marshal-sabre': {'name': 'Сабля маршала', 'rarity': 'rare', 'slot': 'weapon', 'perks': {'attack': 0.06}},
    'field-baton': {'name': 'Жезл фельдмаршала', 'rarity': 'epic', 'slot': 'weapon', 'perks': {'attack': 0.08, 'morale': 0.05}},
    # armor
    'plated-greatcoat': {'name': 'Шинель с бронепластинами', 'rarity': 'uncommon', 'slot': 'armor', 'perks': {'defense': 0.04}},
    'veteran-cuirass': {'name': 'Кираса ветерана', 'rarity': 'rare', 'slot': 'armor', 'perks': {'defense': 0.07}},
    'bastion-armor': {'name': 'Доспех «Бастион»', 'rarity': 'epic', 'slot': 'armor', 'perks': {'defense': 0.10}},
    # badge
    'valor-medal': {'name': 'Медаль за отвагу', 'rarity': 'uncommon', 'slot': 'badge', 'perks': {'morale': 0.05}},
    'staff-badge': {'name': 'Знак штабиста', 'rarity': 'rare', 'slot': 'badge', 'perks': {'initiative': 1}},
    'fortune-order': {'name': 'Орден Фортуны', 'rarity': 'epic', 'slot': 'badge', 'perks': {'luck': 0.08, 'morale': 0.04}},
    # optics / kit
    'field-binoculars': {'name': 'Полевой бинокль', 'rarity': 'uncommon', 'slot': 'optics', 'perks': {'vision': 1}},
    'quartermaster-bag': {'name': 'Сумка интенданта', 'rarity': 'rare', 'slot': 'optics', 'perks': {'plunder': 0.12}},
    'route-atlas': {'name': 'Атлас маршрутов', 'rarity': 'epic', 'slot': 'optics', 'perks': {'movement': 2}},
}
for _key, _d in DEFINITIONS.items():
    _d['image'] = f'/art/equipment/{_key}.webp'
    _d['slot_name'] = SLOTS[_d['slot']]
    _d['damage_bonus'] = _d['perks'].get('attack', 0)   # legacy field for old clients
LOOT_VERSION = 'gar-loot-v2'
RARITY_WEIGHTS = {  # by NPC tier index: uncommon / rare / epic
    0: (80, 18, 2), 1: (62, 30, 8), 2: (45, 38, 17), 3: (25, 45, 30),
}


def loot(seed, tier=0):
    """Deterministic artifact roll from the battle seed; better tiers shift rarity up."""
    roll = int(hashlib.sha256(f'{LOOT_VERSION}:{seed}'.encode()).hexdigest()[:8], 16)
    weights = RARITY_WEIGHTS.get(tier, RARITY_WEIGHTS[0])
    r = roll % 100
    rarity = 'uncommon' if r < weights[0] else 'rare' if r < weights[0] + weights[1] else 'epic'
    pool = sorted(k for k, d in DEFINITIONS.items() if d['rarity'] == rarity and k != 'field-module')
    return pool[(roll // 100) % len(pool)], r


def artifact_perks(items):
    out = {}
    for i in items:
        d = DEFINITIONS.get(i.definition_id)
        if d and i.equipped:
            for k, v in d['perks'].items():
                out[k] = out.get(k, 0) + v
    return out


def damage_bonus(items):
    """Legacy (pre-perks) battles: best equipped attack bonus, capped at 5 %."""
    return min(.05, max((DEFINITIONS.get(i.definition_id, {}).get('perks', {}).get('attack', 0) for i in items if i.equipped), default=0))
