"""
Сцена боя: связывает модель (Level) с рендером, HUD и вводом.
Сцена - тонкий слой: грузит выбранный уровень из общего контекста, передаёт dt
в модель и события - в контроллер, рисует через Renderer/Hud. На победе начисляет
очки прогрессии и сохраняет профиль. Игровая логика живёт в модели, не здесь.
"""

import pygame
from src.controller.input_handler import InputHandler
from src.model.level.level import BattleState, Level
from src.scenes.scene import Scene, SceneManager
from src.view.hud import Hud
from src.view.renderer import Renderer


class GameScene(Scene):
    def __init__(self, manager: SceneManager, level_id: str) -> None:
        super().__init__(manager)
        ctx = self.context
        self.level_id = level_id
        campaign_level = ctx.level_by_id(level_id)
        level_data = ctx.loader.load_level(campaign_level.file)

        self.level = Level(level_data, ctx.enemy_catalog, ctx.ballista_levels,
                           ctx.synergy_rules, ctx.progression.unlocked_branches, self.events)
        self.renderer = Renderer()
        self.hud = Hud(ctx.tower_catalog)
        self.input = InputHandler(self.level, ctx.tower_catalog, self.hud)
        self._result_recorded = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from src.scenes.pause_scene import PauseScene

            self.manager.change(PauseScene(self.manager, resume_to=self))
            return
        if self.level.state is not BattleState.RUNNING:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                from src.scenes.world_map_scene import WorldMapScene

                self.manager.change(WorldMapScene(self.manager))
            return
        self.input.handle_event(event)

    def update(self, dt: float) -> None:
        self.level.update(dt)
        self._record_result_once()

    def _record_result_once(self) -> None:
        if self._result_recorded or self.level.state is BattleState.RUNNING:
            return
        self._result_recorded = True
        if self.level.state is BattleState.WON:
            self.context.progression.complete_level(
                self.level_id, self.level.data.reward_points, self._stars_earned())
            self.context.save()

    def _stars_earned(self) -> int:
        """3 звезды — без потерь жизней, 2 — потеряно до половины, 1 — победа на последних."""
        lives = self.level.economy.base_lives
        start = self.level.data.start_lives
        if lives >= start:
            return 3
        if lives * 2 >= start:
            return 2
        return 1

    def render(self, surface: pygame.Surface) -> None:
        aim_point = self.viewport.mouse_pos() if self.input.ballista_selected else None
        self.renderer.draw(surface, self.level, self.input.selected_slot,
                           self.input.ballista_selected, aim_point)
        self.hud.draw(surface, self.level, self.input.selected_slot, self.input.ballista_selected)
