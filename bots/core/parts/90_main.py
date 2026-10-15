"""Entry: `if cambc.is_draft(): draft_main() else: play_main()` (docs/design/CORE.md).

Draft: pick FIRST on every draft turn (a missed pick is random [rules]); nothing is written to draft memory
(draft_memory.submit() raises Error 18 once pick() was called in the same turn [measured, tzu 40_draft]).
Play, per round: fuel start -> w.snapshot -> team_read -> play() (50_rules; kit_init once) -> team_write ->
w.work() background fields under the fuel guard -> one trace line
    P|r|T|id|t|<tag> x,y hp=.. bag=.. gold=.. fuel=.. [bg=jobs/fuel]
A turn that raises traces err:<line>:<type>:<msg> as its tag and still writes the team bytes (heartbeat).
"""

if cambc.is_draft():
    # ChampionDraft values [sdk]: RYTH 0, VENDETTA 2, VARG 9, MARCELLA 6, STELLAR 4; then any other as backup,
    # so the pick is never None (pick(None) raises). The enemy holding a champion does not block it [rules].
    PICKS = (0, 2, 9, 6, 4)
    BACKUP = PICKS + tuple(d for d in range(11) if d not in PICKS)

    def draft_main():
        try:
            _TAG[0] = f"{'AB'[cambc._bc.my_team()]}|draft"
        except Exception:
            pass
        while True:
            try:
                ours = [int(p) for p in cambc.draft.current_draft(Team.ALLY)]
                p = next((d for d in BACKUP if d not in ours), PICKS[0])
                cambc.draft.pick(p)                    # FIRST, before anything else this turn
                trace("draft", f"picked={p} ours={ours}")
            except Exception as e:
                trace("draft", err_text(e))
            cambc.end_turn()

    draft_main()
else:
    def play_main():
        base_init()
        trace("boot", f"f={fuel()} type={int(cambc.me().champion_name())}")
        w = nav = None
        kit_done = False
        claim = rally = None           # last claim (also the snapshot's target group) and this turn's rally
        while True:
            FUEL.start()
            rnd = cambc.round_number()
            tag, rally, jobs, bgf = "boot", None, 0, 0
            try:
                if w is None:
                    w = World()
                    nav = w.nav = Nav(w)
                s = w.snapshot(rnd, claim)
                team = team_read(w, s)
                if not w.ready and w.setup():
                    s = w.snapshot(rnd, claim)                     # camp table ready: near groups now known
                    trace("world", f"groups={len(w.groups)} altars={len(w.altar_pos)} map={w.W}x{w.H} "
                                   f"bank=a{w.bank_altar} contested={int(w.contested)} fuel={FUEL.used()}")
                if w.ready:
                    if not kit_done:
                        kit_done = True
                        kit_init(w, s)
                    tag, claim, rally = play(w, s, team)
            except Exception as e:
                tag = err_text(e)
            try:
                if w is not None and w.snap is not None:
                    team_write(w, w.snap, claim, rally)            # every turn, crashed ones too
            except Exception as e:
                tag += " w" + err_text(e)
            try:
                if w is not None and w.ready:
                    jobs, bgf = w.work()                            # background fields under the reserve
            except Exception as e:
                tag += " b" + err_text(e)
            try:
                s = w.snap if w is not None else None
                if s is not None:
                    p = nav.dest if nav.moved_round == rnd else s.pos
                    bg = f" bg={jobs}/{bgf}" if jobs else ""
                    cl = ",".join(f"{k}:{v}" for k, v in sorted(team.claims.items())) if team else "-"
                    trace("t", f"{tag} {p.x},{p.y} hp={int(s.hp)} bag={s.bag} gold={s.gold} "
                               f"fuel={FUEL.used()} cl={cl}{bg}")
                else:
                    trace("t", f"{tag} fuel={FUEL.used()}")
            except Exception as e:
                trace("t", f"{err_text(e)} fuel={FUEL.used()}")
            cambc.end_turn()

    play_main()
