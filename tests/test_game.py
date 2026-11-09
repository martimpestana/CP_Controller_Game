import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from railgame.game import Game
from railgame.levels import LEVELS


def test_every_level_can_be_chosen_from_the_menu_at_the_start():
    pygame.init()
    screen = pygame.display.set_mode((320, 180))
    game = Game(screen)
    game.draw()
    actions = {action for _, action in game.buttons}
    assert {f"level:{info.number}" for info in LEVELS} <= actions
    game.key(pygame.K_0 + len(LEVELS))  # the last level, straight away
    assert game.scene == "playing" and game.level_number == len(LEVELS)


def test_space_carries_on_at_the_speed_used_before_the_pause():
    pygame.init()
    game = Game(pygame.display.set_mode((320, 180)))
    game.start_level(1)
    game.key(pygame.K_4)
    assert game.speed == 20
    game.key(pygame.K_SPACE)
    assert game.speed == 0
    game.key(pygame.K_SPACE)
    assert game.speed == 20
