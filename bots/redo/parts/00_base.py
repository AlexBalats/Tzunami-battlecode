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
    global KILL_G
    KILL_G = cambc.constants.KILL_GOLD            # X4 (50_prices): read at boot, never at preload
    t = int(cambc.me().champion_name())        # ChampionType; the tag shows the draft id (ME['id'])
    _TAG[0] = f"{'AB'[cambc._bc.my_team()]}|{_TYPE_TO_DRAFT[t] if 0 <= t < len(_TYPE_TO_DRAFT) else t}"


def trace(tag, text):
    if TRACE:
        print(f"P|{cambc.round_number()}|{_TAG[0]}|{tag}|{text}", flush=True)


def err_text(error):
    """err:<lines>:<type>:<msg>, the lines of the 3 innermost frames, outer>inner (no traceback module)."""
    tb, ls = error.__traceback__, []
    while tb is not None:
        ls.append(str(tb.tb_lineno))
        tb = tb.tb_next
    line = ">".join(ls[-3:])
    msg = str(error).replace(" ", "_").replace("|", "/")[:60]
    return f"err:{line}:{type(error).__name__}:{msg}"
