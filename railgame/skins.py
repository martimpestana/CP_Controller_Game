"""Train skins: how each type of train (R, IR, M, H) looks on the map.

Every type has six skins. "real" is how the trains look in real life; the others are just for
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

TRAIN_TYPES = ("R", "IR", "M", "H")
TYPE_NAMES = {"R": "Regional", "IR": "Inter-Regional", "M": "Freight", "H": "Historic"}

# (id, name shown in the menu) for each train type, in menu order. The first one is the default.
SKINS = {
    "R": [
        ("real", "Real"),
        ("vintage", "Vintage"),
        ("modern", "Modern"),
        ("future", "Futuristic"),
        ("dragon", "Jade dragon"),
        ("gem", "Diamond"),
    ],
    "IR": [
        ("real", "Real"),
        ("vintage", "Steam"),
        ("modern", "Modern"),
        ("future", "Futuristic"),
        ("dragon", "Fire dragon"),
        ("gem", "Ruby"),
    ],
    "M": [
        ("real", "Real"),
        ("vintage", "Steam"),
        ("modern", "Modern"),
        ("future", "Futuristic"),
        ("dragon", "Ice dragon"),
        ("gem", "Emerald"),
    ],
    "H": [
        ("real", "Real"),
        ("vintage", "Royal"),
        ("modern", "Panoramic"),
        ("future", "Futuristic"),
        ("dragon", "Iron dragon"),
        ("gem", "Amethyst"),
    ],
}

DEFAULT_SKINS = {kind: SKINS[kind][0][0] for kind in TRAIN_TYPES}

# How far a skin reaches beyond the front and the rear of the train (heads, fire, tails),
# in design pixels, so the menu can fit the whole picture in its card.
EXTENT = {("R", "dragon"): (23, 19), ("IR", "dragon"): (30, 19), ("R", "modern"): (6, 6), ("R", "future"): (12, 8), ("IR", "future"): (12, 8), ("IR", "modern"): (13, 9),
          ("R", "gem"): (5, 5), ("IR", "gem"): (5, 5), ("R", "vintage"): (2, 0), ("IR", "vintage"): (3, 0),
          ("M", "vintage"): (3, 0), ("M", "modern"): (4, 0), ("M", "future"): (12, 5), ("M", "dragon"): (29, 19), ("M", "gem"): (5, 5),
          ("H", "real"): (3, 0), ("H", "vintage"): (3, 0), ("H", "modern"): (4, 0), ("H", "future"): (12, 8), ("H", "dragon"): (30, 18),
          ("H", "gem"): (5, 5)}

# How many carriages each type has on the map.
CARS = {"R": 2, "IR": 3, "M": 6, "H": 4}


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


CONTAINERS = [(40, 110, 170), (190, 60, 50), (230, 170, 40), (60, 140, 90), (210, 210, 214)]


def _real_m(car, front, rear, stripe, t, index) -> None:
    # A freight diesel locomotive pulling container flats and cement wagons.
    L = car.length
    if index == 0:
        _base(car, (52, 60, 72), (34, 38, 46), stripe)
        car.band(-1, 1.5, 0.5, L - 0.5, (240, 196, 40))  # yellow band
        car.band(-4.5, -0.5, 1.5, 6, (40, 52, 70))  # cab window
        for x in range(9, int(L) - 2, 3):
            car.line((24, 28, 34), x, -3.5, x, -1.5, 0.6)
        car.dot((255, 236, 150), 1.4, 4.2, 0.9)
        return
    car.band(-7.5, 7.5, -0.5, L + 0.5, INK)
    car.band(3.5, 5.2, 0, L, (70, 66, 62))  # the flat underframe
    if index % 2:
        colour = CONTAINERS[index % len(CONTAINERS)]
        car.band(-5.5, 3.5, 0.8, L - 0.8, colour)
        for x in range(3, int(L) - 1, 2):
            car.line(_shade(colour, 0.75), x, -5, x, 3, 0.4)  # corrugated sides
    else:
        grey = (176, 172, 164)
        car.poly(grey, [(1, 3.5), (2.5, -5), (L - 2.5, -5), (L - 1, 3.5)])  # cement hopper
        car.band(-5, -4, 3, L - 3, _shade(grey, 0.7))
    car.band(5.2, 6.8, 0.5, L - 0.5, stripe)
    if rear:
        car.dot((230, 60, 50), L - 1.2, 4.2, 0.8)


def _real_h(car, front, rear, stripe, t, index) -> None:
    # The Douro historic train: a black steam locomotive and old brown wooden coaches.
    L = car.length
    if index == 0:
        _vintage_ir(car, front, rear, stripe, t, 0)
        return
    _base(car, (120, 62, 36), (60, 44, 34), stripe)
    for x in range(2, int(L) - 1, 4):
        car.line((96, 48, 28), x, -4, x, 5, 0.5)  # wooden planks
    _windows(car, False, rear, (236, 214, 150), o0=-3.2, o1=-0.4, step=4.0, size=2.4)
    car.line((214, 180, 96), 0.5, 1.5, L - 0.5, 1.5, 0.5)
    if rear:
        car.dot((230, 60, 50), L - 1.2, 3.8, 0.8)


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


def _steam_loco(car, stripe, t, boiler=(34, 34, 38), cab=(40, 40, 46), trim=(180, 150, 60), wheel=(180, 40, 40)) -> None:
    """A steam locomotive with a chimney, big wheels and a puff of smoke."""
    L = car.length
    car.band(-7.5, 7.5, -0.5, L + 0.5, INK)
    car.band(-4, 4, 0, L, boiler)
    car.band(-6, 4, L - 7, L, cab)
    car.band(-4.5, -1, L - 6, L - 2, (230, 190, 90))  # lit cab window
    car.band(-9, -4, 3, 5.5, boiler)  # chimney
    car.band(-4.5, -3.5, 0, L, trim)  # brass line
    for x in (4, 10, 16):
        if x < L - 1:
            car.dot(wheel, x, 4.5, 2.2)
    car.poly((60, 60, 66), [(0, 2), (-2.5, 6.5), (0, 6.5)])  # cow catcher
    car.dot((255, 230, 140), 0.5, -1, 1.1)
    car.band(5.2, 6.8, 0.5, L - 0.5, stripe)
    phase = (t * 1.5) % 1.0
    for i in range(3):
        f = (phase + i / 3) % 1.0
        car.dot(_shade((200, 200, 205), 1 - 0.5 * f), 4 + 6 * f, -10 - 6 * f, 1.4 + 2.2 * f)


def _vintage_ir(car, front, rear, stripe, t, index) -> None:
    L = car.length
    if index == 0:
        _steam_loco(car, stripe, t)
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


def _pantograph(car, l, t) -> None:
    """The arm on the roof that touches the overhead wire."""
    car.line(INK, l - 2.5, -6, l, -9.5, 0.9)
    car.line(INK, l + 2.5, -6, l, -9.5, 0.9)
    car.line((150, 156, 166), l - 2.5, -6, l, -9.5, 0.45)
    car.line((150, 156, 166), l + 2.5, -6, l, -9.5, 0.45)
    car.line(INK, l - 3, -9.8, l + 3, -9.8, 0.9)
    car.line((200, 206, 216), l - 3, -9.8, l + 3, -9.8, 0.45)
    if math.sin(t * 13 + l) > 0.92:  # the odd spark from the wire
        car.dot((180, 220, 255), l + 1, -10.3, 0.7)


def _modern_r(car, front, rear, stripe, t, index) -> None:
    """R: a modern electric unit, like a new metro: white and graphite, one long window, doors
    marked with green lights, a glowing strip, and a big rounded windscreen."""
    L = car.length
    white, graphite, roof = (234, 238, 242), (52, 58, 68), (176, 182, 192)
    glass, glass_light, led = (24, 32, 46), (70, 96, 130), (110, 255, 160)
    car.band(-7.5, 7.5, -0.5, L + 0.5, INK)
    car.band(-6, 6, 0, L, white)
    car.band(-6, -4.8, 0.3, L - 0.3, roof)
    car.band(2.8, 6, 0, L, graphite)
    g0, g1 = (5.0 if front else 1.2), L - (5.0 if rear else 1.2)
    car.band(-4, 0.9, g0, g1, glass)
    # Reflections running across the glass.
    x = g0 + ((t * 6 + index * 5) % 9.0)
    while x < g1 - 1:
        car.poly(glass_light, [(x, -4), (x + 1.4, -4), (x - 0.4, 0.9), (x - 1.8, 0.9)])
        x += 9.0
    # Doors: a lighter outline through the window band and the skirt, with a green light above.
    for d in (L * 0.3, L * 0.72):
        car.band(-4, 2.8, d - 1.6, d + 1.6, (205, 210, 218))
        car.band(-3.4, 0.6, d - 1.1, d - 0.15, glass)
        car.band(-3.4, 0.6, d + 0.15, d + 1.1, glass)
        car.dot(led, d, -4.4, 0.45)
    car.band(1.5, 2.3, 0, L, led)
    car.line(_shade(led, 0.55), 0, 2.6, L, 2.6, 0.3)
    car.band(5.2, 6.8, 0.5, L - 0.5, stripe)
    if index == 0:
        _pantograph(car, L * 0.6, t)
    for end, sign in ((front, 1), (rear, -1)):
        if not end:
            continue
        x0 = 0 if sign == 1 else L

        def P(dl, o):
            return (x0 - sign * dl, o)

        nose = [P(0, -6), P(2, -5.6), P(3.6, -3.8), P(4.3, -0.5), P(4.1, 3), P(3.2, 5.4), P(0, 6)]
        car.poly(INK, [P(0, -7.5), P(2.6, -7), P(4.8, -4.4), P(5.6, -0.5), P(5.4, 3.4), P(4.2, 7), P(0, 7.5)])
        car.poly(white, nose)
        car.poly(graphite, [P(0, 2.8), P(4.15, 2.8), P(4.1, 3), P(3.2, 5.4), P(0, 6)])
        car.poly(glass, [P(0, -5), P(2, -4.6), P(3.3, -3), P(3.8, -0.3), P(3.7, 0.9), P(0, 0.9)])
        car.poly(glass_light, [P(1.2, -4.8), P(2.2, -4.4), P(1, 0.9), P(0.2, 0.9)])
        light = (240, 250, 255) if sign == 1 else (255, 60, 60)
        car.band(1.5, 2.3, *sorted((x0, x0 - sign * 4.1)), led)
        car.dot(light, x0 - sign * 3.4, 3.8, 0.7)
        car.dot(light, x0 - sign * 2.3, 4.2, 0.55)


def _modern_ir(car, front, rear, stripe, t, index) -> None:
    """IR: a high-speed train: white, with a deep blue swoosh and a pink line, small windows and a
    long pointed nose with the cab window on top."""
    L = car.length
    white, blue, pink = (242, 244, 248), (28, 58, 150), (240, 70, 170)
    glass = (26, 34, 50)
    car.band(-7.5, 7.5, -0.5, L + 0.5, INK)
    car.band(-6, 6, 0, L, white)
    car.band(-6, -5, 0.3, L - 0.3, (196, 202, 212))
    car.band(2.2, 6, 0, L, blue)
    car.band(1.2, 1.7, 0, L, pink)
    _windows(car, False, False, glass, o0=-3.6, o1=-0.9, step=3.6, size=2.4, start=2.0, end=L - 2.0)
    # A shine sliding along the body.
    s = ((t * 0.7 + index * 0.25) % 1.5 - 0.25) * L
    if 0 < s < L - 2:
        car.poly((255, 255, 255), [(s, -4.6), (s + 1.2, -4.6), (s + 0.4, -4.2), (s - 0.8, -4.2)])
    car.band(5.2, 6.8, 0.5, L - 0.5, stripe)
    if index == 1:
        _pantograph(car, L * 0.5, t)
    if front:
        top = [(0, -6), (-3, -5.4), (-6, -4), (-9, -1.6), (-11.5, 1.4)]
        bottom = [(-11.5, 2.6), (-9, 4.6), (-5, 5.7), (0, 6)]
        car.poly(INK, [(l * 1.08 + 0.2, o * 1.2) for l, o in top + bottom])
        car.poly(white, top + bottom)
        car.poly(blue, [(0, 2.2), (-6, 2.9), (-11.5, 2.6), (-9, 4.6), (-5, 5.7), (0, 6)])
        car.poly(pink, [(0, 1.2), (-6, 2.0), (-11, 2.1), (-6, 2.5), (0, 1.7)])
        car.poly(glass, [(-1.5, -5.2), (-4.5, -4.3), (-7, -2.6), (-6.6, -1.6), (-1.5, -2.6)])
        car.poly((90, 120, 160), [(-2.5, -4.9), (-3.6, -4.5), (-2.6, -2.8), (-1.6, -2.7)])
        car.dot((240, 250, 255), -10.2, 2.0, 0.7)
    if rear:
        top = [(L, -6), (L + 3, -5.2), (L + 6, -3), (L + 8, 0.2)]
        bottom = [(L + 8, 1.6), (L + 5, 4.8), (L, 6)]
        car.poly(INK, [(L + (l - L) * 1.1 + 0.2, o * 1.2) for l, o in top + bottom])
        car.poly(white, top + bottom)
        car.poly(blue, [(L, 2.2), (L + 7.6, 1.6), (L + 5, 4.8), (L, 6)])
        car.poly(pink, [(L, 1.2), (L + 6, 0.9), (L, 1.7)])
        car.poly(glass, [(L + 1.2, -5.1), (L + 3.6, -4.3), (L + 5, -2.8), (L + 1.2, -2.6)])
        car.dot((255, 60, 60), L + 7, 1.2, 0.6)


# ---------------------------------------------------------------------- futuristic


def _future(car, front, rear, stripe, t, index, neon, accent, fins: bool) -> None:
    """A maglev floating over the track: no wheels, a dark glossy shell with one long canopy,
    neon edges that pulse, energy running along the side and a glow underneath."""
    L = car.length
    shell, shell_top, canopy = (18, 22, 32), (48, 56, 76), (10, 14, 24)
    pulse = 0.55 + 0.45 * math.sin(t * 4 + index * 0.8)
    glow = _lerp_colour(_shade(neon, 0.45), neon, pulse)
    # Glow under the train: it floats, so there are no wheels, just light.
    for i, o in enumerate((8.6, 7.8)):
        car.band(o - 0.35, o + 0.35, 1 + i, L - 1 - i, _shade(neon, 0.35 + 0.3 * i * pulse))
    car.band(-6.6, 6.6, -0.3, L + 0.3, INK)
    car.band(-5.6, 5.6, 0, L, shell)
    car.band(-5.6, -3.6, 0, L, shell_top)
    # One long tinted canopy with a sharp reflection.
    c0, c1 = (6.0 if front else 0.0), L - (5.0 if rear else 0.0)
    car.band(-3.4, -0.4, c0, c1, canopy)
    car.line(_shade(neon, 0.7), c0, -3.4, c1, -3.4, 0.3)
    shine = c0 + ((t * 9 + index * 7) % max(1.0, c1 - c0 + 6)) - 3
    if c0 < shine < c1 - 1.5:
        car.poly((150, 190, 230), [(shine, -3.4), (shine + 1.5, -3.4), (shine + 0.8, -0.4), (shine - 0.7, -0.4)])
    # Neon edges, and energy pulses running back along the side.
    car.band(-5.6, -5.0, 0, L, glow)
    car.band(4.4, 5.0, 0, L, glow)
    car.band(1.3, 1.8, 0, L, _shade(accent, 0.6))
    for i in range(3):
        x = ((t * 18 + i * L / 3 + index * 4) % L)
        car.band(1.0, 2.1, x, min(L, x + 1.6), accent)
    car.band(5.4, 6.4, 0.5, L - 0.5, stripe)
    if fins and index == 1:  # a blade along the roof
        car.poly(INK, [(L * 0.25, -5.6), (L * 0.55, -9.5), (L * 0.8, -9.5), (L * 0.75, -5.6)])
        car.poly(shell_top, [(L * 0.3, -5.6), (L * 0.56, -8.8), (L * 0.77, -8.8), (L * 0.72, -5.6)])
        car.line(accent, L * 0.56, -8.8, L * 0.77, -8.8, 0.5)
    if front:
        top = [(0, -5.6), (-3, -5.2), (-6.5, -3.4), (-9.5, -0.6), (-10.5, 1.6)]
        bottom = [(-10.5, 2.4), (-8, 4.4), (-4, 5.4), (0, 5.6)]
        car.poly(INK, [(l * 1.08 + 0.2, o * 1.18) for l, o in top + bottom])
        car.poly(shell, top + bottom)
        car.poly(shell_top, [(0, -5.6), (-3, -5.2), (-6.5, -3.4), (-5, -2.6), (0, -3.6)])
        car.poly(canopy, [(0, -3.4), (-5, -2.6), (-7.6, -0.6), (0, -0.4)])
        car.line(glow, 0, -5.3, -3, -4.9, 0.6)
        car.line(glow, -3, -4.9, -6.5, -3.1, 0.6)
        car.line(glow, -6.5, -3.1, -9.6, -0.2, 0.6)
        car.line(glow, -4, 5.0, 0, 5.0, 0.6)
        car.line((240, 255, 255), -10, 1.2, -8, 1.8, 0.7)  # light bar
        if fins:
            car.poly(INK, [(-2, 4.6), (-6, 9), (-1, 9), (1, 4.6)])
            car.poly(accent, [(-1.6, 5), (-5, 8.4), (-1.2, 8.4), (0.6, 5)])
    if rear:
        top = [(L, -5.6), (L + 3, -4.8), (L + 6, -2.4), (L + 7, 0.6)]
        bottom = [(L + 7, 1.4), (L + 5, 4.2), (L, 5.6)]
        car.poly(INK, [(L + (l - L) * 1.1 + 0.2, o * 1.18) for l, o in top + bottom])
        car.poly(shell, top + bottom)
        car.line(glow, L, -5.3, L + 3, -4.6, 0.6)
        car.line(glow, L + 3, -4.6, L + 6, -2.2, 0.6)
        car.line((255, 50, 90), L + 6.6, 0.4, L + 5.6, 2.6, 0.7)
        if fins:
            car.poly(INK, [(L - 1, -5.6), (L + 4, -11), (L + 6, -11), (L + 4, -4.6)])
            car.poly(accent, [(L - 0.4, -5.6), (L + 4.2, -10.4), (L + 5.4, -10.4), (L + 3.6, -4.8)])


def _future_r(car, front, rear, stripe, t, index) -> None:
    _future(car, front, rear, stripe, t, index, (0, 230, 255), (140, 255, 250), False)


def _future_ir(car, front, rear, stripe, t, index) -> None:
    _future(car, front, rear, stripe, t, index, (190, 90, 255), (255, 200, 70), True)


# ---------------------------------------------------------------------- dragons


def _lerp_colour(c0, c1, f: float):
    return tuple(round(a + (b - a) * f) for a, b in zip(c0, c1))


def _jade_dragon(car, front, rear, stripe, t, index) -> None:
    """R: a long, wavy eastern dragon in jade and gold, with a flame mane, whiskers and antlers,
    chasing a glowing pearl."""
    L = car.length
    jade, jade_dark, jade_light = (46, 160, 112), (24, 104, 74), (120, 220, 170)
    gold, gold_dark, mane = (244, 202, 84), (190, 140, 40), (236, 84, 56)
    phase = index * 2.4 + t * 2.0

    def centre(l):  # the body snakes up and down along the carriage
        return 0.4 + 1.3 * math.sin(l / 7.0 + phase)

    steps = [i * L / 16 for i in range(17)]
    top = [(l, centre(l) - 4.6) for l in steps]
    bottom = [(l, centre(l) + 4.6) for l in steps]
    belly_top = [(l, centre(l) + 1.6) for l in steps]
    # Mane: little flames along the back, flickering.
    for i, l in enumerate(steps[1:-1:2]):
        h = 3.2 + 1.2 * math.sin(t * 7 + i * 1.7 + index)
        c = centre(l) - 4.4
        car.poly(INK, [(l - 1.8, c + 0.6), (l + 0.6, c - h - 0.8), (l + 1.8, c + 0.6)])
        car.poly(mane, [(l - 1.2, c + 0.4), (l + 0.5, c - h), (l + 1.2, c + 0.4)])
        car.poly(gold, [(l - 0.4, c + 0.3), (l + 0.3, c - h * 0.5), (l + 0.6, c + 0.3)])
    car.poly(INK, [(l, o - 1) for l, o in top] + [(l, o + 1) for l, o in reversed(bottom)])
    car.poly(jade, top + list(reversed(bottom)))
    car.poly(gold, belly_top + list(reversed(bottom)))
    for l in steps[1:-1]:  # belly plates
        car.line(gold_dark, l, centre(l) + 1.8, l, centre(l) + 4.3, 0.4)
    # Scales: rows of little half-moons, light on top and dark below.
    for row, (off, colour) in enumerate(((-3.0, jade_light), (-0.6, jade_dark))):
        x = 1.0 + row * 1.5
        while x < L - 1.5:
            c = centre(x) + off
            car.poly(colour, [(x, c), (x + 0.75, c + 1.2), (x + 1.5, c)])
            x += 3.0
    car.band(5.8, 7.0, 0.5, L - 0.5, stripe)
    if index % 2 == 0:  # a golden claw under some carriages
        c = centre(L * 0.5) + 4.2
        for dx in (-1.2, 0, 1.2):
            car.poly(INK, [(L * 0.5 + dx - 0.6, c), (L * 0.5 + dx, c + 2.6), (L * 0.5 + dx + 0.6, c)])
            car.poly(gold, [(L * 0.5 + dx - 0.35, c), (L * 0.5 + dx, c + 2.1), (L * 0.5 + dx + 0.35, c)])
    if front:
        c = centre(0)
        sway = math.sin(t * 2.5)
        # Antlers, branching back.
        for base, tip, branch in (((-2, c - 4), (4, c - 11), (1.5, c - 9.5)), ((-4, c - 3.5), (0, c - 10), (-1.5, c - 8.5))):
            car.line(INK, *base, *tip, 1.4)
            car.line(gold, *base, *tip, 0.8)
            car.line(gold, branch[0], branch[1], branch[0] - 1.6, branch[1] - 1.8, 0.6)
        head = [(1, c - 4.6), (-3, c - 5.4), (-7, c - 4), (-11, c - 2.2), (-12.5, c - 0.5), (-12, c + 1),
                (-8, c + 1.6), (-11.5, c + 3.2), (-9, c + 4.6), (-3, c + 4.8), (1, c + 4.6)]
        car.poly(INK, [(l * 1.08 - 0.3, o * 1.12) for l, o in head])
        car.poly(jade, head)
        car.poly(gold, [(-8, c + 1.6), (-11.5, c + 3.2), (-9, c + 4.6), (-3, c + 4.8), (-3, c + 2.4)])  # jaw
        for i, o in enumerate((-4.5, -2, 0.5, 3)):  # a flame mane behind the head
            reach = 4.5 + 1.2 * math.sin(t * 6 + i)
            car.poly(INK, [(-1.5, c + o - 1.6), (-1.5 + reach + 0.8, c + o - 2.2), (-1.5, c + o + 1.6)])
            car.poly(mane, [(-1.2, c + o - 1.2), (-1.2 + reach, c + o - 1.8), (-1.2, c + o + 1.2)])
        car.poly((255, 255, 240), [(-10.8, c + 1.4), (-10.2, c + 2.6), (-9.6, c + 1.5)])  # fang
        car.dot(INK, -5.6, c - 2.3, 1.5)
        car.dot((230, 40, 40), -5.6, c - 2.3, 1.1)
        car.dot((255, 230, 120), -5.9, c - 2.6, 0.45)
        car.dot(INK, -11.6, c - 1.2, 0.45)  # nostril
        # Long whiskers, waving.
        for o0, bend in ((-0.4, -1), (0.6, 1)):
            pts = [(-11.5 - i * 1.6, c + o0 + bend * (i * 0.5) + sway * i * 0.35) for i in range(6)]
            pts = [(-11.5, c + o0)] + [(l + i * 2.4, o) for i, (l, o) in enumerate(pts)]
            for p0, p1 in zip(pts, pts[1:]):
                car.line(INK, *p0, *p1, 0.9)
                car.line(gold, *p0, *p1, 0.55)
        # Beard.
        car.poly(gold_dark, [(-6, c + 4.6), (-5, c + 8 + sway * 0.5), (-4, c + 4.6)])
        # The pearl it is chasing.
        glow = 0.5 + 0.5 * math.sin(t * 4)
        px, po = -19 - 1.5 * math.sin(t * 1.3), c - 3 + math.sin(t * 2)
        car.dot(_lerp_colour((120, 160, 255), (220, 240, 255), glow), px, po, 2.6 + 0.4 * glow)
        car.dot((255, 255, 255), px, po, 1.6)
        car.dot((255, 255, 255), px - 0.6, po - 0.6, 0.6)
    if rear:
        c = centre(L)
        wag = 2.0 * math.sin(t * 3 + index)
        tail = [(L - 0.5, c - 4.4), (L + 5, c - 2.5 + wag * 0.5), (L + 10, c - 1 + wag), (L + 14, c - 1.5 + wag),
                (L + 10, c + 1 + wag), (L + 5, c + 2.6 + wag * 0.5), (L - 0.5, c + 4.4)]
        car.poly(INK, [(l, o * 1.15) for l, o in tail])
        car.poly(jade, tail)
        for i in range(4):  # flame tuft at the end of the tail
            a = -0.8 + i * 0.55
            tip = (L + 14 + 4 * math.cos(a), c - 1.5 + wag + 4 * math.sin(a))
            car.poly(mane, [(L + 12.5, c - 2.4 + wag), tip, (L + 12.5, c - 0.6 + wag)])


def _fire_dragon(car, front, rear, stripe, t, index) -> None:
    """IR: a heavy western dragon, crimson and black, with armour plates, a bat wing,
    curled horns, a spade-tipped tail and a big breath of fire."""
    L = car.length
    red, red_dark, red_light = (176, 30, 36), (96, 12, 22), (226, 70, 60)
    belly, belly_dark, horn = (226, 170, 104), (170, 116, 64), (236, 224, 196)
    plate = (54, 18, 26)
    flap = math.sin(t * 2.2)
    if index == 1:  # the wing, over the middle carriage
        root, elbow = (L * 0.25, -6), (L * 0.45, -19 - 2.5 * flap)
        fingers = [(L * 0.05, -12 - flap), (L * 0.4, -10 - flap), (L * 0.8, -14 - 1.5 * flap), (L + 4, -10 - flap)]
        membrane = [root, elbow, (L + 6, -16 - 2.5 * flap), (L + 4, -10 - flap), (L * 0.8, -8.5), (L * 0.4, -7), (L * 0.05, -8)]
        car.poly(INK, [(l, o - 0.8) for l, o in membrane])
        car.poly((120, 20, 30), membrane)
        car.poly(red_light, [elbow, (L + 6, -16 - 2.5 * flap), (L + 4, -13.5 - flap)])
        car.line(INK, *root, *elbow, 1.2)
        car.line(horn, *root, *elbow, 0.6)
        for f in fingers:
            car.line(red_dark, *elbow, *f, 0.6)
        car.poly(horn, [elbow, (elbow[0] - 1.2, elbow[1] - 2), (elbow[0] + 0.6, elbow[1] + 0.2)])  # claw
    # Back plates.
    x = 1.5
    while x < L - 1:
        car.poly(INK, [(x - 2.2, -5.6), (x + 0.4, -10), (x + 2.2, -5.6)])
        car.poly(plate, [(x - 1.6, -5.8), (x + 0.3, -9), (x + 1.6, -5.8)])
        x += 4.2
    car.band(-7.5, 7.5, -0.5, L + 0.5, INK)
    car.band(-6, 6, 0, L, red)
    car.band(-6, -4.4, 0, L, red_dark)
    # Scales: a lattice of diamonds with a lit upper edge.
    for row, o in enumerate((-3.6, -1.2)):
        x = 0.5 + row * 1.6
        while x < L - 2.5:
            car.poly(red_dark, [(x, o + 1.1), (x + 1.6, o), (x + 3.2, o + 1.1), (x + 1.6, o + 2.2)])
            car.line(red_light, x, o + 1.1, x + 1.6, o, 0.4)
            x += 3.2
    car.band(2.0, 6, 0, L, belly)
    for xx in range(1, int(L), 2):
        car.line(belly_dark, xx, 2.0, xx, 6, 0.4)
    car.band(5.2, 6.8, 0.5, L - 0.5, stripe)
    if index == 0:  # front legs with black talons
        for lx in (L * 0.35, L * 0.7):
            car.poly(INK, [(lx - 2.2, 4), (lx + 2.2, 4), (lx + 1.6, 8.6), (lx - 2.6, 8.6)])
            car.poly(red_dark, [(lx - 1.6, 4), (lx + 1.6, 4), (lx + 1, 8), (lx - 2, 8)])
            for dx in (-2.4, -1.2, 0):
                car.poly(horn, [(lx + dx, 8), (lx + dx - 0.8, 9.6), (lx + dx + 0.4, 8)])
    if front:
        jaw_open = 1.0 + 0.8 * (0.5 + 0.5 * math.sin(t * 5))
        head = [(1, -6.2), (-3, -7), (-8, -5.5), (-12, -3), (-13.5, -0.5), (-13, 0.6), (-6, 1.2)]
        jaw = [(-6, 1.6), (-12.5, 1.6 + jaw_open), (-11.5, 3.6 + jaw_open), (-4, 5.6), (1, 6.2), (1, 1)]
        car.poly(INK, [(l * 1.06 - 0.3, o * 1.12) for l, o in head + [(1, 1.5)]])
        car.poly(INK, [(l * 1.06 - 0.3, o * 1.1) for l, o in jaw])
        car.poly(red, head + [(1, 1.5)])
        car.poly(belly, jaw)
        car.poly((60, 10, 14), [(-6, 1.2), (-13, 0.6), (-12.5, 1.6 + jaw_open), (-6, 1.6)])  # mouth
        for x in (-12, -10.4, -8.8):  # teeth
            car.poly((255, 255, 240), [(x, 0.6), (x + 0.5, 1.8), (x + 1, 0.7)])
        car.poly(red_dark, [(-3, -7), (-8, -5.5), (-5, -4.5)])  # brow
        # Two horns curling back over the head.
        for base, mid, tip in (((-4, -6.6), (0, -11), (5, -11.5)), ((-6.5, -5.8), (-4, -10), (0.5, -12.5))):
            car.line(INK, *base, *mid, 1.6)
            car.line(INK, *mid, *tip, 1.2)
            car.line(horn, *base, *mid, 1.0)
            car.line(horn, *mid, *tip, 0.6)
        car.dot(INK, -7.2, -3.4, 1.3)
        car.dot((255, 170, 30), -7.2, -3.4, 0.95)
        car.line(INK, -7.2, -4.2, -7.2, -2.6, 0.35)  # slit pupil
        car.dot(INK, -12.6, -1.6, 0.5)
        # Fire: three layers, flickering.
        f = 0.6 + 0.4 * math.sin(t * 11) * math.sin(t * 7.3)
        reach = 10 + 6 * f
        base_o = 1.6 + jaw_open / 2
        car.poly((200, 40, 20), [(-13, base_o - 1.6), (-13 - reach, base_o - 4 * f), (-14 - reach * 1.15, base_o + 0.5), (-13 - reach, base_o + 4 * f), (-13, base_o + 1.6)])
        car.poly((255, 140, 30), [(-13, base_o - 1), (-13 - reach * 0.8, base_o - 2.4 * f), (-13.5 - reach * 0.95, base_o + 0.3), (-13 - reach * 0.8, base_o + 2.4 * f), (-13, base_o + 1)])
        car.poly((255, 240, 150), [(-13, base_o - 0.5), (-13 - reach * 0.5, base_o), (-13, base_o + 0.6)])
        for i in range(3):  # sparks
            s = (t * 3 + i * 0.33) % 1.0
            car.dot((255, 200, 80), -13 - reach * (0.6 + 0.6 * s), base_o + (i - 1) * 3 * s, 0.5 * (1 - s) + 0.2)
    if rear:
        wag = 2.5 * math.sin(t * 2.6 + index)
        tail = [(L - 0.5, -5), (L + 6, -3 + wag * 0.4), (L + 12, -1 + wag), (L + 12, 1.4 + wag), (L + 6, 3 + wag * 0.4), (L - 0.5, 5)]
        car.poly(INK, [(l, o * 1.2) for l, o in tail])
        car.poly(red, tail)
        car.poly(belly, [(L - 0.5, 2), (L + 6, 1.6 + wag * 0.4), (L + 12, 1 + wag), (L + 12, 1.4 + wag), (L + 6, 3 + wag * 0.4), (L - 0.5, 5)])
        for x in (L + 2, L + 6):
            car.poly(plate, [(x - 1.2, -3.2 + wag * (x - L) / 15), (x, -6 + wag * (x - L) / 15), (x + 1.2, -2.8 + wag * (x - L) / 15)])
        spade = [(L + 11, 0.2 + wag), (L + 13.5, -3.5 + wag), (L + 18.5, 0.2 + wag), (L + 13.5, 3.9 + wag)]
        car.poly(INK, [(l + (0.6 if l > L + 15 else 0), o * 1.1 - 0.1 * wag) for l, o in spade])
        car.poly(plate, spade)
        car.poly(red_dark, [(L + 12.5, 0.2 + wag), (L + 13.5, -2 + wag), (L + 16.5, 0.2 + wag)])


# ---------------------------------------------------------------------- precious stones


def _facet_colour(palette, seed: int, light: float):
    """One of the palette's tones, picked by seed, brightened by light (0..1)."""
    base = palette[(seed * 7 + seed // 3) % len(palette)]
    return _lerp_colour(base, (255, 255, 255), max(0.0, min(1.0, light)))


def _gem(car, front, rear, stripe, t, index, palette, metal, metal_dark, studs) -> None:
    """A carriage cut like a gemstone: rows of facets in many tones, set in a metal frame with
    small stones along it. A band of light sweeps along the train and sparkles come and go."""
    L = car.length
    car.band(-7.5, 7.5, -0.5, L + 0.5, INK)
    car.band(-6, 6, 0, L, palette[2])
    sweep = ((t * 0.45 + index * 0.18) % 1.6 - 0.3) * L  # where the band of light is now

    def light(l, o):
        d = abs((l + o * 0.6) - sweep)
        return max(0.0, 0.75 - d / 5.0) + (0.12 if o < -1 else 0.0)

    # Facets: each segment is a brilliant cut seen from the side (crown on top, pavilion below).
    seg = 5.5
    n = max(1, round((L - 1) / seg))
    seg = (L - 1) / n
    for i in range(n):
        x0 = 0.5 + i * seg
        x1, m = x0 + seg, x0 + seg / 2
        table, girdle = -2.6, 0.4
        crown = [
            [(x0, -5.2), (m, -5.2), (m - seg * 0.18, table)],
            [(m, -5.2), (x1, -5.2), (m + seg * 0.18, table)],
            [(x0, -5.2), (m - seg * 0.18, table), (x0, girdle)],
            [(x1, -5.2), (m + seg * 0.18, table), (x1, girdle)],
            [(m - seg * 0.18, table), (m + seg * 0.18, table), (m, -5.2)],
            [(x0, girdle), (m - seg * 0.18, table), (m + seg * 0.18, table), (x1, girdle)],
        ]
        pavilion = [
            [(x0, girdle), (m, girdle), (m, 4.2)],
            [(m, girdle), (x1, girdle), (m, 4.2)],
            [(x0, girdle), (m, 4.2), (x0, 4.2)],
            [(x1, girdle), (x1, 4.2), (m, 4.2)],
        ]
        for j, tri in enumerate(crown + pavilion):
            cl = sum(p[0] for p in tri) / len(tri)
            co = sum(p[1] for p in tri) / len(tri)
            shade = (0.35 if j < 2 else 0.18) if j < len(crown) else -0.05
            colour = _facet_colour(palette, i * 11 + j + index * 5, light(cl, co) + max(0.0, shade) * 0.6)
            if shade < 0:
                colour = _shade(colour, 0.82)
            car.poly(colour, tri)
        car.line(_lerp_colour(palette[0], (255, 255, 255), 0.6), x0, girdle, x1, girdle, 0.3)
        car.line(_lerp_colour(palette[0], (255, 255, 255), 0.5), m - seg * 0.18, table, m + seg * 0.18, table, 0.3)
    # Metal setting: rails top and bottom, prongs, and a small stone in each prong.
    car.band(-6, -5.0, 0, L, metal)
    car.band(4.2, 5.2, 0, L, metal)
    car.line(metal_dark, 0, -5.0, L, -5.0, 0.3)
    car.line(metal_dark, 0, 5.2, L, 5.2, 0.3)
    for i in range(n + 1):
        x = 0.5 + i * seg
        car.poly(metal, [(x - 0.9, -5.0), (x, -3.9), (x + 0.9, -5.0)])
        car.poly(metal, [(x - 0.9, 4.2), (x, 3.2), (x + 0.9, 4.2)])
        stud = studs[(i + index) % len(studs)]
        car.dot(metal_dark, x, 4.7, 0.9)
        car.dot(stud, x, 4.7, 0.65)
        car.dot((255, 255, 255), x - 0.2, 4.5, 0.2)
    if front:
        car.poly(INK, [(0.5, -7.5), (-5, -2), (-5, 2), (0.5, 7.5)])
        car.poly(metal, [(0, -6), (-4, -1.6), (-4, 1.6), (0, 6)])
        car.poly(_facet_colour(palette, 1, 0.5), [(0, -4.8), (-3, -1.2), (0, -0.2)])
        car.poly(_facet_colour(palette, 3, 0.1), [(0, -0.2), (-3, -1.2), (-3, 1.2), (0, 4.4)])
        car.dot((255, 255, 255), -3.6, 2.6, 0.9)
    if rear:
        car.poly(INK, [(L - 0.5, -7.5), (L + 5, -2), (L + 5, 2), (L - 0.5, 7.5)])
        car.poly(metal, [(L, -6), (L + 4, -1.6), (L + 4, 1.6), (L, 6)])
        car.poly(_facet_colour(palette, 2, 0.3), [(L, -4.8), (L + 3, -1.2), (L, -0.2)])
        car.poly(_facet_colour(palette, 4, 0.0), [(L, -0.2), (L + 3, -1.2), (L + 3, 1.2), (L, 4.4)])
        car.dot((255, 70, 70), L + 3.6, 2.6, 0.8)
    car.band(5.4, 6.8, 0.5, L - 0.5, stripe)
    # Sparkles: four-pointed stars, some with a touch of rainbow fire.
    fire = [(255, 255, 255), (255, 240, 170), (190, 230, 255), (255, 200, 240)]
    for i in range(4):
        s = math.sin(t * 3.3 + i * 1.9 + index * 2.3)
        if s > 0.5:
            r = (s - 0.5) * 6
            cx = ((i * 0.27 + index * 0.13) % 0.9 + 0.05) * L
            co = (-3.8, -1.2, 2.4, -2.8)[i]
            colour = fire[(i + index) % len(fire)]
            car.line(colour, cx - r, co, cx + r, co, 0.45)
            car.line(colour, cx, co - r, cx, co + r, 0.45)
            car.line(colour, cx - r * 0.4, co - r * 0.4, cx + r * 0.4, co + r * 0.4, 0.3)
            car.line(colour, cx - r * 0.4, co + r * 0.4, cx + r * 0.4, co - r * 0.4, 0.3)


def _gem_r(car, front, rear, stripe, t, index) -> None:
    # Diamond: icy blue-white facets in platinum, with small sapphires.
    palette = [(246, 252, 255), (190, 226, 250), (120, 180, 230), (70, 130, 200), (160, 210, 245), (40, 90, 170)]
    _gem(car, front, rear, stripe, t, index, palette, (214, 220, 230), (130, 140, 156), [(60, 110, 230), (240, 250, 255)])


def _gem_ir(car, front, rear, stripe, t, index) -> None:
    # Ruby: deep reds in gold, with small emeralds and diamonds.
    palette = [(255, 110, 130), (220, 30, 64), (176, 10, 44), (120, 4, 34), (244, 64, 90), (84, 0, 24)]
    _gem(car, front, rear, stripe, t, index, palette, (236, 196, 90), (160, 120, 40), [(40, 190, 110), (240, 250, 255)])


# ---------------------------------------------------------------------- freight (M) and historic (H)


def _vintage_m(car, front, rear, stripe, t, index) -> None:
    """M: a green steam engine pulling wooden box wagons and open coal wagons."""
    L = car.length
    if index == 0:
        _steam_loco(car, stripe, t, boiler=(30, 72, 50), cab=(36, 84, 58), trim=(214, 178, 80), wheel=(170, 40, 36))
        return
    if index % 2:
        # A wooden box wagon with a sliding door.
        wood, dark = (134, 62, 42), (96, 42, 28)
        _base(car, wood, (84, 76, 70), stripe)
        for x in range(2, int(L) - 1, 3):
            car.line(dark, x, -4, x, 5, 0.45)
        d0, d1 = L * 0.35, L * 0.65
        car.band(-3.8, 4.6, d0, d1, dark)
        car.line(wood, d0, -3.8, d1, 4.6, 0.5)
        car.line(wood, d0, 4.6, d1, -3.8, 0.5)
        car.line((40, 36, 34), d0 - 1, -4.4, d1 + 1, -4.4, 0.6)  # door rail
    else:
        # An open wagon heaped with coal.
        car.poly(INK, [(-0.5, -2.5), (-0.5, 7.5), (L + 0.5, 7.5), (L + 0.5, -2.5)])
        for i in range(6):
            x = (i + 0.5) * L / 6
            car.dot(INK, x, -2.6 - (i % 2) * 0.8, 2.6)
        car.band(-1.5, 6, 0, L, (90, 84, 78))
        for i in range(6):
            x = (i + 0.5) * L / 6
            car.dot((44, 44, 48), x, -2.6 - (i % 2) * 0.8, 2.0)
            car.dot((90, 90, 100), x - 0.6, -3.4 - (i % 2) * 0.8, 0.5)  # a shiny lump
        for x in range(3, int(L) - 1, 4):
            car.line((64, 60, 56), x, -1.5, x, 5, 0.45)
        car.band(5.2, 6.8, 0.5, L - 0.5, stripe)
    for x in (3.5, L - 3.5):
        car.dot((40, 40, 44), x, 6.2, 1.4)
    if rear:
        car.dot((230, 60, 50), L - 1.2, 3.8, 0.8)


def _electric_loco(car, stripe, t, body, lower, accent, pantograph=True) -> None:
    """A modern locomotive with a sloped nose, a dark windscreen and a warning-yellow chin."""
    L = car.length
    car.band(-7.5, 7.5, -0.5, L + 0.5, INK)
    car.poly(INK, [(0.5, -7.5), (-3.8, -2), (-3.8, 7.5), (0.5, 7.5)])
    car.band(-6, 6, 0, L, body)
    car.poly(body, [(0, -6), (-3, -1.6), (-3, 6), (0, 6)])
    car.band(1.5, 6, -3, L, lower)
    car.poly((24, 32, 46), [(0, -5), (-2.4, -1.8), (2.5, -1.8), (2.5, -5)])  # windscreen
    car.line((110, 140, 180), 0.6, -4.6, 2, -2.4, 0.4)
    car.band(4.2, 6, -3, 1.5, (250, 204, 40))
    car.band(-0.6, 0.6, 4, L - 1, accent)
    for x in range(7, int(L) - 3, 3):
        car.band(-4.2, -2.2, x, x + 1.6, _shade(body, 0.75))  # grilles
    car.dot((255, 240, 190), -2.9, 2.6, 0.8)
    car.band(5.2, 6.8, 0.5, L - 0.5, stripe)
    if pantograph:
        _pantograph(car, L * 0.6, t)


def _modern_m(car, front, rear, stripe, t, index) -> None:
    """M: a red electric locomotive pulling tank wagons and car carriers."""
    L = car.length
    if index == 0:
        _electric_loco(car, stripe, t, (196, 36, 40), (200, 206, 214), (255, 255, 255))
        return
    car.band(3.4, 6.8, -0.5, L + 0.5, INK)
    car.band(4, 5.4, 0, L, (60, 62, 68))
    car.band(5.4, 6.8, 0.5, L - 0.5, stripe)
    if index % 2:
        # A silver tank wagon.
        silver, dark = (196, 202, 210), (130, 136, 146)
        car.poly(INK, [(1, -5.2), (L - 1, -5.2), (L + 0.6, -1), (L - 1, 4.4), (1, 4.4), (-0.6, -1)])
        car.poly(silver, [(1.5, -4.4), (L - 1.5, -4.4), (L - 0.2, -1), (L - 1.5, 3.8), (1.5, 3.8), (0.2, -1)])
        car.line((240, 244, 250), 2, -3.2, L - 2, -3.2, 0.6)  # shine
        car.line(dark, 2, 2.2, L - 2, 2.2, 0.5)
        car.band(-6.4, -4.4, L / 2 - 1.5, L / 2 + 1.5, dark)  # filler dome
        car.band(-1.6, 0.4, L * 0.3, L * 0.7, (240, 140, 40))  # hazard panel
    else:
        # A car carrier: two decks of brand new cars in different colours.
        frame = (90, 96, 106)
        car.band(-7, -6.2, 0.5, L - 0.5, frame)
        car.band(-1.2, -0.4, 0.5, L - 0.5, frame)
        for x in (0.8, L / 2, L - 1.6):
            car.band(-7, 4, x, x + 0.8, frame)
        colours = [(230, 230, 236), (40, 90, 200), (210, 40, 40), (30, 30, 34), (240, 190, 40), (120, 124, 132)]
        for deck, o in enumerate((-1.4, 3.8)):
            for j in range(2):
                x = 2 + j * (L - 4) / 2
                w = (L - 4) / 2 - 1.2
                c = colours[(index * 3 + deck * 2 + j) % len(colours)]
                car.poly(INK, [(x - 0.3, o + 0.3), (x - 0.3, o - 2.3), (x + w * 0.25, o - 2.3), (x + w * 0.4, o - 4.3),
                               (x + w * 0.8, o - 4.3), (x + w + 0.3, o - 2.3), (x + w + 0.3, o + 0.3)])
                car.poly(c, [(x, o), (x, o - 2), (x + w * 0.28, o - 2), (x + w * 0.42, o - 4), (x + w * 0.78, o - 4), (x + w, o - 2), (x + w, o)])
                car.poly((60, 80, 110), [(x + w * 0.36, o - 2.2), (x + w * 0.46, o - 3.6), (x + w * 0.74, o - 3.6), (x + w * 0.84, o - 2.2)])
    if rear:
        car.dot((230, 60, 50), L - 1, 4.6, 0.8)


def _future_m(car, front, rear, stripe, t, index) -> None:
    """M: a maglev engine pushing glowing cargo pods that float over the track."""
    neon, accent = (70, 255, 150), (210, 255, 110)
    if index == 0:
        _future(car, front, False, stripe, t, index, neon, accent, False)
        return
    L = car.length
    pulse = 0.55 + 0.45 * math.sin(t * 4 + index * 0.8)
    glow = _lerp_colour(_shade(neon, 0.45), neon, pulse)
    for i, o in enumerate((8.6, 7.8)):
        car.band(o - 0.35, o + 0.35, 1 + i, L - 1 - i, _shade(neon, 0.35 + 0.3 * i * pulse))
    car.band(3.4, 6.6, -0.3, L + 0.3, INK)
    car.band(4, 6, 0, L, (18, 22, 32))  # the spine that holds the pod
    car.band(5.4, 6.4, 0.5, L - 0.5, stripe)
    # A hexagonal pod, bobbing gently.
    bob = 0.5 * math.sin(t * 2.5 + index)
    hexagon = [(1, -1 + bob), (2.6, -6 + bob), (L - 2.6, -6 + bob), (L - 1, -1 + bob), (L - 2.6, 3.6 + bob), (2.6, 3.6 + bob)]
    car.poly(INK, [(l + (0.6 if l > L / 2 else -0.6), o * 1.12) for l, o in hexagon])
    car.poly((26, 32, 46), hexagon)
    car.poly((44, 54, 76), hexagon[:4])
    for p0, p1 in zip(hexagon, hexagon[1:] + hexagon[:1]):
        car.line(glow, *p0, *p1, 0.45)
    # The cargo core, glowing, and a scan line passing over it.
    core = _lerp_colour(_shade(accent, 0.5), accent, 0.5 + 0.5 * math.sin(t * 3 + index * 1.7))
    car.band(-3.6 + bob, 1.4 + bob, L * 0.3, L * 0.7, _shade(neon, 0.25))
    car.dot(core, L * 0.5, -1.1 + bob, 1.8)
    car.dot((240, 255, 240), L * 0.5 - 0.5, -1.6 + bob, 0.6)
    scan = L * 0.3 + (t * 6 + index * 3) % (L * 0.4)
    car.line(accent, scan, -3.6 + bob, scan, 1.4 + bob, 0.35)
    if rear:
        car.poly(INK, [(L, 3.4), (L + 4.5, 4.6), (L + 4.5, 6.4), (L, 6.6)])
        car.poly((18, 22, 32), [(L, 4), (L + 3.8, 5), (L + 3.8, 6), (L, 6)])
        car.line((255, 50, 90), L + 3.6, 5, L + 3.6, 6, 0.8)


def _ice_dragon(car, front, rear, stripe, t, index) -> None:
    """M: a long frost serpent with crystal spikes along its back, a crown of icicles and a
    freezing breath. Six carriages make it the longest beast on the rails."""
    L = car.length
    ice, ice_dark, ice_light = (126, 186, 230), (52, 96, 156), (214, 240, 255)
    belly, crystal = (232, 244, 255), (170, 230, 255)

    def centre(l):  # the waves travel smoothly from one carriage to the next
        return 0.3 + 1.2 * math.sin((l + index * (L + 3)) / 6.5 - t * 2.2)

    steps = [i * L / 16 for i in range(17)]
    top = [(l, centre(l) - 4.4) for l in steps]
    bottom = [(l, centre(l) + 4.4) for l in steps]
    # Crystal spikes along the back, catching the light.
    for i, l in enumerate(steps[2:-1:3]):
        h = 4.2 + (i % 2) * 1.8
        c = centre(l) - 4.2
        car.poly(INK, [(l - 1.9, c + 0.6), (l, c - h - 0.9), (l + 1.9, c + 0.6)])
        car.poly(crystal, [(l - 1.3, c + 0.4), (l, c - h), (l + 1.3, c + 0.4)])
        shine = 0.5 + 0.5 * math.sin(t * 3 + l * 0.4 + index)
        car.poly(_lerp_colour(crystal, (255, 255, 255), shine), [(l - 0.4, c + 0.2), (l, c - h * 0.9), (l + 0.2, c + 0.2)])
    car.poly(INK, [(l, o - 1) for l, o in top] + [(l, o + 1) for l, o in reversed(bottom)])
    car.poly(ice, top + list(reversed(bottom)))
    car.poly(ice_light, top + [(l, o + 1.4) for l, o in reversed(top)])
    car.poly(belly, [(l, centre(l) + 1.8) for l in steps] + list(reversed(bottom)))
    for l in steps[1:-1]:
        car.line(ice, l, centre(l) + 2.0, l, centre(l) + 4.2, 0.35)
    # Scales: small diamonds in a lattice.
    for row, off in enumerate((-2.6, -0.2)):
        x = 0.8 + row * 1.4
        while x < L - 2:
            c = centre(x + 1.4) + off
            car.poly(ice_dark, [(x, c), (x + 1.4, c - 0.9), (x + 2.8, c), (x + 1.4, c + 0.9)])
            x += 2.8
    car.band(5.8, 7.0, 0.5, L - 0.5, stripe)
    # Snowflakes drifting off its body.
    for i in range(3):
        f = (t * 0.5 + i / 3 + index * 0.21) % 1.0
        x = (i * 0.33 + 0.15) * L + f * 6
        o = -7 - f * 8
        r = 0.9 * (1 - f) + 0.3
        car.line((235, 248, 255), x - r, o, x + r, o, 0.3)
        car.line((235, 248, 255), x, o - r, x, o + r, 0.3)
    if front:
        c = centre(0)
        jaw = 0.8 + 0.6 * (0.5 + 0.5 * math.sin(t * 3))
        # A crown of icicles swept back over the head.
        for base, tip in (((-3, c - 4.5), (3, c - 12)), ((-5.5, c - 4), (-2, c - 11)), ((-7.5, c - 3.2), (-6, c - 8.5))):
            car.poly(INK, [(base[0] - 1.3, base[1] + 0.4), tip, (base[0] + 1.3, base[1] + 0.4)])
            car.poly(crystal, [(base[0] - 0.8, base[1]), (tip[0] - 0.3, tip[1] + 0.8), (base[0] + 0.8, base[1])])
        head = [(1, c - 4.4), (-4, c - 5), (-9, c - 3.6), (-13, c - 1.2), (-13.5, c + 0.4), (-6, c + 0.8)]
        lower = [(-6, c + 1.2), (-13, c + 1 + jaw), (-11, c + 3 + jaw), (-4, c + 4.6), (1, c + 4.4)]
        car.poly(INK, [(l * 1.06 - 0.3, o * 1.1) for l, o in head + [(1, c + 1)]])
        car.poly(INK, [(l * 1.06 - 0.3, o * 1.1) for l, o in lower + [(1, c + 1)]])
        car.poly(ice, head + [(1, c + 1)])
        car.poly(ice_light, [(1, c - 4.4), (-4, c - 5), (-9, c - 3.6), (-5, c - 2.6)])
        car.poly(belly, lower + [(1, c + 1)])
        car.poly((30, 50, 90), [(-6, c + 0.8), (-13.5, c + 0.4), (-13, c + 1 + jaw), (-6, c + 1.2)])
        for x in (-12.4, -10.8, -9.2):
            car.poly((255, 255, 255), [(x, c + 0.5), (x + 0.4, c + 1.6), (x + 0.8, c + 0.6)])
        # A glowing cyan eye.
        eye = 0.6 + 0.4 * math.sin(t * 5)
        car.dot(INK, -7.4, c - 2.2, 1.3)
        car.dot(_lerp_colour((40, 160, 220), (160, 255, 255), eye), -7.4, c - 2.2, 1.0)
        car.dot((255, 255, 255), -7.7, c - 2.5, 0.35)
        # Freezing breath: a pale cone with snowflakes tumbling in it.
        f = 0.6 + 0.4 * math.sin(t * 6) * math.sin(t * 3.7)
        reach = 9 + 5 * f
        b = c + 1 + jaw / 2
        car.poly((150, 210, 245), [(-13, b - 1.4), (-13 - reach, b - 3.6 * f - 1), (-14 - reach * 1.1, b), (-13 - reach, b + 3.6 * f + 1), (-13, b + 1.4)])
        car.poly((225, 245, 255), [(-13, b - 0.8), (-13 - reach * 0.75, b - 1.8 * f), (-13 - reach * 0.85, b), (-13 - reach * 0.75, b + 1.8 * f), (-13, b + 0.8)])
        for i in range(3):
            s = (t * 2.5 + i * 0.33) % 1.0
            x, o = -14 - reach * (0.4 + 0.7 * s), b + (i - 1) * 3.2 * s
            r = 0.9 * (1 - s) + 0.3
            car.line((255, 255, 255), x - r, o, x + r, o, 0.35)
            car.line((255, 255, 255), x, o - r, x, o + r, 0.35)
    if rear:
        c = centre(L)
        wag = 1.6 * math.sin(t * 2.8)
        tail = [(L - 0.5, c - 4.2), (L + 6, c - 2 + wag * 0.5), (L + 12, c - 0.4 + wag), (L + 12, c + 0.8 + wag),
                (L + 6, c + 2.4 + wag * 0.5), (L - 0.5, c + 4.2)]
        car.poly(INK, [(l, o * 1.15) for l, o in tail])
        car.poly(ice, tail)
        tip = [(L + 11.5, c + 0.2 + wag), (L + 14, c - 3.2 + wag), (L + 18, c + 0.2 + wag), (L + 14, c + 3.6 + wag)]
        car.poly(INK, [(l + (0.6 if l > L + 15 else 0), o) for l, o in tip])
        car.poly(crystal, tip)
        car.poly((255, 255, 255), [(L + 13, c + 0.2 + wag), (L + 14, c - 2 + wag), (L + 15.5, c + 0.2 + wag)])


def _gem_m(car, front, rear, stripe, t, index) -> None:
    # Emerald: deep greens in gold, with small rubies and diamonds.
    palette = [(150, 250, 180), (40, 200, 110), (16, 150, 80), (8, 100, 56), (80, 224, 140), (4, 70, 40)]
    _gem(car, front, rear, stripe, t, index, palette, (236, 196, 90), (160, 120, 40), [(220, 30, 60), (240, 250, 255)])


def _vintage_h(car, front, rear, stripe, t, index) -> None:
    """H: the royal train: a green engine lined in gold and maroon saloons with cream window
    panels, a raised roof and the royal crest."""
    L = car.length
    gold = (226, 186, 80)
    if index == 0:
        _steam_loco(car, stripe, t, boiler=(26, 76, 54), cab=(32, 88, 62), trim=gold, wheel=(150, 30, 34))
        car.dot(gold, 10, -1.2, 0.8)
        return
    maroon = (112, 24, 38)
    car.band(-8.6, -6.4, 3, L - 3, INK)  # the raised clerestory roof
    car.band(-8, -6, 3.5, L - 3.5, (70, 50, 40))
    _base(car, maroon, (70, 50, 40), stripe)
    car.band(-3.8, 0.2, 0.8, L - 0.8, (236, 222, 184))  # cream window panel
    _windows(car, False, False, (50, 40, 50), o0=-3.2, o1=-0.4, step=3.6, size=2.4, start=2, end=L - 2)
    pos = 2.0
    while pos + 2.4 <= L - 2:  # curtains tied back
        car.band(-3.2, -0.4, pos, pos + 0.5, (180, 40, 50))
        car.band(-3.2, -0.4, pos + 1.9, pos + 2.4, (180, 40, 50))
        pos += 3.6
    car.line(gold, 0.6, -4.0, L - 0.6, -4.0, 0.4)
    car.line(gold, 0.6, 0.4, L - 0.6, 0.4, 0.4)
    car.line(gold, 0.6, 4.6, L - 0.6, 4.6, 0.4)
    # The crest: a gold shield with a little crown.
    m = L / 2
    car.poly(INK, [(m - 1.8, 1.0), (m + 1.8, 1.0), (m + 1.8, 2.8), (m, 4.6), (m - 1.8, 2.8)])
    car.poly(gold, [(m - 1.3, 1.3), (m + 1.3, 1.3), (m + 1.3, 2.7), (m, 4.1), (m - 1.3, 2.7)])
    car.dot((30, 60, 160), m, 2.4, 0.6)
    if rear:
        car.dot((230, 60, 50), L - 1.2, 3.8, 0.8)


def _modern_h(car, front, rear, stripe, t, index) -> None:
    """H: a panoramic tourist train for the Douro valley: glass all the way up into the roof,
    so the passengers can see the vineyards, and a navy diesel at the front."""
    L = car.length
    if index == 0:
        _electric_loco(car, stripe, t, (28, 48, 92), (210, 216, 224), (230, 180, 60), pantograph=False)
        heat = (t * 2) % 1.0  # a shimmer of exhaust from the diesel
        car.dot(_shade((150, 150, 160), 1 - 0.4 * heat), L * 0.55 + heat * 4, -7.5 - heat * 4, 0.8 + heat * 1.4)
        return
    navy, white = (28, 48, 92), (236, 238, 242)
    car.band(-7.5, 7.5, -0.5, L + 0.5, INK)
    car.poly(INK, [(1, -7.5), (L - 1, -7.5), (L + 0.5, -6), (-0.5, -6)])
    car.band(-6, 6, 0, L, white)
    # The glass: up the side and curving over the roof.
    glass, roof_glass = (40, 70, 110), (90, 130, 170)
    car.poly(roof_glass, [(1.5, -4.2), (2.5, -6.8), (L - 2.5, -6.8), (L - 1.5, -4.2)])
    car.band(-4.2, 1.6, 1.5, L - 1.5, glass)
    for x in range(int(L * 0.25), int(L), int(L * 0.25)):
        car.line(white, x, -6.8, x, 1.6, 0.5)  # window frames
    # Passengers looking out.
    for j in range(5):
        x = 3 + j * (L - 6) / 4
        if (j + index) % 3 != 2:
            car.dot((30, 34, 44), x, -0.6, 1.1)
            car.band(0.3, 1.6, x - 1.2, x + 1.2, (30, 34, 44))
    # A reflection gliding over the glass.
    shine = ((t * 10 + index * 9) % (L + 8)) - 4
    if 1.5 < shine < L - 3:
        car.poly((150, 190, 225), [(shine, -6.6), (shine + 1.4, -6.6), (shine + 0.4, 1.4), (shine - 1, 1.4)])
    car.band(2.4, 3.6, 0, L, navy)
    car.band(3.6, 4.2, 0, L, (230, 180, 60))
    car.band(5.2, 6.8, 0.5, L - 0.5, stripe)
    if rear:
        car.dot((230, 60, 50), L - 1.2, 4.6, 0.8)


def _future_h(car, front, rear, stripe, t, index) -> None:
    _future(car, front, rear, stripe, t, index, (255, 140, 40), (255, 226, 120), True)


def _iron_dragon(car, front, rear, stripe, t, index) -> None:
    """H: a steam-powered mechanical dragon in riveted bronze and iron, with turning gears,
    pistons driving its wheels, a furnace for a heart and clouds of steam for breath."""
    L = car.length
    bronze, bronze_dark, bronze_light = (176, 120, 56), (110, 70, 34), (226, 172, 96)
    iron, iron_light, furnace = (64, 66, 72), (110, 114, 124), (255, 120, 30)
    flicker = 0.6 + 0.4 * math.sin(t * 9) * math.sin(t * 5.3)
    # Spiked iron plates along the back.
    x = 2.0
    while x < L - 1:
        car.poly(INK, [(x - 2, -5.6), (x + 0.6, -9.6), (x + 2, -5.6)])
        car.poly(iron, [(x - 1.4, -5.8), (x + 0.5, -8.7), (x + 1.4, -5.8)])
        x += 4.5
    car.band(-7.5, 7.5, -0.5, L + 0.5, INK)
    car.band(-6, 6, 0, L, bronze)
    car.band(-6, -4.6, 0, L, bronze_light)
    # Riveted panels.
    n = max(2, round(L / 7))
    for i in range(n + 1):
        px = i * L / n
        car.line(bronze_dark, px, -6, px, 3, 0.5)
        for o in (-5.2, -1.5, 2.2):
            if 0.6 < px < L - 0.6:
                car.dot(bronze_dark, px - 0.9, o, 0.35)
                car.dot(bronze_dark, px + 0.9, o, 0.35)
    car.band(3, 6, 0, L, iron)
    # A big gear in the middle, turning.
    gx, go = L / 2, -1.2
    angle = t * 2 + index
    for i in range(8):
        a = angle + i * math.pi / 4
        car.line(INK, gx + 2.4 * math.cos(a), go + 2.4 * math.sin(a), gx + 3.6 * math.cos(a), go + 3.6 * math.sin(a), 1.4)
        car.line(iron_light, gx + 2.4 * math.cos(a), go + 2.4 * math.sin(a), gx + 3.4 * math.cos(a), go + 3.4 * math.sin(a), 0.8)
    car.dot(INK, gx, go, 3.0)
    car.dot(iron_light, gx, go, 2.5)
    car.dot(bronze_dark, gx, go, 1.0)
    if index == 0:
        # The furnace glowing through a grate in its chest.
        car.band(-2.5, 1.5, L * 0.12, L * 0.3, _lerp_colour((120, 30, 10), furnace, flicker))
        for gx2 in range(int(L * 0.12) + 1, int(L * 0.3), 1):
            car.line(INK, gx2, -2.5, gx2, 1.5, 0.3)
    # Wheels with pistons pushing them round.
    for wx in (L * 0.25, L * 0.75):
        a = t * 6 + index
        car.dot(INK, wx, 5.4, 2.6)
        car.dot((150, 40, 30), wx, 5.4, 2.1)
        car.dot(iron_light, wx, 5.4, 0.7)
        cx, co = wx + 1.5 * math.cos(a), 5.4 + 1.5 * math.sin(a)
        car.line(INK, cx, co, wx - 5, 2.6, 1.0)
        car.line(iron_light, cx, co, wx - 5, 2.6, 0.5)
    car.band(5.6, 6.8, 0.5, L - 0.5, stripe)
    # Puffs of steam from a vent on the back.
    phase = (t * 1.3 + index * 0.37) % 1.0
    for i in range(2):
        f = (phase + i / 2) % 1.0
        car.dot(_shade((220, 222, 228), 1 - 0.4 * f), L * 0.7 + 4 * f, -8 - 6 * f, 1 + 2 * f)
    if front:
        jaw = 1.0 + 1.0 * (0.5 + 0.5 * math.sin(t * 4))
        head = [(1, -6.2), (-4, -6.6), (-9, -5), (-13, -2.6), (-13, 0.4), (-5, 0.8)]
        lower = [(-5, 1.4), (-12.5, 1 + jaw), (-12, 3.4 + jaw), (-4, 5.6), (1, 6)]
        car.poly(INK, [(l * 1.06 - 0.3, o * 1.12) for l, o in head + [(1, 1)]])
        car.poly(INK, [(l * 1.06 - 0.3, o * 1.1) for l, o in lower + [(1, 1)]])
        car.poly(bronze, head + [(1, 1)])
        car.poly(iron, lower + [(1, 1)])
        car.poly(_lerp_colour((120, 30, 10), furnace, flicker), [(-5, 0.8), (-13, 0.4), (-12.5, 1 + jaw), (-5, 1.4)])
        for x in (-12.2, -10.6, -9, -7.4):  # iron teeth
            car.poly(iron_light, [(x, 0.5), (x + 0.5, 1.7), (x + 1, 0.6)])
        car.line(bronze_dark, -9, -5, -13, -1, 0.5)
        for rx, ro in ((-3, -5.4), (-7, -4.4), (-10.5, -2.6)):
            car.dot(bronze_dark, rx, ro, 0.4)
        # Two iron horns and a gauge for an eye.
        for base, tip in (((-3, -6.4), (4, -11)), ((-6, -5.8), (-1, -10.5))):
            car.line(INK, *base, *tip, 1.5)
            car.line(iron_light, *base, *tip, 0.8)
        car.dot(INK, -7.4, -3.2, 1.6)
        car.dot((240, 230, 200), -7.4, -3.2, 1.25)
        needle = math.sin(t * 3) * 0.8
        car.line((200, 30, 30), -7.4, -3.2, -7.4 + math.cos(needle - 1.6), -3.2 + math.sin(needle - 1.6), 0.35)
        # Breath: clouds of steam with a glow of the furnace inside.
        b = 1.2 + jaw / 2
        for i in range(4):
            f = (t * 1.6 + i / 4) % 1.0
            car.dot(_shade((230, 232, 238), 1 - 0.35 * f), -14 - f * 12, b - f * 2.5 + (i % 2) * 1.5, 1.4 + 2.6 * f)
        car.dot(_lerp_colour((255, 150, 60), (255, 230, 150), flicker), -14, b, 1.2)
    if rear:
        wag = 2.0 * math.sin(t * 2.4)
        segs = 4
        for i in range(segs):
            l0 = L - 0.5 + i * 3.2
            w = 4.6 - i * 0.9
            o = wag * i / segs
            car.poly(INK, [(l0, o - w - 0.6), (l0 + 3.6, o - w + 0.3), (l0 + 3.6, o + w - 0.3), (l0, o + w + 0.6)])
            car.poly(bronze if i % 2 == 0 else bronze_dark, [(l0, o - w), (l0 + 3.2, o - w + 0.6), (l0 + 3.2, o + w - 0.6), (l0, o + w)])
            car.dot(bronze_light, l0 + 1.6, o - w + 1, 0.35)
        end = L - 0.5 + segs * 3.2
        o = wag
        car.poly(INK, [(end - 0.4, o - 2.4), (end + 5.6, o), (end - 0.4, o + 2.4)])
        car.poly(iron_light, [(end, o - 1.8), (end + 4.6, o), (end, o + 1.8)])


def _gem_h(car, front, rear, stripe, t, index) -> None:
    # Amethyst: violets in silver, with small topazes and diamonds.
    palette = [(230, 190, 255), (170, 100, 230), (126, 56, 190), (84, 28, 140), (200, 140, 245), (56, 14, 100)]
    _gem(car, front, rear, stripe, t, index, palette, (214, 220, 230), (130, 140, 156), [(255, 190, 40), (240, 250, 255)])


DRAW = {
    ("R", "real"): _real_r,
    ("IR", "real"): _real_ir,
    ("R", "vintage"): _vintage_r,
    ("IR", "vintage"): _vintage_ir,
    ("R", "modern"): _modern_r,
    ("IR", "modern"): _modern_ir,
    ("R", "future"): _future_r,
    ("IR", "future"): _future_ir,
    ("R", "dragon"): _jade_dragon,
    ("IR", "dragon"): _fire_dragon,
    ("R", "gem"): _gem_r,
    ("IR", "gem"): _gem_ir,
    ("M", "real"): _real_m,
    ("M", "vintage"): _vintage_m,
    ("M", "modern"): _modern_m,
    ("M", "future"): _future_m,
    ("M", "dragon"): _ice_dragon,
    ("M", "gem"): _gem_m,
    ("H", "real"): _real_h,
    ("H", "vintage"): _vintage_h,
    ("H", "modern"): _modern_h,
    ("H", "future"): _future_h,
    ("H", "dragon"): _iron_dragon,
    ("H", "gem"): _gem_h,
}


def draw_car(screen, a, b, kind: str, skin: str, stripe, index: int, cars: int, k: float, t: float) -> None:
    """Draw carriage number `index` (0 = the front) of a train of `cars` carriages, from a
    (its front end) to b (its rear end), in screen pixels; k is screen pixels per design pixel."""
    draw = DRAW.get((kind, skin)) or DRAW.get((kind, "real")) or _real_r
    draw(Car(screen, a, b, k), index == 0, index == cars - 1, stripe, t, index)


# The Customise menu shows long trains shortened to this many carriages, so they stay big enough.
PREVIEW_CARS = 3


def preview_cars(kind: str) -> int:
    return min(CARS.get(kind, 2), PREVIEW_CARS)


def draw_preview(screen, kind: str, skin: str, x: float, y: float, k: float, stripe, t: float, car_len=22.0, gap=3.0) -> None:
    """A train running to the left, its front at (x, y), as in the Customise menu."""
    cars = preview_cars(kind)
    for i in reversed(range(cars)):
        a = (x + i * (car_len + gap) * k, y)
        b = (a[0] + car_len * k, y)
        if i < cars - 1:
            pygame.draw.line(screen, INK, b, (b[0] + gap * k, y), max(1, round(3 * k)))
        draw_car(screen, a, b, kind, skin, stripe, i, cars, k, t)
