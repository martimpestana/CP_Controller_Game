"""Storybook scenery for the Linha do Norte in Lisbon, in the style of the other maps.

Inland: Alfama climbing up to the Castelo de São Jorge, the white dome of the Panteão, old
warehouses and chimneys in Marvila and Xabregas, the hills of Chelas along the Cintura line,
jacarandas and stone pines, and the modern towers of the Parque das Nações. On the river side:
the wide Tejo with its quays, a cruise ship at Santa Apolónia, the Oceanário, the Torre Vasco
da Gama, the cable car along the river, and the long Ponte Vasco da Gama.

Most of it is drawn once into the background. What moves (the waves, the orange ferry, the
cable car, the yellow tram, lit windows at night, the bridge lights) is drawn every frame by
animate(), from lists that draw() fills in.
"""

import math
import random

import pygame

from railgame import render as R
from railgame import ui
from railgame.render import HEIGHT, PANEL_X, TOP_BAR, glow
from railgame.ui import S

DAY = {
    "city": (238, 226, 200),  # the light stone of the streets and squares
    "street": (214, 198, 168),
    "park": (150, 204, 104),
    "park_dark": (110, 170, 80),
    "river": (70, 168, 214),
    "river_light": (120, 200, 230),
    "river_dark": (44, 128, 182),
    "quay": (176, 168, 152),
    "quay_dark": (128, 120, 108),
    "roof": (214, 104, 62),
    "roof_dark": (168, 74, 46),
    "facades": ((250, 236, 170), (246, 196, 186), (186, 214, 236), (250, 248, 240), (236, 210, 140), (214, 232, 200)),
    "window": (70, 90, 120),
    "outline": (80, 64, 56),
    "stone": (226, 218, 198),
    "stone_dark": (176, 166, 146),
    "jacaranda": (168, 120, 214),
    "jacaranda_dark": (126, 84, 176),
    "glass": (150, 196, 224),
    "label": (255, 255, 255),
}
NIGHT = {
    "city": (62, 64, 80),
    "street": (50, 52, 66),
    "park": (44, 78, 60),
    "park_dark": (32, 60, 46),
    "river": (18, 44, 84),
    "river_light": (30, 64, 108),
    "river_dark": (12, 30, 62),
    "quay": (84, 84, 94),
    "quay_dark": (60, 60, 70),
    "roof": (110, 62, 50),
    "roof_dark": (84, 46, 38),
    "facades": ((128, 120, 96), (124, 104, 104), (98, 110, 128), (130, 132, 140), (122, 110, 84), (108, 120, 104)),
    "window": (36, 42, 58),
    "outline": (16, 16, 24),
    "stone": (120, 120, 130),
    "stone_dark": (84, 84, 96),
    "jacaranda": (96, 70, 130),
    "jacaranda_dark": (72, 50, 104),
    "glass": (60, 90, 120),
    "label": (236, 240, 250),
}

SHORE = -50  # pixels from the line to the river bank (negative: the river side)


def _at(self, pos, off):
    """Screen point `off` design pixels to the side of the line (positive: inland)."""
    x, y = self.layout.base(pos)
    nx, ny = self.layout.normal(pos)
    return x + nx * S(off), y + ny * S(off)


def _px(surf, x, y):
    """The colour under a point, or None outside the surface."""
    if not surf.get_rect().collidepoint(int(x), int(y)):
        return None
    return tuple(surf.get_at((int(x), int(y)))[:3])


def draw(self, surf) -> None:
    c = NIGHT if self.night else DAY
    self.lx = c
    self.lx_smoke = []
    rng = random.Random("Lisboa")
    area = pygame.Rect(0, S(TOP_BAR), S(PANEL_X), S(HEIGHT - TOP_BAR))
    surf.fill(c["city"], area)
    self.lx_waves, self.lx_lights = [], []
    _river(self, surf, c, rng)
    keep_out = _track_samples(self)

    def free(x, y, r=S(8)):
        if not area.inflate(-S(8), -S(8)).collidepoint(x, y):
            return False
        if _px(surf, x, y) in (c["river"], c["quay"], c["quay_dark"]):
            return False
        return all((x - kx) ** 2 + (y - ky) ** 2 > (r + kr) ** 2 for kx, ky, kr in keep_out)

    _streets(self, surf, c, rng, free)
    _parks(self, surf, c, rng, free)
    _alfama(self, surf, c, rng, free)
    _marvila(self, surf, c, rng, free)
    _chelas(self, surf, c, rng, free)
    _parque_das_nacoes(self, surf, c, rng, free)
    _river_side(self, surf, c, rng)
    _labels(self, surf, c)


def _track_samples(self):
    """Places to keep clear: every track, the station names and the edge labels."""
    lay, line = self.layout, self.sim.line
    out = []
    for t in line.tracks.values():
        for x, y in lay.polyline(t.id, step=60):
            out.append((x, y, S(16)))
    for pos in range(-200, line.east_edge + 600, 50):
        out.append((*_at(self, pos, 0), S(36)))
    for st in line.stations:
        _, centre = self._station_place(st)
        out.append((*centre, S(40)))
    return out


# ---------------------------------------------------------------------- the river


def _river(self, surf, c, rng) -> None:
    line = self.sim.line
    shore = []
    for pos in range(-900, line.east_edge + 1200, 60):
        wobble = 5 * math.sin(pos / 230) + 3 * math.sin(pos / 97)
        shore.append(_at(self, pos, SHORE - wobble))
    right, bottom = S(PANEL_X), S(HEIGHT)
    water = shore + [(right + S(200), shore[-1][1]), (right + S(200), bottom + S(10)), (shore[0][0] - S(200), bottom + S(10))]
    pygame.draw.polygon(surf, c["river"], water)
    # The quay: a stone edge along the bank.
    ui.thick_lines(surf, c["quay_dark"], shore, S(7))
    ui.thick_lines(surf, c["quay"], shore, S(4))
    # Lighter water in a band near the bank, darker far out.
    near = [_at(self, pos, SHORE - 26 - 6 * math.sin(pos / 300)) for pos in range(-900, line.east_edge + 1200, 80)]
    ui.thick_lines(surf, c["river_light"], near, S(10))
    for _ in range(70):  # little wave marks, rocked by animate()
        pos = rng.uniform(-400, line.east_edge + 600)
        off = rng.uniform(70, 420)
        x, y = _at(self, pos, -off)
        if 0 < x < S(PANEL_X - 10) and S(TOP_BAR + 10) < y < S(HEIGHT - 10):
            if _px(surf, x, y) == c["river"]:
                self.lx_waves.append((x, y, rng.uniform(0, 6.3)))


def _river_side(self, surf, c, rng) -> None:
    """On the river: the cruise terminal, the bridge, the Oceanário, the tower, the cable car."""
    line = self.sim.line
    # Cruise ship at the Jardim do Tabaco terminal, just past Santa Apolónia.
    x, y = _at(self, 640, SHORE - 34)
    _cruise_ship(self, surf, x, y, c)
    # Ponte Vasco da Gama: from the north bank out across the estuary.
    start = _at(self, line.east_edge - 150, SHORE - 4)
    nx, ny = self.layout.normal(line.east_edge)
    ux, uy = -nx, -ny  # straight out across the river
    bx, by = (ux * 0.55 + 0.45), (uy * 0.55 + 0.84)
    length = math.hypot(bx, by)
    bx, by = bx / length, by / length
    end = (start[0] + bx * S(520), start[1] + by * S(520))
    ui.thick_line(surf, c["outline"], start, end, S(7))
    ui.thick_line(surf, c["stone"], start, end, S(5))
    for i in range(1, 22):  # the piers
        px, py = start[0] + bx * S(24) * i, start[1] + by * S(24) * i
        pygame.draw.line(surf, c["stone_dark"], (px, py + S(2)), (px, py + S(6)), max(1, S(2)))
        self.lx_lights.append((px, py - S(1), i * 0.7))
    for f in (0.32, 0.44):  # the cable-stayed main span
        px, py = start[0] + bx * S(520) * f, start[1] + by * S(520) * f
        top = (px, py - S(26))
        ui.thick_line(surf, c["outline"], (px, py), top, S(3))
        ui.thick_line(surf, c["stone"], (px, py), top, S(2))
        for k in (-0.08, -0.04, 0.04, 0.08):
            qx, qy = start[0] + bx * S(520) * (f + k), start[1] + by * S(520) * (f + k)
            pygame.draw.aaline(surf, c["stone_dark"], top, (qx, qy))
        self.lx_lights.append((top[0], top[1], f * 9))
    mx, my = start[0] + bx * S(330), start[1] + by * S(330)
    self.lx_bridge_label = (mx + S(56), my - S(10))
    # Oceanário: a building out on the water, on its pier.
    ox, oy = _at(self, 2700, SHORE - 58)
    pier = [_at(self, 2700, SHORE + 2), (ox, oy)]
    ui.thick_lines(surf, c["quay_dark"], pier, S(6))
    body = pygame.Rect(0, 0, S(34), S(20))
    body.center = (ox, oy)
    pygame.draw.rect(surf, c["outline"], body.inflate(S(3), S(3)), border_radius=S(3))
    pygame.draw.rect(surf, c["stone"], body, border_radius=S(3))
    glass = pygame.Rect(0, 0, S(22), S(9))
    glass.midbottom = (ox, body.top + S(2))
    pygame.draw.rect(surf, c["outline"], glass.inflate(S(2), S(2)), border_radius=S(2))
    pygame.draw.rect(surf, c["glass"], glass, border_radius=S(2))
    for i in range(4):  # blue tiles of waves on its walls
        pygame.draw.arc(surf, (60, 120, 200), (body.x + S(3) + i * S(8), body.y + S(9), S(8), S(6)), 0, math.pi, max(1, S(1)))
    _tag(self, surf, "Oceanário", (ox, body.bottom + S(10)), small=True)
    # Torre Vasco da Gama: a tall white tower with a sail on top.
    tx, ty = _at(self, 3020, SHORE - 18)
    pygame.draw.polygon(surf, c["outline"], [(tx - S(5), ty), (tx + S(5), ty), (tx + S(3), ty - S(54)), (tx - S(3), ty - S(54))])
    pygame.draw.polygon(surf, c["stone"], [(tx - S(4), ty), (tx + S(4), ty), (tx + S(2), ty - S(53)), (tx - S(2), ty - S(53))])
    sail = [(tx - S(2), ty - S(52)), (tx + S(12), ty - S(60)), (tx + S(3), ty - S(76))]
    pygame.draw.polygon(surf, c["outline"], sail)
    pygame.draw.polygon(surf, c["glass"], [(tx - S(1), ty - S(53)), (tx + S(10), ty - S(60)), (tx + S(2.5), ty - S(73))])
    self.lx_lights.append((tx + S(3), ty - S(76), 2.0))
    # The cable car along the river, from the Oceanário to the tower.
    a = _at(self, 2600, SHORE - 20)
    b = _at(self, 3020, SHORE - 20)
    for p in (a, b):
        ui.thick_line(surf, c["outline"], (p[0], p[1] + S(10)), (p[0], p[1] - S(6)), S(3))
    pygame.draw.aaline(surf, c["outline"], (a[0], a[1] - S(6)), (b[0], b[1] - S(6)))
    self.lx_cable = ((a[0], a[1] - S(6)), (b[0], b[1] - S(6)))
    # Little boats moored by the bank, and sailing boats out on the Tejo.
    for pos, off in ((900, -95), (1500, -170), (2100, -120), (-200, -150)):
        x, y = _at(self, pos, off)
        if _px(surf, x, y) == c["river"]:
            self._boat(surf, x, y, S(0.75), rng)
    # The orange ferry (cacilheiro) crosses the river: animate() moves it along this route.
    self.lx_ferry = (_at(self, 700, SHORE - 30), _at(self, 300, -560))


def _cruise_ship(self, surf, x, y, c) -> None:
    nx, ny = self.layout.normal(330)
    ang = math.atan2(-nx, ny)  # the ship lies along the quay
    length, width = S(84), S(14)
    ca, sa = math.cos(ang), math.sin(ang)

    def P(u, v):
        return (x + ca * u - sa * v, y + sa * u + ca * v)

    hull = [P(-length / 2, -width / 2), P(length / 2 - S(10), -width / 2), P(length / 2, 0), P(length / 2 - S(10), width / 2), P(-length / 2, width / 2)]
    pygame.draw.polygon(surf, c["outline"], hull)
    inner = [P(-length / 2 + S(1.5), -width / 2 + S(1.5)), P(length / 2 - S(11), -width / 2 + S(1.5)), P(length / 2 - S(2), 0),
             P(length / 2 - S(11), width / 2 - S(1.5)), P(-length / 2 + S(1.5), width / 2 - S(1.5))]
    pygame.draw.polygon(surf, (250, 250, 250) if not self.night else (150, 154, 166), inner)
    deck = [P(-length / 2 + S(8), -width / 2 + S(3.5)), P(length / 2 - S(22), -width / 2 + S(3.5)),
            P(length / 2 - S(22), width / 2 - S(3.5)), P(-length / 2 + S(8), width / 2 - S(3.5))]
    pygame.draw.polygon(surf, (70, 130, 190), deck)
    for i in range(9):
        wx, wy = P(-length / 2 + S(11) + i * S(6), 0)
        pygame.draw.rect(surf, (255, 230, 150) if self.night else (220, 236, 250), (wx - S(1), wy - S(1), S(2), S(2)))
        if self.night:
            self.windows.append((wx - S(1), wy - S(1), i * 1.3, 9.0))
    fx, fy = P(-length / 2 + S(20), 0)
    ui.circle(surf, c["outline"], (fx, fy), S(4))
    ui.circle(surf, (210, 50, 50), (fx, fy), S(3))


# ---------------------------------------------------------------------- the city


def _streets(self, surf, c, rng, free) -> None:
    """A few winding streets, so the city does not look flat."""
    for _ in range(18):
        x, y = rng.uniform(S(20), S(PANEL_X - 20)), rng.uniform(S(TOP_BAR + 20), S(HEIGHT - 20))
        pts = [(x, y)]
        angle = rng.uniform(0, math.tau)
        for _ in range(8):
            angle += rng.uniform(-0.5, 0.5)
            x += math.cos(angle) * S(16)
            y += math.sin(angle) * S(16)
            if not free(x, y, S(4)):
                break
            pts.append((x, y))
        if len(pts) > 2:
            ui.thick_lines(surf, c["street"], pts, S(4))


def _parks(self, surf, c, rng, free) -> None:
    """Gardens with jacarandas (purple in spring) and stone pines."""
    for _ in range(9):
        for _ in range(40):
            x, y = rng.uniform(S(30), S(PANEL_X - 30)), rng.uniform(S(TOP_BAR + 30), S(HEIGHT - 30))
            if free(x, y, S(30)):
                break
        else:
            continue
        r = S(rng.uniform(18, 28))
        pygame.draw.ellipse(surf, c["park_dark"], (x - r, y - r * 0.62, 2 * r, 1.24 * r))
        pygame.draw.ellipse(surf, c["park"], (x - r + S(2), y - r * 0.62 + S(2), 2 * r - S(4), 1.24 * r - S(4)))
        trees = [(x + rng.uniform(-r, r) * 0.7, y + rng.uniform(-r, r) * 0.4) for _ in range(5)]
        for tx, ty in sorted(trees, key=lambda t: t[1]):
            if rng.random() < 0.5:
                _jacaranda(surf, tx, ty, S(rng.uniform(4.5, 6)), c, rng)
            else:
                self._stone_pine(surf, tx, ty, S(rng.uniform(4.5, 5.5)), rng)


def _jacaranda(surf, x, y, r, c, rng) -> None:
    ui.thick_line(surf, c["outline"], (x, y), (x, y - r), S(2.4))
    ui.thick_line(surf, (120, 84, 56), (x, y), (x, y - r), S(1.4))
    lumps = [(rng.uniform(-0.7, 0.7) * r, rng.uniform(-0.4, 0.3) * r - r * 1.3, rng.uniform(0.45, 0.6) * r) for _ in range(5)]
    for dx, dy, rr in lumps:
        ui.circle(surf, c["outline"], (x + dx, y + dy), rr + S(1))
    for dx, dy, rr in lumps:
        ui.circle(surf, c["jacaranda_dark"], (x + dx, y + dy), rr)
    for dx, dy, rr in lumps[:3]:
        ui.circle(surf, c["jacaranda"], (x + dx - rr * 0.2, y + dy - rr * 0.25), rr * 0.7)


def _house(self, surf, x, y, c, rng, tall=1.0) -> None:
    """A Lisbon house: a narrow pastel facade (some tiled in blue azulejos), rows of windows
    and an orange tiled roof."""
    w, h = S(rng.uniform(7, 10)), S(rng.uniform(9, 14) * tall)
    front = pygame.Rect(0, 0, w, h)
    front.midbottom = (x, y)
    facade = rng.choice(c["facades"])
    pygame.draw.rect(surf, facade, front)
    if rng.random() < 0.2:  # azulejos: a blue pattern of little tiles
        for i in range(int(w // S(2))):
            for j in range(int(h // S(2))):
                if (i + j) % 2 == 0:
                    pygame.draw.rect(surf, (90, 130, 200) if not self.night else (60, 80, 120),
                                     (front.x + i * S(2), front.y + j * S(2), max(1, S(1)), max(1, S(1))))
    roof = [(front.left - S(1), front.top), (front.left + S(1.5), front.top - S(4)), (front.right - S(1.5), front.top - S(4)), (front.right + S(1), front.top)]
    pygame.draw.polygon(surf, c["roof"], roof)
    pygame.draw.polygon(surf, c["outline"], roof, 1)
    pygame.draw.rect(surf, c["outline"], front, 1)
    rows = max(1, int((h - S(4)) // S(4)))
    for j in range(rows):
        for wx in (front.left + S(1.5), front.right - S(3.5)):
            wy = front.top + S(2) + j * S(4)
            pygame.draw.rect(surf, c["window"], (wx, wy, S(2), S(2.4)))
            if self.night and rng.random() < 0.55:
                self.windows.append((wx, wy, rng.uniform(0, 20), rng.uniform(6, 16)))


def _blob(cx, cy, rx, ry, rng, n=120):
    """Random spots inside a wobbly ellipse."""
    pts = []
    for _ in range(n):
        a = rng.uniform(0, math.tau)
        d = math.sqrt(rng.random())
        pts.append((cx + math.cos(a) * rx * d, cy + math.sin(a) * ry * d))
    return pts


def _alfama(self, surf, c, rng, free) -> None:
    """Alfama on its hill, the castle on top, the Panteão's white dome, and the yellow tram."""
    hx, hy = _at(self, 260, 150)
    hill = pygame.Rect(0, 0, S(250), S(170))
    hill.center = (hx, hy)
    pygame.draw.ellipse(surf, c["stone_dark"], hill.inflate(S(6), S(6)))
    pygame.draw.ellipse(surf, c["stone"], hill)
    spots = [p for p in _blob(hx, hy + S(10), S(118), S(74), rng, 260) if free(*p, S(5))]
    castle = (hx - S(18), hy - S(40))
    for x, y in sorted(spots, key=lambda p: p[1]):
        if math.dist((x, y), castle) < S(34):
            continue
        _house(self, surf, x, y, c, rng)
    _castle(self, surf, *castle, c)
    px, py = _at(self, 520, 92)
    if free(px, py, S(14)):
        _pantheon(self, surf, px, py, c)
    # The tram climbs a street through Alfama: animate() moves it along these points.
    route = []
    for i in range(9):
        f = i / 8
        route.append((hx - S(110) + f * S(190), hy + S(54) - math.sin(f * math.pi) * S(46) + S(6) * math.sin(f * 9)))
    ui.thick_lines(surf, c["street"], route, S(5))
    for a, b in zip(route, route[1:]):
        pygame.draw.aaline(surf, c["outline"], a, b)
    self.lx_tram = route


def _castle(self, surf, x, y, c) -> None:
    """The Castelo de São Jorge: walls with battlements, square towers and the flag."""
    wall = pygame.Rect(0, 0, S(52), S(16))
    wall.midbottom = (x, y + S(8))
    pygame.draw.rect(surf, c["outline"], wall.inflate(S(2), S(2)))
    pygame.draw.rect(surf, c["stone"], wall)
    for i in range(7):  # battlements
        pygame.draw.rect(surf, c["stone"], (wall.x + i * S(7.6), wall.y - S(3), S(4), S(3)))
        pygame.draw.rect(surf, c["outline"], (wall.x + i * S(7.6), wall.y - S(3), S(4), S(3)), 1)
    for tx in (wall.left + S(2), wall.centerx - S(5), wall.right - S(12)):
        tower = pygame.Rect(tx, wall.y - S(14), S(10), S(16))
        pygame.draw.rect(surf, c["outline"], tower.inflate(S(2), S(2)))
        pygame.draw.rect(surf, c["stone"], tower)
        for i in range(3):
            pygame.draw.rect(surf, c["stone"], (tower.x + i * S(3.5), tower.y - S(2.5), S(2.5), S(2.5)))
        pygame.draw.rect(surf, c["window"], (tower.centerx - S(1), tower.y + S(4), S(2), S(4)))
    mast = (wall.centerx, wall.y - S(14))
    pygame.draw.line(surf, c["outline"], mast, (mast[0], mast[1] - S(14)), max(1, S(1.4)))
    flag = pygame.Rect(mast[0], mast[1] - S(14), S(10), S(6))
    pygame.draw.rect(surf, (210, 30, 40), flag)
    pygame.draw.rect(surf, (20, 120, 50), (flag.x, flag.y, S(4), flag.h))
    ui.circle(surf, (250, 210, 60), (flag.x + S(4), flag.centery), S(1.5))
    _tag(self, surf, "Castelo de S. Jorge", (wall.centerx, wall.bottom + S(10)), small=True)
    if self.night:
        glow(surf, wall.centerx, wall.centery, S(40), (255, 210, 130), 0.5)


def _pantheon(self, surf, x, y, c) -> None:
    """The Panteão Nacional (Santa Engrácia): a white church with a big dome."""
    body = pygame.Rect(0, 0, S(26), S(14))
    body.midbottom = (x, y)
    pygame.draw.rect(surf, c["outline"], body.inflate(S(2), S(2)))
    pygame.draw.rect(surf, c["stone"], body)
    for i in range(4):
        pygame.draw.line(surf, c["stone_dark"], (body.x + S(4) + i * S(6), body.y + S(3)), (body.x + S(4) + i * S(6), body.bottom - S(1)), max(1, S(1)))
    drum = pygame.Rect(0, 0, S(14), S(6))
    drum.midbottom = (x, body.top)
    pygame.draw.rect(surf, c["outline"], drum.inflate(S(2), S(2)))
    pygame.draw.rect(surf, c["stone"], drum)
    dome = pygame.Rect(0, 0, S(16), S(16))
    dome.center = (x, drum.top)
    pygame.draw.ellipse(surf, c["outline"], dome.inflate(S(2), S(2)))
    pygame.draw.ellipse(surf, c["stone"], dome)
    pygame.draw.rect(surf, c["city"], (dome.x - S(2), dome.centery + S(1), dome.w + S(4), dome.h))
    pygame.draw.rect(surf, c["outline"], drum.inflate(S(2), S(2)), 1)
    pygame.draw.rect(surf, c["stone"], drum)
    pygame.draw.line(surf, c["outline"], (x, dome.top), (x, dome.top - S(5)), max(1, S(1.4)))
    _tag(self, surf, "Panteão", (x, body.bottom + S(9)), small=True)


def _marvila(self, surf, c, rng, free) -> None:
    """Xabregas and Marvila: old warehouses with saw-tooth roofs and brick chimneys."""
    for pos in (820, 1000, 1180):
        x, y = _at(self, pos, rng.uniform(68, 92))
        if not free(x, y, S(18)):
            continue
        w, h = S(36), S(16)
        body = pygame.Rect(0, 0, w, h)
        body.midbottom = (x, y)
        pygame.draw.rect(surf, c["outline"], body.inflate(S(2), S(2)))
        pygame.draw.rect(surf, (196, 120, 90) if not self.night else (100, 66, 56), body)
        for i in range(4):  # the saw-tooth roof
            bx = body.x + i * w / 4
            pygame.draw.polygon(surf, c["roof_dark"], [(bx, body.y), (bx + w / 4, body.y - S(5)), (bx + w / 4, body.y)])
        for i in range(5):
            pygame.draw.rect(surf, c["window"], (body.x + S(3) + i * S(6.5), body.y + S(5), S(3), S(5)))
        cx = body.right - S(5)
        pygame.draw.rect(surf, c["outline"], (cx - S(3), body.y - S(24), S(6), S(24)))
        pygame.draw.rect(surf, (170, 80, 60) if not self.night else (90, 50, 44), (cx - S(2), body.y - S(23), S(4), S(23)))
        self.lx_smoke = getattr(self, "lx_smoke", []) + [(cx, body.y - S(25))]
    for _ in range(40):
        pos = rng.uniform(700, 1500)
        x, y = _at(self, pos, rng.uniform(45, 120))
        if free(x, y, S(7)):
            _house(self, surf, x, y, c, rng, tall=0.9)


def _chelas(self, surf, c, rng, free) -> None:
    """Houses up the slopes on both sides of the Cintura line, and blocks of flats."""
    for _ in range(300):
        x = rng.uniform(S(200), S(620))
        y = rng.uniform(S(TOP_BAR + 10), S(420))
        if free(x, y, S(7)):
            if rng.random() < 0.15:
                _flats(self, surf, x, y, c, rng)
            else:
                _house(self, surf, x, y, c, rng, tall=0.9)


def _flats(self, surf, x, y, c, rng) -> None:
    w, h = S(14), S(rng.uniform(20, 28))
    body = pygame.Rect(0, 0, w, h)
    body.midbottom = (x, y)
    pygame.draw.rect(surf, c["outline"], body.inflate(S(2), S(2)))
    pygame.draw.rect(surf, rng.choice(c["facades"]), body)
    for j in range(int(h // S(4))):
        for i in range(3):
            wx, wy = body.x + S(1.5) + i * S(4.2), body.y + S(1.5) + j * S(4)
            pygame.draw.rect(surf, c["window"], (wx, wy, S(2.4), S(2)))
            if self.night and rng.random() < 0.5:
                self.windows.append((wx, wy, rng.uniform(0, 20), rng.uniform(6, 16)))


def _parque_das_nacoes(self, surf, c, rng, free) -> None:
    """Glass towers and the white trees of the Oriente station roof."""
    for _ in range(14):
        pos = rng.uniform(2250, 3300)
        x, y = _at(self, pos, rng.uniform(55, 150))
        if not free(x, y, S(10)):
            continue
        w, h = S(rng.uniform(12, 18)), S(rng.uniform(26, 44))
        body = pygame.Rect(0, 0, w, h)
        body.midbottom = (x, y)
        pygame.draw.rect(surf, c["outline"], body.inflate(S(2), S(2)))
        pygame.draw.rect(surf, c["glass"], body)
        pygame.draw.rect(surf, R.mix(c["glass"], (255, 255, 255), 0.35), (body.x, body.y, w * 0.35, h))
        for j in range(int(h // S(5))):
            pygame.draw.line(surf, c["outline"], (body.x, body.y + j * S(5)), (body.right, body.y + j * S(5)), 1)
            if self.night and rng.random() < 0.7:
                self.windows.append((body.x + S(2) + rng.uniform(0, w - S(6)), body.y + j * S(5) + S(1.5), rng.uniform(0, 20), rng.uniform(6, 16)))
    # The roof of Oriente station: rows of white steel "trees" beside the platforms.
    ori = self.sim.line.station("ORI")
    for pos in range(int(ori.pos - 150), int(ori.pos + 160), 50):
        for off in (40, -40):
            x, y = _at(self, pos, off)
            col = c["stone"]
            pygame.draw.line(surf, c["outline"], (x, y), (x, y - S(10)), max(1, S(2.5)))
            pygame.draw.line(surf, col, (x, y), (x, y - S(10)), max(1, S(1.4)))
            for dx in (-S(5), 0, S(5)):
                pygame.draw.aaline(surf, col, (x, y - S(8)), (x + dx, y - S(14)))


def _tag(self, surf, text, centre, small=False) -> None:
    self._outlined(surf, self.f_small if small else self.f_bold, text, self.lx["label"], centre)


def _labels(self, surf, c) -> None:
    def spaced(text):
        return "  ".join(" ".join(word.upper()) for word in text.split())

    for text, pos, off in (("Alfama", 260, 252), ("Marvila", 1050, 140), ("Chelas", 1350, 300),
                           ("Parque das Nações", 2750, 175)):
        x, y = _at(self, pos, off)
        x = max(S(80), min(S(PANEL_X - 90), x))
        y = max(S(TOP_BAR + 16), min(S(HEIGHT - 16), y))
        _tag(self, surf, spaced(text), (x, y))
    x, y = _at(self, 1400, -260)
    _tag(self, surf, spaced("Rio Tejo"), (x, y))
    if hasattr(self, "lx_bridge_label"):
        _tag(self, surf, "Ponte Vasco da Gama", self.lx_bridge_label, small=True)


# ---------------------------------------------------------------------- every frame


def animate(self, screen, speed) -> None:
    ticks = pygame.time.get_ticks()
    dt = 0.0 if self._last_tick is None else (ticks - self._last_tick) / 1000
    self._last_tick = ticks
    now = ticks / 1000
    if speed > 0:
        self.sea_time += min(dt, 0.1)
    t = self.sea_time
    c = self.lx
    width = max(1, S(1.4))
    for x, y, phase in self.lx_waves:
        dx = math.sin(t * 1.6 + phase) * S(3)
        for side in (-S(4), S(4)):
            pygame.draw.arc(screen, c["river_dark"], (x + dx + side - S(4), y - S(3), S(8), S(6)), 0.2, math.pi - 0.2, width)
    # The ferry goes across and back.
    (ax, ay), (bx, by) = self.lx_ferry
    f = 0.5 - 0.5 * math.cos(t * 0.12)
    fx, fy = ax + (bx - ax) * f, ay + (by - ay) * f
    pygame.draw.ellipse(screen, c["outline"], (fx - S(12), fy - S(5), S(24), S(10)))
    pygame.draw.ellipse(screen, (240, 130, 40), (fx - S(11), fy - S(4), S(22), S(8)))
    pygame.draw.rect(screen, (250, 250, 250), (fx - S(6), fy - S(7), S(12), S(5)))
    pygame.draw.rect(screen, c["outline"], (fx - S(6), fy - S(7), S(12), S(5)), 1)
    pygame.draw.arc(screen, c["river_light"], (fx - S(18), fy + S(2), S(36), S(6)), math.pi + 0.3, 2 * math.pi - 0.3, width)
    # Cable car gondolas sliding along the river.
    (a0, a1), (b0, b1) = self.lx_cable
    for i in range(3):
        g = (t * 0.05 + i / 3) % 1.0
        gx, gy = a0 + (b0 - a0) * g, a1 + (b1 - a1) * g
        pygame.draw.line(screen, c["outline"], (gx, gy), (gx, gy + S(4)), 1)
        pygame.draw.rect(screen, c["outline"], (gx - S(3.5), gy + S(4), S(7), S(6)), border_radius=S(2))
        pygame.draw.rect(screen, (230, 80, 70) if i % 2 else (80, 140, 220), (gx - S(2.5), gy + S(5), S(5), S(4)), border_radius=S(1))
    # The yellow tram climbing through Alfama.
    route = self.lx_tram
    g = 0.5 - 0.5 * math.cos(t * 0.15)
    seg = g * (len(route) - 1)
    i = min(int(seg), len(route) - 2)
    k = seg - i
    (x0, y0), (x1, y1) = route[i], route[i + 1]
    tx, ty = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
    ang = math.atan2(y1 - y0, x1 - x0)
    ca, sa = math.cos(ang), math.sin(ang)
    body = [(tx + ca * u - sa * v, ty + sa * u + ca * v) for u, v in ((-S(7), -S(3.5)), (S(7), -S(3.5)), (S(7), S(3.5)), (-S(7), S(3.5)))]
    pygame.draw.polygon(screen, c["outline"], [(x + (x - tx) * 0.15, y + (y - ty) * 0.25) for x, y in body])
    pygame.draw.polygon(screen, (250, 204, 40), body)
    for u in (-S(4), 0, S(4)):
        wx, wy = tx + ca * u + sa * S(1), ty + sa * u - ca * S(1)
        pygame.draw.rect(screen, (60, 80, 110), (wx - S(1), wy - S(1), S(2), S(2)))
    pygame.draw.line(screen, c["outline"], (tx, ty - S(3)), (tx + S(2), ty - S(9)), 1)
    # Smoke from the old factory chimneys.
    for cx, cy in getattr(self, "lx_smoke", []):
        for j in range(3):
            p = (t * 0.6 + j / 3) % 1.0
            ui.circle(screen, R.mix(c["stone"], c["city"], p), (cx + p * S(10), cy - p * S(14)), S(1.5 + 2.5 * p))
    if not self.night:
        return
    for x, y, phase, period in self.windows:
        if (now + phase) % period < period * 0.72:
            pygame.draw.rect(screen, R.LIT_WINDOW, (x, y, S(2), S(2)))
    for x, y, phase in self.lx_lights:
        on = 0.6 + 0.4 * math.sin(now * 2 + phase)
        glow(screen, x, y, S(5), (255, 220, 140), on)
