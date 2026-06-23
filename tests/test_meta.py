"""Синергии расстановки и мета-прогрессия (очки, ветки, сохранение)."""
from src.core.event_bus import EventBus
from src.core.save_manager import SaveManager
from src.model.entities.tower import make_tower
from src.model.level.level import Level
from src.model.meta.progression import Progression


def test_adjacent_archers_get_synergy(loader, enemies, towers):
    data = loader.load_level("level1.json")
    level = Level(data, enemies, loader.load_ballista_levels(), loader.load_synergies(),
                  set(), EventBus())
    level.economy.gold = 9999
    level.build_tower(make_tower(towers["archer"], 0, data.slots[0].position))
    a1 = level.world.tower_at(0)
    base_rate = a1.effective_fire_rate
    level.build_tower(make_tower(towers["archer"], 1, data.slots[1].position))

    assert a1.active_synergies
    assert a1.effective_fire_rate > base_rate           
    assert (0, 1) in level.world.synergy_links

    level.sell_tower(1)
    assert a1.active_synergies == [] and level.world.synergy_links == set()


def test_progression_points_unlock_and_stars():
    p = Progression(["level1", "level2", "level3"])
    assert p.is_unlocked("level1") and not p.is_unlocked("level2")

    assert p.complete_level("level1", reward_points=2, stars=3) is True
    assert p.points == 2 and p.is_unlocked("level2") and p.get_stars("level1") == 3

    assert p.complete_level("level1", reward_points=2, stars=1) is False
    assert p.points == 2 and p.get_stars("level1") == 3


def test_branch_unlock_costs_points():
    p = Progression(["level1"])
    p.points = 2
    assert p.unlock_branch("archer:poison", cost=2) is True
    assert p.points == 0 and p.is_branch_unlocked("archer:poison")
    assert p.unlock_branch("mage:frost", cost=3) is False


def test_save_load_round_trip(tmp_path):
    ids = ["level1", "level2", "level3"]
    p = Progression(ids)
    p.complete_level("level1", reward_points=3, stars=2)
    p.unlock_branch("archer:musket", cost=0)

    sm = SaveManager(tmp_path / "savegame.json")
    sm.save(p)
    loaded = sm.load(ids)

    assert loaded.points == p.points
    assert loaded.completed_levels == p.completed_levels
    assert loaded.unlocked_levels == p.unlocked_levels
    assert loaded.unlocked_branches == p.unlocked_branches
    assert loaded.stars == p.stars


def test_load_missing_file_is_fresh(tmp_path):
    fresh = SaveManager(tmp_path / "none.json").load(["level1", "level2"])
    assert fresh.points == 0 and fresh.unlocked_levels == {"level1"}
