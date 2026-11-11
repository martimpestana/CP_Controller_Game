import math
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from railgame.layout import Layout
from railgame.track import LINES


@pytest.mark.parametrize("key", LINES)
def test_track_is_continuous_on_screen(key):
    line = LINES[key]()
    layout = Layout(line, (40, 100, 800, 400))
    pts = layout.main_track()
    biggest_jump = max(math.dist(a, b) for a, b in zip(pts, pts[1:]))
    assert biggest_jump < 10


@pytest.mark.parametrize("key", LINES)
def test_track_two_joins_track_one_at_the_points(key):
    line = LINES[key]()
    layout = Layout(line, (40, 100, 800, 400))
    for p in line.points:
        assert math.dist(layout.point(p.pos, 1), layout.point(p.pos, 2)) < 0.5


@pytest.mark.parametrize("key", LINES)
def test_station_boxes_never_overlap(key):
    line = LINES[key]()
    layout = Layout(line, line.geo.map_box or (40, 176, 820, 414))
    centres = sorted(layout.station_px.values())
    assert all(b - a >= 2 * layout.zone_px for a, b in zip(centres, centres[1:]))


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
        assert x > 1000  # Tavira is at about x=760 in a 1280 px window
        game.click((round(x), round(y)))
        assert signal.green
    finally:
        ui.set_scale(1.0)
        pygame.quit()


def test_train_tags_never_cover_each_other():
    """On the busiest Oeste level the tags of trains passing close together move apart."""
    import pygame

    from railgame import render
    from railgame.levels import build_level
    from tests.test_simulation import careful_player_move

    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    info, sim = build_level("oeste", 8)
    renderer = render.Renderer(sim)
    for step in range(1500):
        careful_player_move(sim)
        sim.advance(2)
        if sim.over:
            break
        if step % 5:
            continue
        renderer.draw(screen, info, 1, (0, 0), None)
        tags = [box for i, (box, _) in enumerate(renderer.train_boxes) if i % 2 == 0]
        for i, a in enumerate(tags):
            assert not any(a.colliderect(b) for b in tags[i + 1 :])
