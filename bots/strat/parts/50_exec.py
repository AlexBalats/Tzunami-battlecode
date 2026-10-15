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
        self.lastfarm = tg                      # kill exclusions: this group's monsters are not avoided (camp_zone)
        walk = self.gd.get(tg, 40)
        o = self.G[tg]
        mons = [m for m in (o.hp if o.hp is not None else o.mons) if m[0] > 0]
        k = max(1, o.need)
        work = (clear_dmg(mons, s_eff(self, s, tg, k), k)[0] if mons else 0) + 8
        if o.need >= 2:
            work += 10                          # waiting for the partner (group mode: walking to it)
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


World.set_cur = _set_cur


CLOSE_TTK = 3               # [user plan 15 Oct, ladder 4] close dash only when my hits to kill are <= this
WAIT_CAP = 10               # [guess] rounds of pair waiting before the take fails ("failed partner")
PAIR_NEAR = 6               # [user plan 15 Oct, pair/trio opener; guess] group mode: attack a pair group with an ally this close
GROUP_SEEK_CAP = 15         # [guess] group mode: rounds stepping toward a partner at a group before the take fails
WAIT_EXCL = 30              # [guess] rounds that (farm, group) is excluded after a failed partner wait
RETREAT_HP = 0.6            # [guess] fallback retreats from enemies within 4 below this HP fraction
PEEK_ON = 1                 # [user decision 15 Oct afternoon] dead-camp pickup: step onto a spawn tile of an unseen group at the goal
PEEK_ROUNDS = 3             # ... within 2 of its tiles this many rounds with nothing seen: remembered as a waiting reward
SPLASH_ON = 1               # [user decision 15 Oct] splash champions (profile `splash`): target / walk to the monster with the
                            # most live neighbours within 1 (0: lowest HP in range, the old rule; the `splash` trace stays)
KILL_CAMP_R = -1            # [user decision 15 Oct] kill / hunt never step within this of a live monster of a group I do
                            # not farm (camp_zone); no such path: the kill / hunt fails (-1: off)
                            # [user decision 15 Oct afternoon] off by default (3 blocked most melee kills); code kept


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
        w.recall_r = s.r
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
    """Visible allies within 4 of the group's camps that broadcast farm on it, or join."""
    n = 0
    o = w.G[h]
    for c, p, _hp, _st in s.allies:
        if min(t.chebyshev_distance(p) for t in o.tiles) <= 4:
            k = w.ally_slot(c)
            b = s.mem[k] if k < 5 else 0
            if ((b & 7) == 1 and (b >> 3) == o.mi) or (b & 7) == 6:
                n += 1
    return n


def live_ok(w, s, h, k):
    """k bodies (Strength like mine) clear h with the most-hit body keeping KEEP_HP (live clear model)."""
    o = w.G[h]
    mons = [m for m in (o.hp if o.hp is not None else o.mons) if m[0] > 0]
    if not mons:
        return True
    return clear_dmg(mons, s_eff(w, s, h, k), k)[1] * tank(k) <= s.hp * SURVIVE     # TANK_SHARE


def handoff(w, s, o):
    """[user plan 15 Oct, pair/trio opener] True when I should leave group o's capture to an ally. Candidates: me and
    the visible allies within 4 of the group's spawn tiles that broadcast farm on it or join; the carry is Vesper if
    she is one of them (she took it), else the lowest slot among them. Everyone else leaves (its reward is unsplit)."""
    ks = []
    for c, p, _hp, _st in s.allies:
        k = w.ally_slot(c)
        b = s.mem[k] if k < 5 else 0
        if ((b & 7) == 1 and (b >> 3) == o.mi or (b & 7) == 6) and min(t.chebyshev_distance(p) for t in o.tiles) <= 4:
            ks.append(k)
    if not ks:
        return False
    vs = w.roster.index(VESPER_ID) if VESPER_ID in w.roster else -1
    carry = vs if vs == w.slot or vs in ks else min(ks + [w.slot])
    return carry != w.slot


def group_go(w, s, h, o):
    """[user plan 15 Oct, pair/trio opener] group mode, a pair group I cannot solo, monsters at full HP: None = attack
    now (an ally within PAIR_NEAR of me); else one step toward the nearest visible ally that claims this group, or
    toward spawn (where the partners come from) when none is visible; "failed" when nobody claims it or after
    GROUP_SEEK_CAP such rounds. Never stands still (no waiting share)."""
    if any(p.chebyshev_distance(s.pos) <= PAIR_NEAR for _c, p, _hp, _st in s.allies):
        return None
    cl = [k for k in range(min(5, len(w.roster))) if k != w.slot and (s.mem[k] & 7) == 1 and (s.mem[k] >> 3) == o.mi]
    w.waited += 1
    if not cl or w.waited > GROUP_SEEK_CAP:
        w.excl[("farm", h)] = s.r + WAIT_EXCL
        trace("exec", f"farm {tname(w, 'farm', h)} failed partner seek={w.waited} claims={len(cl)}")
        return "failed"
    vis = sorted((p.chebyshev_distance(s.pos), p.x, p.y) for c, p, _hp, _st in s.allies if w.ally_slot(c) in cl)
    if vis:
        w.step_near(V(vis[0][1], vis[0][2]), 1, s)
    else:
        w.step_to("home", s)
    return "going"


def splash_nb(lv, i):
    """Live monsters of lv (sense entries) other than lv[i] within Chebyshev 1 of it (Varg's splash reach [rules])."""
    p = lv[i][2]
    n = 0
    for j, (_c, hp, q, _st) in enumerate(lv):
        if j != i and hp > 0 and q.chebyshev_distance(p) <= 1:
            n += 1
    return n


def camp_zone(w, s, skip=None):
    """[user decision 15 Oct, kill exclusions] tiles within KILL_CAMP_R of the visible live monsters (s.live) of every
    group but my last farm group (w.lastfarm) and skip; None when there are none (or KILL_CAMP_R < 0)."""
    if KILL_CAMP_R < 0:
        return None
    z = None
    for h, lv in s.live.items():
        if h == w.lastfarm or h == skip:
            continue
        for _c, hp, p, _st in lv:
            if hp > 0:
                if z is None:
                    z = Bitboard()
                z.draw_chebyshev(p, KILL_CAMP_R)
    return z


def exec_farm(w, s, h):
    o = w.G[h]
    lv = s.live.get(h)
    if lv:
        tgt = [(hp, i) for i, (_c, hp, p, _st) in enumerate(lv) if p.chebyshev_distance(s.pos) <= ME.get("range", 1)]
        hurt = any(hp < w.G_maxhp(c) for c, hp, _p, _st in lv)
        sm = stack_mode(w, s.r)
        if sm and o.need >= 2 and not hurt and not live_ok(w, s, h, 1):
            res = group_go(w, s, h, o)          # [user plan 15 Oct, pair/trio opener] no waiting at camps
            if res is not None:
                return res
        elif not sm and o.need >= 2 and not hurt and not live_ok(w, s, h, 1 + partners_near(w, s, h)):
            # pair take: wait (monsters are friendly until hit) near the group for the partner
            near = min(p.chebyshev_distance(s.pos) for _c, _hp, p, _st in lv)
            if near > 4:
                w.step_to(f"g{h}", s)
            else:
                w.waited += 1                   # counts rounds waiting at the group, not walking to it
                if w.waited >= WAIT_CAP:
                    # no partner in WAIT_CAP rounds: give the pair up for WAIT_EXCL rounds and no un-partnered pair
                    # takes for as long (40_prices pair_until), so the next choice is the best solo group
                    w.excl[("farm", h)] = s.r + WAIT_EXCL
                    w.pair_until = max(w.pair_until, s.r + WAIT_EXCL)
                    trace("exec", f"farm {tname(w, 'farm', h)} failed partner waited={w.waited}")
                    return "failed"
            w.waiting = True
            return "going"
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
            try:
                w.me.attack(c)
                w.attacked = True
                w.reset_attack(c, tgt[0][0])
            except Exception:
                pass
            if s.st & 0x800:                     # CAN_CAST
                w.cast(c, True)
            return "going"
        if tgt:
            w.attacked = True                   # in range, attack spent this turn
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
            return "done"
        if o.st == "reward":
            onspawn = any(t == s.pos for t in o.tiles)
            if GROUP_HANDOFF and stack_mode(w, s.r) and handoff(w, s, o):
                # [user plan 15 Oct, pair/trio opener] not the carry: step off the spawn tiles, leave it unsplit
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
            w.kfail[hd] = s.r + KFAIL_ROUNDS    # [bug fix 15 Oct, ladder 4] finishers too; [15 Oct afternoon] 6 rounds
            return "failed"
    else:
        w.kn = 0
    w.kd = dd
    # CLOSE [user plan 15 Oct]: 1-2 tiles beyond range -> dash into range (farthest such tile), then try the attack.
    # [user plan 15 Oct, ladder 4] only onto a target I kill in <= CLOSE_TTK hits, and with enemies within 8 of me
    # <= allies within 8 + 1 (ladder: dashes onto 750-HP targets, 5 hits, with 4 enemies in sight); else walk
    z = camp_zone(w, s) if kz else None         # [user decision 15 Oct] never step within KILL_CAMP_R of other camps
    if rng < dd <= rng + 2 and -(-int(hp) // int(s.S)) <= CLOSE_TTK             and sum(1 for x in s.enemies if x[4] <= 8) <= sum(1 for a in s.allies if a[1].chebyshev_distance(s.pos) <= 8) + 1             and w.dash_to(s, lambda q: -q.chebyshev_distance(p) if q.chebyshev_distance(p) <= rng and (z is None or not z.is_set(q)) else None, "close"):
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
    if w.step_near(p, rng, s, z) == "nopath":
        w.kfail[hd] = s.r + KFAIL_ROUNDS
        trace("exec", f"kill {hd} failed camp tp={p.x},{p.y}")
        return "failed"
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
    z = camp_zone(w, s, a - 100 if a >= 100 else None)     # [user decision 15 Oct] kill exclusions (target group exempt)
    if z is None:
        w.step_to(key, s)
    elif w.step_avoid(key, s, z) == "nopath":
        trace("exec", f"hunt {tname(w, 'hunt', a)} failed camp")
        return "failed"
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
    if (b & 7) != 1 or (b >> 3) not in w.idx:
        return "failed"
    h = w.idx[b >> 3]
    if min(t.chebyshev_distance(s.pos) for t in w.G[h].tiles) <= 4:
        return "done"
    w.step_to(f"g{h}", s)
    return "going"


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
                dash_escape(w, s, [e[1] for e in near])
                w.step_away(s, [e[1] for e in near])
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


EXEC = {"farm": exec_farm, "bank": exec_bank, "kill": exec_kill, "hold": exec_hold, "shop": exec_shop,
        "join": exec_join, "fall": exec_fall, "heal": exec_heal, "ward": exec_ward, "hunt": exec_hunt}
