"""
LevelLoader превращает json-данные в объекты модели.
Каталоги врагов/башен задают баланс, level*.json (levels/) — карту и
волны. Загрузчик не зависит от pygame и принимает пути снаружи (легко тестировать
на любой папке). Числовые характеристики живут только в данных, не в коде.
"""
import json
from pathlib import Path as FilePath
import config
from src.model.entities.ballista import BallistaStats
from src.model.entities.enemy import EnemyStats
from src.model.entities.soldier import SoldierStats
from src.model.entities.tower import TowerBlueprint, TowerBranch, TowerStats
from src.model.level.level_data import LevelData
from src.model.level.path import Path
from src.model.meta.campaign import CampaignLevel
from src.model.level.slot import BuildSlot
from src.model.level.wave_plan import SpawnGroup, WavePlan
from src.model.systems.damage import DamageType
from src.model.systems.effects import EffectKind, EffectSpec
from src.model.systems.synergy import SynergyModifiers, SynergyRule
from src.model.vector import Vec2


def _damage_type(name: str) -> DamageType:
    try:
        return DamageType[name.upper()]
    except KeyError:
        raise ValueError(f"Неизвестный тип урона: {name!r}")


def _resistances(raw: dict[str, float]) -> dict[DamageType, float]:
    return {_damage_type(name): value for name, value in raw.items()}


def _effect_spec(raw: dict) -> EffectSpec:
    try:
        kind = EffectKind[raw["kind"].upper()]
    except KeyError:
        raise ValueError(f"Неизвестный эффект: {raw['kind']!r}")
    return EffectSpec(kind=kind, magnitude=raw["magnitude"], duration=raw["duration"])


def _vec(pair: list[float]) -> Vec2:
    return Vec2(pair[0], pair[1])


def _read_json(file: FilePath) -> dict:
    return json.loads(file.read_text(encoding="utf-8"))


class LevelLoader:
    def __init__(self, data_dir: FilePath, levels_dir: FilePath) -> None:
        self.data_dir: FilePath = data_dir
        self.levels_dir: FilePath = levels_dir

    def load_enemy_catalog(self) -> dict[str, EnemyStats]:
        raw = _read_json(self.data_dir / "enemies.json")
        return {
            kind: EnemyStats(
                kind=kind,
                max_hp=entry["max_hp"],
                speed=entry["speed"],
                reward=entry["reward"],
                base_damage=entry["base_damage"],
                attack_damage=entry.get("attack_damage", 0),
                attack_rate=entry.get("attack_rate", 1.0),
                radius=entry.get("radius", float(config.ENEMY_RADIUS)),
                resistances=_resistances(entry.get("resistances", {})),
            )
            for kind, entry in raw.items()
        }

    def load_tower_catalog(self) -> dict[str, TowerBlueprint]:
        """Каждый тип башни -> дерево прокачки (базовые уровни + ветки)."""
        raw = _read_json(self.data_dir / "towers.json")
        return {kind: self._blueprint(kind, entry) for kind, entry in raw.items()}

    def _blueprint(self, kind: str, entry: dict) -> TowerBlueprint:
        base_levels = [self._tower_level(kind, level) for level in entry["levels"]]
        branches = {
            key: TowerBranch(
                key=key,
                name=branch["name"],
                levels=[self._tower_level(kind, level) for level in branch["levels"]],
                unlock_cost=branch.get("unlock_cost", 0),
            )
            for key, branch in entry.get("branches", {}).items()
        }
        return TowerBlueprint(kind=kind, base_levels=base_levels, branches=branches)

    def _tower_level(self, kind: str, level: dict) -> TowerStats:
        soldier_raw = level.get("soldier")
        effect_raw = level.get("effect")
        damage_type = level.get("damage_type")
        return TowerStats(
            kind=kind,
            cost=level["cost"],
            range=level["range"],
            fire_rate=level.get("fire_rate", 1.0),
            damage=level.get("damage", 0),
            damage_type=_damage_type(damage_type) if damage_type else DamageType.PHYSICAL,
            projectile_speed=level.get("projectile_speed", 0.0),
            splash_radius=level.get("splash_radius", 0.0),
            soldier=SoldierStats(**soldier_raw) if soldier_raw else None,
            effect=_effect_spec(effect_raw) if effect_raw else None,
        )

    def load_ballista_levels(self) -> list[BallistaStats]:
        raw = _read_json(self.data_dir / "ballista.json")
        return [
            BallistaStats(
                cost=level["cost"],
                damage=level["damage"],
                reload=level["reload"],
                pierce=level["pierce"],
                bolt_speed=level["bolt_speed"],
                range=level["range"],
                damage_type=_damage_type(level["damage_type"]) if level.get("damage_type") else DamageType.PHYSICAL,
            )
            for level in raw["levels"]
        ]

    def load_synergies(self) -> list[SynergyRule]:
        raw = _read_json(self.data_dir / "synergies.json")
        return [
            SynergyRule(
                tower=rule["tower"],
                neighbor=rule["neighbor"],
                name=rule["name"],
                mods=SynergyModifiers(
                    damage=rule.get("damage", 1.0),
                    range=rule.get("range", 1.0),
                    fire_rate=rule.get("fire_rate", 1.0),
                    splash=rule.get("splash", 1.0),
                    soldier_hp=rule.get("soldier_hp", 1.0),
                    soldier_damage=rule.get("soldier_damage", 1.0),
                ),
            )
            for rule in raw
        ]

    def load_campaign(self) -> list[CampaignLevel]:
        raw = json.loads((self.levels_dir / "campaign.json").read_text(encoding="utf-8"))
        return [
            CampaignLevel(id=item["id"], file=item["file"], name=item["name"],
                          map_pos=_vec(item["map_pos"]))
            for item in raw
        ]

    def load_level(self, level_file: str) -> LevelData:
        raw = _read_json(self.levels_dir / level_file)
        path = Path([_vec(point) for point in raw["path"]])
        slots = [
            BuildSlot(slot["index"], _vec(slot["position"]), slot.get("neighbors", []))
            for slot in raw["slots"]
        ]
        waves = [self._parse_wave(wave) for wave in raw["waves"]]
        ballista_pos = _vec(raw["ballista"]) if "ballista" in raw else path.waypoints[-1]
        return LevelData(
            level_id=raw["id"],
            start_gold=raw["start_gold"],
            start_lives=raw["start_lives"],
            path=path,
            slots=slots,
            waves=waves,
            ballista_pos=ballista_pos,
            reward_points=raw.get("reward_points", 1),
        )

    def _parse_wave(self, raw: dict) -> WavePlan:
        groups = [
            SpawnGroup(
                enemy_kind=group["enemy"],
                count=group["count"],
                interval=group["interval"],
                start_delay=group.get("start_delay", 0.0),
                batch=group.get("batch", 1),
            )
            for group in raw["groups"]
        ]
        return WavePlan(groups)
