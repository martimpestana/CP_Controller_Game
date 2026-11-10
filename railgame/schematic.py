"""A schematic view of a line, like the panels in a railway control centre, that still keeps
the shape of the coast the line runs along.

Every crossing station gets a box of the same size, so the stations are easy to read and to
click, whatever the real distances are. Between the stations the track rises and falls with the
real line (from rough GPS coordinates), so the Algarve line climbs from Faro up to Tavira.
Positions are in design pixels (1280 x 720); the renderer scales them with S().
"""

from railgame.layout import ALGARVE_SHAPE, ALGARVE_STATION_SHAPE_INDEX
from railgame.track import LOOP_HALF, POINT_OFFSET, ZONE_HALF, Line, Station

STATION_W = 230  # width of a crossing station box
STATION_GAP = 80  # minimum width of the open line between two station boxes
RISE = 110  # how many pixels higher the east end of the stations sits than the west end


class Schematic:
    def __init__(self, line: Line, left: float, right: float, track_y: float, gap: float):
        self.line = line
        self.track_y = track_y  # height of the track at the lowest crossing station
        self.gap = gap  # vertical distance between track 1 and track 2
        self.left, self.right = left, right
        loops = [st for st in line.stations if st.has_loop]
        # Lay out the boxes at their natural size, then stretch everything to fit.
        anchors: list[tuple[float, float]] = []
        x = 0.0
        for st in loops:
            anchors += [(st.pos - ZONE_HALF, x), (st.pos + ZONE_HALF, x + STATION_W)]
            x += STATION_W + STATION_GAP
        inner_left, inner_right = left + 40, right - 40
        natural = anchors[-1][1] - anchors[0][1]
        k = (inner_right - inner_left) / natural
        self.anchors = [(line.west_edge, left)]
        self.anchors += [(m, inner_left + px * k) for m, px in anchors]
        self.anchors.append((line.east_edge, right))
        self.station_w = STATION_W * k
        self.profile = self._make_profile(loops)

    # ------------------------------------------------------------------ the shape of the line

    def _make_profile(self, loops: list[Station]) -> list[tuple[float, float]]:
        """(x, y) points of track 1, flat through each station box and following the real line
        in between. Lines without known coordinates are drawn flat."""
        if not all(st.code in ALGARVE_STATION_SHAPE_INDEX for st in loops):
            return [(self.left, self.track_y), (self.right, self.track_y)]
        lats = [lat for lat, _ in ALGARVE_SHAPE]
        low, high = min(lats[i] for i in ALGARVE_STATION_SHAPE_INDEX.values()), max(
            lats[i] for i in ALGARVE_STATION_SHAPE_INDEX.values()
        )

        def y_of(lat: float) -> float:
            return self.track_y - (lat - low) / (high - low) * RISE

        def lon_between(lon, lon0, lon1, x0, x1):
            return x0 + (x1 - x0) * (lon - lon0) / (lon1 - lon0)

        idx = [ALGARVE_STATION_SHAPE_INDEX[st.code] for st in loops]
        boxes = [(self.x(st.pos - ZONE_HALF), self.x(st.pos + ZONE_HALF)) for st in loops]
        pts = [(self.left, y_of(ALGARVE_SHAPE[0][0]))]
        # Shape points west of the first station.
        for i in range(1, idx[0]):
            lat, lon = ALGARVE_SHAPE[i]
            pts.append((lon_between(lon, ALGARVE_SHAPE[0][1], ALGARVE_SHAPE[idx[0]][1], self.left, boxes[0][0]), y_of(lat)))
        for n, (st_i, (x0, x1)) in enumerate(zip(idx, boxes)):
            y = y_of(ALGARVE_SHAPE[st_i][0])
            pts += [(x0, y), (x1, y)]
            nxt = idx[n + 1] if n + 1 < len(idx) else len(ALGARVE_SHAPE) - 1
            nx = boxes[n + 1][0] if n + 1 < len(idx) else self.right
            for i in range(st_i + 1, nxt):
                lat, lon = ALGARVE_SHAPE[i]
                pts.append((lon_between(lon, ALGARVE_SHAPE[st_i][1], ALGARVE_SHAPE[nxt][1], x1, nx), y_of(lat)))
        pts.append((self.right, y_of(ALGARVE_SHAPE[-1][0])))
        return pts

    def base_y(self, x: float) -> float:
        """Height of track 1 at screen x."""
        p = self.profile
        if x <= p[0][0]:
            return p[0][1]
        for (x0, y0), (x1, y1) in zip(p, p[1:]):
            if x <= x1:
                return y0 if x1 == x0 else y0 + (y1 - y0) * (x - x0) / (x1 - x0)
        return p[-1][1]

    # ------------------------------------------------------------------ positions

    def x(self, pos: float) -> float:
        a = self.anchors
        if pos <= a[0][0]:
            return a[0][1]
        for (m0, p0), (m1, p1) in zip(a, a[1:]):
            if pos <= m1:
                return p0 + (p1 - p0) * (pos - m0) / (m1 - m0)
        return a[-1][1]

    def y(self, pos: float, track: int = 1) -> float:
        base = self.base_y(self.x(pos))
        if track != 2:
            return base
        st = self.line.loop_station_at(pos)
        if st is None:
            return base
        # Track 2 rises from the points to its full height at the end of the platform.
        d = abs(pos - st.pos)
        t = max(0.0, min(1.0, (POINT_OFFSET - d) / (POINT_OFFSET - LOOP_HALF)))
        return base - self.gap * t

    def point(self, pos: float, track: int = 1) -> tuple[float, float]:
        return (self.x(pos), self.y(pos, track))

    def station_y(self, st: Station) -> float:
        """Height of track 1 through a crossing station."""
        return self.y(st.pos)

    def station_box(self, st: Station) -> tuple[float, float, float, float]:
        """x, y, width, height of the box drawn behind a crossing station."""
        x0, x1 = self.x(st.pos - ZONE_HALF), self.x(st.pos + ZONE_HALF)
        ty = self.station_y(st)
        top = ty - self.gap - 84
        return (x0, top, x1 - x0, ty + 42 - top)
