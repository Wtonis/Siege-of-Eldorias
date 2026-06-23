"""Расчёт урона с учётом сопротивлений."""
from src.model.systems.damage import DamageType, resolve_damage


def test_physical_reduced_by_armor():
    assert resolve_damage(100, DamageType.PHYSICAL, {DamageType.PHYSICAL: 0.4}) == 60


def test_magic_reduced_by_resist():
    assert resolve_damage(100, DamageType.MAGIC, {DamageType.MAGIC: 0.5}) == 50


def test_true_ignores_all_resist():
    resist = {DamageType.PHYSICAL: 0.9, DamageType.MAGIC: 0.9}
    assert resolve_damage(100, DamageType.TRUE, resist) == 100


def test_wrong_resist_type_not_applied():
    # Физброня не снижает магический урон.
    assert resolve_damage(40, DamageType.MAGIC, {DamageType.PHYSICAL: 0.5}) == 40


def test_never_negative():
    assert resolve_damage(20, DamageType.PHYSICAL, {DamageType.PHYSICAL: 1.0}) == 0
