"""Level definitions. Each line has its own list of levels, from an easy start to an expert shift.

A level is a list of trains with their timetables. To make a new level, add a LevelInfo to the
line's list in LEVELS. Times are written as "HH:MM".
"""

import random
from dataclasses import dataclass

from railgame.netsim import APPEAR_BEFORE, NetSimulation
from railgame.network import Network
from railgame.simulation import Simulation
from railgame.track import EAST, LINES, WEST, Line, Station
from railgame.train import TRAIN_TYPES, Stop, Train, TrainType

RUNNING_MARGIN = 60  # seconds of slack added to each section of the timetable


@dataclass
class TrainPlan:
    name: str
    direction: int
    enters: str  # "HH:MM". From a terminus (Santa Apolónia): the departure time.
    # Only on networks (Linha do Norte): where it starts and ends, "SAP" (Santa Apolónia, the
    # default), "CIN" (the Cintura line) or "N" (north, off the map), and a platform it should use.
    frm: str = ""
    to: str = ""
    platform: str = ""

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
    # Some trains reach the map late, by a different amount every time the level is played
    # (see random_delays). Their own lateness is not counted, only what the controller adds.
    random_delays: bool = False


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
        LevelInfo(
            9,
            "Running late",
            "Level 7's trains, but some reach the map late, and never the same ones twice. Their own lateness is not counted, only the delay you add.",
            "16:58",
            6,
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
            random_delays=True,
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
        LevelInfo(
            9,
            "Running late",
            "Level 7's trains, but some reach the map late, and never the same ones twice. Their own lateness is not counted, only the delay you add.",
            "15:58",
            7,
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
            random_delays=True,
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
        LevelInfo(
            9,
            "Running late",
            "Level 7's trains, but some reach the map late, and never the same ones twice. Their own lateness is not counted, only the delay you add.",
            "14:58",
            7,
            [
                TrainPlan("H 1803", EAST, "15:00"),
                TrainPlan("R 860121", WEST, "15:08"),
                TrainPlan("H 1802", WEST, "15:33"),
                TrainPlan("R 860122", EAST, "15:44"),
                TrainPlan("IR 873", EAST, "15:47"),
                TrainPlan("R 860124", WEST, "16:26"),
            ],
            line="douro",
            random_delays=True,
        ),
    ],
    "lisboa": [
        LevelInfo(
            1,
            "Santa Apolónia",
            "A terminus: trains to Lisbon end here, trains from Lisbon start here. One out, one in.",
            "06:56",
            3,
            [
                TrainPlan("R 16001", EAST, "07:00"),
                TrainPlan("R 16002", WEST, "07:01"),
            ],
            line="lisboa",
        ),
        LevelInfo(
            2,
            "The Alfa Pendular",
            "The Alfa is fast. After Braço de Prata send it onto the fast track, away from the regionals.",
            "06:56",
            3,
            [
                TrainPlan("AP 120", EAST, "07:00"),
                TrainPlan("R 16003", EAST, "07:03"),
                TrainPlan("AP 121", WEST, "07:02"),
            ],
            line="lisboa",
        ),
        LevelInfo(
            3,
            "Four platforms",
            "Trains in and out at the same time. Keep arrivals and departures on their own platforms.",
            "06:56",
            3,
            [
                TrainPlan("R 16005", EAST, "07:00"),
                TrainPlan("R 16006", WEST, "07:00"),
                TrainPlan("IC 520", EAST, "07:04"),
                TrainPlan("R 16008", WEST, "07:03"),
                TrainPlan("R 16007", EAST, "07:07"),
            ],
            line="lisboa",
        ),
        LevelInfo(
            4,
            "The Cintura line",
            "Trains from Sintra join at Braço de Prata, and some trains from the north go off to Sintra.",
            "06:58",
            3,
            [
                TrainPlan("R 18201", EAST, "07:00", frm="CIN"),
                TrainPlan("R 16011", EAST, "07:01"),
                TrainPlan("R 18202", WEST, "07:01", to="CIN"),
                TrainPlan("R 16012", WEST, "07:03"),
                TrainPlan("R 18203", EAST, "07:05", frm="CIN"),
            ],
            line="lisboa",
        ),
        LevelInfo(
            5,
            "Overtaking at Oriente",
            "The regional leaves first, the Intercidades soon after. Let the fast train pass at Oriente.",
            "06:56",
            3,
            [
                TrainPlan("R 16021", EAST, "07:00"),
                TrainPlan("IC 522", EAST, "07:01"),
                TrainPlan("R 16022", WEST, "07:00"),
                TrainPlan("AP 123", WEST, "07:01"),
                TrainPlan("R 18205", EAST, "07:03", frm="CIN"),
            ],
            line="lisboa",
        ),
        LevelInfo(
            6,
            "Freight to Alcântara",
            "A long, slow freight train comes down from the north and turns off onto the Cintura line.",
            "06:58",
            3,
            [
                TrainPlan("M 60101", WEST, "07:00", to="CIN"),
                TrainPlan("AP 125", WEST, "07:01"),
                TrainPlan("R 16031", EAST, "07:00"),
                TrainPlan("R 16032", WEST, "07:03"),
                TrainPlan("AP 126", EAST, "07:04"),
                TrainPlan("M 60102", EAST, "07:02", frm="CIN"),
            ],
            line="lisboa",
        ),
        LevelInfo(
            7,
            "Full house",
            "More trains arrive than platforms 3 and 4 can take. Use the crossover to platforms 1 and 2.",
            "06:56",
            4,
            [
                TrainPlan("R 16041", EAST, "07:00"),
                TrainPlan("R 16042", WEST, "06:59"),
                TrainPlan("AP 127", WEST, "07:00"),
                TrainPlan("IC 524", WEST, "07:02"),
                TrainPlan("R 16044", WEST, "07:04"),
                TrainPlan("AP 128", EAST, "07:05"),
                TrainPlan("R 16043", EAST, "07:08"),
            ],
            line="lisboa",
        ),
        LevelInfo(
            8,
            "Morning rush",
            "The busiest hour of the day: Alfas, Intercidades, regionals, the Cintura and a freight.",
            "06:56",
            4,
            [
                TrainPlan("R 16051", EAST, "07:00"),
                TrainPlan("R 16052", WEST, "06:59"),
                TrainPlan("AP 131", WEST, "07:00"),
                TrainPlan("R 18211", EAST, "07:01", frm="CIN"),
                TrainPlan("AP 130", EAST, "07:03"),
                TrainPlan("M 60111", WEST, "07:02", to="CIN"),
                TrainPlan("R 16054", WEST, "07:04"),
                TrainPlan("IC 530", EAST, "07:06"),
                TrainPlan("R 18212", WEST, "07:06", to="CIN"),
                TrainPlan("R 16053", EAST, "07:08"),
                TrainPlan("IC 531", WEST, "07:07"),
            ],
            line="lisboa",
        ),
    ],
    "alentejo": [
        LevelInfo(
            1,
            "Across the plain",
            "Two regionals between Casa Branca and Beja. The line is long: plan where they cross.",
            "07:58",
            3,
            [
                TrainPlan("R 5901", EAST, "08:00"),
                TrainPlan("R 5902", WEST, "08:05"),
            ],
            line="alentejo",
        ),
        LevelInfo(
            2,
            "The long section",
            "Between Alcáçovas and Alvito there are 23 km of single track and nowhere to cross.",
            "07:58",
            3,
            [
                TrainPlan("R 5901", EAST, "08:00"),
                TrainPlan("R 5902", WEST, "08:20"),
                TrainPlan("R 5903", EAST, "09:04"),
            ],
            line="alentejo",
        ),
        LevelInfo(
            3,
            "Intercidades to Beja",
            "The Intercidades (IC) from Lisbon is fast and only stops at the crossing stations.",
            "07:58",
            3,
            [
                TrainPlan("R 5902", WEST, "08:00"),
                TrainPlan("IC 591", EAST, "08:09"),
                TrainPlan("R 5903", EAST, "08:40"),
            ],
            line="alentejo",
        ),
        LevelInfo(
            4,
            "The grain train",
            "A long freight train (M) brings grain from Beja. It is slow: do not let it hold up the others.",
            "07:58",
            4,
            [
                TrainPlan("M 59101", WEST, "08:00"),
                TrainPlan("R 5901", EAST, "08:02"),
                TrainPlan("R 5904", WEST, "08:28"),
                TrainPlan("R 5903", EAST, "08:50"),
            ],
            line="alentejo",
        ),
        LevelInfo(
            5,
            "Market day in Beja",
            "Five trains on a market morning, crossing at every station.",
            "07:58",
            4,
            [
                TrainPlan("R 5901", EAST, "08:00"),
                TrainPlan("R 5902", WEST, "08:05"),
                TrainPlan("R 5904", WEST, "08:28"),
                TrainPlan("IC 591", EAST, "08:31"),
                TrainPlan("R 5903", EAST, "08:57"),
            ],
            line="alentejo",
        ),
        LevelInfo(
            6,
            "Harvest",
            "Two grain trains and the regionals. Find the freights a quiet place to wait.",
            "07:58",
            8,
            [
                TrainPlan("M 59101", WEST, "08:00"),
                TrainPlan("R 5901", EAST, "08:00"),
                TrainPlan("R 5902", WEST, "08:31"),
                TrainPlan("M 59102", EAST, "08:39"),
                TrainPlan("R 5903", EAST, "09:02"),
                TrainPlan("IC 592", WEST, "09:21"),
            ],
            line="alentejo",
        ),
        LevelInfo(
            7,
            "Summer heat",
            "Seven trains on a hot afternoon, two at a time.",
            "15:58",
            6,
            [
                TrainPlan("IC 593", EAST, "16:00"),
                TrainPlan("R 5912", WEST, "16:03"),
                TrainPlan("R 5913", EAST, "16:10"),
                TrainPlan("M 59104", WEST, "16:17"),
                TrainPlan("R 5915", EAST, "17:06"),
                TrainPlan("IC 594", WEST, "17:10"),
                TrainPlan("R 5916", WEST, "17:34"),
            ],
            line="alentejo",
        ),
        LevelInfo(
            8,
            "Feira de Beja",
            "Eight trains for the Beja fair. Only the best controllers keep the plain moving.",
            "15:58",
            8,
            [
                TrainPlan("IC 593", EAST, "16:00"),
                TrainPlan("R 5912", WEST, "16:00"),
                TrainPlan("M 59104", WEST, "16:20"),
                TrainPlan("R 5913", EAST, "16:29"),
                TrainPlan("R 5915", EAST, "16:59"),
                TrainPlan("IC 594", WEST, "17:01"),
                TrainPlan("M 59105", EAST, "17:30"),
                TrainPlan("R 5916", WEST, "17:39"),
            ],
            line="alentejo",
        ),
        LevelInfo(
            9,
            "Running late",
            "Level 7's trains, but some reach the map late, and never the same ones twice. Their own lateness is not counted, only the delay you add.",
            "15:58",
            6,
            [
                TrainPlan("IC 593", EAST, "16:00"),
                TrainPlan("R 5912", WEST, "16:03"),
                TrainPlan("R 5913", EAST, "16:10"),
                TrainPlan("M 59104", WEST, "16:17"),
                TrainPlan("R 5915", EAST, "17:06"),
                TrainPlan("IC 594", WEST, "17:10"),
                TrainPlan("R 5916", WEST, "17:34"),
            ],
            line="alentejo",
            random_delays=True,
        ),
    ],
}

LINE_NAMES = {key: make().name for key, make in LINES.items()}

# What the menu says about each line: a short description and the trains that run on it.
LINE_BLURBS = {
    "algarve": ("Faro to Tavira, along the Ria Formosa.", "Regional · Inter-Regional"),
    "oeste": ("Torres Vedras to Caldas da Rainha, north along the coast.", "Regional · Freight"),
    "douro": ("Peso da Régua to Ferradosa, along the river.", "Regional · Inter-Regional · Historic steam"),
    "alentejo": ("Casa Branca to Beja, across the plain.", "Regional · Intercidades · Freight"),
    "lisboa": ("Santa Apolónia to Oriente, four tracks by the Tejo.", "Alfa Pendular · Intercidades · Regional · Freight"),
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


NET_MARGIN = 30  # seconds of slack per section on the short Lisbon line
NET_PLACES = {
    "SAP": "Santa Apolónia",
    "CIN": {"R": "Sintra", "M": "Alcântara"},
    "N": {"AP": "Porto", "IC": "Coimbra", "R": "Azambuja", "M": "Bobadela"},
}


def _place(key: str, code: str) -> str:
    place = NET_PLACES[key]
    return place if isinstance(place, str) else place.get(code, "the north")


def make_net_timetable(net: Network, plan: TrainPlan) -> Train:
    """A timetable on the Linha do Norte. Fast trains (AP, IC) stop at Santa Apolónia and
    Oriente; regionals also at Braço de Prata; freight trains do not stop at all."""
    kind = plan.type
    code = kind.code
    d = plan.direction
    fast = code in ("AP", "IC")
    freight = kind.stops == "none"
    sa, bp, ori = net.station("SAP"), net.station("BPR"), net.station("ORI")
    frm = plan.frm or ("SAP" if d == EAST else "N")
    to = plan.to or ("N" if d == EAST else "SAP")
    terminus_order = ("P2", "P1", "P3", "P4") if d == EAST else ("P3", "P4", "P1", "P2")
    if plan.platform:
        terminus_order = (plan.platform,) + tuple(p for p in terminus_order if p != plan.platform)
    slow_first = ("A", "A2") if d == EAST else ("B", "B2")
    oriente = tuple(reversed(slow_first)) if fast else slow_first
    route: list[tuple[Station, tuple[str, ...]]] = []
    if d == EAST:
        if frm == "SAP":
            route.append((sa, terminus_order))
        if not fast:
            route.append((bp, ("A",)))
        route.append((ori, oriente))
        exit_tracks = oriente
        entry, pos = ("", sa.stop_position(EAST)) if frm == "SAP" else ("CN", net.tracks["CN"].start)
    else:
        route.append((ori, oriente))
        if not fast:
            route.append((bp, ("B",)))
        if to == "SAP":
            route.append((sa, terminus_order))
        exit_tracks = ("CS",) if to == "CIN" else ()
        entry, pos = ("B2" if fast else "B"), net.tracks["B"].end
    time = clock(plan.enters)
    enter_time = time - APPEAR_BEFORE if frm == "SAP" else time
    stops = []
    for i, (st, options) in enumerate(route):
        target = st.stop_position(d)
        if i == 0 and frm == "SAP":
            stops.append(Stop(st, options[0], round(time - 120), round(time), options=options))
            pos = target
            continue
        time += abs(target - pos) / kind.max_speed + NET_MARGIN
        arrive = time
        if not freight:
            time += kind.dwell_loop if st is ori else 30
        stops.append(Stop(st, options[0], round(arrive), round(time), passing=freight, options=options))
        pos = target
    train = Train(plan.name, d, enter_time, stops)
    train.origin = _place(frm, code)
    train.destination = _place(to, code)
    train.entry_track = entry
    train.exit_tracks = exit_tracks
    return train


def all_levels() -> list[LevelInfo]:
    return [info for levels in LEVELS.values() for info in levels]


def build_level(line_key: str, number: int, seed: int | None = None) -> tuple[LevelInfo, Simulation]:
    """The level's line and trains, ready to play. On a level with random delays, seed picks
    the delays (None: different every time it is played)."""
    info = LEVELS[line_key][number - 1]
    line = LINES[info.line]()
    if isinstance(line, Network):
        trains = [make_net_timetable(line, plan) for plan in info.trains]
        return info, NetSimulation(line, trains, clock(info.start), info.max_average_delay_min * 60)
    trains = [make_timetable(line, plan) for plan in info.trains]
    if info.random_delays:
        random_delays(trains, random.Random(seed))
    sim = Simulation(line, trains, clock(info.start), info.max_average_delay_min * 60)
    return info, sim


def random_delays(trains: list[Train], rng: random.Random) -> None:
    """Make about half of the trains reach the map 1 to 5 minutes late: always at least one,
    never more than two trains in three. The timetables stay as they were planned."""
    late = [t for t in trains if rng.random() < 0.5]
    if not late:
        late = [rng.choice(trains)]
    late = late[: max(1, len(trains) * 2 // 3)]
    for train in late:
        minutes = rng.randint(1, 5)
        train.enter_time += minutes * 60
        train.brought_delay = minutes * 60.0
        train.announced = False  # the driver says so only shortly before (Simulation.ANNOUNCE_BEFORE)


__all__ = ["LEVELS", "LINE_BLURBS", "LINE_NAMES", "all_levels", "LevelInfo", "TrainPlan", "build_level", "clock", "make_timetable", "WEST", "EAST"]
