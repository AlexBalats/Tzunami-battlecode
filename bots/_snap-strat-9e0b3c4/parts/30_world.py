"""World (play side): the round-1 boot, distance fields, groups and altars, roster slot, opening seed, movement.

Boot (once, round 1, ~1.5-3.5M): decode the draft memory (fallback: a minimal world from game_map, every side
contested), camp_groups() ONCE (~0.9M), fields F_alt (all altar rings), F_enemy (enemy spawn), F_me (my position;
rebuilt when I am > FME_MOVE tiles from its root or after a recall/death). Navigation uses goal fields per key
("g<h>" stand tiles of group h, "c<h>" its spawn tiles, "a<i>" altar i's ring, "home"), built on first use
(~280k at 80x80) and kept in a small cache. Nothing map-specific: everything comes from game_map at runtime.
"""

ROSTER = (9, 1, 0, 2, 6)    # draft ids in pick order: MUST match PICKS in 90_main's draft branch
CAMP_R = 3                  # every monster's attack range [measured A31]
FME_MOVE = 6                # rebuild F_me when I am more than this from its root (spec)
NAV_CACHE = 6               # goal fields kept (each ~31k memory, ~280k fuel to build at 80x80)
DIRS = tuple(V(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)
G_HP = {}                   # CampType -> (base HP, base Strength) [sdk base_stats]


def fget(f, p):
    try:
        v = f.get(p)
    except Exception:
        return FAR
    return v if 0 <= v < FAR else FAR


def disk(c, r):
    b = Bitboard()
    b.draw_chebyshev(c, r)
    return b


G2G_K = 0.5                 # [tuned 15 Oct; PRICES guess 1.5] gems per gold at round 0


def g2g(r):
    """Gems per gold [guess, strat/PRICES.md G2G], falling linearly to 0 at round 2000."""
    return G2G_K * (2000 - r) / 2000


def clear_dmg(mons, S, k):
    """clear_damage (10_model) with a live Strength: (rounds, damage summed over the k bodies). mons: [(hp, str)]
    of the live monsters; monsters die one at a time, the most dangerous per HP first [measured A3, A4]."""
    r, dmg, kS = 0, 0, max(1.0, k * S)
    for hp, st in sorted(mons, key=lambda m: -m[1] / max(1, m[0])):
        r += -(-int(hp) // int(kS))
        dmg += st * (r - 1)
    return r, dmg


class Grp:
    __slots__ = ("h", "obj", "camps", "tiles", "anchor", "mons", "gems", "gold", "resp", "need", "side", "near",
                 "d_us", "d_them", "mi", "hp", "st", "until", "seen")


def _uhp(u):
    try:
        return u.health()
    except Exception as e:
        return "?" + type(e).__name__


class World:
    def boot(self):
        f0 = fuel()
        self.me = me = cambc.me()
        self.Wm, self.Hm = game_map.width(), game_map.height()
        self.sp = game_map.spawn_region(Team.ALLY)
        self.esp = game_map.spawn_region(Team.ENEMY)
        self.sp0, self.esp0 = self.sp.positions()[0], self.esp.positions()[0]
        ab = game_map.altars()
        self.apos = ab.positions()
        terr = game_map.walls() | game_map.holes()
        d = None
        try:
            d = decode(cambc.draft_memory)
        except Exception as e:
            trace("boot", "decode " + err_text(e))
        self.d = d
        # groups: the only camp_groups() call
        self.G = {}
        self.order = []                 # group handles in camp_groups() order (draft-memory order)
        ct = Bitboard()
        for g in game_map.camp_groups():
            o = Grp()
            o.h, o.obj = int(g), g
            o.camps = g.camps()
            o.tiles = [c.spawn_position() for c in o.camps]
            o.anchor = o.tiles[0]
            mons = []
            for c in o.camps:
                k = int(c.kind())
                st = G_HP.get(k)
                if st is None:
                    b = c.base_stats()
                    st = G_HP[k] = (int(b.base_health), int(b.base_strength))
                mons.append(st)
            o.mons = mons
            o.gems, o.gold, o.resp = g.gem_value(), g.gold_value(), g.max_respawn_timer()
            o.need, o.side, o.near, o.d_us, o.d_them, o.mi = 1, 1, 255, 255, 255, 31
            o.hp = None                 # remembered live monsters [(hp, str)] (None: full)
            o.st, o.until, o.seen = "alive", 0, -1
            ct |= g.spawn_tiles()
            self.G[o.h] = o
            self.order.append(o.h)
        self.ctiles = ct
        self.blk_nav = terr | ab | self.esp | ct
        self.blk_dist = terr | self.esp            # F_me / F_enemy: altar and camp tiles passable (distances to them)
        nA = len(self.apos)
        self.aside = [1] * nA
        self.bank = 255
        if d:
            by = {h & 255: h for h in self.order}
            for i, rec in enumerate(d["groups"]):
                h = by.get(rec[0])
                if h is None:
                    continue
                o = self.G[h]
                o.side, o.need, o.near, o.d_us, o.d_them, o.mi = rec[1], rec[2], rec[4], rec[5], rec[6], min(i, 31)
            for i, a in enumerate(d["altars"][:nA]):
                self.aside[i] = a[0]
            self.bank = d["bank_altar"]
        else:
            S = max(1, len(cambc.champions(Team.ALLY)))
            for i, h in enumerate(self.order):
                o = self.G[h]
                o.mi = min(i, 31)
                o.need = bodies_needed(list(o.mons), S)
        self.idx = {self.G[h].mi: h for h in self.order if self.G[h].mi < 31}
        # fields
        self.nav = {}
        self.nav_keys = []
        rings = Bitboard()
        for a in self.apos:
            rings.draw_chebyshev(a, 1)
        rings &= ~self.blk_nav
        self.F_alt = DistanceField()
        self.F_alt.compute(self.blk_nav & ~rings, rings, Bitboard(), FAR - 1)
        self.F_enemy = DistanceField()
        self.F_enemy.compute(terr, self.esp, Bitboard(), FAR - 1)
        self.F_home = None
        if not d:
            self.F_home = DistanceField()
            self.F_home.compute(terr, self.sp, Bitboard(), FAR - 1)
            for h in self.order:
                o = self.G[h]
                o.d_us = min(255, fget(self.F_home, o.anchor))
                o.d_them = min(255, fget(self.F_enemy, o.anchor))
        if self.bank == 255 and nA:
            sp0 = self.sp.positions()[0]
            self.bank = min(range(nA), key=lambda i: sp0.chebyshev_distance(self.apos[i]))
        self.pos = me.position()
        self.build_fme(self.pos)
        self.slot_init()
        self.cast_init()
        trace("boot", f"mem={'ok' if d else 'none'} groups={len(self.order)} altars={nA} slot={self.slot} "
                      f"bank=A{self.bank} fuel={f0 - fuel()}")

    # ---- fields ----
    def build_fme(self, pos):
        """F_me from pos; gd/ad: walk distance to every group anchor / altar tile (stale until the next build)."""
        f = DistanceField()
        b = Bitboard()
        b.set(pos)
        f.compute(self.blk_dist, b, Bitboard(), FAR - 1)
        self.F_me, self.fme_root = f, pos
        self.gd = {h: fget(f, self.G[h].anchor) for h in self.order}
        self.ad = [fget(f, a) for a in self.apos]
        self.near6 = sorted(self.order, key=lambda h: self.gd[h])[:6]

    def home_field(self):
        if self.F_home is None:
            self.F_home = DistanceField()
            self.F_home.compute(game_map.walls() | game_map.holes(), self.sp, Bitboard(), FAR - 1)
        return self.F_home

    def goal(self, key):
        """Goal field for a nav key, built on first use, LRU-capped."""
        f = self.nav.get(key)
        if f is not None:
            return f
        k, blk = key[0], self.blk_nav
        if k == "g":
            r = max(1, ME.get("range", 1))
            roots = Bitboard()
            for t in self.G[int(key[1:])].tiles:
                roots.draw_chebyshev(t, r)
            roots &= ~blk
        elif k == "c":
            roots = Bitboard()
            for t in self.G[int(key[1:])].tiles:
                roots.set(t)
        elif k == "a":
            roots = disk(self.apos[int(key[1:])], 1) & ~blk
        elif k == "w":                          # ward j: any free tile within 2 of its tile (placement reach 2 [rules])
            roots = disk(self.wtiles[int(key[1:])], 2) & ~blk
        else:
            roots = self.sp & ~blk
        f = DistanceField()
        f.compute(blk & ~roots, roots, Bitboard(), FAR - 1)
        self.nav[key] = f
        self.nav_keys.append(key)
        if len(self.nav_keys) > NAV_CACHE:
            self.nav.pop(self.nav_keys.pop(0), None)
        return f

    def walk_to(self, key, pos):
        """Exact walk if key's goal field is cached, else None."""
        f = self.nav.get(key)
        return None if f is None else fget(f, pos)

    # ---- roster slot ----
    def slot_init(self):
        """Roster slot = index of my draft id in the picked roster (ROSTER order, others after, by id)."""
        self.slot_of = {}
        ids = {}
        try:
            for c in cambc.champions(Team.ALLY):
                if c.is_visible():
                    t = int(c.champion_name())
                    ids[int(c)] = _TYPE_TO_DRAFT[t] if 0 <= t < len(_TYPE_TO_DRAFT) else t
        except Exception as e:
            trace("boot", "allies " + err_text(e))
        ids[int(self.me)] = ME.get("id", -1)
        ds = set(ids.values())
        roster = [p for p in ROSTER if p in ds] + sorted(p for p in ds if p not in ROSTER)
        self.roster = roster
        for hd, dd in ids.items():
            self.slot_of[hd] = roster.index(dd)
        mid = ME.get("id", -1)
        self.slot = min(4, roster.index(mid) if mid in roster else (ROSTER.index(mid) if mid in ROSTER else 4))

    def ally_slot(self, c):
        hd = int(c)
        s = self.slot_of.get(hd)
        if s is None:
            try:
                t = int(c.champion_name())
                dd = _TYPE_TO_DRAFT[t]
                s = ROSTER.index(dd) if dd in ROSTER else 4
            except Exception:
                s = 4
            self.slot_of[hd] = s
        return s

    # ---- abilities ----
    def cast_init(self):
        """Slots by use: camp damage, champion damage, CC (ME['has_cc'] rule), attack reset."""
        self.ab, self.dash_ab = [], None
        try:
            for a in self.me.abilities():
                if a.is_dash():
                    self.dash_ab = a                # dash_to (ground target, 2 tiles [rules])
                info = a.info()
                if info is None:
                    continue
                aoe, dmg = a.is_aoe_damage(), a.is_damage()
                cc = a.is_cc() or (aoe and getattr(info, "duration", 0) > 0) or bool(getattr(info, "enhanced_attack", False))
                self.ab.append((a, (dmg or aoe) and a.can_target_camps(), (dmg or aoe or cc) and a.can_target_enemies(),
                                cc, a.is_attack_reset(), a.can_target_ground()))
        except Exception as e:
            trace("boot", "abilities " + err_text(e))

    def cast(self, target, camp):
        """One cast this turn on target (Unit) if a fitting slot is ready; False if none fired."""
        for a, on_camp, on_enemy, cc, reset, ground in self.ab:
            if (on_camp if camp else (on_enemy or (cc and not reset))) and not reset:
                try:
                    if not a.is_ready():
                        continue
                    if a.use(target):
                        return True
                except Exception:
                    try:
                        if ground and a.use(target.position()):
                            return True
                    except Exception:
                        pass
        return False

    def reset_attack(self, target, pre=None):
        """Attack-reset slots (self-cast), then a second basic attack. TRACE: `reset` line with the target's HP
        before my first hit (pre), at cast and right after the second attack() (verification, 15 Oct); the next
        turn's HP is traced by reset_check()."""
        for a, _c, _e, _cc, reset, _g in self.ab:
            if reset:
                try:
                    if a.is_ready() and a.use(None):
                        h0 = _uhp(target) if TRACE else 0
                        err = "-"
                        try:
                            ret = self.me.attack(target)
                            err = f"ret={ret}"
                        except Exception as e:
                            err = "raise " + err_text(e)[:80]
                        if TRACE:
                            h1 = _uhp(target)
                            self.rst = (target, pre, h0, cambc.round_number())
                            trace("reset", f"tgt={int(target)} pre={pre} cast={h0} after2={h1} str={self.me.strength():.0f} "
                                           f"{err} range={ME.get('range')}")
                        return True
                except Exception:
                    pass
        return False

    def reset_check(self):
        """TRACE only: the target's HP one turn after a reset cast (see reset_attack)."""
        rs = getattr(self, "rst", None)
        if rs is None:
            return
        self.rst = None
        t, pre, h0, r0 = rs
        trace("reset", f"next tgt={int(t)} pre={pre} cast={h0} now={_uhp(t)} rounds={cambc.round_number() - r0}")

    # ---- movement ----
    def dash_to(self, s, key, kind):
        """[user plan 15 Oct] Dash (the is_dash slot, if ready) to the valid free tile with the lowest key(q) (None =
        not a candidate); tries the best 4 (use() returns False on an unseen occupant, raises on a known bad tile).
        On success s.pos is the landing tile; traces `dash`. True if I dashed."""
        a = self.dash_ab
        try:
            if a is None or not a.is_ready():
                return False
            vt = a.valid_tiles() & ~(self.blk_nav | vision.champion_tiles())
        except Exception:
            return False
        cand = sorted((k, q.x, q.y) for q in vt.positions() for k in (key(q),) if k is not None)
        for _k, x, y in cand[:4]:
            try:
                if a.use(V(x, y)):
                    trace("dash", f"{kind} {s.pos.x},{s.pos.y}->{x},{y}")
                    s.pos = V(x, y)
                    return True
            except Exception:
                pass
        return False

    def move(self, q):
        try:
            ok = self.me.move_absolute(q)
        except Exception:
            return False
        if ok:
            self.moved = True
        return ok

    def step_field(self, f, pos):
        """One step down field f: its optimal step, else the lowest finite neighbour below my value, else (on a
        wall tile of f, e.g. a camp spawn tile) the lowest finite neighbour. 'here' | 'moved' | 'blocked'."""
        v = fget(f, pos)
        if v == 0:
            return "here"
        dv = None
        if v < FAR:
            try:
                dv = f.next_move_from(pos)
            except Exception:
                dv = None
        self.last_step = f"v={v} dv={dv}"
        if dv is not None and self.move(pos + dv):
            self.nblock = 0
            return "moved"
        best = []
        nb = getattr(self, "nblock", 0)
        lim = v - 1 if nb < 1 else v if nb < 3 else v + 1     # sidestep after 1 blocked turn, uphill after 3
        for dv in DIRS:
            q = pos + dv
            u = fget(f, q)
            if u <= lim and u < FAR:
                best.append((u, q.x, q.y))
        best.sort()
        for u, x, y in best[:4]:
            if self.move(V(x, y)):
                self.nblock = 0
                return "moved"
        self.nblock = nb + 1
        return "blocked"

    def step_to(self, key, s):
        if not s.can_move:
            return "blocked"
        f = self.goal(key)
        if s.near_e > 8 and self.cur[0] in ("farm", "bank", "ward", "hunt") and self.dash_ab is not None:
            v = fget(f, s.pos)                  # TRAVERSE: 2 tiles down the field, then the normal step
            if 2 < v < FAR and self.dash_to(s, lambda q: fget(f, q) if fget(f, q) <= v - 2 else None, "traverse"):
                st = self.step_field(f, s.pos)
                trace("dash", f"traverse then step={st}")
                return st
        return self.step_field(f, s.pos)

    def step_near(self, tiles, r, s):
        """Towards the tiles within r of tile(s) (a one-off compute_to, ~75k)."""
        if not s.can_move:
            return "blocked"
        blk = self.blk_nav | vision.champion_tiles()
        blk.set(s.pos, False)
        roots = Bitboard()
        for t in (tiles if isinstance(tiles, list) else (tiles,)):
            roots.draw_chebyshev(t, r)
        roots &= ~blk
        if roots.is_empty():
            return "blocked"
        dest = Bitboard()
        dest.set(s.pos)
        f = DistanceField()
        f.compute_to(blk & ~roots, roots, dest, Bitboard(), FAR - 1)
        return self.step_field(f, s.pos)

    def step_flee(self, s, pts):
        """HEAL / recall refused: one step that keeps the min distance to pts (enemies) as large as possible, capped
        at 7 (out of reach + a step), and among those the lowest home-field value (towards spawn)."""
        if not s.can_move:
            return "blocked"
        hf = self.home_field()
        pos = s.pos
        cand = []
        for dv in DIRS:
            q = pos + dv
            if not (0 <= q.x < self.Wm and 0 <= q.y < self.Hm) or self.blk_nav.is_set(q):
                continue
            de = min(q.chebyshev_distance(p) for p in pts)
            cand.append((-min(de, 7), fget(hf, q), q.x, q.y))
        cand.sort()
        for _d, _h, x, y in cand[:3]:
            if self.move(V(x, y)):
                return "moved"
        return "blocked"

    def step_away(self, s, pts):
        """A step maximising the min Chebyshev distance to pts (out of camp range)."""
        if not s.can_move:
            return "blocked"
        pos = s.pos
        cand = []
        for dv in DIRS:
            q = pos + dv
            if not (0 <= q.x < self.Wm and 0 <= q.y < self.Hm) or self.blk_nav.is_set(q):
                continue
            cand.append((-min(q.chebyshev_distance(p) for p in pts), q.x, q.y))
        cand.sort()
        for _d, x, y in cand[:3]:
            if self.move(V(x, y)):
                return "moved"
        return "blocked"


WORLD = World()


def opening_seed(w):
    """My entry of opening_slots (None past its end)."""
    slots = opening_slots(w, 5)               # 5: the same list whatever roster I saw at boot
    return slots[w.slot] if w.slot < len(slots) else None


def ward_init(w):
    """Wards on the way (15 Oct, late): the draft's ward tiles (d['wards'], up to 3) are a team list of pending tiles
    for the whole game. No round-1 assignment and no rush: any champion whose own ward is still unplaced (one per
    champion, permanent [rules]) places a pending one when it is on its way (WARD price, 40_prices). w.wtiles[j] is
    tile j; w.ward_pending the indices not yet seen placed (an ally ward seen within 2 of the tile, or mine)."""
    w.wtiles, w.ward_pending, w.ward_tries = [], set(), {}
    d = w.d
    if not d or not d.get("wards"):
        return
    for j, (x, y) in enumerate(d["wards"][:3]):
        w.wtiles.append(V(x, y))
        w.ward_pending.add(j)


VESPER_ID = 1                # draft id of Vesper Vale (her slot takes a gold group first)


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


GROUP_NAMES = {3: "trio", 2: "pair", 1: "solo"}


def group_slots(w):
    """[user plan 15 Oct, pair/trio opener] group-game seeds: the roster split by size (5 -> trio + pair, 4 -> two
    pairs, 3 -> pair + solo, <= 2 -> one subgroup). Subgroup 0 takes the richest group needing 2..its size (else >= 2,
    else any); a pair as subgroup 1 the next richest needing exactly 2 (else >= 2, else any); a solo the best need-1
    group (else any). Vesper's slot joins the subgroup whose group has more gold (ties: subgroup 0); the other slots
    fill hers first, lowest slot first, then the other. Sets w.subs {slot: tuple of its subgroup's slots}; returns
    5 entries (slot -> group). Same on every champion: draft S, roster order, draft records only."""
    S = min(5, max(1, (w.d or {}).get("S") or len(w.roster)))
    sizes = (3, 2) if S >= 5 else (2, 2) if S == 4 else (2, 1) if S == 3 else (S,)
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
    vs = w.roster.index(VESPER_ID) if VESPER_ID in w.roster else -1
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
    slots = [None] * 5
    for i, ms in enumerate(mem):
        for k in ms:
            w.subs[k] = tuple(sorted(ms))
            slots[k] = gs[i]
    return slots


def opening_slots(w, n):
    """n DISTINCT group handles (slot i takes entry i); every champion computes the same list with no comms.
    Groups on our side (0) and contested (1), ranked by the walk from our spawn (d_us; ties: higher value per round),
    solo groups (need 1) first, then pair groups (need 2). [rule, 15 Oct ladder 2] Vesper's slot first takes the nearest
    group with gold > 0 (one she can take alone if any: all gold to Vesper); no group is given to two slots (the
    50x50 4-pick ladder map had one seedable group and three champions on it); when the list runs out, the
    next-nearest unused reachable group of any need and side. Seeds only the first choice."""
    if stack_mode(w, cambc.round_number()):
        return group_slots(w)[:n]               # [user plan 15 Oct, pair/trio opener] subgroup seeds
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
    vs = w.roster.index(VESPER_ID) if VESPER_ID in w.roster else -1
    vg = None
    if 0 <= vs < n:
        gold = sorted((w.G[h].side > 1, w.G[h].need > 1, w.G[h].d_us, h) for h in order if w.G[h].gold > 0)
        vg = gold[0][3] if gold else None
    slots, it = [], iter(h for h in order if h != vg)
    for i in range(n):
        slots.append(vg if i == vs and vg is not None else next(it, None))
    assert len(set(h for h in slots if h is not None)) == sum(1 for h in slots if h is not None), "seed dup"
    return slots
