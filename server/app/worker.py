import logging, os, time
from sqlalchemy import select
from .db import SessionLocal
from .models import Player
from .game import settle
from . import seasons


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


def tick():
    season_check()
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
