"""
LevelData - разобранное описание одного уровня (результат LevelLoader).
Это чертеж уровня: путь, слоты, план волн, стартовая экономика. Runtime-бой
(World + WaveManager) строится из него. Каждая загрузка создаёт
свежие объекты, поэтому состояние одного боя не протекает в следующий.
"""
from dataclasses import dataclass
from src.model.level.path import Path
from src.model.level.slot import BuildSlot
from src.model.level.wave_plan import WavePlan
from src.model.vector import Vec2


@dataclass(frozen=True)
class LevelData:
    level_id: str
    start_gold: int
    start_lives: int
    path: Path
    slots: list[BuildSlot]
    waves: list[WavePlan]
    ballista_pos: Vec2
    reward_points: int = 1
