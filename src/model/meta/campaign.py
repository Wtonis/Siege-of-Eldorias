"""
Описание кампании: упорядоченный список уровней для карты мира.
Чистые данные (из levels/campaign.json): порядок задаёт, какой уровень открывается
следующим, map_pos - где рисовать узел на карте. Динамика (что открыто/пройдено) -
в Progression.
"""
from dataclasses import dataclass
from src.model.vector import Vec2


@dataclass(frozen=True)
class CampaignLevel:
    id: str
    file: str           # имя json-файла уровня
    name: str           # отображаемое название
    map_pos: Vec2       # позиция узла на карте мира
