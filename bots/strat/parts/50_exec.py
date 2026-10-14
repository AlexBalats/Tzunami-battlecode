"""Executors: one step of the current (option, target) per turn -> "going" | "done" | "failed".

No stored intent beyond (option, target, started, deadline, exclusions) plus per-executor progress counters.
Timeout = walk estimate + 10 rounds, plus the option's own work (clear + capture for farm, the channel for bank,
30 rounds for hold); a timeout is a failure and excludes (option, target) for EXCL rounds.
"""


def _set_cur(self, new, r, s):
    op, tg = new
    self.cur, self.started, self.status = new, r, "going"
    self.kd, self.kn, self.arrived = 99, 0, None
    self.lastbag, self.lastgold = s.bag, s.gold
    walk, work = 0, 0
    if op == "farm" and tg in self.G:
        walk = self.gd.get(tg, 40)
        o = self.G[tg]
        mons = [m for m in (o.hp if o.hp is not None else o.mons) if m[0] > 0]
        work = (clear_dmg(mons, s.S, max(1, o.need))[0] if mons else 0) + 8
        if o.need >= 2:
            work += 10                          # waiting for the partner
    elif op in ("bank", "hold") and tg is not None and tg < len(self.ad):
        walk = self.ad[tg]
        work = max(1, -(-s.bag // 10)) + 2 if op == "bank" else 30
    elif op == "shop":
        work = 8
    elif op == "join" and tg is not None:
        walk = 20
    elif op == "kill":
        walk = 6
    elif op == "fall":
        walk = 15
    elif op == "heal":
        walk, work = 10, 7                      # step out of reach, 5-turn recall, the heal turn on spawn
    self.deadline = r + min(walk, 150) + 10 + work


World.set_cur = _set_cur


RETREAT_HP = 0.6            # [guess] fallback retreats from enemies within 4 below this HP fraction


def in_camp_range(s, w):
    pts = []
    for h, lv in s.live.items():
        for _c, _hp, p, st in lv:
            if st > 0 and p.chebyshev_distance(s.pos) <= CAMP_R:
                pts.append(p)
    return pts


def safe_recall(w, s):
    """Recall unless an enemy is within 3 or a live camp within range 3 (its hit would cancel it): then step out."""
    if s.recalling:
        return "going"
    pts = in_camp_range(s, w)
    if pts:
        w.step_away(s, pts)
        return "going"
    if s.near_e <= 3:
        w.step_to("home", s)
        return "going"
    try:
        w.me.recall()
        w.recall_r = s.r
    except Exception:
        w.step_to("home", s)
    return "going"


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
    return clear_dmg(mons, s.S, k)[1] / k <= s.hp * SURVIVE


def exec_farm(w, s, h):
    o = w.G[h]
    lv = s.live.get(h)
    if lv:
        tgt = [(hp, i) for i, (_c, hp, p, _st) in enumerate(lv) if p.chebyshev_distance(s.pos) <= ME.get("range", 1)]
        hurt = any(hp < w.G_maxhp(c) for c, hp, _p, _st in lv)
        if o.need >= 2 and not hurt and not live_ok(w, s, h, 1 + partners_near(w, s, h)):
            # pair take: wait (monsters are friendly until hit) near the group for the partner
            near = min(p.chebyshev_distance(s.pos) for _c, _hp, p, _st in lv)
            if near > 4:
                w.step_to(f"g{h}", s)
            w.waiting = True
            return "going"
        if tgt and s.can_attack:
            tgt.sort()
            c = lv[tgt[0][1]][0]
            try:
                w.me.attack(c)
                w.attacked = True
                w.reset_attack(c)
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
    if visible(w, s, o):
        if o.seen != s.r:
            update_groups(w, s, [h])
        if o.st == "resp":
            return "done"
        if o.st == "reward":
            onspawn = any(t == s.pos for t in o.tiles)
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
    rng = ME.get("range", 1)
    if dd <= rng:
        w.attacked = True
        if s.can_attack:
            try:
                w.me.attack(c)
                w.reset_attack(c)
            except Exception:
                pass
        if s.st & 0x800:
            w.cast(c, False)
        return "going"
    if dd >= w.kd:
        w.kn += 1
        ttk = -(-int(hp) // int(s.S))
        if w.kn >= (2 * ttk + 2 if ttk <= 2 else 3):   # a finisher chase gets 2 ttk + 2 rounds (pinned / 1 tile/turn)
            return "failed"
    else:
        w.kn = 0
    w.kd = dd
    if s.st & 0x800:
        w.cast(c, False)                        # dashes and ranged spells close the gap
    w.step_near(p, rng, s)
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
    item = ME["prof"]["item"]
    n = 0
    try:
        while n < 10 and w.me.can_buy(item):
            w.me.buy(item)
            n += 1
    except Exception:
        pass
    return n


def exec_shop(w, s, _t):
    if s.spawn or not s.alive:
        buy_all(w, s)
        return "done"
    return safe_recall(w, s)


def exec_join(w, s, k):
    b = s.mem[k] if k < 5 else 0
    if (b & 7) != 1 or (b >> 3) not in w.idx:
        return "failed"
    h = w.idx[b >> 3]
    if min(t.chebyshev_distance(s.pos) for t in w.G[h].tiles) <= 4:
        return "done"
    w.step_to(f"g{h}", s)
    return "going"


def retreat_now(s):
    """The fallback's retreat condition: enemies within 4 outnumber us + 1, or HP < RETREAT_HP with one there."""
    near = [e for e in s.enemies if e[4] <= 4]
    if not near or s.spawn:
        return False
    allies = sum(1 for a in s.allies if a[1].chebyshev_distance(s.pos) <= 4)
    return len(near) > allies + 1 or s.hp < RETREAT_HP * s.maxhp


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
    near = [e for e in s.enemies if e[4] <= 4]
    if near and not s.spawn:
        if retreat_now(s):
            if s.near_e <= 3:                   # retreat: out of their reach first, recall once clear
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


EXEC = {"farm": exec_farm, "bank": exec_bank, "kill": exec_kill, "hold": exec_hold, "shop": exec_shop,
        "join": exec_join, "fall": exec_fall, "heal": exec_heal}
