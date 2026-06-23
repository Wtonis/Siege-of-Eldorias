"""
Статус-эффекты на врагах: яд (урон по времени) и замедление.
EffectSpec - неизменяемое описание эффекта (живёт в данных ветки и в снаряде).
Effect - активный эффект на конкретном враге (у него тикает остаток времени).
Логику тика (урон/замедление) ведёт сам враг - здесь только данные, без зависимости
Effect -> Enemy (иначе был бы цикл).
"""

from dataclasses import dataclass
from enum import Enum, auto


class EffectKind(Enum):
    POISON = auto()     # magnitude = урон в игровую секунду (в обход брони)
    SLOW = auto()       # magnitude = множитель скорости (0..1)


@dataclass(frozen=True)
class EffectSpec:
    kind: EffectKind
    magnitude: float
    duration: float


@dataclass
class Effect:
    kind: EffectKind
    magnitude: float
    remaining: float
