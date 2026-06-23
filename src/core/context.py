"""
GameContext - общие для всех сцен данные и сервисы.
Каталоги/кампания грузятся один раз при старте, профиль игрока (Progression) -
единый экземпляр на всю сессию, персист через SaveManager. Сцены берут это из
менеджера сцен, чтобы не загружать одно и то же повторно.
"""
from pathlib import Path as FilePath
from src.core.save_manager import SaveManager
from src.model.entities.ballista import BallistaStats
from src.model.entities.enemy import EnemyStats
from src.model.entities.tower import TowerBlueprint
from src.model.level.loader import LevelLoader
from src.model.meta.campaign import CampaignLevel
from src.model.meta.progression import Progression
from src.model.systems.synergy import SynergyRule


class GameContext:
    def __init__(self, base_dir: FilePath) -> None:
        self.loader: LevelLoader = LevelLoader(base_dir / "data", base_dir / "levels")
        self.tower_catalog: dict[str, TowerBlueprint] = self.loader.load_tower_catalog()
        self.enemy_catalog: dict[str, EnemyStats] = self.loader.load_enemy_catalog()
        self.ballista_levels: list[BallistaStats] = self.loader.load_ballista_levels()
        self.synergy_rules: list[SynergyRule] = self.loader.load_synergies()
        self.campaign: list[CampaignLevel] = self.loader.load_campaign()

        self.save_manager: SaveManager = SaveManager(base_dir / "savegame.json")
        self.progression: Progression = self.save_manager.load([lvl.id for lvl in self.campaign])

    def level_by_id(self, level_id: str) -> CampaignLevel:
        for lvl in self.campaign:
            if lvl.id == level_id:
                return lvl
        raise ValueError(f"Нет уровня с id: {level_id!r}")

    def new_game(self) -> None:
        """Сбросить профиль (новая игра) и сохранить."""
        self.progression = Progression([lvl.id for lvl in self.campaign])
        self.save()

    def save(self) -> None:
        self.save_manager.save(self.progression)
