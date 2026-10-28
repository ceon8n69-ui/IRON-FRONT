from types import SimpleNamespace
from sqlalchemy import select
from app import commander, combat
from app.combat import new_battle, make_stack, resolve, preview
from app.models import Hero, Item
from conftest import post
from test_expeditions import commander as setup, create, order, home, player_id
from test_movement import at_time


def me(c, h):
    return c.get('/api/v1/player/me', headers=h).json()


def hero_of(c, uid=123):
    with c.factory() as db:
        return db.get(Hero, player_id(c, uid))


def test_levels_offers_and_picks(client, monkeypatch):
    c = client; h, u = setup(c, monkeypatch)
    view = me(c, h)['commander']
    assert view['level'] == 2 and view['xp'] == 100 and view['pending'] == 1   # tutorial gives 100 XP
    keys = [o['key'] for o in view['offers']]
    assert len(keys) == 3 and keys == [o['key'] for o in me(c, h)['commander']['offers']]   # stable on reload
    other = next(k for k in commander.SKILLS if k not in keys)
    assert post(c, '/commander/skill', {'key': other}, h).status_code == 409
    s = post(c, '/commander/skill', {'key': keys[0]}, h).json()['state']
    assert s['commander']['pending'] == 0 and s['commander']['skills'][0] == {
        **s['commander']['skills'][0], 'key': keys[0], 'rank': 1}
    assert post(c, '/commander/skill', {'key': keys[1]}, h).status_code == 409   # no points left
    with c.factory.begin() as db:
        db.get(Hero, player_id(c, 123)).xp = 1000                                # level 6 -> 4 more picks
    assert me(c, h)['commander']['pending'] == 4


def test_offers_respect_skill_slots_and_ranks():
    hero = SimpleNamespace(player_id='p', xp=99999, skills={k: 1 for k in list(commander.SKILLS)[:6]})
    assert all(k in hero.skills for k in commander.offers(hero))                # 6 skills: only upgrades
    hero.skills = {k: 3 for k in commander.SKILLS}
    assert commander.offers(hero) == []


def test_perks_merge_level_skills_artifacts_and_caps(client, monkeypatch):
    c = client; h, u = setup(c, monkeypatch)
    pid = player_id(c, 123)
    with c.factory.begin() as db:
        hero = db.get(Hero, pid); hero.xp = 1000; hero.skills = {'offense': 3, 'logistics': 2}
        db.add(Item(id='sabre', owner_id=pid, definition_id='marshal-sabre', source_id='t1', equipped=True, created_at=0))
    with c.factory() as db:
        perks = commander.perks(db, pid)
        army_only = commander.army_perks(db, pid)
    assert perks['attack'] == round(0.05 + 0.15 + 0.06, 4)          # level 6, Натиск III, sabre (tutorial module not equipped)
    assert perks['movement'] == 4 and army_only.get('plunder') is None


def test_perks_change_combat():
    me_ = lambda: make_stack('p1', 'player', 'rifles', 10, [3, 4], 'u')
    them = lambda: make_stack('n1', 'npc', 'rifles', 10, [5, 4])
    hp = lambda s: next(x for x in s['stacks'] if x['side'] == 'npc')['hp']
    plain = new_battle([me_()], [them()], [], 'seed', 'ghost', 0, {})[0]
    strong = new_battle([me_()], [them()], [], 'seed', 'ghost', 0, {'attack': 0.3})[0]
    assert hp(resolve(strong, {'action': 'attack'}, 'seed', 'ghost', 0)[0]) < hp(resolve(plain, {'action': 'attack'}, 'seed', 'ghost', 0)[0])
    lucky = new_battle([me_()], [them()], [], 'seed', 'ghost', 0, {'luck': 1.0, 'morale': 1.0})[0]
    _, events, _ = resolve(lucky, {'action': 'attack'}, 'seed', 'ghost', 0)
    assert any(e['type'] == 'luck' for e in events) and any(e['type'] == 'morale' for e in events)
    fast = new_battle([make_stack('p1', 'player', 'rifles', 10, [3, 4], 'u')], [make_stack('n1', 'npc', 'assault', 4, [5, 4])],
                      [], 'seed', 'ghost', 0, {'initiative': 3})[0]
    assert fast['order'][0] == 'p1'        # rifles 5 + 3 beat assault 6


def test_preview_brackets_the_real_hit():
    s = new_battle([make_stack('p1', 'player', 'rifles', 10, [3, 4], 'u')], [make_stack('n1', 'npc', 'rifles', 10, [5, 4])],
                   [], 'seed', 'ghost', 0, {})[0]
    info = preview(s, 'seed', 'ghost', 0)['n1']
    after, events, _ = resolve(s, {'action': 'attack', 'target': 'n1'}, 'seed', 'ghost', 0)
    dealt = next(e for e in events if e['type'] == 'attack')['damage']
    assert info['reach'] and info['damage'][0] <= dealt <= info['damage'][1]
    melee = new_battle([make_stack('p1', 'player', 'assault', 8, [3, 4], 'u')], [make_stack('n1', 'npc', 'rifles', 10, [4, 4])],
                       [], 'seed', 'ghost', 0, {})[0]
    assert preview(melee, 'seed', 'ghost', 0)['n1']['retaliation'] is not None


def test_quick_combat_finishes_a_garrison_battle(client, monkeypatch):
    c = client; h, u = setup(c, monkeypatch); a = create(c, h, u); Q, R = home(c, h)
    res = order(c, h, a, Q, R+1)
    at_time(monkeypatch, res.json()['state']['armies'][0]['orders'][0]['ready_at'] + 1)
    battle = next(b for b in me(c, h)['battles'] if b['status'] == 'active')
    assert battle['preview'] and all('damage' in v for v in battle['preview'].values())
    done = post(c, '/battles/auto', {'battle_id': battle['id']}, h)
    assert done.status_code == 200, done.text
    assert done.json()['result']['outcome'] in ('victory', 'defeat')
    replay = c.get(f"/api/v1/battles/{battle['id']}/replay", headers=h).json()
    assert replay['turns'] and all(t['command'].get('auto') for t in replay['turns'])


def test_artifacts_equip_one_per_slot(client, monkeypatch):
    c = client; h, u = setup(c, monkeypatch); pid = player_id(c, 123)
    with c.factory.begin() as db:
        for i, d in enumerate(['service-pistol', 'marshal-sabre', 'valor-medal']):
            db.add(Item(id=f'it{i}', owner_id=pid, definition_id=d, source_id=f's{i}', equipped=False, created_at=0))
    for item in ('it0', 'it2', 'it1'):
        assert post(c, '/equipment/equip', {'item_id': item, 'equipped': True}, h).status_code == 200
    eq = {i['id']: i['equipped'] for i in me(c, h)['inventory']}
    assert eq['it1'] and eq['it2'] and not eq['it0']          # sabre replaced pistol, medal kept


def test_logistics_and_first_aid(client, monkeypatch):
    c = client; h, u = setup(c, monkeypatch); a = create(c, h, u)
    with c.factory.begin() as db:
        db.get(Hero, player_id(c, 123)).skills = {'logistics': 3}
    assert me(c, h)['armies'][0]['movement_max'] == 20
    from app.game import apply_losses
    battle = SimpleNamespace(state={'perks': {'first_aid': 0.3}, 'stacks': [
        {**make_stack('p1', 'player', 'rifles', 10, [1, 1], u), 'hp': 41}]})
    with c.factory.begin() as db:
        apply_losses(db, battle, 'victory', SimpleNamespace(kind='ghost'))
        from app.models import Unit
        assert db.get(Unit, u).count == 5 + 1                  # 5 alive + floor(0.3 * 5)
