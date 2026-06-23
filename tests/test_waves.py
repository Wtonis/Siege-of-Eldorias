"""WaveManager: спавн, групповой выпуск (batch), конечный автомат, ранний вызов."""
import config
from src.core.event_bus import EventBus
from src.model.level.path import Path
from src.model.level.wave_plan import SpawnGroup, WavePlan
from src.model.systems.wave import WaveManager, WaveState
from src.model.vector import Vec2

DT = 1.0 / 60.0


def _manager(waves, enemies):
    spawned = []
    wm = WaveManager(waves, enemies, Path([Vec2(0, 0), Vec2(500, 0)]),
                     lambda e: spawned.append(e), EventBus())
    return wm, spawned


def test_spawns_exact_count(enemies):
    wm, spawned = _manager([WavePlan([SpawnGroup("goblin", count=5, interval=0.5, start_delay=0.0)])], enemies)
    for _ in range(600):
        wm.update(DT, field_clear=False)
    assert len(spawned) == 5


def test_batch_releases_row_at_once(enemies):
    wm, spawned = _manager([WavePlan([SpawnGroup("goblin", count=6, interval=1.0, start_delay=0.0, batch=3)])], enemies)
    for _ in range(3):
        wm.update(DT, field_clear=False)
        if spawned:
            break
    assert len(spawned) == 3
    offsets = sorted(e._lane_offset for e in spawned)
    assert offsets == [-config.ENEMY_LANE_HALF, 0.0, config.ENEMY_LANE_HALF]


def test_finishes_after_last_wave_cleared(enemies):
    wm, _ = _manager([WavePlan([SpawnGroup("goblin", count=2, interval=0.3, start_delay=0.0)])], enemies)
    for _ in range(600):
        wm.update(DT, field_clear=True)
    assert wm.finished


def test_early_call_available_while_clearing_and_gives_bonus(enemies):
    waves = [WavePlan([SpawnGroup("goblin", count=2, interval=0.2, start_delay=0.0)]),
             WavePlan([SpawnGroup("goblin", count=2, interval=0.2, start_delay=0.0)])]
    wm, _ = _manager(waves, enemies)
    for _ in range(600):
        wm.update(DT, field_clear=False)
        if wm.state is WaveState.CLEARING:
            break
    assert wm.can_call_next()
    bonus = wm.call_next()
    assert bonus == round(config.WAVE_GAP * config.EARLY_CALL_GOLD_PER_SEC)
    assert wm.state is WaveState.SPAWNING and wm.current_index == 1
