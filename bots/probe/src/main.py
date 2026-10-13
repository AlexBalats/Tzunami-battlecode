"""Probe bot: measures the open entries in docs/ASSUMPTIONS.md. Not a competitive bot.

Imports cost a lot of fuel (measured 13 Oct), so the draft instance imports only draft.py.
"""
import cambc

if cambc.is_draft():
    print(f"P|-1|?|draft|boot|{{\"fuel\": {cambc.fuel_remaining()}}}", flush=True)
    _t = 0
    while True:
        _t += 1
        try:
            try:
                _rn = cambc.round_number()
            except Exception as _e:
                _rn = "ERR " + str(_e)
            print(f"P|-1|?|draft|inline_turn|t={_t} fuel={cambc.fuel_remaining()} round={_rn} size={cambc.draft.team_size()}", flush=True)
            if _t == 1:
                # A19: what can the draft bot read about the map? Inline: importing our own modules kills the draft instance.
                from cambc import game_map as _gm
                for _name, _f in (
                    ("width", lambda: _gm.width()),
                    ("symmetry", lambda: int(_gm.symmetry())),
                    ("walls", lambda: _gm.walls().count()),
                    ("altars", lambda: _gm.altars().count()),
                    ("spawn_ally", lambda: _gm.spawn_region(cambc.Team.ALLY).count()),
                    ("camp_groups", lambda: len(_gm.camp_groups())),
                    ("raw_num_camp_groups", lambda: cambc._bc.map_num_camp_groups()),
                    ("raw_map_camp_groups", lambda: repr(cambc._bc.map_camp_groups())[:300]),
                    ("bc_names", lambda: [n for n in dir(cambc._bc) if "map" in n or "camp" in n]),
                ):
                    _f0 = cambc.fuel_remaining()
                    try:
                        _v = _f()
                    except Exception as _e:
                        _v = "ERR " + type(_e).__name__ + " " + str(_e)
                    print(f"P|-1|?|draft|a19|{_name}={_v!r} fuel={_f0 - cambc.fuel_remaining()}", flush=True)
            # A27: does importing a module not named "draft" work in the draft instance?
            _f0 = cambc.fuel_remaining()
            try:
                import plan as _plan
                _picks = _plan.PICKS_A if cambc._bc.my_team() == 0 else _plan.PICKS_B
                print(f"P|-1|?|draft|a27_import_plan|ok fuel={_f0 - cambc.fuel_remaining()} picks={_picks}", flush=True)
            except Exception as _e:
                _picks = (0, 5, 4, 8, 1)
                print(f"P|-1|?|draft|a27_import_plan|ERR {_e!r}", flush=True)
            _ally = [int(p) for p in cambc.draft.current_draft(cambc.Team.ALLY)]
            cambc.draft_memory.submit(bytes([7, _t]))
            for _p in _picks:
                if _p not in _ally:
                    cambc.draft.pick(_p)
                    break
            print(f"P|-1|?|draft|inline_picked|t={_t} fuel={cambc.fuel_remaining()}", flush=True)
        except Exception as error:
            print(f"P|-1|?|draft|error|{error!r}", flush=True)
        cambc.end_turn()
else:
    f0 = cambc.fuel_remaining()
    import probe
    from log import log
    log("boot", fuel_before_imports=f0, fuel_after_imports=cambc.fuel_remaining())
    import plan
    while True:
        r0, f0 = cambc.round_number(), cambc.fuel_remaining()
        try:
            probe.play_turn()
        except Exception as error:
            # Never import traceback: its first use froze every champion for ~136 rounds (ASSUMPTIONS A17).
            tb, where = error.__traceback__, []
            while tb is not None:
                where.append(f"{tb.tb_frame.f_code.co_name}:{tb.tb_lineno}")
                tb = tb.tb_next
            log("error", kind=type(error).__name__, msg=str(error), where=where[-4:], fuel_turn=f0 - cambc.fuel_remaining())
        if getattr(plan, "TICK", False):
            log("tick", r0=r0, f0=f0, f1=cambc.fuel_remaining())
        cambc.end_turn()
