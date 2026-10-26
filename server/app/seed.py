import hashlib
from sqlalchemy.dialects.postgresql import insert
from .db import SessionLocal
from .models import Tile


def seed():
    tiles = []
    for q in range(128):
        for r in range(128):
            # Coherent patches rather than independent tile noise.
            n = int(
                hashlib.sha256(f"iron-1:{q//5}:{r//5}".encode()).hexdigest()[:8], 16
            )
            tiles.append(
                {
                    "world_id": 1,
                    "q": q,
                    "r": r,
                    "biome": ["plain", "forest", "hills", "desert"][n % 4],
                }
            )
    with SessionLocal.begin() as db:
        for start in range(0, len(tiles), 1000):
            db.execute(
                insert(Tile)
                .values(tiles[start : start + 1000])
                .on_conflict_do_nothing()
            )


if __name__ == "__main__":
    seed()
