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
        ("dragon", "Jade dragon"),
        ("gem", "Diamond"),
    ],
    "IR": [
        ("real", "Real"),
        ("vintage", "Steam"),
        ("modern", "Modern"),
        ("dragon", "Fire dragon"),
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


DRAW = {
    ("R", "real"): _real_r,
    ("IR", "real"): _real_ir,
    ("R", "vintage"): _vintage_r,
    ("IR", "vintage"): _vintage_ir,
    ("R", "modern"): _modern_r,
    ("IR", "modern"): _modern_ir,
    ("R", "dragon"): _jade_dragon,
    ("IR", "dragon"): _fire_dragon,
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
