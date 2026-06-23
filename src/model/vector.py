"""Двумерный вектор для логики модели.

Своя реализация, чтобы модель не зависела от pygame.Vector2 (рендер — отдельно).
Иммутабельный: операции возвращают новый вектор, старый не меняется.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Vec2:
    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vec2":
        return Vec2(self.x * scalar, self.y * scalar)

    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def distance_to(self, other: "Vec2") -> float:
        return math.hypot(other.x - self.x, other.y - self.y)

    def normalized(self) -> "Vec2":
        length = self.length()
        if length == 0.0:
            return Vec2(0.0, 0.0)
        return Vec2(self.x / length, self.y / length)

    def move_towards(self, target: "Vec2", step: float) -> "Vec2":
        """Шаг к target на step; если ближе шага — ровно в target (без перелёта)."""
        to_target = target - self
        if to_target.length() <= step:
            return target
        return self + to_target.normalized() * step
