"""World PvE uses the existing battle engine and persistent battle state."""
import uuid
from sqlalchemy import select
from .models import Battle, ArmyUnit, Unit, Army, ArmyOrder, Tile, TileOwnership
from .config import VERSION
from . import bases


def guarded(q, r, sites):
    """Neutral NPC garrison rule relative to nearby base sites.

    Each base has a tutorial garrison directly south (q, r+1); the rest of its
    safe zone (|dq|+|dr| <= 4) stays open, so the first eastward expansion is
    always free. Outside every safe zone a fixed coordinate pattern applies.
    """
    sites = list(sites)
    if (q, r - 1) in sites:
        return True
    if any(abs(q - b[0]) + abs(r - b[1]) <= bases.SAFE_RADIUS for b in sites):
        return False
    return (q*7 + r*11) % 13 == 0


def guarded_at(db, q, r):
    return guarded(q, r, bases.near(db, q, r, bases.SAFE_RADIUS))


def active(db, pid):
    return db.scalar(select(Battle).where(Battle.player_id==pid, Battle.status=='active'))


def begin(db, p, army, order):
    unit_id=db.scalar(select(ArmyUnit.unit_id).where(ArmyUnit.army_id==army.id))
    unit=db.get(Unit,unit_id)
    unit.status='battle'
    db.add(Battle(id=str(uuid.uuid4()),player_id=p.id,unit_id=unit.id,status='active',
        seed=str(uuid.uuid4()),balance_version=VERSION,state={
            'turn':1,'player':{'pos':[2,4],'hp':unit.hp},
            'npc':{'pos':[6,4],'hp':55},'cover':[[3,4],[4,2],[5,5]],
            'expedition':{'army_id':army.id,'order_id':order.id,'q':order.q,'r':order.r},
        }))
    order.status='complete';order.result='Гарнизон NPC: требуется победа в бою'
    army.status='idle'


def finish(db, p, battle, outcome, at):
    from .expeditions import owned, linked, discover
    from .config import EXPEDITIONS
    ctx=battle.state['expedition'];army=db.get(Army,ctx['army_id']);order=db.get(ArmyOrder,ctx['order_id'])
    db.scalar(select(Tile).where(Tile.world_id==1,Tile.q==ctx['q'],Tile.r==ctx['r']).with_for_update())
    owner=db.get(TileOwnership,(1,ctx['q'],ctx['r']))
    captured=outcome=='victory' and owner is None and len(owned(db,p.id))<EXPEDITIONS['control_limit'] and linked(db,p.id,ctx['q'],ctx['r'])
    if captured:
        db.add(TileOwnership(world_id=1,q=ctx['q'],r=ctx['r'],player_id=p.id,acquired_at=at))
        army.q,army.r=ctx['q'],ctx['r'];discover(db,army,at)
        order.result='Гарнизон побеждён. Территория захвачена'
    else:
        order.result='Территория уже занята или недоступна' if outcome=='victory' else 'Поражение. Соединение осталось на исходной позиции'
    unit=db.get(Unit,battle.unit_id);unit.status='army';unit.hp=max(50,battle.state['player']['hp'])
    return captured
