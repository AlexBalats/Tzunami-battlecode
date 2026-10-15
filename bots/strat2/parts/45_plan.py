"""Layered choice (strat2, 15 Oct): PLAN (regions from the draft) -> DUTY (option whitelist per champion) -> DANGER
(safe / careful / flee) -> HOT regions (fresh sightings) -> COMMIT until a breakpoint. The price formulas of
40_prices (price_all) are the cost functions; this part filters and scales them and decides WHEN to re-price."""

# ---- numbers (one-line constants; tools/variant.py keys) ----
PLAN_OTHER = 0.7            # FARM x this on groups outside my assigned region (current target exempt)
LEAD_OFF = 8                # region lead = clamp((d_them - d_us + LEAD_OFF) / LEAD_DIV, LEAD_MIN, LEAD_MAX)
LEAD_DIV = 16
LEAD_MIN = 0.2
LEAD_MAX = 1.5
OPEN_END = 60               # phase open before this round
CLOSE_ROUND = 1200          # phase close from this round ...
CLOSE_GAP = 300             # ... or when |score gap| >= this
PLAN_MIN_SHARE = 0.25         # the plan applies only with >= 2 regions scoring >= this x the best
PLAN_CAND_MAX = 12          # FARM candidates at most (near6 + region groups + live)
COMMIT_MAX = 40             # rounds a choice runs before a forced re-price
COMMIT_FALL = 5             # re-price every this many rounds while idle / falling back
COMMIT_SIGHT = 1            # 1: an enemy newly within DANGER_R is a breakpoint (deviation from the spec list)
CAPT_GOLD = 25              # a gold jump >= this in one turn counts as a capture / kill completed
ARRIVE_R = 2                # within this of the target's anchor / altar / ward tile = arrived (once)
HOT_ROUNDS = 60             # rounds a sighted altar's region stays hot
HOT_FARM = 0.0              # FARM / BANK in a hot region x this for non-carry duties (no partner within HOT_PARTNER_R)
HOT_CARRY = 0.2             # the same for the carry (was STACK_FARM)
HOT_PARTNER_R = 4           # an ally of my subgroup / pair within this lifts the hot penalty
DANGER_R = 8                # enemies within this count for danger
FLEE_HP = 0.25              # flee when hp - burst <= this x maxhp (burst > 0)
FLEE_LOW = 0.3              # ... or hp < this x maxhp with an enemy within DANGER_R
FLEE_MOB_HP = 0.7           # the mob rule flees only below this hp fraction (else careful)
FLEE_CLEAR = 8              # flee ends after 3 rounds with no enemy within this, or on spawn
FLEE_MOB = 3                # ... or >= this many enemies within DANGER_R, no ally within FLEE_ALLY_R and plose > FLEE_PLOSE
FLEE_ALLY_R = 5
FLEE_PLOSE = 0.5
CAREFUL_HP = 0.6            # careful when hp < this x maxhp with an enemy within DANGER_R ...
CAREFUL_PLOSE = 0.5         # ... or plose > this
CAREFUL_EXIT = 0.35         # careful exits only below this plose ...
CAREFUL_HP_EXIT = 0.7       # ... and above this hp fraction
DANGER_MIN = 5              # rounds a level holds before it can drop
FLEE_BURST_HP = 0.5         # burst flee only below this hp fraction
BURST_OTHER = 0.5           # burst: the strongest enemy in reach + this x the others
ESCAPE_WALK = 6             # escape available: dash ready or the walk home <= this
BURST_X = 2                 # turn-order exposure: the enemy swings first (2 hits before I act twice)
DASH_EXTRA = 2              # flee: dash the moment an enemy is within its reach + this
FLEE_RECALL_R = 6           # flee: recall only with no enemy within this
LEAD_WAIT = 25              # group leader waits this long at a group it cannot solo
MIN_COMMIT = 0.5            # a farm priced below this ...
FAR_COMMIT = 15             # ... and farther than this: fall instead (re-priced every COMMIT_FALL)
FARMER_BANK_BAG = 40        # farmer duty: bank runner from this bag ...
FARMER_BANK_X = 3.0         # ... at x this

DUTY_OF = {1: "carry", 9: "clearer", 0: "partner", 2: "farmer", 6: "farmer"}    # draft id -> duty (else farmer)
DUTY_OPTS = {
    "carry": ("farm", "bank", "shop", "kill", "heal", "hunt"),
    "clearer": ("farm", "join", "kill", "heal", "bank", "shop"),
    "partner": ("farm", "join", "kill", "heal", "bank", "shop"),
    "farmer": ("farm", "bank", "ward", "heal", "kill", "shop"),
}
DUTY_MUL = {
    "carry": {"bank": 1.5},
    "clearer": {"join": 1.5},
    "partner": {},
    "farmer": {"bank": 1.3},
}
KILL_LIMIT = {"clearer": "fin_att", "farmer": "fin"}    # kill only finishers (and the attacker for the clearer)
DRANK = {"safe": 0, "careful": 1, "flee": 2}
FIGHT_OPS = ("kill", "join", "hunt")


def _lead(o):
    return min(LEAD_MAX, max(LEAD_MIN, (o.d_them - o.d_us + LEAD_OFF) / LEAD_DIV))


def region_scores(w):
    """{altar index: sum over its groups of (gems + g2g(1) gold) x lead}, cached (draft only: same on every body)."""
    rs = getattr(w, "rscore", None)
    if rs is not None:
        return rs
    rs = {}
    k = g2g(1)
    for h, o in w.G.items():
        if o.near is None or o.near >= len(w.apos) or o.d_us >= 255:
            continue
        rs[o.near] = rs.get(o.near, 0.0) + (o.gems + k * o.gold) * _lead(o)
    w.rscore = rs
    w.rgroups = {}
    for h, o in w.G.items():
        if o.near in rs:
            w.rgroups.setdefault(o.near, []).append(h)
    return rs


def my_duty(w):
    rid = w.roster[w.slot] if w.roster and w.slot < len(w.roster) else None
    return DUTY_OF.get(rid, "farmer")


def phase(w, s):
    r = s.r
    if r >= CLOSE_ROUND or abs(w.score[0] - w.score[1]) >= CLOSE_GAP:
        return "close"
    if r < OPEN_END:
        return "open"
    if not w.spike and r < SPIKE_ROUND:
        return "build"
    return "spike"


def assign(w):
    """slot -> region, deterministic from the draft, roster size and slots (no comms)."""
    rs = region_scores(w)
    order = sorted(rs, key=lambda a: (-rs[a], a))
    if not order or sum(1 for a in order if rs[a] >= PLAN_MIN_SHARE * rs[order[0]]) < 2:
        return {}                               # one region (collision): no plan, normal near6 candidates
    n = len(w.roster) if w.roster else 5
    out = {}
    sb = getattr(w, "subs", None) or {}
    if stack_mode(w, 1) and sb:
        subs = sorted({tuple(v) for v in sb.values()}, key=lambda t: t[0])
        for i, t in enumerate(subs):
            for k in t:
                out[k] = order[i % len(order)]
        return out
    left = list(order)
    vs = next((k for k in range(n) if w.roster and k < len(w.roster) and w.roster[k] == VESPER_ID), None)
    if vs is not None:
        gold = {}
        for a in order:
            gold[a] = sum(w.G[h].gold for h in w.rgroups.get(a, ()))
        ours = [a for a in order if w.aside[a] == 0] or [a for a in order if w.aside[a] <= 1] or order
        va = max(ours, key=lambda a: (gold[a], rs[a], -a))
        out[vs] = va
        left.remove(va)
    i = 0
    for k in range(n):
        if k in out:
            continue
        out[k] = left[i % len(left)] if left else order[0]
        i += 1
    return out


def region_dead(w, s, a):
    """All groups of region a are respawning (memory) or seen taken."""
    hs = w.rgroups.get(a, ())
    return bool(hs) and all(w.G[h].st == "resp" and w.G[h].until > s.r for h in hs)


def plan(w, s, by):
    """Sets w.region (my assigned region) and w.pgroups; returns True on a re-assignment."""
    if not w.apos:
        w.region, w.pgroups = None, ()
        return False
    base = assign(w)
    a = w.region_over if getattr(w, "region_over", None) is not None else base.get(w.slot)
    if a is not None and region_dead(w, s, a):
        held = set()
        for k, (op, tg) in by.items():
            if k < w.slot and op == 1 and tg in w.idx:
                held.add(w.G[w.idx[tg]].near)
        rs = w.rscore
        nxt = [b for b in sorted(rs, key=lambda b: (-rs[b], b)) if b != a and b not in held and not region_dead(w, s, b)]
        if nxt:
            w.region_over = a = nxt[0]
    ch = a != getattr(w, "region", None)
    w.region = a
    w.pgroups = tuple(w.rgroups.get(a, ())) if a is not None else ()
    if ch:
        trace("plan", f"slot={w.slot} region=A{a} score={w.rscore.get(a, 0):.0f} groups={len(w.pgroups)} "
                      f"assign={'/'.join(f'{k}:A{v}' for k, v in sorted(base.items()))} "
                      f"over={int(getattr(w, 'region_over', None) is not None)}")
    return ch


def danger(w, s):
    """safe | careful | flee (replaces the survival rules in the choice). Traces on change with the inputs."""
    hp, mx = s.hp, s.maxhp
    near = [e for e in s.enemies if e[4] <= DANGER_R]
    bs = [BURST_X * e[5] * rmul(e[0]) for e in s.enemies if e[4] <= arng(e[0]) + 1]
    burst = max(bs) + BURST_OTHER * (sum(bs) - max(bs)) if bs else 0.0
    s.plose = pl = lanchester(s, s.pos) if s.enemies else 0.0
    wb = fget(w.F_home, s.pos) if w.F_home is not None else s.pos.chebyshev_distance(w.sp0)
    try:
        dash = w.dash_ab is not None and w.dash_ab.is_ready()
    except Exception:
        dash = False
    esc = dash or wb <= ESCAPE_WALK
    ally5 = any(a[1].chebyshev_distance(s.pos) <= FLEE_ALLY_R for a in s.allies)
    old = getattr(w, "dl", "safe")
    if old == "safe":
        cpl, chp = CAREFUL_PLOSE, CAREFUL_HP
    else:
        cpl, chp = CAREFUL_EXIT, CAREFUL_HP_EXIT
    lv = "safe"
    if s.spawn:
        lv = "safe"
    elif (burst > 0 and hp - burst <= FLEE_HP * mx and hp < FLEE_BURST_HP * mx) or (near and hp < FLEE_LOW * mx) \
            or (len(near) >= FLEE_MOB and not ally5 and pl > FLEE_PLOSE and hp < FLEE_MOB_HP * mx):
        lv = "flee"
    elif (near and hp < chp * mx) or pl > cpl or (len(near) >= FLEE_MOB and not ally5 and pl > FLEE_PLOSE):
        lv = "careful"
    if DRANK[lv] < DRANK[old] and s.r - w.dl_since < DANGER_MIN and not s.spawn:
        lv = old                                # a level holds DANGER_MIN rounds before it drops
    if lv != old:
        w.dl_since = s.r
    if lv != getattr(w, "dl", "safe"):
        trace("danger", f"{getattr(w, 'dl', 'safe')}->{lv} hp={hp / mx:.2f} burst={burst:.0f} ne8={len(near)} "
                        f"pl={pl:.2f} esc={int(esc)} dash={int(dash)} wb={wb} ally5={int(ally5)}")
    w.burst, w.esc = burst, esc
    return lv


def hot_update(w, s):
    """Fresh sighting -> its altar's region hot for HOT_ROUNDS. Returns the set of hot altars."""
    hot = w.hot
    if s.sc and s.sage <= SIGHT_FRESH and s.sa < len(w.apos):
        t = s.r - s.sage
        if s.r - hot.get(s.sa, -999) >= HOT_ROUNDS:
            trace("hot", f"A{s.sa} n={s.sc} age={s.sage} mine={int(s.sa == w.region)}")
        if t > hot.get(s.sa, -999):
            hot[s.sa] = t
    return {a for a, t in hot.items() if s.r - t < HOT_ROUNDS}


def partner_near(w, s):
    mine = (getattr(w, "subs", None) or {}).get(w.slot, ())
    for c, p, _hp, _st in s.allies:
        if p.chebyshev_distance(s.pos) <= HOT_PARTNER_R:
            k = w.ally_slot(c)
            if not mine or k in mine:
                return True
    return False


def exec_flee(w, s, _t):
    """Flee: dash the moment an enemy is within its reach + DASH_EXTRA, step toward home, recall when nobody is
    within FLEE_RECALL_R (safe_recall). Trapped with no flee that can end: fight the attacker."""
    if s.trapped and not flee_ok(s) and s.attacker is not None:
        return exec_kill(w, s, int(s.attacker[0]))
    if s.spawn:
        return "done"
    if any(e[4] <= FLEE_CLEAR for e in s.enemies):
        w.fclr = 0
    else:
        w.fclr = getattr(w, "fclr", 0) + 1
        if w.fclr >= 3:
            w.fclr = 0
            return "done"
    ne = [e for e in s.enemies if e[4] <= FLEE_RECALL_R]
    if ne:
        if any(e[4] <= arng(e[0]) + DASH_EXTRA for e in ne):
            dash_escape(w, s, [e[1] for e in ne], 99)
        if w.step_flee(s, [e[1] for e in ne]) == "blocked":
            w.step_to("home", s)
        return "going"
    return safe_recall(w, s)


def _fin(w, s, hd):
    e = next((x for x in s.enemies if int(x[0]) == hd), None)
    return e is not None and -(-int(e[2]) // int(s.S)) <= 2


def _target_pos(w, op, tg):
    if op == "farm" and tg in w.G:
        return w.G[tg].anchor
    if op in ("bank", "hold", "hunt") and tg is not None and tg < len(w.apos):
        return w.apos[tg]
    if op == "ward" and tg is not None and tg < len(w.wtiles):
        return w.wtiles[tg]
    return None


def breakpoint(w, s, dl, reass):
    """Why re-price now (None: the current choice continues)."""
    r = s.r
    cur = w.cur
    if w.status != "going":
        return f"status={w.status}"
    if DRANK[dl] > DRANK[w.dl]:                 # only a RISE re-prices
        return f"danger={w.dl}->{dl}"
    if reass:
        return "plan"
    if w.seed_was and w.seed is None:
        return "seed"
    if cur[0] in ("idle", "fall", "dead"):
        return "idle" if r - w.cprice >= COMMIT_FALL else None
    tp = _target_pos(w, cur[0], cur[1])
    if tp is not None and not w.arr and s.pos.chebyshev_distance(tp) <= ARRIVE_R:
        w.arr = True
        return "arrived"
    pb, pg = w.pb
    if (s.bag > pb) or (pb > 0 and s.bag == 0) or s.gold - pg >= CAPT_GOLD:
        return f"reward bag={pb}->{s.bag} gold={pg}->{s.gold}"
    if COMMIT_SIGHT:
        ne = sum(1 for e in s.enemies if e[4] <= DANGER_R)
        if ne and not w.ne8:
            return f"sight n={ne}"
    if r - w.cprice >= COMMIT_MAX:
        return "max"
    return None


def choose(w, s):
    """Layered choice; returns True when the (option, target) changed."""
    r = s.r
    cl, by = claims(w, s)
    w.claims = cl
    w.lowcl = {w.idx[tg] for k, (op, tg) in by.items() if k < w.slot and op == 1 and tg in w.idx}
    w.lowcn = {}
    for k, (op, tg) in by.items():
        if k < w.slot and op == 1 and tg in w.idx:
            w.lowcn[w.idx[tg]] = w.lowcn.get(w.idx[tg], 0) + 1
    sb = getattr(w, "subs", None) or {}
    mine = sb.get(w.slot, ())
    w.lowsub = {w.idx[tg] for k, (op, tg) in by.items() if k < w.slot and k in mine and op == 1 and tg in w.idx}
    reass = plan(w, s, by)
    w.hotset = hot_update(w, s)
    w.myhot = w.region in w.hotset
    dl = danger(w, s)
    duty = my_duty(w)
    if duty != w.duty:
        trace("duty", f"{w.duty}->{duty} slot={w.slot}")
        w.duty = duty
    if w.seed is not None:
        w.seed_was = True
    sd = seeded(w, s) and dl != "flee"
    why = None if sd else breakpoint(w, s, dl, reass)
    ne8 = any(e[4] <= DANGER_R for e in s.enemies)
    w.pb, w.ne8 = (s.bag, s.gold), ne8
    if why is None:
        w.dl = dl
        return False
    w.dl = dl
    w.seed_was = w.seed is not None
    w.cprice = r
    trace("commit", f"{why} cur={w.cur[0]}:{tname(w, w.cur[0], w.cur[1])} since={r - w.started}")
    if dl == "flee":
        new, best = ("flee", None), (0.0, "flee", None)
        ps = []
    else:
        ps = price_all(w, s, cl, by)
        ok = DUTY_OPTS[duty]
        mul = DUTY_MUL[duty]
        lim = KILL_LIMIT.get(duty)
        ph = phase(w, s)
        hot = w.hotset
        pn = partner_near(w, s) if hot else False
        q = []
        alt = []                                # farms without PLAN_OTHER / far rule (fall fallback)
        for p, op, tg in ps:
            if op != "heal" and w.excl.get((op, tg), -1) > r:
                continue
            if op not in ok:
                continue
            if op == "hunt" and duty == "carry" and ph != "spike":
                continue
            if op == "kill" and lim and not (_fin(w, s, tg) or (lim == "fin_att" and s.attacker is not None
                                                               and int(s.attacker[0]) == tg)):
                continue
            if dl == "careful":
                if op in FIGHT_OPS and not (w.cur == ("kill", tg) and _fin(w, s, tg)):
                    continue
                if op == "ward":
                    continue
                if op == "bank" and any(e[1].chebyshev_distance(w.apos[tg]) <= DANGER_R for e in s.enemies):
                    continue
            p *= mul.get(op, 1.0)
            if op == "bank" and duty == "farmer" and s.bag >= FARMER_BANK_BAG:
                p *= FARMER_BANK_X
            if op == "farm" and tg in w.G:
                o = w.G[tg]
                if w.region is not None and o.near != w.region and w.cur != ("farm", tg):
                    alt.append((p, op, tg))
                    p *= PLAN_OTHER
                if o.near in hot and not pn:
                    p *= HOT_CARRY if duty == "carry" else HOT_FARM
            if op == "bank" and tg in hot and not pn:
                p *= HOT_CARRY if duty == "carry" else HOT_FARM
            q.append((p, op, tg))
        q.sort(key=lambda t: -t[0])
        ps = q
        best = ps[0] if ps and ps[0][0] > 0 else (0.0, "fall", None)
        if best[1] == "farm" and best[0] < MIN_COMMIT and best[2] in w.G                 and w.G[best[2]].anchor.chebyshev_distance(s.pos) > FAR_COMMIT:
            best = (0.0, "fall", None)          # no far commits on a cheap farm
        if best[1] == "fall" and dl == "safe":  # fall is not a rest: any group with a price counts
            alt += [x for x in q if x[1] == "farm"]
            alt = [x for x in alt if x[0] > 0]
            if alt:
                best = max(alt, key=lambda x: x[0])
        new = (best[1], best[2])
    if new == w.cur and w.status == "going":
        return False
    cur = w.cur
    w.set_cur(new, r, s)
    w.arr = False
    if TRACE:
        t2 = ps[1] if len(ps) > 1 else (0.0, "-", None)
        trace("choice", f"{new[0]} {tname(w, new[0], new[1])} {best[0]:.2f} | {t2[1]} {tname(w, t2[1], t2[2])} "
                        f"{t2[0]:.2f} bag={s.bag} hp={s.hp / s.maxhp:.2f} dl={dl} duty={duty} reg=A{w.region} "
                        f"pl={getattr(s, 'plose', 0):.2f} ne={s.near_e} from={cur[0]}:{cur[1]} why={why}")
    return True
