"""
План волн: ЧТО и КОГДА спаунить (только описание, без тайминга).
Тайминг (отсчёт задержек, выпуск врагов) исполняет WaveManager.
Здесь лежат неизменяемые данные, прочитанные из level.json.
SpawnGroup - порция врагов в волне.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SpawnGroup: 
    enemy_kind: str
    count: int            # всего врагов в группе
    interval: float       # секунд между релизами внутри группы
    start_delay: float    # секунд от начала волны до первого релиза группы
    batch: int = 1        # сколько врагов выпускать за один релиз (идут в ряд)


@dataclass(frozen=True)
class WavePlan:
    groups: list[SpawnGroup]
