import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from railgame import render
from railgame.game import Game
from railgame.render import Renderer
from railgame.themes import THEMES


@pytest.fixture(autouse=True)
def restore_theme():
    yield
    render.apply_theme(THEMES["night"])


def algarve_renderer(theme: str) -> Renderer:
    pygame.init()
    game = Game(pygame.display.set_mode((1280, 720)))
    render.apply_theme(THEMES[theme])
    game.start_level(3, "algarve")
    game.renderer.info = game.info
    return game.renderer


def frame(renderer: Renderer, speed: int, ticks: int, monkeypatch) -> pygame.Surface:
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: ticks)
    screen = pygame.Surface((1280, 720))
    renderer.draw(screen, renderer.info, speed, (0, 0), None)
    return screen


@pytest.mark.parametrize("theme", ["day", "night"])
def test_day_and_night_get_the_storybook_map(theme):
    r = algarve_renderer(theme)
    assert r.storybook and r.night == (theme == "night")
    assert r.wave_marks and r.lamp
    assert bool(r.windows) == (theme == "night")  # only night has windows that light up


@pytest.mark.parametrize("theme", ["sunset", "retro"])
def test_other_themes_keep_the_original_map(theme):
    r = algarve_renderer(theme)
    assert not r.storybook and r.plain
    assert not r.wave_marks and r.lamp is None


def test_waves_move_only_while_the_trains_run(monkeypatch):
    r = algarve_renderer("day")
    frame(r, 5, 1000, monkeypatch)
    paused = frame(r, 0, 3000, monkeypatch)
    assert r.sea_time == 0
    paused_again = frame(r, 0, 5000, monkeypatch)
    assert pygame.image.tobytes(paused, "RGB") == pygame.image.tobytes(paused_again, "RGB")
    moving = frame(r, 5, 5050, monkeypatch)
    assert r.sea_time > 0
    assert pygame.image.tobytes(moving, "RGB") != pygame.image.tobytes(paused_again, "RGB")


def test_at_night_the_lights_change_over_time(monkeypatch):
    r = algarve_renderer("night")
    a = frame(r, 0, 1000, monkeypatch)
    b = frame(r, 0, 2500, monkeypatch)  # paused: the lighthouse and windows still go on
    assert pygame.image.tobytes(a, "RGB") != pygame.image.tobytes(b, "RGB")


def test_the_lighthouse_beam_only_sweeps_over_the_sea(monkeypatch):
    import math

    r = algarve_renderer("night")
    seen = []
    real_polygon = pygame.draw.polygon

    def spy(surface, colour, points, *args):
        if colour == (110, 96, 50):  # the bright core of the beam
            (cx, cy), a, b = points
            seen.append(math.atan2(((a[1] + b[1]) / 2 - cy) / 0.6, (a[0] + b[0]) / 2 - cx))
        return real_polygon(surface, colour, points, *args)

    monkeypatch.setattr(pygame.draw, "polygon", spy)
    for t in range(0, 20000, 250):
        frame(r, 0, t, monkeypatch)
    away = [abs((angle - r.sea_angle + math.pi) % (2 * math.pi) - math.pi) for angle in seen]
    assert seen and max(away) < math.pi / 2  # never more than a quarter turn from straight out to sea
    assert max(away) > 1.0  # but it does sweep from side to side


@pytest.mark.parametrize("theme", ["day", "night"])
def test_station_names_have_no_white_box_on_a_window_with_alpha(theme, monkeypatch):
    """On macOS the window surface can have an alpha channel. Names must not get a white box."""
    r = algarve_renderer(theme)
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 1000)
    screen = pygame.Surface((1280, 720), pygame.SRCALPHA)
    r.draw(screen, r.info, 0, (0, 0), None)
    faro = next(st for st in r.sim.line.stations if st.name == "Faro")
    x, y = r.layout.local(faro, 0, 52)
    w, h = r.f_bold.size("Faro")
    corners = [(x - w / 2 + 1, y - h / 2 + 1), (x + w / 2 - 1, y - h / 2 + 1), (x - w / 2 + 1, y + h / 2 - 1)]
    for cx, cy in corners:  # the corners of the label box are map, not white
        assert screen.get_at((int(cx), int(cy)))[:3] != (255, 255, 255)


def line_renderer(line: str, theme: str) -> Renderer:
    pygame.init()
    game = Game(pygame.display.set_mode((1280, 720)))
    render.apply_theme(THEMES[theme])
    game.start_level(3, line)
    game.renderer.info = game.info
    return game.renderer


@pytest.mark.parametrize("line", ["oeste", "douro"])
@pytest.mark.parametrize("theme", ["day", "night", "sunset", "retro"])
def test_oeste_and_douro_get_their_own_map_by_day_and_night(line, theme):
    r = line_renderer(line, theme)
    storybook = theme in ("day", "night")
    assert r.storybook == storybook and r.plain == (not storybook)
    assert bool(r.wave_marks) == storybook  # sea waves on the Oeste, ripples on the Douro
    if line == "oeste" and storybook:
        assert len(r.windmills) >= 3 and r.turbines and r.lamp


def test_oeste_windmills_turn_only_while_the_trains_run(monkeypatch):
    r = line_renderer("oeste", "day")
    frame(r, 0, 1000, monkeypatch)
    frame(r, 0, 3000, monkeypatch)
    assert r.mill_time == 0
    frame(r, 5, 3050, monkeypatch)
    assert r.mill_time > 0


def test_oeste_lighthouse_beam_stays_over_the_sea(monkeypatch):
    import math

    r = line_renderer("oeste", "night")
    assert r.beam_sweep < math.pi / 2 - 0.25
    sea_x = math.cos(r.sea_angle)
    assert sea_x < 0  # the Atlantic is to the west, on the left of the map
