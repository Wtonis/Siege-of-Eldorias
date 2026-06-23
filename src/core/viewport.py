"""
Viewport - связывает внутренний холст игры с реальным окном.
Вся игра рисуется на холсте фиксированного размера (config.WINDOW_WIDTH*HEIGHT),
а потом растягивается под окно любого размера с сохранением пропорций.
Благодаря этому ни одна игровая координата, уровень, HUD и
шрифт не зависят от размера окна - мы лишь масштабируем готовую картинку.

Здесь же живёт перевод координат мыши «окно - холст»: клик приходит в координатах
окна, а игре нужны координаты холста. Выбор размера сохраняется в settings.json.
"""
import json
from pathlib import Path as FilePath
import pygame
import config


class Viewport:
    def __init__(self, base_dir: FilePath) -> None:
        self.settings_path: FilePath = base_dir / "settings.json"
        self.canvas: pygame.Surface = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        self.resolution_index: int = 0
        self.fullscreen: bool = False
        self.scale: float = 1.0
        self.offset_x: float = 0.0
        self.offset_y: float = 0.0
        self.screen: pygame.Surface = pygame.Surface((0, 0))
        self._load_settings()
        self.apply()

    def apply(self) -> None:
        """Пересоздать окно по текущему выбору и пересчитать масштаб/поля."""
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(config.RESOLUTIONS[self.resolution_index])
        pygame.display.set_caption(config.TITLE)
        window_w, window_h = self.screen.get_size()
        self.scale = min(window_w / config.WINDOW_WIDTH, window_h / config.WINDOW_HEIGHT)
        drawn_w = config.WINDOW_WIDTH * self.scale
        drawn_h = config.WINDOW_HEIGHT * self.scale
        self.offset_x = (window_w - drawn_w) / 2
        self.offset_y = (window_h - drawn_h) / 2

    def present(self) -> None:
        """Растянуть холст под окно (с полями по краям) и показать кадр."""
        target = (int(config.WINDOW_WIDTH * self.scale), int(config.WINDOW_HEIGHT * self.scale))
        scaled = pygame.transform.smoothscale(self.canvas, target)
        self.screen.fill((0, 0, 0))
        self.screen.blit(scaled, (int(self.offset_x), int(self.offset_y)))
        pygame.display.flip()

    def to_canvas(self, pos: tuple[int, int]) -> tuple[int, int]:
        """Перевести координаты окна в координаты холста (обратно к выводу картинки)."""
        x = (pos[0] - self.offset_x) / self.scale
        y = (pos[1] - self.offset_y) / self.scale
        return int(x), int(y)

    def mouse_pos(self) -> tuple[int, int]:
        """Позиция мыши в координатах холста (для наведения и прицела)."""
        return self.to_canvas(pygame.mouse.get_pos())

    def cycle_resolution(self) -> None:
        """Переключить оконный размер на следующий пресет (выключает полный экран)."""
        self.fullscreen = False
        self.resolution_index = (self.resolution_index + 1) % len(config.RESOLUTIONS)
        self.apply()
        self._save_settings()

    def toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        self.apply()
        self._save_settings()

    def label(self) -> str:
        """Подпись текущего режима для кнопки меню."""
        if self.fullscreen:
            return "полный экран"
        width, height = config.RESOLUTIONS[self.resolution_index]
        return f"{width}x{height}"

    def _load_settings(self) -> None:
        if not self.settings_path.exists():
            return
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        index = data.get("resolution_index", 0)
        if 0 <= index < len(config.RESOLUTIONS):
            self.resolution_index = index
        self.fullscreen = bool(data.get("fullscreen", False))

    def _save_settings(self) -> None:
        data = {"resolution_index": self.resolution_index, "fullscreen": self.fullscreen}
        self.settings_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
