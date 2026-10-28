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
VERSION = "slice-6"
RESOURCES = ["metal", "oil", "fuel", "electronics", "food"]
INITIAL = {"metal": 1000, "oil": 300, "fuel": 200, "electronics": 200, "food": 300}
# Fictional balance. Level effects come from app.economy; every value here is
# the level-1 baseline. "hq" is the headquarters level required to build.
BUILDINGS = {
    "hq": {"name": "Главный штаб", "cost": {"metal": 300, "electronics": 60}, "seconds": 90, "power": 0, "hq": 1,
           "about": "Командный центр. Уровень штаба ограничивает уровни остальных зданий и открывает новые постройки."},
    "power": {"name": "Электростанция", "cost": {"metal": 100}, "seconds": 30, "power": 20, "hq": 1,
              "about": "Даёт энергию производственным зданиям."},
    "quarry": {"name": "Металлургический карьер", "cost": {"metal": 140}, "seconds": 45, "power": -4, "hq": 1,
               "output": {"metal": 12}, "about": "Добывает металл каждую минуту."},
    "barracks": {"name": "Казармы", "cost": {"metal": 200, "electronics": 30}, "seconds": 60, "power": -6, "hq": 1,
                 "about": "Открывает подготовку стрелков в разделе «Армия»."},
    "refinery": {"name": "НПЗ", "cost": {"metal": 180, "electronics": 20}, "seconds": 60, "power": -5, "hq": 1,
                 "input": {"oil": 2}, "output": {"fuel": 3}, "about": "Перерабатывает нефть в топливо."},
    "oil_well": {"name": "Нефтедобывающий комплекс", "cost": {"metal": 160}, "seconds": 50, "power": -3, "hq": 1,
                 "output": {"oil": 4}, "about": "Добывает сырую нефть для НПЗ."},
    "farm": {"name": "Агрокомплекс", "cost": {"metal": 120}, "seconds": 40, "power": -2, "hq": 1,
             "output": {"food": 6}, "about": "Производит провизию для подготовки войск."},
    "warehouse": {"name": "Склад", "cost": {"metal": 220}, "seconds": 60, "power": -1, "hq": 2,
                  "storage": 2500, "about": "Увеличивает вместимость каждого ресурса."},
    "watchtower": {"name": "Сторожевая башня", "cost": {"metal": 180, "electronics": 20}, "seconds": 60, "power": -2, "hq": 2,
                   "vision": 1, "about": "Расширяет обзор мировой карты вокруг базы."},
    "electronics": {"name": "Электронный завод", "cost": {"metal": 260, "electronics": 40}, "seconds": 90, "power": -8, "hq": 3,
                    "input": {"metal": 4}, "output": {"electronics": 2}, "about": "Превращает металл в электронику."},
    "repair": {"name": "Ремонтный центр", "cost": {"metal": 240, "electronics": 50}, "seconds": 90, "power": -4, "hq": 3,
               "repair": 2, "about": "Восстанавливает здоровье отрядов вне боя."},
}
MAX_LEVEL = 10
BASE_STORAGE = 5000
GROWTH = {"cost": 1.6, "time": 1.45, "output": 0.25, "power_use": 0.15, "power_gen": 0.3}
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
    "staging": [64, 64],  # legacy shared point; each player now has a world base
    # Heroes-style movement: points refill in real time, terrain sets the price.
    "movement_max": 12,
    "movement_regen_seconds": 2400,   # +1 point every 40 min -> full in 8 h
    "terrain_cost": {"plain": 1, "desert": 2, "forest": 2, "hills": 3},
    "step_seconds": 10,               # real seconds per movement point spent
    "seconds": 30,                    # legacy single-hex duration (pre-0.5 orders)
    "fuel": 1,                        # fuel per hex travelled
    "control_limit": 12,
    "army_vision": 2,
    "territory_yield": {
        "plain": {"food": 2}, "forest": {"metal": 2},
        "hills": {"metal": 3}, "desert": {"oil": 2},
    },
}
