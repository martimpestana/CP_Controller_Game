"""Start the game with:  uv run main.py

The same file also runs in the browser (see README: "Play in the browser").
"""

import asyncio

# pygbag (the browser version) only loads pygame when main.py itself imports it.
# Without this line the browser stops with "module 'pygame' has no attribute 'Rect'".
import pygame  # noqa: F401

from railgame.game import main

asyncio.run(main())
