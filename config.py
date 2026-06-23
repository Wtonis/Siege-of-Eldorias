"""
Константы проекта: окно, тайминги цикла, цвета.
Баланс башен и врагов лежит отдельно в data/*.json.
"""

# --- Окно ---
# Размер внутреннего холста (design-резолюция): вся вёрстка и координаты заданы под него.
# Реальное окно может быть больше — картинка холста растягивается под него (см. Viewport).
WINDOW_WIDTH: int = 1280
WINDOW_HEIGHT: int = 720
TITLE: str = "Siege of Eldoria"

# Пресеты размера окна для выбора в меню (соотношение 16:9 — без искажений при масштабе).
RESOLUTIONS: list[tuple[int, int]] = [(1280, 720), (1600, 900), (1920, 1080)]

# --- Игровой цикл ---
FPS: int = 120                      # верхняя граница частоты кадров
FIXED_DT: float = 1.0 / 60.0        # шаг симуляции модели (сек)
MAX_FRAME_TIME: float = 0.25        # ограничение шага при сильных просадках FPS

# --- Размер тайла/сетки ---
TILE_SIZE: int = 64

# --- Цвета (R, G, B) ---
COLOR_BG: tuple[int, int, int] = (24, 26, 32)
COLOR_TEXT: tuple[int, int, int] = (230, 230, 235)
COLOR_TEXT_DIM: tuple[int, int, int] = (150, 150, 160)
COLOR_ACCENT: tuple[int, int, int] = (220, 180, 80)
COLOR_DEFEAT: tuple[int, int, int] = (210, 90, 80)      # заголовок экрана поражения

# --- Экономика боя ---
SELL_REFUND_RATIO: float = 0.7         # доля вложенного золота при продаже башни

# --- Волны ---
WAVE_GAP: float = 10.0                 # пауза между волнами (сек)
EARLY_CALL_GOLD_PER_SEC: int = 3       # золото за каждую сэкономленную секунду при досрочном вызове

# --- Враги ---
ENEMY_LANE_HALF: float = 22.0          # макс. боковое смещение врага от центра пути (формация «в ряд»)

# --- Солдаты казармы ---
SOLDIER_SPEED: float = 95.0            # скорость выхода к врагу/возврата
SOLDIER_MELEE_RANGE: float = 18.0      # дистанция, с которой солдат бьёт

# --- Радиусы и размеры отрисовки (пиксели) ---
PATH_WIDTH: int = 60
SLOT_RADIUS: int = 22
TOWER_RADIUS: int = 20
ENEMY_RADIUS: int = 14
SOLDIER_RADIUS: int = 9
PROJECTILE_RADIUS: int = 5
BALLISTA_RADIUS: int = 16
BOLT_RADIUS: int = 5
HP_BAR_WIDTH: int = 30
HP_BAR_HEIGHT: int = 4

# --- Цвета мира боя ---
COLOR_PATH: tuple[int, int, int] = (58, 52, 42)
COLOR_SLOT: tuple[int, int, int] = (70, 78, 90)
COLOR_SLOT_SELECTED: tuple[int, int, int] = (220, 180, 80)
COLOR_RANGE: tuple[int, int, int] = (120, 130, 150)
COLOR_PROJECTILE: tuple[int, int, int] = (240, 230, 180)
COLOR_SOLDIER: tuple[int, int, int] = (200, 190, 120)
COLOR_POISON: tuple[int, int, int] = (120, 220, 90)
COLOR_SLOW: tuple[int, int, int] = (110, 180, 240)
COLOR_BALLISTA: tuple[int, int, int] = (205, 120, 80)
COLOR_BALLISTA_RELOADING: tuple[int, int, int] = (110, 80, 60)
COLOR_BOLT: tuple[int, int, int] = (250, 210, 140)
COLOR_AIM: tuple[int, int, int] = (220, 120, 90)
COLOR_SYNERGY: tuple[int, int, int] = (90, 230, 180)

# --- Связь синергии ---
SYNERGY_LINK_WIDTH: int = 4
SYNERGY_NODE_RADIUS: int = 6
COLOR_HP_BG: tuple[int, int, int] = (50, 24, 24)
COLOR_HP_FG: tuple[int, int, int] = (90, 200, 90)
COLOR_ENEMY_DEFAULT: tuple[int, int, int] = (200, 200, 200)

TOWER_COLORS: dict[str, tuple[int, int, int]] = {
    "archer": (90, 170, 90),
    "mage": (110, 120, 230),
    "bomber": (210, 130, 60),
    "warrior": (200, 170, 90),
}
TOWER_NAMES: dict[str, str] = {
    "archer": "Лучник",
    "mage": "Маг",
    "bomber": "Бомбер",
    "warrior": "Воин",
}
ENEMY_COLORS: dict[str, tuple[int, int, int]] = {
    "goblin": (120, 200, 120),
    "orc": (200, 90, 80),
    "wisp": (120, 220, 230),
    "scout": (230, 220, 120),
    "knight": (170, 175, 190),
    "shaman": (180, 120, 220),
    "troll": (110, 150, 90),
    "raider": (210, 140, 70),
    "ogre": (150, 80, 60),
    "dragon": (200, 60, 70),
}

# --- Цвета HUD ---
COLOR_PANEL_BG: tuple[int, int, int] = (32, 36, 44)
COLOR_PANEL_BORDER: tuple[int, int, int] = (70, 78, 90)
COLOR_BUTTON: tuple[int, int, int] = (54, 60, 72)
COLOR_BUTTON_HOVER: tuple[int, int, int] = (74, 82, 98)
COLOR_BUTTON_DISABLED: tuple[int, int, int] = (40, 44, 52)
COLOR_BUTTON_BORDER: tuple[int, int, int] = (90, 100, 116)
