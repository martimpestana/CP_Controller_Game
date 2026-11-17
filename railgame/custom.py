"""Levels made by the player in the level editor ("My levels" in the menu).

A custom level is a single-track line the player lays out (its stations, how far apart they
are, which ones have two tracks to cross at, the shape of the line and the landscape around
it), the trains that run on it and when each one enters the map. From that description this
module builds the same Line, timetables and Simulation as the game's own levels use, so a
custom level plays by exactly the same rules.

A level can also have a second line (a branch, a line that crosses the first at one of its
stations, or a separate line), or a main line with double track. Then the lines are joined into
a network (junction.py).

The levels are kept in a small JSON file in the user's home folder (in the browser: in the
page's local storage), next to the settings.
"""

import json
import math
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

from railgame import i18n, junction
from railgame.levels import LevelInfo, TrainPlan, clock, make_timetable
from railgame.netsim import NetSimulation
from railgame.simulation import Simulation
from railgame.track import EAST, WEST, ZONE_HALF, Geography, Line, Station, build_line
from railgame.train import TRAIN_TYPES

LEVELS_FILE = Path(os.environ.get("CP_CONTROLLER_LEVELS", Path.home() / ".cp_controller_levels.json"))
STORAGE_KEY = "cp_controller_levels"  # in the browser

MAX_LEVELS = 8
MIN_STATIONS, MAX_STATIONS = 2, 7
MAX_BRANCH_STATIONS = 4
MAX_TRAINS = 12
MIN_GAP_KM, MAX_GAP_KM = 3, 30  # between two stations (a station area is 2 km long)
EDGE_KM = 2.5  # the line goes on this far past the first and the last station
MIN_LIMIT, MAX_LIMIT = 1, 15  # allowed average delay, in minutes
NAME_LENGTH = 22
TITLE_LENGTH = 28

# The trains a single-track line can carry (the editor offers them in this order).
TRAIN_KINDS = ("R", "IR", "IC", "AP", "M", "H")

# The shape of the line on the map: a function from t (0 at the first end, 1 at the last)
# to (x, y), with x to the right and y up. Only the proportions matter.
SHAPES = {
    "coast": ("Gentle curve", lambda t: (t, 0.42 * t + 0.10 * math.sin(math.pi * t))),
    "straight": ("Straight", lambda t: (t, 0.25 * t)),
    "bend": ("Big bend", lambda t: (t, 0.50 * math.sin(math.pi * t))),
    "s": ("S-curve", lambda t: (t, 0.30 * t + 0.16 * math.sin(2 * math.pi * t))),
    "north": ("South to north", lambda t: (0.45 * t + 0.10 * math.sin(math.pi * t), 1.1 * t)),
}

# The landscape: (name in the editor, water, scenery of the map, label of the water).
LANDSCAPES = {
    "coast": ("Coast", "sea", "algarve-storybook", "Atlantic Ocean"),
    "plain": ("Plain", "none", "alentejo-storybook", ""),
    "river": ("River valley", "river", "douro-storybook", "River"),
    "simple": ("Simple map", "none", "plain", ""),
}

SHAPE_POINTS = 41
DRAWN = "drawn"  # CustomLevel.shape when the player drew the line by hand (CustomLevel.path)
DRAWN_NAME = "Drawn by hand"
MIN_DRAWN_LENGTH = 0.5  # a drawn line must be at least this long (the drawing area is 1 wide)


def _resample(points: list[tuple[float, float]], count: int) -> list[tuple[float, float]]:
    """The same polyline as `count` points spaced evenly along it."""
    cum = [0.0]
    for a, b in zip(points, points[1:]):
        cum.append(cum[-1] + math.dist(a, b))
    total = cum[-1]
    if total <= 0:
        return [points[0]] * count
    out, j = [], 0
    for i in range(count):
        d = total * i / (count - 1)
        while j < len(points) - 2 and cum[j + 1] < d:
            j += 1
        seg = cum[j + 1] - cum[j]
        t = 0.0 if seg <= 0 else (d - cum[j]) / seg
        (ax, ay), (bx, by) = points[j], points[j + 1]
        out.append((ax + (bx - ax) * t, ay + (by - ay) * t))
    return out


def _crosses_itself(points: list[tuple[float, float]]) -> bool:
    def side(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    segments = list(zip(points, points[1:]))
    for i, (a, b) in enumerate(segments):
        for c, d in segments[i + 2 :]:
            if side(a, b, c) * side(a, b, d) < 0 and side(c, d, a) * side(c, d, b) < 0:
                return True
    return False


def _path_problem(path: list[tuple[float, float]]) -> str:
    """Why this path cannot be a railway line ("" when it can)."""
    length = sum(math.dist(a, b) for a, b in zip(path, path[1:]))
    if length < MIN_DRAWN_LENGTH:
        return "The line is too short. Draw it across the map."
    if _crosses_itself(path):
        return "The line cannot cross itself."
    # No hairpins: the station areas must have room to lie along the line.
    for i in range(2, len(path) - 2):
        (ax, ay), (bx, by), (cx, cy) = path[i - 2], path[i], path[i + 2]
        if (bx - ax) * (cx - bx) + (by - ay) * (cy - by) < 0:
            return "That bend is too sharp for a train. Draw wider curves."
    return ""


def tidy_path(points) -> tuple[list[tuple[float, float]], str]:
    """Turn what the mouse drew into a line the map can use: (path, "") or ([], why not).

    Points are (x, y) with x to the right and y DOWN, both from 0 to 1 across the drawing
    area. The path comes back smoothed (a shaky hand must not put kinks in the track), as
    SHAPE_POINTS evenly spaced points, running left to right (or bottom to top for a line
    that is taller than it is wide), like the ready-made shapes.
    """
    pts = [(min(1.0, max(0.0, float(x))), min(1.0, max(0.0, float(y)))) for x, y in points]
    pts = [p for i, p in enumerate(pts) if i == 0 or math.dist(p, pts[i - 1]) > 1e-4]
    if len(pts) < 2:
        return [], "Hold the mouse button down and draw the line."
    if len(pts) == SHAPE_POINTS and not _path_problem(pts):
        path = pts  # already tidied (read back from the file): keep it exactly as it is
    else:
        path = _resample(pts, SHAPE_POINTS)
        for _ in range(3):  # smooth, keeping both ends where they were drawn
            path = [path[0]] + [
                tuple((a + 2 * b + c) / 4 for a, b, c in zip(path[i - 1], path[i], path[i + 1]))
                for i in range(1, len(path) - 1)
            ] + [path[-1]]
        path = _resample(path, SHAPE_POINTS)
    why = _path_problem(path)
    if why:
        return [], why
    width = max(p[0] for p in path) - min(p[0] for p in path)
    height = max(p[1] for p in path) - min(p[1] for p in path)
    if (path[-1][0] < path[0][0]) if width >= height else (path[-1][1] > path[0][1]):
        path.reverse()
    return [(round(x, 4), round(y, 4)) for x, y in path], ""


@dataclass
class CustomStation:
    name: str
    crossing: bool = True  # two tracks, where trains can pass each other; False: a halt
    gap_km: int = 8  # distance to the next station (not used for the last one)


# The kinds of second line: (name in the editor, what it is).
SECOND_KINDS = {
    "branch": ("Branch", "A line that leaves the first one just past one of its crossing stations."),
    "cross": ("Crossing line", "A line that comes in from one side, runs through a crossing station of the first one and leaves on the other side."),
    "separate": ("Separate line", "A line of its own on the same map, which never meets the first one."),
}


@dataclass
class CustomBranch:
    """The second line of a level: a branch, a crossing line or a separate line (junction.py)."""

    junction: int = 0  # branch, crossing line: the station of the main line where they meet
    gap_km: int = 6  # from that station to the next station of the second line
    stations: list[CustomStation] = field(default_factory=list)  # the second line's own, in order
    kind: str = "branch"  # a key of SECOND_KINDS
    before: int = 0  # a crossing line: how many of its stations come before the shared one

    def ordered(self) -> list:
        """The stations of the second line in the order a train meets them (a crossing line
        includes the shared station, as None)."""
        if self.kind != "cross":
            return list(self.stations)
        return self.stations[: self.before] + [None] + self.stations[self.before :]


@dataclass
class CustomTrain:
    kind: str = "R"  # a key of train.TRAIN_TYPES
    direction: int = EAST  # EAST: from the first station towards the last
    enters: str = "08:00"  # when it reaches the edge of the map
    branch: bool = False  # True: it runs on the second line (see CustomLevel.route_ends)


@dataclass
class CustomLevel:
    title: str = "My level"
    shape: str = "coast"
    landscape: str = "coast"
    limit_min: int = 4
    path: list[tuple[float, float]] = field(default_factory=list)  # the line drawn by hand (see tidy_path)
    stations: list[CustomStation] = field(default_factory=list)
    trains: list[CustomTrain] = field(default_factory=list)
    branch: CustomBranch | None = None  # the second line, if any
    double: bool = False  # the main line has two tracks all the way

    # ------------------------------------------------------------------ what it is made of

    @classmethod
    def starter(cls, number: int = 1) -> "CustomLevel":
        """What a new level looks like before the player changes anything."""
        return cls(
            title=f"{i18n.t('My level', collect=False)} {number}",  # in the player's language
            stations=[
                CustomStation("Vila Nova", True, 9),
                CustomStation("Ponte", False, 7),
                CustomStation("Monte Alto", True, 10),
                CustomStation("Porto Belo", True, 8),
            ],
            trains=[
                CustomTrain("R", EAST, "08:00"),
                CustomTrain("R", WEST, "08:05"),
                CustomTrain("IR", EAST, "08:20"),
            ],
        )

    def problems(self) -> list[str]:
        """Why the level cannot be played yet (empty when it can)."""
        out = []
        if len(self.stations) < MIN_STATIONS:
            out.append("A line needs at least two stations.")
        if sum(st.crossing for st in self.stations) < 2 and not self.double:
            out.append("At least two stations must be crossing stations.")
        if any(not st.name.strip() for st in self.all_stations()):
            out.append("Every station needs a name.")
        names = [st.name.strip().lower() for st in self.all_stations()]
        if len(set(names)) < len(names):
            out.append("Two stations have the same name.")
        branch = self.branch
        if branch is not None:
            if not branch.stations:
                out.append("The second line needs at least one station.")
            if branch.kind != "separate":
                if not 0 <= branch.junction < len(self.stations) or not self.stations[branch.junction].crossing:
                    out.append("The second line must meet the first at a crossing station.")
                if self.double:
                    out.append("With double track the second line can only be a separate line.")
        if not self.trains:
            out.append("Add at least one train.")
        return out

    def all_stations(self) -> list[CustomStation]:
        """The stations of the main line, then those of the branch."""
        return self.stations + (self.branch.stations if self.branch is not None else [])

    def codes(self) -> list[str]:
        """A short code for each station (used in the names of its signals and points): the
        main line's stations first, then the branch's."""
        codes: list[str] = []
        for i, st in enumerate(self.all_stations()):
            letters = "".join(ch for ch in _plain(st.name).upper() if ch.isalpha())
            code = (letters[:3] or "ST").ljust(3, "X")
            if code in codes:
                code = f"{code[:2]}{i + 1}"
            codes.append(code)
        return codes

    def shape_name(self) -> str:
        return DRAWN_NAME if self.shape == DRAWN else SHAPES[self.shape][0]

    def shape_points(self, count: int = SHAPE_POINTS) -> list[tuple[float, float]]:
        """The line from its first end to its last, as (x, y) with x to the right and y up."""
        if self.shape == DRAWN and len(self.path) >= 2:
            return [(x, 1.0 - y) for x, y in _resample(list(self.path), count)]
        curve = SHAPES.get(self.shape, SHAPES["coast"])[1]
        return [curve(i / (count - 1)) for i in range(count)]

    def tall(self) -> bool:
        """Does the line run up the map more than across it? (Then the sea is on the left.)"""
        pts = self.shape_points()
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return max(ys) - min(ys) > max(xs) - min(xs)

    def length_km(self) -> float:
        return sum(st.gap_km for st in self.stations[:-1])

    # ------------------------------------------------------------------ building the game

    def line(self) -> Line:
        codes = self.codes()
        stations, pos = [], 0.0
        for st, code in zip(self.stations, codes):
            stations.append(Station(st.name.strip(), code, pos, st.crossing))
            pos += st.gap_km * 1000
        last = stations[-1].pos
        west, east = -EDGE_KM * 1000, last + EDGE_KM * 1000
        _, water, scenery, water_label = LANDSCAPES.get(self.landscape, LANDSCAPES["simple"])
        # Imaginary coordinates somewhere in Portugal: only the shape is used.
        shape = [(38.0 + y * 0.5, -8.5 + x * 0.64) for x, y in self.shape_points()]
        # Each crossing station sits on its own point of the shape, in order along the line.
        index, used = {}, 0
        loops = [st for st in stations if st.has_loop]
        for k, st in enumerate(loops):
            wanted = round((st.pos - west) / (east - west) * (SHAPE_POINTS - 1))
            used = max(used + 1, min(wanted, SHAPE_POINTS - 1 - (len(loops) - k)))
            index[st.code] = used
        towns = {st.name: 34 for st in loops}  # a town around every crossing station
        tall = self.tall()
        geo = Geography(
            shape=shape,
            station_shape_index=index,
            start_label="",
            end_label="",
            water=water,
            # A line running up the map has the sea on its left, like the Linha do Oeste.
            water_side=1 if tall and water == "sea" else -1,
            water_edge="left" if tall else "bottom",
            map_box=self._map_box(tall),
            water_label=water_label,
            scenery=scenery,
            towns=towns,
        )
        return build_line(self.title.strip() or "My level", stations, west, east, geo)

    def _stations(self, items, codes, start: float, step: int) -> list[Station]:
        """Stations from the editor's list, from `start` metres, each gap_km further on (step 1)
        or back (step -1, for a list given from the far end)."""
        stations, pos = [], start
        for st, code in zip(items, codes):
            stations.append(Station(st.name.strip(), code, pos, st.crossing))
            pos += step * st.gap_km * 1000
        return stations

    def side_line(self, main: Line) -> Line:
        """The second line on its own: the branch, the part of a crossing line after the shared
        station, or the separate line (see junction.py for where their positions start)."""
        branch = self.branch
        codes = dict(zip(map(id, branch.stations), self.codes()[len(self.stations):]))
        name = f"{main.name} (2)"
        if branch.kind == "separate":
            stations = self._stations(branch.stations, [codes[id(st)] for st in branch.stations], 0, 1)
            west, east = -EDGE_KM * 1000, stations[-1].pos + EDGE_KM * 1000
            geo = _geography(self._second_points(), stations, west, east, self._second_box())
            return build_line(name, stations, west, east, geo)
        start = main.stations[branch.junction]
        after = branch.stations[branch.before :] if branch.kind == "cross" else branch.stations
        stations, pos = [], start.pos + branch.gap_km * 1000
        for st in after:
            stations.append(Station(st.name.strip(), codes[id(st)], pos, st.crossing))
            pos += st.gap_km * 1000
        begin = start.pos + junction.JUNCTION_OFFSET
        east = (stations[-1].pos if stations else begin) + EDGE_KM * 1000
        return build_line(name, stations, begin, east, None)

    def west_line(self, main: Line) -> Line:
        """A crossing line: its part before the shared station, counting up to it."""
        branch = self.branch
        codes = dict(zip(map(id, branch.stations), self.codes()[len(self.stations):]))
        start = main.stations[branch.junction]
        before = branch.stations[: branch.before]
        stations, pos = [], start.pos
        for st in reversed(before):  # each one's gap is to the next station, the last one's to the shared one
            pos -= st.gap_km * 1000
            stations.insert(0, Station(st.name.strip(), codes[id(st)], pos, st.crossing))
        end = start.pos - junction.JUNCTION_OFFSET
        west = (stations[0].pos if stations else end) - EDGE_KM * 1000
        return build_line(f"{main.name} (2, west)", stations, west, end, None)

    def _second_points(self) -> list[tuple[float, float]]:
        """The shape of a separate line: a gentle curve along the main line."""
        if self.tall():
            return [(0.12 * math.sin(math.pi * t), t) for t in (i / (SHAPE_POINTS - 1) for i in range(SHAPE_POINTS))]
        return [(t, 0.10 * math.sin(math.pi * t)) for t in (i / (SHAPE_POINTS - 1) for i in range(SHAPE_POINTS))]

    def _second_box(self) -> tuple[int, int, int, int]:
        """Where a separate line is drawn: on the dry side of the main line."""
        return (660, 120, 200, 540) if self.tall() else (70, 110, 760, 190)

    def network(self) -> junction.JunctionNetwork:
        """The lines of the level joined into one network."""
        main = self.line()
        branch = self.branch
        if branch is None:
            return junction.build_network(main, double=self.double)
        side = self.side_line(main)
        if branch.kind == "separate":
            return junction.build_network(main, side, kind="separate", double=self.double)
        west = self.west_line(main) if branch.kind == "cross" else None
        return junction.build_network(main, side, main.stations[branch.junction], branch.kind, west, self.double)

    def route_ends(self, train: CustomTrain) -> tuple[str, str]:
        """Where a train comes from and where it goes."""
        first, last = self.stations[0].name, self.stations[-1].name
        branch = self.branch
        if train.branch and branch is not None and branch.stations:
            line = [st.name if st else self.stations[branch.junction].name for st in branch.ordered()]
            if branch.kind == "branch":
                line = [first] + line
            first, last = line[0], line[-1]
        return (first, last) if train.direction == EAST else (last, first)

    def _map_box(self, tall: bool) -> tuple[int, int, int, int] | None:
        """Where the main line is drawn (None: the usual place). With a second line it moves
        over, to leave room for it on its dry side: above it, or to its right if it is tall."""
        branch = self.branch
        if branch is None:
            return None
        landscape_water = LANDSCAPES.get(self.landscape, LANDSCAPES["simple"])[1]
        if branch.kind == "cross" and landscape_water == "none":  # room on both sides
            return (230, 130, 400, 540) if tall else (40, 250, 820, 230)
        if branch.kind == "separate":
            return (40, 150, 560, 500) if tall else (40, 380, 820, 250)
        return (40, 150, 600, 500) if tall else (40, 350, 820, 250)

    def map_key(self) -> str:
        """Everything the drawn map depends on (the trains and the times do not change it)."""
        branch = asdict(self.branch) if self.branch is not None else None
        stations = [asdict(st) for st in self.stations]
        return json.dumps([self.title, self.shape, self.path, self.landscape, stations, branch, self.double])

    def plans(self) -> list[TrainPlan]:
        """The trains in the order they enter, each with a number of its own."""
        plans, counts = [], {}
        for train in sorted(self.trains, key=lambda t: clock(t.enters)):
            kind = train.kind if train.kind in TRAIN_TYPES else "R"
            counts[kind] = counts.get(kind, 0) + 1
            # Odd numbers one way and even numbers the other, as on the real railway.
            number = 100 * (TRAIN_KINDS.index(kind) + 1) + 2 * counts[kind] - (1 if train.direction == EAST else 0)
            on_branch = train.branch and self.branch is not None
            plans.append(
                TrainPlan(
                    f"{kind} {number}", train.direction, train.enters,
                    frm="branch" if on_branch and train.direction == WEST else "",
                    to="branch" if on_branch and train.direction == EAST else "",
                )
            )
        return plans

    def start(self) -> str:
        """The level starts two minutes before the first train."""
        first = min((clock(t.enters) for t in self.trains), default=clock("08:00"))
        return clock_text(max(0, first - 120))

    def info(self, number: int) -> LevelInfo:
        km = self.length_km()
        extra = ", double track" if self.double else ""
        if self.branch is not None:
            extra += {"branch": " and a branch", "cross": " and a crossing line", "separate": " and a second line"}[self.branch.kind]
        description = f"{len(self.all_stations())} stations, {km:.0f} km{extra}. Made in the level editor."
        return LevelInfo(number, self.title.strip() or "My level", description, self.start(), self.limit_min, self.plans(), line="custom")

    def build(self, number: int = 1) -> tuple[LevelInfo, Simulation]:
        """The level ready to play, like levels.build_level for the game's own levels."""
        info = self.info(number)
        if self.branch is not None or self.double:
            net = self.network()
            trains = [
                junction.make_timetable(net, plan.name, plan.direction, clock(plan.enters), "branch" in (plan.frm, plan.to))
                for plan in info.trains
            ]
            return info, NetSimulation(net, trains, clock(info.start), info.max_average_delay_min * 60)
        line = self.line()
        trains = [make_timetable(line, plan) for plan in info.trains]
        return info, Simulation(line, trains, clock(info.start), info.max_average_delay_min * 60)

    # ------------------------------------------------------------------ saving

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CustomLevel":
        """A level read from the file. Anything odd in it is put right, never trusted."""
        level = cls()
        level.title = _text(data.get("title"), TITLE_LENGTH) or "My level"
        level.shape = data.get("shape") if data.get("shape") in SHAPES else "coast"
        if data.get("shape") == DRAWN:  # only with a path that still makes a proper line
            try:
                raw = data.get("path")
                pairs = [(float(x), float(y)) for x, y in raw[:500]] if isinstance(raw, list) else []
            except (TypeError, ValueError):
                pairs = []
            if all(math.isfinite(v) for pair in pairs for v in pair):
                level.path, why = tidy_path(pairs)
                if not why:
                    level.shape = DRAWN
        level.landscape = data.get("landscape") if data.get("landscape") in LANDSCAPES else "coast"
        level.limit_min = _number(data.get("limit_min"), MIN_LIMIT, MAX_LIMIT, 4)
        for st in _dicts(data.get("stations"))[:MAX_STATIONS]:
            level.stations.append(
                CustomStation(
                    _text(st.get("name"), NAME_LENGTH),
                    bool(st.get("crossing", True)),
                    _number(st.get("gap_km"), MIN_GAP_KM, MAX_GAP_KM, 8),
                )
            )
        branch = data.get("branch")
        if isinstance(branch, dict) and level.stations:
            stations = [
                CustomStation(
                    _text(st.get("name"), NAME_LENGTH),
                    bool(st.get("crossing", True)),
                    _number(st.get("gap_km"), MIN_GAP_KM, MAX_GAP_KM, 8),
                )
                for st in _dicts(branch.get("stations"))[:MAX_BRANCH_STATIONS]
            ]
            if stations:  # a second line with no station left is no second line
                kind = branch.get("kind") if branch.get("kind") in SECOND_KINDS else "branch"
                level.branch = CustomBranch(
                    _number(branch.get("junction"), 0, len(level.stations) - 1, 0),
                    _number(branch.get("gap_km"), MIN_GAP_KM, MAX_GAP_KM, 6),
                    stations,
                    kind,
                    _number(branch.get("before"), 0, len(stations), 0) if kind == "cross" else 0,
                )
        level.double = data.get("double") is True
        for tr in _dicts(data.get("trains"))[:MAX_TRAINS]:
            level.trains.append(
                CustomTrain(
                    tr.get("kind") if tr.get("kind") in TRAIN_KINDS else "R",
                    WEST if tr.get("direction") == WEST else EAST,
                    _time(tr.get("enters")),
                    tr.get("branch") is True and level.branch is not None,
                )
            )
        return level


def _geography(points, stations: list[Station], west: float, east: float, map_box) -> Geography:
    """How a second line is placed on the map: its shape (x right, y up) stretched into map_box,
    with each crossing station on a point of its own, in order along the line."""
    shape = [(38.0 + y * 0.5, -8.5 + x * 0.64) for x, y in points]
    index, used = {}, 0
    loops = [st for st in stations if st.has_loop]
    for k, st in enumerate(loops):
        wanted = round((st.pos - west) / (east - west) * (len(points) - 1))
        used = max(used + 1, min(wanted, len(points) - 1 - (len(loops) - k)))
        index[st.code] = used
    return Geography(shape=shape, station_shape_index=index, start_label="", end_label="", water="none", map_box=map_box)


def clock_text(seconds: float) -> str:
    minutes = int(seconds // 60) % (24 * 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def shift_time(text: str, minutes: int) -> str:
    """A time some minutes later (or earlier), kept inside one day."""
    total = clock(text) // 60 + minutes
    return clock_text(max(0, min(23 * 60 + 59, total)) * 60)


def _plain(text: str) -> str:
    """Letters without their accents (Évora -> Evora), for station codes."""
    try:
        import unicodedata
    except ImportError:  # a build without it: letters with accents are simply left out of the code
        return text

    return "".join(ch for ch in unicodedata.normalize("NFD", text) if not unicodedata.combining(ch))


def _text(value, length: int) -> str:
    if not isinstance(value, str):
        return ""
    return "".join(ch for ch in value if ch.isprintable())[:length].strip()


def _number(value, low: int, high: int, default: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return default
    return int(max(low, min(high, value)))


def _dicts(value) -> list[dict]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _time(value) -> str:
    try:
        return clock_text(clock(value)) if 0 <= clock(value) < 24 * 3600 else "08:00"
    except (AttributeError, TypeError, ValueError):
        return "08:00"


# ---------------------------------------------------------------------- the file


def _browser_storage():
    """The page's local storage when the game runs in the browser, otherwise None."""
    try:
        from platform import window  # only exists in the browser (pygbag)

        return window.localStorage
    except Exception:
        return None


def load_levels(path: Path | None = None) -> list[CustomLevel]:
    text = None
    storage = _browser_storage() if path is None else None
    try:
        if storage is not None:
            text = storage.getItem(STORAGE_KEY)
        else:
            text = Path(path or LEVELS_FILE).read_text(encoding="utf-8")
    except Exception:
        return []
    try:
        data = json.loads(text) if text else []
    except ValueError:
        return []
    return [CustomLevel.from_dict(item) for item in _dicts(data)][:MAX_LEVELS]


def save_levels(levels: list[CustomLevel], path: Path | None = None) -> bool:
    """Write the levels. Returns False if they could not be saved (they stay for this session)."""
    text = json.dumps([level.to_dict() for level in levels], indent=2, ensure_ascii=False)
    storage = _browser_storage() if path is None else None
    try:
        if storage is not None:
            storage.setItem(STORAGE_KEY, text)
        else:
            Path(path or LEVELS_FILE).write_text(text, encoding="utf-8")
    except Exception:
        return False
    return True
