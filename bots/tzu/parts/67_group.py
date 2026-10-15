# tzu: lazy
"""Group takes (P10: concentrate force; ROLES_AND_LAYERS §1.3 Flex `partner`, §2.1 two-champion elk take).

Some groups no single pick survives (every elk group; wolf triples for all but Varg): a tank and a partner
clear them together. Monsters hit the NEAREST champion in range, ties to the lowest unit id [rules,
measured A2], so the tank steps in first and the partner stands where it is never nearer than the tank.

    GroupTake(h, role, mate_ctype)   role "tank" | "partner"; a Task (60_tasks interface: start/step/abort,
                                     key = h, act, fight, hit, then = the Capture tail)
    pair_pred(tank_kit, partner_kit, mons)   L3's predict_pair cached by both kits and the composition
    pair_ok(w, tank_kit, partner_kit, mons, keep)  the I3 gate of a pair: (ok, pred) or (None, None) on fuel
    pair_slots(dec)                  (guard slot, partner slot) of the alive team
    best_pair(dec, s, g, p)          (gems per round, h, pred) of the best pair group, deterministic
    pair_choice(dec, s)              L5 hook: a GroupTake to start, or None (call first in Decider.choose)
    pair_filter(dec, s, r)           L5 hook: drops interrupt rows GroupTake handles itself
    pair_after_end(dec, t, s)        L5 hook: group rest after a take the mate captures
    pair_has_work(dec, s)            L5 hook: Station / WaitRespawn re-checks
    pair_work(dec)                   background hook (step 8): predictions best_pair could not afford inline

Phases: walk -> stage (tank: on the group's ring, waits until the partner is ready, i.e. within one step
of attack reach of a threat or READY_SLACK rounds within MATE_NEAR of us; at most WAIT_MAX rounds, WAIT_ACK
once the partner claims the group; partner: walks to the focus threat's own ring "c<x>_<y>" and stops one
step short of reach, waits for the tank's first hit (it acts after the Guard, so it steps in the same
round), at most PARTNER_WAIT) -> fight (both plan_turn/act; threats first: a 0-Strength cluster only after
every monster that hits, see fight_targets; the partner picks its tile with stand_tile) -> cleared: ONE
captures (I5): the one with more room under its bank_at, ties / unseen mate the lower unit id (Capture as
`then`); the other logs cap|skip why=ally_on and moves on | out (leave every awake range, hold outside
until the group sleeps, end fail).
Gate (I3): the tank's live kit + the partner's design kit (self-only shield/heal dropped) through
predict_pair (every hit on the tank, casts serialised: pessimistic), damage x GATE_X must leave the tank's
keep_hp. During: the tank aborts when hp - pred_dmg x rem/rem0 < keep; the partner steps out when the hits
still to land on IT (nearest test with the tank's tile, each monster until it dies in focus order) would
take it below its keep. Mate gone (not engaged and no foreign damage for MATE_GONE rounds, or never engaged
APPROACH rounds after the first hit): solo_ok re-check, continue alone or step out (why=partner_left).
Foreign damage = camp HP below what our own last action left (the shared-fight detection of LESSONS §4).
Coordination: the tank asks through the shared help field (80_team writes it from `wants_help`; without
80_team the task writes w.mem.set_help itself); the partner joins on a fresh help, and leaves a staged take
for a fresh help elsewhere (why=retarget) or when the tank claims another group for AWAY_MAX rounds.
Fallback (no help seen): both compute best_pair from the plan only (d_ours, design kits, full HP), so they
pick the same group with no message. Uncached pair predictions run in the background (pair_work) or inline
only with PAIR_FUEL to spare, one per turn (I9).
Trace: pair|start g= role= mate= via= rate= ; pair|stage ; pair|engage g= wait= mate_d= pred_r= pred_dmg= hp= ;
pair|alone ok= ; pair|end g= role= res= why= r= fight_r= dmg= pred_r= pred_dmg= ; pair|eval (once per
composition). Play-only (the draft never pays for these definitions).
"""

if not cambc.is_draft():
    PAIR_ON = True          # toggle (CLAUDE.md rule 1): False = no group takes
    HELP_ON = True          # False = the deterministic plan fallback only (no help field read or written)
    WAIT_MAX = 25           # tank: rounds staged with no sign of the partner [provisional, no A# yet]
    WAIT_ACK = 60           # tank: rounds staged once the partner claims the group (it is on its way) [provisional]
    PARTNER_WAIT = 60       # partner: rounds staged without the tank's first hit [provisional]
    MATE_NEAR = 2           # partner this close to the tank (and READY_SLACK rounds) counts as ready [provisional]
    MATE_FIGHT = 1          # the mate counts as engaged within this of a live monster (or its attack range)
    MATE_GONE = 2           # rounds without the mate (unseen and no foreign damage) before the solo re-check
    APPROACH = 4            # rounds the partner has from the tank's first hit to its first engaged turn
    STAGE_R = 3             # partner: walks to the group's ring until this close, then to the focus camp's ring
    AWAY_MAX = 12           # partner: rounds the tank may claim another group (a capture is 5-6) before re-choosing
    READY_SLACK = 4         # tank: engage anyway after the partner stood this long within MATE_NEAR
    CAP_HEADROOM = True     # capturer = the champion with more room under its bank_at (fewer bank trips); ties
                            # and an unseen mate: the lower unit id. False = always the lower unit id
    PAIR_SIDES = 1 | 2      # home + mid: the Guard's home side plus the middle (P9) [provisional]
    PAIR_REEVAL = 5         # rounds between best_pair recomputations per champion (cached in between)
    PAIR_FUEL = 10 ** 9     # an uncached pair prediction (0.2-0.72M measured) inline only with this much above
                            # RESERVE: never (integration 13 Oct: pair_choice + candidates + the first ClearCamp step
                            # ran a turn into the next round, I9); best_pair's misses go to pair_work (background)
    CHOICE_FUEL = 1_000_000  # pair_choice / pair_has_work run only with this much above RESERVE
    RETARGET_REST = 20      # rounds a group rests after the partner's take of it ended why=retarget [provisional]
    PLAN_NOCLAIM = 5        # partner (via plan): rounds in a row the tank claims another code before no_tank [provisional]
    FORCE_FUEL = 900_000    # tank gate: an uncached pair prediction runs inline above this (else after FORCE_WAIT)
    FORCE_WAIT = 2          # ... or once staged-and-ready this many rounds (fuel: the turn may carry over, I9)
    _PAIR = {}              # pair_pred cache: (kits, composition) -> (rounds, damage on the tank, casts)
    _PEVAL = set()          # compositions already logged (pair|eval)
    _SOLO_EST = {}          # slot -> [(plan-based solo gems per round, h)] best first
    _SRATE = {}             # slot -> (round, solo_rate), cached PAIR_REEVAL rounds
    _PREP = [None]          # (guard slot, partner slot) whose static tables pair_work must build
    PREP_FUEL = 150_000     # the static tables are built a group at a time while this much is to spare
    _BUILD = {}             # resumable builders' progress: key -> [next group, rows so far]
    _BEST = {}              # champion-local cache of best_pair: (g, p, tank S, tank max HP) -> (round, result)
    _PRND = [-1]            # round of the last uncached pair prediction (one per turn)
    _NEED = {}              # pair predictions best_pair could not afford inline -> pair_work (background)
    _PCOST = [800_000]      # self-corrected cost estimate of one background pair prediction
    _HOPE = {}              # (pair key, summed S) -> quick_clear says HOPELESS (cached: asked on every best_pair)
    _ROWS = {}              # (guard slot, partner slot) -> static candidate rows (_pair_rows)
    _GRES = {}              # ((tank kit, partner kit), h) -> pair prediction of group h at full HP

    _CFULL = {}

    def comp_full(w, h):
        """Group h at full HP as (hp, str, x, y) rows (the predictors' mons), cached (static)."""
        c = _CFULL.get(h)
        if c is None:
            c = _CFULL[h] = [(m[1], m[2], m[3], m[4]) for m in group_comp(w, h)]
        return c

    def pair_pred(tank, partner, mons, force=False):
        """predict_pair cached by BOTH kits (type, S, F, max HP) and the relative composition; None when
        uncached and the fuel is short (unless force). HOPELESS when even summed basic attacks can't finish."""
        if not mons:
            return (0, 0.0, 0)
        x0, y0 = mons[0][2], mons[0][3]
        key = (tank.ctype, tank.S, tank.F, tank.max_hp, partner.ctype, partner.S, partner.F,
               tuple((m[0], m[1], m[2] - x0, m[3] - y0) for m in mons))
        p = _PAIR.get(key)
        if p is not None:
            return p
        S2 = tank.S + partner.S
        hk = (key, S2)
        hl = _HOPE.get(hk)
        if hl is None:
            hl = _HOPE[hk] = quick_clear(tank, mons, S2) is HOPELESS
        if hl:
            p = HOPELESS
        elif not force and (fuel() - RESERVE < PAIR_FUEL or _PRND[0] == cambc.round_number()):
            return None                                   # one uncached prediction per turn, with room (I9)
        else:
            f0 = fuel()
            th = [m for m in mons if m[1] > 0]             # threats first (fight_targets): the harmless
            r_rest = int(-(-sum(m[0] for m in mons if m[1] <= 0) // S2))   # clusters after, 0 damage
            _PRND[0] = cambc.round_number()
            p = predict_pair(tank, _Helper(partner), th) if th else (0, 0.0, 0)
            if p[0] < FAR:
                p = (p[0] + r_rest, p[1], p[2])
            c = (len(mons), "".join("w" if m[1] == 20 else "e" if m[1] == 60 else "g" if m[1] == 0 else "m"
                                    for m in mons))
            if (tank.ctype, partner.ctype, c) not in _PEVAL:
                _PEVAL.add((tank.ctype, partner.ctype, c))
                trace("pair", f"eval comp={c[1]} tank={tank.ctype} partner={partner.ctype} S={tank.S}+{partner.S} "
                              f"pred={p[0]}/{int(p[1])}/{p[2]} hp={int(tank.max_hp)} fuel={f0 - fuel()}")
        _PAIR[key] = p
        return p

    class _Helper:
        """The partner as predict_pair sees it: its self-only casts (shield, heal) protect the partner, not
        the tank who takes every hit, so they are dropped (predict_pair would credit Varg's shield to the
        tank: 720 -> 340 on elkring's elk + cluster)."""
        __slots__ = ("ctype", "S", "F", "slots")

        def __init__(self, k):
            self.ctype, self.S, self.F = k.ctype, k.S, k.F
            self.slots = tuple(sl for sl in k.slots if sl.kind not in (K_SHIELD, K_HEAL))

    def fight_targets(tg):
        """Threats first: while a monster with Strength lives, only those are targets (a 0-Strength cluster
        hit early costs every awake monster's hits for its rounds; Smith's rule on Str/HP). Same policy in
        pair_pred, so prediction and play agree (LESSONS §4)."""
        th = [t for t in tg if t[1] > 0]
        return th or tg

    def pair_ok(w, tank_kit, partner_kit, mons, keep, hp=None, force=False):
        """I3 gate of a pair take: pred damage x GATE_X < hp - keep x max HP (keep a fraction, the TANK's card
        keep_hp [provisional A43]). (ok, pred), or (None, None) when the prediction is not affordable now."""
        p = pair_pred(tank_kit, partner_kit, mons, force)
        if p is None:
            return None, None
        hp = tank_kit.max_hp if hp is None else hp
        return p[0] < FAR and p[1] * GATE_X < hp - keep * tank_kit.max_hp, p

    # ---------------------------------------------------------------- who pairs with whom (L6, pure)
    def _team(w):
        t = getattr(w, "team", None)
        return t if t is not None and getattr(t, "ready", False) else None

    def _alive_roles(dec):
        """(alive mask, {slot: role}) from 80_team when it runs, else from the Decider's debounced mask."""
        t = _team(dec.w)
        if t is not None:
            return t.alive_mask, t.roles
        miss = getattr(dec, "miss", [0] * 5)
        am = sum(1 << i for i in range(5) if miss[i] < globals().get("MISS_DEAD", 2))
        f = globals().get("roles")
        return am, (f(am, dec.size, dec.cards) if f is not None else {i: c.role for i, c in enumerate(dec.cards)
                                                                       if c is not None})

    def pair_slots(dec):
        """(guard slot, partner slot) of the alive team; partner = the alive Flex, else the alive Farmer with
        the best Guard rank (Varg before Vendetta in the fixed picks; never the Hunter). (None, None) when no
        Guard is alive, (g, None) when nobody can partner. Same answer on every champion (no messages)."""
        if not dec.cards:
            return None, None
        am, roles_ = _alive_roles(dec)
        alive = [i for i in roles_ if am >> i & 1 and dec.cards[i] is not None]
        g = next((i for i in sorted(alive) if roles_[i] == ROLE_GUARD), None)
        if g is None:
            return None, None
        flex = [i for i in sorted(alive) if i != g and roles_[i] == ROLE_FLEX]
        if flex:
            return g, flex[0]
        farm = [i for i in alive if i != g and roles_[i] == ROLE_FARMER]
        if not farm:
            return g, None
        return g, min(farm, key=lambda i: (dec.cards[i].guard_rank, i))

    def _row_comp(r):
        """Plan row -> mons rows for quick_clear (positions irrelevant there)."""
        R = globals().get("CAMP_ROWS") or {0: (1350, 20), 1: (2400, 60), 2: (500, 0), 4: (20000, 200)}
        return [R[0]] * r.wolves + [R[1]] * r.elks + [R[2]] * (r.gem_cl + r.gold_cl) + [R[4]] * r.monoliths

    def solo_rate(dec, slot, cool=None, rnd=0):
        """Best plan-based solo gems per round of a slot: (gems + gold x A41) / (d_ours + quick_clear + 5) over
        the groups whose solo bit is set for it. Deterministic (plan + design kit). The per-group rates are
        computed once per slot (sorted best first); the answer is cached PAIR_REEVAL rounds (0.1-0.5M a call
        uncached [measured 13 Oct])."""
        c = _SRATE.get(slot)
        if c is not None and rnd - c[0] < PAIR_REEVAL:
            return c[1]
        rows = _SOLO_EST.get(slot)
        if rows is None:
            _build_solo_rows(dec, slot, 0)
            rows = _SOLO_EST[slot]
        best = 0.0
        for v, h in rows:                                 # best first: the first one not resting is the answer
            if cool is None or cool.get(h, -1) <= rnd:
                best = v
                break
        _SRATE[slot] = (rnd, best)
        return best

    def best_pair(dec, s, g, p, tk=None):
        """(gems per round, h, pred) of the best pair group for Guard slot g + partner slot p, or None.
        Candidates: a plan row with no monolith, on PAIR_SIDES, reachable, solo bit unset for both (a group
        one of them solos is solo work), not resting (cool), not claimed by a third ally, and pair_ok with the
        design kits at full HP and the Guard's keep_hp. Rate = (gems + gold x A41) / (d_ours + pred + 5).
        Plan-only inputs (tk: the tank's design kit unless given), so the tank and the partner pick the same
        group with no message; the tank passes its live kit (Health shards move the gate: rows' wolf triple
        fails at 1,200 HP by 2 HP and passes at 1,500), the help request then tells the partner."""
        w, plan = dec.w, dec.plan
        tk = tk or kit_of(dec.cards[g].ctype)
        ck = (g, p, tk.S, tk.max_hp)
        c = _BEST.get(ck)
        if c is not None and s.rnd - c[0] < PAIR_REEVAL:
            return c[1]
        pk = kit_of(dec.cards[p].ctype)
        if w.queue:
            return None                                   # fields first (setup turns: I9)
        keep = CARD_DEFAULTS[ROLE_GUARD]["keep_hp"] / 100
        tm = _team(w)
        claimed = {tm.claims[i] for i in range(5) if i not in (g, p) and tm.claims[i] >= 0} if tm is not None else ()
        sig = (tk.ctype, tk.S, tk.F, tk.max_hp, pk.ctype, pk.S, pk.F)
        lim = tk.max_hp - keep * tk.max_hp
        best, pending = None, False
        cool, rnd = dec.cool, s.rnd
        for h, val, d in _pair_rows(dec, g, p):
            if h in claimed or cool.get(h, -1) > rnd:
                continue
            rk = (sig, h)
            pr = _GRES.get(rk)
            if pr is None:                                # predicted by pair_work in the background (I9)
                pending = True
                if rk not in _NEED and len(_NEED) < 8:
                    _NEED[rk] = (tk, pk, comp_full(w, h))
                continue
            if pr[0] >= FAR or pr[1] * GATE_X >= lim:
                continue
            rate = val / (d + pr[0] + CAP_FIXED)
            if best is None or rate > best[0]:
                best = (rate, h, pr)
        # cached either way (I9: a pending best_pair redone on every call cost up to 1.8M a turn [measured 13 Oct]);
        # with predictions pending it is redone after 2 rounds, when pair_work has had a background turn
        _BEST[ck] = (s.rnd - (PAIR_REEVAL - 2 if pending else 0), best)
        return best

    def _pair_rows(dec, g, p):
        """[(h, value, d_ours)] of the plan rows a pair (g, p) may take, the static filters of best_pair once
        per pair: PAIR_SIDES, no monolith, solo bit unset for both, reachable (d_ours). Each Python bytecode
        costs ~200 fuel [measured], so best_pair's per-call loop keeps only the dynamic tests."""
        c = _ROWS.get((g, p))
        if c is None:
            _build_pair_rows(dec, g, p, 0)
            c = _ROWS[(g, p)]
        return c

    def _build_pair_rows(dec, g, p, spare):
        """Builds _ROWS[(g, p)] a group at a time while fuel() - RESERVE - BG_MARGIN > spare (resumable: the
        progress is kept in _BUILD). True when complete."""
        st = _BUILD.setdefault(("pair", g, p), [0, []])
        plan, w = dec.plan, dec.w
        fl, solo = plan.groups.column(11), plan.groups.column(12)
        n = len(plan.groups)
        while st[0] < n:
            if spare and fuel() - RESERVE - BG_MARGIN < spare:
                return False
            h = st[0]
            st[0] += 1
            if not PAIR_SIDES >> (fl[h] & 3) & 1 or fl[h] >> 3 & 3 or solo[h] >> g & 1 or solo[h] >> p & 1:
                continue
            if h not in w.groups:
                continue
            r = plan.groups[h]
            if r.d_ours == 255:
                continue
            st[1].append((h, r.gems + r.gold * GOLD_GEM, r.d_ours))
        _ROWS[(g, p)] = st[1]
        return True

    def _build_solo_rows(dec, slot, spare):
        """Builds _SOLO_EST[slot] (solo_rate's per-group rates, best first) a group at a time, resumable."""
        st = _BUILD.setdefault(("solo", slot), [0, []])
        plan = dec.plan
        kit = kit_of(dec.cards[slot].ctype)
        solo = plan.groups.column(12)
        n = len(plan.groups)
        while st[0] < n:
            if spare and fuel() - RESERVE - BG_MARGIN < spare:
                return False
            h = st[0]
            st[0] += 1
            if not solo[h] >> slot & 1:
                continue
            r = plan.groups[h]
            q = quick_clear(kit, _row_comp(r))
            if r.d_ours != 255 and q[0] < FAR:
                st[1].append(((r.gems + r.gold * GOLD_GEM) / (r.d_ours + q[0] + CAP_FIXED), h))
        st[1].sort(reverse=True)
        _SOLO_EST[slot] = st[1]
        return True

    def tank_claim(w, g):
        """The Guard's claim code (handle, CLAIM_*) from shared memory, None when unknown."""
        t = _team(w)
        if t is None or g is None or not 0 <= g < 5:
            return None
        return t.claims[g]

    def help_seen(w, g):
        """(handle, age, sos) of a fresh help request, via 80_team's view or SharedMem directly (g: the Guard
        slot, Variant B reads the request from the Guard's claim)."""
        t = _team(w)
        if t is not None:
            return t.help
        m = w.mem
        return m.help(g) if m is not None else None

    def pair_choice(dec, s):
        """L5 hook, first thing in Decider.choose: a GroupTake for the Guard or its partner, else None.
        Tank: best_pair beats the two champions' best solo rates summed (P10: concentrate only when the
        concentration out-earns dispersion). Partner: a fresh help request first; else the same best_pair."""
        w = dec.w
        if not PAIR_ON or dec.plan is None or dec.slot is None or not dec.cards:
            return None
        if fuel() - RESERVE < CHOICE_FUEL:
            return None                                   # I9: the turn's other work first; asked again later
        if not getattr(dec, "ticked", True):          # never on the first tick (setup turn, I9)
            return None
        g, p = pair_slots(dec)
        if p is None or dec.slot not in (g, p):
            return None
        if (g, p) not in _ROWS or g not in _SOLO_EST or p not in _SOLO_EST:
            _PREP[0] = (g, p)                             # the static tables are built by pair_work (I9)
            return None
        if s.hp < card(w, "recall_hp") * s.max_hp or s.bag >= card(w, "bank_at"):
            return None                                   # heal / bank first
        tank = dec.slot == g
        mate = p if tank else g
        mct = dec.cards[mate].ctype
        mbank = getattr(dec.cards[mate], "bank_at", 40) or 40
        if tank:                                          # a take the tank can't pass at THIS hp: heal first
            b = best_pair(dec, s, g, p, dec.kit)         # live tank kit (shards), design partner kit
            if b is None or b[2][1] * GATE_X >= s.hp - card(w, "keep_hp") * s.max_hp:
                return None
        if not tank and HELP_ON:
            hp = help_seen(w, g)
            if hp is not None and not hp[2] and hp[0] in w.groups and \
                    (dec.cool.get(hp[0], -1) <= s.rnd or dec.cool_why.get(hp[0]) == "retarget"):
                return GroupTake(hp[0], "partner", mct, via="help", gslot=g, mate_bank=mbank)
        if not tank:
            tc = tank_claim(w, g)
            if tc == CLAIM_HUNT:
                return None                               # the tank is fighting a champion: no plan-only walk
            b = best_pair(dec, s, g, p)
            # The partner follows only a tank that works this group (its claim): the tank decides with its live
            # kit, HP and bag, the partner's best_pair with the design kit at full HP, so they disagreed and the
            # partner staged alone for 12-60 rounds at a time (ladder 14 Oct). tc None: no 80_team, old fallback.
            if b is not None and tc is not None and tc != b[1]:
                return None
        if b is None:
            return None
        rate, h, pred = b
        if rate <= solo_rate(dec, g, dec.cool, s.rnd) + solo_rate(dec, p, dec.cool, s.rnd):
            return None
        return GroupTake(h, "tank" if tank else "partner", mct, pred=pred, via="plan", rate=rate, gslot=g,
                         mate_bank=mbank)

    def pair_work(dec):
        """Background hook (skeleton step 8, after acting, like Decider.work): the pair predictions best_pair
        asked for, one at a time while the self-corrected cost fits above RESERVE + BG_MARGIN (I9).
        Returns (jobs, fuel)."""
        n, f0 = 0, fuel()
        if _PREP[0] is not None:                          # static tables first: 0.3-1.3M each on 40-60 groups,
            g, p = _PREP[0]                               # built a group at a time over as many turns as needed
            done = (g, p) in _ROWS or _build_pair_rows(dec, g, p, PREP_FUEL)
            done = done and (g in _SOLO_EST or _build_solo_rows(dec, g, PREP_FUEL))
            done = done and (p in _SOLO_EST or _build_solo_rows(dec, p, PREP_FUEL))
            n += 1
            if done:
                _PREP[0] = None
        while _NEED and fuel() - RESERVE - BG_MARGIN > _PCOST[0]:
            k = next(iter(_NEED))
            tk, pk, mons = _NEED.pop(k)
            f1, r1 = fuel(), cambc.round_number()
            _GRES[k] = pair_pred(tk, pk, mons, True)
            c = int(spent(f1, r1) * 1.3)
            if c > _PCOST[0] * 1.3:
                trace("fuel", f"over est={_PCOST[0]} job=pair cost={c * 10 // 13}")
            if c > _PCOST[0]:
                _PCOST[0] = c
            n += 1
        return n, f0 - fuel()

    def pair_has_work(dec, s):
        """L5 hook for Station / WaitRespawn re-checks: a group take is waiting (a help request for me, or a
        best_pair that beats solo)."""
        return pair_choice(dec, s) is not None

    def pair_filter(dec, s, r):
        """L5 hook on the interrupt result: rows a GroupTake handles itself are dropped while it runs."""
        t = dec.task
        if r is None or not isinstance(t, GroupTake) or t.status != "run":
            return r
        evn, nt, pause, text = r
        g = f"g=g{t.key} "
        engaged = t.phase in ("fight", "out")
        if evn == "FLEE" and "why=camp" in text:
            return None                                   # its own step-out (like ClearCamp)
        if evn in ("AWAKE", "CAPTURE") and (text + " ").startswith(g):
            return None                                   # its own group: the take, or its own capture
        if evn == "BANK" and (engaged or t.phase == "stage" and "why=bag" in text) and "why=endgame" not in text:
            return None                                   # never leave mid-take, nor a staged take for a full
                                                          # bag (commitment A42); threat banking still fires
        if evn == "HOME" and engaged:
            return None                                   # the take's own I3 during-test decides (inc may be 0
                                                          # on the tank's tile when the partner wins a tie)
        if evn == "STALL" and t.phase == "stage":
            return None
        return r

    def pair_after_end(dec, t, s):
        """L5 hook after a task ends: the mate captures -> the group rests until it respawns (event 9 then
        skips it silently; the cap|skip ally_on line was written by the take)."""
        if isinstance(t, GroupTake) and t.why == "retarget":
            # Rest it (ladder 14 Oct: fail retarget -> start the same group in the same round, ~9 times, 350
            # rounds of hold). A help request from the tank for it still gets through (pair_choice).
            dec.cool[t.key] = s.rnd + RETARGET_REST
            dec.cool_why[t.key] = "retarget"
            return
        if isinstance(t, GroupTake) and t.status == "ok" and t.why == "mate_cap":
            try:
                u = s.rnd + CAP_FIXED + dec.w.groups[t.key].max_respawn_timer()
            except Exception:
                u = s.rnd + 60
            if dec.cool.get(t.key, -1) < u:
                dec.cool[t.key] = u
                dec.cool_why[t.key] = "ally_on"                # event 9 logs cap|skip why=ally_on (I4)

    # ---------------------------------------------------------------- the task
    class GroupTake(Task):
        name = "GroupTake"

        def __init__(self, h, role, mate_ctype, pred=None, via="plan", rate=0.0, gslot=None, mate_bank=40):
            Task.__init__(self, h)
            self.mate_bank = mate_bank
            self.role, self.mate_ct, self.pred, self.via, self.rate = role, mate_ctype, pred, via, rate
            self.gslot = gslot
            self.phase = "new"
            self.capturing = False          # 80_team contract: the Capture tail is its own task

        @property
        def wants_help(self):
            """80_team contract: the tank asks while it walks, waits or fights."""
            return self.role == "tank" and self.status == "run" and self.phase in ("walk", "stage", "fight")

        def start(self, w, s):
            Task.start(self, w, s)
            self.phase = "walk"
            self.f = None
            self.r_stage = self.r_fight = None
            self.mate_seen_r = s.rnd
            self.foreign_r = -99
            self.expect = None
            self.rem0 = 1
            self.dpr = 1.0
            self.solo = False
            self.hp0 = s.hp
            self.mate = self.mate_pos = self.mate_id = None
            self.my_id = int(w.me)
            self.out_why = ""
            self.nohelp = 0
            self.noclaim = 0                # partner via plan: rounds in a row the tank's claim is not this group
            self.ready_r = None             # tank: first round the partner was ready (FORCE_WAIT)
            self.ring_r = None              # engage: walk round to the target camp's ring (60_tasks ring_reach)
            self.mate_was = False
            self.near_r = None
            self.away = 0
            _ev("pair", f"start g=g{self.key} role={self.role} mate={self.mate_ct} via={self.via} rate={self.rate:.2f}")

        # ---- bookkeeping
        def end(self, s, status, why):
            r = Task.end(self, s, status, why)
            p = self.pred or (0, 0.0, 0)
            _ev("pair", f"end g=g{self.key} role={self.role} res={status} why={why} r={s.rnd - self.r0} "
                        f"fight_r={'-' if self.r_fight is None else s.rnd - self.r_fight} dmg={int(self.hp0 - s.hp)} "
                        f"pred_r={p[0]} pred_dmg={int(p[1])}")
            return r

        def fight_end(self, s, res, why):
            if self.f is not None:
                self.f.end(s.rnd, s.hp, res, why)
                self.f = None

        def abort(self, w, s, why):
            if self.status == "run":
                self.fight_end(s, "died" if why == "died" else "abort", why)
                self.unhelp(w)
                self.end(s, "abort" if why != "died" else "fail", why)

        def fin(self, w, s, status, why):
            self.fight_end(s, "abort", why)
            self.unhelp(w)
            return self.end(s, status, why)

        def help(self, w):
            """Without 80_team, the tank re-writes the help request itself every turn (A: 3-round stamp)."""
            if HELP_ON and self.role == "tank" and _team(w) is None and w.mem is not None:
                try:
                    w.mem.set_help(self.key)
                except Exception:
                    pass

        def unhelp(self, w):
            if HELP_ON and self.role == "tank" and _team(w) is None and w.mem is not None:
                try:
                    w.mem.clear_help()
                except Exception:
                    pass

        def see_mate(self, w, s):
            """The mate this turn: visible ally of mate_ct (vision.champions lists visible ones only [sdk])."""
            self.mate = self.mate_pos = None
            for c in vision.champions(Team.ALLY):
                try:
                    if int(c) != self.my_id and int(c.champion_name()) == self.mate_ct:
                        self.mate, self.mate_pos, self.mate_id = c, c.position(), int(c)
                        return
                except Exception:
                    pass

        def acked(self, w):
            """The partner claims this group (it is coming): its claim code is our handle."""
            t = _team(w)
            return t is not None and any(t.claims[i] == self.key for i in range(5) if i != t.slot)

        def hits_on(self, p, tg, dpr=None):
            """Strength of the live monsters that would hit tile p (nearest champion: me at p vs the mate;
            ties to the lower unit id [rules]); without a visible mate every monster in range counts. With
            dpr: the damage still to land on p, each such monster hitting until it dies in focus order
            (weakest first, the pair's dpr), i.e. sum Str_i x t_i [same kill order as plan_turn]."""
            mp, mid, me = self.mate_pos, self.mate_id, self.my_id
            out = 0
            t_ = 0.0
            for t in (sorted(tg, key=lambda x: x[0]) if dpr else tg):
                if dpr:
                    t_ += t[0] / dpr
                d = max(abs(p.x - t[2]), abs(p.y - t[3]))
                if d > CAMP_RANGE:
                    continue
                if mp is not None:
                    dm = max(abs(mp.x - t[2]), abs(mp.y - t[3]))
                    if dm < d or (dm == d and mid is not None and mid < me):
                        continue
                out += t[1] * (-(-t_ // 1) if dpr else 1)
            return out

        # ---- step
        def step(self, w, s):
            h = self.key
            sense(w, s)
            kit = my_kit(w)
            if kit is None:
                return self.fin(w, s, "fail", "no_kit")
            self.fight = self.hit = "-"
            self.see_mate(w, s)
            self.help(w)
            tg = camp_targets(w, s, h)
            if not tg:
                gst = w.gstate(h) if w.anchor[h].chebyshev_distance(s.pos) <= 7 else "-"
                if gst == "dead":
                    return self.cleared(w, s)
                if gst == "respawning":
                    return self.fin(w, s, "fail", "respawning")
                r = self.goto(w, h)
                if r in ("full", "stuck"):
                    return self.fin(w, s, "fail", r)
                if r == "here":
                    return self.fin(w, s, "fail", "unseen")
                return "run"
            if self.phase == "out":
                return self.step_out(w, s)
            if self.phase == "stage" and self.r_stage is not None and s.rnd - self.r_stage > WAIT_ACK:
                return self.fin(w, s, "fail", "no_partner" if self.role == "tank" else "no_tank")   # hard cap
            if self.phase in ("walk", "stage"):
                return self.pre(w, s, kit, tg)
            return self.engage(w, s, kit, tg)

        def woken(self, w, s, tg):
            """Someone hit the group: HP below full, or the snapshot's awake inference."""
            return self.key in s.awake     # HP below full is no proof: damaged camps don't regenerate [A28]

        def pre(self, w, s, kit, tg):
            h = self.key
            near = min(max(abs(t[2] - s.pos.x), abs(t[3] - s.pos.y)) for t in tg)
            md = None if self.mate_pos is None else self.mate_pos.chebyshev_distance(s.pos)
            if self.role == "tank":
                if self.phase == "walk":
                    if near > kit.arange:
                        r = self.goto(w, h)
                        if r in ("full", "stuck"):
                            return self.fin(w, s, "fail", r)
                        if r != "here":
                            return "run"
                    self.phase, self.r_stage = "stage", s.rnd
                    _ev("pair", f"stage g=g{h} role=tank mate_d={md if md is not None else '-'}")
                if self.woken(w, s, tg):
                    return self.fin(w, s, "fail", "contested")
                if not self.mate_ready(s, tg, md):
                    # an ack only extends the wait while the partner shows up (fix: a Guard staged 400+ rounds
                    # at mate_d=- on a claim that never arrived)
                    lim = WAIT_ACK if self.acked(w) and md is not None else WAIT_MAX
                    if s.rnd - self.r_stage > lim:
                        return self.fin(w, s, "fail", "no_partner")
                    self.act = "wait why=hold"
                    return "run"
                # I3 gate before the first hit, live tank kit + the partner's design kit
                mons = comp_of(tg)
                if self.ready_r is None:
                    self.ready_r = s.rnd
                # Uncached (the live kit with shards misses best_pair's design-kit cache) and nothing queues it:
                # the old 1.6M-above-reserve condition held the tank 61 rounds to the hard cap (ladder 14 Oct).
                force = fuel() - RESERVE > FORCE_FUEL or s.rnd - self.ready_r >= FORCE_WAIT
                ok, p = pair_ok(w, kit, kit_of(self.mate_ct), mons, card(w, "keep_hp"), s.hp, force)
                if ok is None:
                    self.act = "wait why=hold"             # forced within FORCE_WAIT rounds
                    return "run"
                if not ok:
                    self.pred = p
                    return self.fin(w, s, "fail", "gate")
                if self.enemy_bad(w, s, kit, p[0]):
                    return self.fin(w, s, "fail", "enemy")
                self.pred = p
                self.phase, self.r_fight, self.mate_seen_r = "fight", s.rnd, s.rnd
                _ev("pair", f"engage g=g{h} wait={s.rnd - self.r_stage} mate_d={md} pred_r={p[0]} "
                            f"pred_dmg={int(p[1])} hp={int(s.hp)}")
                return self.engage(w, s, kit, tg)
            # partner: stage one step short of attack reach of the focus threat (sleeping camps are harmless
            # [measured A6]), so its first hit can follow the tank's in the same round (it acts after the Guard)
            if self.via == "plan":                        # a plan take follows a tank that claims this group
                tcl = tank_claim(w, self.gslot)
                self.noclaim = self.noclaim + 1 if tcl is not None and tcl != h else 0
                if self.noclaim > PLAN_NOCLAIM:
                    return self.fin(w, s, "fail", "no_tank")
            focus = min(fight_targets(tg), key=lambda t: t[0])
            df = max(abs(focus[2] - s.pos.x), abs(focus[3] - s.pos.y))
            ring = f"c{focus[2]}_{focus[3]}"
            if self.phase == "walk":
                if df > kit.arange + 1:
                    r = self.goto(w, ring if near <= STAGE_R + 4 else h)
                    if r in ("full", "stuck"):
                        return self.fin(w, s, "fail", r)
                    if r != "here":
                        return "run"
                self.phase, self.r_stage = "stage", s.rnd
                _ev("pair", f"stage g=g{h} role=partner mate_d={md if md is not None else '-'} d={df}")
            if HELP_ON:                                   # the tank asks elsewhere or withdrew: re-choose
                hp = help_seen(w, self.gslot)
                if hp is not None and not hp[2] and hp[0] != h and hp[0] in w.groups:
                    return self.fin(w, s, "fail", "retarget")
                if self.via == "help":
                    self.nohelp = self.nohelp + 1 if hp is None or hp[0] != h else 0
                    if self.nohelp > 3 and self.mate_pos is None:
                        return self.fin(w, s, "fail", "no_tank")
            if self.woken(w, s, tg):
                tank_in = self.mate_pos is not None and min(
                    max(abs(self.mate_pos.x - t[2]), abs(self.mate_pos.y - t[3])) for t in tg) <= \
                    max(MATE_FIGHT, kit_of(self.mate_ct).arange)
                if not tank_in:
                    return self.fin(w, s, "fail", "contested")
                mk, mons = kit_of(self.mate_ct), comp_of(tg)          # informational for the partner: never a
                p = self.pred or pair_pred(mk, kit, mons) or pair_pred(mk, kit_of(kit.ctype), mons) or \
                    quick_clear(mk, mons, mk.S + kit.S)       # (the design pair is cached by best_pair)
                self.pred = p
                self.phase, self.r_fight, self.mate_seen_r = "fight", s.rnd, s.rnd
                _ev("pair", f"engage g=g{h} wait={s.rnd - self.r_stage} mate_d={md} pred_r={p[0]} "
                            f"pred_dmg={int(p[1])} hp={int(s.hp)}")
                return self.engage(w, s, kit, tg)
            tc = tank_claim(w, self.gslot)                # the tank works another group for longer than a
            # Only rounds the tank claims a different group count (a bank trip/home/dead does not): counting
            # every non-h round caused 40 retargets and long Station aborts on elkring.
            self.away = self.away + 1 if tc is not None and tc >= 0 and tc != h else 0
            if self.away > AWAY_MAX and self.mate_pos is None:
                return self.fin(w, s, "fail", "retarget")
            if s.rnd - self.r_stage > PARTNER_WAIT:
                return self.fin(w, s, "fail", "no_tank")
            if df > kit.arange + 1 and s.can_move:
                self.goto(w, ring)
                if w.nav.moved_round == s.rnd:
                    self.act = "mv how=pair"
                    return "run"
            self.act = "wait why=hold"
            return "run"

        def mate_ready(self, s, tg, md):
            """Tank: the partner stands within one step of attack reach of a threat (it engages in the same
            round, after us), or has been within MATE_NEAR of us for READY_SLACK rounds (blocked approach)."""
            if self.mate_pos is None:
                self.near_r = None
                return False
            mp, ar = self.mate_pos, kit_of(self.mate_ct).arange
            if min(max(abs(mp.x - t[2]), abs(mp.y - t[3])) for t in fight_targets(tg)) <= ar + 1:
                return True
            if md is not None and md <= MATE_NEAR:
                if self.near_r is None:
                    self.near_r = s.rnd
                return s.rnd - self.near_r >= READY_SLACK
            self.near_r = None
            return False

        def enemy_bad(self, w, s, kit, rounds):
            """ClearCamp's entry rule: within R1 the duel gate must pass; farther (but able to arrive before
            the clear ends) only an enemy that would win the duel stops us."""
            for e in s.enemies:
                dd = e[0].chebyshev_distance(s.pos)
                if dd > R1 + rounds:
                    continue
                try:
                    dg = duel_gate(kit, s, kit_of(int(e[3].champion_name())), e[1], their_bag=e[2])
                    if (not dg.ok) if dd <= R1 else dg.ttk_us < dg.ttk_them:
                        return True
                except Exception:
                    return True
            return False

        def engage(self, w, s, kit, tg):
            h = self.key
            keep = card(w, "keep_hp") * s.max_hp
            tg_all, tg = tg, fight_targets(tg)
            rem = sum(t[0] for t in tg) if tg[0][1] > 0 else 0
            if self.expect is not None:                    # foreign damage = the mate's (or anyone's) hits
                for t in tg:
                    e = self.expect.get((t[2], t[3]))
                    if e is not None and t[0] < e - 0.5:
                        self.foreign_r = s.rnd
                        if self.f is not None:
                            self.f.shared = True
            mp = self.mate_pos
            engaged = mp is not None and min(max(abs(mp.x - t[2]), abs(mp.y - t[3])) for t in tg) <= \
                max(MATE_FIGHT, kit_of(self.mate_ct).arange)
            if engaged or s.rnd - self.foreign_r <= 1:
                self.mate_seen_r = s.rnd
                self.mate_was = True
            gone = s.rnd - self.mate_seen_r >= MATE_GONE if self.mate_was else s.rnd - self.r_fight > APPROACH
            if self.f is not None and not self.solo and gone:
                ok, p = solo_ok(kit, comp_of(tg), card(w, "keep_hp"), s.hp, kit.cds(s.rnd))
                _ev("pair", f"alone g=g{h} role={self.role} ok={int(ok)} pred={p[0]}/{int(p[1])} hp={int(s.hp)}")
                if not ok:
                    return self.go_out(w, s, "partner_left")
                self.solo = True
            if self.f is not None:
                if self.role == "tank" and not self.solo and s.hp - self.pred[1] * rem / self.rem0 < keep:
                    return self.go_out(w, s, "losing")
                mine = self.hits_on(s.pos, tg, max(1.0, self.dpr)) if self.role == "partner" else 0
                if mine and s.hp - mine < keep:                 # partner: what still lands on IT (tank: pred)
                    return self.go_out(w, s, "losing")
                if any(e[0].chebyshev_distance(s.pos) <= R1 and not duel_gate(
                        kit, s, kit_of(int(e[3].champion_name())), e[1], their_bag=e[2]).ok for e in s.enemies):
                    return self.go_out(w, s, "enemy")
            # the flee condition on what lands on ME (pair-aware for the partner; the tank takes them all)
            if self.role == "tank" or self.mate_pos is None:
                holds = flee_cond(w, s)[0]
            else:
                mine = self.hits_on(s.pos, tg)
                t_ = ttd_of(w, s, mine) if mine else FAR
                holds = t_ <= SAFE_MAX + 2 and t_ <= sts(w, s) + card(w, "flee_margin")
            if holds:
                return self.go_out(w, s, "flee")
            inc = inc_at(w, s, s.pos)
            avoid = [(q.x, q.y) for q, g in w.near(s.pos, 5) if g != h]      # never wake a neighbour (I17)
            mv = ""
            if self.role == "partner" and engaged and s.can_move:
                q, gap = self.stand_tile(w, s, kit, tg)
                if gap > 0:                                # no reach tile one step away: walk round to the
                    weak = min(tg, key=lambda t: t[0])     # focus monster's own melee ring (Nav, a field)
                    self.goto(w, f"c{weak[2]}_{weak[3]}")
                    if w.nav.moved_round == s.rnd:
                        mv = "mv"
                    elif tg_all is not tg:                 # ring full (the tank holds the only free tile):
                        q, gap = self.stand_tile(w, s, kit, tg_all)     # clear the harmless ones meanwhile
                        if q is not None and q != s.pos and w.nav.move(q):
                            mv = "mv"
                        tg = tg_all
                elif q is not None and q != s.pos and w.nav.move(q):
                    mv = "mv"
            it = plan_turn(kit, s, tg, False, inc, pos=w.nav.dest if mv else None, moved=bool(mv), avoid=avoid)
            if not mv and not it.needs_stand and s.can_move and (it.atk is None or not kit.ranged) and \
                    (self.role == "tank" or not engaged):
                want = tg[it.want] if it.want is not None and it.want < len(tg) else \
                    min(tg, key=lambda x: (max(abs(x[2] - s.pos.x), abs(x[3] - s.pos.y)), x[0]))
                if max(abs(want[2] - s.pos.x), abs(want[3] - s.pos.y)) > kit.arange:
                    if self.ring_r is None and self.goto(w, h) == "here" and \
                            not step_towards(w, s, V(want[2], want[3])):
                        self.ring_r = s.rnd                    # the target sits behind other camps (60_tasks)
                    if self.ring_r is not None and w.nav.moved_round != s.rnd and not ring_reach(self, w, s, want):
                        return self.fin(w, s, "fail", "unreach")
                    if w.nav.moved_round == s.rnd:
                        mv = "mv"
                        it = plan_turn(kit, s, tg, False, inc, pos=w.nav.dest, moved=True, avoid=avoid)
                    elif self.ring_r is None and self.goto(w, h) in ("full", "stuck"):
                        return self.fin(w, s, "fail", "stuck")
                else:
                    self.ring_r = None
            if self.f is None:
                if it.atk is None and it.cast is None:
                    self.act = mv or "wait why=hold"
                    return "run"
                p = self.pred
                kinds_ = "".join("wegGm"[c[0]] for c in group_comp(w, h))
                # the partner's own predicted damage is 0: it stands where it is never the nearest (the
                # pair prediction puts every hit on the tank); its own during-test watches what lands
                pf = p if self.role == "tank" else (p[0], 0.0, 0)
                self.f = Fight(f"g{h}", pf, s.hp, keep, kinds_, enemies=len(s.enemies))
                self.f.start(s.rnd)
                self.rem0 = max(1, rem)
                self.dpr = max(1.0, rem / max(1, p[0]))
            a = act(it, w)
            self.f.turn(it, s.rnd)
            self.expect = {(t[2], t[3]): hh for t, hh in zip(it.tg, it.hp)}
            self.fight = self.f.vs
            if a:
                self.hit = gid(h)
            self.act = ",".join(x for x in (mv, a.replace(" ", ",")) if x) or "wait why=hold"
            return "run"

        def stand_tile(self, w, s, kit, tg):
            """Partner: the tile within one step that keeps it farther than the tank from every live monster
            in range (strict first), then closest to attack reach (the weakest first), then lower-id ties,
            then the widest margin over the tank. (tile, gap): gap = steps short of attack reach from it."""
            wl = walls(w, s)
            mp, mid, me = self.mate_pos, self.mate_id, self.my_id
            live = [t for t in tg if t[0] > 0]
            if not live:
                return None, FAR
            weak = min(live, key=lambda t: t[0])
            best, bk = None, None
            for dv in (None,) + DIRS:
                q = s.pos if dv is None else s.pos + dv
                if dv is not None:
                    try:
                        if wl.is_set(q):
                            continue
                    except Exception:
                        continue
                strict = tie = 0
                margin = 0
                gap = FAR
                for t in live:
                    d = max(abs(q.x - t[2]), abs(q.y - t[3]))
                    dm = max(abs(mp.x - t[2]), abs(mp.y - t[3]))
                    if d - kit.arange < gap:
                        gap = max(0, d - kit.arange)
                    if d <= CAMP_RANGE:
                        if d < dm:
                            strict += 1
                        elif d == dm and mid is not None and me < mid:
                            tie += 1
                    margin += min(d - dm, 3)
                rw = max(abs(q.x - weak[2]), abs(q.y - weak[3])) <= kit.arange
                k = (strict, gap, not rw, tie, -margin, dv is not None)
                if bk is None or k < bk:
                    best, bk = q, k
            return best, (bk[1] if bk is not None else FAR)

        def go_out(self, w, s, why):
            _ev("pair", f"out g=g{self.key} role={self.role} why={why} hp={int(s.hp)}")
            self.fight_end(s, "abort", why)
            self.unhelp(w)
            self.phase, self.out_why, self.r_out = "out", why, s.rnd
            return self.step_out(w, s)

        def step_out(self, w, s):
            """Leave every awake range, then hold outside it until the group sleeps (2 rounds with nobody in
            range [measured A32]) so the next leg doesn't walk back into it and keep it awake; then end fail."""
            if danger(w, s).is_set(s.pos) and inc_at(w, s, s.pos) > 0:
                self.act = "mv how=out" if s.can_move and flee_step(w, s) else "wait why=blocked"
                return "run"
            if self.key in s.awake and s.rnd - self.r_out < 6:
                self.act = "wait why=hold"
                return "run"
            return self.end(s, "fail", self.out_why or "out")

        def cleared(self, w, s):
            """All dead: ONE captures (I5): the one with more room under its bank_at (CAP_HEADROOM; both read
            the same bags, gem_count() on a visible ally [sdk]), ties and an unseen mate to the lower unit id;
            the other leaves the region (I12) and logs the allowed skip."""
            h = self.key
            self.fight_end(s, "done", "cleared")
            self.unhelp(w)
            mid = self.mate_id if self.mate_pos is not None else None
            capt = mid is None or self.my_id < mid
            if mid is not None and CAP_HEADROOM:
                try:
                    mine = card(w, "bank_at") - s.bag
                    theirs = self.mate_bank - self.mate.gem_count()
                    capt = (mine, -self.my_id) > (theirs, -mid)
                except Exception:
                    pass
            if capt:
                cap = self.then = Capture(h)
                cap.start(w, s)
                cap.step(w, s)
                self.act = cap.act
                return self.end(s, "ok", "cleared")
            _ev("cap", f"skip g=g{h} why=ally_on")
            if spawn_tiles(w, h).is_set(s.pos) and s.can_move:
                for dv in DIRS:
                    q = s.pos + dv
                    try:
                        if walls(w, s).is_set(q):
                            continue
                    except Exception:
                        continue
                    if w.nav.move(q):
                        self.act = "mv"
                        break
            return self.end(s, "ok", "mate_cap")
