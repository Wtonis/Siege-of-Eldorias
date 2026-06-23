"""Экономика боя: золото и жизни базы."""
from src.model.systems.economy import Economy


def test_spend_succeeds_when_affordable():
    eco = Economy(gold=100, base_lives=10)
    assert eco.spend(70) is True
    assert eco.gold == 30


def test_spend_fails_when_too_expensive():
    eco = Economy(gold=50, base_lives=10)
    assert eco.spend(70) is False
    assert eco.gold == 50


def test_add_gold():
    eco = Economy(gold=0, base_lives=10)
    eco.add_gold(15)
    assert eco.gold == 15


def test_lose_life_clamps_at_zero_and_marks_defeat():
    eco = Economy(gold=0, base_lives=2)
    eco.lose_life(5)
    assert eco.base_lives == 0
    assert eco.is_defeated is True


def test_not_defeated_with_lives():
    assert Economy(0, 1).is_defeated is False
