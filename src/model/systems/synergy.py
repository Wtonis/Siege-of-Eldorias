"""
SynergySystem - бонусы за соседство башен в слотах.
Правило: башне даётся множитель к статам, если в соседнем занятом слоте стоит башня
нужного типа. Бонус - за факт наличия (не накапливается за количество соседей).
Пересчёт идёт только при изменениях расстановки (build/sell), а не каждый кадр.
Правила лежат в data/synergies.json.

Связи - пары слотов с активной синергией, их рисует view, чтобы игроку
была видна связь между башнями.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.model.entities.tower import Tower
    from src.model.level.slot import BuildSlot


@dataclass(frozen=True)
class SynergyModifiers:
    """Множители к статам башни (1.0 — без изменения)."""
    damage: float = 1.0
    range: float = 1.0
    fire_rate: float = 1.0
    splash: float = 1.0
    soldier_hp: float = 1.0
    soldier_damage: float = 1.0

    def combined(self, other: "SynergyModifiers") -> "SynergyModifiers":
        return SynergyModifiers(
            damage=self.damage * other.damage,
            range=self.range * other.range,
            fire_rate=self.fire_rate * other.fire_rate,
            splash=self.splash * other.splash,
            soldier_hp=self.soldier_hp * other.soldier_hp,
            soldier_damage=self.soldier_damage * other.soldier_damage,
        )


@dataclass(frozen=True)
class SynergyRule:
    tower: str               # тип башни, получающей бонус
    neighbor: str            # тип соседа, активирующего бонус
    name: str                # подпись для UI
    mods: SynergyModifiers


class SynergySystem:
    def __init__(self, rules: list[SynergyRule]) -> None:
        self.rules: list[SynergyRule] = rules
        self.links: set[tuple[int, int]] = set()   # пары слотов с активной синергией

    # Алгоритм для пересчета синергии при измененении расстановки.
    # Синергии пересчитываются только когда меняется расстановка - при постройке или продаже, а не каждый кадр.
    def recompute(self, towers: list["Tower"], slots: list["BuildSlot"]) -> None:
        by_slot = {tower.slot_index: tower for tower in towers}
        self.links = set()
        for tower in towers:
            mods = SynergyModifiers()
            labels: list[str] = []
            neighbors = [(n, by_slot[n]) for n in slots[tower.slot_index].neighbors if n in by_slot]
            for rule in self.rules:
                if rule.tower != tower.kind:
                    continue
                matched = [n for n, neighbor in neighbors if neighbor.kind == rule.neighbor]
                if matched:
                    mods = mods.combined(rule.mods)
                    labels.append(rule.name)
                    for n in matched:
                        self.links.add((min(tower.slot_index, n), max(tower.slot_index, n)))
            tower.modifiers = mods
            tower.active_synergies = labels
