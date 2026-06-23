"""
Progression - профиль игрока между боями.
Хранит, какие уровни открыты/пройдены, накопленные очки и разблокированные ветки
специализаций (ключ "kind:branch", напр. "archer:poison"). Чистая логика без файлов
и pygame.
"""


class Progression:
    def __init__(self, level_ids: list[str]) -> None:
        self.level_ids: list[str] = level_ids
        self.unlocked_levels: set[str] = {level_ids[0]} if level_ids else set()
        self.completed_levels: set[str] = set()
        self.stars: dict[str, int] = {}                 # лучший результат уровня
        self.points: int = 0
        self.unlocked_branches: set[str] = set()

    def is_unlocked(self, level_id: str) -> bool:
        return level_id in self.unlocked_levels

    def is_completed(self, level_id: str) -> bool:
        return level_id in self.completed_levels

    def complete_level(self, level_id: str, reward_points: int, stars: int = 0) -> bool:
        """Отметить уровень пройденным: очки даются за ПЕРВОЕ прохождение, затем
        открывается следующий уровень. Звёзды запоминаются как лучший результат.
        Возвращает True, если уровень пройден впервые."""
        first_time = level_id not in self.completed_levels
        self.completed_levels.add(level_id)
        if first_time:
            self.points += reward_points
            self._unlock_next(level_id)
        self.stars[level_id] = max(self.stars.get(level_id, 0), stars)
        return first_time

    def get_stars(self, level_id: str) -> int:
        return self.stars.get(level_id, 0)

    def _unlock_next(self, level_id: str) -> None:
        index = self.level_ids.index(level_id)
        if index + 1 < len(self.level_ids):
            self.unlocked_levels.add(self.level_ids[index + 1])

    def is_branch_unlocked(self, branch_key: str) -> bool:
        return branch_key in self.unlocked_branches

    def unlock_branch(self, branch_key: str, cost: int) -> bool:
        """Купить ветку за очки. False - уже открыта или не хватает очков."""
        if branch_key in self.unlocked_branches or self.points < cost:
            return False
        self.points -= cost
        self.unlocked_branches.add(branch_key)
        return True
