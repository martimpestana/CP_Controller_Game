"""The railway itself: stations, points (switches) and signals.

All positions are in metres along the line, measured from Faro.
Positive direction is EAST (towards Tavira), negative is WEST (towards Faro).
"""

from dataclasses import dataclass

EAST = 1
WEST = -1

# Layout of a crossing station (distances from the station centre, in metres).
# The whole station area is drawn as a fixed-size box on the map.
LOOP_HALF = 400  # station tracks 1 and 2 run side by side for 400 m each way
POINT_OFFSET = 600  # the two sets of points sit 600 m each side of the centre
ENTRY_SIGNAL_OFFSET = 900  # entry signals protect the points from outside
ZONE_HALF = 1000  # half the length of the station area


@dataclass
class Station:
    name: str
    code: str
    pos: float
    has_loop: bool  # True: crossing station with two tracks. False: simple halt.

    def stop_position(self, direction: int) -> float:
        """Where the head of a train stops, so that the train sits centred in the platform."""
        return self.pos + direction * 75


@dataclass
class Point:
    """A set of points (in Portuguese: agulha). Straight leads to track 1, diverging to track 2."""

    id: str
    station: Station
    pos: float
    side: int  # WEST or EAST end of the station
    diverging: bool = False

    @property
    def track(self) -> int:
        return 2 if self.diverging else 1

    def is_facing(self, direction: int) -> bool:
        """A train meets facing points when it enters the station, and trailing points when it leaves."""
        return self.side == -direction


@dataclass
class Signal:
    """A two-aspect signal. Red means stop, green means go."""

    id: str
    station: Station
    pos: float
    direction: int  # the direction of the trains this signal talks to
    track: int | None  # None: entry signal on the single line. 1 or 2: exit signal of that track.
    green: bool = False

    def applies_to(self, direction: int, track: int) -> bool:
        return self.direction == direction and (self.track is None or self.track == track)

    @property
    def is_entry(self) -> bool:
        return self.track is None


@dataclass
class Geography:
    """How a line looks on the map. Only used for drawing, never by the game rules."""

    shape: list[tuple[float, float]]  # approximate (latitude, longitude) points along the line
    station_shape_index: dict[str, int]  # which shape point each crossing station sits on
    start_label: str  # where the line continues off the map, at each end
    end_label: str
    water: str = "sea"  # "sea" or "river"
    water_side: int = -1  # -1: to the right of a train going in the positive direction, +1: to the left
    water_edge: str = "bottom"  # for the sea: which edge of the map it reaches ("bottom" or "left")
    water_label: str = "Atlantic Ocean"
    barrier_islands: bool = False  # the sandy islands of the Ria Formosa
    # Where the map is drawn, in 1280x720 design pixels (x, y, width, height). None: the default box.
    map_box: tuple[int, int, int, int] | None = None


@dataclass
class Line:
    name: str
    stations: list[Station]
    points: list[Point]
    signals: list[Signal]
    west_edge: float  # where the map ends on each side
    east_edge: float
    geo: Geography | None = None

    def station(self, code: str) -> Station:
        for st in self.stations:
            if st.code == code:
                return st
        raise KeyError(code)

    def signal(self, signal_id: str) -> Signal:
        for s in self.signals:
            if s.id == signal_id:
                return s
        raise KeyError(signal_id)

    def point(self, point_id: str) -> Point:
        for p in self.points:
            if p.id == point_id:
                return p
        raise KeyError(point_id)

    def loop_station_at(self, pos: float) -> Station | None:
        """The crossing station whose area contains this position, if any."""
        for st in self.stations:
            if st.has_loop and abs(pos - st.pos) <= ZONE_HALF:
                return st
        return None


def build_line(
    name: str, stations: list[Station], west_edge: float, east_edge: float, geo: Geography | None = None
) -> Line:
    """Create the points and signals for every crossing station automatically."""
    points: list[Point] = []
    signals: list[Signal] = []
    for st in stations:
        if not st.has_loop:
            continue
        points.append(Point(f"{st.code}-PW", st, st.pos - POINT_OFFSET, WEST))
        points.append(Point(f"{st.code}-PE", st, st.pos + POINT_OFFSET, EAST))
        # Entry signals, one for each direction, in front of the points.
        signals.append(Signal(f"{st.code}-E0", st, st.pos - ENTRY_SIGNAL_OFFSET, EAST, None))
        signals.append(Signal(f"{st.code}-W0", st, st.pos + ENTRY_SIGNAL_OFFSET, WEST, None))
        # Exit signals at the end of each platform track.
        for track in (1, 2):
            signals.append(Signal(f"{st.code}-E{track}", st, st.pos + LOOP_HALF, EAST, track))
            signals.append(Signal(f"{st.code}-W{track}", st, st.pos - LOOP_HALF, WEST, track))
    return Line(name, stations, points, signals, west_edge, east_edge, geo)


# ---------------------------------------------------------------------- the lines
#
# Positions are in metres from the first crossing station. "EAST" is simply the positive direction
# along the line (on the Linha do Oeste it points north, towards Caldas da Rainha).
# Distances and coordinates are approximate: the map is simplified, not to scale.


def algarve_faro_tavira() -> Line:
    """Linha do Algarve between Faro and Tavira (single track, trains cross at stations)."""
    stations = [
        Station("Faro", "FAR", 0, True),
        Station("Bom João", "BJO", 1900, False),
        Station("Olhão", "OLH", 8600, True),
        Station("Fuseta-A", "FUA", 16000, False),
        Station("Fuseta", "FUS", 17400, True),
        Station("Livramento", "LIV", 23000, False),
        Station("Tavira", "TAV", 30000, True),
    ]
    geo = Geography(
        shape=[
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
        ],
        station_shape_index={"FAR": 1, "OLH": 4, "FUS": 7, "TAV": 10},
        start_label="Loulé",
        end_label="V. R. S. António",
        barrier_islands=True,
    )
    return build_line("Linha do Algarve", stations, west_edge=-2500, east_edge=32500, geo=geo)


def oeste_torres_caldas() -> Line:
    """Linha do Oeste between Torres Vedras and Caldas da Rainha (single track, north-south)."""
    stations = [
        Station("Torres Vedras", "TVD", 0, True),
        Station("Ramalhal", "RML", 8000, True),
        Station("Outeiro", "OUT", 14500, False),
        Station("Bombarral", "BBR", 22500, True),
        Station("Óbidos", "OBI", 33000, False),
        Station("Caldas da Rainha", "CRA", 38500, True),
    ]
    geo = Geography(
        shape=[
            (39.0700, -9.2700),  # towards Lisboa
            (39.0935, -9.2585),  # Torres Vedras
            (39.1180, -9.2560),
            (39.1430, -9.2420),  # Ramalhal
            (39.1800, -9.2150),
            (39.2250, -9.1800),
            (39.2672, -9.1556),  # Bombarral
            (39.3100, -9.1650),
            (39.3600, -9.1572),  # Óbidos
            (39.3850, -9.1450),
            (39.4030, -9.1385),  # Caldas da Rainha
            (39.4300, -9.1200),  # towards Leiria
        ],
        station_shape_index={"TVD": 1, "RML": 3, "BBR": 6, "CRA": 10},
        start_label="Lisboa",
        end_label="Leiria",
        water="sea",
        water_side=1,  # the Atlantic is to the west, on the left of a northbound train
        water_edge="left",
        map_box=(300, 80, 440, 620),  # a north-south line gets a tall map
    )
    return build_line("Linha do Oeste", stations, west_edge=-2500, east_edge=41000, geo=geo)


def douro_regua_ferradosa() -> Line:
    """Linha do Douro between Peso da Régua and Ferradosa, along the river (single track)."""
    stations = [
        Station("Peso da Régua", "REG", 0, True),
        Station("Covelinhas", "COV", 9500, False),
        Station("Ferrão", "FRR", 15500, False),
        Station("Pinhão", "PIN", 22500, True),
        Station("Tua", "TUA", 35500, True),
        Station("Alegria", "ALE", 41000, False),
        Station("Ferradosa", "FRD", 47000, True),
    ]
    geo = Geography(
        shape=[
            (41.1580, -7.8250),  # towards Porto
            (41.1600, -7.7870),  # Peso da Régua
            (41.1580, -7.7400),
            (41.1630, -7.6890),
            (41.1770, -7.6180),
            (41.1900, -7.5460),  # Pinhão
            (41.2080, -7.4750),
            (41.2140, -7.4280),  # Tua
            (41.2080, -7.3900),
            (41.1600, -7.3600),
            (41.1440, -7.3300),  # Ferradosa
            (41.1350, -7.2900),  # towards Pocinho
        ],
        station_shape_index={"REG": 1, "PIN": 5, "TUA": 7, "FRD": 10},
        start_label="Porto",
        end_label="Pocinho",
        water="river",
        water_side=-1,
        water_label="Rio Douro",
    )
    return build_line("Linha do Douro", stations, west_edge=-2500, east_edge=49500, geo=geo)


LINES = {
    "algarve": algarve_faro_tavira,
    "oeste": oeste_torres_caldas,
    "douro": douro_regua_ferradosa,
}
