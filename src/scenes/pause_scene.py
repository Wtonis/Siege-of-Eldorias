"""Экран паузы поверх боя - кнопки мышью (Esc - быстрое продолжение)."""
import pygame
import config
from src.scenes.scene import Scene, SceneManager
from src.view.button import MenuButton
from src.view.draw_utils import draw_text_center

_CENTER_X = config.WINDOW_WIDTH // 2


class PauseScene(Scene):
    def __init__(self, manager: SceneManager, resume_to: Scene) -> None:
        super().__init__(manager)
        self._resume_to = resume_to
        self.buttons = [
            MenuButton((_CENTER_X, 360), "Продолжить", self._resume),
            MenuButton((_CENTER_X, 440), "В меню", self._to_menu),
        ]

    def _resume(self) -> None:
        self.manager.change(self._resume_to)

    def _to_menu(self) -> None:
        from src.scenes.menu_scene import MenuScene

        self.manager.change(MenuScene(self.manager))

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._handle_buttons(event):
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._resume()

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        draw_text_center(surface, "Пауза", 64, 240, config.COLOR_ACCENT)
        self._draw_buttons(surface)
