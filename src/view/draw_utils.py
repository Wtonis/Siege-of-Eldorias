"""Мелкие помощники отрисовки, общие для сцен."""

import pygame
import config

_font_cache: dict[int, pygame.font.Font] = {}


def get_font(size: int) -> pygame.font.Font:
    """Кэшируем шрифты по размеру: создание Font на каждый кадр дорого."""
    if size not in _font_cache:
        _font_cache[size] = pygame.font.SysFont("arial", size)
    return _font_cache[size]


def draw_text_center(
    surface: pygame.Surface,
    text: str,
    size: int,
    y: int,
    color: tuple[int, int, int] = config.COLOR_TEXT,
) -> None:
    """Рисует строку по центру по горизонтали на высоте y."""
    rendered = get_font(size).render(text, True, color)
    rect = rendered.get_rect(center=(config.WINDOW_WIDTH // 2, y))
    surface.blit(rendered, rect)


def draw_text(
    surface: pygame.Surface,
    text: str,
    size: int,
    pos: tuple[int, int],
    color: tuple[int, int, int] = config.COLOR_TEXT,
) -> None:
    """Рисует строку от левого верхнего угла pos."""
    rendered = get_font(size).render(text, True, color)
    surface.blit(rendered, pos)


def draw_text_centered(
    surface: pygame.Surface,
    text: str,
    size: int,
    center: tuple[int, int],
    color: tuple[int, int, int] = config.COLOR_TEXT,
) -> None:
    """Рисует строку по центру относительно произвольной точки center."""
    rendered = get_font(size).render(text, True, color)
    surface.blit(rendered, rendered.get_rect(center=center))
