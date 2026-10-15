"""Entry. The draft branch comes first; everything play-only is defined inside the `else` so the draft bot
never pays for it. The play loop IS the per-turn skeleton of INVARIANTS.md §3:

  1 SENSE      World.snapshot()                         (< 150k fuel)
  2 READ MEM   team_begin (80_team): the 8 shared bytes, one read (a raw read until 80_team is loaded)
  3 INTERRUPTS Decider.tick: the §2 table, one pass, first match wins
  4 TASK STEP  Decider.tick: the chosen task's step emits Nav / act() calls
  5 ACT        Nav.move is the only mover, act() the only attacker/caster (I14)
  6 HOUSEKEEP  every turn, dead ones too: shop (I7), then team_commit (claim, sighting, heartbeat)
  7 FACTS      inc, on_spawn, gstate, dead for the t line (before background: gstate is ~27k each)
  8 BACKGROUND World.work(): distance fields under the reserve; Decider.work(): clear and pair predictions
  7' TRACE     the t line, then the event lines of this round

Boot (tools/assemble.py): only the eager parts (00, 10, 20, 30, 40, 90) run at import; the lazy ones (50, 60,
65, 66, 67, 70, 80) are wrapped in loader functions (_LAZY), called in order as setup jobs (load_parts) whenever
fuel() - RESERVE covers LOAD_LINE x their code lines; each logs load|<part> fuel= lines=. Meanwhile World.setup's
stages run and the champion walks its opening route (Nav, eager). The Decider is built once every part is
loaded (DEC_FUEL); its first tick needs TICK_FUEL; until then the opening step.
The t line is written after background work so its fuel is the whole turn's (I9's bg= field).
    P|r|T|c|t|x,y <fuel> <act> tgt=<key> [bag= inc= fight= on_spawn= gstate= dead= hit=] [q=done/total]
             [+<jobs> bg=<jobs>/<bg fuel>] [snap=<fuel>]
The replay keeps only ~1 MB of stdout per team [measured], so the bracketed fields are written only when
they differ from their default (0 or -), except on a full line every FULL_EVERY rounds and until the
field queue is done (tools/invariants.py reads a missing field as its default).
"""

if cambc.is_draft():
    _dm = globals().get("draft_main")
    if _dm is not None:
        _dm()
    while True:                                        # no planner: let the engine pick (it never returns)
        cambc.end_turn()
else:
    FULL_EVERY = 100                # every field on the t line this often; else only non-default ones
    SNAP_WARN = 150_000             # snapshot budget [INVARIANTS §0]; snap= is logged when above it
    EVENTS = []                     # (tag, text) event lines of this turn, written after the t line (same round)
    LOAD_LINE = [1600]              # fuel per code line of a lazy part: 0.5-1.55k measured (13 Oct, 70_decide the
                                    # worst); raised to any worse measurement
    LAST_ROUND = 2000               # [rules]
    _MEMBUF = bytearray(8)

    def ev(tag, text):
        EVENTS.append((tag, text))

    # ------------------------------------------------------------ boot: lazy parts as setup jobs
    def load_parts(pending, force):
        """Execute the next lazy parts in order while each fits above RESERVE (force: the first one anyway,
        so loading never starves). A part that raises is logged and skipped (the bot runs without it)."""
        n = 0
        while pending:
            name, lines, loader = pending[0]
            if not (force and n == 0) and fuel() - RESERVE < LOAD_LINE[0] * lines:
                break
            f0 = fuel()
            pending.pop(0)
            try:
                loader()
                c = f0 - fuel()
                ev("load", f"{name} fuel={c} lines={lines}")
            except Exception as e:
                c = f0 - fuel()
                ev("load", f"{name} fail fuel={c} {err_text(e)}")
            if lines and 0 < c and c // lines + 1 > LOAD_LINE[0]:          # c < 0: it crossed a turn
                LOAD_LINE[0] = c // lines + 1
            n += 1
        return n

    def read_raw(s):
        cambc.shared_memory.read(0, _MEMBUF)
        s.mem = int.from_bytes(_MEMBUF, "little")

    # ------------------------------------------------------------ step 6: housekeeping
    def housekeep(w, s, dec):
        """Every turn, dead or alive: shop (I7), then my claim, sighting and heartbeat (team_commit, 80_team).
        Returns "shop" when something was bought."""
        sh = globals().get("shop_turn")                # boot turns too (dead or on spawn: I7)
        tok = None
        if dec is not None:
            tok = dec.shop(s)
        elif sh is not None:
            try:
                tok = sh(w, s)
            except Exception:
                tok = None
        wt = globals().get("ward_turn")                # 69_ward, living champions (WARD_ON)
        if wt is not None and globals().get("WARD_ON", False) and s.alive and dec is not None:
            t2 = wt(w, s, dec.task)
            if t2:
                tok = f"{tok},{t2}" if tok else t2
        tc = globals().get("team_commit")
        if tc is not None:
            tc(w, s, team_task(dec))
        return tok

    def opening(w, nav):
        """Before the Decider's first tick: one step towards the first group of my route (plan decoded),
        else the map centre."""
        goal = V(w.W // 2, w.H // 2)
        if w.plan_ok:
            c = w.plan.card_for(w.ctype)
            r = [h for h in (c.route if c is not None else ()) if h in w.anchor]
            if r:
                goal = w.anchor[r[0]]
            _tg = globals().get('tempo_goal')
            _tg = _tg(w) if _tg is not None else None
            if _tg is not None:
                goal = _tg
        nav.greedy(goal, sideways=True)
        return nav.act.replace("how=gr", "how=open")

    # ------------------------------------------------------------ crash recovery
    ERR_REPEAT = 2                  # the same error this many turns in a row drops the task(s) that raised
    CRASH_COOL = 30                 # rounds the dropped task's group rests [provisional]

    def recover(w, nav, dec, n, rnd):
        """A crashed turn must not repeat forever (the task, unchanged, raises again every round). The same
        error ERR_REPEAT turns in a row: abort the running and paused task (their group rests CRASH_COOL), so
        the next tick re-decides. Without a Decider (its build raised) or after a repeat: the opening step, so
        the champion still moves. Returns the tokens added to the t-line act."""
        s = w.snap if w is not None else None
        if s is None or not s.alive or nav is None:
            return ""
        tok = ""
        if dec is not None and n >= ERR_REPEAT:
            for t in (dec.task, dec.paused):
                if t is None:
                    continue
                try:
                    t.abort(w, s, "crash")
                except Exception:
                    pass
                k = getattr(t, "key", None)
                if isinstance(k, int):
                    dec.cool[k] = rnd + CRASH_COOL
            dec.task = dec.paused = None
            if nav.key is not None:
                nav.end(rnd, "abort")
            ev("int", f"CRASH n={n}")
            tok = " crash"
        if (dec is None or n >= ERR_REPEAT) and nav.moved_round != rnd and s.can_move:
            try:
                opening(w, nav)
                tok += " open"
            except Exception:
                pass
        return tok

    # ------------------------------------------------------------ the play loop
    def play_main():
        base_init()
        trace("boot", f"f={fuel()} type={int(cambc.me().champion_name())} lazy={len(_LAZY)}")
        w = nav = dec = None
        pending = list(_LAZY)
        was_alive, last_bag = True, 0
        q_done = False
        first = True
        idle_load = 0                                                         # turns in a row nothing loaded
        err_last, err_n = None, 0                                             # the same crash, turns in a row
        while True:
            FUEL.start()
            rnd = cambc.round_number()
            act_, jobs, bgf, sc, facts = "wait why=unknown", 0, 0, 0, None
            try:
                if w is None:
                    w = World()
                    nav = Nav(w)
                s = w.snap = w.snapshot(rnd, dec.key if dec is not None else None)   # 1 SENSE
                sc = s.cost
                if dec is None and w.setup(first) and not pending and fuel() - RESERVE > DEC_FUEL:
                    dec = Decider(w, nav)                                         # every part is loaded
                    dec.built = rnd                                               # first tick next turn (~1.6M)
                    trace("world", f"init={w.init_fuel} groups={len(w.groups)} altars={len(w.altar_pos)} "
                                   f"map={w.W}x{w.H} jobs={w.total} plan={int(w.plan_ok)} "
                                   f"route={len(dec.route)} role={dec.role}")
                tb = globals().get("team_begin")                                  # 2 READ MEM
                if tb is not None:
                    tb(w, s)
                else:
                    read_raw(s)
                _db = globals().get('defend_begin')                             # 2b 68
                if _db is not None and w.stage == 2 and getattr(w, 'team', None) is not None:
                    _db(w, s, dec)
                if dec is None or (not dec.ticked and (dec.built == rnd or fuel() - RESERVE < TICK_FUEL)):
                    act_ = opening(w, nav) if s.alive else "wait why=dead"
                elif not s.alive:
                    if was_alive:
                        ev("death", f"gems={last_bag} task={dec.task_name()} by={dec.death_cause()}")
                        if nav.key is not None:
                            nav.end(rnd, "died")                                  # a leg can't survive a death
                        dec.died(s)
                    act_ = "wait why=dead"
                else:
                    last_bag = s.bag
                    act_ = dec.tick(s)                                            # 3 INTERRUPTS + 4 STEP + 5 ACT
                tok = housekeep(w, s, dec)                                        # 6 HOUSEKEEP
                if tok:
                    act_ = tok if act_.startswith("wait") else f"{act_},{tok}"
                first = False
                was_alive = s.alive
                err_n = 0
            except Exception as e:
                act_ = err_text(e)
                err_n = err_n + 1 if act_ == err_last else 1
                err_last = act_
                try:                                                              # never freeze silently
                    act_ += recover(w, nav, dec, err_n, rnd)
                except Exception:
                    pass
                try:                                                              # a crashed turn still beats
                    tc = globals().get("team_commit")
                    if tc is not None and w is not None and w.snap is not None:
                        tc(w, w.snap, team_task(dec))
                except Exception:
                    pass
            if pending:                                                           # boot: lazy parts (setup jobs)
                try:
                    if w is not None and w.stage == 2 and w.queue and w.queue[0] in INDEX_JOBS:
                        w.work_index()                                            # the camp index first (snapshot)
                    k = load_parts(pending, idle_load >= 2)
                    idle_load = 0 if k else idle_load + 1
                except Exception as e:
                    act_ += " l" + err_text(e)
            try:                                                                  # 7 FACTS (before background)
                if w is not None and w.snap is not None:
                    s = w.snap
                    p = nav.dest if nav.moved_round == rnd else s.pos
                    facts = (p,) + (w.facts(s, p) if s.alive else (0, "-", "-", "-"))
            except Exception as e:
                act_ += " f" + err_text(e)
            try:
                if w is not None and w.stage == 2:
                    jobs, bgf = w.work()                                          # 8 BACKGROUND
                    if dec is not None and dec.ticked:
                        j2, f2 = dec.work()
                        jobs, bgf = jobs + j2, bgf + f2
            except Exception as e:
                act_ += " w" + err_text(e)
            try:                                                                  # 7' TRACE
                if facts is not None:
                    s = w.snap
                    p, inc, on, gst, dead = facts
                    k = dec.key if dec is not None and dec.key is not None else "-"
                    fight = dec.fight if dec is not None and dec.fight is not None else "-"
                    hit = (dec.hit or "-") if dec is not None else "-"
                    full = rnd % FULL_EVERY == 0 or not q_done
                    ex = "".join(f" {n}={v}" for n, v in (("bag", s.bag), ("inc", inc), ("fight", fight),
                                                         ("on_spawn", on), ("gstate", gst), ("dead", dead),
                                                         ("hit", hit))
                                 if full or (v != 0 and v != "-"))
                    if not q_done:
                        ex += f" q={w.done()}/{w.total or '-'}"
                        q_done = w.total > 0 and w.done() == w.total
                    if jobs:
                        ex += f" +{jobs} bg={jobs}/{bgf}"
                    if full or sc > SNAP_WARN:
                        ex += f" snap={sc}"
                    trace("t", f"{p.x},{p.y} {FUEL.used()} {act_} tgt={k}{ex}")
                else:
                    p = cambc.me().position()
                    trace("t", f"{p.x},{p.y} {FUEL.used()} {act_} tgt=- q=- +0")
                for tag, text in EVENTS:
                    trace(tag, text)
                EVENTS.clear()
                while nav is not None and nav.legs:
                    k, d0, took, res = nav.legs.pop(0)
                    trace("leg", f"{k} d0={d0} took={took} {res}")
                if rnd >= LAST_ROUND - 1 and dec is not None:
                    dec.report()
            except Exception as e:
                trace("t", f"0,0 {FUEL.used()} {err_text(e)} tgt=- q=- +0")
            cambc.end_turn()

    play_main()
