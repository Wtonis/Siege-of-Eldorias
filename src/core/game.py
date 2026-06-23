"""
Игровой цикл и запуск приложения.
Модель обновляется фиксированным шагом FIXED_DT, рендер - каждый кадр.
Аккумулятор копит реальное время и тратит его шагами симуляции.
"""
from pathlib import Path as FilePath
import pygame
import config
from src.core.context import GameContext
from src.core.event_bus import EventBus
from src.core.viewport import Viewport
from src.scenes.scene import SceneManager

_BASE_DIR = FilePath(__file__).resolve().parents[2]
_MOUSE_EVENTS = (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION)


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.viewport: Viewport = Viewport(_BASE_DIR)
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.running: bool = False

        self.event_bus: EventBus = EventBus()
        self.context: GameContext = GameContext(_BASE_DIR)
        self.scenes: SceneManager = SceneManager(self.event_bus, self.context, self.viewport)

        from src.scenes.menu_scene import MenuScene

        self.scenes.change(MenuScene(self.scenes))

    def run(self) -> None:
        self.running = True
        accumulator = 0.0
        while self.running:
            frame_time = self.clock.tick(config.FPS) / 1000.0
            frame_time = min(frame_time, config.MAX_FRAME_TIME)
            accumulator += frame_time * self.scenes.current.time_scale  # реальное время -> игровое

            self._process_input()
            while accumulator >= config.FIXED_DT:
                self.scenes.current.update(config.FIXED_DT)
                accumulator -= config.FIXED_DT
            self._render()

            if self.scenes.quit_requested:
                self.running = False

        pygame.quit()

    def _process_input(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue
            if event.type in _MOUSE_EVENTS:
                canvas_pos = self.viewport.to_canvas(event.pos)
                event = pygame.event.Event(event.type, {**event.dict, "pos": canvas_pos})
            self.scenes.current.handle_event(event)

    def _render(self) -> None:
        canvas = self.viewport.canvas
        canvas.fill(config.COLOR_BG)
        self.scenes.current.render(canvas)
        self.viewport.present()
