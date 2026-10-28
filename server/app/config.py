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
VERSION = "slice-8"
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
# Fictional stack balance (no real-world weapon data). hp is per member.
UNITS = {
    "rifles": {"name": "Стрелки", "hp": 10, "damage": 3, "defense": 1, "speed": 2, "initiative": 5,
               "range": 4, "melee": False, "infantry": True, "count": 10, "seconds": 45,
               "cost": {"metal": 60, "food": 40}, "requires": {"barracks": 1}},
    "scouts": {"name": "Разведчики", "hp": 8, "damage": 2, "defense": 1, "speed": 4, "initiative": 8,
               "range": 3, "melee": False, "infantry": True, "count": 6, "seconds": 40,
               "cost": {"metal": 40, "food": 30}, "requires": {"barracks": 1}},
    "assault": {"name": "Штурмовики", "hp": 14, "damage": 5, "defense": 2, "speed": 3, "initiative": 6,
                "range": 1, "melee": True, "infantry": True, "count": 8, "seconds": 60,
                "cost": {"metal": 90, "food": 50}, "requires": {"barracks": 2}},
    "artillery": {"name": "Артиллерия", "hp": 12, "damage": 7, "defense": 0, "speed": 1, "initiative": 3,
                  "range": 7, "melee": False, "infantry": False, "count": 4, "seconds": 90,
                  "cost": {"metal": 140, "fuel": 30, "electronics": 20}, "requires": {"barracks": 3}},
    "armor": {"name": "Бронетехника", "hp": 40, "damage": 9, "defense": 5, "speed": 3, "initiative": 4,
              "range": 1, "melee": True, "infantry": False, "count": 3, "seconds": 120,
              "cost": {"metal": 220, "fuel": 60, "electronics": 40}, "requires": {"barracks": 4, "electronics": 1}},
}
# Commander factions, Heroes-style: each commander recruits five unique units.
# A variant inherits its role's baseline above, then applies small stat mods and
# at most one trait. "art" selects the client sprite, "accent" the faction colour.
FACTIONS = {
    "raven": {"name": "Железный легион", "accent": "#c8433a", "units": [
        {"key": "raven_line", "role": "rifles", "name": "Стрелки легиона", "gen": "стрелков легиона", "art": "rifleman", "trait": "bayonet"},
        {"key": "raven_scouts", "role": "scouts", "name": "Егеря", "gen": "егерей", "art": "scout", "mods": {"speed": 1}},
        {"key": "raven_assault", "role": "assault", "name": "Ударники", "gen": "ударников", "art": "stormtrooper", "trait": "first_strike"},
        {"key": "raven_artillery", "role": "artillery", "name": "Траншейная мортира", "gen": "траншейную мортиру", "art": "mortar"},
        {"key": "raven_heavy", "role": "armor", "name": "Экзоброня «Таран»", "gen": "экзоброню «Таран»", "art": "exosuit_drill", "trait": "charge", "mods": {"damage": 1}},
    ]},
    "valkyrie": {"name": "Серый дозор", "accent": "#5f8fd0", "units": [
        {"key": "valkyrie_line", "role": "rifles", "name": "Стрелки дозора", "gen": "стрелков дозора", "art": "rifleman", "mods": {"range": 1}},
        {"key": "valkyrie_walker", "role": "scouts", "name": "Шагоход-разведчик", "gen": "шагоход-разведчик", "art": "walker", "mods": {"hp": 4, "count": -2, "speed": 1, "initiative": 1}},
        {"key": "valkyrie_raiders", "role": "assault", "name": "Диверсанты", "gen": "диверсантов", "art": "raider", "trait": "first_strike", "mods": {"initiative": 2}},
        {"key": "valkyrie_snipers", "role": "artillery", "name": "Снайперская пара", "gen": "снайперскую пару", "art": "sniper", "trait": "marksman", "mods": {"range": 1, "damage": -1}},
        {"key": "valkyrie_heavy", "role": "armor", "name": "Шагоход «Гончая»", "gen": "шагоход «Гончая»", "art": "walker_heavy", "mods": {"speed": 1, "defense": -1}},
    ]},
    "titan": {"name": "Стальной заслон", "accent": "#c9a04a", "units": [
        {"key": "titan_line", "role": "rifles", "name": "Стрелки заслона", "gen": "стрелков заслона", "art": "rifleman", "mods": {"defense": 1}},
        {"key": "titan_mg", "role": "scouts", "name": "Пулемётный расчёт", "gen": "пулемётный расчёт", "art": "mg_crew", "mods": {"speed": -2, "damage": 2, "count": -2, "range": 1, "initiative": -3}},
        {"key": "titan_shields", "role": "assault", "name": "Щитоносцы", "gen": "щитоносцев", "art": "shieldbearer", "trait": "shield"},
        {"key": "titan_gun", "role": "artillery", "name": "Полевая пушка", "gen": "полевую пушку", "art": "field_gun", "mods": {"damage": 1}},
        {"key": "titan_heavy", "role": "armor", "name": "Экзоброня «Бастион»", "gen": "экзоброню «Бастион»", "art": "exosuit_cannon", "mods": {"defense": 2, "speed": -1}},
    ]},
    "phoenix": {"name": "Тыловой корпус", "accent": "#d9783a", "units": [
        {"key": "phoenix_line", "role": "rifles", "name": "Стрелки снабжения", "gen": "стрелков снабжения", "art": "rifleman"},
        {"key": "phoenix_medics", "role": "scouts", "name": "Санитары", "gen": "санитаров", "art": "medic", "trait": "medic", "mods": {"damage": -1}},
        {"key": "phoenix_sappers", "role": "assault", "name": "Сапёры", "gen": "сапёров", "art": "engineer", "mods": {"defense": 1}},
        {"key": "phoenix_howitzer", "role": "artillery", "name": "Гаубица", "gen": "гаубицу", "art": "field_gun", "mods": {"range": 1}},
        {"key": "phoenix_heavy", "role": "armor", "name": "Ремонтная экзоброня", "gen": "ремонтную экзоброню", "art": "exosuit_claw", "trait": "self_repair"},
    ]},
    "ghost": {"name": "Отдел «Призрак»", "accent": "#3fb7a8", "units": [
        {"key": "ghost_line", "role": "rifles", "name": "Стрелки-техники", "gen": "стрелков-техников", "art": "rifleman", "mods": {"initiative": 1}},
        {"key": "ghost_drones", "role": "scouts", "name": "Дроны-разведчики", "gen": "дронов-разведчиков", "art": "drone", "mods": {"speed": 2, "hp": -2}},
        {"key": "ghost_automatons", "role": "assault", "name": "Автоматоны", "gen": "автоматонов", "art": "automaton", "mods": {"defense": 2, "initiative": -1}},
        {"key": "ghost_tesla", "role": "artillery", "name": "Разрядная пушка", "gen": "разрядную пушку", "art": "tesla", "trait": "pierce"},
        {"key": "ghost_heavy", "role": "armor", "name": "Шагоход «Призрак»", "gen": "шагоход «Призрак»", "art": "walker_heavy", "trait": "pierce", "mods": {"initiative": 1}},
    ]},
    "storm": {"name": "Бронекорпус «Шторм»", "accent": "#a3b34a", "units": [
        {"key": "storm_line", "role": "rifles", "name": "Мотострелки", "gen": "мотострелков", "art": "rifleman", "mods": {"speed": 1}},
        {"key": "storm_cars", "role": "scouts", "name": "Бронеавтомобиль", "gen": "бронеавтомобиль", "art": "armored_car", "mods": {"hp": 6, "defense": 2, "count": -2}},
        {"key": "storm_tankers", "role": "assault", "name": "Танковый десант", "gen": "танковый десант", "art": "stormtrooper", "trait": "charge"},
        {"key": "storm_spg", "role": "artillery", "name": "Самоходная мортира", "gen": "самоходную мортиру", "art": "spg", "mods": {"speed": 1}},
        {"key": "storm_heavy", "role": "armor", "name": "Шагоход-танк «Шторм»", "gen": "шагоход-танк «Шторм»", "art": "walker_tank", "mods": {"damage": 2}},
    ]},
}
TRAITS = {
    "bayonet": "Штыковой бой: ответный удар вплотную без штрафа стрелков",
    "first_strike": "Внезапная атака: цель не наносит ответный удар",
    "charge": "Натиск: +30% урона, если стек подошёл к цели в этом ходу",
    "shield": "Щиты: урон от стрельбы ×0.6",
    "marksman": "Меткость: игнорирует укрытия и не теряет точность вплотную",
    "pierce": "Пробой: игнорирует защиту цели",
    "medic": "Медики: после хода лечат соседние свои стеки на 15%",
    "self_repair": "Саморемонт: после хода восстанавливает 10% здоровья",
}
ART = {role: art for role, art in (("rifles", "rifleman"), ("scouts", "scout"), ("assault", "stormtrooper"),
                                   ("artillery", "mortar"), ("armor", "exosuit_drill"))}
for _hero, _faction in FACTIONS.items():
    for _v in _faction["units"]:
        _base = UNITS[_v["role"]]
        _unit = {**_base, "name": _v["name"], "gen": _v["gen"], "role": _v["role"], "faction": _hero,
                 "art": _v["art"], "trait": _v.get("trait")}
        for _k, _d in _v.get("mods", {}).items():
            _unit[_k] = max(0 if _k in ("defense", "damage") else 1, _base[_k] + _d)
        UNITS[_v["key"]] = _unit
for _role, _art in ART.items():
    UNITS[_role].setdefault("art", _art)
    UNITS[_role].setdefault("trait", None)
    UNITS[_role].setdefault("role", _role)
ARMY_STACKS = 5
NPC_TIERS = [
    {"name": "Патруль", "xp": 50, "stacks": [["rifles", 5]]},
    {"name": "Рота", "xp": 75, "stacks": [["rifles", 8], ["assault", 4]]},
    {"name": "Батальон", "xp": 110, "stacks": [["rifles", 8], ["assault", 6], ["armor", 1]]},
]
TUTORIAL_NPC = [["rifles", 7]]
ABILITIES = {
    "raven": {"name": "Штурм", "about": "Атака активного стека с уроном ×1.5"},
    "valkyrie": {"name": "Корректировка огня", "about": "Выстрел по любой цели без учёта дальности"},
    "titan": {"name": "Стальная стена", "about": "Все ваши стеки встают в оборону до конца раунда"},
    "phoenix": {"name": "Полевой госпиталь", "about": "Активный стек восстанавливает 30% здоровья"},
    "ghost": {"name": "РЭБ", "about": "Выбранный вражеский стек пропускает ход в этом раунде"},
    "storm": {"name": "Прорыв", "about": "Активный стек получает дополнительное действие"},
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
        "effect": "После боя возвращается 10% павших",
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
        "effect": "Скорость ваших стеков в бою +1",
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
