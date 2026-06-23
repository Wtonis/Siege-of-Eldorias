"""
SaveManager - сохранение/загрузка профиля игрока в json-файл.
Персист отделён от модели (Progression - чистая логика, файлы - здесь). Если файла
нет или он битый, возвращается свежий профиль с открытым первым уровнем.
"""

import json
from pathlib import Path as FilePath

from src.model.meta.progression import Progression


class SaveManager:
    def __init__(self, path: FilePath) -> None:
        self.path: FilePath = path

    def load(self, level_ids: list[str]) -> Progression:
        progression = Progression(level_ids)
        if not self.path.exists():
            return progression
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return progression                      # битый файл - начинаем заново

        valid_levels = set(level_ids)
        progression.points = data.get("points", 0)
        progression.completed_levels = set(data.get("completed", [])) & valid_levels
        unlocked = set(data.get("unlocked_levels", [])) & valid_levels
        progression.unlocked_levels = unlocked or progression.unlocked_levels
        progression.unlocked_branches = set(data.get("unlocked_branches", []))
        progression.stars = {k: v for k, v in data.get("stars", {}).items() if k in valid_levels}
        return progression

    def save(self, progression: Progression) -> None:
        data = {
            "points": progression.points,
            "completed": sorted(progression.completed_levels),
            "unlocked_levels": sorted(progression.unlocked_levels),
            "unlocked_branches": sorted(progression.unlocked_branches),
            "stars": progression.stars,
        }
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
