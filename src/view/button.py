"""
MenuButton - кликабельная кнопка меню с подсветкой при наведении.
Один виджет на все экраны меню: хранит прямоугольник, подпись и действие,
сам себя рисует и проверяет попадание клика. Наведение определяется текущей
позицией мыши, поэтому состояние хранить не нужно.
"""
from typing import Callable
import pygame
import config
from src.view.draw_utils import get_font


class MenuButton:
    def __init__(
        self,
        center: tuple[int, int],
        label: str,
        on_click: Callable[[], None],
        width: int = 340,
        height: int = 64,
        size: int = 32,
    ) -> None:
        self.rect: pygame.Rect = pygame.Rect(0, 0, width, height)
        self.rect.center = center
        self.label: str = label
        self.on_click: Callable[[], None] = on_click
        self.size: int = size

    def draw(self, surface: pygame.Surface, mouse_pos: tuple[int, int]) -> None:
        hovered = self.rect.collidepoint(mouse_pos)
        background = config.COLOR_BUTTON_HOVER if hovered else config.COLOR_BUTTON
        pygame.draw.rect(surface, background, self.rect, border_radius=8)
        pygame.draw.rect(surface, config.COLOR_BUTTON_BORDER, self.rect, 2, border_radius=8)
        rendered = get_font(self.size).render(self.label, True, config.COLOR_TEXT)
        surface.blit(rendered, rendered.get_rect(center=self.rect.center))

    def handle_click(self, pos: tuple[int, int]) -> bool:
        if self.rect.collidepoint(pos):
            self.on_click()
            return True
        return False
