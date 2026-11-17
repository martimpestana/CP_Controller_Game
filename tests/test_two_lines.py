"""Custom levels with two lines or two tracks: a crossing line, a separate line and double track."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pytest

from junction_player import play
from railgame import custom, i18n
from railgame.custom import CustomBranch, CustomLevel, CustomStation, CustomTrain
from railgame.junction import BRANCH, BRANCH_WEST, JUNCTION_OFFSET, MAIN, MAIN_BACK, SECOND, JunctionNetwork
from railgame.junctionrender import JunctionRenderer
from railgame.netsim import NetSimulation
from railgame.track import EAST, WEST
from test_editor import click, new_game


def two_line_level(kind: str, double: bool = False) -> CustomLevel:
    """The starter line (Vila Nova, Ponte, Monte Alto, Porto Belo) with a second line of three
    stations, Serra, Fonte and Alto: a crossing line through Monte Alto with Serra before it, or
    a separate line. Trains run on both lines, both ways."""
    level = CustomLevel.starter()
    level.title = f"Two lines {kind} {double}"
    level.double = double
    if kind:
        stations = [CustomStation("Serra", True, 7), CustomStation("Fonte", False, 5), CustomStation("Alto", True, 6)]
        level.branch = CustomBranch(2, 6, stations, kind, 1 if kind == "cross" else 0)
    second = bool(kind)
    level.trains = [
        CustomTrain("R", EAST, "08:00"), CustomTrain("R", EAST, "08:12", second), CustomTrain("R", WEST, "08:30", second),
        CustomTrain("IR", WEST, "08:40"), CustomTrain("M", EAST, "08:05"), CustomTrain("IC", EAST, "08:15"),
        CustomTrain("R", WEST, "08:20", second),
    ]
    return level


def train(sim, name: str):
    return next(t for t in sim.trains if t.name == name)


# ---------------------------------------------------------------------- the networks


def test_a_crossing_line_runs_through_its_station():
    level = two_line_level("cross")
    assert level.problems() == []
    info, sim = level.build()
    net = sim.line
    assert isinstance(net, JunctionNetwork) and net.kind == "cross"
    assert "crossing line" in info.description
    monte_alto, serra, fonte = net.station("MON"), net.station("SER"), net.station("FON")
    # Serra comes before Monte Alto, the others after it, each the set distance from the last.
    assert serra.pos == monte_alto.pos - 7000  # Serra's distance to the next station
    assert fonte.pos == monte_alto.pos + 6000  # the distance from the shared station
    # Points join the crossing line to the main line on each side of Monte Alto.
    west, east = net.point("MON-K"), net.point("MON-J")
    assert west.pos == monte_alto.pos - JUNCTION_OFFSET == net.tracks[BRANCH_WEST].end
    assert east.pos == monte_alto.pos + JUNCTION_OFFSET == net.tracks[BRANCH].start
    assert (west.stem, west.straight, west.branch) == (MAIN, MAIN, BRANCH_WEST)
    # A train on the crossing line runs from one end of it to the other, through Monte Alto.
    t = train(sim, "R 103")
    assert [s.station.name for s in t.stops if not s.passing][0] == "Serra"
    assert "Monte Alto" in [s.station.name for s in t.stops]
    assert (t.entry_track, t.exit_tracks) == (BRANCH_WEST, (BRANCH,))
    back = next(t for t in sim.trains if t.direction == WEST and t.entry_track == BRANCH)
    assert back.exit_tracks == (BRANCH_WEST,)


def test_a_separate_line_never_meets_the_first():
    level = two_line_level("separate")
    assert level.problems() == []
    info, sim = level.build()
    net = sim.line
    assert net.kind == "separate" and "second line" in info.description
    assert net.tracks[SECOND].open_start and net.tracks[SECOND].open_end
    assert not any(p.id.endswith(("-J", "-K")) for p in net.points)
    # No points lead from one line to the other.
    assert all({p.stem, p.straight, p.branch} <= {SECOND, "SER-2", "ALT-2"} or SECOND not in {p.stem, p.straight, p.branch}
               for p in net.points)
    t = train(sim, "R 103")
    assert (t.entry_track, t.exit_tracks) == (SECOND, (SECOND,))
    assert [s.station.name for s in t.stops if not s.passing] == ["Serra", "Fonte", "Alto"]
    assert t.origin == "Serra" and t.destination == "Alto"


def test_double_track_has_a_track_each_way_and_crossovers():
    level = two_line_level("", double=True)
    level.stations[0].crossing = False  # with double track one crossing station is enough
    level.stations[3].crossing = False
    assert level.problems() == []
    info, sim = level.build()
    net = sim.line
    assert net.double and "double track" in info.description
    assert set(net.tracks) == {MAIN, MAIN_BACK}
    assert all(net.platforms[st.code] == (MAIN, MAIN_BACK) for st in net.stations)
    assert net.crossovers == {"MON-XE", "MON-YE", "MON-XW", "MON-YW"}
    east = next(t for t in sim.trains if t.direction == EAST)
    west = next(t for t in sim.trains if t.direction == WEST)
    assert (east.entry_track, east.exit_tracks) == (MAIN, (MAIN,))
    assert (west.entry_track, west.exit_tracks) == (MAIN_BACK, (MAIN_BACK,))


def test_a_train_can_cross_over_to_pass_another_and_comes_back():
    _, sim = two_line_level("", double=True).build()
    t = next(t for t in sim.trains if t.direction == EAST)
    monte_alto = sim.line.station("MON")
    t.track, t.pos = MAIN, monte_alto.pos - 1500
    straight_on = {it.track for it in sim.walk(t, 3000)}
    assert straight_on == {MAIN}  # as the points are set at first: on its own track
    sim.toggle_point("MON-XE")
    items = sim.walk(t, 40000)
    assert MAIN_BACK in [it.track for it in items]  # over to the other track, past the station...
    assert items[-1].kind == "edge" and items[-1].track == MAIN  # ...and back to its own one


def test_the_editor_rules_for_two_lines():
    level = two_line_level("cross")
    level.branch.junction = 1  # Ponte is a halt
    assert "The second line must meet the first at a crossing station." in level.problems()
    level.branch.kind = "separate"  # a separate line meets nothing, so that is fine
    assert level.problems() == []
    level.branch.kind = "cross"
    level.branch.junction = 2
    level.double = True
    assert "With double track the second line can only be a separate line." in level.problems()


@pytest.mark.parametrize("kind, double", [("cross", False), ("separate", False), ("", True), ("separate", True)])
def test_a_careful_player_wins_every_kind(kind, double):
    _, sim = two_line_level(kind, double).build()
    assert isinstance(sim, NetSimulation)
    play(sim)
    assert sim.finished and sim.crash is None
    assert sim.passed, sim.average_delay()
    assert all(t.track in t.exit_tracks for t in sim.trains)  # everyone left on their own line


def test_two_lines_are_saved_and_read_back(tmp_path):
    level = two_line_level("cross")
    level.double = False
    path = tmp_path / "levels.json"
    assert custom.save_levels([level, two_line_level("separate", True)], path)
    back, other = custom.load_levels(path)
    assert back.to_dict() == level.to_dict()
    assert (back.branch.kind, back.branch.before) == ("cross", 1)
    assert other.double and other.branch.kind == "separate"
    data = level.to_dict()
    data["double"] = "yes"
    data["branch"]["kind"] = "tunnel"
    data["branch"]["before"] = 40
    odd = CustomLevel.from_dict(data)
    assert odd.double is False and odd.branch.kind == "branch"
    assert 0 <= odd.branch.before <= len(odd.branch.stations)


# ---------------------------------------------------------------------- the map


def test_every_kind_is_drawn_on_every_landscape():
    game = new_game()
    for kind, double in (("cross", False), ("separate", False), ("", True), ("separate", True)):
        for shape in custom.SHAPES:
            for landscape in ("coast", "river", "plain", "simple"):
                level = two_line_level(kind, double)
                level.shape, level.landscape = shape, landscape
                game.editor.levels = [level]
                game.start_level(1, "custom")
                r = game.renderer
                assert isinstance(r, JunctionRenderer)
                where = f"{kind or 'double'}, {shape}, {landscape}"
                for lay in r.layout.layouts.values():
                    assert all(-1 <= x <= 901 and 55 <= y <= 721 for x, y in lay.path), where
                sim = game.sim
                for _ in range(40):
                    play(sim, 30)
                    game.draw()
                # Every point and signal can be clicked.
                for obj in (*sim.line.points, *sim.line.signals):
                    pos = r.point_position(obj) if hasattr(obj, "stem") else r.signal_position(obj)
                    assert r.object_at(pos) is obj, (where, obj.id)


# ---------------------------------------------------------------------- the editor


def test_choosing_the_second_line_in_the_editor():
    game = new_game()
    click(game, "mylevels")
    click(game, "ed:new")
    level = game.editor.level
    click(game, "ed:branch")
    game.draw()
    assert {"ed:branchadd:0", "ed:branchadd:1", "ed:branchadd:2"} <= {a for _, a in game.buttons}
    click(game, "ed:branchadd:1")
    assert level.branch.kind == "cross" and len(level.branch.stations) == 2 and level.branch.before == 1
    assert level.branch.ordered()[1] is None  # the shared station between the two
    click(game, "ed:before:1")
    assert level.branch.before == 2
    click(game, "ed:before:1")
    assert level.branch.before == 2  # no more stations to put before it
    click(game, "ed:bkind:1")
    assert level.branch.kind == "separate" and level.branch.before == 0
    assert level.problems() == []
    game.draw()
    click(game, "ed:branchdone")
    click(game, "ed:double")
    assert level.double and level.problems() == []
    game.draw()
    click(game, "ed:test")
    for _ in range(3):
        game.frame()
    assert game.scene == "playing" and game.sim.line.double and game.sim.line.kind == "separate"


def test_two_lines_in_portuguese():
    i18n.set_language("pt")
    try:
        assert i18n.t("7 stations, 26 km, double track and a crossing line. Made in the level editor.") == (
            "7 estações, 26 km, via dupla e uma linha que cruza. Feito no editor de níveis."
        )
        assert i18n.t("7 stations, 26 km and a branch. Made in the level editor.") == (
            "7 estações, 26 km e um ramal. Feito no editor de níveis."
        )
        assert i18n.t("+ Separate line") == "+ Linha separada"
        game = new_game()
        click(game, "mylevels")
        click(game, "ed:new")
        click(game, "ed:branch")
        game.draw()
        click(game, "ed:branchadd:1")
        game.draw()
    finally:
        i18n.set_language("en")
