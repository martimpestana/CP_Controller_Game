"""Drawing a custom line with a second line or a second track (junction.py), from the editor.

The main line is drawn exactly like any single line, with its landscape (render.Renderer does
that). The other lines are laid over the same map: a branch leaves the main line at the
junction points and runs off to the edge of the map, on the side away from the water; a
crossing line does the same on both sides of its station; a separate line has a place of its
own on the map. A double line gets its second track beside the first.
"""

import math

import pygame

from railgame import render as R
from railgame import ui
from railgame.junction import MAIN_BACK, JunctionNetwork
from railgame.layout import ZONE_PX, Layout
from railgame.netrender import NetRenderer
from railgame.netsim import NetSimulation
from railgame.render import HEIGHT, PANEL_X, TOP_BAR, Renderer
from railgame.track import EAST, LOOP_HALF, Line, Signal
from railgame.train import Train
from railgame.ui import S

FIRST_ANGLE = 32  # degrees between the main line and the branch where they part
BEND_PX = 110  # the branch turns to its final direction over this many pixels
CLEAR_PX = 70  # how close the branch may come to the main line again
WALL_PX = 90  # the branch starts turning away this far from an edge of the map
MAX_TURN = math.radians(5)  # how much the branch can turn in one step of its path (6 pixels)
LEAD_PX = 70  # the first station box of the branch keeps this far from the junction (and its station)
LEG_PX = 24  # length of the two short legs drawn at the junction points
CROSSOVER_M = 150  # metres over which a train moves across to the other track at a crossover


class _MainOnly:
    """Stands in for the simulation while the main line's map is drawn."""

    def __init__(self, line):
        self.line = line


def branch_length(side) -> float:
    """How long the branch is drawn, in design pixels: room for its stations and a bit more."""
    loops = sum(st.has_loop for st in side.stations)
    return 150 + LEAD_PX + loops * (2 * ZONE_PX + 50) + (len(side.stations) - loops) * 50


def branch_path(
    main: Layout, start_pos: float, sides: tuple[int, ...], length: float, scale: float = 1.0, wet=None,
    backwards: bool = False, avoid: list | None = None,
) -> tuple[list[tuple[float, float]], int]:
    """Where the branch runs on the screen: `length` pixels of line from the junction points.

    The branch leaves the main line at a gentle angle, bends away from it and then keeps
    clear of the main line and of the edges of the map, turning along them when it must.
    Several directions are tried, on the `sides` allowed (1: to the left of a train going up
    the main line, -1: to its right); the one that stays furthest from the main line wins.
    `wet(x, y)` says where there is water on the map (a lake, a bend of the river), which the
    branch avoids when it can. With `backwards` the branch leaves towards the start of the main
    line instead of its end. `avoid`: more points (another branch) to keep clear of.

    Returns the path, from the junction outwards, and the side it went to.
    """
    k = scale
    x0, y0 = main.point(start_pos)
    ahead = main.point(start_pos + 300)
    behind = main.point(start_pos - 300)
    d = math.dist(behind, ahead) or 1.0
    ux, uy = (ahead[0] - behind[0]) / d, (ahead[1] - behind[1]) / d
    nx, ny = uy, -ux  # to the left of a train going up the line
    if backwards:  # turned round: the same side of the line is now the other way
        ux, uy, nx, ny = -ux, -uy, -nx, -ny
    left, top, right, bottom = 24 * k, (TOP_BAR + 34) * k, (PANEL_X - 24) * k, (HEIGHT - 24) * k
    step, reach = 6 * k, WALL_PX * k
    samples = [main._path_at(i * 12 * k) for i in range(int(main.cum[-1] / (12 * k)) + 1)] + list(avoid or [])
    best, best_score, best_side = None, -math.inf, sides[0]
    for wanted_side in sides:
        side = -wanted_side if backwards else wanted_side
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
                best, best_score, best_side = pts, score, wanted_side
    return best, best_side


def dry_sides(main: Line) -> tuple[int, ...]:
    """The sides of the main line a second line may go to: away from the water, if any."""
    geo = main.geo
    return (1, -1) if geo.water == "none" else (-geo.water_side,)


def make_layouts(net: JunctionNetwork, main_layout: Layout, k: float, wet=None) -> dict[int, Layout]:
    """A Layout for every line of the network (keyed by id(line)), given the main line's."""
    layouts = {id(net.main): main_layout}
    sides = dry_sides(net.main)
    if net.kind in ("branch", "cross"):
        side = net.side
        path, went = branch_path(main_layout, side.west_edge, sides, branch_length(side) * k, k, wet)
        layouts[id(side)] = Layout(side, None, k, path=path, lead=LEAD_PX * k)
        if net.kind == "cross":
            west = net.west_side
            # Without water the crossing line goes on across the main line, to its other side.
            other = (-went,) if net.main.geo.water == "none" else sides
            back, _ = branch_path(main_layout, west.east_edge, other, branch_length(west) * k, k, wet, backwards=True, avoid=path)
            layouts[id(west)] = Layout(west, None, k, path=back[::-1], trail=LEAD_PX * k)
    elif net.kind == "separate":
        box = net.side.geo.map_box
        layouts[id(net.side)] = Layout(net.side, tuple(v * k for v in box), k)
    return layouts


class JunctionLayout:
    """The layouts of all the lines of the network, used as one.

    Like layout.Layout it turns metres into pixels, but a place is (metres, track id), with
    the track ids of the network. Where a caller only gives metres (code shared with the
    single lines), the layout in `focus` answers: set it to the line being drawn.
    """

    def __init__(self, net: JunctionNetwork, main: Layout):
        self.net, self.main = net, main
        self.layouts: dict[int, Layout] = {id(net.main): main}
        self.focus = main
        self.track_gap = main.track_gap
        self.zone_px = main.zone_px

    def of_line(self, line) -> Layout:
        return self.layouts[id(line)]

    def of_track(self, track) -> Layout:
        return self.of_line(self.net.line_of_track(track))

    def of_station(self, st) -> Layout:
        return self.of_line(self.net.line_of(st))

    def point(self, pos: float, track=None) -> tuple[float, float]:
        if isinstance(track, str):
            if track == MAIN_BACK:  # the second track of a double line, all the way beside the first
                x, y = self.main.point(pos)
                nx, ny = self.main.normal(pos)
                return x + nx * self.track_gap, y + ny * self.track_gap
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
        self.draw_loops = not net.double  # a double line draws its second track itself
        super().__init__(sim, train_skins)

    @property
    def side_layout(self) -> Layout | None:
        """The layout of the second line (None without one)."""
        side = self.net.side
        return self.layout.layouts.get(id(side)) if side is not None else None

    def _make_layout(self):
        return JunctionLayout(self.net, self.main_layout)

    def _place_lines(self, surf) -> None:
        """Choose where the other lines run, keeping them out of the water drawn on the map."""
        water = [R.gc(c) for c in (self.sea, R.SB_SEA, R.SB_SHALLOW, R.SB_RIVER)]
        width, height = surf.get_size()

        def wet(x: float, y: float) -> bool:
            if not (0 <= x < width and 0 <= y < height):
                return False
            r, g, b = surf.get_at((int(x), int(y)))[:3]
            return any(abs(r - c[0]) + abs(g - c[1]) + abs(b - c[2]) < 36 for c in water)

        self.layout.layouts = make_layouts(self.net, self.main_layout, ui.scale(), wet)

    # ------------------------------------------------------------------ background

    def _prepare_background(self) -> None:
        # The main line with its landscape, drawn (and kept) as for a line without a branch...
        sim, lay = self.sim, self.layout
        self.sim, self.layout = _MainOnly(self.net.main), self.main_layout
        try:
            super()._prepare_background()
        finally:
            self.sim, self.layout = sim, lay
        # ...and the other lines on top of a copy of it.
        surf = self.background.copy()
        self._place_lines(surf)
        tracks = []
        for line in self.net.lines()[1:]:
            lay = self.layout.of_line(line)
            tracks += [lay.main_track()] + [lay.loop_track(st) for st in line.stations if st.has_loop]
        if self.net.double:
            main = self.net.main
            tracks.append([self.layout.point(p, MAIN_BACK) for p in _steps(main.west_edge, main.east_edge, 25)])
        R.draw_rails(surf, tracks, colour=R.gc)
        self.background = surf

    # ------------------------------------------------------------------ positions

    def signal_position(self, signal: Signal) -> tuple[float, float]:
        if not isinstance(signal.track, str):  # the main line on its own, while its map is drawn
            return super().signal_position(signal)
        x, y = self.layout.point(signal.pos, signal.track)
        nx, ny = self.layout.normal(signal.pos, signal.track)
        outer = self.net.is_loop(signal.track) or signal.track == MAIN_BACK
        side = S(R.SIGNAL_SIDE) if outer else -S(R.SIGNAL_SIDE)
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
        lay, net = self.layout, self.net
        here = lay.point(sw.pos, sw.stem)
        if sw.id in net.crossovers:  # over to the other track of a double line
            ahead = sw.pos + sw.facing * CROSSOVER_M
            return [here, lay.point(ahead, sw.straight)], [here, lay.point(ahead, sw.branch)]
        joined = net.line_of_track(sw.branch)
        if joined is net.line_of_track(sw.stem):  # the points of a crossing station, as on a single line
            inner = sw.station.pos + sw.side * LOOP_HALF
            return [here, lay.point(inner, sw.straight)], [here, lay.point(inner, sw.branch)]
        # Where two lines meet: along the main line, or along the other line.
        main, other = self.main_layout, lay.of_line(joined)
        along = main._metres_to_px(sw.pos) + sw.facing * S(LEG_PX)
        leg = other._path_at(S(LEG_PX)) if sw.facing == EAST else other._path_at(other.cum[-1] - S(LEG_PX))
        return [here, main._path_at(along)], [here, leg]

    def _draw_points(self, screen, highlighted) -> None:
        for sw in self.sim.line.points:
            straight, diverging = self._legs(sw)
            active, other = (diverging, straight) if sw.diverging else (straight, diverging)
            R.draw_point_legs(screen, active, other, sw.diverging)
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
            ui.thick_line(screen, (60, 60, 64), self.layout.point(s.pos, s.track), (x, y), S(2))  # the post
            R.draw_signal(screen, x, y, s.green)
            if s.id in highlighted:
                self._pulse(screen, (x, y), highlighted[s.id])

    def _walk_back(self, train: Train, px_dists: list[float]) -> list[tuple[float, float]]:
        """As on a single line, but each part of the train is on a named track of the network
        (the front may be on the branch while the rear is still on the main line)."""
        prev = self._body_point(train, train.pos)
        done, metres = 0.0, 0.0
        out = []
        for want in px_dists:
            while done < want and metres < 6000:
                metres += 5
                pos = train.pos - train.direction * metres
                cur = self._body_point(train, pos)
                done += math.dist(prev, cur)
                prev = cur
            out.append(prev)
        return out

    def _body_point(self, train: Train, pos: float) -> tuple[float, float]:
        """A point of the train's body. Over a crossover it slides across to the other track."""
        lay = self.layout
        track = self.sim.track_at(train, pos)
        for sw, old, new in train.switches_used:
            if new == track and sw.id in self.net.crossovers:
                f = (pos - sw.pos) * sw.facing / CROSSOVER_M
                if 0 <= f <= 1:
                    (ax, ay), (bx, by) = lay.point(pos, old), lay.point(pos, new)
                    f = f * f * (3 - 2 * f)
                    return ax + (bx - ax) * f, ay + (by - ay) * f
        return lay.point(pos, track)

    def _draw_train_labels(self, screen) -> None:
        taken = [self._station_box(st) for st in self.sim.line.stations] + self._control_boxes()
        for train, ends in self._labels_to_draw:
            self.layout.focus = self.layout.of_track(train.track)  # the tag stands beside its own line
            self._draw_train_label(screen, train, ends, taken)
        self.layout.focus = self.main_layout

    _draw_next_trains = NetRenderer._draw_next_trains
    _draw_hover = NetRenderer._draw_hover


def _steps(start: float, end: float, step: float) -> list[float]:
    out, pos = [], start
    while pos < end:
        out.append(pos)
        pos += step
    return out + [end]
