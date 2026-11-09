"""The game rules: moving trains, signals, points, drivers' requests and accidents.

This module has no graphics, so it can be tested with pytest.
"""

import math
from dataclasses import dataclass

from railgame.track import EAST, POINT_OFFSET, Line, Point, Signal, Station
from railgame.train import ACCELERATION, BRAKING, MAX_SPEED, MIN_DWELL, TRAIN_LENGTH, Stop, Train

STEP = 0.5  # seconds per simulation step (big time jumps are split into steps)
LOOKAHEAD = 4000.0  # how far ahead a driver looks, in metres
REQUEST_DISTANCE = 2500.0  # drivers start asking when they are this close
STOP_TOLERANCE = 3.0  # metres
SIGNAL_MARGIN = 15.0  # trains stop this far before a red signal or a wrong point
SPAWN_CLEARANCE = 2500.0  # a new train needs this much free track at the edge of the map
POINT_LOCK = 40.0  # points cannot move while a moving train is this close to them
POINT_LOCK_STOPPED = 5.0  # ...or while a train is standing on them (less than SIGNAL_MARGIN)


@dataclass
class Request:
    key: tuple
    train: Train
    text: str
    target_id: str  # the signal or point the driver is talking about
    created: float


@dataclass
class Blocker:
    distance: float  # metres from the front of the train
    kind: str  # "stop", "signal" or "point"
    obj: object


class Simulation:
    def __init__(self, line: Line, trains: list[Train], start_time: float, max_average_delay: float):
        self.line = line
        self.trains = trains
        self.time = start_time
        self.max_average_delay = max_average_delay
        self.requests: dict[tuple, Request] = {}
        self.crash: tuple[Train, Train] | None = None

    # ------------------------------------------------------------------ player actions

    def toggle_signal(self, signal_id: str) -> str | None:
        """Switch a signal between red and green. Returns an error message, or None if it worked."""
        if self.over:
            return "The level is over."
        signal = self.line.signal(signal_id)
        signal.green = not signal.green
        self._update_requests()
        return None

    def toggle_point(self, point_id: str) -> str | None:
        """Throw a set of points. They are locked while a train is on top of them."""
        if self.over:
            return "The level is over."
        point = self.line.point(point_id)
        for train in self.running_trains:
            if self._locks_point(train, point):
                return f"Points at {point.station.name} are locked: {train.name} is passing over them."
        point.diverging = not point.diverging
        self._update_requests()
        return None

    @staticmethod
    def _locks_point(train: Train, point: Point) -> bool:
        """A train locks the points under it, and the points just ahead of it while it moves.

        A train that has stopped in front of wrong points (SIGNAL_MARGIN away) must not lock
        them, otherwise nobody could ever set them for it and it would be stuck forever.
        """
        ahead = POINT_LOCK if train.speed > 0 else POINT_LOCK_STOPPED
        low, high = train.span
        if train.direction == EAST:
            low, high = low - POINT_LOCK_STOPPED, high + ahead
        else:
            low, high = low - ahead, high + POINT_LOCK_STOPPED
        return low <= point.pos <= high

    # ------------------------------------------------------------------ state

    @property
    def running_trains(self) -> list[Train]:
        return [t for t in self.trains if t.state == "running"]

    @property
    def finished(self) -> bool:
        return all(t.state == "finished" for t in self.trains)

    @property
    def over(self) -> bool:
        return self.crash is not None or self.finished

    @property
    def passed(self) -> bool:
        return self.finished and self.crash is None and self.average_delay() <= self.max_average_delay

    def average_delay(self) -> float:
        """Average delay in seconds of the trains that have already appeared."""
        started = [t for t in self.trains if t.state != "waiting"]
        if not started:
            return 0.0
        return sum(t.delay(self.time) for t in started) / len(started)

    # ------------------------------------------------------------------ time

    def advance(self, seconds: float) -> None:
        """Move the game forward. Large jumps are split into small steps."""
        while seconds > 1e-9 and not self.over:
            dt = min(STEP, seconds)
            self._step(dt)
            seconds -= dt

    def _step(self, dt: float) -> None:
        self.time += dt
        for train in self.trains:
            if train.state == "waiting":
                self._try_to_enter(train)
            elif train.state == "running":
                self._move(train, dt)
        self._check_collisions()
        self._update_requests()

    def _try_to_enter(self, train: Train) -> None:
        if self.time < train.enter_time:
            return
        edge = self.line.west_edge if train.direction == EAST else self.line.east_edge
        # The stretch between the edge of the map and the first station is outside the
        # player's control, so a new train only appears when it is completely free.
        loops = sorted((st for st in self.line.stations if st.has_loop), key=lambda st: st.pos * train.direction)
        first = loops[0]
        inner = first.pos - train.direction * POINT_OFFSET
        low_edge, high_edge = sorted((edge - train.direction * SPAWN_CLEARANCE, inner))
        for other in self.running_trains:
            low, high = other.span
            if high >= low_edge and low <= high_edge:
                return
        for s in self.line.signals:
            if s.station is first and s.direction == -train.direction and s.track and s.green:
                # A train has been given the way out towards us. Only wait if there is a train
                # that can still use that signal: a green signal left behind with nobody to use
                # it would otherwise keep the new train off the map forever.
                if any(
                    other.direction == s.direction and (other.pos - s.pos) * train.direction > 0
                    for other in self.running_trains
                ):
                    return
        train.pos = edge + train.direction * TRAIN_LENGTH
        train.speed = MAX_SPEED * 0.8
        train.track = 1
        train.state = "running"

    # ------------------------------------------------------------------ looking ahead

    def _objects_ahead(self, train: Train) -> list[tuple[float, str, object]]:
        d = train.direction
        items: list[tuple[float, str, object]] = []
        for p in self.line.points:
            ahead = (p.pos - train.pos) * d
            if 0 < ahead <= LOOKAHEAD:
                items.append((ahead, "point", p))
        for s in self.line.signals:
            ahead = (s.pos - train.pos) * d
            if s.direction == d and 0 < ahead <= LOOKAHEAD:
                items.append((ahead, "signal", s))
        stop = train.next_stop()
        if stop is not None:
            ahead = (stop.station.stop_position(d) - train.pos) * d
            if ahead <= LOOKAHEAD:
                items.append((max(ahead, 0.0), "stop", stop))
        items.sort(key=lambda item: item[0])
        return items

    def _blocker(self, train: Train) -> Blocker | None:
        """The first thing that will make the train stop: a platform, a red signal or wrong points."""
        track = train.track
        for ahead, kind, obj in self._objects_ahead(train):
            if kind == "stop":
                return Blocker(ahead, kind, obj)
            if kind == "signal":
                if obj.applies_to(train.direction, track) and not obj.green:
                    return Blocker(ahead - SIGNAL_MARGIN, kind, obj)
            elif kind == "point":
                if obj.is_facing(train.direction):
                    track = obj.track
                else:
                    if obj.track != track:
                        return Blocker(ahead - SIGNAL_MARGIN, kind, obj)
                    track = 1
        return None

    # ------------------------------------------------------------------ movement

    def _move(self, train: Train, dt: float) -> None:
        blocker = self._blocker(train)
        if blocker is not None and blocker.kind == "stop" and blocker.distance <= STOP_TOLERANCE:
            self._dwell(train, blocker.obj)
            blocker = self._blocker(train)

        distance = math.inf if blocker is None else max(0.0, blocker.distance)
        pending = train.pending_departure()
        if (
            blocker is not None
            and blocker.kind == "signal"
            and pending is not None
            and pending.served
            and blocker.obj.station is pending.station
        ):
            distance = 0.0  # ready to go, but waits at the platform until the exit signal clears
        if distance <= STOP_TOLERANCE:
            train.speed = 0.0
            return
        # The fastest speed from which the train can still stop in time.
        safe = math.sqrt(2 * BRAKING * max(0.0, distance - STOP_TOLERANCE / 2))
        target = min(MAX_SPEED, safe)
        if train.speed < target:
            train.speed = min(target, train.speed + ACCELERATION * dt)
        else:
            train.speed = target
        step = min(train.speed * dt, distance)
        if step <= 0:
            return

        old = train.pos
        train.pos += train.direction * step
        train.stopped_since = None
        self._passed_objects(train, old)

        stop = train.pending_departure()
        if stop is not None and stop.served and stop.departed_at is None:
            stop.departed_at = self.time
            if stop is train.stops[-1]:
                train.final_delay = max(0.0, stop.departed_at - stop.depart)

        edge = self.line.east_edge if train.direction == EAST else self.line.west_edge
        if (train.tail - edge) * train.direction > 0:
            train.state = "finished"
            if train.final_delay is None:
                train.final_delay = train.delay(self.time)

    def _dwell(self, train: Train, stop: Stop) -> None:
        train.speed = 0.0
        if train.stopped_since is None:
            train.stopped_since = self.time
        ready_at = max(train.stopped_since + MIN_DWELL, stop.depart)
        if self.time >= ready_at:
            stop.served = True

    def _passed_objects(self, train: Train, old: float) -> None:
        """Handle everything the front of the train went past during this step."""
        low, high = sorted((old, train.pos))
        passed = [p for p in self.line.points if low < p.pos <= high or low <= p.pos < high]
        passed += [s for s in self.line.signals if low < s.pos <= high or low <= s.pos < high]
        passed.sort(key=lambda o: (o.pos - old) * train.direction)
        for obj in passed:
            if isinstance(obj, Point):
                train.track = obj.track if obj.is_facing(train.direction) else 1
            elif isinstance(obj, Signal) and obj.applies_to(train.direction, train.track):
                obj.green = False  # signals go back to red once a train has passed

    # ------------------------------------------------------------------ accidents

    def _check_collisions(self) -> None:
        trains = self.running_trains
        for i, a in enumerate(trains):
            for b in trains[i + 1 :]:
                if self._collide(a, b):
                    self.crash = (a, b)
                    return

    def _collide(self, a: Train, b: Train) -> bool:
        a_low, a_high = a.span
        b_low, b_high = b.span
        low, high = max(a_low, b_low), min(a_high, b_high)
        if low > high:
            return False
        if a.track != b.track:
            station = self.line.loop_station_at((low + high) / 2)
            if station is not None and abs((low + high) / 2 - station.pos) < POINT_OFFSET:
                return False  # side by side on different platform tracks
        return True

    # ------------------------------------------------------------------ drivers' requests

    def _update_requests(self) -> None:
        wanted: dict[tuple, tuple[Train, str, str]] = {}
        for train in self.running_trains:
            for key, text, target in self._requests_for(train):
                wanted[key] = (train, text, target)
        for key in list(self.requests):
            if key not in wanted:
                del self.requests[key]
        for key, (train, text, target) in wanted.items():
            if key in self.requests:
                self.requests[key].text = text
            else:
                self.requests[key] = Request(key, train, text, target, self.time)

    def _requests_for(self, train: Train) -> list[tuple[tuple, str, str]]:
        out = []
        track = train.track
        waiting_at: Stop | None = None
        asked_for_signal = False
        for ahead, kind, obj in self._objects_ahead(train):
            if ahead > REQUEST_DISTANCE:
                break
            if kind == "stop":
                if asked_for_signal:
                    break
                ready_soon = (
                    ahead <= STOP_TOLERANCE
                    and train.stopped_since is not None
                    and self.time >= max(train.stopped_since + MIN_DWELL, obj.depart) - 45
                )
                if not ready_soon:
                    break  # the driver only asks for the way out when nearly ready to leave
                waiting_at = obj
                continue
            if kind == "point":
                point: Point = obj
                if point.is_facing(train.direction):
                    planned = train.planned_track(point.station)
                    if planned is not None and planned != point.track:
                        out.append(
                            (
                                (train.name, point.id),
                                f"Approaching {point.station.name}. Please set the points to "
                                f"track {planned} for me.",
                                point.id,
                            )
                        )
                        planned_track = planned
                    else:
                        planned_track = point.track
                    track = planned_track
                else:
                    if point.track != track:
                        out.append(
                            (
                                (train.name, point.id),
                                f"I'm on track {track} at {point.station.name}. Please set the "
                                f"points so I can get out.",
                                point.id,
                            )
                        )
                    track = 1
            elif kind == "signal":
                signal: Signal = obj
                if not signal.applies_to(train.direction, track):
                    continue
                if signal.green:
                    continue
                if asked_for_signal:
                    break  # one red signal at a time
                if signal.is_entry:
                    text = f"Approaching {signal.station.name}. Signal {signal.id} to green, please."
                elif waiting_at is not None and waiting_at.station is signal.station or (
                    train.speed < 0.1 and self.line.loop_station_at(train.pos) is signal.station
                ):
                    text = (
                        f"Ready to leave {signal.station.name} on track {track}. "
                        f"Signal {signal.id} to green, please."
                    )
                else:
                    text = f"Coming through {signal.station.name}. Signal {signal.id} to green, please."
                out.append(((train.name, signal.id), text, signal.id))
                if not signal.is_entry:
                    break
                # Behind a red entry signal the driver still asks for the points to be set.
                asked_for_signal = True
        return out
