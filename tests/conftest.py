"""Shared set-up for the tests."""

import pytest

from railgame import custom


@pytest.fixture(autouse=True)
def own_levels_file(tmp_path, monkeypatch):
    """Tests never read or write the player's own levels (the level editor's file)."""
    monkeypatch.setattr(custom, "LEVELS_FILE", tmp_path / "levels.json")
