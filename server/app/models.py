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
    shield_until = Column(BigInteger, nullable=False, default=0, server_default="0")
    upkeep_at = Column(BigInteger, nullable=False, default=0, server_default="0")
    vp = Column(Integer, nullable=False, default=0, server_default="0")
    tutorial_done = Column(Boolean, nullable=False, default=False, server_default="false")
    alliance_id = Column(String, ForeignKey("alliances.id", use_alter=True, name="fk_users_alliance"), index=True)


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
    skills = Column(JSON, nullable=False, default=dict, server_default="{}")


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
    player_id = Column(ForeignKey("users.id"), nullable=False, index=True)
    world_id = Column(Integer, nullable=False, default=1)
    q = Column(Integer, nullable=False)
    r = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="idle")
    number = Column(Integer, nullable=False, default=1, server_default="1")
    commander = Column(Boolean, nullable=False, default=False, server_default="false")
    movement = Column(Integer, nullable=False, server_default="12")
    movement_at = Column(BigInteger, nullable=False, server_default="0")
    __table_args__ = (
        ForeignKeyConstraint(["world_id", "q", "r"], ["hex_tiles.world_id", "hex_tiles.q", "hex_tiles.r"]),
        CheckConstraint("status IN ('idle', 'moving')"),
        CheckConstraint("movement >= 0", name="ck_armies_movement"),
        UniqueConstraint("player_id", "number", name="uq_armies_player_number"),
        Index("uq_armies_commander", "player_id", unique=True, postgresql_where=text("commander")),
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
        CheckConstraint("action IN ('move', 'capture', 'attack')", name="army_orders_action_check"),
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
        CheckConstraint("kind IN ('pile', 'chest', 'ruin')", name="ck_map_pickups_kind"),
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


class PvpReport(Base):
    """One finished PvP battle, visible to both sides; also drives repeat-attack limits."""
    __tablename__ = "pvp_reports"
    id = Column(String, primary_key=True)
    battle_id = Column(ForeignKey("battles.id"), nullable=False, unique=True)
    attacker_id = Column(ForeignKey("users.id"), nullable=False)
    defender_id = Column(ForeignKey("users.id"), nullable=False)
    target = Column(String, nullable=False)
    q = Column(Integer, nullable=False)
    r = Column(Integer, nullable=False)
    outcome = Column(String, nullable=False)
    loot = Column(JSON, nullable=False)
    losses = Column(JSON, nullable=False)
    created_at = Column(BigInteger, nullable=False)
    __table_args__ = (
        CheckConstraint("target IN ('base', 'territory', 'mine')", name="ck_pvp_reports_target"),
        CheckConstraint("outcome IN ('victory', 'defeat')", name="ck_pvp_reports_outcome"),
        Index("ix_pvp_reports_pair", "attacker_id", "defender_id", "created_at"),
        Index("ix_pvp_reports_defender", "defender_id", "created_at"),
    )


class Season(Base):
    """A two-week world. The latest row is the active season."""
    __tablename__ = "seasons"
    number = Column(Integer, primary_key=True)
    seed = Column(String, nullable=False)
    started_at = Column(BigInteger, nullable=False)
    ends_at = Column(BigInteger, nullable=False)
    status = Column(String, nullable=False, default="active")
    results = Column(JSON)
    __table_args__ = (CheckConstraint("status IN ('active', 'finished')", name="ck_seasons_status"),
                      CheckConstraint("ends_at > started_at", name="ck_seasons_span"))


class SeasonResult(Base):
    """A commander's final standing in a finished season; kept across resets."""
    __tablename__ = "season_results"
    season = Column(ForeignKey("seasons.number"), primary_key=True)
    player_id = Column(ForeignKey("users.id"), primary_key=True)
    rank = Column(Integer, nullable=False)
    vp = Column(Integer, nullable=False)
    title = Column(String)
    hero = Column(String)
    name = Column(String(100), nullable=False)


class Doctrine(Base):
    """A researched (or researching) doctrine; season-scoped."""
    __tablename__ = "player_doctrines"
    player_id = Column(ForeignKey("users.id"), primary_key=True)
    key = Column(String, primary_key=True)
    started_at = Column(BigInteger, nullable=False)
    ready_at = Column(BigInteger, nullable=False)


class CampHire(Base):
    """One mercenary stack per camp per in-game week; first hire wins."""
    __tablename__ = "camp_hires"
    world_id = Column(Integer, primary_key=True)
    q = Column(Integer, primary_key=True)
    r = Column(Integer, primary_key=True)
    season = Column(Integer, primary_key=True)
    week = Column(Integer, primary_key=True)
    player_id = Column(ForeignKey("users.id"), nullable=False)
    kind = Column(String, nullable=False)
    hired_at = Column(BigInteger, nullable=False)


class Alliance(Base):
    __tablename__ = "alliances"
    id = Column(String, primary_key=True)
    name = Column(String(24), nullable=False)
    tag = Column(String(5), nullable=False, unique=True)
    code = Column(String(8), nullable=False, unique=True)
    owner_id = Column(String, nullable=False)
    created_at = Column(BigInteger, nullable=False)


class Raid(Base):
    """A marauder band camped next to a commander's land; burns the target at strikes_at unless beaten."""
    __tablename__ = "raids"
    id = Column(String, primary_key=True)
    player_id = Column(ForeignKey("users.id"), nullable=False, index=True)
    q = Column(Integer, nullable=False)
    r = Column(Integer, nullable=False)
    target_q = Column(Integer, nullable=False)
    target_r = Column(Integer, nullable=False)
    season = Column(Integer, nullable=False)
    day = Column(Integer, nullable=False)
    stacks = Column(JSON, nullable=False)
    strikes_at = Column(BigInteger, nullable=False)
    status = Column(String, nullable=False, default="active")
    result = Column(String)
    __table_args__ = (
        CheckConstraint("status IN ('active', 'defeated', 'struck')", name="ck_raids_status"),
        Index("uq_raids_active_hex", "q", "r", unique=True, postgresql_where=text("status = 'active'")),
        UniqueConstraint("player_id", "season", "day", name="uq_raids_player_day"),
    )
