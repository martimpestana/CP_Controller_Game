"""A careful player for a line with a branch, used by the tests to show such a level can be won."""

from railgame.track import Signal


def track_is_clear(sim, train, signal) -> bool:
    """Is the single track beyond this signal free of trains coming the other way, as far as
    the platforms of the next crossing station?"""
    d = train.direction
    entry = signal.id.endswith("0")
    pieces, last, started = [], signal.pos, False
    for it in sim.walk(train, 60000, want=True):
        pos = train.pos + d * it.distance
        if it.obj is signal:
            started = True
            continue
        if not started:
            continue
        pieces.append((it.track, min(last, pos), max(last, pos)))
        last = pos
        if it.kind == "stop" and entry:
            break
        if it.kind == "facing" and not it.obj.id.endswith("-J") and it.obj.station is not signal.station:
            far = it.obj.station  # ...and on to the exit signals of that station
            a, b = sorted((pos, far.pos - d * 399))
            pieces += [(track, a, b) for track in sim.line.platforms[far.code]]
            break
        if it.kind in ("edge", "buffer"):
            break
    for other in sim.running_trains:
        if other.direction == d:
            continue
        for track, low, high in sim.body(other):
            if any(track == t and high >= a and low <= b for t, a, b in pieces):
                return False
    for s in sim.line.signals:
        if s.green and s.direction != d:
            if entry and s.station is signal.station:
                return False
            if any(s.track == t and a - 1 <= s.pos <= b + 1 for t, a, b in pieces):
                return False
    return True


def careful_junction_move(sim) -> None:
    """Do what the drivers ask: points at once, signals only when the way is clear."""
    line = sim.line
    for request in sorted(sim.requests.values(), key=lambda r: r.created):
        obj = next(o for o in (*line.signals, *line.points) if o.id == request.target_id)
        if not isinstance(obj, Signal):
            sim.toggle_point(obj.id)
        elif not obj.green and track_is_clear(sim, request.train, obj):
            sim.toggle_signal(obj.id)


def play(sim, seconds: int = 20000) -> None:
    for _ in range(seconds):
        if sim.over:
            return
        sim.advance(1)
        careful_junction_move(sim)
