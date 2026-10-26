import logging, time
from sqlalchemy import select
from .db import SessionLocal
from .models import Player
from .game import settle


def tick():
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
