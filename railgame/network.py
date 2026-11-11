"""Lines with several tracks side by side, like the Linha do Norte in Lisbon.

The single-track lines (track.py) have one track with short loops at the crossing stations.
A network is more general: any number of tracks run along the line, each with its own number
of metres along the line, joined by points (switches). Tracks can end at a buffer stop (the
platforms of a terminus) or at the edge of the map.

Positions are still metres along the line, from Santa Apolónia. EAST (+1) is north, towards
Oriente and Porto; WEST (-1) is south, towards Santa Apolónia.
"""

from dataclasses import dataclass, field

from railgame.track import EAST, WEST, Point, Signal, Station


@dataclass
class Track:
    id: str
    name: str  # what the drivers call it: "platform 3", "the fast track"
    start: float
    end: float
    lane: float  # where it is drawn: lanes to the left of a northbound train are positive
    open_start: bool = False  # True: the track runs off the map at its start (trains enter/leave)
    open_end: bool = False
    # A track drawn along its own line on the map instead of beside the main line: a list of
    # (x, y) points in design pixels, from its start to its end (the Linha de Cintura).
    path: list[tuple[float, float]] | None = None

    def contains(self, pos: float) -> bool:
        return self.start - 1e-6 <= pos <= self.end + 1e-6

    def end_in(self, direction: int) -> float:
        return self.end if direction == EAST else self.start

    def open_in(self, direction: int) -> bool:
        return self.open_end if direction == EAST else self.open_start


@dataclass
class Switch(Point):
    """Points that join two tracks. A train running in the `facing` direction on the `stem`
    track goes on to `straight` (normal) or to `branch` (diverging, drawn yellow). A train
    coming the other way can only pass if the points are set for the track it is on."""

    stem: str = ""
    straight: str = ""
    branch: str = ""
    facing: int = EAST

    @property
    def track(self) -> str:  # the track the points lead to now
        return self.branch if self.diverging else self.straight

    def is_facing(self, direction: int) -> bool:
        return direction == self.facing


@dataclass
class Geo:
    """How the network looks on the map (never used by the rules)."""

    path: list[tuple[float, float]]  # the main line, in design pixels, from west_edge to east_edge
    start_label: str
    end_label: str
    scenery: str = "plain"
    water_label: str = ""
    lane_gap: float = 15.0  # design pixels between two tracks side by side
    labels: dict[str, str] = field(default_factory=dict)  # track id -> where it goes ("Cintura")


@dataclass
class Network:
    name: str
    stations: list[Station]
    tracks: dict[str, Track]
    points: list[Switch]
    signals: list[Signal]
    platforms: dict[str, tuple[str, ...]]  # station code -> tracks with a platform
    west_edge: float
    east_edge: float
    geo: Geo
    terminus: str | None = None  # station code of the terminus at the west end, if any

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

    def point(self, point_id: str) -> Switch:
        for p in self.points:
            if p.id == point_id:
                return p
        raise KeyError(point_id)

    def track_name(self, track_id: str) -> str:
        return self.tracks[track_id].name


# ---------------------------------------------------------------------- Lisbon

# Positions along the line, in metres from the buffer stops at Santa Apolónia.
SA_THROAT = 420  # the platforms end here, where the points into the station are
BP_JUNCTION_A = 1300  # Linha de Cintura joins the northbound track
BP_JUNCTION_B = 1380  # ...and leaves the southbound track
SPLIT = 1950  # two tracks become four
NORTH_EDGE = 3200


def lisboa_norte() -> Network:
    """Linha do Norte from Santa Apolónia to Oriente.

    Santa Apolónia is a terminus with four platforms. Two tracks run north past Braço de
    Prata, where the Linha de Cintura joins, and then four: a slow and a fast track each way,
    through the big station at Oriente. Northbound trains use track A (slow) or A2 (fast),
    southbound trains B (slow) or B2 (fast).
    """
    sa = Station("Santa Apolónia", "SAP", 140, True)
    bp = Station("Braço de Prata", "BPR", 1650, True)
    ori = Station("Oriente", "ORI", 2550, True)
    stations = [sa, bp, ori]
    T = Track
    # Drawn from the junction up to the top of the map (the last bit to the junction is added
    # by the renderer, so it meets the main line exactly).
    cintura_n = [(400, 372), (378, 266), (362, 160), (350, 62)]
    tracks = {
        "P1": T("P1", "platform 1", 0, SA_THROAT, 1.5),
        "P2": T("P2", "platform 2", 0, SA_THROAT, 0.5),
        "P3": T("P3", "platform 3", 0, SA_THROAT, -0.5),
        "P4": T("P4", "platform 4", 0, SA_THROAT, -1.5),
        "A": T("A", "the northbound track", SA_THROAT, NORTH_EDGE, 0.5, open_end=True),
        "B": T("B", "the southbound track", SA_THROAT, NORTH_EDGE, -0.5, open_end=True),
        "A2": T("A2", "the northbound fast track", SPLIT, NORTH_EDGE, 1.5, open_end=True),
        "B2": T("B2", "the southbound fast track", SPLIT, NORTH_EDGE, -1.5, open_end=True),
        # The Linha de Cintura comes down from Chelas on its own line on the map.
        "CN": T("CN", "the Cintura line", 400, BP_JUNCTION_A, 3, open_start=True, path=list(reversed(cintura_n))),
        "CS": T("CS", "the Cintura line", 480, BP_JUNCTION_B, 4, open_start=True,
                path=[(x + 16, y + 6) for x, y in reversed(cintura_n)]),
    }
    S = Switch
    points = [
        # Into the terminus: A leads to platforms 1 and 2, B to platforms 3 and 4.
        S("SAP-A", sa, SA_THROAT, WEST, stem="A", straight="P2", branch="P1", facing=WEST),
        S("SAP-B", sa, SA_THROAT, WEST, stem="B", straight="P3", branch="P4", facing=WEST),
        # Crossovers in the station throat, so any platform can be used in both directions.
        S("SAP-X", sa, 540, WEST, stem="B", straight="B", branch="A", facing=WEST),
        S("SAP-Y", sa, 650, EAST, stem="B", straight="B", branch="A", facing=EAST),
        # Braço de Prata: the Cintura junction, then the start of the four tracks.
        S("BPR-C", bp, BP_JUNCTION_A, WEST, stem="A", straight="A", branch="CN", facing=WEST),
        S("BPR-D", bp, BP_JUNCTION_B, WEST, stem="B", straight="B", branch="CS", facing=WEST),
        S("BPR-F", bp, SPLIT, EAST, stem="A", straight="A", branch="A2", facing=EAST),
        S("BPR-G", bp, SPLIT, EAST, stem="B", straight="B", branch="B2", facing=EAST),
    ]
    signals = [
        # Leaving Santa Apolónia, one signal at the end of each platform.
        Signal("SAP-1", sa, 395, EAST, "P1"),
        Signal("SAP-2", sa, 395, EAST, "P2"),
        Signal("SAP-3", sa, 395, EAST, "P3"),
        Signal("SAP-4", sa, 395, EAST, "P4"),
        # Coming into Santa Apolónia from the north.
        Signal("SAP-E", sa, 820, WEST, "B"),
        # Trains from the Cintura wait here until the way onto the Linha do Norte is clear.
        Signal("BPR-CN", bp, BP_JUNCTION_A - 120, EAST, "CN"),
        # Leaving Oriente, one signal for each of the four tracks.
        Signal("ORI-A", ori, 2690, EAST, "A"),
        Signal("ORI-A2", ori, 2690, EAST, "A2"),
        Signal("ORI-B", ori, 2410, WEST, "B"),
        Signal("ORI-B2", ori, 2410, WEST, "B2"),
    ]
    platforms = {
        "SAP": ("P1", "P2", "P3", "P4"),
        "BPR": ("A", "B"),
        "ORI": ("A", "A2", "B", "B2"),
    }
    geo = Geo(
        path=[(120, 612), (230, 560), (340, 502), (450, 436), (555, 372), (660, 304), (765, 230), (880, 150)],
        start_label="",
        end_label="Porto · Azambuja",
        scenery="lisboa-storybook",
        water_label="Rio Tejo",
        labels={"CN": "Cintura · Sintra", "CS": ""},
    )
    return Network(
        "Linha do Norte", stations, tracks, points, signals, platforms,
        west_edge=0, east_edge=NORTH_EDGE, geo=geo, terminus="SAP",
    )
