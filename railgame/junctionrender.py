"""Drawing a line with a branch (junction.py), made in the level editor.

The main line is drawn exactly like any single line, with its landscape (render.Renderer does
that). The branch is a second line laid over the same map: it leaves the main line at the
junction points and runs off to the edge of the map, on the side away from the water.
"""

import math

import pygame

from railgame import render as R
from railgame import ui
from railgame.junction import BRANCH, MAIN, JunctionNetwork
from railgame.layout import ZONE_PX, Layout
from railgame.netrender import NetRenderer
from railgame.netsim import NetSimulation
from railgame.render import HEIGHT, PANEL_X, TOP_BAR, Renderer
from railgame.track import LOOP_HALF, Signal
from railgame.train import Train
from railgame.ui import S

FIRST_ANGLE = 32  # degrees between the main line and the branch where they part
BEND_PX = 110  # the branch turns to its final direction over this many pixels
CLEAR_PX = 70  # how close the branch may come to the main line again
WALL_PX = 90  # the branch starts turning away this far from an edge of the map
MAX_TURN = math.radians(5)  # how much the branch can turn in one step of its path (6 pixels)
LEAD_PX = 70  # the first station box of the branch keeps this far from the junction (and its station)
LEG_PX = 24  # length of the two short legs drawn at the junction points


class _MainOnly:
    """Stands in for the simulation while the main line's map is drawn."""

    def __init__(self, line):
        self.line = line


def branch_length(side) -> float:
    """How long the branch is drawn, in design pixels: room for its stations and a bit more."""
    loops = sum(st.has_loop for st in side.stations)
    return 150 + LEAD_PX + loops * (2 * ZONE_PX + 50) + (len(side.stations) - loops) * 50


def branch_path(
    main: Layout, start_pos: float, water_side: int, length: float, scale: float = 1.0, wet=None
) -> list[tuple[float, float]]:
    """Where the branch runs on the screen: `length` pixels of line from the junction points.

    The branch leaves the main line at a gentle angle, bends away from it and then keeps
    clear of the main line and of the edges of the map, turning along them when it must.
    Several directions are tried, on the dry side of the line (either side when there is no
    water); the one that stays furthest from the main line wins. `water_side` is 0 without
    water, otherwise as in Geography. `wet(x, y)` says where there is water on the map (a
    lake, a bend of the river), which the branch avoids when it can.
    """
    k = scale
    x0, y0 = main.point(start_pos)
    ahead = main.point(start_pos + 300)
    behind = main.point(start_pos - 300)
    d = math.dist(behind, ahead) or 1.0
    ux, uy = (ahead[0] - behind[0]) / d, (ahead[1] - behind[1]) / d
    nx, ny = uy, -ux  # to the left of a train going up the line
    left, top, right, bottom = 24 * k, (TOP_BAR + 34) * k, (PANEL_X - 24) * k, (HEIGHT - 24) * k
    step, reach = 6 * k, WALL_PX * k
    samples = [main._path_at(i * 12 * k) for i in range(int(main.cum[-1] / (12 * k)) + 1)]
    best, best_score = None, -math.inf
    for side in ((1, -1) if water_side == 0 else (-water_side,)):
        # A sharper junction is only tried for when the gentle one has no room to turn.
        for first, final in [(FIRST_ANGLE, f) for f in (75, 55, 95, 115, 40, 135, 155)] + [(70, 95), (70, 130), (110, 130), (110, 160)]:
            pts, x, y, gone = [(x0, y0)], x0, y0, 0.0
            c, sn = math.cos(math.radians(first)), math.sin(math.radians(first))
            heading = math.atan2(uy * c + side * ny * sn, ux * c + side * nx * sn)
            clear, ok = math.inf, True
            while gone < length:
                t = min(1.0, gone / (BEND_PX * k))
                angle = math.radians(first + (final - first) * t)
                dx = ux * math.cos(angle) + side * nx * math.sin(angle)
                dy = uy * math.cos(angle) + side * ny * math.sin(angle)
                # Pushed away from the edges of the map...
                for dist, px, py in ((x - left, 1, 0), (right - x, -1, 0), (y - top, 0, 1), (bottom - y, 0, -1)):
                    if dist < reach:
                        push = ((reach - dist) / reach) ** 2 * 4
                        dx, dy = dx + px * push, dy + py * push
                # ...and from the main line, once it has left it.
                if gone > 50 * k:
                    near = min(samples, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)
                    away = math.dist(near, (x, y))
                    clear = min(clear, away)
                    if away < reach * 2:
                        push = ((reach * 2 - away) / (reach * 2)) ** 2 * 8
                        dx, dy = dx + (x - near[0]) / (away or 1) * push, dy + (y - near[1]) / (away or 1) * push
                want = math.atan2(dy, dx)
                turn = (want - heading + math.pi) % (2 * math.pi) - math.pi
                heading += max(-MAX_TURN, min(MAX_TURN, turn))
                x, y, gone = x + math.cos(heading) * step, y + math.sin(heading) * step, gone + step
                if not (left <= x <= right and top <= y <= bottom):
                    ok = False
                    break
                pts.append((x, y))
            score = min(clear, 200 * k) - abs(final - 75) * 0.4 * k - (first - FIRST_ANGLE) * 1.5 * k
            if not ok:  # it left the map: only better than nothing, the longer the better
                score += (len(pts) - 1) * step - 5000 * k
            if wet is not None:
                score -= sum(wet(px, py) for px, py in pts[4::2]) * 25 * k
            if clear < CLEAR_PX * k:
                score -= 2000 * k  # it runs into the main line again
            if score > best_score:
                best, best_score = pts, score
    return best


class JunctionLayout:
    """The layouts of the main line and of the branch, used as one.

    Like layout.Layout it turns metres into pixels, but a place is (metres, track id), with
    the track ids of the network. Where a caller only gives metres (code shared with the
    single lines), the layout in `focus` answers: set it to the line being drawn.
    """

    def __init__(self, net: JunctionNetwork, main: Layout, side: Layout):
        self.net, self.main, self.side = net, main, side
        self.focus = main
        self.track_gap = main.track_gap
        self.zone_px = main.zone_px

    def of_track(self, track) -> Layout:
        return self.side if self.net.on_branch(track) else self.main

    def of_station(self, st) -> Layout:
        return self.side if self.net.line_of(st) is self.net.side else self.main

    def point(self, pos: float, track=None) -> tuple[float, float]:
        if isinstance(track, str):
            return self.of_track(track).point(pos, 2 if self.net.is_loop(track) else 1)
        return self.focus.point(pos, track or 1)

    def normal(self, pos: float, track: str | None = None) -> tuple[float, float]:
        return (self.of_track(track) if track else self.focus).normal(pos)

    def local(self, st, along_m: float, offset_px: float) -> tuple[float, float]:
        return self.of_station(st).local(st, along_m, offset_px)


class JunctionRenderer(Renderer):
    def __init__(self, sim: NetSimulation, train_skins: dict[str, str] | None = None):
        self.net: JunctionNetwork = sim.line
        net = self.net
        box = net.main.geo.map_box or (40, TOP_BAR + 120, PANEL_X - 80, HEIGHT - TOP_BAR - 250)
        self.main_layout = Layout(net.main, tuple(S(v) for v in box), ui.scale())
        self.side_layout = None  # made in _prepare_background, once the landscape is drawn
        super().__init__(sim, train_skins)

    def _make_layout(self):
        return JunctionLayout(self.net, self.main_layout, None)

    def _place_branch(self, surf) -> Layout:
        """Choose where the branch runs, keeping it out of the water drawn on the map."""
        net, k = self.net, ui.scale()
        water = [R.gc(c) for c in (self.sea, R.SB_SEA, R.SB_SHALLOW, R.SB_RIVER)]
        width, height = surf.get_size()

        def wet(x: float, y: float) -> bool:
            if not (0 <= x < width and 0 <= y < height):
                return False
            r, g, b = surf.get_at((int(x), int(y)))[:3]
            return any(abs(r - c[0]) + abs(g - c[1]) + abs(b - c[2]) < 36 for c in water)

        side = 0 if net.main.geo.water == "none" else net.main.geo.water_side
        path = branch_path(self.main_layout, net.side.west_edge, side, branch_length(net.side) * k, k, wet)
        return Layout(net.side, None, k, path=path, lead=LEAD_PX * k)

    # ------------------------------------------------------------------ background

    def _prepare_background(self) -> None:
        # The main line with its landscape, drawn (and kept) as for a line without a branch...
        sim, lay = self.sim, self.layout
        self.sim, self.layout = _MainOnly(self.net.main), self.main_layout
        try:
            super()._prepare_background()
        finally:
            self.sim, self.layout = sim, lay
        # ...and the branch on top of a copy of it.
        surf = self.background.copy()
        self.side_layout = self.layout.side = self._place_branch(surf)
        side, line = self.side_layout, self.net.side
        tracks = [side.main_track()] + [side.loop_track(st) for st in line.stations if st.has_loop]
        if self.storybook:
            for pts in tracks:
                ui.thick_lines(surf, R.gc(R.SB_TRACK_EDGE), pts, S(8))
        for pts in tracks:
            ui.thick_lines(surf, R.gc(R.TRACK), pts, S(4))
        self.background = surf

    # ------------------------------------------------------------------ positions

    def signal_position(self, signal: Signal) -> tuple[float, float]:
        if not isinstance(signal.track, str):  # the main line on its own, while its map is drawn
            return super().signal_position(signal)
        x, y = self.layout.point(signal.pos, signal.track)
        nx, ny = self.layout.normal(signal.pos, signal.track)
        side = S(R.SIGNAL_SIDE) if self.net.is_loop(signal.track) else -S(R.SIGNAL_SIDE)
        return (x + nx * side, y + ny * side)

    def point_position(self, point) -> tuple[float, float]:
        if not hasattr(point, "stem"):
            return super().point_position(point)
        return self.layout.point(point.pos, point.stem)

    def _station_layout(self, st):
        return self.layout.of_station(st)

    # ------------------------------------------------------------------ every frame

    def _legs(self, sw) -> tuple[list, list]:
        """The two short pieces of track after a set of points: (straight, diverging)."""
        lay = self.layout
        here = lay.point(sw.pos, sw.stem)
        if sw.branch != BRANCH:  # the points of a crossing station, as on a single line
            inner = sw.station.pos + sw.side * LOOP_HALF
            return [here, lay.point(inner, sw.straight)], [here, lay.point(inner, sw.branch)]
        main, side = self.main_layout, self.side_layout
        straight = main._path_at(main._metres_to_px(sw.pos) + S(LEG_PX))
        return [here, straight], [here, side._path_at(S(LEG_PX))]

    def _draw_points(self, screen, highlighted) -> None:
        for sw in self.sim.line.points:
            straight, diverging = self._legs(sw)
            active, other = (diverging, straight) if sw.diverging else (straight, diverging)
            ui.thick_line(screen, R.TRACK_DIM, other[0], other[1], S(4))
            ui.thick_line(screen, R.YELLOW if sw.diverging else R.WHITE, active[0], active[1], S(4))
            x, y = self.point_position(sw)
            rect = pygame.Rect(0, 0, S(13), S(13))
            rect.center = (int(x), int(y))
            pygame.draw.rect(screen, R.YELLOW if sw.diverging else R.WHITE, rect, border_radius=S(2))
            pygame.draw.rect(screen, R.BG, rect, S(2), border_radius=S(2))
            if sw.id in highlighted:
                self._pulse(screen, (x, y), highlighted[sw.id])

    def _draw_signals(self, screen, highlighted) -> None:
        for s in self.sim.line.signals:
            x, y = self.signal_position(s)
            ui.thick_line(screen, R.MUTED, self.layout.point(s.pos, s.track), (x, y), S(2))
            ui.circle(screen, (8, 8, 8), (x, y), S(8))
            ui.circle(screen, R.GREEN if s.green else R.RED, (x, y), S(6))
            if s.id in highlighted:
                self._pulse(screen, (x, y), highlighted[s.id])

    def _walk_back(self, train: Train, px_dists: list[float]) -> list[tuple[float, float]]:
        """As on a single line, but each part of the train is on a named track of the network
        (the front may be on the branch while the rear is still on the main line)."""
        sim, lay = self.sim, self.layout
        prev = lay.point(train.pos, train.track)
        done, metres = 0.0, 0.0
        out = []
        for want in px_dists:
            while done < want and metres < 6000:
                metres += 5
                pos = train.pos - train.direction * metres
                cur = lay.point(pos, sim.track_at(train, pos))
                done += math.dist(prev, cur)
                prev = cur
            out.append(prev)
        return out

    def _draw_train_labels(self, screen) -> None:
        taken = [self._station_box(st) for st in self.sim.line.stations] + self._control_boxes()
        for train, ends in self._labels_to_draw:
            self.layout.focus = self.layout.of_track(train.track)  # the tag stands beside its own line
            self._draw_train_label(screen, train, ends, taken)
        self.layout.focus = self.main_layout

    _draw_next_trains = NetRenderer._draw_next_trains
    _draw_hover = NetRenderer._draw_hover
