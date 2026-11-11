"""Storybook scenery for the Oeste and Douro lines (the Algarve's is in render.py).

Oeste: ochre Atlantic cliffs with coves, the Óbidos lagoon, a lighthouse on a cape, the walled
town of Óbidos, vineyards, pear orchards, white windmills and the Montejunto hills with wind
turbines. Douro: the wide river with a bridge at Régua and rabelo boats, terraced vineyards on
both banks, quintas, olive and almond trees and pine woods on the hilltops.

Everything here is drawn once into the background, except the windmill sails, the turbines,
the little waves, the lit windows and the lighthouse beam, which render.Renderer._draw_animated
draws every frame from the lists these functions fill in. Colours are the SB_* constants in
render.py, which change between the Day and the Night theme.
"""

import math
import random

import pygame

from railgame import render as R
from railgame import ui
from railgame.layout import NearestSample
from railgame.render import HEIGHT, PANEL_X, TOP_BAR, WHITE, glow, mix
from railgame.ui import S


def along_fn(self):
    line, lay = self.sim.line, self.layout
    side = line.geo.water_side

    def along(off_fn, first, last, every=200):
        pts, pos = [], first
        while pos <= last:
            x, y = lay.point(pos)
            nx, ny = lay.normal(pos)
            off = off_fn(pos)
            pts.append((x + side * nx * S(off), y + side * ny * S(off)))
            pos += every
        return pts
    return along


def at(self, pos, off):
    x, y = self.layout.point(pos)
    nx, ny = self.layout.normal(pos)
    side = self.sim.line.geo.water_side
    return (x + side * nx * S(off), y + side * ny * S(off))


def blur(surf, factor):
    w, h = surf.get_size()
    small = pygame.transform.smoothscale(surf, (max(1, int(w / factor)), max(1, int(h / factor))))
    return pygame.transform.smoothscale(small, (w, h))


def find_spot_factory(self, surf, rng, taken):
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
    return find_spot


def station_name_rects(self):
    names = []
    for st in self.sim.line.stations:
        if st.has_loop:
            w = self.f_bold.size(st.name)[0]
            cx, cy = self.layout.local(st, 0, S(52))
            names.append(pygame.Rect(0, 0, w + S(24), S(30)).move(cx - w / 2 - S(12), cy - S(15)))
        else:
            w = self.f_small.size(st.name)[0]
            x, y = self.layout.point(st.pos)
            nx, ny = self.layout.normal(st.pos)
            cx, cy = x + nx * S(24), y + ny * S(24)
            names.append(pygame.Rect(0, 0, w + S(16), S(22)).move(cx - w / 2 - S(8), cy - S(11)))
    return names


def towns_with_roofs(self, surf, cells, rng, names, keep=0.3):
    """Whitewashed houses with terracotta roofs (the cube houses, with a tiled top)."""
    old = R.SB_WALL_TOP
    R.SB_WALL_TOP = R.SB_ROOF
    houses = []
    for x, y in cells["town"]:
        if any(r.collidepoint(x, y) for r in names):
            continue
        if rng.random() < keep:
            houses.append((x + rng.uniform(-3, 3), y + rng.uniform(-3, 3)))
    for x, y in sorted(houses, key=lambda h: h[1]):
        if rng.random() < 0.3:
            continue
        self._cube_house(surf, x, y, rng)
    R.SB_WALL_TOP = old
    if self.night:
        land_side = -self.sim.line.geo.water_side
        for st in self.sim.line.stations:
            if st.name in self.sim.line.geo.towns:
                r = S(self.sim.line.geo.towns[st.name])
                tx, ty = self.layout.local(st, 0, land_side * (r * 0.5 + S(30)))
                glow(surf, tx, ty, r * 1.4, (255, 190, 100), 0.35)


def rocky_hills(self, surf, cells, rng, turbines=0):
    """The hills the user liked: pointed, green slopes, rocky tops, pines and olives at the feet."""
    for x, y in cells["hills"]:
        ui.circle(surf, R.SB_HILL_BASE, (x, y), S(8.5))
    peaks = []
    for x, y in rng.sample(cells["hills"], len(cells["hills"])):
        if all(math.dist((x, y), (px, py)) > S(38) for px, py, _ in peaks):
            peaks.append((x, y, S(rng.uniform(26, 38))))
    feet, tops = [], []
    for x, y, r in sorted(peaks, key=lambda p: p[1]):
        top = (x + r * rng.uniform(-0.15, 0.15), y - r * 1.15)
        base_l, base_r = (x - r, y), (x + r, y)
        pygame.draw.polygon(surf, R.SB_HILL, [base_l, top, base_r])
        pygame.draw.polygon(surf, R.SB_HILL_LIGHT, [base_l, top, (x - r * 0.05, y)])
        k = 0.38
        tl = (top[0] + (base_l[0] - top[0]) * k, top[1] + (base_l[1] - top[1]) * k)
        tr = (top[0] + (base_r[0] - top[0]) * k, top[1] + (base_r[1] - top[1]) * k)
        jag = [tl, (tl[0] + r * 0.2, tl[1] + r * 0.12), (top[0], tl[1] - r * 0.02), (tr[0] - r * 0.2, tr[1] + r * 0.14), tr]
        pygame.draw.polygon(surf, R.SB_ROCK_DARK, [top] + jag[::-1])
        pygame.draw.polygon(surf, R.SB_ROCK, [top, jag[0], jag[1], jag[2]])
        pygame.draw.lines(surf, R.SB_OUTLINE, True, [base_l, top, base_r], max(1, S(2)))
        tops.append(top)
        for _ in range(2):
            feet.append((x + rng.uniform(-r, r) * 0.85, y + rng.uniform(-2, 3)))
    for x, y in sorted(feet, key=lambda f: f[1]):
        (self._stone_pine if rng.random() < 0.67 else self._olive_tree)(surf, x, y, S(rng.uniform(4.5, 6)), rng)
    for x, y in rng.sample(tops, min(turbines, len(tops))):
        self.turbines.append((x, y - S(2), rng.uniform(0, 6.3)))
    geo = self.sim.line.geo
    if geo.hills_label and cells["hills"]:
        text = "  ".join(" ".join(w.upper()) for w in geo.hills_label.split())
        hx = sum(x for x, _ in cells["hills"]) / len(cells["hills"])
        hy = sum(y for _, y in cells["hills"]) / len(cells["hills"])
        w = self.f_bold.size(text)[0]
        hx = max(S(10) + w / 2, min(S(PANEL_X - 10) - w / 2, hx))
        self._outlined(surf, self.f_bold, text, WHITE, (hx, hy))


def tree_clumps(self, surf, spots, rng, kind_at=None, want="field"):
    trees = []
    for x, y in spots:
        for _ in range(rng.randint(1, 3)):
            trees.append((x + rng.uniform(-9, 9), y + rng.uniform(-6, 6), S(rng.uniform(4, 5.5))))
    for x, y, r in sorted(trees, key=lambda t: t[1]):
        if kind_at is None or kind_at(x, y + r) == want:
            (self._stone_pine if rng.random() < 0.67 else self._olive_tree)(surf, x, y, r, rng)


# ================================================================ OESTE
def oeste_water(self, surf, label_pos):
    """The Atlantic of the Oeste: ochre cliffs with little coves, surf, the Óbidos lagoon,
    a lighthouse on a cape, fishing boats and gulls."""
    line, lay = self.sim.line, self.layout
    rng = random.Random("oeste sea")
    along = along_fn(self)
    A, B = line.west_edge - 4000, line.east_edge + 4000
    ui.thick_lines(surf, R.SB_SHALLOW, along(lambda p: 45 + 14, A, B), S(30))

    def jag(p):
        return 5 + 3 * math.sin(p / 260) + 2 * math.sin(p / 97 + 1)

    # Cliffs: a ragged band of ochre rock along the coast, with darker strata.
    outer = along(lambda p: 47, A, B, 100)
    inner = along(lambda p: 47 - 6 - jag(p), A, B, 100)
    pygame.draw.polygon(surf, R.SB_CLIFF, outer + inner[::-1])
    ui.thick_lines(surf, R.SB_CLIFF_DARK, along(lambda p: 46, A, B, 100), S(2))
    ui.thick_lines(surf, mix(R.SB_CLIFF, R.SB_CLIFF_DARK, 0.5), along(lambda p: 47 - 3 - jag(p) * 0.5, A, B, 100), S(1))
    # Sandy coves.
    for c in (2500, 12000, 19000, 28000):
        pts_o = along(lambda p: 50 + 3 * math.sin((p - c) / 1500 * math.pi), c, c + 1500, 100)
        pts_i = along(lambda p: 38, c, c + 1500, 100)
        pygame.draw.polygon(surf, R.SB_SAND, pts_o + pts_i[::-1])
    # Surf along the cliffs.
    pos = A
    while pos <= B:
        for k in range(2):
            x, y = at(self, pos + rng.uniform(-60, 60), 49 + k * 3 + rng.uniform(-1, 1))
            ui.circle(surf, mix(WHITE, R.SB_SHALLOW, 0.35 * k), (x, y), S(rng.uniform(1, 2)))
        pos += 90
    # Lagoa de Óbidos: a shallow lagoon behind a sand bar, between Óbidos and Caldas.
    c0, c1 = 34200, 37400
    mid = (c0 + c1) / 2
    lag_o = along(lambda p: 46, c0, c1, 100)
    lag_i = along(lambda p: 46 - 30 * math.sin((p - c0) / (c1 - c0) * math.pi) ** 0.7, c0, c1, 100)
    pygame.draw.polygon(surf, R.SB_SAND, along(lambda p: 49, c0 - 200, c1 + 200, 100) + along(lambda p: 46 - 33 * math.sin(max(0, min(1, (p - c0 + 200) / (c1 - c0 + 400))) * math.pi) ** 0.7, c0 - 200, c1 + 200, 100)[::-1])
    pygame.draw.polygon(surf, R.SB_SHALLOW, lag_o[2:-2] + lag_i[2:-2][::-1])
    ui.thick_lines(surf, R.SB_SHALLOW, [at(self, mid, 44), at(self, mid, 54)], S(5))
    lx, ly = at(self, mid, 95)
    self._outlined(surf, self.f_small, "Lagoa de Óbidos", WHITE, (lx, ly))
    # A lighthouse on a cape.
    cape = 11000
    for k, r in ((0, 13), (1, 10)):
        x, y = at(self, cape, 54)
        ui.circle(surf, R.SB_CLIFF_DARK if k == 0 else R.SB_CLIFF, (x, y), S(r))
    x, y = at(self, cape, 54)
    self._lighthouse(surf, x, y + S(4))
    nx, ny = lay.normal(cape)
    side = line.geo.water_side
    self.sea_angle = math.atan2(side * ny / 0.6, side * nx)
    self.beam_sweep = 1.0  # the coast runs north-south here: keep the beam off the shore
    # Sea stacks.
    for p in (6000, 16500, 30500):
        x, y = at(self, p, 62)
        ui.circle(surf, R.SB_CLIFF_DARK, (x + S(1), y + S(1)), S(5))
        ui.circle(surf, R.SB_CLIFF, (x, y), S(4.5))
        for k in range(8):
            a = k * math.pi / 4
            ui.circle(surf, WHITE, (x + math.cos(a) * S(7), y + math.sin(a) * S(5)), S(1.1))
    # Boats, waves, gulls.
    label_rect = self.f_bold.render(line.geo.water_label, True, WHITE).get_rect(center=label_pos).inflate(S(30), S(20))
    find_spot = find_spot_factory(self, surf, rng, [label_rect])
    for _ in range(3):
        spot = find_spot(S(16))
        if spot:
            self._boat(surf, *spot, S(1), rng)
    for _ in range(40):
        spot = find_spot(S(9), tries=40)
        if spot:
            self.wave_marks.append((*spot, rng.uniform(0, 2 * math.pi)))
    if not self.night:
        for _ in range(4):
            spot = find_spot(S(8), tries=60)
            if spot:
                x, y = spot
                for sgn in (-1, 1):
                    pygame.draw.arc(surf, (250, 250, 250), (x + (sgn - 1) * S(3), y - S(2), S(6), S(5)), 0.3, math.pi - 0.3, max(1, S(1.4)))
    else:
        layer = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        cx, cy = S(120), S(420)
        for k in range(12):
            ww = S(24) * (1 - k / 14)
            pygame.draw.ellipse(layer, (220, 230, 255, 70 - k * 5), (cx - ww / 2 + math.sin(k) * S(4), cy - k * S(5), ww, S(2.5)))
        surf.blit(layer, (0, 0))
    label = self.f_bold.render(line.geo.water_label, True, R.SB_OCEAN_TEXT)
    surf.blit(label, label.get_rect(center=label_pos))


def windmill(self, surf, x, y, rng):
    """A white Oeste windmill: round tower, dark cap. The sails are drawn every frame."""
    w, h = S(9), S(18)
    body = [(x - w / 2, y), (x + w / 2, y), (x + w * 0.38, y - h), (x - w * 0.38, y - h)]
    pygame.draw.polygon(surf, R.SB_WALL, body)
    pygame.draw.polygon(surf, R.SB_WALL_SHADE, [(x, y), (x + w / 2, y), (x + w * 0.38, y - h), (x, y - h)])
    pygame.draw.polygon(surf, R.SB_HOUSE_OUTLINE, body, 1)
    cap = [(x - w * 0.45, y - h), (x + w * 0.45, y - h), (x, y - h - S(6))]
    pygame.draw.polygon(surf, mix(R.SB_ROOF, (40, 30, 30), 0.3), cap)
    pygame.draw.polygon(surf, R.SB_HOUSE_OUTLINE, cap, 1)
    pygame.draw.rect(surf, R.SB_DOOR, (x - S(1.5), y - S(5), S(3), S(5)))
    if self.night:
        pygame.draw.rect(surf, R.SB_WINDOW, (x - S(1), y - h * 0.65, S(2.5), S(2.5)))
        self.windows.append((x - S(1), y - h * 0.65, rng.uniform(0, 20), rng.uniform(5, 14)))
    self.windmills.append((x, y - h - S(2), S(rng.uniform(13, 16)), rng.uniform(0, 6.3)))


def obidos(self, surf, rng):
    """Óbidos: a little white town inside medieval walls, with a keep."""
    st = next(s for s in self.sim.line.stations if s.name == "Óbidos")
    cx, cy = at(self, st.pos, 0)
    nx, ny = self.layout.normal(st.pos)
    side = self.sim.line.geo.water_side
    cx, cy = cx - side * nx * S(72), cy - side * ny * S(72)
    rx, ry = S(34), S(22)
    ring = [(cx + math.cos(a) * rx * (1 + 0.08 * math.sin(3 * a)), cy + math.sin(a) * ry) for a in [k * math.pi / 18 for k in range(36)]]
    pygame.draw.polygon(surf, mix(R.SB_LAND, R.SB_HILL, 0.6), [(x, y + S(4)) for x, y in ring])
    inside = []
    for _ in range(26):
        a, d = rng.uniform(0, 2 * math.pi), rng.uniform(0, 0.75) ** 0.6
        inside.append((cx + math.cos(a) * rx * d * 0.85, cy + math.sin(a) * ry * d * 0.8))
    old = R.SB_WALL_TOP
    R.SB_WALL_TOP = R.SB_ROOF
    for x, y in sorted(inside, key=lambda p: p[1]):
        self._cube_house(surf, x, y, rng)
    R.SB_WALL_TOP = old
    ui.thick_lines(surf, R.SB_STONE_DARK, ring + ring[:1], S(5))
    ui.thick_lines(surf, R.SB_STONE, ring + ring[:1], S(3.5))
    for i, (x, y) in enumerate(ring):  # battlements
        if i % 2 == 0:
            pygame.draw.rect(surf, R.SB_STONE, (x - S(1.5), y - S(4), S(3), S(3)))
            pygame.draw.rect(surf, R.SB_STONE_DARK, (x - S(1.5), y - S(4), S(3), S(3)), 1)
    for a in (0.3, 2.2, 3.6, 5.2):  # towers
        x, y = cx + math.cos(a) * rx, cy + math.sin(a) * ry
        t = pygame.Rect(0, 0, S(7), S(10))
        t.midbottom = (x, y + S(2))
        pygame.draw.rect(surf, R.SB_STONE, t)
        pygame.draw.rect(surf, R.SB_STONE_DARK, t, 1)
        for k in range(3):
            pygame.draw.rect(surf, R.SB_STONE, (t.left + k * S(2.5), t.top - S(2.5), S(1.8), S(2.5)))
    keep = pygame.Rect(0, 0, S(11), S(16))
    keep.midbottom = (cx + rx * 0.45, cy - ry * 0.2)
    pygame.draw.rect(surf, R.SB_STONE, keep)
    pygame.draw.rect(surf, R.SB_STONE_DARK, keep, 1)
    for k in range(4):
        pygame.draw.rect(surf, R.SB_STONE, (keep.left + k * S(3), keep.top - S(3), S(2), S(3)))
    pygame.draw.line(surf, R.SB_HOUSE_OUTLINE, keep.midtop, (keep.centerx, keep.top - S(9)), 1)
    pygame.draw.polygon(surf, (200, 40, 40), [(keep.centerx, keep.top - S(9)), (keep.centerx + S(6), keep.top - S(7.5)), (keep.centerx, keep.top - S(6))])
    return pygame.Rect(cx - rx - S(6), cy - ry - S(16), 2 * rx + S(12), 2 * ry + S(24))


def oeste_land(self, surf, cells, rng, area, kind_at):
    """Rolling farmland: vineyards, pear orchards, white windmills, the Montejunto hills with
    wind turbines, red-roofed towns and the walled town of Óbidos."""
    self.windmills, self.turbines = [], []
    names = station_name_rects(self)
    castle = obidos(self, surf, rng)
    fields = [c for c in cells["field"] if not castle.collidepoint(c)]
    angle = -1.15
    ca, sa = math.cos(angle), math.sin(angle)

    def plot(cx, cy, w, h):
        fu, fv = cx * ca + cy * sa, -cx * sa + cy * ca
        pts = [(fu - w / 2, fv - h / 2), (fu + w / 2, fv - h / 2), (fu + w / 2, fv + h / 2), (fu - w / 2, fv + h / 2)]
        return [(u * ca - v * sa, u * sa + v * ca) for u, v in pts]

    def ok(quad):
        return all(kind_at(px, py) == "field" and not castle.collidepoint(px, py) for px, py in quad)

    farms = []
    for x, y in rng.sample(fields, len(fields)):
        if len(farms) >= 16:
            break
        if all(math.dist((x, y), f) > S(62) for f in farms):
            farms.append((x, y))
    for i, (fx, fy) in enumerate(farms):
        kind = ("vineyard", "orchard", "fields")[i % 3]
        w, h = S(rng.uniform(42, 58)), S(rng.uniform(30, 40))
        quad = plot(fx, fy, w, h)
        if not ok(quad):
            continue
        if kind == "vineyard":
            pygame.draw.polygon(surf, R.SB_VINE_EARTH, quad)
            for k in range(1, 8):
                t = k / 8
                a = (quad[0][0] + (quad[3][0] - quad[0][0]) * t, quad[0][1] + (quad[3][1] - quad[0][1]) * t)
                b = (quad[1][0] + (quad[2][0] - quad[1][0]) * t, quad[1][1] + (quad[2][1] - quad[1][1]) * t)
                ui.thick_lines(surf, R.SB_VINE, [a, b], S(2.6))
            pygame.draw.polygon(surf, R.SB_OUTLINE, quad, 1)
        elif kind == "orchard":  # pear trees in a grid: narrow, upright crowns with little pears
            pygame.draw.polygon(surf, mix(R.SB_LAND, R.SB_SAND, 0.25), quad)
            pygame.draw.polygon(surf, R.SB_OUTLINE, quad, 1)
            for a in range(1, 5):
                for b in range(1, 4):
                    ta, tb = a / 5, b / 4
                    top = (quad[0][0] + (quad[1][0] - quad[0][0]) * ta, quad[0][1] + (quad[1][1] - quad[0][1]) * ta)
                    bot = (quad[3][0] + (quad[2][0] - quad[3][0]) * ta, quad[3][1] + (quad[2][1] - quad[3][1]) * ta)
                    x, y = top[0] + (bot[0] - top[0]) * tb, top[1] + (bot[1] - top[1]) * tb
                    pygame.draw.line(surf, R.SB_TRUNK, (x, y), (x, y - S(3)), max(1, S(1.5)))
                    crown = pygame.Rect(0, 0, S(5), S(8))
                    crown.midbottom = (x, y - S(2))
                    pygame.draw.ellipse(surf, R.SB_OUTLINE, crown.inflate(S(2), S(2)))
                    pygame.draw.ellipse(surf, R.SB_PEAR, crown)
                    ui.circle(surf, (226, 210, 90) if not self.night else (120, 112, 60), (x + S(1), y - S(5)), S(1))
        else:
            cols = 3
            for k in range(cols):
                t0, t1 = k / cols, (k + 1) / cols
                sub = [
                    (quad[0][0] + (quad[1][0] - quad[0][0]) * t0, quad[0][1] + (quad[1][1] - quad[0][1]) * t0),
                    (quad[0][0] + (quad[1][0] - quad[0][0]) * t1, quad[0][1] + (quad[1][1] - quad[0][1]) * t1),
                    (quad[3][0] + (quad[2][0] - quad[3][0]) * t1, quad[3][1] + (quad[2][1] - quad[3][1]) * t1),
                    (quad[3][0] + (quad[2][0] - quad[3][0]) * t0, quad[3][1] + (quad[2][1] - quad[3][1]) * t0),
                ]
                pygame.draw.polygon(surf, rng.choice(R.SB_FIELDS), sub)
                pygame.draw.polygon(surf, R.SB_SAND, sub, max(1, S(1.5)))
    rocky_hills(self, surf, cells, rng, turbines=4)
    tree_clumps(self, surf, rng.sample(fields, min(30, len(fields))), rng, kind_at)
    mills = []
    for x, y in rng.sample(fields, len(fields)):
        if len(mills) >= 6:
            break
        if kind_at(x, y) == "field" and all(math.dist((x, y), m) > S(80) for m in mills) and not any(r.collidepoint(x, y) for r in names):
            mills.append((x, y))
    for x, y in sorted(mills, key=lambda m: m[1]):
        windmill(self, surf, x, y, rng)
    towns_with_roofs(self, surf, cells, rng, names)


# ================================================================ DOURO
def douro_river(self, surf):
    """The Douro: a wide green-blue river between stony banks, a bridge at Régua and
    rabelo boats carrying barrels of port."""
    line, lay = self.sim.line, self.layout
    rng = random.Random("douro river")
    along = along_fn(self)
    A, B = line.west_edge - 2500, line.east_edge + 600

    def near(p):
        return 20 + 2 * math.sin(p / 900)

    def far(p):
        return 56 + 5 * math.sin(p / 1700 + 1) + 3 * math.sin(p / 600)

    a_pts, b_pts = along(near, A, B, 120), along(far, A, B, 120)
    pygame.draw.polygon(surf, R.SB_SCHIST, along(lambda p: near(p) - 3, A, B, 120) + along(lambda p: far(p) + 3, A, B, 120)[::-1])
    pygame.draw.polygon(surf, R.SB_RIVER, a_pts + b_pts[::-1])
    ui.thick_lines(surf, R.SB_RIVER_EDGE, along(lambda p: near(p) + 2, A, B, 120), S(3))
    ui.thick_lines(surf, R.SB_RIVER_EDGE, along(lambda p: far(p) - 2, A, B, 120), S(3))
    for pts in (along(lambda p: near(p) - 1.5, A, B, 60), along(lambda p: far(p) + 1.5, A, B, 60)):
        for x, y in pts:
            ui.circle(surf, rng.choice((R.SB_STONE, R.SB_STONE_DARK, R.SB_SCHIST)), (x + rng.uniform(-2, 2), y + rng.uniform(-1, 1)), S(rng.uniform(1, 1.8)))
    # The bridge at Régua.
    p = 1400
    a, b = at(self, p, 10), at(self, p, 66)
    ui.thick_lines(surf, R.SB_STONE_DARK, [a, b], S(9))
    ui.thick_lines(surf, R.SB_STONE, [a, b], S(7))
    for k in range(1, 5):
        t = k / 5
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        ui.circle(surf, R.SB_STONE_DARK, (x, y), S(1.4))
    # Rabelo boats.
    for p in (6000, 18500, 30000, 42000):
        off = (near(p) + far(p)) / 2 + rng.uniform(-4, 4)
        rabelo(self, surf, p, off, rng)
    # Little ripples, drawn every frame.
    for _ in range(46):
        p = rng.uniform(A + 3000, B - 3000)
        x, y = at(self, p, rng.uniform(near(p) + 5, far(p) - 5))
        if S(10) < x < S(PANEL_X - 10) and S(TOP_BAR + 10) < y < S(HEIGHT - 10):
            self.wave_marks.append((x, y, rng.uniform(0, 2 * math.pi)))
    if self.night:  # moonlight on the river
        layer = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        for p in (11000, 27000, 39000):
            x, y = at(self, p, (near(p) + far(p)) / 2)
            for k in range(6):
                pygame.draw.ellipse(layer, (220, 230, 255, 60 - k * 8), (x - S(10) + math.sin(k) * S(3), y - S(6) + k * S(2.5), S(20) * (1 - k / 8), S(2)))
        surf.blit(layer, (0, 0))
    mid = 24500
    x, y = at(self, mid, far(mid) + 16)
    self._outlined(surf, self.f_bold, line.geo.water_label, WHITE, (x, y))


def rabelo(self, surf, pos, off, rng):
    lay = self.layout
    x, y = at(self, pos, off)
    ax, ay = lay.point(pos - 100)
    bx, by = lay.point(pos + 100)
    ang = math.atan2(by - ay, bx - ax)
    ca, sa = math.cos(ang), math.sin(ang)

    def p(u, v):
        return (x + u * ca - v * sa, y + u * sa + v * ca)

    k = S(1)
    hull = [p(-15 * k, -2 * k), p(-12 * k, 3 * k), p(12 * k, 3 * k), p(17 * k, -3 * k), p(10 * k, 0), p(-10 * k, 0)]
    pygame.draw.polygon(surf, (110, 70, 40) if not self.night else (60, 42, 30), hull)
    pygame.draw.polygon(surf, R.SB_HOUSE_OUTLINE, hull, 1)
    for u in (-6, -2, 2):  # barrels of port
        bx, by = p(u * k, -1 * k)
        ui.circle(surf, (150, 96, 54) if not self.night else (80, 56, 40), (bx, by), S(2))
        ui.ring(surf, (70, 44, 28), (bx, by), S(2), 1)
    pygame.draw.line(surf, R.SB_TRUNK, p(-14 * k, 0), p(-22 * k, 4 * k), max(1, S(1.4)))  # steering oar
    mx, my = p(2 * k, -1 * k)
    pygame.draw.line(surf, R.SB_TRUNK, (mx, my), (mx, my - S(16)), max(1, S(1.4)))
    sail = pygame.Rect(0, 0, S(11), S(10))
    sail.midtop = (mx, my - S(15))
    pygame.draw.rect(surf, R.SB_SAIL, sail)
    pygame.draw.rect(surf, R.SB_HOUSE_OUTLINE, sail, 1)
    pygame.draw.line(surf, (190, 60, 50), (sail.left, sail.centery), (sail.right, sail.centery), max(1, S(1.5)))
    if self.night:
        glow(surf, mx + S(6), my - S(4), S(9), (255, 220, 120), 0.9)


def douro_land(self, surf, cells, rng, area, kind_at):
    """Terraced vineyards on both banks, white quintas among them, olive and almond trees,
    pine woods on the hilltops, and villages of white houses with red roofs."""
    line, lay = self.sim.line, self.layout
    side = line.geo.water_side
    names = station_name_rects(self)
    keep_away = []
    for st in line.stations:
        if st.has_loop:
            keep_away.append((*lay.local(st, 0, 0), lay.zone_px + S(10)))
    before = surf.copy()
    samples, pos = [], line.west_edge - 3000
    while pos <= line.east_edge + 3000:
        samples.append((*lay.point(pos), *lay.normal(pos), pos))
        pos += 150

    nearest = NearestSample(samples, S(60)).nearest

    def where(x, y):
        sx, sy, nx, ny, p = nearest(x, y)
        beyond = not (line.west_edge - 1500 <= p <= line.east_edge + 1500)  # past the ends of the line
        return math.dist((x, y), (sx, sy)), ((x - sx) * nx + (y - sy) * ny) * side > 0, beyond

    town_spots = set(cells["town"])
    step = S(7)
    plots = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    free_land = []
    noise_cells = {}

    def bump(i, j):
        if (i, j) not in noise_cells:
            noise_cells[(i, j)] = rng.random()
        return noise_cells[(i, j)]

    def patchy(x, y):  # smooth random patches
        cell = S(46)
        fx, fy = x / cell, y / cell
        i, j = int(fx), int(fy)
        tx, ty = fx - i, fy - j
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        a = bump(i, j) + (bump(i + 1, j) - bump(i, j)) * tx
        b = bump(i, j + 1) + (bump(i + 1, j + 1) - bump(i, j + 1)) * tx
        return a + (b - a) * ty

    y = area.top + step / 2
    while y < area.bottom:
        x = area.left + step / 2
        while x < area.right:
            if before.get_at((int(x), int(y)))[:3] == R.SB_LAND:
                d, river_side, beyond = where(x, y)
                blocked = (d < S(24) and not river_side) or (river_side and d < S(66)) or \
                    any(r.collidepoint(x, y) for r in names) or (x, y) in town_spots or \
                    any(math.dist((x, y), (kx, ky)) < kr for kx, ky, kr in keep_away)
                if not blocked:
                    if d > S(230) or beyond:
                        free_land.append((x, y, "top"))
                    elif patchy(x, y) > 0.36:
                        ui.circle(plots, (255, 255, 255, 255), (x, y), step * 0.95)
                    else:
                        free_land.append((x, y, "scrub"))
            x += step
        y += step
    mask = pygame.mask.from_surface(blur(plots, 2.5), 120)
    mask_surf = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))

    # Terraces: rows that follow the slope along the river, earth, a vine row and a schist wall.
    terr = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    terr.fill((*R.SB_VINE_EARTH, 255))
    A, B = line.west_edge - 6000, line.east_edge + 6000
    along = along_fn(self)
    for k in range(0, 46):
        d = 24 + k * 6.5
        for off in (-d, d):
            pts = along(lambda p, off=off, k=k: off + 1.2 * math.sin(p / 500 + k), A, B, 120)
            ui.thick_lines(terr, (*R.SB_SCHIST, 255), [(x, y + S(2.2)) for x, y in pts], S(1.4))
            ui.thick_lines(terr, (*R.SB_VINE, 255), pts, S(2.6))
    terr.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surf.blit(terr, (0, 0))
    for comp in mask.connected_components(30):
        o = comp.outline(2)
        if len(o) > 2:
            pygame.draw.aalines(surf, R.SB_OUTLINE, True, o)

    # Scrub between the vineyards: olive and almond trees; pine woods on the hilltops.
    scrub = [(x, y) for x, y, kind in free_land if kind == "scrub"]
    tops = [(x, y) for x, y, kind in free_land if kind == "top"]
    for x, y in tops:
        ui.circle(surf, R.SB_HILL_BASE, (x, y), S(8))
    for x, y in sorted(rng.sample(tops, min(160, len(tops))), key=lambda t: t[1]):
        self._stone_pine(surf, x + rng.uniform(-3, 3), y, S(rng.uniform(4.5, 6)), rng)
    for x, y in sorted(rng.sample(scrub, min(70, len(scrub))), key=lambda t: t[1]):
        if rng.random() < 0.6:
            self._olive_tree(surf, x, y, S(rng.uniform(4, 5.5)), rng)
        else:  # an almond tree in blossom
            pygame.draw.line(surf, R.SB_TRUNK, (x, y), (x, y - S(5)), max(1, S(1.5)))
            for _ in range(5):
                bx, by = x + rng.uniform(-4, 4), y - S(7) + rng.uniform(-3, 3)
                ui.circle(surf, (246, 214, 226) if not self.night else (130, 116, 126), (bx, by), S(1.8))
    # Quintas: white manor houses with red roofs among the vineyards.
    vine_cells = []
    y = area.top + S(20)
    while y < area.bottom - S(20):
        x = area.left + S(20)
        while x < area.right - S(20):
            if mask.get_at((int(x), int(y))) and before.get_at((int(x), int(y)))[:3] == R.SB_LAND:
                vine_cells.append((x, y))
            x += S(20)
        y += S(20)
    quintas = []
    for x, y in rng.sample(vine_cells, len(vine_cells)):
        if len(quintas) >= 6:
            break
        if all(math.dist((x, y), q) > S(110) for q in quintas):
            quintas.append((x, y))
    for x, y in sorted(quintas, key=lambda q: q[1]):
        quinta(self, surf, x, y, rng)
    towns_with_roofs(self, surf, cells, rng, names, keep=0.35)
    geo = line.geo
    if tops:
        hx = sum(x for x, _ in tops) / len(tops)
        hy = sum(y for _, y in tops) / len(tops)
        text = "  ".join(" ".join(w.upper()) for w in geo.hills_label.split())
        self._outlined(surf, self.f_bold, text, WHITE, (hx, min(hy, S(TOP_BAR + 40))))


def quinta(self, surf, x, y, rng):
    old = R.SB_WALL_TOP
    R.SB_WALL_TOP = R.SB_ROOF
    w, d, h = S(18), S(7), S(10)
    front = pygame.Rect(0, 0, w, h)
    front.midbottom = (x, y + h / 2)
    side = [front.topright, (front.right + d * 0.6, front.top - d * 0.5), (front.right + d * 0.6, front.bottom - d * 0.5), front.bottomright]
    top = [front.topleft, (front.left + d * 0.6, front.top - d * 0.5), (front.right + d * 0.6, front.top - d * 0.5), front.topright]
    pygame.draw.polygon(surf, R.SB_WALL_SHADE, side)
    pygame.draw.polygon(surf, R.SB_ROOF, top)
    pygame.draw.rect(surf, R.SB_WALL, front)
    for poly in (side, top):
        pygame.draw.polygon(surf, R.SB_HOUSE_OUTLINE, poly, 1)
    pygame.draw.rect(surf, R.SB_HOUSE_OUTLINE, front, 1)
    pygame.draw.rect(surf, R.SB_DOOR, (front.centerx - S(2), front.bottom - S(5), S(4), S(5)))
    for k in range(3):
        wx = front.left + S(2) + k * S(5.5)
        if k != 1:
            pygame.draw.rect(surf, R.SB_WINDOW, (wx, front.top + S(2), S(3), S(3)))
            if self.night:
                self.windows.append((wx, front.top + S(2), rng.uniform(0, 20), rng.uniform(6, 16)))
    R.SB_WALL_TOP = old
