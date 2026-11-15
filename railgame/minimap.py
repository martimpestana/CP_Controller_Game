"""A small map of Portugal with a line marked on it, for the line's card in the main menu."""

import math

import pygame

from railgame.ui import S

# A rough outline of mainland Portugal, (latitude, longitude), clockwise from the Minho.
PORTUGAL = [
    (41.87, -8.87), (42.06, -8.65), (42.15, -8.19), (41.88, -8.10), (41.82, -7.70), (41.92, -7.20),
    (41.96, -6.90), (41.99, -6.55), (41.67, -6.20), (41.50, -6.27), (41.30, -6.45), (41.03, -6.93),
    (40.60, -6.80), (40.25, -6.86), (40.02, -6.95), (39.66, -7.53), (39.40, -7.30), (38.88, -7.10),
    (38.42, -7.30), (38.20, -6.95), (37.95, -7.25), (37.55, -7.50), (37.19, -7.42), (37.02, -7.93),
    (37.08, -8.30), (37.10, -8.67), (37.02, -8.95), (37.40, -8.80), (37.95, -8.87), (38.30, -8.80),
    (38.42, -9.21), (38.69, -9.32), (38.78, -9.50), (39.10, -9.40), (39.36, -9.40), (39.60, -9.08),
    (40.15, -8.87), (40.64, -8.75), (41.15, -8.68), (41.50, -8.78),
]
# Lines whose map is not drawn from coordinates (the Lisbon network): where they are.
PLACES = {"lisboa": [(38.713, -9.123), (38.740, -9.105), (38.768, -9.099)]}

LAND, COAST, MARK, SHADOW = (60, 78, 98), (120, 140, 160), (250, 200, 60), (20, 20, 20)


def line_coords(key: str, line) -> list[tuple[float, float]]:
    """Where a line is, as (latitude, longitude) points."""
    geo = getattr(line, "geo", None)
    shape = getattr(geo, "shape", None)
    return list(shape) if shape else PLACES.get(key, [])


def draw(surf: pygame.Surface, rect: pygame.Rect, coords: list[tuple[float, float]]) -> None:
    """Portugal fitted into rect, with the line drawn in yellow and circled."""
    lat0, lat1, lon0, lon1 = 36.9, 42.25, -9.65, -6.05
    k = math.cos(math.radians(39.5))  # a degree of longitude is shorter than one of latitude here
    w_deg, h_deg = (lon1 - lon0) * k, lat1 - lat0
    scale = min(rect.width / w_deg, rect.height / h_deg)
    ox = rect.centerx - w_deg * scale / 2
    oy = rect.centery - h_deg * scale / 2

    def px(lat, lon):
        return (ox + (lon - lon0) * k * scale, oy + (lat1 - lat) * scale)

    outline = [px(*p) for p in PORTUGAL]
    pygame.draw.polygon(surf, LAND, outline)
    pygame.draw.lines(surf, COAST, True, outline, 1)
    if not coords:
        return
    pts = [px(*p) for p in coords]
    if len(pts) > 1:
        pygame.draw.lines(surf, SHADOW, False, pts, max(3, S(4)))
        pygame.draw.lines(surf, MARK, False, pts, max(2, S(2.5)))
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    pygame.draw.circle(surf, MARK, (cx, cy), S(7), max(1, S(1.5)))
