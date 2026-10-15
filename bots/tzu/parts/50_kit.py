# tzu: lazy
"""L3 kit and actions (ROLES_AND_LAYERS §3 L3): Kit from engine data, plan_turn (pure), act (the ONLY
attack and cast site, I14), event-based clear predictors, the duel gate. Play only: the draft has its
own quick_clear (40_draft _clears), so everything sits under `if not cambc.is_draft()` (import fuel).

Target rows handed to plan_turn: [hp, hit, x, y, ref, tag, stun_immune]
    hp    current HP (+ shield for a champion)      hit  what it deals us per round (a stun's value)
    ref   the Camp / Champion / AltarLock act() hits tag  "g<h>" (camp group), "c<id>" (champion), "lock"
Values are damage-equivalent HP: damage = modifier x Focus; a stun = the stunned unit's next hit;
a shield = min(modifier x Focus, inc x duration); a reset = one Strength; a heal = up to missing HP;
a dash = 0 (L3 never moves) [design: ROLES §3 L3, LESSONS §4].
Walk first: a camp fight casts nothing until a monster is in basic-attack reach (why=excl_walk_flee /
no_target), so the clear starts from the stand the predictor assumes (P1 calculate, P4 win first).
I14: act() drops an excl cast after a move this round and spends the walk (snap.can_move = False)
after an excl cast or a ranged attack, so Nav refuses a later move.
Trace: cast|slot= kind= tgt= val=; cast|idle slot= why= (on change only); splash|g=g<h> by=;
fight|start / fight|end and the clear line (Fight).

Champion fights (14 Oct). ONE enemy damage model, used by every gate and threat query:
    enemy_model(c, snap, row) -> UnitModel   live S / F / max HP / HP / shield / stun / channel / cooldowns
                                             (if the engine lets us read them, else all ready); burst table
                                             bt[d] = the most it can deal to a tile at distance d on its next
                                             turn (basic + reset or its best ready spell, walk, dash), stt[d]
                                             = it can stun that tile; dpr (sustained), reach, hp_eff.
    enemy_threat(snap, pos)                  sum of bt[d] over visible enemies (the I2/I3 "inc" of champions)
    team_strength(snap, allies, enemies)     Lanchester (sum dpr) x (sum hp) per side, their alpha strike off ours
    duel_gate(...) / duel(...) -> Duel       burst-first then sustained, per-turn sequence, several enemies
                                             summed, outnumbered -> no; .pred_dmg .burst .seq .why
plan_turn(...) with champion rows (row[7] = UnitModel, champ_target(..., em=)) runs the champion policy
(_plan_champ): focus fire, ranged kiting, melee dash-in, dash-away on retreat, stun priority; Intent gains
.move_to (one walk the task makes with Nav BEFORE act), .land (a dash landing act() casts), .pre (cast
before the attack), .retreat.
"""
if not cambc.is_draft():
    K_RESET, K_DMG, K_AOE, K_CC, K_HEAL, K_DASH, K_SHIELD = 1, 2, 3, 4, 5, 6, 7     # AbilityKind [sdk]
    KIND_NAME = ("none", "reset", "dmg", "aoe", "cc", "heal", "dash", "shield")
    P_GEM_FOCUS, P_SPLASH, P_RESET_ON_KILL, P_RETALIATE, P_STUN_IMMUNE = 3, 4, 6, 7, 8   # PassiveType [sdk]
    GEM_FOCUS = 0.2         # Prism: Focus per carried gem [rules]
    RETALIATE = 0.2         # Ren: x Focus back to each attacker hit [rules]
    COOLDOWN = 8            # owner turn ends, both slots; a cast on t is ready on t+8 [rules, measured]
    SIM_CAP = 200           # rounds; a longer clear is hopeless (monoliths) [design]
    PRED_COST = 1_000_000   # fuel that covers any one uncached predict_clear [measured max 0.58M]
    EV_COST = 80_000        # fuel per sim event (cast or kill), the per-call estimate [measured 57-73k]
    HOPELESS = (FAR, FAR, 0)
    SOLO_SAFETY = 1.1       # PROVISIONAL A43: predicted damage x 1.1 < hp - keep (same value as the draft's)
    TTK_RATIO = 1.3         # PROVISIONAL A44: fight iff ttk_them x 1.3 <= ttk_us
    P_WIN = 0.65            # PROVISIONAL A44: P(win) when the ratio passes (the A44 floor)
    GOLD_GEM = 0.1          # PROVISIONAL A41: gems per gold
    INCOME = 0.3            # gems per round alive [measured A12]
    RESPAWN = 60            # rounds out after a death [rules]
    KILL_GOLD = 50          # gold to the killer [rules]
    USEFUL = (K_RESET, K_DMG, K_AOE, K_CC, K_SHIELD, K_HEAL)
    SF_EVERY = 10           # rounds between re-reads of a visible champion's Strength / Focus (shards: spawn only)
    KIT_R1 = 5              # enemy reach next turn [measured A46] (60_tasks' R1; the same number)
    DMAX = 7                # burst / stun tables cover distances 0..DMAX-1; farther deals nothing (R1 = 5)

    CHAN_VAL = 150          # PROVISIONAL (no A# yet): HP-equivalent of breaking an enemy channel with a stun (P15)
    KILL_VAL = 300          # PROVISIONAL (no A# yet): HP-equivalent bonus of a hit that finishes a champion
    FLEE_VAL = 100          # PROVISIONAL (no A# yet): stun value bonus on a carrier walking away from us

    class Slot:
        __slots__ = ("i", "kind", "mod", "rng", "radius", "dur", "excl", "camps", "enemies", "self_",
                     "ground", "enhanced", "stun")

        def __init__(self, i, a):
            info = a.info()
            g = getattr
            self.i = i
            self.kind = next((k for k in range(1, 8) if a.has(k)), 0) if info is not None else 0
            self.mod = g(info, "modifier", 0.0) or 0.0
            self.rng = int(g(info, "range", 0) or 0)
            self.radius = max(1, int(g(info, "radius", 0) or 0))
            self.dur = int(g(info, "duration", 0) or 0)
            self.excl = bool(g(info, "exclusive_with_movement", False))
            self.enhanced = bool(g(info, "enhanced_attack", False))
            ok = info is not None
            self.camps = ok and a.can_target_camps()
            self.enemies = ok and a.can_target_enemies()
            self.self_ = ok and a.can_target_self()
            self.ground = ok and a.can_target_ground()
            k = self.kind       # stunner kit test, INVARIANTS §0; AoE stuns iff duration > 0 [sdk]
            self.stun = k == K_CC or (k == K_AOE and self.dur > 0) or (k == K_RESET and self.enhanced)

    class Kit:
        """What one champion type can do. Kit(me) is live (S, F, HP via refresh(), cooldowns via cds());
        kit_of(t) is the design of any of the 12 types (Champion.design works for all [sdk])."""

        def __init__(self, champ, design=False):
            self.ctype = int(champ.champion_name())
            self.slots = tuple(Slot(i, a) for i, a in enumerate(champ.abilities()))
            p = int(champ.passive())
            self.splash, self.reset_on_kill = p == P_SPLASH, p == P_RESET_ON_KILL
            self.retaliate, self.stun_immune, self.gem_focus = p == P_RETALIATE, p == P_STUN_IMMUNE, p == P_GEM_FOCUS
            self.me = None if design else champ
            if design:
                bs = champ.base_stats()
                self.arange, self.S, self.F, self.max_hp = int(bs.base_attack_range), bs.base_strength, \
                    bs.base_focus, bs.base_health
            else:
                self.arange = champ.attack_range()
                self.refresh()
            self.ranged = self.arange > 1
            self.stunner = any(sl.stun for sl in self.slots)
            self.dash = next((sl for sl in self.slots if sl.kind == K_DASH and sl.ground), None)
            self.cd_r, self.cd = -1, (0, 0)
            if not design:
                trace("kit", f"type={self.ctype} ar={self.arange} S={self.S} F={self.F} hp={self.max_hp} p={p} " +
                      " ".join(f"s{sl.i}={KIND_NAME[sl.kind]}/{sl.mod}/{sl.rng}/{sl.radius}/{sl.dur}/"
                               f"{'x' if sl.excl else '-'}{'c' if sl.camps else '-'}{'g' if sl.ground else '-'}"
                               for sl in self.slots))

        def refresh(self):
            """Live S, F, max HP (items change them); Prism's Focus already includes its gems [sdk]."""
            m = self.me
            self.S, self.F, self.max_hp = m.strength(), m.focus(), m.max_health()

        def cds(self, rnd):
            """Cooldowns, read once per round."""
            if self.cd_r != rnd and self.me is not None:
                self.cd = tuple(a.cooldown() for a in self.me.abilities())
                self.cd_r = rnd
            return self.cd

        def focus(self, bag=0):
            return self.F + (GEM_FOCUS * bag if self.gem_focus and self.me is None else 0)

        def dpr(self, vs_champ=False, bag=0):
            """Sustained damage per round: basic attacks plus each damaging slot once per COOLDOWN."""
            F, d = self.focus(bag), self.S
            for sl in self.slots:
                if sl.kind in (K_DMG, K_CC, K_AOE) and (sl.ground or (sl.enemies if vs_champ else sl.camps)):
                    d += sl.mod * F / COOLDOWN
                elif sl.kind == K_RESET:
                    d += self.S / COOLDOWN
            return d

        def burst(self, bag=0):
            """One turn's worst case: a basic attack plus the best damaging spell (INVARIANTS §0)."""
            F = self.focus(bag)
            return self.S + max([sl.mod * F for sl in self.slots if sl.kind in (K_DMG, K_CC, K_AOE)]
                                + [self.S for sl in self.slots if sl.kind == K_RESET] + [0])

    _KITS = {}

    def kit_of(ctype):
        k = _KITS.get(ctype)
        if k is None:
            k = _KITS[ctype] = Kit(cambc.Champion.design(ctype), design=True)
        return k

    # ---------------------------------------------------------------- targets
    _COMP = {}      # group h -> ((kind, max hp, strength, x, y), ...) static [sdk camp design]
    _CAMP_HP = {}   # camp kind -> base health

    def group_comp(w, h):
        c = _COMP.get(h)
        if c is None:
            out = []
            for camp in w.camps[h]:
                k = int(camp.kind())
                if k not in _CAMP_HP:
                    _CAMP_HP[k] = camp.base_stats().base_health
                p = camp.spawn_position()
                out.append((k, _CAMP_HP[k], CAMP_STR[k], p.x, p.y))
            c = _COMP[h] = tuple(out)
        return c

    def camp_targets(w, s, h):
        """Live monsters of group h as target rows, HP from the snapshot (last-known HP if not read this
        turn, World.hp_known; full HP when never read or stale)."""
        row = s.camp_hp.get(h)
        tag = f"g{h}"
        out = []
        for i, (k, mx, st, x, y) in enumerate(group_comp(w, h)):
            hp = w.hp_known(w.camps[h][i], mx, s.rnd) if row is None else row[i]
            if hp is not None and hp > 0:
                out.append([hp, st, x, y, w.camps[h][i], tag, False])
        return out

    def champ_target(c, pos, hp, bag, shield=0, em=None):
        """A visible enemy champion as a target row; its hit is its sustained dpr (stun value). em = its
        UnitModel (enemy_model): appended as row[7], so plan_turn runs the champion policy (_plan_champ)."""
        if em is not None:
            return [hp + shield, em.dpr_v, pos.x, pos.y, c, f"c{int(c)}", em.stun_immune, em]
        k = kit_of(int(c.champion_name()))
        return [hp + shield, k.dpr(True, bag), pos.x, pos.y, c, f"c{int(c)}", k.stun_immune]

    def champ_rows(snap, pos=None, maxd=KIT_R1 + 2):
        """Every visible enemy within maxd of pos (default: us) as a champion row with its model (row[7]),
        HP including its current shield."""
        p = pos if pos is not None else snap.pos
        out = []
        for e in snap.enemies:
            if e[0].chebyshev_distance(p) <= maxd:
                m = enemy_model(e[3], snap, e)
                out.append([m.hp_eff, m.dpr_v, e[0].x, e[0].y, e[3], f"c{m.id}", m.stun_immune, m])
        return out

    def comp_of(tg):
        return tuple((t[0], t[1], t[2], t[3]) for t in tg)

    KIT = None          # this champion's live Kit (70_decide sets it)

    # ---------------------------------------------------------------- the enemy damage model (one, used everywhere)
    class UnitModel:
        """What one visible champion (either team) can do on its NEXT turn and over a fight. Built by
        enemy_model (live reads) or kit_model (a Kit alone, every slot ready).
            bt[d]   most damage it can land on a tile at Chebyshev distance d next turn (0 beyond reach)
            stt[d]  it can stun a tile at distance d next turn
            burst_v bt[1] (contact)    reach   largest d with bt[d] > 0    dpr_v  sustained per round vs us
            hp_eff  HP + current shield; shield_rdy = a self-shield it can still cast (Varg)
            chan    remaining tribute / recall channel rounds (0 none)    casts  ((value, ready-in, stun), ...)
        It also passes for a Kit (duck-typed: S, F, max_hp, slots, arange, ranged, passives, stunner, dash,
        dpr(), burst(), focus()), so any Kit consumer (duel_gate's them, 65_hunt's live_kit) can take it."""
        __slots__ = ("id", "ctype", "kit", "pos", "prev", "S", "F", "max_hp", "hp", "shield", "shield_rdy", "stunned",
                     "chan", "bag", "cds", "cd_known", "ranged", "arange", "bt", "stt", "burst_v", "dpr_v", "reach",
                     "stunner", "hp_eff", "retaliate", "stun_immune", "rnd", "casts", "slots", "splash",
                     "reset_on_kill", "gem_focus", "dash", "me", "sf_r", "sf_bag", "shield_kit", "cd_r", "cd_read")

        def dpr(self, vs_champ=True, bag=0):
            """Kit-compatible: the live sustained damage per round (vs champions)."""
            return self.dpr_v

        def burst(self, bag=0):
            """Kit-compatible: the live contact burst (basic + its best ready spell or reset)."""
            return self.burst_v

        def focus(self, bag=0):
            return self.F

        def fleeing(self, frm):
            """A carrier that walked away from frm since the previous round we modelled it."""
            return self.bag > 0 and self.prev is not None and self.prev != self.pos and                 self.pos.chebyshev_distance(frm) > self.prev.chebyshev_distance(frm)

    _TAB = {}        # (ctype, S, F, slot 0 ready, slot 1 ready, stunned) -> table entry (any unit in that state)

    def _tables(m):
        # Burst / stun tables for the unit's next turn [rules: one walk, one basic attack, one successful cast;
        # ranged champions move OR attack, also with a ranged damaging spell; an excl spell takes the walk; a
        # reset gives a second basic attack. measured A46: melee dash + walk + attack (reach 4), ranged dash +
        # attack (reach 5); a dash is the turn's cast]. Also the fight cast list ((value, ready-in, stun), ...)
        # the duel schedules, the sustained dpr vs champions and a self-shield it can still cast. One dict lookup
        # per call once warm (fuel: ~1k per loop iteration [measured]).
        cds = m.cds
        key = (m.ctype, m.S, m.F, cds[0] == 0, len(cds) > 1 and cds[1] == 0, m.stunned)
        r = _TAB.get(key)
        if r is None:
            k, S, F, ar = m.kit, m.S, m.F, m.arange
            best = [0.0] * DMAX
            stun = [False] * DMAX
            casts = []                                           # template: (slot, value, stun)
            dpr, sh = S, 0.0
            rb = ar if m.ranged else ar + 1                      # basic reach: a melee may walk first
            opts = [(rb, S, False)]
            for sl in k.slots:
                kd = sl.kind
                ready = cds[sl.i] if sl.i < len(cds) else 0
                if kd == K_RESET:
                    dpr += S / COOLDOWN
                    casts.append((sl.i, S, sl.enhanced))
                    if not ready:
                        opts.append((rb, 2 * S, sl.enhanced))
                elif kd == K_DASH and sl.ground:
                    if not ready:
                        opts.append((sl.rng + ar + (0 if m.ranged else 1), S, False))
                elif kd in (K_DMG, K_CC, K_AOE) and (sl.enemies or sl.ground):
                    v = sl.mod * F
                    dpr += v / COOLDOWN
                    area = kd == K_AOE or (sl.ground and not sl.enemies)
                    rc = sl.rng + (sl.radius if area else 0)
                    casts.append((sl.i, v, sl.stun))
                    if ready:
                        continue
                    if sl.excl or (m.ranged and v > 0):          # no walk this turn: basic from where it stands
                        opts.append((min(rc, ar), S + v, sl.stun))
                        opts.append((rc, v, sl.stun))
                    else:                                        # walk-compatible (Cassi's stun): walk, then cast
                        opts.append((min(rc + 1, rb), S + v, sl.stun))
                        opts.append((rc + 1, v, sl.stun))
                elif kd == K_SHIELD and sl.self_ and not ready:
                    sh = sl.mod * F
            if not m.stunned:                                    # a stunned unit loses its next turn [rules]
                for rr, v, s_ in opts:
                    rr = min(rr, DMAX - 1)
                    if v > best[rr]:
                        best[rr] = v
                    if s_:
                        stun[rr] = True
                for d in range(DMAX - 2, -1, -1):                # reach d also covers every nearer tile
                    if best[d + 1] > best[d]:
                        best[d] = best[d + 1]
                    stun[d] = stun[d] or stun[d + 1]
            reach = max([d for d in range(DMAX) if best[d] > 0] + [0])
            r = _TAB[key] = (tuple(best), tuple(stun), tuple(casts), best[1], reach, any(stun), dpr, sh)
        m.bt, m.stt, tm, m.burst_v, m.reach, m.stunner, m.dpr_v, m.shield_rdy = r
        if len(tm) == 2:                                         # the fight cast list: (value, ready-in, stun)
            a, b = tm
            m.casts = ((a[1], cds[a[0]], a[2]), (b[1], cds[b[0]], b[2]))
        else:
            m.casts = tuple([(v, cds[i], s_) for i, v, s_ in tm])
        m.hp_eff = m.hp + m.shield

    def _static(m, kit):
        m.kit = kit
        m.ctype = kit.ctype
        m.ranged, m.arange = kit.ranged, kit.arange
        m.retaliate, m.stun_immune = kit.retaliate, kit.stun_immune
        m.slots, m.splash, m.reset_on_kill, m.gem_focus = kit.slots, kit.splash, kit.reset_on_kill, kit.gem_focus
        m.dash, m.me, m.sf_r, m.sf_bag, m.cd_r = kit.dash, None, -99, 0, -1
        m.cds = m.cd_read = (0,) * len(kit.slots)
        m.shield_kit = any([sl.kind == K_SHIELD for sl in kit.slots])
        m.prev = m.pos = None
        m.rnd = -1

    _EM = {}            # champion id -> UnitModel (refilled once per round)
    _CD_OK = [None]     # can another champion's cooldowns be read? None untested, then True / False (probed once)

    def enemy_model(c, snap=None, row=None):
        """The live model of a visible champion (any team), once per (id, round). row = its snapshot row
        (pos, hp, bag, Champion) when the caller has it (saves three reads). Reads Strength, Focus, max HP
        (shards and Prism's gems included [sdk]; re-read every SF_EVERY rounds), buffs (shield value, stun; only
        for a kit with a self-shield), state (tribute / recall channel)
        and the ability cooldowns when the engine allows reading them on another champion (probed once and
        traced kit|enemy_cd; else every slot is assumed ready: the safe side)."""
        i = int(c)
        rnd = snap.rnd if snap is not None else cambc.round_number()
        m = _EM.get(i)
        if m is not None and m.rnd == rnd:
            return m
        if m is None:
            m = UnitModel()
            m.id = i
            _static(m, kit_of(int(c.champion_name())))
            _EM[i] = m
        m.prev = m.pos if m.rnd == rnd - 1 else None            # a fresh sighting has no direction of travel
        m.rnd = rnd
        if row is None and snap is not None:
            for e in snap.enemies:
                if int(e[3]) == i:
                    row = e
                    break
        k = m.kit
        try:
            if row is not None:
                m.pos, m.hp, m.bag = row[0], row[1], row[2]
            else:
                m.pos, m.hp, m.bag = c.position(), c.health(), c.gem_count()
        except Exception:
            m.pos, m.hp, m.bag = m.pos or V(0, 0), k.max_hp, 0
        if m.sf_r < rnd - SF_EVERY or m.prev is None:          # shards change only at a spawn: re-read rarely
            try:
                m.S, m.F, m.max_hp = c.strength(), c.focus(), c.max_health()
            except Exception:
                m.S, m.F, m.max_hp = k.S, k.F, k.max_hp
            m.sf_r, m.sf_bag = rnd, m.bag
        elif m.gem_focus and m.bag != m.sf_bag:                  # Prism: 0.2 Focus per carried gem [rules]
            m.F += GEM_FOCUS * (m.bag - m.sf_bag)
            m.sf_bag = m.bag
        m.shield, m.stunned = 0.0, False
        if m.shield_kit:                                         # buffs + 2 tests ~23k [measured]: only for a kit
            try:                                                 # that can shield itself (else no shield; a stun
                b = c.buffs()                                    # on it is ignored: the safe side)
                if b.has_shield():
                    m.shield = b.get(cambc.BuffShield).value
                m.stunned = b.has_stun()
            except Exception:
                pass
        m.chan = 0
        try:
            if int(c.state()) & (ST_SUBMITTING | ST_RECALLING):
                m.chan = max(1, int(c.remaining_channel_time()))
        except Exception:
            pass
        cds = (0,) * len(k.slots)
        m.cd_known = False
        if m.cd_r >= 0 and m.prev is not None:                   # cooldowns tick down exactly; only a cast (on a
            dt = rnd - m.cd_r                                    # ready slot) raises one: re-read only when some
            pc = tuple([c - dt if c > dt else 0 for c in m.cd_read])   # slot may be ready (~31k a read)
            if 0 not in pc or dt <= 1:                            # (a ready slot read last round: still assumed ready)
                cds = pc
                m.cd_known = True
        if not m.cd_known and _CD_OK[0] is not False:
            try:
                cds = tuple([int(a.cooldown()) for a in c.abilities()])
                m.cd_known = True
                m.cd_r, m.cd_read = rnd, cds
                if _CD_OK[0] is None:
                    _CD_OK[0] = True
                    trace("kit", f"enemy_cd readable=1 vs=c{i} cds={'/'.join(map(str, cds))}")
            except Exception as e:
                if _CD_OK[0] is None:
                    _CD_OK[0] = False
                    trace("kit", f"enemy_cd readable=0 {err_text(e)}")
                cds = (0,) * len(k.slots)
        m.cds = cds
        _tables(m)
        return m

    unit_model = enemy_model        # the same reads work on a visible ally

    _KM = {}

    def kit_model(kit, hp=None, bag=0, shield=0.0, cds=None):
        """A model from a Kit alone (design or live; every slot ready unless cds is given), for callers with
        no Champion handle. One object per kit, refilled on each call: read it before the next call."""
        m = _KM.get(id(kit))
        if m is None or m.kit is not kit:
            m = _KM[id(kit)] = UnitModel()
            _static(m, kit)
            m.id = -1 - len(_KM)
            m.prev = None
        hp = kit.max_hp if hp is None else hp
        known = cds is not None
        cds = tuple(cds) if cds is not None else (0,) * len(kit.slots)
        if m.rnd == (kit.S, kit.F, hp, bag, shield, cds):
            return m                                             # same state as the last call: nothing to redo
        m.rnd = (kit.S, kit.F, hp, bag, shield, cds)
        m.S, m.F, m.max_hp, m.hp = kit.S, kit.F, kit.max_hp, hp
        m.bag, m.shield, m.stunned, m.chan = bag, shield, False, 0
        m.cds, m.cd_known = cds, known
        _tables(m)
        return m

    def enemy_threat(snap, pos, rows=None):
        """Damage the visible enemies can land on tile pos on their next turn: the sum of each one's bt[d]
        (its burst at that distance, 0 beyond its reach). rows default snap.enemies. The champion half of inc."""
        x, y = pos.x, pos.y
        t = 0.0
        for e in (snap.enemies if rows is None else rows):
            p = e[0]
            d = max(abs(p.x - x), abs(p.y - y))
            if d < DMAX:
                t += enemy_model(e[3], snap, e).bt[d]
        return t

    def stun_threat(snap, pos, rows=None):
        """True when a visible enemy can stun tile pos on its next turn (stt): tribute / recall safety."""
        x, y = pos.x, pos.y
        for e in (snap.enemies if rows is None else rows):
            p = e[0]
            d = max(abs(p.x - x), abs(p.y - y))
            if d < DMAX and enemy_model(e[3], snap, e).stt[d]:
                return True
        return False

    def team_strength(snap, allies=(), enemies=None, kit=None, shield=0.0, r=KIT_R1 + 3):
        """Lanchester square law: a side's strength = (sum dpr) x (sum effective HP); we win a straight brawl
        iff ours > theirs. allies: visible ally Champion handles (live models) or (pos, ctype[, hp]) rows
        (design kit; full HP unless given); I am included when kit (my live Kit) is given. enemies: snapshot
        rows (default every visible enemy). Their first-turn alpha strike (sum burst - sum dpr) comes off our
        HP pool (pessimistic: they strike first). Returns (ours, theirs).
        Also callable as team_strength(w, s, p): everything visible within r of tile p, me included (my live
        Kit, my shield), allies read live (vision.champions ~17k)."""
        if hasattr(snap, "snap") and hasattr(snap, "me"):        # (World, Snap, Vec2) form
            w, snap, p = snap, allies, enemies
            me = int(w.me)
            allies = []
            try:
                for a in vision.champions(Team.ALLY):
                    if int(a) != me and a.position().chebyshev_distance(p) <= r:
                        allies.append(a)
            except Exception:
                pass
            enemies = [e for e in snap.enemies if e[0].chebyshev_distance(p) <= r]
            mk = globals().get("my_kit")
            kit = mk(w) if mk is not None else KIT
            sh = globals().get("shield_of")
            shield = sh(w) if sh is not None else 0.0
        dpr = hp = 0.0
        if kit is not None:
            dpr, hp = kit.dpr(True), snap.hp + shield
        for a in allies:
            if isinstance(a, (tuple, list)):
                k = kit_of(a[1])
                dpr += k.dpr(True)
                hp += a[2] if len(a) > 2 else k.max_hp
            else:
                try:
                    m = enemy_model(a, snap)
                    dpr += m.dpr_v
                    hp += m.hp_eff
                except Exception:
                    pass
        tdpr = thp = alpha = 0.0
        for e in (snap.enemies if enemies is None else enemies):
            m = enemy_model(e[3], snap, e)
            tdpr += m.dpr_v
            thp += m.hp_eff + m.shield_rdy
            alpha += m.burst_v - m.dpr_v
        return dpr * max(0.0, hp - alpha), tdpr * thp

    # ---------------------------------------------------------------- plan_turn
    class Intent:
        """atk / atk2 = target index; cast = (slot, None | index | (x, y)); move_to = the one walk (Vec2) the
        champion policy wants BEFORE act() (the task makes it with Nav, the single mover); land = a dash
        landing (x, y) that act() casts; pre = act() casts before attacking (dash-in); retreat = the plan
        disengages (flee / kite out); focus = the champion target index the policy fires at."""
        __slots__ = ("kit", "tg", "atk", "cast", "atk2", "needs_stand", "dmg", "val", "idle", "hp", "want",
                     "move_to", "retreat", "land", "pre", "focus", "why")

        def __init__(self, kit, tg):
            self.kit, self.tg = kit, tg
            self.atk = self.cast = self.atk2 = self.want = None
            self.move_to = self.land = self.focus = None
            self.needs_stand = self.retreat = self.pre = False
            self.dmg = self.val = 0.0
            self.idle = []
            self.why = "-"

        @property
        def attack(self):
            return self.atk

        @property
        def expected_damage(self):
            return self.dmg

    def plan_turn(kit, snap, targets, allow_walk=False, inc=0, cds=None, pos=None, moved=False,
                  walk_value=None, avoid=(), w=None, blocked=None, retreat=False, shield=0.0):
        """Pure: the best (attack, cast) this turn. allow_walk = the caller wants to walk this turn; an
        "excludes walking" cast then needs value > walk_value (default one Strength; FAR when fleeing),
        and a ranged attack needs S >= walk_value. moved = a walk already happened (no excl cast, no
        ranged attack). Walk first: in a camp fight with no monster in attack reach of the stand,
        nothing is cast. avoid = (x, y) of monsters we must not wake (other groups, I17). Intent: atk /
        atk2 = target index, cast = (slot, None | index | (x, y)), want (Varg: the target to stand
        next to), needs_stand, dmg (expected), val, idle.
        Champion fights: when any row carries a UnitModel (row[7]: champ_target(..., em=) or champ_rows) the
        champion policy (_plan_champ) plans the turn, including .move_to / .land when w (World: walls(w, snap)
        is the passability mask) or blocked (a Bitboard of tiles we cannot stand on) is given; retreat=True
        disengages (walk + dash away); shield = our current shield (ttd)."""
        p = pos if pos is not None else snap.pos
        for t in targets:
            if len(t) > 7 and t[7] is not None:
                if cds is None:
                    cds = kit.cds(snap.rnd)
                if blocked is None and w is not None:
                    try:
                        blocked = walls(w, snap)
                    except Exception:
                        blocked = None
                return _plan_champ(kit, snap, targets, inc, cds, p, moved, blocked, retreat, shield)
        px, py = p.x, p.y
        n = len(targets)
        hp = [t[0] for t in targets]
        xs = [t[2] for t in targets]
        ys = [t[3] for t in targets]
        dist = [max(abs(xs[i] - px), abs(ys[i] - py)) for i in range(n)]
        if cds is None:
            cds = kit.cds(snap.rnd)
        st = snap.st
        S, F = kit.S, kit.F
        wv = S if walk_value is None else walk_value
        it = Intent(kit, targets)
        reach = [i for i in range(n) if hp[i] > 0 and dist[i] <= kit.arange]
        camps = all(t[5][0] == "g" for t in targets)
        nb = [[]] * n
        if n > 1:                                # neighbours within 1, cached per group shape
            shape = tuple(zip(xs, ys))
            nb = _NEAR.get(shape)
            if nb is None:
                nb = _NEAR[shape] = [[j for j in range(n) if j != i and -2 < xs[i] - xs[j] < 2
                                      and -2 < ys[i] - ys[j] < 2] for i in range(n)]
        nc = [len(x) for x in nb]
        wk = [any(max(abs(xs[i] - a), abs(ys[i] - b)) <= 1 for a, b in avoid) for i in range(n)] if avoid \
            else [False] * n

        def pick(cand):
            if kit.splash:                       # Varg: widest splash, never next to another group
                return min(cand, key=lambda i: (wk[i], -nc[i], hp[i]), default=None)
            return min(cand, key=lambda i: (hp[i], nc[i]), default=None)   # weakest; ties: edge first

        def hit(i, d):
            dealt = min(max(hp[i], 0), d)
            hp[i] -= d
            if kit.splash:                       # Strength onto the others within 1 of the target [rules]
                for j in nb[i]:
                    if hp[j] > 0:
                        dealt += min(hp[j], d)
                        hp[j] -= d
            return dealt

        if kit.splash and n:
            it.want = pick([i for i in range(n) if hp[i] > 0])
        if reach and st & ST_CAN_ATTACK and not (kit.ranged and (moved or (allow_walk and S < wv))):
            i = it.atk = pick(reach)
            it.dmg += hit(i, S)
            it.needs_stand = kit.ranged          # ranged: move OR attack [rules]
            if kit.reset_on_kill and (hp[i] <= 0 or kit.splash and any(hp[j] <= 0 for j in nb[i])):
                cds = (0,) * len(cds)            # Vendetta: a kill resets every cooldown [rules]
            reach = [j for j in reach if hp[j] > 0]
        if not st & ST_CAN_CAST or not n:
            it.hp = hp
            return it
        approach = camps and not reach and it.atk is None      # walk first: no cast from out of reach
        best, bv, why = None, 0.0, {}
        for sl in kit.slots:
            s, k = sl.i, sl.kind
            if cds[s] > 0 or k not in USEFUL:
                continue
            if approach:
                why[s] = "excl_walk_flee" if sl.excl else "no_target"
                continue
            v, tgt = 0.0, None
            if k == K_RESET:
                if it.atk is not None and reach:
                    j = pick(reach)
                    v = S + (targets[j][1] if sl.enhanced and not targets[j][6] else 0)
            elif k == K_SHIELD:
                v = min(sl.mod * F, inc * sl.dur)
            elif k == K_HEAL:
                v = min(sl.mod * F, kit.max_hp - snap.hp) if sl.self_ else 0
            elif k == K_AOE or (sl.ground and not sl.camps and not sl.enemies):
                d, r = sl.mod * F, sl.radius
                for c in range(n):
                    if hp[c] > 0 and dist[c] <= sl.rng and targets[c][5] != "lock" and not wk[c]:
                        cov = nb[c] if r == 1 else [j for j in range(n) if j != c and
                                                    max(abs(xs[c] - xs[j]), abs(ys[c] - ys[j])) <= r]
                        vv = 0.0
                        for j in cov + [c]:
                            if hp[j] > 0:
                                vv += min(hp[j], d) + (targets[j][1] if sl.stun and not targets[j][6] else 0)
                        if vv > v:
                            v, tgt = vv, c
            else:                                # unit damage / cc: the weakest valid target in range
                cand = [j for j in range(n) if hp[j] > 0 and dist[j] <= sl.rng and
                        (sl.camps if targets[j][5][0] == "g" else sl.enemies and targets[j][5][0] == "c")]
                if cand:
                    tgt = min(cand, key=hp.__getitem__)
                    v = min(hp[tgt], sl.mod * F) + (targets[tgt][1] if sl.stun and not targets[tgt][6] else 0)
            if v <= 0:
                why[s] = "no_value" if (tgt is not None or k in (K_SHIELD, K_HEAL, K_RESET)) else "no_target"
                continue
            if sl.excl and (moved or (allow_walk and v <= wv)):
                why[s] = "excl_walk_flee"        # the walk wins this turn (I6 reason)
                continue
            if v > bv:
                best, bv = (s, tgt, k == K_AOE or (sl.ground and not sl.camps and not sl.enemies)), v
        if best is None:
            it.idle = sorted(why.items())
            it.hp = hp
            return it
        s, tgt, area = best
        sl = kit.slots[s]
        it.val = bv
        it.needs_stand = it.needs_stand or sl.excl
        if sl.kind == K_RESET:
            it.cast = (s, None)
            it.atk2 = pick(reach)
            it.dmg += hit(it.atk2, S)
        elif area:
            it.cast = (s, (xs[tgt], ys[tgt]))
            d, r = sl.mod * F, sl.radius
            for j in range(n):
                if hp[j] > 0 and max(abs(xs[tgt] - xs[j]), abs(ys[tgt] - ys[j])) <= r:
                    it.dmg += min(hp[j], d)
                    hp[j] -= d
        else:
            it.cast = (s, tgt)
            if tgt is not None:
                it.dmg += min(hp[tgt], sl.mod * F)
                hp[tgt] -= sl.mod * F
        it.hp = hp
        return it

    # ---------------------------------------------------------------- the champion policy (plan_turn with models)
    # One champion-fight turn, data-driven per kit (no champion names; passives as data) [ROLES §3 L3].
    # Focus: the champion we kill soonest (ceil(hp / our best turn)), among those we can hit this turn first;
    # ties: a carrier (P8 strike the weak carrier), then one that can stun us next turn, then the nearest;
    # a reset-on-kill kit (Vendetta) takes the lowest HP first (the kill resets her cooldowns [rules]).
    # Moves (P6, position before force):
    #   melee   in reach: attack; one walk short: walk then attack; walk + dash short: dash in (walk first if
    #           needed) and attack (reach 4 [measured A46]); else walk closer
    #   ranged  in range: attack, unless the enemies can hit this tile next turn AND the trade is losing: then
    #           step to a tile in range no enemy reaches (kite); out of range: dash to a tile in range (dash +
    #           attack, reach 5 [measured A46]), else walk to the safest closer tile
    #   retreat walk to the tile with the least enemy burst, then dash farther if still in reach (P8, P21)
    # Walking is weighed against staying: a staying excl cast (nuke, area stun) or a ranged attack wins when
    # worth more than what the walk buys (the attack it enables, the threat it avoids; FAR on retreat).
    # Casts (one per turn): damage + KILL_VAL when it finishes a champion; a stun is worth the stunned unit's
    # next-turn burst on us (x2 when it would kill us), + CHAN_VAL on a channel (P15), + FLEE_VAL on a carrier
    # walking away; shield = min(amount, threat x duration) once an enemy is in contact reach; reset = a second
    # attack (an enhanced reset goes to a carrier in reach: Marcella's stun); area spells are valued over
    # every row in the radius (Ryth / Stellar pick the centre covering the most).
    # Fuel: every Python call costs ~2-6k [measured], so no closures, lambdas or sort keys per candidate.
    _NB = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
    _RING = {}          # dash range -> the offsets at exactly that range

    def _scored(E, tiles, tx, ty, mode):
        """[(key, (x, y))] for candidate tiles. mode 0: (threat, dist to (tx, ty)); 1: (threat, -dist to tx,ty);
        2: (threat, -nearest enemy); 3: (dist to (tx, ty), threat); 4: (threat > 0, dist, threat)."""
        out = []
        for q in tiles:
            x, y = q
            t = 0.0
            m = FAR
            for ex, ey, bt in E:
                dx = ex - x
                dy = ey - y
                d = (dx if dx > 0 else -dx)
                if dy > d or -dy > d:
                    d = dy if dy > 0 else -dy
                if d < DMAX:
                    t += bt[d]
                if d < m:
                    m = d
            dx = tx - x
            dy = ty - y
            df = (dx if dx > 0 else -dx)
            if dy > df or -dy > df:
                df = dy if dy > 0 else -dy
            if mode == 0:
                out.append(((t, df), q))
            elif mode == 1:
                out.append(((t, -df), q))
            elif mode == 2:
                out.append(((t, -m), q))
            elif mode == 3:
                out.append(((df, t), q))
            else:
                out.append(((t > 0, df, t), q))
        out.sort()
        return out

    def _first_free(blocked, scored):
        """(key, (x, y)) of the best-scored tile we may stand on, or None (no mask: nothing planned blind)."""
        if blocked is None:
            return None
        for k, q in scored:
            if q[0] < 0 or q[1] < 0:
                continue
            try:
                if not blocked.is_set(V(q[0], q[1])):
                    return k, q
            except Exception:
                pass
        return None

    def _plan_champ(kit, snap, targets, inc, cds, p, moved, blocked, retreat, shield):
        it = Intent(kit, targets)
        it.retreat = retreat
        n = len(targets)
        S, F, ar = kit.S, kit.F, kit.arange
        st = snap.st
        px, py = p.x, p.y
        hp = [t[0] for t in targets]
        xs = [t[2] for t in targets]
        ys = [t[3] for t in targets]
        ems = [t[7] if len(t) > 7 else None for t in targets]
        d0 = [max(abs(xs[i] - px), abs(ys[i] - py)) for i in range(n)]
        ch = [i for i in range(n) if ems[i] is not None and hp[i] > 0]
        can_atk = bool(st & ST_CAN_ATTACK)
        can_cast = bool(st & ST_CAN_CAST)
        can_walk = bool(snap.can_move) and not moved and blocked is not None
        dsl = kit.dash
        dash = dsl if (can_cast and dsl is not None and cds[dsl.i] == 0 and blocked is not None) else None
        myhp = snap.hp + shield
        E = [(xs[i], ys[i], ems[i].bt) for i in ch]
        here = 0.0
        for i in ch:
            if d0[i] < DMAX:
                here += ems[i].bt[d0[i]]
        spell = 0.0
        for sl in kit.slots:
            if cds[sl.i] == 0:
                if sl.kind in (K_DMG, K_CC, K_AOE) and (sl.enemies or sl.ground):
                    spell = max(spell, sl.mod * F)
                elif sl.kind == K_RESET:
                    spell = max(spell, S)
        per = S + spell
        reach_now = ar + (1 if (not kit.ranged and can_walk) else 0) + (dash.rng if dash is not None else 0)
        # stun value of each row, from where we stand (I6 currency: damage-equivalent HP)
        sv = [0.0] * n
        stun_rdy = False
        for sl in kit.slots:
            if sl.stun and cds[sl.i] == 0:
                stun_rdy = True
        fbest = None
        tdpr = 0.0
        for i in range(n):
            m = ems[i]
            if m is None:
                sv[i] = 0 if targets[i][6] else targets[i][1]
                continue
            dd = d0[i] if d0[i] < DMAX else DMAX - 1
            if stun_rdy and not m.stun_immune:
                v = m.bt[dd]
                if v >= myhp:
                    v += myhp                                     # the enemy about to kill us
                if m.chan:
                    v += CHAN_VAL                                 # a stun breaks the channel [rules] (P15)
                if m.bag > 0 and m.prev is not None and m.prev != m.pos and \
                        dd > max(abs(m.prev.x - px), abs(m.prev.y - py)):
                    v += FLEE_VAL                                 # a carrier walking away
                sv[i] = v
            if hp[i] > 0:
                if d0[i] <= m.reach + 1:
                    tdpr += m.dpr_v
                k = (d0[i] > reach_now, hp[i] if kit.reset_on_kill else 0, -(-hp[i] // per), m.bag <= 0,
                     not m.stt[dd], d0[i], hp[i], i)
                if fbest is None or k < fbest:
                    fbest = k
        focus = fbest[-1] if fbest is not None else None
        it.focus = focus
        losing = False
        if focus is not None and kit.ranged:
            a = -(-hp[focus] // max(1.0, kit.dpr(True)))
            losing = a * TTK_RATIO > (myhp // tdpr if tdpr > 0 else FAR)

        # ------------------------------------------------ movement: one walk (mv) and / or a dash landing
        mv = land = None
        kite = False
        nbr = [(px + a, py + b) for a, b in _NB]
        if retreat and E:
            cx = sum([e[0] for e in E]) / len(E)                  # the enemies' centre: retreat tiles point away
            cy = sum([e[1] for e in E]) / len(E)
            sc = _scored(E, [(px, py)] + [(px + a, py + b) for a, b in _NB if a * (px - cx) + b * (py - cy) >= 0]
                         if can_walk else [(px, py)], px, py, 2)
            cur = [k for k, q in sc if q[0] == px and q[1] == py][0]
            if can_walk:
                r = _first_free(blocked, [x for x in sc if x[1][0] != px or x[1][1] != py])
                if r is not None and r[0] < cur:
                    mv, cur = r[1], r[0]
            ox, oy = mv if mv is not None else (px, py)
            if dash is not None and cur[0] > 0:
                ring = _RING.get(dash.rng)
                if ring is None:
                    rr = dash.rng
                    ring = _RING[rr] = [(a, b) for a in range(-rr, rr + 1) for b in range(-rr, rr + 1)
                                        if a in (-rr, rr) or b in (-rr, rr)]
                away = sorted([(-(a * (ox - cx) + b * (oy - cy)), a, b) for a, b in ring])[:5]   # the 5 most away
                r = _first_free(blocked, _scored(E, [(ox + a, oy + b) for _, a, b in away], ox, oy, 2))
                if r is not None and r[0] < cur:
                    land = r[1]
            it.why = "retreat"
        elif focus is not None:
            fx, fy = xs[focus], ys[focus]
            df = d0[focus]
            if kit.ranged:
                if df <= ar:
                    if here > 0 and losing and can_walk:
                        cands = [q for q in nbr if 0 < max(abs(q[0] - fx), abs(q[1] - fy)) <= ar]
                        r = _first_free(blocked, _scored(E, cands, fx, fy, 1))
                        if r is not None and r[0][0] == 0:
                            mv, kite = r[1], True
                            it.why = "kite"
                else:
                    if dash is not None and df <= dash.rng + ar:
                        rr = dash.rng
                        cands = [(px + a, py + b) for a in range(-rr, rr + 1) for b in range(-rr, rr + 1)
                                 if (a or b) and 0 < max(abs(px + a - fx), abs(py + b - fy)) <= ar]
                        r = _first_free(blocked, _scored(E, cands, fx, fy, 1))
                        if r is not None and (not losing or r[0][0] == 0):
                            land = r[1]
                            it.why = "dash_in"
                    if land is None and can_walk:
                        cands = [q for q in nbr if max(abs(q[0] - fx), abs(q[1] - fy)) < df]
                        r = _first_free(blocked, _scored(E, cands, fx, fy, 4 if losing else 3))
                        if r is not None:
                            mv = r[1]
                            it.why = "approach"
            elif df > ar:
                if can_walk and df <= ar + 1:
                    cands = [q for q in nbr if 0 < max(abs(q[0] - fx), abs(q[1] - fy)) <= ar]
                    r = _first_free(blocked, _scored(E, cands, fx, fy, 0))
                    if r is not None:
                        mv = r[1]
                        it.why = "close"
                if mv is None and dash is not None and df <= ar + dash.rng + (1 if can_walk else 0):
                    ox, oy = px, py
                    rr = dash.rng
                    if df > ar + rr:                              # walk first, then dash [measured A46: either order]
                        cands = [q for q in nbr if max(abs(q[0] - fx), abs(q[1] - fy)) == df - 1]
                        r = _first_free(blocked, _scored(E, cands, fx, fy, 0))
                        if r is not None:
                            mv = r[1]
                            ox, oy = mv
                    if max(abs(fx - ox), abs(fy - oy)) <= ar + rr:
                        cands = [(fx + a, fy + b) for a in range(-ar, ar + 1) for b in range(-ar, ar + 1)
                                 if (a or b) and max(abs(fx + a - ox), abs(fy + b - oy)) <= rr
                                 and (fx + a != ox or fy + b != oy)]
                        r = _first_free(blocked, _scored(E, cands, ox, oy, 0))
                        if r is not None:
                            land = r[1]
                            it.why = "dash_in"
                if mv is None and land is None and can_walk:
                    cands = [q for q in nbr if max(abs(q[0] - fx), abs(q[1] - fy)) < df]
                    r = _first_free(blocked, _scored(E, cands, fx, fy, 3))
                    if r is not None:
                        mv = r[1]
                        it.why = "approach"

        # ------------------------------------------------ attack and cast valuation
        def best_cast(x, y, allow_excl, atk):
            """(value, slot, target, area, why) of the best ready cast from tile (x, y), given our attack."""
            best, why = (0.0, None, None, False), {}
            h2 = hp[:]                                            # rows' HP after this turn's planned attack
            cd = cds
            if atk is not None:
                h2[atk] -= S
                if kit.reset_on_kill and h2[atk] <= 0 and ems[atk] is not None:
                    cd = (0,) * len(cds)                          # Vendetta: the kill resets every cooldown [rules]
            for sl in kit.slots:
                s_, k = sl.i, sl.kind
                if cd[s_] > 0 or k not in USEFUL:
                    continue
                if sl.excl and not allow_excl:
                    why[s_] = "excl_walk_flee"
                    continue
                v, tgt, area = 0.0, None, False
                if k == K_RESET:
                    if atk is not None:
                        j, jk = None, None
                        for i in range(n):
                            if h2[i] > 0 and max(abs(xs[i] - x), abs(ys[i] - y)) <= ar:
                                if sl.enhanced:                   # Marcella: the stunning attack on a carrier
                                    m = ems[i]
                                    kk = (not (m is not None and m.bag > 0 and not m.stun_immune), i != atk, h2[i])
                                else:
                                    kk = (i != atk, h2[i])
                                if jk is None or kk < jk:
                                    j, jk = i, kk
                        if j is not None:
                            v, tgt = min(h2[j], S) + (sv[j] if sl.enhanced else 0) + \
                                (KILL_VAL if ems[j] is not None and h2[j] <= S else 0), j
                elif k == K_SHIELD:
                    th = inc
                    for ex, ey, bt in E:
                        dd = max(abs(ex - x), abs(ey - y))
                        if dd <= 2:                               # an enemy in contact reach (walk + attack)
                            th += bt[dd]
                    v = min(sl.mod * F, th * sl.dur)
                elif k == K_HEAL:
                    v = min(sl.mod * F, kit.max_hp - snap.hp) if sl.self_ else 0
                elif k == K_AOE or (sl.ground and not sl.camps and not sl.enemies):
                    d, r = sl.mod * F, sl.radius
                    for c in range(n):
                        if h2[c] > 0 and max(abs(xs[c] - x), abs(ys[c] - y)) <= sl.rng and targets[c][5] != "lock":
                            vv = 0.0
                            for j in range(n):
                                h = h2[j]
                                if h > 0 and max(abs(xs[c] - xs[j]), abs(ys[c] - ys[j])) <= r:
                                    vv += (h if h < d else d) + (sv[j] if sl.stun else 0) + \
                                        (KILL_VAL if ems[j] is not None and h <= d else 0)
                            if vv > v:
                                v, tgt, area = vv, c, True
                elif k in (K_DMG, K_CC):
                    d = sl.mod * F
                    for j in range(n):
                        h = h2[j]
                        if h > 0 and max(abs(xs[j] - x), abs(ys[j] - y)) <= sl.rng and \
                                (sl.enemies if ems[j] is not None else sl.camps):
                            vv = (h if h < d else d) + (sv[j] if sl.stun else 0) + \
                                (KILL_VAL if ems[j] is not None and h <= d else 0)
                            if vv > v:
                                v, tgt = vv, j
                if v <= 0:
                    why[s_] = "no_value" if (tgt is not None or k in (K_SHIELD, K_HEAL, K_RESET)) else "no_target"
                    continue
                if v > best[0]:
                    best = (v, s_, tgt, area)
            return best + (why,)

        def atk_at(x, y, walked):
            if not can_atk or (kit.ranged and walked):
                return None
            if focus is not None and max(abs(xs[focus] - x), abs(ys[focus] - y)) <= ar:
                return focus
            b = None
            for i in range(n):
                if hp[i] > 0 and max(abs(xs[i] - x), abs(ys[i] - y)) <= ar:
                    k = (ems[i] is None, hp[i], i)
                    if b is None or k < b:
                        b = k
            return b[-1] if b is not None else None

        it.idle = []
        if land is not None:
            a = atk_at(land[0], land[1], kit.ranged and mv is not None)
            vd = FAR if retreat else (S if a is not None else 0.0)
            if not retreat:
                ox, oy = mv if mv is not None else (px, py)
                c0 = best_cast(ox, oy, mv is None and not moved, atk_at(ox, oy, mv is not None or moved))
                if c0[0] > vd:
                    land = None
            if land is not None:
                atk = a
                c = (vd, dsl.i, land, False, {})
        if land is None:
            if mv is not None:
                a1 = atk_at(mv[0], mv[1], True)
                c1 = best_cast(mv[0], mv[1], False, a1)
                # staying differs only through an excl cast or a ranged attack from here (else the walk is free)
                alt = not retreat and (kit.ranged or any([sl.excl and cds[sl.i] == 0 for sl in kit.slots]))
                a2 = atk_at(px, py, moved) if alt else None
                c2 = best_cast(px, py, not moved, a2) if alt else (0.0,)
                wv = FAR if retreat else 0.0
                if kite:
                    wv = here - _scored(E, [mv], px, py, 0)[0][0][0]
                if alt and c2[0] + (S if a2 is not None else 0) > c1[0] + (S if a1 is not None else 0) + wv:
                    mv = None
                    atk, c = a2, c2
                else:
                    atk, c = a1, c1
            else:
                atk = atk_at(px, py, moved)
                c = best_cast(px, py, not moved, atk)

        # ------------------------------------------------ apply (expected damage, rows' HP after our turn)
        it.move_to = V(mv[0], mv[1]) if mv is not None else None
        if atk is not None:
            it.atk = atk
            dealt = min(max(hp[atk], 0), S)
            hp[atk] -= S
            if kit.splash:                                        # Strength onto every row within 1 [rules]
                for j in range(n):
                    if j != atk and hp[j] > 0 and max(abs(xs[atk] - xs[j]), abs(ys[atk] - ys[j])) <= 1:
                        dealt += min(hp[j], S)
                        hp[j] -= S
            it.dmg += dealt
            it.needs_stand = kit.ranged
        v, s_, tgt, area, why = c
        if s_ is None:
            it.idle = sorted(why.items())
        else:
            sl = kit.slots[s_]
            it.val = v
            if land is not None:
                it.cast, it.land, it.pre = (s_, land), land, True
            elif sl.kind == K_RESET:
                it.cast = (s_, None)
                if tgt is not None:
                    it.atk2 = tgt
                    it.dmg += min(max(hp[tgt], 0), S)
                    hp[tgt] -= S
            elif sl.kind in (K_SHIELD, K_HEAL):
                it.cast = (s_, None)
            elif area:
                it.cast = (s_, (xs[tgt], ys[tgt]))
                d, r = sl.mod * F, sl.radius
                for j in range(n):
                    if hp[j] > 0 and max(abs(xs[tgt] - xs[j]), abs(ys[tgt] - ys[j])) <= r:
                        it.dmg += min(hp[j], d)
                        hp[j] -= d
            else:
                it.cast = (s_, tgt)
                if tgt is not None:
                    it.dmg += min(max(hp[tgt], 0), sl.mod * F)
                    hp[tgt] -= sl.mod * F
            it.needs_stand = it.needs_stand or sl.excl
        it.hp = hp
        return it


    # ---------------------------------------------------------------- act: the only attack / cast site
    HIT = [-1, []]      # [round, groups hit this round] (hit= on the t line, I17)
    _IDLE = {}          # slot -> last idle why logged (log on change: ~1 MB stdout cap)

    def kit_hit(rnd):
        """Groups hit this round, "g7,g9" or "-" (the t line's hit=)."""
        return ",".join(HIT[1]) if HIT[0] == rnd and HIT[1] else "-"

    def _mark(rnd, tag):
        if HIT[0] != rnd:
            HIT[0], HIT[1] = rnd, []
        if tag[0] == "g" and tag not in HIT[1]:
            HIT[1].append(tag)

    def _splash(w, own, x, y, r, by, rnd):
        """Log every other group within r of an area effect's centre (I17's allowed wake)."""
        for g in {f"g{h}" for _, h in w.near(V(x, y), r)} - {own}:
            trace("splash", f"g={g} by={by}")
            _mark(rnd, g)

    def act(it, w):
        """Execute an Intent. Returns the t-line act tokens ("at", "cs", "at" again after a reset).
        I14: an excl cast is dropped when Nav already moved this round, and after an excl cast or a
        ranged attack the snapshot's walk is spent (s.can_move = False), so Nav refuses to move. w (the
        World) is required. it.pre: the cast goes first (a dash in, then the attack from the landing). A dash
        adds the token "dash" ("cs dash") and, for a ground landing (x, y), sets Nav's moved_round / dest to
        it. it.move_to is NOT made here: the task walks with Nav before calling act()."""
        kit, tg = it.kit, it.tg
        me = kit.me
        s = w.snap
        rnd = s.rnd
        nav = getattr(w, "nav", None)
        moved = nav is not None and nav.moved_round == rnd
        toks = []

        def attack(i):
            t = tg[i]
            try:
                me.attack(t[4])
            except Exception as e:
                trace("kit", f"atk_fail tgt={t[5]} {err_text(e)}")
                return
            toks.append("at")
            _mark(rnd, t[5])
            if kit.ranged:
                s.can_move = False
            if kit.splash:
                _splash(w, t[5], t[2], t[3], 1, "passive", rnd)

        def cast():
            s_, tgt = it.cast
            sl = kit.slots[s_]
            if tgt is None:
                ref, txt = None, "self"
            elif isinstance(tgt, tuple):
                ref, txt = V(tgt[0], tgt[1]), f"{tgt[0]},{tgt[1]}"
            else:
                ref, txt = tg[tgt][4], tg[tgt][5]
            ok = False
            if sl.excl and moved:
                it.idle = it.idle + [(s_, "excl_walk_flee")]
            else:
                try:
                    ok = me.abilities()[s_].use(ref)
                except Exception as e:
                    trace("kit", f"cast_fail slot={s_} {err_text(e)}")
            if ok:
                toks.append("cs")
                trace("cast", f"slot={s_} kind={KIND_NAME[sl.kind]} tgt={txt} val={int(min(it.val, FAR))}")
                _IDLE.clear()
                kit.cd_r = -1
                if sl.excl:
                    s.can_move = False
                if sl.kind == K_DASH:
                    toks.append("dash")                  # I14: the t line's displacement allowance (2)
                    if nav is not None and isinstance(tgt, tuple):
                        nav.moved_round, nav.dest = rnd, ref     # the t line's position; no walk after it
                elif isinstance(tgt, tuple):
                    own = tg[0][5]
                    _mark(rnd, own)
                    _splash(w, own, tgt[0], tgt[1], sl.radius, f"slot{s_}", rnd)
                elif tgt is not None:
                    _mark(rnd, txt)
                if it.atk2 is not None:
                    attack(it.atk2)
            else:
                it.cast = None

        if it.pre and it.cast is not None:               # dash in, then attack from the landing [measured A46]
            cast()
            if it.atk is not None and not (kit.ranged and moved):
                attack(it.atk)
        else:
            if it.atk is not None and not (kit.ranged and moved):
                attack(it.atk)
            if it.cast is not None:
                cast()
        for s_, why in it.idle:
            if _IDLE.get(s_) != why:
                _IDLE[s_] = why
                trace("cast", f"idle slot={s_} why={why}")
        return " ".join(toks)

    # ---------------------------------------------------------------- predictors (event-based)
    def quick_clear(kit, comp, dpr=None):
        """Pessimistic O(n): basic attacks only (or a given dpr), weakest first, every monster hitting
        starting the round after our first hit until it dies [measured A1, A3]. comp rows start (hp, str)."""
        S = dpr or kit.S
        r, taken = 0, 0.0
        for m in sorted(comp):
            r += int(-(-m[0] // S))
            taken += m[1] * (r - 1)
        return (r, taken, 0) if r <= SIM_CAP else HOPELESS

    _NEAR = {}

    def _sim(S, splash, rok, casters, mons, cds, cap=FAR, walk_in=False):
        """plan_turn's policy, one loop per cast or kill, no inner calls (~200 fuel per bytecode
        [measured]) [LESSONS §4]. casters: (Slot, Focus, owner S). Monster i hits rounds 2..dead_i
        [measured A1]; a stun on a live monster skips its next hit; a shield soaks what lands in its
        duration [measured S3]. Hopeless once the damage landed passes cap (we would be dead). walk_in:
        a melee walks in and attacks on round 1, so a cast that excludes walking waits for round 2.
        Returns (rounds, damage taken, casts)."""
        n = len(mons)
        hp = [m[0] for m in mons]
        sv = [m[1] for m in mons]
        cs, nxt = [], []
        for sl, F, so in casters:
            k = sl.kind
            if k in (K_RESET, K_SHIELD, K_AOE) or (k in (K_DMG, K_CC) and (sl.camps or sl.ground)):
                cs.append((k, so if k == K_RESET else sl.mod * F, sl.stun, sl.dur))
                nxt.append(max(2, cds[sl.i] + 1) if k == K_SHIELD or walk_in and sl.excl else cds[sl.i] + 1)
        splash = splash and n > 1
        crowd = splash or n > 1 and any(c[0] == K_AOE for c in cs)
        near = None
        if crowd:                            # neighbours within 1, cached per group shape
            shape = tuple((m[2], m[3]) for m in mons)
            near = _NEAR.get(shape)
            if near is None:
                near = _NEAR[shape] = [[j for j in range(n) if j != i and -2 < a[0] - shape[j][0] < 2
                                        and -2 < a[1] - shape[j][1] < 2] for i, a in enumerate(shape)]
        dead = [0] * n
        ncnt = [len(x) for x in near] if crowd else None
        alive = list(range(n))
        wide = alive
        saved = soak = landed = 0.0
        inc = sum(sv)
        shields = []
        r = casts = 0
        dirty = crowd
        while alive:
            if dirty:                            # after kills: alive ordered edge first (min() keeps the
                alive.sort(key=ncnt.__getitem__)     # first of equal HP), wide = the most crowded
                m = ncnt[alive[-1]]
                wide = [i for i in alive if ncnt[i] == m]
                dirty = False
            if r > SIM_CAP or landed - saved - soak > cap:
                return HOPELESS
            # plan_turn's target: weakest, edge first (Varg: widest splash, then weakest)
            p = min(wide if splash else alive, key=hp.__getitem__)
            t_ev = min(nxt) if nxt else FAR
            kl = 0
            if t_ev > r:                         # basic attacks until the next cast or kill
                e = r + int(-(-hp[p] // S))
                if e > t_ev:
                    e = t_ev
                landed += inc * (e - (r or 1))
                k = (e - r) * S
                for j in (near[p] + [p] if splash else (p,)):
                    if not dead[j]:
                        h = hp[j]
                        hp[j] = h - k
                        if hp[j] <= 0:
                            dead[j] = r + max(1, int(-(-h // S)))
                            alive.remove(j)
                            inc -= sv[j]
                            kl += 1
                            if crowd:
                                for i in near[j]:
                                    ncnt[i] -= 1
                r = e
                if kl:
                    dirty = crowd
                    if rok:                      # Vendetta: a kill resets every cooldown [rules]
                        nxt = [r] * len(nxt)     # (no cast yet this round: the reset fires now)
                continue
            bi, bv = -1, 0.0                     # the due slot worth the most now; the others wait
            c = (p if p in wide else wide[0]) if crowd else p    # area centre: the most crowded
            for ci in range(len(cs)):
                if nxt[ci] > r:
                    continue
                kd, d, stun, dur = cs[ci]
                if kd == K_RESET:
                    v = d + (sv[p] if stun else 0)
                elif kd == K_SHIELD:
                    v = min(d, inc * dur)
                elif kd == K_AOE and crowd:
                    v = sum([min(hp[j], d) + (sv[j] if stun else 0) for j in near[c] + [c] if not dead[j]])
                else:
                    v = min(hp[p], d) + (sv[p] if stun else 0)
                if v > bv:
                    bi, bv = ci, v
            for ci in range(len(cs)):
                if nxt[ci] <= r and ci != bi:
                    nxt[ci] = r + 1 if cs[ci][0] != K_SHIELD or inc > 0 else FAR
            if bi < 0:
                continue
            kd, d, stun, dur = cs[bi]
            casts += 1
            nxt[bi] = r + COOLDOWN
            if kd == K_SHIELD:
                shields.append((r, d, dur))
                soak += min(d, inc * dur)
                continue
            hits = near[c] + [c] if kd == K_AOE and crowd else near[p] + [p] if kd == K_RESET and splash else (p,)
            for j in hits:
                if not dead[j]:
                    hp[j] -= d
                    if hp[j] <= 0:
                        dead[j] = r
                        alive.remove(j)
                        inc -= sv[j]
                        kl += 1
                        if crowd:
                            for i in near[j]:
                                ncnt[i] -= 1
                    elif stun and (kd != K_RESET or j == p):
                        saved += sv[j]
            if kl:
                dirty = crowd
                if rok:
                    nxt = [r + 1] * len(nxt)
        taken = sum([sv[i] * (dead[i] - 1) for i in range(n)]) - saved
        for t0, amount, dur in shields:
            taken -= min(amount, sum([sv[i] * max(0, min(dead[i], t0 + dur) - t0) for i in range(n)]))
        return int(max(dead)), max(0.0, taken), casts

    _PRED = {}
    SIM_FUEL = [0]      # fuel of the last uncached predict (the clear line's sim=)

    def _key(kit, mons, cds):
        x0, y0 = mons[0][2], mons[0][3]
        return (kit.ctype, kit.S, kit.F, kit.max_hp, tuple(cds),
                tuple((m[0], m[1], m[2] - x0, m[3] - y0) for m in mons))

    def predict_clear(kit, mons, cds=(0, 0), force=False, walk_in=None):
        """(rounds, damage taken, casts) of a solo clear (a melee walks in on round 1), memoised by
        (champion type, S, F, max HP, cooldowns, composition). mons rows start (hp, str, x, y).
        HOPELESS when quick_clear says so or the damage would pass max HP; None when uncached and
        fuel is short (unless force): the caller falls back to quick_clear. walk_in (default: melee)
        = round 1 starts with a walk, so no cast that excludes walking that round; pass
        nav.moved_round == rnd at the gate."""
        if not mons:
            return (0, 0.0, 0)
        if walk_in is None:
            walk_in = not kit.ranged
        key = _key(kit, mons, cds) + (walk_in,)
        p = _PRED.get(key)
        if p is not None:
            return p
        if quick_clear(kit, mons) is HOPELESS:
            p = HOPELESS
        elif not force and fuel() - RESERVE < EV_COST * (len(mons) + 1 + len(kit.slots) * quick_clear(
                kit, mons, kit.S * (len(mons) if kit.splash else 1))[0] // COOLDOWN):
            return None
        else:
            f0 = fuel()
            p = _sim(kit.S, kit.splash, kit.reset_on_kill, [(sl, kit.F, kit.S) for sl in kit.slots], mons, cds,
                     kit.max_hp, walk_in)
            SIM_FUEL[0] = f0 - fuel()
            if SIM_FUEL[0] > 600_000:
                trace("kit", f"simcost {SIM_FUEL[0]} n={len(mons)} -> {p[0]}/{int(p[1])}")
        _PRED[key] = p
        return p

    def predict_pair(tank, other, mons):
        """Two champions on one group: summed Strength, both kits' casts serialised one per round
        (pessimistic), every monster hit on the tank (the nearest champion [rules, measured A2]); no
        splash or kill-reset credit. (rounds, damage on the tank, casts)."""
        if not mons:
            return (0, 0.0, 0)
        key = ("pair", other.ctype) + _key(tank, mons, (0, 0))
        p = _PRED.get(key)
        if p is None:
            cs = [(sl, tank.F, tank.S) for sl in tank.slots] + [(sl, other.F, other.S) for sl in other.slots]
            p = _PRED[key] = _sim(tank.S + other.S, False, False, cs, mons, (0,) * 4, tank.max_hp)
        return p

    def ttk(dpr, hp):
        return FAR if dpr <= 0 else -(-hp // dpr)

    def ttd(hp, shield, inc):
        """floor((hp + shield) / inc) rounds; FAR when nothing hits us (INVARIANTS §0)."""
        return FAR if inc <= 0 else int((hp + shield) // inc)

    def solo_ok(kit, mons, keep_hp, hp=None, cds=(0, 0), force=False):
        """I3 camp gate: predicted damage x SOLO_SAFETY < hp - keep_hp x max_hp (keep_hp a fraction,
        card field [provisional A43]). Exact predictor when cached or affordable, else quick_clear.
        Returns (ok, (rounds, damage, casts))."""
        p = predict_clear(kit, mons, cds, force) or quick_clear(kit, mons)
        hp = kit.max_hp if hp is None else hp
        return p[0] < FAR and p[1] * SOLO_SAFETY < hp - keep_hp * kit.max_hp, p

    class Duel:
        """The duel gate's verdict. ok; ttk_them (our rounds to kill everything in the fight) and ttk_us (their
        rounds to kill us); value (STRATEGY.md fight value, gems); pred_dmg (HP we lose, net of our shields,
        before the last of them dies); burst (their first turn on us); seq (predicted damage on us in turns 1, 2, 3); n
        (enemies counted); why (ok | outnumbered | ratio | value | keep)."""
        __slots__ = ("ok", "ttk_them", "ttk_us", "value", "pred_dmg", "burst", "seq", "n", "why")

        def __init__(self, ok, a, b, v, pred=0.0, burst=0.0, seq=(), n=1, why="-"):
            self.ok, self.ttk_them, self.ttk_us, self.value = ok, a, b, v
            self.pred_dmg, self.burst, self.seq, self.n, self.why = pred, burst, seq, n, why

        def text(self):
            """The fields every fight log carries (fight|start extras, duel lines)."""
            return (f"ttk={self.ttk_them}/{self.ttk_us} pred_dmg={int(self.pred_dmg)} burst={int(self.burst)} "
                    f"seq={'/'.join(str(int(x)) for x in self.seq)} n={self.n} val={self.value:.1f} why={self.why}")

    # Cast schedules in closed form: slot i fires at t_i, t_i + 8, ... (its cooldown [rules]); when two slots
    # are ready in the same round the more valuable fires first and the other a round later (one cast per
    # turn [rules]). A cast fired in round t (0-based) has landed by the end of round t + 1.
    _DUEL = {}         # memo: one verdict per (round, both sides' state): the gate is asked by several layers
    _PC = {}           # cast list -> schedule

    # Cast schedules in closed form: slot i fires at t_i, t_i + 8, ... (its cooldown [rules]); when two slots
    # are ready in the same round the more valuable fires first and the other a round later (one cast per
    # turn [rules]). A cast fired in round t (0-based) has landed by the end of round t + 1.
    def _plan_casts(cs):
        """cs = ((value, ready-in, stun), ...) -> ((t0, value, stun), ...), memoised."""
        r = _PC.get(cs)
        if r is None:
            out, used = [], []
            for v, rd, s_ in sorted(cs, reverse=True):
                t = rd
                while t in used:
                    t += 1
                used.append(t)
                out.append((t, v, s_))
            r = _PC[cs] = tuple(out)
        return r

    def _ttk_seq(H, S, sc, rate):
        """Rounds until S per round plus the casts sc ((t0, value, stun), ...) total H; rate = S + sum value / 8
        (the start guess; casts are front-loaded, so 1-3 evaluations). FAR when nothing hurts."""
        if H <= 0:
            return 0
        if rate <= 0:
            return FAR
        off = 0.0
        for t0, v, _ in sc:
            off += v * (0.5 - t0 / COOLDOWN)            # ceil(x / 8) ~ x / 8 + 1/2: the front-loading
        n = int(-(-(H - off) // rate))
        if n < 1:
            n = 1
        up = None
        while True:
            d = n * S
            for t0, v, _ in sc:
                if n > t0:
                    d += v * ((n - t0 - 1) // COOLDOWN + 1)
            if d >= H:
                if up or n <= 1:
                    return n
                up = False
                n -= 1
            else:
                if up is False:
                    return n + 1
                up = True
                n += 1

    def duel(us, snap_me, ems, allies_dpr=0.0, n_allies=0, shield=0.0, keep=0.0, cds=None, first=False,
             still=0, bag=None):
        """The one duel model (I3), burst first then sustained. ems: UnitModels in the fight, the target first.
        Ours: Strength + allies' dpr every round plus our ready casts on their cooldowns; theirs: each enemy's
        Strength (+ Ren's retaliation per our hit) plus its casts (read cooldowns, else every slot ready). We
        kill them one at a time, quickest first; each deals damage until it dies. Our stuns remove the target's
        rounds; theirs cost us rounds (none on a stun-immune side). still = rounds the target channels (P15).
        first = we strike before they act (in reach now). bag = gems a kill yields (default: their bags).
        Gate: ttk_them x TTK_RATIO <= ttk_us, fight value > 0, pred_dmg x SOLO_SAFETY < hp - keep (pred_dmg net
        of our current and castable shield),
        and at most 1 + n_allies enemies (outnumbered -> no) [provisional A44, A43]."""
        rnd = snap_me.rnd
        key = (rnd, id(us), snap_me.hp, tuple([(id(m), m.hp_eff, m.bag) for m in ems]), allies_dpr, n_allies,
               shield, keep, first, still, bag, cds)
        r = _DUEL.get(key)
        if r is not None and r[0] is ems[0]:
            return r[1]
        if len(_DUEL) > 64:
            _DUEL.clear()
        ucds = cds if cds is not None else (us.cds(rnd) if us.me is not None else (0,) * len(us.slots))
        cs, sh = [], 0.0
        for sl in us.slots:
            k = sl.kind
            rdy = ucds[sl.i] if sl.i < len(ucds) else 0
            if k in (K_DMG, K_CC, K_AOE) and (sl.enemies or sl.ground):
                cs.append((sl.mod * us.F, rdy, sl.stun))
            elif k == K_RESET:
                cs.append((us.S, rdy, sl.enhanced))
            elif k == K_SHIELD and sl.self_ and not rdy:
                sh = sl.mod * us.F
        sc_us = _plan_casts(tuple(cs))
        S_us = us.S + allies_dpr
        rate_us = S_us + sum([c[1] for c in sc_us]) / COOLDOWN
        hp_us = snap_me.hp + shield + sh
        ne = len(ems)
        if ne == 1:
            order = [(_ttk_seq(ems[0].hp_eff + ems[0].shield_rdy, S_us, sc_us, rate_us), 0)]
        else:
            order = sorted([(_ttk_seq(m.hp_eff + m.shield_rdy, S_us, sc_us, rate_us), i) for i, m in enumerate(ems)])
        pred = s1 = s2 = s3 = theirS = rate = 0.0
        t_all = stun_them = 0
        allc = []
        for k, i in order:
            m = ems[i]
            t_all += k
            Sm = m.S + (RETALIATE * m.F if m.retaliate else 0.0)
            sc = _plan_casts(m.casts)                            # ready-in = its read cooldowns, else 0
            nh = t_all - (1 if first else 0)                     # it acts until it dies (one fewer if we lead)
            d = (nh if nh > 0 else 0) * Sm
            s1 += Sm
            s2 += Sm
            s3 += Sm
            for t0, v, st_ in sc:
                if nh > t0:
                    c = (nh - t0 - 1) // COOLDOWN + 1
                    d += v * c
                    if st_ and not us.stun_immune:
                        stun_them += c
                if t0 == 0:
                    s1 += v
                elif t0 == 1:
                    s2 += v
                elif t0 == 2:
                    s3 += v
                rate += v / COOLDOWN
                allc.append((t0, v, st_))
            pred += d
            theirS += Sm
        m0 = ems[0]
        if not m0.stun_immune:                                   # our stuns skip the target's rounds
            ns_ = 0
            for t0, _, st_ in sc_us:
                if st_ and t_all > t0:
                    ns_ += (t_all - t0 - 1) // COOLDOWN + 1
            if ns_:
                pred = max(0.0, pred - ns_ * (m0.S + (RETALIATE * m0.F if m0.retaliate else 0.0)))
        if stun_them:                                            # their stuns: rounds we stand still under fire
            t_all += stun_them
            pred += stun_them * theirS
        if still and ne == 1:
            pred = max(0.0, pred - min(still, t_all) * theirS)
        ttk_us = _ttk_seq(hp_us, theirS, allc, theirS + rate)   # every enemy alive throughout (pessimistic)
        if ttk_us < FAR and still and ne == 1:
            ttk_us += still                                      # a channelling target can't hit back
        b = bag if bag is not None else sum([m.bag for m in ems])
        ratio = t_all * TTK_RATIO <= ttk_us
        p = P_WIN if ratio else 1 - P_WIN
        v = p * (b + (KILL_GOLD * GOLD_GEM + RESPAWN * INCOME) * ne) - (1 - p) * (snap_me.bag + RESPAWN * INCOME) \
            - min(t_all, RESPAWN) * INCOME
        pred = max(0.0, pred - shield - sh)                      # HP we lose: our shields soak first (I3's hp line)
        keep_ok = pred * SOLO_SAFETY < snap_me.hp - keep
        why = "outnumbered" if ne > 1 + n_allies else ("ratio" if not ratio else ("value" if v <= 0 else
                                                                                 ("keep" if not keep_ok else "ok")))
        r = Duel(why == "ok", t_all, ttk_us, v, pred, s1, (s1, s2, s3), ne, why)
        _DUEL[key] = (ems[0], r)
        return r

    def duel_gate(us, snap_me, them, their_hp, allies_dpr=0.0, their_bag=0, shield=0.0, their_shield=0.0,
                  others=(), n_allies=None, keep=0.0, first=False, still=0, cds=None):
        """I3 champion gate (the one duel model, see duel()): them = a UnitModel (enemy_model, live: preferred)
        or a Kit (design / live: kit_model, every slot ready, HP their_hp + their_shield). others = UnitModels of
        further enemies in the fight (within R1 of it); n_allies = allies in reach (default: 1 if allies_dpr).
        keep = the HP floor the fight must leave (keep_hp x max_hp). Returns a Duel (.ok, .ttk_them, .ttk_us,
        .value, .pred_dmg, .burst, .seq, .why)."""
        if isinstance(them, UnitModel):
            em = them
        else:
            em = kit_model(them, their_hp, their_bag, their_shield)
        ems = [em] + [m for m in others if m is not em]
        na = n_allies if n_allies is not None else (1 if allies_dpr > 0 else 0)
        bag = their_bag if their_bag else None
        return duel(us, snap_me, ems, allies_dpr, na, shield, keep, cds, first, still, bag)

    # ---------------------------------------------------------------- the fight record (trace + accuracy)
    FIGHT = [None]      # the open Fight of this champion

    class Fight:
        """One fight: fight|start before the first hit, fight|end and (camps) the clear line after.
        clear: <h> kind= pred= took= dpred= dmg= casts= idle=a/b allies= <done|died|abort> sim= (scenario.py).
        idle counts fight turns where a ready slot with value waited for the walk.
        Champion fights (vs=c<id>): extra (Duel.text()) is appended to fight|start; fight|end adds dealt= (HP the
        enemy rows lost between our turns, observed: ours plus allies') and pdealt= (what our plans expected),
        and turn1= (HP we lost by our second fight turn: the burst check against the start's burst=)."""

        def __init__(self, vs, pred, hp, keep, kinds="", ttk_="-", enemies=0, extra=""):
            self.vs, self.pred, self.hp0, self.keep, self.kinds = vs, pred, hp, keep, kinds
            self.extra = extra
            self.chp = {}
            self.dealt = self.pdealt = 0.0
            self.turn1 = None
            self.ttk, self.enemies = ttk_, enemies
            self.r0 = self.killed = None
            self.turns = self.idle = self.casts = 0
            self.shared = False
            self.expect = None
            self.sim = SIM_FUEL[0]

        def start(self, rnd):
            self.r0 = rnd
            FIGHT[0] = self
            trace("fight", f"start vs={self.vs} pred_r={self.pred[0]} pred_dmg={int(self.pred[1])} hp={int(self.hp0)} "
                           f"keep={int(self.keep)} ttk={self.ttk} enemies={self.enemies}" + (f" {self.extra}" if self.extra else ""))

        def seen(self, tg):
            """HP below what our own action left: someone else is hitting this group (allies=1)."""
            if self.expect is not None:
                for t in tg:
                    e = self.expect.get((t[2], t[3]))
                    if e is not None and t[0] < e - 0.5:
                        self.shared = True
            self.expect = {}

        def turn(self, it, rnd, hp=None):
            self.turns += 1
            if self.turns == 2 and hp is not None:
                self.turn1 = self.hp0 - hp
            self.pdealt += it.dmg
            for t in it.tg:
                if t[5][0] == "c":
                    o = self.chp.get(t[5])
                    if o is not None and t[0] < o:
                        self.dealt += o - t[0]
            for t, h in zip(it.tg, it.hp):
                if t[5][0] == "c":
                    self.chp[t[5]] = t[0]
            self.casts += it.cast is not None
            self.idle += it.cast is None and any(w not in ("no_target", "no_value") for _, w in it.idle)
            self.expect = {(t[2], t[3]): h for t, h in zip(it.tg, it.hp)}
            if all(h <= 0 for h in it.hp):
                self.killed = rnd

        def end(self, rnd, hp, res, why="-"):
            FIGHT[0] = None
            if self.r0 is None:
                return
            if res == "abort" and self.killed is not None:
                res, why = "done", f"cleared_{why}"      # our last action killed the group (an interrupt ended it)
            killed = self.killed if self.killed is not None else rnd - 1
            took = killed - self.r0 + 1
            dmg = int(self.hp0 - hp)
            ex = ""
            if self.vs[0] == "c":
                if res == "done":
                    self.dealt += sum(self.chp.values()) if len(self.chp) == 1 else 0   # the killing blow, unseen
                ex = f" dealt={int(self.dealt)} pdealt={int(self.pdealt)} turn1={'-' if self.turn1 is None else int(self.turn1)}"
            trace("fight", f"end {'win' if res == 'done' else res} vs={self.vs} r={took} dmg={dmg} why={why}{ex}")
            if self.vs[0] == "g":
                p = self.pred
                trace("clear", f"{self.vs[1:]} kind={self.kinds} pred={p[0]} took={took} dpred={int(p[1])} dmg={dmg} "
                               f"casts={self.casts} idle={self.idle}/{self.turns} allies={int(self.shared)} {res} "
                               f"sim={self.sim}")
