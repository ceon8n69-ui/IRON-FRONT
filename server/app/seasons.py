"""Seasons and the in-game calendar.

A season lasts two real weeks. Inside it, Heroes-style time runs fast:
one in-game day = 4 real hours (every army refills its movement points at
dawn), one in-game week = 6 days = one real day, with a weekly event.
"""
import hashlib
from sqlalchemy import select
from .models import Season

DAY = 4 * 3600
DAYS_PER_WEEK = 6
SEASON_SECONDS = 14 * 24 * 3600

# Weekly events (fictional). Effects are read by economy, training, movement and upkeep.
EVENTS = [
    {"key": "infantry", "name": "Неделя пехоты", "about": "Подготовка пехоты дешевле на 25 %",
     "effects": {"infantry_cost": 0.75}},
    {"key": "armor", "name": "Неделя брони", "about": "Техника готовится на 40 % быстрее",
     "effects": {"vehicle_time": 0.6}},
    {"key": "harvest", "name": "Неделя изобилия", "about": "Производство базы +20 %",
     "effects": {"production": 1.2}},
    {"key": "fog", "name": "Туман войны", "about": "Обзор соединений −1",
     "effects": {"army_vision": -1}},
    {"key": "mud", "name": "Распутица", "about": "Лес, холмы и броды стоят на 1 очко хода дороже",
     "effects": {"rough_cost": 1}},
    {"key": "supply", "name": "Неделя снабжения", "about": "Содержание войск вдвое дешевле",
     "effects": {"upkeep": 0.5}},
    {"key": "spoils", "name": "Неделя трофеев", "about": "Находки на карте +50 %",
     "effects": {"pickups": 1.5}},
]


def current(db):
    """The active season (the latest one), cached for the session's lifetime."""
    if "season" not in db.info:
        db.info["season"] = db.scalar(select(Season).order_by(Season.number.desc()).limit(1))
    return db.info["season"]


def calendar(season, at):
    if not season:
        return None
    elapsed = max(0, at - season.started_at)
    day_index = elapsed // DAY
    week = day_index // DAYS_PER_WEEK + 1
    return {
        "season": season.number,
        "day": day_index % DAYS_PER_WEEK + 1,
        "week": week,
        "day_index": day_index,
        "day_started_at": season.started_at + day_index * DAY,
        "next_day_at": season.started_at + (day_index + 1) * DAY,
        "ends_at": season.ends_at,
        "event": event(season, week),
    }


def event(season, week):
    roll = int(hashlib.sha256(f"week-event-1:{season.seed}:{week}".encode()).hexdigest()[:8], 16)
    return EVENTS[roll % len(EVENTS)]


def effect(db, key, at, default=1):
    """Current weekly modifier, or `default` when this week has no such effect."""
    season = current(db)
    cal = calendar(season, at)
    return cal["event"]["effects"].get(key, default) if cal else default


def day_start(db, at):
    season = current(db)
    if not season:
        return None
    return calendar(season, at)["day_started_at"]
