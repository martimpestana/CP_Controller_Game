"""Levels made by the player in the level editor ("My levels" in the menu).

A custom level is a single-track line the player lays out (its stations, how far apart they
are, which ones have two tracks to cross at, the shape of the line and the landscape around
it), the trains that run on it and when each one enters the map. From that description this
module builds the same Line, timetables and Simulation as the game's own levels use, so a
custom level plays by exactly the same rules.

The levels are kept in a small JSON file in the user's home folder (in the browser: in the
page's local storage), next to the settings.
"""

import json
import math
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

from railgame import i18n
from railgame.levels import LevelInfo, TrainPlan, clock, make_timetable
from railgame.simulation import Simulation
from railgame.track import EAST, WEST, ZONE_HALF, Geography, Line, Station, build_line
from railgame.train import TRAIN_TYPES

LEVELS_FILE = Path(os.environ.get("CP_CONTROLLER_LEVELS", Path.home() / ".cp_controller_levels.json"))
STORAGE_KEY = "cp_controller_levels"  # in the browser

MAX_LEVELS = 8
MIN_STATIONS, MAX_STATIONS = 2, 7
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


@dataclass
class CustomStation:
    name: str
    crossing: bool = True  # two tracks, where trains can pass each other; False: a halt
    gap_km: int = 8  # distance to the next station (not used for the last one)


@dataclass
class CustomTrain:
    kind: str = "R"  # a key of train.TRAIN_TYPES
    direction: int = EAST  # EAST: from the first station towards the last
    enters: str = "08:00"  # when it reaches the edge of the map


@dataclass
class CustomLevel:
    title: str = "My level"
    shape: str = "coast"
    landscape: str = "coast"
    limit_min: int = 4
    stations: list[CustomStation] = field(default_factory=list)
    trains: list[CustomTrain] = field(default_factory=list)

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
        if sum(st.crossing for st in self.stations) < 2:
            out.append("At least two stations must be crossing stations.")
        if any(not st.name.strip() for st in self.stations):
            out.append("Every station needs a name.")
        names = [st.name.strip().lower() for st in self.stations]
        if len(set(names)) < len(names):
            out.append("Two stations have the same name.")
        if not self.trains:
            out.append("Add at least one train.")
        return out

    def codes(self) -> list[str]:
        """A short code for each station (used in the names of its signals and points)."""
        codes: list[str] = []
        for i, st in enumerate(self.stations):
            letters = "".join(ch for ch in _plain(st.name).upper() if ch.isalpha())
            code = (letters[:3] or "ST").ljust(3, "X")
            if code in codes:
                code = f"{code[:2]}{i + 1}"
            codes.append(code)
        return codes

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
        curve = SHAPES.get(self.shape, SHAPES["coast"])[1]
        # Imaginary coordinates somewhere in Portugal: only the shape is used.
        shape = []
        for i in range(SHAPE_POINTS):
            x, y = curve(i / (SHAPE_POINTS - 1))
            shape.append((38.0 + y * 0.5, -8.5 + x * 0.64))
        # Each crossing station sits on its own point of the shape, in order along the line.
        index, used = {}, 0
        loops = [st for st in stations if st.has_loop]
        for k, st in enumerate(loops):
            wanted = round((st.pos - west) / (east - west) * (SHAPE_POINTS - 1))
            used = max(used + 1, min(wanted, SHAPE_POINTS - 1 - (len(loops) - k)))
            index[st.code] = used
        towns = {st.name: 34 for st in loops}  # a town around every crossing station
        geo = Geography(
            shape=shape,
            station_shape_index=index,
            start_label="",
            end_label="",
            water=water,
            water_side=-1,
            water_edge="left" if self.shape == "north" else "bottom",
            water_label=water_label,
            scenery=scenery,
            towns=towns,
        )
        return build_line(self.title.strip() or "My level", stations, west, east, geo)

    def map_key(self) -> str:
        """Everything the drawn map depends on (the trains and the times do not change it)."""
        return json.dumps([self.title, self.shape, self.landscape, [asdict(st) for st in self.stations]])

    def plans(self) -> list[TrainPlan]:
        """The trains in the order they enter, each with a number of its own."""
        plans, counts = [], {}
        for train in sorted(self.trains, key=lambda t: clock(t.enters)):
            kind = train.kind if train.kind in TRAIN_TYPES else "R"
            counts[kind] = counts.get(kind, 0) + 1
            # Odd numbers one way and even numbers the other, as on the real railway.
            number = 100 * (TRAIN_KINDS.index(kind) + 1) + 2 * counts[kind] - (1 if train.direction == EAST else 0)
            plans.append(TrainPlan(f"{kind} {number}", train.direction, train.enters))
        return plans

    def start(self) -> str:
        """The level starts two minutes before the first train."""
        first = min((clock(t.enters) for t in self.trains), default=clock("08:00"))
        return clock_text(max(0, first - 120))

    def info(self, number: int) -> LevelInfo:
        km = self.length_km()
        description = f"{len(self.stations)} stations, {km:.0f} km. Made in the level editor."
        return LevelInfo(number, self.title.strip() or "My level", description, self.start(), self.limit_min, self.plans(), line="custom")

    def build(self, number: int = 1) -> tuple[LevelInfo, Simulation]:
        """The level ready to play, like levels.build_level for the game's own levels."""
        info = self.info(number)
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
        for tr in _dicts(data.get("trains"))[:MAX_TRAINS]:
            level.trains.append(
                CustomTrain(
                    tr.get("kind") if tr.get("kind") in TRAIN_KINDS else "R",
                    WEST if tr.get("direction") == WEST else EAST,
                    _time(tr.get("enters")),
                )
            )
        return level


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
