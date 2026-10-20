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
    PICKS = ROSTER                  # [B6] COMP (30_world)
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
                    cambc.draft_memory.submit(data)    # before the pick (see the docstring)
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
        if TRACE:
            w.reset_check()                       # verification of the attack reset (30_world reset_attack)
        r = s.r
        flags = (w.attacked, w.capt, w.waiting)
        w.attacked = w.capt = w.waiting = w.moved = False
        if flags[0]:
            w.hit = True
        if not s.alive:
            w.act[6] += 1
            if w.was_alive:
                trace("death", f"bag={w.bag_alive} pos={w.pos.x},{w.pos.y} hp={w.hp_alive:.0f} cur={w.cur[0]} "
                               f"{tname(w, w.cur[0], w.cur[1])} enemies={w.ne_alive}")
                w.was_alive = False
                op, tg = w.cur
                w.excl[w.cur] = r + DEATH_EXCL            # no re-entry where I just died
                if op in ("kill", "hold", "hunt"):
                    w.kh_until = r + DEATH_EXCL
                w.dead_mi = w.G[tg].mi if op == "farm" and tg in w.G else 31   # broadcast: dead byte's target
                w.cur, w.status = ("dead", None), "done"
            if s.gold >= 30:
                buy_all(w, s)                     # dead champions may shop [rules]
            broadcast(w, s, 7)
            return
        if ROLE_BUILD and s.spawn and s.gold >= 30:
            buy_all(w, s)                         # [K2] on the spawn tiles for any reason: buy now
        if not w.spike:
            vs = 0                                # [user decision 15 Oct afternoon] spike shift: an ally Vesper's Strength
            for c, _p, _hp, st in s.allies:
                try:
                    if _TYPE_TO_DRAFT[int(c.champion_name())] == VESPER_ID and st > vs:
                        vs = st
                except Exception:
                    pass
            if vs >= SPIKE_STR or r >= SPIKE_ROUND or VESPER_ID not in getattr(w, "roster", ROSTER):     # [B6] no Vesper: gold for all
                w.spike = True
                trace("phase", f"spike r={r} vstr={vs:.0f}")
                apply_phase(w)
        if r - w.shards_r >= 20:
            w.shards_r = r
            fs = fuel()
            w.shards = shards_owned(w.me)
            fs -= fuel()
            apply_phase(w)                          # 20_champs: ME["prof"] = base row + the current phase's overrides
            mit_refresh(w)                          # [K3 ROLE_PRICE] Jungle / shield mitigation for my_dmg
            if w.shards_fuel is None or w.shards_fuel < 2:
                if w.shards_fuel is None:           # the first read also builds the weight table
                    trace("shards", f"n={w.shards} fuel={fs} (first read: item_count + weight table)")
                    w.shards_fuel = 0
                else:
                    f1 = fuel()
                    n = w.me.item_count()
                    f1 -= fuel()
                    trace("shards", f"n={w.shards} fuel={fs} (read) item_count_alone={f1} len={len(n)}")
                    w.shards_fuel += 1
        if not w.was_alive:
            w.was_alive = True
            w.status = "done"
            w.build_fme(s.pos)
        elif s.pos.chebyshev_distance(w.fme_root) > FME_MOVE:
            w.build_fme(s.pos)                    # also after a recall (the jump is > 6)
        # stuck guard: same tile, last turn neither capturing, channelling, attacking, waiting (T5/T6) nor dead
        exempt = flags[0] or flags[1] or s.recalling or s.submitting
        if s.pos == w.pos and not exempt and not flags[2]:
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
        if w.osc >= OSC_N and not w.osc_fired:
            w.osc_fired = True
            ex = ",".join(f"{k[0]}:{tname(w, k[0], k[1])}" for k, v in w.excl.items() if v > r)
            trace("osc", f"{s.pos.x},{s.pos.y}<->{w.p2.x},{w.p2.y} {w.cur[0]} {tname(w, w.cur[0], w.cur[1])} "
                         f"wait={int(flags[2])} same={w.same} excl={ex or '-'}")
        elif w.osc == 0:
            w.osc_fired = False
        if w.tflip is not None:                   # [user decision 15 Oct afternoon] target flips count as oscillation
            trace("osc", f"target g{w.tflip[0]}<->g{w.tflip[1]} flips={w.flips} {w.cur[0]} {tname(w, w.cur[0], w.cur[1])}")
            w.tflip = None
        if KIT_ON and s.st & 0x800 and not (s.recalling or s.submitting):
            w.kit_shield(s, s.hp < (w.hp_alive or 0))     # [K1] Varg's shield first: walking allows it [rules]
        w.pos, w.bag_alive, w.hp_alive = s.pos, s.bag, s.hp
        w.ne_alive = len(s.enemies)
        if w.same >= 20 and w.status == "going":
            trace("exec", f"{w.cur[0]} {tname(w, w.cur[0], w.cur[1])} failed stuck")
            w.excl[w.cur] = r + EXCL
            w.status = "failed"
            w.same = 0
        if SUNK_ON and w.status == "going":
            # [IMPROVEMENTS 2] stall guard: w.prog has not risen for PROG_STALL rounds -> failed like `stuck`. Exempt:
            # attacking / capturing / waiting last turn, recalling, channelling, and kill / shop / heal / fall / hold
            # (own chase and timeout rules)
            prog_update(w, s, flags[0])
            seek = w.waited != w.pw
            w.pw = w.waited
            if exempt or flags[2] or seek or w.cur[0] not in ("farm", "bank", "ward", "join", "hunt"):
                w.pstall = 0
            elif w.pstall >= PROG_STALL:
                trace("exec", f"{w.cur[0]} {tname(w, w.cur[0], w.cur[1])} failed stall prog={w.prog:.2f}")
                w.excl[w.cur] = r + EXCL
                w.status = "failed"
                w.pstall = 0
        if w.status == "going" and r > w.deadline and not (s.recalling or s.submitting):
            trace("exec", f"{w.cur[0]} {tname(w, w.cur[0], w.cur[1])} failed timeout")
            if w.cur[0] == "kill":
                kban(w, w.cur[1], r)                    # a timed-out kill: finishers excluded too (40_prices KILL); backoff
                w.excl[w.cur] = w.kfail[w.cur[1]]
            else:
                w.excl[w.cur] = r + EXCL
            w.status = "failed"
        for _k in range(2):
            if not (s.recalling or s.submitting) and fuel() > FUEL_FLOOR:
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
                w.excl[w.cur] = max(w.excl.get(w.cur, 0), w.kfail.get(tg, 0) if op == "kill" else r + EXCL)   # keeps a longer one
            w.status = st
            if fuel() < 900_000:
                break
        if SCAN_WARD and not (s.recalling or s.submitting) and fuel() > SCAN_FUEL:
            fb = fuel()
            scan_ward(w, s)                       # [B1] after my move: the ward goes 2 ahead onto an unseen bush
            w.ph[2] = max(w.ph[2], fb - fuel())
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
        w.claims, w.was_alive, w.same, w.stay = {}, True, 0, 0
        w.prog, w.pbest, w.pstall, w.pw, w.waited = 0.0, 0.0, 0, 0, 0     # [IMPROVEMENTS 2] sunk progress (50_exec prog_update)
        w.lowcn, w.ncrew, w.dead_mi, w.gathered, w.gmates, w.contest = {}, 1, 31, False, 0, 0                         # [T3] lower-slot claims per group (40_prices choose); crew of my take
        w.phase = None                                    # 20_champs (phase index, spike) last applied
        w.spike = False                                   # spike shift on (20_champs SPIKE_*)
        w.attacked = w.capt = w.waiting = False
        w.bag_alive, w.hp_alive, w.ne_alive, w.kd, w.kn, w.arrived = 0, 0, 0, 99, 0, None
        w.lastbag = w.lastgold = 0
        w.ph = [0] * 3
        w.idle = 0
        w.osc, w.osc_fired, w.p2 = 0, False, None
        w.fh, w.flips, w.tflip = [], 0, None              # farm target history (50_exec set_cur flip lock), flips, last flip
        w.peekn, w.peeked = 0, False                      # dead-camp pickup (50_exec exec_farm)
        w.kh_until = 0
        w.hit = False
        w.hvis, w.roam, w.big3 = {}, 0.0, -999                                       # hunt patrol: altar (or 100 + group) -> round I reached it
        w.kfail, w.kfn = {}, {}                           # enemy handle -> round a chased-out kill stays excluded to; consecutive fails
        w.score = (0, 0)
        w.post = None                                     # posture column last traced
        w.ward_done, w.ward_fails = False, {}
        w.bush, w.sw_pos, w.swn, w.sw_seen = None, None, 0, {}   # [SCAN_WARD] bush tiles, my ward, placements, enemy -> round seen
        w.twin = False                                    # [C6] Issac: shares Cassi's slot (set after me_init)
        w.wtiles, w.ward_pending, w.ward_tries = [], set(), {}
        w.shards, w.shards_r, w.shards_fuel = 0, -99, None                     # shards owned (emblems count their shards), read every 20
        w.act = [0] * 7                                   # mv atk cap chan wait idle dead (turns per tick)
        w.moved = False
        errs = set()
        fu = []
        f0 = fuel()
        trace("env", f"round={cambc.round_number()} fuel_at_start={f0} turn_budget={cambc.constants.FUEL_PER_TURN if hasattr(cambc.constants, 'FUEL_PER_TURN') else '?'}")
        try:
            me_init()                                     # 20_champs: ME facts, once (traces tag me)
            w.twin = ME.get("type") == 4                  # [C6] ChampionType ISSAC [sdk]: only with Cassi & Issac drafted
            apply_phase(w)
            w.boot()
            w.pos = w.fme_root
            ward_init(w)                                  # pending ward tiles, placed on the way (no round-1 rush)
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
            r = cambc.round_number()
            fu.append(used)
            if r % 50 == 0:
                try:
                    me = cambc.me()
                    alive = me.is_alive()
                    trace("tick", f"{w.cur[0]} hp={me.health() if alive else 0:.0f} bag={me.gem_count() if alive else 0} "
                                  f"gold={me.gold_count()} fuel={used} fmax={max(fu)} fmed={sorted(fu)[len(fu) // 2]} "
                                  f"pos={w.pos.x},{w.pos.y} act={'/'.join(map(str, w.act))} ph={w.ph} "
                                  f"score={w.score[0]}-{w.score[1]} shards={w.shards} "
                                  f"str={me.strength() if alive else 0:.0f}" + (f" sw={w.swn}" if SCAN_WARD else ""))
                except Exception as e:
                    trace("err", "tick " + err_text(e))
                fu = []
                w.ph = [0] * 3
                w.act = [0] * 7
            cambc.end_turn()

    play_main()
