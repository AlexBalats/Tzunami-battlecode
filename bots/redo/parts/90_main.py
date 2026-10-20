"""Entry: the play turn loop (play_main, turn); the draft entry is 80_draft draft_main."""


def turn(w):
    """One play turn, 03_ARCHITECTURE.md section 2.4: sense + Comms.decode, the dead gate, Mem / Info, reflexes, the
    guards, act (<= 2x decide + execute), post, Comms.encode, Nav.order, traces. The guards' order is strat-sw's."""
    fa = fuel()
    s = sense(w)
    Comms.decode(w, s)
    w.ph[0] = max(w.ph[0], fa - fuel())
    if TRACE:
        w.kit.reset_check()                   # verification of the attack reset (20_champs Kit.reset_attack)
    flags = (w.attacked, w.capt, w.waiting)
    w.attacked = w.capt = w.waiting = False
    w.nav.begin()
    if flags[0]:
        w.hit = True
    if not s.alive:
        dead(w, s)
        return
    MEM.update(s)                             # 35_info: what Nav reads (05 L2, L5)
    INFO.begin(w, s)
    reflexes(w, s)
    guards(w, s, flags)
    act(w, s)
    if not (s.recalling or s.submitting) and fuel() > SCAN_FUEL:
        fb = fuel()
        SCAN.post(w, s)                       # [B1] after my move: the ward goes 2 ahead onto an unseen bush
        w.ph[2] = max(w.ph[2], fb - fuel())
    Comms.encode(w, s, BEH[w.cur[0]])
    w.nav.order(w, s)                         # 05 L3: next round's turn order
    act_trace(w, s)
    if w.nav.F_home is None and fuel() > 1_200_000:
        w.nav.home_field()


def dead(w, s):
    """The dead gate: on the death turn trace, exclude where I died and mark the team; shop; broadcast dead."""
    r = s.r
    w.act[6] += 1
    if w.was_alive:
        trace("death", f"bag={w.bag_alive} pos={w.pos.x},{w.pos.y} hp={w.hp_alive:.0f} cur={w.cur[0]} "
                       f"{tname(w, w.cur[0], w.cur[1])} enemies={w.ne_alive}")
        w.was_alive = False
        op, tg = w.cur
        w.excl[w.cur] = r + DEATH_EXCL            # no re-entry where I just died
        if op in ("kill", "hold", "hunt"):
            w.kh_until = r + DEATH_EXCL
        if op == "farm" and tg in w.G and w.G[tg].mi < 31:
            Comms.mark_death(w.G[tg].mi, r)       # team marker: avoid this group
        w.cur, w.status = ("dead", None), "done"
    if s.gold >= 30:
        buy_all(w, s)                         # dead champions may shop [rules]
    Comms.encode(w, s, DEAD)


def reflexes(w, s):
    """Before any decision: buy on spawn, the spike shift, the shards read, Varg's shield."""
    r = s.r
    if s.spawn and s.gold >= 30:
        buy_all(w, s)                         # [K2] on the spawn tiles for any reason: buy now
    if not w.spike:
        vs = s.S if w.role == "main" else 0   # [user decision 15 Oct afternoon] spike shift: the main carry's Strength
        for c, _p, _hp, st in s.allies:
            if w.ally_slot(c) == w.main and st > vs:
                vs = st
        if vs >= SPIKE_STR or r >= SPIKE_ROUND:
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
    if s.st & 0x800 and not (s.recalling or s.submitting):
        w.kit.shield(s, s.hp < (w.hp_alive or 0))     # [K1] Varg's shield first: walking allows it [rules]


def guards(w, s, flags):
    """State upkeep and the Behavior rules, in strat-sw's order: F_me rebuild, the `stay` trace (a measure), my
    position, stall (PROG_STALL rounds without progress), timeout (the deadline). A failed rule sets status 'failed'
    and excludes the current (op, target) so decide picks again. Stuck and oscillation are Nav's (05 L6: act)."""
    r = s.r
    if not w.was_alive:
        w.was_alive = True
        w.status = "done"
        w.nav.build_fme(s.pos)
    elif s.pos.chebyshev_distance(w.nav.fme_root) > FME_MOVE:
        w.nav.build_fme(s.pos)                    # also after a recall (the jump is > 6)
    # still: same tile, last turn neither capturing, channelling, attacking nor dead
    exempt = flags[0] or flags[1] or s.recalling or s.submitting
    if flags[2] and not exempt and stack_mode(w, r):
        exempt = True                         # [user plan 15 Oct, stack opener] group mode never sets waiting
    w.stay = w.stay + 1 if s.pos == w.pos and not exempt else 0
    if w.stay == 30:
        trace("stay", f"{s.pos.x},{s.pos.y} {w.cur[0]} {tname(w, w.cur[0], w.cur[1])} wait={int(flags[2])}")
    if FARM.tflip is not None:                # [user decision 15 Oct afternoon] target flips count as oscillation
        trace("osc", f"target g{FARM.tflip[0]}<->g{FARM.tflip[1]} flips={FARM.flips} {w.cur[0]} {tname(w, w.cur[0], w.cur[1])}")
        FARM.tflip = None
    w.pos, w.bag_alive, w.hp_alive = s.pos, s.bag, s.hp
    w.ne_alive = len(s.enemies)
    if w.status == "going":
        # [IMPROVEMENTS 2] stall guard: w.prog has not risen for PROG_STALL rounds -> failed like `stuck`. Exempt:
        # attacking / capturing / waiting last turn, recalling, channelling, a pair seek (Farm.seeking: own 10-15
        # round fail), and kill / shop / heal / fall / hold (own chase and timeout rules)
        prog_update(w, s, flags[0])
        seek = BEH[w.cur[0]].seeking()
        if exempt or flags[2] or seek or w.cur[0] not in ("farm", "bank", "join", "hunt"):
            w.pstall = 0
        elif w.pstall >= PROG_STALL:
            trace("exec", f"{w.cur[0]} {tname(w, w.cur[0], w.cur[1])} failed stall prog={w.prog:.2f}")
            w.excl[w.cur] = r + EXCL
            w.status = "failed"
            w.pstall = 0
    if w.status == "going" and r > w.deadline and not (s.recalling or s.submitting):
        trace("exec", f"{w.cur[0]} {tname(w, w.cur[0], w.cur[1])} failed timeout")
        if w.cur[0] == "kill":
            KILL.ban(w.cur[1], r)                   # a timed-out kill: finishers excluded too (60_behaviors Kill); backoff
            w.excl[w.cur] = KILL.kfail[w.cur[1]]
        else:
            w.excl[w.cur] = r + EXCL
        w.status = "failed"


def act(w, s):
    """Up to 2 decide + execute: a Behavior that ends this turn (done / failed) lets decide pick again, fuel
    permitting (FUEL_FLOOR before decide, DECIDE2_FUEL after an execute). Channelling and recalling skip decide. A Nav
    failure this execute (05 L6: no gain on the goal for STALL_FAIL turns) fails the Behavior."""
    r = s.r
    for _k in range(2):
        if not (s.recalling or s.submitting) and fuel() > FUEL_FLOOR:
            fb = fuel()
            UPD.decide(w, s)
            w.ph[1] = max(w.ph[1], fb - fuel())
        op, tg = w.cur
        fb = fuel()
        w.nav.fail = None
        st = BEH[op].execute(w, s, tg)
        if st is None:
            break                             # idle / dead: nothing to execute
        w.ph[2] = max(w.ph[2], fb - fuel())
        if st == "going" and w.nav.fail:
            st = f"failed {w.nav.fail}"
        if st == "going":
            w.status = st
            break
        trace("exec", f"{op} {tname(w, op, tg)} {st}")
        if st.startswith("failed"):
            st = "failed"
            w.excl[w.cur] = max(w.excl.get(w.cur, 0), KILL.kfail.get(tg, 0) if op == "kill" else r + EXCL)   # keeps a longer one
        w.status = st
        if fuel() < DECIDE2_FUEL:
            break                             # 08 F1 (M6): no second decide that would roll the turn over


def act_trace(w, s):
    """Turn counters by what I did (w.act) and the `idle` trace after 4 idle turns."""
    k = 3 if s.recalling or s.submitting else 1 if w.attacked else 2 if w.capt else 4 if w.waiting else \
        0 if w.nav.moved else 5
    w.act[k] += 1
    w.idle = w.idle + 1 if k == 5 else 0
    if w.idle == 4 and TRACE:
        op, tg = w.cur
        x = ""
        if op == "farm" and tg in w.G:
            o = w.G[tg]
            x = (f"st={o.st} live={len(s.live.get(tg, ()))} vis={int(visible(w, s, o))} "
                 f"d={min(t.chebyshev_distance(s.pos) for t in o.tiles)} walk={w.nav.walk_to(f'g{tg}', s.pos)} "
                 f"canmove={int(s.can_move)}")
        trace("idle", f"{op} {tname(w, op, tg)} {x} step={w.nav.last_step} "
                      f"occ={vision.champion_tiles().count()}")
        w.nav.last_step = "-"


def play_main():
    base_init()
    w = WORLD
    w.cur, w.status, w.excl, w.sent, w.started, w.deadline = ("idle", None), "done", {}, -1, 0, 0
    w.was_alive, w.stay = True, 0
    w.prog, w.pbest, w.pstall, w.d0 = 0.0, 0.0, 0, None     # [IMPROVEMENTS 2] sunk progress (60_behaviors prog_update)
    w.subs = {}                                       # stack subgroups (70_updaters group_slots)
    w.subs_r = 0                                      # round w.subs was last set (decide re-splits at OPEN_END)
    w.phase = None                                    # 20_champs (phase index, spike, role) last applied
    w.spike = False                                   # spike shift on (20_champs SPIKE_*)
    w.attacked = w.capt = w.waiting = False
    w.bag_alive, w.hp_alive, w.ne_alive = 0, 0, 0
    w.ph = [0] * 3
    w.idle = 0
    w.kh_until = 0
    w.hit = False
    w.rawb, w.uhit = 0.0, -99                         # 08 F1: last full turn's best farm price; F4: round of an unseen hit
    w.roam, w.big3 = 0.0, -999                        # no-sighting hunt weight, last >= 3-enemy sighting (50_prices)
    w.score = (0, 0)
    w.post = None                                     # posture column last traced
    w.shards, w.shards_r, w.shards_fuel = 0, -99, None                     # shards owned (emblems count their shards), read every 20
    w.act = [0] * 7                                   # mv atk cap chan wait idle dead (turns per tick)
    errs, nerr = set(), [0]          # turn errors: each text traced once, all counted (tick `errs=`)
    fu = []
    f0 = fuel()
    trace("env", f"round={cambc.round_number()} fuel_at_start={f0} turn_budget={cambc.constants.FUEL_PER_TURN if hasattr(cambc.constants, 'FUEL_PER_TURN') else '?'}")
    try:
        me_init()                                     # 20_champs: ME facts, once (traces tag me)
        apply_phase(w)
        w.boot()
        apply_phase(w)                                # again after boot: the role (World.slot_init) sets gold and build
        w.pos = w.nav.fme_root
        seed = opening_seed(w)
        if seed is not None:
            s = sense(w)
            Comms.decode(w, s)
            w.start(("farm", seed), s.r, s)
            UPD.seed, UPD.seed_until = seed, SEED_UNTIL   # decide keeps it until then unless HEAL / retreat (seeded)
            if stack_mode(w, s.r):
                trace("choice", f"farm {tname(w, 'farm', seed)} group seed slot={w.slot} "
                                f"team={GROUP_NAMES.get(sub_size(w), '?')} with={w.subs.get(w.slot)}")
            else:
                trace("choice", f"farm {tname(w, 'farm', seed)} seed slot={w.slot}")
            Comms.encode(w, s, FARM)
        if w.slot == 0 and TRACE:                     # the whole list (S = 5; S = 3 / 4 are its prefixes)
            trace("choice", "seeds " + " ".join(tname(w, "farm", h) for h in opening_slots(w, 5)))
    except Exception as e:
        trace("err", "boot " + err_text(e))
    trace("boot", f"round1 fuel={f0 - fuel()} left={fuel()}")
    cambc.end_turn()
    while True:
        f0 = fuel()
        try:
            turn(w)
        except Exception as e:
            nerr[0] += 1
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
                              f"score={w.score[0]}-{w.score[1]} shards={w.shards} "
                              f"str={me.strength() if alive else 0:.0f} sw={SCAN.n} nav={'/'.join(map(str, w.nav.n))} "
                              f"errs={nerr[0]}")
            except Exception as e:
                trace("err", "tick " + err_text(e))
            fu = []
            w.ph = [0] * 3
            w.act = [0] * 7
            w.nav.n = [0] * 8
        cambc.end_turn()


if cambc.is_draft():
    draft_main()
else:
    play_main()
