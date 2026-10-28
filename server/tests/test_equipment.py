from types import SimpleNamespace
from app.equipment import loot, DEFINITIONS, damage_bonus
from app.combat import resolve, new_battle, make_stack


def test_loot_reproducible_and_all_tiers_reachable():
    rolls=[loot(str(i)) for i in range(1000)]
    assert rolls==[loot(str(i)) for i in range(1000)]
    assert {kind for kind,_ in rolls}==set(DEFINITIONS)-{'field-module'}
    for kind,roll in rolls:
        assert 0<=roll<100
        assert kind==('garrison-module-v1' if roll<70 else 'precision-module-v1' if roll<95 else 'vanguard-module-v1')


def test_equipment_bonus_is_capped_and_changes_combat_damage():
    items=[SimpleNamespace(definition_id=k,equipped=True) for k in DEFINITIONS]
    assert damage_bonus(items)==.05
    assert damage_bonus([SimpleNamespace(definition_id='unknown',equipped=True)])==0
    for item in items:item.equipped=False
    assert damage_bonus(items)==0
    state=new_battle([make_stack('p1','player','rifles',10,[3,4],'u')],[make_stack('n1','npc','rifles',10,[5,4])],[],'same-seed','ghost',0)[0]
    npc=lambda s:next(x for x in s['stacks'] if x['side']=='npc')['hp']
    baseline=resolve(state,{'action':'attack'},'same-seed','ghost',0)[0]
    boosted=resolve(state,{'action':'attack'},'same-seed','ghost',.05)[0]
    assert npc(boosted)<npc(baseline)
