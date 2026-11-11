"""The browser version uses the fonts that ship with the game instead of system fonts."""

from pathlib import Path

import pygame

from railgame import ui

GAME_DIR = Path(ui.__file__).parent


def used_characters() -> set[str]:
    text = "".join(p.read_text(encoding="utf-8") for p in GAME_DIR.glob("*.py"))
    return {c for c in text if c.isprintable() and not c.isspace()}


def test_browser_fonts_have_every_character_the_game_writes(monkeypatch):
    pygame.font.init()
    monkeypatch.setattr(ui, "IN_BROWSER", True)
    for bold in (False, True):
        f = ui.font(16, bold=bold)
        missing = [c for c in used_characters() if f.metrics(c)[0] is None]
        assert not missing, f"bold={bold} misses {missing}"


def test_browser_font_falls_back_when_the_file_is_missing(monkeypatch, tmp_path):
    pygame.font.init()
    monkeypatch.setattr(ui, "IN_BROWSER", True)
    monkeypatch.setattr(ui, "FONT_DIR", tmp_path)
    assert ui.font(16).size("Faro")[0] > 0


def test_smoothing_the_canvas_does_nothing_on_the_desktop():
    ui.smooth_browser_canvas()  # must not fail outside the browser
