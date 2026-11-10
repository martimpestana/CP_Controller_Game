"""A schematic view of a line, like the panels in a railway control centre.

The line is drawn straight across the screen. Every crossing station gets a box of the same
size, so the stations are easy to read and to click, whatever the real distances are.
Positions are in design pixels (1280 x 720); the renderer scales them with S().
"""

from railgame.track import LOOP_HALF, POINT_OFFSET, ZONE_HALF, Line, Station

STATION_W = 230  # width of a crossing station box
STATION_GAP = 80  # minimum width of the open line between two station boxes


class Schematic:
    def __init__(self, line: Line, left: float, right: float, track_y: float, gap: float):
        self.line = line
        self.track_y = track_y
        self.gap = gap  # vertical distance between track 1 and track 2
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

    def x(self, pos: float) -> float:
        a = self.anchors
        if pos <= a[0][0]:
            return a[0][1]
        for (m0, p0), (m1, p1) in zip(a, a[1:]):
            if pos <= m1:
                return p0 + (p1 - p0) * (pos - m0) / (m1 - m0)
        return a[-1][1]

    def y(self, pos: float, track: int = 1) -> float:
        if track != 2:
            return self.track_y
        st = self.line.loop_station_at(pos)
        if st is None:
            return self.track_y
        # Track 2 rises from the points to its full height at the end of the platform.
        d = abs(pos - st.pos)
        t = max(0.0, min(1.0, (POINT_OFFSET - d) / (POINT_OFFSET - LOOP_HALF)))
        return self.track_y - self.gap * t

    def point(self, pos: float, track: int = 1) -> tuple[float, float]:
        return (self.x(pos), self.y(pos, track))

    def station_box(self, st: Station) -> tuple[float, float, float, float]:
        """x, y, width, height of the box drawn behind a crossing station."""
        x0, x1 = self.x(st.pos - ZONE_HALF), self.x(st.pos + ZONE_HALF)
        top = self.track_y - self.gap - 84
        return (x0, top, x1 - x0, self.track_y + 42 - top)
