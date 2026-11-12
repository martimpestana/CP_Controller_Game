import pytest

from railgame.levels import all_levels, build_level, clock, make_timetable, TrainPlan
from railgame.network import Network
from railgame.simulation import Simulation
from railgame.track import EAST, LINES, LOOP_HALF, WEST, algarve_faro_tavira
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


# The Linha do Norte (several tracks) has its own tests in test_network.py.
SINGLE_TRACK_LEVELS = [info for info in all_levels() if not isinstance(LINES[info.line](), Network)]


@pytest.mark.parametrize("info", SINGLE_TRACK_LEVELS, ids=lambda info: f"{info.line}{info.number}")
def test_levels_build_and_timetables_are_in_order(info):
    _, sim = build_level(info.line, info.number)
    assert len(sim.trains) == len(info.trains)
    for train in sim.trains:
        times = [t for stop in train.stops for t in (stop.arrive, stop.depart)]
        assert times == sorted(times)
        halts = sum(1 for st in sim.line.stations if not st.has_loop)
        stops = train.type.stops
        expected = len(sim.line.stations) - (0 if stops == "all" else halts)
        assert len(train.stops) == expected
        assert all(stop.passing for stop in train.stops) == (stops == "none")


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


@pytest.mark.parametrize("info", SINGLE_TRACK_LEVELS, ids=lambda info: f"{info.line}{info.number}")
def test_careful_player_passes_level(info):
    _, sim = build_level(info.line, info.number, seed=0)  # seed: the same random delays every run
    for _ in range(5 * 3600):
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


def test_freight_train_runs_through_stations_without_stopping():
    line = algarve_faro_tavira()
    train = make_timetable(line, TrainPlan("M 1", EAST, "08:00"))
    assert train.length > 300 and train.max_speed < 25
    sim = Simulation(line, [train], clock("08:00"), 180)
    for s in sim.line.signals:
        s.green = s.direction == EAST and s.track in (None, 1)
    stopped_in_station = False
    for _ in range(4 * 3600):
        if sim.over:
            break
        sim.advance(1)
        for s in sim.line.signals:  # keep the way clear, as a player would
            if s.direction == EAST and s.track in (None, 1):
                s.green = True
        if train.state == "running" and train.speed == 0 and sim.line.loop_station_at(train.pos):
            stopped_in_station = True
    assert train.state == "finished"
    assert not stopped_in_station
    assert all(stop.departed_at is not None for stop in train.stops)
    assert train.final_delay == 0


def test_steam_train_stays_longer_at_pinhao():
    line = LINES["douro"]()
    train = make_timetable(line, TrainPlan("H 1", EAST, "10:00"))
    dwell = {stop.station.code: stop.depart - stop.arrive for stop in train.stops}
    assert dwell["PIN"] > dwell["TUA"] > 0
    assert "COV" not in dwell  # it does not stop at the small halts


def test_new_train_waits_while_the_first_station_is_full():
    line = algarve_faro_tavira()
    waiting = [
        Train("A", WEST, 0, [], pos=300, state="running"),
        Train("B", EAST, 0, [], pos=-300, track=2, state="running"),
    ]
    arriving = make_timetable(line, TrainPlan("IN", EAST, "00:00"))
    for t in waiting:
        t.speed = 0
    sim = Simulation(line, [*waiting, arriving], 0, 180)
    sim.advance(1)
    assert arriving.state == "waiting"



# ---------------------------------------------------------------------- random delays (level 9)

RANDOM_LINES = ["algarve", "oeste", "douro", "alentejo"]


@pytest.mark.parametrize("line", RANDOM_LINES)
def test_level_nine_has_random_delays_and_the_others_do_not(line):
    from railgame.levels import LEVELS

    levels = LEVELS[line]
    assert len(levels) == 9 and levels[8].random_delays
    assert not any(info.random_delays for info in levels[:8])
    assert [p.name for p in levels[8].trains] == [p.name for p in levels[6].trains]  # level 7's trains
    for number in range(1, 9):
        _, sim = build_level(line, number, seed=1)
        assert all(t.brought_delay == 0 for t in sim.trains)


@pytest.mark.parametrize("line", RANDOM_LINES)
def test_random_delays_change_from_one_game_to_the_next(line):
    seen = set()
    for seed in range(12):
        _, sim = build_level(line, 9, seed=seed)
        late = [t for t in sim.trains if t.brought_delay]
        assert 1 <= len(late) <= max(1, len(sim.trains) * 2 // 3)
        assert all(60 <= t.brought_delay <= 300 and t.brought_delay % 60 == 0 for t in late)
        seen.add(tuple(t.brought_delay for t in sim.trains))
    assert len(seen) > 6  # not the same delays every time


def test_delay_a_train_brings_with_it_is_not_counted():
    _, sim = build_level("algarve", 9, seed=2)
    train = next(t for t in sim.trains if t.brought_delay)
    first = train.stops[0]
    first.departed_at = first.depart + train.brought_delay  # left exactly as late as it arrived
    assert train.delay(first.departed_at) == 0
    first.departed_at += 90  # and then the controller held it for another minute and a half
    assert train.delay(first.departed_at) == 90


@pytest.mark.parametrize("line", RANDOM_LINES)
def test_careful_player_passes_level_nine_almost_always(line):
    passed = 0
    for seed in range(10):
        _, sim = build_level(line, 9, seed=seed)
        for _ in range(6 * 3600):
            if sim.over:
                break
            careful_player_move(sim)
            sim.advance(1)
        passed += sim.crash is None and sim.passed
    assert passed >= 9


def test_a_late_train_says_so_only_shortly_before_it_was_due():
    from railgame.simulation import ANNOUNCE_BEFORE

    _, sim = build_level("alentejo", 9, seed=3)
    late = min((t for t in sim.trains if t.brought_delay), key=lambda t: t.planned_enter_time)
    assert not late.announced and not sim.notices  # at the start nobody knows
    sim.advance(late.planned_enter_time - ANNOUNCE_BEFORE - sim.time - 5)
    assert not late.announced and not sim.notices
    sim.advance(10)
    assert late.announced
    assert [n.train for n in sim.notices] == [late]
    assert f"{round(late.brought_delay / 60)} min late" in sim.notices[0].text
    assert all(t.announced for t in sim.trains if not t.brought_delay)  # trains on time say nothing
