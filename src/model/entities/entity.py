"""
Базовая сущность поля боя.
Общее у всех «вещей» на поле: уникальный id, позиция, признак жизни и шаг
обновления. Конкретное поведение в подклассах.
"""

from src.model.vector import Vec2


class Entity:
    # Общий счётчик id на весь класс: нужен событиям (EnemyKilled.enemy_id и т.п.).
    _next_id: int = 1

    def __init__(self, position: Vec2) -> None:
        self.id: int = Entity._next_id
        Entity._next_id += 1
        self.position: Vec2 = position
        self.alive: bool = True

    def update(self, dt: float) -> None:
        """Шаг симуляции (игровые секунды). Переопределяется в подклассах."""
