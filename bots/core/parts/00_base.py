"""Base: constants, trace lines, fuel, error capture (docs/design/CORE.md).

Trace format (tools/plog.py): P|round|team|champ|tag|text, team A or B, champ = int(ChampionType).
Never import traceback (froze champions ~136 rounds [measured A17]) or json (~35 rounds [measured A29]).
"""
import cambc
from cambc import game_map, vision

V = cambc.Vec2
Bitboard = cambc.Bitboard
DistanceField = cambc.DistanceField
Team = cambc.Team
fuel = cambc.fuel_remaining

TRACE = 1                   # 0: no trace lines at all (ladder submissions)
FUEL_BUDGET = 2_500_000     # per play turn, Python [measured A16]; the first play turn has ~4.6M [measured]
RESERVE = 400_000           # fuel never spent on background work (fields) [provisional, tzu's value]
FAR = 65535                 # "unreachable" in every distance we hand out (field max_distance) [sdk]
DIRS = (V.NORTH, V.NORTH_EAST, V.EAST, V.SOUTH_EAST, V.SOUTH, V.SOUTH_WEST, V.WEST, V.NORTH_WEST)

# ChampionState bits [sdk __init__.py]: read me.state() once per turn and test bits.
ST_ALIVE = 1
ST_RECALLING = 2
ST_SUBMITTING = 4
ST_CAN_MOVE = 8
ST_CAN_ATTACK = 16

_TAG = ["?|draft"]          # "team|champ", set by base_init() on the first play turn


def base_init():
    """Team letter and champion id, once. cambc._bc.my_team() is the absolute team (0 = A) [sdk]."""
    _TAG[0] = f"{'AB'[cambc._bc.my_team()]}|{int(cambc.me().champion_name())}"


def trace(tag, text):
    if TRACE:
        print(f"P|{cambc.round_number()}|{_TAG[0]}|{tag}|{text}", flush=True)


def err_text(error):
    """err:<line>:<type>:<msg>, line of the innermost frame, walked from __traceback__ (no traceback module)."""
    tb, line = error.__traceback__, 0
    while tb is not None:
        line, tb = tb.tb_lineno, tb.tb_next
    msg = str(error).replace(" ", "_").replace("|", "/")[:60]
    return f"err:{line}:{type(error).__name__}:{msg}"


class Fuel:
    """Per-turn fuel accounting: start() at the top of the turn, used() any time after."""
    __slots__ = ("f0",)

    def __init__(self):
        self.f0 = 0

    def start(self):
        self.f0 = fuel()

    def used(self):
        return self.f0 - fuel()


FUEL = Fuel()


def spent(f1, r1):
    """Fuel spent since fuel() read f1 in round r1, also across a turn boundary (an overrun: the turn went on in
    the next round, which started at FUEL_BUDGET)."""
    f = fuel()
    return f1 - f if cambc.round_number() == r1 else f1 + FUEL_BUDGET - f


def cheb(a, b):
    return max(abs(a.x - b.x), abs(a.y - b.y))
