"""
Renderer - рисует мир боя, ТОЛЬКО читая модель (ничего в ней не меняет).
Пока без спрайтов: примитивы (линии, круги).
"""
import pygame
import config
from src.model.entities.ballista import Ballista
from src.model.entities.bolt import Bolt
from src.model.entities.enemy import Enemy
from src.model.entities.projectile import Projectile
from src.model.entities.soldier import Soldier
from src.model.entities.tower import Tower
from src.model.level.level import Level
from src.model.level.path import Path
from src.model.systems.effects import EffectKind
from src.model.vector import Vec2


def _p(vec: Vec2) -> tuple[int, int]:
    return int(vec.x), int(vec.y)


class Renderer:
    def draw(self, surface: pygame.Surface, level: Level, selected_slot: int | None,
             ballista_selected: bool = False, aim_point: tuple[int, int] | None = None) -> None:
        world = level.world
        self._draw_path(surface, world.path)
        self._draw_slots(surface, world.slots, selected_slot)
        self._draw_synergy_links(surface, world.slots, world.synergy_links)
        self._draw_towers(surface, world.towers, selected_slot)
        self._draw_soldiers(surface, world.soldiers)
        self._draw_ballista(surface, world.ballista, ballista_selected, aim_point)
        self._draw_enemies(surface, world.enemies)
        self._draw_projectiles(surface, world.projectiles)
        self._draw_bolts(surface, world.bolts)

    def _draw_path(self, surface: pygame.Surface, path: Path) -> None:
        points = [_p(point) for point in path.waypoints]
        pygame.draw.lines(surface, config.COLOR_PATH, False, points, config.PATH_WIDTH)

    def _draw_slots(self, surface: pygame.Surface, slots, selected_slot: int | None) -> None:
        for slot in slots:
            center = _p(slot.position)
            if not slot.occupied:
                pygame.draw.circle(surface, config.COLOR_SLOT, center, config.SLOT_RADIUS, 3)
            if slot.index == selected_slot:
                pygame.draw.circle(surface, config.COLOR_SLOT_SELECTED, center, config.SLOT_RADIUS + 4, 2)

    def _draw_synergy_links(self, surface: pygame.Surface, slots, links: set[tuple[int, int]]) -> None:
        for a, b in links:
            start, end = _p(slots[a].position), _p(slots[b].position)
            pygame.draw.line(surface, config.COLOR_SYNERGY, start, end, config.SYNERGY_LINK_WIDTH)
            pygame.draw.circle(surface, config.COLOR_SYNERGY, start, config.SYNERGY_NODE_RADIUS)
            pygame.draw.circle(surface, config.COLOR_SYNERGY, end, config.SYNERGY_NODE_RADIUS)

    def _draw_towers(self, surface: pygame.Surface, towers: list[Tower], selected_slot: int | None) -> None:
        for tower in towers:
            center = _p(tower.position)
            color = config.TOWER_COLORS.get(tower.kind, config.COLOR_TEXT)
            pygame.draw.circle(surface, color, center, config.TOWER_RADIUS)
            self._draw_level_pips(surface, center, tower.level_index + 1)
            if tower.active_synergies:  # значок активной синергии
                pygame.draw.circle(surface, config.COLOR_SYNERGY, center, config.TOWER_RADIUS + 3, 2)
            if tower.slot_index == selected_slot:
                pygame.draw.circle(surface, config.COLOR_RANGE, center, int(tower.effective_range), 1)

    def _draw_level_pips(self, surface: pygame.Surface, center: tuple[int, int], level: int) -> None:
        """Точки-индикаторы текущего уровня башни."""
        cx, cy = center
        for i in range(level):
            x = cx - (level - 1) * 4 + i * 8
            pygame.draw.circle(surface, config.COLOR_BG, (x, cy), 2)

    def _draw_enemies(self, surface: pygame.Surface, enemies: list[Enemy]) -> None:
        for enemy in enemies:
            center = _p(enemy.position)
            radius = int(enemy.stats.radius)
            color = config.ENEMY_COLORS.get(enemy.stats.kind, config.COLOR_ENEMY_DEFAULT)
            pygame.draw.circle(surface, color, center, radius)
            self._draw_effect_rings(surface, enemy, center, radius)
            self._draw_hp_bar(surface, enemy, center, radius)

    def _draw_effect_rings(self, surface: pygame.Surface, enemy: Enemy, center: tuple[int, int],
                           radius: int) -> None:
        kinds = {effect.kind for effect in enemy.effects}
        if EffectKind.SLOW in kinds:
            pygame.draw.circle(surface, config.COLOR_SLOW, center, radius + 2, 2)
        if EffectKind.POISON in kinds:
            pygame.draw.circle(surface, config.COLOR_POISON, center, radius + 4, 2)

    def _draw_hp_bar(self, surface: pygame.Surface, enemy: Enemy, center: tuple[int, int],
                     radius: int) -> None:
        self._draw_health_bar(surface, center, center[1] - radius - 8, enemy.hp / enemy.stats.max_hp)

    def _draw_health_bar(self, surface: pygame.Surface, center: tuple[int, int],
                         top_y: int, fraction: float) -> None:
        """Полоска HP над сущностью (общая для врагов и солдат)."""
        x = center[0] - config.HP_BAR_WIDTH // 2
        pygame.draw.rect(surface, config.COLOR_HP_BG, (x, top_y, config.HP_BAR_WIDTH, config.HP_BAR_HEIGHT))
        pygame.draw.rect(surface, config.COLOR_HP_FG,
                         (x, top_y, int(config.HP_BAR_WIDTH * fraction), config.HP_BAR_HEIGHT))

    def _draw_soldiers(self, surface: pygame.Surface, soldiers: list[Soldier]) -> None:
        for soldier in soldiers:
            center = _p(soldier.position)
            pygame.draw.circle(surface, config.COLOR_SOLDIER, center, config.SOLDIER_RADIUS)
            top_y = center[1] - config.SOLDIER_RADIUS - 7
            self._draw_health_bar(surface, center, top_y, soldier.hp / soldier.max_hp)

    def _draw_projectiles(self, surface: pygame.Surface, projectiles: list[Projectile]) -> None:
        for projectile in projectiles:
            pygame.draw.circle(surface, config.COLOR_PROJECTILE, _p(projectile.position), config.PROJECTILE_RADIUS)

    def _draw_ballista(self, surface: pygame.Surface, ballista: Ballista, selected: bool,
                       aim_point: tuple[int, int] | None) -> None:
        center = _p(ballista.position)
        color = config.COLOR_BALLISTA if ballista.is_ready else config.COLOR_BALLISTA_RELOADING
        if selected and aim_point is not None:
            pygame.draw.line(surface, config.COLOR_AIM, center, aim_point, 2)
        pygame.draw.circle(surface, color, center, config.BALLISTA_RADIUS)
        if selected:
            pygame.draw.circle(surface, config.COLOR_AIM, center, config.BALLISTA_RADIUS + 4, 2)

    def _draw_bolts(self, surface: pygame.Surface, bolts: list[Bolt]) -> None:
        for bolt in bolts:
            pygame.draw.circle(surface, config.COLOR_BOLT, _p(bolt.position), config.BOLT_RADIUS)
