"""Updaters (03_ARCHITECTURE.md section 2.3): SwUpdater.decide picks the Behavior each turn (R1: one updater, strat-sw's
choose). The opening seeds: every champion computes the same slot -> group list out of the draft record, with no
comms."""

SEED_UNTIL = 40             # [rule, 15 Oct ladder phase 1] the opening seed holds to this round (was round 1 + 2)


def opening_seed(w):
    """My entry of opening_slots (None past its end)."""
    slots = opening_slots(w, 6)               # 6 bodies at most: the same list whatever roster I saw at boot
    return slots[w.slot] if w.slot < len(slots) else None



def rich_group(w, m, used, tests):
    """[user plan 15 Oct, pair/trio opener] the richest reachable group not in used for m bodies: sides 0/1 before 2,
    then (gems + g2g(1) gold) / (d_us + clear rounds with m bodies); tests are need filters tried in order (the first
    that matches anything wins). None if nothing is reachable."""
    for ok in tests:
        best = None
        for h in w.order:
            o = w.G[h]
            if o.d_us >= 255 or h in used or not ok(o.need):
                continue
            cr = -(-sum(x[0] for x in o.mons) // (CHAMP_STR * m))
            key = (o.side > 1, -(o.gems + g2g(1) * o.gold) / (o.d_us + cr + 1), h)
            if best is None or key < best:
                best = key
        if best:
            return best[2]
    return None


GROUP_NAMES = {6: "six", 5: "five", 4: "quad", 3: "trio", 2: "pair", 1: "solo"}


def group_slots(w, r):
    """Stack seeds and subgroups. Before OPEN_END (06 section 4.1) the whole team is one subgroup on the richest group.
    After it, on a group map [user plan 15 Oct, pair/trio opener], the roster splits by size (5 -> trio + pair, 4 -> two
    pairs, 3 -> pair + solo, <= 2 -> one subgroup; 6 bodies with Cassi & Issac -> two trios). Subgroup 0 takes the richest group needing 2..its size (else >= 2,
    else any); a pair as subgroup 1 the next richest needing exactly 2 (else >= 2, else any); a solo the best need-1
    group (else any). The main carry's slot (06 section 3) joins the subgroup whose group has more gold (ties: subgroup 0); the other slots
    fill hers first, lowest slot first, then the other. Sets w.subs {slot: tuple of its subgroup's slots}; returns
    6 entries (slot -> group). Same on every champion: draft S (as bodies, nbody), roster order, draft records only."""
    S = min(6, max(1, nbody((w.d or {}).get("S") or 0) or len(w.roster)))
    sizes = (S,) if r < OPEN_END else (3, 3) if S >= 6 else (3, 2) if S == 5 else (2, 2) if S == 4 else (2, 1) if S == 3 else (S,)
    gs, used = [], set()
    for i, m in enumerate(sizes):
        if m == 1:
            tests = (lambda n: n <= 1, lambda n: True)
        elif i == 0:
            tests = (lambda n, m=m: 2 <= n <= m, lambda n: n >= 2, lambda n: True)
        else:
            tests = (lambda n: n == 2, lambda n: n >= 2, lambda n: True)
        g = rich_group(w, m, used, tests)
        gs.append(g)
        if g is not None:
            used.add(g)
    vs = w.main
    gold = [w.G[g].gold if g is not None else -1 for g in gs]
    iv = gold.index(max(gold)) if 0 <= vs < S else 0
    rest = [k for k in range(S) if k != vs] if 0 <= vs < S else list(range(S))
    mem = [[] for _ in sizes]
    if 0 <= vs < S:
        mem[iv].append(vs)
    for i in [iv] + [j for j in range(len(sizes)) if j != iv]:
        while len(mem[i]) < sizes[i] and rest:
            mem[i].append(rest.pop(0))
    w.subs = {}
    slots = [None] * 6
    for i, ms in enumerate(mem):
        for k in ms:
            w.subs[k] = tuple(sorted(ms))
            slots[k] = gs[i]
    return slots


def opening_slots(w, n):
    """n DISTINCT group handles (slot i takes entry i); every champion computes the same list with no comms.
    Groups on our side (0) and contested (1), ranked by the walk from our spawn (d_us; ties: higher value per round),
    solo groups (need 1) first, then pair groups (need 2). [rule, 15 Oct ladder 2] the main carry's slot first takes the
    nearest group with gold > 0 (one she can take alone if any: all gold to the main carry); no group is given to two slots (the
    50x50 4-pick ladder map had one seedable group and three champions on it); when the list runs out, the
    next-nearest unused reachable group of any need and side. Seeds only the first choice."""
    if stack_mode(w, cambc.round_number()):
        return group_slots(w, cambc.round_number())[:n]     # the team (open) or its subgroups (group map)
    solo, pair, rest = [], [], []
    for h in w.order:
        o = w.G[h]
        if o.d_us >= 255:
            continue
        hp = sum(m[0] for m in o.mons)
        cr = -(-hp // (CHAMP_STR * max(1, o.need)))
        key = (o.d_us, -(o.gems + g2g(1) * o.gold) / (o.d_us + cr + 1), h)
        (rest if o.side > 1 or o.need > 2 else solo if o.need <= 1 else pair).append(key)
    solo.sort()
    pair.sort()
    rest.sort()
    order = [k[2] for k in solo + pair + rest]
    vs = w.main
    vg = None
    if 0 <= vs < n:
        gold = sorted((w.G[h].side > 1, w.G[h].need > 1, w.G[h].d_us, h) for h in order if w.G[h].gold > 0)
        vg = gold[0][3] if gold else None
    slots, it = [], iter(h for h in order if h != vg)
    for i in range(n):
        slots.append(vg if i == vs and vg is not None else next(it, None))
    assert len(set(h for h in slots if h is not None)) == sum(1 for h in slots if h is not None), "seed dup"
    return slots


class SwUpdater:
    """R1's one updater (strat-sw's choose): price every option (50_prices price_all), drop the excluded ones, keep
    the current Behavior while the opening seed, the HOLD_TURNS hold, a chase hold or hysteresis says so, else start
    the best (World.start). Holds the opening seed and this turn's claims read from the slot bytes (lowcl / lowcn /
    lowsub: the claims of lower slots, read by the prices). retreat_now and flee_ok stay shared helpers."""
    __slots__ = ("seed", "seed_until", "claims", "lowcl", "lowcn", "lowsub")

    def __init__(self):
        self.seed, self.seed_until = None, 0    # opening seed (play_main) and the round it holds to
        self.claims, self.lowcl, self.lowcn, self.lowsub = {}, set(), {}, set()

    def seeded(self, w, s):
        """True while the opening seed holds: until SEED_UNTIL, while I still execute it (going), and the seeded group is
        not cleared / respawning (seen taken on arrival: Farm returns done) and no reward came in yet (bag or gold
        above what I held when it was set: a capture; a fast respawn otherwise kept me re-farming it). Clears seed and traces once on end."""
        sd = self.seed
        if sd is None:
            return False
        o = w.G.get(sd)
        if s.r <= self.seed_until and w.cur == ("farm", sd) and w.status == "going" and o is not None \
                and not (o.st == "resp" and o.until > s.r) and s.bag <= FARM.lastbag and s.gold <= FARM.lastgold:
            return True
        self.seed = None
        trace("choice", f"seed end {tname(w, 'farm', sd)} cur={w.cur[0]} status={w.status} st={o.st if o else '-'} "
                        f"bag={s.bag} gold={s.gold}")
        return False

    def decide(self, w, s):
        """Argmax with a HOLD_TURNS hold, then hysteresis; returns True when the choice changed.
        [rule, 15 Oct ladder 3] the HOLD_TURNS hold applies to HEAL too (ladder: heal/kill/heal/bank/heal dither with a
        44 bag); only retreat_now breaks it. Farm -> another farm needs the race row's farm_hyst, and the current job's
        price counts its sunk progress (SUNK_K). HEAL is never excluded (a death or timeout while healing must not forbid
        the next heal)."""
        cur = w.cur
        cl, by = Comms.claims(w, s)
        self.claims = cl
        self.lowcl = {w.idx[tg] for k, (op, tg) in by.items() if k < w.slot and op == 1 and tg in w.idx}
        self.lowcn = {}                                # group -> claimants with a lower slot than mine (one-way partners)
        for k, (op, tg) in by.items():
            if k < w.slot and op == 1 and tg in w.idx:
                self.lowcn[w.idx[tg]] = self.lowcn.get(w.idx[tg], 0) + 1
        if s.r >= OPEN_END and w.subs_r < OPEN_END:
            w.subs_r = s.r                             # the opening ends: subgroups on a group map, else none
            if group_map(w):
                group_slots(w, s.r)
            else:
                w.subs = {}
            trace("stack", f"open end subs={w.subs.get(w.slot)}")
        sb = getattr(w, "subs", None) or {}
        mine = sb.get(w.slot, ())
        self.lowsub = {w.idx[tg] for k, (op, tg) in by.items() if k < w.slot and k in mine and op == 1 and tg in w.idx}
        ps = price_all(w, s, cl, by)
        r = s.r
        ps = [t for t in ps if t[1] == "heal" or w.excl.get((t[1], t[2]), -1) <= r]
        ps.sort(key=lambda t: -t[0])
        curp = None
        for t in ps:
            if t[1] == cur[0] and t[2] == cur[1]:
                curp = t[0]
                break
        best = ps[0] if ps else (0.0, "fall", None)
        if best[0] <= 0:
            best = (0.0, "fall", None)
        if TRACE and s.attacker is not None and w.cur[0] in ("heal", "fall") or TRACE and s.attacker is not None and best[1] in ("heal", "fall"):
            trace("flee", f"{w.cur[0]}->{best[1]} att={int(s.attacker[0])} d={s.attacker[4]} trapped={int(s.trapped)} "
                          f"ok={int(flee_ok(s))} hp={s.hp / s.maxhp:.2f} pl={s.plose:.2f}")
        if self.seeded(w, s) and best[1] != "heal" and not retreat_now(s):
            return False                            # the opening seed holds (only HEAL / retreat break it)
        going = curp is not None and curp > 0 and w.status == "going"
        held = going and r - w.started < HOLD_TURNS and not retreat_now(s)
        # [user plan 15 Oct, ladder 5] a KILL on a still-visible target, or a HUNT on a fresh sighting while it prices,
        # holds for the phase's `chase` rounds (default 3) whatever its price, unless hp < 30 % or retreat_now (ladder:
        # Vesper chose a kill, stepped once, it priced negative and she dropped it, 4 times in one game)
        if (w.status == "going" and s.hp >= 0.3 * s.maxhp and not retreat_now(s)
                and r - w.started < ME["prof"].get("chase", 3)
                and ((cur[0] == "kill" and any(int(e[0]) == cur[1] for e in s.enemies))
                     or (cur[0] == "hunt" and curp is not None and cur[1] == s.sa and s.sc and s.sage <= SIGHT_FRESH))):
            held = True
        hy = HYST
        if cur[0] == "farm" and best[1] == "farm" and best[2] != cur[1]:
            hy = race(w)["farm_hyst"]
        if best[1] != "heal" and not retreat_now(s):
            hy = max(hy, 1.0 + SUNK_K * w.prog)     # [IMPROVEMENTS 2] sunk progress; HYST / farm_hyst stay the floor
        keep = held or (going and best[0] <= curp * hy) or \
               (cur[0] == "fall" and best[1] == "fall" and w.status == "going")
        if keep:
            return False
        new = (best[1], best[2])
        if new == cur and w.status == "going":
            return False
        hit, pg = w.hit, w.prog
        w.start(new, r, s)
        if TRACE:
            t2 = ps[1] if len(ps) > 1 else (0.0, "-", None)
            bfi = max((t[0] for t in ps if t[1] in ("kill", "hunt") or (t[1] == "join" and by.get(t[2], (0,))[0] == 3)),
                      default=0.0)
            trace("choice", f"{new[0]} {tname(w, new[0], new[1])} {best[0]:.2f} | {t2[1]} {tname(w, t2[1], t2[2])} "
                            f"{t2[0]:.2f} cur={curp if curp is None else round(curp, 2)} bag={s.bag} "
                            f"hp={s.hp / s.maxhp:.2f} fight={bfi:.2f} dcost={s.dcost:.0f} pl={getattr(s, 'plose', 0):.2f} ne={s.near_e} "
                            f"d={w.G[new[1]].anchor.chebyshev_distance(s.pos) if new[0] == 'farm' and new[1] in w.G else '-'} "
                            f"from={cur[0]}:{cur[1]} hit={int(hit)} prog={pg:.2f}"
                            + (f" roam={w.roam:.2f}" if new[0] == "hunt" and new[1] != s.sa else "")
                            + "".join(f" tp={e[1].x},{e[1].y} desp={min(e[1].chebyshev_distance(q) for q in w.esp.positions())}"
                                      for e in s.enemies if new[0] == "kill" and int(e[0]) == new[1]))
        return True


UPD = SwUpdater()
