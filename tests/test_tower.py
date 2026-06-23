"""Башни: выбор цели, уровни прокачки, замок специализаций."""
from src.core.event_bus import EventBus
from src.model.entities.enemy import Enemy, EnemyStats
from src.model.entities.tower import ProjectileTower, make_tower
from src.model.level.level import Level
from src.model.level.path import Path
from src.model.vector import Vec2


def _enemy(progress: float, pos: Vec2) -> Enemy:
    e = Enemy(EnemyStats(kind="t", max_hp=50, speed=10, reward=1, base_damage=1),
              Path([Vec2(0, 0), Vec2(1000, 0)]))
    e.progress = progress
    e.position = pos
    return e


def test_target_priority_is_furthest_progress(towers):
    tower = ProjectileTower(towers["archer"], 0, Vec2(0, 0))
    near = _enemy(progress=5, pos=Vec2(50, 0))
    leader = _enemy(progress=20, pos=Vec2(120, 0))
    assert tower._select_target([near, leader]) is leader


def test_target_none_when_out_of_range(towers):
    tower = ProjectileTower(towers["archer"], 0, Vec2(0, 0))
    far = _enemy(progress=99, pos=Vec2(500, 0))       # вне радиуса лучника (160)
    assert tower._select_target([far]) is None


def test_levels_then_specialization(towers):
    tower = make_tower(towers["archer"], 0, Vec2(0, 0))
    assert tower.level_index == 0 and tower.can_upgrade
    tower.upgrade()
    tower.upgrade()
    assert tower.level_index == 2 and not tower.can_upgrade
    assert tower.can_specialize


def test_specialization_locked_until_unlocked(loader, enemies, towers):
    data = loader.load_level("level1.json")
    unlocked: set[str] = set()
    level = Level(data, enemies, loader.load_ballista_levels(), loader.load_synergies(),
                  unlocked, EventBus())
    level.economy.gold = 9999
    level.build_tower(make_tower(towers["archer"], 0, data.slots[0].position))
    level.upgrade_tower(0)
    level.upgrade_tower(0)


    assert level.available_specializations(0) == []
    assert level.specialize_tower(0, "poison") is False


    unlocked.add("archer:poison")
    assert any(key == "poison" for key, _, _ in level.available_specializations(0))
    assert level.specialize_tower(0, "poison") is True
    assert level.world.tower_at(0).branch_key == "poison"
