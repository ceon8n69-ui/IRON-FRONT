from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    Index,
    text,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Player(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(BigInteger, nullable=False)
    settled_at = Column(BigInteger, nullable=False)
    revision = Column(Integer, nullable=False, default=0)


class Session(Base):
    __tablename__ = "player_sessions"
    token_hash = Column(String, primary_key=True)
    player_id = Column(ForeignKey("users.id"), nullable=False, index=True)
    expires_at = Column(BigInteger, nullable=False)


class Resource(Base):
    __tablename__ = "player_resources"
    player_id = Column(ForeignKey("users.id"), primary_key=True)
    kind = Column(String, primary_key=True)
    amount = Column(Integer, nullable=False)
    __table_args__ = (CheckConstraint("amount >= 0"),)


class Building(Base):
    __tablename__ = "player_buildings"
    id = Column(String, primary_key=True)
    player_id = Column(ForeignKey("users.id"), nullable=False, index=True)
    kind = Column(String, nullable=False)
    q = Column(Integer, nullable=False)
    r = Column(Integer, nullable=False)
    level = Column(Integer, nullable=False, default=1)
    ready_at = Column(BigInteger, nullable=False)
    status = Column(String, nullable=False)
    upgrade_ready_at = Column(BigInteger)
    __table_args__ = (
        UniqueConstraint("player_id", "q", "r"),
        CheckConstraint("level >= 1 AND level <= 10"),
    )


class Job(Base):
    __tablename__ = "production_jobs"
    id = Column(String, primary_key=True)
    player_id = Column(ForeignKey("users.id"), nullable=False, index=True)
    kind = Column(String, nullable=False)
    ready_at = Column(BigInteger, nullable=False)
    status = Column(String, nullable=False)


class Unit(Base):
    __tablename__ = "player_units"
    id = Column(String, primary_key=True)
    player_id = Column(ForeignKey("users.id"), nullable=False, index=True)
    kind = Column(String, nullable=False)
    hp = Column(Integer, nullable=False, default=100)      # health % of the top member
    count = Column(Integer, nullable=False, default=10, server_default="10")
    status = Column(String, nullable=False, default="reserve")
    __table_args__ = (CheckConstraint("hp >= 0 AND hp <= 100"),
                      CheckConstraint("count >= 1", name="ck_player_units_count"))


class Hero(Base):
    __tablename__ = "player_heroes"
    player_id = Column(ForeignKey("users.id"), primary_key=True)
    kind = Column(String, nullable=False)
    xp = Column(Integer, nullable=False, default=0)


class Item(Base):
    __tablename__ = "equipment_instances"
    id = Column(String, primary_key=True)
    owner_id = Column(ForeignKey("users.id"), nullable=False, index=True)
    definition_id = Column(String, nullable=False)
    source_id = Column(String, unique=True, nullable=False)
    equipped = Column(Boolean, nullable=False, default=False)
    created_at = Column(BigInteger, nullable=False)


class Ownership(Base):
    __tablename__ = "item_ownership_history"
    id = Column(String, primary_key=True)
    item_id = Column(ForeignKey("equipment_instances.id"), nullable=False, index=True)
    owner_id = Column(ForeignKey("users.id"), nullable=False)
    reason = Column(String, nullable=False)
    created_at = Column(BigInteger, nullable=False)


class Battle(Base):
    __tablename__ = "battles"
    id = Column(String, primary_key=True)
    player_id = Column(ForeignKey("users.id"), nullable=False, index=True)
    unit_id = Column(ForeignKey("player_units.id"), nullable=False)
    status = Column(String, nullable=False)
    seed = Column(String, nullable=False)
    balance_version = Column(String, nullable=False)
    state = Column(JSON, nullable=False)


class BattleTurn(Base):
    __tablename__ = "battle_turns"
    battle_id = Column(ForeignKey("battles.id"), primary_key=True)
    turn = Column(Integer, primary_key=True)
    command = Column(JSON, nullable=False)
    events = Column(JSON, nullable=False)


class Reward(Base):
    __tablename__ = "mission_rewards"
    player_id = Column(ForeignKey("users.id"), primary_key=True)
    mission = Column(String, primary_key=True)
    battle_id = Column(ForeignKey("battles.id"), nullable=False)


class Ledger(Base):
    __tablename__ = "resource_transactions"
    id = Column(String, primary_key=True)
    player_id = Column(ForeignKey("users.id"), nullable=False, index=True)
    kind = Column(String, nullable=False)
    delta = Column(Integer, nullable=False)
    after = Column(Integer, nullable=False)
    operation = Column(String, nullable=False)
    created_at = Column(BigInteger, nullable=False)
    __table_args__ = (CheckConstraint("after >= 0"),)


class Command(Base):
    __tablename__ = "idempotency_records"
    player_id = Column(ForeignKey("users.id"), primary_key=True)
    key = Column(String(100), primary_key=True)
    fingerprint = Column(String, nullable=False)
    result = Column(JSON, nullable=False)


class Event(Base):
    __tablename__ = "player_events"
    player_id = Column(ForeignKey("users.id"), primary_key=True)
    revision = Column(Integer, primary_key=True)
    kind = Column(String, nullable=False)
    created_at = Column(BigInteger, nullable=False)


class Tile(Base):
    __tablename__ = "hex_tiles"
    world_id = Column(Integer, primary_key=True, default=1)
    q = Column(Integer, primary_key=True)
    r = Column(Integer, primary_key=True)
    biome = Column(String, nullable=False)
    __table_args__ = (CheckConstraint("q >= 0 AND q < 128 AND r >= 0 AND r < 128"),)


class Army(Base):
    __tablename__ = "armies"
    id = Column(String, primary_key=True)
    player_id = Column(ForeignKey("users.id"), nullable=False, unique=True)
    world_id = Column(Integer, nullable=False, default=1)
    q = Column(Integer, nullable=False)
    r = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="idle")
    movement = Column(Integer, nullable=False, server_default="12")
    movement_at = Column(BigInteger, nullable=False, server_default="0")
    __table_args__ = (
        ForeignKeyConstraint(["world_id", "q", "r"], ["hex_tiles.world_id", "hex_tiles.q", "hex_tiles.r"]),
        CheckConstraint("status IN ('idle', 'moving')"),
        CheckConstraint("movement >= 0", name="ck_armies_movement"),
    )


class ArmyUnit(Base):
    __tablename__ = "army_units"
    army_id = Column(ForeignKey("armies.id"), primary_key=True)
    unit_id = Column(ForeignKey("player_units.id"), primary_key=True, unique=True)


class ArmyOrder(Base):
    __tablename__ = "army_orders"
    id = Column(String, primary_key=True)
    army_id = Column(ForeignKey("armies.id"), nullable=False, index=True)
    world_id = Column(Integer, nullable=False, default=1)
    from_q = Column(Integer, nullable=False)
    from_r = Column(Integer, nullable=False)
    q = Column(Integer, nullable=False)
    r = Column(Integer, nullable=False)
    action = Column(String, nullable=False)
    status = Column(String, nullable=False)
    started_at = Column(BigInteger, nullable=False)
    ready_at = Column(BigInteger, nullable=False, index=True)
    finished_at = Column(BigInteger)
    result = Column(String)
    path = Column(JSON)          # [[q, r, arrive_at], ...] excluding the start hex
    __table_args__ = (
        ForeignKeyConstraint(["world_id", "q", "r"], ["hex_tiles.world_id", "hex_tiles.q", "hex_tiles.r"]),
        CheckConstraint("action IN ('move', 'capture')"),
        CheckConstraint("status IN ('moving', 'complete', 'blocked')"),
        CheckConstraint("ready_at > started_at"),
        Index("uq_army_active_order", "army_id", unique=True, postgresql_where=text("status = 'moving'")),
    )


class TileOwnership(Base):
    __tablename__ = "tile_ownership"
    world_id = Column(Integer, primary_key=True)
    q = Column(Integer, primary_key=True)
    r = Column(Integer, primary_key=True)
    player_id = Column(ForeignKey("users.id"), nullable=False, index=True)
    acquired_at = Column(BigInteger, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(["world_id", "q", "r"], ["hex_tiles.world_id", "hex_tiles.q", "hex_tiles.r"]),
        CheckConstraint("NOT (q = 64 AND r = 64)"),
    )


class Discovery(Base):
    __tablename__ = "fog_of_war"
    player_id = Column(ForeignKey("users.id"), primary_key=True)
    world_id = Column(Integer, primary_key=True)
    q = Column(Integer, primary_key=True)
    r = Column(Integer, primary_key=True)
    discovered_at = Column(BigInteger, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(["world_id", "q", "r"], ["hex_tiles.world_id", "hex_tiles.q", "hex_tiles.r"]),
    )


class WorldBase(Base):
    __tablename__ = "player_bases"
    player_id = Column(ForeignKey("users.id"), primary_key=True)
    world_id = Column(Integer, nullable=False, default=1)
    q = Column(Integer, nullable=False)
    r = Column(Integer, nullable=False)
    created_at = Column(BigInteger, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(["world_id", "q", "r"], ["hex_tiles.world_id", "hex_tiles.q", "hex_tiles.r"]),
        UniqueConstraint("world_id", "q", "r", name="uq_player_bases_site"),
        CheckConstraint("NOT (q = 64 AND r = 64)", name="ck_player_bases_not_staging"),
    )


class MapPickup(Base):
    """One-time adventure-map pickup (resource pile or chest); first claim wins."""
    __tablename__ = "map_pickups"
    world_id = Column(Integer, primary_key=True)
    q = Column(Integer, primary_key=True)
    r = Column(Integer, primary_key=True)
    kind = Column(String, nullable=False)
    player_id = Column(ForeignKey("users.id"), nullable=False, index=True)
    taken_at = Column(BigInteger, nullable=False)
    choice = Column(String)
    __table_args__ = (
        ForeignKeyConstraint(["world_id", "q", "r"], ["hex_tiles.world_id", "hex_tiles.q", "hex_tiles.r"]),
        CheckConstraint("kind IN ('pile', 'chest')", name="ck_map_pickups_kind"),
        CheckConstraint("choice IS NULL OR choice IN ('resources', 'xp')", name="ck_map_pickups_choice"),
    )


class MapMine(Base):
    __tablename__ = "map_mines"
    world_id = Column(Integer, primary_key=True)
    q = Column(Integer, primary_key=True)
    r = Column(Integer, primary_key=True)
    player_id = Column(ForeignKey("users.id"), nullable=False, index=True)
    resource = Column(String, nullable=False)
    rate = Column(Integer, nullable=False)
    acquired_at = Column(BigInteger, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(["world_id", "q", "r"], ["hex_tiles.world_id", "hex_tiles.q", "hex_tiles.r"]),
        CheckConstraint("rate > 0", name="ck_map_mines_rate"),
    )


class BiomeBackup(Base):
    """Pre-v2 terrain kept by migration a2c4e6f8b0d1 so the world change can be reverted."""
    __tablename__ = "hex_tiles_biome_v1"
    world_id = Column(Integer, primary_key=True)
    q = Column(Integer, primary_key=True)
    r = Column(Integer, primary_key=True)
    biome = Column(String, nullable=False)


class ClearedSite(Base):
    """A defeated sea raider site; stays clear for everyone (no territory on water)."""
    __tablename__ = "map_cleared"
    world_id = Column(Integer, primary_key=True)
    q = Column(Integer, primary_key=True)
    r = Column(Integer, primary_key=True)
    player_id = Column(ForeignKey("users.id"), nullable=False)
    cleared_at = Column(BigInteger, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(["world_id", "q", "r"], ["hex_tiles.world_id", "hex_tiles.q", "hex_tiles.r"]),
    )
