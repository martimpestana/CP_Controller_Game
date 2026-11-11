"""Drawing a network with several tracks side by side (the Linha do Norte, see network.py).

It reuses everything from render.Renderer that does not depend on the shape of the line (the
top bar, the drivers' requests, the next trains, the legend) and replaces the map: the tracks,
points, signals, stations and trains.

On this map the trains are drawn to scale: a carriage is as long on the screen as it is on
the line, so a train that stops behind another one never seems to overlap it.
"""

import math

import pygame

from railgame import render as R
from railgame import skins, ui
from railgame.network import Network, Switch
from railgame.netsim import NetSimulation
from railgame.render import HEIGHT, PANEL_X, TOP_BAR, WIDTH, Renderer, clock_text, train_colour, train_kind
from railgame.track import EAST, Signal
from railgame.train import Train
from railgame.ui import S, SR

RAMP = 90.0  # metres over which a track bends from one lane into the next at a set of points
LABEL_GAP = 30  # design pixels from the outermost track to a train's label


def _smooth(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


class NetLayout:
    """Turns (metres, track) into pixels."""

    def __init__(self, line: Network):
        self.line = line
        geo = line.geo
        self.path = [(S(x), S(y)) for x, y in geo.path]
        self.cum = [0.0]
        for a, b in zip(self.path, self.path[1:]):
            self.cum.append(self.cum[-1] + math.dist(a, b))
        self.px_per_m = self.cum[-1] / (line.east_edge - line.west_edge)
        self.gap = S(geo.lane_gap)
        self._own_paths: dict[str, tuple[list, list]] = {}
        for t in line.tracks.values():
            if t.path:
                self._prepare_own_path(t)

    # ------------------------------------------------------------------ the main line

    def _along(self, d: float) -> tuple[float, float, float, float]:
        """Point and unit direction at d pixels along the main path (straight on past the ends)."""
        path, cum = self.path, self.cum
        if d <= 0:
            i = 0
        elif d >= cum[-1]:
            i = len(path) - 2
        else:
            i = next(k for k in range(len(path) - 1) if cum[k + 1] >= d)
        a, b = path[i], path[i + 1]
        length = cum[i + 1] - cum[i]
        ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
        t = d - cum[i]
        return a[0] + ux * t, a[1] + uy * t, ux, uy

    def base(self, pos: float) -> tuple[float, float]:
        x, y, _, _ = self._along((pos - self.line.west_edge) * self.px_per_m)
        return x, y

    def normal(self, pos: float) -> tuple[float, float]:
        """Unit vector to the left of a northbound train (inland, away from the river)."""
        # Average the direction over a little stretch so the tracks bend smoothly at corners.
        d = (pos - self.line.west_edge) * self.px_per_m
        _, _, ux0, uy0 = self._along(d - S(14))
        _, _, ux1, uy1 = self._along(d + S(14))
        ux, uy = ux0 + ux1, uy0 + uy1
        length = math.hypot(ux, uy) or 1.0
        return uy / length, -ux / length

    def at_lane(self, pos: float, lane: float) -> tuple[float, float]:
        x, y = self.base(pos)
        nx, ny = self.normal(pos)
        return x + nx * lane * self.gap, y + ny * lane * self.gap

    # ------------------------------------------------------------------ tracks

    def lane(self, track_id: str, pos: float) -> float:
        """The lane of a track here, bending towards the stem track near the points where it
        starts or ends."""
        t = self.line.tracks[track_id]
        lane = t.lane
        for sw in self.line.points:
            if track_id == sw.stem or track_id not in (sw.straight, sw.branch):
                continue
            if abs(t.start - sw.pos) > 1e-6 and abs(t.end - sw.pos) > 1e-6:
                continue  # the track runs on past these points (a crossover)
            f = (pos - sw.pos) * sw.facing / RAMP
            if 0 <= f <= 1:
                stem = self.line.tracks[sw.stem].lane
                lane = stem + (lane - stem) * _smooth(f)
        return lane

    def _prepare_own_path(self, t) -> None:
        # The Cintura line: its own drawn line, which ends where it meets the main line.
        junction = next(sw for sw in self.line.points if t.id in (sw.straight, sw.branch))
        stem = self.line.tracks[junction.stem]
        pts = [(S(x), S(y)) for x, y in t.path]
        end = self.at_lane(junction.pos + junction.facing * RAMP * 1.5, stem.lane)
        pts.append(end)
        cum = [0.0]
        for a, b in zip(pts, pts[1:]):
            cum.append(cum[-1] + math.dist(a, b))
        self._own_paths[t.id] = (pts, cum)

    def point(self, pos: float, track_id: str) -> tuple[float, float]:
        t = self.line.tracks[track_id]
        if t.id in self._own_paths:
            pts, cum = self._own_paths[t.id]
            f = (pos - t.start) / (t.end - t.start)
            d = max(-S(60), min(cum[-1], f * cum[-1]))
            for i in range(len(pts) - 1):
                if cum[i + 1] >= d or i == len(pts) - 2:
                    a, b = pts[i], pts[i + 1]
                    seg = (cum[i + 1] - cum[i]) or 1.0
                    k = (d - cum[i]) / seg
                    return a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k
        return self.at_lane(pos, self.lane(track_id, pos))

    def polyline(self, track_id: str, step: float = 20.0) -> list[tuple[float, float]]:
        t = self.line.tracks[track_id]
        start, end = t.start, t.end
        if t.open_start and not t.path:
            start -= 400
        if t.open_end:
            end += 400
        pts, pos = [], start
        while pos < end:
            pts.append(self.point(pos, track_id))
            pos += step
        pts.append(self.point(end, track_id))
        return pts

    def leg(self, sw: Switch, to: str) -> list[tuple[float, float]]:
        """The short piece of track from the points onto one of their two tracks."""
        stem_lane = self.line.tracks[sw.stem].lane
        to_lane = self.lane(to, sw.pos + sw.facing * RAMP)
        if self.line.tracks[to].path:
            return [self.point(sw.pos, sw.stem), self.point(self.line.tracks[to].end_in(-sw.facing), to)]
        pts = []
        for i in range(7):
            f = i / 6
            pos = sw.pos + sw.facing * RAMP * f
            pts.append(self.at_lane(pos, stem_lane + (to_lane - stem_lane) * _smooth(f)))
        return pts


class NetRenderer(Renderer):
    def __init__(self, sim: NetSimulation, train_skins: dict[str, str] | None = None):
        self.sim = sim
        self.skins = train_skins or dict(skins.DEFAULT_SKINS)
        self.layout = NetLayout(sim.line)
        self.gap = self.layout.gap
        f = ui.font
        self.f_small = f(13)
        self.f_text = f(15)
        self.f_bold = f(15, bold=True)
        self.f_title = f(19, bold=True)
        self.f_big = f(34, bold=True)
        self.speed_buttons = []
        self.restart_button = None
        self.menu_button = None
        self.request_buttons = []
        self.train_boxes = []
        self._prepare_background()

    # ------------------------------------------------------------------ positions used for clicks

    def signal_position(self, signal: Signal) -> tuple[float, float]:
        return self.layout.point(signal.pos, signal.track)

    def point_position(self, point: Switch) -> tuple[float, float]:
        return self.layout.point(point.pos, point.stem)

    # ------------------------------------------------------------------ background

    def _prepare_background(self) -> None:
        line, lay = self.sim.line, self.layout
        surf = pygame.Surface((S(WIDTH), S(HEIGHT)))
        surf.fill(R.BG)
        storybook_line = line.geo.scenery.endswith("storybook")
        self.storybook = storybook_line and R.MAP_MODE in ("day", "night")
        self.night = self.storybook and R.MAP_MODE == "night"
        if self.storybook:
            R.__dict__.update(R.SB_NIGHT if self.night else R.SB_DAY)
        self.land = R.SB_LAND if self.storybook else R.LAND
        self.sea = R.SB_SEA if self.storybook else R.SEA
        self.wave_marks, self.windows, self.lamp = [], [], None
        self.windmills, self.turbines = [], []
        self.mill_time = self.sea_time = 0.0
        self._last_tick = None
        self.animated = []  # (kind, data): things the Lisbon scenery moves every frame
        pygame.draw.rect(surf, self.land, SR(0, TOP_BAR, PANEL_X, HEIGHT - TOP_BAR))
        if self.storybook:
            from railgame import scenery_lisboa

            scenery_lisboa.draw(self, surf)
        else:
            self._plain_river(surf)
        self._draw_platforms(surf)
        edge = R.SB_TRACK_EDGE if self.storybook else None
        for t in line.tracks.values():
            pts = lay.polyline(t.id)
            if edge:
                ui.thick_lines(surf, edge, pts, S(7))
        for t in line.tracks.values():
            ui.thick_lines(surf, R.TRACK, lay.polyline(t.id), S(3))
        for t in line.tracks.values():
            if not t.open_start and not t.open_end and t.start == line.west_edge:
                # Buffer stops at the end of the terminus platforms.
                x, y = lay.point(t.start, t.id)
                nx, ny = lay.normal(t.start)
                ui.thick_line(surf, (200, 70, 60), (x - nx * S(5), y - ny * S(5)), (x + nx * S(5), y + ny * S(5)), S(3))
        self._edge_labels(surf)
        self.background = surf

    def _plain_river(self, surf) -> None:
        """The Tejo, on the river side of the line (the simple map of the other themes)."""
        lay, line = self.layout, self.sim.line
        shore = []
        pos = line.west_edge - 1500
        while pos <= line.east_edge + 1500:
            x, y = lay.base(pos)
            nx, ny = lay.normal(pos)
            shore.append((x - nx * S(70), y - ny * S(70)))
            pos += 100
        right, bottom = S(PANEL_X), S(HEIGHT)
        polygon = shore + [(right, shore[-1][1]), (right, bottom), (shore[0][0], bottom)]
        pygame.draw.polygon(surf, self.sea, polygon)
        label = self.f_small.render(line.geo.water_label, True, R.OCEAN_TEXT)
        surf.blit(label, label.get_rect(center=(S(700), S(560))))

    def _draw_platforms(self, surf) -> None:
        """Platforms: light strips beside every track that has one."""
        lay, line = self.layout, self.sim.line
        colour = (196, 186, 166) if self.storybook else (70, 82, 96)
        for code, tracks in line.platforms.items():
            st = line.station(code)
            for track in tracks:
                t = line.tracks[track]
                if t.start == line.west_edge:
                    low, high = t.start + 10, t.end - RAMP - 20
                else:
                    low, high = st.pos - 160, st.pos + 160
                lane = t.lane
                side = 0.5 if lane > 0 else -0.5
                pts = [lay.at_lane(p, lane + side) for p in (low, (low + high) / 2, high)]
                ui.thick_lines(surf, colour, pts, S(5))

    def _edge_labels(self, surf) -> None:
        lay, line, geo = self.layout, self.sim.line, self.sim.line.geo
        x, y = lay.base(line.east_edge)
        self._label(surf, f"{geo.end_label} ↗", (x - S(80), y - S(34)), small=True)
        for t in line.tracks.values():
            name = geo.labels.get(t.id)
            if name and t.path:
                px, py = lay.point(t.start, t.id)
                self._label(surf, f"↑ {name}", (px + S(52), py + S(14)), small=True)

    def _label(self, surf, text, centre, small=False) -> None:
        fnt = self.f_small if small else self.f_bold
        if self.storybook:
            self._outlined(surf, fnt, text, R.WHITE, centre)
            return
        label = fnt.render(text, True, R.MAP_MUTED if small else R.WHITE)
        surf.blit(label, label.get_rect(center=centre))

    # ------------------------------------------------------------------ every frame

    def draw(self, screen, info, speed, hover, toast) -> None:
        self.first_level = getattr(info, "number", None) == 1
        screen.blit(self.background, (0, 0))
        if screen.get_flags() & pygame.SRCALPHA:
            screen.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MAX)
        if self.storybook:
            from railgame import scenery_lisboa

            scenery_lisboa.animate(self, screen, speed)
        highlighted = self._highlighted_targets(hover)
        self._draw_points(screen, highlighted)
        self._draw_trains(screen)
        self._draw_signals(screen, highlighted)
        self._draw_stations(screen)
        self._draw_top_bar(screen, info, speed)
        self._draw_requests(screen, hover)
        self._draw_next_trains(screen)
        self._draw_legend(screen)
        self._draw_hover(screen, hover)
        if toast:
            self._draw_toast(screen, toast)

    def _draw_points(self, screen, highlighted) -> None:
        lay = self.layout
        for sw in self.sim.line.points:
            active = sw.track
            other = sw.straight if sw.diverging else sw.branch
            ui.thick_lines(screen, R.TRACK_DIM, lay.leg(sw, other), S(3))
            ui.thick_lines(screen, R.YELLOW if sw.diverging else R.WHITE, lay.leg(sw, active), S(3))
        for sw in self.sim.line.points:
            x, y = self.point_position(sw)
            rect = pygame.Rect(0, 0, S(11), S(11))
            rect.center = (int(x), int(y))
            pygame.draw.rect(screen, R.YELLOW if sw.diverging else R.WHITE, rect, border_radius=S(2))
            pygame.draw.rect(screen, R.BG, rect, max(1, S(2)), border_radius=S(2))
            if sw.id in highlighted:
                self._pulse(screen, (x, y), highlighted[sw.id])

    def _draw_signals(self, screen, highlighted) -> None:
        for s in self.sim.line.signals:
            x, y = self.signal_position(s)
            ui.circle(screen, (8, 8, 8), (x, y), S(7))
            ui.circle(screen, R.GREEN if s.green else R.RED, (x, y), S(5))
            if s.id in highlighted:
                self._pulse(screen, (x, y), highlighted[s.id])

    def train_point(self, train: Train, pos: float) -> tuple[float, float]:
        """A point of the train's body, following the track that part of it is on. On a
        crossover the train slides across from one track to the other."""
        lay = self.layout
        track = self.sim.track_at(train, pos)
        for sw, old, new in train.switches_used:
            if new != track or self.sim.line.tracks[new].path:
                continue
            f = (pos - sw.pos) * sw.facing / RAMP
            t = self.sim.line.tracks[new]
            if 0 <= f <= 1 and abs(t.start - sw.pos) > 1e-6 and abs(t.end - sw.pos) > 1e-6:
                a = self.sim.line.tracks[old].lane
                lane = a + (lay.lane(new, pos) - a) * _smooth(f)
                return lay.at_lane(pos, lane)
        return lay.point(pos, track)

    def _draw_trains(self, screen) -> None:
        crashed = self.sim.crash or ()
        self.train_boxes = []
        self._placed = [self._station_label_rect(st) for st in self.sim.line.stations]
        t = pygame.time.get_ticks() / 1000
        ppm = self.layout.px_per_m
        for train in self.sim.trains:
            if train.state != "running":
                continue
            stripe = R.RED if train in crashed else train_colour(train)
            kind = train_kind(train)
            cars = skins.CARS.get(kind, 2)
            skin = self.skins.get(kind, "real")
            pitch = train.length / cars  # metres per carriage, coupling included
            gap = S(2) / ppm  # about two pixels between carriages
            scale = ui.scale()
            k = max(0.45 * scale, min(scale, (pitch * ppm - S(2)) / 22))
            d = train.direction
            ends = []
            for i in range(cars):
                front = train.pos - d * i * pitch
                back = front - d * (pitch - gap)
                ends.append((self.train_point(train, front), self.train_point(train, back)))
            for i in reversed(range(cars)):
                a, b = ends[i]
                if i < cars - 1:
                    pygame.draw.line(screen, R.INK, b, ends[i + 1][0], max(1, S(2)))
                skins.draw_car(screen, a, b, kind, skin, stripe, i, cars, k, t)
            self._draw_train_label(screen, train, ends)

    def _draw_train_label(self, screen, train, ends) -> None:
        head, tail = ends[0][0], ends[-1][1]
        mid_pos = train.pos - train.direction * train.length / 2
        nx, ny = self.layout.normal(mid_pos)
        side = 1 if train.direction == EAST else -1
        lane = self.layout.lane(train.track, train.pos) if not self.sim.line.tracks[train.track].path else 0
        reach = max(2.0, abs(lane) + 0.6) * self.gap + S(LABEL_GAP)
        mid = ((head[0] + tail[0]) / 2, (head[1] + tail[1]) / 2)
        lx, ly = mid[0] + nx * reach * side, mid[1] + ny * reach * side
        colour = train_colour(train)
        chip = self.f_bold.render(train_kind(train), True, R.BG)
        number = self.f_small.render(train.name.split()[-1], True, R.WHITE)
        delay = train.delay(self.sim.time)
        tag = self.f_small.render("on time" if delay < 30 else f"+{delay / 60:.0f} min", True, R.GREEN if delay < 30 else R.RED)
        arrow = self.f_bold.render("↗" if train.direction == EAST else "↙", True, colour)
        width = chip.get_width() + number.get_width() + tag.get_width() + arrow.get_width() + S(34)
        box = pygame.Rect(0, 0, width, S(22))
        area = SR(4, TOP_BAR + 4, PANEL_X - 8, HEIGHT - TOP_BAR - 8)
        for step in range(8):  # move it further out until it no longer covers another label
            box.center = (int(lx + nx * side * step * S(16)), int(ly + ny * side * step * S(16)))
            box.clamp_ip(area)
            if not any(box.colliderect(other.inflate(S(4), S(4))) for other in self._placed):
                break
        self._placed.append(box)
        pygame.draw.line(screen, colour, mid, box.center, max(1, S(1)))
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
        self.train_boxes.append((body.inflate(S(8), S(8)), train))

    def _station_place(self, st):
        """Where a station's dot and name go: beside its platforms, inland (the terminus: on
        the river side, where there is room)."""
        lay, line = self.layout, self.sim.line
        lanes = [line.tracks[t].lane for t in line.platforms.get(st.code, ())]
        if st.code == line.terminus:
            pos, lane, side = 200, min(lanes) - 1.6, -1
        else:
            pos, lane, side = st.pos, max(lanes) + 1.6, 1
        x, y = lay.at_lane(pos, lane)
        nx, ny = lay.normal(pos)
        return (x, y), (x + nx * side * S(22), y + ny * side * S(22))

    def _station_label_rect(self, st) -> pygame.Rect:
        _, centre = self._station_place(st)
        w, h = self.f_bold.size(st.name)
        return pygame.Rect(0, 0, w + S(8), h + S(4)).move(centre[0] - w / 2 - S(4), centre[1] - h / 2 - S(2))

    def _draw_stations(self, screen) -> None:
        for st in self.sim.line.stations:
            dot, centre = self._station_place(st)
            ui.circle(screen, R.BG, dot, S(8))
            ui.circle(screen, R.WHITE, dot, S(6))
            self._label(screen, st.name, centre)

    def _draw_next_trains(self, screen) -> None:
        x0, y = PANEL_X + 18, R.REQUESTS_BOTTOM + 10
        right = WIDTH - 18
        pygame.draw.line(screen, R.CARD, (S(PANEL_X + 16), S(y - 8)), (S(right), S(y - 8)), max(1, S(1)))
        screen.blit(self.f_bold.render("Next trains", True, R.WHITE), (S(x0), S(y)))
        waiting = sorted((t for t in self.sim.trains if t.state == "waiting"), key=lambda t: t.enter_time)
        y += 26
        if not waiting:
            screen.blit(self.f_small.render("No more trains to come.", True, R.MUTED), (S(x0), S(y)))
            return
        for train in waiting[:5]:
            colour = train_colour(train)
            screen.blit(self.f_text.render(clock_text(train.enter_time), True, R.TEXT), (S(x0), S(y)))
            chip = SR(x0 + 56, y + 1, 30, 18)
            pygame.draw.rect(screen, colour, chip, border_radius=S(4))
            text = self.f_bold.render(train_kind(train), True, R.BG)
            screen.blit(text, text.get_rect(center=chip.center))
            screen.blit(self.f_text.render(train.name.split()[-1], True, R.TEXT), (S(x0 + 92), S(y)))
            side = f"to {train.destination}"
            screen.blit(self.f_small.render(side, True, R.MUTED), (S(x0 + 150), S(y + 2)))
            minutes = (train.enter_time - self.sim.time) / 60
            when = self.f_bold.render("now" if minutes < 0.5 else f"{minutes:.0f} min", True, R.YELLOW if minutes < 3 else R.TEXT)
            screen.blit(when, (S(right) - when.get_width(), S(y)))
            y += 24

    def _draw_legend(self, screen) -> None:
        y = HEIGHT - 135
        screen.blit(self.f_bold.render("How to play", True, R.WHITE), (S(PANEL_X + 18), S(y)))
        items = [
            ("signal", "Click a signal: red ↔ green"),
            ("point", "Click points: white straight, yellow the other way"),
            ("ring", "Fast trains: keep them off the slow tracks"),
            ("keys", "Space pause · 1/2/3/4 speed · R restart · Esc levels"),
        ]
        for i, (kind, text) in enumerate(items):
            cy = y + 32 + i * 24
            cx = PANEL_X + 30
            if kind == "signal":
                ui.circle(screen, R.GREEN, (S(cx - 6), S(cy)), S(6))
                ui.circle(screen, R.RED, (S(cx + 8), S(cy)), S(6))
            elif kind == "point":
                pygame.draw.rect(screen, R.YELLOW, SR(cx - 6, cy - 6, 12, 12), border_radius=S(2))
            elif kind == "ring":
                ui.ring(screen, R.EAST_COLOUR, (S(cx), S(cy)), S(8), S(2))
            screen.blit(self.f_small.render(text, True, R.TEXT), (S(cx + 22), S(cy - 9)))

    def _draw_hover(self, screen, hover) -> None:
        line = self.sim.line
        obj = self.object_at(hover)
        if obj is None:
            train = self.train_at(hover)
            if train is None:
                return
            stop = train.next_stop()
            where = f"next stop {stop.station.name} {clock_text(stop.arrive)}" if stop else "leaving the map"
            text = f"{train.name} to {train.destination} · {where} · on {line.track_name(train.track)}"
        elif isinstance(obj, Signal):
            state = "green" if obj.green else "red"
            text = f"Signal {obj.id} · {obj.station.name}, {line.track_name(obj.track)} · {state}"
        else:
            text = f"Points {obj.id} · {obj.station.name} · set to {line.track_name(obj.track)}"
        label = self.f_small.render(text, True, R.WHITE)
        box = label.get_rect(topleft=(hover[0] + S(14), hover[1] + S(14))).inflate(S(12), S(8))
        if box.right > S(PANEL_X):
            box.right = hover[0] - S(10)
        pygame.draw.rect(screen, (0, 0, 0), box, border_radius=S(5))
        screen.blit(label, label.get_rect(center=box.center))
