# CP Controller

A railway signalling game. You are the controller of the Algarve line (Faro to Tavira):
a single track where trains in opposite directions can only pass each other at crossing
stations. Drivers send you requests, you set the signals and the points, and you try to keep
every train on time without letting two of them onto the same track.

## How to run

You need [uv](https://docs.astral.sh/uv/). It installs Python 3.12 and pygame for you.

```bash
uv sync          # first time only
uv run main.py   # play
uv run pytest    # run the tests
```

## Play in the browser

Every push to `main` builds a browser version with [pygbag](https://pypi.org/project/pygbag/)
(the same Python code, compiled to WebAssembly) and publishes it with GitHub Pages
(see `.github/workflows/web.yml`). The address appears under **Settings → Pages**.
Each build is also kept as a download in the **Actions** tab (`cp-controller-web`).

## How to play

- **Signals** (green/red dots): click to switch. Trains stop at red. A signal goes back to red
  by itself once a train has passed it.
- **Points** (squares): click to switch. White sends trains straight to track 1, yellow sends
  them to track 2. Points are locked while a train is on them.
- **Drivers' requests** (right panel): each driver tells you what they need. A request stays
  until it is done, and the signal or point it is about pulses on the map.
- **Speed**: Pause, 1x, 5x or 10x with the buttons at the top, or Space / 1 / 2 / 3.
  R restarts the level, Esc goes back to the menu.
- **Winning**: get every train through with an average delay under the level's limit.
  A collision ends the level straight away.

Eastbound trains (blue) are planned on track 1 at crossing stations and westbound trains
(orange) on track 2, so that they can cross.

## Levels

| Level | Name | Trains | Delay limit |
| --- | --- | --- | --- |
| 1 | First shift | 2 | 3 min |
| 2 | Morning service | 4 | 3 min |
| 3 | Rush hour | 6 | 3 min |
| 4 | Summer chaos | 8 | 7 min |

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
| `tests/` | pytest tests |

### Adding a level

Add a `LevelInfo` to `LEVELS` in `railgame/levels.py` with a list of trains
(`TrainPlan(name, EAST or WEST, "HH:MM")`). Timetables are calculated automatically from the
distances between stations.

### Adding another line

Create a function like `algarve_faro_tavira()` in `railgame/track.py` with the stations and
their positions, and add its shape (approximate coordinates) to `railgame/layout.py`.
