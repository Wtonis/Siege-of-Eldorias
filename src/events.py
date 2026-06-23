"""
Типы игровых событий (передаются через EventBus).
События - это неизменяемые факты о том, что уже произошло в модели.
View/звук/экономика подписываются на нужные им типы.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EnemyKilled:
    enemy_id: int
    reward: int


@dataclass(frozen=True)
class EnemyReachedBase:
    enemy_id: int
    damage: int


@dataclass(frozen=True)
class TowerBuilt:
    slot_index: int
    tower_kind: str


@dataclass(frozen=True)
class WaveCleared:
    wave_index: int


@dataclass(frozen=True)
class LevelCompleted:
    level_id: str
    points_awarded: int


@dataclass(frozen=True)
class LevelFailed:
    level_id: str
