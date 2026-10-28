"""Persistent expeditions with Heroes-style movement points and multi-hex routes.

Caller holds the player's row lock.
"""
import heapq
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from .models import Army, ArmyUnit, ArmyOrder, Tile, TileOwnership, Discovery, Unit, Hero, Reward
from .config import EXPEDITIONS as RULES
from .combat import distance
from . import garrisons, bases


def fail(reason):
    raise HTTPException(409, reason)


DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]


def movement_max(db, pid):
    hero = db.get(Hero, pid)
    return RULES['movement_max'] + (2 if hero and hero.kind == 'storm' else 0)


def refresh_movement(db, army, at):
    """Lazy real-time regeneration: +1 point per regen period, capped."""
    cap, period = movement_max(db, army.player_id), RULES['movement_regen_seconds']
    if not army.movement_at:
        army.movement_at = at
    if army.movement >= cap:
        army.movement, army.movement_at = cap, at
        return
    gained = max(0, (at - army.movement_at) // period)
    if gained:
        army.movement = min(cap, army.movement + gained)
        army.movement_at = at if army.movement >= cap else army.movement_at + gained * period


def spend_movement(db, army, cost, at):
    refresh_movement(db, army, at)
    if army.movement >= movement_max(db, army.player_id):
        army.movement_at = at  # regeneration clock starts with the first spent point
    army.movement -= cost


def route(db, p, army, target, at):
    """Cheapest path over known, passable hexes. Returns [(q, r, cost), ...] and total."""
    radius = movement_max(db, p.id) + 1
    q0, r0 = army.q, army.r
    box = lambda m: (m.world_id == 1, m.q.between(q0-radius, q0+radius), m.r.between(r0-radius, r0+radius))
    tiles = {(t.q, t.r): t.biome for t in db.scalars(select(Tile).where(*box(Tile)))}
    found = {(d.q, d.r) for d in db.scalars(select(Discovery).where(Discovery.player_id == p.id, *box(Discovery)))}
    owners = {(o.q, o.r): o.player_id for o in db.scalars(select(TileOwnership).where(*box(TileOwnership)))}
    sites = bases.near(db, q0, r0, radius + bases.SAFE_RADIUS)
    home, vision = bases.home(db, p.id), home_vision(db, p.id)

    def known(c):
        return c in found or distance(home, c) <= vision or distance((q0, r0), c) <= RULES['army_vision']

    def blocked(c, final):
        if c not in tiles or not known(c):
            return 'Маршрут проходит через неразведанную местность'
        if c in sites and sites[c] not in (None, p.id):
            return 'Это база другого командира. PvP пока не включён'
        if c in owners and owners[c] != p.id:
            return 'Вход на чужую территорию пока недоступен: PvP не включён'
        if not final and c not in owners and c not in sites and garrisons.guarded(c[0], c[1], sites):
            return 'Путь перекрыт гарнизоном NPC'
        return None

    target = tuple(target)
    reason = blocked(target, True)
    if reason:
        fail(reason)
    costs = RULES['terrain_cost']
    best, prev, heap = {(q0, r0): 0}, {}, [(0, q0, r0)]
    while heap:
        spent, q, r = heapq.heappop(heap)
        if (q, r) == target:
            break
        if spent > best.get((q, r), 1 << 30):
            continue
        for dq, dr in DIRECTIONS:
            c = (q + dq, r + dr)
            if abs(c[0]-q0) > radius or abs(c[1]-r0) > radius or blocked(c, c == target):
                continue
            total = spent + costs.get(tiles[c], 1)
            if total < best.get(c, 1 << 30):
                best[c], prev[c] = total, (q, r)
                heapq.heappush(heap, (total, c[0], c[1]))
    if target not in best:
        fail('Нет проходимого маршрута к этому гексу')
    steps, c = [], target
    while c != (q0, r0):
        steps.append((c[0], c[1], costs.get(tiles[c], 1)))
        c = prev[c]
    steps.reverse()
    return steps, best[target]


def owned(db, pid):
    return list(db.scalars(select(TileOwnership).where(TileOwnership.player_id == pid)))


def linked(db, pid, q, r):
    return distance(bases.home(db, pid), [q, r]) == 1 or any(
        distance([t.q, t.r], [q, r]) == 1 for t in owned(db, pid))


def home_vision(db, pid):
    from .models import Building
    from . import economy
    hero = db.get(Hero, pid)
    towers = [b for b in db.scalars(select(Building).where(Building.player_id == pid, Building.kind == 'watchtower'))
              if b.status == 'ready']
    bonus = economy.vision_bonus({'watchtower': towers[0].level}) if towers else 0
    return (4 if hero and hero.kind == 'valkyrie' else 3) + bonus


def visible(db, pid, q, r):
    if distance(bases.home(db, pid), [q, r]) <= home_vision(db, pid):
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
    if not army:
        return False
    refresh_movement(db, army, at)
    if army.status != 'moving':
        return False
    order = db.scalar(select(ArmyOrder).where(ArmyOrder.army_id == army.id, ArmyOrder.status == 'moving'))
    if not order:
        return False
    moved = False
    # The army walks hex by hex; it stops on the last intermediate hex reached.
    reached = [(q, r) for q, r, arrive in (order.path or [])[:-1] if arrive <= at]
    if reached and (army.q, army.r) != reached[-1]:
        army.q, army.r = reached[-1]
        discover(db, army, at)
        moved = True
    if order.ready_at > at:
        db.flush()
        return moved
    # Lock the existing world tile even if no ownership row exists yet.
    # All capture paths use player -> tile order; never lock another player.
    tile = db.scalar(select(Tile).where(Tile.world_id == 1, Tile.q == order.q, Tile.r == order.r).with_for_update())
    owner = db.get(TileOwnership, (1,order.q,order.r))
    reason = None
    is_base, base_owner = bases.at(db, order.q, order.r)
    if is_base and base_owner not in (None, p.id):
        reason = 'Это база другого командира. PvP пока не включён.'
    elif is_base and order.action == 'capture':
        reason = 'Базу нельзя захватить как территорию.'
    elif owner and owner.player_id != p.id:
        reason = 'Территорию занял другой игрок. Соединение остановилось на предыдущем гексе.'
    elif order.action == 'capture':
        if owner:
            reason = 'Территория уже под вашим контролем.'
        elif len(owned(db,p.id)) >= RULES['control_limit']:
            reason = 'Достигнут лимит контроля.'
        elif not linked(db,p.id,order.q,order.r):
            reason = 'Нет связи с подконтрольной территорией.'
        elif not garrisons.guarded_at(db,order.q,order.r):
            db.add(TileOwnership(world_id=1,q=tile.q,r=tile.r,player_id=p.id,acquired_at=at))
    if not reason and not owner and not is_base and garrisons.guarded_at(db,order.q,order.r):
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
        base = bases.ensure(db, p, at)
        army = Army(id=uid(),player_id=p.id,world_id=1,q=base.q,r=base.r,status='idle')
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
    if (q, r) == (army.q, army.r):
        fail('Соединение уже на этом гексе')
    tile = db.get(Tile,(1,q,r))
    if not tile:
        fail('Гекс недоступен для приказа')
    owner = db.get(TileOwnership,(1,q,r))
    is_base, base_owner = bases.at(db, q, r)
    if is_base and base_owner not in (None, p.id):
        fail('Это база другого командира. PvP пока не включён')
    if owner and owner.player_id != p.id:
        fail('Вход на чужую территорию пока недоступен: PvP не включён')
    steps, cost = route(db, p, army, (q, r), at)
    if data['action'] == 'capture' or (not owner and not is_base and garrisons.guarded_at(db,q,r)):
        if is_base:
            fail('Базу нельзя захватить как территорию')
        if owner:
            fail('Территория уже принадлежит вам')
        if len(owned(db,p.id)) >= RULES['control_limit']:
            fail('Достигнут лимит контроля')
        if not linked(db,p.id,q,r):
            fail('Захват требует связи с вашей территорией или базой')
    refresh_movement(db, army, at)
    if cost > army.movement:
        fail(f'Недостаточно очков хода: нужно {cost}, доступно {army.movement}')
    change(db,p,{'fuel':-RULES['fuel']*len(steps)},'army_march')
    spend_movement(db, army, cost, at)
    t, path = at, []
    for sq, sr, step_cost in steps:
        t += step_cost * RULES['step_seconds']
        path.append([sq, sr, t])
    order=ArmyOrder(id=uid(),army_id=army.id,world_id=1,from_q=army.q,from_r=army.r,
        q=q,r=r,action=data['action'],status='moving',started_at=at,ready_at=t,path=path)
    db.add(order);army.status='moving'
    return {'id':order.id}


def state(db,pid):
    army=db.scalar(select(Army).where(Army.player_id == pid))
    armies=[]
    if army:
        orders=list(db.scalars(select(ArmyOrder).where(ArmyOrder.army_id == army.id).order_by(ArmyOrder.started_at.desc(),ArmyOrder.id).limit(10)))
        cap=movement_max(db,pid);period=RULES['movement_regen_seconds']
        armies=[{'id':army.id,'q':army.q,'r':army.r,'status':army.status,
            'movement':army.movement,'movement_max':cap,
            'movement_next_at':None if army.movement>=cap else army.movement_at+period,
            'unit_ids':list(db.scalars(select(ArmyUnit.unit_id).where(ArmyUnit.army_id==army.id))),
            'orders':[{k:getattr(o,k) for k in ('id','q','r','from_q','from_r','action','status','started_at','ready_at','finished_at','result','path')} for o in orders]}]
    territories=[]
    for t in owned(db,pid):
        tile=db.get(Tile,(1,t.q,t.r))
        territories.append({'q':t.q,'r':t.r,'biome':tile.biome,'yield':RULES['territory_yield'].get(tile.biome,{}),'acquired_at':t.acquired_at})
    return {'armies':armies,'territories':territories}
