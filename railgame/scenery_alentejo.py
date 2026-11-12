"""Storybook scenery for the Linha do Alentejo, in the style of the other maps.

The plain: a patchwork of golden wheat, stubble with round hay bales, ploughed earth, green
pasture with sheep, olive groves in rows and the montado (cork oaks with their red, stripped
trunks). White villages with blue or ochre bands, red roofs and big chimneys, the castles of
Alvito and Beja, church towers and poles crowned with storks' nests, and the Alvito reservoir.

Drawn once into the background by draw(). What moves is drawn every frame: the ripples on the
reservoir and the lit windows (by render.Renderer._draw_animated, from self.wave_marks and
self.windows), and the storks gliding over the plain (by animate()).
"""

import math
import random

import pygame

from railgame import render as R
from railgame import ui
from railgame.render import HEIGHT, PANEL_X, TOP_BAR, WHITE, glow
from railgame.scenery_lines import blur, station_name_rects
from railgame.ui import S

DAY = {
    "grass": (180, 196, 104),
    "wheat": (232, 196, 92),
    "wheat_row": (210, 172, 70),
    "stubble": (236, 218, 156),
    "stubble_row": (214, 194, 130),
    "plough": (180, 124, 80),
    "plough_row": (152, 100, 64),
    "pasture": (164, 198, 96),
    "montado": (204, 196, 118),
    "olive_ground": (222, 206, 150),
    "hedge": (150, 140, 84),
    "oak": (74, 110, 54),
    "oak_dark": (52, 84, 42),
    "oak_light": (110, 146, 72),
    "cork": (200, 96, 54),
    "bark": (102, 80, 60),
    "bale": (228, 192, 104),
    "bale_dark": (176, 138, 70),
    "sheep": (246, 244, 236),
    "sheep_head": (40, 38, 36),
    "water": (78, 152, 192),
    "water_light": (132, 196, 220),
    "shore": (214, 196, 150),
    "wall": (252, 250, 244),
    "wall_shade": (214, 210, 200),
    "blue": (40, 100, 180),
    "ochre": (216, 168, 56),
    "roof": (204, 98, 58),
    "roof_dark": (162, 72, 46),
    "stone": (216, 202, 170),
    "stone_dark": (170, 152, 122),
    "outline": (64, 58, 46),
    "window": (90, 130, 170),
    "door": (60, 96, 160),
    "nest": (128, 94, 58),
    "stork": (250, 250, 250),
    "stork_wing": (28, 28, 32),
    "beak": (226, 84, 50),
    "pole": (120, 110, 100),
}


def _night(c):
    return tuple(round(a + (b - a) * 0.62) for a, b in zip(c, (18, 28, 48)))


NIGHT = {k: _night(v) for k, v in DAY.items()}
NIGHT.update(window=(40, 50, 70), water=(22, 54, 90), water_light=(40, 80, 112))


def _colours(self):
    return NIGHT if self.night else DAY


class _Noise:
    """Smooth random patches (value noise): which kind of farm goes where."""

    def __init__(self, cell, rng):
        self.cell, self.rng, self.grid = cell, rng, {}

    def _at(self, i, j):
        if (i, j) not in self.grid:
            self.grid[(i, j)] = self.rng.random()
        return self.grid[(i, j)]

    def __call__(self, x, y):
        fx, fy = x / self.cell, y / self.cell
        i, j = math.floor(fx), math.floor(fy)
        tx, ty = fx - i, fy - j
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        a = self._at(i, j) + (self._at(i + 1, j) - self._at(i, j)) * tx
        b = self._at(i, j + 1) + (self._at(i + 1, j + 1) - self._at(i, j + 1)) * tx
        return a + (b - a) * ty


# ---------------------------------------------------------------- small drawings

def cork_oak(surf, c, x, y, r, rng):
    """A cork oak: a short trunk, stripped red-orange at the bottom, and a wide, lumpy crown."""
    trunk_top = (x + rng.uniform(-0.2, 0.2) * r, y - r * 1.1)
    ui.thick_lines(surf, c["outline"], [(x, y), trunk_top], S(3.4))
    ui.thick_lines(surf, c["bark"], [(x, y), trunk_top], S(2.2))
    ui.thick_lines(surf, c["cork"], [(x, y), (x + (trunk_top[0] - x) * 0.5, y - r * 0.55)], S(2.2))
    cx, cy = trunk_top[0], trunk_top[1] - r * 0.3
    lumps = [(rng.uniform(-1.0, 1.0) * r, rng.uniform(-0.45, 0.2) * r, rng.uniform(0.45, 0.65) * r) for _ in range(6)]
    for dx, dy, rr in lumps:
        pygame.draw.ellipse(surf, c["outline"], (cx + dx - rr - S(1), cy + dy - rr * 0.75 - S(1), 2 * rr + S(2), rr * 1.5 + S(2)))
    for dx, dy, rr in lumps:
        pygame.draw.ellipse(surf, c["oak"], (cx + dx - rr, cy + dy - rr * 0.75, 2 * rr, rr * 1.5))
    for dx, dy, rr in lumps[:3]:
        pygame.draw.ellipse(surf, c["oak_light"], (cx + dx - rr * 0.7, cy + dy - rr * 0.7, rr * 0.9, rr * 0.6))


def hay_bale(surf, c, x, y, r):
    ui.circle(surf, c["outline"], (x + S(1), y + S(1)), r + S(1))
    ui.circle(surf, c["bale"], (x, y), r)
    pygame.draw.arc(surf, c["bale_dark"], (x - r * 0.65, y - r * 0.65, r * 1.3, r * 1.3), 0.3, 5.2, max(1, S(1.2)))
    ui.circle(surf, c["bale_dark"], (x, y), max(1, r * 0.2))


def sheep(surf, c, x, y):
    pygame.draw.ellipse(surf, c["outline"], (x - S(4), y - S(2.6), S(8), S(5.2)))
    pygame.draw.ellipse(surf, c["sheep"], (x - S(3.5), y - S(2.2), S(7), S(4.4)))
    ui.circle(surf, c["sheep_head"], (x + S(3.6), y - S(0.6)), S(1.5))


def stork_nest(surf, c, x, y):
    """A storks' nest (on a pole, a chimney or a tower top) with a stork standing in it."""
    pygame.draw.ellipse(surf, c["outline"], (x - S(7), y - S(3), S(14), S(6)))
    pygame.draw.ellipse(surf, c["nest"], (x - S(6.5), y - S(2.5), S(13), S(5)))
    for k in range(5):
        a = k * 0.7
        pygame.draw.line(surf, c["outline"], (x - S(5) + k * S(2.4), y - S(1)), (x - S(4) + k * S(2.4) + math.sin(a) * S(1.5), y + S(2)), 1)
    body = pygame.Rect(0, 0, S(5), S(7))
    body.midbottom = (x, y - S(1))
    pygame.draw.ellipse(surf, c["stork"], body)
    pygame.draw.ellipse(surf, c["stork_wing"], (body.x + S(2), body.y + S(3), S(3.5), S(4)))
    ui.circle(surf, c["stork"], (x - S(0.5), body.y - S(1)), S(1.6))
    pygame.draw.line(surf, c["beak"], (x - S(1.5), body.y - S(1)), (x - S(5), body.y), max(1, S(1.2)))


def pole_with_nest(surf, c, x, y):
    ui.thick_lines(surf, c["outline"], [(x, y), (x, y - S(22))], S(3.2))
    ui.thick_lines(surf, c["pole"], [(x, y), (x, y - S(22))], S(2))
    stork_nest(surf, c, x, y - S(22))


def alentejo_house(self, surf, c, x, y, rng):
    """A long, low whitewashed house with a blue or ochre band, a red roof and a big chimney."""
    w, h = S(rng.uniform(11, 16)), S(rng.uniform(6, 8))
    front = pygame.Rect(0, 0, w, h)
    front.midbottom = (x, y + h / 2)
    roof = [(front.left - S(1), front.top + S(1)), (front.right + S(1), front.top + S(1)),
            (front.right - S(1.5), front.top - h * 0.45), (front.left + S(1.5), front.top - h * 0.45)]
    pygame.draw.rect(surf, c["wall_shade"], front.move(S(1.5), S(1)))
    pygame.draw.rect(surf, c["wall"], front)
    band = c["blue"] if rng.random() < 0.65 else c["ochre"]
    pygame.draw.rect(surf, band, (front.left, front.bottom - S(2), w, S(2)))
    pygame.draw.polygon(surf, c["roof"], roof)
    pygame.draw.line(surf, c["roof_dark"], roof[3], roof[2], max(1, S(1)))
    pygame.draw.polygon(surf, c["outline"], roof, 1)
    pygame.draw.rect(surf, c["outline"], front, 1)
    chimney = pygame.Rect(0, 0, S(4), S(6))
    chimney.midbottom = (front.left + w * rng.choice((0.2, 0.8)), front.top - h * 0.2)
    pygame.draw.rect(surf, c["wall"], chimney)
    pygame.draw.rect(surf, c["outline"], chimney, 1)
    pygame.draw.rect(surf, c["door"], (front.centerx - S(1.5), front.bottom - S(4.5), S(3), S(4.5)))
    wx, wy = front.left + S(2), front.top + S(1.8)
    pygame.draw.rect(surf, c["window"], (wx, wy, S(2.5), S(2.5)))
    if self.night and rng.random() < 0.8:
        self.windows.append((wx, wy, rng.uniform(0, 20), rng.uniform(5, 14)))
    return chimney.midtop


def castle(surf, c, x, y, keep_height):
    """A castle: a ring of crenellated walls, round towers and a tall square keep."""
    rx, ry = S(26), S(15)
    ring = [(x + math.cos(a) * rx, y + math.sin(a) * ry) for a in [k * math.pi / 14 for k in range(28)]]
    ui.thick_lines(surf, c["stone_dark"], ring + ring[:1], S(5))
    ui.thick_lines(surf, c["stone"], ring + ring[:1], S(3.5))
    for i, (px, py) in enumerate(ring):
        if i % 2 == 0:
            pygame.draw.rect(surf, c["stone"], (px - S(1.5), py - S(4), S(3), S(3)))
            pygame.draw.rect(surf, c["stone_dark"], (px - S(1.5), py - S(4), S(3), S(3)), 1)
    for a in (0.6, 2.5, 3.8, 5.6):
        tx, ty = x + math.cos(a) * rx, y + math.sin(a) * ry
        tower = pygame.Rect(0, 0, S(7), S(9))
        tower.midbottom = (tx, ty + S(2))
        pygame.draw.rect(surf, c["stone"], tower, border_top_left_radius=S(2), border_top_right_radius=S(2))
        pygame.draw.rect(surf, c["stone_dark"], tower, 1, border_top_left_radius=S(2), border_top_right_radius=S(2))
    keep = pygame.Rect(0, 0, S(13), keep_height)
    keep.midbottom = (x + S(4), y + S(3))
    pygame.draw.rect(surf, c["stone"], keep)
    pygame.draw.rect(surf, c["stone_dark"], (keep.right - S(4), keep.top, S(4), keep.height))
    pygame.draw.rect(surf, c["outline"], keep, 1)
    for k in range(4):
        pygame.draw.rect(surf, c["stone"], (keep.left + k * S(3.5), keep.top - S(3), S(2.4), S(3)))
        pygame.draw.rect(surf, c["outline"], (keep.left + k * S(3.5), keep.top - S(3), S(2.4), S(3)), 1)
    for k in range(2):
        pygame.draw.rect(surf, c["outline"], (keep.centerx - S(1), keep.top + S(5) + k * S(8), S(2), S(3.5)))
    return keep.midtop


def church(surf, c, x, y):
    """A whitewashed church with a bell tower (and a storks' nest on top)."""
    nave = pygame.Rect(0, 0, S(15), S(9))
    nave.midbottom = (x, y)
    tower = pygame.Rect(0, 0, S(6), S(19))
    tower.bottomright = (nave.left + S(1), nave.bottom)
    for rect in (nave, tower):
        pygame.draw.rect(surf, c["wall"], rect)
        pygame.draw.rect(surf, c["outline"], rect, 1)
    pygame.draw.polygon(surf, c["roof"], [nave.topleft, nave.topright, (nave.centerx, nave.top - S(5))])
    pygame.draw.polygon(surf, c["outline"], [nave.topleft, nave.topright, (nave.centerx, nave.top - S(5))], 1)
    pygame.draw.rect(surf, c["outline"], (tower.centerx - S(1.2), tower.top + S(3), S(2.4), S(4)))
    pygame.draw.rect(surf, c["blue"], (nave.left, nave.bottom - S(2), nave.width, S(2)))
    pygame.draw.rect(surf, c["door"], (nave.centerx - S(2), nave.bottom - S(5.5), S(4), S(5.5)), border_top_left_radius=S(2), border_top_right_radius=S(2))
    return (tower.centerx, tower.top)


# ---------------------------------------------------------------- the map

def draw(self, surf, cells, rng, area, kind_at) -> None:
    """Draw the plain, its farms, villages, castles, storks and the reservoir."""
    c = _colours(self)
    line, lay, geo = self.sim.line, self.layout, self.sim.line.geo
    rng = random.Random("alentejo")
    self.storks = []  # (centre x, centre y, radius, phase) of the storks gliding in circles
    land_side = -geo.water_side

    samples, pos = [], line.west_edge - 3000
    while pos <= line.east_edge + 3000:
        samples.append((*lay.point(pos), pos))
        pos += 150

    def from_track(x, y):
        sx, sy, p = min(samples, key=lambda s: (s[0] - x) ** 2 + (s[1] - y) ** 2)
        return math.dist((x, y), (sx, sy)), p

    names = station_name_rects(self)
    keep_away = []
    for st in line.stations:
        if st.has_loop:
            keep_away.append((*lay.local(st, 0, 0), lay.zone_px + S(12)))
        else:
            keep_away.append((*lay.point(st.pos), S(40)))
    for p in (line.west_edge, line.east_edge):
        keep_away.append((*lay.point(p), S(90)))

    towns = []
    for st in line.stations:
        if st.name in geo.towns:
            r = S(geo.towns[st.name])
            towns.append((st, *lay.local(st, 0, land_side * (r * 0.6 + S(40))), r))

    def in_town(x, y, grow=1.0):
        return any(math.dist((x, y), (tx, ty)) < r * grow for _, tx, ty, r in towns)

    # The Alvito reservoir, on the far side of the line from the town.
    alvito = next(s for s in line.stations if s.name == "Alvito")
    lake_c = lay.local(alvito, 0, -land_side * S(120))
    lake = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    lake_noise = _Noise(S(26), random.Random("lake"))
    lake_r = S(52)
    for i in range(-30, 31):
        for j in range(-20, 21):
            x, y = lake_c[0] + i * S(4), lake_c[1] + j * S(4)
            d = math.hypot((x - lake_c[0]) / 1.35, y - lake_c[1])
            if d < lake_r * (0.55 + 0.75 * lake_noise(x, y)) and area.collidepoint(x, y) and from_track(x, y)[0] > S(36):
                ui.circle(lake, (255, 255, 255, 255), (x, y), S(4))
    lake_mask = pygame.mask.from_surface(blur(lake, 3), 120)

    def blocked(x, y, margin=0):
        if not area.collidepoint(x, y):
            return True
        d, p = from_track(x, y)
        if d < S(24) + margin:
            return True
        if any(r.collidepoint(x, y) for r in names):
            return True
        if any(math.dist((x, y), (kx, ky)) < kr for kx, ky, kr in keep_away):
            return True
        if lake_mask.get_at((int(x), int(y))):
            return True
        return False

    # Ground: the plain is dry grass, a little golden.
    pygame.draw.rect(surf, c["grass"], area.inflate(S(12), S(12)))

    # Farms: a patchwork turned to follow the line.
    (ax, ay), (bx, by) = lay.point(line.west_edge), lay.point(line.east_edge)
    angle = math.atan2(by - ay, bx - ax)
    ca, sa = math.cos(angle), math.sin(angle)
    kind_noise = _Noise(S(150), random.Random("farms"))

    def to_xy(u, v):
        return (u * ca - v * sa, u * sa + v * ca)

    corners = [(area.left, area.top), (area.right, area.top), (area.left, area.bottom), (area.right, area.bottom)]
    us = [x * ca + y * sa for x, y in corners]
    vs = [-x * sa + y * ca for x, y in corners]
    plots = []
    v = min(vs)
    while v < max(vs):
        h = S(rng.uniform(34, 54))
        u = min(us) - rng.uniform(0, S(40))
        while u < max(us):
            w = S(rng.uniform(48, 86))
            gap = S(2)
            quad = [to_xy(u + du, v + dv) for du, dv in ((gap, gap), (w - gap, gap), (w - gap, h - gap), (gap, h - gap))]
            cx, cy = sum(p[0] for p in quad) / 4, sum(p[1] for p in quad) / 4
            if not any(blocked(px, py) or in_town(px, py, 1.15) for px, py in (*quad, (cx, cy))):
                n = kind_noise(cx, cy) + rng.uniform(-0.12, 0.12)
                kind = "montado" if n < 0.32 else "olive" if n < 0.45 else "wheat" if n < 0.66 else "stubble" if n < 0.78 else "plough" if n < 0.9 else "pasture"
                plots.append((kind, quad, (u, v, w, h)))
            u += w
        v += h

    def rows(quad, colour, count, width):
        for k in range(1, count):
            t = k / count
            a = (quad[0][0] + (quad[3][0] - quad[0][0]) * t, quad[0][1] + (quad[3][1] - quad[0][1]) * t)
            b = (quad[1][0] + (quad[2][0] - quad[1][0]) * t, quad[1][1] + (quad[2][1] - quad[1][1]) * t)
            pygame.draw.line(surf, colour, a, b, width)

    def inside(quad, s, t):
        top = (quad[0][0] + (quad[1][0] - quad[0][0]) * s, quad[0][1] + (quad[1][1] - quad[0][1]) * s)
        bot = (quad[3][0] + (quad[2][0] - quad[3][0]) * s, quad[3][1] + (quad[2][1] - quad[3][1]) * s)
        return (top[0] + (bot[0] - top[0]) * t, top[1] + (bot[1] - top[1]) * t)

    oaks, olives, bales, flock = [], [], [], []
    for kind, quad, _ in plots:
        if kind == "wheat":
            pygame.draw.polygon(surf, c["wheat"], quad)
            rows(quad, c["wheat_row"], 7, max(1, S(1.2)))
        elif kind == "stubble":
            pygame.draw.polygon(surf, c["stubble"], quad)
            rows(quad, c["stubble_row"], 9, max(1, S(1)))
            for _ in range(rng.randint(3, 6)):
                bales.append(inside(quad, rng.uniform(0.15, 0.85), rng.uniform(0.2, 0.8)))
        elif kind == "plough":
            pygame.draw.polygon(surf, c["plough"], quad)
            rows(quad, c["plough_row"], 8, max(1, S(1.6)))
        elif kind == "pasture":
            pygame.draw.polygon(surf, c["pasture"], quad)
            fx, fy = inside(quad, rng.uniform(0.3, 0.7), rng.uniform(0.3, 0.7))
            for _ in range(rng.randint(4, 8)):
                flock.append((fx + rng.uniform(-S(14), S(14)), fy + rng.uniform(-S(7), S(7))))
        elif kind == "olive":
            pygame.draw.polygon(surf, c["olive_ground"], quad)
            for s_ in (0.2, 0.4, 0.6, 0.8):
                for t_ in (0.3, 0.75):
                    olives.append(inside(quad, s_, t_))
        else:  # montado
            pygame.draw.polygon(surf, c["montado"], quad)
            for _ in range(rng.randint(2, 4)):
                oaks.append(inside(quad, rng.uniform(0.15, 0.85), rng.uniform(0.3, 0.9)))
        pygame.draw.polygon(surf, c["hedge"], quad, max(1, S(1.2)))

    # The reservoir, with a sandy shore and ripples (drawn every frame by the renderer).
    lake_surf = lake_mask.to_surface(setcolor=(*c["shore"], 255), unsetcolor=(0, 0, 0, 0))
    surf.blit(lake_surf, (0, 0))
    water = lake_mask.to_surface(setcolor=(*c["water"], 255), unsetcolor=(0, 0, 0, 0))
    eroded = pygame.mask.from_surface(blur(water, 2), 200)
    surf.blit(eroded.to_surface(setcolor=(*c["water"], 255), unsetcolor=(0, 0, 0, 0)), (0, 0))
    for comp in lake_mask.connected_components(40):
        o = comp.outline(2)
        if len(o) > 2:
            pygame.draw.aalines(surf, c["outline"], True, o)
    for _ in range(40):
        x = lake_c[0] + rng.uniform(-lake_r * 1.3, lake_r * 1.3)
        y = lake_c[1] + rng.uniform(-lake_r, lake_r)
        if area.collidepoint(x, y) and all(eroded.get_at((int(x + dx), int(y))) for dx in (-S(9), 0, S(9))):
            self.wave_marks.append((x, y, rng.uniform(0, 2 * math.pi)))
    if lake_mask.count():
        lx, ly = lake_mask.centroid()
        self._outlined(surf, self.f_small, geo.water_label, WHITE, (lx, ly + S(2)))

    # Trees, bales and sheep, back to front.
    things = [("oak", x, y) for x, y in oaks] + [("olive", x, y) for x, y in olives]
    things += [("bale", x, y) for x, y in bales] + [("sheep", x, y) for x, y in flock]
    for kind, x, y in sorted(things, key=lambda t: t[2]):
        if blocked(x, y, S(4)) or in_town(x, y, 1.1):
            continue
        if kind == "oak":
            cork_oak(surf, c, x, y, S(rng.uniform(5.5, 7.5)), rng)
        elif kind == "olive":
            self._olive_tree(surf, x, y, S(rng.uniform(3.6, 4.4)), rng)
        elif kind == "bale":
            hay_bale(surf, c, x, y, S(rng.uniform(3.2, 4)))
        else:
            sheep(surf, c, x, y)

    # Villages: white houses around each station, a church, and the castles of Alvito and Beja.
    controls = [self.signal_position(s) for s in line.signals] + [self.point_position(p) for p in line.points]
    circles = [lay.local(st, 0, self.gap / 2) if st.has_loop else lay.point(st.pos) for st in line.stations]

    def house_blocked(x, y):
        """Houses may come close to a station: they only keep clear of what you click."""
        if not area.collidepoint(x, y) or from_track(x, y)[0] < S(30) or lake_mask.get_at((int(x), int(y))):
            return True
        if any(r.inflate(S(10), S(10)).collidepoint(x, y) for r in names):
            return True
        return any(math.dist((x, y), q) < S(18) for q in controls) or any(math.dist((x, y), q) < S(26) for q in circles)

    houses = []
    for st, tx, ty, r in towns:
        count = int(14 * (r / S(30)) ** 2) + 4
        for _ in range(count * 10):
            if len(houses) and sum(1 for h in houses if h[0] is st) >= count:
                break
            a, d = rng.uniform(0, 2 * math.pi), rng.uniform(0, 1) ** 0.7 * r
            x, y = tx + math.cos(a) * d, ty + math.sin(a) * d * 0.75
            if house_blocked(x, y) or any(math.dist((x, y), (hx, hy)) < S(11) for _, hx, hy in houses):
                continue
            houses.append((st, x, y))
    chimneys = []
    for st, x, y in sorted(houses, key=lambda h: h[2]):
        chimneys.append(alentejo_house(self, surf, c, x, y, rng))
    tops = []
    for st, tx, ty, r in towns:
        if st.name == "Beja":
            tops.append(castle(surf, c, tx + r * 0.35, ty - r * 0.15, S(30)))
        elif st.name == "Alvito":
            tops.append(castle(surf, c, tx + r * 0.3, ty - r * 0.1, S(20)))
        elif r >= S(20):
            tops.append(church(surf, c, tx - r * 0.25, ty - r * 0.2))
    if self.night:
        for st, tx, ty, r in towns:
            glow(surf, tx, ty, r * 1.5, (255, 190, 100), 0.35)

    # Storks' nests: on the castles and church towers, a few chimneys and poles in the fields.
    for x, y in tops:
        stork_nest(surf, c, x, y - S(2))
    for x, y in rng.sample(chimneys, min(3, len(chimneys))):
        stork_nest(surf, c, x, y)
    open_spots = [(kind, quad) for kind, quad, _ in plots if kind in ("wheat", "stubble", "pasture")]
    for kind, quad in rng.sample(open_spots, min(5, len(open_spots))):
        x, y = inside(quad, 0.5, 0.5)
        if not blocked(x, y, S(6)):
            pole_with_nest(surf, c, x, y)
            if not self.night and len(self.storks) < 4:
                self.storks.append((x + S(30), y - S(40), S(rng.uniform(26, 40)), rng.uniform(0, 6.3)))

    # The name of the plain, across an open stretch of it.
    if geo.hills_label:
        text = "  ".join(" ".join(word.upper()) for word in geo.hills_label.split())
        w = self.f_bold.size(text)[0]
        best, best_d = None, -1
        for _ in range(300):
            x = rng.uniform(area.left + w / 2 + S(10), area.right - w / 2 - S(10))
            y = rng.uniform(area.top + S(30), area.bottom - S(30))
            box = pygame.Rect(0, 0, w, S(20))
            box.center = (x, y)
            d = min(from_track(px, py)[0] for px, py in (box.topleft, box.topright, box.bottomleft, box.bottomright, box.center))
            if d > best_d and not any(box.colliderect(r) for r in names) and not in_town(x, y, 1.6):
                best, best_d = (x, y), d
        if best:
            self._outlined(surf, self.f_bold, text, WHITE, best)


def animate(self, screen, speed) -> None:
    """Storks gliding in slow circles over the plain (by day and at sunset)."""
    storks = getattr(self, "storks", None)
    if not storks:
        return
    t = pygame.time.get_ticks() / 1000
    body, wing = R.gc(DAY["stork"]), R.gc(DAY["stork_wing"])
    for cx, cy, r, phase in storks:
        a = t * 0.35 + phase
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * 0.5
        heading = a + math.pi / 2
        flap = math.sin(t * 2 + phase) * S(1.5)
        ux, uy = math.cos(heading), math.sin(heading)
        px, py = -uy, ux
        span = S(9)
        tip_l = (x + px * span, y + py * span + flap)
        tip_r = (x - px * span, y - py * span + flap)
        pygame.draw.line(screen, wing, tip_l, tip_r, max(2, S(2.4)))
        pygame.draw.line(screen, body, (x - px * span * 0.5, y - py * span * 0.5), (x + px * span * 0.5, y + py * span * 0.5), max(2, S(2.4)))
        pygame.draw.line(screen, body, (x - ux * S(5), y - uy * S(5)), (x + ux * S(5), y + uy * S(5)), max(2, S(2.2)))
        pygame.draw.line(screen, R.gc(DAY["beak"]), (x + ux * S(5), y + uy * S(5)), (x + ux * S(8), y + uy * S(8)), max(1, S(1.2)))
