"""
Болт баллисты: летит прямой наводкой и пробивает несколько врагов.
Болт движется по фиксированному направлению, бьёт каждого врага на пути и гаснет, 
исчерпав пробитие или дальность.
Коллизии и урон считает World (у болта нет доступа к списку врагов); болт помнит,
кого уже задел, чтобы не бить одного дважды.
"""

from src.model.systems.damage import DamageType
from src.model.vector import Vec2


class Bolt:
    def __init__(self) -> None:
        self.active: bool = False
        self.position: Vec2 = Vec2()
        self.direction: Vec2 = Vec2()
        self.speed: float = 0.0
        self.damage: int = 0
        self.damage_type: DamageType = DamageType.PHYSICAL
        self.pierce_remaining: int = 0
        self.max_range: float = 0.0
        self.traveled: float = 0.0
        self.hit_ids: set[int] = set()

    def reset(
        self,
        origin: Vec2,
        direction: Vec2,
        damage: int,
        damage_type: DamageType,
        speed: float,
        pierce: int,
        max_range: float,
    ) -> None:
        self.active = True
        self.position = origin
        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.damage_type = damage_type
        self.pierce_remaining = pierce
        self.max_range = max_range
        self.traveled = 0.0
        self.hit_ids = set()

    def update(self, dt: float) -> None:
        if not self.active:
            return
        step = self.speed * dt
        self.position += self.direction * step
        self.traveled += step
        if self.traveled >= self.max_range:
            self.active = False
