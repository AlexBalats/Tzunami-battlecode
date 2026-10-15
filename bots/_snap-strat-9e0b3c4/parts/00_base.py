"""Base: trace lines, fuel helpers, error text (copied from bots/core/parts/00_base.py, trimmed).

Trace format (tools/plog.py): P|round|team|champ|tag|text. Never import traceback or json [measured A17, A29].
"""
import cambc
from cambc import game_map, vision

V = cambc.Vec2
Bitboard = cambc.Bitboard
DistanceField = cambc.DistanceField
Team = cambc.Team
fuel = cambc.fuel_remaining

TRACE = 1                   # 0: no trace lines at all (ladder submissions)
FAR = 65535                 # unreached in a DistanceField [sdk, measured]

_TAG = ["?|draft"]


def base_init():
    t = int(cambc.me().champion_name())        # ChampionType; the tag shows the draft id (ME['id'])
    _TAG[0] = f"{'AB'[cambc._bc.my_team()]}|{_TYPE_TO_DRAFT[t] if 0 <= t < len(_TYPE_TO_DRAFT) else t}"


def trace(tag, text):
    if TRACE:
        print(f"P|{cambc.round_number()}|{_TAG[0]}|{tag}|{text}", flush=True)


def err_text(error):
    """err:<line>:<type>:<msg>, line of the innermost frame (no traceback module)."""
    tb, line = error.__traceback__, 0
    while tb is not None:
        line, tb = tb.tb_lineno, tb.tb_next
    msg = str(error).replace(" ", "_").replace("|", "/")[:60]
    return f"err:{line}:{type(error).__name__}:{msg}"
