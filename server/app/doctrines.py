"""Doctrines: a Polytopia-style research tree with exclusive choices.

Three branches, three tiers each. In every tier the commander picks ONE of two
doctrines; a tier needs the previous tier of the same branch. One research at
a time; it costs resources and real time. Doctrines are season-scoped.
"""
from fastapi import HTTPException
from sqlalchemy import select
from .models import Doctrine

BRANCHES = {"infantry": "Пехота", "armor": "Техника", "logistics": "Логистика"}
# key: branch, tier, name, about, effects
DOCTRINES = {
    "trenches": ("infantry", 1, "Окопы", "Пехота получает на 10 % меньше урона", {"inf_defense": 0.10}),
    "bayonets": ("infantry", 1, "Штыковой натиск", "Урон пехоты +10 %", {"inf_attack": 0.10}),
    "levy": ("infantry", 2, "Массовый призыв", "Пехота дешевле на 20 %", {"inf_cost": 0.80}),
    "veterans": ("infantry", 2, "Ветераны", "Пехота: урон +8 %, защита +5 %", {"inf_attack": 0.08, "inf_defense": 0.05}),
    "kitchens": ("infantry", 3, "Полевые кухни", "Расход провизии −30 %", {"food_upkeep": 0.70}),
    "storm_groups": ("infantry", 3, "Ударные группы", "Урон пехоты +15 %", {"inf_attack": 0.15}),
    "plating": ("armor", 1, "Бронелисты", "Техника получает на 10 % меньше урона", {"veh_defense": 0.10}),
    "engines": ("armor", 1, "Форсированные моторы", "Урон техники +10 %", {"veh_attack": 0.10}),
    "assembly": ("armor", 2, "Конвейер", "Техника готовится на 30 % быстрее", {"veh_time": 0.70}),
    "calibres": ("armor", 2, "Тяжёлые калибры", "Урон орудий и стрелковой техники +15 %", {"gun_attack": 0.15}),
    "fuel_economy": ("armor", 3, "Экономия топлива", "Расход топлива −30 %", {"fuel_upkeep": 0.70}),
    "iron_fist": ("armor", 3, "Бронированный кулак", "Урон техники +15 %", {"veh_attack": 0.15}),
    "roads": ("logistics", 1, "Дороги", "Все соединения: +2 очка хода", {"movement": 2}),
    "recon": ("logistics", 1, "Разведка боем", "Все соединения: обзор +1", {"vision": 1}),
    "depots": ("logistics", 2, "Склады", "Вместимость склада +25 %", {"storage": 1.25}),
    "factories": ("logistics", 2, "Военные заводы", "Производство базы +10 %", {"production": 1.10}),
    "front_hq": ("logistics", 3, "Штаб фронта", "Ещё одно соединение", {"armies": 1}),
    "hold": ("logistics", 3, "Удержание рубежей", "Лимит территорий +4", {"control": 4}),
}
TIER_COST = {1: ({"metal": 400, "electronics": 80}, 600), 2: ({"metal": 900, "electronics": 200}, 1800),
             3: ({"metal": 1800, "electronics": 400, "fuel": 200}, 3600)}
ADDITIVE = {"inf_defense", "inf_attack", "veh_defense", "veh_attack", "gun_attack", "movement", "vision", "armies", "control"}


def rows(db, pid):
    return list(db.scalars(select(Doctrine).where(Doctrine.player_id == pid)))


def done(db, pid, at):
    return {d.key for d in rows(db, pid) if d.ready_at <= at}


def effects(db, pid, at):
    """Merged effects of finished doctrines: additive bonuses add, multipliers multiply."""
    out = {}
    for key in done(db, pid, at):
        for k, v in DOCTRINES[key][4].items():
            out[k] = out.get(k, 0) + v if k in ADDITIVE else out.get(k, 1) * v
    return out


def effect(db, pid, key, at, default=None):
    value = effects(db, pid, at).get(key)
    return value if value is not None else (default if default is not None else (0 if key in ADDITIVE else 1))


def start(db, p, key, at, change):
    if key not in DOCTRINES:
        raise HTTPException(404, "Неизвестная доктрина")
    branch, tier, name, _, _ = DOCTRINES[key]
    mine = rows(db, p.id)
    if any(d.ready_at > at for d in mine):
        raise HTTPException(409, "Идёт другое исследование")
    have = {d.key for d in mine}
    if key in have:
        raise HTTPException(409, "Доктрина уже изучена")
    rivals = [k for k, d in DOCTRINES.items() if d[0] == branch and d[1] == tier and k != key]
    if any(k in have for k in rivals):
        raise HTTPException(409, "В этом ярусе уже выбрана другая доктрина")
    finished = {d.key for d in mine if d.ready_at <= at}
    if tier > 1 and not any(DOCTRINES[k][0] == branch and DOCTRINES[k][1] == tier - 1 for k in finished):
        raise HTTPException(409, "Сначала изучите предыдущий ярус этой ветки")
    cost, seconds = TIER_COST[tier]
    from .commander import perk
    seconds = max(60, round(seconds * (1 - perk(db, p.id, "engineering"))))
    change(db, p, {k: -v for k, v in cost.items()}, "doctrine")
    db.add(Doctrine(player_id=p.id, key=key, started_at=at, ready_at=at + seconds))
    return {"key": key, "ready_at": at + seconds}


def view(db, pid, at):
    mine = {d.key: d for d in rows(db, pid)}
    return {
        "branches": BRANCHES,
        "doctrines": [{"key": k, "branch": b, "tier": t, "name": n, "about": a,
                       "cost": TIER_COST[t][0], "seconds": TIER_COST[t][1],
                       "state": ("done" if mine[k].ready_at <= at else "research") if k in mine else "available",
                       "ready_at": mine[k].ready_at if k in mine else None}
                      for k, (b, t, n, a, _) in DOCTRINES.items()],
        "effects": effects(db, pid, at),
    }
