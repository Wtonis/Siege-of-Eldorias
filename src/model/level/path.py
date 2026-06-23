"""
Путь врагов: ломаная из waypoints от входа до базы.
Геометрия маршрута; движение по нему - забота Enemy (он хранит свой индекс).
"""

from src.model.vector import Vec2


class Path:
    def __init__(self, waypoints: list[Vec2]) -> None:
        if len(waypoints) < 2:
            raise ValueError("Путь должен содержать хотя бы 2 точки")
        self.waypoints: list[Vec2] = waypoints

    @property
    def start(self) -> Vec2:
        """Точка появления врагов."""
        return self.waypoints[0]

    def waypoint(self, index: int) -> Vec2:
        return self.waypoints[index]

    def is_last(self, index: int) -> bool:
        """index указывает на конечную точку (базу)."""
        return index >= len(self.waypoints) - 1
