"""World: map cache, camp table, distance fields, per-turn snapshot (CORE.md). Trimmed from tzu's 20_world.

Field keys: "spawn" (our spawn), "espawn" (enemy spawn region), "a<i>" (altar i's tribute ring, i = row-major
index in game_map.altars().positions() [sdk]), "g<h>" (stand next to a camp of group h, h = int(CampGroup)).
w.dist(key, pos) is None while the field is not computed yet, FAR when unreachable.
Fuel [measured 13 Oct, tzu]: camp_groups() ~0.74-1M (ONCE), a field ~280k at 80x80, field.get ~2.3k,
vision.champions(team) ~17k, camp.health() ~3k, CampGroup.state() ~27k.
"""

SNAP_RANGE = 4      # read camp HP only for groups within this of us (+ the target group)
AWAKE_ROUNDS = 2    # a camp sleeps 2 rounds after nobody is in range [measured A32]
HP_STALE = 40       # last-known camp HP is trusted this many rounds: no regen [measured A28]
CAMP_RANGE = 3      # every monster's attack range [measured A31]
CAMP_STR = (20, 60, 0, 0, 200)   # Strength by CampType WOLF, ELK, GEM, GOLD, MONOLITH [rules]
CONTEST_X = 1.3     # bank altar contested iff d(espawn, altar) <= CONTEST_X * d(spawn, altar) (CORE.md -> Modes)
BG_MARGIN = 100_000         # background leaves room for the trace line after it
JOB_CAP = 1_200_000         # no job estimate above this: the queue must never stall behind one job
INDEX_FUEL = 1_000_000      # boot step "index" (the one camp_groups() call) [measured ~0.74-1M]


def fget(field, pos):
    """Field value at pos; FAR when unreached, off the map or a wall."""
    try:
        v = field.get(pos)
    except Exception:
        return FAR
    return v if 0 <= v < FAR else FAR


def disk(center, r):
    b = Bitboard()
    b.draw_chebyshev(center, r)
    return b


class Snap:
    """What this champion knows this turn. Filled by World.snapshot()."""
    __slots__ = ("rnd", "st", "alive", "can_move", "can_attack", "submitting", "recalling", "stunned",
                 "pos", "hp", "max_hp", "bag", "gold", "enemies", "allies", "camp_hp", "near", "near_t",
                 "awake", "cost", "_occ")

    def occupied(self):
        """Tiles of visible champions plus teleport reservations (not walkable) [sdk]. Read lazily."""
        if self._occ is None:
            self._occ = vision.champion_tiles() | vision.teleport_tiles()
        return self._occ


class World:
    def __init__(self):
        """Cheap part only; setup() does the expensive boot steps."""
        self.me = me = cambc.me()
        self.ctype = int(me.champion_name())
        self.W, self.H = game_map.width(), game_map.height()
        self.spawn = game_map.spawn_region(Team.ALLY)          # Bitboard
        self.espawn_bb = game_map.spawn_region(Team.ENEMY)     # Bitboard
        self.espawn = self.espawn_bb.positions()               # list of enemy spawn tiles
        self.altar_pos = game_map.altars().positions()
        self.last_pos = me.position()
        self.snap = None
        self.groups = {}       # handle -> CampGroup
        self.camps = {}        # handle -> tuple of Camp
        self.anchor = {}       # key (and int h) -> one tile of the goal's object (greedy fallback)
        self.fields, self.goals, self.queue = {}, {}, []      # field key -> DistanceField / goal Bitboard; bg queue
        self.blocked = self.free = self.tile_group = self.camp_tiles = None
        self.scratch = Bitboard()
        self.est = {"field": self.W * self.H * 60 + 40_000, "_blk": 400_000, "_tiles": 1_000_000}
        self.last_hp, self.last_hp_r, self.awake_until = {}, {}, {}
        self.my_hp = 0.0         # my HP last turn (a drop with no enemy in sight: a camp hits me)
        self.bank_altar = None   # altar index nearest our spawn by field
        self.contested = False   # CORE.md -> Modes
        self.boot = ["index", "_blk", "_tiles", "spawn", "espawn", "modes"]
        self.ready = False

    def setup(self):
        """Boot steps in order, as many as fit above RESERVE (always at least one per call). True when ready."""
        ran = False
        while self.boot:
            k = self.boot[0]
            need = INDEX_FUEL if k == "index" else (50_000 if k == "modes" else self.cost_of(k))
            if ran and fuel() - RESERVE < need:
                break
            self.index() if k == "index" else self.modes() if k == "modes" else self.run(k)
            self.boot.pop(0)
            ran = True
        self.ready = not self.boot
        return self.ready

    def index(self):
        for g in game_map.camp_groups():           # the ONLY camp_groups() call (~0.74M)
            h = int(g)
            self.groups[h] = g
            cs = self.camps[h] = g.camps()
            self.anchor[h] = self.anchor[f"g{h}"] = cs[0].spawn_position()
        self.anchor["spawn"] = self.spawn.positions()[0]
        self.anchor["espawn"] = self.espawn[0]
        for i, a in enumerate(self.altar_pos):
            self.anchor[f"a{i}"] = a

    def ring_min(self, key, i):
        """Field key's smallest value on altar i's tribute ring (FAR if none)."""
        f = self.fields.get(key)
        return FAR if f is None else min((fget(f, p) for p in self.goal(f"a{i}").positions()), default=FAR)

    def modes(self):
        """Bank altar, contested flag, then the background queue: altars, groups nearest-first."""
        n = len(self.altar_pos)
        ds = [self.ring_min("spawn", i) for i in range(n)]
        if n:
            sp = self.anchor["spawn"]
            b = min(range(n), key=lambda i: (ds[i], sp.chebyshev_distance(self.altar_pos[i])))
            self.bank_altar = b
            self.contested = ds[b] < FAR and self.ring_min("espawn", b) <= CONTEST_X * ds[b]
        pos = self.last_pos
        alt = sorted(range(n), key=lambda i: ds[i])
        grp = sorted(self.groups, key=lambda h: pos.chebyshev_distance(self.anchor[h]))
        self.queue = [f"a{i}" for i in alt] + [f"g{h}" for h in grp]

    def job_blk(self):
        """Blocked mask: walls, holes, altars, the enemy spawn [sdk], camp spawn tiles (never routed over)."""
        ct = Bitboard()
        for g in self.groups.values():
            ct |= g.spawn_tiles()
        self.camp_tiles = ct
        self.blocked = game_map.walls() | game_map.holes() | game_map.altars() | self.espawn_bb | ct
        self.free = ~self.blocked

    def goal(self, key):
        """The goal bitboard of a field key, built on first use (needs "_blk")."""
        b = self.goals.get(key)
        if b is not None:
            return b
        free = self.free
        if key == "spawn":
            b = self.spawn & free
        elif key == "espawn":
            b = self.espawn_bb
        elif key[0] == "a":
            b = disk(self.altar_pos[int(key[1:])], cambc.constants.SUBMIT_GEMS_RANGE) & free
        else:                                          # "g<h>": stand next to a camp of the group
            b = Bitboard()
            for c in self.camps[int(key[1:])]:
                b.draw_chebyshev(c.spawn_position(), 1)
            b &= free
        self.goals[key] = b
        return b

    def run(self, key):
        """Run one job now (index job or field); self-correct its kind's estimate."""
        kind = key if key in ("_blk", "_tiles") else "field"
        if kind == "field" and self.blocked is None:
            self.run("_blk")
        f0, r0 = fuel(), cambc.round_number()
        if kind == "_blk":
            self.job_blk()
        elif kind == "_tiles":
            self.tile_group = {c.spawn_position(): h for h, cs in self.camps.items() for c in cs}
        else:
            roots = self.goal(key)
            f = DistanceField()
            f.compute(self.blocked & ~roots, roots, self.scratch, FAR)
            self.fields[key] = f
        cost = spent(f0, r0)
        self.queue = [k for k in self.queue if k != key]
        est, target = self.est[kind], int(cost * 1.3)
        self.est[kind] = target if target > est else (3 * est + target) // 4
        return cost

    def cost_of(self, key):
        k = key if key in ("_blk", "_tiles") else "field"
        c = self.est[k] + (self.est["_blk"] if k == "field" and self.blocked is None else 0)
        return min(c, JOB_CAP)

    def ensure(self, key):
        """Compute key's field now if it is missing and fits the turn under the reserve."""
        if key not in self.fields and fuel() - RESERVE > self.cost_of(key):
            self.run(key)
        return key in self.fields

    def want(self, key):
        """Move key's field to the front of the background queue."""
        if key not in self.fields:
            self.queue = [key] + [k for k in self.queue if k != key]

    def work(self):
        """Background: fields until the next one might not fit. Returns (jobs, fuel)."""
        n, f0 = 0, fuel()
        while self.queue and fuel() - RESERVE - BG_MARGIN > self.cost_of(self.queue[0]):
            self.run(self.queue[0])
            n += 1
        return n, f0 - fuel()

    def dist(self, key, pos):
        """Walking distance from pos to key's goal tiles; None while not computed, FAR when unreachable."""
        f = self.fields.get(key)
        return None if f is None else fget(f, pos)

    def near(self, pos, r):
        """[(spawn tile, group handle)] of camps within Chebyshev r of pos."""
        if self.tile_group is None:
            return []
        b = disk(pos, r)
        b &= self.camp_tiles
        tg = self.tile_group
        return [] if b.is_empty() else [(p, tg[p]) for p in b.positions()]

    def snapshot(self, rnd, target=None):
        """One state() read; champions in vision; camp HP only for groups within SNAP_RANGE + the target."""
        f0 = fuel()
        self.snap = s = Snap()
        s.rnd, s._occ = rnd, None
        s.enemies, s.allies, s.camp_hp, s.awake = [], [], {}, set()
        me = self.me
        s.st = st = int(me.state())
        s.alive = bool(st & ST_ALIVE)
        s.recalling = bool(st & ST_RECALLING)
        s.submitting = bool(st & ST_SUBMITTING)
        s.can_move = bool(st & ST_CAN_MOVE)
        s.can_attack = bool(st & ST_CAN_ATTACK)
        try:
            s.gold = me.gold_count()                   # dead too: rule 0 shops [unverified whether it raises]
        except Exception:
            s.gold = 0
        if not s.alive:
            s.pos, s.near, s.near_t, s.stunned, s.hp, s.max_hp, s.bag = self.last_pos, set(), [], False, 0.0, 0.0, 0
            s.cost = f0 - fuel()
            return s
        s.pos = pos = me.position()
        self.last_pos = pos
        s.hp, s.max_hp, s.bag, s.stunned = me.health(), me.max_health(), me.gem_count(), False
        if not s.can_move and not s.recalling and not s.submitting:
            try:
                s.stunned = me.buffs().has_stun()
            except Exception:
                pass
        for c in vision.champions(Team.ENEMY):       # visible only [sdk]: no read raises
            s.enemies.append((c.position(), c.health(), c.gem_count(), c))
        for c in vision.champions(Team.ALLY):
            p = c.position()
            if p != pos:                              # not me
                s.allies.append((p, c.health(), c.gem_count(), c))
        hurt = s.hp < self.my_hp and not s.enemies     # hit with no enemy in sight: a camp in range hits me
        self.my_hp = s.hp
        s.near_t = nt = self.near(pos, SNAP_RANGE)
        s.near = hs = {h for _, h in nt}
        if isinstance(target, int) and target in self.camps:
            hs = hs | {target}
        for h in hs:
            row = []
            for c in self.camps[h]:
                if not c.is_visible():               # dead or out of vision: health() would raise [sdk]
                    row.append(None)
                    continue
                hp = c.health()
                k = int(c)
                old = self.last_hp.get(k)
                if old is not None and hp < old:      # took damage: awake (no engine flag [sdk])
                    self.awake_until[h] = rnd + AWAKE_ROUNDS
                self.last_hp[k] = hp
                self.last_hp_r[k] = rnd
                row.append(hp)
            s.camp_hp[h] = row
            if self.awake_until.get(h, -1) >= rnd - 1 or hurt:
                self.keep_awake(h, row, pos, rnd)
            if self.awake_until.get(h, -1) >= rnd:
                s.awake.add(h)
        s.cost = f0 - fuel()
        return s

    def keep_awake(self, h, row, pos, rnd):
        """A group sleeps only after AWAKE_ROUNDS with no champion in range [rules, measured A32]: an awake group
        (or one hitting me) with a live monster within CAMP_RANGE of me stays awake although its HP is not
        dropping (nobody hits it while I step out or recall: damage would cancel the recall [rules])."""
        for c, hp in zip(self.camps[h], row):
            if hp and c.spawn_position().chebyshev_distance(pos) <= CAMP_RANGE:
                self.awake_until[h] = rnd + AWAKE_ROUNDS
                return

    def hp_known(self, camp, mx, rnd):
        """Last-known HP of a camp not read this turn, else mx (no regen [measured A28]; stale after HP_STALE)."""
        k = int(camp)
        r = self.last_hp_r.get(k)
        return mx if r is None or rnd - r > HP_STALE else self.last_hp.get(k, mx)

    def gstate(self, h):
        """alive | dead (cleared, reward unclaimed) | respawning | - (unknown). ~27k out of vision."""
        try:
            st = self.groups[h].state()
        except Exception:
            return "-"
        if isinstance(st, game_map.CampGroupRewardAvailable):
            return "dead"
        if isinstance(st, game_map.CampGroupRespawning):
            return "respawning"
        return "alive"


_COMP = {}       # group handle -> rows (cached: static)
_CAMP_HP = {}    # CampType -> base health [sdk base_stats(); works out of vision]


def group_comp(w, h):
    """Rows (kind, max_hp, Str, x, y) of group h's camps, cached."""
    c = _COMP.get(h)
    if c is None:
        out = []
        for camp in w.camps.get(h, ()):
            k = int(camp.kind())
            if k not in _CAMP_HP:
                _CAMP_HP[k] = camp.base_stats().base_health
            p = camp.spawn_position()
            out.append((k, _CAMP_HP[k], CAMP_STR[k], p.x, p.y))
        c = _COMP[h] = tuple(out)
    return c
