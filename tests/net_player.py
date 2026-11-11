"""A careful player for the Linha do Norte, used by the tests to show every level can be won."""

from railgame.track import EAST, WEST


def careful_net_move(sim) -> None:
    line = sim.line
    thrown = set()
    for request in sorted(sim.requests.values(), key=lambda r: r.created):
        target = request.target_id
        if any(p.id == target for p in line.points):
            if target not in thrown:  # first come, first served
                thrown.add(target)
                sim.toggle_point(target)
            continue
        signal = line.signal(target)
        if signal.id.startswith("SAP-") and signal.direction == EAST:
            # A departure: only when no train is coming into the station.
            if any(t.direction == WEST and t.pos < 1150 for t in sim.running_trains):
                continue
            if any(s.green for s in line.signals if s.id.startswith("SAP-") and s is not signal):
                continue
        elif signal.id == "SAP-E":
            # An arrival: only when no departure is still in the station throat.
            if any(t.direction == EAST and t.tail < 900 and t.speed > 0 for t in sim.running_trains):
                continue
            if any(s.green for s in line.signals if s.id.startswith("SAP-") and s.direction == EAST):
                continue
        if not signal.green:
            sim.toggle_signal(target)
