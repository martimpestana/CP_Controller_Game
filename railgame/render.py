"""Everything that is drawn on the screen during a level.

The map follows the real shape of the line along the coast (see layout.py). Trains are drawn as
short carriages, and the panel on the right holds the drivers' requests (each with a "Do it"
button), the trains still to come and a short how-to-play.
"""

import math
import random

import pygame

from railgame import skins, ui
from railgame.layout import Layout, NearestSample
from railgame.simulation import Request, Simulation
from railgame.track import EAST, Point, Signal
from railgame.train import Train
from railgame.ui import S, SR, font

WIDTH, HEIGHT = 1280, 720
TOP_BAR = 56
PANEL_X = 900  # the drivers' requests panel starts here

BG = (16, 24, 33)
LAND = (24, 35, 45)
SEA = (14, 44, 64)
SAND = (120, 110, 80)

# The "storybook" Algarve map has its own bright palette, like an illustrated board-game map.
SB_LAND = (146, 206, 96)
SB_SEA = (56, 186, 214)
SB_SHALLOW = (128, 220, 230)
SB_WAVE = (34, 146, 188)
SB_SAND = (248, 230, 172)
SB_SAND_DARK = (214, 184, 118)
SB_FIELDS = ((244, 212, 92), (190, 226, 108), (112, 180, 72), (232, 186, 104))
SB_HILL_BASE = (118, 182, 80)
SB_HILL = (92, 160, 64)
SB_HILL_LIGHT = (142, 200, 92)
SB_TREE = (64, 150, 62)
SB_TREE_DARK = (36, 102, 50)
SB_OUTLINE = (40, 80, 42)
SB_TRUNK = (124, 84, 50)
SB_ROOF = (206, 98, 60)
SB_WALL = (250, 246, 236)
SB_WALL_SHADE = (208, 202, 190)
SB_TRACK_EDGE = (96, 74, 54)
SB_TEXT_SHADOW = (28, 52, 40)
SB_ROCK = (214, 176, 118)
SB_ROCK_DARK = (172, 132, 86)
SB_OLIVE = (132, 160, 96)
SB_OLIVE_DARK = (100, 128, 76)
SB_OLIVE_LIGHT = (176, 196, 132)
SB_OLIVE_TRUNK = (128, 110, 86)
SB_GRASS = (96, 164, 70)
SB_WALL_TOP = (236, 232, 222)
SB_DOOR = (60, 110, 180)
SB_HOUSE_OUTLINE = (70, 70, 76)
SB_WINDOW = (90, 130, 170)
SB_LIGHTHOUSE_RED = (220, 60, 50)
SB_LIGHTHOUSE_WHITE = (245, 245, 245)
SB_LAMP = (150, 170, 190)  # the lighthouse lamp, unlit by day
# Oeste and Douro (see scenery_lines.py)
SB_VINE = (64, 132, 56)
SB_VINE_EARTH = (196, 170, 118)
SB_SCHIST = (150, 126, 104)
SB_RIVER = (72, 158, 186)
SB_RIVER_EDGE = (128, 196, 206)
SB_STONE = (196, 190, 178)
SB_STONE_DARK = (140, 134, 124)
SB_SAIL = (246, 240, 224)
SB_CLIFF = (206, 156, 104)
SB_CLIFF_DARK = (160, 112, 76)
SB_PEAR = (120, 170, 70)
SB_TURBINE = (240, 240, 240)

# The storybook map is only used with the Day and Night themes, each with its own colours.
SB_DAY = {name: value for name, value in globals().items() if name.startswith("SB_")}
SB_NIGHT = dict(
    SB_DAY,
    SB_LAND=(50, 88, 68), SB_SEA=(16, 46, 86), SB_SHALLOW=(30, 80, 114), SB_WAVE=(58, 104, 152),
    SB_SAND=(146, 136, 108), SB_SAND_DARK=(112, 102, 82),
    SB_FIELDS=((116, 108, 62), (70, 102, 62), (52, 84, 54), (108, 94, 64)),
    SB_HILL_BASE=(42, 78, 58), SB_HILL=(38, 72, 54), SB_HILL_LIGHT=(58, 96, 70),
    SB_TREE=(36, 76, 50), SB_TREE_DARK=(22, 50, 36),
    SB_OUTLINE=(10, 22, 20), SB_TRUNK=(76, 58, 42),
    SB_ROCK=(128, 110, 84), SB_ROCK_DARK=(96, 80, 62),
    SB_OLIVE=(78, 100, 72), SB_OLIVE_DARK=(58, 78, 56), SB_OLIVE_LIGHT=(102, 122, 88), SB_OLIVE_TRUNK=(82, 70, 58),
    SB_TRACK_EDGE=(36, 30, 28), SB_OCEAN_TEXT=(150, 190, 222), SB_TEXT_SHADOW=(6, 12, 20),
    SB_GRASS=(58, 98, 62), SB_WALL=(150, 156, 172), SB_WALL_SHADE=(98, 104, 122), SB_WALL_TOP=(128, 134, 150),
    SB_DOOR=(40, 58, 90), SB_HOUSE_OUTLINE=(16, 20, 30), SB_WINDOW=(40, 50, 70),
    SB_LIGHTHOUSE_RED=(150, 50, 46), SB_LIGHTHOUSE_WHITE=(170, 174, 186), SB_LAMP=(255, 236, 150),
    SB_VINE=(40, 78, 48), SB_VINE_EARTH=(104, 94, 74), SB_SCHIST=(82, 72, 64),
    SB_RIVER=(20, 54, 88), SB_RIVER_EDGE=(36, 76, 104), SB_STONE=(112, 112, 118), SB_STONE_DARK=(78, 78, 86),
    SB_SAIL=(150, 150, 150), SB_CLIFF=(112, 92, 72), SB_CLIFF_DARK=(84, 68, 54), SB_PEAR=(58, 92, 58),
    SB_ROOF=(118, 62, 46), SB_TURBINE=(150, 154, 166),
)
LIT_WINDOW = (255, 214, 110)
MAP_MODE = "night"  # "day" or "night" for the Day and Night themes, otherwise None (set by apply_theme)
SB_OCEAN_TEXT = (24, 96, 136)
TRACK = (190, 196, 204)
TRACK_DIM = (95, 104, 115)
WHITE = (245, 245, 245)
TEXT = (215, 222, 230)
MUTED = (150, 160, 172)
GREEN = (60, 220, 110)
RED = (235, 70, 60)
YELLOW = (250, 200, 60)
EAST_COLOUR = (90, 160, 255)
WEST_COLOUR = (255, 150, 60)
PANEL = (28, 38, 50)
CARD = (38, 52, 68)
BUTTON = (48, 64, 82)
BUTTON_ON = (70, 120, 200)

OCEAN_TEXT = (90, 130, 150)
MAP_MUTED = (150, 160, 172)  # small labels on the map
INK = (8, 10, 14)
CAR_PX = 22  # length of one carriage on screen, in design pixels
CAR_GAP_PX = 3
REQUESTS_BOTTOM = HEIGHT - 300  # the drivers' requests stop here, the next trains start below
SIGNAL_SIDE = 14  # pixels between a signal and its track

# Speed buttons in the top bar: (simulated seconds per real second, label).
SPEEDS = ((0, "Pause"), (1, "1x"), (5, "5x"), (10, "10x"), (20, "20x"))


def clock_text(seconds: float, with_seconds: bool = False) -> str:
    seconds = int(seconds) % (24 * 3600)
    text = f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}"
    return text + f":{seconds % 60:02d}" if with_seconds else text


def minutes_text(seconds: float) -> str:
    return f"{seconds / 60:.1f} min"


def mix(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    """A colour t of the way from a to b (so scenery follows the chosen colour theme)."""
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def apply_theme(colours: dict[str, tuple[int, int, int]]) -> None:
    """Switch the map and panel colours (see themes.py). Takes effect for the next Renderer."""
    global MAP_MODE
    globals().update({name: value for name, value in colours.items() if name in globals()})
    from railgame.themes import THEMES

    name = next((tid for tid, c in THEMES.items() if c == colours), None)
    MAP_MODE = name if name in ("day", "night") else None


_glow_cache: dict = {}

# Maps already drawn, by line, colours and scale (see Renderer._prepare_background).
_background_cache: dict = {}
_CACHED_SCENERY = ("background", "wave_marks", "windows", "lamp", "sea_angle", "beam_sweep", "windmills", "turbines")


def _theme_colour_names() -> tuple[str, ...]:
    from railgame.themes import THEMES

    return tuple(sorted({name for colours in THEMES.values() for name in colours}))


def _background_key(line_name: str) -> tuple:
    return (line_name, ui.scale(), MAP_MODE, tuple(globals().get(name) for name in _theme_colour_names()))


def map_is_ready(line_name: str) -> bool:
    """True when the map of this line is already drawn for the current colours and scale."""
    return _background_key(line_name) in _background_cache




def glow(surf, x: float, y: float, r: float, colour, strength: float) -> None:
    """Light added on top of what is already drawn, brightest in the middle."""
    key = (round(r), colour, strength)
    sprite = _glow_cache.get(key)
    if sprite is None:
        size = int(r * 2) + 2
        sprite = pygame.Surface((size, size))
        sprite.fill((0, 0, 0))
        for k in range(16, 0, -1):
            t = (1 - k / 16) ** 2 * strength
            ui.circle(sprite, tuple(min(255, int(c * t)) for c in colour), (r + 1, r + 1), r * k / 16)
        _glow_cache[key] = sprite
    surf.blit(sprite, (x - sprite.get_width() / 2, y - sprite.get_height() / 2), special_flags=pygame.BLEND_RGB_ADD)


def train_kind(train: Train) -> str:
    """The train type ("R", "IR", "M" or "H"), from the train's name."""
    return train.name.split()[0]


def train_colour(train: Train) -> tuple[int, int, int]:
    return EAST_COLOUR if train.direction == EAST else WEST_COLOUR


class Renderer:
    def __init__(self, sim: Simulation, train_skins: dict[str, str] | None = None):
        self.sim = sim
        self.skins = train_skins or dict(skins.DEFAULT_SKINS)
        box = sim.line.geo.map_box or (40, TOP_BAR + 120, PANEL_X - 80, HEIGHT - TOP_BAR - 250)
        self.layout = Layout(sim.line, tuple(S(v) for v in box), ui.scale())
        self.gap = self.layout.track_gap
        self.f_small = font(13)
        self.f_text = font(15)
        self.f_bold = font(15, bold=True)
        self.f_title = font(19, bold=True)
        self.f_big = font(34, bold=True)
        self.speed_buttons: list[tuple[pygame.Rect, int]] = []
        self.restart_button: pygame.Rect | None = None
        self.menu_button: pygame.Rect | None = None
        self.request_buttons: list[tuple[pygame.Rect, Request]] = []
        self.train_boxes: list[tuple[pygame.Rect, Train]] = []
        self._prepare_background()

    # ------------------------------------------------------------------ positions used for clicks

    def signal_position(self, signal: Signal) -> tuple[float, float]:
        x, y = self.layout.point(signal.pos, signal.track or 1)
        nx, ny = self.layout.normal(signal.pos)
        side = S(SIGNAL_SIDE) if signal.track == 2 else -S(SIGNAL_SIDE)
        return (x + nx * side, y + ny * side)

    def point_position(self, point: Point) -> tuple[float, float]:
        return self.layout.point(point.pos)

    def object_at(self, pos: tuple[int, int]) -> Signal | Point | None:
        best, best_dist = None, S(13)
        for s in self.sim.line.signals:
            dist = math.dist(pos, self.signal_position(s))
            if dist < best_dist:
                best, best_dist = s, dist
        for p in self.sim.line.points:
            dist = math.dist(pos, self.point_position(p))
            if dist < best_dist:
                best, best_dist = p, dist
        return best

    def speed_button_at(self, pos: tuple[int, int]) -> int | None:
        for rect, speed in self.speed_buttons:
            if rect.collidepoint(pos):
                return speed
        return None

    def restart_button_at(self, pos: tuple[int, int]) -> bool:
        return self.restart_button is not None and self.restart_button.collidepoint(pos)

    def menu_button_at(self, pos: tuple[int, int]) -> bool:
        return self.menu_button is not None and self.menu_button.collidepoint(pos)

    def request_button_at(self, pos: tuple[int, int]) -> Request | None:
        """The request whose "Do it" button is at this position, if any."""
        for rect, request in self.request_buttons:
            if rect.collidepoint(pos):
                return request
        return None

    def train_at(self, pos: tuple[int, int]) -> Train | None:
        for rect, train in self.train_boxes:
            if rect.collidepoint(pos):
                return train
        return None

    # ------------------------------------------------------------------ background (drawn once)

    def _prepare_background(self) -> None:
        line = self.sim.line
        lay = self.layout
        storybook_line = line.geo.scenery.endswith("storybook")
        self.storybook = storybook_line and MAP_MODE in ("day", "night")
        self.night = self.storybook and MAP_MODE == "night"
        self.plain = storybook_line and not self.storybook  # other themes: the original, simple map
        if self.storybook:
            globals().update(SB_NIGHT if self.night else SB_DAY)
        self.wave_marks: list[tuple[float, float, float]] = []  # drawn every frame, so they can move
        self.windows: list[tuple[float, float, float, float]] = []  # lit windows at night: x, y, phase, period
        self.lamp: tuple[float, float] | None = None
        self.sea_angle = math.pi / 2
        self.beam_sweep = math.pi / 2 - 0.25  # how far the beam swings each way from straight out to sea
        self.windmills: list[tuple[float, float, float, float]] = []  # Oeste: hub x, y, sail length, phase
        self.turbines: list[tuple[float, float, float]] = []  # Oeste: foot x, y, phase
        self.mill_time = 0.0  # the sails turn while the trains run
        self.sea_time = 0.0
        self._last_tick: int | None = None
        self.land = SB_LAND if self.storybook else LAND
        self.sea = SB_SEA if self.storybook else SEA

        # The map only depends on the line, the colours and the screen scale, so it is drawn
        # once and reused when the same line is played again (the Douro takes a while to draw).
        key = _background_key(line.name)
        cached = _background_cache.get(key)
        if cached is not None:
            self.__dict__.update(cached)
            return

        surf = pygame.Surface((S(WIDTH), S(HEIGHT)))
        surf.fill(BG)
        pygame.draw.rect(surf, self.land, SR(0, TOP_BAR, PANEL_X, HEIGHT - TOP_BAR))

        self._draw_water(surf)
        if self.storybook:
            self._draw_scenery(surf)

        # Track
        if self.storybook:  # a brown bed under the rails, so the line stands out on the bright map
            ui.thick_lines(surf, SB_TRACK_EDGE, lay.main_track(), S(8))
            for st in line.stations:
                if st.has_loop:
                    ui.thick_lines(surf, SB_TRACK_EDGE, lay.loop_track(st), S(8))
        ui.thick_lines(surf, TRACK, lay.main_track(), S(4))
        for st in line.stations:
            if st.has_loop:
                ui.thick_lines(surf, TRACK, lay.loop_track(st), S(4))

        # Where the line continues off the map
        geo = line.geo
        self._edge_label(surf, line.west_edge, -1, geo.start_label)
        self._edge_label(surf, line.east_edge, 1, geo.end_label)
        self.background = surf
        _background_cache[key] = {name: getattr(self, name) for name in _CACHED_SCENERY}

    def _edge_label(self, surf, pos: float, outwards: int, name: str) -> None:
        """Label where the line leaves the map, with an arrow pointing the way it goes."""
        lay = self.layout
        end = lay.point(pos)
        inner = lay.point(pos - outwards * 1500)
        dx, dy = end[0] - inner[0], end[1] - inner[1]
        if abs(dx) >= abs(dy):
            arrow = "→" if dx > 0 else "←"
        else:
            arrow = "↓" if dy > 0 else "↑"
        text = f"{name} {arrow}" if arrow == "→" else f"{arrow} {name}"
        label = self.f_small.render(text, True, MAP_MUTED)
        nx, ny = lay.normal(pos)
        x, y = end[0] + nx * S(26), end[1] + ny * S(26)
        rect = label.get_rect(center=(x, y))
        rect.clamp_ip(pygame.Rect(S(4), S(TOP_BAR + 4), S(PANEL_X - 8), S(HEIGHT - TOP_BAR - 8)))
        if self.storybook:
            self._outlined(surf, self.f_small, text, WHITE, rect.center)
            return
        surf.blit(label, rect)

    def _outlined(self, surf, fnt, text: str, colour, centre) -> None:
        """Text with a dark outline, readable on the bright storybook map."""
        shadow = fnt.render(text, True, SB_TEXT_SHADOW)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
            surf.blit(shadow, shadow.get_rect(center=(centre[0] + dx * S(1), centre[1] + dy * S(1))))
        label = fnt.render(text, True, colour)
        surf.blit(label, label.get_rect(center=centre))

    def _draw_water(self, surf) -> None:
        """The sea or the river, following the shape of the line."""
        line, lay, geo = self.sim.line, self.layout, self.sim.line.geo
        side = geo.water_side
        offset = 45 if geo.water == "sea" else 30
        shore, island = [], []
        pos = line.west_edge - 4000
        while pos <= line.east_edge + 4000:
            x, y = lay.point(pos)
            nx, ny = lay.normal(pos)
            shore.append((x + side * nx * S(offset), y + side * ny * S(offset)))
            wave = 10 * math.sin(pos / 2500)
            if line.west_edge + 2000 <= pos <= line.east_edge - 3000:
                island.append((x + side * nx * S(90 + wave), y + side * ny * S(90 + wave)))
            pos += 250
        left, top, right, bottom = 0, S(TOP_BAR), S(PANEL_X), S(HEIGHT)
        if geo.water == "river" and self.storybook:
            from railgame import scenery_lines

            scenery_lines.douro_river(self, surf)
            return
        if geo.water == "river":
            ui.thick_lines(surf, self.sea, shore, S(18))
            mid = shore[len(shore) // 2]
            label = self.f_small.render(geo.water_label, True, OCEAN_TEXT)
            nx, ny = lay.normal((line.west_edge + line.east_edge) / 2)
            surf.blit(label, label.get_rect(center=(mid[0] + side * nx * S(26), mid[1] + side * ny * S(26))))
            return
        if geo.water_edge == "left":
            polygon = [(shore[0][0], bottom)] + shore + [(shore[-1][0], top), (left, top), (left, bottom)]
            label_pos = (S(70), S(HEIGHT // 2))
        else:
            polygon = [(left, shore[0][1] + S(20))] + shore + [(right, shore[-1][1] - S(60)), (right, bottom), (left, bottom)]
            label_pos = (S(PANEL_X // 2), S(HEIGHT - 32))
        pygame.draw.polygon(surf, self.sea, polygon)
        if self.storybook and geo.scenery == "oeste-storybook":
            from railgame import scenery_lines

            scenery_lines.oeste_water(self, surf, label_pos)
            return
        if self.storybook:
            self._storybook_water(surf, label_pos)
            return
        if geo.barrier_islands:
            ui.thick_lines(surf, SAND, island, S(5))
        label = self.f_small.render(geo.water_label, True, OCEAN_TEXT)
        surf.blit(label, label.get_rect(center=label_pos))

    def _draw_scenery(self, surf) -> None:
        """The storybook land: sorts the map into towns, hills and fields, then lets the line's
        own scenery draw them (the Algarve here, the Oeste and Douro in scenery_lines.py).

        Drawn once into the background: decoration only, it never blocks a click.
        """
        line, lay, geo = self.sim.line, self.layout, self.sim.line.geo
        rng = random.Random(line.name)
        land_side = -geo.water_side

        # Where the track is, to measure how far a spot is from it and on which side.
        samples = []
        pos = line.west_edge - 3000
        while pos <= line.east_edge + 3000:
            samples.append((*lay.point(pos), *lay.normal(pos)))
            pos += 150

        nearest = NearestSample(samples, S(60)).nearest

        def from_track(x: float, y: float) -> tuple[float, bool]:
            sx, sy, nx, ny = nearest(x, y)
            inland = ((x - sx) * nx + (y - sy) * ny) * land_side > 0
            return math.dist((x, y), (sx, sy)), inland

        keep_away = []  # station boxes, small stations' names, the arrows at the ends of the line
        for st in line.stations:
            if st.has_loop:
                keep_away.append((*lay.local(st, 0, 0), lay.zone_px + S(16)))
            else:
                keep_away.append((*lay.point(st.pos), S(54)))
        for pos in (line.west_edge, line.east_edge):
            keep_away.append((*lay.point(pos), S(100)))

        towns = []  # (x, y, radius, phase of the wobbly edge)
        for st in line.stations:
            if st.name in geo.towns:
                r = S(geo.towns[st.name])
                towns.append((*lay.local(st, 0, land_side * (r * 0.5 + S(30))), r, rng.uniform(0, 6.3)))

        def in_town(x: float, y: float) -> bool:
            for tx, ty, r, phase in towns:
                angle = math.atan2(y - ty, x - tx)
                if math.dist((x, y), (tx, ty)) < r * (1 + 0.22 * math.sin(3 * angle + phase)):
                    return True
            return False

        def hills_start(x: float, y: float) -> float:
            return S(190) + S(32) * math.sin(x / S(83)) + S(18) * math.sin(y / S(47) + x / S(130))

        area = pygame.Rect(S(6), S(TOP_BAR + 6), S(PANEL_X - 12), S(HEIGHT - TOP_BAR - 12))
        before = surf.copy()  # land and water as they were before any scenery was painted

        def kind_at(x: float, y: float) -> str | None:
            """What belongs at this spot: "town", "hills", "field" or None (track, water, labels)."""
            if not area.collidepoint(x, y) or before.get_at((int(x), int(y)))[:3] != self.land:
                return None
            d, inland = from_track(x, y)
            if not inland or d < S(32):
                return None
            if in_town(x, y):
                return "town"
            if any(math.dist((x, y), (kx, ky)) < r for kx, ky, r in keep_away):
                return None
            start = hills_start(x, y)
            if start < d < start + S(150) + S(40) * math.sin(x / S(61) + 1.3) + S(25) * math.sin(y / S(37)):
                return "hills"
            return "field" if d > S(38) else None

        # Look at the land in small cells first (before painting, so water is still recognisable).
        step = S(7)
        cells: dict[str, list[tuple[float, float]]] = {"town": [], "hills": [], "field": []}
        y = area.top + step / 2
        while y < area.bottom:
            x = area.left + step / 2
            while x < area.right:
                kind = kind_at(x, y)
                if kind:
                    cells[kind].append((x, y))
                x += step
            y += step
        if geo.scenery == "algarve-storybook":
            self._algarve_storybook(surf, cells, rng, area, kind_at)
        else:
            from railgame import scenery_lines

            draw = scenery_lines.oeste_land if geo.scenery == "oeste-storybook" else scenery_lines.douro_land
            draw(self, surf, cells, rng, area, kind_at)

    def _sea_free(self, surf, x: float, y: float, r: float) -> bool:
        """Open sea (deep water colour) all around this spot, inside the map."""
        area = pygame.Rect(S(8), S(TOP_BAR + 8), S(PANEL_X - 16), S(HEIGHT - TOP_BAR - 16))
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (0.7, 0.7), (-0.7, 0.7), (0.7, -0.7), (-0.7, -0.7)):
            px, py = int(x + dx * r), int(y + dy * r)
            if not area.collidepoint(px, py) or surf.get_at((px, py))[:3] != SB_SEA:
                return False
        return True

    def _storybook_water(self, surf, label_pos) -> None:
        """Turquoise sea, a light shallow lagoon, wide sandy beaches and barrier islands with
        palm trees, a lighthouse, fishing boats, dolphins and a compass."""
        line, lay = self.sim.line, self.layout
        side = line.geo.water_side
        rng = random.Random("storybook sea")

        def along(off_fn, first, last, every=200):
            pts, pos = [], first
            while pos <= last:
                x, y = lay.point(pos)
                nx, ny = lay.normal(pos)
                off = off_fn(pos)
                pts.append((x + side * nx * S(off), y + side * ny * S(off)))
                pos += every
            return pts

        def wave(pos):
            return 10 * math.sin(pos / 2500)

        all_start, all_end = line.west_edge - 4000, line.east_edge + 4000
        isl_start, isl_end = line.west_edge + 2000, line.east_edge - 3000
        # Shallow water: the whole lagoon, and a light rim outside the islands.
        ui.thick_lines(surf, SB_SHALLOW, along(lambda p: 45 + 24, all_start, all_end), S(50))
        ui.thick_lines(surf, SB_SHALLOW, along(lambda p: 90 + wave(p) + 8, isl_start, isl_end), S(26))
        # A wide beach with a wavy inner edge, fading into the grass in specks of sand,
        # with tufts of marram grass on it.
        def depth(p):  # how far the sand reaches inland from the water, in pixels
            d = 20 + 8 * math.sin(p / 1700) + 5 * math.sin(p / 530 + 2) + 3 * math.sin(p / 190)
            return max(9, min(33, d))

        shore = along(lambda p: 47, all_start, all_end, 100)
        inner = along(lambda p: 45 - depth(p), all_start, all_end, 100)
        pygame.draw.polygon(surf, SB_SAND, shore + inner[::-1])
        ui.thick_lines(surf, mix(SB_SAND, SB_SAND_DARK, 0.5), along(lambda p: 46, all_start, all_end, 100), S(3))
        pos = all_start
        while pos <= all_end:
            for _ in range(3):
                off = 45 - depth(pos) - rng.uniform(0, 16) ** 1.3 / 2
                x, y = along(lambda p: off, pos, pos, 1)[0]
                ui.circle(surf, mix(SB_SAND, SB_LAND, rng.uniform(0, 0.5)), (x + rng.uniform(-6, 6), y), S(rng.uniform(1.2, 2.6)))
            pos += 60
        pos = all_start
        while pos <= all_end:
            if rng.random() < 0.55:
                off = 45 - rng.uniform(4, depth(pos) - 3)
                x, y = along(lambda p: off, pos, pos, 1)[0]
                for k in (-1, 0, 1):
                    pygame.draw.line(surf, SB_GRASS, (x, y), (x + k * S(2), y - S(4) + abs(k) * S(1)), max(1, S(1.2)))
            pos += 140

        # Barrier islands: wide, with ragged edges, marram grass and palm trees.
        upper = along(lambda p: 90 + wave(p) - (6 + 3 * math.sin(p / 700)), isl_start, isl_end, 120)
        lower = along(lambda p: 90 + wave(p) + (5 + 2 * math.sin(p / 450 + 1)), isl_start, isl_end, 120)
        island = upper + lower[::-1]
        pygame.draw.polygon(surf, SB_SAND, island)
        pygame.draw.lines(surf, SB_SAND_DARK, True, island, max(1, S(2)))
        for x, y in upper[::4]:
            for k in (-1, 0, 1):
                pygame.draw.line(surf, SB_GRASS, (x, y + S(3)), (x + k * S(2), y - S(1)), max(1, S(1.2)))
        pos = isl_start + 1200
        while pos < isl_end - 800:
            x, y = lay.point(pos)
            nx, ny = lay.normal(pos)
            off = 90 + wave(pos)
            self._palm(surf, x + side * nx * S(off), y + side * ny * S(off), S(rng.uniform(9, 12)), rng)
            pos += rng.uniform(2600, 4200)

        # The lighthouse of Cabo de Santa Maria, on the island south of Faro.
        pos = line.west_edge + 6500
        x, y = lay.point(pos)
        nx, ny = lay.normal(pos)
        off = 90 + wave(pos)
        self._lighthouse(surf, x + side * nx * S(off), y + side * ny * S(off))

        # Things at sea, only where there is open water around them.
        label_rect = self.f_small.render(line.geo.water_label, True, WHITE).get_rect(center=label_pos).inflate(S(30), S(20))
        taken = [label_rect]

        def find_spot(r, tries=300):
            for _ in range(tries):
                x = rng.uniform(S(20), S(PANEL_X - 20))
                y = rng.uniform(S(TOP_BAR + 20), S(HEIGHT - 20))
                box = pygame.Rect(0, 0, 2 * r, 2 * r)
                box.center = (int(x), int(y))
                if self._sea_free(surf, x, y, r) and not any(box.colliderect(t) for t in taken):
                    taken.append(box)
                    return x, y
            return None

        spot = find_spot(S(40))
        if spot:
            self._compass(surf, *spot, S(30))
        for _ in range(3):
            spot = find_spot(S(16))
            if spot:
                self._boat(surf, *spot, S(1), rng)
        spot = find_spot(S(22))
        if spot:
            self._dolphin(surf, spot[0] - S(9), spot[1], S(1))
            self._dolphin(surf, spot[0] + S(9), spot[1] + S(5), S(0.85))
        for _ in range(45):  # little waves, drawn every frame (see _draw_animated)
            spot = find_spot(S(9), tries=40)
            if spot:
                self.wave_marks.append((*spot, rng.uniform(0, 2 * math.pi)))
        if self.night:  # the moon on the water: a soft, rippled path of light
            layer = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            cx, cy = S(640), S(640)
            for k in range(14):
                ww = S(26) * (1 - k / 16)
                pygame.draw.ellipse(layer, (220, 230, 255, 70 - k * 4), (cx - ww / 2 + math.sin(k) * S(4), cy - k * S(5), ww, S(2.5)))
            surf.blit(layer, (0, 0))

        label = self.f_bold.render(line.geo.water_label, True, SB_OCEAN_TEXT)
        surf.blit(label, label.get_rect(center=label_pos))

    def _cube_house(self, surf, x, y, rng) -> None:
        """A flat-roofed white cube house, as in Olhão, with a blue door and a roof terrace.
        At night most windows are noted down, to be lit (and switched off) in _draw_animated."""
        w, d, h = S(rng.uniform(8, 12)), S(rng.uniform(4, 6)), S(rng.uniform(6, 9))
        front = pygame.Rect(0, 0, w, h)
        front.midbottom = (x, y + h / 2)
        side = [front.topright, (front.right + d * 0.6, front.top - d * 0.5), (front.right + d * 0.6, front.bottom - d * 0.5), front.bottomright]
        top = [front.topleft, (front.left + d * 0.6, front.top - d * 0.5), (front.right + d * 0.6, front.top - d * 0.5), front.topright]
        pygame.draw.polygon(surf, SB_WALL_SHADE, side)
        pygame.draw.polygon(surf, SB_WALL_TOP, top)
        pygame.draw.rect(surf, SB_WALL, front)
        for poly in (side, top):
            pygame.draw.polygon(surf, SB_HOUSE_OUTLINE, poly, 1)
        pygame.draw.rect(surf, SB_HOUSE_OUTLINE, front, 1)
        pygame.draw.rect(surf, SB_DOOR, (front.centerx - S(1.5), front.bottom - S(4), S(3), S(4)))
        windows = [(front.left + S(1.5), front.top + S(1.5))]
        if w > S(10):
            windows.append((front.right - S(4.5), front.top + S(1.5)))
        for wx, wy in windows:
            pygame.draw.rect(surf, SB_WINDOW, (wx, wy, S(3), S(3)))
            if self.night and rng.random() < 0.8:
                self.windows.append((wx, wy, rng.uniform(0, 20), rng.uniform(5, 14)))
        if rng.random() < 0.4:  # a little stair tower on the roof terrace
            t = pygame.Rect(0, 0, S(3.5), S(3.5))
            t.midbottom = (front.left + w * 0.3, front.top - S(0.5))
            pygame.draw.rect(surf, SB_WALL, t)
            pygame.draw.rect(surf, SB_HOUSE_OUTLINE, t, 1)

    def _stone_pine(self, surf, x, y, r, rng) -> None:
        """Stone pine (pinheiro-manso): a bare trunk and a wide, flat crown."""
        top = (x + rng.uniform(-0.25, 0.25) * r, y - r * 1.5)
        ui.thick_lines(surf, SB_OUTLINE, [(x, y), top], S(3))
        ui.thick_lines(surf, SB_TRUNK, [(x, y), top], S(1.8))
        w, h = r * 2.0, r * 0.75
        parts = ((-0.45, 0.1, 0.6), (0.4, 0.1, 0.6), (0, -0.15, 0.75))
        for dx, dy, k in parts:
            pygame.draw.ellipse(surf, SB_OUTLINE, (top[0] + dx * w - w * k / 2 - S(1), top[1] + dy * h - h * k - S(1), w * k + S(2), h * k * 2 + S(2)))
        for dx, dy, k in parts:
            pygame.draw.ellipse(surf, SB_TREE_DARK, (top[0] + dx * w - w * k / 2, top[1] + dy * h - h * k, w * k, h * k * 2))
        pygame.draw.ellipse(surf, SB_TREE, (top[0] - w * 0.42, top[1] - h * 0.95, w * 0.7, h * 1.1))

    def _olive_tree(self, surf, x, y, r, rng) -> None:
        """An olive tree: a short twisted trunk and a lumpy, silvery-green crown."""
        trunk = [(x, y), (x - r * 0.2, y - r * 0.6), (x + r * 0.1, y - r)]
        ui.thick_lines(surf, SB_OUTLINE, trunk, S(3.2))
        ui.thick_lines(surf, SB_OLIVE_TRUNK, trunk, S(2))
        cy = y - r * 1.4
        lumps = [(rng.uniform(-0.8, 0.8) * r, rng.uniform(-0.45, 0.35) * r, rng.uniform(0.38, 0.55) * r) for _ in range(5)]
        for dx, dy, rr in lumps:
            ui.circle(surf, SB_OUTLINE, (x + dx, cy + dy), rr + S(1.2))
        for dx, dy, rr in lumps:
            ui.circle(surf, SB_OLIVE_DARK, (x + dx, cy + dy), rr)
        for dx, dy, rr in lumps[:3]:
            ui.circle(surf, SB_OLIVE, (x + dx - rr * 0.2, cy + dy - rr * 0.25), rr * 0.7)
            ui.circle(surf, SB_OLIVE_LIGHT, (x + dx - rr * 0.35, cy + dy - rr * 0.4), rr * 0.25)

    def _palm(self, surf, x, y, h, rng) -> None:
        lean = h * rng.uniform(-0.35, 0.35)
        top = (x + lean, y - h)
        mid = (x + lean * 0.4, y - h * 0.5)
        ui.thick_lines(surf, SB_TRUNK, [(x, y), mid, top], max(2, S(2.2)))
        for angle in (-2.6, -1.9, -1.2, -0.5, 0.2):
            end = (top[0] + math.cos(angle) * h * 0.7, top[1] + math.sin(angle) * h * 0.45 + h * 0.18)
            ui.thick_lines(surf, SB_TREE_DARK, [top, ((top[0] + end[0]) / 2, (top[1] + end[1]) / 2 - h * 0.12), end], max(2, S(2.6)))
        ui.circle(surf, SB_TRUNK, top, S(1.8))

    def _lighthouse(self, surf, x, y) -> None:
        """The tower. Its lamp is dark by day; at night its turning light is drawn every frame."""
        w0, w1, h = S(9), S(6), S(26)
        stripes = 4
        for i in range(stripes):
            t0, t1 = i / stripes, (i + 1) / stripes
            a0, a1 = w0 + (w1 - w0) * t0, w0 + (w1 - w0) * t1
            quad = [(x - a0 / 2, y - h * t0), (x + a0 / 2, y - h * t0), (x + a1 / 2, y - h * t1), (x - a1 / 2, y - h * t1)]
            pygame.draw.polygon(surf, SB_LIGHTHOUSE_RED if i % 2 == 0 else SB_LIGHTHOUSE_WHITE, quad)
        pygame.draw.rect(surf, (60, 60, 70), (x - w1 / 2 - S(1), y - h - S(7), w1 + S(2), S(7)))
        self.lamp = (x, y - h - S(3.5))
        # Which way the open sea is from here (straight away from the coast), for the beam.
        pos = self.sim.line.west_edge + 6500
        nx, ny = self.layout.normal(pos)
        side = self.sim.line.geo.water_side
        self.sea_angle = math.atan2(side * ny / 0.6, side * nx)
        ui.circle(surf, SB_LAMP, self.lamp, S(2.6))
        pygame.draw.polygon(surf, SB_LIGHTHOUSE_RED, [(x - w1 / 2 - S(2), y - h - S(7)), (x + w1 / 2 + S(2), y - h - S(7)), (x, y - h - S(12))])

    def _boat(self, surf, x, y, k, rng) -> None:
        if self.night:  # a lantern at the top of the mast
            glow(surf, x, y - 16 * k, S(9), (255, 220, 120), 0.9)
        hull = rng.choice(((200, 70, 60), (60, 110, 190), (240, 170, 60)))
        pygame.draw.polygon(surf, hull, [(x - 11 * k, y), (x + 11 * k, y), (x + 7 * k, y + 6 * k), (x - 7 * k, y + 6 * k)])
        pygame.draw.line(surf, WHITE, (x - 11 * k, y + 1.5 * k), (x + 11 * k, y + 1.5 * k), max(1, round(1.4 * k)))
        pygame.draw.line(surf, SB_TRUNK, (x, y), (x, y - 16 * k), max(1, round(1.6 * k)))
        pygame.draw.polygon(surf, WHITE, [(x + 1.5 * k, y - 15 * k), (x + 1.5 * k, y - 2 * k), (x + 10 * k, y - 2 * k)])
        pygame.draw.polygon(surf, (236, 236, 226), [(x - 1.5 * k, y - 12 * k), (x - 1.5 * k, y - 2 * k), (x - 7 * k, y - 2 * k)])
        pygame.draw.arc(surf, SB_WAVE, (x - 15 * k, y + 4 * k, 30 * k, 6 * k), math.pi + 0.3, 2 * math.pi - 0.3, max(1, round(1.4 * k)))

    def _dolphin(self, surf, x, y, k) -> None:
        body = (96, 128, 170)
        pygame.draw.arc(surf, body, (x - 9 * k, y - 7 * k, 18 * k, 14 * k), 0.3, math.pi - 0.2, max(2, round(4 * k)))
        pygame.draw.polygon(surf, body, [(x - 1 * k, y - 6 * k), (x + 3 * k, y - 11 * k), (x + 4 * k, y - 6 * k)])
        pygame.draw.polygon(surf, body, [(x - 8 * k, y - 1 * k), (x - 12 * k, y + 1 * k), (x - 8 * k, y + 3 * k), (x - 6 * k, y)])
        pygame.draw.arc(surf, SB_WAVE, (x - 12 * k, y, 24 * k, 5 * k), math.pi + 0.2, 2 * math.pi - 0.2, max(1, round(1.4 * k)))

    def _compass(self, surf, x, y, r) -> None:
        ui.circle(surf, SB_SHALLOW, (x, y), r * 0.82)
        ui.ring(surf, SB_OCEAN_TEXT, (x, y), r * 0.82, max(1, S(1.5)))
        dark, light = (36, 72, 130), (90, 140, 200)
        for i in range(8):
            a = i * math.pi / 4 - math.pi / 2
            length = r if i % 2 == 0 else r * 0.6
            tip = (x + math.cos(a) * length, y + math.sin(a) * length)
            for sgn, col in ((-1, dark), (1, light)):
                b = a + sgn * math.pi / 2
                base = (x + math.cos(b) * r * 0.14, y + math.sin(b) * r * 0.14)
                pygame.draw.polygon(surf, col, [(x, y), base, tip])
        for text, a in (("N", -math.pi / 2), ("E", 0), ("S", math.pi / 2), ("W", math.pi)):
            label = self.f_small.render(text, True, SB_OCEAN_TEXT)
            surf.blit(label, label.get_rect(center=(x + math.cos(a) * (r + S(9)), y + math.sin(a) * (r + S(9)))))

    def _algarve_storybook(self, surf, cells, rng, area, kind_at) -> None:
        """Bright, illustrated land: pointed hills with rocky tops, patchwork fields with crop
        rows, stone pines and olive trees, and towns of white houses with terracotta roofs."""

        def tree(x, y, r):
            """A stone pine (two out of three) or an olive tree, standing on (x, y)."""
            if rng.random() < 0.67:
                self._stone_pine(surf, x, y, r, rng)
            else:
                self._olive_tree(surf, x, y, r, rng)

        # Fields: a few patchwork farms with crop rows, turned to follow the coast.
        angle = -0.47
        ca, sa = math.cos(angle), math.sin(angle)
        farms = []
        for x, y in rng.sample(cells["field"], len(cells["field"])):
            if len(farms) >= 9:
                break
            if all(math.dist((x, y), f) > S(95) for f in farms):
                farms.append((x, y))
        for fx, fy in farms:
            cols, rows = rng.randint(2, 4), rng.randint(2, 3)
            fu, fv = fx * ca + fy * sa, -fx * sa + fy * ca
            w, h = S(rng.uniform(22, 28)), S(rng.uniform(15, 19))
            for i in range(cols):
                for j in range(rows):
                    u0, v0 = fu + (i - cols / 2) * w, fv + (j - rows / 2) * h
                    pts = [(u0, v0), (u0 + w, v0), (u0 + w, v0 + h), (u0, v0 + h)]
                    quad = [(u * ca - v * sa, u * sa + v * ca) for u, v in pts]
                    cx, cy = sum(p[0] for p in quad) / 4, sum(p[1] for p in quad) / 4
                    if not all(kind_at(px, py) == "field" for px, py in (*quad, (cx, cy))):
                        continue
                    colour = rng.choice(SB_FIELDS)
                    pygame.draw.polygon(surf, colour, quad)
                    rows_colour = mix(colour, SB_OUTLINE, 0.25)
                    for k in range(1, 4):  # crop rows
                        t = k / 4
                        a = (u0 + w * 0.12, v0 + h * t)
                        b = (u0 + w * 0.88, v0 + h * t)
                        pygame.draw.line(surf, rows_colour, (a[0] * ca - a[1] * sa, a[0] * sa + a[1] * ca), (b[0] * ca - b[1] * sa, b[0] * sa + b[1] * ca), max(1, S(1)))
                    pygame.draw.polygon(surf, SB_SAND, quad, max(1, S(1.5)))

        # Hills: pointed, with green wooded slopes, a sunny side and rocky ochre tops.
        for x, y in cells["hills"]:
            ui.circle(surf, SB_HILL_BASE, (x, y), S(8.5))
        peaks = []
        for x, y in rng.sample(cells["hills"], len(cells["hills"])):
            if all(math.dist((x, y), (px, py)) > S(38) for px, py, _ in peaks):
                peaks.append((x, y, S(rng.uniform(26, 38))))
        feet = []
        for x, y, r in sorted(peaks, key=lambda p: p[1]):
            top = (x + r * rng.uniform(-0.15, 0.15), y - r * 1.15)
            base_l, base_r = (x - r, y), (x + r, y)
            pygame.draw.polygon(surf, SB_HILL, [base_l, top, base_r])
            pygame.draw.polygon(surf, SB_HILL_LIGHT, [base_l, top, (x - r * 0.05, y)])
            k = 0.38  # the rocky upper part, with a jagged lower edge
            tl = (top[0] + (base_l[0] - top[0]) * k, top[1] + (base_l[1] - top[1]) * k)
            tr = (top[0] + (base_r[0] - top[0]) * k, top[1] + (base_r[1] - top[1]) * k)
            jag = [tl, (tl[0] + r * 0.2, tl[1] + r * 0.12), (top[0], tl[1] - r * 0.02), (tr[0] - r * 0.2, tr[1] + r * 0.14), tr]
            pygame.draw.polygon(surf, SB_ROCK_DARK, [top] + jag[::-1])
            pygame.draw.polygon(surf, SB_ROCK, [top, jag[0], jag[1], jag[2]])
            pygame.draw.lines(surf, SB_OUTLINE, True, [base_l, top, base_r], max(1, S(2)))
            for _ in range(2):
                feet.append((x + rng.uniform(-r, r) * 0.85, y + rng.uniform(-2, 3)))
        for x, y in sorted(feet, key=lambda f: f[1]):
            tree(x, y, S(rng.uniform(4.5, 6)))
        if self.sim.line.geo.hills_label and cells["hills"]:
            text = "  ".join(" ".join(word.upper()) for word in self.sim.line.geo.hills_label.split())
            hx = sum(x for x, _ in cells["hills"]) / len(cells["hills"])
            hy = sum(y for _, y in cells["hills"]) / len(cells["hills"])
            self._outlined(surf, self.f_bold, text, WHITE, (hx, hy))

        # Trees dotted over the farmland, in little clumps.
        trees = []
        for x, y in rng.sample(cells["field"], min(40, len(cells["field"]))):
            for _ in range(rng.randint(1, 3)):
                trees.append((x + rng.uniform(-9, 9), y + rng.uniform(-6, 6), S(rng.uniform(4, 5.5))))
        for x, y, r in sorted(trees, key=lambda t: t[1]):
            if kind_at(x, y + r) == "field":
                tree(x, y, r)

        # Towns: Olhão's white cube houses, keeping station names clear.
        names = []
        for st in self.sim.line.stations:
            if st.has_loop:
                w = self.f_bold.size(st.name)[0]
                cx, cy = self.layout.local(st, 0, S(52))
                names.append(pygame.Rect(0, 0, w + S(24), S(30)).move(cx - w / 2 - S(12), cy - S(15)))
        houses = []
        for x, y in cells["town"]:
            if any(r.collidepoint(x, y) for r in names):
                continue
            if rng.random() < 0.3:
                houses.append((x + rng.uniform(-3, 3), y + rng.uniform(-3, 3)))
        for x, y in sorted(houses, key=lambda hs: hs[1]):
            if rng.random() < 0.35:
                continue
            self._cube_house(surf, x, y, rng)
        if self.night:  # a warm glow over each town
            land_side = -self.sim.line.geo.water_side
            for st in self.sim.line.stations:
                if st.name in self.sim.line.geo.towns:
                    r = S(self.sim.line.geo.towns[st.name])
                    tx, ty = self.layout.local(st, 0, land_side * (r * 0.5 + S(30)))
                    glow(surf, tx, ty, r * 1.4, (255, 190, 100), 0.35)
        palms = [spot for spot in cells["town"] if not any(r.collidepoint(*spot) for r in names)]
        for x, y in rng.sample(palms, min(8, len(palms))):
            self._palm(surf, x, y + S(6), S(rng.uniform(10, 13)), rng)

    # ------------------------------------------------------------------ drawing a frame

    def draw(self, screen: pygame.Surface, info, speed: int, hover: tuple[int, int], toast: str | None) -> None:
        screen.blit(self.background, (0, 0))
        if screen.get_flags() & pygame.SRCALPHA:
            # Some windows (e.g. on macOS) keep an alpha channel, and the background leaves it at 0.
            # Text blitted onto fully transparent pixels would then show its own (white) box, so
            # make the whole frame opaque first. Only the alpha changes, not the colours.
            screen.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MAX)
        if self.storybook:
            self._draw_animated(screen, speed)
        highlighted = self._highlighted_targets(hover)
        self._draw_points(screen, highlighted)
        self._draw_signals(screen, highlighted)
        self._draw_trains(screen)
        self._draw_stations(screen)
        self._draw_train_labels(screen)
        self._draw_top_bar(screen, info, speed)
        self._draw_requests(screen, hover)
        self._draw_next_trains(screen)
        self._draw_legend(screen)
        self._draw_hover(screen, hover)
        if toast:
            text = self.f_text.render(toast, True, WHITE)
            box = text.get_rect(center=(S(PANEL_X // 2), S(TOP_BAR + 30))).inflate(S(24), S(14))
            pygame.draw.rect(screen, (90, 40, 40), box, border_radius=S(8))
            screen.blit(text, text.get_rect(center=box.center))

    def _draw_animated(self, screen, speed: int) -> None:
        """What moves on the storybook map. By day the little waves rock while the trains run
        (they stop when the game is paused). At night the windows of the houses go on and off
        and the lighthouse's beams turn."""
        ticks = pygame.time.get_ticks()
        dt = 0.0 if self._last_tick is None else (ticks - self._last_tick) / 1000
        self._last_tick = ticks
        now = ticks / 1000
        if speed > 0 and not self.night:
            self.sea_time += min(dt, 0.1)
        if speed > 0:
            self.mill_time += min(dt, 0.1)
        width = max(1, S(1.6))
        for x, y, phase in self.wave_marks:
            t = self.sea_time * 1.8 + phase
            dx, dy = math.sin(t) * S(3), math.sin(t * 0.7) * S(1.2)
            for side in (-S(4), S(4)):
                pygame.draw.arc(screen, SB_WAVE, (x + dx + side - S(4), y + dy - S(3), S(8), S(6)), 0.2, math.pi - 0.2, width)
        self._draw_sails(screen)
        if not self.night:
            return
        for x, y, phase, period in self.windows:
            if (now + phase) % period < period * 0.72:
                pygame.draw.rect(screen, LIT_WINDOW, (x, y, S(3), S(3)))
                glow(screen, x + S(1.5), y + S(1.5), S(6), (255, 200, 100), 0.55)
        if self.lamp:
            self._draw_beams(screen, now)

    def _draw_sails(self, screen) -> None:
        """Oeste: wind turbines on the ridge and the windmills' four triangular sails."""
        t = self.mill_time
        for x, y, phase in self.turbines:
            hub = (x, y - S(16))
            pygame.draw.line(screen, SB_TURBINE, (x, y), hub, max(1, S(2)))
            for k in range(3):
                a = t * 2.2 + phase + k * 2 * math.pi / 3
                pygame.draw.line(screen, SB_TURBINE, hub, (hub[0] + math.cos(a) * S(9), hub[1] + math.sin(a) * S(9)), max(1, S(1.5)))
            ui.circle(screen, (230, 50, 50) if self.night else SB_HOUSE_OUTLINE, hub, S(1.4))
        for x, y, r, phase in self.windmills:
            for k in range(4):
                a = t * 1.3 + phase + k * math.pi / 2
                tip = (x + math.cos(a) * r, y + math.sin(a) * r)
                pygame.draw.line(screen, SB_TRUNK, (x, y), tip, max(1, S(1.3)))
                b = a + 0.45
                sail = [(x + math.cos(a) * r * 0.25, y + math.sin(a) * r * 0.25), tip, (x + math.cos(b) * r * 0.75, y + math.sin(b) * r * 0.75)]
                pygame.draw.polygon(screen, SB_SAIL, sail)
                pygame.draw.polygon(screen, SB_HOUSE_OUTLINE, sail, 1)
            ui.circle(screen, SB_HOUSE_OUTLINE, (x, y), S(1.6))

    def _draw_beams(self, screen, now: float) -> None:
        """One beam of light sweeping to and fro over the sea, never over the land."""
        lx, ly = self.lamp
        reach = S(140)
        size = 2 * reach + 2
        layer = pygame.Surface((size, size))
        layer.fill((0, 0, 0))
        centre = (reach + 1, reach + 1)
        # Swing through the half circle that faces the sea, slowing down at each end.
        a = self.sea_angle + math.sin(now * 0.7) * self.beam_sweep
        for spread, colour in ((0.2, (40, 36, 18)), (0.11, (110, 96, 50))):
            pygame.draw.polygon(layer, colour, [
                centre,
                (centre[0] + math.cos(a - spread) * reach, centre[1] + math.sin(a - spread) * reach * 0.6),
                (centre[0] + math.cos(a + spread) * reach, centre[1] + math.sin(a + spread) * reach * 0.6)])
        layer = pygame.transform.smoothscale(pygame.transform.smoothscale(layer, (size // 4, size // 4)), (size, size))
        screen.blit(layer, (lx - centre[0], ly - centre[1]), special_flags=pygame.BLEND_RGB_ADD)
        glow(screen, lx, ly, S(26), (255, 220, 120), 1.0)
        ui.circle(screen, LIT_WINDOW, (lx, ly), S(2.6))

    def _highlighted_targets(self, hover) -> dict[str, tuple[int, int, int]]:
        targets = {}
        for request in self.sim.requests.values():
            targets[request.target_id] = train_colour(request.train)
        return targets

    def _pulse(self, screen, pos, colour) -> None:
        t = pygame.time.get_ticks() / 1000
        radius = S(13 + 4 * (0.5 + 0.5 * math.sin(t * 6)))
        ui.ring(screen, colour, pos, radius, S(2))

    def _draw_points(self, screen, highlighted) -> None:
        lay = self.layout
        for p in self.sim.line.points:
            st = p.station
            # Show which way the points are set by drawing the chosen route brighter.
            inner = st.pos + p.side * 400
            straight = [lay.point(p.pos), lay.point(inner, 1)]
            diverging = [lay.point(p.pos), lay.point(inner, 2)]
            active, other = (diverging, straight) if p.diverging else (straight, diverging)
            ui.thick_line(screen, TRACK_DIM, other[0], other[1], S(4))
            ui.thick_line(screen, YELLOW if p.diverging else WHITE, active[0], active[1], S(4))
            x, y = self.point_position(p)
            rect = pygame.Rect(0, 0, S(13), S(13))
            rect.center = (int(x), int(y))
            pygame.draw.rect(screen, YELLOW if p.diverging else WHITE, rect, border_radius=S(2))
            pygame.draw.rect(screen, BG, rect, S(2), border_radius=S(2))
            if p.id in highlighted:
                self._pulse(screen, (x, y), highlighted[p.id])

    def _draw_signals(self, screen, highlighted) -> None:
        for s in self.sim.line.signals:
            x, y = self.signal_position(s)
            base = self.layout.point(s.pos, s.track or 1)
            ui.thick_line(screen, MUTED, base, (x, y), S(2))
            ui.circle(screen, (8, 8, 8), (x, y), S(8))
            ui.circle(screen, GREEN if s.green else RED, (x, y), S(6))
            if s.id in highlighted:
                self._pulse(screen, (x, y), highlighted[s.id])

    def _walk_back(self, train: Train, px_dists: list[float]) -> list[tuple[float, float]]:
        """The points on the drawn track px_dists screen pixels behind the front of the train
        (in increasing order), found in a single walk along the track. Each step uses the track
        that part of the train is on, so the carriages follow the front through the points
        instead of jumping across."""
        prev = self.layout.point(train.pos, train.track_at(train.pos))
        done, metres = 0.0, 0.0
        out = []
        for want in px_dists:
            while done < want and metres < 6000:
                metres += 5
                pos = train.pos - train.direction * metres
                cur = self.layout.point(pos, train.track_at(pos))
                done += math.dist(prev, cur)
                prev = cur
            out.append(prev)
        return out

    def _draw_trains(self, screen) -> None:
        line = self.sim.line
        crashed = self.sim.crash or ()
        self.train_boxes = []
        self._labels_to_draw = []
        t = pygame.time.get_ticks() / 1000
        for train in self.sim.trains:
            if train.state != "running":
                continue
            low, high = train.span
            if high < line.west_edge or low > line.east_edge:
                continue  # completely off the map
            stripe = RED if train in crashed else train_colour(train)
            kind = train_kind(train)
            cars = skins.CARS.get(kind, 2)
            skin = self.skins.get(kind, "real")
            dists = []
            for i in range(cars):
                offset = S(i * (CAR_PX + CAR_GAP_PX))
                dists += [offset, offset + S(CAR_PX)]
            points = self._walk_back(train, dists)
            ends = list(zip(points[::2], points[1::2]))
            for i in reversed(range(cars)):
                a, b = ends[i]
                if i < cars - 1:
                    pygame.draw.line(screen, INK, b, ends[i + 1][0], max(1, S(3)))
                skins.draw_car(screen, a, b, kind, skin, stripe, i, cars, ui.scale(), t)
            self._labels_to_draw.append((train, ends))

    def _draw_train_labels(self, screen) -> None:
        """Draw the trains' tags after the stations, so nothing hides them, and move a tag
        further from its train when it would cover another tag or a station."""
        taken = [self._station_box(st) for st in self.sim.line.stations]
        for train, ends in self._labels_to_draw:
            self._draw_train_label(screen, train, ends, taken)

    def _station_box(self, st) -> pygame.Rect:
        """The white circle of a station, as a rectangle that train tags keep clear of."""
        lay = self.layout
        if st.has_loop:
            x, y = lay.local(st, 0, self.gap / 2)
            r = S(16)
        else:
            x, y = lay.point(st.pos)
            r = S(10)
        return pygame.Rect(int(x - r), int(y - r), 2 * r, 2 * r)

    def _draw_train_label(self, screen, train: Train, ends, taken: list[pygame.Rect] | None = None) -> None:
        """A small tag next to the train: type, number, delay and the way it is going."""
        head, tail = ends[0][0], ends[-1][1]
        mid = ((head[0] + tail[0]) / 2, (head[1] + tail[1]) / 2)
        nx, ny = self.layout.normal(train.pos)
        offset = S(34) + (self.gap if train.track == 2 else 0)
        colour = train_colour(train)
        chip = self.f_bold.render(train_kind(train), True, BG)
        number = self.f_small.render(train.name.split()[-1], True, WHITE)
        delay = train.delay(self.sim.time)
        tag = self.f_small.render("on time" if delay < 30 else f"+{delay / 60:.0f} min", True, GREEN if delay < 30 else RED)
        arrow = self.f_bold.render("→" if train.direction == EAST else "←", True, colour)
        width = chip.get_width() + number.get_width() + tag.get_width() + arrow.get_width() + S(34)
        box = pygame.Rect(0, 0, width, S(22))
        area = SR(4, TOP_BAR + 4, PANEL_X - 8, HEIGHT - TOP_BAR - 8)
        taken = taken if taken is not None else []
        # First choice: on its usual side of the track. If that covers another tag or a
        # station, try further out, then the other side of the track.
        for side, extra in ((1, 0), (1, 26), (-1, 6), (-1, 32), (1, 52), (-1, 58), (1, 78), (-1, 84), (1, 104), (-1, 110)):
            o = side * (offset + S(extra)) if side > 0 else -(S(34) + S(extra))
            box.center = (int(mid[0] - nx * o), int(mid[1] - ny * o))
            box.clamp_ip(area)
            if box.collidelist(taken) < 0:
                break
        else:  # nowhere free: keep the usual place
            box.center = (int(mid[0] - nx * offset), int(mid[1] - ny * offset))
            box.clamp_ip(area)
        taken.append(box.inflate(S(4), S(4)))
        pygame.draw.rect(screen, (10, 14, 20), box, border_radius=S(6))
        pygame.draw.rect(screen, colour, box, max(1, S(2)), border_radius=S(6))
        chip_box = pygame.Rect(box.x + S(3), box.y + S(3), chip.get_width() + S(8), S(16))
        pygame.draw.rect(screen, colour, chip_box, border_radius=S(4))
        screen.blit(chip, chip.get_rect(center=chip_box.center))
        x = chip_box.right + S(5)
        screen.blit(number, (x, box.y + S(4)))
        x += number.get_width() + S(7)
        screen.blit(tag, (x, box.y + S(4)))
        screen.blit(arrow, arrow.get_rect(midright=(box.right - S(5), box.centery)))
        body = pygame.Rect(int(min(head[0], tail[0])), int(min(head[1], tail[1])), 1, 1)
        body.union_ip(pygame.Rect(int(max(head[0], tail[0])), int(max(head[1], tail[1])), 1, 1))
        self.train_boxes.append((box, train))
        self.train_boxes.append((body.inflate(S(10), S(10)), train))

    def _draw_stations(self, screen) -> None:
        lay = self.layout
        for st in self.sim.line.stations:
            if st.has_loop:
                x, y = lay.local(st, 0, self.gap / 2)
                ui.circle(screen, BG, (x, y), S(15))
                ui.circle(screen, WHITE, (x, y), S(12))
                label = self.f_bold.render(st.name, True, WHITE)
                lx, ly = lay.local(st, 0, S(52))
            else:
                x, y = lay.point(st.pos)
                ui.circle(screen, BG, (x, y), S(9))
                ui.circle(screen, WHITE, (x, y), S(6))
                label = self.f_small.render(st.name, True, MAP_MUTED)
                nx, ny = lay.normal(st.pos)
                lx, ly = x + nx * S(24), y + ny * S(24)
            if self.storybook:
                fnt, colour = (self.f_bold, WHITE) if st.has_loop else (self.f_small, WHITE)
                self._outlined(screen, fnt, st.name, colour, (lx, ly))
                continue
            screen.blit(label, (lx - label.get_width() / 2, ly - label.get_height() / 2))

    def _draw_top_bar(self, screen, info, speed: int) -> None:
        sim = self.sim
        pygame.draw.rect(screen, PANEL, SR(0, 0, WIDTH, TOP_BAR))
        title = self.f_title.render(f"Level {info.number} · {info.title}", True, WHITE)
        screen.blit(title, (S(18), S(16)))

        x = S(330)
        screen.blit(self.f_title.render(clock_text(sim.time, True), True, WHITE), (x, S(16)))
        x += S(110)
        self.speed_buttons = []
        for value, label in SPEEDS:
            text = self.f_bold.render(label, True, WHITE)
            rect = pygame.Rect(x, S(13), text.get_width() + S(20), S(30))
            pygame.draw.rect(screen, BUTTON_ON if speed == value else BUTTON, rect, border_radius=S(6))
            screen.blit(text, text.get_rect(center=rect.center))
            self.speed_buttons.append((rect, value))
            x = rect.right + S(6)

        # Restart the level from the beginning (same as the R key).
        x += S(8)
        text = self.f_bold.render("Restart", True, WHITE)
        self.restart_button = pygame.Rect(x, S(13), text.get_width() + S(20), S(30))
        pygame.draw.rect(screen, (120, 60, 60), self.restart_button, border_radius=S(6))
        screen.blit(text, text.get_rect(center=self.restart_button.center))
        x = self.restart_button.right

        # Leave the level and go back to the main menu (choose a line).
        x += S(6)
        text = self.f_bold.render("Menu", True, WHITE)
        self.menu_button = pygame.Rect(x, S(13), text.get_width() + S(20), S(30))
        pygame.draw.rect(screen, BUTTON, self.menu_button, border_radius=S(6))
        screen.blit(text, text.get_rect(center=self.menu_button.center))
        x = self.menu_button.right

        x += S(24)
        average = sim.average_delay()
        limit = sim.max_average_delay
        colour = GREEN if average < limit * 0.5 else YELLOW if average <= limit else RED
        text = self.f_bold.render(f"Average delay {minutes_text(average)}", True, colour)
        screen.blit(text, (x, S(19)))
        x += text.get_width() + S(14)
        screen.blit(self.f_text.render(f"(limit {limit / 60:.0f} min)", True, MUTED), (x, S(19)))
        done = sum(1 for t in sim.trains if t.state == "finished")
        text = self.f_text.render(f"Trains done {done}/{len(sim.trains)}", True, MUTED)
        screen.blit(text, (S(WIDTH - 18) - text.get_width(), S(19)))

    def _draw_requests(self, screen, hover) -> None:
        pygame.draw.rect(screen, PANEL, SR(PANEL_X, TOP_BAR, WIDTH - PANEL_X, HEIGHT - TOP_BAR))
        screen.blit(self.f_title.render("Drivers' requests", True, WHITE), (S(PANEL_X + 18), S(TOP_BAR + 14)))
        requests = sorted(self.sim.requests.values(), key=lambda r: r.created)
        y = S(TOP_BAR + 50)
        bottom = S(REQUESTS_BOTTOM)
        width = S(WIDTH - PANEL_X - 32)
        self.request_buttons = []
        if not requests:
            screen.blit(self.f_text.render("All quiet on the line.", True, MUTED), (S(PANEL_X + 18), y))
        for i, request in enumerate(requests):
            lines = self._wrap(request.text, width - S(30))
            height = S(40) + S(19) * len(lines)
            if y + height > bottom:
                more = self.f_text.render(f"+ {len(requests) - i} more…", True, MUTED)
                screen.blit(more, (S(PANEL_X + 18), y))
                break
            card = pygame.Rect(S(PANEL_X + 16), y, width, height)
            pygame.draw.rect(screen, CARD, card, border_radius=S(8))
            colour = train_colour(request.train)
            pygame.draw.rect(screen, colour, (card.x, card.y, S(5), card.h), border_radius=S(3))
            screen.blit(self.f_bold.render(request.train.name, True, WHITE), (card.x + S(16), card.y + S(9)))
            waited = self.sim.time - request.created
            age = "now" if waited < 60 else f"{waited / 60:.0f} min ago"
            name_w = self.f_bold.size(request.train.name)[0]
            screen.blit(self.f_small.render(age, True, MUTED), (card.x + S(26) + name_w, card.y + S(11)))
            # "Do it" switches the signal or points the driver is asking for.
            label = self.f_bold.render("Do it", True, WHITE)
            button = pygame.Rect(0, 0, label.get_width() + S(18), S(24))
            button.topright = (card.right - S(8), card.y + S(6))
            hovered = button.collidepoint(hover)
            pygame.draw.rect(screen, (90, 145, 230) if hovered else BUTTON_ON, button, border_radius=S(6))
            screen.blit(label, label.get_rect(center=button.center))
            self.request_buttons.append((button, request))
            for j, line in enumerate(lines):
                screen.blit(self.f_text.render(line, True, TEXT), (card.x + S(16), card.y + S(32) + S(19) * j))
            y += height + S(10)

    def _wrap(self, text: str, width: int) -> list[str]:
        lines, current = [], ""
        for word in text.split():
            test = (current + " " + word).strip()
            if self.f_text.size(test)[0] > width and current:
                lines.append(current)
                current = word
            else:
                current = test
        lines.append(current)
        return lines

    def _draw_next_trains(self, screen) -> None:
        x0, y = PANEL_X + 18, REQUESTS_BOTTOM + 10
        right = WIDTH - 18
        pygame.draw.line(screen, CARD, (S(PANEL_X + 16), S(y - 8)), (S(right), S(y - 8)), max(1, S(1)))
        screen.blit(self.f_bold.render("Next trains", True, WHITE), (S(x0), S(y)))
        waiting = sorted((t for t in self.sim.trains if t.state == "waiting"), key=lambda t: t.enter_time)
        y += 26
        if not waiting:
            screen.blit(self.f_small.render("No more trains to come.", True, MUTED), (S(x0), S(y)))
            return
        first, last = self.sim.line.stations[0].name, self.sim.line.stations[-1].name
        for train in waiting[:5]:
            colour = train_colour(train)
            screen.blit(self.f_text.render(clock_text(train.enter_time), True, TEXT), (S(x0), S(y)))
            chip = SR(x0 + 56, y + 1, 26, 18)
            pygame.draw.rect(screen, colour, chip, border_radius=S(4))
            text = self.f_bold.render(train_kind(train), True, BG)
            screen.blit(text, text.get_rect(center=chip.center))
            screen.blit(self.f_text.render(train.name.split()[-1], True, TEXT), (S(x0 + 88), S(y)))
            side = f"from {first}" if train.direction == EAST else f"from {last}"
            screen.blit(self.f_small.render(side, True, MUTED), (S(x0 + 150), S(y + 2)))
            minutes = (train.enter_time - self.sim.time) / 60
            when = self.f_bold.render("now" if minutes < 0.5 else f"{minutes:.0f} min", True, YELLOW if minutes < 3 else TEXT)
            screen.blit(when, (S(right) - when.get_width(), S(y)))
            y += 24

    def _draw_legend(self, screen) -> None:
        y = HEIGHT - 135
        screen.blit(self.f_bold.render("How to play", True, WHITE), (S(PANEL_X + 18), S(y)))
        items = [
            ("signal", "Click a signal: red ↔ green"),
            ("point", "Click points: white straight, yellow to track 2"),
            ("ring", "Pulsing ring: a driver is waiting for it"),
            ("keys", "Space pause · 1/2/3/4 speed · R restart · Esc levels"),
        ]
        for i, (kind, text) in enumerate(items):
            cy = y + 32 + i * 24
            cx = PANEL_X + 30
            if kind == "signal":
                ui.circle(screen, GREEN, (S(cx - 6), S(cy)), S(6))
                ui.circle(screen, RED, (S(cx + 8), S(cy)), S(6))
            elif kind == "point":
                pygame.draw.rect(screen, YELLOW, SR(cx - 6, cy - 6, 12, 12), border_radius=S(2))
            elif kind == "ring":
                ui.ring(screen, EAST_COLOUR, (S(cx), S(cy)), S(8), S(2))
            screen.blit(self.f_small.render(text, True, TEXT), (S(cx + 22), S(cy - 9)))

    def _draw_hover(self, screen, hover) -> None:
        obj = self.object_at(hover)
        if obj is None:
            train = self.train_at(hover)
            if train is None:
                return
            last = self.sim.line.stations[-1 if train.direction == EAST else 0].name
            stop = train.next_stop()
            where = f"next stop {stop.station.name} {clock_text(stop.arrive)}" if stop else "leaving the map"
            text = f"{train.name} to {last} · {where} · track {train.track}"
        elif isinstance(obj, Signal):
            state = "green" if obj.green else "red"
            where = "entry" if obj.is_entry else f"track {obj.track} exit"
            text = f"Signal {obj.id} · {obj.station.name} {where} · {state}"
        else:
            text = f"Points {obj.id} · {obj.station.name} · set to track {obj.track}"
        label = self.f_small.render(text, True, WHITE)
        box = label.get_rect(topleft=(hover[0] + S(14), hover[1] + S(14))).inflate(S(12), S(8))
        if box.right > S(PANEL_X):
            box.right = hover[0] - S(10)
        pygame.draw.rect(screen, (0, 0, 0), box, border_radius=S(5))
        screen.blit(label, label.get_rect(center=box.center))
