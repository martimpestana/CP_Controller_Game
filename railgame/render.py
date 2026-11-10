"""Everything that is drawn on the screen during a level.

The map follows the real shape of the line along the coast (see layout.py). Trains are drawn as
short carriages, and the panel on the right holds the drivers' requests (each with a "Do it"
button), the trains still to come and a short how-to-play.
"""

import math

import pygame

from railgame import skins, ui
from railgame.layout import Layout
from railgame.simulation import Request, Simulation
from railgame.track import EAST, Point, Signal
from railgame.train import Train
from railgame.ui import S, SR, font

WIDTH, HEIGHT = 1280, 720
TOP_BAR = 56
PANEL_X = 900  # the drivers' requests panel starts here

BG = (16, 24, 33)
LAND = (24, 35, 45)
SEA = (14, 44, 64)
SAND = (120, 110, 80)
TRACK = (190, 196, 204)
TRACK_DIM = (95, 104, 115)
WHITE = (245, 245, 245)
TEXT = (215, 222, 230)
MUTED = (150, 160, 172)
GREEN = (60, 220, 110)
RED = (235, 70, 60)
YELLOW = (250, 200, 60)
EAST_COLOUR = (90, 160, 255)
WEST_COLOUR = (255, 150, 60)
PANEL = (28, 38, 50)
CARD = (38, 52, 68)
BUTTON = (48, 64, 82)
BUTTON_ON = (70, 120, 200)

OCEAN_TEXT = (90, 130, 150)
MAP_MUTED = (150, 160, 172)  # small labels on the map
INK = (8, 10, 14)
CAR_PX = 22  # length of one carriage on screen, in design pixels
CAR_GAP_PX = 3
REQUESTS_BOTTOM = HEIGHT - 300  # the drivers' requests stop here, the next trains start below
SIGNAL_SIDE = 14  # pixels between a signal and its track

# Speed buttons in the top bar: (simulated seconds per real second, label).
SPEEDS = ((0, "Pause"), (1, "1x"), (5, "5x"), (10, "10x"), (20, "20x"))


def clock_text(seconds: float, with_seconds: bool = False) -> str:
    seconds = int(seconds) % (24 * 3600)
    text = f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}"
    return text + f":{seconds % 60:02d}" if with_seconds else text


def minutes_text(seconds: float) -> str:
    return f"{seconds / 60:.1f} min"


def apply_theme(colours: dict[str, tuple[int, int, int]]) -> None:
    """Switch the map and panel colours (see themes.py). Takes effect for the next Renderer."""
    globals().update({name: value for name, value in colours.items() if name in globals()})


def train_kind(train: Train) -> str:
    """"R" or "IR", from the train's name."""
    return train.name.split()[0]


def train_colour(train: Train) -> tuple[int, int, int]:
    return EAST_COLOUR if train.direction == EAST else WEST_COLOUR


class Renderer:
    def __init__(self, sim: Simulation, train_skins: dict[str, str] | None = None):
        self.sim = sim
        self.skins = train_skins or dict(skins.DEFAULT_SKINS)
        self.layout = Layout(
            sim.line, (S(40), S(TOP_BAR + 120), S(PANEL_X - 80), S(HEIGHT - TOP_BAR - 250)), ui.scale()
        )
        self.gap = self.layout.track_gap
        self.f_small = font(13)
        self.f_text = font(15)
        self.f_bold = font(15, bold=True)
        self.f_title = font(19, bold=True)
        self.f_big = font(34, bold=True)
        self.speed_buttons: list[tuple[pygame.Rect, int]] = []
        self.restart_button: pygame.Rect | None = None
        self.request_buttons: list[tuple[pygame.Rect, Request]] = []
        self.train_boxes: list[tuple[pygame.Rect, Train]] = []
        self._prepare_background()

    # ------------------------------------------------------------------ positions used for clicks

    def signal_position(self, signal: Signal) -> tuple[float, float]:
        x, y = self.layout.point(signal.pos, signal.track or 1)
        nx, ny = self.layout.normal(signal.pos)
        side = S(SIGNAL_SIDE) if signal.track == 2 else -S(SIGNAL_SIDE)
        return (x + nx * side, y + ny * side)

    def point_position(self, point: Point) -> tuple[float, float]:
        return self.layout.point(point.pos)

    def object_at(self, pos: tuple[int, int]) -> Signal | Point | None:
        best, best_dist = None, S(13)
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

    # ------------------------------------------------------------------ background (drawn once)

    def _prepare_background(self) -> None:
        line = self.sim.line
        lay = self.layout
        surf = pygame.Surface((S(WIDTH), S(HEIGHT)))
        surf.fill(BG)
        pygame.draw.rect(surf, LAND, SR(0, TOP_BAR, PANEL_X, HEIGHT - TOP_BAR))

        # The sea follows the shape of the line, a little to the south.
        coast = []
        island = []
        pos = line.west_edge - 3000
        while pos <= line.east_edge + 3000:
            x, y = lay.point(pos)
            nx, ny = lay.normal(pos)
            coast.append((x - nx * S(45), y - ny * S(45)))
            wave = 10 * math.sin(pos / 2500)
            if line.west_edge + 2000 <= pos <= line.east_edge - 3000:
                island.append((x - nx * S(90 + wave), y - ny * S(90 + wave)))
            pos += 250
        coast = [(0, coast[0][1] + S(20))] + coast + [(S(PANEL_X), coast[-1][1] - S(60))]
        pygame.draw.polygon(surf, SEA, coast + [(S(PANEL_X), S(HEIGHT)), (0, S(HEIGHT))])
        ui.thick_lines(surf, SAND, island, S(5))
        label = self.f_small.render("Atlantic Ocean", True, OCEAN_TEXT)
        surf.blit(label, (S(PANEL_X // 2 - 40), S(HEIGHT - 40)))

        # Track
        ui.thick_lines(surf, TRACK, lay.main_track(), S(4))
        for st in line.stations:
            if st.has_loop:
                ui.thick_lines(surf, TRACK, lay.loop_track(st), S(4))

        # Where the line continues off the map
        west = lay.point(line.west_edge)
        east = lay.point(line.east_edge)
        surf.blit(self.f_small.render("← Loulé", True, MAP_MUTED), (west[0], west[1] - S(30)))
        text = self.f_small.render("V. R. S. António →", True, MAP_MUTED)
        surf.blit(text, (east[0] - text.get_width(), east[1] - S(30)))
        self.background = surf

    # ------------------------------------------------------------------ drawing a frame

    def draw(self, screen: pygame.Surface, info, speed: int, hover: tuple[int, int], toast: str | None) -> None:
        screen.blit(self.background, (0, 0))
        highlighted = self._highlighted_targets(hover)
        self._draw_points(screen, highlighted)
        self._draw_signals(screen, highlighted)
        self._draw_trains(screen)
        self._draw_stations(screen)
        self._draw_top_bar(screen, info, speed)
        self._draw_requests(screen, hover)
        self._draw_next_trains(screen)
        self._draw_legend(screen)
        self._draw_hover(screen, hover)
        if toast:
            text = self.f_text.render(toast, True, WHITE)
            box = text.get_rect(center=(S(PANEL_X // 2), S(TOP_BAR + 30))).inflate(S(24), S(14))
            pygame.draw.rect(screen, (90, 40, 40), box, border_radius=S(8))
            screen.blit(text, text.get_rect(center=box.center))

    def _highlighted_targets(self, hover) -> dict[str, tuple[int, int, int]]:
        targets = {}
        for request in self.sim.requests.values():
            targets[request.target_id] = train_colour(request.train)
        return targets

    def _pulse(self, screen, pos, colour) -> None:
        t = pygame.time.get_ticks() / 1000
        radius = S(13 + 4 * (0.5 + 0.5 * math.sin(t * 6)))
        ui.ring(screen, colour, pos, radius, S(2))

    def _draw_points(self, screen, highlighted) -> None:
        lay = self.layout
        for p in self.sim.line.points:
            st = p.station
            # Show which way the points are set by drawing the chosen route brighter.
            inner = st.pos + p.side * 400
            straight = [lay.point(p.pos), lay.point(inner, 1)]
            diverging = [lay.point(p.pos), lay.point(inner, 2)]
            active, other = (diverging, straight) if p.diverging else (straight, diverging)
            ui.thick_line(screen, TRACK_DIM, other[0], other[1], S(4))
            ui.thick_line(screen, YELLOW if p.diverging else WHITE, active[0], active[1], S(4))
            x, y = self.point_position(p)
            rect = pygame.Rect(0, 0, S(13), S(13))
            rect.center = (int(x), int(y))
            pygame.draw.rect(screen, YELLOW if p.diverging else WHITE, rect, border_radius=S(2))
            pygame.draw.rect(screen, BG, rect, S(2), border_radius=S(2))
            if p.id in highlighted:
                self._pulse(screen, (x, y), highlighted[p.id])

    def _draw_signals(self, screen, highlighted) -> None:
        for s in self.sim.line.signals:
            x, y = self.signal_position(s)
            base = self.layout.point(s.pos, s.track or 1)
            ui.thick_line(screen, MUTED, base, (x, y), S(2))
            ui.circle(screen, (8, 8, 8), (x, y), S(8))
            ui.circle(screen, GREEN if s.green else RED, (x, y), S(6))
            if s.id in highlighted:
                self._pulse(screen, (x, y), highlighted[s.id])

    def _walk_back(self, train: Train, px_dist: float) -> tuple[float, float]:
        """The point on the drawn track px_dist screen pixels behind the front of the train.
        Each step uses the track that part of the train is on, so the carriages follow the
        front through the points instead of jumping across."""
        prev = self.layout.point(train.pos, train.track_at(train.pos))
        done, metres = 0.0, 0.0
        while done < px_dist and metres < 6000:
            metres += 5
            pos = train.pos - train.direction * metres
            cur = self.layout.point(pos, train.track_at(pos))
            done += math.dist(prev, cur)
            prev = cur
        return prev

    def _draw_trains(self, screen) -> None:
        line = self.sim.line
        crashed = self.sim.crash or ()
        self.train_boxes = []
        t = pygame.time.get_ticks() / 1000
        for train in self.sim.trains:
            if train.state != "running":
                continue
            low, high = train.span
            if high < line.west_edge or low > line.east_edge:
                continue  # completely off the map
            stripe = RED if train in crashed else train_colour(train)
            kind = train_kind(train)
            cars = skins.CARS.get(kind, 2)
            skin = self.skins.get(kind, "real")
            ends = []
            for i in range(cars):
                offset = S(i * (CAR_PX + CAR_GAP_PX))
                ends.append((self._walk_back(train, offset), self._walk_back(train, offset + S(CAR_PX))))
            for i in reversed(range(cars)):
                a, b = ends[i]
                if i < cars - 1:
                    pygame.draw.line(screen, INK, b, ends[i + 1][0], max(1, S(3)))
                skins.draw_car(screen, a, b, kind, skin, stripe, i, cars, ui.scale(), t)
            self._draw_train_label(screen, train, ends)

    def _draw_train_label(self, screen, train: Train, ends) -> None:
        """A small tag next to the train: type, number, delay and the way it is going."""
        head, tail = ends[0][0], ends[-1][1]
        mid = ((head[0] + tail[0]) / 2, (head[1] + tail[1]) / 2)
        nx, ny = self.layout.normal(train.pos)
        offset = S(34) + (self.gap if train.track == 2 else 0)
        lx, ly = mid[0] - nx * offset, mid[1] - ny * offset
        colour = train_colour(train)
        chip = self.f_bold.render(train_kind(train), True, BG)
        number = self.f_small.render(train.name.split()[-1], True, WHITE)
        delay = train.delay(self.sim.time)
        tag = self.f_small.render("on time" if delay < 30 else f"+{delay / 60:.0f} min", True, GREEN if delay < 30 else RED)
        arrow = self.f_bold.render("→" if train.direction == EAST else "←", True, colour)
        width = chip.get_width() + number.get_width() + tag.get_width() + arrow.get_width() + S(34)
        box = pygame.Rect(0, 0, width, S(22))
        box.center = (int(lx), int(ly))
        box.clamp_ip(SR(4, TOP_BAR + 4, PANEL_X - 8, HEIGHT - TOP_BAR - 8))
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
        self.train_boxes.append((body.inflate(S(10), S(10)), train))

    def _draw_stations(self, screen) -> None:
        lay = self.layout
        for st in self.sim.line.stations:
            if st.has_loop:
                x, y = lay.local(st, 0, self.gap / 2)
                ui.circle(screen, BG, (x, y), S(15))
                ui.circle(screen, WHITE, (x, y), S(12))
                label = self.f_bold.render(st.name, True, WHITE)
                lx, ly = lay.local(st, 0, S(52))
            else:
                x, y = lay.point(st.pos)
                ui.circle(screen, BG, (x, y), S(9))
                ui.circle(screen, WHITE, (x, y), S(6))
                label = self.f_small.render(st.name, True, MAP_MUTED)
                nx, ny = lay.normal(st.pos)
                lx, ly = x + nx * S(24), y + ny * S(24)
            screen.blit(label, (lx - label.get_width() / 2, ly - label.get_height() / 2))

    def _draw_top_bar(self, screen, info, speed: int) -> None:
        sim = self.sim
        pygame.draw.rect(screen, PANEL, SR(0, 0, WIDTH, TOP_BAR))
        title = self.f_title.render(f"Level {info.number} · {info.title}", True, WHITE)
        screen.blit(title, (S(18), S(16)))

        x = S(330)
        screen.blit(self.f_title.render(clock_text(sim.time, True), True, WHITE), (x, S(16)))
        x += S(110)
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
        x = self.restart_button.right

        x += S(24)
        average = sim.average_delay()
        limit = sim.max_average_delay
        colour = GREEN if average < limit * 0.5 else YELLOW if average <= limit else RED
        text = self.f_bold.render(f"Average delay {minutes_text(average)}", True, colour)
        screen.blit(text, (x, S(19)))
        x += text.get_width() + S(14)
        screen.blit(self.f_text.render(f"(limit {limit / 60:.0f} min)", True, MUTED), (x, S(19)))
        done = sum(1 for t in sim.trains if t.state == "finished")
        text = self.f_text.render(f"Trains done {done}/{len(sim.trains)}", True, MUTED)
        screen.blit(text, (S(WIDTH - 18) - text.get_width(), S(19)))

    def _draw_requests(self, screen, hover) -> None:
        pygame.draw.rect(screen, PANEL, SR(PANEL_X, TOP_BAR, WIDTH - PANEL_X, HEIGHT - TOP_BAR))
        screen.blit(self.f_title.render("Drivers' requests", True, WHITE), (S(PANEL_X + 18), S(TOP_BAR + 14)))
        requests = sorted(self.sim.requests.values(), key=lambda r: r.created)
        y = S(TOP_BAR + 50)
        bottom = S(REQUESTS_BOTTOM)
        width = S(WIDTH - PANEL_X - 32)
        self.request_buttons = []
        if not requests:
            screen.blit(self.f_text.render("All quiet on the line.", True, MUTED), (S(PANEL_X + 18), y))
        for i, request in enumerate(requests):
            lines = self._wrap(request.text, width - S(30))
            height = S(40) + S(19) * len(lines)
            if y + height > bottom:
                more = self.f_text.render(f"+ {len(requests) - i} more…", True, MUTED)
                screen.blit(more, (S(PANEL_X + 18), y))
                break
            card = pygame.Rect(S(PANEL_X + 16), y, width, height)
            pygame.draw.rect(screen, CARD, card, border_radius=S(8))
            colour = train_colour(request.train)
            pygame.draw.rect(screen, colour, (card.x, card.y, S(5), card.h), border_radius=S(3))
            screen.blit(self.f_bold.render(request.train.name, True, WHITE), (card.x + S(16), card.y + S(9)))
            waited = self.sim.time - request.created
            age = "now" if waited < 60 else f"{waited / 60:.0f} min ago"
            name_w = self.f_bold.size(request.train.name)[0]
            screen.blit(self.f_small.render(age, True, MUTED), (card.x + S(26) + name_w, card.y + S(11)))
            # "Do it" switches the signal or points the driver is asking for.
            label = self.f_bold.render("Do it", True, WHITE)
            button = pygame.Rect(0, 0, label.get_width() + S(18), S(24))
            button.topright = (card.right - S(8), card.y + S(6))
            hovered = button.collidepoint(hover)
            pygame.draw.rect(screen, (90, 145, 230) if hovered else BUTTON_ON, button, border_radius=S(6))
            screen.blit(label, label.get_rect(center=button.center))
            self.request_buttons.append((button, request))
            for j, line in enumerate(lines):
                screen.blit(self.f_text.render(line, True, TEXT), (card.x + S(16), card.y + S(32) + S(19) * j))
            y += height + S(10)

    def _wrap(self, text: str, width: int) -> list[str]:
        lines, current = [], ""
        for word in text.split():
            test = (current + " " + word).strip()
            if self.f_text.size(test)[0] > width and current:
                lines.append(current)
                current = word
            else:
                current = test
        lines.append(current)
        return lines

    def _draw_next_trains(self, screen) -> None:
        x0, y = PANEL_X + 18, REQUESTS_BOTTOM + 10
        right = WIDTH - 18
        pygame.draw.line(screen, CARD, (S(PANEL_X + 16), S(y - 8)), (S(right), S(y - 8)), max(1, S(1)))
        screen.blit(self.f_bold.render("Next trains", True, WHITE), (S(x0), S(y)))
        waiting = sorted((t for t in self.sim.trains if t.state == "waiting"), key=lambda t: t.enter_time)
        y += 26
        if not waiting:
            screen.blit(self.f_small.render("No more trains to come.", True, MUTED), (S(x0), S(y)))
            return
        first, last = self.sim.line.stations[0].name, self.sim.line.stations[-1].name
        for train in waiting[:5]:
            colour = train_colour(train)
            screen.blit(self.f_text.render(clock_text(train.enter_time), True, TEXT), (S(x0), S(y)))
            chip = SR(x0 + 56, y + 1, 26, 18)
            pygame.draw.rect(screen, colour, chip, border_radius=S(4))
            text = self.f_bold.render(train_kind(train), True, BG)
            screen.blit(text, text.get_rect(center=chip.center))
            screen.blit(self.f_text.render(train.name.split()[-1], True, TEXT), (S(x0 + 88), S(y)))
            side = f"from {first}" if train.direction == EAST else f"from {last}"
            screen.blit(self.f_small.render(side, True, MUTED), (S(x0 + 150), S(y + 2)))
            minutes = (train.enter_time - self.sim.time) / 60
            when = self.f_bold.render("now" if minutes < 0.5 else f"{minutes:.0f} min", True, YELLOW if minutes < 3 else TEXT)
            screen.blit(when, (S(right) - when.get_width(), S(y)))
            y += 24

    def _draw_legend(self, screen) -> None:
        y = HEIGHT - 135
        screen.blit(self.f_bold.render("How to play", True, WHITE), (S(PANEL_X + 18), S(y)))
        items = [
            ("signal", "Click a signal: red ↔ green"),
            ("point", "Click points: white straight, yellow to track 2"),
            ("ring", "Pulsing ring: a driver is waiting for it"),
            ("keys", "Space pause · 1/2/3/4 speed · R restart · Esc menu"),
        ]
        for i, (kind, text) in enumerate(items):
            cy = y + 32 + i * 24
            cx = PANEL_X + 30
            if kind == "signal":
                ui.circle(screen, GREEN, (S(cx - 6), S(cy)), S(6))
                ui.circle(screen, RED, (S(cx + 8), S(cy)), S(6))
            elif kind == "point":
                pygame.draw.rect(screen, YELLOW, SR(cx - 6, cy - 6, 12, 12), border_radius=S(2))
            elif kind == "ring":
                ui.ring(screen, EAST_COLOUR, (S(cx), S(cy)), S(8), S(2))
            screen.blit(self.f_small.render(text, True, TEXT), (S(cx + 22), S(cy - 9)))

    def _draw_hover(self, screen, hover) -> None:
        obj = self.object_at(hover)
        if obj is None:
            train = self.train_at(hover)
            if train is None:
                return
            last = self.sim.line.stations[-1 if train.direction == EAST else 0].name
            stop = train.next_stop()
            where = f"next stop {stop.station.name} {clock_text(stop.arrive)}" if stop else "leaving the map"
            text = f"{train.name} to {last} · {where} · track {train.track}"
        elif isinstance(obj, Signal):
            state = "green" if obj.green else "red"
            where = "entry" if obj.is_entry else f"track {obj.track} exit"
            text = f"Signal {obj.id} · {obj.station.name} {where} · {state}"
        else:
            text = f"Points {obj.id} · {obj.station.name} · set to track {obj.track}"
        label = self.f_small.render(text, True, WHITE)
        box = label.get_rect(topleft=(hover[0] + S(14), hover[1] + S(14))).inflate(S(12), S(8))
        if box.right > S(PANEL_X):
            box.right = hover[0] - S(10)
        pygame.draw.rect(screen, (0, 0, 0), box, border_radius=S(5))
        screen.blit(label, label.get_rect(center=box.center))
