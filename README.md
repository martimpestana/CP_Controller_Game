# CP Controller

A railway signalling game on Portuguese lines. You are the controller of a single-track line
(Algarve, Oeste or Douro), where trains in opposite directions can only pass each other at
crossing stations. Drivers send you requests, you set the signals and the points, and you try to keep
every train on time without letting two of them onto the same track.

**Play it in the browser: <https://martimpestana.github.io/CP_Controller_Game/>**

## Team

| Name | Student number |
| --- | --- |
| Martim Pestana | 75038 |
| José Campos | 75552 |
| Nehir Sarikaya | 78055 |

## How to run

You need [uv](https://docs.astral.sh/uv/). It installs Python 3.12 and pygame for you.

```bash
uv sync          # first time only
uv run main.py   # play
uv run pytest    # run the tests
```

### Windows: desktop shortcut with the game icon

After `uv sync`, double-click `windows\make_shortcut.bat` once. It puts a **CP Controller**
shortcut with the game's icon on the Desktop. The shortcut gets the latest version with
`git pull` (when git is installed) and then starts the game.

## Play in the browser

The game runs at <https://martimpestana.github.io/CP_Controller_Game/>. The **⛶ Full screen**
button at the bottom right of the page (or the F key) fills the screen.

Every push to `main` builds this browser version with [pygbag](https://pypi.org/project/pygbag/)
(the same Python code, compiled to WebAssembly) and publishes it with GitHub Pages
(see `.github/workflows/web.yml`). The workflow also adds `webpage/page_extras.js` to the page
(the full screen button and smooth scaling). Each build is also kept as a download in the
**Actions** tab (`cp-controller-web`).

## Tests and checks

`uv run pytest` runs the tests. They cover the rules of the game (signals, points, interlocking,
collisions, delay), the actions the game refuses (a locked set of points, an exit signal whose
points are wrong), the menus, the drawing of every line and the browser-only parts. Every push and
pull request runs them on GitHub (`.github/workflows/tests.yml`), together with
[pip-audit](https://pypi.org/project/pip-audit/), which checks the dependencies for known
vulnerabilities.

## Security

- There are no accounts, passwords, keys or servers: the game runs entirely on the player's
  computer or in their browser, so there is no access control to enforce.
- The only input is mouse clicks and keys. Every click is checked against the rules in
  `simulation.py`, and a refused action (for example points locked under a train) is explained
  on screen instead of being carried out.
- The only file the game reads is its own settings file (chosen skins and theme). A missing or
  damaged file, or one with unknown or wrongly typed values, falls back to the defaults.
- Dependencies are few and pinned: pygame (and pytest for the tests), with exact versions in
  `pyproject.toml` and `uv.lock`. The browser build uses pygbag 0.9.3.

## How to play

- **Signals** (green/red dots): click to switch. Trains stop at red. A signal goes back to red
  by itself once a train has passed it. An exit signal only turns green when the points after
  it are set for its track.
- **Points** (squares): click to switch. White sends trains straight to track 1, yellow sends
  them to track 2. Points are locked while a train is on them, or while a train is on its way
  over them (a green signal in front of it, or already past that signal).
- **Drivers' requests** (right panel): each driver tells you what they need. A request stays
  until it is done, and the signal or point it is about pulses on the map.
- **Speed**: Pause, 1x, 5x, 10x or 20x with the buttons at the top, or 1 / 2 / 3 / 4.
  Space pauses, and pressing it again carries on at the same speed.
- **Restart**: the Restart button at the top (or R) starts the level again. Esc goes back to the list of levels,
  and the Menu button to the main menu.
- **Winning**: get every train through with an average delay under the level's limit.
  A collision ends the level straight away.

Eastbound trains (blue) are planned on track 1 at crossing stations and westbound trains
(orange) on track 2, so that they can cross. If that track is already taken, the driver asks
for the other one. "East" is simply one direction of the line (on the Oeste it is north).

| Train | Type | Speed | Stops |
| --- | --- | --- | --- |
| R | Regional | 90 km/h | every station |
| IR | Inter-Regional | 90 km/h | crossing stations only |
| M | Freight, 450 m long | 60 km/h | never (it only stops at red signals) |
| H | Historic steam train (Douro) | 50 km/h | crossing stations, 5 minutes at Pinhão |

Train types are defined in `TRAIN_TYPES` in `railgame/train.py`, so Intercidades or Alfa
Pendular trains can be added later.

In the menu you first choose a line, then one of its levels. All levels are available from
the start.

## Levels

### Linha do Algarve

| Level | Name | Trains | Delay limit |
| --- | --- | --- | --- |
| 1 | First shift | 2 | 3 min |
| 2 | Second crossing | 3 | 3 min |
| 3 | Morning service | 4 | 3 min |
| 4 | The Inter-Regional | 5 | 3 min |
| 5 | Rush hour | 6 | 3 min |
| 6 | Market day in Olhão | 6 | 4 min |
| 7 | Beach traffic | 7 | 5 min |
| 8 | Summer chaos | 8 | 7 min |

### Linha do Oeste

| Level | Name | Trains | Delay limit |
| --- | --- | --- | --- |
| 1 | Up the coast | 2 | 3 min |
| 2 | The first freight | 2 | 3 min |
| 3 | Freight on the coast | 3 | 3 min |
| 4 | Behind the freight | 4 | 4 min |
| 5 | Market day | 5 | 4 min |
| 6 | Two freights | 6 | 5 min |
| 7 | Cement and passengers | 7 | 6 min |
| 8 | Night of the freights | 8 | 7 min |

### Linha do Douro

| Level | Name | Trains | Delay limit |
| --- | --- | --- | --- |
| 1 | Along the river | 2 | 3 min |
| 2 | Wine country | 3 | 3 min |
| 3 | The Inter-Regional | 4 | 4 min |
| 4 | Steam! | 3 | 4 min |
| 5 | Overtaking the steam train | 4 | 4 min |
| 6 | Steam on the Douro | 5 | 5 min |
| 7 | Two steam trains | 6 | 6 min |
| 8 | Harvest season | 8 | 8 min |

## Project structure

| File | What it does |
| --- | --- |
| `main.py` | Starts the game |
| `railgame/track.py` | The line: stations, points and signals (positions in metres) |
| `railgame/train.py` | Trains, timetables and how delay is measured |
| `railgame/simulation.py` | The rules: movement, stops, requests, collisions, scoring. No graphics, so it is easy to test |
| `railgame/levels.py` | Level definitions and timetable generation |
| `railgame/layout.py` | Converts metres on the line into pixels on the screen |
| `railgame/render.py` | Draws a level |
| `railgame/game.py` | The window: menu, input, result screen |
| `railgame/scenery_lines.py` | The storybook scenery of each line (towns, hills, vineyards, the sea) |
| `railgame/skins.py`, `railgame/themes.py` | Train skins and map colours for the Customise menu |
| `railgame/assets/` | Game icon and the fonts used in the browser (Liberation Sans, SIL OFL) |
| `webpage/` | Extras added to the browser page (full screen button) |
| `tests/` | pytest tests |

### Adding a level

Add a `LevelInfo` to the line's list in `LEVELS` in `railgame/levels.py`, with a list of trains
(`TrainPlan(name, EAST or WEST, "HH:MM")`). The first word of the name is the train type
(`"R 5701"`, `"M 52101"`...). Timetables are calculated automatically from the
distances between stations.

### Adding another line

Create a function like `oeste_torres_caldas()` in `railgame/track.py` with the stations, their
positions and a `Geography` (approximate coordinates of the line, where the sea or the river
is), add it to `LINES`, write its levels in `LEVELS` and a line about it in `LINE_BLURBS`.
