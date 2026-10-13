"""tzunami444 (v1): draft inline, then bot.play_turn() every round.

The draft branches before importing bot.py, and the draft code stays here: a module named
`draft` kills the draft instance (docs/ARCHITECTURE.md, A27).
"""
import cambc

LOG = True      # one line per error; stdout lands in the replay bundle (finished games only)

if cambc.is_draft():
    import config as _C
    while True:
        try:
            _ours = [int(p) for p in cambc.draft.current_draft(cambc.Team.ALLY)]
            _choice = next((int(p) for p in _C.PICKS if int(p) not in _ours), None)
            if _choice is None:
                _choice = next(p for p in range(11) if p not in _ours)
            cambc.draft.pick(_choice)
        except Exception as error:
            print(f"T|draft|error|{type(error).__name__}: {error}", flush=True)
        cambc.end_turn()
else:
    # Plain imports: the engine compiles our source itself. No precompiled bytecode: the official
    # guide says "do not put generated binaries in your submission" (docs/GETTING_STARTED.md).
    # Compiling costs ~55k fuel per line of code, so booting takes ~56 rounds [measured A29].
    _r0, _f0 = cambc.round_number(), cambc.fuel_remaining()
    import config
    import bot
    if config.TRACE:
        print(f"T|boot|r{_r0}->{cambc.round_number()} fuel {_f0}->{cambc.fuel_remaining()}", flush=True)
    while True:
        try:
            bot.play_turn()
        except Exception as error:
            # Never import traceback: its first use froze every champion for ~136 rounds (A17).
            if LOG:
                tb, where = error.__traceback__, []
                while tb is not None:
                    where.append(f"{tb.tb_frame.f_code.co_name}:{tb.tb_lineno}")
                    tb = tb.tb_next
                print(f"T|{cambc.round_number()}|error|{type(error).__name__}: {error} @ {where[-3:]}", flush=True)
        cambc.end_turn()
