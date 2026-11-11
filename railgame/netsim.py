"""The game rules on a network with several tracks (see network.py).

It works like simulation.Simulation and offers the same things to the game and the renderer
(advance, toggle_signal, toggle_point, requests, crash...), but trains follow named tracks
through any number of points instead of a single line with loops.

Two things are new:
- Trains keep their distance from the train in front going the same way (like the automatic
  protection on a busy line), so a fast train gets stuck behind a slow one: the player has to
  send them onto different tracks. Trains coming the other way are not protected: sending a
  train against the traffic (at the terminus, or over a crossover) can still end in a crash.
- Santa Apolónia is a terminus: trains to Lisbon end there, and trains from Lisbon start there,
  waiting at a platform until their departure time.
"""

import math
from dataclasses import dataclass

from railgame.network import Network, Switch
from railgame.simulation import LOOKAHEAD, POINT_LOCK, REQUEST_DISTANCE, SIGNAL_MARGIN, STEP, STOP_TOLERANCE, Blocker, Request
from railgame.track import EAST, Signal, Station
from railgame.train import MIN_DWELL, Stop, Train

SPACING = 70.0  # metres a train keeps behind the tail of the train in front
SPAWN_CLEAR = 500.0  # free track needed where a train appears at the edge of the map
APPEAR_BEFORE = 180.0  # departures from the terminus are at the platform this long before they leave
TERMINUS_TURNAROUND = 60.0  # an arriving train empties this long, then goes to the depot
LOST_WAIT = 90.0  # a train stuck at the wrong buffer stops is taken away after this long...
LOST_PENALTY = 600.0  # ...counting ten more minutes of delay


@dataclass
class Item:
    """Something a train will meet ahead: distance in metres, what it is, and the track the
    train is on when it gets there."""

    distance: float
    kind: str  # facing, trailing, merge, signal, stop, train, buffer, edge
    obj: object
    track: str


class NetSimulation:
    def __init__(self, line: Network, trains: list[Train], start_time: float, max_average_delay: float):
        self.line = line
        self.trains = trains
        self.time = start_time
        self.max_average_delay = max_average_delay
        self.requests: dict[tuple, Request] = {}
        self.crash: tuple[Train, Train] | None = None

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
        started = [t for t in self.trains if t.state != "waiting" or t.delay(self.time) > 0]
        if not started:
            return 0.0
        return sum(t.delay(self.time) for t in started) / len(started)

    # ------------------------------------------------------------------ where trains are

    def body(self, train: Train) -> list[tuple[str, float, float]]:
        """The pieces of track the train covers: (track, low, high), front piece first."""
        d = train.direction
        tail = train.tail
        pieces = []
        front, track = train.pos, train.track
        for switch, old, _new in reversed(train.switches_used):
            if (switch.pos - tail) * d <= 0:
                break
            low, high = sorted((switch.pos, front))
            pieces.append((track, low, high))
            front, track = switch.pos, old
        low, high = sorted((tail, front))
        pieces.append((track, low, high))
        return pieces

    def track_at(self, train: Train, pos: float) -> str:
        """The track under this point of the train (the rear may still be on the old track)."""
        track = train.track
        for switch, old, _new in reversed(train.switches_used):
            if (pos - switch.pos) * train.direction >= 0:
                return track
            track = old
        return track

    def platform_tracks(self, station: Station) -> tuple[str, ...]:
        return self.line.platforms.get(station.code, ())

    # ------------------------------------------------------------------ looking ahead

    def _role(self, switch: Switch, track: str, d: int) -> str | None:
        """How a train on `track` going in direction d meets these points, if at all."""
        if switch.facing == d:
            return "facing" if switch.stem == track else None
        if track == switch.stem and switch.straight == switch.stem:
            return "trailing"  # running through: only possible while they are set straight
        t = self.line.tracks[track]
        if track in (switch.straight, switch.branch) and abs(t.end_in(d) - switch.pos) < 1e-6:
            return "merge"  # this track ends here and joins the stem
        return None

    def walk(self, train: Train, limit: float, want: bool = False) -> list[Item]:
        """Everything the train meets in the next `limit` metres, following the points as they
        are set (or, with want=True, the way the driver would like them)."""
        items: list[Item] = []
        d = train.direction
        track, pos, base = train.track, train.pos, 0.0
        stop = train.next_stop()
        for _ in range(12):
            t = self.line.tracks[track]
            end = t.end_in(d)
            to_end = (end - pos) * d

            def ahead(x: float) -> float:
                return (x - pos) * d

            events: list[tuple[float, int, str, object]] = []
            for sw in self.line.points:
                a = ahead(sw.pos)
                if 1e-6 < a <= to_end + 1e-6:
                    role = self._role(sw, track, d)
                    if role:
                        events.append((a, 1, role, sw))
            for s in self.line.signals:
                if s.track == track and s.direction == d:
                    a = ahead(s.pos)
                    if 0 < a <= to_end + 1e-6:
                        events.append((a, 2, "signal", s))
            if stop is not None and track in self.platform_tracks(stop.station):
                a = ahead(stop.station.stop_position(d))
                if -STOP_TOLERANCE <= a <= to_end:
                    events.append((max(a, 0.0), 0, "stop", stop))
            for other in self.running_trains:
                if other is train or other.direction != d:
                    continue
                for piece, low, high in self.body(other):
                    if piece != track:
                        continue
                    a = ahead(low if d == EAST else high)
                    if 0 < a <= to_end + 1e-6:
                        events.append((a, 3, "train", other))
            events.sort(key=lambda e: (e[0], e[1]))
            next_track, switch_pos = None, None
            for a, _, kind, obj in events:
                dist = base + a
                if dist > limit:
                    return items
                items.append(Item(dist, kind, obj, track))
                if kind == "facing":
                    choice = obj.track
                    if want:
                        choice = self.wanted_branch(train, obj) or obj.track
                    if choice != track:
                        next_track, switch_pos = choice, obj.pos
                        break
                elif kind == "merge":
                    next_track, switch_pos = obj.stem, obj.pos
                    break
            if next_track is None:
                dist = base + to_end
                if dist <= limit:
                    items.append(Item(dist, "edge" if t.open_in(d) else "buffer", t, track))
                return items
            base += ahead(switch_pos)
            pos, track = switch_pos, next_track
        return items

    def _blocker(self, train: Train) -> Blocker | None:
        """The first thing that makes the train stop: its platform, a red signal, points set
        against it, the train in front or the buffer stop."""
        for it in self.walk(train, LOOKAHEAD):
            kind, obj = it.kind, it.obj
            if kind == "stop":
                return Blocker(it.distance, "stop", obj)
            if kind == "signal" and not obj.green:
                return Blocker(it.distance - SIGNAL_MARGIN, "signal", obj)
            if kind == "trailing" and obj.diverging:
                return Blocker(it.distance - SIGNAL_MARGIN, "point", obj)
            if kind == "merge" and obj.track != it.track:
                return Blocker(it.distance - SIGNAL_MARGIN, "point", obj)
            if kind == "train":
                return Blocker(it.distance - SPACING, "train", obj)
            if kind == "buffer":
                return Blocker(it.distance - 5, "buffer", obj)
        return None

    # ------------------------------------------------------------------ where drivers want to go

    def _reaches(self, track: str, pos: float, d: int, target: str, depth: int = 0) -> bool:
        """Can a train on `track` at `pos` going in direction d get to the `target` track?"""
        if track == target:
            return True
        if depth > 5:
            return False
        t = self.line.tracks[track]
        ahead = []
        for sw in self.line.points:
            a = (sw.pos - pos) * d
            if 1e-6 < a <= (t.end_in(d) - pos) * d + 1e-6:
                role = self._role(sw, track, d)
                if role in ("facing", "merge"):
                    ahead.append((a, role, sw))
        for _, role, sw in sorted(ahead, key=lambda e: e[0]):
            if role == "merge":
                return self._reaches(sw.stem, sw.pos, d, target, depth + 1)
            for b in (sw.straight, sw.branch):
                if b != track and self._reaches(b, sw.pos, d, target, depth + 1):
                    return True
            if sw.straight != track:
                return False
        return False

    def _stop_track(self, other: Train, station: Station) -> str | None:
        """The platform track another train is using, or heading for, at this station."""
        for piece, low, high in self.body(other):
            if piece in self.platform_tracks(station) and low <= station.pos + 400 and high >= station.pos - 400:
                return piece
        for it in self.walk(other, 1500):
            if it.kind == "stop" and it.obj.station is station:
                return it.track
        return None

    def _targets(self, train: Train, after: float) -> list[str]:
        """The tracks the driver wants to reach after this position: the platforms of the next
        stop beyond it (free ones first), or the tracks off the map."""
        d = train.direction
        for stop in train.stops:
            if stop.served or stop.departed_at is not None:
                continue
            if (stop.station.stop_position(d) - after) * d <= 0:
                continue
            options = list(stop.options or (stop.track,))
            taken = {
                self._stop_track(other, stop.station)
                for other in self.running_trains
                if other is not train
            }
            return [o for o in options if o not in taken] + [o for o in options if o in taken]
        return list(train.exit_tracks)

    def wanted_branch(self, train: Train, switch: Switch) -> str | None:
        for target in self._targets(train, switch.pos):
            for branch in (switch.straight, switch.branch):
                if self._reaches(branch, switch.pos, train.direction, target):
                    return branch
        return None

    # ------------------------------------------------------------------ player actions

    def toggle_signal(self, signal_id: str) -> str | None:
        if self.over:
            return "The level is over."
        signal = self.line.signal(signal_id)
        signal.green = not signal.green
        self._update_requests()
        return None

    def toggle_point(self, point_id: str) -> str | None:
        if self.over:
            return "The level is over."
        switch = self.line.point(point_id)
        tracks = {switch.stem, switch.straight, switch.branch}
        for train in self.running_trains:
            for piece, low, high in self.body(train):
                if piece in tracks and low - 5 <= switch.pos <= high + 5:
                    return f"Points {switch.id} are locked: {train.name} is passing over them."
            if train.speed > 0 and any(it.obj is switch for it in self.walk(train, POINT_LOCK)):
                return f"Points {switch.id} are locked: {train.name} is about to go over them."
        switch.diverging = not switch.diverging
        self._update_requests()
        return None

    # ------------------------------------------------------------------ time

    def advance(self, seconds: float) -> None:
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

    def _track_free(self, track: str, low: float, high: float) -> bool:
        for other in self.running_trains:
            for piece, a, b in self.body(other):
                if piece == track and b >= low and a <= high:
                    return False
        return True

    def _heading_into(self, track: str) -> bool:
        """Is a running train on its way onto this track (following the points as set)?"""
        for other in self.running_trains:
            if any(it.track == track for it in self.walk(other, 1500)):
                return True
        return False

    def _try_to_enter(self, train: Train) -> None:
        first = train.stops[0] if train.stops else None
        terminus = self.line.terminus
        if first is not None and terminus and first.station.code == terminus and train.direction == EAST:
            # A departure from the terminus: it waits at a free platform.
            if self.time < train.enter_time:
                return
            for track in first.options or (first.track,):
                t = self.line.tracks[track]
                if self._track_free(track, t.start, t.end) and not self._heading_into(track):
                    first.track = track
                    train.track = track
                    train.pos = first.station.stop_position(EAST)
                    train.speed = 0.0
                    train.stopped_since = self.time
                    train.state = "running"
                    return
            return
        if self.time < train.enter_time:
            return
        t = self.line.tracks[train.entry_track]
        d = train.direction
        edge = t.start if d == EAST else t.end
        low, high = sorted((edge, edge + d * SPAWN_CLEAR))
        if not self._track_free(train.entry_track, low, high):
            return
        train.track = train.entry_track
        train.pos = edge + d * train.length
        train.speed = train.max_speed * 0.8
        train.state = "running"

    def _move(self, train: Train, dt: float) -> None:
        blocker = self._blocker(train)
        if blocker is not None and blocker.kind == "stop" and blocker.distance <= STOP_TOLERANCE:
            self._dwell(train, blocker.obj)
            if train.state != "running":
                return
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
            if blocker is not None and blocker.kind == "buffer":
                self._lost(train)
            return
        kind = train.type
        safe = math.sqrt(2 * kind.braking * max(0.0, distance - STOP_TOLERANCE / 2))
        target = min(kind.max_speed, safe)
        if train.speed < target:
            train.speed = min(target, train.speed + kind.acceleration * dt)
        else:
            train.speed = target
        step = min(train.speed * dt, distance)
        if step <= 0:
            return
        old = train.pos
        train.pos += train.direction * step
        train.stopped_since = None
        self._passed(train, old)

        stop = train.pending_departure()
        while (
            stop is not None
            and stop.passing
            and (train.pos - stop.station.stop_position(train.direction)) * train.direction >= 0
        ):
            stop.served = True
            self._record_departure(train, stop)
            stop = train.pending_departure()
        if stop is not None and stop.served and stop.departed_at is None:
            self._record_departure(train, stop)

        t = self.line.tracks[train.track]
        end = t.end_in(train.direction)
        if t.open_in(train.direction) and (train.tail - end) * train.direction > 0:
            train.state = "finished"
            if train.final_delay is None:
                train.final_delay = train.delay(self.time)

    def _lost(self, train: Train) -> None:
        """A train sent the wrong way ended up at the buffer stops, where it has nothing to do.
        After a while it is taken away to the depot, with a big delay for its passengers."""
        if train.stopped_since is None:
            train.stopped_since = self.time
        if self.time >= train.stopped_since + LOST_WAIT:
            train.final_delay = train.delay(self.time) + LOST_PENALTY
            train.state = "finished"

    def _record_departure(self, train: Train, stop: Stop) -> None:
        stop.departed_at = self.time
        if stop is train.stops[-1]:
            train.final_delay = max(0.0, stop.departed_at - stop.depart)

    def _dwell(self, train: Train, stop: Stop) -> None:
        train.speed = 0.0
        if train.stopped_since is None:
            train.stopped_since = self.time
        last = stop is train.stops[-1]
        terminus = last and self.line.terminus == stop.station.code and train.direction != EAST
        if terminus:
            # The end of the journey: the delay is how late it arrived. Then it goes away.
            if train.final_delay is None:
                train.final_delay = max(0.0, train.stopped_since - stop.arrive)
            if self.time >= train.stopped_since + TERMINUS_TURNAROUND:
                stop.served = True
                stop.departed_at = self.time
                train.state = "finished"
            return
        ready_at = max(train.stopped_since + MIN_DWELL, stop.depart)
        if self.time >= ready_at:
            stop.served = True

    def _passed(self, train: Train, old: float) -> None:
        """Points and signals the front of the train went past in this step."""
        d = train.direction
        travelled = (train.pos - old) * d
        crossed = sorted(
            (sw for sw in self.line.points if 0 < (sw.pos - old) * d <= travelled),
            key=lambda sw: (sw.pos - old) * d,
        )
        for sw in crossed:
            role = self._role(sw, train.track, d)
            if role not in ("facing", "merge"):
                continue
            new = sw.stem if role == "merge" else sw.track
            if new != train.track:
                train.switches_used.append((sw, train.track, new))
                del train.switches_used[:-6]
                train.track = new
        for s in self.line.signals:
            if s.direction == d and 0 < (s.pos - old) * d <= travelled and self.track_at(train, s.pos) == s.track:
                s.green = False  # back to red once a train has passed
        stop = train.next_stop()
        if (
            stop is not None
            and train.track not in self.platform_tracks(stop.station)
            and (train.pos - stop.station.stop_position(d)) * d > 0
        ):
            stop.served = True  # on a track with no platform there: it cannot stop

    # ------------------------------------------------------------------ accidents

    def _check_collisions(self) -> None:
        trains = self.running_trains
        bodies = [self.body(t) for t in trains]
        for i, a in enumerate(trains):
            for j in range(i + 1, len(trains)):
                b = trains[j]
                for ta, la, ha in bodies[i]:
                    if any(tb == ta and hb >= la and lb <= ha for tb, lb, hb in bodies[j]):
                        self.crash = (a, b)
                        return

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
        name = self.line.track_name
        waiting_at: Stop | None = None
        for it in self.walk(train, REQUEST_DISTANCE, want=True):
            kind, obj = it.kind, it.obj
            if kind == "stop":
                ready_soon = (
                    it.distance <= STOP_TOLERANCE
                    and train.stopped_since is not None
                    and self.time >= max(train.stopped_since + MIN_DWELL, obj.depart) - 45
                )
                if not ready_soon:
                    break  # the driver only asks for the way out when nearly ready to leave
                waiting_at = obj
                continue
            if kind == "facing":
                want = self.wanted_branch(train, obj)
                if want is not None and want != obj.track:
                    out.append(((train.name, obj.id), f"Approaching {obj.station.name}. Please set points "
                                f"{obj.id} to {name(want)} for me.", obj.id))
            elif kind == "trailing" and obj.diverging:
                out.append(((train.name, obj.id), f"Points {obj.id} are set against me on {name(it.track)}. "
                            "Please set them back.", obj.id))
            elif kind == "merge" and obj.track != it.track:
                out.append(((train.name, obj.id), f"I'm on {name(it.track)} at {obj.station.name}. Please set "
                            f"points {obj.id} so I can get out.", obj.id))
            elif kind == "signal":
                if obj.green:
                    continue
                pending = train.pending_departure()
                standing = (
                    train.speed < 0.1
                    and pending is not None
                    and pending.station is obj.station
                    and train.track in self.platform_tracks(obj.station)
                )
                if standing or (waiting_at is not None and waiting_at.station is obj.station):
                    text = f"Ready to leave {obj.station.name} from {name(it.track)}. Signal {obj.id} to green, please."
                else:
                    text = f"Coming to {obj.station.name} on {name(it.track)}. Signal {obj.id} to green, please."
                out.append(((train.name, obj.id), text, obj.id))
                break  # one red signal at a time
            elif kind in ("train", "buffer", "edge"):
                break
        return out


def is_network(line) -> bool:
    return isinstance(line, Network)


__all__ = ["NetSimulation", "Signal", "is_network"]
