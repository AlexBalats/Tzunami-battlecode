"""World (03_ARCHITECTURE.md section 2.1): static map facts (round-1 boot): the draft record decoded (fallback: a
minimal world from game_map, every side contested), camp_groups() ONCE (~0.9M), groups and altars, my roster slot;
it makes the Nav (30_nav). Nothing map-specific: everything comes from game_map at runtime.
"""

ROSTER = (9, 1, 8, 0, 2, 6)     # draft ids in pick order: MUST match PICKS in 80_draft (Ren third: 06 section 11.2)
ISSAC_B = 12                # Issac's body id: Cassi and Issac share draft id 3 [sdk], so slots order bodies
#                              (draft id 3 = Cassi, then ISSAC_B right after her; 06 section 11.3). Not in PICKS
#                              (they lost: 06 section 11.6); kept so a backup pick of them gets two slots
# 06 section 3: the roles, the same on every champion from the roster alone (no comms). Main carry: the first of
# MAIN_PREF we have (Vesper Vale: +33 % on gold she captures [sdk 3.0.1]; else Vendetta, resets on kills), else roster
# slot 0; second: the first of SECOND_PREF that is not the main (Ren, then Vendetta), else the lowest other slot.
MAIN_PREF = (1, 2)
SECOND_PREF = (8, 2, 1)
CRNG = {}                   # CampKind -> attack range (X1, 3.0: wolf / clusters 3, elk / golem 4, monolith 5) [sdk]
G_HP = {}                   # CampType -> (base HP, base Strength) [sdk base_stats]


def fget(f, p):
    try:
        v = f.get(p)
    except Exception:
        return FAR
    return v if 0 <= v < FAR else FAR


def body_of(t):
    """Body id of ChampionType t: its draft id, ISSAC_B for Issac (ChampionType 4) [sdk enums]."""
    return ISSAC_B if t == 4 else _TYPE_TO_DRAFT[t] if 0 <= t < len(_TYPE_TO_DRAFT) else t


def nbody(S):
    """Bodies of the first S picks: Cassi & Issac count 2 (06 section 11.3)."""
    return S + (3 in ROSTER[:S])


def crng(c):
    """A camp's attack range by kind (X1) [sdk Camp.attack_range]."""
    try:
        k = int(c.kind())
        rg = CRNG.get(k)
        if rg is None:
            rg = CRNG[k] = c.attack_range()
        return rg
    except Exception:
        return 5


def disk(c, r):
    b = Bitboard()
    b.draw_chebyshev(c, r)
    return b


class Grp:
    __slots__ = ("h", "obj", "camps", "tiles", "anchor", "mons", "gems", "gold", "resp", "need", "side", "near",
                 "d_us", "d_them", "mi", "hp", "st", "until", "seen")


def _dead(u):
    try:
        return u.health() <= 0
    except Exception:
        return True


def _awake(c):
    try:
        return int(c.state()) == 1          # CampState.ALIVE = awake [sdk 2.2]
    except Exception:
        return False


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
            d = draft_decode(cambc.draft_memory)
        except Exception as e:
            trace("boot", "decode " + err_text(e))
        self.d = d
        # groups: the only camp_groups() call
        self.G = {}
        self.order = []                 # group handles in camp_groups() order (draft-memory order)
        ct = Bitboard()
        self.tinfo = {}                 # spawn (x, y) -> (group handle, attack range): Info.camp_hit (35_info)
        for g in game_map.camp_groups():
            o = Grp()
            o.h, o.obj = int(g), g
            o.camps = g.camps()
            o.tiles = [c.spawn_position() for c in o.camps]
            o.anchor = o.tiles[0]
            for c, t in zip(o.camps, o.tiles):
                self.tinfo[(t.x, t.y)] = (o.h, crng(c))
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
        self.nav = nav = Nav(self, terr, ab)     # fields F_alt, F_enemy (30_nav)
        if not d:
            nav.F_home = DistanceField()
            nav.F_home.compute(terr, self.sp, Bitboard(), FAR - 1)
            for h in self.order:
                o = self.G[h]
                o.d_us = min(255, fget(nav.F_home, o.anchor))
                o.d_them = min(255, fget(nav.F_enemy, o.anchor))
        if self.bank == 255 and nA:
            sp0 = self.sp.positions()[0]
            self.bank = min(range(nA), key=lambda i: sp0.chebyshev_distance(self.apos[i]))
        self.gate_init()
        self.pos = me.position()
        nav.build_fme(self.pos)
        self.slot_init()
        self.kit = Kit(me)
        trace("boot", f"mem={'ok' if d else 'none'} groups={len(self.order)} altars={nA} slot={self.slot} "
                      f"bank=A{self.bank} role={self.role} main={self.main} second={self.second} fuel={f0 - fuel()}")

    def gate_init(self):
        """00_PATCH_3_0 X8 (06 section 1.4): an altar none of whose approach-ring tiles (Chebyshev 1 [rules]) is
        reachable from our spawn while the camps stand (a live monster holds its tile) is gated by the groups with a
        spawn tile within 2 of it; w.agate[i] = those handles, or None (open). An empty list: never reachable. One
        DistanceField at boot."""
        f = DistanceField()
        f.compute(self.nav.blk | self.ctiles, self.sp, Bitboard(), FAR - 1)
        self.agate = []
        for a in self.apos:
            ring = disk(a, 1) & ~self.nav.blk
            if any(fget(f, t) < FAR for t in ring.positions()):
                self.agate.append(None)
            else:
                self.agate.append([h for h in self.order if any(t.chebyshev_distance(a) <= 2 for t in self.G[h].tiles)])
        self.gates = {h for g in self.agate if g for h in g}
        if any(g is not None for g in self.agate):
            trace("boot", "gated " + " ".join(f"A{i}:{g}" for i, g in enumerate(self.agate) if g is not None))

    def altar_open(self, i):
        """X8: altar i has a reachable ring tile now (open, or a gate group is not alive: its tile is free)."""
        g = self.agate[i]
        return g is None or any(self.G[h].st != "alive" for h in g)

    # ---- roster slot ----
    def slot_init(self):
        """Roster slot = index of my body in the bodies present (ROSTER order with Issac right after Cassi, others
        after, by id; 06 section 11.3). A sixth body (slot 5) writes no shared byte (40_comms) and reads the others."""
        self.slot_of = {}
        ids = {}
        try:
            for c in cambc.champions(Team.ALLY):
                if c.is_visible():
                    t = int(c.champion_name())
                    ids[int(c)] = body_of(t)
        except Exception as e:
            trace("boot", "allies " + err_text(e))
        mid = body_of(ME.get("type", -1)) if "type" in ME else -1
        ids[int(self.me)] = mid
        ds = set(ids.values())
        order = [b for p in ROSTER for b in ((3, ISSAC_B) if p == 3 else (p,))]
        roster = [p for p in order if p in ds] + sorted(p for p in ds if p not in order)
        self.roster = roster
        for hd, dd in ids.items():
            self.slot_of[hd] = roster.index(dd)
        self.slot = roster.index(mid) if mid in roster else len(roster)
        m = next((roster.index(d) for d in MAIN_PREF if d in roster), 0)
        rest = [k for k in range(len(roster)) if k != m]
        sec = next((roster.index(d) for d in SECOND_PREF if d in roster and roster.index(d) != m), rest[0] if rest else -1)
        self.main, self.second = m, sec
        self.role = "main" if self.slot == m else "second" if self.slot == sec else "crew"

    def ally_slot(self, c):
        hd = int(c)
        s = self.slot_of.get(hd)
        if s is None:
            try:
                dd = body_of(int(c.champion_name()))
                s = self.roster.index(dd) if dd in self.roster else 5
            except Exception:
                s = 5
            self.slot_of[hd] = s
        return s

    def G_maxhp(self, c):
        try:
            return G_HP[int(c.kind())][0]
        except Exception:
            return 1e9

    def start(self, new, r, s):
        """Switch to (option, target) new: the frame (started, status, deadline, sunk progress, hit) and the
        Behavior's own state (enter). Deadline = walk estimate + 10 rounds + the Behavior's own work (60_behaviors)."""
        self.cur, self.started, self.status = new, r, "going"
        self.hit = False                            # trace only: attacked since this choice (choice `hit=`)
        walk, work = BEH[new[0]].enter(self, s, new[1])
        self.deadline = r + min(walk, 150) + 10 + work
        self.prog, self.d0, self.pbest, self.pstall = 0.0, None, 0.0, 0   # [IMPROVEMENTS 2] sunk progress (prog_update)


WORLD = World()
