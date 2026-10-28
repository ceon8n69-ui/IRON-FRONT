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
from . import garrisons, bases, objects, pvp, logistics


def fail(reason):
    raise HTTPException(409, reason)


DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]
TERRAIN_BLOCKED = {"sea": "нужен флот", "lake": "нужен флот", "mountain": "горы непроходимы"}
WATER = {"sea", "lake", "river"}


def has_fleet(db, army):
    from .config import UNITS
    kinds = [db.get(Unit, i).kind for i in db.scalars(select(ArmyUnit.unit_id).where(ArmyUnit.army_id == army.id))]
    return any(UNITS.get(k, {}).get("naval") for k in kinds)


def has_land(db, army):
    from .config import UNITS
    kinds = [db.get(Unit, i).kind for i in db.scalars(select(ArmyUnit.unit_id).where(ArmyUnit.army_id == army.id))]
    return any(not UNITS.get(k, {}).get("naval") for k in kinds)


def movement_max(db, pid, army=None):
    from . import commander
    hero = db.get(Hero, pid)
    from . import doctrines
    extra = commander.perk(db, pid, 'movement') if army is not None and army.commander else 0
    roads = doctrines.effect(db, pid, 'movement', _now())
    return RULES['movement_max'] + (2 if hero and hero.kind == 'storm' else 0) + int(extra) + int(roads)


def army_vision(db, army):
    from . import commander, seasons
    fog = int(seasons.effect(db, 'army_vision', _now(), 0))
    from . import doctrines
    recon = int(doctrines.effect(db, army.player_id, 'vision', _now()))
    return max(1, RULES['army_vision'] + fog + recon + (int(commander.perk(db, army.player_id, 'vision')) if army.commander else 0))


def _now():
    import time
    return int(time.time())


def control_limit(db, pid):
    from .models import Building
    hq = db.scalar(select(Building).where(Building.player_id == pid, Building.kind == 'hq'))
    level = hq.level if hq else 1
    from . import doctrines
    return min(RULES['control_cap'], RULES['control_limit'] + RULES['control_per_hq'] * (level - 1)) \
        + int(doctrines.effect(db, pid, 'control', _now()))


def refresh_movement(db, army, at):
    """Heroes-style days: every army refills its movement in full at each in-game dawn.
    Without a season (legacy data) points trickle back one per regen period."""
    from . import seasons
    cap, period = movement_max(db, army.player_id, army), RULES['movement_regen_seconds']
    dawn = seasons.day_start(db, at)
    if dawn is not None:
        if not army.movement_at or army.movement_at < dawn:
            army.movement, army.movement_at = cap, dawn
        army.movement = min(army.movement, cap)
        return
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
    from . import seasons
    refresh_movement(db, army, at)
    if seasons.day_start(db, at) is None and army.movement >= movement_max(db, army.player_id, army):
        army.movement_at = at  # legacy trickle: the clock starts with the first spent point
    army.movement -= cost


def route(db, p, army, target, at):
    """Cheapest path over known, passable hexes. Returns [(q, r, cost), ...] and total."""
    radius = movement_max(db, p.id, army) + 1
    q0, r0 = army.q, army.r
    box = lambda m: (m.world_id == 1, m.q.between(q0-radius, q0+radius), m.r.between(r0-radius, r0+radius))
    tiles = {(t.q, t.r): t.biome for t in db.scalars(select(Tile).where(*box(Tile)))}
    found = {(d.q, d.r) for d in db.scalars(select(Discovery).where(Discovery.player_id == p.id, *box(Discovery)))}
    owners = {(o.q, o.r): o.player_id for o in db.scalars(select(TileOwnership).where(*box(TileOwnership)))}
    sites = bases.near(db, q0, r0, radius + bases.SAFE_RADIUS + 2)
    home, vision = bases.home(db, p.id), home_vision(db, p.id)
    fleet = has_fleet(db, army)
    sight = army_vision(db, army)
    cleared = garrisons.cleared_in(db, q0, r0, radius)

    radar = logistics.radars(db, p.id)

    def known(c):
        return c in found or distance(home, c) <= vision or distance((q0, r0), c) <= sight \
            or any(distance((rq, rr), c) <= rv for rq, rr, rv in radar)

    water_wall = []

    def blocked(c, final):
        if c not in tiles or not known(c):
            return 'Маршрут проходит через неразведанную местность'
        hostile = (c in sites and sites[c] not in (None, p.id)) or (c in owners and owners[c] != p.id)
        if hostile and not final:
            return 'Путь проходит через чужие владения'
        terrain = tiles[c]
        if terrain in TERRAIN_BLOCKED and not (fleet and terrain in WATER):
            if terrain in WATER:
                water_wall.append(c)
            return 'Туда не пройти: ' + TERRAIN_BLOCKED[terrain]
        if not final and c not in owners and c not in sites and c not in cleared and garrisons.guarded(c[0], c[1], sites, terrain):
            return 'Путь перекрыт гарнизоном NPC'
        if not final and not hostile and objects.blocks_path(db, c, p.id, sites, terrain):
            return 'Путь перекрыт объектом карты: выберите его целью'
        return None

    target = tuple(target)
    reason = blocked(target, True)
    if reason:
        fail(reason)
    costs = dict(RULES['terrain_cost'])
    from . import seasons
    mud = seasons.effect(db, 'rough_cost', at, 0)
    if mud:
        for k in ('forest', 'hills', 'river'):
            costs[k] = costs.get(k, 1) + mud

    def step_cost(here, there):
        if fleet and there in WATER:
            cost = RULES['naval_cost']
        else:
            cost = costs.get(there, 1)
        if fleet and (here in ("sea", "lake")) != (there in ("sea", "lake")):
            cost += RULES['landing_cost']   # embarking or going ashore
        return cost
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
            total = spent + step_cost(tiles[(q, r)] if (q, r) in tiles else "plain", tiles[c])
            if total < best.get(c, 1 << 30):
                best[c], prev[c] = total, (q, r)
                heapq.heappush(heap, (total, c[0], c[1]))
    if target not in best:
        fail('Нет маршрута по суше: нужен флот' if water_wall else 'Нет проходимого маршрута к этому гексу')
    steps, c = [], target
    while c != (q0, r0):
        steps.append((c[0], c[1], step_cost(tiles[prev[c]], tiles[c])))
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
    return any(distance([a.q, a.r], [q, r]) <= army_vision(db, a) for a in armies(db, pid)) \
        or any(distance((rq, rr), (q, r)) <= rv for rq, rr, rv in logistics.radars(db, pid))


def armies(db, pid):
    return list(db.scalars(select(Army).where(Army.player_id == pid).order_by(Army.number, Army.id)))


def armies_max(db, pid):
    from .models import Building
    hq = db.scalar(select(Building).where(Building.player_id == pid, Building.kind == 'hq'))
    from . import doctrines
    return min(RULES['armies_cap'] + 1, min(RULES['armies_cap'], RULES['armies_base'] + ((hq.level if hq else 1) - 1) // 2)
               + int(doctrines.effect(db, pid, 'armies', _now())))


def in_battle(db, pid):
    """Army id currently fighting, or None (one battle at a time per commander)."""
    battle = garrisons.active(db, pid)
    return (battle.state.get('expedition') or {}).get('army_id') if battle else None


def discover(db, army, at):
    # No arbitrary client coordinates; only actual server-side army position.
    radius = army_vision(db, army)
    tiles = db.scalars(select(Tile).where(Tile.world_id == 1,
        Tile.q.between(army.q-radius,army.q+radius), Tile.r.between(army.r-radius,army.r+radius)))
    values = [dict(player_id=army.player_id, world_id=1,q=t.q,r=t.r,discovered_at=at)
              for t in tiles if distance([army.q,army.r],[t.q,t.r]) <= radius]
    if values:
        db.execute(insert(Discovery).values(values).on_conflict_do_nothing())


def settle_orders(db, p, at, change=None):
    moved = False
    for army in armies(db, p.id):
        moved = _settle_army(db, p, army, at, change) or moved
    return moved


def _settle_army(db, p, army, at, change):
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
    if garrisons.active(db, p.id) and _fights_on_arrival(db, p, order):
        # One battle at a time: this army waits on its last step until the current one ends.
        db.flush()
        return moved
    # Lock the existing world tile even if no ownership row exists yet.
    # All capture paths use player -> tile order; never lock another player.
    tile = db.scalar(select(Tile).where(Tile.world_id == 1, Tile.q == order.q, Tile.r == order.r).with_for_update())
    if order.action == 'attack':
        return _arrive_attack(db, p, army, order, at)
    owner = db.get(TileOwnership,(1,order.q,order.r))
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
        elif len(owned(db,p.id)) >= control_limit(db,p.id):
            reason = 'Достигнут лимит контроля.'
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
        found = objects.arrive(db, p, order.q, order.r, at, change) if change else None
        if found:
            order.result += '. ' + found
        discover(db, army, at)
    order.finished_at = at
    army.status = 'idle'
    db.flush()
    return True


def _fights_on_arrival(db, p, order):
    if order.action == 'attack':
        return True
    owner = db.get(TileOwnership, (1, order.q, order.r))
    is_base, _ = bases.at(db, order.q, order.r)
    return not owner and not is_base and garrisons.guarded_at(db, order.q, order.r)


def _arrive_attack(db, p, army, order, at):
    tgt = pvp.target(db, p.id, order.q, order.r)
    reason = 'Цель больше не принадлежит противнику' if not tgt else pvp.blocked_reason(db, p, tgt, at)
    if reason:
        order.status, order.result = 'blocked', reason
        army.status = 'idle'
    else:
        pvp.begin(db, p, army, order, tgt, at)
    order.finished_at = at
    db.flush()
    return True


def _order_attack(db, p, army, tile, tgt, at):
    if tile.biome in WATER:
        fail('Морские владения атаковать пока нельзя')
    if not has_land(db, army):
        fail('Нет сухопутных отрядов для боя')
    reason = pvp.blocked_reason(db, p, tgt, at)
    if reason:
        fail(reason)
    if tgt['kind'] == 'territory':
        if len(owned(db, p.id)) >= control_limit(db, p.id):
            fail('Достигнут лимит контроля: удержать территорию не получится')


def dispatch(db, p, op, data, at, uid, change):
    from .game import tutorial_done
    if not tutorial_done(db, p):
        fail('Сначала завершите учебную PvE-операцию')
    if op == 'army_create':
        unit = db.get(Unit,data['unit_id'])
        if not unit or unit.player_id != p.id or unit.status != 'reserve' or unit.hp <= 0:
            fail('Отряд недоступен')
        mine = armies(db, p.id)
        limit = armies_max(db, p.id)
        if len(mine) >= limit:
            fail(f'Максимум соединений: {limit}. Улучшайте штаб, чтобы командовать большим числом')
        base = bases.ensure(db, p, at)
        number = min(set(range(1, limit + 2)) - {a.number for a in mine})
        army = Army(id=uid(),player_id=p.id,world_id=1,q=base.q,r=base.r,status='idle',number=number,
                    commander=not any(a.commander for a in mine),movement=RULES['movement_max'],movement_at=at)
        db.add(army);db.flush()
        db.add(ArmyUnit(army_id=army.id,unit_id=unit.id));unit.status='army'
        discover(db,army,at)
        return {'id':army.id}
    if op in ('army_assign', 'army_release', 'army_disband', 'army_lead'):
        return compose(db, p, op, data)
    army = db.get(Army,data['army_id'])
    if not army or army.player_id != p.id:
        raise HTTPException(404,'Соединение не найдено')
    if in_battle(db, p.id) == army.id:
        fail('Сначала завершите текущий бой')
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
    tgt = pvp.target(db, p.id, q, r)
    if tgt and data['action'] != 'attack':
        fail('Это владения другого командира: выберите «Атаковать»')
    if not tgt and data['action'] == 'attack':
        fail('Здесь нет противника')
    steps, cost = route(db, p, army, (q, r), at)
    if tgt:
        _order_attack(db, p, army, tile, tgt, at)
    at_water = tile.biome in WATER
    if data['action'] == 'capture' and at_water:
        fail('Водные гексы нельзя захватить: выберите «Переместить»')
    if not tgt and not owner and not is_base and garrisons.guarded_at(db, q, r):
        if at_water and tile.biome == 'sea' and not has_fleet(db, army):
            fail('Для морского боя нужны корабли')
        if not at_water and not has_land(db, army):
            fail('Нет сухопутных отрядов для боя')
    if not tgt and not at_water and (data['action'] == 'capture' or (not owner and not is_base and garrisons.guarded_at(db,q,r))):
        if is_base:
            fail('Базу нельзя захватить как территорию')
        if owner:
            fail('Территория уже принадлежит вам')
        if len(owned(db,p.id)) >= control_limit(db,p.id):
            fail('Достигнут лимит контроля')
    refresh_movement(db, army, at)
    if cost > army.movement:
        fail(f'Недостаточно очков хода: нужно {cost}, доступно {army.movement}')
    change(db,p,{'fuel':-RULES['fuel']*len(steps)},'army_march')
    spend_movement(db, army, cost, at)
    if tgt:
        p.shield_until = 0   # a voluntary attack ends your own protection
    t, path = at, []
    for sq, sr, step_cost in steps:
        t += step_cost * RULES['step_seconds']
        path.append([sq, sr, t])
    order=ArmyOrder(id=uid(),army_id=army.id,world_id=1,from_q=army.q,from_r=army.r,
        q=q,r=r,action=data['action'],status='moving',started_at=at,ready_at=t,path=path)
    db.add(order);army.status='moving'
    return {'id':order.id}


def compose(db, p, op, data):
    """Pick up or leave stacks, disband, hand over the commander: only on the base, Heroes-style."""
    from .config import ARMY_STACKS
    mine = armies(db, p.id)
    if not mine:
        fail('Сначала сформируйте соединение')
    army = next((a for a in mine if a.id == data.get('army_id')), None) if data.get('army_id') else next(
        (a for a in mine if a.commander), mine[0])
    if not army:
        raise HTTPException(404, 'Соединение не найдено')
    home = bases.home(db, p.id)
    at_home = lambda a: a.status == 'idle' and [a.q, a.r] == home
    if not at_home(army) or in_battle(db, p.id) == army.id:
        fail('Состав меняется только на базе: верните соединение домой')
    members = list(db.scalars(select(ArmyUnit).where(ArmyUnit.army_id == army.id)))
    if op == 'army_lead':
        current = next((a for a in mine if a.commander), None)
        if current and current.id != army.id:
            if not at_home(current):
                fail('Командир в походе: верните его соединение на базу')
            current.commander = False
            db.flush()
        army.commander = True
        db.flush()
        return {'army_id': army.id}
    if op == 'army_disband':
        if army.commander and len(mine) > 1:
            fail('Сначала передайте командира другому соединению')
        for m in members:
            db.get(Unit, m.unit_id).status = 'reserve'
            db.delete(m)
        db.flush()
        for o in db.scalars(select(ArmyOrder).where(ArmyOrder.army_id == army.id)):
            db.delete(o)
        db.flush()
        db.delete(army)
        db.flush()
        return {'army_id': army.id}
    unit = db.get(Unit, data['unit_id'])
    if not unit or unit.player_id != p.id:
        raise HTTPException(404, 'Отряд не найден')
    if op == 'army_assign':
        if unit.status != 'reserve':
            fail('Отряд не в резерве')
        if len(members) >= ARMY_STACKS:
            fail(f'В соединении максимум {ARMY_STACKS} стеков')
        db.add(ArmyUnit(army_id=army.id, unit_id=unit.id)); unit.status = 'army'
    else:
        link = next((m for m in members if m.unit_id == unit.id), None)
        if not link:
            fail('Отряд не в этом соединении')
        if len(members) == 1:
            fail('В соединении должен остаться хотя бы один стек: или распустите его')
        db.delete(link); unit.status = 'reserve'
    db.flush()
    return {'army_id': army.id, 'unit_id': unit.id}


def state(db,pid):
    views=[]
    period=RULES['movement_regen_seconds']
    from . import seasons
    cal=seasons.calendar(seasons.current(db),_now())
    dawn_next=cal['next_day_at'] if cal else None
    fighting=in_battle(db,pid)
    for army in armies(db,pid):
        cap=movement_max(db,pid,army)
        orders=list(db.scalars(select(ArmyOrder).where(ArmyOrder.army_id == army.id).order_by(ArmyOrder.started_at.desc(),ArmyOrder.id).limit(10)))
        views.append({'id':army.id,'number':army.number,'commander':army.commander,'in_battle':fighting==army.id,
            'q':army.q,'r':army.r,'status':army.status,'vision':army_vision(db,army),
            'movement':army.movement,'movement_max':cap,
            'movement_next_at':None if army.movement>=cap else (dawn_next or army.movement_at+period),
            'unit_ids':list(db.scalars(select(ArmyUnit.unit_id).where(ArmyUnit.army_id==army.id))),
            'orders':[{k:getattr(o,k) for k in ('id','q','r','from_q','from_r','action','status','started_at','ready_at','finished_at','result','path')} for o in orders]})
    territories=[]
    supply=logistics.supplied(db,pid)
    for t in owned(db,pid):
        tile=db.get(Tile,(1,t.q,t.r))
        node=logistics.node_kind(db,t.q,t.r)
        produce=dict(RULES['territory_yield'].get(tile.biome,{}))
        if node:
            from . import nodes
            for k,v in nodes.KINDS[node]['yield'].items():
                produce[k]=produce.get(k,0)+v
        territories.append({'q':t.q,'r':t.r,'biome':tile.biome,'yield':produce,'acquired_at':t.acquired_at,
                            'supplied':(t.q,t.r) in supply,'node':node})
    return {'armies':views,'armies_max':armies_max(db,pid),'territories':territories}
