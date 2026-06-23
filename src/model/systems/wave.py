"""
WaveManager - исполняет план волн по таймеру.
Конечный автомат одной волны:
  WAITING  - пауза перед волной, затем запуск следующей;
  SPAWNING - выпускаем врагов групп по их интервалам, пока все не выйдут;
  CLEARING - ждём, пока поле очистится (всех убили/пропустили) - волна засчитана;
  FINISHED - все волны пройдены.
Сам менеджер не знает про World: врагов отдаёт через колбэк spawn, а поле чисто
получает параметром - так его легко тестировать без боя.
"""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable
import config
from src.core.event_bus import EventBus
from src.events import WaveCleared
from src.model.entities.enemy import Enemy, EnemyStats
from src.model.level.path import Path
from src.model.level.wave_plan import SpawnGroup, WavePlan

SpawnEnemy = Callable[[Enemy], None]


class WaveState(Enum):
    WAITING = auto()
    SPAWNING = auto()
    CLEARING = auto()
    FINISHED = auto()


@dataclass
class _GroupRunner:
    """Отсчитывает спавны одной группы"""
    group: SpawnGroup
    spawned: int = 0
    timer: float = 0.0

    def __post_init__(self) -> None: # Создает стартувую задержку перед спавном
        self.timer = self.group.start_delay

    @property
    def done(self) -> bool:
        return self.spawned >= self.group.count

    def advance(self, dt: float) -> list[int]:
        """Размеры пачек, которые надо выпустить за этот шаг в размере batch."""
        if self.done:
            return []
        self.timer -= dt
        releases: list[int] = []
        while self.timer <= 0.0 and self.spawned < self.group.count:
            release = min(self.group.batch, self.group.count - self.spawned)
            self.spawned += release
            releases.append(release)
            self.timer += self.group.interval
        return releases


class WaveManager:
    def __init__(
        self,
        waves: list[WavePlan],
        enemy_catalog: dict[str, EnemyStats],
        path: Path,
        spawn: SpawnEnemy,
        events: EventBus,
        wave_gap: float = config.WAVE_GAP,
    ) -> None:
        self.waves: list[WavePlan] = waves
        self.catalog: dict[str, EnemyStats] = enemy_catalog
        self.path: Path = path
        self.spawn: SpawnEnemy = spawn
        self.events: EventBus = events
        self.wave_gap: float = wave_gap

        self.current_index: int = -1
        self.state: WaveState = WaveState.FINISHED if not waves else WaveState.WAITING
        self._gap_timer: float = 0.0            # 0 — первая волна стартует сразу
        self._runners: list[_GroupRunner] = []

    @property
    def finished(self) -> bool:
        return self.state is WaveState.FINISHED

    @property
    def total_waves(self) -> int:
        return len(self.waves)

    @property
    def current_wave_number(self) -> int:
        """Номер текущей волны для HUD (1-based), 0 до старта."""
        return max(0, self.current_index + 1)

    @property
    def _has_next(self) -> bool:
        return self.current_index + 1 < len(self.waves)

    def can_call_next(self) -> bool:
        """Можно ли запустить следующую волну досрочно (в паузе или при дочистке)."""
        return self._has_next and self.state in (WaveState.WAITING, WaveState.CLEARING)

    def early_call_bonus(self) -> int:
        """Награда за досрочный вызов: больше за раньше (за сэкономленное время)."""
        if not self.can_call_next():
            return 0
        seconds = max(0.0, self._gap_timer) if self.state is WaveState.WAITING else self.wave_gap
        return round(seconds * config.EARLY_CALL_GOLD_PER_SEC)

    def call_next(self) -> int:
        """Досрочно запустить следующую волну. Возвращает золотой бонус (0, если нельзя)."""
        if not self.can_call_next():
            return 0
        bonus = self.early_call_bonus()
        self._start_next_wave()
        return bonus

    def update(self, dt: float, field_clear: bool) -> None: # Ждем пока волна опустеет, меняем стостояние волны.
        if self.state is WaveState.WAITING:
            self._gap_timer -= dt
            if self._gap_timer <= 0.0:
                self._start_next_wave()
        elif self.state is WaveState.SPAWNING:
            self._spawn_due(dt)
            if all(runner.done for runner in self._runners):
                self.state = WaveState.CLEARING
        elif self.state is WaveState.CLEARING:
            if field_clear:
                self._finish_current_wave()

    def _spawn_due(self, dt: float) -> None:
        for runner in self._runners:
            for release in runner.advance(dt):
                self._spawn_batch(runner.group.enemy_kind, release)

    def _spawn_batch(self, kind: str, size: int) -> None:
        """Выпустить пачку врагов: одиночка — по центру, несколько — в ряд по дороге."""
        stats = self.catalog[kind]
        for offset in self._lane_offsets(size):
            self.spawn(Enemy(stats, self.path, offset))

    @staticmethod
    def _lane_offsets(size: int) -> list[float]:
        if size <= 1:
            return [0.0]
        half = config.ENEMY_LANE_HALF
        return [-half + 2.0 * half * i / (size - 1) for i in range(size)]

    def _start_next_wave(self) -> None:
        self.current_index += 1
        self._runners = [_GroupRunner(group) for group in self.waves[self.current_index].groups]
        self.state = WaveState.SPAWNING

    def _finish_current_wave(self) -> None:
        self.events.publish(WaveCleared(self.current_index))
        if self.current_index + 1 < len(self.waves):
            self.state = WaveState.WAITING
            self._gap_timer = self.wave_gap
        else:
            self.state = WaveState.FINISHED
