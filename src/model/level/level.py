"""
Level - состояние одного боя.
Связывает World (симуляция), WaveManager (тайминг волн) и Economy, задаёт порядок
их обновления и проверяет конец боя:
  поражение - кончились жизни базы;
  победа - все волны пройдены (последняя зачтена только при чистом поле).
Дискретные исходы (LevelCompleted/LevelFailed) уходят в EventBus.
"""
from enum import Enum, auto
from src.core.event_bus import EventBus
from src.events import LevelCompleted, LevelFailed
from src.model.entities.ballista import Ballista, BallistaStats
from src.model.entities.enemy import EnemyStats
from src.model.entities.tower import Tower
from src.model.level.level_data import LevelData
from src.model.systems.economy import Economy
from src.model.systems.synergy import SynergyRule, SynergySystem
from src.model.systems.wave import WaveManager
from src.model.vector import Vec2
from src.model.world import World


class BattleState(Enum):
    RUNNING = auto()
    WON = auto()
    LOST = auto()


class Level:
    def __init__(
        self,
        data: LevelData,
        enemy_catalog: dict[str, EnemyStats],
        ballista_levels: list[BallistaStats],
        synergy_rules: list[SynergyRule],
        unlocked_branches: set[str],
        event_bus: EventBus,
    ) -> None:
        self.data: LevelData = data
        self.events: EventBus = event_bus
        self.unlocked_branches: set[str] = unlocked_branches
        self.economy: Economy = Economy(data.start_gold, data.start_lives)
        ballista = Ballista(ballista_levels, data.ballista_pos)
        synergy = SynergySystem(synergy_rules)
        self.world: World = World(data.path, data.slots, self.economy, ballista, synergy, event_bus)
        self.waves: WaveManager = WaveManager(
            data.waves, enemy_catalog, data.path, self.world.spawn_enemy, event_bus
        )
        self.state: BattleState = BattleState.RUNNING

    def update(self, dt: float) -> None:
        if self.state is not BattleState.RUNNING:
            return
        field_clear = len(self.world.enemies) == 0
        self.waves.update(dt, field_clear)
        self.world.update(dt)
        self._check_end()

    def build_tower(self, tower: Tower) -> bool:
        return self.world.build_tower(tower)

    def upgrade_tower(self, slot_index: int) -> bool:
        return self.world.upgrade_tower(slot_index)

    def available_specializations(self, slot_index: int) -> list[tuple[str, str, int]]:
        """Ветки башни, открытые в магазине."""
        tower = self.world.tower_at(slot_index)
        if tower is None:
            return []
        return [
            option for option in tower.specializations()
            if f"{tower.kind}:{option[0]}" in self.unlocked_branches
        ]

    def specialize_tower(self, slot_index: int, branch_key: str) -> bool:
        tower = self.world.tower_at(slot_index)
        if tower is None or f"{tower.kind}:{branch_key}" not in self.unlocked_branches:
            return False
        return self.world.specialize_tower(slot_index, branch_key)

    def sell_tower(self, slot_index: int) -> bool:
        return self.world.sell_tower(slot_index)

    def can_call_next_wave(self) -> bool:
        return self.waves.can_call_next()

    def early_call_bonus(self) -> int:
        return self.waves.early_call_bonus()

    def call_next_wave(self) -> bool:
        """Досрочный вызов волны: начисляет золотой бонус."""
        if not self.waves.can_call_next():
            return False
        self.economy.add_gold(self.waves.call_next())
        return True

    def fire_ballista(self, target: Vec2) -> bool:
        return self.world.fire_ballista(target)

    def upgrade_ballista(self) -> bool:
        return self.world.upgrade_ballista()

    def _check_end(self) -> None:
        if self.economy.is_defeated:
            self.state = BattleState.LOST
            self.events.publish(LevelFailed(self.data.level_id))
        elif self.waves.finished:
            self.state = BattleState.WON
            self.events.publish(LevelCompleted(self.data.level_id, self.data.reward_points))
