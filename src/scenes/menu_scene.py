"""Главное меню: новая игра / продолжить / выход (кнопки мышью)."""

import pygame

import config
from src.scenes.scene import Scene, SceneManager
from src.view.button import MenuButton
from src.view.draw_utils import draw_text_center

_CENTER_X = config.WINDOW_WIDTH // 2


class MenuScene(Scene):
    def __init__(self, manager: SceneManager) -> None:
        super().__init__(manager)
        self._build_buttons()

    def _build_buttons(self) -> None:
        """Собрать кнопки меню (пересобираем при смене размера, чтобы обновить подпись)."""
        self.buttons = [
            MenuButton((_CENTER_X, 320), "Новая игра", self._new_game),
            MenuButton((_CENTER_X, 395), "Продолжить игру", self._continue),
            MenuButton((_CENTER_X, 470), "Выход", self.manager.request_quit),
            MenuButton((_CENTER_X, 560), f"Размер экрана: {self.viewport.label()}",
                       self._cycle_resolution, width=420, height=52, size=26),
            MenuButton((_CENTER_X, 622), "Полный экран", self._toggle_fullscreen,
                       width=420, height=52, size=26),
        ]

    def _cycle_resolution(self) -> None:
        self.viewport.cycle_resolution()
        self._build_buttons()

    def _toggle_fullscreen(self) -> None:
        self.viewport.toggle_fullscreen()
        self._build_buttons()

    def _new_game(self) -> None:
        self.context.new_game()
        self._open_map()

    def _continue(self) -> None:
        self._open_map()

    def _open_map(self) -> None:
        from src.scenes.world_map_scene import WorldMapScene

        self.manager.change(WorldMapScene(self.manager))

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._handle_buttons(event):
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.manager.request_quit()

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        draw_text_center(surface, config.TITLE, 72, 200, config.COLOR_ACCENT)
        self._draw_buttons(surface)
