"""Level definitions. Each line has its own list of levels, from an easy start to an expert shift.

A level is a list of trains with their timetables. To make a new level, add a LevelInfo to the
line's list in LEVELS. Times are written as "HH:MM".
"""

from dataclasses import dataclass

from railgame.simulation import Simulation
from railgame.track import EAST, LINES, WEST, Line
from railgame.train import TRAIN_TYPES, Stop, Train, TrainType

RUNNING_MARGIN = 60  # seconds of slack added to each section of the timetable


@dataclass
class TrainPlan:
    name: str
    direction: int
    enters: str  # "HH:MM"

    @property
    def type(self) -> TrainType:
        return TRAIN_TYPES.get(self.name.split()[0], TRAIN_TYPES["R"])

    @property
    def stops_at_halts(self) -> bool:
        """Regional trains (R) stop everywhere; Inter-Regional trains (IR) skip the halts."""
        return self.type.stops == "all"


@dataclass
class LevelInfo:
    number: int
    title: str
    description: str
    start: str
    max_average_delay_min: float
    trains: list[TrainPlan]
    line: str = "algarve"  # a key of track.LINES


LEVELS: dict[str, list[LevelInfo]] = {
    "algarve": [
        LevelInfo(
            1,
            "First shift",
            "Two trains, one crossing. Learn how signals and points work.",
            "07:58",
            3,
            [
                TrainPlan("R 5701", EAST, "08:00"),
                TrainPlan("R 5702", WEST, "08:04"),
            ],
            line="algarve",
        ),
        LevelInfo(
            2,
            "Second crossing",
            "Three trains. The third one crosses somewhere else.",
            "07:58",
            3,
            [
                TrainPlan("R 5701", EAST, "08:00"),
                TrainPlan("R 5702", WEST, "08:04"),
                TrainPlan("R 5703", EAST, "08:24"),
            ],
            line="algarve",
        ),
        LevelInfo(
            3,
            "Morning service",
            "Four trains. Decide where each pair crosses.",
            "07:58",
            3,
            [
                TrainPlan("R 5701", EAST, "08:00"),
                TrainPlan("R 5702", WEST, "08:08"),
                TrainPlan("R 5703", EAST, "08:18"),
                TrainPlan("R 5704", WEST, "08:26"),
            ],
            line="algarve",
        ),
        LevelInfo(
            4,
            "The Inter-Regional",
            "An IR train skips the small halts and catches up with the regionals.",
            "07:58",
            3,
            [
                TrainPlan("R 5701", EAST, "08:00"),
                TrainPlan("R 5702", WEST, "08:06"),
                TrainPlan("IR 801", EAST, "08:16"),
                TrainPlan("R 5704", WEST, "08:24"),
                TrainPlan("R 5705", EAST, "08:36"),
            ],
            line="algarve",
        ),
        LevelInfo(
            5,
            "Rush hour",
            "Six trains in less than an hour. Keep the requests under control.",
            "07:28",
            3,
            [
                TrainPlan("R 5701", EAST, "07:30"),
                TrainPlan("R 5702", WEST, "07:39"),
                TrainPlan("R 5703", EAST, "07:46"),
                TrainPlan("R 5704", WEST, "07:55"),
                TrainPlan("R 5705", EAST, "08:02"),
                TrainPlan("R 5706", WEST, "08:11"),
            ],
            line="algarve",
        ),
        LevelInfo(
            6,
            "Market day in Olhão",
            "Six trains with two IRs. Some pairs arrive at the same time.",
            "07:58",
            4,
            [
                TrainPlan("R 5711", EAST, "08:00"),
                TrainPlan("IR 801", WEST, "08:04"),
                TrainPlan("R 5713", EAST, "08:17"),
                TrainPlan("R 5714", WEST, "08:23"),
                TrainPlan("IR 803", EAST, "08:35"),
                TrainPlan("R 5716", WEST, "08:41"),
            ],
            line="algarve",
        ),
        LevelInfo(
            7,
            "Beach traffic",
            "Seven trains, often two at a time.",
            "16:58",
            5,
            [
                TrainPlan("IR 801", EAST, "17:00"),
                TrainPlan("R 5712", WEST, "17:00"),
                TrainPlan("R 5713", EAST, "17:14"),
                TrainPlan("IR 802", WEST, "17:14"),
                TrainPlan("R 5715", EAST, "17:28"),
                TrainPlan("R 5716", WEST, "17:28"),
                TrainPlan("R 5717", EAST, "17:42"),
            ],
            line="algarve",
        ),
        LevelInfo(
            8,
            "Summer chaos",
            "Eight trains, two at a time. Only the best controllers keep the delay down.",
            "16:58",
            7,
            [
                TrainPlan("IR 801", EAST, "17:00"),
                TrainPlan("R 5712", WEST, "17:00"),
                TrainPlan("R 5713", EAST, "17:14"),
                TrainPlan("IR 802", WEST, "17:14"),
                TrainPlan("R 5715", EAST, "17:28"),
                TrainPlan("R 5716", WEST, "17:28"),
                TrainPlan("R 5717", EAST, "17:42"),
                TrainPlan("R 5718", WEST, "17:42"),
            ],
            line="algarve",
        ),
    ],
    "oeste": [
        LevelInfo(
            1,
            "Up the coast",
            "Two regionals on the Linha do Oeste, a long line with four crossing stations.",
            "08:58",
            3,
            [
                TrainPlan("R 15501", EAST, "09:00"),
                TrainPlan("R 15502", WEST, "09:05"),
            ],
            line="oeste",
        ),
        LevelInfo(
            2,
            "The first freight",
            "A freight train (M) is slow and long, and never stops at a station unless a signal is red.",
            "08:58",
            3,
            [
                TrainPlan("R 15501", EAST, "09:00"),
                TrainPlan("M 52101", WEST, "09:05"),
            ],
            line="oeste",
        ),
        LevelInfo(
            3,
            "Freight on the coast",
            "The freight train has to let the regionals cross it. Find it a place to wait.",
            "08:58",
            3,
            [
                TrainPlan("R 15501", EAST, "09:00"),
                TrainPlan("M 52101", WEST, "09:00"),
                TrainPlan("R 15502", WEST, "09:28"),
            ],
            line="oeste",
        ),
        LevelInfo(
            4,
            "Behind the freight",
            "A regional follows the freight train in the same direction.",
            "08:58",
            4,
            [
                TrainPlan("M 52111", EAST, "09:00"),
                TrainPlan("R 15511", WEST, "09:10"),
                TrainPlan("R 15513", EAST, "09:20"),
                TrainPlan("R 15512", WEST, "09:35"),
            ],
            line="oeste",
        ),
        LevelInfo(
            5,
            "Market day",
            "Regionals both ways and a freight train in the middle of them.",
            "08:58",
            4,
            [
                TrainPlan("R 15511", EAST, "09:00"),
                TrainPlan("R 15512", WEST, "09:07"),
                TrainPlan("M 52111", EAST, "09:12"),
                TrainPlan("R 15513", EAST, "09:36"),
                TrainPlan("R 15514", WEST, "09:48"),
            ],
            line="oeste",
        ),
        LevelInfo(
            6,
            "Two freights",
            "Freight trains in both directions. They need the long gaps between regionals.",
            "08:58",
            5,
            [
                TrainPlan("R 15521", EAST, "09:00"),
                TrainPlan("M 52121", WEST, "09:04"),
                TrainPlan("R 15522", WEST, "09:23"),
                TrainPlan("M 52122", EAST, "09:25"),
                TrainPlan("R 15523", EAST, "09:50"),
                TrainPlan("R 15524", WEST, "09:50"),
            ],
            line="oeste",
        ),
        LevelInfo(
            7,
            "Cement and passengers",
            "Two freight trains against the passenger service. Decide who waits.",
            "15:58",
            6,
            [
                TrainPlan("R 15521", EAST, "16:00"),
                TrainPlan("M 52121", WEST, "16:06"),
                TrainPlan("R 15522", WEST, "16:25"),
                TrainPlan("M 52122", EAST, "16:25"),
                TrainPlan("R 15524", WEST, "16:47"),
                TrainPlan("R 15523", EAST, "16:51"),
                TrainPlan("R 15525", EAST, "17:12"),
            ],
            line="oeste",
        ),
        LevelInfo(
            8,
            "Night of the freights",
            "Eight trains, three of them freight. Only the best controllers keep the line moving.",
            "19:58",
            7,
            [
                TrainPlan("M 52131", EAST, "20:00"),
                TrainPlan("R 15531", WEST, "20:05"),
                TrainPlan("R 15532", EAST, "20:20"),
                TrainPlan("M 52132", WEST, "20:24"),
                TrainPlan("R 15533", WEST, "20:45"),
                TrainPlan("M 52133", EAST, "20:57"),
                TrainPlan("R 15534", EAST, "21:22"),
                TrainPlan("R 15535", WEST, "21:32"),
            ],
            line="oeste",
        ),
    ],
    "douro": [
        LevelInfo(
            1,
            "Along the river",
            "Two regionals on the Linha do Douro. The single-track sections are long.",
            "09:58",
            3,
            [
                TrainPlan("R 860101", EAST, "10:00"),
                TrainPlan("R 860102", WEST, "10:05"),
            ],
            line="douro",
        ),
        LevelInfo(
            2,
            "Wine country",
            "Three trains. Plan where the second regional crosses.",
            "09:58",
            3,
            [
                TrainPlan("R 860101", EAST, "10:00"),
                TrainPlan("R 860102", WEST, "10:05"),
                TrainPlan("R 860103", EAST, "10:38"),
            ],
            line="douro",
        ),
        LevelInfo(
            3,
            "The Inter-Regional",
            "An IR train skips the small halts and catches up with the regionals.",
            "09:58",
            4,
            [
                TrainPlan("R 860101", EAST, "10:00"),
                TrainPlan("R 860102", WEST, "10:00"),
                TrainPlan("IR 871", EAST, "10:20"),
                TrainPlan("R 860104", WEST, "10:39"),
            ],
            line="douro",
        ),
        LevelInfo(
            4,
            "Steam!",
            "The historic steam train (H) is slow and stays a long time at Pinhão.",
            "09:58",
            4,
            [
                TrainPlan("H 1801", EAST, "10:00"),
                TrainPlan("R 860111", WEST, "10:05"),
                TrainPlan("R 860112", WEST, "10:40"),
            ],
            line="douro",
        ),
        LevelInfo(
            5,
            "Overtaking the steam train",
            "A regional catches up with the steam train. Let it pass at a station.",
            "09:58",
            4,
            [
                TrainPlan("H 1801", EAST, "10:00"),
                TrainPlan("R 860111", WEST, "10:03"),
                TrainPlan("R 860112", EAST, "10:36"),
                TrainPlan("R 860114", WEST, "10:46"),
            ],
            line="douro",
        ),
        LevelInfo(
            6,
            "Steam on the Douro",
            "Steam, regionals and an IR. Plan around the slow train.",
            "09:58",
            5,
            [
                TrainPlan("H 1801", EAST, "10:00"),
                TrainPlan("R 860111", WEST, "10:09"),
                TrainPlan("R 860112", EAST, "10:33"),
                TrainPlan("IR 872", WEST, "10:42"),
                TrainPlan("R 860114", WEST, "11:02"),
            ],
            line="douro",
        ),
        LevelInfo(
            7,
            "Two steam trains",
            "Steam trains in both directions meet somewhere on the line.",
            "14:58",
            6,
            [
                TrainPlan("H 1803", EAST, "15:00"),
                TrainPlan("R 860121", WEST, "15:08"),
                TrainPlan("H 1802", WEST, "15:33"),
                TrainPlan("R 860122", EAST, "15:44"),
                TrainPlan("IR 873", EAST, "15:47"),
                TrainPlan("R 860124", WEST, "16:26"),
            ],
            line="douro",
        ),
        LevelInfo(
            8,
            "Harvest season",
            "Steam trains both ways, regionals and IRs. Only for expert controllers.",
            "14:58",
            8,
            [
                TrainPlan("H 1803", EAST, "15:00"),
                TrainPlan("R 860121", WEST, "15:06"),
                TrainPlan("R 860122", EAST, "15:32"),
                TrainPlan("H 1802", WEST, "15:32"),
                TrainPlan("IR 873", EAST, "16:03"),
                TrainPlan("R 860124", WEST, "16:16"),
                TrainPlan("R 860125", EAST, "16:49"),
                TrainPlan("IR 874", WEST, "17:04"),
            ],
            line="douro",
        ),
    ],
}

LINE_NAMES = {key: make().name for key, make in LINES.items()}

# What the menu says about each line: a short description and the trains that run on it.
LINE_BLURBS = {
    "algarve": ("Faro to Tavira, along the Ria Formosa.", "Regional · Inter-Regional"),
    "oeste": ("Torres Vedras to Caldas da Rainha, north along the coast.", "Regional · Freight"),
    "douro": ("Peso da Régua to Ferradosa, along the river.", "Regional · Inter-Regional · Historic steam"),
}


def clock(text: str) -> float:
    hours, minutes = text.split(":")
    return int(hours) * 3600 + int(minutes) * 60


def make_timetable(line: Line, plan: TrainPlan) -> Train:
    """Work out a realistic timetable: running time at line speed plus a small margin.

    Trains that do not stop (freight) still get a passing time at every crossing station.
    """
    kind = plan.type
    direction = plan.direction
    stations = sorted(line.stations, key=lambda st: st.pos * direction)
    edge = line.west_edge if direction == EAST else line.east_edge
    time = clock(plan.enters)
    pos = edge
    stops = []
    for st in stations:
        if not st.has_loop and kind.stops != "all":
            continue
        passing = kind.stops == "none"
        target = st.stop_position(direction)
        time += abs(target - pos) / kind.max_speed + RUNNING_MARGIN
        arrive = time
        if passing:
            pass
        elif st.code in kind.long_stops:
            time += kind.long_dwell
        else:
            time += kind.dwell_loop if st.has_loop else kind.dwell_halt
        # Eastbound trains use track 1 and westbound trains track 2, so they can cross.
        track = (1 if direction == EAST else 2) if st.has_loop else 1
        stops.append(Stop(st, track, round(arrive), round(time), passing=passing))
        pos = target
    return Train(plan.name, direction, clock(plan.enters), stops)


def all_levels() -> list[LevelInfo]:
    return [info for levels in LEVELS.values() for info in levels]


def build_level(line_key: str, number: int) -> tuple[LevelInfo, Simulation]:
    info = LEVELS[line_key][number - 1]
    line = LINES[info.line]()
    trains = [make_timetable(line, plan) for plan in info.trains]
    sim = Simulation(line, trains, clock(info.start), info.max_average_delay_min * 60)
    return info, sim


__all__ = ["LEVELS", "LINE_BLURBS", "LINE_NAMES", "all_levels", "LevelInfo", "TrainPlan", "build_level", "clock", "make_timetable", "WEST", "EAST"]
