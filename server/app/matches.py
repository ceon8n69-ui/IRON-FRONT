"""Match rooms: lobby, seats, turns and the Telegram "your turn" outbox.

The board is match_engine state stored on the Match row. Every action locks the
row (SELECT ... FOR UPDATE), checks the client's version, applies the action,
lets AI seats play immediately, and hands the turn to the next human at once.
A turn that outlives the room's limit is ended for that player.
"""
import copy, random, secrets, uuid
from fastapi import HTTPException
from sqlalchemy import select, or_
from .models import Match, MatchSeat, MatchNotice, Player, Hero
from . import match_engine as E, match_ai as AI
from .config import FACTIONS

TURN_LIMITS = (300, 3600, 86400)
AI_NAMES = ["ИИ «Шестерня»", "ИИ «Клапан»", "ИИ «Поршень»"]
MAX_OPEN = 5   # unfinished rooms a player may sit in at once


def fail(message, code=409):
    raise HTTPException(code, message)


def _faction(db, pid):
    hero = db.get(Hero, pid)
    return hero.kind if hero and hero.kind in FACTIONS else "raven"


def _seats(db, match_id):
    return list(db.scalars(select(MatchSeat).where(MatchSeat.match_id == match_id).order_by(MatchSeat.seat)))


def _locked(db, match_id):
    m = db.scalar(select(Match).where(Match.id == match_id).with_for_update())
    if not m:
        fail("Комната не найдена", 404)
    return m


def _open_count(db, pid):
    return len(list(db.scalars(select(Match.id).join(MatchSeat, MatchSeat.match_id == Match.id)
                               .where(MatchSeat.player_id == pid, Match.status != "finished"))))


def create(db, pid, name, size, seats, turn_limit, private, vs_ai, at):
    if size not in E.SIZES or not 2 <= seats <= 4 or turn_limit not in TURN_LIMITS:
        fail("Недопустимые настройки комнаты", 422)
    if _open_count(db, pid) >= MAX_OPEN:
        fail(f"Можно участвовать максимум в {MAX_OPEN} незавершённых партиях")
    player = db.get(Player, pid)
    m = Match(id=str(uuid.uuid4()), code=secrets.token_hex(3).upper(), name=(name or "").strip()[:40] or f"Партия {player.name}"[:40],
              status="lobby", size=size, seats=seats, turn_limit=turn_limit, private=private, host_id=pid,
              version=0, created_at=at, updated_at=at)
    db.add(m); db.flush()
    db.add(MatchSeat(match_id=m.id, seat=0, player_id=pid, ai=False, name=player.name, faction=_faction(db, pid), joined_at=at))
    db.flush()
    if vs_ai:
        _start(db, m, at, fill_ai=True)
    return m


def join(db, pid, match_id, at, code=None):
    if code:
        m = db.scalar(select(Match).where(Match.code == code.strip().upper()).with_for_update())
        if not m:
            fail("Комната с таким кодом не найдена", 404)
    else:
        m = _locked(db, match_id)
        if m.private:
            fail("Это закрытая комната: войдите по коду")
    if m.status != "lobby":
        fail("Партия уже началась")
    seats = _seats(db, m.id)
    if any(s.player_id == pid for s in seats):
        return m
    if len(seats) >= m.seats:
        fail("Мест нет")
    if _open_count(db, pid) >= MAX_OPEN:
        fail(f"Можно участвовать максимум в {MAX_OPEN} незавершённых партиях")
    free = min(set(range(m.seats)) - {s.seat for s in seats})
    player = db.get(Player, pid)
    db.add(MatchSeat(match_id=m.id, seat=free, player_id=pid, ai=False, name=player.name, faction=_faction(db, pid), joined_at=at))
    m.version += 1; m.updated_at = at
    if len(seats) + 1 == m.seats:
        db.flush()
        _start(db, m, at, fill_ai=False)
    return m


def leave(db, pid, match_id, at):
    m = _locked(db, match_id)
    seat = next((s for s in _seats(db, m.id) if s.player_id == pid), None)
    if not seat:
        fail("Вы не в этой комнате")
    if m.status == "lobby":
        db.delete(seat)
        if m.host_id == pid:
            db.flush()
            db.delete(m)
        else:
            m.version += 1; m.updated_at = at
        return None
    if m.status == "active":
        return act(db, pid, match_id, {"type": "resign"}, m.version, at, forced=True)
    return None


def start(db, pid, match_id, fill_ai, at):
    m = _locked(db, match_id)
    if m.host_id != pid:
        fail("Начать партию может только создатель комнаты")
    if m.status != "lobby":
        fail("Партия уже идёт")
    if len(_seats(db, m.id)) < 2 and not fill_ai:
        fail("Нужен хотя бы один соперник: дождитесь игрока или добавьте ИИ")
    _start(db, m, at, fill_ai)
    return m


def _start(db, m, at, fill_ai):
    seats = _seats(db, m.id)
    taken = {s.faction for s in seats}
    pool = [f for f in FACTIONS if f not in taken] or list(FACTIONS)
    rng = random.Random(m.id)
    if fill_ai:
        for seat in sorted(set(range(m.seats)) - {s.seat for s in seats}):
            faction = pool.pop(rng.randrange(len(pool))) if pool else rng.choice(list(FACTIONS))
            db.add(MatchSeat(match_id=m.id, seat=seat, player_id=None, ai=True, name=AI_NAMES[seat - 1] if seat else AI_NAMES[0],
                             faction=faction, joined_at=at))
        db.flush()
        seats = _seats(db, m.id)
    m.seats = len(seats)
    m.state = E.generate(m.size, [s.seat for s in seats], m.id, {s.seat: s.faction for s in seats})
    m.status, m.turn_started_at, m.updated_at = "active", at, at
    m.version += 1
    _after_turn_change(db, m, seats, at, previous=None)


def _after_turn_change(db, m, seats, at, previous):
    """Let AI seats play, then announce the human whose turn it is (or the winner)."""
    by_seat = {s.seat: s for s in seats}
    state = m.state
    guard = 0
    while state["winner"] is None and by_seat[state["current"]].ai and guard < 16:
        state, _ = AI.play_turn(state, state["current"])
        guard += 1
    m.state = state
    if state["current"] != previous:
        m.turn_started_at = at
    if state["winner"] is not None:
        m.status, m.winner_seat = "finished", state["winner"]
        winner = by_seat[state["winner"]].name
        for s in seats:
            if s.player_id:
                text = "🏆 Победа" if s.seat == state["winner"] else f"Партия окончена: победил {winner}"
                db.add(MatchNotice(player_id=s.player_id, match_id=m.id, text=f"{text} · «{m.name}»", created_at=at))
        return
    nxt = by_seat[state["current"]]
    if nxt.player_id and state["current"] != previous and len([s for s in seats if s.player_id]) > 1:
        db.add(MatchNotice(player_id=nxt.player_id, match_id=m.id, text=f"⚔ Ваш ход в партии «{m.name}» (ход {state['turn']})", created_at=at))


def act(db, pid, match_id, action, version, at, forced=False):
    m = _locked(db, match_id)
    expire(db, m, at)
    if m.status != "active":
        fail("Партия не идёт")
    seats = _seats(db, m.id)
    me = next((s for s in seats if s.player_id == pid), None)
    if not me:
        fail("Вы не участвуете в этой партии", 403)
    if not forced and version != m.version:
        fail("Состояние обновилось: повторите действие")
    previous = m.state["current"]
    if action.get("type") == "resign" and previous != me.seat:
        state, events = _resign_out_of_turn(m.state, me.seat)
    else:
        try:
            state, events = E.apply(m.state, me.seat, action)
        except E.Illegal as exc:
            fail(str(exc))
    m.state = state
    m.version += 1
    m.updated_at = at
    _after_turn_change(db, m, seats, at, previous)
    return {"events": events}


def _resign_out_of_turn(state, seat):
    s = copy.deepcopy(state)
    events = []
    for c in s["cities"].values():
        if c["owner"] == seat:
            c["owner"], c["capital"] = None, False
    E._check_elimination(s, events)
    return s, events


def expire(db, m, at):
    """End a turn that outlived the room's limit (one skip per call)."""
    if m.status != "active" or not m.turn_started_at or at - m.turn_started_at < m.turn_limit:
        return False
    previous = m.state["current"]
    m.state, _ = E.apply(m.state, previous, {"type": "end_turn"})
    m.version += 1
    m.updated_at = at
    _after_turn_change(db, m, _seats(db, m.id), at, previous)
    return True


def view(db, pid, match_id, at):
    m = db.get(Match, match_id)
    if not m:
        fail("Комната не найдена", 404)
    seats = _seats(db, m.id)
    me = next((s for s in seats if s.player_id == pid), None)
    if m.private and not me and m.status == "lobby":
        fail("Закрытая комната", 403)
    out = summary(m, seats, pid, at)
    if m.state and (me or m.status == "finished"):
        out["board"] = E.view(m.state, me.seat if me else None)
    return out


def summary(m, seats, pid, at):
    me = next((s for s in seats if s.player_id == pid), None)
    current = m.state["current"] if m.state else None
    return {"id": m.id, "code": m.code if (me or not m.private) else None, "name": m.name, "status": m.status, "size": m.size,
            "seats_max": m.seats, "turn_limit": m.turn_limit, "private": m.private, "host": m.host_id == pid,
            "version": m.version, "my_seat": me.seat if me else None, "current": current,
            "turn": m.state["turn"] if m.state else 0, "winner": m.winner_seat,
            "deadline": (m.turn_started_at + m.turn_limit) if m.status == "active" and m.turn_started_at else None,
            "your_turn": bool(me and m.status == "active" and current == me.seat),
            "seats": [{"seat": s.seat, "name": s.name, "ai": s.ai, "faction": s.faction, "me": s.player_id == pid} for s in seats]}


def listing(db, pid, at):
    mine_ids = list(db.scalars(select(MatchSeat.match_id).where(MatchSeat.player_id == pid)))
    mine = list(db.scalars(select(Match).where(Match.id.in_(mine_ids)).order_by(Match.updated_at.desc()).limit(30))) if mine_ids else []
    open_rooms = list(db.scalars(select(Match).where(Match.status == "lobby", Match.private.is_(False),
                                                     ~Match.id.in_(mine_ids) if mine_ids else True)
                                 .order_by(Match.created_at.desc()).limit(20)))
    for m in mine:
        if m.status == "active" and m.turn_started_at and at - m.turn_started_at >= m.turn_limit:
            locked = _locked(db, m.id)
            expire(db, locked, at)
    return {"mine": [summary(m, _seats(db, m.id), pid, at) for m in mine],
            "open": [summary(m, _seats(db, m.id), pid, at) for m in open_rooms],
            "sizes": list(E.SIZES), "turn_limits": list(TURN_LIMITS)}


def expire_all(db, at):
    """Worker: skip every overdue turn."""
    ids = list(db.scalars(select(Match.id).where(Match.status == "active")))
    done = 0
    for mid in ids:
        m = db.scalar(select(Match).where(Match.id == mid).with_for_update(skip_locked=True))
        if m and expire(db, m, at):
            done += 1
    return done
