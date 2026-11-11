import pytest

from net_player import careful_net_move
from railgame.levels import LEVELS, TrainPlan, build_level, make_net_timetable
from railgame.netsim import LOST_PENALTY, NetSimulation
from railgame.network import lisboa_norte
from railgame.track import EAST, WEST


def run(sim, seconds, player=True):
    for _ in range(seconds):
        if sim.over:
            break
        if player:
            careful_net_move(sim)
        sim.advance(1)


def sim_with(*plans, start="06:58"):
    from railgame.levels import clock

    line = lisboa_norte()
    trains = [make_net_timetable(line, plan) for plan in plans]
    return NetSimulation(line, trains, clock(start), 180)


def grant_all(sim):
    """Do every request at once, without thinking (for single-train tests)."""
    for request in list(sim.requests.values()):
        target = request.target_id
        if any(p.id == target for p in sim.line.points):
            sim.toggle_point(target)
        elif not sim.line.signal(target).green:
            sim.toggle_signal(target)


@pytest.mark.parametrize("number", range(1, len(LEVELS["lisboa"]) + 1))
def test_careful_player_passes_every_lisbon_level(number):
    _, sim = build_level("lisboa", number)
    run(sim, 3 * 3600)
    assert sim.crash is None
    assert sim.passed


def test_every_track_meets_its_neighbours():
    line = lisboa_norte()
    for sw in line.points:
        for track in (sw.stem, sw.straight, sw.branch):
            assert line.tracks[track].contains(sw.pos), (sw.id, track)
    for s in line.signals:
        assert line.tracks[s.track].contains(s.pos), s.id


def test_departure_waits_at_its_platform_until_the_signal_is_green():
    sim = sim_with(TrainPlan("R 1", EAST, "07:00"))
    run(sim, 300, player=False)
    train = sim.trains[0]
    assert train.state == "running" and train.track == "P2" and train.speed == 0
    assert any(r.target_id == "SAP-2" for r in sim.requests.values())
    sim.toggle_signal("SAP-2")
    run(sim, 30, player=False)
    assert train.pos > 400 and train.track == "A"


def test_alfa_asks_for_the_fast_track_and_regional_for_the_slow_one():
    sim = sim_with(TrainPlan("AP 1", EAST, "07:00"))
    ap = sim.trains[0]
    for _ in range(600):
        grant_all(sim)
        sim.advance(1)
        if ap.track == "A2":
            break
    assert ap.track == "A2"
    sim = sim_with(TrainPlan("R 1", EAST, "07:00"))
    r = sim.trains[0]
    for _ in range(600):
        grant_all(sim)
        sim.advance(1)
        if r.pos > 2100:
            break
    assert r.track == "A"


def test_arrival_ends_at_the_terminus_and_counts_its_arrival_delay():
    sim = sim_with(TrainPlan("R 2", WEST, "07:00"))
    for _ in range(1200):
        grant_all(sim)
        sim.advance(1)
    train = sim.trains[0]
    assert train.state == "finished"
    assert train.stops[-1].station.code == "SAP"
    assert train.final_delay is not None and train.final_delay < 60


def test_a_fast_train_waits_behind_a_slow_one_on_the_same_track():
    sim = sim_with(TrainPlan("R 1", EAST, "07:00"), TrainPlan("AP 2", EAST, "07:00"))
    r, ap = sim.trains
    for _ in range(900):
        grant_all(sim)
        sim.advance(1)
        if r.state == "running" and ap.state == "running" and r.track == ap.track:
            gap = abs(r.tail - ap.pos)
            assert gap > 40 or ap.speed == 0  # never runs into the back of the regional
    assert sim.crash is None


def test_sending_a_train_against_the_traffic_ends_in_a_crash():
    # A departure from platform 3 runs north on the southbound track if the crossover is
    # left alone, straight into an arriving train.
    sim = sim_with(TrainPlan("R 1", EAST, "07:00", platform="P3"), TrainPlan("R 2", WEST, "07:00"))
    dep, arr = sim.trains
    for _ in range(900):
        for request in list(sim.requests.values()):
            if request.target_id in ("SAP-3", "SAP-E", "ORI-B"):
                if not sim.line.signal(request.target_id).green:
                    sim.toggle_signal(request.target_id)
        sim.advance(1)
        if sim.crash:
            break
    assert sim.crash is not None


def test_points_are_locked_under_a_train():
    sim = sim_with(TrainPlan("R 1", EAST, "07:00"))
    run(sim, 300, player=False)
    sim.toggle_signal("SAP-2")
    train = sim.trains[0]
    while train.pos < 425:
        sim.advance(0.5)
    assert sim.toggle_point("SAP-A") is not None


def test_a_train_lost_at_the_buffer_stops_is_taken_away_with_a_penalty():
    # A freight for the Cintura line that nobody sends onto it ends up at Santa Apolónia.
    sim = sim_with(TrainPlan("M 9", WEST, "07:00", to="CIN"))
    for _ in range(1500):
        for request in list(sim.requests.values()):
            if any(p.id == request.target_id for p in sim.line.points):
                continue  # never set the points for it
            if not sim.line.signal(request.target_id).green:
                sim.toggle_signal(request.target_id)
        sim.advance(1)
    train = sim.trains[0]
    assert train.state == "finished"
    assert train.final_delay >= LOST_PENALTY
