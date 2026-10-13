"""What this champion knows: cached map facts, distance fields, camp memory, enemy sightings.

Fuel rules (docs/ARCHITECTURE.md): camp_groups() once (~1M), never vision.camp*(), static fields once,
one field from our own tile per turn, target fields cached.
"""
import cambc
from cambc import game_map, vision

import config as C

Team = cambc.Team
V = cambc.Vec2
FAR = 65535
# ChampionType numbers [sdk] -> names (champion_name() returns a plain int in game).
NAMES = ("RYTH", "VESPER_VALE", "VENDETTA", "CASSI", "ISSAC", "STELLAR", "PRISM", "MARCELLA", "WILLOW",
         "REN", "VARG", "TAVI")


def cname(u):
    t = int(u.champion_name())
    return NAMES[t] if 0 <= t < len(NAMES) else str(t)
DIRS = [V.NORTH, V.NORTH_EAST, V.EAST, V.SOUTH_EAST, V.SOUTH, V.SOUTH_WEST, V.WEST, V.NORTH_WEST]


def disk(center, r):
    b = cambc.Bitboard()
    b.draw_chebyshev(center, r)
    return b


def fget(field, pos):
    """Field distance, FAR when unreached or off the map."""
    try:
        v = field.get(pos)
    except cambc.Error:
        return FAR
    return v if 0 <= v < FAR else FAR


class Group:
    """One camp group plus what we remember about it."""

    def __init__(self, idx, g, blocked):
        self.idx = idx
        self.g = g
        self.camps = list(g.camps())
        self.tiles = g.spawn_tiles()
        self.spawns = [c.spawn_position() for c in self.camps]
        self.center = self.spawns[0]
        self.gems = g.gem_value()
        self.gold = g.gold_value()
        self.respawn = g.max_respawn_timer()
        self.str_each = [0.0] * len(self.camps)   # monster Strength, read when first seen
        self.hp = [None] * len(self.camps)        # last seen HP per monster; None = assume full
        self.max_hp = [None] * len(self.camps)
        self.state = "unknown"   # alive | reward | respawn | unknown
        self.respawn_at = 0      # round it is back, when state == respawn
        self.seen = -999         # round last seen
        self.hit_by_us = -999    # round we last hit it (it is awake for 2 rounds after) [rules]
        self.cleared_by_us = False
        self.enemy_near = -999   # round an enemy was last seen within 4 of it
        ring = cambc.Bitboard()
        for p in self.spawns:
            ring |= disk(p, 1)
        ring &= ~blocked
        self.ring = ring.positions()[:8]
        self.kind_known = False

    def hp_left(self, w):
        """Total HP of the monsters still standing, from memory (unknown = full by type)."""
        total = 0.0
        for i, c in enumerate(self.camps):
            if self.hp[i] is None:
                total += _FULL_HP.get(int(c.kind()), 1350)
            else:
                total += max(0.0, self.hp[i])
        return total

    def splash_neighbours(self):
        """Most standing monsters next to one standing monster: what Varg's splash adds per hit."""
        alive = [p for i, p in enumerate(self.spawns) if self.hp[i] is None or self.hp[i] > 0]
        return max((sum(1 for q in alive if q != p and q.chebyshev_distance(p) <= 1) for p in alive), default=0)

    def strength(self):
        """Damage per round the standing monsters can deal, assuming all hit one target (A2 open)."""
        s = 0.0
        for i, c in enumerate(self.camps):
            if self.hp[i] is None or self.hp[i] > 0:
                s += self.str_each[i] if self.kind_known else _STR.get(int(c.kind()), 20)
        return s

    def awake(self, rnd):
        return rnd - self.hit_by_us <= 2


# Per-monster values [rules] (GameRules camp table), used before a camp has been seen.
_FULL_HP = {}
_STR = {}


def _init_tables():
    T = cambc.CampType
    _FULL_HP.update({int(T.GEM_CLUSTER): 500, int(T.GOLD_CLUSTER): 500, int(T.WOLF): 1350,
                     int(T.ELK): 2400, int(T.MONOLITH): 20000})
    _STR.update({int(T.GEM_CLUSTER): 0, int(T.GOLD_CLUSTER): 0, int(T.WOLF): 20, int(T.ELK): 60,
                 int(T.MONOLITH): 200})


class Enemy:
    __slots__ = ("u", "pos", "hp", "max_hp", "gems", "strength", "range", "name", "channelling")


class World:
    def __init__(self):
        _init_tables()
        me = cambc.me()
        self.rnd = cambc.round_number()
        self.my_team = me.team()
        self.name = cname(me)
        self.static = (game_map.walls() | game_map.holes() | game_map.altars()
                       | game_map.spawn_region(Team.ENEMY))
        self.groups = []
        raw = list(game_map.camp_groups())      # ~1M fuel: the only call all game
        self.camp_tiles = cambc.Bitboard()
        for g in raw:
            self.camp_tiles |= g.spawn_tiles()
        self.blocked = self.static | self.camp_tiles
        for i, g in enumerate(raw):
            self.groups.append(Group(i, g, self.blocked))
        self.altars = game_map.altars().positions()
        self.spawn = game_map.spawn_region(Team.ALLY)
        self.enemy_spawn = game_map.spawn_region(Team.ENEMY)
        self.spawn_c = self.spawn.positions()[0]
        self.enemy_spawn_c = self.enemy_spawn.positions()[0]
        self.f_spawn = None
        self.f_altar = None
        self.f_me = None
        self.f_me_round = -1
        self.cache = {}           # key -> (field, goals); small LRU of target fields
        self.cache_order = []
        # Team facts, fixed on turn 1 while every ally is visible on spawn.
        allies = [a for a in cambc.champions(Team.ALLY) if a.is_visible()]
        allies.sort(key=lambda a: int(a.champion_name()))
        self.ally_types = [int(a.champion_name()) for a in allies]
        self.ally_str = [a.strength() for a in allies]
        self.slot = self.ally_types.index(int(me.champion_name())) if int(me.champion_name()) in self.ally_types else 0
        # Per-turn sensed state.
        self.enemies = []
        self.enemy_log = []       # (round, pos) of every enemy seen, for the hazard rate
        self.hp_prev = me.health()
        self.dmg_taken = 0.0
        self.gems_hist = []       # (round, banked team gems) for live income
        self.opening_claims = {}  # group idx -> ally slot (opening assignment)
        self.ready = False

    # ------------------------------------------------------------ fields
    def static_fields(self):
        """Spawn and altar fields: computed once (second turn, to spread the fuel)."""
        if self.f_spawn is None:
            self.f_spawn = cambc.DistanceField()
            self.f_spawn.compute(self.blocked & ~self.spawn, self.spawn, cambc.Bitboard(), FAR)
            return False
        if self.f_altar is None:
            goals = cambc.Bitboard()
            for a in self.altars:
                goals |= disk(a, cambc.constants.SUBMIT_GEMS_RANGE)
            goals &= ~self.blocked
            self.f_altar = cambc.DistanceField()
            self.f_altar.compute(self.blocked & ~goals, goals, cambc.Bitboard(), FAR)
            self.altar_goals = goals
            return False
        return True

    def field_to(self, key, goals):
        """Cached distance field towards a set of goal tiles."""
        hit = self.cache.get(key)
        if hit is not None:
            return hit[0]
        f = cambc.DistanceField()
        f.compute(self.blocked & ~goals, goals, cambc.Bitboard(), FAR)
        self.cache[key] = (f, goals)
        self.cache_order.append(key)
        if len(self.cache_order) > 6:
            old = self.cache_order.pop(0)
            self.cache.pop(old, None)
        return f

    def drop_field(self, key):
        if key in self.cache:
            self.cache.pop(key)
            self.cache_order.remove(key)

    def dist_me(self, positions):
        """Walking distance from us to the nearest of positions (field from our tile, once per turn)."""
        if self.f_me is None:
            return FAR
        return min((fget(self.f_me, p) for p in positions), default=FAR)

    # ------------------------------------------------------------ sensing
    def sense(self, me):
        self.rnd = cambc.round_number()
        self.me = me
        self.pos = me.position()
        hp = me.health()
        self.dmg_taken = max(0.0, self.hp_prev - hp) if me.is_alive() else 0.0
        self.hp_prev = hp
        self.hp = hp
        self.max_hp = me.max_health()
        self.gems = me.gem_count()
        self.banked = cambc.global_submitted_gems(Team.ALLY)
        self.enemy_banked = cambc.global_submitted_gems(Team.ENEMY)
        self.gems_hist.append((self.rnd, self.banked))
        while self.gems_hist and self.gems_hist[0][0] < self.rnd - C.INCOME_WINDOW:
            self.gems_hist.pop(0)
        if not me.is_alive():
            return
        # Enemies in vision.
        self.enemies = []
        for u in vision.champions(Team.ENEMY):
            e = Enemy()
            e.u = u
            e.pos = u.position()
            e.hp = u.health()
            e.max_hp = u.max_health()
            try:
                e.gems = u.gem_count()      # PROVISIONAL A18: the real bag
            except cambc.Error:
                e.gems = 0
            e.strength = u.strength()
            e.range = u.attack_range()
            e.name = cname(u)
            try:
                e.channelling = u.is_submitting_gems()
            except cambc.Error:
                e.channelling = False
            self.enemies.append(e)
            self.enemy_log.append((self.rnd, e.pos))
        while self.enemy_log and self.enemy_log[0][0] < self.rnd - max(C.H_WINDOW, 30):
            self.enemy_log.pop(0)
        # Camps near us: only groups whose tiles can be in vision (radius 8).
        vis = vision.visible_tiles()
        for gr in self.groups:
            if gr.center.chebyshev_distance(self.pos) > 10:
                continue
            if (vis & gr.tiles).is_empty():
                continue
            self.observe(gr)
            # Awake monsters stay awake while a champion is in range 3 [rules]: we are one.
            if gr.state == "alive" and gr.awake(self.rnd) and self.in_range_of(gr):
                gr.hit_by_us = self.rnd
            for e in self.enemies:
                if e.pos.chebyshev_distance(gr.center) <= 4:
                    gr.enemy_near = self.rnd
        # One field from our tile per turn: walking distance to everything (fuel ~285k worst case).
        if cambc.fuel_remaining() > 900_000:
            blocked = self.blocked.copy()
            blocked.set(self.pos, False)
            f = cambc.DistanceField()
            f.compute(blocked, disk(self.pos, 0), cambc.Bitboard(), FAR)
            self.f_me = f
            self.f_me_round = self.rnd

    def in_range_of(self, gr):
        return any(p.chebyshev_distance(self.pos) <= 3 and (gr.hp[i] is None or gr.hp[i] > 0)
                   for i, p in enumerate(gr.spawns))

    def observe(self, gr):
        try:
            s = gr.g.state()
        except cambc.Error:
            return
        gr.seen = self.rnd
        name = type(s).__name__
        if name.endswith("Alive"):
            if gr.state in ("respawn", "reward"):
                gr.hp = [None] * len(gr.camps)    # respawned at full health [rules]
                gr.cleared_by_us = False
            gr.state = "alive"
            for i, c in enumerate(gr.camps):
                try:
                    if c.is_visible():
                        gr.hp[i] = c.health()
                        gr.max_hp[i] = c.max_health()
                        gr.str_each[i] = c.strength()
                except cambc.Error:
                    pass
            gr.kind_known = all(m is not None for m in gr.max_hp)
        elif name.endswith("RewardAvailable"):
            gr.state = "reward"
            gr.hp = [0.0] * len(gr.camps)
        else:
            gr.state = "respawn"
            gr.respawn_at = self.rnd + getattr(s, "timer", gr.respawn)
            gr.hp = [None] * len(gr.camps)

    # ------------------------------------------------------------ derived numbers
    def income(self):
        """Team gems banked per round over the window, per champion (L4)."""
        if len(self.gems_hist) < 30:
            return C.INCOME_DEFAULT
        (r0, g0), (r1, g1) = self.gems_hist[0], self.gems_hist[-1]
        per_team = (g1 - g0) / max(1, r1 - r0)
        return max(0.2, per_team / max(1, len(self.ally_types)))

    def hazard(self):
        """L1: chance per round of losing the bag."""
        if not C.USE_HAZARD_BANK:
            return C.H_BASE
        n = sum(1 for r, p in self.enemy_log
                if r >= self.rnd - C.H_WINDOW and p.chebyshev_distance(self.pos) <= C.H_RADIUS)
        return C.H_BASE + C.H_PER_ENEMY * min(n, 3)

    def enemy_recent(self, radius, window):
        return any(r >= self.rnd - window and p.chebyshev_distance(self.pos) <= radius
                   for r, p in self.enemy_log)

    def dist_spawn(self, pos=None):
        return fget(self.f_spawn, pos or self.pos) if self.f_spawn else FAR

    def dist_altar(self, pos=None):
        return fget(self.f_altar, pos or self.pos) if self.f_altar else FAR

    def on_enemy_side(self, pos):
        return pos.chebyshev_distance(self.enemy_spawn_c) < pos.chebyshev_distance(self.spawn_c)


# ---------------------------------------------------------------- movement

def step_field(me, field, flee=False):
    """One move along a field (towards its roots, or away if flee). Returns True if we moved.

    Based on bots/probe Nav.step, with gotcha 7 handled: if our own tile is blocked in the field
    (standing on a cleared camp's spawn tile), fall back to the best reachable neighbour.
    """
    if not me.can_move():
        return False
    pos = me.position()
    occupied = vision.champion_tiles()
    here = fget(field, pos)
    scored = []
    for d in DIRS:
        q = pos + d
        v = fget(field, q)
        if v >= FAR or occupied.is_set(q):
            continue
        scored.append((-v if flee else v, q))
    scored.sort(key=lambda s: s[0])
    for v, q in scored:
        if here < FAR and ((not flee and v > here) or (flee and -v < here)):
            break      # never step to a worse tile (equal is fine: sidestep around a blocker)
        try:
            if me.move_absolute(q):
                return True
        except cambc.Error:
            continue
    return False
