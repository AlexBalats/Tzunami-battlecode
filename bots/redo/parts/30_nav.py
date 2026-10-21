"""Nav (docs/redo/05_PATHFINDING.md; 03_ARCHITECTURE.md section 2.1): every move and dash. Returns a status, never a
decision: "here" | "moved" | "blocked" | "waiting" | ("failed", reason).

L0 global goal fields over static blockers (walls, holes, altars, enemy spawn; camp tiles are NOT blockers: which
   camps live is dynamic), per key: "g<h>" tiles within my attack range of group h's camps, "c<h>" its spawn tiles,
   "a<i>" altar i's ring, "home"; LRU-capped. Plus F_alt, F_enemy, F_home, and F_me with the walks gd / ad / near6
   that Prices read. Every build asks the turn ledger first (09 H1: can_build; fcost = one build's measured fuel).
L1 a waypoint K_WP steps down the global field (units ignored), then a local window compute_to(waypoint -> me) with
   units, live camps and danger as walls: Om Nom's Optimal Bug, our exact field as the bug walk. Fast path: nothing
   within FAST_R of the next FAST_N steps -> the global step.
L2 danger passes (Info, 35_info): camp_hit | enemy_hit, then camp_hit, then none (mode "fight": camp_hit, none).
L3 order(): set_priority, nearer my goal acts first, the capturer last.
L4 movement dash ("fast" walks, quiet rounds): 2 tiles down the field, then the step.
L5 a False move = an unseen champion in a bush: Mem, then the next candidate.
L6 progress monitor per goal: no gain STALL_RAND turns -> allies are walls 3 times in 4, STALL_SIDE -> a sidestep,
   STALL_FAIL -> ("failed", "stuck" | "osc"); 90_main's act fails the Behavior on it.
L7 tie-breaks among the window's optimal steps. L8 near the goal the window's roots are the goal's free tiles, so the
   bodies of a crew take distinct tiles; none free -> "waiting".
"""

FME_MOVE = 6                # rebuild F_me when I am more than this from its root
NAV_CACHE = 6               # goal fields kept (~31k memory each; ~0.77M fuel to build at 100x100 [measured 20 Oct])
FIELD_K = 770_000           # 09 H1: one field build at 100x100 [measured 20 Oct]; x area until the boot build is measured
GOAL_RES = 200_000          # 09 H1: fuel a goal-field build leaves for the rest of execute
HOME_RES = 100_000          # 09 H1: ... and the home field (its callers are cheap)
K_WP = 8                    # GUESS: waypoint steps down the global field (05 L1)
WIN_EXTRA = 4               # window max distance = K_WP + this: the detour it can find (05 L1)
FAST_N, FAST_R = 3, 2       # GUESS: fast path when no unit / live camp / danger within FAST_R of the next FAST_N steps
STALL_RAND = 2              # GUESS: L6 no-gain turns before allies count as walls only 3 times in 4 (Gone Fishin)
STALL_SIDE = 4              # GUESS: ... before a sidestep (05 L6 said "another ring tile": L8 makes that automatic)
STALL_FAIL = 8              # GUESS: ... before ("failed", "stuck" | "osc")
MAXP = 100                  # L3 priority scale
ESCAPE_DASH = (1, 8)        # draft ids of Vesper and Ren: the dash is the escape, no movement dash with a bag (05 L4)
DASH_QUIET = 8              # no movement dash this many rounds after an enemy within DASH_QUIET_R (05 L4)
DASH_GAIN = 2               # a movement dash lands this much lower on the goal field: its full 2 tiles [rules]
DIRS = tuple(V(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)


class Nav:
    def __init__(self, w, terr, ab):
        """Round-1 fields (boot). w: the World (groups, altars, spawns, me)."""
        self.w = w
        self.hd = int(w.me)
        self.blk = terr | ab | w.esp            # L0: static walk blockers
        self.blk_dist = terr | w.esp            # F_me / F_enemy: altar and camp tiles passable (distances to them)
        nw = terr | terr.shift_right(1) | terr.shift_right(-1)
        self.nearw = (nw | nw.shift_up(1) | nw.shift_up(-1)) & ~terr     # L7: tiles along a wall
        self.goals, self.keys, self.cw = {}, [], set()
        self.fcost = FIELD_K * w.Wm * w.Hm // 10000   # GUESS (09 U2): area scaling, replaced by build_fme's measure
        self.moved, self.fail, self.last_step, self.lastp = False, None, "-", None
        self.wp = self.wpk = None
        self.mk, self.mbest, self.mn, self.mr, self.mpos = None, FAR, 0, -9, []
        self.lastv, self.prio = None, None
        self.n = [0] * 8                        # steps fast window pass>1 unit-blocked bush dash failed (tick `nav=`)
        rings = Bitboard()
        for a in w.apos:
            rings.draw_chebyshev(a, 1)
        rings &= ~self.blk
        self.F_alt = DistanceField()
        self.F_alt.compute(self.blk & ~rings, rings, Bitboard(), FAR - 1)
        self.F_enemy = DistanceField()
        self.F_enemy.compute(terr, w.esp, Bitboard(), FAR - 1)
        self.F_home = self.F_me = None
        self.dash_ab = None
        try:
            for a in w.me.abilities():
                if a.is_dash():
                    self.dash_ab = a            # dash_to (ground target, 2 tiles [rules])
        except Exception as e:
            trace("boot", "abilities " + err_text(e))

    def begin(self):
        """Turn start (90_main turn)."""
        self.moved, self.fail, self.lastv = False, None, None

    # ---- fields ----
    def can_build(self, extra):
        """09 H1 (P12): a field build starts only if the turn can still pay for it plus `extra` after it."""
        return fuel() > self.fcost + extra

    def build_fme(self, pos):
        """F_me from pos; gd/ad: walk distance to every group anchor / altar tile (stale until the next build). Its
        cost sets fcost (the first build measures it, later ones can only raise it)."""
        w = self.w
        f = DistanceField()
        b = Bitboard()
        b.set(pos)
        f0 = fuel()
        f.compute(self.blk_dist, b, Bitboard(), FAR - 1)
        c = f0 - fuel()
        self.fcost = c if self.F_me is None else max(self.fcost, c)
        self.F_me, self.fme_root = f, pos
        self.gd = {h: fget(f, w.G[h].anchor) for h in w.order}
        self.ad = [fget(f, a) for a in w.apos]
        self.near6 = sorted(w.order, key=lambda h: self.gd[h])[:6]

    def home_field(self):
        """F_home, built lazily when the ledger allows (else None: fget(None, p) is FAR)."""
        if self.F_home is None and self.can_build(HOME_RES):
            self.F_home = DistanceField()
            self.F_home.compute(game_map.walls() | game_map.holes(), self.w.sp, Bitboard(), FAR - 1)
        return self.F_home

    def build(self, key, cw=False):
        """L0 goal field for key -> (field, roots). cw: the camp tiles are walls too (the window found no way past
        a camp: 05 L0's fallback)."""
        w = self.w
        k, blk = key[0], self.blk
        if k == "g":
            r = max(1, ME.get("range", 1))
            roots = Bitboard()
            for t in w.G[int(key[1:])].tiles:
                roots.draw_chebyshev(t, r)
            roots &= ~(blk | w.ctiles)          # never a spawn tile: an occupied one delays the respawn [rules]
        elif k == "c":
            roots = Bitboard()
            for t in w.G[int(key[1:])].tiles:
                roots.set(t)
        elif k == "a":
            roots = disk(w.apos[int(key[1:])], 1) & ~blk
        else:
            roots = w.sp & ~blk
        walls = (blk | w.ctiles) if cw else blk
        f = DistanceField()
        f.compute(walls & ~roots, roots, Bitboard(), FAR - 1)
        if key not in self.goals:
            self.keys.append(key)
            if len(self.keys) > NAV_CACHE:
                old = self.keys.pop(0)
                self.goals.pop(old, None)
                self.cw.discard(old)
        self.goals[key] = g = (f, roots)
        if self.wpk == key:
            self.wpk = None
        return g

    def goal(self, key, r):
        """Cached goal field, else built if the ledger allows (09 H1); None: not this turn."""
        g = self.goals.get(key)
        if g is not None:
            return g
        if not self.can_build(GOAL_RES):
            return None
        return self.build(key)

    def walk_to(self, key, pos):
        """Exact walk if key's goal field is cached, else None."""
        g = self.goals.get(key)
        return None if g is None else fget(g[0], pos)

    # ---- dashes ----
    def dash_to(self, s, key, kind):
        """Dash (the is_dash slot, if ready) to the valid free tile with the lowest key(q) (None = not a candidate);
        tries the best 4 (use() returns False on an unseen occupant, raises on a known bad tile). On success s.pos is
        the landing tile; traces `dash`. True if I dashed."""
        a = self.dash_ab
        try:
            if a is None or not a.is_ready():
                return False
            vt = a.valid_tiles() & ~(self.blk | INFO.units() | INFO.camps())
        except Exception:
            return False
        cand = sorted((k, q.x, q.y) for q in vt.positions() for k in (key(q),) if k is not None)
        for _k, x, y in cand[:4]:
            try:
                if a.use(V(x, y)):
                    trace("dash", f"{kind} {s.pos.x},{s.pos.y}->{x},{y}")
                    s.pos = V(x, y)
                    self.moved = True
                    self.n[6] += 1
                    return True
                MEM.note_bush(V(x, y), s.r)
            except Exception:
                pass
        return False

    def escape(self, s, ne):
        """ESCAPE: an enemy within 2 -> dash to the tile farthest from the nearest enemy (capped 7), ties down the
        home field."""
        if s.near_e <= 2 and self.dash_ab is not None:
            hf = self.home_field()
            self.dash_to(s, lambda q: (-min(7, min(q.chebyshev_distance(p) for p in ne)), fget(hf, q)), "escape")

    # ---- moves ----
    def try_moves(self, s, cands, units):
        """Move to the first candidate that works. A False is a hidden champion in a bush [rules]: Mem notes it (L5)
        and the next candidate is tried this turn. Known-occupied tiles (units) are skipped: they raise [rules]."""
        w = self.w
        for q in cands:
            if not (0 <= q.x < w.Wm and 0 <= q.y < w.Hm) or units.is_set(q) or self.blk.is_set(q):
                continue
            try:
                ok = w.me.move_absolute(q)
            except Exception:
                continue
            if ok:
                self.moved = True
                self.lastp = q
                return True
            MEM.note_bush(q, s.r)
            units.set(q, True)
            self.n[5] += 1
        return False

    def coin(self, s, q):
        """1 time in 4, different per body, round and tile (L6: Gone Fishin's 25 % ally-as-empty)."""
        return (self.hd * 7919 + s.r * 104729 + q.x * 31 + q.y * 17) % 4 == 0

    def passes(self, mode, skip):
        """L2: the danger boards, one per pass, the empty ones dropped; None = no danger."""
        if mode == "raw":
            return [None]
        ch = INFO.camp_hit(skip)
        out = []
        if mode != "fight":
            eh = INFO.enemy_hit()
            if not eh.is_empty():
                out.append(ch | eh)
        if not ch.is_empty():
            out.append(ch)
        out.append(None)
        return out

    def window(self, s, roots, passes, units, md):
        """L1/L2: compute_to(roots -> me) with units, live camps and each pass's danger as walls -> (field, pass index)
        or (None, -1). L6: after STALL_RAND no-gain turns, allies are walls only 3 times in 4."""
        pos = s.pos
        uw = units
        if self.mn >= STALL_RAND:
            uw = units.copy()
            for _c, p, _hp, _st in s.allies:
                if self.coin(s, p):
                    uw.set(p, False)
        base = self.blk | uw | INFO.camps()
        dest = Bitboard()
        dest.set(pos)
        for i, dz in enumerate(passes):
            walls = base | dz if dz is not None else base.copy()
            walls.set(pos, False)
            rt = roots & ~walls
            if rt.is_empty():
                continue
            g = DistanceField()
            g.compute_to(walls, rt, dest, Bitboard(), md)
            if fget(g, pos) < FAR:
                return g, i
        return None, -1

    def order_steps(self, s, g, f, dz):
        """L7: the window's optimal steps, best first: outside danger, lower global value, not on the map edge or along
        a wall (unless the goal is there), orthogonal, farther from the nearest ally."""
        pos, w = s.pos, self.w
        cands = [pos + d for d in g.next_moves_from(pos)]
        if len(cands) < 2:
            return cands
        key = []
        for q in cands:
            gv = fget(f, q) if f is not None else 0
            edge = gv > 0 and (q.x in (0, w.Wm - 1) or q.y in (0, w.Hm - 1) or self.nearw.is_set(q))
            ad = min((p.chebyshev_distance(q) for _c, p, _hp, _st in s.allies), default=3)
            key.append((dz is not None and dz.is_set(q), gv, edge, q.x != pos.x and q.y != pos.y, -min(ad, 3), q.x, q.y))
        key.sort()
        return [V(k[5], k[6]) for k in key]

    def monitor(self, s, key, v):
        """L6: no-gain turns on this goal (a new goal, or 2+ rounds without a step on it, starts again)."""
        pos = s.pos
        if key != self.mk or s.r - self.mr > 2:
            self.mk, self.mbest, self.mn, self.mpos = key, v, 0, []
        elif v < self.mbest:
            self.mbest, self.mn = v, 0
        else:
            self.mn += 1
        self.mr = s.r
        self.mpos = (self.mpos + [pos])[-4:]
        return self.mn

    def failed(self, s, key, v):
        m = self.mpos
        why = "osc" if len(m) == 4 and m[0] == m[2] and m[1] == m[3] and m[0] != m[1] else "stuck"
        trace("nav", f"failed {why} {key} v={v} best={self.mbest} n={self.mn} {s.pos.x},{s.pos.y}")
        self.fail, self.mk = why, None
        self.n[7] += 1
        return ("failed", why)

    def sidestep(self, s, f, v, units):
        """L6: any free neighbour no more than one worse on the global field, in a per-body order."""
        pos = s.pos
        cand = []
        for d in DIRS:
            q = pos + d
            u = fget(f, q)
            if u <= v + 1:
                cand.append((u, not self.coin(s, q), q.x, q.y))
        cand.sort()
        return self.try_moves(s, [V(x, y) for _u, _c, x, y in cand], units)

    def step(self, s, key, mode="safe"):
        """One step towards goal key. mode: "safe" (danger passes 1 -> 3), "fast" (safe + the movement dash),
        "fight" (camp danger only), "raw" (no danger)."""
        self.n[0] += 1
        if not s.can_move:
            return "blocked"
        g = self.goal(key, s.r)
        if g is None:
            return "blocked"
        f, roots = g
        v = fget(f, s.pos)
        if v == 0:
            self.mk, self.lastv = None, 0
            return "here"
        if v >= FAR:
            return "blocked"
        if self.monitor(s, key, v) >= STALL_FAIL:
            return self.failed(s, key, v)
        skip = int(key[1:]) if key[0] in "gc" else None     # the take's own group is not danger for its crew (05 L2)
        # L4: quiet rounds only; Vesper / Ren keep the dash (their escape) while carrying [05 L4]
        if mode == "fast" and v > 2 and self.dash_ab is not None and s.r - MEM.loud > DASH_QUIET \
                and not (s.bag > 0 and ME.get("id") in ESCAPE_DASH):
            ch = INFO.camp_hit(skip)
            if self.dash_to(s, lambda q: None if ch.is_set(q) else (lambda u: u if u <= v - DASH_GAIN else None)(fget(f, q)),
                            "traverse"):
                v = fget(f, s.pos)
                if v == 0:
                    self.lastv = 0
                    return "moved"
        units = INFO.units()
        passes = self.passes(mode, skip)
        pos = s.pos
        d0 = f.next_move_from(pos)
        q0 = pos + d0 if d0 is not None else None
        if q0 is not None and units.is_set(q0):
            self.n[4] += 1                      # L3 measure: a unit stands on my global optimal step
        if q0 is not None and self.mn < STALL_RAND:             # fast path
            box = disk(q0, FAST_R)
            q = q0
            for _ in range(FAST_N - 1):
                d = f.next_move_from(q)
                if d is None:
                    break
                q = q + d
                box.draw_chebyshev(q, FAST_R)
            obs = units | INFO.camps()
            if passes[0] is not None:
                obs |= passes[0]
            if (box & obs).is_empty() and self.try_moves(s, [q0], units):
                self.n[1] += 1
                self.lastv = v - 1
                self.last_step = f"{key} v={v} fast"
                return "moved"
        # L1 waypoint; L8 near the goal: the goal's tiles in the window are the roots
        wp = self.wp
        if self.wpk != key or wp is None or wp.chebyshev_distance(pos) <= 3 or fget(f, wp) >= v:
            q = pos
            for _ in range(K_WP):
                d = f.next_move_from(q)
                if d is None:
                    break
                q = q + d
            self.wp = wp = q
            self.wpk = key
        md = K_WP + WIN_EXTRA
        wr = roots & disk(pos, md) if fget(f, wp) == 0 else disk(wp, 1)
        gw, i = self.window(s, wr, passes, units, md)
        if gw is not None:
            self.n[2] += 1
            if i > 0:
                self.n[3] += 1
            if self.try_moves(s, self.order_steps(s, gw, f, passes[0]), units):
                self.lastv = fget(f, self.lastp)
                self.last_step = f"{key} v={v} win{i}"
                return "moved"
        elif fget(f, wp) == 0 and (wr & ~(self.blk | units | INFO.camps())).is_empty():
            self.last_step = f"{key} v={v} waiting"
            return "waiting"                    # L8: every goal tile near me is taken (Gone Fishin's congested well)
        elif key not in self.cw and not (INFO.camps() & disk(pos, md)).is_empty() and self.can_build(GOAL_RES):
            self.cw.add(key)                    # L0 fallback: the global path runs into live camps the window can't pass
            self.build(key, True)
            trace("nav", f"camp walls {key} v={v}")
        if self.mn >= STALL_SIDE and self.sidestep(s, f, v, units):
            self.lastv = fget(f, self.lastp)
            self.last_step = f"{key} v={v} side"
            return "moved"
        self.last_step = f"{key} v={v} blocked n={self.mn}"
        return "blocked"

    def near(self, s, tiles, r, mode="safe", skip=None):
        """One step towards the tiles within r of tile(s) (r = 0: onto them): the window alone (no global field), as
        far as it takes. For goals that move or live in vision (a chase, an ally, a live monster, a peek)."""
        self.n[0] += 1
        if not s.can_move:
            return "blocked"
        pos = s.pos
        roots = Bitboard()
        for t in (tiles if isinstance(tiles, list) else (tiles,)):
            if r:
                roots.draw_chebyshev(t, r)
            else:
                roots.set(t)
        roots &= ~self.blk
        if roots.is_set(pos):
            return "here"
        units = INFO.units()
        passes = self.passes(mode, skip)
        gw, i = self.window(s, roots, passes, units, FAR - 1)
        if gw is None:
            return "blocked"
        self.n[2] += 1
        if i > 0:
            self.n[3] += 1
        return "moved" if self.try_moves(s, self.order_steps(s, gw, None, passes[0]), units) else "blocked"

    def away(self, s, pts, cap=7):
        """One step that keeps the min distance to pts (enemies, or monsters in range) as large as possible, capped at
        cap, and among those the lowest home-field value (towards spawn)."""
        if not s.can_move:
            return "blocked"
        hf = self.home_field()
        pos, w = s.pos, self.w
        units, camps = INFO.units(), INFO.camps()
        cand = []
        for dv in DIRS:
            q = pos + dv
            if not (0 <= q.x < w.Wm and 0 <= q.y < w.Hm) or self.blk.is_set(q) or units.is_set(q) or camps.is_set(q):
                continue
            de = min(q.chebyshev_distance(p) for p in pts)
            cand.append((-min(de, cap), fget(hf, q), q.x, q.y))
        cand.sort()
        return "moved" if self.try_moves(s, [V(x, y) for _d, _h, x, y in cand[:3]], units) else "blocked"

    def order(self, w, s):
        """L3 (Gone Fishin's formation through turn order): the body nearest its goal acts first next round and
        clears the way for those behind; the capturer acts last, so the others have left the spawn tiles [rules:
        higher priority acts first within the team, from the next round]."""
        p = 0 if w.capt else (MAXP - min(self.lastv, MAXP - 1)) if self.lastv is not None else None
        if p is not None and p != self.prio:
            try:
                w.me.set_priority(p)
                self.prio = p
            except Exception as e:
                trace("nav", "set_priority " + err_text(e))
