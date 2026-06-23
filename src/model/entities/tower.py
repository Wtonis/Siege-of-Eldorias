"""
Башни: общая база и два поведения, с базовой прокачкой и ветками специализаций.
Прогрессия башни - это дерево: общие базовые уровни, затем выбор одной специализации,
которая меняет числа и/или поведение (накладываемый эффект).
Данные дерева (база + ветки + эффекты) живут в data/towers.json, не в коде.
Tower — абстрактная база: дерево уровней, апгрейд, специализация. Поведение в подклассах.
BarracksTower держит солдат. Ветки воина чисто числовые (меняют статы солдат).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Optional
from src.model.entities.entity import Entity
from src.model.entities.enemy import Enemy
from src.model.entities.soldier import Soldier, SoldierStats
from src.model.systems.damage import DamageType
from src.model.systems.effects import EffectSpec
from src.model.systems.synergy import SynergyModifiers
from src.model.vector import Vec2

# Колбэк создания снаряда: (откуда, цель, урон, тип, скорость, радиус AoE, эффект), чтобы не зависить от world.
SpawnProjectile = Callable[[Vec2, Enemy, int, DamageType, float, float, Optional[EffectSpec]], None]


@dataclass
class TowerStats:
    """Характеристики башни на одном уровне (из данных, шаг 3).

    cost — стоимость достижения уровня (постройка / апгрейд / специализация).
    range — радиус стрельбы у проектильных, радиус сбора солдат у казармы.
    soldier задаётся только казарме, effect — только специализациям с поведением.
    """
    kind: str
    cost: int
    range: float
    fire_rate: float = 1.0
    damage: int = 0
    damage_type: DamageType = DamageType.PHYSICAL
    projectile_speed: float = 0.0
    splash_radius: float = 0.0                  # >0 у бомбера (AoE)
    soldier: Optional[SoldierStats] = None      # задано только у казармы
    effect: Optional[EffectSpec] = None         # накладывается при попадании


@dataclass
class TowerBranch:
    """Ветка специализации: имя для UI, цена разблокировки в очках и уровни прокачки."""
    key: str
    name: str
    levels: list[TowerStats]
    unlock_cost: int = 0


@dataclass
class TowerBlueprint:
    """Полное дерево башни: базовые уровни + ветки специализаций. Данные берем из json."""
    kind: str
    base_levels: list[TowerStats]
    branches: dict[str, TowerBranch] = field(default_factory=dict)


class Tower(Entity, ABC):
    def __init__(self, blueprint: TowerBlueprint, slot_index: int, position: Vec2) -> None:
        super().__init__(position)
        self.blueprint: TowerBlueprint = blueprint
        self.branch_key: Optional[str] = None   # None - на базовой ветке
        self.level_index: int = 0               # Индекс уровня внутри текущей ветки
        self.slot_index: int = slot_index
        self.invested: int = 0                  # Вложенное золото - для возврата при продаже
        self.soldiers: list[Soldier] = []
        self.modifiers: SynergyModifiers = SynergyModifiers() # Множитель от синергии
        self.active_synergies: list[str] = []

    @property
    def effective_range(self) -> float:
        return self.stats.range * self.modifiers.range

    @property
    def effective_damage(self) -> int:
        return round(self.stats.damage * self.modifiers.damage)

    @property
    def effective_fire_rate(self) -> float:
        return self.stats.fire_rate * self.modifiers.fire_rate

    @property
    def effective_splash(self) -> float:
        return self.stats.splash_radius * self.modifiers.splash

    @property
    def _segment(self) -> list[TowerStats]:
        if self.branch_key is None:
            return self.blueprint.base_levels
        return self.blueprint.branches[self.branch_key].levels

    @property
    def stats(self) -> TowerStats:
        return self._segment[self.level_index]

    @property
    def kind(self) -> str:
        return self.blueprint.kind

    @property
    def branch_name(self) -> Optional[str]:
        return self.blueprint.branches[self.branch_key].name if self.branch_key else None

    @property
    def can_upgrade(self) -> bool:
        return self.level_index + 1 < len(self._segment)

    @property
    def upgrade_cost(self) -> int:
        return self._segment[self.level_index + 1].cost if self.can_upgrade else 0

    def upgrade(self) -> None:
        if self.can_upgrade:
            self.level_index += 1

    @property
    def can_specialize(self) -> bool:
        """На последнем базовом уровне и есть из чего выбрать ветку."""
        return self.branch_key is None and not self.can_upgrade and bool(self.blueprint.branches)

    def specializations(self) -> list[tuple[str, str, int]]:
        """Доступные ветки как (ключ, имя, стоимость) — для UI."""
        if not self.can_specialize:
            return []
        return [(b.key, b.name, b.levels[0].cost) for b in self.blueprint.branches.values()]

    def specialization_cost(self, branch_key: str) -> int:
        branch = self.blueprint.branches.get(branch_key)
        return branch.levels[0].cost if branch else 0

    def specialize(self, branch_key: str) -> None:
        if self.can_specialize and branch_key in self.blueprint.branches:
            self.branch_key = branch_key
            self.level_index = 0

    def on_sold(self) -> None:
        """Хук перед удалением башни (казарма отпускает врагов)."""

    @abstractmethod
    def update(self, dt: float, enemies: list[Enemy], spawn: SpawnProjectile) -> None: ...


class ProjectileTower(Tower):
    """Лучник/маг/бомбер: выпускает снаряд в выбранную цель."""

    def __init__(self, blueprint: TowerBlueprint, slot_index: int, position: Vec2) -> None:
        super().__init__(blueprint, slot_index, position)
        self._cooldown: float = 0.0             # время до следующего выстрела

    def update(self, dt: float, enemies: list[Enemy], spawn: SpawnProjectile) -> None:
        self._cooldown = max(0.0, self._cooldown - dt)
        if self._cooldown > 0.0:
            return
        target = self._select_target(enemies)
        if target is None:
            return
        spawn(self.position, target, self.effective_damage, self.stats.damage_type,
              self.stats.projectile_speed, self.effective_splash, self.stats.effect)
        self._cooldown = 1.0 / self.effective_fire_rate

    # Алгоритм атаки врага, прошедшего дальше всех. Линейный подход (ищем перебором кто прошел дальше всех в радиусе атаки).
    def _select_target(self, enemies: list[Enemy]) -> Optional[Enemy]:
        """Приоритет — враг, прошедший дальше всех, в пределах радиуса."""
        best: Optional[Enemy] = None
        for enemy in enemies:
            if not enemy.alive:
                continue
            if self.position.distance_to(enemy.position) > self.effective_range:
                continue
            if best is None or enemy.progress > best.progress:
                best = enemy
        return best


class BarracksTower(Tower):
    """Воин: держит солдат у точки сбора и блокирует ими врагов."""

    def __init__(self, blueprint: TowerBlueprint, slot_index: int, position: Vec2) -> None:
        super().__init__(blueprint, slot_index, position)
        self.rally_point: Vec2 = position
        self.soldiers: list[Soldier] = []
        self._respawn_timers: list[float] = []
        for _ in range(self._soldier_stats.count):
            self._spawn_soldier()

    @property
    def _soldier_stats(self) -> SoldierStats:
        assert self.stats.soldier is not None
        return self.stats.soldier

    def on_sold(self) -> None:
        for soldier in self.soldiers:
            soldier.release()

    def update(self, dt: float, enemies: list[Enemy], spawn: SpawnProjectile) -> None:
        self._collect_fallen()
        self._refill(dt)
        for soldier in self.soldiers:
            soldier.update(dt)
        self._assign_targets(enemies)

    def _spawn_soldier(self) -> None:
        base = self._soldier_stats
        mods = self.modifiers
        stats = SoldierStats(
            count=base.count,
            hp=round(base.hp * mods.soldier_hp),
            damage=round(base.damage * mods.soldier_damage),
            attack_rate=base.attack_rate,
            respawn=base.respawn,
        )
        self.soldiers.append(Soldier(self.rally_point, stats))

    def _collect_fallen(self) -> None:
        for soldier in [s for s in self.soldiers if not s.alive]:
            soldier.release()
            self.soldiers.remove(soldier)
            self._respawn_timers.append(self._soldier_stats.respawn)

    def _refill(self, dt: float) -> None:
        deficit = self._soldier_stats.count - (len(self.soldiers) + len(self._respawn_timers))
        self._respawn_timers.extend([self._soldier_stats.respawn] * max(0, deficit))

        pending: list[float] = []
        for timer in self._respawn_timers:
            timer -= dt
            if timer <= 0.0:
                self._spawn_soldier()
            else:
                pending.append(timer)
        self._respawn_timers = pending

    # Линейный поиск ближайшего врага к каждому содладу. Алгоритм.
    def _assign_targets(self, enemies: list[Enemy]) -> None:
        free_soldiers = [s for s in self.soldiers if s.target is None]
        if not free_soldiers:
            return
        leash = self.stats.range
        candidates = [
            e for e in enemies
            if e.alive and e.blocker is None and self.rally_point.distance_to(e.position) <= leash
        ]
        for soldier in free_soldiers:
            if not candidates:
                break
            target = min(candidates, key=lambda e: soldier.position.distance_to(e.position))
            candidates.remove(target)
            soldier.engage(target)


def make_tower(blueprint: TowerBlueprint, slot_index: int, position: Vec2) -> Tower:
    """Создаёт нужный тип башни по данным: есть солдаты -> казарма, иначе проектильная."""
    if blueprint.base_levels[0].soldier is not None:
        return BarracksTower(blueprint, slot_index, position)
    return ProjectileTower(blueprint, slot_index, position)
