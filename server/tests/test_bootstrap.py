from sqlalchemy import select, func
from app import bootstrap, seed
from app.models import Tile


def test_world_bootstrap_is_complete_and_preserves_existing_tiles(client, monkeypatch):
    monkeypatch.setattr(seed, 'SessionLocal', client.factory)
    monkeypatch.setattr(bootstrap, 'SessionLocal', client.factory)
    bootstrap.prepare_world()
    with client.factory.begin() as db:
        db.get(Tile, (1,64,64)).biome = 'forest'
    bootstrap.prepare_world()
    with client.factory() as db:
        assert db.scalar(select(func.count()).select_from(Tile)) == 16384
        assert db.get(Tile, (1,64,64)).biome == 'forest'
