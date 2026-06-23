"""
Типы урона и расчёт урона с учётом сопротивлений врага.
Физический и магический урон снижаются сопротивлением своего типа (доля 0..1),
истинный (true) урон проходит без снижения.
"""

from enum import Enum, auto


class DamageType(Enum):
    PHYSICAL = auto()
    MAGIC = auto()
    TRUE = auto()


def resolve_damage(
    amount: int,
    damage_type: DamageType,
    resistances: dict[DamageType, float],
) -> int:
    """Сколько HP реально снимется с учётом сопротивлений (>= 0)."""
    if damage_type is DamageType.TRUE:
        return max(0, amount)
    reduction = resistances.get(damage_type, 0.0)
    return max(0, round(amount * (1.0 - reduction)))
