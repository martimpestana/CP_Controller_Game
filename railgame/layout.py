"""Turns positions on the line (metres) into pixels on the screen.

The line follows its real shape (from approximate GPS coordinates), but every crossing
station gets a box of fixed size so that the platforms, points and signals are easy to click.
"""

import math

from railgame.track import LOOP_HALF, POINT_OFFSET, ZONE_HALF, Line, Station

# Approximate coordinates (latitude, longitude) that give the line its shape.
ALGARVE_SHAPE = [
    (37.0300, -8.0000),  # towards Loulé
    (37.0190, -7.9405),  # Faro
    (37.0225, -7.9180),
    (37.0250, -7.8800),
    (37.0285, -7.8420),  # Olhão
    (37.0380, -7.8000),
    (37.0505, -7.7580),
    (37.0540, -7.7440),  # Fuseta
    (37.0700, -7.7150),
    (37.0850, -7.6900),
    (37.1265, -7.6510),  # Tavira
    (37.1500, -7.6050),  # towards Vila Real de Santo António
]
# Which shape point each crossing station sits on.
ALGARVE_STATION_SHAPE_INDEX = {"FAR": 1, "OLH": 4, "FUS": 7, "TAV": 10}

ZONE_PX = 80  # half width of a station box, in pixels
TRACK_GAP = 18  # distance between station tracks 1 and 2, in pixels


def _lerp(a, b, t):
    return a + (b - a) * t


class Layout:
    def __init__(self, line: Line, rect: tuple[int, int, int, int], scale: float = 1.0):
        self.line = line
        self.zone_px = ZONE_PX * scale
        self.track_gap = TRACK_GAP * scale
        left, top, width, height = rect
        raw = [(lon * math.cos(math.radians(37.07)), -lat) for lat, lon in ALGARVE_SHAPE]
        xs = [p[0] for p in raw]
        ys = [p[1] for p in raw]
        self.path = [
            (
                left + (x - min(xs)) / (max(xs) - min(xs)) * width,
                top + (y - min(ys)) / (max(ys) - min(ys)) * height,
            )
            for x, y in raw
        ]
        self.cum = [0.0]
        for a, b in zip(self.path, self.path[1:]):
            self.cum.append(self.cum[-1] + math.dist(a, b))

        # Anchors: (metres along the line, pixels along the drawn path).
        anchors = [(line.west_edge, 0.0), (line.east_edge, self.cum[-1])]
        self.station_px: dict[str, float] = {}
        for st in line.stations:
            if st.has_loop:
                d = self.cum[ALGARVE_STATION_SHAPE_INDEX[st.code]]
                self.station_px[st.code] = d
                anchors.append((st.pos - ZONE_HALF, d - self.zone_px))
                anchors.append((st.pos + ZONE_HALF, d + self.zone_px))
        self.anchors = sorted(anchors)

    # ------------------------------------------------------------------ basic geometry

    def _path_at(self, d: float) -> tuple[float, float]:
        d = max(0.0, min(self.cum[-1], d))
        for i in range(len(self.path) - 1):
            if self.cum[i + 1] >= d:
                a, b = self.path[i], self.path[i + 1]
                t = (d - self.cum[i]) / (self.cum[i + 1] - self.cum[i])
                return (_lerp(a[0], b[0], t), _lerp(a[1], b[1], t))
        return self.path[-1]

    def _metres_to_px(self, pos: float) -> float:
        a = self.anchors
        if pos <= a[0][0]:
            return a[0][1] + (pos - a[0][0]) * (a[1][1] - a[0][1]) / (a[1][0] - a[0][0])
        for (m0, p0), (m1, p1) in zip(a, a[1:]):
            if pos <= m1:
                return _lerp(p0, p1, (pos - m0) / (m1 - m0))
        return a[-1][1] + (pos - a[-1][0]) * (a[-1][1] - a[-2][1]) / (a[-1][0] - a[-2][0])

    def frame(self, st: Station):
        """Centre, direction along the track and direction 'north' for a station box."""
        d = self.station_px[st.code]
        a = self._path_at(d - self.zone_px)
        b = self._path_at(d + self.zone_px)
        length = math.dist(a, b)
        ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
        centre = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        return centre, (ux, uy), (uy, -ux)

    def local(self, st: Station, along_m: float, offset_px: float) -> tuple[float, float]:
        (cx, cy), (ux, uy), (nx, ny) = self.frame(st)
        along = along_m * self.zone_px / ZONE_HALF
        return (cx + ux * along + nx * offset_px, cy + uy * along + ny * offset_px)

    # ------------------------------------------------------------------ public helpers

    def point(self, pos: float, track: int = 1) -> tuple[float, float]:
        """Screen position of a place on the line (track 2 only exists inside crossing stations)."""
        st = self.line.loop_station_at(pos)
        if st is not None:
            offset = 0.0
            if track == 2:
                x = abs(pos - st.pos)
                offset = self.track_gap * max(0.0, min(1.0, (POINT_OFFSET - x) / (POINT_OFFSET - LOOP_HALF)))
            return self.local(st, pos - st.pos, offset)
        return self._path_at(self._metres_to_px(pos))

    def normal(self, pos: float) -> tuple[float, float]:
        """Unit vector pointing 'north' (to the left of an eastbound train) at this place."""
        a = self.point(pos - 50)
        b = self.point(pos + 50)
        length = math.dist(a, b) or 1.0
        ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
        return (uy, -ux)

    def scale(self, pos: float) -> float:
        """Pixels per metre at this place."""
        return math.dist(self.point(pos - 50), self.point(pos + 50)) / 100

    def polyline(self, start: float, end: float, track: int = 1, step: float = 25.0):
        pts = []
        pos = start
        while pos < end:
            pts.append(self.point(pos, track))
            pos += step
        pts.append(self.point(end, track))
        return pts

    def main_track(self) -> list[tuple[float, float]]:
        return self.polyline(self.line.west_edge, self.line.east_edge)

    def loop_track(self, st: Station) -> list[tuple[float, float]]:
        return self.polyline(st.pos - POINT_OFFSET, st.pos + POINT_OFFSET, track=2)
