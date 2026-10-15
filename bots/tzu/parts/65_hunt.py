# tzu: lazy
"""L4 fight tasks (ROLES_AND_LAYERS.md §3 L4): Hunt(enemy) and Hold(tile) (defined here only), plus the gate helpers L5 uses for
INVARIANTS.md §2 rows 4, 5 and 6 (the wiring spec is at the end of this docstring).

Hunt(enemy)   target -> pursue (cut it off on its way to safety) -> strike (L3 plan_turn/act) -> the gate every
              turn; a gate that flips disengages the same turn (step / dash away from every enemy, toward allies
              and spawn, never through the enemy), then ends.
              ok   why=killed   the enemy died to us (its bag + 50 gold [rules]); `hunt|kill gain= gold=` logged
              fail why=gate | outnumbered | stronger | chase | fled | bush | lost | spawn | no_kit
Hold(tile)    stand on / next to the tile (capture spawn tile, altar ring), fight what comes if the gate
              passes, else leave. ok why=released (L5 calls release()) | clear (no enemy for HOLD_CALM
              rounds); fail why=gate | flee | outnumbered | timeout.
Both log fight|start vs=c<id> ... ttk=<ours>/<theirs> before the first hit and fight|end through L3's Fight.

The gate (I3, one duel model): L3's duel_gate on the enemy's LIVE kit (Strength / Focus incl. bought shards;
50_kit's enemy_model when it lands), allies' dpr within R1 of the enemy (P10), the summed bag of an enemy
Cassi & Issac (one dies, both die [rules]); a target that stands still (tribute or recall channel, P15/P20)
gets its remaining channel rounds added to our time-to-die. Their opening turn is a burst. The fight must leave
keep_hp (pred x GATE_X < hp - keep, the I3 line). Not outnumbered (P11): no second enemy can reach the fight
tile within ttk_them rounds (R1 + ttk - 1) unless as many allies stand within R1 of it. Not toward strength:
the Lanchester strength (sum HP x sum dpr) of everything visible around the fight tile must favour us.
Never into or next to the enemy spawn region (P21: leave an outlet), never past chase_max (P23).

Targets (carrier_target, P8 strike weakness): score = (bag + 50 gold x A41 + STILL_BONUS if channelling +
LOW_BONUS x missing HP fraction) / ttk_them; a target moving away beyond our reach this turn is skipped (a
chase we can't win is farming time lost, measured 14-28 failed hunts per game). The Guard hunts only carriers
within GUARD_ALTAR_R of its home altar (defence by attack). Finishing (P20): a target whose HP is below what we
deal this turn (attack + reset + best ready spell, with walk/dash reach) is struck past the gate and
even inside a camp's range, provided nothing visible kills us this turn. A recalling target: any damage cancels
the recall [rules], so one hit lands the value of the chase.

WIRING SPEC (70_decide, applied by the integrator; INT_ON["HUNT"] = INT_ON["JOIN"] = INT_ON["HOLD"] = True;
tested as runs/_tzuhunt2/hunt2_driver.py):
 row 2  skip FLEE (and row 3 EVADE) this turn when name == "Hunt" and hunt_keep(w, s, t, ttd_): only the hunted
        pair within R1, no camp hits us, the gate still passes (or we finish it this turn). We don't run from
        the single enemy we are predicted to beat.
 row 3  unchanged (self.gate on the design kit). Do NOT switch it, nor watch_threats, to hunt_gate: hunt_gate is
        an attack gate (keep_hp, outnumbered, stronger, spawn); as a threat test it flagged every altar and the
        Hunter carried 242 gems for 800 rounds (measured 14 Oct, collision).
 row 4  name == "Capture" and s.enemies and may_fight(w): r = hold_target(w, s, tile, kit); r and r[1] -> HOLD.
 row 5  unchanged: r = carrier_target(w, s, self.cur_vpr(s), kit) -> "HUNT", Hunt(r[0]), True, r[1] (the Guard's
        GUARD_ALTAR_R filter, the HUNT_TTK and HUNT_CLOSE start limits are inside).
 row 6  name not in (Hunt, Hold, Bank, Deny, Flee, GoHome) and may_fight(w): per visible ally within JOIN_R whose HP
        dropped: r = join_target(w, s, ap, kit) -> "JOIN", Hunt(r[0]), True, ...
 rows 7, AWAKE, 9 and the STALL row: skip them (self.blk = 0) while hunt_busy(w, s, t): a Hunt / Hold with an
        open fight whose target is in this turn's reach and passes the gate or dies this turn.
"""

if not cambc.is_draft():
    HUNT_LOST = 3          # rounds out of sight before a Hunt ends why=lost [ROLES L4]
    HOLD_CALM = 3          # Hold ends ok why=clear after this many rounds with no enemy near the tile [provisional]
    HOLD_LEASH = 2         # Hold never steps farther than this from its tile [provisional]
    HOLD_MAX = 60          # a Hold nobody releases ends why=timeout [provisional]
    TWINS = (3, 4)         # ChampionType CASSI, ISSAC [sdk]: killing either kills both [rules]
    HUNT_DEF = dict(intercept_radius=14, chase_max=10)   # Hunter card defaults [provisional A44]
    HUNT_COOL = 15         # rounds an enemy is not re-hunted after a Hunt on it failed or was aborted [provisional]
    HUNT_CD = {}           # enemy id -> round it may be hunted again (stops start/abort churn every round)
    STILL_BONUS = 10       # gems of score for a channelling target: it can't move or hit (P15, P20) [provisional]
    LOW_BONUS = 10         # gems of score x missing HP fraction (P8 strike the weak) [provisional]
    GROW_MAX = 2           # our distance to the target grew this many turns in a row: chase lost (P16) [provisional]
    ESPAWN_R = 3           # never fight within this of the enemy spawn region (P21; respawns appear there) [provisional]
    GUARD_ALTAR_R = 8      # the Guard hunts only carriers this close to its home altar (defence by attack) [provisional]
    LOW_HP = 0.35          # an enemy below this HP fraction is heading home, not to an altar [provisional]
    STRENGTH_R = 7         # Lanchester strength counts champions within this of the fight tile (R1 + 2) [provisional]
    ROLE_G, ROLE_FX, ROLE_H = 1, 2, 3   # ROLE_GUARD, ROLE_FLEX, ROLE_HUNTER (10_mem)
    HUNT_TTK = 6           # row 5 starts only fights we end within this many rounds (P15: short and sharp; a long
                           # one draws the next enemy in) [provisional; measured 14 Oct: ttk 8-13 starts all failed]
    STRIKE_HP = 0.4        # PROVISIONAL (no A# yet): the STRIKE row / strike_ok never fights below this HP fraction
    STRIKE_CHASE = 3       # PROVISIONAL (no A# yet): tiles a STRIKE hunt may chase past its start distance
    HUNT_ALLY_TTK = 4     # PROVISIONAL (no A# yet): extra ttk allowed when an ally fights within R1 (P10, review 14 Oct)
    HUNT_CLOSE = 2         # a target not coming toward us is hunted only within reach_now + this [provisional]

    def card_num(w, k, default=None):
        """card(w, k) that never raises: 60_tasks' CARD_DEF has no intercept_radius / chase_max."""
        try:
            v = card(w, k)
        except Exception:
            v = None
        return (HUNT_DEF.get(k, 0) if default is None else default) if v is None else v

    def may_fight(w):
        """Rows 4 and 6 (Hold / Join): the Hunter, the Guard and the Flex; a Farmer (intercept 0) leaves."""
        return card_num(w, "role", 0) in (ROLE_G, ROLE_FX, ROLE_H) or card_num(w, "intercept_radius", 0) > 0

    _CT = {}               # champion id -> ChampionType int (never changes; each host call costs)

    def ctype_of(ch):
        i = int(ch)
        t = _CT.get(i)
        if t is None:
            t = _CT[i] = int(ch.champion_name())
        return t

    _LK = {}               # enemy id -> (round, live Kit)

    def live_kit(ch, rnd, s=None):
        """The enemy's kit with its live Strength / Focus [sdk: readable on any visible champion]: 50_kit's
        enemy_model(c, snap) when it exists, else the design Kit with S/F overwritten (bought shards are not in
        Champion.design; starter-python buys Strength shards). Once per round per enemy."""
        i = int(ch)
        r = _LK.get(i)
        if r is not None and r[0] == rnd:
            return r[1]
        k = None
        em = globals().get("enemy_model")
        if em is not None:
            try:
                k = em(ch, s)
                if not hasattr(k, "dpr") or not hasattr(k, "burst"):
                    k = None
            except Exception:
                k = None
        if k is None:
            k = kit_of(ctype_of(ch))
            try:
                S, F = ch.strength(), ch.focus()
                if S != k.S or F != k.F:
                    lk = object.__new__(Kit)
                    lk.__dict__.update(k.__dict__)
                    lk.S, lk.F = S, F
                    k = lk
            except Exception:
                pass
        _LK[i] = (rnd, k)
        return k

    _EH = {}               # enemy id -> (round, hp, pos) last seen (focus fire, direction of travel)

    def enemy_track(s):
        """Once per round: (hp_dropped, moved_away_from(p)) data for every visible enemy."""
        m = memo(s)
        if "etrack" in m:
            return m["etrack"]
        prev = {}
        for p, hp, bag, ch in s.enemies:
            i = int(ch)
            o = _EH.get(i)
            if o is not None and o[0] >= s.rnd - 1:
                prev[i] = o
            _EH[i] = (s.rnd, hp, p)
        m["etrack"] = prev
        return prev

    def _camp_hits(w, s, q):
        """True when an awake live monster has tile q in range (the camp half of inc_at)."""
        for h in s.awake:
            row = s.camp_hp.get(h)
            if row is None:
                continue
            for (sp, k), hp in zip(kinds(w, h), row):
                if hp and sp.chebyshev_distance(q) <= (5 if k == MONO else CAMP_RANGE):
                    return True
        return False

    _ESP = []

    def espawn_d(w, p):
        """Chebyshev distance from p to the enemy spawn region (positions cached once)."""
        if not _ESP:
            try:
                _ESP.extend(w.espawn.positions())
            except Exception:
                _ESP.append(w.anchor.get("espawn", V(-99, -99)))
        return min(q.chebyshev_distance(p) for q in _ESP)

    def twin_row(s, ch):
        """The other body of an enemy Cassi & Issac, as a snapshot row, or None."""
        try:
            t = ctype_of(ch)
        except Exception:
            return None
        if t not in TWINS:
            return None
        o = TWINS[1] if t == TWINS[0] else TWINS[0]
        for e in s.enemies:
            if ctype_of(e[3]) == o:
                return e
        return None

    def allies_rows(w, s):
        """[(pos, ChampionType, hp)] of visible allies other than me, once per turn (vision.champions ~17k)."""
        m = memo(s)
        r = m.get("allies")
        if r is None:
            r = []
            me = int(w.me)
            try:
                for a in vision.champions(Team.ALLY):
                    if int(a) != me:
                        r.append((a.position(), ctype_of(a), a.health()))
            except Exception:
                pass
            m["allies"] = r
        return r

    def allies_dpr(w, p, r=R1, s=None):
        """Summed sustained dpr (vs champions) of visible allies (not me) within r of p (P10)."""
        return sum(kit_of(t).dpr(True) for q, t, _ in allies_rows(w, s or w.snap) if q.chebyshev_distance(p) <= r)

    def still_rounds(ch):
        """Rounds a visible enemy stands still: its tribute or recall channel (P15 hit them when tired)."""
        try:
            if int(ch.state()) & (ST_SUBMITTING | ST_RECALLING):        # one host read [sdk]
                return max(1, int(ch.remaining_channel_time()))
        except Exception:
            pass
        return 0

    def recalling(ch):
        try:
            return bool(int(ch.state()) & ST_RECALLING)
        except Exception:
            return False

    def team_power(w, s, p, kit, skip=()):
        """(ours, theirs): Lanchester strength (sum HP x sum dpr) of the visible champions within STRENGTH_R
        of fight tile p; me always counts. 50_kit's team_strength(...) replaces it when it lands."""
        ts = globals().get("team_strength")
        if ts is not None:
            try:
                r = ts(w, s, p)
                if isinstance(r, tuple) and len(r) == 2:
                    return r
            except Exception:
                pass
        hp_a, d_a = s.hp, kit.dpr(True)
        for q, t, hp in allies_rows(w, s):
            if q.chebyshev_distance(p) <= STRENGTH_R:
                hp_a += hp
                d_a += kit_of(t).dpr(True)
        hp_e = d_e = 0.0
        for q, hp, bag, ch in s.enemies:
            if q.chebyshev_distance(p) <= STRENGTH_R:
                k = live_kit(ch, s.rnd, s)
                hp_e += hp
                d_e += k.dpr(True, bag)
        return hp_a * d_a, hp_e * d_e

    def fin_dmg(kit, s):
        """What we deal to a champion this turn: a basic attack, a second one with a ready attack reset, and
        the best ready damaging spell that can target an enemy (the finishing blow, P20)."""
        cds = kit.cds(s.rnd)
        d, sp = kit.S, 0.0
        for sl in kit.slots:
            if cds[sl.i]:
                continue
            if sl.kind == K_RESET:
                d += kit.S
            elif sl.kind in (K_DMG, K_CC, K_AOE) and (sl.enemies or sl.ground):
                sp = max(sp, sl.mod * kit.F)
        return d + sp

    def reach_now(kit, s):
        """Tiles from which we land a basic attack this turn: walk + attack (melee), attack (ranged), plus a
        ready ground dash [measured A46]."""
        r = kit.arange + (0 if kit.ranged else 1)
        if s.st & ST_CAN_CAST:
            cds = kit.cds(s.rnd)
            sl = next((sl for sl in kit.slots if sl.kind == K_DASH and sl.ground and cds[sl.i] == 0), None)
            if sl is not None:
                r += sl.rng
        return r

    class HGate:
        __slots__ = ("ok", "d", "still", "bags", "allies", "others", "pred", "ttd", "why")

    def hunt_gate(w, s, ch, hp, bag, kit=None, p=None):
        """The I3 champion gate for Hunt/Hold/rows 3-6. ok, d (L3 Duel), still (channel rounds), bags (summed
        with the twin), allies (dpr added), others (enemies other than the target pair that reach the fight
        tile within ttk_them), ttd (our time-to-die, channel rounds included), pred (damage we take before it
        dies), why (gate | outnumbered | stronger | spawn). ok also needs the I3 keep test:
        pred x GATE_X < hp - keep_hp x max_hp (the line tools/invariants.py checks)."""
        g = HGate()
        kit = kit or my_kit(w)
        g.ok, g.d, g.still, g.bags, g.allies, g.others, g.pred, g.ttd, g.why = \
            False, None, 0, bag, 0.0, 0, 0, FAR, "gate"
        if kit is None:
            return g
        p = p or ch.position()
        tw = twin_row(s, ch)
        if tw is not None:
            g.bags = bag + tw[2]
        g.allies = allies_dpr(w, p, R1, s)
        k = live_kit(ch, s.rnd, s)
        d = g.d = duel_gate(kit, s, k, hp, g.allies, g.bags, shield_of(w))
        g.still = still_rounds(ch)
        ok = d.ok
        if not ok and g.still:
            # A channelling target can't hit back for `still` rounds: our time-to-die grows by that much.
            ratio = d.ttk_them * TTK_RATIO <= d.ttk_us + g.still
            pw = P_WIN if ratio else 1 - P_WIN
            v = pw * (g.bags + KILL_GOLD * GOLD_GEM + RESPAWN * INCOME) - (1 - pw) * (s.bag + RESPAWN * INCOME) \
                - min(d.ttk_them, RESPAWN) * INCOME
            ok = ratio and v > 0
            if ok:
                d.value = v
        g.ttd = d.ttk_us if d.ttk_us >= FAR else d.ttk_us + g.still
        g.pred = 0 if g.ttd >= FAR else int(s.hp * min(1.0, d.ttk_them / max(1, g.ttd)))
        # (the extra burst line is gone: 50_kit's Duel is burst-first, d.pred_dmg includes their opening turn)
        ok = ok and g.pred * GATE_X < s.hp - card(w, "keep_hp") * s.max_hp      # I3: the fight leaves keep_hp
        if ok:
            # P11 not outnumbered: any other enemy that reaches the fight tile before it ends (R1 + ttk - 1).
            pair = {int(ch)} | ({int(tw[3])} if tw is not None else set())
            rr = R1 + max(0, min(d.ttk_them, 6) - 1)
            g.others = sum(1 for e in s.enemies if int(e[3]) not in pair and e[0].chebyshev_distance(p) <= rr)
            if g.others:
                na = sum(1 for q, _, _ in allies_rows(w, s) if q.chebyshev_distance(p) <= R1)
                if na < g.others:
                    ok, g.why = False, "outnumbered"
        if ok and len(s.enemies) > 1:
            ours, theirs = team_power(w, s, p, kit)
            if theirs * TTK_RATIO > ours:
                ok, g.why = False, "stronger"
        if ok and espawn_d(w, p) <= ESPAWN_R:
            ok, g.why = False, "spawn"
        g.ok = ok
        return g

    def can_finish(w, s, kit, p, hp, ch):
        """P20: the target dies to what we deal this turn, it is within this turn's reach, and nothing visible
        kills us before our next turn (inc here, camps included, below our HP)."""
        if p.chebyshev_distance(s.pos) > reach_now(kit, s):
            return False
        try:
            sh = ch.buffs().get(cambc.BuffShield).value if ch.buffs().has_shield() else 0
        except Exception:
            sh = 0
        return hp + sh <= fin_dmg(kit, s) and inc_at(w, s, s.pos) * GATE_X < s.hp

    def strike_ok(w, s, ch, p, hp, kit):
        """The STRIKE gate (66_deny strike_row, Hunt mode chan/outnumber): not about to die, HP >= STRIKE_HP,
        not at the enemy spawn, the target not in an awake camp's range (it would hit us next to it); then a lone
        channeller (it can't act until it cancels [rules], P15) or we outnumber the enemies around it with more
        Lanchester strength (P11; no TTK_RATIO margin)."""
        if kit is None or flee_cond(w, s)[0] or s.hp < STRIKE_HP * s.max_hp or espawn_d(w, p) <= ESPAWN_R:
            return False
        if _camp_hits(w, s, p):
            return False
        foes = [e for e in s.enemies if e[0].chebyshev_distance(p) <= R1 + 1]
        if still_rounds(ch) and len(foes) <= 1:
            return True
        allies = sum(1 for q, _, _ in allies_rows(w, s) if q.chebyshev_distance(p) <= R1)
        if allies + 1 <= len(foes):
            return False
        ours, theirs = team_power(w, s, p, kit)
        return ours > theirs

    def strike_keep(w, s, t):
        """Row 3 (EVADE) exception for a STRIKE hunt (mode set): its target is visible and strike_ok still holds.
        Row 2 is unaffected (strike_ok is False whenever flee_cond holds)."""
        try:
            if t is None or t.name != "Hunt" or not getattr(t, "mode", None) or t.status != "run":
                return False
            rows = [e for e in s.enemies if int(e[3]) in t.ids]
            if not rows:
                return False
            p, hp, bag, ch = min(rows, key=lambda e: e[0].chebyshev_distance(s.pos))
            return strike_ok(w, s, ch, p, hp, my_kit(w))
        except Exception:
            return False

    def hunt_value(g):
        """Gems a kill is worth (STRATEGY.md fight value, the reward half): bag(s) + 50 gold x A41."""
        return g.bags + KILL_GOLD * GOLD_GEM

    def home_altar_pos(w):
        i = card_num(w, "home_altar", 255)
        if i is None or i == 255 or i >= len(w.altar_pos):
            return None
        return w.altar_pos[i]

    def carrier_target(w, s, cur_vpr=INCOME, kit=None):
        """INVARIANTS §2 row 5: the best visible enemy carrier within the card's intercept_radius whose gate
        passes and whose kill value beats what the current task earns meanwhile (cur_vpr x ttk). Score (P8,
        P15): (bag + gold + STILL_BONUS if channelling + LOW_BONUS x missing HP) / ttk_them. The Guard only
        within GUARD_ALTAR_R of its home altar. Returns (Champion, text) or None."""
        ir = card_num(w, "intercept_radius", 0)
        if not ir or not s.enemies:
            return None
        kit = kit or my_kit(w)
        if kit is None:
            return None
        # Due to bank (a carrier in sight is a threat): row 10 pre-empts the Hunt, except on a channelling target
        # already in this turn's reach (it can't act until it cancels [rules]; review 14 Oct).
        carrying = s.bag >= card(w, "bank_at_threat")
        guard = card_num(w, "role", 0) == ROLE_G
        ha = home_altar_pos(w) if guard else None
        if guard and ha is None:
            return None
        # Standing in an awake camp's range (paused mid-clear), or a target in one: only a kill we finish this
        # turn (measured 14 Oct: hunts started from our own awake camp ended by row 2 the next round, why=both).
        incamp = _camp_hits(w, s, s.pos)
        if incamp:
            ir = min(ir, reach_now(kit, s))
        prev = enemy_track(s)
        rn = reach_now(kit, s)
        best = None
        for p, hp, bag, ch in s.enemies:
            d0 = p.chebyshev_distance(s.pos)
            if d0 > ir or HUNT_CD.get(int(ch), -1) > s.rnd:
                continue
            if ha is not None and p.chebyshev_distance(ha) > GUARD_ALTAR_R:
                continue
            tw = twin_row(s, ch)
            if bag <= 0 and (tw is None or tw[2] <= 0):
                continue
            still = still_rounds(ch)
            if carrying and not (still and d0 <= rn):
                continue
            o = prev.get(int(ch))
            coming = o is not None and o[2].chebyshev_distance(s.pos) > d0
            if not still and not coming and d0 > rn + HUNT_CLOSE:
                continue             # not coming to us and beyond a short close: a chase we don't win (P16)
            if still and recalling(ch) and d0 - rn > still:
                continue             # the recall lands before we reach it
            g = hunt_gate(w, s, ch, hp, bag, kit, p)
            fin = can_finish(w, s, kit, p, hp, ch)
            if not fin and (not g.ok or incamp or _camp_hits(w, s, p)):
                continue
            if g.d.ttk_them > HUNT_TTK + (g.still or 0) + (HUNT_ALLY_TTK if g.allies else 0) \
                    or hunt_value(g) <= cur_vpr * g.d.ttk_them:
                continue
            try:
                mx = max(1.0, ch.max_health())
            except Exception:
                mx = max(1.0, hp)
            sc = (hunt_value(g) + (STILL_BONUS if still else 0) + LOW_BONUS * max(0.0, 1 - hp / mx)) \
                / max(1, g.d.ttk_them)
            key = (-sc, d0)
            if best is None or key < best[0]:
                best = (key, ch, f"vs=c{int(ch)} bag={g.bags} d={d0} ttk={g.d.ttk_them}/{g.d.ttk_us} "
                                 f"still={still} sc={sc:.1f} val={g.d.value:.1f}")
        return None if best is None else (best[1], best[2])

    def join_target(w, s, ally_pos, kit=None):
        """INVARIANTS §2 row 6: an enemy within R1 of a hurt ally if the combined gate passes (the ally's dpr
        is in allies_dpr because it is within R1 of that enemy). Focus fire (P10): prefer the enemy whose HP
        dropped since last round (the one the ally is hitting), then the nearest to the ally. No role filter
        here (68_defend's TURN uses it for any role); row 6 checks may_fight(w)."""
        foes = [e for e in s.enemies if e[0].chebyshev_distance(ally_pos) <= R1
                and HUNT_CD.get(int(e[3]), -1) <= s.rnd]
        if not foes:
            return None
        prev = enemy_track(s)

        def key(e):
            o = prev.get(int(e[3]))
            hit = o is not None and e[1] < o[1]
            return (not hit, e[0].chebyshev_distance(ally_pos))

        incamp = _camp_hits(w, s, s.pos)
        for p, hp, bag, ch in sorted(foes, key=key)[:2]:
            g = hunt_gate(w, s, ch, hp, bag, kit, p)
            if g.ok and not incamp and not _camp_hits(w, s, p):
                return ch, f"vs=c{int(ch)} bag={g.bags} ttk={g.d.ttk_them}/{g.d.ttk_us} allies={g.allies:.0f}"
        return None

    def hold_target(w, s, tile, kit=None):
        """INVARIANTS §2 row 4: the enemy nearest tile within R1 of it -> (Champion, gate ok, text) or None.
        Row 4 checks may_fight(w): a Farmer's capture leaves on its own enemy_on test."""
        foes = [e for e in s.enemies if e[0].chebyshev_distance(tile) <= R1]
        if not foes:
            return None
        p, hp, bag, ch = min(foes, key=lambda e: e[0].chebyshev_distance(tile))
        g = hunt_gate(w, s, ch, hp, bag, kit, p)
        return ch, g.ok, f"vs=c{int(ch)} tile={tile.x},{tile.y} ttk={g.d.ttk_them if g.d else '-'}/" \
                         f"{g.d.ttk_us if g.d else '-'} why={'ok' if g.ok else g.why}"

    def hunt_keep(w, s, t, ttd_=None):
        """Row 2 exception while hunting: True = don't flee. The only enemies within R1 are the hunted pair, no
        camp hits us, and the gate (burst + sustained model, keep_hp left) still passes or we finish it this turn.
        flee_cond's inc counts the enemy's burst every round, so its ttd would veto every duel the gate wins."""
        try:
            if t is None or t.name != "Hunt" or t.status != "run" or _camp_hits(w, s, s.pos):
                return False
            if any(int(e[3]) not in t.ids for e in s.enemies if e[0].chebyshev_distance(s.pos) <= R1):
                return False
            rows = [e for e in s.enemies if int(e[3]) in t.ids]
            if not rows:
                return False
            p, hp, bag, ch = min(rows, key=lambda e: e[0].chebyshev_distance(s.pos))
            kit = my_kit(w)
            if can_finish(w, s, kit, p, hp, ch):
                return True
            return hunt_gate(w, s, ch, hp, bag, kit, p).ok
        except Exception:
            return False

    def hunt_busy(w, s, t):
        """Rows 7-12 housekeeping (HOME, AWAKE, CAPTURE passed-by, STALL) must not end a Hunt / Hold in an open
        fight whose target is in this turn's reach and still passes the gate (or dies this turn): one more turn
        is the kill. Row 2 (hunt_keep) and row 10 (bank) still apply."""
        try:
            if t is None or t.name not in ("Hunt", "Hold") or t.status != "run" or getattr(t, "f", None) is None:
                return False
            kit = my_kit(w)
            ids = getattr(t, "ids", None)
            rows = [e for e in s.enemies if (ids is None or int(e[3]) in ids)]
            for p, hp, bag, ch in rows:
                if p.chebyshev_distance(s.pos) <= reach_now(kit, s) and                         (can_finish(w, s, kit, p, hp, ch) or hunt_gate(w, s, ch, hp, bag, kit, p).ok):
                    return True
            return False
        except Exception:
            return False

    def escape_goal(w, s, ch, p, hp, bag):
        """Where a hunted enemy is going (P6 foreknowledge): home (its spawn) when recalling or low on HP, else
        the nearest altar when it carries, else None (it is farming: no lead)."""
        try:
            mx = ch.max_health()
        except Exception:
            mx = hp
        if recalling(ch) or hp < LOW_HP * mx:
            espawn_d(w, p)
            return min(_ESP, key=lambda q: q.chebyshev_distance(p))
        if bag > 0 and w.altar_pos:
            return min(w.altar_pos, key=lambda q: q.chebyshev_distance(p))
        return None

    def lead_tile(s, p, goal, kit):
        """The cut-off point: the tile on the target's straight line to goal that we reach no later than it
        (our distance <= its distance + attack reach), nearest to it; the target itself if none."""
        if goal is None:
            return p
        q = p
        for _ in range(min(12, p.chebyshev_distance(goal))):
            dx = (goal.x > q.x) - (goal.x < q.x)
            dy = (goal.y > q.y) - (goal.y < q.y)
            q = V(q.x + dx, q.y + dy)
            if s.pos.chebyshev_distance(q) <= p.chebyshev_distance(q) + kit.arange:
                return q
        return p

    # ---------------------------------------------------------------- shared engage logic
    class Engage(Task):
        """Fight bookkeeping shared by Hunt and Hold: the Fight record, the approach step, the dash, act."""

        def start(self, w, s):
            Task.start(self, w, s)
            self.f = None
            self.moves = 0

        def end(self, s, status, why):
            if self.f is not None:
                res = "done" if status == "ok" else ("died" if why == "died" else "abort")
                self.f.end(s.rnd, s.hp, res, why)
                self.f = None
            return Task.end(self, s, status, why)

        def step_to(self, w, s, goal, leash=None, bold=False, p=None):
            """One greedy step strictly closer (Chebyshev) to goal: no wall / camp spawn tile / enemy spawn
            (World.blocked), no occupied tile, no awake camp's range unless bold (a finishing blow); leash =
            (tile, r) bounds the step. p (the enemy): ties broken by its distance (stay on it while cutting)."""
            if not s.can_move or w.nav.moved_round == s.rnd:
                return False
            wl = walls(w, s)
            d0 = goal.chebyshev_distance(s.pos)
            ref = p or goal
            for dv in sorted(DIRS, key=lambda v: (goal.chebyshev_distance(s.pos + v),
                                                  ref.chebyshev_distance(s.pos + v))):
                q = s.pos + dv
                if goal.chebyshev_distance(q) >= d0:
                    break
                try:
                    if wl.is_set(q):
                        continue
                except Exception:
                    continue
                if leash is not None and leash[0].chebyshev_distance(q) > leash[1]:
                    continue
                if not bold and _camp_hits(w, s, q) and not _camp_hits(w, s, s.pos):
                    continue
                if w.nav.move(q):
                    self.moves += 1
                    return True
            return False

        def dash_slot(self, kit, s):
            if not s.st & ST_CAN_CAST:
                return None
            cds = kit.cds(s.rnd)
            return next((sl for sl in kit.slots if sl.kind == K_DASH and sl.ground and cds[sl.i] == 0), None)

        def cast_dash(self, w, s, kit, sl, q):
            """The dash through act() (the one cast site, I14) with a ground target row. True if cast."""
            it = Intent(kit, [[0, 0, q.x, q.y, q, "dash", True]])
            it.cast = (sl.i, 0)
            if "cs" not in act(it, w):
                return False
            w.nav.moved_round, w.nav.dest = s.rnd, q      # the t line's position; no walk after it
            self.moves += 2
            return True

        def dash_to(self, w, s, kit, frm, p, leash=None, bold=False):
            """Dash so that the enemy at p is in basic-attack reach (Vendetta: walk + dash + attack closes 4
            [measured A46]). Only when the attack lands this turn (P15: the dash is the strike, not the chase).
            Landing tile or None."""
            sl = self.dash_slot(kit, s)
            if sl is None or frm.chebyshev_distance(p) > kit.arange + sl.rng:
                return None
            wl = walls(w, s)
            best = None
            ar = kit.arange                  # landing tiles: within attack reach of p and dash range of frm
            for dx in range(-ar, ar + 1):
                for dy in range(-ar, ar + 1):
                    q = V(p.x + dx, p.y + dy)
                    if q.chebyshev_distance(frm) > sl.rng or q == frm or q == p:
                        continue
                    try:
                        if wl.is_set(q) or (w.nav.moved_round == s.rnd and q == s.pos):
                            continue
                    except Exception:
                        continue
                    if leash is not None and leash[0].chebyshev_distance(q) > leash[1]:
                        continue
                    if not bold and _camp_hits(w, s, q):
                        continue
                    k = (q.chebyshev_distance(p), q.chebyshev_distance(frm))
                    if best is None or k < best[0]:
                        best = (k, q)
            if best is None:
                return None
            q = best[1]
            return q if self.cast_dash(w, s, kit, sl, q) else None

        def disengage(self, w, s, kit):
            """P21/I3: the gate flipped. Step (or dash, if an enemy is within R1) to the tile that maximises the
            distance from every visible enemy, never closer to any of them (never through the enemy), ties
            toward allies, then our spawn. Returns the act token or None."""
            es = [e[0] for e in s.enemies]
            if not es or not s.can_move or w.nav.moved_round == s.rnd:
                return None
            wl = walls(w, s)
            al = [q for q, _, _ in allies_rows(w, s)]
            here = [e.chebyshev_distance(s.pos) for e in es]

            def score(q):
                ds = [e.chebyshev_distance(q) for e in es]
                if any(a < b for a, b in zip(ds, here)):
                    return None
                ha = min((a.chebyshev_distance(q) for a in al), default=0)
                hs = w.dist("spawn", q)
                return (-min(ds), -sum(ds), ha, hs if hs is not None else 0)

            best = None
            for dv in DIRS:
                q = s.pos + dv
                try:
                    if wl.is_set(q) or _camp_hits(w, s, q):
                        continue
                except Exception:
                    continue
                k = score(q)
                if k is not None and (best is None or k < best[0]):
                    best = (k, q, "mv")
            sl = self.dash_slot(kit, s)
            if sl is not None and min(here) <= R1:
                r = sl.rng
                for dx in range(-r, r + 1):
                    for dy in range(-r, r + 1):
                        q = V(s.pos.x + dx, s.pos.y + dy)
                        if max(abs(dx), abs(dy)) < 2:
                            continue
                        try:
                            if wl.is_set(q) or _camp_hits(w, s, q):
                                continue
                        except Exception:
                            continue
                        k = score(q)
                        if k is not None and (best is None or k < best[0]):
                            best = (k, q, "dash")
            if best is None:
                return None
            q = best[1]
            if best[2] == "dash":
                return "dash how=disengage" if self.cast_dash(w, s, kit, sl, q) else None
            if w.nav.move(q):
                self.moves += 1
                return "mv how=disengage"
            return None

        def strike(self, w, s, kit, row, g, leash=None, chase=None, lead=None, bold=False):
            """One turn against the enemy row (p, hp, bag, ch): approach (walk toward lead, else the enemy;
            dash when the attack then lands) unless in reach, then plan_turn/act with it as target. Returns the
            act tokens. chase = a goal tile to walk to instead (Hold walks back to its tile; no dash)."""
            p, hp, bag, ch = row
            rnd = s.rnd
            # The champion row carries its live model (row[7]): plan_turn runs 50_kit's champion policy (focus,
            # KILL_VAL, CHAN_VAL on a channel). No w / blocked is passed, so that policy plans no walk or dash:
            # the movement above stays the only mover (review 14 Oct).
            try:
                em = enemy_model(ch, s)
            except Exception:
                em = None
            tg = [champ_target(ch, p, hp, bag, em=em)]
            inc = inc_at(w, s, s.pos)
            dd = p.chebyshev_distance(s.pos)
            if dd > kit.arange and not bold:                     # a monster hitting us, while the enemy is away
                for h in s.awake:
                    for t in camp_targets(w, s, h):
                        if max(abs(t[2] - s.pos.x), abs(t[3] - s.pos.y)) <= CAMP_RANGE:
                            tg.append(t)
            toks = []
            pos, moved = s.pos, False
            if dd > kit.arange:
                # Dash first when it lands the attack from here (walk + dash both allowed for melee [A46]).
                q = None
                if chase is None and not kit.ranged and dd <= kit.arange + 2 + 1:
                    sl = self.dash_slot(kit, s)
                    if sl is not None and dd <= kit.arange + sl.rng:
                        q = self.dash_to(w, s, kit, pos, p, leash, bold)
                        if q is not None:
                            toks.append("dash")
                            pos, moved = q, True
                if q is None:
                    goal = chase or (lead if lead is not None and dd > kit.arange + 1 else p)
                    if self.step_to(w, s, goal, leash, bold, p):
                        toks.append("mv")
                        pos, moved = w.nav.dest, True
                    if pos.chebyshev_distance(p) > kit.arange and not kit.ranged and chase is None:
                        q = self.dash_to(w, s, kit, pos, p, leash, bold)
                        if q is not None:
                            toks.append("dash")
                            pos, moved = q, True
            cds = kit.cds(rnd)
            if "dash" in toks:
                cds = (FAR,) * len(cds)                          # one successful cast per turn [rules]
            it = plan_turn(kit, s, tg, False, inc, cds=cds, pos=pos, moved=moved)
            if it.atk is None and it.cast is None:
                return toks
            if self.f is None:
                d = g.d                  # ttk ours/theirs; theirs counts a channelling target's still rounds
                self.f = Fight(f"c{int(ch)}", (d.ttk_them, g.pred), s.hp, card(w, "keep_hp") * s.max_hp,
                               ttk_=f"{d.ttk_them}/{g.ttd}", enemies=len(s.enemies))
                self.f.start(rnd)
            a = act(it, w)
            self.f.turn(it, rnd)
            if a:
                toks.append(a.replace(" ", ","))
                i = it.atk if it.atk is not None else (it.cast[1] if isinstance(it.cast[1], int) else None)
                if i is not None and i < len(tg) and tg[i][5][0] == "g":
                    self.hit = tg[i][5]
            return toks

        def killed(self, w, s):
            """Our kill this turn or last: the 50 gold [rules] landed (or the bag grew outside a capture)."""
            try:
                return w.me.gold_count() >= self.gold + KILL_GOLD or w.me.gem_count() > self.bag
            except Exception:
                return False

        def log_kill(self, w, s, vs):
            try:
                gain, gold = w.me.gem_count() - self.bag, w.me.gold_count() - self.gold
            except Exception:
                gain = gold = -1
            _ev("hunt", f"kill vs={vs} gain={gain} gold={gold} r={s.rnd - self.r0}")

    # ---------------------------------------------------------------- Hunt
    class Hunt(Engage):
        """target -> pursue (cut-off) -> strike -> the gate every turn; disengage when it flips (ROLES L4)."""
        name = "Hunt"

        def __init__(self, enemy, mode=None):
            Task.__init__(self, f"c{int(enemy)}")
            self.enemy = enemy
            self.ids = {int(enemy)}
            self.mode = mode            # None (rows 5/6, TURN) | "chan" | "outnumber" (STRIKE row, strike_ok gate)

        def start(self, w, s):
            Engage.start(self, w, s)
            self.lost = 0
            self.grow = 0
            self.last = self.enemy.position() if self.enemy.is_visible() else None
            self.lastd = self.d0 = self.last.chebyshev_distance(s.pos) if self.last is not None else 0
            self.goal = None
            self.gold, self.bag = s.gold, s.bag
            self.fight = self.key
            tw = twin_row(s, self.enemy)
            if tw is not None:
                self.ids.add(int(tw[3]))
            _ev("hunt", f"start vs={self.key} d={self.d0} bag={s.bag} hp={int(s.hp)} mode={self.mode or '-'}")

        def fail(self, w, s, why, kit=None):
            """End the Hunt; on a flipped gate disengage this turn first (I3 abort, P21)."""
            if kit is not None and why in ("gate", "outnumbered", "stronger", "spawn"):
                tok = self.disengage(w, s, kit)
                if tok:
                    self.act = tok
            return self.end(s, "fail", why)

        def end(self, s, status, why):
            if status != "ok":
                for i in self.ids:
                    HUNT_CD[i] = s.rnd + HUNT_COOL
            return Engage.end(self, s, status, why)

        def step(self, w, s):
            kit = my_kit(w)
            if kit is None:
                return self.end(s, "fail", "no_kit")
            sense(w, s)
            self.fight, self.hit = self.key, "-"
            rows = [e for e in s.enemies if int(e[3]) in self.ids]
            if not rows:
                if self.killed(w, s):
                    self.log_kill(w, s, self.key)
                    return self.end(s, "ok", "killed")
                if self.last is not None:
                    try:
                        b = game_map.bushes()
                        if any(b.is_set(self.last + dv) for dv in DIRS) or b.is_set(self.last):
                            return self.fail(w, s, "bush")         # P16: never follow into what we can't see
                    except Exception:
                        pass
                self.lost += 1
                if self.lost >= HUNT_LOST:
                    return self.fail(w, s, "lost")
                tgt = self.last
                if tgt is not None and self.goal is not None:
                    tgt = lead_tile(s, self.last, self.goal, kit)
                if tgt is not None and self.step_to(w, s, tgt):
                    self.act = "mv how=hunt"
                else:
                    self.act = "wait why=blocked"
                self.gold, self.bag = s.gold, s.bag
                return "run"
            self.lost = 0
            row = min(rows, key=lambda e: e[0].chebyshev_distance(s.pos))   # the body we can reach (twins)
            p, hp, bag, ch = row
            self.last = p
            dd = p.chebyshev_distance(s.pos)
            if w.espawn.is_set(p) or espawn_d(w, p) <= ESPAWN_R - 1:
                return self.fail(w, s, "spawn", kit)                # P21: never into the enemy spawn
            fin = can_finish(w, s, kit, p, hp, ch)
            if not fin:
                if self.moves - self.d0 > max(card_num(w, "chase_max"), STRIKE_CHASE if self.mode else 0):
                    return self.fail(w, s, "chase")                 # P23: not out of anger
                self.grow = self.grow + 1 if dd > self.lastd and dd > kit.arange else 0
                if self.grow >= GROW_MAX:
                    return self.fail(w, s, "fled")                  # it outruns us: farming time, not a kill
                g = hunt_gate(w, s, ch, hp, bag, kit, p)
                # STRIKE hunts (66_deny strike_row) keep going while the relaxed strike gate holds (P11, P15)
                if not g.ok:
                    if not (self.mode and strike_ok(w, s, ch, p, hp, kit)):
                        return self.fail(w, s, g.why, kit)
                    _ev("strike", f"keep vs={self.key} mode={self.mode} gate={g.why} d={dd} hp={int(hp)}")
            else:
                g = hunt_gate(w, s, ch, hp, bag, kit, p)
            self.lastd = dd
            self.goal = escape_goal(w, s, ch, p, hp, bag)
            lead = lead_tile(s, p, self.goal, kit) if not still_rounds(ch) else None
            self.gold, self.bag = s.gold, s.bag
            toks = self.strike(w, s, kit, row, g, lead=lead, bold=fin)
            self.act = ",".join(toks) or "wait why=blocked"
            if fin:
                self.act += " how=finish"
            if any(t.startswith(("at", "cs")) for t in toks) and self.killed(w, s):
                self.log_kill(w, s, self.key)
                return self.end(s, "ok", "killed")
            return "run"

    # ---------------------------------------------------------------- Hold
    class Hold(Engage):
        """Stand on / next to tile, fight whatever comes within R1 of it if the gate passes, else leave."""
        name = "Hold"

        def __init__(self, tile, rounds=HOLD_MAX):
            Task.__init__(self, f"h{tile.x}_{tile.y}")
            self.tile = tile
            self.rounds = rounds
            self.released = False

        def release(self):
            self.released = True

        def start(self, w, s):
            Engage.start(self, w, s)
            self.calm = 0
            self.gold, self.bag = s.gold, s.bag

        def step(self, w, s):
            kit = my_kit(w)
            if kit is None:
                return self.end(s, "fail", "no_kit")
            sense(w, s)
            self.fight, self.hit = "-", "-"
            if self.released:
                return self.end(s, "ok", "released")
            if s.rnd - self.r0 > self.rounds:
                return self.end(s, "fail", "timeout")
            if flee_cond(w, s)[0]:
                return self.end(s, "fail", "flee")
            if self.f is not None and self.killed(w, s):
                self.log_kill(w, s, self.f.vs)
                self.f.end(s.rnd, s.hp, "done", "killed")
                self.f = None
            self.gold, self.bag = s.gold, s.bag
            t = self.tile
            foes = [e for e in s.enemies if e[0].chebyshev_distance(t) <= R1 or e[0].chebyshev_distance(s.pos) <= R1]
            if not foes:
                if self.f is not None:
                    self.f.end(s.rnd, s.hp, "abort", "gone")
                    self.f = None
                self.calm += 1
                if self.calm >= HOLD_CALM:
                    return self.end(s, "ok", "clear")
                self.act = "mv how=hold" if s.pos.chebyshev_distance(t) > 1 and self.step_to(w, s, t) \
                    else "wait why=hold"
                return "run"
            self.calm = 0
            row = min(foes, key=lambda e: e[0].chebyshev_distance(t))
            fin = can_finish(w, s, kit, row[0], row[1], row[3])
            g = hunt_gate(w, s, row[3], row[1], row[2], kit, row[0])
            if not g.ok and not fin:
                tok = self.disengage(w, s, kit)
                if tok:
                    self.act = tok
                return self.end(s, "fail", g.why)
            self.fight = f"c{int(row[3])}"
            back = t if row[0].chebyshev_distance(t) > HOLD_LEASH + kit.arange else None
            toks = self.strike(w, s, kit, row, g, leash=(t, HOLD_LEASH), chase=back, bold=fin)
            self.act = ",".join(toks) or "wait why=hold"
            return "run"
