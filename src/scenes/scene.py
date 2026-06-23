"""
Базовая сцена и менеджер сцен.
Сцена отвечает за один экран: принимает ввод, обновляется и рисует себя.
Переключение экранов идёт через SceneManager.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import pygame
from src.core.event_bus import EventBus
from src.view.button import MenuButton
if TYPE_CHECKING:
    from src.core.context import GameContext
    from src.core.viewport import Viewport


class Scene(ABC):
    # Множитель игрового времени к реальному: 1 — норма, 2 — ускорение,
    # 0 — стоп. Боевая сцена меняет его; остальные оставляют 1.
    time_scale: float = 1.0

    def __init__(self, manager: "SceneManager") -> None:
        self.manager = manager
        self.buttons: list[MenuButton] = []

    @property
    def events(self) -> EventBus:
        return self.manager.event_bus

    @property
    def context(self) -> "GameContext":
        return self.manager.context

    @property
    def viewport(self) -> "Viewport":
        return self.manager.viewport

    def _handle_buttons(self, event: pygame.event.Event) -> bool:
        """Левый клик по кнопке меню: выполняет её действие. True — клик попал."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.handle_click(event.pos):
                    return True
        return False

    def _draw_buttons(self, surface: pygame.Surface) -> None:
        mouse_pos = self.viewport.mouse_pos()
        for button in self.buttons:
            button.draw(surface, mouse_pos)

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None: ...

    @abstractmethod
    def update(self, dt: float) -> None: ...

    @abstractmethod
    def render(self, surface: pygame.Surface) -> None: ...

    def on_enter(self) -> None:
        """Вызывается при входе в сцену (опционально переопределяется)."""

    def on_exit(self) -> None:
        """Вызывается при выходе из сцены (опционально переопределяется)."""


class SceneManager:
    """Хранит активную сцену, общий EventBus и общий GameContext."""

    def __init__(self, event_bus: EventBus, context: "GameContext", viewport: "Viewport") -> None:
        self.event_bus = event_bus
        self.context = context
        self.viewport = viewport
        self._current: Scene | None = None
        self.quit_requested: bool = False

    @property
    def current(self) -> Scene:
        if self._current is None:
            raise RuntimeError("Активная сцена не установлена")
        return self._current

    def change(self, scene: Scene) -> None:
        if self._current is not None:
            self._current.on_exit()
        self._current = scene
        scene.on_enter()

    def request_quit(self) -> None:
        self.quit_requested = True
