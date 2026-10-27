"""Initialize and verify the persistent world before accepting traffic."""
from sqlalchemy import select, func
from .db import SessionLocal
from .models import Tile
from .seed import seed


def prepare_world():
    seed()
    with SessionLocal() as db:
        count = db.scalar(select(func.count()).select_from(Tile).where(Tile.world_id == 1))
        if count != 16384 or db.get(Tile, (1, 64, 64)) is None:
            raise RuntimeError('World initialization incomplete')
    print(f'World ready: {count} tiles; staging hex 64:64 verified', flush=True)


if __name__ == '__main__':
    import os
    prepare_world()
    os.execvp('uvicorn', ['uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', os.getenv('PORT', '8000')])
