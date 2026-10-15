# tzu: lazy
"""L4 tasks (ROLES_AND_LAYERS.md §3 L4): state machines that emit intents; they never decide WHICH task.

Interface for the driver (L5):
    t = ClearCamp(h) | Capture(h) | Bank(i) | GoHome(why) | Flee(threat) | Shop()
        (ClearLock(i) and Deny(enemy): 66_deny.py; Hold(tile) and Hunt(enemy): 65_hunt.py; GroupTake: 67_group.py)
    t.start(w, s)            once, the turn the task is picked (logs task|<Name> start g=<key>)
    t.step(w, s) -> status   once per turn: 'run' | 'ok' | 'fail' | 'abort'; at most one move (Nav), one
                             attack/cast (act), one channel/shop call. After it, t.act is the t-line act.
    t.abort(w, s, why)       an interrupt pre-empts it (logs the end line; cancels nothing by itself)
    t.key                    goal key for tgt= ; t.fight / t.hit for the t line (group id or '-')
    t.then                   ClearCamp only: the running Capture to adopt when ClearCamp ends ok
Nav is read from w.nav (the driver sets w.nav = nav once). Status words are the ones tools/scenario.py
reads; the end line is task|<Name> <ok|fail|abort> why=.. g=.. r=.. cap=.. trib=.. carry=..
Helpers for interrupts: card(w, k), sense(w, s), inc_at(w, s, p), ttd_of(w, s, inc), sts(w, s), flee_cond(w, s),
recall_safe(w, s), shop_turn(w, s).
Group ids are g<int(group)> in every line (cap g=, fight vs= via L3's Fight, task g=, hit=); Nav keys stay ints.
Bank(i)/ClearLock(i): i = altar index of World.altar_pos (the plan's index when plan_ok); None or 255 = the
"altar" goal (nearest), the altar then resolved by position. Kit (50_kit.py) is optional: without it the
fighting tasks end fail why=no_kit. The whole part is skipped by the draft bot (import fuel).
"""

if not cambc.is_draft():     # the draft bot never runs tasks: skip ~1-2M of definitions on its first turn
    R1 = 5                 # enemy reach next turn [measured A46]; global constant, provisional as a tuning choice
    RECALL_WALK = 5        # walk home instead of recalling when spawn_d <= this (I16 forbids recall at <= 5) [provisional]
    R_RECALL = 10          # I1: no enemy within R1 + recall ticks [rules arithmetic]
    CAMP_SAFE = 5          # I1: no camp tile within 5 of a recall start [INVARIANTS I1]
    SAFE_MAX = 8           # sts search depth; beyond it sts = SAFE_MAX + 1
    FLEE_OK = 3            # Flee ends ok after this many rounds without the flee condition [ROLES L4]
    SIDESTEP_MAX = 12      # GoHome with a bag: rounds it may side-step a fresh enemy between it and spawn [provisional]
    CAP_GRACE = 3          # rounds past CAPTURE_TIME before a stalled capture is given up
    ENEMY_DPR_X = 2        # enemy damage next turn ~ 2x Strength (attack + a spell) when the kit can't say [provisional]
    PRED_SLACK = 600_000  # fuel kept for the rest of the turn after an uncached predict [measured: 2.3-2.4M turns at 400k]
    GATE_X = 1.1           # predicted camp damage x1.1 must leave keep_hp [provisional A43, INVARIANTS I3]
    MONO = 4               # CampType MONOLITH; range treated as 5 for safety [INVARIANTS §5]
    RING_MAX = 10          # rounds a fight may walk its target camp's own ring "c<x>_<y>" before it ends why=unreach
                           # (the group then rests 70_decide COOL["unreach"]) [provisional]
    CARD_DEF = dict(bank_at=40, bank_at_threat=20, recall_hp=35, keep_hp=15, flee_margin=2, carry_lock=False, role=0,
                    home_altar=255)
    IT = cambc.ItemType
    SHOP_PLAN = {0: (IT.MONSTER_SHARD_OF_STRENGTH,), 1: (IT.DURABILITY_SHARD_OF_HEALTH,),     # ROLES §1.2 shop_plan,
                 2: (IT.BRUISER_SHARD_OF_HEALTH, IT.BRUISER_SHARD_OF_STRENGTH), 3: (IT.MONSTER_SHARD_OF_STRENGTH,)}
    LOCK = cambc.ConsumableType.ALTAR_LOCK
    HEAL_FIRST = 0.6       # shop_turn: Health first on spawn below this HP fraction [rules: it heals what it adds]

    _M = {"id": None}      # per-turn memo (danger mask, walls, inc)
    _S = {"hp": None, "seen": [], "card": False, "kinds": {}, "spt": {}, "stun": {}}


    def _ev(tag, text):
        e = globals().get("EVENTS")
        if e is None:
            trace(tag, text)
        else:
            e.append((tag, text))


    def card(w, k):
        """Card field k (role card of my slot, else the no-plan Farmer defaults); HP fields as fractions."""
        c = _S["card"]
        if c is False:
            c = _S["card"] = w.plan.card_for(w.ctype) if w.plan_ok else None
        v = getattr(c, k, None) if c is not None else None
        if v is None:
            v = CARD_DEF[k]
        return v / 100 if k in ("recall_hp", "keep_hp") else v


    def kinds(w, h):
        """((spawn tile, CampType int), ...) of group h, cached."""
        r = _S["kinds"].get(h)
        if r is None:
            r = _S["kinds"][h] = tuple((c.spawn_position(), int(c.kind())) for c in w.camps[h])
        return r


    def spawn_tiles(w, h):
        b = _S["spt"].get(h)
        if b is None:
            b = _S["spt"][h] = w.groups[h].spawn_tiles()
        return b


    def live(w, s, h):
        """[(Camp, hp)] of group h alive and visible this turn (needs h in the snapshot's camp rows)."""
        row = s.camp_hp.get(h) or ()
        return [(c, hp) for c, hp in zip(w.camps[h], row) if hp is not None and hp > 0]


    def gid(k):
        """Group ids as g<id> in every line (cap g=, fight vs=, hit=, task g=); other keys as they are."""
        return f"g{k}" if isinstance(k, int) else k


    def memo(s):
        if _M["id"] is not s:
            _M.clear()
            _M["id"] = s
        return _M


    # ---------------------------------------------------------------- sensing extras and danger
    def sense(w, s):
        """Once per turn: the enemy sighting log (I1, 10 rounds) and the 'hit with no enemy in reach' awake
        inference of INVARIANTS §0 (the SDK has no awake flag)."""
        m = memo(s)
        if "sensed" in m:
            return
        m["sensed"] = True
        if not s.alive:
            _S["hp"] = None
            return
        seen = _S["seen"]
        for e in s.enemies:
            seen.append((s.rnd, e[0]))
        while seen and seen[0][0] < s.rnd - 10:
            seen.pop(0)
        old, _S["hp"] = _S["hp"], s.hp
        if old is not None and s.hp < old and not any(e[0].chebyshev_distance(s.pos) <= R1 for e in s.enemies) \
                and inc_at(w, s, s.pos) == 0:
            for t, h in s.near_t:
                if t.chebyshev_distance(s.pos) <= 5:
                    w.awake_until[h] = s.rnd + 2        # [measured A32]
                    s.awake.add(h)
                    m.pop("D", None)
                    m.pop(("inc", s.pos.x, s.pos.y), None)


    def enemy_dpr(c, bag=0, live=False):
        """What a visible enemy can deal next turn: L3's burst (attack + best spell), else 2x Strength.
        live=True: the larger of the two (levels and shards grow Strength past the design kit; Bank's channel
        check, where the design kit alone let a Vendetta start a 5-tick tribute next to a grown starter
        champion and die, s2d collision r1051)."""
        em = globals().get("enemy_model")
        if em is not None:                             # 50_kit: the live model (shards, cooldowns) of the one enemy model
            try:
                return em(c).burst()
            except Exception:
                pass
        b = 0.0
        try:
            b = kit_of(int(c.champion_name())).burst(bag)
            if not live:
                return b
        except Exception:
            pass
        try:
            return max(b, c.strength() * ENEMY_DPR_X)
        except Exception:
            return b or 100


    def foes_acting(s):
        """s.enemies minus those channelling a tribute or a recall this round: a channeller cannot hit without
        cancelling first [rules: a channel is an action that ends only on completion, cancel, stun or death;
        PROVISIONAL that cancel + attack in one turn is impossible]. So inc (and flee_cond) ignores it and the
        STRIKE reflex can fire on it at the altar. Toggle INT_ON["FLEE_GATE"] (70_decide, read at call time).
        One state() read per visible enemy (~3-5k), memoised per snapshot."""
        if not s.enemies or not globals().get("INT_ON", {}).get("FLEE_GATE", True):
            return s.enemies
        m = memo(s)
        r = m.get("acting")
        if r is None:
            r = []
            for e in s.enemies:
                try:
                    ch = int(e[3].state()) & (ST_SUBMITTING | ST_RECALLING)
                except Exception:
                    ch = 0
                if not ch:
                    r.append(e)
            m["acting"] = r
        return r


    def inc_at(w, s, p):
        """Damage that can land on tile p next round: awake monsters with p in range + enemies within R1."""
        m = memo(s)
        key = ("inc", p.x, p.y)
        v = m.get(key)
        if v is not None:
            return v
        inc = 0
        for h in s.awake:
            row = s.camp_hp.get(h)
            if row is None:
                continue
            for (sp, k), hp in zip(kinds(w, h), row):
                if hp and sp.chebyshev_distance(p) <= (5 if k == MONO else CAMP_RANGE):
                    inc += CAMP_STR[k]
        _es = globals().get('enemy_scale')
        _esc = _es(w, s) if _es is not None else 1.0
        ens = foes_acting(s)                           # a channeller can't hit us this round (FLEE_GATE)
        if ens:
            et = globals().get("enemy_threat")
            if et is not None:                         # 50_kit: each enemy's burst at its distance (0 past reach)
                try:
                    inc += et(s, p, ens) * _esc
                    et = True
                except Exception:
                    et = None
            if et is not True:
                for e in ens:
                    if e[0].chebyshev_distance(p) <= R1:
                        inc += enemy_dpr(e[3], e[2]) * _esc
        m[key] = inc
        return inc


    def shield_of(w):
        try:
            b = w.me.buffs()
            return b.get(cambc.BuffShield).value if b.has_shield() else 0
        except Exception:
            return 0


    def ttd_of(w, s, inc):
        if inc <= 0:
            return FAR
        f = globals().get("ttd")
        if f is not None:
            try:
                return f(s.hp, shield_of(w), inc)
            except Exception:
                pass
        return int((s.hp + shield_of(w)) // inc)


    def danger(w, s):
        """Chebyshev danger mask: awake live camps (range 3, monolith 5) and enemies within R1 [INVARIANTS §0]."""
        m = memo(s)
        d = m.get("D")
        if d is None:
            d = Bitboard()
            for h in s.awake:
                row = s.camp_hp.get(h)
                if row is None:
                    continue
                for (sp, k), hp in zip(kinds(w, h), row):
                    if hp:
                        d.draw_chebyshev(sp, 5 if k == MONO else CAMP_RANGE)
            for e in s.enemies:
                d.draw_chebyshev(e[0], R1)
            m["D"] = d
        return d


    def walls(w, s):
        m = memo(s)
        b = m.get("W")
        if b is None:
            base = w.blocked if w.blocked is not None else game_map.walls() | game_map.holes() | game_map.altars()
            b = base | s.occupied()
            b.set(s.pos, False)
            m["W"] = b
        return b


    def sts(w, s, p=None, cap=SAFE_MAX):
        """Steps to safety from p (default: here): reachable tiles (native flood) outside the danger mask."""
        p = p or s.pos
        d = danger(w, s)
        if d.is_empty() or not d.is_set(p):
            return 0
        # One distance field per turn rooted at the safe tiles near us (walking through danger is allowed),
        # read for here and every neighbour: the per-call reachable_tiles floods cost up to 2.15M on one Flee
        # turn (review 13 Oct).
        m = memo(s)
        f = m.get("SF")
        if f is None:
            wl = walls(w, s)
            roots = ~(d | wl) & disk(s.pos, SAFE_MAX + 3)
            f = DistanceField()
            f.compute(wl & ~roots, roots, Bitboard(), SAFE_MAX + 1)
            m["SF"] = f
        v = fget(f, p)
        return v if v <= cap else cap + 1


    def flee_cond(w, s):
        """(holds, inc, ttd, sts): the one flee test ttd <= sts + flee_margin [INVARIANTS §0]. Once per turn;
        sts (the costly part) only when ttd is small enough for it to matter (sts <= SAFE_MAX + 1)."""
        m = memo(s)
        r = m.get("flee")
        if r is not None:
            return r
        sense(w, s)
        inc = inc_at(w, s, s.pos)
        if inc <= 0:
            r = (False, 0, FAR, 0)
        else:
            t = ttd_of(w, s, inc)
            mg = card(w, "flee_margin")
            if t > SAFE_MAX + 2 + mg:
                r = (False, inc, t, -1)     # sts not computed: it can't reach t - margin
            else:
                k = sts(w, s) + (0 if s.can_move else 1)     # stunned: we can't step this round (I2)
                r = (t <= k + mg, inc, t, k)
        m["flee"] = r
        return r


    def flee_step(w, s):
        """Move to a free neighbour outside the danger mask if there is one, else to the neighbour with the
        lowest steps-to-safety (ties: least inc there). True if moved."""
        nav = w.nav
        d = danger(w, s)
        wl = walls(w, s)
        free = []
        for dv in DIRS:
            q = s.pos + dv
            try:
                if not wl.is_set(q):
                    free.append(q)
            except Exception:
                pass
        for q in free:
            if not d.is_set(q) and nav.move(q):
                return True
        here = max(1, sts(w, s))
        ranked = sorted(range(len(free)), key=lambda i: (sts(w, s, free[i], here), inc_at(w, s, free[i])))
        return any(nav.move(free[i]) for i in ranked[:3])


    def step_towards(w, s, goal):
        """One step strictly closer (Chebyshev) to goal on a non-wall tile; camp spawn tiles count as walls,
        so a fight never parks on a spawn tile (I12, LESSONS §3). True if moved."""
        wl = walls(w, s)
        d0 = goal.chebyshev_distance(s.pos)
        for dv in sorted(DIRS, key=lambda v: goal.chebyshev_distance(s.pos + v)):
            q = s.pos + dv
            if goal.chebyshev_distance(q) >= d0:
                break
            try:
                if wl.is_set(q):
                    continue
            except Exception:
                continue
            if w.nav.move(q):
                return True
        return False


    def ring_reach(t, w, s, want):
        """A fight on its group's ring whose target camp is out of reach with no strictly-closer step (camp
        spawn tiles are walls): walk that camp's own melee ring "c<x>_<y>" (World.goal key), at most RING_MAX
        rounds from t.ring_r. False = give up (the caller ends why=unreach)."""
        if t.ring_r is None:
            t.ring_r = s.rnd
        if s.rnd - t.ring_r >= RING_MAX:
            return False
        return t.goto(w, f"c{want[2]}_{want[3]}") not in ("full", "stuck")


    def nearest_d(b, p, rmax):
        """Chebyshev distance from p to the nearest set tile of b within rmax, else None (bitboard tests)."""
        for r in range(rmax + 1):
            if not (disk(p, r) & b).is_empty():
                return r
        return None


    def recall_safe(w, s):
        """I1's recall-safety condition and the recall|start fields (awake, camp, enemy)."""
        sense(w, s)
        p = s.pos
        aw = sum(1 for h in s.awake for (sp, k), hp in zip(kinds(w, h), s.camp_hp.get(h) or ())
                 if hp and sp.chebyshev_distance(p) <= (5 if k == MONO else CAMP_RANGE))
        cd = nearest_d(w.camp_tiles, p, CAMP_SAFE + 1) if w.camp_tiles is not None else None
        ed = min((e[0].chebyshev_distance(p) for e in s.enemies), default=None)
        recent = min((q.chebyshev_distance(p) for r, q in _S["seen"] if r >= s.rnd - 5), default=None)
        tm = getattr(w, "team", None)                    # the team's shared sighting (80_team), cell error added
        sg = tm.sighting if tm is not None else None
        if sg is not None and sg[2] <= 5:
            d = max(0, max(abs(sg[0] - p.x), abs(sg[1] - p.y)) - tm.sight_err)
            recent = d if recent is None else min(recent, d)
        ok = aw == 0 and (cd is None or cd > CAMP_SAFE) and (ed is None or ed > R_RECALL) \
            and (recent is None or recent > R_RECALL) and w.camp_tiles is not None
        return ok, aw, "-" if cd is None else cd, "-" if ed is None else ed


    BANK_FRESH = 3          # Bank walking: an own/team sighting this fresh within R1 + 2 of the altar ends it

    def team_sight(w, s, recent):
        """[(pos, err)] of the team's shared sighting (80_team) if at most `recent` rounds old."""
        tm = getattr(w, "team", None)
        sg = tm.sighting if tm is not None else None
        if sg is None or sg[2] > recent:
            return []
        return [(V(sg[0], sg[1]), tm.sight_err)]

    def fresh_near(w, s, p, r, recent):
        """An own sighting (or visible enemy) or the team sighting at most `recent` rounds old within r of p."""
        if any(e[0].chebyshev_distance(p) <= r for e in s.enemies):
            return True
        if any(q.chebyshev_distance(p) <= r for t, q in _S["seen"] if t >= s.rnd - recent):
            return True
        return any(q.chebyshev_distance(p) <= r + e for q, e in team_sight(w, s, recent))


    def is_stunner(c):
        """Kit test of INVARIANTS §0 via L3's kit_of (Champion.design); unknown -> True (safe side)."""
        try:
            return kit_of(int(c.champion_name())).stunner
        except Exception:
            return True


    # ---------------------------------------------------------------- kit adapter (50_kit.py, L3)
    def my_kit(w):
        """My live Kit (50_kit.py), refreshed once per turn; None when L3 is absent (tasks fail why=no_kit)."""
        k = _S.get("kit")
        if k is None:
            if "Kit" not in globals():
                return None
            k = _S["kit"] = Kit(w.me)
        if _S.get("kit_r") != w.snap.rnd:
            _S["kit_r"] = w.snap.rnd
            k.refresh()
        return k


    def our_lock(w):
        try:
            return w.me.consumables()[int(LOCK)].count() > 0
        except Exception:
            return False


    # ---------------------------------------------------------------- shop (I7)
    def shop_turn(w, s):
        """Housekeeping on every spawn or dead turn: shards per the role's shop_plan while gold >= 30; an altar
        lock first if carry_lock (keep 10 for it). Logs shop|gold= bought= [why=]. Returns 'shop' or None."""
        me = w.me
        if s.alive and not w.spawn.is_set(s.pos):
            return None
        try:
            gold = me.gold_count()
        except Exception:
            return None
        g0, bought, why = gold, [], None
        lock = card(w, "carry_lock") and not our_lock(w)
        if lock and gold >= 40 and me.can_buy(LOCK):
            me.buy(LOCK)
            bought.append("lock")
            gold -= 10
            lock = False
        keep = 10 if lock else 0
        plan = SHOP_PLAN.get(card(w, "role"), SHOP_PLAN[0])
        i = 0
        # Health first on spawn below HEAL_FIRST x max HP: a spawn purchase of Health heals the amount gained
        # [rules]. One shard of the plan's own family (5 matching shards make the emblem [rules]).
        if s.alive and s.hp < HEAL_FIRST * s.max_hp and gold - keep >= 30:
            hk = next((k for k in plan if k.name.endswith("_HEALTH")), None)
            if hk is None:
                hk = getattr(IT, plan[0].name.split("_SHARD_")[0] + "_SHARD_OF_HEALTH", None)
            if hk is not None and me.can_buy(hk):
                me.buy(hk, 1)
                bought.append("hea")
                gold -= 30
                if hk in plan:
                    i = plan.index(hk) + 1                    # keep the plan's rotation (Bruiser: hea, str)
        if len(plan) == 1 and gold - keep >= 30:              # one kind: one buy(kind, n) call, no per-turn cap
            kind = plan[0]                                    # (the old 12-a-turn cap left 180 gold of 570)
            n = (gold - keep) // 30
            if me.can_buy(kind, n):
                me.buy(kind, n)
                bought.extend([kind.name.split("_")[-1][:3].lower()] * n)
                gold -= 30 * n
        while gold - keep >= 30 and i < 40:
            kind = plan[i % len(plan)]
            if not me.can_buy(kind):
                why = "cap_limit"
                break
            me.buy(kind, 1)
            bought.append(kind.name.split("_")[-1][:3].lower())
            gold -= 30
            i += 1
        if not bought and g0 >= 30:
            why = why or ("save_lock" if keep else "cap_limit")
        if bought or g0 >= 30 or s.alive:
            b = ",".join(bought) or "-"
            _ev("shop", f"gold={g0} bought={b}" + (f" why={why}" if why and not bought else ""))
        return "shop" if bought else None


    # ---------------------------------------------------------------- tasks
    class Task:
        name = "Task"

        def __init__(self, key=None):
            self.key = key
            self.status = "run"
            self.why = ""
            self.r0 = 0
            self.bag0 = 0
            self.cap = self.trib = 0
            self.act = "wait why=blocked"
            self.fight = self.hit = "-"
            self.then = None

        def start(self, w, s):
            self.r0, self.bag0 = s.rnd, s.bag
            _ev("task", f"{self.name} start g={gid(self.key)}")

        def end(self, s, status, why):
            self.status, self.why = status, why
            _ev("task", f"{self.name} {status} why={why} g={gid(self.key)} r={s.rnd - self.r0} cap={self.cap} "
                        f"trib={self.trib} carry={s.bag}")
            return status

        def abort(self, w, s, why):
            if self.status == "run":
                self.end(s, "abort", why)

        def goto(self, w, key):
            """One Nav leg step; returns the leg result and sets self.act."""
            r = w.nav.goto(key, w.snap.rnd)
            self.act = w.nav.act
            return r

        def step(self, w, s):
            return self.end(s, "fail", "not_built")


    class Capture(Task):
        """Walk onto any free spawn tile of a dead group, stand until paid, step off the same turn (I4, I5, I12)."""
        name = "Capture"

        def start(self, w, s):
            Task.start(self, w, s)
            self.on = None           # round we first stood on a spawn tile
            self.gold0 = w.me.gold_count()
            self.logged = False

        def blockers(self, w, s):
            h, me = self.key, w.me
            tiles = spawn_tiles(w, h)
            ally = vision.champion_tiles(Team.ALLY) & tiles
            ally.set(s.pos, False)                       # not me
            if not ally.is_empty() and tiles.is_set(s.pos):
                # Both of us on the region (cleared together): the lower unit id keeps it, the other leaves (I5).
                mine = int(me)
                if all(int(c) > mine for c in vision.champions(Team.ALLY) if c != me and ally.is_set(c.position())):
                    ally.clear()
            tm = getattr(w, "team", None)                # 80_team: an alive ally capturing h (A: its status bit)
            claimed = tm is not None and tm.ready and h in tm.capturing_groups
            enemy = not (vision.champion_tiles(Team.ENEMY) & tiles).is_empty()
            return (not ally.is_empty()) or claimed, enemy

        def skip(self, s, why, w=None):
            if w is not None and spawn_tiles(w, self.key).is_set(s.pos):
                self.step_off(w, s)                      # never squat a region we leave (I12)
            _ev("cap", f"{'end' if self.logged else 'skip'} g={gid(self.key)}" + (" abort" if self.logged else "")
                + f" r={0 if self.on is None else s.rnd - self.on} why={why}")
            return self.end(s, "fail", why)

        def step(self, w, s):
            h = self.key
            ally, enemy = self.blockers(w, s)
            if ally and self.on is None:
                return self.skip(s, "ally_on", w)      # never join an ally's capture (I5)
            if enemy:
                return self.skip(s, "enemy_on", w)     # progress resets at once [rules; measured A9]
            tiles = spawn_tiles(w, h)
            if not self.logged:
                gst = w.gstate(h)
                if gst != "dead":
                    return self.end(s, "fail", gst if gst != "-" else "unseen")
                if inc_at(w, s, s.pos) > 0 and danger(w, s).is_set(s.pos):
                    return self.skip(s, "danger", w)
                on = tiles.is_set(s.pos)
                free = disk(s.pos, 1) & tiles & ~s.occupied()
                d = 0 if on else (1 if not free.is_empty() else (w.dist(h, s.pos) or 0) + 1)
                _ev("cap", f"start g={gid(h)} d={d} allies=0 enemies={len(s.enemies)}")
                self.logged = True
            if tiles.is_set(s.pos):
                if self.on is None:
                    self.on = s.rnd
                bag, gold = s.bag, w.me.gold_count()
                gst = w.gstate(h) if (s.rnd - self.on) % 3 == 2 else "dead"     # ~27-50k: not every round
                if bag > self.bag0 or gold >= self.gold0 + 30 or gst == "respawning":
                    self.cap = bag - self.bag0
                    _ev("cap", f"end g={gid(h)} paid r={s.rnd - self.on} gems={self.cap} gold={gold - self.gold0}")
                    self.step_off(w, s)
                    return self.end(s, "ok", "paid")
                if gst == "alive" or s.rnd - self.on > cambc.constants.CAPTURE_TIME + CAP_GRACE:
                    _ev("cap", f"end g={gid(h)} reset r={s.rnd - self.on} gems=0 gold=0 why={'respawned' if gst == 'alive' else 'timeout'}")
                    return self.end(s, "fail", "timeout")
                if inc_at(w, s, s.pos) > 0:                  # an awake neighbour hits the tile (I10)
                    return self.skip(s, "danger", w)
                self.act = "cap"
                return "run"
            if self.on is not None:                     # pushed off the region
                self.on = None
            free = disk(s.pos, 1) & tiles & ~s.occupied()
            if not free.is_empty():
                if s.can_move and w.nav.move(free.positions()[0]):
                    self.act = "mv how=cap"
                else:
                    self.act = "wait why=blocked"
                return "run"
            r = self.goto(w, h)
            if r in ("full", "stuck"):
                return self.skip(s, "danger", w) if r == "stuck" else self.end(s, "fail", r)
            if r == "here":                              # on the ring but every adjacent spawn tile is taken
                self.act = "wait why=blocked"
            return "run"

        def step_off(self, w, s):
            """I12: off the spawn tile on the paid turn itself, onto a free non-camp tile."""
            if not s.can_move:
                return
            wl = walls(w, s)
            for dv in DIRS:
                q = s.pos + dv
                try:
                    if wl.is_set(q):
                        continue
                except Exception:
                    continue
                if w.nav.move(q):
                    self.act = "cap,mv"
                    return


    class ClearCamp(Task):
        """walk -> fight (L3 plan_turn/act; I3 gate before the first hit, during-condition every turn) -> step
        out when the flee condition holds -> re-engage if the clear still leaves keep_hp -> all dead: Capture as
        the tail (self.then, already started and stepped this turn); ok when the capture has started."""
        name = "ClearCamp"

        def start(self, w, s):
            Task.start(self, w, s)
            self.f = None           # L3's Fight record once the gate passed (fight|start/end, clear line)
            self.out = False        # stepping out of range
            self.dpr = 1.0
            self.ring_r = None      # round the walk round to the target camp's own ring began (ring_reach)

        def fight_end(self, s, res, why):
            if self.f is not None:
                self.f.end(s.rnd, s.hp, res, why)
                self.f = None

        def abort(self, w, s, why):
            if self.status == "run":
                self.fight_end(s, "died" if why == "died" else "abort", why)
                self.end(s, "abort" if why != "died" else "fail", why)

        def fail(self, s, why):
            self.fight_end(s, "abort", why)
            return self.end(s, "fail", why)

        def step(self, w, s):
            h = self.key
            sense(w, s)
            kit = my_kit(w)
            if kit is None:
                return self.end(s, "fail", "no_kit")
            self.fight = self.hit = "-"
            tg = camp_targets(w, s, h)
            if not tg:
                gst = w.gstate(h) if w.anchor[h].chebyshev_distance(s.pos) <= 7 else "-"
                if gst == "dead":
                    self.fight_end(s, "done", "cleared")
                    cap = self.then = Capture(h)
                    cap.start(w, s)
                    cap.step(w, s)
                    self.act = cap.act
                    return self.end(s, "ok", "cleared")
                if gst == "respawning":
                    return self.fail(s, "respawning")
                r = self.goto(w, h)
                if r in ("full", "stuck"):
                    return self.fail(s, r)
                if r == "here":
                    return self.fail(s, "unseen")
                return "run"
            keep = card(w, "keep_hp") * s.max_hp
            inc = inc_at(w, s, s.pos)
            rem = sum(t[0] for t in tg)
            if self.f is not None:
                self.f.seen(tg)
                # I3 during: the predicted damage still to come (scaled by HP left) must leave keep_hp. Other
                # groups' hits are the flee test's business, not this one's.
                if not self.out and s.hp - self.f.pred[1] * rem / self.rem0 < keep:
                    self.fight_end(s, "abort", "losing")
                    self.out = True
                elif any(e[0].chebyshev_distance(s.pos) <= R1 and not duel_gate(
                        kit, s, kit_of(int(e[3].champion_name())), e[1], their_bag=e[2]).ok for e in s.enemies):
                    return self.fail(s, "enemy")
            holds, inc, t, k = flee_cond(w, s)
            if holds or self.out:
                if not self.out:
                    _ev("flee", f"hp={int(s.hp)} inc={inc} ttd={t} sts={k} bag={s.bag} why=camp")
                self.out = True
                if inc > 0 and danger(w, s).is_set(s.pos):
                    self.act = "mv how=out" if s.can_move and flee_step(w, s) else "wait why=blocked"
                    return "run"
                # Out of range (it sleeps after 2 rounds [measured A32], no regen [measured A28]): re-engage only
                # if this group's hits alone still leave keep_hp.
                if s.hp - sum(x[1] for x in tg) * -(-rem // self.dpr) < keep:
                    return self.fail(s, "lowhp")
                self.out = False
            avoid = [(q.x, q.y) for q, g in w.near(s.pos, 5) if g != h]     # never wake a neighbour (I17)
            it = plan_turn(kit, s, tg, False, inc, avoid=avoid)
            mv = ""
            if not it.needs_stand and s.can_move and (it.atk is None or not kit.ranged):
                # Varg: stand next to plan_turn's widest-splash target, not the nearest end of the line.
                want = tg[it.want] if it.want is not None and it.want < len(tg) else \
                    min(tg, key=lambda x: (max(abs(x[2] - s.pos.x), abs(x[3] - s.pos.y)), x[0]))
                if max(abs(want[2] - s.pos.x), abs(want[3] - s.pos.y)) > kit.arange:
                    if self.ring_r is None and self.goto(w, h) == "here" and \
                            not step_towards(w, s, V(want[2], want[3])):
                        self.ring_r = s.rnd                    # the last camps sit behind the others
                    if self.ring_r is not None and w.nav.moved_round != s.rnd and not ring_reach(self, w, s, want):
                        return self.fail(s, "unreach")         # ladder 14 Oct: 737 rounds blocked here
                    if w.nav.moved_round == s.rnd:
                        mv = "mv"
                        it = plan_turn(kit, s, tg, False, inc, pos=w.nav.dest, moved=True, avoid=avoid)
                    elif self.ring_r is None and self.goto(w, h) in ("full", "stuck"):
                        return self.fail(s, "stuck")
                else:
                    self.ring_r = None
            if self.f is None:
                if it.atk is None and it.cast is None:
                    self.act = mv or "wait why=blocked"
                    return "run"
                # I3 gate before the first hit (P1 calculate, P4 fight battles already won).
                comp = comp_of(tg)
                # The exact (event-based) predictor when it fits this turn with room for the rest of the turn;
                # else the pessimistic quick_clear: if even that passes, the exact one would too.
                p = predict_clear(kit, comp, kit.cds(s.rnd), fuel() - RESERVE > PRED_COST + PRED_SLACK,
                                  walk_in=(w.nav.moved_round == s.rnd))
                exact = p is not None
                p = p or quick_clear(kit, comp)
                if not exact and (p[0] >= FAR or p[1] * GATE_X >= s.hp - keep):
                    self.act = mv or "wait why=blocked"   # the exact prediction runs next turn (fuel, I9)
                    return "run"
                if p[0] >= FAR or p[1] * GATE_X >= s.hp - keep:
                    self.act = mv or "wait why=blocked"
                    return self.end(s, "fail", "gate")
                # An enemy that can reach us before the clear ends: within R1 it must pass the duel gate;
                # farther out only one that would win the duel stops us (P9 is about not fighting, not
                # about not farming).
                for e in s.enemies:
                    dd = e[0].chebyshev_distance(s.pos)
                    if dd > R1 + p[0]:
                        continue
                    try:
                        dg = duel_gate(kit, s, kit_of(int(e[3].champion_name())), e[1], their_bag=e[2])
                        bad = not dg.ok if dd <= R1 else dg.ttk_us < dg.ttk_them
                    except Exception:
                        bad = True
                    if bad:
                        self.act = mv or "wait why=blocked"
                        return self.end(s, "fail", "enemy")
                kinds_ = "".join("wegGm"[c[0]] for c in group_comp(w, h))
                self.f = Fight(f"g{h}", p, s.hp, keep, kinds_, enemies=len(s.enemies))
                self.f.start(s.rnd)
                self.dpr = max(1.0, rem / max(1, p[0]))
                self.rem0 = max(1, rem)
            a = act(it, w)
            self.f.turn(it, s.rnd)
            self.fight = self.f.vs
            if a:
                self.hit = gid(h)
            self.act = ",".join(x for x in (mv, a.replace(" ", ",")) if x) or "wait why=blocked"
            return "run"


    class Bank(Task):
        """Walk into submit range of altar i (plan index when plan.ok; None = nearest), refuse locks (I13) and
        stunners in reach, submit_gems, hold the channel; ok when the bag is 0."""
        name = "Bank"

        def __init__(self, altar=None):
            Task.__init__(self, "altar" if altar is None or altar == 255 else f"a{altar}")
            self.i = None if altar is None or altar == 255 else altar

        def start(self, w, s):
            Task.start(self, w, s)
            self.ch = False
            self.lock = None
            self.pos = None

        def altar(self, w, s):
            if self.i is not None:          # World orders altar_pos by the plan's index when plan_ok
                return w.altar_pos[self.i] if self.i < len(w.altar_pos) else None
            rng = cambc.constants.SUBMIT_GEMS_RANGE
            return next((a for a in w.altar_pos if a.chebyshev_distance(s.pos) <= rng), None)

        def step(self, w, s):
            me = w.me
            if self.ch:
                if s.st & ST_SUBMITTING:
                    self.act = "ch"
                    return "run"
                done = s.bag == 0
                lock = False
                if not done and self.pos is not None:          # an enemy lock placed on the altar breaks it [rules]
                    try:
                        lock = vision.has_altar_lock(self.pos) and not vision.altar_lock_at(self.pos).is_ally()
                    except Exception:
                        lock = False
                by = "-" if done else ("lock" if lock else "stun")
                _ev("bank", f"end {'done' if done else 'broken'} by={by} gems={self.g0 if done else 0} "
                            f"took={s.rnd - self.c0} pred={self.ticks}")
                self.ch = False
                if done:
                    self.trib = self.g0
                    return self.end(s, "ok", "banked")
                return self.end(s, "fail", "locked" if lock else "broken")   # locked: L5 runs ClearLock (I13)
            if s.bag <= 0:
                return self.end(s, "ok", "empty")
            a0 = self.altar(w, s) if self.i is not None else None
            if a0 is not None and fresh_near(w, s, a0, R1 + 2, BANK_FRESH) and a0.chebyshev_distance(s.pos) > 1:
                return self.end(s, "fail", "enemy")          # I11/I13: an own or team sighting at the altar now
            r = self.goto(w, self.key)
            if r == "stuck" and w.nav.risk_out == s.rnd:
                return self.end(s, "fail", "enemy")          # I11: held RISK_HOLD rounds at the risk mask
            if r in ("full", "stuck"):
                return self.end(s, "fail", r)
            if r != "here":
                return "run"
            a = self.pos = self.altar(w, s)
            if a is None:
                return self.end(s, "fail", "no_altar")
            lock = "none"
            if vision.has_altar_lock(a):
                lk = vision.altar_lock_at(a)
                lock = "ours" if lk.is_ally() else "enemy"
            if lock == "enemy":
                return self.end(s, "fail", "locked")         # I13: the driver runs ClearLock(i) if safe
            k = max(1, -(-s.bag // 10))
            ed = min((e[0].chebyshev_distance(s.pos) for e in s.enemies), default=None)
            st = min((e[0].chebyshev_distance(s.pos) for e in s.enemies if is_stunner(e[3])), default=None)
            if st is not None and st <= R1 + k and not (k == 1 and st > R1):
                return self.end(s, "fail", "enemy")          # I13: a stunner could break it
            # Damage does not interrupt a tribute [rules]; only death does. A non-stunner in channel reach is a
            # reason to leave only if its burst over the k ticks could take us below keep_hp (I2).
            near = sum(enemy_dpr(e[3], e[2], True) for e in s.enemies if e[0].chebyshev_distance(s.pos) <= R1 + k)
            if near * k >= s.hp - card(w, "keep_hp") * s.max_hp:
                return self.end(s, "fail", "enemy")
            me.submit_gems(a)
            self.ch, self.c0, self.g0, self.ticks = True, s.rnd, s.bag, k
            _ev("bank", f"start altar={a.x},{a.y} gems={s.bag} ticks={k} lock={lock} enemy={ed if ed is not None else '-'} "
                        f"stunner={st if st is not None else '-'}")
            self.act = "ch"
            return "run"


    class GoHome(Task):
        """Walk towards spawn; recall as soon as I1's safety condition holds and spawn is farther than
        RECALL_WALK; cancel if damage becomes possible; on arrival stay one turn (full heal [rules])."""
        name = "GoHome"

        def __init__(self, why="heal"):
            Task.__init__(self, "spawn")
            self.reason = why

        def start(self, w, s):
            Task.start(self, w, s)
            self.rec = False
            self.fails = 0
            self.home = None        # round we arrived on spawn
            self.side = 0           # side-step rounds used (a carrier never walks home through a fresh enemy)

        def abort(self, w, s, why):
            if self.rec and s.st & ST_RECALLING:
                w.me.cancel_recall()
                _ev("recall", "end cancel by=self")
                self.rec = False
            Task.abort(self, w, s, why)

        def step(self, w, s):
            me = w.me
            on = w.spawn.is_set(s.pos)
            if self.rec:
                if s.st & ST_RECALLING:
                    rem = me.remaining_channel_time()
                    if inc_at(w, s, s.pos) > 0 or any(e[0].chebyshev_distance(s.pos) <= R1 + rem for e in s.enemies):
                        me.cancel_recall()                       # I1: cancel the turn it stops being safe
                        _ev("recall", "end cancel by=self")
                        self.rec = False
                        self.fails += 1
                    else:
                        self.act = "ch"
                        return "run"
                else:
                    self.rec = False
                    if on:
                        _ev("recall", "end done by=-")
                        self.home = s.rnd
                        self.act = "ch"                          # arrival turn: stay to heal
                        return "run"
                    _ev("recall", "end broken by=dmg")
                    self.fails += 1
            if on:
                if self.home is None:
                    self.home = s.rnd
                    self.act = "wait why=channel"
                    return "run"
                return self.end(s, "ok", "home")
            sd = w.dist("spawn", s.pos)
            if sd is None:
                a = w.anchor.get("spawn")
                sd = FAR if a is None else s.pos.chebyshev_distance(a)
            if sd > RECALL_WALK and self.fails < 2:
                ok, aw, cd, ed = recall_safe(w, s)
                if ok:
                    me.recall()
                    self.rec = True
                    _ev("recall", f"start hp={int(s.hp)} bag={s.bag} awake={aw} camp={cd} enemy={ed} why={self.reason} "
                                  f"spawn_d={sd}")
                    self.act = "ch"
                    return "run"
                if s.bag > 0 and self.sidestep(w, s, sd):
                    return "run"
            r = self.goto(w, "spawn")
            if r in ("full", "stuck"):
                return self.end(s, "fail", r)
            return "run"

        def sidestep(self, w, s, sd):
            """Recall blocked by a fresh enemy (I1) that stands between us and spawn: walking home would carry
            the bag into it (the collision Bank/EVADE/GoHome loop). Step away from it instead, outside the
            danger mask, until the recall is safe; hold if no step gains distance. Bounded by SIDESTEP_MAX."""
            if self.side >= SIDESTEP_MAX:
                return False
            pos = s.pos
            foes = [e[0] for e in s.enemies] + [q for r, q in _S["seen"] if r >= s.rnd - 5]
            if s.bag >= card(w, "bank_at_threat"):
                foes += [q for q, e in team_sight(w, s, 5)]
            foes = [q for q in foes if q.chebyshev_distance(pos) <= R_RECALL + 2]
            ahead = []
            for q in foes:
                dq = w.dist("spawn", q)
                if dq is not None and dq < sd:
                    ahead.append(q)
            if not ahead:
                return False
            self.side += 1
            d, wl = danger(w, s), walls(w, s)
            e0 = min(q.chebyshev_distance(pos) for q in foes)
            inside = d.is_set(pos)          # already in an enemy's reach: any step that gains distance
            best = None
            if s.can_move:
                for dv in DIRS:
                    q = pos + dv
                    try:
                        if wl.is_set(q) or (d.is_set(q) and not inside):
                            continue
                    except Exception:
                        continue
                    e = min(f.chebyshev_distance(q) for f in foes)
                    if e <= e0:
                        continue
                    k = w.dist("spawn", q)
                    sc = (e, -(FAR if k is None else k))
                    if best is None or sc > best[0]:
                        best = (sc, q)
            if best is not None and w.nav.move(best[1]):
                self.act = "mv how=side"
            else:
                self.act = "wait why=hold"
            return True


    class Flee(Task):
        """The step that lowers steps-to-safety most (native danger masks); ok after FLEE_OK rounds without
        the flee condition (meanwhile it keeps retreating towards spawn)."""
        name = "Flee"

        def __init__(self, threat="camp"):
            Task.__init__(self, "spawn")
            self.threat = threat

        def start(self, w, s):
            Task.start(self, w, s)
            self.calm = 0

        def step(self, w, s):
            holds, inc, t, k = flee_cond(w, s)
            if holds:
                self.calm = 0
                _ev("flee", f"hp={int(s.hp)} inc={inc} ttd={t} sts={k} bag={s.bag} why={self.threat}")
            else:
                self.calm += 1
                if self.calm >= FLEE_OK:
                    return self.end(s, "ok", "safe")
            if inc > 0 and danger(w, s).is_set(s.pos):
                self.act = "mv how=fl" if s.can_move and flee_step(w, s) else "wait why=blocked"
                return "run"
            if w.spawn.is_set(s.pos):
                return self.end(s, "ok", "home")
            r = self.goto(w, "spawn")
            if r in ("full", "stuck"):
                return self.end(s, "ok", r)
            return "run"


    class Shop(Task):
        """On spawn or dead: shop_turn(); ok when nothing more to buy (gold < 30 or only the lock reserve)."""
        name = "Shop"

        def step(self, w, s):
            a = shop_turn(w, s)
            self.act = a or "wait why=blocked"
            return self.end(s, "ok", "done" if a else "nothing")
