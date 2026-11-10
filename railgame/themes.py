"""Colour themes for the map and the panels, chosen in the Customise menu."""

DEFAULT_THEME = "night"

# (id, name in the menu, colours). The colour names match the constants in render.py.
_THEMES = [
    (
        "night",
        "Night",
        {
            "BG": (16, 24, 33), "LAND": (24, 35, 45), "SEA": (14, 44, 64), "SAND": (120, 110, 80),
            "TRACK": (190, 196, 204), "TRACK_DIM": (95, 104, 115), "PANEL": (28, 38, 50),
            "CARD": (38, 52, 68), "BUTTON": (48, 64, 82), "OCEAN_TEXT": (90, 130, 150), "MAP_MUTED": (150, 160, 172),
        },
    ),
    (
        "day",
        "Day",
        {
            "BG": (26, 38, 50), "LAND": (98, 138, 90), "SEA": (52, 112, 160), "SAND": (226, 210, 160),
            "TRACK": (246, 246, 246), "TRACK_DIM": (66, 90, 66), "PANEL": (28, 40, 54),
            "CARD": (40, 56, 74), "BUTTON": (50, 68, 88), "OCEAN_TEXT": (190, 220, 240), "MAP_MUTED": (232, 240, 222),
        },
    ),
    (
        "sunset",
        "Sunset",
        {
            "BG": (28, 18, 32), "LAND": (60, 36, 58), "SEA": (42, 46, 96), "SAND": (224, 150, 100),
            "TRACK": (242, 222, 210), "TRACK_DIM": (112, 84, 106), "PANEL": (40, 26, 44),
            "CARD": (58, 40, 62), "BUTTON": (76, 50, 82), "OCEAN_TEXT": (170, 150, 210), "MAP_MUTED": (200, 170, 196),
        },
    ),
    (
        "retro",
        "Control room",
        {
            "BG": (6, 10, 8), "LAND": (10, 24, 14), "SEA": (6, 14, 26), "SAND": (60, 110, 70),
            "TRACK": (140, 255, 160), "TRACK_DIM": (40, 90, 50), "PANEL": (12, 22, 16),
            "CARD": (20, 36, 26), "BUTTON": (28, 52, 36), "OCEAN_TEXT": (60, 130, 90), "MAP_MUTED": (90, 190, 110),
        },
    ),
]

THEMES = {tid: colours for tid, _, colours in _THEMES}
THEME_NAMES = [(tid, name) for tid, name, _ in _THEMES]
