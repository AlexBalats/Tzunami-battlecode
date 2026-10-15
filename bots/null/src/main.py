"""Null bot: drafts, then does nothing. Opponent for isolated scenarios, and the startup floor:
its boot line says the earliest round a Python champion can act (docs/HANDOFF.md, A29)."""
import cambc

if cambc.is_draft():
    PREFS = (0, 6, 9, 2, 1, 4)
    while True:
        try:
            ours = [int(p) for p in cambc.draft.current_draft(cambc.Team.ALLY)]
            for p in PREFS:
                if p not in ours:
                    cambc.draft.pick(p)
                    break
        except Exception:
            pass
        cambc.end_turn()
else:
    me = cambc.me()
    print(f"P|{cambc.round_number()}|{'AB'[cambc._bc.my_team()]}|{int(me.champion_name())}|boot|"
          f"f={cambc.fuel_remaining()}", flush=True)
    while True:
        cambc.end_turn()
