"""The level editor: "My levels" in the main menu.

Two screens, both drawn here for the Game (game.py):

- the list of the player's own levels, to play, change or delete, and
- the editor itself: on the left the line (its shape, its landscape and its stations), on the
  right the trains (what kind, which way, at what time) and the allowed delay.

Two more screens open from the editor: one to draw the line by hand, and one for the branch (a
second line that leaves the first at one of its stations).

What a custom level is, and how it becomes a playable level, is in custom.py.
"""

import pygame

from railgame import custom, i18n, render, ui
from railgame.custom import CustomBranch, CustomLevel, CustomStation, CustomTrain
from railgame.junctionrender import make_layouts
from railgame.layout import Layout
from railgame.levels import clock
from railgame.render import BUTTON_ON, EAST_COLOUR, GREEN, HEIGHT, MUTED, RED, TEXT, WEST_COLOUR, WHITE, WIDTH
from railgame.track import EAST, WEST
from railgame.train import TRAIN_TYPES
from railgame.ui import S, SR, circle, thick_lines

ROW = 38  # height of a station or train row, in design pixels
LEFT, RIGHT = 40, 670  # where the two columns start
FIELD = (20, 30, 42)


class Editor:
    def __init__(self, game):
        self.game = game
        self.levels: list[CustomLevel] = custom.load_levels()
        self.index = 0  # the level being edited (its place in self.levels)
        self.level = CustomLevel.starter()  # a working copy: nothing is kept until "Save"
        self.is_new = True
        self.focus: tuple | None = None  # the text field being typed in: ("title",) or ("station", i)
        self.fields: list[tuple[pygame.Rect, tuple]] = []
        self.message = ""  # "Saved", or why it could not be
        self.message_until = 0
        self.confirm_delete: int | None = None  # the level whose "Delete" was clicked once
        # Drawing the line by hand (the "draw" screen):
        self.stroke: list[tuple[float, float]] = []  # what the mouse has drawn, 0..1 across the canvas
        self.drawing = False  # the mouse button is down on the canvas
        self.drawn: list[tuple[float, float]] = []  # the stroke tidied into a line, when it can be one
        self.draw_note = ""  # why the stroke cannot be a line
        self.canvas = pygame.Rect(0, 0, 1, 1)
        self._map_cache: tuple = (None, ())  # the little map on the branch screen

    # ------------------------------------------------------------------ opening and saving

    def new_level(self) -> None:
        self.level = CustomLevel.starter(len(self.levels) + 1)
        self.index, self.is_new = len(self.levels), True
        self._open()

    def edit_level(self, index: int) -> None:
        self.level = CustomLevel.from_dict(self.levels[index].to_dict())  # a copy
        self.index, self.is_new = index, False
        self._open()

    def _open(self) -> None:
        self.focus, self.message = None, ""
        self.game.scene = "editor"

    def save(self) -> bool:
        """Keep the level being edited. Returns False (and says why) if it is not playable."""
        problems = self.level.problems()
        if problems:
            self.say(problems[0])
            return False
        kept = CustomLevel.from_dict(self.level.to_dict())
        if self.is_new:
            self.levels.append(kept)
            self.index, self.is_new = len(self.levels) - 1, False
        else:
            self.levels[self.index] = kept
        if custom.save_levels(self.levels):
            self.say("Saved.")
        else:
            self.say("Could not write the file: the level is kept until you close the game.")
        return True

    def delete(self, index: int) -> None:
        del self.levels[index]
        custom.save_levels(self.levels)
        self.confirm_delete = None

    def say(self, text: str) -> None:
        self.message = text
        self.message_until = pygame.time.get_ticks() + 4000

    # ------------------------------------------------------------------ actions (buttons)

    def do(self, action: str) -> None:
        """An "ed:..." button was clicked."""
        parts = action.split(":")[1:]
        what, args = parts[0], [int(a) for a in parts[1:] if a.lstrip("-").isdigit()]
        level = self.level
        self.focus = None
        if what != "delete":
            self.confirm_delete = None
        if what == "new":
            if len(self.levels) < custom.MAX_LEVELS:
                self.new_level()
        elif what == "edit":
            self.edit_level(args[0])
        elif what == "delete":
            if self.confirm_delete == args[0]:
                self.delete(args[0])
            else:
                self.confirm_delete = args[0]  # asks "Sure?" first
        elif what == "play":
            self.game.play_custom(args[0], back_to="mylevels")
        elif what == "test":
            if self.save():
                self.game.play_custom(self.index, back_to="editor")
        elif what == "save":
            self.save()
        elif what == "close":
            self.game.scene = "mylevels"
        elif what == "shape":
            shapes = list(custom.SHAPES) + ([custom.DRAWN] if level.path else [])
            level.shape = _step(shapes, level.shape, args[0])
        elif what == "draw":  # open the drawing screen, with the line drawn before (if any)
            self.stroke, self.drawn, self.draw_note, self.drawing = [], list(level.path), "", False
            self.game.scene = "draw"
        elif what == "drawclear":
            self.stroke, self.drawn, self.draw_note = [], [], ""
        elif what == "drawuse":
            if self.drawn:
                level.path, level.shape = list(self.drawn), custom.DRAWN
            self.game.scene = "editor"
        elif what == "drawcancel":
            self.game.scene = "editor"
        elif what == "branch":  # open the second line's screen
            self.game.scene = "branch"
        elif what == "branchdone":
            self.game.scene = "editor"
        elif what == "branchadd":  # a new second line, of the kind on the button
            crossings = [i for i, st in enumerate(level.stations) if st.crossing]
            # By default it meets the main line at a station in the middle of it.
            start = crossings[len(crossings) // 2] if crossings else 0
            kind = list(custom.SECOND_KINDS)[args[0] if args else 0]
            level.branch = CustomBranch(start, 6, [CustomStation(self._new_name(), True, 8)], kind)
            if kind != "branch":  # two stations: one each side of the shared one, or both ends of the line
                level.branch.stations.append(CustomStation(self._new_name(), True, 8))
                level.branch.before = 1 if kind == "cross" else 0
        elif what == "bkind" and level.branch is not None:
            branch = level.branch
            branch.kind = _step(list(custom.SECOND_KINDS), branch.kind, args[0])
            branch.before = len(branch.stations) // 2 if branch.kind == "cross" else 0
        elif what == "before" and level.branch is not None:
            branch = level.branch
            branch.before = max(0, min(len(branch.stations), branch.before + args[0]))
        elif what == "double":
            level.double = not level.double
        elif what == "branchremove":
            level.branch = None
            for train in level.trains:
                train.branch = False
        elif what == "junction" and level.branch is not None:
            crossings = [i for i, st in enumerate(level.stations) if st.crossing]
            if crossings:
                level.branch.junction = _step(crossings, level.branch.junction, args[0])
        elif what == "bgap0" and level.branch is not None:
            level.branch.gap_km = max(custom.MIN_GAP_KM, min(custom.MAX_GAP_KM, level.branch.gap_km + args[0]))
        elif what == "baddstation" and level.branch is not None:
            if len(level.branch.stations) < custom.MAX_BRANCH_STATIONS:
                level.branch.stations.append(CustomStation(self._new_name(), True, 8))
                self.focus = ("bstation", len(level.branch.stations) - 1)
        elif what == "bdelstation" and level.branch is not None:
            if len(level.branch.stations) > 1:
                del level.branch.stations[args[0]]
                if args[0] < level.branch.before:
                    level.branch.before -= 1
        elif what == "bcrossing" and level.branch is not None:
            st = level.branch.stations[args[0]]
            st.crossing = not st.crossing
        elif what == "bgap" and level.branch is not None:
            st = level.branch.stations[args[0]]
            st.gap_km = max(custom.MIN_GAP_KM, min(custom.MAX_GAP_KM, st.gap_km + args[1]))
        elif what == "landscape":
            level.landscape = _step(list(custom.LANDSCAPES), level.landscape, args[0])
        elif what == "limit":
            level.limit_min = max(custom.MIN_LIMIT, min(custom.MAX_LIMIT, level.limit_min + args[0]))
        elif what == "addstation":
            if len(level.stations) < custom.MAX_STATIONS:
                level.stations.append(CustomStation(self._new_name(), True, 8))
                self.focus = ("station", len(level.stations) - 1)
        elif what == "delstation":
            if len(level.stations) > custom.MIN_STATIONS:
                del level.stations[args[0]]
                branch = level.branch
                if branch is not None:  # the branch still leaves from the same station, if it is there
                    branch.junction = min(branch.junction - (args[0] < branch.junction), len(level.stations) - 1)
        elif what == "crossing":
            st = level.stations[args[0]]
            st.crossing = not st.crossing
        elif what == "gap":
            st = level.stations[args[0]]
            st.gap_km = max(custom.MIN_GAP_KM, min(custom.MAX_GAP_KM, st.gap_km + args[1]))
        elif what == "addtrain":
            if len(level.trains) < custom.MAX_TRAINS:
                last = max(level.trains, key=lambda t: clock(t.enters), default=None)
                level.trains.append(
                    CustomTrain(
                        last.kind if last else "R",
                        -last.direction if last else EAST,
                        custom.shift_time(last.enters, 6) if last else "08:00",
                    )
                )
        elif what == "deltrain":
            del level.trains[args[0]]
        elif what == "kind":
            train = level.trains[args[0]]
            train.kind = _step(list(custom.TRAIN_KINDS), train.kind, 1)
        elif what == "direction":
            # Each click: the other way; with a branch, then the same two ways on the branch.
            train = level.trains[args[0]]
            if train.direction == EAST:
                train.direction = WEST
            else:
                train.direction = EAST
                train.branch = level.branch is not None and not train.branch
        elif what == "time":
            train = level.trains[args[0]]
            train.enters = custom.shift_time(train.enters, args[1])
        elif what == "sort":
            level.trains.sort(key=lambda t: clock(t.enters))

    def _new_name(self) -> str:
        taken = {st.name for st in self.level.all_stations()}
        for name in ("Vila Nova", "Ponte", "Monte Alto", "Porto Belo", "Santa Clara", "Pinhal", "Vale Verde", "Castelo", "Serra", "Fonte Nova", "Ribeira"):
            if name not in taken:
                return name
        return f"Station {len(taken) + 1}"

    # ------------------------------------------------------------------ typing

    def click(self, pos) -> None:
        """A click that hit no button: on a text field it starts typing there."""
        self.focus = next((key for rect, key in self.fields if rect.collidepoint(pos)), None)
        self.confirm_delete = None

    def _focused_station(self) -> CustomStation | None:
        """The station whose name is being typed (None: the title, or a station that has gone)."""
        if self.focus is None or self.focus[0] == "title":
            return None
        branch = self.level.branch
        stations = self.level.stations if self.focus[0] == "station" else (branch.stations if branch is not None else [])
        return stations[self.focus[1]] if self.focus[1] < len(stations) else None

    def _text(self) -> str:
        if self.focus == ("title",):
            return self.level.title
        return self._focused_station().name

    def _set_text(self, text: str) -> None:
        if self.focus == ("title",):
            self.level.title = text[: custom.TITLE_LENGTH]
        else:
            self._focused_station().name = text[: custom.NAME_LENGTH]

    def event(self, event) -> bool:
        """Keys while the editor is open. Returns True when the key was used here."""
        if self.focus is not None and self.focus != ("title",) and self._focused_station() is None:
            self.focus = None
        if event.type == pygame.TEXTINPUT:
            if self.focus is not None:
                self._set_text(self._text() + "".join(ch for ch in event.text if ch.isprintable()))
            return True
        if event.type != pygame.KEYDOWN:
            return False
        if self.focus is None:
            if event.key == pygame.K_ESCAPE:  # out of the branch screen, or out of the editor
                self.game.scene = "editor" if self.game.scene == "branch" else "mylevels"
            return True
        if event.key == pygame.K_BACKSPACE:
            self._set_text(self._text()[:-1])
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
            self.focus = None
        elif event.key == pygame.K_TAB:  # on to the next field
            keys = [key for _, key in self.fields]
            self.focus = keys[(keys.index(self.focus) + 1) % len(keys)] if self.focus in keys else None
        return True

    # ------------------------------------------------------------------ drawing the line by hand

    def _canvas_point(self, pos) -> tuple[float, float]:
        c = self.canvas
        return (min(1.0, max(0.0, (pos[0] - c.x) / c.width)), min(1.0, max(0.0, (pos[1] - c.y) / c.height)))

    def draw_event(self, event) -> None:
        """The mouse on the drawing screen: press on the map, drag, let go."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.scene = "editor"
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.drawn:
                self.do("ed:drawuse")
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.canvas.collidepoint(event.pos):  # a new stroke replaces the last one
                self.stroke, self.drawn, self.draw_note, self.drawing = [self._canvas_point(event.pos)], [], "", True
        elif event.type == pygame.MOUSEMOTION and self.drawing:
            point = self._canvas_point(event.pos)
            if abs(point[0] - self.stroke[-1][0]) + abs(point[1] - self.stroke[-1][1]) > 0.004:
                self.stroke.append(point)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.drawing:
            self.drawing = False
            self.drawn, self.draw_note = custom.tidy_path(self.stroke)
            if self.drawn:
                self.stroke = []

    def draw_canvas(self) -> None:
        """The drawing screen: a blank map to draw the line on, from its first station to its last."""
        g, s, level = self.game, self.game.screen, self.level
        s.fill(render.BG)
        mouse = pygame.mouse.get_pos()
        s.blit(g.f_head.render("Draw the line", True, WHITE), (S(LEFT), S(20)))
        hint = "Hold the mouse button down and draw the line across the map, from the first station to the last."
        s.blit(g.f_small.render(hint, True, MUTED), (S(LEFT + 200), S(25)))
        self.canvas = c = SR(LEFT, 60, 900, 580)
        pygame.draw.rect(s, render.LAND, c, border_radius=S(10))
        for i in range(1, 9):  # a faint grid, to help judge distances
            x = c.x + c.width * i // 9
            pygame.draw.line(s, render.CARD, (x, c.y + S(6)), (x, c.bottom - S(6)), 1)
        for i in range(1, 6):
            y = c.y + c.height * i // 6
            pygame.draw.line(s, render.CARD, (c.x + S(6), y), (c.right - S(6), y), 1)

        def px(p):
            return (c.x + p[0] * c.width, c.y + p[1] * c.height)

        if len(self.stroke) > 1:  # being drawn, or drawn but not usable
            thick_lines(s, RED if self.draw_note else WHITE, [px(p) for p in self.stroke], S(3))
        if self.drawn:
            self._sketch([px(p) for p in self.drawn], render.LAND)
        elif not self.stroke:
            text = g.f_text.render("Draw here", True, MUTED)
            s.blit(text, text.get_rect(center=c.center))

        x = LEFT + 920
        if self.draw_note:
            for i, line in enumerate(g.renderer_wrap(self.draw_note, S(WIDTH - x - 30))):
                s.blit(g.f_text.render(line, True, RED), (S(x), S(70 + i * 24)))
        elif self.drawn:
            for i, line in enumerate(g.renderer_wrap("This is your line, with its stations. Draw again to change it.", S(WIDTH - x - 30))):
                s.blit(g.f_text.render(line, True, TEXT), (S(x), S(70 + i * 24)))
        legend = g.f_small.render("○ " + i18n.t("Crossing") + "   • " + i18n.t("Halt"), True, MUTED)
        s.blit(legend, (S(x), S(190)))
        if self.drawn:
            g.button(SR(x, HEIGHT - 240, 280, 44), "Use this line", "ed:drawuse", primary=True)
        if self.drawn or self.stroke:
            g.button(SR(x, HEIGHT - 186, 280, 44), "Clear", "ed:drawclear")
        g.button(SR(x, HEIGHT - 132, 280, 44), "Cancel", "ed:drawcancel")

    def _sketch(self, path: list[tuple[float, float]], behind) -> None:
        """The track along a path in screen pixels, with the level's stations marked on it:
        rings for crossing stations, dots for halts, each with its number from the list."""
        g, s, level = self.game, self.game.screen, self.level
        thick_lines(s, render.TRACK, path, S(3))
        if level.double:  # the second track, beside the first
            thick_lines(s, render.TRACK, [(x, y - S(6)) for x, y in path], S(3))
        total = level.length_km() + 2 * custom.EDGE_KM
        km = custom.EDGE_KM
        for i, st in enumerate(level.stations):
            x, y = path[round(km / total * (len(path) - 1))]
            if st.crossing:
                circle(s, WHITE, (x, y), S(7))
                circle(s, behind, (x, y), S(4))
            else:
                circle(s, WHITE, (x, y), S(4))
            number = g.f_small.render(str(i + 1), True, TEXT if st.crossing else MUTED)
            s.blit(number, number.get_rect(center=(x, y - S(18))))
            if level.branch is not None and level.branch.kind != "separate" and level.branch.junction == i:
                # The branch: a short line leaving just past this station (the map shows where it really runs).
                a = path[min(len(path) - 1, round(km / total * (len(path) - 1)) + 2)]
                b = (a[0] + S(26), a[1] - S(22))
                thick_lines(s, render.TRACK, [a, (a[0] + S(12), a[1] - S(6)), b], S(3))
                circle(s, render.YELLOW, b, S(4))
            km += st.gap_km

    # ------------------------------------------------------------------ the branch screen

    def draw_branch(self) -> None:
        """The second line: what kind it is, where it meets the main line, and its own stations."""
        g, s, level = self.game, self.game.screen, self.level
        s.fill(render.BG)
        mouse = pygame.mouse.get_pos()
        self.fields = []
        s.blit(g.f_head.render("Second line", True, WHITE), (S(LEFT), S(20)))
        branch = level.branch
        if branch is None:
            hint = "Add a second line to the level. Trains can then run on either line."
            s.blit(g.f_small.render(hint, True, MUTED), (S(LEFT), S(58)))
            y = 100
            for i, (kind, (name, what)) in enumerate(custom.SECOND_KINDS.items()):
                g.button(SR(LEFT, y, 300, 44), f"+ {name}", f"ed:branchadd:{i}", primary=i == 0)
                for j, line in enumerate(g.renderer_wrap(what, S(560))):
                    s.blit(g.f_small.render(line, True, TEXT), (S(LEFT + 320), S(y + 4 + j * 20)))
                y += 74
            lines = g.renderer_wrap(
                "Where two lines meet you set the points for each train: the driver tells you which way he is going. "
                "For two tracks on the whole main line, use Double track in the editor.",
                S(600),
            )
            for i, line in enumerate(lines):
                s.blit(g.f_small.render(line, True, MUTED), (S(LEFT), S(y + 10 + i * 20)))
            g.button(SR(LEFT, HEIGHT - 64, 130, 44), "Back", "ed:branchdone")
            return
        y = 64
        name, what = custom.SECOND_KINDS[branch.kind]
        self._chooser(LEFT, y, 544, "Kind", name, "ed:bkind", mouse)
        for j, line in enumerate(g.renderer_wrap(what, S(600))[:2]):
            s.blit(g.f_small.render(line, True, MUTED), (S(LEFT), S(y + 40 + j * 18)))
        y += 84
        junction = level.stations[branch.junction] if branch.junction < len(level.stations) else None
        shared = junction.name if junction else "?"
        if branch.kind == "branch":
            self._chooser(LEFT, y, 544, "Leaves from", shared, "ed:junction", mouse, as_typed=True)
            y += 44
        elif branch.kind == "cross":
            self._chooser(LEFT, y, 290, "Crosses at", shared, "ed:junction", mouse, as_typed=True)
            self._chooser(LEFT + 310, y, 234, "Before it", str(branch.before), "ed:before", mouse)
            y += 44
        y += 8
        for x, label in ((LEFT + 30, "Station"), (LEFT + 262, "Type"), (LEFT + 392, "Distance to the next")):
            s.blit(g.f_small.render(label, True, MUTED), (S(x), S(y)))
        y += 22
        rows = branch.ordered()
        if branch.kind == "branch":
            rows = [None] + rows  # the junction station first: the branch starts there
        own = 0
        for r, st in enumerate(rows):
            more = r < len(rows) - 1  # a distance to the next station
            if st is None:  # the station the lines share: named in the main line's list
                box = SR(LEFT + 26, y, 226, 32)
                pygame.draw.rect(s, render.CARD, box, border_radius=S(6))
                label = g.f_text._font.render(shared, True, MUTED)
                s.blit(label, (box.x + S(10), box.centery - label.get_height() // 2))
                text = g.f_small.render("Shared", True, MUTED)
                s.blit(text, text.get_rect(center=(S(LEFT + 321), S(y + 16))))
                if more:
                    self._gap(y, branch.gap_km, "ed:bgap0", mouse)
                y += ROW
                continue
            i = own
            own += 1
            number = g.f_small.render(str(own), True, MUTED)
            s.blit(number, number.get_rect(center=(S(LEFT + 10), S(y + 16))))
            self._field(SR(LEFT + 26, y, 226, 32), ("bstation", i), st.name, g.f_text)
            self._button(
                SR(LEFT + 260, y, 122, 32), "Crossing" if st.crossing else "Halt", f"ed:bcrossing:{i}", mouse,
                colour=(46, 104, 70) if st.crossing else None,
            )
            if more:
                self._gap(y, st.gap_km, f"ed:bgap:{i}", mouse)
            if len(branch.stations) > 1:
                self._button(SR(LEFT + 568, y, 32, 32), "×", f"ed:bdelstation:{i}", mouse)
            y += ROW
        if len(branch.stations) < custom.MAX_BRANCH_STATIONS:
            self._button(SR(LEFT + 26, y, 170, 32), "+ Station", "ed:baddstation", mouse)
        y += 50
        lines = g.renderer_wrap(
            "In the list of trains, click a train's route to send it along the second line. "
            "The second line goes on off the map at its ends.",
            S(600),
        )
        for i, line in enumerate(lines):
            s.blit(g.f_small.render(line, True, MUTED), (S(LEFT), S(y + i * 20)))
        self._branch_map(SR(RIGHT + 30, 64, 540, 470))
        g.button(SR(LEFT, HEIGHT - 64, 130, 44), "Done", "ed:branchdone", primary=True)
        g.button(SR(LEFT + 146, HEIGHT - 64, 270, 44), "Remove the second line", "ed:branchremove")
        problems = level.problems()
        if problems:
            for i, line in enumerate(g.renderer_wrap(problems[0], S(WIDTH - LEFT - 450))):
                s.blit(g.f_small.render(line, True, RED), (S(LEFT + 436), S(HEIGHT - 58 + i * 18)))

    def _gap(self, y, km, action, mouse) -> None:
        """The distance to the next station, with − and + buttons."""
        g = self.game
        self._button(SR(LEFT + 392, y, 32, 32), "−", f"{action}:-1", mouse)
        text = g.f_text.render(f"{km} km", True, TEXT)
        g.screen.blit(text, text.get_rect(center=(S(LEFT + 468), S(y + 16))))
        self._button(SR(LEFT + 512, y, 32, 32), "+", f"{action}:1", mouse)

    def _branch_map(self, box: pygame.Rect) -> None:
        """A small map of the lines, laid out as they will be in the game."""
        g, s, level = self.game, self.game.screen, self.level
        pygame.draw.rect(s, render.CARD, box, border_radius=S(10))
        if level.problems():
            text = g.f_small.render("The map shows once the level has no problems.", True, MUTED)
            s.blit(text, text.get_rect(center=box.center))
            return
        key = (level.map_key(), box.size)
        if self._map_cache[0] != key:  # worked out again only when the lines change
            k = box.width / S(render.PANEL_X)
            net = level.network()
            main = net.main
            map_box = main.geo.map_box or (40, render.TOP_BAR + 120, render.PANEL_X - 80, HEIGHT - render.TOP_BAR - 250)
            scale = ui.scale() * k
            lay = Layout(main, tuple(v * S(1) * k for v in map_box), scale)
            self._map_cache = (key, list(make_layouts(net, lay, scale).values()))
        top = box.y + (box.height - S(HEIGHT) * box.width / S(render.PANEL_X)) / 2 - S(20)
        for lay in self._map_cache[1]:
            track = [(box.x + x, top + y) for x, y in lay.main_track()]
            thick_lines(s, render.TRACK, track, S(3))
            for st in lay.line.stations:
                x, y = lay.point(st.pos)
                x, y = box.x + x, top + y
                if st.has_loop:
                    circle(s, WHITE, (x, y), S(7))
                    circle(s, render.CARD, (x, y), S(4))
                else:
                    circle(s, WHITE, (x, y), S(4))
                name = g.f_small._font.render(st.name, True, TEXT if st.has_loop else MUTED)
                s.blit(name, name.get_rect(midtop=(x, y + S(10))))

    # ------------------------------------------------------------------ drawing: the list

    def draw_list(self) -> None:
        g, s = self.game, self.game.screen
        s.fill(render.BG)
        mouse = pygame.mouse.get_pos()
        s.blit(g.f_title.render("My levels", True, WHITE), (S(80), S(40)))
        s.blit(
            g.f_text.render("Make your own line, choose the trains and their times, then play it.", True, MUTED),
            (S(80), S(98)),
        )
        if not self.levels:
            s.blit(g.f_text.render("No levels yet. Make the first one!", True, TEXT), (S(80), S(160)))
        for i, level in enumerate(self.levels):
            rect = SR(80, 140 + i * 58, 1120, 50)
            pygame.draw.rect(s, render.CARD, rect, border_radius=S(10))
            title = g.f_head._font.render(level.title, True, WHITE)  # as typed, never translated
            s.blit(title, (rect.x + S(20), rect.centery - title.get_height() // 2))
            crossings = sum(st.crossing for st in level.stations)
            branch = " · double track" if level.double else ""
            branch += " · with a second line" if level.branch is not None else ""
            meta = (
                f"{len(level.stations)} stations ({crossings} crossing) · {level.length_km():.0f} km{branch} · "
                f"{len(level.trains)} trains · limit {level.limit_min:.0f} min"
            )
            text = g.f_small.render(meta, True, MUTED)
            s.blit(text, (rect.x + S(370), rect.centery - text.get_height() // 2))
            y = rect.y + S(7)
            self._button(pygame.Rect(rect.right - S(318), y, S(90), S(36)), "Play", f"ed:play:{i}", mouse, on=True)
            self._button(pygame.Rect(rect.right - S(220), y, S(90), S(36)), "Edit", f"ed:edit:{i}", mouse)
            sure = self.confirm_delete == i
            self._button(
                pygame.Rect(rect.right - S(122), y, S(110), S(36)), "Sure?" if sure else "Delete", f"ed:delete:{i}", mouse,
                colour=(150, 50, 50) if sure else None,
            )
        g.button(SR(80, HEIGHT - 70, 140, 44), "Back", "menu")
        if len(self.levels) < custom.MAX_LEVELS:
            g.button(SR(240, HEIGHT - 70, 200, 44), "New level", "ed:new", primary=True)
        else:
            text = g.f_small.render(f"The list is full ({custom.MAX_LEVELS} levels). Delete one to make another.", True, MUTED)
            s.blit(text, (S(240), S(HEIGHT - 56)))

    # ------------------------------------------------------------------ drawing: the editor

    def draw(self) -> None:
        g, s = self.game, self.game.screen
        level = self.level
        s.fill(render.BG)
        mouse = pygame.mouse.get_pos()
        self.fields = []
        s.blit(g.f_head.render("Level editor", True, MUTED), (S(LEFT), S(18)))
        self._field(SR(LEFT + 220, 12, 380, 34), ("title",), level.title, g.f_head)

        # ---- left: the line
        y = 64
        s.blit(g.f_head.render("The line", True, WHITE), (S(LEFT), S(y)))
        km = g.f_small.render(f"{level.length_km():.0f} km", True, MUTED)
        s.blit(km, (S(LEFT + 110), S(y + 5)))
        y += 34
        self._chooser(LEFT, y, 290, "Shape", level.shape_name(), "ed:shape", mouse)
        self._chooser(LEFT + 310, y, 290, "Landscape", custom.LANDSCAPES[level.landscape][0], "ed:landscape", mouse)
        y += 48
        for x, label in ((LEFT + 30, "Station"), (LEFT + 262, "Type"), (LEFT + 392, "Distance to the next")):
            s.blit(g.f_small.render(label, True, MUTED), (S(x), S(y)))
        y += 22
        last = len(level.stations) - 1
        for i, st in enumerate(level.stations):
            number = g.f_small.render(str(i + 1), True, MUTED)
            s.blit(number, number.get_rect(center=(S(LEFT + 10), S(y + 16))))
            self._field(SR(LEFT + 26, y, 226, 32), ("station", i), st.name, g.f_text)
            self._button(
                SR(LEFT + 260, y, 122, 32), "Crossing" if st.crossing else "Halt", f"ed:crossing:{i}", mouse,
                colour=(46, 104, 70) if st.crossing else None,
            )
            if i < last:
                self._button(SR(LEFT + 392, y, 32, 32), "−", f"ed:gap:{i}:-1", mouse)
                text = g.f_text.render(f"{st.gap_km} km", True, TEXT)
                s.blit(text, text.get_rect(center=(S(LEFT + 468), S(y + 16))))
                self._button(SR(LEFT + 512, y, 32, 32), "+", f"ed:gap:{i}:1", mouse)
            if len(level.stations) > custom.MIN_STATIONS:
                self._button(SR(LEFT + 568, y, 32, 32), "×", f"ed:delstation:{i}", mouse)
            y += ROW
        if len(level.stations) < custom.MAX_STATIONS:
            self._button(SR(LEFT + 26, y, 170, 32), "+ Station", "ed:addstation", mouse)
        self._preview(SR(LEFT, 500, 600, 138))

        # ---- right: the trains
        y = 64
        s.blit(g.f_head.render("The trains", True, WHITE), (S(RIGHT), S(y)))
        text = g.f_small.render("Allowed average delay", True, MUTED)
        s.blit(text, (S(RIGHT + 240), S(y + 5)))
        self._button(SR(RIGHT + 410, y - 2, 30, 30), "−", "ed:limit:-1", mouse)
        text = g.f_text.render(f"{level.limit_min} min", True, TEXT)
        s.blit(text, text.get_rect(center=(S(RIGHT + 484), S(y + 13))))
        self._button(SR(RIGHT + 528, y - 2, 30, 30), "+", "ed:limit:1", mouse)
        y += 40
        for x, label in ((RIGHT, "Train"), (RIGHT + 168, "Route" if level.branch else "From"), (RIGHT + 372, "Enters the map at")):
            s.blit(g.f_small.render(label, True, MUTED), (S(x), S(y)))
        y += 22
        first, final = level.stations[0].name, level.stations[-1].name
        for i, train in enumerate(level.trains):
            kind = TRAIN_TYPES[train.kind]
            colour = EAST_COLOUR if train.direction == EAST else WEST_COLOUR
            self._button(SR(RIGHT, y, 160, 32), f"{kind.code} · {kind.name}", f"ed:kind:{i}", mouse)
            origin = first if train.direction == EAST else final
            arrow = "→" if train.direction == EAST else "←"
            route = f"{arrow} {_short(origin, 18)}"
            if level.branch is not None:  # with a second line: where from and where to
                ends = level.route_ends(train)
                route = f"{_short(ends[0], 10)} → {_short(ends[1], 10)}"
            self._route_button(SR(RIGHT + 168, y, 196, 32), route, f"ed:direction:{i}", mouse, colour)
            self._button(SR(RIGHT + 372, y, 36, 32), "−5", f"ed:time:{i}:-5", mouse)
            self._button(SR(RIGHT + 410, y, 28, 32), "−", f"ed:time:{i}:-1", mouse)
            text = g.f_head_small.render(train.enters, True, WHITE)
            s.blit(text, text.get_rect(center=(S(RIGHT + 466), S(y + 16))))
            self._button(SR(RIGHT + 494, y, 28, 32), "+", f"ed:time:{i}:1", mouse)
            self._button(SR(RIGHT + 524, y, 36, 32), "+5", f"ed:time:{i}:5", mouse)
            self._button(SR(RIGHT + 568, y, 32, 32), "×", f"ed:deltrain:{i}", mouse)
            y += ROW
        if len(level.trains) < custom.MAX_TRAINS:
            self._button(SR(RIGHT, y, 160, 32), "+ Train", "ed:addtrain", mouse)
        if len(level.trains) > 1:
            self._button(SR(RIGHT + 168, y, 196, 32), "Sort by time", "ed:sort", mouse)

        # ---- bottom: what to do with it
        g.button(SR(LEFT, HEIGHT - 64, 130, 44), "Back", "ed:close")
        g.button(SR(LEFT + 146, HEIGHT - 64, 130, 44), "Save", "ed:save")
        g.button(SR(LEFT + 292, HEIGHT - 64, 190, 44), "Save and play", "ed:test", primary=True)
        problems = level.problems()
        if pygame.time.get_ticks() < self.message_until:
            note, colour = self.message, (GREEN if self.message == "Saved." else render.YELLOW)
        elif problems:
            note, colour = problems[0], RED
        else:
            note, colour = "Click a name to type. The level starts two minutes before the first train.", MUTED
        s.blit(g.f_small.render(note, True, colour), (S(LEFT + 500), S(HEIGHT - 50)))

    # ------------------------------------------------------------------ drawing: the parts

    def _button(self, rect, label, action, mouse, on=False, colour=None, text_colour=WHITE) -> None:
        g = self.game
        hovered = rect.collidepoint(mouse)
        fill = BUTTON_ON if on or hovered else (colour or render.BUTTON)
        pygame.draw.rect(g.screen, fill, rect, border_radius=S(6))
        text = g.f_text.render(label, True, WHITE if hovered else text_colour)
        g.screen.blit(text, text.get_rect(center=rect.center))
        g.buttons.append((rect, action))

    def _route_button(self, rect, label, action, mouse, colour) -> None:
        """A button whose label is made of station names: shown as typed, never translated."""
        g = self.game
        hovered = rect.collidepoint(mouse)
        pygame.draw.rect(g.screen, BUTTON_ON if hovered else render.BUTTON, rect, border_radius=S(6))
        text = g.f_text._font.render(label, True, WHITE if hovered else colour)
        g.screen.blit(text, text.get_rect(center=rect.center))
        g.buttons.append((rect, action))

    def _chooser(self, x, y, width, label, value, action, mouse, as_typed=False) -> None:
        """A label with the chosen value between two arrows: ◀ value ▶."""
        g = self.game
        g.screen.blit(g.f_small.render(label, True, MUTED), (S(x), S(y + 7)))
        left = x + 84
        self._button(SR(left, y, 30, 32), "<", f"{action}:-1", mouse)
        box = SR(left + 34, y, width - 84 - 68, 32)
        pygame.draw.rect(g.screen, render.CARD, box, border_radius=S(6))
        text = (g.f_text._font if as_typed else g.f_text).render(value, True, WHITE)
        g.screen.blit(text, text.get_rect(center=box.center))
        self._button(SR(x + width - 30, y, 30, 32), ">", f"{action}:1", mouse)

    def _field(self, rect, key, text, fnt) -> None:
        """A box to type in. The one being typed in has a bright edge and a blinking cursor."""
        s = self.game.screen
        active = self.focus == key
        pygame.draw.rect(s, FIELD, rect, border_radius=S(6))
        pygame.draw.rect(s, BUTTON_ON if active else render.BUTTON, rect, max(1, S(2)), border_radius=S(6))
        # Names are typed by the player, so they are shown as typed (never translated).
        label = fnt._font.render(text, True, WHITE)
        s.blit(label, (rect.x + S(10), rect.centery - label.get_height() // 2), (0, 0, rect.width - S(20), label.get_height()))
        if active and pygame.time.get_ticks() % 1000 < 550:
            x = min(rect.right - S(8), rect.x + S(11) + label.get_width())
            pygame.draw.line(s, WHITE, (x, rect.y + S(7)), (x, rect.bottom - S(7)), max(1, S(1.5)))
        self.fields.append((rect, key))

    def _preview(self, box: pygame.Rect) -> None:
        """A sketch of the line: its shape, the crossing stations (rings) and the halts (dots),
        each with its number from the list above."""
        g, s, level = self.game, self.game.screen, self.level
        pygame.draw.rect(s, render.CARD, box, border_radius=S(10))
        if len(level.stations) < 2:
            return
        raw = level.shape_points(61)
        xs, ys = [p[0] for p in raw], [p[1] for p in raw]
        w, h = max(max(xs) - min(xs), 1e-6), max(max(ys) - min(ys), 1e-6)
        inner = box.inflate(-S(70), -S(64))
        inner.width -= S(150)  # room for the "Draw by hand" button on the right
        # Fill the box: the sketch only has to show the bends, not the true proportions.
        kx, ky = inner.width / w, inner.height / h
        kx, ky = min(kx, ky * 6), min(ky, kx * 2)
        ox = inner.centerx - (min(xs) + w / 2) * kx
        oy = inner.centery + (min(ys) + h / 2) * ky
        path = [(ox + x * kx, oy - y * ky) for x, y in raw]
        water = custom.LANDSCAPES[level.landscape][1]
        if water != "none":
            shore = [(x, y + S(15 if water == "sea" else 9)) for x, y in path]
            thick_lines(s, render.SEA, shore, S(12 if water == "sea" else 6))
        self._sketch(path, render.CARD)
        legend = g.f_small.render("○ " + i18n.t("Crossing") + "   • " + i18n.t("Halt"), True, MUTED)
        s.blit(legend, (box.x + S(12), box.bottom - S(24)))
        self._button(
            pygame.Rect(box.right - S(162), box.y + S(10), S(150), S(34)), "Draw by hand", "ed:draw",
            pygame.mouse.get_pos(), on=level.shape == custom.DRAWN,
        )
        self._button(
            pygame.Rect(box.right - S(162), box.y + S(50), S(150), S(34)), "Second line", "ed:branch",
            pygame.mouse.get_pos(), on=level.branch is not None,
        )
        self._button(
            pygame.Rect(box.right - S(162), box.y + S(90), S(150), S(34)), "Double track", "ed:double",
            pygame.mouse.get_pos(), on=level.double,
        )


def _step(options: list, value, by: int):
    return options[(options.index(value) + by) % len(options)] if value in options else options[0]


def _short(text: str, length: int) -> str:
    return text if len(text) <= length else text[: length - 1] + "…"
