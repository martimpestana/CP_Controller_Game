"""Custom lines with more than one track or more than one line, made in the level editor.

The level editor (custom.py) can add to its first line, the main line:

- a branch: a second line that leaves the main line just past one of its crossing stations
  and runs off to the edge of the map;
- a crossing line: a second line that comes in from one side, runs through one crossing
  station of the main line (sharing its two tracks) and leaves on the other side;
- a separate line: a second line on the same map that never meets the first;
- double track: the main line has two tracks all the way, one for each direction, with
  crossovers at its crossing stations so a train can overtake a slower one.

For the rules every such level is a Network (network.py) played by NetSimulation: each line is
one long track, every crossing station of a single-track line adds a second track beside it,
and points join the lines. For the map each line is an ordinary Line (track.py), drawn by
junctionrender.py with a Layout of its own.

Positions are metres along each line. The branch, and the part of a crossing line after the
shared station, carry on from the main line: a station 6 km down the branch is 6 km further
than the junction station. The part of a crossing line before the shared station counts up to
it in the same way. A separate line has positions of its own (its tracks have their own ids, so
the rules never mix the two).
"""

from dataclasses import dataclass, field

from railgame.network import Geo, Network, Switch, Track
from railgame.track import EAST, ENTRY_SIGNAL_OFFSET, LOOP_HALF, POINT_OFFSET, WEST, ZONE_HALF, Line, Signal, Station
from railgame.train import Stop, Train

MAIN = "M"  # the track of the main line (on a double line: the track of the trains going EAST)
MAIN_BACK = "W"  # on a double line: the track of the trains going WEST
BRANCH = "B"  # the branch, or the part of a crossing line after the shared station
BRANCH_WEST = "BW"  # the part of a crossing line before the shared station
SECOND = "S"  # the track of a separate line
JUNCTION_OFFSET = ZONE_HALF  # the junction points are this far from the centre of their station
CROSSOVER_FAR, CROSSOVER_NEAR = 700, 500  # where a double line's crossovers are, from the station centre
RUNNING_MARGIN = 60  # seconds of slack added to each section of the timetable (as on the other lines)

KINDS = ("branch", "cross", "separate")


def loop_track(code: str) -> str:
    """The id of the second track of a crossing station."""
    return f"{code}-2"


@dataclass
class JunctionNetwork(Network):
    main: Line | None = None  # the first line on its own
    side: Line | None = None  # the branch, the crossing line after the shared station, or the separate line
    west_side: Line | None = None  # a crossing line: its part before the shared station
    junction: Station | None = None  # the station of the main line where the lines meet
    kind: str = ""  # "branch", "cross", "separate" or "" (no second line)
    double: bool = False  # the main line has two tracks all the way
    track_lines: dict = field(default_factory=dict)  # track id -> the Line it is drawn along
    crossovers: set = field(default_factory=set)  # ids of the crossovers of a double line

    def lines(self) -> list[Line]:
        return [line for line in (self.main, self.side, self.west_side) if line is not None]

    def line_of(self, station: Station) -> Line:
        return next(line for line in self.lines() if any(station is st for st in line.stations))

    def line_of_track(self, track_id: str) -> Line:
        return self.track_lines[track_id]

    def is_loop(self, track_id: str) -> bool:
        """Is this the second track of a crossing station?"""
        return track_id.endswith("-2")

    def stem_of(self, line: Line) -> str:
        """The long track of a line."""
        return next(t for t, ln in self.track_lines.items() if ln is line and not self.is_loop(t) and t != MAIN_BACK)


def junction_points(junction: Station) -> str:
    return f"{junction.code}-J"


def west_junction_points(junction: Station) -> str:
    return f"{junction.code}-K"


class _Builder:
    def __init__(self):
        self.tracks: dict[str, Track] = {}
        self.points: list[Switch] = []
        self.signals: list[Signal] = []
        self.platforms: dict[str, tuple[str, ...]] = {}
        self.track_lines: dict[str, Line] = {}
        self.crossovers: set[str] = set()

    def track(self, line: Line, track: Track) -> None:
        self.tracks[track.id] = track
        self.track_lines[track.id] = line

    def single(self, line: Line, stem: str) -> None:
        """The crossing stations of a single-track line: a second track, points and signals."""
        for st in line.stations:
            if not st.has_loop:
                self.platforms[st.code] = (stem,)
                continue
            loop = loop_track(st.code)
            self.track(line, Track(loop, "track 2", st.pos - POINT_OFFSET, st.pos + POINT_OFFSET, 1))
            self.platforms[st.code] = (stem, loop)
            self.points.append(Switch(f"{st.code}-PW", st, st.pos - POINT_OFFSET, WEST, stem=stem, straight=stem, branch=loop, facing=EAST))
            self.points.append(Switch(f"{st.code}-PE", st, st.pos + POINT_OFFSET, EAST, stem=stem, straight=stem, branch=loop, facing=WEST))
            # Entry signals in front of the points, exit signals at the end of each platform.
            self.signals.append(Signal(f"{st.code}-E0", st, st.pos - ENTRY_SIGNAL_OFFSET, EAST, stem))
            self.signals.append(Signal(f"{st.code}-W0", st, st.pos + ENTRY_SIGNAL_OFFSET, WEST, stem))
            for number, track in ((1, stem), (2, loop)):
                self.signals.append(Signal(f"{st.code}-E{number}", st, st.pos + LOOP_HALF, EAST, track))
                self.signals.append(Signal(f"{st.code}-W{number}", st, st.pos - LOOP_HALF, WEST, track))

    def double(self, line: Line) -> None:
        """The stations of a double line. Every station has a platform on both tracks. At a
        crossing station a train can cross over to the other track before the station (to pass
        a train standing at its own platform) and back again after it: the crossovers back are
        set for the train's own track, the ones across are not."""
        for st in line.stations:
            self.platforms[st.code] = (MAIN, MAIN_BACK)
            if not st.has_loop:
                continue
            c, p = st.code, st.pos
            for sid, pos, side, stem, straight, branch, facing in (
                (f"{c}-XE", p - CROSSOVER_FAR, WEST, MAIN, MAIN, MAIN_BACK, EAST),  # going east: over to the other track
                (f"{c}-YE", p + CROSSOVER_FAR, EAST, MAIN_BACK, MAIN, MAIN_BACK, EAST),  # ...and back
                (f"{c}-XW", p + CROSSOVER_NEAR, EAST, MAIN_BACK, MAIN_BACK, MAIN, WEST),  # going west: over
                (f"{c}-YW", p - CROSSOVER_NEAR, WEST, MAIN, MAIN_BACK, MAIN, WEST),  # ...and back
            ):
                self.points.append(Switch(sid, st, pos, side, stem=stem, straight=straight, branch=branch, facing=facing))
                self.crossovers.add(sid)
            self.signals.append(Signal(f"{c}-E0", st, p - ENTRY_SIGNAL_OFFSET, EAST, MAIN))
            self.signals.append(Signal(f"{c}-W0", st, p + ENTRY_SIGNAL_OFFSET, WEST, MAIN_BACK))
            for number, (east, west) in ((1, (MAIN, MAIN_BACK)), (2, (MAIN_BACK, MAIN))):
                self.signals.append(Signal(f"{c}-E{number}", st, p + LOOP_HALF, EAST, east))
                self.signals.append(Signal(f"{c}-W{number}", st, p - LOOP_HALF, WEST, west))


def build_network(
    main: Line,
    side: Line | None = None,
    junction: Station | None = None,
    kind: str = "",
    west_side: Line | None = None,
    double: bool = False,
) -> JunctionNetwork:
    """Join the lines of a custom level into one network (see the top of this file)."""
    b = _Builder()
    b.track(main, Track(MAIN, "the main line", main.west_edge, main.east_edge, 0, open_start=True, open_end=True))
    if double:
        b.track(main, Track(MAIN_BACK, "the westbound track", main.west_edge, main.east_edge, 1, open_start=True, open_end=True))
        b.tracks[MAIN].name = "the eastbound track"
        b.double(main)
    else:
        b.single(main, MAIN)
    if kind in ("branch", "cross"):
        start = junction.pos + JUNCTION_OFFSET
        name = "the branch line" if kind == "branch" else "the crossing line"
        b.track(side, Track(BRANCH, name, start, side.east_edge, 0, open_end=True))
        b.single(side, BRANCH)
        b.points.append(Switch(junction_points(junction), junction, start, EAST, stem=MAIN, straight=MAIN, branch=BRANCH, facing=EAST))
    if kind == "cross":
        end = junction.pos - JUNCTION_OFFSET
        b.track(west_side, Track(BRANCH_WEST, "the crossing line", west_side.west_edge, end, 0, open_start=True))
        b.single(west_side, BRANCH_WEST)
        b.points.append(
            Switch(west_junction_points(junction), junction, end, WEST, stem=MAIN, straight=MAIN, branch=BRANCH_WEST, facing=WEST)
        )
    if kind == "separate":
        b.track(side, Track(SECOND, "the second line", side.west_edge, side.east_edge, 0, open_start=True, open_end=True))
        b.single(side, SECOND)
    lines = [line for line in (main, side, west_side) if line is not None]
    return JunctionNetwork(
        main.name,
        [st for line in lines for st in line.stations],
        b.tracks,
        b.points,
        b.signals,
        b.platforms,
        west_edge=min(t.start for t in b.tracks.values()),
        east_edge=max(t.end for t in b.tracks.values()),
        geo=Geo(path=[], start_label="", end_label=""),
        drivers_refuse_wrong_way=True,
        main=main,
        side=side,
        west_side=west_side,
        junction=junction,
        kind=kind,
        double=double,
        track_lines=b.track_lines,
        crossovers=b.crossovers,
    )


def route(net: JunctionNetwork, direction: int, second: bool) -> list[Station]:
    """The stations a train runs past, in the order it meets them. `second`: the train runs on
    the second line (along the branch, along the crossing line, or on the separate line)."""
    if not second or net.kind == "":
        stations = list(net.main.stations)
    elif net.kind == "branch":  # the main line as far as the junction, then the branch
        stations = [st for st in net.main.stations if st.pos <= net.junction.pos] + list(net.side.stations)
    elif net.kind == "cross":
        stations = list(net.west_side.stations) + [net.junction] + list(net.side.stations)
    else:
        stations = list(net.side.stations)
    return stations if direction == EAST else stations[::-1]


def ends(net: JunctionNetwork, direction: int, second: bool) -> tuple[str, str]:
    """The track a train appears on and the track it leaves the map on."""
    if second and net.kind == "branch":
        return (MAIN, BRANCH) if direction == EAST else (BRANCH, MAIN)
    if second and net.kind == "cross":
        return (BRANCH_WEST, BRANCH) if direction == EAST else (BRANCH, BRANCH_WEST)
    if second and net.kind == "separate":
        return SECOND, SECOND
    if net.double and direction == WEST:
        return MAIN_BACK, MAIN_BACK
    return MAIN, MAIN


def make_timetable(net: JunctionNetwork, name: str, direction: int, enters: float, second: bool) -> Train:
    """A train with its timetable: running time at line speed plus a small margin, like the
    timetables of the single lines (levels.make_timetable).

    Main-line trains run from one end of the main line to the other. Trains on the second line
    run along it: from the first station of the main line to the end of the branch, from one
    end of the crossing line to the other, or along the separate line.
    """
    train = Train(name, direction, enters, [])
    kind = train.type
    stations = route(net, direction, second)
    entry, exit_track = ends(net, direction, second)
    pos = net.tracks[entry].start if direction == EAST else net.tracks[entry].end
    time = enters
    for st in stations:
        if not st.has_loop and kind.stops != "all":
            continue
        passing = kind.stops == "none"
        target = st.stop_position(direction)
        time += abs(target - pos) / kind.max_speed + RUNNING_MARGIN
        arrive = time
        if not passing:
            time += kind.dwell_loop if st.has_loop else kind.dwell_halt
        options = net.platforms[st.code]
        if direction == WEST:  # trains one way use track 1 and the other way track 2, so they can cross
            options = options[::-1]
        train.stops.append(Stop(st, options[0], round(arrive), round(time), passing=passing, options=options))
        pos = target
    if stations:
        train.origin = stations[0].name
        train.destination = stations[-1].name
    train.entry_track = entry
    train.exit_tracks = (exit_track,)
    return train
