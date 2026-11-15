import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from railgame import i18n, skins
from railgame.game import Game
from railgame.levels import LEVELS, LINE_BLURBS
from railgame.themes import THEME_NAMES


# Names that are written the same in Portuguese.
SAME_IN_BOTH = {"Regional", "Inter-Regional", "Regional · Inter-Regional", "Santa Apolónia", "Feira de Beja"}


@pytest.fixture
def portuguese():
    i18n.set_language("pt")
    yield
    i18n.set_language("en")


def test_english_is_shown_as_written():
    i18n.set_language("en")
    assert i18n.t("Drivers' requests") == "Drivers' requests"
    assert i18n.t("Average delay 7.5 min") == "Average delay 7.5 min"


def test_menus_levels_and_names_all_have_portuguese(portuguese):
    texts = ["Choose a line", "How it works", "Customise", "Back", "Next level", "Try again"]
    for levels in LEVELS.values():
        for info in levels:
            texts += [info.title, info.description]
    for where, trains in LINE_BLURBS.values():
        texts += [where, trains]
    texts += [name for _, name in THEME_NAMES]
    texts += [name for kind in skins.SKINS.values() for _, name in kind if name not in ("Real", "Foguete", "Sud Express")]
    missing = [text for text in texts if i18n.t(text) == text and text not in SAME_IN_BOTH]
    assert missing == []


def test_messages_with_names_and_numbers(portuguese):
    assert i18n.t("Level 3 · Rush hour") == "Nível 3 · Hora de ponta"
    assert i18n.t("Average delay 7.5 min") == "Atraso médio 7,5 min"  # a decimal comma
    assert i18n.t("Approaching Ferradosa. Signal FRD-W0 to green, please.") == (
        "A chegar à Ferradosa. Sinal FRD-W0 a verde, por favor.")
    assert i18n.t("Running 3 min late. We'll reach the map at 08:15.") == (
        "Vamos com 3 min de atraso. Chegamos ao mapa às 08:15.")
    assert i18n.t("from Peso da Régua") == "do Peso da Régua"
    assert i18n.t("Some text nobody translated") == "Some text nobody translated"


def test_the_language_button_changes_the_language_and_it_is_remembered(tmp_path):
    from railgame.settings import Settings

    pygame.init()
    game = Game(pygame.display.set_mode((1280, 720)))
    game.settings.path = tmp_path / "settings.json"  # never touch the player's own settings
    i18n.set_language("en")
    try:
        game.draw()  # the main menu: the button is at the top right
        button = next(rect for rect, action in game.buttons if action == "language")
        game.click(button.center)
        assert i18n.LANG == "pt" and Settings.load(tmp_path / "settings.json").language == "pt"
        game.start_level(1, "algarve")
        game.draw()  # in a level it is in the top bar
        game.click(game.renderer.language_button.center)
        assert i18n.LANG == "en" and Settings.load(tmp_path / "settings.json").language == "en"
    finally:
        i18n.set_language("en")
