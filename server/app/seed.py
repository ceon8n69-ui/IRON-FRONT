from sqlalchemy.dialects.postgresql import insert
from .db import SessionLocal
from .models import Tile
from . import worldgen


def seed():
    """Insert the generated world into an empty database (existing tiles are left alone)."""
    world = worldgen.generate()
    tiles = [{"world_id": 1, "q": q, "r": r, "biome": b} for (q, r), b in world.items()]
    with SessionLocal.begin() as db:
        for start in range(0, len(tiles), 1000):
            db.execute(insert(Tile).values(tiles[start: start + 1000]).on_conflict_do_nothing())


if __name__ == "__main__":
    seed()
