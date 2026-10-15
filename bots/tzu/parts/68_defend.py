# tzu: lazy
"""L5 defence doctrine (68_defend): survive a stronger, hunting opponent WITHOUT freezing.

Measured defect it answers (baseline _snap-tzu-pre vs tzunami444, 14 Oct: 5 W / 13 L, 0 deaths in 18 games): we
lose on a farming and banking stall, not on survival. collision: 44 and 88 gems tributed all game while carriers held
220+ (every Bank failed `enemy` at the one contested altar, then BANKAVOID, then BANKHOME, which carries the bag to
spawn and never tributes); interlock: Banks aborted by FLEE on an enemy that never struck (inc = full burst of every
enemy within R1). Ladder loss (the brief): a six-body opponent hunted us one at a time; we stopped banking after
round 300 with 108 gems carried. So: banking must go on when the enemy is merely present (P22: over-caution is a
fault), and the team only gathers or shrinks when the enemy is both stronger and actually striking (P3, P10, P11).

Pieces (all champion-agnostic, cheap: one quiet-turn pass is a handful of compares):
    defend_begin(w, s, dec)   every turn (dead too), after team_begin: ally deaths from the alive mask, own hits by
                              champions (hostility), the threat picture, the posture (with hysteresis), the bag-stall
                              clock. Sets w.threat (a Threat).
    threat_map(w, s)          the Threat of this round (enemy group estimate: pos, last seen, size, strength).
    posture(w)                P_FARM / P_AVOID / P_REGROUP / P_TURTLE (this champion's derived view, shared inputs).
    def_skip_mask(w, s)       Bitboard of group anchors candidates() must skip (AVOID side filter, TURTLE radius), None.
    def_bank_at(dec)          bank_at, or bank_at_threat under TURTLE (short trips).
    enemy_scale(w, s)         factor on enemy damage in inc_at: 1 when hostile (hit by a champion / an ally died
                              lately), PASSIVE_X otherwise (an enemy merely present is not a full burst every round).
    unfreeze(dec, s, why)     row tuple ("ESCORT", EscortBank, False, text) for a carrier whose bank is blocked, or None.
    stall_row(dec, s)         row tuple: BANKSTALL (bag > STALL_BAG held STALL_R rounds without a bank attempt).
    escort_row(dec, s)        row tuple ("ESCORTJOIN", Escort, True, text) for the Guard (or Flex) on a fresh SOS.
    regroup_row(dec, s)       row tuple ("REGROUP", Regroup, False, text) when a hostile, stronger group is near me alone.
    turn_row(dec, s)          row tuple ("TURN", Hunt, False, text) after a GroupRetreat met an ally and the combined
                              gate passes (P11: when equal, offer battle).
    GroupRetreat(threat, need)  Retreat with the tie-break towards the nearest visible ally (not spawn) when closer.
    tempo_choice(dec, s)      a GroupTake for the Guard/Flex pair from the first tick on a 4-5 team (plan + design kits
                              only: both pick the same group with no message), or None.
    tempo_goal(w)             the opening's walking goal for the Guard/Flex (anchor of that group), or None.
    def_sos(w, s)             True while my EscortBank asks for an escort (team_commit writes the SOS help).
Tasks: EscortBank(i) (trace name EscortBank, a Bank subclass so after_end's Bank bookkeeping applies), Escort(i),
Regroup(key). Trace: int|POSTURE old->new why= ; int|BANKSTALL ; int|ESCORT ; int|ESCORTJOIN ; int|REGROUP ;
int|TURN ; esc|wait/go/timeout lines; pair|start via=tempo.
Toggles: DEF_ON (CLAUDE.md rule 1). Wiring: the integrator applies the spec in the report (70_decide, 80_team, 90_main,
60_tasks inc_at); nothing here edits another part.
"""

if not cambc.is_draft():
    DEF_ON = dict(POSTURE=True, AVOID=True, TURTLE=True, REGROUP=True, ESCORT=True, STALL=True, JOIN=True,
                  GROUPFLEE=True, TURN=True, TEMPO=False, PASSIVE=True)
    P_FARM, P_AVOID, P_REGROUP, P_TURTLE = 0, 1, 2, 3
    P_NAME = ("FARM", "AVOID", "REGROUP", "TURTLE")
    POSTURE_HOLD = 20       # a posture holds at least this long before it de-escalates (brief) [provisional]
    GROUP_R = 6             # enemies within this of the nearest one are one group [provisional]
    GROUP_TTL = 30          # the group estimate drives AVOID this long after its last sighting [provisional]
    SIZE_MEM = 12           # a size / strength seen this recently is kept when only part of the group shows (bushes)
    FRESH = 8               # REGROUP needs a sighting this fresh [provisional]
    THREAT_R = 10           # AVOID: groups within this of the enemy group are skipped (P9) [provisional]
    REGROUP_R = 12          # a hostile stronger group this close to me starts a Regroup [provisional]
    TOGETHER = 4            # an ally this close: we are together (P10)
    KILL_TTL = 150          # ally deaths this recent count as being hunted [provisional]
    HUNTED_N = 2            # ... this many of them
    HOSTILE_TTL = 25        # rounds a champion hit on me keeps the enemy "hostile" [provisional; a hunter strikes
                            # again within this, tzunami444 hits once every ~100-300 rounds]
    KILL_HOSTILE = 80       # rounds an ally death keeps it hostile [provisional]
    PASSIVE_X = 0.35        # enemy damage factor in inc while not hostile [provisional; measured: tzunami444 dealt
                            # 0-2,000 champion damage per GAME while our flee model priced 150-390 per ROUND]
    LONE_X = 1.3            # group strength > my solo strength x this: stronger than any of us alone [provisional]
    WEAK_X = 1.2            # enemy roster strength > our alive strength x this: weaker overall [provisional]
    TURTLE_R = 14           # TURTLE: groups within this of the home altar or spawn (min map/4) [provisional]
    STALL_BAG = 60          # brief: never hold a bag > 60 ...
    STALL_R = 40            # ... for more than 40 rounds without acting
    ESCORT_WAIT = 15        # rounds an EscortBank waits for an ally before the relaxed solo bank (brief)
    ESCORT_REST = 30        # after an EscortBank timeout/fail: rounds before the next one (GoHome meanwhile)
    ESCORT_MAX = 30         # an Escort (responder) holds the altar at most this long
    ESCORT_FAR = 40         # a responder farther than this (path) from the altar ignores the SOS
    STAGE_D = 9             # EscortBank waits this far from the altar while it is hot
    ESC_X = 1.0             # go in when our power near me >= theirs near the altar x this
    LETHAL_ROUNDS = 2       # relaxed start: the enemies in reach must not kill us within this many rounds
    REGROUP_MAX = 25        # a Regroup ends after this many rounds
    TEMPO_UNTIL = 80        # tempo_choice only before this round
    TEMPO_FUEL = 900_000    # tempo table rows are scored only while this much is above the reserve
    TEMPO_SIDES = 1 | 2     # home + mid (67_group PAIR_SIDES)
    TWIN = (3, 4)           # Cassi & Issac [sdk]

    _D = dict(prev_am=None, pend={}, claims=None, kills=[], hit_r=-999, hp=None, big_since=None, stall_r=-999,
              esc_rest=-999, sos_r=-999, turn=None, tempo=None, roster=None, ours={}, sk=None, sk_r=-1, logged=-1)

    class Threat:
        __slots__ = ("rnd", "grp", "posture", "since", "want", "why", "rg", "hostile", "deaths", "me_pow")

        def __init__(self):
            self.rnd, self.grp, self.posture, self.since, self.want, self.why = -1, None, P_FARM, 0, P_FARM, "-"
            self.rg, self.hostile, self.deaths, self.me_pow = False, False, 0, 1.0

    _TP = Threat()

    # ---------------------------------------------------------------- strength (fallback until 50_kit lands its API)
    _DK = {}

    def _dk(ct):
        """(dpr vs champions, max HP) of a design kit; a middling champion when unknown."""
        r = _DK.get(ct)
        if r is None:
            try:
                k = kit_of(ct)
                r = (float(k.dpr(True)), float(k.max_hp))
            except Exception:
                r = (60.0, 1000.0)
            _DK[ct] = r
        return r

    def _enemy_rows(s, near=None, r=GROUP_R):
        """[(dpr, hp)] of the visible enemies (within r of `near` if given): 50_kit's enemy_model / 65_hunt's
        live_kit when loaded (shards grow Strength), else the design kit scaled by the live Strength."""
        out = []
        lk = globals().get("live_kit")
        for p, hp, bag, ch in s.enemies:
            if near is not None and p.chebyshev_distance(near) > r:
                continue
            d = None
            if lk is not None:
                try:
                    d = float(lk(ch, s.rnd, s).dpr(True, bag))
                except Exception:
                    d = None
            if d is None:
                try:
                    ct = int(ch.champion_name())
                    k = kit_of(ct)
                    d = k.dpr(True, bag) * max(1.0, ch.strength() / max(1.0, k.S))
                except Exception:
                    d = 60.0
            out.append((d, float(hp)))
        return out

    def _pow(rows):
        """Lanchester square-law strength: sum dpr x sum HP (P10/P11: concentration counts twice)."""
        if not rows:
            return 0.0
        return sum(r[0] for r in rows) * sum(r[1] for r in rows)

    def _roster(w):
        """[(dpr, hp)] of every enemy body, from the draft's enemy profiles; unknown picks = middling champions;
        Cassi & Issac = two bodies. Cached."""
        r = _D["roster"]
        if r is not None:
            return r
        out = []
        plan = w.plan if w.plan_ok else None
        n = plan.team_size if plan is not None else 3
        known = 0
        if plan is not None:
            for e in range(5):
                try:
                    row = plan.enemies[e]
                except Exception:
                    row = None
                if row is None:
                    continue
                known += 1
                ct = int(row.ctype)
                if ct in TWIN:
                    out.append(_dk(TWIN[0]))
                    out.append(_dk(TWIN[1]))
                else:
                    out.append(_dk(ct))
        for _ in range(max(0, n - known)):
            out.append((60.0, 1000.0))
        _D["roster"] = out
        return out

    def _ours(w, am):
        """Our alive strength from the cards' design kits (alive mask am), cached per mask."""
        c = _D["ours"].get(am)
        if c is not None:
            return c
        plan = w.plan if w.plan_ok else None
        rows = []
        if plan is not None:
            for i in range(plan.team_size):
                if am >> i & 1:
                    try:
                        rows.append(_dk(plan.cards[i].ctype))
                    except Exception:
                        pass
        c = _D["ours"][am] = _pow(rows) if rows else 1.0
        return c

    # ---------------------------------------------------------------- the per-turn picture
    def _team(w):
        t = getattr(w, "team", None)
        return t if t is not None and getattr(t, "ready", False) else None

    def _death_pos(w, code, slot):
        """Where an ally probably died: its last claimed group's anchor, its home altar while banking."""
        if code is not None and code >= 0 and code in w.anchor:
            return w.anchor[code]
        if code == CLAIM_BANK and w.plan_ok:
            try:
                i = w.plan.cards[slot].home_altar
                if i != 255 and i < len(w.altar_pos):
                    return w.altar_pos[i]
            except Exception:
                pass
        return None

    def _watch_deaths(w, s, t):
        """Ally deaths from the alive mask (heartbeat): a bit that went 1 -> 0 and stayed 0 for 2 rounds (a fuel
        suspension recovers sooner). Backdated to the flip; position from the claim it held."""
        am = t.alive_mask
        pv = _D["prev_am"]
        pend = _D["pend"]
        size = w.plan.team_size if w.plan_ok else 5
        if pv is not None and am != pv and s.rnd > 10:
            gone = pv & ~am
            for i in range(size):
                if gone >> i & 1 and i != t.slot:
                    code = _D["claims"][i] if _D["claims"] is not None else None
                    pend[i] = (s.rnd, _death_pos(w, code, i))
        for i in list(pend):
            if am >> i & 1:
                del pend[i]                                   # back: a suspension, not a death
            elif s.rnd - pend[i][0] >= 2:
                r0, p = pend.pop(i)
                try:
                    out = w.mem.claim_raw(i) == 63            # a dead champion writes OUT on its first dead turn
                except Exception:
                    out = True
                if not out:
                    continue                                  # never wrote OUT: a fuel suspension, not a death
                _D["kills"].append((r0, p))
                ev("int", f"ALLYDEAD slot={i} r={r0} at={'-' if p is None else f'{p.x},{p.y}'}")
        _D["prev_am"] = am
        _D["claims"] = list(t.claims)

    def defend_begin(w, s, dec=None):
        """Skeleton step 2b (every turn, after team_begin). Cheap on quiet turns."""
        tp = _TP
        if tp.rnd == s.rnd:
            return tp
        tp.rnd = s.rnd
        w.threat = tp
        t = _team(w)
        if t is not None:
            _watch_deaths(w, s, t)
        kills = _D["kills"]
        while kills and kills[0][0] < s.rnd - KILL_TTL:
            kills.pop(0)
        if not s.alive:
            if _D["hp"] is not None:                          # my own death: the enemy is there (P6)
                kills.append((s.rnd, w.last_pos))
                _D["hp"] = None
            _D["big_since"] = None
            return tp
        # hostility: my HP dropped with an enemy in reach and no awake monster on me (60_tasks' sense() infers the
        # reverse); an ally death counts too
        old, _D["hp"] = _D["hp"], s.hp
        if old is not None and s.hp < old and s.enemies and \
                any(e[0].chebyshev_distance(s.pos) <= R1 for e in s.enemies) and not _camp_on(w, s):
            _D["hit_r"] = s.rnd
        last_kill = kills[-1][0] if kills else -999
        tp.hostile = s.rnd - _D["hit_r"] <= HOSTILE_TTL or s.rnd - last_kill <= KILL_HOSTILE
        tp.deaths = len(kills)
        # bag-stall clock: rounds with bag > STALL_BAG since the last bank attempt
        if s.bag > STALL_BAG:
            if _D["big_since"] is None:
                _D["big_since"] = s.rnd
        else:
            _D["big_since"] = None
        _group(w, s, t, tp)
        if DEF_ON["POSTURE"]:
            _posture(w, s, t, tp, dec)
        return tp

    def _camp_on(w, s):
        f = globals().get("_camp_hits")
        if f is not None:
            try:
                return f(w, s, s.pos)
            except Exception:
                return False
        return bool(s.awake)

    def _group(w, s, t, tp):
        """The enemy group estimate [pos, last seen round, size, strength]: visible enemies first (exact), else
        the team sighting, else an ally's death site. Sizes seen in the last SIZE_MEM rounds are kept (P6)."""
        g = tp.grp
        if s.enemies:
            n = min(s.enemies, key=lambda e: e[0].chebyshev_distance(s.pos))[0]
            rows = _enemy_rows(s, n, GROUP_R)
            size, es = len(rows), _pow(rows)
            if g is not None and s.rnd - g[1] <= SIZE_MEM and g[0].chebyshev_distance(n) <= 2 * GROUP_R:
                size, es = max(size, g[2]), max(es, g[3])
            tp.grp = [n, s.rnd, size, es]
            return
        sg = t.sighting if t is not None else None
        if sg is not None and (g is None or s.rnd - sg[2] > g[1]):
            p = V(sg[0], sg[1])
            size = 2 if (t.variant == "B" and sg[4] & 2) else 1
            ro = _roster(w)
            avg = (sum(r[0] for r in ro) / len(ro), sum(r[1] for r in ro) / len(ro)) if ro else (60.0, 1000.0)
            es = _pow([avg] * size)
            if g is not None and s.rnd - g[1] <= SIZE_MEM and g[0].chebyshev_distance(p) <= 2 * GROUP_R:
                size, es = max(size, g[2]), max(es, g[3])
            tp.grp = [p, s.rnd - sg[2], size, es]
            return
        kills = _D["kills"]
        if kills and kills[-1][1] is not None and (g is None or kills[-1][0] > g[1]):
            ro = _roster(w)
            avg = (sum(r[0] for r in ro) / len(ro), sum(r[1] for r in ro) / len(ro)) if ro else (60.0, 1000.0)
            sz = max(2, g[2] if g is not None else 2)
            tp.grp = [kills[-1][1], kills[-1][0], sz, _pow([avg] * sz)]

    def _home_pos(w, dec):
        i = None
        try:
            i = card(w, "home_altar")
        except Exception:
            pass
        if i is not None and i != 255 and i < len(w.altar_pos):
            return w.altar_pos[i]
        return w.anchor.get("altar")

    def _posture(w, s, t, tp, dec):
        """FARM < AVOID < REGROUP < TURTLE. Escalates at once, de-escalates after POSTURE_HOLD rounds. Every rule
        needs hostility (we were struck or lost a champion lately): a merely present enemy changes nothing (P22)."""
        kit = dec.kit if dec is not None and getattr(dec, "kit", None) is not None else None
        me_pow = (kit.dpr(True) if kit is not None else 60.0) * max(1.0, s.hp)
        tp.me_pow = me_pow
        g = tp.grp
        want, why = P_FARM, "-"
        tp.rg = False
        if tp.hostile and g is not None:
            age = s.rnd - g[1]
            strong = g[3] > me_pow * LONE_X
            if strong and age <= GROUP_TTL and DEF_ON["AVOID"]:
                want, why = P_AVOID, f"g={g[0].x},{g[0].y} age={age} size={g[2]}"
            if strong and age <= FRESH and g[2] >= 2:
                dm = g[0].chebyshev_distance(s.pos)
                hp_ = _home_pos(w, dec)
                dh = g[0].chebyshev_distance(hp_) if hp_ is not None else FAR
                if dm <= REGROUP_R or dh <= REGROUP_R:
                    tp.rg = dm <= REGROUP_R
                    if DEF_ON["REGROUP"]:
                        want, why = P_REGROUP, f"g={g[0].x},{g[0].y} age={age} size={g[2]} d={dm} dh={dh}"
        if DEF_ON["TURTLE"] and t is not None and tp.deaths >= HUNTED_N:
            ours, theirs = _ours(w, t.alive_mask), _pow(_roster(w))
            if theirs > ours * WEAK_X:
                want, why = P_TURTLE, f"deaths={tp.deaths} ours={int(ours)} theirs={int(theirs)}"
        tp.want = want
        cur = tp.posture
        if want >= cur:
            if want != cur:
                _set_posture(tp, s, want, why)
            tp.since = s.rnd
        elif s.rnd - tp.since >= POSTURE_HOLD:
            _set_posture(tp, s, want, why)
            tp.since = s.rnd

    def _set_posture(tp, s, p, why):
        ev("int", f"POSTURE {P_NAME[tp.posture]}->{P_NAME[p]} why={why}")
        tp.posture, tp.why = p, why
        _D["sk_r"] = -1

    def threat_map(w, s):
        return _TP if _TP.rnd == s.rnd else defend_begin(w, s)

    def posture(w=None):
        return _TP.posture

    def def_skip_mask(w, s):
        """Bitboard of tiles whose groups candidates() skips this round (AVOID: the enemy group's side, P9;
        TURTLE: everything outside the home altar / spawn disks, P3), or None. Once per round."""
        if _D["sk_r"] == s.rnd:
            return _D["sk"]
        _D["sk_r"] = s.rnd
        tp, m = _TP, None
        g = tp.grp
        if tp.posture >= P_AVOID and g is not None and s.rnd - g[1] <= GROUP_TTL:
            m = Bitboard()
            m.draw_chebyshev(g[0], THREAT_R)
        if tp.posture == P_TURTLE:
            r = max(TURTLE_R, min(w.W, w.H) // 4)
            ok = Bitboard()
            h = _home_pos(w, None)
            if h is not None:
                ok.draw_chebyshev(h, r)
            sp = w.anchor.get("spawn")
            if sp is not None:
                ok.draw_chebyshev(sp, r)
            m = (~ok) if m is None else (m | ~ok)
        _D["sk"] = m
        return m

    def def_bank_at(dec):
        b = dec.c("bank_at")
        if _TP.posture == P_TURTLE:
            return min(b, dec.c("bank_at_threat"))
        return b

    def enemy_scale(w, s):
        """Factor on enemy damage in inc_at: full once they strike (or an ally died), PASSIVE_X before."""
        if not DEF_ON["PASSIVE"] or _TP.rnd != s.rnd:
            return 1.0
        return 1.0 if _TP.hostile else PASSIVE_X

    # ---------------------------------------------------------------- carriers: escort and unfreeze
    def _guard_altar(w, dec):
        """The rendezvous: the acting Guard's home altar (static, every champion knows it: no bits), else mine."""
        t = _team(w)
        g = t.guard if t is not None else None
        if g is not None and dec is not None and dec.cards and g < len(dec.cards):
            i = dec.cards[g].home_altar
            if i != 255 and i < len(w.altar_pos):
                return i
        try:
            i = card(w, "home_altar")
            if i != 255 and i < len(w.altar_pos):
                return i
        except Exception:
            pass
        return 0 if w.altar_pos else None

    def unfreeze(dec, s, why):
        """A carrier whose Bank is blocked (no altar passes bank_target) banks WITH an escort instead of
        carrying the bag home (BANKHOME never tributes). None while resting after a failed escort."""
        if not DEF_ON["ESCORT"] or s.bag <= 0 or s.rnd - _D["esc_rest"] < ESCORT_REST:
            return None
        i = _guard_altar(dec.w, dec)
        if i is None:
            return None
        return "ESCORT", EscortBank(i), False, f"bag={s.bag} why={why} altar=a{i}"

    def stall_row(dec, s):
        """Brief: never hold a bag > STALL_BAG for STALL_R rounds without acting. Logs int|BANKSTALL (the metric)."""
        if not DEF_ON["STALL"]:
            return None
        b = _D["big_since"]
        if b is None or s.rnd - b < STALL_R:
            return None
        _D["big_since"] = s.rnd                               # one line per STALL_R rounds of stall
        r = unfreeze(dec, s, "stall")
        if r is None:
            return "BANKSTALL", GoHome("bank"), False, f"bag={s.bag} r={s.rnd - b} how=home"
        return "BANKSTALL", r[1], False, f"bag={s.bag} r={s.rnd - b} how=escort altar=a{r[1].i}"

    def def_sos(w, s):
        return DEF_ON["ESCORT"] and s.rnd - _D["sos_r"] <= 1

    def _power_near(w, s, kit, r=TOGETHER + 1):
        """(our power: me + visible allies within r, number of those allies)."""
        rows = [(kit.dpr(True) if kit is not None else 60.0, float(s.hp))]
        ar = globals().get("allies_rows")
        n = 0
        if ar is not None:
            try:
                for q, ct, hp in ar(w, s):
                    if q.chebyshev_distance(s.pos) <= r:
                        rows.append((_dk(ct)[0], float(hp)))
                        n += 1
            except Exception:
                pass
        return _pow(rows), n

    def _their_power(w, s, a):
        """Power of the enemies at altar tile a: visible within R1 + 3, plus fresh (3 rounds) unseen sightings."""
        rows = _enemy_rows(s, a, R1 + 3)
        if not rows:
            fresh = [q for r, q in _S["seen"] if r >= s.rnd - 3 and q.chebyshev_distance(a) <= R1 + 3]
            fresh += [q for q, e in team_sight(w, s, 3) if q.chebyshev_distance(a) <= R1 + 3 + e]
            if fresh:
                ro = _roster(w)
                avg = (sum(r[0] for r in ro) / len(ro), sum(r[1] for r in ro) / len(ro)) if ro else (60.0, 1000.0)
                rows = [avg]
        return _pow(rows), len(rows)

    class EscortBank(Bank):
        """Bank with the doctrine's checks instead of Bank's 'any enemy near the altar -> fail':
        go in when our power near me (allies within TOGETHER + 1) >= theirs near the altar; else wait at STAGE_D
        (outside their reach) asking for an escort (SOS) up to ESCORT_WAIT rounds; then go anyway if the enemies
        in reach cannot kill us within LETHAL_ROUNDS (a stun only breaks the channel: time, not gems [rules]),
        else end fail why=escort_timeout (the caller goes home). The channel is cancelled when the flee condition
        holds (I2), which Bank never re-checks."""
        name = "EscortBank"

        def start(self, w, s):
            Bank.start(self, w, s)
            self.waited = 0
            self.go = False
            self.how = "-"

        def step(self, w, s):
            me = w.me
            if self.ch:
                if s.st & ST_SUBMITTING:
                    if flee_cond(w, s)[0]:
                        try:
                            me.cancel_submit_gems()
                        except Exception:
                            pass
                        _ev("bank", f"end cancel by=danger gems=0 took={s.rnd - self.c0} pred={self.ticks}")
                        self.ch = False
                        _D["esc_rest"] = s.rnd
                        return self.end(s, "fail", "danger")
                    self.act = "ch"
                    return "run"
                return Bank.step(self, w, s)                  # completion / broken bookkeeping
            if s.bag <= 0:
                return self.end(s, "ok", "empty")
            a = self.altar(w, s)
            if a is None:
                return self.end(s, "fail", "no_altar")
            kit = KIT
            if not self.go:
                ours, n = _power_near(w, s, kit)
                theirs, ne = _their_power(w, s, a)
                if theirs <= 0 or ours >= theirs * ESC_X:
                    self.go, self.how = True, f"escort n={n}" if n else "clear"
                elif self.waited >= ESCORT_WAIT:
                    if self.lethal(w, s, a):
                        _ev("esc", f"timeout bag={s.bag} theirs={ne} waited={self.waited}")
                        _D["esc_rest"] = s.rnd
                        return self.end(s, "fail", "escort_timeout")
                    self.go, self.how = True, "relaxed"
                else:
                    self.waited += 1
                    _D["sos_r"] = s.rnd
                    d = a.chebyshev_distance(s.pos)
                    if self.waited == 1:
                        _ev("esc", f"wait bag={s.bag} altar={a.x},{a.y} d={d} ours={int(ours)} theirs={int(theirs)} ne={ne}")
                    if d > STAGE_D:
                        w.risk = None                         # stage outside their reach: no I11 hold on the way
                        r = self.goto(w, self.key)
                        if r in ("full", "stuck"):
                            return self.end(s, "fail", r)
                        return "run"
                    if danger(w, s).is_set(s.pos) and s.can_move and flee_step(w, s):
                        self.act = "mv how=fl"
                        return "run"
                    self.act = "wait why=hold"
                    return "run"
                _ev("esc", f"go bag={s.bag} how={self.how} waited={self.waited}")
            w.risk = None                                     # committed: the escort / the gate replaces I11's hold
            r = self.goto(w, self.key)
            if r in ("full", "stuck"):
                return self.end(s, "fail", r)
            if r != "here":
                return "run"
            self.pos = a
            if vision.has_altar_lock(a) and not vision.altar_lock_at(a).is_ally():
                return self.end(s, "fail", "locked")         # I13: 70_decide's after_end runs ClearLock
            if self.lethal(w, s, s.pos):
                return self.end(s, "fail", "enemy")
            k = max(1, -(-s.bag // 10))
            me.submit_gems(a)
            self.ch, self.c0, self.g0, self.ticks = True, s.rnd, s.bag, k
            ed = min((e[0].chebyshev_distance(s.pos) for e in s.enemies), default=None)
            _ev("bank", f"start altar={a.x},{a.y} gems={s.bag} ticks={k} lock=- enemy={'-' if ed is None else ed} "
                        f"stunner=- how={self.how}")
            self.act = "ch"
            return "run"

        def end(self, s, status, why):
            if status != "ok":
                _D["esc_rest"] = s.rnd                        # any failed / pre-empted escort rests ESCORT_REST rounds
            return Bank.end(self, s, status, why)            # (a fail at the altar re-picked every turn: died there)

        def lethal(self, w, s, p):
            """The enemies within R1 + 1 of p could take us below keep_hp within LETHAL_ROUNDS (live burst)."""
            dmg = sum(enemy_dpr(e[3], e[2], True) for e in s.enemies if e[0].chebyshev_distance(p) <= R1 + 1)
            return dmg * LETHAL_ROUNDS >= s.hp - card(w, "keep_hp") * s.max_hp

    class Escort(Task):
        """Responder to an SOS (P19 unity, P3 guard the bank): walk to the rendezvous altar and hold its ring until
        the SOS has been quiet for 3 rounds or ESCORT_MAX rounds; lower rows (DENY, HOLD...) still fire there."""
        name = "Escort"

        def __init__(self, i):
            Task.__init__(self, f"a{i}")
            self.i = i

        def step(self, w, s):
            tm = _team(w)
            hp = tm.help if tm is not None else None
            if hp is not None and hp[2]:
                self.quiet = 0
            else:
                self.quiet = getattr(self, "quiet", 0) + 1
            if self.quiet >= 3:
                return self.end(s, "ok", "quiet")
            if s.rnd - self.r0 >= ESCORT_MAX:
                return self.end(s, "ok", "timeout")
            if w.dist(self.key, s.pos) == 0:
                self.act = "wait why=hold"
                return "run"
            r = self.goto(w, self.key)
            if r in ("full", "stuck"):
                return self.end(s, "fail", r)
            if r == "here":
                self.act = "wait why=hold"
            return "run"

    def escort_row(dec, s):
        """The Guard (or, with no Guard alive, the Flex) answers a fresh SOS: Escort to the rendezvous altar. Not
        while carrying a big bag itself, not on a channel, not mid-fight, not already there."""
        if not DEF_ON["JOIN"]:
            return None
        w = dec.w
        t = _team(w)
        if t is None or t.help is None or not t.help[2] or t.help[1] > 1:
            return None
        if s.rnd - _D["sos_r"] <= 1:
            return None                                       # I am the one asking
        role = dec.role
        if role != ROLE_GUARD and not (role == ROLE_FLEX and t.guard is None):
            return None
        task = dec.task
        name = task.name if task is not None else None
        if name in ("Escort", "Flee", "Bank", "EscortBank", "GoHome", "Hunt", "Hold", "Deny", "ClearLock", "Capture") \
                or (name in ("ClearCamp", "GroupTake") and getattr(task, "f", None) is not None):
            return None
        if s.bag >= dec.c("bank_at_threat"):
            return None
        i = _guard_altar(w, dec)
        if i is None:
            return None
        d = w.dist(f"a{i}", s.pos)
        if d is None or d > ESCORT_FAR:
            return None
        return "ESCORTJOIN", Escort(i), True, f"altar=a{i} d={d}"

    # ---------------------------------------------------------------- regroup and group retreat (P10, P11, P19)
    class Regroup(Task):
        """Walk to the nearest visible ally, else the rendezvous altar; never towards the enemy group. Ends when an
        ally is within TOGETHER, the group is stale or far, or REGROUP_MAX rounds."""
        name = "Regroup"

        def step(self, w, s):
            tp = _TP
            g = tp.grp
            if g is None or s.rnd - g[1] > FRESH + 4 or g[0].chebyshev_distance(s.pos) > REGROUP_R + 4:
                return self.end(s, "ok", "clear")
            if s.rnd - self.r0 >= REGROUP_MAX:
                return self.end(s, "ok", "timeout")
            a = _nearest_ally(w, s)
            if a is not None and a[1] <= TOGETHER:
                return self.end(s, "ok", "together")
            if a is not None and a[0].chebyshev_distance(g[0]) > g[0].chebyshev_distance(s.pos) - 1:
                if not s.can_move:
                    self.act = "wait why=blocked"
                    return "run"
                if step_towards(w, s, a[0]):
                    self.act = "mv how=rg"
                    return "run"
            r = self.goto(w, self.key)
            if r in ("full", "stuck"):
                return self.end(s, "fail", r)
            if r == "here":
                self.act = "wait why=hold"
            return "run"

    def _nearest_ally(w, s):
        ar = globals().get("allies_rows")
        if ar is None:
            return None
        try:
            rows = ar(w, s)
        except Exception:
            return None
        best = None
        for q, ct, hp in rows:
            d = q.chebyshev_distance(s.pos)
            if best is None or d < best[1]:
                best = (q, d)
        return best

    def regroup_row(dec, s):
        tp = _TP
        if not DEF_ON["REGROUP"] or not tp.rg or tp.posture < P_REGROUP:
            return None
        task = dec.task
        name = task.name if task is not None else None
        if name in ("Regroup", "Flee", "Bank", "EscortBank", "GoHome", "Capture", "Hunt", "Hold", "Deny", "Escort") \
                or (name in ("ClearCamp", "GroupTake") and getattr(task, "f", None) is not None):
            return None
        a = _nearest_ally(dec.w, s)
        if a is not None and a[1] <= TOGETHER:
            return None
        i = _guard_altar(dec.w, dec)
        g = tp.grp
        return "REGROUP", Regroup(f"a{i}" if i is not None else "altar"), False, \
            f"g={g[0].x},{g[0].y} size={g[2]} es={int(g[3])} me={int(tp.me_pow)} ally={'-' if a is None else a[1]}"

    _GR = [None]

    def GroupRetreat(threat="camp", need=None):
        """Factory: Retreat lives in 70_decide (loaded after this part), so the subclass is built on first use."""
        c = _GR[0]
        if c is None:
            c = _GR[0] = _make_group_retreat()
        return c(threat, FLEE_OK if need is None else need)

    def _make_group_retreat():
        class GroupRetreat(Retreat):
            """Retreat whose tie-break is the nearest visible ally when it is closer than spawn (fleeing alone is how
            the ladder opponent killed us 14 times); meeting it (within 2) with the combined gate passing ends the
            retreat (why=together) and arms turn_row (P11: when equal, offer battle)."""

            def step(self, w, s):
                if DEF_ON["TURN"] and self.threat != "camp" and s.enemies and not flee_cond(w, s)[0]:
                    a = _nearest_ally(w, s)
                    jt = globals().get("join_target")
                    if a is not None and a[1] <= 2 and jt is not None:
                        try:
                            r = jt(w, s, a[0], KIT)
                        except Exception:
                            r = None
                        if r is not None:
                            _D["turn"] = (s.rnd, r)
                            return self.end(s, "ok", "together")
                return Retreat.step(self, w, s)

            def away(self, w, s, d, foes):
                if not DEF_ON["GROUPFLEE"]:
                    return Retreat.away(self, w, s, d, foes)
                a = _nearest_ally(w, s)
                pos = s.pos
                sp0 = w.dist("spawn", pos)
                sp0 = FAR if sp0 is None else sp0
                if a is None or a[1] >= sp0 or a[1] <= 1:
                    return Retreat.away(self, w, s, d, foes)
                tgt = a[0]
                wl = walls(w, s)
                cap = R1 + 4
                e0 = min(min((q.chebyshev_distance(pos) for q in foes), default=FAR), cap)
                t0 = tgt.chebyshev_distance(pos)
                best = None
                for dv in DIRS:
                    q = pos + dv
                    try:
                        if wl.is_set(q) or d.is_set(q):
                            continue
                    except Exception:
                        continue
                    e = min(min((f.chebyshev_distance(q) for f in foes), default=FAR), cap)
                    td = tgt.chebyshev_distance(q)
                    if not (e > e0 or (e == e0 and td < t0)):
                        continue
                    sc = (e, -td)
                    if best is None or sc > best[0]:
                        best = (sc, q)
                return best is not None and w.nav.move(best[1])
        return GroupRetreat

    def turn_row(dec, s):
        t = _D["turn"]
        if t is None or t[0] < s.rnd - 1:
            return None
        _D["turn"] = None
        ch, text = t[1]
        return "TURN", Hunt(ch), False, text

    # ---------------------------------------------------------------- early tempo: the pair take from the first tick
    def _tempo_table(dec, st):
        """Resumable (I9: one pass cost a skipped turn on the first tick): st = [next h, best, sol, g, p, kits].
        Returns (h, rate, g, p), False (nothing beats solo / no pair), or None (not finished: fuel). Rate: (gems +
        gold x A41) / (d_ours + quick_clear at the summed sustained camp dpr + 5) on rows the draft marked `take`
        (no solo, pair clears) on TEMPO_SIDES; it must beat the two best plan solo rates (same model) summed (P10).
        Deterministic: the tank and the partner compute the same answer from draft memory and design kits."""
        plan = dec.plan
        if not st:
            ps = globals().get("pair_slots")
            if plan is None or ps is None or dec.size < 4:
                return False
            g, p = ps(dec)
            if g is None or p is None or dec.slot not in (g, p):
                return False
            gk, pk = kit_of(dec.cards[g].ctype), kit_of(dec.cards[p].ctype)
            st.extend([0, None, {g: 0.0, p: 0.0}, g, p, (gk, pk, gk.dpr(), pk.dpr())])
        g, p = st[3], st[4]
        gk, pk, gd, pd = st[5]
        lim = gk.max_hp * (1 - CARD_DEFAULTS[ROLE_GUARD]["keep_hp"] / 100)
        fl, solo = plan.groups.column(11), plan.groups.column(12)
        sol = st[2]
        n = len(plan.groups)
        while st[0] < n:
            if fuel() - RESERVE < TEMPO_FUEL:
                return None
            h = st[0]
            st[0] += 1
            if h not in dec.w.groups:
                continue
            r = plan.groups[h]
            if r.d_ours == 255:
                continue
            val = r.gems + r.gold * GOLD_GEM
            comp = _row_comp(r)
            for sl, k, kd in ((g, gk, gd), (p, pk, pd)):
                if solo[h] >> sl & 1:
                    q = quick_clear(k, comp, kd)
                    if q[0] < FAR:
                        sol[sl] = max(sol[sl], val / (r.d_ours + q[0] + CAP_FIXED))
            # the draft's `take` bit (fl & 4) is never set by the fixed plan (no Flex card at draft time: take=0 in
            # every plan line), so: a row neither of the pair solos, no monolith, on TEMPO_SIDES (67's _pair_rows)
            if solo[h] >> g & 1 or solo[h] >> p & 1 or not TEMPO_SIDES >> (fl[h] & 3) & 1 or fl[h] >> 3 & 3:
                continue
            q = quick_clear(gk, comp, gd + pd)
            if q[0] >= FAR or q[1] * GATE_X >= lim:
                continue
            rate = val / (r.d_ours + q[0] + CAP_FIXED)
            if st[1] is None or rate > st[1][1]:
                st[1] = (h, rate)
        best = st[1]
        ev("pair", f"tempo best={'-' if best is None else f'g{best[0]}:{best[1]:.2f}'} solo={sol[g]:.2f}+{sol[p]:.2f}")
        if best is None or best[1] <= sol[g] + sol[p]:
            return False
        return (best[0], best[1], g, p)

    def tempo_choice(dec, s):
        """Wiring: first thing in Decider.choose (before pair_choice), only before TEMPO_UNTIL. Once per game per
        champion: when the take ends (or is not chosen) pair_choice takes over."""
        if not DEF_ON["TEMPO"] or s.rnd > TEMPO_UNTIL or dec.slot is None or not dec.cards:
            return None
        tb = _D["tempo"]
        if tb is None:
            st = _D.setdefault("tempo_st", [])
            r = _tempo_table(dec, st)
            if r is None:
                return None
            tb = _D["tempo"] = r
        if not tb or tb == "used":
            return None
        h, rate, g, p = tb
        if dec.slot not in (g, p) or dec.cool.get(h, -1) > s.rnd or h in dec.claimed():
            return None
        if s.bag >= dec.c("bank_at") or s.hp < dec.c("recall_hp") * s.max_hp:
            return None
        _D["tempo"] = "used"
        tank = dec.slot == g
        mate = p if tank else g
        mb = getattr(dec.cards[mate], "bank_at", 40) or 40
        return GroupTake(h, "tank" if tank else "partner", dec.cards[mate].ctype, via="tempo", rate=rate, gslot=g,
                         mate_bank=mb)

    def tempo_goal(w):
        """Opening walk goal for the Guard/Flex of a 4-5 team (plan only, before the Decider exists): the anchor
        of the nearest `take` row on TEMPO_SIDES, else None (90_main keeps its route goal)."""
        if not DEF_ON["TEMPO"] or not w.plan_ok:
            return None
        plan = w.plan
        if plan.team_size < 4:
            return None
        c = plan.card_for(w.ctype)
        if c is None or c.role not in (ROLE_GUARD, ROLE_FLEX):
            return None
        fl = plan.groups.column(11)
        dd = plan.groups.column(7)
        best = None
        for h in range(len(plan.groups)):
            if fl[h] & 4 and TEMPO_SIDES >> (fl[h] & 3) & 1 and not fl[h] >> 3 & 3 and dd[h] != 255 \
                    and h in w.anchor and (best is None or dd[h] < best[0]):
                best = (dd[h], h)
        return w.anchor[best[1]] if best is not None else None
