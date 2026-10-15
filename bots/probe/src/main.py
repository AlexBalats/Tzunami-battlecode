"""Probe bot: measures the open entries in docs/ASSUMPTIONS.md. Not a competitive bot.

Imports cost a lot of fuel (measured 13 Oct), so the draft instance imports only draft.py.
"""
import cambc

if cambc.is_draft():
    print(f"P|-1|?|draft|boot|{{\"fuel\": {cambc.fuel_remaining()}}}", flush=True)
    _t = 0
    while True:
        _t += 1
        _fuel_start = cambc.fuel_remaining()   # draft-turns measurement: fuel at the top of every draft turn
        _picked = None
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
                # Group handles and order as the draft sees them (compare with the champions' `gids` lines).
                try:
                    _gs = _gm.camp_groups()
                    print(f'P|-1|?|draft|gids|{{"n":{len(_gs)},"gids":{[int(g) for g in _gs]},'
                          f'"camp0":{[int(g.camps()[0]) for g in _gs]},'
                          f'"spawn0":{[[g.camps()[0].spawn_position().x, g.camps()[0].spawn_position().y] for g in _gs[:3]]}}}', flush=True)
                except Exception as _e:
                    print(f"P|-1|?|draft|gids|ERR {_e!r}", flush=True)
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
                    _picked = _p
                    break
            print(f"P|-1|?|draft|inline_picked|t={_t} fuel={cambc.fuel_remaining()}", flush=True)
        except Exception as error:
            print(f"P|-1|?|draft|error|{error!r}", flush=True)
        # Draft-turns measurement: one line per draft turn (turn count, fuel, team size, picks so far).
        try:
            _rn = cambc.round_number()
        except Exception:
            _rn = -1
        try:
            _n_ally = len(cambc.draft.current_draft(cambc.Team.ALLY))
            _n_enemy = len(cambc.draft.current_draft(cambc.Team.ENEMY))
        except Exception as _e:
            _n_ally = _n_enemy = "ERR " + str(_e)
        try:
            _team = "AB"[cambc._bc.my_team()]
        except Exception:
            _team = "?"
        print(f'P|{_rn}|{_team}|draft|dturn|{{"turn":{_t},"fuel_start":{_fuel_start},"fuel_end":{cambc.fuel_remaining()},'
              f'"picked":{_picked if _picked is not None else "null"},"size":{cambc.draft.team_size()},'
              f'"n_ally":{_n_ally!r},"n_enemy":{_n_enemy!r}}}', flush=True)
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
