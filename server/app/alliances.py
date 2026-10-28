"""Alliances: up to five commanders, joined by an invite code.

Allies can't attack each other, may march through each other's land and see
each other's holdings as friendly. The season table ranks alliances by the sum
of their members' victory points. Alliances outlive seasons.
"""
import re, secrets, time
from fastapi import HTTPException
from sqlalchemy import select, func
from .models import Alliance, Player

MAX_MEMBERS = 5
NAME = re.compile(r"^[\w .\-«»]{3,24}$", re.UNICODE)
TAG = re.compile(r"^[\w]{2,5}$", re.UNICODE)


def fail(message, code=409):
    raise HTTPException(code, message)


def allied(db, a_id, b_id):
    if not a_id or not b_id or a_id == b_id:
        return a_id == b_id and a_id is not None
    a, b = db.get(Player, a_id), db.get(Player, b_id)
    return bool(a and b and a.alliance_id and a.alliance_id == b.alliance_id)


def ally_ids(db, pid):
    me = db.get(Player, pid)
    if not me or not me.alliance_id:
        return set()
    return set(db.scalars(select(Player.id).where(Player.alliance_id == me.alliance_id, Player.id != pid)))


def members(db, alliance_id):
    return list(db.scalars(select(Player).where(Player.alliance_id == alliance_id).order_by(Player.created_at, Player.id)))


def create(db, p, name, tag):
    if p.alliance_id:
        fail("Вы уже в альянсе")
    name, tag = name.strip(), tag.strip().upper()
    if not NAME.match(name):
        fail("Название: 3–24 символа (буквы, цифры, пробел, точка, дефис)", 422)
    if not TAG.match(tag):
        fail("Тег: 2–5 букв или цифр", 422)
    if db.scalar(select(Alliance).where(func.upper(Alliance.tag) == tag)):
        fail("Такой тег уже занят")
    alliance = Alliance(id=secrets.token_hex(8), name=name, tag=tag, code=secrets.token_urlsafe(6)[:8].upper(),
                        owner_id=p.id, created_at=int(time.time()))
    db.add(alliance)
    db.flush()
    p.alliance_id = alliance.id
    return {"alliance_id": alliance.id}


def join(db, p, code):
    if p.alliance_id:
        fail("Сначала покиньте текущий альянс")
    alliance = db.scalar(select(Alliance).where(Alliance.code == code.strip().upper()).with_for_update())
    if not alliance:
        fail("Код приглашения не найден", 404)
    if len(members(db, alliance.id)) >= MAX_MEMBERS:
        fail(f"В альянсе уже {MAX_MEMBERS} командиров")
    p.alliance_id = alliance.id
    return {"alliance_id": alliance.id}


def leave(db, p):
    if not p.alliance_id:
        fail("Вы не в альянсе")
    alliance = db.scalar(select(Alliance).where(Alliance.id == p.alliance_id).with_for_update())
    p.alliance_id = None
    db.flush()
    rest = members(db, alliance.id)
    if not rest:
        db.delete(alliance)
    elif alliance.owner_id == p.id:
        alliance.owner_id = rest[0].id          # the longest-serving member takes over
    return {"left": True}


def kick(db, p, player_id):
    alliance = db.get(Alliance, p.alliance_id) if p.alliance_id else None
    if not alliance or alliance.owner_id != p.id:
        fail("Исключать может только глава альянса", 403)
    if player_id == p.id:
        fail("Чтобы уйти самому, нажмите «Покинуть»")
    # Never lock another player's row here; the member flag is a single-column update.
    target = db.get(Player, player_id)
    if not target or target.alliance_id != alliance.id:
        fail("Командир не в вашем альянсе", 404)
    target.alliance_id = None
    return {"kicked": player_id}


def view(db, pid):
    me = db.get(Player, pid)
    if not me or not me.alliance_id:
        return None
    alliance = db.get(Alliance, me.alliance_id)
    from .models import Hero
    people = members(db, alliance.id)
    return {"id": alliance.id, "name": alliance.name, "tag": alliance.tag, "code": alliance.code,
            "owner": alliance.owner_id == pid, "max": MAX_MEMBERS,
            "members": [{"id": m.id, "name": m.name, "vp": m.vp, "hero": (db.get(Hero, m.id).kind if db.get(Hero, m.id) else None),
                         "owner": m.id == alliance.owner_id, "me": m.id == pid} for m in people],
            "vp": sum(m.vp for m in people)}


def ranking(db, limit=10):
    rows = db.execute(select(Alliance.name, Alliance.tag, func.sum(Player.vp), func.count(Player.id))
                      .join(Player, Player.alliance_id == Alliance.id)
                      .group_by(Alliance.id).order_by(func.sum(Player.vp).desc(), Alliance.created_at).limit(limit))
    return [{"rank": i + 1, "name": n, "tag": t, "vp": int(v or 0), "members": c} for i, (n, t, v, c) in enumerate(rows)]
