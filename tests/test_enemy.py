"""Враг: урон/смерть, доход до базы, эффекты (яд/замедление)."""
import pytest

from src.model.entities.enemy import Enemy, EnemyState, EnemyStats
from src.model.level.path import Path
from src.model.systems.damage import DamageType
from src.model.systems.effects import EffectKind, EffectSpec
from src.model.vector import Vec2

DT = 1.0 / 60.0


def make_path() -> Path:
    return Path([Vec2(0, 0), Vec2(100, 0)])


def make_stats(**kw) -> EnemyStats:
    base = dict(kind="t", max_hp=50, speed=100, reward=5, base_damage=2)
    base.update(kw)
    return EnemyStats(**base)


def test_takes_damage_with_resist_and_dies():
    e = Enemy(make_stats(max_hp=50, resistances={DamageType.PHYSICAL: 0.5}), make_path())
    e.take_damage(40, DamageType.PHYSICAL)
    assert e.hp == 30 and e.alive
    e.take_damage(100, DamageType.PHYSICAL)
    assert e.hp == 0 and not e.alive and e.state is EnemyState.DEAD


def test_reaches_base():
    e = Enemy(make_stats(speed=100), make_path())
    for _ in range(120):
        e.update(DT)
        if e.reached_base:
            break
    assert e.reached_base


def test_poison_is_true_damage_and_kills():
    # Орк с физброней: яд должен проходить мимо брони и добить.
    e = Enemy(make_stats(max_hp=40, speed=0, resistances={DamageType.PHYSICAL: 0.9}), make_path())
    e.apply_effect(EffectSpec(EffectKind.POISON, magnitude=20, duration=5))
    elapsed = 0.0
    while e.alive and elapsed < 5:
        e.update(DT)
        elapsed += DT
    assert not e.alive and elapsed < 3


def test_slow_reduces_progress():
    normal = Enemy(make_stats(speed=100), make_path())
    slowed = Enemy(make_stats(speed=100), make_path())
    slowed.apply_effect(EffectSpec(EffectKind.SLOW, magnitude=0.5, duration=10))
    for _ in range(30):
        normal.update(DT)
        slowed.update(DT)
    assert slowed.progress == pytest.approx(normal.progress * 0.5, rel=0.05)
