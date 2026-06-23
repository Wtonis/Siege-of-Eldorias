"""
Враг: движется по пути к базе, получает урон, дерётся с солдатами казармы.
Состояния: WALKING — идёт по пути; FIGHTING — заблокирован солдатом, стоит на месте
и обменивается уроном; DEAD — убит.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Optional
import config
from src.model.entities.entity import Entity
from src.model.level.path import Path
from src.model.systems.damage import DamageType, resolve_damage
from src.model.systems.effects import Effect, EffectKind, EffectSpec
from src.model.vector import Vec2
if TYPE_CHECKING:
    from src.model.entities.soldier import Soldier

# Конечный автомат состояний
class EnemyState(Enum):
    WALKING = auto()
    FIGHTING = auto()
    DEAD = auto()


@dataclass
class EnemyStats:
    """Числовые характеристики врага (неизменяемые данные из enemies.json)."""
    kind: str
    max_hp: int
    speed: float                                # пикселей в игровую секунду
    reward: int                                 # золото за убийство
    base_damage: int                            # урон базе при доходе до конца
    attack_damage: int = 0                      # урон солдату в ближнем бою
    attack_rate: float = 1.0                    # ударов в игровую секунду
    radius: float = float(config.ENEMY_RADIUS)  # размер 
    resistances: dict[DamageType, float] = field(default_factory=dict)


class Enemy(Entity):
    def __init__(self, stats: EnemyStats, path: Path, lane_offset: float = 0.0) -> None:
        super().__init__(path.start)
        self.stats: EnemyStats = stats
        self.path: Path = path
        self.hp: int = stats.max_hp
        self.state: EnemyState = EnemyState.WALKING
        self.progress: float = 0.0              # пройденный путь — для выбора цели башней
        self.reached_base: bool = False
        self.blocker: Optional["Soldier"] = None # Держит ли солдат
        self.effects: list[Effect] = []
        self._waypoint_index: int = 0           # индекс последней достигнутой точки
        self._attack_timer: float = 0.0
        self._poison_carry: float = 0.0         # накопитель дробного урона яда
        self._center: Vec2 = path.start
        self._lane_offset: float = lane_offset
        self._direction: Vec2 = (path.waypoint(1) - path.start).normalized()
        self.position = self._offset_position()

    def _offset_position(self) -> Vec2:
        """Позиция со сдвигом вбок (перпендикуляр к направлению движения)."""
        perpendicular = Vec2(-self._direction.y, self._direction.x)
        return self._center + perpendicular * self._lane_offset

    def take_damage(self, amount: int, damage_type: DamageType) -> None:
        self.hp -= resolve_damage(amount, damage_type, self.stats.resistances)
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.state = EnemyState.DEAD

    def apply_effect(self, spec: EffectSpec) -> None:
        """Наложить эффект; повторное наложение того же вида обновляет его."""
        for effect in self.effects:
            if effect.kind is spec.kind:
                effect.magnitude = spec.magnitude
                effect.remaining = spec.duration
                return
        self.effects.append(Effect(spec.kind, spec.magnitude, spec.duration))

    @property
    def slow_factor(self) -> float:
        """Множитель скорости от замедления (минимальный из активных, иначе 1)."""
        factor = 1.0
        for effect in self.effects:
            if effect.kind is EffectKind.SLOW:
                factor = min(factor, effect.magnitude)
        return factor

    def engage(self, soldier: "Soldier") -> None:
        """Солдат заблокировал врага: остановиться и драться."""
        self.blocker = soldier
        self.state = EnemyState.FIGHTING

    def release(self, soldier: "Soldier") -> None:
        """Солдат отцепился/погиб: возобновить движение."""
        if self.blocker is soldier:
            self.blocker = None
            self._attack_timer = 0.0
            if self.state is EnemyState.FIGHTING:
                self.state = EnemyState.WALKING

    def update(self, dt: float) -> None:
        if not self.alive:
            return
        self._tick_effects(dt)
        if not self.alive:
            return
        if self.state is EnemyState.FIGHTING:
            self._fight(dt)
            return
        if self.reached_base:
            return
        self._advance(dt)

    def _tick_effects(self, dt: float) -> None:
        if not self.effects:
            return
        for effect in self.effects:
            effect.remaining -= dt
        poison_dps = sum(e.magnitude for e in self.effects if e.kind is EffectKind.POISON)
        if poison_dps > 0.0:
            self._poison_carry += poison_dps * dt
            whole = int(self._poison_carry)       # бьём целыми единицами HP
            if whole > 0:
                self._poison_carry -= whole
                self.take_damage(whole, DamageType.TRUE)
        self.effects = [e for e in self.effects if e.remaining > 0.0]

    def _fight(self, dt: float) -> None:
        if self.blocker is None or not self.blocker.alive:
            self.state = EnemyState.WALKING
            self.blocker = None
            return
        self._attack_timer = max(0.0, self._attack_timer - dt)
        if self._attack_timer <= 0.0:
            self.blocker.take_damage(self.stats.attack_damage)
            self._attack_timer = 1.0 / self.stats.attack_rate

    def _advance(self, dt: float) -> None:
        """Движение по пути к базе"""
        remaining = self.stats.speed * self.slow_factor * dt
        while remaining > 0.0:
            if self.path.is_last(self._waypoint_index):
                self.reached_base = True
                break
            target = self.path.waypoint(self._waypoint_index + 1)
            to_target = target - self._center
            distance = to_target.length()
            if distance == 0.0:
                self._waypoint_index += 1
                continue
            self._direction = to_target.normalized()
            if distance <= remaining:
                self._center = target
                self.progress += distance
                remaining -= distance
                self._waypoint_index += 1
            else:
                self._center = self._center + self._direction * remaining
                self.progress += remaining
                remaining = 0.0
        self.position = self._offset_position()
