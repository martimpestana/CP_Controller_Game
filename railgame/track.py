"""The railway itself: stations, points (switches) and signals.

All positions are in metres along the line, measured from Faro.
Positive direction is EAST (towards Tavira), negative is WEST (towards Faro).
"""

from dataclasses import dataclass

EAST = 1
WEST = -1

# Layout of a crossing station (distances from the station centre, in metres).
# The whole station area is drawn as a fixed-size box on the map.
LOOP_HALF = 400  # station tracks 1 and 2 run side by side for 400 m each way
POINT_OFFSET = 600  # the two sets of points sit 600 m each side of the centre
ENTRY_SIGNAL_OFFSET = 900  # entry signals protect the points from outside
ZONE_HALF = 1000  # half the length of the station area


@dataclass
class Station:
    name: str
    code: str
    pos: float
    has_loop: bool  # True: crossing station with two tracks. False: simple halt.

    def stop_position(self, direction: int) -> float:
        """Where the head of a train stops, so that the train sits centred in the platform."""
        return self.pos + direction * 75


@dataclass
class Point:
    """A set of points (in Portuguese: agulha). Straight leads to track 1, diverging to track 2."""

    id: str
    station: Station
    pos: float
    side: int  # WEST or EAST end of the station
    diverging: bool = False

    @property
    def track(self) -> int:
        return 2 if self.diverging else 1

    def is_facing(self, direction: int) -> bool:
        """A train meets facing points when it enters the station, and trailing points when it leaves."""
        return self.side == -direction


@dataclass
class Signal:
    """A two-aspect signal. Red means stop, green means go."""

    id: str
    station: Station
    pos: float
    direction: int  # the direction of the trains this signal talks to
    track: int | None  # None: entry signal on the single line. 1 or 2: exit signal of that track.
    green: bool = False

    def applies_to(self, direction: int, track: int) -> bool:
        return self.direction == direction and (self.track is None or self.track == track)

    @property
    def is_entry(self) -> bool:
        return self.track is None


@dataclass
class Line:
    name: str
    stations: list[Station]
    points: list[Point]
    signals: list[Signal]
    west_edge: float  # where the map ends on each side
    east_edge: float

    def station(self, code: str) -> Station:
        for st in self.stations:
            if st.code == code:
                return st
        raise KeyError(code)

    def signal(self, signal_id: str) -> Signal:
        for s in self.signals:
            if s.id == signal_id:
                return s
        raise KeyError(signal_id)

    def point(self, point_id: str) -> Point:
        for p in self.points:
            if p.id == point_id:
                return p
        raise KeyError(point_id)

    def loop_station_at(self, pos: float) -> Station | None:
        """The crossing station whose area contains this position, if any."""
        for st in self.stations:
            if st.has_loop and abs(pos - st.pos) <= ZONE_HALF:
                return st
        return None


def build_line(name: str, stations: list[Station], west_edge: float, east_edge: float) -> Line:
    """Create the points and signals for every crossing station automatically."""
    points: list[Point] = []
    signals: list[Signal] = []
    for st in stations:
        if not st.has_loop:
            continue
        points.append(Point(f"{st.code}-PW", st, st.pos - POINT_OFFSET, WEST))
        points.append(Point(f"{st.code}-PE", st, st.pos + POINT_OFFSET, EAST))
        # Entry signals, one for each direction, in front of the points.
        signals.append(Signal(f"{st.code}-E0", st, st.pos - ENTRY_SIGNAL_OFFSET, EAST, None))
        signals.append(Signal(f"{st.code}-W0", st, st.pos + ENTRY_SIGNAL_OFFSET, WEST, None))
        # Exit signals at the end of each platform track.
        for track in (1, 2):
            signals.append(Signal(f"{st.code}-E{track}", st, st.pos + LOOP_HALF, EAST, track))
            signals.append(Signal(f"{st.code}-W{track}", st, st.pos - LOOP_HALF, WEST, track))
    return Line(name, stations, points, signals, west_edge, east_edge)


def algarve_faro_tavira() -> Line:
    """Linha do Algarve between Faro and Tavira (single track, trains cross at stations)."""
    stations = [
        Station("Faro", "FAR", 0, True),
        Station("Bom João", "BJO", 1900, False),
        Station("Olhão", "OLH", 8600, True),
        Station("Fuseta-A", "FUA", 16000, False),
        Station("Fuseta", "FUS", 17400, True),
        Station("Livramento", "LIV", 23000, False),
        Station("Tavira", "TAV", 30000, True),
    ]
    return build_line("Linha do Algarve", stations, west_edge=-2500, east_edge=32500)
