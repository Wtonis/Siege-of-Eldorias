"""
Магазин: разблокировка веток специализаций за очки прогрессии.
Очки копятся за прохождение уровней. Купленная ветка становится доступной к выбору
в бою (строгий замок). Покупка сразу сохраняется в профиль.
"""

from typing import Callable

import pygame

import config
from src.scenes.scene import Scene, SceneManager
from src.view.button import MenuButton
from src.view.draw_utils import draw_text, draw_text_center

_CENTER_X = config.WINDOW_WIDTH // 2
_FIRST_Y = 160
_ROW_STEP = 52


class ShopScene(Scene):
    def __init__(self, manager: SceneManager) -> None:
        super().__init__(manager)
        self._unlocked_rows: list[tuple[int, str]] = []
        self._rebuild()

    def _rebuild(self) -> None:
        """Пересобрать список веток по текущему профилю (после покупки)."""
        self.buttons = []
        self._unlocked_rows = []
        progression = self.context.progression
        row = 0
        for kind, blueprint in self.context.tower_catalog.items():
            for branch_key, branch in blueprint.branches.items():
                key = f"{kind}:{branch_key}"
                name = f"{config.TOWER_NAMES.get(kind, kind)} — {branch.name}"
                y = _FIRST_Y + row * _ROW_STEP
                if progression.is_branch_unlocked(key):
                    self._unlocked_rows.append((y, f"{name}  —  открыто"))
                else:
                    label = f"{name}  ({branch.unlock_cost} оч.)"
                    self.buttons.append(MenuButton((_CENTER_X, y), label,
                                                   self._make_buyer(key, branch.unlock_cost),
                                                   width=620, height=44, size=24))
                row += 1
        self.buttons.append(MenuButton((_CENTER_X, _FIRST_Y + row * _ROW_STEP + 20), "Назад",
                                       self._back, width=200))

    def _make_buyer(self, key: str, cost: int) -> Callable[[], None]:
        def buy() -> None:
            if self.context.progression.unlock_branch(key, cost):
                self.context.save()
                self._rebuild()
        return buy

    def _back(self) -> None:
        from src.scenes.world_map_scene import WorldMapScene

        self.manager.change(WorldMapScene(self.manager))

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._handle_buttons(event):
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back()

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        draw_text_center(surface, "Магазин специализаций", 48, 70, config.COLOR_ACCENT)
        draw_text_center(surface, f"Очки: {self.context.progression.points}", 30, 118, config.COLOR_SYNERGY)
        for y, text in self._unlocked_rows:
            draw_text_center(surface, text, 24, y + 12, config.COLOR_SYNERGY)
        self._draw_buttons(surface)
