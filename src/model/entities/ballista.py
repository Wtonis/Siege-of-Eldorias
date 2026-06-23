"""
Баллиста - орудие под ручным управлением.
FSM: READY -> (выстрел) -> RELOADING -> (таймер) -> READY. Стрелять можно только
в состоянии READY. Сам болт создаёт World (у орудия нет доступа к врагам), 
баллиста лишь следит за состоянием и перезарядкой.
"""
from dataclasses import dataclass
from enum import Enum, auto
from src.model.systems.damage import DamageType
from src.model.vector import Vec2

# Автомат состояния балисты (FSM)
class BallistaState(Enum):
    READY = auto()
    RELOADING = auto()


@dataclass
class BallistaStats:
    """Характеристики баллисты на одном уровне (из данных)."""
    cost: int                   
    damage: int
    reload: float               
    pierce: int                 # сколько врагов пробивает болт
    bolt_speed: float
    range: float                # макс дальность полёта болта
    damage_type: DamageType = DamageType.PHYSICAL


class Ballista:
    def __init__(self, levels: list[BallistaStats], position: Vec2) -> None:
        self.levels: list[BallistaStats] = levels
        self.level_index: int = 0
        self.position: Vec2 = position
        self.state: BallistaState = BallistaState.READY
        self.invested: int = 0
        self._reload_timer: float = 0.0

    # Хранит хар-ки нужного уровня по индексу. При абгрейде индекс + 1.
    @property
    def stats(self) -> BallistaStats:
        return self.levels[self.level_index]

    @property
    def is_ready(self) -> bool:
        return self.state is BallistaState.READY

    @property
    def reload_progress(self) -> float:
        """Насколько перезарядилась балиста (1 - готова, 0 - нет)."""
        if self.is_ready:
            return 1.0
        return 1.0 - self._reload_timer / self.stats.reload

    @property
    def can_upgrade(self) -> bool:
        return self.level_index + 1 < len(self.levels)

    @property
    def upgrade_cost(self) -> int:
        return self.levels[self.level_index + 1].cost if self.can_upgrade else 0

    def upgrade(self) -> None:
        if self.can_upgrade:
            self.level_index += 1

    def fire(self) -> bool:
        """Перевести в перезарядку, если готова. True — выстрел разрешён."""
        if not self.is_ready:
            return False
        self.state = BallistaState.RELOADING
        self._reload_timer = self.stats.reload
        return True

    def update(self, dt: float) -> None:
        if self.state is BallistaState.RELOADING:
            self._reload_timer -= dt
            if self._reload_timer <= 0.0:
                self._reload_timer = 0.0
                self.state = BallistaState.READY
