"""Trains and their timetables."""

from dataclasses import dataclass, field

from railgame.track import EAST, Station

TRAIN_LENGTH = 150.0  # metres
MAX_SPEED = 25.0  # metres per second (90 km/h)
ACCELERATION = 0.6  # m/s²
BRAKING = 0.8  # m/s²
MIN_DWELL = 30.0  # seconds a train always stays at a platform


@dataclass
class Stop:
    station: Station
    track: int  # the platform track the train is planned to use (1 or 2)
    arrive: float  # scheduled times, in seconds since midnight
    depart: float
    served: bool = False  # passengers are on board and the train is ready to leave
    departed_at: float | None = None


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

    @property
    def tail(self) -> float:
        return self.pos - self.direction * TRAIN_LENGTH

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
        for stop in self.stops:
            if not stop.served:
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
