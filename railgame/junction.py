"""A line with a branch: a second line that leaves the first one at one of its stations.

The level editor makes these (custom.py). The first line is single track with crossing
stations, exactly like the game's own lines (track.py). At the junction station a set of points
just past the station sends trains onto the branch, which is single track too and may have
crossing stations and halts of its own.

For the rules it is a Network (network.py) played by NetSimulation: the main line is one long
track, every crossing station adds a second track beside it, and the branch is one more track
that starts at the junction points. For the map it is two ordinary lines, `main` and `side`,
drawn by junctionrender.py.

Positions are metres along the main line. The branch carries on from the junction: a station
6 km down the branch is 6 km further than the junction station.
"""

from dataclasses import dataclass

from railgame.network import Geo, Network, Switch, Track
from railgame.track import EAST, ENTRY_SIGNAL_OFFSET, LOOP_HALF, POINT_OFFSET, WEST, ZONE_HALF, Line, Signal, Station
from railgame.train import Stop, Train

MAIN = "M"  # the track of the main line
BRANCH = "B"  # the track of the branch line
JUNCTION_OFFSET = ZONE_HALF  # the junction points are this far past the centre of their station
RUNNING_MARGIN = 60  # seconds of slack added to each section of the timetable (as on the other lines)


def loop_track(code: str) -> str:
    """The id of the second track of a crossing station."""
    return f"{code}-2"


@dataclass
class JunctionNetwork(Network):
    main: Line | None = None  # the first line on its own
    side: Line | None = None  # the branch as a line of its own, from the junction points to its end
    junction: Station | None = None  # the station of the main line where the branch leaves

    def on_branch(self, track_id: str) -> bool:
        """Is this track part of the branch (and not of the main line)?"""
        return track_id == BRANCH or any(track_id == loop_track(st.code) for st in self.side.stations)

    def is_loop(self, track_id: str) -> bool:
        return track_id not in (MAIN, BRANCH)

    def line_of(self, station: Station) -> Line:
        return self.side if any(station is st for st in self.side.stations) else self.main


def junction_points(junction: Station) -> str:
    return f"{junction.code}-J"


def build_network(main: Line, side: Line, junction: Station) -> JunctionNetwork:
    """Join two lines into one network. `side` starts at the junction points and its stations
    have positions that carry on from there (see the top of this file)."""
    start = junction.pos + JUNCTION_OFFSET
    tracks = {
        MAIN: Track(MAIN, "the main line", main.west_edge, main.east_edge, 0, open_start=True, open_end=True),
        BRANCH: Track(BRANCH, "the branch line", start, side.east_edge, 0, open_end=True),
    }
    points: list[Switch] = []
    signals: list[Signal] = []
    platforms: dict[str, tuple[str, ...]] = {}
    for line, stem in ((main, MAIN), (side, BRANCH)):
        for st in line.stations:
            if not st.has_loop:
                platforms[st.code] = (stem,)
                continue
            loop = loop_track(st.code)
            tracks[loop] = Track(loop, "track 2", st.pos - POINT_OFFSET, st.pos + POINT_OFFSET, 1)
            platforms[st.code] = (stem, loop)
            points.append(Switch(f"{st.code}-PW", st, st.pos - POINT_OFFSET, WEST, stem=stem, straight=stem, branch=loop, facing=EAST))
            points.append(Switch(f"{st.code}-PE", st, st.pos + POINT_OFFSET, EAST, stem=stem, straight=stem, branch=loop, facing=WEST))
            # Entry signals in front of the points, exit signals at the end of each platform.
            signals.append(Signal(f"{st.code}-E0", st, st.pos - ENTRY_SIGNAL_OFFSET, EAST, stem))
            signals.append(Signal(f"{st.code}-W0", st, st.pos + ENTRY_SIGNAL_OFFSET, WEST, stem))
            for number, track in ((1, stem), (2, loop)):
                signals.append(Signal(f"{st.code}-E{number}", st, st.pos + LOOP_HALF, EAST, track))
                signals.append(Signal(f"{st.code}-W{number}", st, st.pos - LOOP_HALF, WEST, track))
    points.append(Switch(junction_points(junction), junction, start, EAST, stem=MAIN, straight=MAIN, branch=BRANCH, facing=EAST))
    return JunctionNetwork(
        main.name,
        list(main.stations) + list(side.stations),
        tracks,
        points,
        signals,
        platforms,
        west_edge=main.west_edge,
        east_edge=max(main.east_edge, side.east_edge),
        geo=Geo(path=[], start_label="", end_label=""),
        drivers_refuse_wrong_way=True,
        main=main,
        side=side,
        junction=junction,
    )


def route(net: JunctionNetwork, direction: int, branch: bool) -> list[Station]:
    """The stations a train runs past, in the order it meets them."""
    if not branch:
        stations = list(net.main.stations)
    else:  # the main line as far as the junction, then the branch
        stations = [st for st in net.main.stations if st.pos <= net.junction.pos] + list(net.side.stations)
    return stations if direction == EAST else stations[::-1]


def make_timetable(net: JunctionNetwork, name: str, direction: int, enters: float, branch: bool) -> Train:
    """A train with its timetable: running time at line speed plus a small margin, like the
    timetables of the single lines (levels.make_timetable).

    Main-line trains run from one end of the main line to the other. Branch trains run between
    the first station of the main line and the end of the branch.
    """
    train = Train(name, direction, enters, [])
    kind = train.type
    stations = route(net, direction, branch)
    if direction == EAST:
        entry, pos = MAIN, net.main.west_edge
        exit_track = BRANCH if branch else MAIN
    else:
        entry = BRANCH if branch else MAIN
        pos = net.tracks[entry].end
        exit_track = MAIN
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
    train.origin = stations[0].name
    train.destination = stations[-1].name
    train.entry_track = entry
    train.exit_tracks = (exit_track,)
    return train
