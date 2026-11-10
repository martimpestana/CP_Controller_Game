"""Train skins: how each type of train (R, IR) looks on the map.

Every type has five skins. "real" is how the trains look in real life; the others are just for
fun. Whatever the skin, a thin line under each carriage keeps the colour of the train's
direction (blue eastbound, orange westbound), so the map stays easy to read.

A carriage is drawn in its own little coordinate system, in design pixels:
  l runs along the carriage, from 0 at its front end to `length` at its rear end,
  o runs across it, from -6 (roof, always at the top of the screen) to +6 (underframe).
The same drawing is used on the map (small) and in the Customise menu (big).
"""

import math

import pygame

from railgame import ui

INK = (8, 10, 14)

TRAIN_TYPES = ("R", "IR")
TYPE_NAMES = {"R": "Regional", "IR": "Inter-Regional"}

# (id, name shown in the menu) for each train type, in menu order. The first one is the default.
SKINS = {
    "R": [
        ("real", "Real"),
        ("vintage", "Vintage"),
        ("modern", "Modern"),
        ("dragon", "Dragon"),
        ("gem", "Diamond"),
    ],
    "IR": [
        ("real", "Real"),
        ("vintage", "Steam"),
        ("modern", "Modern"),
        ("dragon", "Dragon"),
        ("gem", "Ruby"),
    ],
}

DEFAULT_SKINS = {kind: SKINS[kind][0][0] for kind in TRAIN_TYPES}

# How many carriages each type has on the map.
CARS = {"R": 2, "IR": 3}


class Car:
    """Maps carriage coordinates (l, o) to the screen, for one carriage from a to b."""

    def __init__(self, screen, a, b, k: float):
        self.screen = screen
        self.a = a
        ux, uy = b[0] - a[0], b[1] - a[1]
        size = math.hypot(ux, uy) or 1.0
        self.ux, self.uy = ux / size, uy / size
        nx, ny = -self.uy, self.ux
        if ny < 0 or (ny == 0 and nx < 0):
            nx, ny = -nx, -ny  # make o point down the screen, so the roof is always on top
        self.nx, self.ny = nx, ny
        self.k = k
        self.length = size / k

    def p(self, l: float, o: float) -> tuple[float, float]:
        k = self.k
        return (self.a[0] + (self.ux * l + self.nx * o) * k, self.a[1] + (self.uy * l + self.ny * o) * k)

    def poly(self, colour, points) -> None:
        pygame.draw.polygon(self.screen, colour, [self.p(l, o) for l, o in points])

    def band(self, o0, o1, l0, l1, colour) -> None:
        self.poly(colour, [(l0, o0), (l1, o0), (l1, o1), (l0, o1)])

    def dot(self, colour, l, o, r) -> None:
        ui.circle(self.screen, colour, self.p(l, o), max(1.0, r * self.k))

    def line(self, colour, l0, o0, l1, o1, width=1.0) -> None:
        pygame.draw.line(self.screen, colour, self.p(l0, o0), self.p(l1, o1), max(1, round(width * self.k)))


def _shade(colour, f: float):
    return tuple(max(0, min(255, round(c * f))) for c in colour)


def _windows(car: Car, front: bool, rear: bool, colour, o0=-3.0, o1=1.0, step=5.0, size=3.0, start=None, end=None):
    L = car.length
    pos = start if start is not None else (7.0 if front else 3.0)
    stop = end if end is not None else L - (7.0 if rear else 3.0)
    while pos + size <= stop:
        car.band(o0, o1, pos, pos + size, colour)
        pos += step


def _base(car: Car, body, roof, stripe) -> None:
    L = car.length
    car.band(-7.5, 7.5, -0.5, L + 0.5, INK)
    car.band(-6, 6, 0, L, body)
    car.band(-6, -4.2, 1, L - 1, roof)
    car.band(5.2, 6.8, 0.5, L - 0.5, stripe)  # direction colour, on every skin


# ---------------------------------------------------------------------- real life


def _real_r(car, front, rear, stripe, t, index) -> None:
    # CP regional diesel units: white body, red band under the windows, dark windows.
    L = car.length
    _base(car, (236, 238, 240), (150, 156, 166), stripe)
    car.band(2, 4, 0.5, L - 0.5, (200, 40, 45))
    _windows(car, front, rear, (40, 52, 70))
    if front:
        car.band(-4.5, 1.5, 1, 5, (60, 90, 120))
        car.dot((255, 236, 150), 1.4, 4.2, 0.9)
    if rear:
        car.band(-4.5, 1.5, L - 5, L - 1, (60, 90, 120))
        car.dot((230, 60, 50), L - 1.4, 4.2, 0.8)


def _real_ir(car, front, rear, stripe, t, index) -> None:
    # A diesel locomotive (orange and white) pulling stainless steel coaches.
    L = car.length
    if index == 0:
        _base(car, (232, 120, 40), (90, 90, 96), stripe)
        car.band(-1, 1.5, 0.5, L - 0.5, (240, 240, 240))
        car.band(-4.5, -0.5, 1.5, 6, (40, 52, 70))  # cab window
        for x in range(9, int(L) - 2, 3):
            car.line((150, 70, 20), x, -3.5, x, 0.5, 0.6)  # engine grilles
        car.dot((255, 236, 150), 1.4, 4.2, 0.9)
        return
    _base(car, (196, 202, 210), (130, 136, 146), stripe)
    for o in (-2.0, 2.5, 4.0):
        car.line((160, 166, 176), 0.5, o, L - 0.5, o, 0.5)  # the fluted steel sides
    _windows(car, False, rear, (40, 52, 70), o0=-3.5, o1=0.5, step=4.5)
    if rear:
        car.dot((230, 60, 50), L - 1.4, 4.2, 0.8)


# ---------------------------------------------------------------------- vintage / steam


def _vintage_r(car, front, rear, stripe, t, index) -> None:
    # A 1950s railcar: cream on top, maroon below, rounded ends.
    L = car.length
    _base(car, (226, 210, 170), (110, 92, 70), stripe)
    car.band(0.5, 5.2, 0, L, (120, 36, 40))
    car.line((200, 170, 90), 0.3, 0.5, L - 0.3, 0.5, 0.6)
    _windows(car, front, rear, (50, 46, 40), o0=-3.2, o1=-0.2, step=4.0, size=2.6)
    if front:
        car.poly((226, 210, 170), [(0, -4.2), (-1.8, -2), (-1.8, 3), (0, 5)])
        car.dot((255, 220, 140), -1, 3, 0.9)
    if rear:
        car.dot((230, 60, 50), L - 1.2, 3.8, 0.8)


def _vintage_ir(car, front, rear, stripe, t, index) -> None:
    L = car.length
    if index == 0:
        # A black steam locomotive with a chimney, red wheels and a puff of smoke.
        car.band(-7.5, 7.5, -0.5, L + 0.5, INK)
        car.band(-4, 4, 0, L, (34, 34, 38))  # boiler
        car.band(-6, 4, L - 7, L, (40, 40, 46))  # cab
        car.band(-4.5, -1, L - 6, L - 2, (230, 190, 90))  # lit cab window
        car.band(-9, -4, 3, 5.5, (34, 34, 38))  # chimney
        car.band(-4.5, -3.5, 0, L, (180, 150, 60))  # brass line
        for x in (4, 10, 16):
            if x < L - 1:
                car.dot((180, 40, 40), x, 4.5, 2.2)
        car.poly((60, 60, 66), [(0, 2), (-2.5, 6.5), (0, 6.5)])  # cow catcher
        car.dot((255, 230, 140), 0.5, -1, 1.1)
        car.band(5.2, 6.8, 0.5, L - 0.5, stripe)
        phase = (t * 1.5) % 1.0
        for i in range(3):
            f = (phase + i / 3) % 1.0
            car.dot(_shade((200, 200, 205), 1 - 0.5 * f), 4 + 6 * f, -10 - 6 * f, 1.4 + 2.2 * f)
        return
    # Old wooden coaches.
    _base(car, (40, 92, 60), (60, 50, 40), stripe)
    for x in range(2, int(L) - 1, 4):
        car.line((30, 70, 46), x, -4, x, 5, 0.5)
    _windows(car, False, rear, (220, 200, 140), o0=-3.2, o1=-0.4, step=4.0, size=2.4)
    car.line((200, 170, 90), 0.5, 1.5, L - 0.5, 1.5, 0.5)
    if rear:
        car.dot((230, 60, 50), L - 1.2, 3.8, 0.8)


# ---------------------------------------------------------------------- modern


def _modern(car, front, rear, stripe, t, index, glow) -> None:
    L = car.length
    car.band(-7.5, 7.5, -0.5, L + 0.5, INK)
    car.band(-6, 6, 0, L, (46, 50, 58))
    car.band(-6, -4.8, 0.5, L - 0.5, (90, 96, 108))
    car.band(-3.6, 0.8, 0.5 if not front else 5, L - (0.5 if not rear else 5), (24, 32, 44))  # long glass
    car.band(1.6, 2.6, 0, L, glow)  # LED strip
    car.band(5.2, 6.8, 0.5, L - 0.5, stripe)
    for x in range(6, int(L) - 3, 6):
        car.line((60, 70, 86), x, -3.6, x, 0.8, 0.4)
    if front:  # pointed nose
        car.poly(INK, [(5.5, -7.5), (-5, 1), (-5, 3), (5.5, 7.5)])
        car.poly((46, 50, 58), [(5, -6), (-4, 1.2), (-4, 2.6), (5, 6)])
        car.poly((24, 32, 44), [(5, -3.6), (0.5, -0.4), (5, 0.8)])
        car.dot((230, 250, 255), -2.6, 2.6, 0.9)
    if rear:
        car.poly(INK, [(L - 5.5, -7.5), (L + 5, 1), (L + 5, 3), (L - 5.5, 7.5)])
        car.poly((46, 50, 58), [(L - 5, -6), (L + 4, 1.2), (L + 4, 2.6), (L - 5, 6)])
        car.dot((255, 60, 60), L + 2.6, 2.6, 0.8)


def _modern_r(car, front, rear, stripe, t, index) -> None:
    _modern(car, front, rear, stripe, t, index, (120, 255, 150))


def _modern_ir(car, front, rear, stripe, t, index) -> None:
    _modern(car, front, rear, stripe, t, index, (255, 90, 200))


# ---------------------------------------------------------------------- dragons


def _dragon(car, front, rear, stripe, t, index, body, belly, spikes) -> None:
    L = car.length
    dark = _shade(body, 0.65)
    car.band(-7.5, 7.5, -0.5, L + 0.5, INK)
    # Spikes along the back.
    for x in range(2, int(L) - 1, 4):
        car.poly(INK, [(x - 2, -6), (x, -10.5), (x + 2, -6)])
        car.poly(spikes, [(x - 1.3, -6), (x, -9.3), (x + 1.3, -6)])
    car.band(-6, 6, 0, L, body)
    car.band(2.5, 6, 0, L, belly)
    for x in range(1, int(L), 3):  # belly plates
        car.line(_shade(belly, 0.8), x, 2.5, x, 6, 0.5)
    # Scales: rows of little arcs.
    for row, o in enumerate((-4.2, -1.6, 1.0)):
        for x in range(1 + (row % 2) * 2, int(L) - 1, 4):
            car.poly(dark, [(x, o), (x + 1.5, o + 1.6), (x + 3, o)])
    car.band(5.2, 6.8, 0.5, L - 0.5, stripe)
    if front:  # the head, sticking out in front, with an eye, horns and a bit of fire
        car.poly(INK, [(1, -7.5), (-4, -7), (-11, -3), (-12, 1.5), (-9, 4.5), (-2, 6), (1, 7.5)])
        car.poly(body, [(0.5, -6.5), (-4, -6), (-10, -2.6), (-10.8, 1.2), (-8.5, 3.6), (-2, 5), (0.5, 6.5)])
        car.poly(belly, [(-10.8, 1.2), (-8.5, 3.6), (-2, 5), (0.5, 5.2), (0.5, 2.6), (-6, 2)])
        car.line(INK, -10.5, 1.4, -3, 2.4, 0.6)  # mouth
        for x in (-9, -7, -5):
            car.poly((240, 240, 230), [(x, 1.6), (x + 0.7, 3), (x + 1.4, 1.8)])  # teeth
        car.poly(INK, [(-3, -6.2), (0, -12), (0.5, -6)])
        car.poly(spikes, [(-2.4, -6.2), (-0.2, -10.6), (0, -6.2)])  # horn
        car.dot((255, 220, 40), -5.5, -3, 1.4)
        car.dot(INK, -5.8, -3, 0.6)
        car.dot(INK, -10.4, -1.6, 0.4)  # nostril
        flame = 0.5 + 0.5 * math.sin(t * 9 + index)
        if flame > 0.35:
            car.poly((255, 140, 30), [(-11.5, 0), (-15 - 3 * flame, -1.5), (-14 - 2 * flame, 1), (-16 - 4 * flame, 2.5), (-11.5, 2.4)])
            car.poly((255, 230, 90), [(-11.5, 0.6), (-13.5 - 2 * flame, 0.6), (-11.5, 1.8)])
    if rear:  # a tail curling off the back
        sway = 1.5 * math.sin(t * 3 + index)
        car.poly(INK, [(L - 1, -4), (L + 6, -2 + sway), (L + 12, -5 + sway), (L + 11, -1 + sway), (L + 6, 3 + sway), (L - 1, 5)])
        car.poly(body, [(L - 1, -3), (L + 6, -1 + sway), (L + 10.5, -3.8 + sway), (L + 10, -1.2 + sway), (L + 6, 2 + sway), (L - 1, 4)])
        car.poly(spikes, [(L + 9, -3.5 + sway), (L + 13, -7 + sway), (L + 11, -2 + sway)])


def _dragon_r(car, front, rear, stripe, t, index) -> None:
    _dragon(car, front, rear, stripe, t, index, (60, 150, 70), (210, 200, 120), (230, 220, 160))


def _dragon_ir(car, front, rear, stripe, t, index) -> None:
    _dragon(car, front, rear, stripe, t, index, (190, 40, 40), (240, 170, 80), (250, 210, 120))


# ---------------------------------------------------------------------- precious stones


def _gem(car, front, rear, stripe, t, index, light, mid, dark) -> None:
    L = car.length
    car.band(-7.5, 7.5, -0.5, L + 0.5, INK)
    car.band(-6, 6, 0, L, mid)
    # Facets: a row of diamonds, lit from the top left.
    step = 5.0
    x = 0.0
    while x < L - 0.1:
        x1 = min(L, x + step)
        m = (x + x1) / 2
        car.poly(light, [(x, -6), (m, -6), (x, 0)])
        car.poly(_shade(light, 0.85), [(m, -6), (x1, -6), (x1, 0)])
        car.poly(dark, [(x, 0), (m, 6), (x, 6)])
        car.poly(_shade(dark, 1.25), [(x1, 0), (x1, 6), (m, 6)])
        car.line(_shade(light, 1.1), x, 0, m, -6, 0.4)
        car.line(_shade(dark, 0.8), m, 6, x1, 0, 0.4)
        x = x1
    if front:
        car.poly(INK, [(0.5, -7.5), (-4.5, 0), (0.5, 7.5)])
        car.poly(light, [(0, -6), (-3.5, 0), (0, 0)])
        car.poly(dark, [(0, 0), (-3.5, 0), (0, 6)])
    if rear:
        car.poly(INK, [(L - 0.5, -7.5), (L + 4.5, 0), (L - 0.5, 7.5)])
        car.poly(_shade(light, 0.85), [(L, -6), (L + 3.5, 0), (L, 0)])
        car.poly(dark, [(L, 0), (L + 3.5, 0), (L, 6)])
    car.band(5.2, 6.8, 0.5, L - 0.5, stripe)
    # Sparkles that come and go.
    for i, (sx, so) in enumerate(((0.25, -3.5), (0.6, -1.5), (0.85, -4.2))):
        s = math.sin(t * 4 + i * 2.1 + index * 1.3)
        if s > 0.4:
            r = (s - 0.4) * 4
            cx = sx * L
            car.line((255, 255, 255), cx - r, so, cx + r, so, 0.5)
            car.line((255, 255, 255), cx, so - r, cx, so + r, 0.5)


def _gem_r(car, front, rear, stripe, t, index) -> None:
    _gem(car, front, rear, stripe, t, index, (235, 250, 255), (170, 220, 240), (110, 170, 205))  # diamond


def _gem_ir(car, front, rear, stripe, t, index) -> None:
    _gem(car, front, rear, stripe, t, index, (255, 150, 170), (215, 40, 80), (140, 15, 50))  # ruby


DRAW = {
    ("R", "real"): _real_r,
    ("IR", "real"): _real_ir,
    ("R", "vintage"): _vintage_r,
    ("IR", "vintage"): _vintage_ir,
    ("R", "modern"): _modern_r,
    ("IR", "modern"): _modern_ir,
    ("R", "dragon"): _dragon_r,
    ("IR", "dragon"): _dragon_ir,
    ("R", "gem"): _gem_r,
    ("IR", "gem"): _gem_ir,
}


def draw_car(screen, a, b, kind: str, skin: str, stripe, index: int, cars: int, k: float, t: float) -> None:
    """Draw carriage number `index` (0 = the front) of a train of `cars` carriages, from a
    (its front end) to b (its rear end), in screen pixels; k is screen pixels per design pixel."""
    draw = DRAW.get((kind, skin)) or DRAW.get((kind, "real")) or _real_r
    draw(Car(screen, a, b, k), index == 0, index == cars - 1, stripe, t, index)


def draw_preview(screen, kind: str, skin: str, x: float, y: float, k: float, stripe, t: float, car_len=22.0, gap=3.0) -> None:
    """A whole train running to the left, its front at (x, y), as in the Customise menu."""
    cars = CARS.get(kind, 2)
    for i in reversed(range(cars)):
        a = (x + i * (car_len + gap) * k, y)
        b = (a[0] + car_len * k, y)
        if i < cars - 1:
            pygame.draw.line(screen, INK, b, (b[0] + gap * k, y), max(1, round(3 * k)))
        draw_car(screen, a, b, kind, skin, stripe, i, cars, k, t)
