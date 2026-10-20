"""Executors: one step of the current (option, target) per turn -> "going" | "done" | "failed".

No stored intent beyond (option, target, started, deadline, exclusions) plus per-executor progress counters.
Timeout = walk estimate + 10 rounds, plus the option's own work (clear + capture for farm, the channel for bank,
30 rounds for hold); a timeout is a failure and excludes (option, target) for EXCL rounds.
"""


def _set_cur(self, new, r, s):
    op, tg = new
    self.cur, self.started, self.status = new, r, "going"
    self.kd, self.kn, self.arrived, self.waited = 99, 0, None, 0
    self.hit = False                            # trace only: attacked since this choice (choice `hit=`)
    self.lastbag, self.lastgold = s.bag, s.gold
    self.peekn, self.peeked = 0, False          # dead-camp pickup (exec_farm): rounds near the group seeing nothing
    self.gathered, self.gmates = False, 0       # [T5] this take's gather is over; most mates seen at the rally
    self.contest = 0                            # rounds on the spawn with an enemy on the group's tiles (exec_farm)
    walk, work = 0, 0
    if op == "farm" and tg in self.G:
        # [user decision 15 Oct afternoon, ladder cd737718] backstop: farm target A -> B -> A within FLIP_WINDOW rounds
        # locks A (B excluded FLIP_LOCK rounds); 90_main's osc detector traces the flip
        fh = self.fh = (self.fh + [(r, tg)])[-3:]
        if len(fh) == 3 and fh[0][1] == tg != fh[1][1] and r - fh[0][0] <= FLIP_WINDOW:
            self.excl[("farm", fh[1][1])] = r + FLIP_LOCK
            self.flips += 1
            self.tflip = (fh[1][1], tg)
            trace("choice", f"flip lock {tname(self, 'farm', tg)} excl={tname(self, 'farm', fh[1][1])} in={r - fh[0][0]}")
            self.fh = []
        walk = self.gd.get(tg, 40)
        o = self.G[tg]
        mons = [m for m in (o.mons if o.hp is None else o.hp) if m[0] > 0]
        k = self.ncrew = crew(self, s, tg)     # [T2] the crew this take is priced for
        work = (clear_dmg(mons, s_eff(self, s, tg, k), k)[0] if mons else 0) + 8
        if k >= 2:
            work += GATHER_MAX + 2              # [T5] gathering the crew
        if o.st == "resp":
            walk = max(walk, o.until - r)       # [T6] waiting for the respawn
    elif op in ("bank", "hold") and tg is not None and tg < len(self.ad):
        walk = self.ad[tg]
        work = max(1, -(-s.bag // 10)) + 2 if op == "bank" else 30
    elif op == "shop":
        work = 8
    elif op == "join" and tg is not None:
        walk = 20
    elif op == "kill":
        walk = 6 + ME["prof"].get("hunt", 0)
    elif op == "hunt":
        walk = HUNT_MAX
    elif op == "fall":
        walk = 15
    elif op == "heal":
        walk, work = 10, 7                      # step out of reach, 5-turn recall, the heal turn on spawn
    elif op == "ward" and tg is not None and tg < len(self.wtiles):
        self.ward_tries[tg] = self.ward_tries.get(tg, 0) + 1    # WARD_TRIES choices per tile at most (no stall)
        t = self.wtiles[tg]
        walk = fget(self.F_me, t)
        if walk >= FAR:
            walk = 2 * s.pos.chebyshev_distance(t)
        work = 3
    self.deadline = r + min(walk, 150) + 10 + work
    # [IMPROVEMENTS 2] sunk progress (prog_update): start distance (chebyshev, set lazily)
    self.prog = 0.0
    self.d0, self.pbest, self.pstall, self.chan, self.chanlen, self.khits, self.pw = None, 0.0, 0, 0, 1, 0, 0
    self.hp0, self.ttk0 = None, None
    if op == "farm" and tg in self.G:
        self.hp0 = sum(m[0] for m in mons) if self.G[tg].st == "alive" else 0.0
    if op == "kill":
        e = find_enemy(s, tg)
        if e is not None:
            self.ttk0 = max(1, -(-int(e[2]) // int(s.S)))


World.set_cur = _set_cur


def prog_target(w, s):
    """The current choice's target tile for the walk fraction (None: no walk target)."""
    op, tg = w.cur
    if tg is None:
        return None
    if op == "farm":
        return w.G[tg].anchor if tg in w.G else None
    if op in ("bank", "hold"):
        return w.apos[tg] if tg < len(w.apos) else None
    if op == "ward":
        return w.wtiles[tg] if tg < len(w.wtiles) else None
    if op == "hunt":
        return w.G[tg - 100].anchor if tg >= 100 else (w.apos[tg] if tg < len(w.apos) else None)
    if op == "kill":
        e = find_enemy(s, tg)
        return e[1] if e is not None else None
    if op == "join":
        b = s.mem[tg] if tg < 5 else 0
        if (b & 7) == 3:
            return next((a[1] for a in s.allies if w.ally_slot(a[0]) == tg), None)
        if (b & 7) == 1 and (b >> 3) in w.idx:
            return w.G[w.idx[b >> 3]].anchor
    return None


def prog_update(w, s, hit):
    """[IMPROVEMENTS 2, 15 Oct night] w.prog in [0, 1] for the current choice from values already at hand (the walk
    on the goal field for farm / bank, else chebyshev to the target; s.live / o.hp, s.submitting, last turn's attack):
    farm = walk x 0.5 before my first hit, then 0.5 + 0.5 x group HP removed / group HP at the first hit; bank = walk
    x 0.5, then 0.5 + 0.5 x channel turns / ceil(bag / 10); kill = hits / ttk (walk without a ttk); ward, join, hunt =
    walk; shop, heal, fall, hold = 0."""
    op, tg = w.cur
    p = 0.0
    if op in ("farm", "bank", "ward", "join", "hunt", "kill"):
        t = prog_target(w, s)
        wf = 0.0
        if t is not None:
            # farm / bank: the walk left on the goal field I step down; the chebyshev distance stalls while the path
            # leads round a wall (rows / ambush 19 Oct: 29 and 60 stall failures a game on bodies that were walking)
            key = f"g{tg}" if op == "farm" and tg in w.G else (f"a{tg}" if op == "bank" and tg < len(w.apos) else None)
            d = fget(w.goal(key), s.pos) if key else FAR
            if d >= FAR:
                d = t.chebyshev_distance(s.pos)
            if w.d0 is None:
                w.d0 = d
            wf = 1.0 - d / w.d0 if w.d0 > 0 else 1.0
        if op == "farm" and tg in w.G:
            o = w.G[tg]
            lv = s.live.get(tg)
            if lv:
                ghp = sum(max(0.0, hp) for _c, hp, _p, _st in lv)
            else:
                ghp = sum(m[0] for m in (o.hp if o.hp is not None else o.mons) if m[0] > 0) if o.st == "alive" else 0.0
            if not w.hit:
                w.hp0 = ghp                     # the latest group HP seen before my first hit
                p = 0.5 * wf
            else:
                p = 0.5 + 0.5 * (1.0 - ghp / w.hp0) if w.hp0 else 1.0
            if w.hp0 is not None and w.hp0 <= 0 and not w.hit:
                p = wf                          # a cleared group: the walk (then the capture) is the job
        elif op == "bank":
            if s.submitting:
                if w.chan == 0:
                    w.chanlen = max(1, -(-s.bag // 10))
                w.chan += 1
                p = 0.5 + 0.5 * w.chan / w.chanlen
            else:
                p = 0.5 * wf
        elif op == "kill":
            if hit:
                w.khits += 1
            p = w.khits / w.ttk0 if w.ttk0 else wf
        else:
            p = wf
    w.prog = min(1.0, max(0.0, p))
    if w.prog > w.pbest + 1e-6:
        w.pbest, w.pstall = w.prog, 0
    else:
        w.pstall += 1


CLOSE_TTK = 3               # [user plan 15 Oct, ladder 4] close dash only when my hits to kill are <= this (ranged)
CLOSE_TTK_MELEE = 6         # [user decision 15 Oct night] melee dashers (Vale): ladder showed 0 close dashes in 5 games with 3
GATHER_MAX = 8              # PROVISIONAL A77 [T5] rounds a crew body waits at the rally for the next mate
GATHER_R = 6                # PROVISIONAL A77 [T5] claimants within this of the group's camps count as gathered
RALLY_D = 4                 # [T5] the rally: this far from the group's nearest camp (camps have range 3 [measured A31])
WAIT_EXCL = 30              # [guess] rounds that (farm, group) is excluded after a failed gather
CONTEST_MAX = 5             # PROVISIONAL A79 rounds on the spawn with an enemy on the group's tiles before I leave
RETREAT_HP = 0.6            # [guess] fallback retreats from enemies within 4 below this HP fraction
PEEK_ON = 1                 # [user decision 15 Oct afternoon] dead-camp pickup: step onto a spawn tile of an unseen group at the goal
PEEK_ROUNDS = 3             # ... within 2 of its tiles this many rounds with nothing seen: remembered as a waiting reward
SPLASH_ON = 1               # [user decision 15 Oct] splash champions (profile `splash`): target / walk to the monster with the
                            # most live neighbours within 1 (0: lowest HP in range, the old rule; the `splash` trace stays)


def in_camp_range(s, w):
    pts = []
    for h, lv in s.live.items():
        for _c, _hp, p, st in lv:
            if st > 0 and p.chebyshev_distance(s.pos) <= CAMP_R:
                pts.append(p)
    return pts


RECALL_CLEAR = 6            # no recall started or kept with an enemy within this (ranged reach 3 + a step + margin)


def safe_recall(w, s):
    """Recall only when clear [rules: damage or stun breaks it]: never start or keep one while an enemy is within
    RECALL_CLEAR or a live camp within its range 3. Not clear: cancel a running recall, then step away from the
    enemies towards home (step_flee) or out of camp range (step_away)."""
    ne = [e[1] for e in s.enemies if e[4] <= RECALL_CLEAR]
    pts = in_camp_range(s, w)
    if s.recalling:
        if not ne and not pts:
            return "going"
        try:
            w.me.cancel_recall()
            st = int(w.me.state())
            s.recalling, s.can_move, s.can_attack = bool(st & 2), bool(st & 8), bool(st & 16)
            trace("exec", f"recall cancelled enemies={len(ne)} camps={len(pts)} hp={s.hp:.0f}")
        except Exception as e:
            trace("exec", "cancel_recall " + err_text(e))
            return "going"
    if ne:
        dash_escape(w, s, ne)
        if w.step_flee(s, ne) == "blocked":
            w.step_to("home", s)
        return "going"
    if pts:
        w.step_away(s, pts)
        return "going"
    try:
        w.me.recall()
    except Exception:
        w.step_to("home", s)
    return "going"


def dash_escape(w, s, ne):
    """ESCAPE [user plan 15 Oct]: an enemy within 2 -> dash to the tile farthest from the nearest enemy (capped 7),
    ties down the home field."""
    if s.near_e <= 2 and w.dash_ab is not None:
        hf = w.home_field()
        w.dash_to(s, lambda q: (-min(7, min(q.chebyshev_distance(p) for p in ne)), fget(hf, q)), "escape")


def partners_near(w, s, h):
    """Visible allies within GATHER_R of the group's camps that broadcast farm on it."""
    n = 0
    o = w.G[h]
    for c, p, _hp, _st in s.allies:
        if min(t.chebyshev_distance(p) for t in o.tiles) <= GATHER_R:
            k = w.ally_slot(c)
            b = s.mem[k] if k < 5 else 0
            if (b & 7) == 1 and (b >> 3) == o.mi:
                n += 1
    return n


def live_ok(w, s, h, k):
    """k bodies (Strength like mine) clear h with the most-hit body keeping KEEP_HP (live clear model)."""
    o = w.G[h]
    mons = [m for m in (o.hp if o.hp is not None else o.mons) if m[0] > 0]
    if not mons:
        return True
    cd = clear_dmg(mons, s_eff(w, s, h, k), k)
    return my_dmg(cd[1], k, cd[0]) <= s.hp * SURVIVE     # TANK_SHARE; [K3] mitigation


def handoff(w, s, o):
    """[T7, from the pair/trio opener] True when I should leave group o's capture to an ally. Candidates: me and the
    visible allies within 4 of the group's spawn tiles that broadcast farm on it; the carry is Vesper if she is one of
    them (she took it), else the lowest slot among them. Everyone else leaves (its reward is unsplit) and re-prices."""
    ks = []
    for c, p, _hp, _st in s.allies:
        k = w.ally_slot(c)
        b = s.mem[k] if k < 5 else 0
        if (b & 7) == 1 and (b >> 3) == o.mi and min(t.chebyshev_distance(p) for t in o.tiles) <= 4:
            ks.append(k)
    if not ks:
        return False
    vs = w.roster.index(VESPER_ID) if VESPER_ID in w.roster else -1
    ks.append(w.slot)
    if vs in ks:
        carry = vs
    else:
        carry = min(ks)
    return carry != w.slot


def splash_nb(lv, i):
    """Live monsters of lv (sense entries) other than lv[i] within Chebyshev 1 of it (Varg's splash reach [rules])."""
    p = lv[i][2]
    n = 0
    for j, (_c, hp, q, _st) in enumerate(lv):
        if j != i and hp > 0 and q.chebyshev_distance(p) <= 1:
            n += 1
    return n


def exec_farm(w, s, h):
    o = w.G[h]
    lv = s.live.get(h)
    if lv:
        tgt = [(hp, i) for i, (_c, hp, p, _st) in enumerate(lv) if p.chebyshev_distance(s.pos) <= ME.get("range", 1)]
        hurt = any(hp < w.G_maxhp(c) for c, hp, _p, _st in lv)
        if w.ncrew >= 2 and not hurt and not w.gathered:
            # [T5] P19 gather before the first hit (monsters are friendly until hit [rules]): hit once the bodies at
            # the group are enough, the draft need (the number every body counts; the crew's extra body joins the take
            # under way) or my live clear model says they survive it. Short: wait at the rally while the crew is
            # coming, i.e. enough bodies still claim the group and a mate arrived within the last GATHER_MAX rounds.
            # (19 Oct: waiting for all of need + 1 with one timer per body failed 28-47 times a game on elkring: the
            # early bodies gave up as the late ones arrived, and each failure dropped the others below the crew.)
            mates = partners_near(w, s, h)
            need = min(w.ncrew, max(1, o.need))
            if 1 + mates < need and not live_ok(w, s, h, 1 + mates):
                if min(p.chebyshev_distance(s.pos) for _c, _hp, p, _st in lv) > RALLY_D:
                    w.step_to(f"g{h}", s)
                    w.waiting = True
                    return "going"
                if mates > w.gmates:
                    w.gmates, w.waited = mates, 0      # a mate arrived: the crew is coming, the clock restarts
                w.waited += 1                   # counts rounds at the rally, not walking to it
                # the bodies on it: my byte goes out at the end of this turn, so count me in place of it
                ncl = claimants(w, s, o.mi) + (s.mem[w.slot] != 1 | o.mi << 3)
                if w.waited < GATHER_MAX and ncl >= need:
                    w.waiting = True
                    return "going"
                w.excl[("farm", h)] = s.r + WAIT_EXCL
                trace("exec", f"farm {tname(w, 'farm', h)} failed gather waited={w.waited} mates={mates} "
                              f"cl={ncl}/{need}")
                return "failed"
            w.gathered = True
            trace("gather", f"g{h} waited={w.waited} mates={mates}/{need - 1}")
        spl = ME["prof"].get("splash")
        if spl and SPLASH_ON and not hurt and len(lv) >= 2:
            # [user decision 15 Oct, Varg's splash] before the first hit: stand next to the monster with the most live
            # neighbours within 1 when no monster in range has as many
            nb = [(splash_nb(lv, i), -hp, i) for i, (_c, hp, _p, _st) in enumerate(lv) if hp > 0]
            if nb:
                bn = max(nb)
                inr = max((splash_nb(lv, i) for _hp, i in tgt), default=-1)
                if bn[0] > inr and bn[0] >= 1 and w.step_near(lv[bn[2]][2], ME.get("range", 1), s) == "moved":
                    return "going"
        if tgt and s.can_attack:
            if spl and SPLASH_ON:
                tgt = [(-splash_nb(lv, i), hp, i) for hp, i in tgt]    # most neighbours, then lowest HP
                tgt.sort()
                tgt = [(hp, i) for _n, hp, i in tgt]
            else:
                tgt.sort()
            c = lv[tgt[0][1]][0]
            if spl and TRACE:
                trace("splash", f"nb={splash_nb(lv, tgt[0][1])} live={sum(1 for x in lv if x[1] > 0)} hp={tgt[0][0]:.0f} g{h}")
            alts = [lv[i][0] for _hp, i in tgt[1:]]
            kit = KIT_ON and s.st & 0x800 and (w.kit_shield(s, False, c) or w.kit_stun(s, h, c))  # [K1] the turn's cast
            try:
                w.me.attack(c)
                w.attacked = True
                if not kit:
                    w.reset_attack(c, tgt[0][0], alts)
            except Exception:
                pass
            if s.st & 0x800 and not kit:         # CAN_CAST
                if KIT_ON and _dead(c):
                    c = next((u for u in alts if not _dead(u)), c)     # [K1] not on the monster my hits just killed
                w.cast(c, True)
            return "going"
        if tgt:
            w.attacked = True                   # in range, attack spent this turn
            return "going"
        if LIVE_STEP and hurt:
            # [LIVE_STEP] the take is under way: towards a free tile in range of a live monster (no dead camp's tile)
            live = [p for _c, hp, p, _st in lv if hp > 0]
            if live and min(p.chebyshev_distance(s.pos) for p in live) <= 6:
                w.step_near(live, ME.get("range", 1), s)
                return "going"
        if len(lv) < len(o.tiles) and w.walk_to(f"g{h}", s.pos) == 0:
            w.step_near([p for _c, _hp, p, _st in lv], ME.get("range", 1), s)    # next to a dead camp only
        else:
            w.step_to(f"g{h}", s)
        return "going"
    # no live camp of h in vision
    vis = visible(w, s, o)
    if vis:
        if o.seen != s.r:
            update_groups(w, s, [h])
        if o.st == "resp":
            if w.capt or o.until - s.r > RESP_LOOK:
                return "done"                   # my capture came in, or it respawns too late to wait for
            # [T6] at the respawn early: wait out of camp range for it (and the crew)
            if min(t.chebyshev_distance(s.pos) for t in o.tiles) > RALLY_D:
                w.step_to(f"g{h}", s)
            w.waiting = True
            return "going"
        if o.st == "reward":
            onspawn = any(t == s.pos for t in o.tiles)
            if handoff(w, s, o):
                # [T7] not the carry: step off the spawn tiles, leave it unsplit, re-price at once
                if onspawn:
                    w.step_away(s, o.tiles)
                o.st, o.until = "resp", s.r + o.resp
                w.excl[("farm", h)] = s.r + EXCL        # update_groups re-reads "reward" while it is visible
                trace("exec", f"farm {tname(w, 'farm', h)} handoff bag={s.bag} gold={s.gold}")
                return "done"
            if onspawn:
                w.capt = True
                if s.bag > w.lastbag or s.gold > w.lastgold:
                    o.st, o.until = "resp", s.r + o.resp
                    return "done"
                # P17 "on contentious ground, attack not" / P11: an enemy on the group's spawn tiles resets the capture
                # [rules; region = spawn tiles, A79]. Past one capture timer the take is over: re-price (kill if the
                # fight pays, else elsewhere). (packs 19 Oct: Vesper and theirs stood on one gold group r44-r92, no
                # capture, no blow, until their Varg and Ryth came and killed ours.)
                if any(e[1] in o.tiles for e in s.enemies):
                    w.contest += 1
                    if w.contest > CONTEST_MAX:
                        w.excl[("farm", h)] = s.r + EXCL
                        trace("exec", f"farm {tname(w, 'farm', h)} contested n={w.contest}")
                        return "failed"
                return "going"
            if w.step_to(f"c{h}", s) == "blocked" and s.can_move:
                w.step_near(o.anchor, 0, s)
            return "going"
    if s.bag > w.lastbag and w.capt:
        o.st, o.until = "resp", s.r + o.resp
        return "done"
    if o.st == "reward":
        # memory says cleared (seen, or aged below): the capture tile shows the cluster on arrival (reward branch above)
        if w.step_to(f"c{h}", s) == "blocked" and s.can_move:
            w.step_near(o.tiles, 0, s)
        return "going"
    dm = min(t.chebyshev_distance(s.pos) for t in o.tiles)
    if PEEK_ON and not vis and dm <= max(1, ME.get("range", 1)):
        # [user decision 15 Oct afternoon, ladder cd737718: Varg and Ryth priced two cleared camps as alive for 900
        # rounds from the ring around a bush cluster] at the goal, nothing of the group seen: step onto its nearest spawn
        # tile (inside the bush the cluster is visible; a failed step onto an occupied tile reveals it [rules])
        if dm <= 2:
            w.peekn += 1
            if w.peekn >= PEEK_ROUNDS and o.st == "alive":
                o.st = "reward"                 # memory ageing: priced / executed as a waiting reward (capture branch)
                trace("exec", f"farm {tname(w, 'farm', h)} aged reward n={w.peekn}")
        if not w.peeked:
            w.peeked = True
            trace("exec", f"farm {tname(w, 'farm', h)} peek d={dm} st={o.st}")
        if dm > 0:
            w.step_near(o.tiles, 0, s)
        return "going"
    w.step_to(f"g{h}", s)
    return "going"


def _maxhp(self, c):
    try:
        return G_HP[int(c.kind())][0]
    except Exception:
        return 1e9


World.G_maxhp = _maxhp


def exec_bank(w, s, a):
    if s.submitting:
        return "going"
    if s.bag == 0:
        return "done"
    ap = w.apos[a]
    if s.pos.chebyshev_distance(ap) <= 1:
        if s.near_e <= 3 and s.bag > 10:
            return "failed"                     # [tuned] no multi-turn channel next to an enemy (8 bank deaths)
        try:
            w.me.submit_gems(ap)
            return "going"
        except Exception:
            return "failed"
    if w.step_to(f"a{a}", s) == "blocked" and (w.walk_to(f"a{a}", s.pos) or FAR) >= FAR:
        return "failed"
    return "going"


def find_enemy(s, hd):
    for e in s.enemies:
        if int(e[0]) == hd:
            return e
    return None


def kban(w, hd, r):
    """Ban target hd after a failed chase: KFAIL_ROUNDS x 2^(consecutive failures - 1), capped KFAIL_MAX; a landed hit resets."""
    n = w.kfn.get(hd, 0) + 1
    w.kfn[hd] = n
    w.kfail[hd] = r + min(KFAIL_MAX, KFAIL_ROUNDS * (1 << (n - 1)))
    if n > 1:
        trace("exec", f"kill {hd} ban x{n} until r{w.kfail[hd]}")


def exec_kill(w, s, hd):
    e = find_enemy(s, hd)
    if e is None:
        return "failed"
    c, p, hp, _b, dd, _st = e
    if hp <= 0:
        return "done"
    kz = w.cur[0] == "kill"                     # the exclusions apply to a chosen kill, not the trapped fight (exec_fall)
    if kz and near_espawn(w, p):
        w.kfail[hd] = s.r + EXCL                # [user decision 15 Oct] the target reached their spawn: heals to full
        trace("exec", f"kill {hd} failed espawn tp={p.x},{p.y}")
        return "failed"
    rng = ME.get("range", 1)
    if dd <= rng:
        w.attacked = True
        if s.can_attack:
            try:
                w.me.attack(c)
                w.kfn[hd] = 0                   # a landed hit resets the failure backoff
                w.reset_attack(c, hp)
            except Exception:
                pass
        if s.st & 0x800:
            w.cast(c, False)
        return "going"
    if dd >= w.kd:
        w.kn += 1
        ttk = -(-int(hp) // int(s.S))
        # a finisher chase gets 2 ttk + 2 rounds (pinned / 1 tile/turn); else the phase's `chase` (default 3)
        if w.kn >= (2 * ttk + 2 if ttk <= 2 else ME["prof"].get("chase", 3)):
            kban(w, hd, s.r)                    # [bug fix 15 Oct, ladder 4] finishers too; [15 Oct afternoon] 6 rounds; [night] backoff
            return "failed"
    else:
        w.kn = 0
    w.kd = dd
    # CLOSE [user plan 15 Oct]: 1-2 tiles beyond range -> dash into range (farthest such tile), then try the attack.
    # [user plan 15 Oct, ladder 4] only onto a target I kill in <= CLOSE_TTK hits, and with enemies within 8 of me
    # <= allies within 8 + 1 (ladder: dashes onto 750-HP targets, 5 hits, with 4 enemies in sight); else walk
    if rng < dd <= rng + 2 and -(-int(hp) // int(s.S)) <= (CLOSE_TTK_MELEE if rng <= 1 else CLOSE_TTK)             and sum(1 for x in s.enemies if x[4] <= 8) <= sum(1 for a in s.allies if a[1].chebyshev_distance(s.pos) <= 8) + 1             and w.dash_to(s, lambda q: -q.chebyshev_distance(p) if q.chebyshev_distance(p) <= rng else None, "close"):
        res = "no-attack"
        try:
            w.me.attack(c)
            w.attacked, res = True, f"attacked hp {hp:.0f}->{_uhp(c)}"
        except Exception as ex:
            res = "raise " + err_text(ex)[:60]
        trace("dash", f"close then {res} ttk={-(-int(hp) // int(s.S))}")
        return "going"
    if s.st & 0x800:
        w.cast(c, False)                        # dashes and ranged spells close the gap
    w.step_near(p, rng, s)
    return "going"


def exec_hunt(w, s, a):
    """Walk toward the sighting's altar a; done once an enemy is visible (KILL prices it); failed (excluded EXCL
    rounds) on arrival with nobody there or after HUNT_MAX rounds."""
    if s.enemies:
        return "done"
    key, t = (f"g{a - 100}", w.G[a - 100].anchor) if a >= 100 else (f"a{a}", w.apos[a])
    if s.pos.chebyshev_distance(t) <= 2 and (a >= 100 or w.aside[a] == 2):
        w.hvis[a] = s.r                         # patrol arrival: recorded, done (HUNT_REVISIT); the loop in 90_main
        trace("patrol", f"visit {'g' + str(a - 100) if a >= 100 else 'A' + str(a)}")    # re-chooses this turn: next altar
        return "done"
    if s.r - w.started >= HUNT_MAX or s.pos.chebyshev_distance(t) <= 2:
        return "failed"
    w.step_to(key, s)
    return "going"


def exec_hold(w, s, a):
    ap = w.apos[a]
    if s.pos.chebyshev_distance(ap) > 1:
        w.step_to(f"a{a}", s)
        return "going"
    if w.arrived is None:
        w.arrived = s.r
    w.capt = True                               # deliberate stand
    for c, p, hp, _b, dd, _st in s.enemies:
        try:
            chan = c.is_submitting_gems()
        except Exception:
            chan = False
        if chan:
            if s.st & 0x800:
                for ab, _oc, _oe, cc, _rs, _g in w.ab:
                    if cc:
                        try:
                            if ab.is_ready() and ab.use(c):
                                break
                        except Exception:
                            pass
            if dd <= ME.get("range", 1) and s.can_attack:
                try:
                    w.me.attack(c)
                    w.attacked = True
                except Exception:
                    pass
            break
    return "done" if s.r - w.arrived >= 30 else "going"


def buy_all(w, s):
    """Buy shards along the profile's build: each buy goes to the first entry whose emblem is not complete
    (build_target, re-read after every buy so a finished emblem moves on to the next family). Trace per buy."""
    build = ME["prof"].get("build") or (ME["prof"]["item"],)
    me_id = w.roster[w.slot] if w.slot < len(w.roster) else -1
    if ROLE_BUILD and (me_id in TANK_IDS if ROLE_BUILD == 1 else me_id != VESPER_ID):
        build = (cambc.ItemType.JUNGLE_SHARD_OF_STRENGTH,) + tuple(build)     # [K2] the tanks take camp hits
    n = 0
    try:
        while n < 10:
            item, _c = build_target(w.me, build, ME["prof"].get("alt"))
            ME["target"] = item
            if not w.me.can_buy(item):
                break
            w.me.buy(item)
            n += 1
            trace("shop", f"buy {item.name} gold={w.me.gold_count()}")
    except Exception as e:
        trace("err", "shop " + err_text(e))
    if n:
        mit_refresh(w)                          # [K3] a new Jungle emblem counts at once
    return n


def exec_shop(w, s, _t):
    if s.spawn or not s.alive:
        buy_all(w, s)
        return "done"
    return safe_recall(w, s)


def exec_join(w, s, k):
    b = s.mem[k] if k < 5 else 0
    if (b & 7) == 3:                            # a fight (40_prices JOIN a fight): walk to the ally, then KILL
        p = next((a[1] for a in s.allies if w.ally_slot(a[0]) == k), None)
        if p is None or p.chebyshev_distance(s.pos) <= 2:
            return "done"
        w.step_near(p, 1, s)
        return "going"
    return "failed"


def retreat_now(s):
    """The fallback's retreat condition: enemies within 4 outnumber us + 1 AND my square-law P(lose) > 0.5, or HP <
    the profile / phase `retreat_hp` (default RETREAT_HP) with one there [user plan 15 Oct, ladder 5]."""
    near = [e for e in s.enemies if e[4] <= 4]
    if not near or s.spawn or not flee_ok(s):
        return False
    allies = sum(1 for a in s.allies if a[1].chebyshev_distance(s.pos) <= 4)
    pl = getattr(s, "plose", None)
    if pl is None:
        pl = lanchester(s)
    return (len(near) > allies + 1 and pl > 0.5) or s.hp < ME["prof"].get("retreat_hp", RETREAT_HP) * s.maxhp


def exec_heal(w, s, _t):
    """Recall (safe_recall steps out of camp range / away from enemies first); done on spawn at full HP, or at
    >= 0.9 max HP once arrived. Standing on spawn heals to full at turn end [rules]."""
    if not s.spawn:
        return safe_recall(w, s)
    if s.hp >= s.maxhp or (w.arrived is not None and s.hp >= 0.9 * s.maxhp):
        return "done"
    if w.arrived is None:
        w.arrived = s.r
    w.capt = True                               # healing on spawn: a deliberate stand
    return "going"


def exec_fall(w, s, _t):
    if s.trapped and not flee_ok(s):
        return exec_kill(w, s, int(s.attacker[0]))    # [ladder 5] no flee can end: fight the attacker
    near = [e for e in s.enemies if e[4] <= 4]
    if near and not s.spawn:
        if retreat_now(s):
            if s.near_e <= 3:                   # retreat: out of their reach first, recall once clear
                ne = [e[1] for e in near]
                dash_escape(w, s, ne)
                w.step_away(s, ne)
                return "going"
            return safe_recall(w, s)
    if (s.bag > 0 or s.hp < KEEP_HP * s.maxhp) and not s.spawn:
        return safe_recall(w, s)
    if s.spawn and s.hp < s.maxhp:
        w.capt = True                           # healing on spawn
        return "going"
    if w.bank < len(w.apos):
        w.step_to(f"a{w.bank}", s)
    return "going"


WARD_FAILS = 2              # place_ward failures (False / raise / no placement tile) before the ward is given up


def exec_ward(w, s, j):
    """Walk to within 2 of pending draft ward tile j (goal field "w<j>"), place my ward on the placement tile nearest
    it, done. Unreachable or WARD_FAILS failed placements: tile j dropped from my pending list (traced `ward skip`)."""
    if w.ward_done or j is None or j not in w.ward_pending:
        return "done"
    t = w.wtiles[j]
    key = f"w{j}"
    v = fget(w.goal(key), s.pos)
    if v >= FAR and fget(w.F_me, t) >= FAR:     # FAR on my own tile alone = standing on a camp spawn tile
        w.ward_pending.discard(j)
        trace("ward", f"skip W{j}@{t.x},{t.y} unreachable")
        return "done"
    if v > 0:
        w.step_to(key, s)
        return "going"
    try:
        if w.me.ward_cooldown() > 0:
            return "going"
        ps = (w.me.ward_placement_tiles() & disk(t, 2)).positions()
    except Exception:
        ps = []
    if ps:
        q = min(ps, key=lambda p: p.chebyshev_distance(t))
        try:
            ok = w.me.place_ward(q)
        except Exception as e:
            ok = False
            trace("ward", f"err W{j} {q.x},{q.y} {err_text(e)}")
        if ok:
            w.ward_done = True
            w.ward_pending.discard(j)
            trace("ward", f"place {q.x},{q.y} W{j}@{t.x},{t.y} slot={w.slot} start={w.started}")
            return "done"
    w.ward_fails[j] = w.ward_fails.get(j, 0) + 1
    if w.ward_fails[j] >= WARD_FAILS:
        w.ward_pending.discard(j)
        trace("ward", f"skip W{j}@{t.x},{t.y} failed tiles={len(ps)}")
        return "done"
    return "going"


def scan_goal(w):
    """[SCAN_WARD] the tile my executor is heading for (group anchor, altar, spawn), or None."""
    op, tg = w.cur
    if op == "farm" and tg in w.G:
        return w.G[tg].anchor
    if op in ("bank", "hold") and tg is not None and tg < len(w.apos):
        return w.apos[tg]
    if op in ("shop", "heal"):
        return w.sp0
    return None


def scan_ward(w, s):
    """[B1 SCAN_WARD] P6 foreknowledge, P17 know the ground: after my move, my free ward (cooldown 1 [measured A10],
    one active, re-placed once a round, within 2, sees 6 [rules]) goes on a bush tile within 2 that my own sight does
    not cover. A ward on a bush tile sees its cluster [measured A60]; from outside nobody sees in [rules]. Among those,
    the one nearest my goal tile (none: farthest from spawn). My current ward's tile stays a candidate, so the ward
    moves only when a better tile comes into reach; no unseen bush within 2: it stays where it is. Counts placements
    (w.swn) and enemies first seen through it (trace `sward spot`)."""
    if w.bush is None:
        w.bush = game_map.bushes()
    if w.bush.is_empty():
        return
    me = w.me
    if me.ward_cooldown() > 0:
        return
    p = me.position()
    c = me.ward_placement_tiles() & w.bush
    if not c.is_empty():
        aw = vision.ward_tiles(Team.ALLY)      # an ally's ward tile raises [measured]; my own stays a candidate
        if w.sw_pos is not None:
            aw.set(w.sw_pos, False)
        c = c & ~me.visible_tiles_from(p) & ~aw
    if not c.is_empty():
        gt = scan_goal(w)
        fh = w.F_home
        best, bk = None, None
        for q in c.positions():
            k = (q.chebyshev_distance(gt) if gt is not None else 0, -(fget(fh, q) if fh is not None else 0), q.x, q.y)
            if bk is None or k < bk:
                best, bk = q, k
        if best != w.sw_pos and not int(me.state()) & 6:   # a recall / tribute started this turn: no acting [sdk]
            try:
                ok = me.place_ward(best)
            except Exception as e:
                ok = False
                trace("sward", f"err {best.x},{best.y} {err_text(e)}")
            if ok:
                w.sw_pos = best
                w.swn += 1
    if s.enemies and w.sw_pos is not None:
        sv = me.visible_tiles_from(s.pos)       # my own sight when the enemies were sensed (before my move)
        for e in s.enemies:
            ep, k = e[1], int(e[0])
            if w.bush.is_set(ep) and not sv.is_set(ep):
                if w.sw_seen.get(k, -99) < s.r - 10:    # a new sighting after 10 rounds unseen
                    trace("sward", f"spot e{k} {ep.x},{ep.y} d={e[4]} ward={w.sw_pos.x},{w.sw_pos.y} {w.cur[0]}")
                w.sw_seen[k] = s.r


EXEC = {"farm": exec_farm, "bank": exec_bank, "kill": exec_kill, "hold": exec_hold, "shop": exec_shop,
        "join": exec_join, "fall": exec_fall, "heal": exec_heal, "ward": exec_ward, "hunt": exec_hunt}
