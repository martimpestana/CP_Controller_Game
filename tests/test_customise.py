import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from railgame import render, skins
from railgame.settings import Settings
from railgame.themes import THEMES


def test_every_skin_draws_on_the_map_and_in_the_menu():
    pygame.init()
    screen = pygame.Surface((400, 200))
    for kind in skins.TRAIN_TYPES:
        for skin, _ in skins.SKINS[kind]:
            skins.draw_preview(screen, kind, skin, 60, 100, 3.0, (90, 160, 255), 1.0)
            # On the map the train can point any way, also straight up.
            skins.draw_car(screen, (200, 50), (200, 80), kind, skin, (255, 150, 60), 0, 2, 1.0, 0.0)


def test_every_train_type_has_all_six_skins():
    ids = [sid for sid, _ in skins.SKINS["R"]]
    for kind in skins.TRAIN_TYPES:
        assert [sid for sid, _ in skins.SKINS[kind]] == ids
        for sid in ids:
            assert (kind, sid) in skins.DRAW


def test_choices_are_saved_and_loaded(tmp_path):
    path = tmp_path / "settings.json"
    settings = Settings.load(path)
    assert settings.skin("R") == "real" and settings.theme == "night"
    settings.set_skin("R", "dragon")
    settings.set_skin("IR", "not-a-skin")  # ignored
    settings.set_theme("sunset")
    again = Settings.load(path)
    assert again.skin("R") == "dragon"
    assert again.skin("IR") == "real"
    assert again.theme == "sunset"


def test_a_broken_settings_file_falls_back_to_the_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{not json")
    assert Settings.load(path).theme == "night"


def test_customise_screen_changes_skin_and_theme(tmp_path, monkeypatch):
    from railgame import settings as settings_module
    from railgame.game import Game

    monkeypatch.setattr(settings_module, "SETTINGS_FILE", tmp_path / "settings.json")
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    try:
        game = Game(screen)
        game.settings = Settings.load(tmp_path / "settings.json")
        game.do("customise")
        game.draw()
        assert not any(a.startswith("skin:IR:") for _, a in game.buttons)  # only the open tab shows
        rect = next(r for r, a in game.buttons if a == "tab:IR")
        game.click(rect.center)
        game.draw()
        action = next(a for _, a in game.buttons if a == "skin:IR:gem")
        rect = next(r for r, a in game.buttons if a == action)
        game.click(rect.center)
        assert game.settings.skin("IR") == "gem"
        rect = next(r for r, a in game.buttons if a == "theme:retro")
        game.click(rect.center)
        assert render.LAND == THEMES["retro"]["LAND"]
        game.start_level(1)
        assert game.renderer.skins["IR"] == "gem"
        game.sim.advance(600)
        game.draw()
    finally:
        render.apply_theme(THEMES["night"])
        pygame.quit()
