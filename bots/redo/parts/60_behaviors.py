"""Behaviors (03_ARCHITECTURE.md section 2.2): one singleton per kind. enter(w, s, tg) resets the Behavior's own state
and returns (walk, work), the estimates behind the deadline (World.start: started + min(walk, 150) + 10 + work);
execute(w, s, tg) does one turn of work -> "going" | "done" | "failed" (None: nothing to execute, the loop stops);
progress(w, s, hit) is the sunk-progress value in [0, 1] (prog_update); seeking() tells the stall guard a pair seek
moved this turn. The frame (cur, started, status, deadline, prog, pbest, pstall, d0, hit) lives on w, reset by
World.start; so do the per-turn flags attacked, capt, waiting. A timeout or a failure excludes (option, target)
for EXCL rounds (90_main). After the loop, the scan ward (ScanWard.post) re-places my free ward.
"""

CLOSE_TTK = 3               # [user plan 15 Oct, ladder 4] close dash only when my hits to kill are <= this (ranged)
CLOSE_TTK_MELEE = 6         # [user decision 15 Oct night] melee dashers (Vale): ladder showed 0 close dashes in 5 games with 3
WAIT_CAP = 10               # [guess] rounds of pair waiting before the take fails ("failed partner")
PAIR_NEAR = 6               # [user plan 15 Oct, pair/trio opener; guess] group mode: attack a pair group with an ally this close
GROUP_SEEK_CAP = 15         # [guess] group mode: rounds stepping toward a partner at a group before the take fails
WAIT_EXCL = 30              # [guess] rounds that (farm, group) is excluded after a failed partner wait
RETREAT_HP = 0.6            # [guess] fallback retreats from enemies within 4 below this HP fraction
PEEK_ROUNDS = 3             # [user decision 15 Oct afternoon] dead-camp pickup (Farm): this many rounds within 2 of an
                            # unseen group's tiles with nothing seen -> remembered as a waiting reward
RECALL_DASH = 2             # 08 F4 (M4): an enemy's dash, counted for every enemy (cooldowns unread, P-h)
UHIT_ROUNDS = 2             # 08 F4 (P-a): no recall this many rounds after a hit by nobody visible (a bush)


# ---- shared helpers ----
def in_camp_range(s, w):
    pts = []
    for h, lv in s.live.items():
        for c, _hp, p, st in lv:
            if st > 0 and p.chebyshev_distance(s.pos) <= crng(c):
                pts.append(p)
    return pts


def safe_recall(w, s):
    """Recall only when clear [rules: damage or stun breaks it]: never start or keep one while an enemy could reach me
    before it ends (08 F4, M4: within its range + my recall turns + RECALL_DASH), within UHIT_ROUNDS of a hit by
    nobody visible, or with a live camp in range. Not clear: cancel a running recall, then step away from the
    enemies towards home or out of camp range (Nav.away). P9: a recall in reach is a free turn for them (M6)."""
    rt = ME.get("recall", 5) + RECALL_DASH
    ne = [e[1] for e in s.enemies if e[4] <= arng(e[0]) + rt]
    if not ne and s.r - getattr(w, "uhit", -99) <= UHIT_ROUNDS:
        if s.recalling:
            try:
                w.me.cancel_recall()
                st = int(w.me.state())
                s.recalling, s.can_move, s.can_attack = bool(st & 2), bool(st & 8), bool(st & 16)
            except Exception as e:
                trace("exec", "cancel_recall " + err_text(e))
                return "going"
        w.nav.step(s, "home")
        return "going"
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
        w.nav.escape(s, ne)
        if w.nav.away(s, ne) == "blocked":
            w.nav.step(s, "home")
        return "going"
    if pts:
        w.nav.away(s, pts)
        return "going"
    try:
        w.me.recall()
    except Exception:
        w.nav.step(s, "home")
    return "going"


def partners_near(w, s, h):
    """Visible allies within 4 of the group's camps that broadcast farm on it, or join."""
    n = 0
    o = w.G[h]
    for c, p, _hp, _st in s.allies:
        if min(t.chebyshev_distance(p) for t in o.tiles) <= 4:
            k = w.ally_slot(c)
            op, t = s.slots[k] if k < 5 else (0, 0)
            if (op == 1 and t == o.mi) or op == 6:
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
    """06 section 1.2: True when I should leave group o's capture to an ally. Candidates: me and the visible allies
    within 4 of the group's spawn tiles that broadcast farm on it or join; the capturer is the main carry if she is
    one of them, else the second, else the lowest slot among them. Everyone else leaves: the reward is unsplit (an
    emblem only pays once whole, 06 section 1.1) and the others start the next walk 5 rounds sooner."""
    ks = []
    for c, p, _hp, _st in s.allies:
        k = w.ally_slot(c)
        op, t = s.slots[k] if k < 5 else (0, 0)
        if (op == 1 and t == o.mi or op == 6) and min(t.chebyshev_distance(p) for t in o.tiles) <= 4:
            ks.append(k)
    if not ks:
        return False
    ks.append(w.slot)
    carry = w.main if w.main in ks else w.second if w.second in ks else min(ks)
    return carry != w.slot


def splash_nb(lv, i):
    """Live monsters of lv (sense entries) other than lv[i] within Chebyshev 1 of it (Varg's splash reach [rules])."""
    p = lv[i][2]
    n = 0
    for j, (_c, hp, q, _st) in enumerate(lv):
        if j != i and hp > 0 and q.chebyshev_distance(p) <= 1:
            n += 1
    return n


def find_enemy(s, hd):
    for e in s.enemies:
        if int(e[0]) == hd:
            return e
    return None


def retreat_now(s):
    """The fallback's retreat condition: enemies within 4 outnumber us + 1 AND my square-law P(lose) > 0.5, or HP <
    the profile / phase `retreat_hp` (default RETREAT_HP) with one there [user plan 15 Oct, ladder 5]. P(lose): duel."""
    near = [e for e in s.enemies if e[4] <= 4]
    if not near or s.spawn or not flee_ok(s):
        return False
    allies = sum(1 for a in s.allies if a[1].chebyshev_distance(s.pos) <= 4)
    pl = getattr(s, "plose", 0.0)
    return (len(near) > allies + 1 and pl > 0.5) or s.hp < ME["prof"].get("retreat_hp", RETREAT_HP) * s.maxhp


# ---- the Behaviors ----
class Behavior:
    """Base, and the idle Behavior (before the first choice). code: the 3-bit slot code (40_comms)."""
    __slots__ = ()
    name, code = "idle", 0

    def enter(self, w, s, tg):
        return 0, 0

    def execute(self, w, s, tg):
        return None

    def target(self, w, s, tg):
        """The tile the walk fraction measures to (None: no walk target)."""
        return None

    def walkf(self, w, s):
        """Walk fraction to target(): 1 - distance / distance at the first look (w.d0, set lazily)."""
        tg = w.cur[1]
        t = None if tg is None else self.target(w, s, tg)
        if t is None:
            return 0.0
        d = t.chebyshev_distance(s.pos)
        if w.d0 is None:
            w.d0 = d
        return 1.0 - d / w.d0 if w.d0 > 0 else 1.0

    def progress(self, w, s, hit):
        return 0.0

    def seeking(self):
        return False

    def target_bits(self, w, tg):
        return 0 if tg is None else int(tg) & 31


class Farm(Behavior):
    """Walk to the group, take it (pair waits, group seeks, Varg's splash, the turn's cast), capture, pick up a
    dead camp's waiting reward. Long-lived: the farm target history and flip lock (fh, flips, tflip), pair_until."""
    __slots__ = ("waited", "pw", "peekn", "peeked", "hp0", "lastbag", "lastgold", "fh", "flips", "tflip", "pair_until")
    name, code = "farm", 1

    def __init__(self):
        self.waited = self.pw = self.peekn = 0
        self.peeked = False
        self.hp0 = None
        self.lastbag = self.lastgold = 0
        self.fh, self.flips, self.tflip, self.pair_until = [], 0, None, 0

    def enter(self, w, s, tg):
        self.waited = self.pw = self.peekn = 0
        self.peeked = False                     # dead-camp pickup: rounds near the group seeing nothing
        self.lastbag, self.lastgold = s.bag, s.gold
        self.hp0 = None
        if tg not in w.G:
            return 0, 0
        r = s.r
        # [user decision 15 Oct afternoon, ladder cd737718] backstop: farm target A -> B -> A within FLIP_WINDOW rounds
        # locks A (B excluded FLIP_LOCK rounds); 90_main's osc detector traces the flip
        fh = self.fh = (self.fh + [(r, tg)])[-3:]
        if len(fh) == 3 and fh[0][1] == tg != fh[1][1] and r - fh[0][0] <= FLIP_WINDOW:
            w.excl[("farm", fh[1][1])] = r + FLIP_LOCK
            self.flips += 1
            self.tflip = (fh[1][1], tg)
            trace("choice", f"flip lock {tname(w, 'farm', tg)} excl={tname(w, 'farm', fh[1][1])} in={r - fh[0][0]}")
            self.fh = []
        walk = w.nav.gd.get(tg, 40)
        o = w.G[tg]
        mons = [m for m in (o.hp if o.hp is not None else o.mons) if m[0] > 0]
        k = max(1, o.need)
        work = (clear_dmg(mons, s_eff(w, s, tg, k), k)[0] if mons else 0) + 8
        if o.need >= 2:
            work += 10                          # waiting for the partner (group mode: walking to it)
        self.hp0 = sum(m[0] for m in mons) if o.st == "alive" else 0.0
        return walk, work

    def target(self, w, s, tg):
        return w.G[tg].anchor if tg in w.G else None

    def progress(self, w, s, hit):
        """walk x 0.5 before my first hit, then 0.5 + 0.5 x group HP removed / group HP at the first hit."""
        wf = self.walkf(w, s)
        tg = w.cur[1]
        if tg not in w.G:
            return wf
        o = w.G[tg]
        lv = s.live.get(tg)
        if lv:
            ghp = sum(max(0.0, hp) for _c, hp, _p, _st in lv)
        else:
            ghp = sum(m[0] for m in (o.hp if o.hp is not None else o.mons) if m[0] > 0) if o.st == "alive" else 0.0
        if not w.hit:
            self.hp0 = ghp                      # the latest group HP seen before my first hit
            p = 0.5 * wf
        else:
            p = 0.5 + 0.5 * (1.0 - ghp / self.hp0) if self.hp0 else 1.0
        if self.hp0 is not None and self.hp0 <= 0 and not w.hit:
            p = wf                              # a cleared group: the walk (then the capture) is the job
        return p

    def seeking(self):
        """A pair seek (group_go) or a pair wait counted a round since the last look: not a stall."""
        sk = self.waited != self.pw
        self.pw = self.waited
        return sk

    def target_bits(self, w, tg):
        if tg is None:
            return 0
        return w.G[tg].mi if tg in w.G else 31

    def group_go(self, w, s, h, o):
        """[user plan 15 Oct, pair/trio opener] group mode, a pair group I cannot solo, monsters at full HP: None =
        attack now (an ally within PAIR_NEAR of me); else one step toward the nearest visible ally that claims this
        group, or toward spawn (where the partners come from) when none is visible; "failed" when nobody claims it or
        after GROUP_SEEK_CAP such rounds. Never stands still (no waiting share)."""
        if any(p.chebyshev_distance(s.pos) <= PAIR_NEAR for _c, p, _hp, _st in s.allies):
            return None
        cl = [k for k in range(min(5, len(w.roster))) if k != w.slot and s.slots[k] == (1, o.mi)]
        self.waited += 1
        if not cl or self.waited > GROUP_SEEK_CAP:
            w.excl[("farm", h)] = s.r + WAIT_EXCL
            trace("exec", f"farm {tname(w, 'farm', h)} failed partner seek={self.waited} claims={len(cl)}")
            return "failed"
        vis = sorted((p.chebyshev_distance(s.pos), p.x, p.y) for c, p, _hp, _st in s.allies if w.ally_slot(c) in cl)
        if vis:
            w.nav.near(s, V(vis[0][1], vis[0][2]), 1)
        else:
            w.nav.step(s, "home", "fast")
        return "going"

    def execute(self, w, s, h):
        o = w.G[h]
        lv = s.live.get(h)
        if lv:
            tgt = [(hp, i) for i, (_c, hp, p, _st) in enumerate(lv) if p.chebyshev_distance(s.pos) <= ME.get("range", 1)]
            hurt = any(hp < w.G_maxhp(c) for c, hp, _p, _st in lv)
            sm = stack_mode(w, s.r)
            if sm and o.need >= 2 and not hurt and not live_ok(w, s, h, 1):
                res = self.group_go(w, s, h, o)     # [user plan 15 Oct, pair/trio opener] no waiting at camps
                if res is not None:
                    return res
            elif not sm and o.need >= 2 and not hurt and not live_ok(w, s, h, 1 + partners_near(w, s, h)):
                # pair take: wait (monsters are friendly until hit) near the group for the partner
                near = min(p.chebyshev_distance(s.pos) for _c, _hp, p, _st in lv)
                if near > 4:
                    w.nav.step(s, f"g{h}", "fast")
                else:
                    self.waited += 1            # counts rounds waiting at the group, not walking to it
                    if self.waited >= WAIT_CAP:
                        # no partner in WAIT_CAP rounds: give the pair up for WAIT_EXCL rounds and no un-partnered pair
                        # takes for as long (50_prices pair_until), so the next choice is the best solo group
                        w.excl[("farm", h)] = s.r + WAIT_EXCL
                        self.pair_until = max(self.pair_until, s.r + WAIT_EXCL)
                        trace("exec", f"farm {tname(w, 'farm', h)} failed partner waited={self.waited}")
                        return "failed"
                w.waiting = True
                return "going"
            spl = ME["prof"].get("splash")
            if spl and not hurt and len(lv) >= 2:
                # [user decision 15 Oct, Varg's splash] before the first hit: stand next to the monster with the most
                # live neighbours within 1 when no monster in range has as many
                nb = [(splash_nb(lv, i), -hp, i) for i, (_c, hp, _p, _st) in enumerate(lv) if hp > 0]
                if nb:
                    bn = max(nb)
                    inr = max((splash_nb(lv, i) for _hp, i in tgt), default=-1)
                    if bn[0] > inr and bn[0] >= 1 and w.nav.near(s, lv[bn[2]][2], ME.get("range", 1), skip=h) == "moved":
                        return "going"
            if tgt and s.can_attack:
                if spl:
                    tgt = [(-splash_nb(lv, i), hp, i) for hp, i in tgt]    # most neighbours, then lowest HP
                    tgt.sort()
                    tgt = [(hp, i) for _n, hp, i in tgt]
                else:
                    tgt.sort()
                c = lv[tgt[0][1]][0]
                if spl and TRACE:
                    trace("splash", f"nb={splash_nb(lv, tgt[0][1])} live={sum(1 for x in lv if x[1] > 0)} hp={tgt[0][0]:.0f} g{h}")
                alts = [lv[i][0] for _hp, i in tgt[1:]]
                kit = s.st & 0x800 and (w.kit.shield(s, False, c) or w.kit.stun(s, h, c, w.nav.moved))  # [K1] the turn's cast
                try:
                    w.me.attack(c)
                    w.attacked = True
                    if not kit:
                        w.kit.reset_attack(c, tgt[0][0], alts)
                except Exception:
                    pass
                if s.st & 0x800 and not kit:     # CAN_CAST
                    if _dead(c):
                        c = next((u for u in alts if not _dead(u)), c)     # [K1] not on the monster my hits just killed
                    w.kit.cast(c, True)
                return "going"
            if tgt:
                w.attacked = True               # in range, attack spent this turn
                return "going"
            if hurt:
                # [_dev-strat, 17 Oct] the take is under way: towards a free tile in range of a live monster (no dead camp's tile)
                live = [p for _c, hp, p, _st in lv if hp > 0]
                if live and min(p.chebyshev_distance(s.pos) for p in live) <= 6:
                    w.nav.near(s, live, ME.get("range", 1), skip=h)
                    return "going"
            if len(lv) < len(o.tiles) and w.nav.walk_to(f"g{h}", s.pos) == 0:
                w.nav.near(s, [p for _c, _hp, p, _st in lv], ME.get("range", 1), skip=h)    # next to a dead camp only
            else:
                w.nav.step(s, f"g{h}", "fast")
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
                leave = handoff(w, s, o)        # 06 section 1.2: one body captures (the carry if there), the rest walk on
                if leave:
                    # [user plan 15 Oct, pair/trio opener] not the carry: step off the spawn tiles, leave it unsplit
                    if onspawn:
                        w.nav.away(s, o.tiles, 1)
                    o.st, o.until = "resp", s.r + o.resp
                    w.excl[("farm", h)] = s.r + EXCL        # update_groups re-reads "reward" while it is visible
                    trace("exec", f"farm {tname(w, 'farm', h)} handoff bag={s.bag} gold={s.gold}")
                    return "done"
                if onspawn:
                    w.capt = True
                    if s.bag > self.lastbag or s.gold > self.lastgold:
                        o.st, o.until = "resp", s.r + o.resp
                        return "done"
                    return "going"
                if w.nav.step(s, f"c{h}", "fast") == "blocked" and s.can_move:
                    w.nav.near(s, o.anchor, 0, skip=h)
                return "going"
        if s.bag > self.lastbag and w.capt:
            o.st, o.until = "resp", s.r + o.resp
            return "done"
        if o.st == "reward":
            # memory says cleared (seen, or aged below): the capture tile shows the cluster on arrival (reward branch above)
            if w.nav.step(s, f"c{h}", "fast") == "blocked" and s.can_move:
                w.nav.near(s, o.tiles, 0, skip=h)
            return "going"
        dm = min(t.chebyshev_distance(s.pos) for t in o.tiles)
        if not vis and dm <= max(1, ME.get("range", 1)):
            # [user decision 15 Oct afternoon, ladder cd737718: Varg and Ryth priced two cleared camps as alive for 900
            # rounds from the ring around a bush cluster] at the goal, nothing of the group seen: step onto its nearest
            # spawn tile (inside the bush the cluster is visible; a failed step onto an occupied tile reveals it [rules])
            if dm <= 2:
                self.peekn += 1
                if self.peekn >= PEEK_ROUNDS and o.st == "alive":
                    o.st = "reward"             # memory ageing: priced / executed as a waiting reward (capture branch)
                    trace("exec", f"farm {tname(w, 'farm', h)} aged reward n={self.peekn}")
            if not self.peeked:
                self.peeked = True
                trace("exec", f"farm {tname(w, 'farm', h)} peek d={dm} st={o.st}")
            if dm > 0:
                w.nav.near(s, o.tiles, 0, skip=h)
            return "going"
        w.nav.step(s, f"g{h}", "fast")
        return "going"


class Bank(Behavior):
    """Walk to the altar's ring, tribute (channel ceil(bag / 10) turns [rules])."""
    __slots__ = ("chan", "chanlen")
    name, code = "bank", 2

    def __init__(self):
        self.chan, self.chanlen = 0, 1

    def enter(self, w, s, tg):
        self.chan, self.chanlen = 0, 1
        if tg is not None and tg < len(w.nav.ad):
            return w.nav.ad[tg], max(1, -(-s.bag // 10)) + 2
        return 0, 0

    def target(self, w, s, tg):
        return w.apos[tg] if tg < len(w.apos) else None

    def progress(self, w, s, hit):
        """walk x 0.5, then 0.5 + 0.5 x channel turns / ceil(bag / 10)."""
        wf = self.walkf(w, s)
        if s.submitting:
            if self.chan == 0:
                self.chanlen = max(1, -(-s.bag // 10))
            self.chan += 1
            return 0.5 + 0.5 * self.chan / self.chanlen
        return 0.5 * wf

    def execute(self, w, s, a):
        if s.submitting:
            return "going"
        if s.bag == 0:
            return "done"
        ap = w.apos[a]
        if s.pos.chebyshev_distance(ap) <= 1:
            if s.near_e <= 3 and s.bag > 10:
                return "failed"                 # [tuned] no multi-turn channel next to an enemy (8 bank deaths)
            try:
                w.me.submit_gems(ap)
                return "going"
            except Exception:
                return "failed"
        if w.nav.step(s, f"a{a}", "fast") == "blocked" and (w.nav.walk_to(f"a{a}", s.pos) or FAR) >= FAR:
            return "failed"
        return "going"


class Kill(Behavior):
    """Chase and hit one enemy (CLOSE dash into range). Long-lived: the failed-chase bans (kfail, read by KILL's
    price) and the consecutive-failure counts (kfn)."""
    __slots__ = ("kd", "kn", "khits", "ttk0", "kfail", "kfn")
    name, code = "kill", 3

    def __init__(self):
        self.kd, self.kn, self.khits, self.ttk0 = 99, 0, 0, None
        self.kfail, self.kfn = {}, {}           # enemy handle -> round a chased-out kill stays excluded to; consecutive fails

    def enter(self, w, s, tg):
        self.kd, self.kn, self.khits, self.ttk0 = 99, 0, 0, None
        e = find_enemy(s, tg)
        if e is not None:
            self.ttk0 = max(1, -(-int(e[2]) // int(s.S)))
        return 6 + ME["prof"].get("hunt", 0), 0

    def target(self, w, s, tg):
        e = find_enemy(s, tg)
        return e[1] if e is not None else None

    def progress(self, w, s, hit):
        """hits / ttk (walk without a ttk)."""
        wf = self.walkf(w, s)
        if hit:
            self.khits += 1
        return self.khits / self.ttk0 if self.ttk0 else wf

    def ban(self, hd, r):
        """Ban target hd after a failed chase: KFAIL_ROUNDS x 2^(consecutive failures - 1), capped KFAIL_MAX; a landed
        hit resets."""
        n = self.kfn.get(hd, 0) + 1
        self.kfn[hd] = n
        self.kfail[hd] = r + min(KFAIL_MAX, KFAIL_ROUNDS * (1 << (n - 1)))
        if n > 1:
            trace("exec", f"kill {hd} ban x{n} until r{self.kfail[hd]}")

    def execute(self, w, s, hd):
        return self.fight(w, s, hd, self, True)

    def fight(self, w, s, hd, st, kz):
        """One kill step on enemy hd. st holds the chase counters (kd, kn): mine, or Fall's for its trapped fight.
        kz: a chosen kill (the espawn exclusion applies), not Fall's trapped fight."""
        e = find_enemy(s, hd)
        if e is None:
            return "failed"
        c, p, hp, _b, dd, _st = e
        if hp <= 0:
            return "done"
        if kz and near_espawn(w, p):
            self.kfail[hd] = s.r + EXCL         # [user decision 15 Oct] the target reached their spawn: heals to full
            trace("exec", f"kill {hd} failed espawn tp={p.x},{p.y}")
            return "failed"
        rng = ME.get("range", 1)
        if dd <= rng:
            w.attacked = True
            if s.can_attack:
                try:
                    w.me.attack(c)
                    self.kfn[hd] = 0            # a landed hit resets the failure backoff
                    w.kit.reset_attack(c, hp)
                except Exception:
                    pass
            if s.st & 0x800:
                w.kit.cast(c, False)
            return "going"
        if dd >= st.kd:
            st.kn += 1
            ttk = -(-int(hp) // int(s.S))
            # a finisher chase gets 2 ttk + 2 rounds (pinned / 1 tile/turn); else the phase's `chase` (default 3)
            if st.kn >= (2 * ttk + 2 if ttk <= 2 else ME["prof"].get("chase", 3)):
                self.ban(hd, s.r)               # [bug fix 15 Oct, ladder 4] finishers too; [15 Oct afternoon] 6 rounds; [night] backoff
                return "failed"
        else:
            st.kn = 0
        st.kd = dd
        # CLOSE [user plan 15 Oct]: 1-2 tiles beyond range -> dash into range (farthest such tile), then try the attack.
        # [user plan 15 Oct, ladder 4] only onto a target I kill in <= CLOSE_TTK hits, and with enemies within 8 of me
        # <= allies within 8 + 1 (ladder: dashes onto 750-HP targets, 5 hits, with 4 enemies in sight); else walk
        if rng < dd <= rng + 2 and -(-int(hp) // int(s.S)) <= (CLOSE_TTK_MELEE if rng <= 1 else CLOSE_TTK) \
                and sum(1 for x in s.enemies if x[4] <= 8) <= sum(1 for a in s.allies if a[1].chebyshev_distance(s.pos) <= 8) + 1 \
                and w.nav.dash_to(s, lambda q: -q.chebyshev_distance(p) if q.chebyshev_distance(p) <= rng else None, "close"):
            res = "no-attack"
            try:
                w.me.attack(c)
                w.attacked, res = True, f"attacked hp {hp:.0f}->{_uhp(c)}"
            except Exception as ex:
                res = "raise " + err_text(ex)[:60]
            trace("dash", f"close then {res} ttk={-(-int(hp) // int(s.S))}")
            return "going"
        if s.st & 0x800:
            w.kit.cast(c, False)                # dashes and ranged spells close the gap
        w.nav.near(s, p, rng, "fight")
        return "going"


class Hunt(Behavior):
    """Walk toward a sighting's altar, or patrol (target 100 + group: an enemy-side group). Long-lived: hvis, the
    round I reached each patrol altar / group (read by HUNT's price)."""
    __slots__ = ("hvis",)
    name, code = "hunt", 3                      # broadcast as kill with target 31

    def __init__(self):
        self.hvis = {}

    def enter(self, w, s, tg):
        return HUNT_MAX, 0

    def target(self, w, s, tg):
        return w.G[tg - 100].anchor if tg >= 100 else (w.apos[tg] if tg < len(w.apos) else None)

    def progress(self, w, s, hit):
        return self.walkf(w, s)

    def target_bits(self, w, tg):
        return 31

    def execute(self, w, s, a):
        """Done once an enemy is visible (KILL prices it); failed (excluded EXCL rounds) on arrival with nobody there
        or after HUNT_MAX rounds."""
        if s.enemies:
            return "done"
        key, t = (f"g{a - 100}", w.G[a - 100].anchor) if a >= 100 else (f"a{a}", w.apos[a])
        if s.pos.chebyshev_distance(t) <= 2 and (a >= 100 or w.aside[a] == 2):
            self.hvis[a] = s.r                  # patrol arrival: recorded, done (HUNT_REVISIT); the loop in 90_main
            trace("patrol", f"visit {'g' + str(a - 100) if a >= 100 else 'A' + str(a)}")    # re-chooses this turn: next altar
            return "done"
        if s.r - w.started >= HUNT_MAX or s.pos.chebyshev_distance(t) <= 2:
            return "failed"
        w.nav.step(s, key, "fast")
        return "going"


class Hold(Behavior):
    """Stand next to an altar 30 rounds; hit (and stun) an enemy channelling there."""
    __slots__ = ("arrived",)
    name, code = "hold", 4

    def __init__(self):
        self.arrived = None

    def enter(self, w, s, tg):
        self.arrived = None
        if tg is not None and tg < len(w.nav.ad):
            return w.nav.ad[tg], 30
        return 0, 0

    def execute(self, w, s, a):
        ap = w.apos[a]
        if s.pos.chebyshev_distance(ap) > 1:
            w.nav.step(s, f"a{a}")
            return "going"
        if self.arrived is None:
            self.arrived = s.r
        w.capt = True                           # deliberate stand
        for c, p, hp, _b, dd, _st in s.enemies:
            try:
                chan = c.is_submitting_gems()
            except Exception:
                chan = False
            if chan:
                if s.st & 0x800:
                    for ab, _oc, _oe, cc, _rs, _g in w.kit.ab:
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
        return "done" if s.r - self.arrived >= 30 else "going"


class Shop(Behavior):
    """Recall (safe_recall), buy on spawn."""
    __slots__ = ()
    name, code = "shop", 5

    def enter(self, w, s, tg):
        return 0, 8

    def execute(self, w, s, _t):
        if s.spawn or not s.alive:
            buy_all(w, s)
            return "done"
        return safe_recall(w, s)


class Join(Behavior):
    """Walk to an ally's farm (it broadcasts farm) or fight (it broadcasts kill); target = the ally's slot."""
    __slots__ = ()
    name, code = "join", 6

    def enter(self, w, s, tg):
        return (20, 0) if tg is not None else (0, 0)

    def target(self, w, s, tg):
        op, t = s.slots[tg] if tg < 5 else (0, 0)
        if op == 3:
            return next((a[1] for a in s.allies if w.ally_slot(a[0]) == tg), None)
        if op == 1 and t in w.idx:
            return w.G[w.idx[t]].anchor
        return None

    def progress(self, w, s, hit):
        return self.walkf(w, s)

    def execute(self, w, s, k):
        op, t = s.slots[k] if k < 5 else (0, 0)
        if op == 3:                             # a fight (50_prices JOIN a fight): walk to the ally, then KILL
            p = next((a[1] for a in s.allies if w.ally_slot(a[0]) == k), None)
            if p is None or p.chebyshev_distance(s.pos) <= 2:
                return "done"
            w.nav.near(s, p, 1)
            return "going"
        if op != 1 or t not in w.idx:
            return "failed"
        h = w.idx[t]
        if min(t.chebyshev_distance(s.pos) for t in w.G[h].tiles) <= 4:
            return "done"
        w.nav.step(s, f"g{h}")
        return "going"


class Heal(Behavior):
    """Recall (safe_recall steps out of camp range / away from enemies first); done on spawn at full HP, or at >= 0.9
    max HP once arrived. Standing on spawn heals to full at turn end [rules]."""
    __slots__ = ("arrived",)
    name, code = "heal", 0                      # broadcast as idle: the byte has no free code (7 is dead)

    def __init__(self):
        self.arrived = None

    def enter(self, w, s, tg):
        self.arrived = None
        return 10, 7                            # step out of reach, 5-turn recall, the heal turn on spawn

    def execute(self, w, s, _t):
        if not s.spawn:
            return safe_recall(w, s)
        if s.hp >= s.maxhp or (self.arrived is not None and s.hp >= 0.9 * s.maxhp):
            return "done"
        if self.arrived is None:
            self.arrived = s.r
        w.capt = True                           # healing on spawn: a deliberate stand
        return "going"


class Fall(Behavior):
    """Nothing priced above 0: fight the attacker when no flee can end (Kill.fight with my own chase counters),
    retreat, recall a bag or low HP, heal on spawn, else walk to the bank altar."""
    __slots__ = ("kd", "kn")
    name, code = "fall", 0                      # broadcast as idle, target 0 (was 8: overflowed into the target bits, 04_COMMS.md section 2)

    def __init__(self):
        self.kd, self.kn = 99, 0

    def enter(self, w, s, tg):
        self.kd, self.kn = 99, 0
        return 15, 0

    def execute(self, w, s, _t):
        if s.trapped and not flee_ok(s):
            return KILL.fight(w, s, int(s.attacker[0]), self, False)    # [ladder 5] no flee can end: fight the attacker
        near = [e for e in s.enemies if e[4] <= 4]
        if near and not s.spawn:
            if retreat_now(s):
                if s.near_e <= 3:               # retreat: out of their reach first, recall once clear
                    w.nav.escape(s, [e[1] for e in near])
                    w.nav.away(s, [e[1] for e in near])
                    return "going"
                return safe_recall(w, s)
        if (s.bag > 0 or s.hp < KEEP_HP * s.maxhp) and not s.spawn:
            return safe_recall(w, s)
        if s.spawn and s.hp < s.maxhp:
            w.capt = True                       # healing on spawn
            return "going"
        if w.bank < len(w.apos) and w.altar_open(w.bank):     # X8: never walk at a gated altar (Nav cannot reach it)
            w.nav.step(s, f"a{w.bank}")
        return "going"


class Dead(Behavior):
    """Out for 60 rounds [rules]: the dead gate in 90_main shops and broadcasts code 7."""
    __slots__ = ()
    name, code = "dead", 7


FARM, BANK, KILL, HUNT, HOLD, SHOP, JOIN, HEAL, FALL, DEAD = (Farm(), Bank(), Kill(), Hunt(), Hold(), Shop(), Join(),
                                                              Heal(), Fall(), Dead())
BEH = {b.name: b for b in (Behavior(), FARM, BANK, KILL, HUNT, HOLD, SHOP, JOIN, HEAL, FALL, DEAD)}


def prog_update(w, s, hit):
    """[IMPROVEMENTS 2, 15 Oct night] w.prog in [0, 1] for the current choice (Behavior.progress, from values already
    at hand: chebyshev to the target, s.live / o.hp, s.submitting, last turn's attack); join, hunt = walk; shop,
    heal, fall, hold = 0. pbest / pstall: the best so far and the rounds since it rose."""
    w.prog = min(1.0, max(0.0, BEH[w.cur[0]].progress(w, s, hit)))
    if w.prog > w.pbest + 1e-6:
        w.pbest, w.pstall = w.prog, 0
    else:
        w.pstall += 1


# ---- post pass ----
class ScanWard:
    """[B1 SCAN_WARD] P6 foreknowledge, P17 know the ground: after my move, my free ward (cooldown 10 [sdk 3.0.1
    WARD_COOLDOWN; was 1], one active, within 2, sees 6 [rules]) goes on a bush tile within 2 that my own sight does
    not cover. X3: the ward costs no gold, so cooldown 10 only caps it at one placement per 10 rounds; the goal-nearest
    rule below already places it ahead of me, where it stays useful while the cooldown runs. A ward on a bush tile sees its cluster [measured A60]; from outside nobody sees in [rules]. Among those,
    the one nearest my goal tile (none: farthest from spawn). My current ward's tile stays a candidate, so the ward
    moves only when a better tile comes into reach; no unseen bush within 2: it stays where it is. Counts placements
    (n) and enemies first seen through it (trace `sward spot`)."""
    __slots__ = ("bush", "pos", "n", "seen")

    def __init__(self):
        self.bush, self.pos, self.n, self.seen = None, None, 0, {}   # bush tiles, my ward, placements, enemy -> round seen

    @staticmethod
    def goal(w):
        """The tile my Behavior is heading for (group anchor, altar, spawn), or None."""
        op, tg = w.cur
        if op == "farm" and tg in w.G:
            return w.G[tg].anchor
        if op in ("bank", "hold") and tg is not None and tg < len(w.apos):
            return w.apos[tg]
        if op in ("shop", "heal"):
            return w.sp0
        return None

    def post(self, w, s):
        if self.bush is None:
            self.bush = game_map.bushes()
        if self.bush.is_empty():
            return
        me = w.me
        st = int(me.state())
        if not st & 1:
            return          # 08 G3: this turn rolled over into the round I died: position() is (-1, -1), the SDK raises
        if me.ward_cooldown() > 0:
            return
        p = me.position()
        c = me.ward_placement_tiles() & self.bush
        if not c.is_empty():
            aw = vision.ward_tiles(Team.ALLY)  # an ally's ward tile raises [measured]; my own stays a candidate
            if self.pos is not None:
                aw.set(self.pos, False)
            c = c & ~me.visible_tiles_from(p) & ~aw
        if not c.is_empty():
            gt = self.goal(w)
            fh = w.nav.F_home
            best, bk = None, None
            for q in c.positions():
                k = (q.chebyshev_distance(gt) if gt is not None else 0, -(fget(fh, q) if fh is not None else 0), q.x, q.y)
                if bk is None or k < bk:
                    best, bk = q, k
            # a recall / tribute started this turn: no acting [sdk]; 08 G3: stunned raises "cannot act" [measured]
            if best != self.pos and not st & 6 and not me.buffs().has_stun():
                try:
                    ok = me.place_ward(best)
                except Exception as e:
                    ok = False
                    trace("sward", f"err {best.x},{best.y} {err_text(e)}")
                if ok:
                    self.pos = best
                    self.n += 1
        if s.enemies and self.pos is not None:
            sv = me.visible_tiles_from(s.pos)   # my own sight when the enemies were sensed (before my move)
            for e in s.enemies:
                ep, k = e[1], int(e[0])
                if self.bush.is_set(ep) and not sv.is_set(ep):
                    if self.seen.get(k, -99) < s.r - 10:    # a new sighting after 10 rounds unseen
                        trace("sward", f"spot e{k} {ep.x},{ep.y} d={e[4]} ward={self.pos.x},{self.pos.y} {w.cur[0]}")
                    self.seen[k] = s.r


SCAN = ScanWard()
