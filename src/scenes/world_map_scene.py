"""
Карта мира: узлы уровней (открыт / пройден / закрыт).
Узлы и их позиции - из кампании (данные), состояние и звёзды - из Progression.
Клик по узлу открывает меню уровня (название, звёзды, кнопка начать уровень);
сам бой запускается уже кнопкой.
"""
import math
import pygame
import config
from src.model.meta.campaign import CampaignLevel
from src.scenes.scene import Scene, SceneManager
from src.view.button import MenuButton
from src.view.draw_utils import draw_text, draw_text_center, draw_text_centered

_CENTER_X = config.WINDOW_WIDTH // 2
_NODE_RADIUS = 28
_PANEL = pygame.Rect(420, 410, 440, 170)


class WorldMapScene(Scene):
    def __init__(self, manager: SceneManager) -> None:
        super().__init__(manager)
        self._nodes: list[tuple[CampaignLevel, tuple[int, int]]] = [
            (lvl, (int(lvl.map_pos.x), int(lvl.map_pos.y))) for lvl in self.context.campaign
        ]
        self.selected: CampaignLevel | None = None
        self._base_buttons = [
            MenuButton((_CENTER_X - 130, 665), "Магазин", self._open_shop, width=200),
            MenuButton((_CENTER_X + 130, 665), "В меню", self._back_to_menu, width=200),
        ]
        self._refresh_buttons()

    def _refresh_buttons(self) -> None:
        self.buttons = []
        if self.selected is not None and self.context.progression.is_unlocked(self.selected.id):
            self.buttons.append(MenuButton((_CENTER_X, 556), "Начать уровень",
                                           self._start_selected, width=260, height=46, size=26))
        self.buttons += self._base_buttons

    def _start_selected(self) -> None:
        from src.scenes.game_scene import GameScene

        if self.selected is not None:
            self.manager.change(GameScene(self.manager, self.selected.id))

    def _open_shop(self) -> None:
        from src.scenes.shop_scene import ShopScene

        self.manager.change(ShopScene(self.manager))

    def _back_to_menu(self) -> None:
        from src.scenes.menu_scene import MenuScene

        self.manager.change(MenuScene(self.manager))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._click_node(event.pos):
                return
        if self._handle_buttons(event):
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back_to_menu()

    def _click_node(self, pos: tuple[int, int]) -> bool:
        for level, center in self._nodes:
            if (pos[0] - center[0]) ** 2 + (pos[1] - center[1]) ** 2 <= _NODE_RADIUS ** 2:
                self.selected = level
                self._refresh_buttons()
                return True
        return False

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        draw_text_center(surface, "Карта мира", 52, 70, config.COLOR_ACCENT)
        draw_text(surface, f"Очки: {self.context.progression.points}", 30, (30, 28), config.COLOR_SYNERGY)
        self._draw_route(surface)
        for level, center in self._nodes:
            self._draw_node(surface, level, center)
        if self.selected is not None:
            self._draw_panel(surface)
        self._draw_buttons(surface)

    def _draw_route(self, surface: pygame.Surface) -> None:
        for (_, a), (_, b) in zip(self._nodes, self._nodes[1:]):
            pygame.draw.line(surface, config.COLOR_PANEL_BORDER, a, b, 3)

    def _draw_node(self, surface: pygame.Surface, level: CampaignLevel, center: tuple[int, int]) -> None:
        progression = self.context.progression
        unlocked = progression.is_unlocked(level.id)
        if progression.is_completed(level.id):
            color = config.COLOR_SYNERGY
        elif unlocked:
            color = config.COLOR_ACCENT
        else:
            color = config.COLOR_SLOT
        pygame.draw.circle(surface, color, center, _NODE_RADIUS)
        pygame.draw.circle(surface, config.COLOR_BG, center, _NODE_RADIUS, 3)
        if self.selected is not None and self.selected.id == level.id:
            pygame.draw.circle(surface, config.COLOR_TEXT, center, _NODE_RADIUS + 4, 2)
        label = level.name if unlocked else level.name + " (закрыто)"
        text_color = config.COLOR_TEXT if unlocked else config.COLOR_TEXT_DIM
        draw_text_centered(surface, label, 22, (center[0], center[1] + _NODE_RADIUS + 16), text_color)

    def _draw_panel(self, surface: pygame.Surface) -> None:
        level = self.selected
        progression = self.context.progression
        pygame.draw.rect(surface, config.COLOR_PANEL_BG, _PANEL, border_radius=8)
        pygame.draw.rect(surface, config.COLOR_PANEL_BORDER, _PANEL, 2, border_radius=8)
        draw_text_centered(surface, level.name, 30, (_PANEL.centerx, _PANEL.y + 32), config.COLOR_ACCENT)
        if progression.is_unlocked(level.id):
            self._draw_stars(surface, _PANEL.centerx, _PANEL.y + 78, progression.get_stars(level.id))
        else:
            draw_text_centered(surface, "Уровень закрыт", 24, (_PANEL.centerx, _PANEL.y + 78),
                               config.COLOR_TEXT_DIM)

    def _draw_stars(self, surface: pygame.Surface, cx: int, y: int, earned: int) -> None:
        spacing = 46
        for i in range(3):
            self._draw_star(surface, (cx - spacing + i * spacing, y), 16, i < earned)

    def _draw_star(self, surface: pygame.Surface, center: tuple[int, int], radius: int, filled: bool) -> None:
        cx, cy = center
        points = []
        for i in range(10):
            r = radius if i % 2 == 0 else radius * 0.45
            angle = -math.pi / 2 + i * math.pi / 5
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        if filled:
            pygame.draw.polygon(surface, config.COLOR_ACCENT, points)
        else:
            pygame.draw.polygon(surface, config.COLOR_SLOT, points, 2)
