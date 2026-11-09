"""Screen scaling and smooth (anti-aliased) drawing helpers.

The game is designed for a 1280 x 720 window. On bigger screens, or on Windows with display
zoom at 125% / 150%, everything is drawn bigger with S() so it stays sharp instead of being
stretched by the operating system.
"""

import math
import os
import sys

import pygame
from pygame import gfxdraw

DESIGN_WIDTH, DESIGN_HEIGHT = 1280, 720

_scale = 1.0


def set_scale(value: float) -> None:
    global _scale
    _scale = value


def scale() -> float:
    return _scale


def S(value: float) -> int:
    """Convert a size from the 1280 x 720 design into real screen pixels."""
    return int(round(value * _scale))


def SR(x: float, y: float, w: float, h: float) -> pygame.Rect:
    return pygame.Rect(S(x), S(y), S(w), S(h))


def font(size: int, bold: bool = False) -> pygame.font.Font:
    return pygame.font.SysFont("segoeui,dejavusans,arial,helvetica", S(size), bold=bold)


def make_dpi_aware() -> None:
    """Ask Windows for real pixels, so the window is not blurred by display zoom."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def best_scale() -> float:
    """The biggest scale that fits the window comfortably on the screen."""
    override = os.environ.get("CP_SCALE")
    if override:
        return float(override)
    try:
        width, height = pygame.display.get_desktop_sizes()[0]
    except (pygame.error, IndexError):
        return 1.0
    value = min((width - 40) / DESIGN_WIDTH, (height - 110) / DESIGN_HEIGHT)
    return max(0.6, round(value, 2))


# ---------------------------------------------------------------------- smooth drawing


def circle(surf, colour, centre, radius) -> None:
    x, y, r = int(round(centre[0])), int(round(centre[1])), int(round(radius))
    if r < 1:
        return
    gfxdraw.aacircle(surf, x, y, r, colour)
    gfxdraw.filled_circle(surf, x, y, r, colour)


def ring(surf, colour, centre, radius, width) -> None:
    x, y = int(round(centre[0])), int(round(centre[1]))
    for i in range(max(1, int(round(width)))):
        gfxdraw.aacircle(surf, x, y, int(round(radius)) - i, colour)


def thick_lines(surf, colour, points, width) -> None:
    """A smooth polyline of any width, with round joints."""
    half = width / 2
    pts = [p for i, p in enumerate(points) if i == 0 or math.dist(p, points[i - 1]) > 0.01]
    for a, b in zip(pts, pts[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        nx, ny = -dy / length * half, dx / length * half
        quad = [(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)]
        gfxdraw.aapolygon(surf, quad, colour)
        gfxdraw.filled_polygon(surf, quad, colour)
    if half >= 1.5:
        for p in pts:
            circle(surf, colour, p, half - 0.5)


def thick_line(surf, colour, a, b, width) -> None:
    thick_lines(surf, colour, [a, b], width)
