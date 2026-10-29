"""World PvE uses the existing battle engine and persistent battle state."""
import uuid
from sqlalchemy import select
from .models import Battle, ArmyUnit, Unit, Army, ArmyOrder, Tile, TileOwnership
from .config import VERSION
from . import bases


LAND_BLOCKED = {"sea", "lake", "river", "mountain"}


def guarded(q, r, sites, biome="plain"):
    """Neutral NPC garrison rule relative to nearby base sites.

    Each base has a tutorial garrison directly south (q, r+1); the rest of its
    safe zone (|dq|+|dr| <= 4) stays open, so the first eastward expansion is
    always free. Outside every safe zone a fixed coordinate pattern applies.
    """
    sites = list(sites)
    if biome == "sea":
        return pirates(q, r, sites)
    if biome in LAND_BLOCKED:
        return False
    from . import nodes
    if nodes.at(q, r, biome, sites):
        return True
    if (q, r - 1) in sites:
        return True
    if any(abs(q - b[0]) + abs(r - b[1]) <= bases.SAFE_RADIUS for b in sites):
        return False
    return (q*7 + r*11) % 13 == 0


def pirates(q, r, sites):
    """Sea raiders: open water away from every base."""
    if any(abs(q - b[0]) + abs(r - b[1]) <= bases.SAFE_RADIUS + 2 for b in sites):
        return False
    return (q * 5 + r * 13) % 29 == 0


def cleared_in(db, q, r, radius):
    from .models import ClearedSite
    return {(c.q, c.r) for c in db.scalars(select(ClearedSite).where(ClearedSite.world_id == 1,
        ClearedSite.q.between(q - radius, q + radius), ClearedSite.r.between(r - radius, r + radius)))}


def guarded_at(db, q, r):
    from .models import ClearedSite
    from . import raids
    if raids.active_at(db, q, r):
        return True
    if db.get(ClearedSite, (1, q, r)):
        return False
    tile = db.get(Tile, (1, q, r))
    return guarded(q, r, bases.near(db, q, r, bases.SAFE_RADIUS + 2), tile.biome if tile else "plain")


WATER = {"sea", "lake", "river"}


def is_water(db, q, r):
    tile = db.get(Tile, (1, q, r))
    return bool(tile and tile.biome in WATER)


def active(db, pid):
    return db.scalar(select(Battle).where(Battle.player_id==pid, Battle.status=='active'))


def fighting_units(db, army, at_sea):
    """Ships fight at sea, everyone else on land."""
    from .config import UNITS
    units=[db.get(Unit,i) for i in db.scalars(select(ArmyUnit.unit_id).where(ArmyUnit.army_id==army.id).order_by(ArmyUnit.unit_id))]
    return [u for u in units if u and u.status=='army' and bool(UNITS.get(u.kind,{}).get('naval'))==at_sea]


def begin(db, p, army, order):
    from .objects import strength, tier_definition
    from .models import Hero, Item
    from . import combat, equipment
    from .game import PLAYER_SPOTS, npc_stacks
    at_sea = is_water(db, order.q, order.r)
    units = fighting_units(db, army, at_sea)[:len(PLAYER_SPOTS)]
    if not units:
        order.status, order.result = 'blocked', ('Для морского боя нужны корабли' if at_sea else 'Нет сухопутных отрядов для боя')
        army.status = 'idle'
        return
    from . import veterancy
    stacks=[]
    for i,u in enumerate(units):
        u.status='battle'
        stacks.append(combat.make_stack(f"p{i+1}","player",u.kind,u.count,PLAYER_SPOTS[i],u.id,u.hp,veterancy.rank(u.xp)))
    tile = db.get(Tile, (1, order.q, order.r))
    from . import raids
    raid=raids.active_at(db,order.q,order.r)
    if raid:
        name,hp,xp=raids.strength(raid)
        tier={"name":name,"xp":xp,"stacks":raid.stacks}
    else:
        name,hp,xp=strength(order.q,order.r,tile.biome,bases.near(db,order.q,order.r,bases.SAFE_RADIUS+2))
        tier=tier_definition(name)
    hero=db.get(Hero,p.id)
    led=bool(army.commander)
    from . import commander
    seed=str(uuid.uuid4())
    state,_,outcome=combat.new_battle(stacks,npc_stacks(tier["stacks"]),[] if at_sea else [[3,4],[4,2],[5,5]],seed,hero.kind if led else None,0,
                                      commander.battle_perks(db,p.id,led))
    state['led']=led
    state['expedition']={'army_id':army.id,'order_id':order.id,'q':order.q,'r':order.r}
    state['npc_tier']={'name':name,'hp':hp,'xp':xp}
    state['terrain']='sea' if at_sea else tile.biome
    db.add(Battle(id=str(uuid.uuid4()),player_id=p.id,unit_id=units[0].id,status='active',
        seed=seed,balance_version=VERSION,state=state))
    order.status='complete';order.result=f'{name}: требуется победа в бою'
    army.status='idle'


def finish(db, p, battle, outcome, at):
    from .expeditions import owned, linked, discover
    from .config import EXPEDITIONS
    ctx=battle.state['expedition'];army=db.get(Army,ctx['army_id']);order=db.get(ArmyOrder,ctx['order_id'])
    db.scalar(select(Tile).where(Tile.world_id==1,Tile.q==ctx['q'],Tile.r==ctx['r']).with_for_update())
    owner=db.get(TileOwnership,(1,ctx['q'],ctx['r']))
    if battle.state.get('terrain') == 'sea':
        return _finish_sea(db, p, battle, outcome, at, ctx, army, order)
    from .expeditions import control_limit
    if outcome=='victory':
        from . import raids
        raids.defeat(db,ctx['q'],ctx['r'])
    captured=outcome=='victory' and owner is None and len(owned(db,p.id))<control_limit(db,p.id)
    if captured:
        db.add(TileOwnership(world_id=1,q=ctx['q'],r=ctx['r'],player_id=p.id,acquired_at=at))
        army.q,army.r=ctx['q'],ctx['r'];discover(db,army,at)
        order.result='Гарнизон побеждён. Территория захвачена'
    else:
        order.result='Территория уже занята или недоступна' if outcome=='victory' else 'Поражение. Соединение осталось на исходной позиции'
    from .game import battle_units
    for unit in battle_units(db,battle):
        unit.status='army'
    return captured


def _finish_sea(db, p, battle, outcome, at, ctx, army, order):
    """Sea raiders: victory clears the site for everyone and pays salvage; water is never owned."""
    from sqlalchemy.dialects.postgresql import insert
    from .models import ClearedSite
    from .objects import tier_definition
    from .game import battle_units, change
    from .expeditions import discover
    won = False
    if outcome == 'victory':
        won = db.execute(insert(ClearedSite).values(world_id=1, q=ctx['q'], r=ctx['r'], player_id=p.id, cleared_at=at)
                         .on_conflict_do_nothing().returning(ClearedSite.q)).scalar() is not None
    if won:
        from . import commander
        bonus = commander.perk(db, p.id, 'plunder')
        change(db, p, {k: round(v * (1 + bonus)) for k, v in tier_definition(battle.state['npc_tier']['name'])['loot'].items()}, 'sea_raid')
        army.q, army.r = ctx['q'], ctx['r']; discover(db, army, at)
        order.result = 'Пираты разбиты. Трофеи доставлены на базу'
    else:
        order.result = 'Пиратов уже разбил другой флот' if outcome == 'victory' else 'Поражение. Флот отступил'
    for unit in battle_units(db, battle):
        unit.status = 'army'
    return won
