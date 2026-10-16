"""tzunami-lite (v2) entry point: only the loop lives here.

On cambc 2.1.6 every other module is imported before the game starts and main.py runs when it
starts [sdk, measured A48]; so modules make no game calls at import time.
"""
import cambc

import config

if cambc.is_draft():
    import plan
    while True:
        try:
            plan.draft_turn()
        except Exception as error:
            print(f"T|draft|error|{type(error).__name__}: {error}", flush=True)
        cambc.end_turn()
else:
    import core
    while True:
        try:
            core.turn()
        except Exception as error:
            # Never import traceback: its first use froze every champion for ~136 rounds (A17).
            tb, where = error.__traceback__, []
            while tb is not None:
                where.append(f"{tb.tb_frame.f_code.co_name}:{tb.tb_lineno}")
                tb = tb.tb_next
            print(f"T|{cambc.round_number()}|error|{type(error).__name__}: {error} @ {where[-3:]}", flush=True)
        cambc.end_turn()
