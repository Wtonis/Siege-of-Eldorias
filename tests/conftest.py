"""Общие фикстуры тестов. Гарантирует, что корень проекта в sys.path (для import config)."""

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.model.level.loader import LevelLoader


@pytest.fixture(scope="session")
def loader() -> LevelLoader:
    return LevelLoader(_ROOT / "data", _ROOT / "levels")


@pytest.fixture(scope="session")
def enemies(loader):
    return loader.load_enemy_catalog()


@pytest.fixture(scope="session")
def towers(loader):
    return loader.load_tower_catalog()
