"""
Экономика боя: золото на постройку/прокачку и жизни базы.
Чистое состояние с операциями; события о тратах/смертях публикует World.
"""


class Economy:
    def __init__(self, gold: int, base_lives: int) -> None:
        self.gold: int = gold
        self.base_lives: int = base_lives

    def can_afford(self, cost: int) -> bool:
        return self.gold >= cost

    def spend(self, cost: int) -> bool:
        """Списывает золото, если хватает. Возвращает успех операции."""
        if not self.can_afford(cost):
            return False
        self.gold -= cost
        return True

    def add_gold(self, amount: int) -> None:
        self.gold += amount

    def lose_life(self, amount: int) -> None:
        self.base_lives = max(0, self.base_lives - amount)

    @property
    def is_defeated(self) -> bool:
        return self.base_lives <= 0
