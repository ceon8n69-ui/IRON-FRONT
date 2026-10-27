"""Versioned server-owned item definitions and deterministic garrison loot."""
import hashlib

DEFINITIONS = {
    'field-module': {'name':'Полевой модуль','rarity':'uncommon','damage_bonus':0.03},
    'garrison-module-v1': {'name':'Трофейный модуль','rarity':'uncommon','damage_bonus':0.03},
    'precision-module-v1': {'name':'Модуль точности','rarity':'rare','damage_bonus':0.04},
    'vanguard-module-v1': {'name':'Модуль «Авангард»','rarity':'epic','damage_bonus':0.05},
}
for definition in DEFINITIONS.values():
    definition['image']='/art/equipment/field-module-v1.webp'


def loot(seed):
    roll=int(hashlib.sha256(f'gar-loot-v1:{seed}'.encode()).hexdigest()[:8],16)%100
    return ('garrison-module-v1' if roll<70 else 'precision-module-v1' if roll<95 else 'vanguard-module-v1'),roll


def damage_bonus(items):
    return min(.05,max((DEFINITIONS.get(i.definition_id,{}).get('damage_bonus',0) for i in items if i.equipped),default=0))
