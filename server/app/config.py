import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://iron:iron@localhost:5432/iron"
)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
ENV = os.environ.get("APP_ENV", "production")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
VERSION = "slice-2"
RESOURCES = ["metal", "oil", "fuel", "electronics", "food"]
INITIAL = {"metal": 1000, "oil": 300, "fuel": 200, "electronics": 200, "food": 300}
BUILDINGS = {
    "hq": {"name": "Главный штаб", "cost": {}, "seconds": 0, "power": 0},
    "power": {
        "name": "Электростанция",
        "cost": {"metal": 100},
        "seconds": 30,
        "power": 20,
    },
    "quarry": {
        "name": "Металлургический карьер",
        "cost": {"metal": 140},
        "seconds": 45,
        "power": -4,
        "output": {"metal": 12},
    },
    "barracks": {
        "name": "Казармы",
        "cost": {"metal": 200, "electronics": 30},
        "seconds": 60,
        "power": -6,
    },
    "refinery": {
        "name": "НПЗ",
        "cost": {"metal": 180, "electronics": 20},
        "seconds": 60,
        "power": -5,
        "input": {"oil": 2},
        "output": {"fuel": 3},
    },
}
HEROES = {
    "raven": {
        "name": "Генерал Рейвен",
        "role": "Наступление",
        "bio": "Ведёт подразделения через самые сложные рубежи.",
        "effect": "Урон пехоты +5%",
    },
    "valkyrie": {
        "name": "Командир Валькирия",
        "role": "Разведка",
        "bio": "Находит путь там, где карты заканчиваются.",
        "effect": "Обзор карты +1 гекс",
    },
    "titan": {
        "name": "Полковник Титан",
        "role": "Оборона",
        "bio": "Превращает каждую позицию в опорный пункт.",
        "effect": "Входящий урон −5%",
    },
    "phoenix": {
        "name": "Маршал Феникс",
        "role": "Логистика",
        "bio": "Возвращает бойцов в строй и сохраняет снабжение.",
        "effect": "Восстановление после боя +10 HP",
    },
    "ghost": {
        "name": "Инженер Призрак",
        "role": "Технологии",
        "bio": "Собирает преимущество из точных инженерных решений.",
        "effect": "Карьер производит +1 металл/мин",
    },
    "storm": {
        "name": "Генерал Шторм",
        "role": "Бронетехника",
        "bio": "Предпочитает скорость и инициативу.",
        "effect": "Перемещение в учебном бою до 2 гексов",
    },
}

EXPEDITIONS = {
    "home": [64, 64],
    "seconds": 30,
    "fuel": 2,
    "control_limit": 12,
    "army_vision": 2,
    "territory_yield": {
        "plain": {"food": 2}, "forest": {"metal": 2},
        "hills": {"metal": 3}, "desert": {"oil": 2},
    },
}
