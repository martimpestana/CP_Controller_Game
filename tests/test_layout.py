import math
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from railgame.layout import Layout
from railgame.track import algarve_faro_tavira


def test_track_is_continuous_on_screen():
    line = algarve_faro_tavira()
    layout = Layout(line, (40, 100, 800, 400))
    pts = layout.main_track()
    biggest_jump = max(math.dist(a, b) for a, b in zip(pts, pts[1:]))
    assert biggest_jump < 10


def test_track_two_joins_track_one_at_the_points():
    line = algarve_faro_tavira()
    layout = Layout(line, (40, 100, 800, 400))
    for p in line.points:
        assert math.dist(layout.point(p.pos, 1), layout.point(p.pos, 2)) < 0.5


def test_game_draws_a_frame():
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    from railgame.game import Game

    game = Game(screen)
    game.draw()  # menu
    game.start_level(1)
    game.sim.advance(600)
    game.draw()
    pygame.quit()


def test_clicks_work_when_the_window_is_scaled():
    from railgame import ui
    from railgame.game import Game

    pygame.init()
    ui.set_scale(1.5)
    try:
        screen = pygame.display.set_mode((ui.S(1280), ui.S(720)))
        game = Game(screen)
        game.start_level(1)
        signal = game.sim.line.signal("TAV-W0")
        x, y = game.renderer.signal_position(signal)
        assert x > 1000  # Tavira is at the right of a 1280 px window, so beyond 1000 px at 1.5x
        game.click((round(x), round(y)))
        assert signal.green
    finally:
        ui.set_scale(1.0)
        pygame.quit()
