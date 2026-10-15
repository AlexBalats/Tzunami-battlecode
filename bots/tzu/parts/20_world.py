"""L1 world model: static caches, the camp index from ONE camp_groups() call, goal bitboards, a
background job queue (index jobs, then distance fields), and a per-turn snapshot.

Keys of goals and fields:
    "spawn"      our spawn region
    "altar"      every altar's tribute ring (nearest altar)
    "a<i>"       altar i's tribute ring. When plan_ok, i is ALWAYS the plan's altar index (draft memory
                 §1.6, sorted by d_ours: a0 = our nearest altar), so cards' home_altar and group rows'
                 nearest altar name the same "a<i>"; altars the plan left out (> 18) follow in row-major
                 order. Without a plan, i is the row-major index in game_map.altars().positions() [sdk].
    <int h>      camp group h = int(group), the engine handle [sdk; measured: same for draft and champions]
    "espawn"     the enemy spawn region (its border: the region itself is blocked for us)
Index jobs (no field): "_blk" (camp tiles + the blocked mask; every field needs it), "_tiles"
(spawn tile -> group, used by the snapshot to find groups near us).

Fuel facts this layout rests on [measured 13 Oct, runs/prof, expanse]: an empty Python loop turn
~1.3k, a call ~2k, a Bitboard op 4-6k, positions() ~8k, me.state() ~5k, other champion reads ~3k,
camp.health() ~3k visible / ~17k when it raises, CampGroup.state() ~27k out of vision,
vision.champions(team) ~17k, a field ~280k at 80x80, field.get ~2.3k, next_move_from ~3k.
Import of the one-file bot is not free either: ~600 fuel per line of code [measured: 2,100 lines of
small defs cost 1.27M; comments cost nothing], so the first play turn starts with only ~2.2-3.1M.
Hence the first turn: a cheap opening step, then setup stages 1-2 only if they fit (World.setup);
the camp index, blocked mask and fields come after, as jobs.
"""

SNAP_RANGE = 4      # read camp HP only for groups within this of us (+ the target group) [INVARIANTS §0]
NEAR_DEAD = 3       # a dead group within 3 steps triggers the capture interrupt (I4) [INVARIANTS event 9]
AWAKE_ROUNDS = 2    # a camp sleeps 2 rounds after nobody is in range [measured A32]
HP_STALE = 40       # last-known camp HP is trusted this many rounds: no regen [measured A28], and a dead camp
                    # needs capture (5) + respawn (>= 40) before it is back at full HP [rules]
CAMP_RANGE = 3      # every monster's attack range [measured A31]
CAMP_STR = (20, 60, 0, 0, 200)   # Strength by CampType WOLF, ELK, GEM, GOLD, MONOLITH [rules]
INDEX_JOBS = ("_blk", "_tiles")
BG_MARGIN = 100_000         # background also leaves room for the t line and event lines after it
JOB_CAP = 1_200_000         # no job estimate above this (cost_of): the queue must never stall behind one job
SETUP1_FUEL = 1_300_000      # first turn: run stage 1 (camp_groups ~0.8-1M + anchors) only above this
SETUP2_FUEL = 1_300_000      # first turn: run stage 2 (sort + plan decode up to ~1M) only above this


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
    """What this champion knows this turn. Filled by World.snapshot(); nothing here is a decision."""
    __slots__ = ("rnd", "st", "alive", "can_move", "pos", "hp", "max_hp", "bag", "gold",
                 "enemies", "camp_hp", "near", "near_t", "awake", "mem", "cost", "_occ")

    def occupied(self):
        """Tiles of visible champions (both teams) plus visible teleport reservations, which are not
        walkable [sdk vision.teleport_tiles]. Read lazily, only on Nav's slow path."""
        if self._occ is None:
            self._occ = vision.champion_tiles() | vision.teleport_tiles()
        return self._occ


class World:
    """Facts only, no decisions."""

    def __init__(self):
        """Cheap part only (~50k): the first play turn acts before the expensive setup stages."""
        self.me = me = cambc.me()
        self.ctype = int(me.champion_name())
        self.W, self.H = game_map.width(), game_map.height()
        self.spawn = game_map.spawn_region(Team.ALLY)
        self.espawn = game_map.spawn_region(Team.ENEMY)
        self.altar_pos = game_map.altars().positions()
        self.last_pos = me.position()
        self.snap = None       # this turn's Snap, set by the play loop
        self.mem = None        # SharedMem (10_mem.py), created by the step-2 hook
        self.groups = {}       # handle -> CampGroup
        self.camps = {}        # handle -> tuple of Camp (cached objects: health() is cheap [sdk])
        self.anchor = {}       # key -> one tile of the goal's object (greedy fallback, nearest-first)
        self.order = []        # groups nearest-first from the start tile (Chebyshev)
        self.queue = []
        self.total = 0
        self.fields = {}
        self.goals = {}
        self.blocked = self.free = None
        self.tile_group = None   # Vec2 spawn tile -> group handle ("_tiles" job)
        self.camp_tiles = None
        self.scratch = Bitboard()
        self.est = {}
        # Awake inference (no engine flag [sdk]): last HP per camp handle, round until awake per group.
        self.last_hp = {}
        self.last_hp_r = {}      # camp handle -> round its HP was last read (hp_known)
        self.awake_until = {}
        self.plan = None
        self.plan_ok = False
        self.stage = 0           # 0 nothing, 1 camp index, 2 ready
        self.waited = False      # the last setup() call ran no stage (the next one forces one)
        self.init_fuel = 0

    def setup(self, first_turn):
        """The expensive setup in two stages, each run only if it fits the turn; a stage that didn't fit
        runs anyway on the next turn after the first (nothing can act without it), so setup never takes
        more than three turns and never runs both stages into a suspension. Returns True when ready.
        Stage 1: the camp index, the ONLY camp_groups() call of this instance (~0.8-1M [measured]).
        Stage 2: start order, job queue, estimates, the draft plan (decode 0.27-0.96M [measured])."""
        f0 = fuel()
        force = not first_turn and self.waited
        ran = False
        if self.stage == 0 and (force or f0 - RESERVE > SETUP1_FUEL):
            for g in game_map.camp_groups():
                h = int(g)
                self.groups[h] = g
                cs = self.camps[h] = g.camps()
                self.anchor[h] = cs[0].spawn_position()
            self.stage = 1
            ran = True
        if self.stage == 1 and ((force and not ran) or fuel() - RESERVE > SETUP2_FUEL):
            self.setup2()
            self.stage = 2
            ran = True
        self.waited = not ran
        self.init_fuel += f0 - fuel()
        return self.stage == 2

    def setup2(self):
        pos = self.last_pos
        # The draft plan, decoded once (10_mem.py). No decoder or a bad buffer -> no-plan mode.
        dec = globals().get("decode_plan")
        if dec is not None:
            try:
                self.plan = dec(bytes(cambc.draft_memory))
            except Exception as e:
                trace("mem", f"decode_fail {err_text(e)}")
                self.plan = None
        self.plan_ok = bool(getattr(self.plan, "ok", False))
        if self.plan_ok:
            self.altar_pos = self.plan_altar_order(self.altar_pos)
        self.anchor["spawn"] = self.spawn.positions()[0]
        self.anchor["espawn"] = self.espawn.positions()[0]
        for i, a in enumerate(self.altar_pos):
            self.anchor[f"a{i}"] = a
        if self.altar_pos:
            self.anchor["altar"] = self.altar_pos[0]
        # Job queue: the index first (both index jobs: work_index runs them during boot), spawn, altars nearest-first, groups nearest-first, enemy spawn.
        d = pos.chebyshev_distance
        alt = sorted(range(len(self.altar_pos)), key=lambda i: d(self.altar_pos[i]))
        self.order = grp = sorted(self.groups, key=lambda h: d(self.anchor[h]))
        self.queue = ["_blk", "_tiles", "spawn", "altar"] + [f"a{i}" for i in alt] + grp + ["espawn"]
        self.total = len(self.queue)
        # Self-correcting cost estimates per job kind. A field: 141k (90x30) to 293k (80x80) [measured]
        # plus its goal ring; start high. Index jobs: per group / per camp costs from the profile above.
        n = len(self.groups)
        self.est = {"field": self.W * self.H * 60 + 40_000, "_blk": 6_000 * n + 80_000,   # measured 182k at 42 groups
                    "_tiles": 40_000 * n + 60_000}

    def plan_altar_order(self, ps):
        """Altar tiles re-indexed so that index i is the plan's altar i (see "a<i>" above)."""
        at = {(p.x, p.y): p for p in ps}
        out = []
        for a in self.plan.altars:
            p = at.pop((a.x, a.y), None)
            if p is None:                    # the plan names a tile that is not an altar: keep row-major
                trace("mem", f"altar_mismatch {a.i} {a.x},{a.y}")
                return list(ps)
            out.append(p)
        out.extend(p for p in ps if (p.x, p.y) in at)
        return out

    # ------------------------------------------------------------------ index jobs
    def job_blk(self):
        """Camp spawn tiles and the blocked mask: walls, holes, altars, the enemy spawn [sdk
        move_towards blocks it], camp spawn tiles (camps stand there; standing on a cleared one
        delays its respawn [rules], so we never route over them, LESSONS §3)."""
        ct = Bitboard()
        for g in self.groups.values():
            ct |= g.spawn_tiles()
        self.camp_tiles = ct
        self.blocked = game_map.walls() | game_map.holes() | game_map.altars() | self.espawn | ct
        self.free = ~self.blocked

    def job_tiles(self):
        tg = {}
        for h, cs in self.camps.items():
            for c in cs:
                tg[c.spawn_position()] = h
        self.tile_group = tg

    def goal(self, key):
        """The goal bitboard of key, built on first use (needs "_blk")."""
        b = self.goals.get(key)
        if b is not None:
            return b
        free = self.free
        if key == "spawn":
            b = self.spawn & free
        elif key == "espawn":
            b = self.espawn
        elif key == "altar":
            b = Bitboard()
            rng = cambc.constants.SUBMIT_GEMS_RANGE       # tribute range [sdk constants]
            for a in self.altar_pos:
                b.draw_chebyshev(a, rng)
            b &= free
        elif isinstance(key, str) and key[0] == "c":       # "c<x>_<y>": melee ring of one camp (L5 Reach)
            x, y = key[1:].split("_")
            b = disk(V(int(x), int(y)), 1) & free
        elif isinstance(key, str):                         # "a<i>"
            b = disk(self.altar_pos[int(key[1:])], cambc.constants.SUBMIT_GEMS_RANGE) & free
        else:                                              # a group: stand next to a camp (melee 1)
            b = Bitboard()
            for c in self.camps[key]:
                b.draw_chebyshev(c.spawn_position(), 1)
            b &= free
        self.goals[key] = b
        return b

    # ------------------------------------------------------------------ jobs and fields
    def run(self, key):
        """Run one job now (index job or field); self-correct its kind's estimate."""
        kind = key if key in INDEX_JOBS else "field"
        if kind == "field" and self.blocked is None:
            self.run("_blk")
        f0, r0 = fuel(), cambc.round_number()
        if kind == "_blk":
            self.job_blk()
        elif kind == "_tiles":
            self.job_tiles()
        else:
            roots = self.goal(key)
            f = DistanceField()
            f.compute(self.blocked & ~roots, roots, self.scratch, FAR)
            self.fields[key] = f
        cost = spent(f0, r0)
        try:
            self.queue.remove(key)
        except ValueError:
            pass
        est = self.est[kind]
        if cost > est * 1.5:
            trace("fuel", f"over est={est} job={key} cost={cost}")
        target = int(cost * 1.3)     # jump up at once, decay slowly towards 1.3x the last actual
        self.est[kind] = target if target > est else (3 * est + target) // 4
        return cost

    def cost_of(self, key):
        """Estimated fuel of a job, capped at JOB_CAP: a larger estimate could never fit a turn with any other
        work in it, and the queue would stall behind it (integration 13 Oct: lanes' _tiles at 1.74M for 42
        groups blocked a busy champion's fields for 80+ rounds)."""
        if key in INDEX_JOBS:
            return min(self.est[key], JOB_CAP)
        c = self.est["field"]
        if self.blocked is None:
            c += self.est["_blk"]
        return min(c, JOB_CAP)

    def ensure(self, key):
        """Compute key's field now if it is missing and fits the turn under the reserve."""
        if key in self.fields:
            return True
        if fuel() - RESERVE > self.cost_of(key):
            self.run(key)
            return True
        return False

    def want(self, key):
        """Move key's field to the front of the queue (after a pending "_blk")."""
        if key in self.fields:
            return
        try:
            self.queue.remove(key)
        except ValueError:
            return
        self.queue.insert(1 if self.queue and self.queue[0] == "_blk" else 0, key)

    def work(self):
        """Background (skeleton step 8): jobs until the next one might not fit. Returns (jobs, fuel)."""
        n, f0 = 0, fuel()
        q = self.queue
        while q and fuel() - RESERVE - BG_MARGIN > self.cost_of(q[0]):
            self.run(q[0])
            n += 1
        return n, f0 - fuel()

    def work_index(self):
        """Boot: the index jobs at the queue head (camp tiles, tile -> group) before the lazy parts load; the
        snapshot's near-group test needs them. Same guard as work()."""
        q = self.queue
        while q and q[0] in INDEX_JOBS and fuel() - RESERVE - BG_MARGIN > self.cost_of(q[0]):
            self.run(q[0])

    def done(self):
        return self.total - len(self.queue)

    def dist(self, key, pos):
        """Walking distance from pos to the goal tiles of key; None while the field isn't computed,
        FAR when unreachable (a value, not an error: some altars are unreachable on foot [measured A13])."""
        f = self.fields.get(key)
        return None if f is None else fget(f, pos)

    def step(self, key, pos):
        """First optimal step (a direction delta) from pos towards key, or None [sdk next_move_from]."""
        f = self.fields.get(key)
        if f is None:
            return None
        try:
            return f.next_move_from(pos)
        except Exception:
            return None

    # ------------------------------------------------------------------ snapshot
    def near(self, pos, r):
        """[(spawn tile, group)] of camps within Chebyshev r of pos: one mask AND, no per-group loop."""
        if self.tile_group is None:
            return []
        b = disk(pos, r)
        b &= self.camp_tiles
        if b.is_empty():
            return []
        tg = self.tile_group
        return [(p, tg[p]) for p in b.positions()]

    def snapshot(self, rnd, target=None):
        """Skeleton step 1 (< 150k). One state() read; camp HP only for near groups + the target."""
        f0 = fuel()
        s = Snap()
        s.rnd, s.mem, s._occ = rnd, 0, None
        s.enemies, s.camp_hp, s.awake = [], {}, set()
        me = self.me
        s.st = st = int(me.state())
        s.alive = bool(st & ST_ALIVE)
        if not s.alive:
            s.pos, s.can_move, s.near, s.near_t = self.last_pos, False, (), ()
            s.hp = s.max_hp = 0.0
            s.bag = s.gold = 0
            s.cost = f0 - fuel()
            return s
        s.can_move = bool(st & ST_CAN_MOVE)
        s.pos = pos = me.position()
        self.last_pos = pos
        s.hp = me.health()
        s.max_hp = me.max_health()
        s.bag = me.gem_count()
        s.gold = me.gold_count()
        # vision.champions(team) returns visible champions only [sdk], so no read can raise
        # on an invisible champion (LESSONS §3).
        for c in vision.champions(Team.ENEMY):
            s.enemies.append((c.position(), c.health(), c.gem_count(), c))
        s.near_t = nt = self.near(pos, SNAP_RANGE)
        s.near = hs = {h for _, h in nt}
        if isinstance(target, int) and target in self.camps:
            hs = hs | {target}
        for h in hs:
            row = []
            for c in self.camps[h]:
                if not c.is_visible():        # dead or out of vision: health() would raise [sdk]
                    row.append(None)
                    continue
                hp = c.health()
                k = int(c)
                old = self.last_hp.get(k)
                if old is not None and hp < old:
                    self.awake_until[h] = rnd + AWAKE_ROUNDS
                self.last_hp[k] = hp
                self.last_hp_r[k] = rnd
                row.append(hp)
            s.camp_hp[h] = row
            if self.awake_until.get(h, -1) >= rnd:
                s.awake.add(h)
        s.cost = f0 - fuel()
        return s

    def hp_known(self, camp, mx, rnd):
        """Last-known HP of a camp not read this turn (stale snapshot), else mx. Damaged camps don't
        regenerate [measured A28]; after HP_STALE rounds it may have died and respawned at full HP."""
        k = int(camp)
        r = self.last_hp_r.get(k)
        if r is None or rnd - r > HP_STALE:
            return mx
        return self.last_hp.get(k, mx)

    # ------------------------------------------------------------------ t-line facts
    def facts(self, s, p):
        """inc, on_spawn, gstate, dead at the final position p (INVARIANTS I4, I10, I12)."""
        inc, others = 0, None
        for h in s.awake:                     # awake monsters with p in range hit us next round, unless another
            for c in self.camps[h]:           # champion is strictly nearer (they hit the nearest [rules])
                sp = c.spawn_position()
                d = sp.chebyshev_distance(p)
                if d <= CAMP_RANGE and c.is_visible():
                    if others is None:
                        others = vision.champion_tiles()
                        others.set(s.pos, False)
                        others.set(p, False)
                    if d > 0 and not (disk(sp, d - 1) & others).is_empty():
                        continue
                    inc += CAMP_STR[c.kind()]
        on, gst, dead = "-", "-", []
        tg = self.tile_group
        if tg is not None and self.camp_tiles.is_set(p):
            h = tg.get(p)
            if h is not None:
                on, gst = f"g{h}", self.gstate(h)
        # Dead = no camp of a near group visible while its tiles are in vision. state() costs ~27k,
        # so it is asked only for near groups (within 3 of p) whose camps all read None this turn.
        for h in {h for t, h in s.near_t if t.chebyshev_distance(p) <= NEAR_DEAD}:
            row = s.camp_hp.get(h)
            if row is not None and all(x is None for x in row) and self.gstate(h) == "dead":
                dead.append(f"g{h}")         # one group-id format everywhere (INVARIANTS §6)
        return inc, on, gst, ",".join(dead) or "-"

    def gstate(self, h):
        try:
            st = self.groups[h].state()
        except Exception:
            return "-"
        if isinstance(st, game_map.CampGroupRewardAvailable):
            return "dead"
        if isinstance(st, game_map.CampGroupRespawning):
            return "respawning"
        return "alive"
