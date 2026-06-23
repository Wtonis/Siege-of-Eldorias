"""
Солдат казармы: выходит к назначенному врагу и бьётся в ближнем бою.
Связь солдат↔враг взаимная: солдат бьёт врага в свой такт, враг бьёт солдата
в свой. Каждый наносит урон сам.
Назначение цели и респаун забота BarracksTower, солдат лишь исполняет.
"""
from dataclasses import dataclass
from typing import Optional
import config
from src.model.entities.enemy import Enemy
from src.model.systems.damage import DamageType
from src.model.vector import Vec2


@dataclass
class SoldierStats:
    """Характеристики солдат одной казармы."""
    count: int                  # сколько солдат держит казарма
    hp: int
    damage: int
    attack_rate: float          # ударов в игровую секунду
    respawn: float              # секунд на возрождение павшего


class Soldier:
    def __init__(self, rally_point: Vec2, stats: SoldierStats) -> None:
        self.rally_point: Vec2 = rally_point # точка сбора солдат
        self.position: Vec2 = rally_point
        self.stats: SoldierStats = stats
        self.hp: int = stats.hp
        self.max_hp: int = stats.hp
        self.alive: bool = True
        self.target: Optional[Enemy] = None
        self._attack_timer: float = 0.0

    def engage(self, enemy: Enemy) -> None:
        self.target = enemy
        enemy.engage(self)

    def release(self) -> None:
        """Отпустить врага и освободиться."""
        if self.target is not None:
            self.target.release(self)
            self.target = None
        self._attack_timer = 0.0

    def take_damage(self, amount: int) -> None:
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def update(self, dt: float) -> None:
        if not self.alive:
            return
        if self.target is None or not self.target.alive:
            self.release()
            self._move_toward(self.rally_point, dt)
            return
        if self.position.distance_to(self.target.position) > config.SOLDIER_MELEE_RANGE:
            self._move_toward(self.target.position, dt)
        else:
            self._attack(dt)

    def _attack(self, dt: float) -> None:
        self._attack_timer = max(0.0, self._attack_timer - dt)
        if self._attack_timer <= 0.0:
            self.target.take_damage(self.stats.damage, DamageType.PHYSICAL)
            self._attack_timer = 1.0 / self.stats.attack_rate

    # Алгоритм Seek/Arrive из vector.py | Переиспользован
    def _move_toward(self, point: Vec2, dt: float) -> None:
        self.position = self.position.move_towards(point, config.SOLDIER_SPEED * dt)
