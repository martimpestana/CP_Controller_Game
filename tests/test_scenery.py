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


@pytest.mark.parametrize("theme", ["day", "night", "sunset", "retro"])
def test_every_theme_gets_the_storybook_map(theme):
    r = algarve_renderer(theme)
    dark = theme in ("night", "retro")  # the control room shows the night map, in green
    assert r.storybook and not r.plain and r.night == dark
    assert r.wave_marks and r.lamp
    assert bool(r.windows) == dark  # only at night do windows light up


def test_sunset_and_control_room_colour_the_map_and_what_moves_on_it():
    from railgame import render

    day, sunset, retro = (algarve_renderer(t) for t in ("day", "sunset", "retro"))
    assert day.grade is None and sunset.grade == "sunset" and retro.grade == "retro"
    sea = render.SB_DAY["SB_SEA"]
    r, g, b = render.grade_colour(sea, "sunset")
    assert r == sea[0] and g < sea[1] and b < sea[2]  # warmer: less green and blue
    r, g, b = render.grade_colour((200, 40, 40), "retro")
    assert g > r and g > b  # everything turns phosphor green
    # The map itself is graded the same way: no strong red or blue left on the control room map.
    px = retro.background.get_at((200, 300))
    assert px.g >= px.r and px.g >= px.b


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
    assert r.storybook and not r.plain
    assert r.wave_marks  # sea waves on the Oeste, ripples on the Douro
    if line == "oeste":
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


@pytest.mark.parametrize("theme", ["day", "night", "sunset", "retro"])
def test_alentejo_gets_its_own_map_in_every_theme(theme):
    r = line_renderer("alentejo", theme)
    assert r.storybook and not r.plain
    assert r.wave_marks  # ripples on the Alvito reservoir
    dark = theme in ("night", "retro")
    assert bool(r.windows) == dark  # lit windows only at night
    assert bool(r.storks) == (not dark)  # storks glide over the plain by day


def test_alentejo_storks_fly(monkeypatch):
    r = line_renderer("alentejo", "day")
    a = frame(r, 0, 1000, monkeypatch)
    b = frame(r, 0, 3000, monkeypatch)
    assert pygame.image.tobytes(a, "RGB") != pygame.image.tobytes(b, "RGB")
