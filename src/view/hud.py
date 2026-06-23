"""
HUD - интерфейс боя: золото/жизни/волна и панель действий по слоту.
build_buttons - чистая функция раскладки кнопок по состоянию: её зовёт и отрисовка,
и контроллер для попадания кликом. Так геометрия кнопок задана в одном месте.
HUD только читает модель; команды выполняет контроллер.
"""

from dataclasses import dataclass

import pygame

import config
from src.model.entities.tower import TowerBlueprint
from src.model.level.level import BattleState, Level
from src.view.draw_utils import draw_text, draw_text_center

# Раскладка панели действий (внизу экрана).
_PANEL_TOP = 556
_BUTTON_Y = 596
_BUTTON_W = 220
_BUTTON_H = 64
_BUTTON_GAP = 16
_BUTTON_X0 = 20
_CALL_WAVE_RECT = pygame.Rect(910, 6, 250, 40)


@dataclass(frozen=True)
class Button:
    rect: pygame.Rect
    label: str
    sublabel: str
    action: str
    enabled: bool


class Hud:
    def __init__(self, tower_catalog: dict[str, TowerBlueprint]) -> None:
        self.catalog: dict[str, TowerBlueprint] = tower_catalog

    def build_buttons(self, level: Level, selected_slot: int | None,
                      ballista_selected: bool = False) -> list[Button]:
        if ballista_selected:
            return self._ballista_menu(level)
        if selected_slot is None:
            return []
        slot = level.world.slots[selected_slot]
        if not slot.occupied:
            return self._build_menu(level)
        return self._tower_menu(level, selected_slot)

    def _ballista_menu(self, level: Level) -> list[Button]:
        ballista = level.world.ballista
        if not ballista.can_upgrade:
            return []
        cost = ballista.upgrade_cost
        return [Button(self._slot_rect(0), "Апгрейд баллисты", f"{cost} з",
                       "ballista_upgrade", level.economy.gold >= cost)]

    def _build_menu(self, level: Level) -> list[Button]:
        gold = level.economy.gold
        buttons: list[Button] = []
        for i, kind in enumerate(self.catalog):
            cost = self.catalog[kind].base_levels[0].cost
            buttons.append(Button(
                rect=self._slot_rect(i),
                label=config.TOWER_NAMES.get(kind, kind),
                sublabel=f"{cost} з",
                action=f"build:{kind}",
                enabled=gold >= cost,
            ))
        return buttons

    def _tower_menu(self, level: Level, slot_index: int) -> list[Button]:
        tower = level.world.tower_at(slot_index)
        if tower is None:
            return []
        buttons: list[Button] = []
        column = 0
        if tower.can_upgrade:
            cost = tower.upgrade_cost
            buttons.append(Button(self._slot_rect(column), "Апгрейд", f"{cost} з",
                                  "upgrade", level.economy.gold >= cost))
            column += 1
        elif tower.can_specialize:
            for key, name, cost in level.available_specializations(slot_index):
                buttons.append(Button(self._slot_rect(column), name, f"{cost} з",
                                      f"specialize:{key}", level.economy.gold >= cost))
                column += 1
        refund = int(tower.invested * config.SELL_REFUND_RATIO)
        buttons.append(Button(self._slot_rect(column), "Продать", f"+{refund} з", "sell", True))
        return buttons

    def _slot_rect(self, column: int) -> pygame.Rect:
        x = _BUTTON_X0 + column * (_BUTTON_W + _BUTTON_GAP)
        return pygame.Rect(x, _BUTTON_Y, _BUTTON_W, _BUTTON_H)

    def call_wave_button(self, level: Level) -> Button | None:
        """Кнопка досрочного вызова волны (None, если сейчас недоступна)."""
        if not level.can_call_next_wave():
            return None
        return Button(_CALL_WAVE_RECT, f"Волна раньше (+{level.early_call_bonus()} з)",
                      "", "call_wave", True)

    def draw(self, surface: pygame.Surface, level: Level, selected_slot: int | None,
             ballista_selected: bool = False) -> None:
        self._draw_top_bar(surface, level)
        self._draw_call_wave(surface, level)
        self._draw_panel(surface, level, selected_slot, ballista_selected)
        if level.state is not BattleState.RUNNING:
            self._draw_outcome(surface, level)

    def _draw_call_wave(self, surface: pygame.Surface, level: Level) -> None:
        button = self.call_wave_button(level)
        if button is None:
            return
        pygame.draw.rect(surface, config.COLOR_BUTTON, button.rect, border_radius=6)
        pygame.draw.rect(surface, config.COLOR_ACCENT, button.rect, 2, border_radius=6)
        draw_text(surface, button.label, 22, (button.rect.x + 12, button.rect.y + 9), config.COLOR_ACCENT)

    def _draw_top_bar(self, surface: pygame.Surface, level: Level) -> None:
        draw_text(surface, f"Золото: {level.economy.gold}", 28, (20, 12), config.COLOR_ACCENT)
        draw_text(surface, f"Жизни: {level.economy.base_lives}", 28, (220, 12))
        wave = f"Волна: {level.waves.current_wave_number}/{level.waves.total_waves}"
        draw_text(surface, wave, 28, (420, 12))
        ballista = level.world.ballista
        if ballista.is_ready:
            draw_text(surface, "Баллиста (S): готова", 28, (640, 12), config.COLOR_ACCENT)
        else:
            draw_text(surface, f"Баллиста (S): {int(ballista.reload_progress * 100)}%", 28,
                      (640, 12), config.COLOR_TEXT_DIM)

    def _draw_panel(self, surface: pygame.Surface, level: Level, selected_slot: int | None,
                    ballista_selected: bool) -> None:
        panel = pygame.Rect(0, _PANEL_TOP, config.WINDOW_WIDTH, config.WINDOW_HEIGHT - _PANEL_TOP)
        pygame.draw.rect(surface, config.COLOR_PANEL_BG, panel)
        pygame.draw.line(surface, config.COLOR_PANEL_BORDER, (0, _PANEL_TOP), (config.WINDOW_WIDTH, _PANEL_TOP), 2)

        if ballista_selected:
            ballista = level.world.ballista
            draw_text(surface, f"Баллиста   ур. {ballista.level_index + 1}   (клик по полю — выстрел)",
                      24, (_BUTTON_X0, _PANEL_TOP + 12), config.COLOR_ACCENT)
            for button in self._ballista_menu(level):
                self._draw_button(surface, button)
            return
        if selected_slot is None:
            draw_text(surface, "Выберите слот для постройки  ·  S — баллиста", 24,
                      (_BUTTON_X0, _PANEL_TOP + 16), config.COLOR_TEXT_DIM)
            return
        self._draw_header(surface, level, selected_slot)
        for button in self.build_buttons(level, selected_slot):
            self._draw_button(surface, button)
        tower = level.world.tower_at(selected_slot)
        if tower is not None and tower.can_specialize and not level.available_specializations(selected_slot):
            draw_text(surface, "Ветки закрыты — откройте в магазине", 24,
                      (self._slot_rect(1).x, _BUTTON_Y + 20), config.COLOR_TEXT_DIM)

    def _draw_header(self, surface: pygame.Surface, level: Level, selected_slot: int) -> None:
        tower = level.world.tower_at(selected_slot)
        if tower is None:
            draw_text(surface, "Построить башню:", 24, (_BUTTON_X0, _PANEL_TOP + 12), config.COLOR_TEXT_DIM)
            return
        name = config.TOWER_NAMES.get(tower.kind, tower.kind)
        branch = f" — {tower.branch_name}" if tower.branch_name else ""
        draw_text(surface, f"{name}{branch}   ур. {tower.level_index + 1}", 24,
                  (_BUTTON_X0, _PANEL_TOP + 12), config.COLOR_ACCENT)
        if tower.active_synergies:
            draw_text(surface, "Синергия: " + ", ".join(tower.active_synergies), 22,
                      (_BUTTON_X0 + 320, _PANEL_TOP + 14), config.COLOR_SYNERGY)

    def _draw_button(self, surface: pygame.Surface, button: Button) -> None:
        bg = config.COLOR_BUTTON if button.enabled else config.COLOR_BUTTON_DISABLED
        text_color = config.COLOR_TEXT if button.enabled else config.COLOR_TEXT_DIM
        pygame.draw.rect(surface, bg, button.rect, border_radius=6)
        pygame.draw.rect(surface, config.COLOR_BUTTON_BORDER, button.rect, 2, border_radius=6)
        draw_text(surface, button.label, 26, (button.rect.x + 14, button.rect.y + 8), text_color)
        draw_text(surface, button.sublabel, 22, (button.rect.x + 14, button.rect.y + 36), config.COLOR_TEXT_DIM)

    def _draw_outcome(self, surface: pygame.Surface, level: Level) -> None:
        won = level.state is BattleState.WON
        title = "Победа!" if won else "Поражение"
        color = config.COLOR_ACCENT if won else config.COLOR_DEFEAT
        draw_text_center(surface, title, 72, 260, color)
        draw_text_center(surface, "Enter — на карту мира", 30, 340, config.COLOR_TEXT_DIM)
