import logging, os, time
import httpx
from sqlalchemy import select
from .db import SessionLocal
from .models import Player, MatchNotice
from .game import settle
from . import seasons, matches
from .config import BOT_TOKEN, ENV


def season_check():
    """End the season and start a new map when it's due (disable with SEASONS_AUTO_RESET=0)."""
    if os.environ.get("SEASONS_AUTO_RESET", "1") == "0":
        return
    try:
        with SessionLocal() as db:
            if not seasons.due(db, int(time.time())):
                return
        with SessionLocal.begin() as db:
            number = seasons.rollover(db, int(time.time()))
        if number:
            logging.warning("Season rolled over: season %s started", number)
    except Exception:
        logging.exception("Season rollover failed; will retry")


def match_check():
    """Skip overdue match turns, then deliver pending Telegram notices."""
    at = int(time.time())
    try:
        with SessionLocal.begin() as db:
            matches.expire_all(db, at)
    except Exception:
        logging.exception("Match deadline check failed; will retry")
    send_notices(at)


def send_notices(at, post=None):
    """Deliver the outbox. Without a production bot token notices are just marked sent."""
    live = ENV == "production" and BOT_TOKEN and post is None
    url = os.environ.get("APP_URL", "")
    with SessionLocal.begin() as db:
        rows = list(db.scalars(select(MatchNotice).where(MatchNotice.sent_at.is_(None))
                               .order_by(MatchNotice.id).limit(30).with_for_update(skip_locked=True)))
        if not rows:
            return 0
        client = httpx.Client(base_url=f"https://api.telegram.org/bot{BOT_TOKEN}/", timeout=10) if live else None
        try:
            for n in rows:
                if at - n.created_at > 3600:   # stale: never spam an old turn
                    n.sent_at = at
                    continue
                player = db.get(Player, n.player_id)
                payload = {"chat_id": player.telegram_id, "text": n.text}
                if url.startswith("https://"):
                    payload["reply_markup"] = {"inline_keyboard": [[{"text": "Открыть партию", "web_app": {"url": url}}]]}
                try:
                    if post:
                        post(payload)
                    elif client:
                        client.post("sendMessage", json=payload)
                except httpx.HTTPError:
                    continue   # retry next tick
                n.sent_at = at
        finally:
            if client:
                client.close()
        return len(rows)


def tick():
    season_check()
    match_check()
    with SessionLocal() as db:
        ids = list(db.scalars(select(Player.id)))
    for pid in ids:
        try:
            with SessionLocal.begin() as db:
                p = db.scalar(
                    select(Player)
                    .where(Player.id == pid)
                    .with_for_update(skip_locked=True)
                )
                if p:
                    settle(db, p)
        except Exception:
            logging.exception("Worker settlement failed for player %s", pid)


if __name__ == "__main__":
    while True:
        tick()
        time.sleep(2)
