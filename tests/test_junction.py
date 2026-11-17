"""A custom line with a branch: the junction rules, the map and the editor's branch screen."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from junction_player import play
from railgame import custom, i18n
from railgame.custom import CustomBranch, CustomLevel, CustomStation, CustomTrain
from railgame.junction import BRANCH, MAIN, JUNCTION_OFFSET, JunctionNetwork
from railgame.junctionrender import JunctionRenderer
from railgame.netsim import NetSimulation
from railgame.track import EAST, WEST
from test_editor import click, new_game, press, type_text


def branch_level(trains=None) -> CustomLevel:
    """The starter line (Vila Nova, Ponte, Monte Alto, Porto Belo) with a branch from Monte
    Alto to Serra (a crossing station) and Fonte (a halt)."""
    level = CustomLevel.starter()
    level.branch = CustomBranch(2, 6, [CustomStation("Serra", True, 7), CustomStation("Fonte", False, 5)])
    level.trains = trains or [CustomTrain("R", EAST, "08:00", True)]
    return level


def train(sim, name: str):
    return next(t for t in sim.trains if t.name == name)


# ---------------------------------------------------------------------- the network


def test_a_level_with_a_branch_becomes_a_network():
    level = branch_level()
    assert level.problems() == []
    info, sim = level.build()
    net = sim.line
    assert isinstance(sim, NetSimulation) and isinstance(net, JunctionNetwork)
    assert [st.name for st in net.stations] == ["Vila Nova", "Ponte", "Monte Alto", "Porto Belo", "Serra", "Fonte"]
    assert len({st.code for st in net.stations}) == 6
    assert "branch" in info.description
    # The branch starts at the junction points, just past Monte Alto, and carries on from there.
    monte_alto, serra = net.station("MON"), net.station("SER")
    points = net.point("MON-J")
    assert points.pos == monte_alto.pos + JUNCTION_OFFSET == net.tracks[BRANCH].start
    assert (points.stem, points.straight, points.branch) == (MAIN, MAIN, BRANCH)
    assert serra.pos == monte_alto.pos + 6000
    # Crossing stations have a second track with points and signals, on both lines.
    assert net.platforms["MON"] == (MAIN, "MON-2") and net.platforms["SER"] == (BRANCH, "SER-2")
    assert net.platforms["PON"] == (MAIN,) and net.platforms["FON"] == (BRANCH,)
    assert {"SER-PW", "SER-PE", "SER-E0", "SER-W2"} <= {o.id for o in (*net.points, *net.signals)}


def test_timetables_follow_the_route():
    level = branch_level([
        CustomTrain("R", EAST, "08:00", True), CustomTrain("R", WEST, "08:00", True),
        CustomTrain("R", EAST, "08:00"), CustomTrain("IR", WEST, "08:00", True),
    ])
    _, sim = level.build()
    out, back, main, fast = sim.trains
    assert [s.station.name for s in out.stops] == ["Vila Nova", "Ponte", "Monte Alto", "Serra", "Fonte"]
    assert (out.entry_track, out.exit_tracks, out.destination) == (MAIN, (BRANCH,), "Fonte")
    assert [s.station.name for s in back.stops] == ["Fonte", "Serra", "Monte Alto", "Ponte", "Vila Nova"]
    assert (back.entry_track, back.exit_tracks, back.destination) == (BRANCH, (MAIN,), "Vila Nova")
    assert [s.station.name for s in main.stops] == ["Vila Nova", "Ponte", "Monte Alto", "Porto Belo"]
    assert main.exit_tracks == (MAIN,)
    assert [s.station.name for s in fast.stops] == ["Serra", "Monte Alto", "Vila Nova"]  # an IR skips the halts
    for t in sim.trains:  # times only ever go forward
        times = [x for s in t.stops for x in (s.arrive, s.depart)]
        assert times == sorted(times) and times[0] > t.enter_time
    # Trains one way are planned on track 1 and the other way on track 2, so they can cross.
    assert out.stops[3].options == (BRANCH, "SER-2") and back.stops[1].options == ("SER-2", BRANCH)


# ---------------------------------------------------------------------- playing


def test_trains_take_the_branch_and_come_back():
    level = branch_level([
        CustomTrain("R", EAST, "08:00"), CustomTrain("R", EAST, "08:12", True),
        CustomTrain("R", WEST, "08:30", True), CustomTrain("IR", WEST, "08:40"),
    ])
    _, sim = level.build()
    play(sim)
    assert sim.finished and sim.crash is None
    assert sim.passed, sim.average_delay()
    # Each one left the map on its own line.
    assert train(sim, "R 103").track == BRANCH and train(sim, "R 101").track == MAIN
    assert all(t.track == MAIN for t in sim.trains if t.direction == WEST)
    assert all(stop.departed_at is not None for t in sim.trains for stop in t.stops)


def test_a_busy_branch_level_ends_without_an_accident():
    level = branch_level([
        CustomTrain("R", EAST, "08:00"), CustomTrain("IC", WEST, "08:05", True), CustomTrain("R", WEST, "08:10"),
        CustomTrain("R", EAST, "08:12", True), CustomTrain("M", EAST, "08:20"), CustomTrain("R", WEST, "08:30", True),
        CustomTrain("H", EAST, "08:35", True), CustomTrain("IR", WEST, "08:40"), CustomTrain("AP", EAST, "08:50"),
    ])
    _, sim = level.build()
    play(sim)
    assert sim.finished and sim.crash is None
    assert all(t.track in t.exit_tracks for t in sim.trains)  # nobody left on the wrong line


def to_the_junction(sim, name: str):
    """Run the train to Monte Alto and give it the signal to leave, without touching the junction."""
    t = train(sim, name)
    for _ in range(4000):
        sim.advance(1)
        for request in list(sim.requests.values()):
            if request.target_id != "MON-J":
                obj = next(o for o in (*sim.line.signals, *sim.line.points) if o.id == request.target_id)
                if hasattr(obj, "green"):
                    if not obj.green:
                        sim.toggle_signal(obj.id)
                else:
                    sim.toggle_point(obj.id)
        if sim.line.signal("MON-E1").green or t.pos > sim.line.station("MON").pos + 200:
            break
    return t


def test_the_driver_asks_for_the_junction_and_waits_for_it():
    _, sim = branch_level().build()  # one train for the branch; the points are set for the main line
    t = to_the_junction(sim, "R 101")
    asked = [r.text for r in sim.requests.values() if r.target_id == "MON-J"]
    assert asked == ["Approaching Monte Alto. Please set points MON-J to the branch line for me."]
    sim.advance(300)  # nobody sets them: it stops in front of the points instead of taking the wrong line
    points = sim.line.point("MON-J")
    assert t.speed == 0 and t.track == MAIN and 0 < points.pos - t.pos < 30
    assert sim.toggle_point("MON-J") is None
    sim.advance(120)
    assert t.track == BRANCH and not any(r.target_id == "MON-J" for r in sim.requests.values())


def test_a_main_line_train_will_not_take_the_branch():
    _, sim = branch_level([CustomTrain("R", EAST, "08:00")]).build()
    sim.toggle_point("MON-J")  # set for the branch
    t = to_the_junction(sim, "R 101")
    assert [r.text for r in sim.requests.values() if r.target_id == "MON-J"] == [
        "Approaching Monte Alto. Please set points MON-J to the main line for me."
    ]
    sim.advance(300)
    assert t.speed == 0 and t.track == MAIN
    sim.toggle_point("MON-J")
    sim.advance(120)
    assert t.track == MAIN and t.pos > sim.line.point("MON-J").pos


def test_a_train_from_the_branch_waits_for_the_junction_points():
    _, sim = branch_level([CustomTrain("R", WEST, "08:00", True)]).build()
    t = sim.trains[0]
    points = sim.line.point("MON-J")
    for _ in range(3000):  # every signal it asks for, but never the junction
        sim.advance(1)
        for request in list(sim.requests.values()):
            if request.target_id != "MON-J" and request.target_id in {s.id for s in sim.line.signals}:
                if not sim.line.signal(request.target_id).green:
                    sim.toggle_signal(request.target_id)
        if t.speed == 0 and 0 < t.pos - points.pos < 30:
            break
    assert t.track == BRANCH and 0 < t.pos - points.pos < 30
    assert [r.text for r in sim.requests.values() if r.target_id == "MON-J"] == [
        "I'm on the branch line at Monte Alto. Please set points MON-J so I can get out."
    ]
    sim.toggle_point("MON-J")
    sim.advance(60)
    assert t.track == MAIN


def test_requests_about_a_branch_are_translated():
    i18n.set_language("pt")
    try:
        assert i18n.t("Approaching Monte Alto. Please set points MON-J to the branch line for me.") == (
            "A chegar a Monte Alto. Põe a agulha MON-J para a linha do ramal, por favor."
        )
        assert i18n.t("Ready to leave Serra from track 2. Signal SER-W2 to green, please.") == (
            "Pronto para partir de Serra da via 2. Sinal SER-W2 a verde, por favor."
        )
        assert i18n.t("7 stations, 26 km and a branch. Made in the level editor.") == (
            "7 estações, 26 km e um ramal. Feito no editor de níveis."
        )
    finally:
        i18n.set_language("en")


# ---------------------------------------------------------------------- saving


def test_a_branch_is_saved_and_read_back(tmp_path):
    level = branch_level([CustomTrain("R", EAST, "08:00", True), CustomTrain("R", WEST, "08:10")])
    path = tmp_path / "levels.json"
    assert custom.save_levels([level], path)
    (back,) = custom.load_levels(path)
    assert back.to_dict() == level.to_dict()
    assert back.branch.junction == 2 and [st.name for st in back.branch.stations] == ["Serra", "Fonte"]
    assert [t.branch for t in back.trains] == [True, False]


def test_an_odd_branch_in_the_file_is_put_right():
    data = branch_level().to_dict()
    data["branch"] = {"junction": 99, "gap_km": 1000, "stations": [{"name": "A" * 80, "crossing": 1, "gap_km": "x"}] * 9}
    level = CustomLevel.from_dict(data)
    assert level.branch.junction == 3 and level.branch.gap_km == custom.MAX_GAP_KM
    assert len(level.branch.stations) == custom.MAX_BRANCH_STATIONS
    assert len(level.branch.stations[0].name) == custom.NAME_LENGTH
    assert "Two stations have the same name." in level.problems()
    for bad in ({"stations": []}, {"junction": 1}, "yes", 3, None):
        data["branch"] = bad
        level = CustomLevel.from_dict(data)
        assert level.branch is None and not any(t.branch for t in level.trains)  # no branch: main-line trains


def test_levels_saved_before_branches_existed_still_load():
    data = CustomLevel.starter().to_dict()
    del data["branch"]
    for t in data["trains"]:
        del t["branch"]
    level = CustomLevel.from_dict(data)
    assert level.branch is None and level.problems() == []
    assert not isinstance(level.build()[1], NetSimulation)


def test_what_is_wrong_with_a_branch():
    level = branch_level()
    level.branch.junction = 1  # Ponte is a halt
    assert "The second line must meet the first at a crossing station." in level.problems()
    level.branch.junction = 2
    level.branch.stations[0].name = "Ponte"
    assert "Two stations have the same name." in level.problems()
    level.branch.stations = []
    assert "The second line needs at least one station." in level.problems()


# ---------------------------------------------------------------------- the map


def test_the_branch_is_drawn_clear_of_the_main_line_on_every_landscape():
    game = new_game()
    for shape in custom.SHAPES:
        for landscape in ("coast", "river", "plain", "simple"):
            for start in (0, 2, 3):
                level = branch_level()
                level.title, level.shape, level.landscape, level.branch.junction = f"{shape} {landscape} {start}", shape, landscape, start
                game.editor.levels = [level]
                game.start_level(1, "custom")
                r = game.renderer
                assert isinstance(r, JunctionRenderer)
                path, main = r.side_layout.path, r.main_layout
                where = f"{shape}, {landscape}, from station {start + 1}"
                # It stays on the map...
                assert all(0 <= x <= 900 and 56 <= y <= 720 for x, y in path), where
                # ...is long enough for its station...
                length = sum(((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5 for (ax, ay), (bx, by) in zip(path, path[1:]))
                assert length > 350, where
                # ...and, once it has left the main line, never comes back to it.
                samples = [main._path_at(d) for d in range(0, int(main.cum[-1]), 8)]
                for x, y in path[24:]:
                    assert min((x - sx) ** 2 + (y - sy) ** 2 for sx, sy in samples) > 40 ** 2, where
                # The stations of the two lines do not sit on top of each other.
                boxes = [r._station_box(st) for st in game.sim.line.stations]
                assert all(not a.colliderect(b) for i, a in enumerate(boxes) for b in boxes[i + 1:]), where
                game.draw()


def test_a_train_is_drawn_through_the_junction():
    game = new_game()
    game.editor.levels = [branch_level()]
    game.start_level(1, "custom")
    sim = game.sim
    t = sim.trains[0]
    for _ in range(4000):
        play(sim, 1)
        game.draw()  # must draw at every moment: on the main line, over the points, on the branch
        if t.track == BRANCH and t.pos > sim.line.station("SER").pos:
            break
    assert t.track == BRANCH
    # It is drawn on the branch: its tag belongs to it, and it is far from the main line by now.
    boxes = [box for box, who in game.renderer.train_boxes if who is t]
    assert boxes
    x, y = game.renderer.layout.point(t.pos, t.track)
    mx, my = game.renderer.main_layout.point(sim.line.station("MON").pos)
    assert (x - mx) ** 2 + (y - my) ** 2 > 100 ** 2
    # Points and signals of both lines can be clicked.
    for obj in (*sim.line.points, *sim.line.signals):
        pos = game.renderer.point_position(obj) if hasattr(obj, "stem") else game.renderer.signal_position(obj)
        assert game.renderer.object_at(pos) is obj, obj.id


# ---------------------------------------------------------------------- the editor


def test_adding_a_branch_in_the_editor():
    game = new_game()
    click(game, "mylevels")
    click(game, "ed:new")
    click(game, "ed:branch")
    assert game.scene == "branch" and game.editor.level.branch is None
    click(game, "ed:branchadd:0")
    level = game.editor.level
    assert level.branch.junction == 2 and len(level.branch.stations) == 1  # from Monte Alto, in the middle
    click(game, "ed:junction:1")
    assert level.branch.junction == 3  # Porto Belo: only crossing stations are offered, never the halt
    click(game, "ed:junction:1")
    assert level.branch.junction == 0
    click(game, "ed:bgap0:1")
    assert level.branch.gap_km == 7
    click(game, "ed:baddstation")  # ...and the new one is ready to be named
    for _ in range(30):
        press(game, pygame.K_BACKSPACE)
    type_text(game, "Serra")
    press(game, pygame.K_RETURN)
    click(game, "ed:bcrossing:1")
    click(game, "ed:bgap:0:-1")
    assert [(st.name, st.crossing) for st in level.branch.stations][1] == ("Serra", False)
    assert level.branch.stations[0].gap_km == 7
    click(game, "ed:baddstation")
    click(game, "ed:baddstation")
    game.draw()
    assert "ed:baddstation" not in [a for _, a in game.buttons]  # four at most
    click(game, "ed:bdelstation:3")
    click(game, "ed:bdelstation:2")
    press(game, pygame.K_ESCAPE)
    assert game.scene == "editor" and level.problems() == []


def test_sending_trains_along_the_branch_in_the_editor():
    game = new_game()
    click(game, "mylevels")
    click(game, "ed:new")
    level = game.editor.level
    first = level.trains[0]
    click(game, "ed:direction:0")
    click(game, "ed:direction:0")
    assert (first.direction, first.branch) == (EAST, False)  # without a branch: just there and back
    click(game, "ed:branch")
    click(game, "ed:branchadd:0")
    click(game, "ed:branchdone")
    seen = []
    for _ in range(4):
        click(game, "ed:direction:0")
        seen.append((first.direction, first.branch))
    assert seen == [(WEST, False), (EAST, True), (WEST, True), (EAST, False)]
    click(game, "ed:direction:0")
    click(game, "ed:direction:0")
    assert first.branch
    click(game, "ed:test")  # save and play
    for _ in range(3):
        game.frame()
    assert game.scene == "playing" and isinstance(game.renderer, JunctionRenderer)
    assert game.sim.trains[0].exit_tracks == (BRANCH,)
    press(game, pygame.K_ESCAPE)
    assert game.scene == "editor"
    # Taking the branch away sends its trains back to the main line.
    click(game, "ed:branch")
    click(game, "ed:branchremove")
    assert level.branch is None and not any(t.branch for t in level.trains)


def test_deleting_a_station_keeps_the_branch_on_its_station():
    game = new_game()
    click(game, "mylevels")
    click(game, "ed:new")
    click(game, "ed:branch")
    click(game, "ed:branchadd:0")
    click(game, "ed:branchdone")
    level = game.editor.level
    assert level.stations[level.branch.junction].name == "Monte Alto"
    click(game, "ed:delstation:1")  # Ponte, before it
    assert level.stations[level.branch.junction].name == "Monte Alto"
    click(game, "ed:delstation:2")  # Porto Belo, after it
    assert level.stations[level.branch.junction].name == "Monte Alto"
    click(game, "ed:crossing:1")  # Monte Alto becomes a halt: the level says what is wrong
    assert "The second line must meet the first at a crossing station." in level.problems()
    game.draw()
