"""A little geography, so the schematic panel still feels like the map of Portugal.

The outline is rough (about 40 points, latitude and longitude); it is only drawn as a small
inset map and is not used by the simulation.
"""

import math

PORTUGAL = [
    # west coast, from the Minho down to Cabo de São Vicente
    (41.87, -8.87), (41.69, -8.84), (41.37, -8.76), (41.15, -8.67), (40.85, -8.66),
    (40.64, -8.75), (40.15, -8.87), (39.84, -8.95), (39.60, -9.07), (39.36, -9.40),
    (39.10, -9.37), (38.78, -9.50), (38.69, -9.42), (38.69, -9.14), (38.65, -9.25),
    (38.42, -9.21), (38.48, -8.90), (38.30, -8.79), (37.95, -8.87), (37.70, -8.80),
    (37.40, -8.82), (37.02, -8.99),
    # the Algarve coast
    (37.08, -8.67), (37.10, -8.45), (37.08, -8.25), (37.06, -8.05), (37.00, -7.93),
    (37.04, -7.80), (37.12, -7.65), (37.18, -7.41),
    # the border with Spain, from the Guadiana back up to the Minho
    (37.55, -7.47), (37.85, -7.28), (38.20, -6.95), (38.55, -7.23), (38.85, -7.05),
    (39.20, -7.25), (39.66, -7.53), (39.85, -7.00), (40.20, -6.86), (40.60, -6.80),
    (41.03, -6.92), (41.35, -6.40), (41.60, -6.20), (41.95, -6.55), (41.95, -7.20),
    (41.85, -7.60), (41.92, -7.95), (42.13, -8.20),
]

# The stretch of line each level is played on, as (latitude, longitude) from west to east.
ALGARVE_LINE = [(37.02, -7.94), (37.03, -7.84), (37.05, -7.74), (37.13, -7.65)]


def project(lat: float, lon: float) -> tuple[float, float]:
    """Flat x/y in degrees, with longitude squeezed so the shape is not stretched."""
    return (lon * math.cos(math.radians(39.5)), -lat)


def fit(points, rect):
    """Scale projected points into rect (x, y, w, h), keeping the shape's proportions.
    Returns a function that maps (lat, lon) to screen positions."""
    xy = [project(*p) for p in points]
    xs, ys = [p[0] for p in xy], [p[1] for p in xy]
    x0, y0, w, h = rect
    k = min(w / (max(xs) - min(xs)), h / (max(ys) - min(ys)))
    ox = x0 + (w - (max(xs) - min(xs)) * k) / 2
    oy = y0 + (h - (max(ys) - min(ys)) * k) / 2

    def to_screen(lat, lon):
        px, py = project(lat, lon)
        return (ox + (px - min(xs)) * k, oy + (py - min(ys)) * k)

    return to_screen
