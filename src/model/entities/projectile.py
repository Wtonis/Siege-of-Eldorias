"""
Снаряд башни: самонаводящийся, летит к цели и при попадании наносит урон.
Снаряды переиспользуются через пул, поэтому состояние сбрасывается
методом reset, а не пересозданием объекта. Сам урон применяет World, у снаряда
нет доступа к списку всех врагов.
"""
from typing import Optional
from src.model.entities.enemy import Enemy
from src.model.systems.damage import DamageType
from src.model.systems.effects import EffectSpec
from src.model.vector import Vec2


class Projectile:
    def __init__(self) -> None:
        self.active: bool = False
        self.has_hit: bool = False
        self.position: Vec2 = Vec2()
        self.target: Enemy | None = None
        self.damage: int = 0
        self.damage_type: DamageType = DamageType.PHYSICAL
        self.speed: float = 0.0
        self.splash_radius: float = 0.0         # 0 - одиночная цель, >0 - урон по площади
        self.effect: Optional[EffectSpec] = None  # эффект, накладываемый при попадании
        self._aim: Vec2 = Vec2()                # точка прицеливания (фиксируется при гибели цели)

    def reset(
        self,
        origin: Vec2,
        target: Enemy,
        damage: int,
        damage_type: DamageType,
        speed: float,
        splash_radius: float,
        effect: Optional[EffectSpec] = None,
    ) -> None:
        self.active = True
        self.has_hit = False
        self.position = origin
        self.target = target
        self.damage = damage
        self.damage_type = damage_type
        self.speed = speed
        self.splash_radius = splash_radius
        self.effect = effect
        self._aim = target.position

    # Тоже использутеся алгоритм из vector.py
    def update(self, dt: float) -> None:
        if not self.active:
            return
        # Пока цель жива ведём снаряд за ней, иначе бьём по последней точке.
        if self.target is not None and self.target.alive:
            self._aim = self.target.position
        step = self.speed * dt
        self.has_hit = self.position.distance_to(self._aim) <= step
        self.position = self.position.move_towards(self._aim, step)

    @property
    def impact_point(self) -> Vec2:
        return self._aim
