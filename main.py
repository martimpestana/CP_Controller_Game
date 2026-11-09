"""Start the game with:  uv run main.py

The same file also runs in the browser (see README: "Play in the browser").
"""

import asyncio

from railgame.game import main

asyncio.run(main())
