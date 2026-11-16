"""The level editor ("My levels"): making a level, saving it and playing it."""

import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from railgame import custom, i18n
from railgame.custom import CustomLevel, CustomStation, CustomTrain
from railgame.game import Game
from railgame.layout import Layout
from railgame.track import EAST, WEST, ZONE_HALF
from test_simulation import careful_player_move


def new_game() -> Game:
    pygame.init()
    return Game(pygame.display.set_mode((1280, 720)))


def click(game: Game, action: str) -> None:
    """Click the button with this action, as the player would."""
    game.draw()
    rect = next(rect for rect, a in game.buttons if a == action)
    game.click(rect.center)


def type_text(game: Game, text: str) -> None:
    game.handle(pygame.event.Event(pygame.TEXTINPUT, text=text))


def press(game: Game, key: int) -> None:
    game.handle(pygame.event.Event(pygame.KEYDOWN, key=key))


# ---------------------------------------------------------------------- the level itself


def test_the_starter_level_can_be_played_and_won():
    _, sim = CustomLevel.starter().build()
    assert [t.name.split()[0] for t in sim.trains] == ["R", "R", "IR"]
    assert sim.time == custom.clock("07:58")  # two minutes before the first train
    for _ in range(3 * 3600):
        if sim.over:
            break
        careful_player_move(sim)
        sim.advance(1)
    assert sim.crash is None and sim.passed


@pytest.mark.parametrize("shape", custom.SHAPES)
@pytest.mark.parametrize("stations", [2, 4, 7])
def test_every_shape_gives_a_line_that_can_be_laid_out(shape, stations):
    level = CustomLevel(shape=shape, trains=[CustomTrain()])
    level.stations = [CustomStation(f"Station {chr(65 + i)}", i != 1 or stations == 2, 3) for i in range(stations)]
    line = level.line()
    loops = [st for st in line.stations if st.has_loop]
    # Station areas never overlap, and every crossing station has its points and signals.
    assert all(b.pos - a.pos >= 2 * ZONE_HALF for a, b in zip(line.stations, line.stations[1:]))
    assert len(line.points) == 2 * len(loops) and len(line.signals) == 6 * len(loops)
    indexes = [line.geo.station_shape_index[st.code] for st in loops]
    assert indexes == sorted(set(indexes)) and indexes[-1] < len(line.geo.shape)
    layout = Layout(line, (40, 100, 820, 560))
    xs = [layout.point(st.pos) for st in line.stations]
    assert len(set(xs)) == len(xs)


def test_station_codes_are_short_and_never_the_same():
    level = CustomLevel(stations=[CustomStation(n) for n in ("Évora", "Évora Norte", "São João", "1", "")])
    codes = level.codes()
    assert codes[0] == "EVO" and len(set(codes)) == len(codes)
    assert all(len(code) == 3 and code.isascii() for code in codes)


def test_trains_are_numbered_by_kind_and_direction_and_sorted_by_time():
    level = CustomLevel.starter()
    level.trains = [CustomTrain("M", WEST, "09:10"), CustomTrain("R", EAST, "08:30"), CustomTrain("R", EAST, "08:00")]
    plans = level.plans()
    assert [p.enters for p in plans] == ["08:00", "08:30", "09:10"]
    assert len({p.name for p in plans}) == 3
    assert [int(p.name.split()[1]) % 2 for p in plans] == [1, 1, 0]  # odd one way, even the other


def test_a_level_that_cannot_be_played_says_why():
    level = CustomLevel.starter()
    assert level.problems() == []
    level.trains = []
    assert "Add at least one train." in level.problems()
    level = CustomLevel.starter()
    for st in level.stations[1:]:
        st.crossing = False
    assert "At least two stations must be crossing stations." in level.problems()
    level = CustomLevel.starter()
    level.stations[1].name = level.stations[0].name.upper()
    assert "Two stations have the same name." in level.problems()
    level.stations[1].name = "  "
    assert "Every station needs a name." in level.problems()


# ---------------------------------------------------------------------- the file


def test_levels_are_saved_and_read_back(tmp_path):
    path = tmp_path / "mine.json"
    level = CustomLevel.starter()
    level.title, level.shape, level.landscape, level.limit_min = "Linha da Avó", "s", "river", 7
    assert custom.save_levels([level], path)
    assert custom.load_levels(path) == [level]
    assert "Linha da Avó" in path.read_text(encoding="utf-8")  # readable, accents and all


def test_a_broken_or_tampered_file_never_breaks_the_game(tmp_path):
    path = tmp_path / "mine.json"
    assert custom.load_levels(path) == []  # no file yet
    path.write_text("{not json", encoding="utf-8")
    assert custom.load_levels(path) == []
    bad = {
        "title": "x" * 500 + "\n",
        "shape": "../../etc",
        "landscape": 3,
        "limit_min": 10**9,
        "stations": [{"name": "A", "gap_km": -5}, "junk", {"name": ["B"], "gap_km": "far", "crossing": "yes"}] * 20,
        "trains": [{"kind": "ROCKET", "direction": 9, "enters": "25:99"}, None] * 50,
    }
    path.write_text(json.dumps([bad, "junk", 7] + [bad] * 30), encoding="utf-8")
    levels = custom.load_levels(path)
    assert len(levels) == custom.MAX_LEVELS
    level = levels[0]
    assert len(level.title) <= custom.TITLE_LENGTH and "\n" not in level.title
    assert level.shape in custom.SHAPES and level.landscape in custom.LANDSCAPES
    assert level.limit_min == custom.MAX_LIMIT
    assert len(level.stations) == custom.MAX_STATIONS and len(level.trains) == custom.MAX_TRAINS
    assert all(custom.MIN_GAP_KM <= st.gap_km <= custom.MAX_GAP_KM for st in level.stations)
    assert all(t.kind == "R" and t.direction == EAST and t.enters == "08:00" for t in level.trains)
    level.line()  # still a line the game can build (its nameless stations are for the player to fix)


def test_saving_to_a_place_that_cannot_be_written_only_says_so(tmp_path):
    assert custom.save_levels([CustomLevel.starter()], tmp_path / "no" / "such" / "folder.json") is False


# ---------------------------------------------------------------------- the screens


def test_from_the_menu_make_a_level_save_it_and_play_it():
    game = new_game()
    click(game, "mylevels")
    assert game.scene == "mylevels" and game.editor.levels == []
    click(game, "ed:new")
    assert game.scene == "editor"
    click(game, "ed:addstation")  # the new station's name is ready to be typed over
    for _ in range(20):
        press(game, pygame.K_BACKSPACE)
    type_text(game, "Évora")
    press(game, pygame.K_RETURN)
    assert game.editor.level.stations[-1].name == "Évora"
    click(game, "ed:addtrain")
    click(game, "ed:shape:1")
    click(game, "ed:landscape:1")
    click(game, "ed:test")  # "Save and play"
    for _ in range(3):
        game.frame()
    assert game.scene == "playing" and game.line_key == "custom"
    assert [st.name for st in game.sim.line.stations][-1] == "Évora"
    assert len(game.sim.trains) == 4
    assert len(custom.load_levels()) == 1  # it was written to the file
    game.draw()
    game.key(pygame.K_r)  # restart works on a custom level too
    assert game.scene == "playing"
    game.key(pygame.K_ESCAPE)  # back to the editor it was started from
    assert game.scene == "editor"
    click(game, "ed:close")
    click(game, "ed:play:0")  # from the list, Esc goes back to the list
    for _ in range(3):
        game.frame()
    assert game.scene == "playing"
    game.key(pygame.K_ESCAPE)
    assert game.scene == "mylevels"


def test_a_finished_custom_level_offers_no_next_level():
    game = new_game()
    game.editor.levels = [CustomLevel.starter(), CustomLevel.starter(2)]
    game.play_custom(0, back_to="mylevels")
    for _ in range(3):
        game.frame()
    for train in game.sim.trains:
        train.state, train.final_delay = "finished", 0.0
    game.frame()
    assert game.scene == "result" and game.sim.passed
    game.draw()
    assert "next" not in {action for _, action in game.buttons}
    click(game, "levels")
    assert game.scene == "mylevels"


def test_the_map_is_drawn_again_after_the_line_is_changed():
    game = new_game()
    game.editor.levels = [CustomLevel.starter()]
    game.play_custom(0, back_to="mylevels")
    for _ in range(3):
        game.frame()
    before = game.renderer.background
    game.editor.levels[0].shape = "bend"
    game.play_custom(0, back_to="mylevels")
    for _ in range(3):
        game.frame()
    assert game.scene == "playing" and game.renderer.background is not before
    game.editor.levels[0].trains.append(CustomTrain("M", WEST, "08:40"))  # trains do not change the map
    kept = game.renderer.background
    game.play_custom(0, back_to="mylevels")
    game.frame()
    assert game.renderer.background is kept


def test_an_unplayable_level_is_not_saved_and_delete_asks_first():
    game = new_game()
    click(game, "mylevels")
    click(game, "ed:new")
    while game.editor.level.trains:
        click(game, "ed:deltrain:0")
    click(game, "ed:test")
    assert game.scene == "editor" and game.editor.levels == []
    click(game, "ed:addtrain")
    click(game, "ed:save")
    assert len(game.editor.levels) == 1
    click(game, "ed:close")
    click(game, "ed:delete:0")
    assert len(game.editor.levels) == 1  # "Sure?"
    click(game, "ed:delete:0")
    assert game.editor.levels == [] and custom.load_levels() == []


def test_the_editor_keeps_to_its_limits():
    game = new_game()
    game.editor.new_level()
    for _ in range(20):
        game.editor.do("ed:addstation")
        game.editor.do("ed:addtrain")
        game.editor.do("ed:gap:0:1")
        game.editor.do("ed:limit:1")
        game.editor.do("ed:time:0:-5")
    level = game.editor.level
    assert len(level.stations) == custom.MAX_STATIONS and len(level.trains) == custom.MAX_TRAINS
    assert level.stations[0].gap_km <= custom.MAX_GAP_KM and level.limit_min == custom.MAX_LIMIT
    assert len({st.name for st in level.stations}) == len(level.stations)
    for _ in range(400):
        game.editor.do("ed:time:0:-5")
    assert level.trains[0].enters == "00:00"
    for _ in range(20):
        game.editor.do("ed:delstation:0")
    assert len(level.stations) == custom.MIN_STATIONS
    game.draw()  # the screen still draws at every limit


def test_the_editor_is_in_portuguese_too():
    i18n.set_language("pt")
    try:
        texts = ["My levels", "Level editor", "New level", "Save and play", "Sort by time", "Crossing", "Halt"]
        texts += [name for name, _ in custom.SHAPES.values()]
        texts += [entry[0] for entry in custom.LANDSCAPES.values()]
        texts += CustomLevel(stations=[CustomStation("")]).problems()
        assert [text for text in texts if i18n.t(text) == text] == []
        assert i18n.t("4 stations (3 crossing) · 26 km · 3 trains · limit 4 min") == (
            "4 estações (3 de cruzamento) · 26 km · 3 comboios · limite 4 min")
        assert CustomLevel.starter(2).title == "O meu nível 2"
    finally:
        i18n.set_language("en")
