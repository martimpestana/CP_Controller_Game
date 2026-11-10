"""Everything that is drawn on the screen during a level.

The line is shown as a schematic control panel (see schematic.py): straight track, one box per
crossing station, arrow signals and points that light up the route they are set for. Below it
are the drivers' requests (each with a "Do it" button) and the list of trains still to come.
"""

import math

import pygame

from railgame import geography, ui
from railgame.schematic import Schematic
from railgame.simulation import Request, Simulation
from railgame.track import EAST, LOOP_HALF, Point, Signal
from railgame.train import Train
from railgame.ui import S, SR, font

WIDTH, HEIGHT = 1280, 720
TOP_BAR = 56

BG = (15, 21, 30)
PANEL = (24, 32, 44)
MAP_BG = (19, 27, 38)
STATION_BG = (25, 36, 50)
PLATFORM = (54, 66, 82)
TRACK = (196, 204, 214)
TRACK_DIM = (70, 80, 94)
WHITE = (248, 248, 248)
TEXT = (226, 232, 240)
MUTED = (140, 152, 168)
GREEN = (60, 220, 120)
RED = (238, 72, 62)
YELLOW = (250, 204, 70)
EAST_COLOUR = (84, 156, 255)
WEST_COLOUR = (255, 152, 64)
CARD = (34, 45, 60)
CARD_HOVER = (44, 60, 82)
BUTTON = (52, 70, 92)
BUTTON_ON = (66, 120, 210)
INK = (8, 10, 14)
TRAIN_BODY = (232, 236, 242)
TRAIN_ROOF = (150, 160, 175)
GLASS = (40, 58, 84)
GLASS_LIGHT = (120, 170, 220)
SEA = (17, 42, 66)
SEA_LINE = (38, 72, 104)
LAGOON = (22, 52, 64)
SAND = (112, 102, 78)
LAND = (44, 58, 74)
LAND_EDGE = (104, 122, 146)

# Design-pixel layout of the screen.
MAP_RECT = (12, 68, WIDTH - 24, 380)
TRACK_Y = 360  # track height at Faro; the line climbs towards Tavira
TRACK_GAP = 50
REQUESTS_RECT = (12, 460, 820, 248)
NEXT_RECT = (844, 460, WIDTH - 856, 248)

CAR_PX, CAR_GAP_PX = 24, 3  # carriage length and coupling gap, in design pixels

# Speed buttons in the top bar: (simulated seconds per real second, label).
SPEEDS = ((0, "Pause"), (1, "1x"), (5, "5x"), (10, "10x"), (20, "20x"))


def clock_text(seconds: float, with_seconds: bool = False) -> str:
    seconds = int(seconds) % (24 * 3600)
    text = f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}"
    return text + f":{seconds % 60:02d}" if with_seconds else text


def minutes_text(seconds: float) -> str:
    return f"{seconds / 60:.1f} min"


def train_colour(train: Train) -> tuple[int, int, int]:
    return EAST_COLOUR if train.direction == EAST else WEST_COLOUR


def train_kind(train: Train) -> str:
    return train.name.split()[0]


def _sp(p: tuple[float, float]) -> tuple[float, float]:
    """Design pixels to screen pixels (keeps fractions, for smooth drawing)."""
    k = ui.scale()
    return (p[0] * k, p[1] * k)


class Renderer:
    def __init__(self, sim: Simulation):
        self.sim = sim
        left = MAP_RECT[0] + 18
        right = MAP_RECT[0] + MAP_RECT[2] - 18
        self.map = Schematic(sim.line, left, right, TRACK_Y, TRACK_GAP)
        self.f_small = font(12)
        self.f_text = font(14)
        self.f_bold = font(14, bold=True)
        self.f_title = font(17, bold=True)
        self.f_big = font(20, bold=True)
        self.speed_buttons: list[tuple[pygame.Rect, int]] = []
        self.restart_button: pygame.Rect | None = None
        self.request_buttons: list[tuple[pygame.Rect, Request]] = []
        self.request_cards: list[tuple[pygame.Rect, Request]] = []
        self.train_boxes: list[tuple[pygame.Rect, Train]] = []
        self._map_bg: tuple[float, pygame.Surface] | None = None

    # ------------------------------------------------------------------ positions used for clicks

    def signal_position(self, signal: Signal) -> tuple[float, float]:
        """Screen position of a signal head. Eastbound signals sit below their track,
        westbound ones above it."""
        x, y = self.map.point(signal.pos, signal.track or 1)
        y += 18 if signal.direction == EAST else -18
        return _sp((x, y))

    def point_position(self, point: Point) -> tuple[float, float]:
        return _sp(self.map.point(point.pos))

    def object_at(self, pos: tuple[int, int]) -> Signal | Point | None:
        best, best_dist = None, S(14)
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

    # ------------------------------------------------------------------ drawing a frame

    def draw(self, screen: pygame.Surface, info, speed: int, hover: tuple[int, int], toast: str | None) -> None:
        screen.fill(BG)
        self._draw_top_bar(screen, info, speed)
        self._draw_map_background(screen)
        hovered_request = next((r for rect, r in self.request_cards if rect.collidepoint(hover)), None)
        highlighted = self._highlighted_targets()
        self._draw_track(screen)
        self._draw_points(screen, highlighted, hovered_request)
        self._draw_signals(screen, highlighted, hovered_request)
        self._draw_halts(screen)
        self._draw_trains(screen)
        self._draw_legend(screen)
        self._draw_requests(screen, hover)
        self._draw_next_trains(screen)
        self._draw_hover(screen, hover)
        if toast:
            text = self.f_text.render(toast, True, WHITE)
            box = text.get_rect(center=(S(WIDTH // 2), S(TOP_BAR + 34))).inflate(S(24), S(14))
            pygame.draw.rect(screen, (110, 44, 44), box, border_radius=S(8))
            screen.blit(text, text.get_rect(center=box.center))

    def _text(self, screen, text, pos, f, colour, anchor="topleft") -> pygame.Rect:
        surf = f.render(text, True, colour)
        rect = surf.get_rect(**{anchor: pos})
        screen.blit(surf, rect)
        return rect

    def _highlighted_targets(self) -> dict[str, tuple[int, int, int]]:
        targets = {}
        for request in self.sim.requests.values():
            targets[request.target_id] = train_colour(request.train)
        return targets

    def _pulse(self, screen, pos, colour, strong=False) -> None:
        t = pygame.time.get_ticks() / 1000
        radius = S((17 if strong else 14) + 4 * (0.5 + 0.5 * math.sin(t * 6)))
        ui.ring(screen, WHITE if strong else colour, pos, radius, S(3 if strong else 2))

    # ------------------------------------------------------------------ top bar

    def _draw_top_bar(self, screen, info, speed: int) -> None:
        sim = self.sim
        pygame.draw.rect(screen, PANEL, SR(0, 0, WIDTH, TOP_BAR))
        self._text(screen, f"Level {info.number} · {info.title}", (S(18), S(16)), self.f_big, WHITE)
        self._text(screen, clock_text(sim.time, True), (S(310), S(16)), self.f_big, WHITE)
        x = S(420)
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

        average = sim.average_delay()
        limit = sim.max_average_delay
        colour = GREEN if average < limit * 0.5 else YELLOW if average <= limit else RED
        r = self._text(screen, f"Average delay {minutes_text(average)}", (S(840), S(19)), self.f_bold, colour)
        self._text(screen, f"(limit {limit / 60:.0f} min)", (r.right + S(10), S(19)), self.f_text, MUTED)
        done = sum(1 for t in sim.trains if t.state == "finished")
        self._text(screen, f"Trains done {done}/{len(sim.trains)}", (S(WIDTH - 18), S(19)), self.f_text, MUTED, "topright")

    # ------------------------------------------------------------------ the schematic map

    def _draw_map_background(self, screen) -> None:
        line, m = self.sim.line, self.map
        if self._map_bg is None or self._map_bg[0] != ui.scale():
            self._map_bg = (ui.scale(), self._make_map_background())
        screen.blit(self._map_bg[1], (S(MAP_RECT[0]), S(MAP_RECT[1])))
        first, last = line.stations[0].name, line.stations[-1].name
        self._text(screen, f"{line.name} · {first} – {last}", (S(28), S(80)), self.f_title, TEXT)
        for st in line.stations:
            if not st.has_loop:
                continue
            box = m.station_box(st)
            pygame.draw.rect(screen, STATION_BG, SR(*box), border_radius=S(10))
            xl, xr = m.x(st.pos - LOOP_HALF), m.x(st.pos + LOOP_HALF)
            ty = m.station_y(st)
            for y in (ty - TRACK_GAP - 12, ty + 8):  # platforms
                pygame.draw.rect(screen, PLATFORM, SR(xl + 6, y, xr - xl - 12, 6), border_radius=S(3))
            self._text(screen, st.name, (S(box[0] + box[2] / 2), S(box[1] + 10)), self.f_title, WHITE, "midtop")
            self._text(screen, "1", (S(xl + 10), S(ty + 16)), self.f_small, MUTED)
            self._text(screen, "2", (S(xl + 10), S(ty - TRACK_GAP - 28)), self.f_small, MUTED)
        west_y, east_y = m.y(line.west_edge), m.y(line.east_edge)
        self._text(screen, "← Loulé", (S(20), S(west_y - 34)), self.f_small, MUTED)
        self._text(screen, "V.R.S.A. →", (S(WIDTH - 20), S(east_y - 34)), self.f_small, MUTED, "topright")

    def _make_map_background(self) -> pygame.Surface:
        """The panel behind the track: land, the Ria Formosa with its sand islands, the
        Atlantic, and a small map of Portugal showing where the line is. Drawn once."""
        mx, my, mw, mh = MAP_RECT
        surf = pygame.Surface((S(mw), S(mh)), pygame.SRCALPHA)
        surf.fill(MAP_BG)

        def P(x, y):  # design position on the screen -> position on this surface
            return (S(x - mx), S(y - my))

        bottom = my + mh
        m = self.map
        xs = list(range(mx, mx + mw + 9, 8))

        def smooth(x, reach=70):  # the track's height, smoothed so the coast has no steps
            samples = [m.base_y(x + d) for d in range(-reach, reach + 1, 10)]
            return sum(samples) / len(samples)

        coast = [(x, smooth(x) + 52 + 2.5 * math.sin(x / 47 + 1)) for x in xs]
        islands_y = [(x, y + 18 + 3 * math.sin(x / 90)) for x, y in coast]
        # Land is the panel itself; the lagoon starts at the shore and the ocean past the islands.
        pygame.draw.polygon(surf, LAGOON, [P(*c) for c in coast] + [P(mx + mw + 8, bottom), P(mx, bottom)])
        pygame.draw.polygon(surf, SEA, [P(x, y + 4) for x, y in islands_y] + [P(mx + mw + 8, bottom), P(mx, bottom)])
        # Sand islands of the Ria Formosa, broken by the inlets (barras).
        inlets = [60, 300, 520, 640, 860, 1000, 1180]
        for a, b in zip(inlets, inlets[1:]):
            pts = [(x, y) for x, y in islands_y if a + 14 <= x <= b - 14]
            if len(pts) > 1:
                ui.thick_lines(surf, SAND, [P(x, y + 2) for x, y in pts], S(5))
        # A few waves out at sea, kept below the islands.
        for wx, dy in [(560, 30), (760, 26), (880, 52), (980, 34), (700, 58), (1060, 66)]:
            wy = smooth(wx) + 52 + 18 + dy
            if wy < bottom - 6:
                arc = [P(wx + dx, wy + 2 * math.sin(dx / 4)) for dx in range(0, 26, 2)]
                ui.thick_lines(surf, SEA_LINE, arc, S(2))
        cap = self.f_small.render("Ria Formosa", True, (88, 130, 140))
        surf.blit(cap, cap.get_rect(midleft=P(530, smooth(530) + 52 + 10)))
        cap = self.f_small.render("O c e a n o   A t l â n t i c o", True, (70, 104, 136))
        surf.blit(cap, cap.get_rect(center=P(860, smooth(860) + 52 + 44)))

        # Inset: Portugal, with the line we are playing on, out in the ocean off Tavira.
        ix, iw, ih = WIDTH - 124, 106, 114
        iy = bottom - ih - 6
        pygame.draw.rect(surf, (13, 33, 54), (*P(ix, iy), S(iw), S(ih)), border_radius=S(8))
        pygame.draw.rect(surf, SEA_LINE, (*P(ix, iy), S(iw), S(ih)), max(1, S(1)), border_radius=S(8))
        to_screen = geography.fit(geography.PORTUGAL, (ix + 40, iy + 6, iw - 46, ih - 12))
        outline = [P(*to_screen(lat, lon)) for lat, lon in geography.PORTUGAL]
        pygame.draw.polygon(surf, LAND, outline)
        pygame.draw.lines(surf, LAND_EDGE, True, outline, max(1, S(1)))
        here = [P(*to_screen(lat, lon)) for lat, lon in geography.ALGARVE_LINE]
        ui.thick_lines(surf, YELLOW, here, S(3))
        for pt in (here[0], here[-1]):
            ui.circle(surf, YELLOW, pt, S(2.5))
        cap = self.f_small.render("Portugal", True, MUTED)
        surf.blit(cap, cap.get_rect(bottomleft=P(ix + 6, iy + ih - 4)))

        # Round the corners like the other panels.
        mask = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=S(12))
        surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        return surf

    def _draw_track(self, screen) -> None:
        line, m = self.sim.line, self.map
        ui.thick_lines(screen, TRACK, [_sp(p) for p in m.profile], S(4))
        for st in line.stations:
            if st.has_loop:
                pts = [_sp(m.point(pos, 2)) for pos in range(int(st.pos - 600), int(st.pos + 601), 20)]
                ui.thick_lines(screen, TRACK, pts, S(4))

    def _draw_points(self, screen, highlighted, hovered_request) -> None:
        m = self.map
        for p in self.sim.line.points:
            inward = -p.side  # from the points towards the middle of the station
            start = _sp(m.point(p.pos))
            straight = _sp(m.point(p.pos + inward * 160, 1))
            branch = _sp(m.point(p.pos + inward * 160, 2))
            active, other = (branch, straight) if p.diverging else (straight, branch)
            colour = YELLOW if p.diverging else WHITE
            ui.thick_line(screen, TRACK_DIM, start, other, S(6))
            ui.thick_line(screen, colour, start, active, S(6))
            ui.circle(screen, BG, start, S(9))
            ui.circle(screen, colour, start, S(6))
            if p.id in highlighted:
                strong = hovered_request is not None and hovered_request.target_id == p.id
                self._pulse(screen, start, highlighted[p.id], strong)

    def _draw_signals(self, screen, highlighted, hovered_request) -> None:
        m = self.map
        for s in self.sim.line.signals:
            base = _sp(m.point(s.pos, s.track or 1))
            x, y = self.signal_position(s)
            ui.thick_line(screen, (90, 100, 115), base, (x, y), S(2))
            body = pygame.Rect(0, 0, S(20), S(14))
            body.center = (int(x), int(y))
            pygame.draw.rect(screen, (12, 16, 22), body, border_radius=S(4))
            d = s.direction
            tip = (x + d * S(7), y)
            back = x - d * S(5)
            pygame.draw.polygon(screen, GREEN if s.green else RED, [tip, (back, y - S(5)), (back, y + S(5))])
            if s.id in highlighted:
                strong = hovered_request is not None and hovered_request.target_id == s.id
                self._pulse(screen, (x, y), highlighted[s.id], strong)

    def _draw_halts(self, screen) -> None:
        m = self.map
        for st in self.sim.line.stations:
            if st.has_loop:
                continue
            x, y = _sp(m.point(st.pos))
            ui.circle(screen, BG, (x, y), S(8))
            ui.circle(screen, MUTED, (x, y), S(5))
            self._text(screen, st.name, (int(x), int(y - S(14))), self.f_small, MUTED, "midbottom")

    # ------------------------------------------------------------------ trains

    def _walk_back(self, train: Train, px_dist: float) -> tuple[float, float]:
        """The point on the drawn track px_dist design pixels behind the front of the train."""
        m = self.map
        prev = m.point(train.pos, train.track_at(train.pos))
        done, metres = 0.0, 0.0
        while done < px_dist and metres < 6000:
            metres += 4
            pos = train.pos - train.direction * metres
            cur = m.point(pos, train.track_at(pos))
            done += math.dist(prev, cur)
            prev = cur
        return prev

    def _draw_car(self, screen, a, b, stripe, front: bool, rear: bool) -> None:
        """One carriage from a (its front end) to b (its rear end), in screen pixels."""
        ux, uy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(ux, uy) or 1.0
        ux, uy = ux / length, uy / length
        nx, ny = -uy, ux
        if ny < 0 or (ny == 0 and nx < 0):
            nx, ny = -nx, -ny  # make n point down the screen, so the roof is always on top
        k = ui.scale()

        def band(o0, o1, l0, l1, colour):
            o0, o1, l0, l1 = o0 * k, o1 * k, l0 * k, l1 * k
            pygame.draw.polygon(
                screen,
                colour,
                [
                    (a[0] + ux * l0 + nx * o0, a[1] + uy * l0 + ny * o0),
                    (a[0] + ux * l1 + nx * o0, a[1] + uy * l1 + ny * o0),
                    (a[0] + ux * l1 + nx * o1, a[1] + uy * l1 + ny * o1),
                    (a[0] + ux * l0 + nx * o1, a[1] + uy * l0 + ny * o1),
                ],
            )

        car_len = length / k
        band(-8, 8, -0.5, car_len + 0.5, INK)
        band(-6.5, 6.5, 0, car_len, TRAIN_BODY)
        band(-6.5, -4.5, 1, car_len - 1, TRAIN_ROOF)
        band(3, 6.5, 0.5, car_len - 0.5, stripe)
        start, end = (7.5 if front else 3.0), car_len - (7.5 if rear else 3.0)
        pos = start
        while pos + 3 <= end:
            band(-3.5, 1, pos, pos + 3, GLASS)
            pos += 5
        if front:
            band(-4.5, 1.5, 1, 5.5, GLASS_LIGHT)
            ui.circle(screen, (255, 236, 150), (a[0] + ux * 1.5 * k + nx * 4.5 * k, a[1] + uy * 1.5 * k + ny * 4.5 * k), 1.6 * k)
        if rear:
            band(-4.5, 1.5, car_len - 5.5, car_len - 1, GLASS)
            ui.circle(screen, (230, 60, 50), (b[0] - ux * 1.5 * k + nx * 4.5 * k, b[1] - uy * 1.5 * k + ny * 4.5 * k), 1.4 * k)

    def _draw_trains(self, screen) -> None:
        line = self.sim.line
        crashed = self.sim.crash or ()
        self.train_boxes = []
        for train in self.sim.trains:
            if train.state != "running":
                continue
            low, high = train.span
            if high < line.west_edge or low > line.east_edge:
                continue  # completely off the map
            stripe = RED if train in crashed else train_colour(train)
            cars = 3 if train_kind(train) == "IR" else 2
            ends = []
            for i in range(cars):
                offset = i * (CAR_PX + CAR_GAP_PX)
                a = self._walk_back(train, offset)
                b = self._walk_back(train, offset + CAR_PX)
                ends.append((_sp(a), _sp(b)))
            for i in reversed(range(cars)):
                a, b = ends[i]
                if i < cars - 1:
                    pygame.draw.line(screen, INK, b, ends[i + 1][0], max(1, S(3)))
                self._draw_car(screen, a, b, stripe, front=i == 0, rear=i == cars - 1)
            self._draw_train_label(screen, train, ends)

    def _draw_train_label(self, screen, train: Train, ends) -> None:
        head, tail = ends[0][0], ends[-1][1]
        mid = ((head[0] + tail[0]) / 2, (head[1] + tail[1]) / 2)
        on_track_two = train.track_at(train.pos) == 2
        y = mid[1] - S(56) if on_track_two else mid[1] + S(34)
        colour = train_colour(train)
        chip = self.f_bold.render(train_kind(train), True, BG)
        number = self.f_small.render(train.name.split()[-1], True, WHITE)
        delay = train.delay(self.sim.time)
        tag = self.f_small.render("on time" if delay < 30 else f"+{delay / 60:.0f} min", True, GREEN if delay < 30 else RED)
        width = chip.get_width() + number.get_width() + tag.get_width() + S(30)
        box = pygame.Rect(0, 0, width, S(22))
        box.center = (int(mid[0]), int(y))
        box.clamp_ip(SR(*MAP_RECT))
        pygame.draw.rect(screen, (10, 14, 20), box, border_radius=S(6))
        pygame.draw.rect(screen, colour, box, max(1, S(2)), border_radius=S(6))
        chip_box = pygame.Rect(box.x + S(3), box.y + S(3), chip.get_width() + S(8), S(16))
        pygame.draw.rect(screen, colour, chip_box, border_radius=S(4))
        screen.blit(chip, chip.get_rect(center=chip_box.center))
        screen.blit(number, (chip_box.right + S(5), box.y + S(4)))
        screen.blit(tag, (chip_box.right + S(5) + number.get_width() + S(8), box.y + S(4)))
        arrow = "→" if train.direction == EAST else "←"
        self._text(screen, arrow, (box.right + S(4), box.centery), self.f_bold, colour, "midleft")
        self.train_boxes.append((box.union(pygame.Rect(int(min(head[0], tail[0])), int(head[1] - S(8)), int(abs(head[0] - tail[0])) + 1, S(16))), train))

    # ------------------------------------------------------------------ legend, requests, next trains

    def _draw_legend(self, screen) -> None:
        x, y = 28, 108
        items = [
            ("signal", "Signal: the arrow shows the direction · click for red/green"),
            ("point", "Points: the bright branch is the route set · click to switch"),
            ("ring", "Ring: a driver is waiting for it"),
        ]
        for kind, label in items:
            cx, cy = S(x + 7), S(y + 8)
            if kind == "signal":
                pygame.draw.polygon(screen, GREEN, [(cx + S(6), cy), (cx - S(4), cy - S(5)), (cx - S(4), cy + S(5))])
            elif kind == "point":
                ui.circle(screen, WHITE, (cx, cy), S(5))
            else:
                ui.ring(screen, EAST_COLOUR, (cx, cy), S(7), S(2))
            r = self._text(screen, label, (S(x + 22), S(y)), self.f_small, MUTED)
            x = r.right / ui.scale() + 30

    def _draw_requests(self, screen, hover) -> None:
        pygame.draw.rect(screen, PANEL, SR(*REQUESTS_RECT), border_radius=S(12))
        self._text(screen, "Drivers' requests", (S(28), S(472)), self.f_title, TEXT)
        self._text(screen, "Space pause · 1-4 speed · R restart · Esc menu", (S(816), S(476)), self.f_small, MUTED, "topright")
        self.request_buttons, self.request_cards = [], []
        requests = sorted(self.sim.requests.values(), key=lambda r: r.created)
        if not requests:
            self._text(screen, "All quiet on the line.", (S(28), S(510)), self.f_text, MUTED)
            return
        for i, request in enumerate(requests[:6]):
            col, row = i % 2, i // 2
            card = SR(28 + col * 400, 504 + row * 66, 388, 60)
            hovered = card.collidepoint(hover)
            pygame.draw.rect(screen, CARD_HOVER if hovered else CARD, card, border_radius=S(8))
            colour = train_colour(request.train)
            pygame.draw.rect(screen, colour, (card.x, card.y, S(5), card.h), border_radius=S(3))
            name = self._text(screen, request.train.name, (card.x + S(16), card.y + S(7)), self.f_bold, WHITE)
            waited = self.sim.time - request.created
            age = "now" if waited < 60 else f"{waited / 60:.0f} min ago"
            self._text(screen, age, (name.right + S(10), card.y + S(9)), self.f_small, MUTED)
            lines = self._wrap(request.text, card.w - S(30))
            for j, text in enumerate(lines[:2]):
                self._text(screen, text, (card.x + S(16), card.y + S(27) + j * S(15)), self.f_small, TEXT)
            button = pygame.Rect(card.right - S(76), card.y + S(6), S(66), S(22))
            pygame.draw.rect(screen, BUTTON_ON, button, border_radius=S(6))
            self._text(screen, "Do it", button.center, self.f_bold, WHITE, "center")
            self.request_buttons.append((button, request))
            self.request_cards.append((card, request))
        if len(requests) > 6:
            self._text(screen, f"+ {len(requests) - 6} more…", (S(816), S(690)), self.f_small, MUTED, "topright")

    def _wrap(self, text: str, width: int) -> list[str]:
        lines, current = [], ""
        for word in text.split():
            test = (current + " " + word).strip()
            if self.f_small.size(test)[0] > width - S(80) and current and not lines or (
                lines and self.f_small.size(test)[0] > width and current
            ):
                lines.append(current)
                current = word
            else:
                current = test
        lines.append(current)
        return lines

    def _draw_next_trains(self, screen) -> None:
        x0, y0 = NEXT_RECT[0], NEXT_RECT[1]
        right = x0 + NEXT_RECT[2] - 16
        pygame.draw.rect(screen, PANEL, SR(*NEXT_RECT), border_radius=S(12))
        self._text(screen, "Next trains", (S(x0 + 16), S(y0 + 12)), self.f_title, TEXT)
        waiting = sorted((t for t in self.sim.trains if t.state == "waiting"), key=lambda t: t.enter_time)
        if not waiting:
            self._text(screen, "No more trains to come.", (S(x0 + 16), S(y0 + 50)), self.f_text, MUTED)
            return
        y = y0 + 46
        for label, x, anchor in (("Time", x0 + 16, "topleft"), ("Train", x0 + 86, "topleft"), ("From", x0 + 196, "topleft"), ("In", right, "topright")):
            self._text(screen, label, (S(x), S(y)), self.f_small, MUTED, anchor)
        y += 22
        first, last = self.sim.line.stations[0].name, self.sim.line.stations[-1].name
        for train in waiting[:6]:
            colour = train_colour(train)
            self._text(screen, clock_text(train.enter_time), (S(x0 + 16), S(y)), self.f_text, TEXT)
            chip = SR(x0 + 86, y, 26, 18)
            pygame.draw.rect(screen, colour, chip, border_radius=S(4))
            self._text(screen, train_kind(train), chip.center, self.f_bold, BG, "center")
            self._text(screen, train.name.split()[-1], (S(x0 + 118), S(y)), self.f_text, TEXT)
            side = f"{first} side" if train.direction == EAST else f"{last} side"
            self._text(screen, side, (S(x0 + 196), S(y)), self.f_text, MUTED)
            minutes = (train.enter_time - self.sim.time) / 60
            when = "now" if minutes < 0.5 else f"{minutes:.0f} min"
            self._text(screen, when, (S(right), S(y)), self.f_bold, YELLOW if minutes < 3 else TEXT, "topright")
            y += 30

    # ------------------------------------------------------------------ hover information

    def _draw_hover(self, screen, hover) -> None:
        lines: list[str] = []
        obj = self.object_at(hover)
        if isinstance(obj, Signal):
            state = "green" if obj.green else "red"
            where = "entry" if obj.is_entry else f"track {obj.track} exit"
            lines = [f"Signal {obj.id}", f"{obj.station.name} {where} · {state}"]
        elif isinstance(obj, Point):
            lines = [f"Points {obj.id}", f"{obj.station.name} · set to track {obj.track}"]
        else:
            train = self.train_at(hover)
            if train is not None:
                last = self.sim.line.stations[-1 if train.direction == EAST else 0].name
                arrow = "→" if train.direction == EAST else "←"
                stop = train.next_stop()
                lines = [
                    f"{train.name}  {arrow} {last}",
                    f"Next stop: {stop.station.name} {clock_text(stop.arrive)}" if stop else "Leaving the map",
                    f"Delay: {train.delay(self.sim.time) / 60:.0f} min · track {train.track}",
                ]
        if not lines:
            return
        width = max(self.f_text.size(text)[0] for text in lines) + S(24)
        box = pygame.Rect(hover[0] + S(16), hover[1] + S(16), width, S(14) + S(19) * len(lines))
        if box.right > S(WIDTH - 8):
            box.right = hover[0] - S(10)
        if box.bottom > S(HEIGHT - 8):
            box.bottom = hover[1] - S(10)
        pygame.draw.rect(screen, (8, 12, 18), box, border_radius=S(8))
        pygame.draw.rect(screen, (90, 104, 124), box, max(1, S(1)), border_radius=S(8))
        for i, text in enumerate(lines):
            f, colour = (self.f_bold, TEXT) if i == 0 else (self.f_text, MUTED)
            self._text(screen, text, (box.x + S(12), box.y + S(8) + i * S(19)), f, colour)
