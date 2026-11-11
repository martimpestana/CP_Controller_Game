import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from railgame.game import Game
from railgame.levels import LEVELS


def test_menu_offers_every_line_and_then_its_levels():
    pygame.init()
    game = Game(pygame.display.set_mode((320, 180)))
    game.draw()
    assert {f"line:{key}" for key in LEVELS} <= {action for _, action in game.buttons}
    for i, (key, levels) in enumerate(LEVELS.items(), 1):
        game.scene = "menu"
        game.key(pygame.K_0 + i)
        assert game.scene == "levels" and game.line_key == key
        game.draw()
        actions = {action for _, action in game.buttons}
        assert {f"level:{key}:{info.number}" for info in levels} <= actions
        game.key(pygame.K_0 + len(levels))  # the last level of the line, straight away
        assert game.scene == "playing" and game.level_number == len(levels)
        game.draw()  # the map of every line can be drawn


def test_next_level_stays_on_the_same_line():
    pygame.init()
    game = Game(pygame.display.set_mode((320, 180)))
    game.start_level(1, "douro")
    game.do("next")
    assert game.line_key == "douro" and game.level_number == 2
    assert game.info.line == "douro"


def test_space_carries_on_at_the_speed_used_before_the_pause():
    pygame.init()
    game = Game(pygame.display.set_mode((320, 180)))
    game.start_level(1, "algarve")
    game.key(pygame.K_4)
    assert game.speed == 20
    game.key(pygame.K_SPACE)
    assert game.speed == 0
    game.key(pygame.K_SPACE)
    assert game.speed == 20


def test_menu_button_goes_back_to_the_main_menu():
    pygame.init()
    game = Game(pygame.display.set_mode((1280, 720)))
    game.start_level(1)
    game.draw()
    assert game.renderer.menu_button is not None
    game.click(game.renderer.menu_button.center)
    assert game.scene == "menu"
