"""Persistent adjacent-hex expeditions. Caller holds the player's row lock."""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from .models import Army, ArmyUnit, ArmyOrder, Tile, TileOwnership, Discovery, Unit, Hero, Reward
from .config import EXPEDITIONS as RULES
from .combat import distance
from . import garrisons


def fail(reason):
    raise HTTPException(409, reason)


def owned(db, pid):
    return list(db.scalars(select(TileOwnership).where(TileOwnership.player_id == pid)))


def linked(db, pid, q, r):
    return distance(RULES['home'], [q, r]) == 1 or any(
        distance([t.q, t.r], [q, r]) == 1 for t in owned(db, pid))


def visible(db, pid, q, r):
    hero = db.get(Hero, pid)
    vision = 4 if hero and hero.kind == 'valkyrie' else 3
    if distance(RULES['home'], [q, r]) <= vision:
        return True
    army = db.scalar(select(Army).where(Army.player_id == pid))
    return bool(army and distance([army.q, army.r], [q, r]) <= RULES['army_vision'])


def discover(db, army, at):
    # No arbitrary client coordinates; only actual server-side army position.
    radius = RULES['army_vision']
    tiles = db.scalars(select(Tile).where(Tile.world_id == 1,
        Tile.q.between(army.q-radius,army.q+radius), Tile.r.between(army.r-radius,army.r+radius)))
    values = [dict(player_id=army.player_id, world_id=1,q=t.q,r=t.r,discovered_at=at)
              for t in tiles if distance([army.q,army.r],[t.q,t.r]) <= radius]
    if values:
        db.execute(insert(Discovery).values(values).on_conflict_do_nothing())


def settle_orders(db, p, at):
    army = db.scalar(select(Army).where(Army.player_id == p.id))
    if not army or army.status != 'moving':
        return False
    order = db.scalar(select(ArmyOrder).where(ArmyOrder.army_id == army.id, ArmyOrder.status == 'moving'))
    if not order or order.ready_at > at:
        return False
    # Lock the existing world tile even if no ownership row exists yet.
    # All capture paths use player -> tile order; never lock another player.
    tile = db.scalar(select(Tile).where(Tile.world_id == 1, Tile.q == order.q, Tile.r == order.r).with_for_update())
    owner = db.get(TileOwnership, (1,order.q,order.r))
    reason = None
    if owner and owner.player_id != p.id:
        reason = 'Территорию занял другой игрок. Армия осталась на исходной позиции.'
    elif order.action == 'capture':
        if owner:
            reason = 'Территория уже под вашим контролем.'
        elif len(owned(db,p.id)) >= RULES['control_limit']:
            reason = 'Достигнут лимит контроля.'
        elif not linked(db,p.id,order.q,order.r):
            reason = 'Нет связи с подконтрольной территорией.'
        elif not garrisons.guarded(order.q,order.r):
            db.add(TileOwnership(world_id=1,q=tile.q,r=tile.r,player_id=p.id,acquired_at=at))
    if not reason and not owner and garrisons.guarded(order.q,order.r):
        # Both movement and capture must engage a neutral garrison.
        garrisons.begin(db,p,army,order)
        order.finished_at=at
        db.flush()
        return True
    if reason:
        order.status, order.result = 'blocked', reason
    else:
        army.q, army.r = order.q, order.r
        order.status = 'complete'
        order.result = 'Территория захвачена' if order.action == 'capture' else 'Армия прибыла'
        discover(db, army, at)
    order.finished_at = at
    army.status = 'idle'
    db.flush()
    return True


def dispatch(db, p, op, data, at, uid, change):
    if not db.get(Reward,(p.id,'first-patrol')):
        fail('Сначала завершите учебную PvE-операцию')
    if op == 'army_create':
        if db.scalar(select(Army).where(Army.player_id == p.id)):
            fail('В первом этапе доступно одно соединение')
        unit = db.get(Unit,data['unit_id'])
        if not unit or unit.player_id != p.id or unit.status != 'reserve' or unit.hp <= 0:
            fail('Отряд недоступен')
        if not db.get(Tile,(1,*RULES['home'])):
            fail('Мировая карта ещё не готова')
        army = Army(id=uid(),player_id=p.id,world_id=1,q=64,r=64,status='idle')
        db.add(army);db.flush()
        db.add(ArmyUnit(army_id=army.id,unit_id=unit.id));unit.status='army'
        discover(db,army,at)
        return {'id':army.id}
    if garrisons.active(db,p.id):
        fail('Сначала завершите текущий бой')
    army = db.get(Army,data['army_id'])
    if not army or army.player_id != p.id:
        raise HTTPException(404,'Соединение не найдено')
    if army.status != 'idle':
        fail('Дождитесь завершения текущего похода')
    q,r=data['q'],data['r']
    if distance([army.q,army.r],[q,r]) != 1:
        fail('Приказ доступен только для соседнего гекса')
    tile = db.get(Tile,(1,q,r))
    if not tile or not visible(db,p.id,q,r):
        fail('Гекс недоступен для приказа')
    owner = db.get(TileOwnership,(1,q,r))
    if owner and owner.player_id != p.id:
        fail('Вход на чужую территорию пока недоступен: PvP не включён')
    if data['action'] == 'capture' or (not owner and garrisons.guarded(q,r)):
        if [q,r] == RULES['home']:
            fail('Стартовый пункт нельзя захватить')
        if owner:
            fail('Территория уже принадлежит вам')
        if len(owned(db,p.id)) >= RULES['control_limit']:
            fail('Достигнут лимит контроля')
        if not linked(db,p.id,q,r):
            fail('Захват требует связи с вашей территорией или стартовым пунктом')
    change(db,p,{'fuel':-RULES['fuel']},'army_march')
    order=ArmyOrder(id=uid(),army_id=army.id,world_id=1,from_q=army.q,from_r=army.r,
        q=q,r=r,action=data['action'],status='moving',started_at=at,ready_at=at+RULES['seconds'])
    db.add(order);army.status='moving'
    return {'id':order.id}


def state(db,pid):
    army=db.scalar(select(Army).where(Army.player_id == pid))
    armies=[]
    if army:
        orders=list(db.scalars(select(ArmyOrder).where(ArmyOrder.army_id == army.id).order_by(ArmyOrder.started_at.desc(),ArmyOrder.id).limit(10)))
        armies=[{'id':army.id,'q':army.q,'r':army.r,'status':army.status,
            'unit_ids':list(db.scalars(select(ArmyUnit.unit_id).where(ArmyUnit.army_id==army.id))),
            'orders':[{k:getattr(o,k) for k in ('id','q','r','from_q','from_r','action','status','started_at','ready_at','finished_at','result')} for o in orders]}]
    territories=[]
    for t in owned(db,pid):
        tile=db.get(Tile,(1,t.q,t.r))
        territories.append({'q':t.q,'r':t.r,'biome':tile.biome,'yield':RULES['territory_yield'].get(tile.biome,{}),'acquired_at':t.acquired_at})
    return {'armies':armies,'territories':territories}
