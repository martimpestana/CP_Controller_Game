"""Level definitions. A level is a line plus a list of trains with their timetables.

To make a new level, add an entry to LEVELS. Times are written as "HH:MM".
"""

from dataclasses import dataclass

from railgame.simulation import Simulation
from railgame.track import EAST, WEST, Line, algarve_faro_tavira
from railgame.train import MAX_SPEED, Stop, Train

RUNNING_MARGIN = 60  # seconds of slack added to each section of the timetable
DWELL_LOOP = 60  # scheduled stop at a crossing station, in seconds
DWELL_HALT = 30  # scheduled stop at a halt


@dataclass
class TrainPlan:
    name: str
    direction: int
    enters: str  # "HH:MM"


@dataclass
class LevelInfo:
    number: int
    title: str
    description: str
    start: str
    max_average_delay_min: float
    trains: list[TrainPlan]


LEVELS = [
    LevelInfo(
        1,
        "First shift",
        "Two trains, one crossing. Learn how signals and points work.",
        "07:58",
        3,
        [TrainPlan("R 5701", EAST, "08:00"), TrainPlan("R 5702", WEST, "08:04")],
    ),
    LevelInfo(
        2,
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
    ),
    LevelInfo(
        3,
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
    ),
    LevelInfo(
        4,
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
    ),
]


def clock(text: str) -> float:
    hours, minutes = text.split(":")
    return int(hours) * 3600 + int(minutes) * 60


def make_timetable(line: Line, plan: TrainPlan) -> Train:
    """Work out a realistic timetable: running time at line speed plus a small margin."""
    direction = plan.direction
    stations = sorted(line.stations, key=lambda st: st.pos * direction)
    edge = line.west_edge if direction == EAST else line.east_edge
    time = clock(plan.enters)
    pos = edge
    stops = []
    for st in stations:
        target = st.stop_position(direction)
        time += abs(target - pos) / MAX_SPEED + RUNNING_MARGIN
        arrive = time
        time += DWELL_LOOP if st.has_loop else DWELL_HALT
        # Eastbound trains use track 1 and westbound trains track 2, so they can cross.
        track = (1 if direction == EAST else 2) if st.has_loop else 1
        stops.append(Stop(st, track, round(arrive), round(time)))
        pos = target
    return Train(plan.name, direction, clock(plan.enters), stops)


def build_level(number: int) -> tuple[LevelInfo, Simulation]:
    info = LEVELS[number - 1]
    line = algarve_faro_tavira()
    trains = [make_timetable(line, plan) for plan in info.trains]
    sim = Simulation(line, trains, clock(info.start), info.max_average_delay_min * 60)
    return info, sim


__all__ = ["LEVELS", "LevelInfo", "TrainPlan", "build_level", "clock", "make_timetable", "WEST", "EAST"]
