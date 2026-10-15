"""Entry. Draft: pick on every draft turn (Varg, Vesper Vale, Ryth, Vendetta, Marcella), run the model stages under
the fuel guard, spilling to later draft turns; encode to draft memory. Play: decode once, trace the summary on
round 1, then do nothing.

Draft memory: submit() raises once pick() was called in the same turn (engine error 18 on later turns; on turn 1
"Memory access requires the owning team's input boundary") [measured 14 Oct, bots/_bench]. So turn 1 picks,
then models and encodes; every later turn submits the bytes encoded so far (~30k fuel) immediately before its
pick, then continues the model. The champions read the last submit [measured]. Work done on the last draft turn
is never submitted, so every stage must finish before it.
"""

if cambc.is_draft():
    # ChampionDraft values [sdk]: RYTH 0, VESPER_VALE 1, VARG 9, MARCELLA 6, VENDETTA 2; others as backup.
    # Three-pick maps take the first three (Varg, Vesper, Ryth).
    PICKS = (9, 1, 0, 2, 6)
    BACKUP = PICKS + tuple(d for d in range(11) if d not in PICKS)
    LATE_RESERVE = 700_000      # later draft turns: the pick and submit are done first; keep room for encode

    def do_pick():
        try:
            ours = [int(p) for p in cambc.draft.current_draft(Team.ALLY)]
            p = next((d for d in BACKUP if d not in ours), PICKS[0])
            cambc.draft.pick(p)
            return p
        except Exception as e:
            trace("draft", "pick " + err_text(e))
            return None

    def draft_main():
        try:
            _TAG[0] = f"{'AB'[cambc._bc.my_team()]}|draft"
        except Exception:
            pass
        dm = None
        data = None
        turn = 0
        while True:
            turn += 1
            f_start = fuel()
            sub = "-"
            if data is not None:
                try:
                    cambc.draft_memory.submit(data)            # before the pick (see the docstring)
                    sub = str(len(data))
                except Exception as e:
                    sub = err_text(e)
            picked = do_pick()
            ran = touched = []
            try:
                if dm is None:
                    dm = DraftModel()
                    if turn == 1 and TRACE:
                        for line in bodies_table(5):
                            trace("bodies", line)
                ran, touched = dm.run(turn, DRAFT_RESERVE if turn == 1 else LATE_RESERVE)
                if ran or data is None:
                    f0 = fuel()
                    data = dm.encode()
                    trace("stage", f"encode turn={turn} fuel={f0 - fuel()} bytes={len(data)}")
            except Exception as e:
                trace("draft", err_text(e))
            trace("draft", f"turn={turn} start={f_start} picked={picked} submitted={sub} ran={','.join(ran)} worked={','.join(touched)} "
                           f"pending={','.join(dm.stages) if dm else '?'} used={f_start - fuel()} left={fuel()}")
            cambc.end_turn()

    draft_main()
else:
    OSC_N = 16                                    # alternating moves between two tiles before `osc` fires

    def turn(w):
        fa = fuel()
        s = sense(w)
        w.ph[0] = max(w.ph[0], fa - fuel())
        r = s.r
        flags = (w.attacked, w.capt, w.waiting)
        w.attacked = w.capt = w.waiting = w.moved = False
        if not s.alive:
            w.act[6] += 1
            if w.was_alive:
                trace("death", f"bag={w.bag_alive} pos={w.pos.x},{w.pos.y} hp={w.hp_alive:.0f} cur={w.cur[0]} "
                               f"{tname(w, w.cur[0], w.cur[1])} enemies={w.ne_alive}")
                w.was_alive = False
                op, tg = w.cur
                w.excl[w.cur] = r + DEATH_EXCL            # no re-entry where I just died
                if op in ("kill", "hold"):
                    w.kh_until = r + DEATH_EXCL
                if op == "farm" and tg in w.G and w.G[tg].mi < 31:
                    try:                                  # team marker: avoid this group (bytes 6-7)
                        cambc.shared_memory[6] = w.G[tg].mi + 1
                        cambc.shared_memory[7] = (r // 8) & 255
                    except Exception:
                        pass
                w.cur, w.status = ("dead", None), "done"
            if s.gold >= 30:
                buy_all(w, s)                     # dead champions may shop [rules]
            broadcast(w, s, 7)
            return
        if not w.was_alive:
            w.was_alive = True
            w.status = "done"
            w.build_fme(s.pos)
        elif s.pos.chebyshev_distance(w.fme_root) > FME_MOVE:
            w.build_fme(s.pos)                    # also after a recall (the jump is > 6)
        # stuck guard: same tile, last turn neither capturing, channelling, attacking nor dead
        exempt = flags[0] or flags[1] or s.recalling or s.submitting
        if s.pos == w.pos and not exempt:
            w.same += 1
            w.stay += 1
        else:
            w.same = w.stay = 0
        if w.stay == 30:
            trace("stay", f"{s.pos.x},{s.pos.y} {w.cur[0]} {tname(w, w.cur[0], w.cur[1])} wait={int(flags[2])}")
        # oscillation: back and forth between the same two tiles (moves that return to the previous distinct tile)
        if exempt:
            w.osc = 0
        elif s.pos != w.pos:
            w.osc = w.osc + 1 if s.pos == w.p2 else 0
            w.p2 = w.pos
        osc_hit = False
        if w.osc >= OSC_N and not w.osc_fired:
            w.osc_fired = osc_hit = True
            ex = ",".join(f"{k[0]}:{tname(w, k[0], k[1])}" for k, v in w.excl.items() if v > r)
            trace("osc", f"{s.pos.x},{s.pos.y}<->{w.p2.x},{w.p2.y} {w.cur[0]} {tname(w, w.cur[0], w.cur[1])} "
                         f"wait={int(flags[2])} same={w.same} excl={ex or '-'} pair_until={w.pair_until}")
        elif w.osc == 0:
            w.osc_fired = False
        w.pos, w.bag_alive, w.hp_alive = s.pos, s.bag, s.hp
        w.ne_alive = len(s.enemies)
        if w.same >= 20 and w.status == "going":
            trace("exec", f"{w.cur[0]} {tname(w, w.cur[0], w.cur[1])} failed stuck")
            w.excl[w.cur] = r + EXCL
            if flags[2]:
                w.pair_until = r + 2 * EXCL       # no partner came: no un-partnered pair takes for a while
            w.status = "failed"
            w.same = 0
        if w.status == "going" and r > w.deadline and not (s.recalling or s.submitting):
            trace("exec", f"{w.cur[0]} {tname(w, w.cur[0], w.cur[1])} failed timeout")
            w.excl[w.cur] = r + EXCL
            w.status = "failed"
        for _k in range(2):
            if not (s.recalling or s.submitting) and fuel() > FUEL_FLOOR and r > w.seed_until:
                fb = fuel()
                choose(w, s)
                w.ph[1] = max(w.ph[1], fb - fuel())
            op, tg = w.cur
            fb = fuel()
            fn = EXEC.get(op)
            if fn is None:
                break
            st = fn(w, s, tg)
            w.ph[2] = max(w.ph[2], fb - fuel())
            if st == "going":
                w.status = st
                break
            trace("exec", f"{op} {tname(w, op, tg)} {st}")
            if st == "failed":
                w.excl[w.cur] = r + EXCL
            w.status = st
            if fuel() < 900_000:
                break
        broadcast(w, s, CODE.get(w.cur[0], 0) if w.cur[0] in CODE else 0)
        k = 3 if s.recalling or s.submitting else 1 if w.attacked else 2 if w.capt else 4 if w.waiting else             0 if w.moved else 5
        w.act[k] += 1
        w.idle = w.idle + 1 if k == 5 else 0
        if w.idle == 4 and TRACE:
            op, tg = w.cur
            x = ""
            if op == "farm" and tg in w.G:
                o = w.G[tg]
                x = (f"st={o.st} live={len(s.live.get(tg, ()))} vis={int(visible(w, s, o))} "
                     f"d={min(t.chebyshev_distance(s.pos) for t in o.tiles)} walk={w.walk_to(f'g{tg}', s.pos)} "
                     f"canmove={int(s.can_move)}")
            trace("idle", f"{op} {tname(w, op, tg)} {x} step={getattr(w, 'last_step', '-')} "
                          f"occ={vision.champion_tiles().count()}")
            w.last_step = "-"
        if w.F_home is None and fuel() > 1_200_000:
            w.home_field()

    def play_main():
        base_init()
        w = WORLD
        w.cur, w.status, w.excl, w.sent, w.started, w.deadline = ("idle", None), "done", {}, -1, 0, 0
        w.claims, w.was_alive, w.same, w.stay, w.seed_until = {}, True, 0, 0, 0
        w.attacked = w.capt = w.waiting = False
        w.bag_alive, w.hp_alive, w.ne_alive, w.kd, w.kn, w.arrived = 0, 0, 0, 99, 0, None
        w.lastbag = w.lastgold = 0
        w.ph = [0] * 3
        w.idle = 0
        w.pair_until = 0
        w.osc, w.osc_fired, w.p2 = 0, False, None
        w.kh_until = 0
        w.score = (0, 0)
        w.act = [0] * 7                                   # mv atk cap chan wait idle dead (turns per tick)
        w.moved = False
        errs = set()
        fu = []
        f0 = fuel()
        trace("env", f"round={cambc.round_number()} fuel_at_start={f0} turn_budget={cambc.constants.FUEL_PER_TURN if hasattr(cambc.constants, 'FUEL_PER_TURN') else '?'}")
        try:
            me_init()                                     # 20_champs: ME facts, once (traces tag me)
            w.boot()
            w.pos = w.fme_root
            seed = opening_seed(w)
            if seed is not None:
                s = sense(w)
                w.set_cur(("farm", seed), s.r, s)
                w.seed_until = s.r + 2                    # everyone writes the seed before anyone re-prices
                trace("choice", f"farm {tname(w, 'farm', seed)} seed slot={w.slot}")
                broadcast(w, s, 1)
        except Exception as e:
            trace("err", "boot " + err_text(e))
        trace("boot", f"round1 fuel={f0 - fuel()} left={fuel()}")
        cambc.end_turn()
        while True:
            f0 = fuel()
            try:
                turn(w)
            except Exception as e:
                t = err_text(e)
                if t not in errs:
                    errs.add(t)
                    trace("err", t)
            used = f0 - fuel()
            fu.append(used)
            r = cambc.round_number()
            if r % 50 == 0:
                try:
                    me = cambc.me()
                    alive = me.is_alive()
                    trace("tick", f"{w.cur[0]} hp={me.health() if alive else 0:.0f} bag={me.gem_count() if alive else 0} "
                                  f"gold={me.gold_count()} fuel={used} fmax={max(fu)} fmed={sorted(fu)[len(fu) // 2]} "
                                  f"pos={w.pos.x},{w.pos.y} act={'/'.join(map(str, w.act))} ph={w.ph} "
                                  f"score={w.score[0]}-{w.score[1]}")
                except Exception as e:
                    trace("err", "tick " + err_text(e))
                fu = []
                w.ph = [0] * 3
                w.act = [0] * 7
            cambc.end_turn()

    play_main()
