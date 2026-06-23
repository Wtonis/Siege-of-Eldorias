"""
InputHandler - превращает мышь/клавиши в команды модели.
Хранит UI-состояние (выбранный слот, выбрана ли баллиста) - его читают рендер и HUD.
Порядок клика: сначала кнопки панели (та же раскладка, что и отрисовка), затем -
если выбрана баллиста - выстрел в точку, иначе выбор баллисты/слота на поле.
"""
import pygame
import config
from src.model.entities.tower import TowerBlueprint, make_tower
from src.model.level.level import Level
from src.model.vector import Vec2
from src.view.hud import Hud


class InputHandler:
    def __init__(self, level: Level, tower_catalog: dict[str, TowerBlueprint], hud: Hud) -> None:
        self.level: Level = level
        self.catalog: dict[str, TowerBlueprint] = tower_catalog
        self.hud: Hud = hud
        self.selected_slot: int | None = None
        self.ballista_selected: bool = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_s:
            self._toggle_ballista()
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        if self._click_button(event.pos):
            return
        if self._click_call_wave(event.pos):
            return
        if self.ballista_selected:
            self.level.fire_ballista(Vec2(event.pos[0], event.pos[1]))
            return
        if self._click_ballista(event.pos):
            return
        self.selected_slot = self._slot_at(event.pos)

    def _toggle_ballista(self) -> None:
        self.ballista_selected = not self.ballista_selected
        if self.ballista_selected:
            self.selected_slot = None

    def _click_button(self, pos: tuple[int, int]) -> bool:
        for button in self.hud.build_buttons(self.level, self.selected_slot, self.ballista_selected):
            if button.enabled and button.rect.collidepoint(pos):
                self._dispatch(button.action)
                return True
        return False

    def _click_call_wave(self, pos: tuple[int, int]) -> bool:
        button = self.hud.call_wave_button(self.level)
        if button is not None and button.rect.collidepoint(pos):
            self.level.call_next_wave()
            return True
        return False

    def _dispatch(self, action: str) -> None:
        if action.startswith("build:"):
            self._build(action.split(":", 1)[1])
        elif action == "upgrade":
            self.level.upgrade_tower(self.selected_slot)
        elif action.startswith("specialize:"):
            self.level.specialize_tower(self.selected_slot, action.split(":", 1)[1])
        elif action == "sell":
            self.level.sell_tower(self.selected_slot)
            self.selected_slot = None
        elif action == "ballista_upgrade":
            self.level.upgrade_ballista()

    def _build(self, kind: str) -> None:
        slot = self.level.world.slots[self.selected_slot]
        tower = make_tower(self.catalog[kind], slot.index, slot.position)
        self.level.build_tower(tower)

    def _click_ballista(self, pos: tuple[int, int]) -> bool:
        """Клик по орудию выбирает баллисту (дальше левый клик = выстрел)."""
        if Vec2(pos[0], pos[1]).distance_to(self.level.world.ballista.position) <= config.BALLISTA_RADIUS + 6:
            self.ballista_selected = True
            self.selected_slot = None
            return True
        return False

    def _slot_at(self, pos: tuple[int, int]) -> int | None:
        click = Vec2(pos[0], pos[1])
        for slot in self.level.world.slots:
            if click.distance_to(slot.position) <= config.SLOT_RADIUS:
                return slot.index
        return None
