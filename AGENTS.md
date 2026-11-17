# AGENTS.md

Notes for AI coding agents (and people) working on this repository. The README has the full
description of the game; this file is the short version of how to work here.

## What this is

CP Controller: a railway signalling game in Python 3.12 with pygame. It runs on the desktop
and, compiled with pygbag, in the browser (GitHub Pages, built by `.github/workflows/web.yml`).

## Commands

```bash
uv sync          # install Python and the locked dependencies (first time)
uv run main.py   # play
uv run pytest    # run all the tests (about a minute and a half)
```

On a machine with no screen, set `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy`.

## Where things are

- `railgame/simulation.py`, `railgame/netsim.py`: the rules. No graphics, so they are tested
  directly. A change to the rules needs a test.
- `railgame/track.py`, `railgame/network.py`, `railgame/levels.py`: the lines and the levels.
- `railgame/render.py`, `railgame/netrender.py`, `railgame/scenery_*.py`, `railgame/skins.py`:
  drawing only. They never change the state of the game.
- `railgame/game.py`: the window, the menus and the input.
- `railgame/custom.py`, `railgame/editor.py`: the level editor and the player's own levels.
- `railgame/junction.py`, `railgame/junctionrender.py`: a custom level with a second line (branch,
  crossing line or separate line) or double track. The rules are a `Network` played by
  `NetSimulation`; the map is one `Layout` per line.
- `railgame/i18n.py`, `railgame/i18n_pt.py`: texts are written in English in the code and
  translated when drawn. Every new text shown on screen needs its Portuguese in `i18n_pt.py`.

## Rules of this repository

- Never delete a branch. Never rewrite the history of `main` or of someone else's branch.
- Work on a new branch, run `uv run pytest`, then open a pull request. A person merges it.
- Commits are made in the name of the team member who asked for the work; an AI assistant is
  named as co-author in the commit message.
- Every train type has six skins (real, vintage, modern, futuristic, dragon, gem). A new train
  type gets all six.
- Sizes on screen go through `S()` / `SR()` from `railgame/ui.py` (the 1280 x 720 design is
  scaled to the window). Do not use raw pixel numbers.
- Dependencies stay pinned to exact versions in `pyproject.toml` and `uv.lock`. Do not add
  one without a reason: the browser build must be able to load it.
- Files the game reads (settings, the player's levels) are data, never code: check every
  value when loading and fall back to a default.
- No secrets, keys or personal data in the repository.
