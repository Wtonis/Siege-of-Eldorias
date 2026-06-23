"""
Слот под башню: фиксированная точка, куда можно поставить одну башню.
neighbors - индексы соседних слотов; нужны для синергий.
"""

from src.model.vector import Vec2


class BuildSlot:
    def __init__(self, index: int, position: Vec2, neighbors: list[int] | None = None) -> None:
        self.index: int = index
        self.position: Vec2 = position
        self.neighbors: list[int] = neighbors if neighbors is not None else []
        self.occupied: bool = False
