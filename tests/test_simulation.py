import pytest

from railgame.levels import LEVELS, build_level, clock, make_timetable, TrainPlan
from railgame.simulation import Simulation
from railgame.track import EAST, LOOP_HALF, WEST, algarve_faro_tavira
from railgame.train import Stop, Train


def single_train_sim(direction=EAST):
    line = algarve_faro_tavira()
    train = make_timetable(line, TrainPlan("T1", direction, "08:00"))
    return Simulation(line, [train], clock("08:00"), 180), train


def run_until(sim, condition, limit=7200):
    for _ in range(limit):
        if condition():
            return True
        sim.advance(1)
    return condition()


def test_line_has_points_and_signals_for_each_crossing_station():
    line = algarve_faro_tavira()
    crossing = [st for st in line.stations if st.has_loop]
    assert len(line.points) == 2 * len(crossing)
    assert len(line.signals) == 6 * len(crossing)
    assert all(not s.green for s in line.signals)


def test_train_stops_at_red_entry_signal():
    sim, train = single_train_sim()
    signal = sim.line.signal("FAR-E0")
    sim.advance(600)
    assert train.state == "running"
    assert train.speed == 0
    assert train.pos < signal.pos
    assert signal.pos - train.pos < 30


def test_signal_turns_red_after_train_passes():
    sim, train = single_train_sim()
    sim.advance(200)
    sim.toggle_signal("FAR-E0")
    signal = sim.line.signal("FAR-E0")
    assert signal.green
    assert run_until(sim, lambda: train.pos > signal.pos)
    assert not signal.green


def test_facing_points_send_train_to_track_two():
    sim, train = single_train_sim()
    sim.toggle_point("FAR-PW")
    sim.toggle_signal("FAR-E0")
    point = sim.line.point("FAR-PW")
    assert run_until(sim, lambda: train.state == "running" and train.pos > point.pos + 10)
    assert train.track == 2


def test_driver_asks_for_signal_and_request_disappears_when_done():
    sim, train = single_train_sim()
    sim.advance(120)
    targets = {r.target_id for r in sim.requests.values()}
    assert "FAR-E0" in targets
    sim.toggle_signal("FAR-E0")
    assert "FAR-E0" not in {r.target_id for r in sim.requests.values()}


def test_driver_asks_for_points_when_planned_track_differs():
    sim, train = single_train_sim(WEST)  # westbound trains are planned on track 2
    sim.advance(120)
    targets = {r.target_id for r in sim.requests.values()}
    assert "TAV-PE" in targets
    sim.toggle_point("TAV-PE")
    assert "TAV-PE" not in {r.target_id for r in sim.requests.values()}


def test_points_are_locked_under_a_train():
    sim, train = single_train_sim()
    sim.toggle_signal("FAR-E0")
    point = sim.line.point("FAR-PW")
    assert run_until(sim, lambda: abs(train.pos - point.pos) < 20)
    error = sim.toggle_point("FAR-PW")
    assert error is not None and "locked" in error
    assert not point.diverging


def test_train_waits_at_platform_until_departure_time():
    sim, train = single_train_sim()
    sim.toggle_signal("FAR-E0")
    first = train.stops[0]
    assert run_until(sim, lambda: train.stopped_since is not None)
    sim.toggle_signal("FAR-E1")
    sim.advance(5)
    assert train.speed == 0  # minimum dwell time not over yet
    assert run_until(sim, lambda: first.departed_at is not None)
    assert first.departed_at >= first.depart


def test_delay_grows_while_train_is_held():
    sim, train = single_train_sim()
    sim.toggle_signal("FAR-E0")
    first = train.stops[0]
    assert run_until(sim, lambda: first.served)
    sim.advance(300)  # exit signal stays red for five minutes
    assert train.delay(sim.time) >= 240
    assert sim.average_delay() >= 240


def make_head_on(track_a: int, track_b: int, pos=8600.0):
    line = algarve_faro_tavira()
    olhao = line.station("OLH")
    a = Train("A", EAST, 0, [Stop(olhao, 1, 0, 0)], pos=pos + 75, track=track_a, state="running")
    b = Train("B", WEST, 0, [Stop(olhao, 2, 0, 0)], pos=pos - 75, track=track_b, state="running")
    return Simulation(line, [a, b], 0, 180)


def test_trains_on_same_track_collide():
    sim = make_head_on(1, 1, pos=5000)
    sim._check_collisions()
    assert sim.crash is not None
    assert sim.over and not sim.passed


def test_trains_cross_side_by_side_in_station():
    sim = make_head_on(1, 2)
    sim._check_collisions()
    assert sim.crash is None


def test_new_train_waits_while_edge_section_is_busy():
    line = algarve_faro_tavira()
    leaving = Train("OUT", WEST, 0, [], pos=-1000, state="running")
    arriving = make_timetable(line, TrainPlan("IN", EAST, "00:00"))
    sim = Simulation(line, [leaving, arriving], 0, 180)
    sim.advance(1)
    assert arriving.state == "waiting"


@pytest.mark.parametrize("info", LEVELS, ids=lambda info: f"level{info.number}")
def test_levels_build_and_timetables_are_in_order(info):
    _, sim = build_level(info.number)
    assert len(sim.trains) == len(info.trains)
    for train in sim.trains:
        times = [t for stop in train.stops for t in (stop.arrive, stop.depart)]
        assert times == sorted(times)
        halts = sum(1 for st in sim.line.stations if not st.has_loop)
        expected = len(sim.line.stations) - (0 if train.name.startswith("R ") else halts)
        assert len(train.stops) == expected


def careful_player_move(sim):
    """Grant every request, but only let a train onto the single line when it is free
    up to the next crossing station."""
    line = sim.line
    loops = sorted((st for st in line.stations if st.has_loop), key=lambda st: st.pos)
    thrown = set()
    for request in sorted(sim.requests.values(), key=lambda r: r.created):
        if request.target_id.endswith(("PW", "PE")):
            if request.target_id not in thrown:  # first come, first served
                thrown.add(request.target_id)
                sim.toggle_point(request.target_id)
            continue
        signal = line.signal(request.target_id)
        if signal.is_entry:
            point = sim._route_point(signal)
            if point.track != sim._wanted_track(request.train, signal.station):
                continue  # set the points first
            if sim._track_busy(signal.station, point.track, request.train):
                continue  # never send a train onto an occupied platform track
            other_entry = [
                s for s in line.signals
                if s.station is signal.station and s.is_entry and s is not signal and s.green
            ]
            if any(sim._route_point(s).track == point.track for s in other_entry):
                continue  # that track is already promised to a train from the other side
            other_track = 2 if point.track == 1 else 1
            if any(
                t is not request.train and t.direction == request.train.direction
                and sim._track_busy(signal.station, other_track, request.train)
                and abs(t.pos - signal.station.pos) < 1000
                for t in sim.running_trains
            ):
                continue  # keep one track free for trains coming the other way (no deadlock)
        else:
            d = signal.direction
            i = loops.index(signal.station) + d
            if 0 <= i < len(loops):
                end = loops[i].pos - d * LOOP_HALF
                opposing = [s for s in line.signals if s.station is loops[i] and s.direction == -d and s.track]
                if any(s.green for s in opposing):
                    continue
            else:
                end = line.east_edge if d == EAST else line.west_edge
            low, high = sorted((signal.pos, end))
            if any(t.span[1] >= low and t.span[0] <= high for t in sim.running_trains):
                continue
        sim.toggle_signal(request.target_id)


@pytest.mark.parametrize("number", [1, 2, 3, 4])
def test_careful_player_passes_level(number):
    _, sim = build_level(number)
    for _ in range(4 * 3600):
        if sim.over:
            break
        careful_player_move(sim)
        sim.advance(1)
    assert sim.crash is None
    assert sim.passed


def test_exit_signal_stays_red_until_the_points_are_set():
    sim, train = single_train_sim()
    sim.toggle_signal("FAR-E0")
    assert run_until(sim, lambda: train.stops[0].served)
    sim.toggle_point("FAR-PE")  # wrong: the train is on track 1
    error = sim.toggle_signal("FAR-E1")
    assert error is not None and "points" in error
    assert not sim.line.signal("FAR-E1").green
    texts = [r.text for r in sim.requests.values()]
    assert any("set the points" in t for t in texts)  # the driver tells you what is wrong
    sim.toggle_point("FAR-PE")
    assert sim.toggle_signal("FAR-E1") is None


def test_points_are_locked_while_a_green_signal_leads_a_train_over_them():
    sim, train = single_train_sim()
    sim.advance(1)
    sim.toggle_signal("FAR-E0")
    error = sim.toggle_point("FAR-PW")
    assert error is not None and "FAR-E0" in error


def test_points_stay_locked_between_the_signal_and_the_points():
    sim, train = single_train_sim()
    sim.toggle_signal("FAR-E0")
    signal, point = sim.line.signal("FAR-E0"), sim.line.point("FAR-PW")
    assert run_until(sim, lambda: train.state == "running" and train.pos > signal.pos + 50)
    assert not signal.green  # back to red behind the train
    assert sim.toggle_point("FAR-PW") is not None


def test_driver_asks_for_the_free_track_when_the_planned_one_is_taken():
    line = algarve_faro_tavira()
    olhao = line.station("OLH")
    sitting = Train("SIT", EAST, 0, [Stop(olhao, 1, 0, 10**6)], pos=olhao.pos + 75, track=1, state="running")
    sitting.stopped_since = 0
    coming = make_timetable(line, TrainPlan("COME", EAST, "00:00"))
    coming.pos, coming.state, coming.speed = olhao.pos - 2000, "running", 0
    for stop in coming.stops[:2]:
        stop.served, stop.departed_at = True, 0
    sim = Simulation(line, [sitting, coming], 0, 10**6)
    sim._update_requests()
    texts = [r.text for r in sim.requests.values() if r.train is coming]
    assert any("track 2" in t for t in texts), texts


def test_inter_regional_trains_skip_the_halts():
    line = algarve_faro_tavira()
    ir = make_timetable(line, TrainPlan("IR 1", EAST, "08:00"))
    r = make_timetable(line, TrainPlan("R 1", EAST, "08:00"))
    assert all(stop.station.has_loop for stop in ir.stops)
    assert len(r.stops) == len(line.stations)
    assert ir.stops[-1].depart < r.stops[-1].depart


def test_tail_stays_on_the_old_track_until_it_passes_the_points():
    sim, train = single_train_sim()
    sim.toggle_point("FAR-PW")
    sim.toggle_signal("FAR-E0")
    point = sim.line.point("FAR-PW")
    assert run_until(sim, lambda: train.state == "running" and point.pos < train.pos < point.pos + 100)
    assert train.track == 2
    assert train.track_at(train.pos) == 2
    assert train.track_at(train.tail) == 1


def test_average_delay_counts_late_trains_still_waiting_to_enter():
    line = algarve_faro_tavira()
    blocker = Train("OUT", WEST, 0, [], pos=-1000, state="running")
    late = make_timetable(line, TrainPlan("IN", EAST, "00:00"))
    sim = Simulation(line, [blocker, late], 0, 180)
    sim.time = late.stops[0].depart + 600
    assert late.state == "waiting"
    assert sim.average_delay() > 0


def test_new_train_waits_while_a_train_leaves_the_first_station_towards_it():
    line = algarve_faro_tavira()
    leaving = Train("OUT", WEST, 0, [], pos=-394, state="running")  # just past the exit signal
    arriving = make_timetable(line, TrainPlan("IN", EAST, "00:00"))
    sim = Simulation(line, [leaving, arriving], 0, 180)
    sim.advance(0.5)
    assert arriving.state == "waiting"


def test_green_signal_with_nobody_to_use_it_does_not_keep_trains_off_the_map():
    line = algarve_faro_tavira()
    arriving = make_timetable(line, TrainPlan("IN", WEST, "00:00"))
    sim = Simulation(line, [arriving], 0, 180)
    sim.toggle_signal("TAV-E2")  # left green, but there is no eastbound train at all
    sim.advance(1)
    assert arriving.state == "running"


def test_new_train_waits_while_a_train_has_the_way_out_towards_it():
    line = algarve_faro_tavira()
    leaving = Train("OUT", EAST, 0, [], pos=29900, track=2, state="running")
    arriving = make_timetable(line, TrainPlan("IN", WEST, "00:00"))
    sim = Simulation(line, [leaving, arriving], 0, 180)
    sim.toggle_signal("TAV-E2")
    sim.advance(0.5)
    assert arriving.state == "waiting"
