"""World PvE uses the existing battle engine and persistent battle state."""
import uuid
from sqlalchemy import select
from .models import Battle, ArmyUnit, Unit, Army, ArmyOrder, Tile, TileOwnership
from .config import VERSION


def guarded(q, r):
    # Keep the first eastward expansion open; explicit nearby tutorial target.
    return (q, r) == (64, 65) or (abs(q-64)+abs(r-64)>4 and (q*7+r*11)%13 == 0)


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
