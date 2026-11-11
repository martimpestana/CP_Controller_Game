"""Trains and their timetables."""

from dataclasses import dataclass, field

from railgame.track import EAST, Station

TRAIN_LENGTH = 150.0  # metres (a regional train)
MAX_SPEED = 25.0  # metres per second (90 km/h)
ACCELERATION = 0.6  # m/s²
BRAKING = 0.8  # m/s²
MIN_DWELL = 30.0  # seconds a train always stays at a platform


@dataclass(frozen=True)
class TrainType:
    """What kind of train it is. The first word of a train's name picks its type ("M 52101")."""

    code: str
    name: str
    max_speed: float = MAX_SPEED  # m/s
    length: float = TRAIN_LENGTH  # metres
    acceleration: float = ACCELERATION
    braking: float = BRAKING
    stops: str = "all"  # "all" stations, only the crossing stations ("loops"), or "none" (passes through)
    dwell_loop: float = 60  # scheduled stop at a crossing station, in seconds
    dwell_halt: float = 30  # scheduled stop at a halt
    long_stops: tuple[str, ...] = ()  # station codes where the train stays longer
    long_dwell: float = 0


# To add a new kind of train (Intercidades, Alfa Pendular...), add it here.
TRAIN_TYPES = {
    "R": TrainType("R", "Regional"),
    "IR": TrainType("IR", "Inter-Regional", stops="loops"),
    "M": TrainType(
        "M", "Freight", max_speed=17.0, length=450.0, acceleration=0.25, braking=0.5, stops="none"
    ),
    "H": TrainType(
        "H",
        "Historic steam train",
        max_speed=14.0,
        length=200.0,
        acceleration=0.3,
        stops="loops",
        dwell_loop=90,
        long_stops=("PIN",),
        long_dwell=300,
    ),
    # The Linha do Norte in Lisbon (network.py). Fast trains only stop at the big stations.
    "AP": TrainType("AP", "Alfa Pendular", max_speed=40.0, length=210.0, acceleration=0.7, braking=0.9, stops="loops", dwell_loop=60),
    "IC": TrainType("IC", "Intercidades", max_speed=33.0, length=210.0, acceleration=0.45, braking=0.7, stops="loops", dwell_loop=60),
}


@dataclass
class Stop:
    station: Station
    track: int  # the platform track the train is planned to use (1 or 2)
    arrive: float  # scheduled times, in seconds since midnight
    depart: float
    served: bool = False  # passengers are on board and the train is ready to leave
    departed_at: float | None = None
    passing: bool = False  # the train runs through without stopping (scheduled passing time)
    options: tuple[str, ...] = ()  # on a network: the platform tracks it may use, best first


@dataclass
class Train:
    name: str
    direction: int
    enter_time: float  # when it appears at the edge of the map
    stops: list[Stop]
    pos: float = 0.0  # position of the front of the train
    speed: float = 0.0
    track: int = 1  # 1 on the single line or station track 1, 2 on station track 2
    state: str = "waiting"  # waiting -> running -> finished
    stopped_since: float | None = None
    final_delay: float | None = None
    # (position, track) where the front of the train last changed track, newest last.
    track_changes: list[tuple[float, int]] = field(default_factory=list)
    # Only used on networks (network.py), where tracks have names instead of numbers:
    origin: str = ""  # where it comes from and where it goes, for the panel
    destination: str = ""
    entry_track: str = ""  # the track it appears on
    exit_tracks: tuple[str, ...] = ()  # the tracks it may leave the map on, best first
    switches_used: list = field(default_factory=list)  # (switch, old track, new track), newest last

    @property
    def kind(self) -> str:
        return self.name.split()[0]

    @property
    def type(self) -> TrainType:
        return TRAIN_TYPES.get(self.kind, TRAIN_TYPES["R"])

    @property
    def length(self) -> float:
        return self.type.length

    @property
    def max_speed(self) -> float:
        return self.type.max_speed

    @property
    def tail(self) -> float:
        return self.pos - self.direction * self.length

    @property
    def span(self) -> tuple[float, float]:
        return (min(self.pos, self.tail), max(self.pos, self.tail))

    @property
    def arrow(self) -> str:
        return "→" if self.direction == EAST else "←"

    def track_at(self, pos: float) -> int:
        """The track under a point of the train's body (the tail may still be on the old track)."""
        for change_pos, track in reversed(self.track_changes):
            if (pos - change_pos) * self.direction >= 0:
                return track
        return self.track_changes[0][1] ^ 3 if self.track_changes else self.track

    def next_stop(self) -> Stop | None:
        """The next station where the train really stops (it runs through passing stops)."""
        for stop in self.stops:
            if not stop.served and not stop.passing:
                return stop
        return None

    def pending_departure(self) -> Stop | None:
        for stop in self.stops:
            if stop.departed_at is None:
                return stop
        return None

    def planned_track(self, station: Station) -> int | None:
        for stop in self.stops:
            if stop.station is station and stop.departed_at is None:
                return stop.track
        return None

    def delay(self, now: float) -> float:
        """Current delay in seconds (never negative)."""
        if self.final_delay is not None:
            return self.final_delay
        recorded = 0.0
        for stop in self.stops:
            if stop.departed_at is not None:
                recorded = max(0.0, stop.departed_at - stop.depart)
        pending = self.pending_departure()
        if pending is not None:
            recorded = max(recorded, now - pending.depart)
        return max(0.0, recorded)
