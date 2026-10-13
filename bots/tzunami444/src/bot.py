"""tzunami444 v1: farm the best camp group we can clear, bank at G*, never die with gems.

One module on purpose: the first import of any module costs ~1.2M fuel (docs/ARCHITECTURE.md).
Turn pipeline (ARCHITECTURE.md): sense -> channels -> shop -> survive -> fight -> bank -> farm.
"""
import cambc
from cambc import game_map, vision, Team, CampType

import config as C

ALLY, ENEMY = Team.ALLY, Team.ENEMY
K = cambc.constants
GAlive, GReward = game_map.CampGroupAlive, game_map.CampGroupRewardAvailable

# Camp design stats [rules] (GameRules.md -> Pick your target): max HP, strength.
CAMP_STATS = {
    CampType.WOLF: (1350, 20),
    CampType.ELK: (2400, 60),
    CampType.GEM_CLUSTER: (500, 0),
    CampType.GOLD_CLUSTER: (500, 0),
    CampType.MONOLITH: (20000, 200),
}


def cheb(a, b):
    return a.chebyshev_distance(b)


# ---------------------------------------------------------------- world (cached once, ARCHITECTURE.md -> Compute)

class Field:
    """A distance field to some root tiles, decoded into a Python buffer so lookups cost no host calls."""

    def __init__(self, roots, blocked):
        self.roots = roots
        self.blocked = blocked & ~roots
        self.f = cambc.DistanceField()
        self.f.compute(self.blocked, roots, cambc.Bitboard(), 65535)
        # A typed buffer (u16 on 2.1.5, len == W*H) [measured]: index it directly, don't cast to bytes.
        self.d = memoryview(self.f.export_linear_buffer())
        if self.d.itemsize == 1:
            self.d = self.d.cast({1: "B", 2: "H", 4: "I"}[len(self.d) // (W * H)])

    def at(self, x, y):
        return self.d[y * W + x]

    def near(self, p):
        """Distance to stand next to p (p itself may be blocked, e.g. a camp tile)."""
        best = 65535
        for y in range(max(0, p.y - 1), min(H, p.y + 2)):
            for x in range(max(0, p.x - 1), min(W, p.x + 2)):
                v = self.d[y * W + x]
                if v < best:
                    best = v
        return best + 1 if best < C.UNREACHED else 65535


class Group:
    __slots__ = ("i", "g", "camps", "tiles", "cells", "center", "hp", "maxhp", "str",
                 "gems", "gold", "respawn", "state", "back_at", "alt", "home", "nav")

    def __init__(self, i, g):
        self.i, self.g = i, g
        self.camps = g.camps()
        self.cells = [c.spawn_position() for c in self.camps]
        self.tiles = g.spawn_tiles()
        self.center = self.cells[len(self.cells) // 2]
        stats = [CAMP_STATS.get(c.kind(), (2000, 50)) for c in self.camps]
        self.maxhp = [s[0] for s in stats]
        self.hp = list(self.maxhp)          # last-known HP; damaged camps don't regenerate [measured A28]
        self.str = [s[1] for s in stats]
        self.gems, self.gold = g.gem_value(), g.gold_value()
        self.respawn = g.max_respawn_timer()
        self.state = "alive"                # alive | reward | resp (all groups start alive)
        self.back_at = 0                    # round a respawning group comes back
        self.alt = self.home = 65535
        self.nav = None


W = H = 0
STATIC = None       # walls, holes, altars, enemy spawn: never standable
CAMPTILES = None    # every camp spawn tile (live camps occupy them)
GROUPS = []
BY_TILE = {}        # (x, y) -> (group index, camp index)
ALTARS = []
ALTAR_FIELD = SPAWN_FIELD = None
ALTAR_HELD = {}     # altar index -> round until which we bank elsewhere (enemies held it)
ALTAR_FIELDS = {}   # altar index -> Field to that altar alone, built on first need
SPAWN = None
RANK = {}           # ChampionType -> our pick index: unit ids follow draft pick order [measured A2]
MONSTER_RANGE = C.SAFE_RANGE - 1    # every monster hits within Chebyshev 3 [rules]


def init_rank():
    """Monsters break distance ties by lowest unit id, which is pick order [measured A2]; we pick C.PICKS in order."""
    types = {}
    for t in range(32):
        try:
            types[cambc.ChampionType.to_string(t).rsplit(".", 1)[-1]] = t
        except Exception:
            break
    for i, p in enumerate(C.PICKS):
        for part in cambc.ChampionDraft.to_string(int(p)).rsplit(".", 1)[-1].split("_AND_"):
            if part in types:
                RANK.setdefault(types[part], i)


def init_world():
    global W, H, STATIC, CAMPTILES, ALTAR_FIELD, SPAWN_FIELD, SPAWN
    W, H = game_map.width(), game_map.height()
    SPAWN = game_map.spawn_region(ALLY)
    STATIC = game_map.walls() | game_map.holes() | game_map.altars() | game_map.spawn_region(ENEMY)
    CAMPTILES = cambc.Bitboard()
    for i, g in enumerate(game_map.camp_groups()):     # ~0.74M fuel: once [measured A17]
        grp = Group(i, g)
        GROUPS.append(grp)
        CAMPTILES |= grp.tiles
        for j, p in enumerate(grp.cells):
            BY_TILE[(p.x, p.y)] = (i, j)
    ALTARS.extend(game_map.altars().positions())
    bank = cambc.Bitboard()
    for a in ALTARS:
        bank.draw_chebyshev(a, K.SUBMIT_GEMS_RANGE)
    blocked = STATIC | CAMPTILES
    ALTAR_FIELD = Field(bank & ~blocked, blocked)
    SPAWN_FIELD = Field(SPAWN, blocked)
    for grp in GROUPS:
        grp.alt = min(ALTAR_FIELD.near(p) for p in grp.cells)
        grp.home = min(SPAWN_FIELD.near(p) for p in grp.cells)


def group_nav(grp):
    if grp.nav is None:
        grp.nav = Field(grp.tiles, STATIC | CAMPTILES)
    return grp.nav


# ---------------------------------------------------------------- per-champion memory

S = {
    "target": None,     # Group we farm
    "mode": "farm",     # farm | heal
    "bought": 0,        # items of C.BUILD bought so far
    "slot": None,       # our byte in shared memory (camp claims)
    "hit_round": -99,   # last round we damaged a camp
    "types": [],        # our team's champion types, sorted (slot order)
    "skip": (-1, 0),    # (group, until round): left for an ally to capture (R7)
    "pull_since": None, # round we started waiting at a sleeping group for the tank
    "contest": (-1, 0), # (group, since round): an enemy has been on its spawn tiles while we capture
}


def my_slot(me):
    """Rank of our champion type among our team's types: decided on turn 1, while everyone is on spawn."""
    mine = int(me.champion_name())
    types = {mine}
    for a in cambc.champions(ALLY):
        if a.is_visible():
            types.add(int(a.champion_name()))
    S["types"] = sorted(types)      # an ally's slot is its type's rank here
    rank = S["types"].index(mine)
    return rank if rank < K.SHARED_MEMORY_BYTES else None


def claim_of(unit):
    """Group index an ally claims in shared memory, or None."""
    t = int(unit.champion_name())
    if t not in S["types"]:
        return None
    k = S["types"].index(t)
    if k >= K.SHARED_MEMORY_BYTES:
        return None
    v = cambc.shared_memory[k]
    return v - 1 if v else None


def claims():
    """Groups our allies are heading to (byte per champion: group index + 1)."""
    out = set()
    for k in range(K.SHARED_MEMORY_BYTES):
        if k != S["slot"]:
            v = cambc.shared_memory[k]
            if v:
                out.add(v - 1)
    return out


def claim(grp):
    if S["slot"] is not None:
        cambc.shared_memory[S["slot"]] = 0 if grp is None or grp.i > 254 else grp.i + 1


# ---------------------------------------------------------------- sensing

def sense(me, now):
    """Update last-known camp HP and group states from what we see (vision.camps() ~31k fuel)."""
    seen = set()
    for camp in vision.camps():
        key = BY_TILE.get((camp.spawn_position().x, camp.spawn_position().y))
        if key is None:
            continue
        grp = GROUPS[key[0]]
        grp.hp[key[1]] = camp.health()
        seen.add(key)
        if grp.state != "alive":
            grp.state = "alive"
            grp.hp = list(grp.maxhp)
            grp.hp[key[1]] = camp.health()
    pos = me.position()
    visible = None
    for grp in GROUPS:
        if cheb(grp.center, pos) > 10:
            continue
        if visible is None:
            visible = me.visible_tiles()
        if (grp.tiles & visible).is_empty():
            continue
        try:
            st = grp.g.state()
        except cambc.Error:
            continue
        if isinstance(st, GAlive):
            # Camps whose tile we see but which aren't listed are dead.
            for j, p in enumerate(grp.cells):
                if (grp.i, j) not in seen and visible.is_set(p):
                    grp.hp[j] = 0
            grp.state = "alive"
        elif isinstance(st, GReward):
            grp.state = "reward"
            grp.hp = [0] * len(grp.hp)
        else:
            grp.state = "resp"
            grp.back_at = now + st.timer
            grp.hp = list(grp.maxhp)
    for grp in GROUPS:
        if grp.state == "resp" and now >= grp.back_at:
            grp.state = "alive"
            grp.hp = list(grp.maxhp)


# ---------------------------------------------------------------- estimates

def camp_dps(me):
    """Damage per round on camps: basic attack, plus resets and damage spells every 8 rounds [rules]."""
    s = me.strength()
    dps = s
    for ab in me.abilities():
        try:
            if ab.is_attack_reset():
                dps += s / 8
            elif ab.is_damage() and (ab.can_target_camps() or ab.can_target_ground()):
                dps += ab.damage_amount() / 8
        except cambc.Error:
            pass
    return max(dps, 1.0)


def clear_cost(grp, dps):
    """(rounds to clear, damage taken) for one champion. Kill hitters first (P3: shortest exposure)."""
    if C.GROUP_TAKE:
        # Smith's rule: most strength per HP first minimises total damage taken; clusters last.
        order = sorted(range(len(grp.hp)), key=lambda j: (grp.str[j] <= 0, -grp.str[j] / max(grp.hp[j], 1)))
    else:
        order = sorted(range(len(grp.hp)), key=lambda j: (-grp.str[j], grp.hp[j]))
    t = dmg = 0.0
    for j in order:
        if grp.hp[j] <= 0:
            continue
        t += grp.hp[j] / dps
        dmg += grp.str[j] * t      # this monster hits every round until it dies [rules]
    return t, dmg * 1.1


def score_group(grp, me, dist, dps, hp, maxhp, now):
    """Gems per round for taking this group now, or None if we shouldn't (P3, P13)."""
    if dist >= C.UNREACHED:
        return None
    wait = 0
    if grp.state == "resp":
        wait = max(0, grp.back_at - (now + dist))
        if wait > C.WAIT_RESPAWN_MAX:
            return None
    if grp.state == "reward":
        t, dmg = 0.0, 0.0       # P13: someone cleared it; free to capture
    elif grp.state == "resp":
        t, dmg = clear_cost_full(grp, dps)
    else:
        t, dmg = clear_cost(grp, dps)
    budget = hp - C.HP_RESERVE * maxhp
    per_trip = (1 - C.HP_RESERVE) * maxhp
    trips = 0
    if dmg > budget:
        trips = int((dmg - budget) // per_trip) + 1
        if trips > C.MAX_TRIPS:
            return None
    trip_time = 2 * min(grp.home, 60) + K.RECALL_TIME + 2
    bank_share = grp.alt * grp.gems / max(C.BANK_AT, grp.gems) if grp.alt < C.UNREACHED else 0
    rounds = dist + wait + t + K.CAPTURE_TIME + trips * trip_time + bank_share + 1
    if now + rounds + min(grp.alt, 200) + C.END_MARGIN > K.MAX_ROUNDS:
        return None
    if grp.alt >= C.UNREACHED:
        return None             # gems we could never bank
    return (grp.gems + C.GOLD_VALUE * grp.gold) / rounds


def clear_cost_full(grp, dps):
    hp = grp.hp
    grp.hp = list(grp.maxhp)
    try:
        return clear_cost(grp, dps)
    finally:
        grp.hp = hp


def choose_target(me, now):
    """Pick the group with the best gems per round (ARCHITECTURE.md -> Score goals)."""
    pos = me.position()
    blocked = STATIC | CAMPTILES
    blocked.set(pos, False)
    root = cambc.Bitboard()
    root.set(pos)
    here = Field(root, blocked)     # one BFS (~0.3M on 80x80) per choice, not per turn
    dps, hp, maxhp = camp_dps(me), me.health(), me.max_health()
    taken = claims()
    best, best_score = None, 0.0
    skip = S["skip"][0] if now < S["skip"][1] else -1
    for shared in (False, True):
        for grp in GROUPS:
            if (grp.i in taken) != shared or grp.i == skip:
                continue
            s = score_group(grp, me, min(here.near(p) for p in grp.cells), dps, hp, maxhp, now)
            if s is None:
                continue
            if shared:
                s *= 0.5            # the reward is split with the ally already there [rules]
            if s > best_score:
                best, best_score = grp, s
        if best is not None:
            break
    return best


# ---------------------------------------------------------------- movement

def step_field(me, field):
    """One move down a field; sidestep units. Returns True if we moved."""
    if not me.can_move():
        return False
    pos = me.position()
    if field.roots.is_set(pos):
        return False
    occupied = vision.champion_tiles() | vision.camp_tiles()
    moves = list(field.f.next_moves_from(pos))
    if not moves:
        # Standing on a tile the field treats as blocked (a camp tile after a capture): step off it.
        here = field.at(pos.x, pos.y)
        cands = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    q = cambc.Vec2(pos.x + dx, pos.y + dy)
                    if 0 <= q.x < W and 0 <= q.y < H and not field.blocked.is_set(q):
                        cands.append((field.at(q.x, q.y), cambc.Vec2(dx, dy)))
        cands.sort(key=lambda c: c[0])
        moves = [d for v, d in cands if v < C.UNREACHED or here >= C.UNREACHED]
    for delta in moves:
        dest = pos + delta
        if occupied.is_set(dest):
            continue
        try:
            if me.move_absolute(dest):
                return True
        except cambc.Error:
            continue
    if C.GROUP_TAKE:
        # Every best move is taken (bodies queue single file at a camp): sidestep at the same distance.
        here = field.at(pos.x, pos.y)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                x, y = pos.x + dx, pos.y + dy
                if not (0 <= x < W and 0 <= y < H) or field.at(x, y) != here:
                    continue
                q = cambc.Vec2(x, y)
                if field.blocked.is_set(q) or occupied.is_set(q):
                    continue
                try:
                    if me.move_absolute(q):
                        return True
                except cambc.Error:
                    pass
    return False


def step_off(me, field):
    """Step to the free neighbour nearest the field's roots without standing on one (roots are 0)."""
    if not me.can_move():
        return False
    pos = me.position()
    occupied = vision.champion_tiles() | vision.camp_tiles()
    best, best_d = None, 65535
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            x, y = pos.x + dx, pos.y + dy
            if not (0 <= x < W and 0 <= y < H) or (dx == 0 and dy == 0):
                continue
            d = field.at(x, y)
            q = cambc.Vec2(x, y)
            if 0 < d < best_d and not field.blocked.is_set(q) and not occupied.is_set(q):
                best, best_d = q, d
    if best is None:
        return False
    try:
        return me.move_absolute(best)
    except cambc.Error:
        return False


def step_away(me, threats):
    """Move to the free neighbour farthest from every threat; ties go towards spawn."""
    if not me.can_move() or not threats:
        return False
    pos = me.position()
    occupied = vision.champion_tiles() | vision.camp_tiles()
    best, best_key = None, None
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            q = cambc.Vec2(pos.x + dx, pos.y + dy)
            if not (0 <= q.x < W and 0 <= q.y < H):
                continue
            if (dx or dy) and (STATIC.is_set(q) or occupied.is_set(q)):
                continue
            key = (min(cheb(q, t) for t in threats), -SPAWN_FIELD.at(q.x, q.y))
            if best_key is None or key > best_key:
                best, best_key = q, key
    if best is None or best == pos:
        return False
    try:
        return me.move_absolute(best)
    except cambc.Error:
        return False


# ---------------------------------------------------------------- combat

def cast_best(me, target, is_camp):
    """Use the ability worth the most damage on target this turn (one cast per turn [rules])."""
    if not me.can_cast():
        return False
    best, best_val, how = None, 0.0, None
    tpos = target.position()
    for ab in me.abilities():
        try:
            if not ab.is_ready():
                continue
            if ab.is_attack_reset():
                val = me.strength() if not me.can_attack() else 0.0
                use = None
            elif ab.is_shield():
                continue
            elif ab.is_damage():
                if not ab.valid_tiles().is_set(tpos):
                    continue
                if ab.can_target_ground() and not (ab.can_target_camps() or ab.can_target_enemies()):
                    use = tpos
                elif (is_camp and ab.can_target_camps()) or (not is_camp and ab.can_target_enemies()):
                    use = target
                elif ab.can_target_ground():
                    use = tpos
                else:
                    continue
                val = ab.damage_amount(None if is_camp else target)
            elif ab.is_cc() and not is_camp and ab.can_target_enemies():
                if not ab.valid_tiles().is_set(tpos):
                    continue
                val, use = 1.0, target      # a stun with no damage: better than nothing on a champion
            else:
                continue
        except cambc.Error:
            continue
        if val > best_val:
            best, best_val, how = ab, val, use
    if best is None:
        return False
    try:
        return best.use(how) if how is not None else best.use()
    except cambc.Error:
        return False


def strike(me, target, is_camp):
    """Basic attack, best spell, and a second attack if the spell was a reset."""
    hit = False
    if me.can_attack() and cheb(me.position(), target.position()) <= me.attack_range():
        try:
            me.attack(target)
            hit = True
        except cambc.Error:
            pass
    if target.is_visible() and cast_best(me, target, is_camp):
        hit = True
    if me.can_attack() and target.is_visible() and cheb(me.position(), target.position()) <= me.attack_range():
        try:
            me.attack(target)
        except cambc.Error:
            pass
    return hit


def shield_if_hurt(me, threatened):
    if not threatened or not me.can_cast():
        return
    for ab in me.abilities():
        try:
            if ab.is_shield() and ab.is_ready() and me.health() < me.max_health() * 0.9:
                ab.use()
                return
        except cambc.Error:
            pass


def awake_camps_near(me, pos, now):
    """Camps that can hit us now: within range 3 and either damaged or in the group we just hit.

    Damage wakes the whole group; it sleeps after 2 rounds with nobody in range [rules] [measured A32].
    """
    tgt = S["target"]
    hot = tgt.i if tgt is not None and now - S["hit_round"] <= 2 else -1
    # Every awake monster in range counts, even one an ally is nearer: targets switch the moment
    # that ally steps away, and a recall started in range gets cancelled [measured: elkring, the
    # tank died recalling at range 3 when the model said a leaving ally was nearer]. P3.
    out = []
    for camp in vision.camps():
        try:
            cp = camp.position()
            if cheb(cp, pos) > MONSTER_RANGE or camp.strength() <= 0:
                continue
            key = BY_TILE.get((cp.x, cp.y))
            if camp.health() < camp.max_health() or (key is not None and key[0] == hot):
                out.append(camp)
        except cambc.Error:
            pass
    return out


# ---------------------------------------------------------------- group takes (R7, R8; P10, P19)

def my_rank(unit):
    return RANK.get(int(unit.champion_name()), 50)


def dist(a, b):
    """Chebyshev distance between (x, y) tuples: pure Python, no host call."""
    dx, dy = a[0] - b[0], a[1] - b[1]
    return max(dx if dx > 0 else -dx, dy if dy > 0 else -dy)


def seen_champions(team=None):
    """vision.champions(team), but a tile it can't resolve drops only that champion: the SDK call
    raises for the whole list [sdk; measured: "No visible entity of this kind occupies the tile"]."""
    try:
        return vision.champions(team)
    except cambc.Error:
        out = []
        for t in vision.champion_tiles(team).positions():
            try:
                out.append(vision.champion_at(t))
            except cambc.Error:
                pass
        return out


def other_bodies(me, pos):
    """([((x, y), rank)] of every other visible champion, [visible allies]). Enemies never win a tie
    for us: we don't know the cross-team tie-break (A2), so assume the worst."""
    bodies, allies = [], []
    mine = int(me.champion_name())
    for u in seen_champions():
        try:
            if not u.is_visible():
                continue
            up = u.position()
            if u.is_ally():
                if int(u.champion_name()) == mine:
                    continue
                allies.append(u)
                bodies.append(((up.x, up.y), my_rank(u)))
            else:
                bodies.append(((up.x, up.y), 99))
        except cambc.Error:
            pass
    return bodies, allies


def hits_me(h, q, mine, bodies):
    """Would a monster at h hit us at q? Nearest champion by Chebyshev, ties to the lowest unit id [measured A2]."""
    d = dist(h, q)
    if d > MONSTER_RANGE:
        return False
    for b, r in bodies:
        e = dist(h, b)
        if e < d or (e == d and r < mine):
            return False
    return True


def hitting_me(me, pos, camps):
    """The awake camps whose nearest champion is us (R8). Only for the retreat trigger: escapes use them all."""
    bodies, mine, q = other_bodies(me, pos)[0], my_rank(me), (pos.x, pos.y)
    return [c for c in camps if hits_me((c.position().x, c.position().y), q, mine, bodies)]


def kill_key(c):
    """P8 + Smith's rule: most strength per HP first (equal strength: lowest HP), clusters last."""
    p = c.position()
    s = c.strength()
    return (s <= 0, -s / max(c.health(), 1), c.health(), p.x, p.y)


def stand_tile(pos, rng, focus, live, hitters, bodies, mine, tank, avoid, taken):
    """R8: the tile to fight from, or None. Tiles: walkable, free, in reach (rng) of a live camp.

    Tank: nearest to every monster (min of the max distance). Others: the least strength aimed at
    them given where the other bodies stand, then reach the focus; ranged keep the most distance.
    """
    me_xy = (pos.x, pos.y)
    # Per monster, the body it would hit instead of us: (distance, rank).
    best_other = [min(((dist(h, b), r) for b, r in bodies), default=(99, 99)) for h, s in hitters]
    x0 = max(0, min(c[0] for c in live) - rng)
    x1 = min(W - 1, max(c[0] for c in live) + rng)
    y0 = max(0, min(c[1] for c in live) - rng)
    y1 = min(H - 1, max(c[1] for c in live) + rng)
    best, best_key = None, None
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if SPAWN_FIELD.d[y * W + x] >= C.UNREACHED:
                continue
            q = (x, y)
            if q == avoid or (q != me_xy and q in taken):
                continue
            reach_f = dist(q, focus) <= rng
            if not reach_f:
                for c in live:
                    if dist(q, c) <= rng:
                        break
                else:
                    continue
            steps = dist(me_xy, q)
            if tank:
                far = 0
                for h, s in hitters:
                    d = dist(q, h)
                    if d > far:
                        far = d
                key = (far, not reach_f, steps)
            else:
                exp, near = 0, 99
                for k, (h, s) in enumerate(hitters):
                    d = dist(q, h)
                    if d < near:
                        near = d
                    if d <= MONSTER_RANGE:
                        e, r = best_other[k]
                        if d < e or (d == e and mine < r):
                            exp += s
                key = (exp, not reach_f, -near if rng > 1 else 0, steps)
            if best_key is None or key < best_key:
                best, best_key = q, key
    return best


def step_to(me, q):
    """One step that brings us closer to tile q (x, y); move_towards() (~100k fuel) if none does."""
    if not me.can_move():
        return False
    pos = me.position()
    here = (pos.x, pos.y)
    d0 = dist(here, q)
    if d0 == 0:
        return False
    occupied = vision.champion_tiles() | vision.camp_tiles()
    best, best_key = None, None
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            x, y = pos.x + dx, pos.y + dy
            if not (0 <= x < W and 0 <= y < H) or SPAWN_FIELD.d[y * W + x] >= C.UNREACHED:
                continue
            d = dist((x, y), q)
            if d >= d0:
                continue
            v = cambc.Vec2(x, y)
            if occupied.is_set(v):
                continue
            key = (d, abs(x - q[0]) + abs(y - q[1]))
            if best_key is None or key < best_key:
                best, best_key = v, key
    try:
        if best is not None:
            return me.move_absolute(best)
        return me.move_towards(cambc.Vec2(q[0], q[1]))
    except cambc.Error:
        return False


def take(me, grp, live, now):
    """R8 group take (P10: one body against their fractions; P19: the snake's head and tail).

    The tank (most max HP, then lowest id: it also wins distance ties) stands nearest every
    monster; the others stand where no monster picks them [measured A2]; all hit one focus.
    """
    pos = me.position()
    mine = my_rank(me)
    rng = me.attack_range()
    focus = min(live, key=kill_key)
    fp = focus.position()
    f_xy = (fp.x, fp.y)
    live_xy = [(c.position().x, c.position().y) for c in live]
    hitters = [((c.position().x, c.position().y), c.strength()) for c in live if c.strength() > 0]
    bodies, allies = other_bodies(me, pos)
    tank, tank_key = None, (me.max_health(), -mine)
    for a in allies:
        try:
            ap = a.position()
            if cheb(ap, fp) > C.TAKE_RADIUS or claim_of(a) != grp.i:
                continue
            k = (a.max_health(), -my_rank(a))
            if k > tank_key:
                tank, tank_key = a, k
        except cambc.Error:
            pass
    avoid = None
    tank_ready = True
    if tank is not None:
        # Plan the tank's tile with its own rule, keep it free and assume it stands there.
        tp = tank.position()
        t_xy = (tp.x, tp.y)
        t_rng = tank.attack_range()
        avoid = stand_tile(tp, t_rng, f_xy, live_xy, hitters, [], my_rank(tank), True, None, set())
        tank_ready = dist(t_xy, f_xy) <= t_rng
        if avoid is not None:
            bodies = [(b, r) if b != t_xy else (avoid, r) for b, r in bodies]
    # The tank plans as the others predict it (allies make way); everyone else avoids every body.
    taken = {b for b, r in bodies if tank is not None or r == 99}
    if tank is not None:
        taken.add(t_xy)
    asleep = all(c.health() >= c.max_health() for c in live)   # before moving: a step can lose sight of a camp
    dest = stand_tile(pos, rng, f_xy, live_xy, hitters, bodies, mine, tank is None, avoid, taken)
    if dest is None:
        step_field(me, group_nav(grp))
    else:
        step_to(me, dest)
    pos = me.position()
    if asleep and not tank_ready and now - S["hit_round"] > 2:
        # Let the tank pull (it takes the first volley), but never wait for ever.
        if S["pull_since"] is None:
            S["pull_since"] = now
        if now - S["pull_since"] < C.PULL_WAIT:
            return True
    S["pull_since"] = None
    live = [c for c in live if c.is_visible()]
    if not live:
        return True
    if focus not in live:
        focus = min(live, key=kill_key)
    in_range = [c for c in live if cheb(c.position(), pos) <= rng]
    if in_range:
        target = focus if focus in in_range else min(in_range, key=kill_key)
        if strike(me, target, True):
            S["hit_round"] = now
    elif not asleep and cast_best(me, focus, True):
        S["hit_round"] = now        # range-4 spells while we can't reach (Marcella, Stellar)
    return True


def capture_contested(grp, now):
    """True once an enemy has stood on grp's spawn tiles for C.CONTEST_MAX rounds of our capture."""
    for e in seen_champions(ENEMY):
        try:
            if e.is_visible() and grp.tiles.is_set(e.position()):
                if S["contest"][0] != grp.i:
                    S["contest"] = (grp.i, now)
                return now - S["contest"][1] >= C.CONTEST_MAX
        except cambc.Error:
            pass
    S["contest"] = (-1, 0)
    return False


def capture_left_to_ally(me, grp, pos):
    """R7: the capture reward is split between allies present [rules]: one body captures, the others
    move on. The capturer is the claimer nearest a spawn tile (ties: lowest id). Not with an enemy in view."""
    for e in seen_champions(ENEMY):
        if e.is_visible():
            return False
    cells = [(c.x, c.y) for c in grp.cells]
    mine = (min(dist((pos.x, pos.y), c) for c in cells), my_rank(me))
    for a in other_bodies(me, pos)[1]:
        try:
            if claim_of(a) != grp.i:
                continue
            ap = a.position()
            k = (min(dist((ap.x, ap.y), c) for c in cells), my_rank(a))
            if k < mine:
                return True
        except cambc.Error:
            pass
    return False


# ---------------------------------------------------------------- actions

def shop(me):
    """Spend gold on the build (on spawn or while dead [rules])."""
    while True:
        item = C.BUILD[S["bought"]] if S["bought"] < len(C.BUILD) else C.AFTER_BUILD
        try:
            if me.gold_count() < item.cost() or not me.can_buy(item):
                return
            me.buy(item)
        except cambc.Error:
            return
        S["bought"] += 1


def hold_altars(enemies, now):
    """P6/P11: enemies standing by an altar hold it; bank elsewhere for a while instead of
    walking in, fleeing and walking in again [measured: collision, two bodies with 44 gems bounced
    in and out of range from round ~300 to 2000]."""
    seen = []
    for e in enemies:       # called after we moved: some may be out of vision now
        try:
            if e.is_visible():
                seen.append(e.position())
        except cambc.Error:
            pass
    for i, a in enumerate(ALTARS):
        if any(cheb(p, a) <= C.ALTAR_GUARD for p in seen):
            ALTAR_HELD[i] = now + C.ALTAR_AVOID


def altar_field(pos, now, force=False):
    """The field to the nearest altar we may use: all of them unless some are held. None: all held."""
    held = [i for i, t in ALTAR_HELD.items() if t > now]
    if force or not held:
        return ALTAR_FIELD
    best = None
    for i, a in enumerate(ALTARS):
        if i in held:
            continue
        if i not in ALTAR_FIELDS:
            bank = cambc.Bitboard()
            bank.draw_chebyshev(a, K.SUBMIT_GEMS_RANGE)
            blocked = STATIC | CAMPTILES
            ALTAR_FIELDS[i] = Field(bank & ~blocked, blocked)    # one BFS per altar, once
        f = ALTAR_FIELDS[i]
        if best is None or f.at(pos.x, pos.y) < best.at(pos.x, pos.y):
            best = f
    return best


def go_bank(me, field=None):
    """Walk to the nearest open altar and tribute (P: bank early, never die with gems)."""
    pos = me.position()
    for a in ALTARS:
        if cheb(a, pos) <= K.SUBMIT_GEMS_RANGE and not vision.has_altar_lock(a):
            try:
                me.submit_gems(a)
                return True
            except cambc.Error:
                pass
    if field is None:
        field = altar_field(pos, cambc.round_number())
        if field is None:
            return go_heal(me)
    return step_field(me, field)


def go_heal(me):
    """Recall if spawn is far, else walk; heal on spawn."""
    pos = me.position()
    if SPAWN.is_set(pos):
        return True
    if SPAWN_FIELD.at(pos.x, pos.y) > K.RECALL_TIME + 1:
        try:
            me.recall()
            return True
        except cambc.Error:
            pass
    return step_field(me, SPAWN_FIELD)


def reachable(me, pos, enemies):
    """Enemies that count: within C.FIGHT_WALK walking tiles, or close enough to attack us anyway.

    Without this, two bots facing each other across a wall chase (or flee and come back) forever
    and never farm [measured: interlock, froze from round ~900 to 2000; collision, flee/return
    every other round from ~300]. Only walls block: cleared spawn tiles are standable [rules],
    live monsters are a short detour. Bounded BFS: cheap.
    """
    root = cambc.Bitboard()
    root.set(pos)
    seen = cambc.Bitboard()
    f = cambc.DistanceField()
    f.compute(STATIC, root, seen, C.FIGHT_WALK)
    out = []
    for e in enemies:
        ep = e.position()
        if (seen.is_set(ep) and f.get(ep) <= C.FIGHT_WALK) or cheb(ep, pos) <= e.attack_range() + 1:
            out.append(e)
    return out


def fight(me, enemies, now):
    """P8: strike the weak when the fight is ours. Returns True if we acted."""
    pos = me.position()
    allies = [a for a in seen_champions(ALLY) if a.is_visible() and cheb(a.position(), pos) <= C.FIGHT_RADIUS]
    our_dps = sum(a.strength() for a in allies) or me.strength()
    their_dps = sum(e.strength() for e in enemies)
    target = min(enemies, key=lambda e: (e.health() - 10 * e.gem_count(), cheb(e.position(), pos)))
    ttk_them = target.health() / max(our_dps, 1)
    ttk_us = me.health() / max(their_dps, 1)
    if ttk_them < ttk_us * C.FIGHT_EDGE:
        if cheb(target.position(), pos) > me.attack_range() and me.can_move():
            try:
                me.move_towards(target.position())      # ~100k fuel: only while chasing
            except cambc.Error:
                pass
        hit = strike(me, target, False)
        if hit or me.position() != pos or not me.can_move():
            return True
        return False    # couldn't close in or hit: don't stand frozen, get on with the turn
    if me.gem_count() > 0 or me.health() < me.max_health() * 0.5:
        # Not our fight: get the gems away (P3). Hit back on the way if we're ranged-safe.
        if step_away(me, [e.position() for e in enemies]):
            return True
        in_range = [e for e in enemies if cheb(e.position(), pos) <= me.attack_range()]
        if in_range:
            return strike(me, min(in_range, key=lambda e: e.health()), False) or True
        # Nowhere farther to go and nothing to hit (often an enemy across a wall): get on with the
        # turn, don't freeze [measured: collision, both teams stood still from round ~600 to 2000].
    return False


def farm(me, now):
    grp = S["target"]
    if grp is None or grp.state == "resp" and grp.back_at - now > C.WAIT_RESPAWN_MAX:
        grp = S["target"] = choose_target(me, now)
        claim(grp)
        if C.TRACE:
            trace(me, now, "choose")
        if grp is None:
            return go_bank(me) if me.gem_count() else go_heal(me)
    pos = me.position()
    live = []
    for camp in vision.camps():
        key = BY_TILE.get((camp.spawn_position().x, camp.spawn_position().y))
        if key is not None and key[0] == grp.i and camp.is_visible():
            live.append(camp)
    if live and C.GROUP_TAKE:
        return take(me, grp, live, now)
    if live:
        def pick(cs):
            return min(cs, key=lambda c: (-c.strength(), c.health()))
        in_range = [c for c in live if cheb(c.position(), pos) <= me.attack_range()]
        if not in_range:
            step_field(me, group_nav(grp))
            pos = me.position()
            # We moved: a camp may have left our vision (position() would raise).
            in_range = [c for c in live if c.is_visible() and cheb(c.position(), pos) <= me.attack_range()]
        if in_range:
            if strike(me, pick(in_range), True):
                S["hit_round"] = now
        return True
    nav = group_nav(grp)
    if grp.state != "reward" and any(h > 0 for h in grp.hp):
        # Waiting for a respawn: never on a spawn tile. "Any occupied spawn tile delays the
        # entire group" [rules], so standing there holds the timer for ever [measured, packs].
        if grp.tiles.is_set(pos):
            step_off(me, nav)
            return True
        if nav.at(pos.x, pos.y) <= C.RESPAWN_WAIT_DIST:
            return True
        return step_field(me, nav)
    if C.GROUP_TAKE and capture_left_to_ally(me, grp, pos):
        S["skip"] = (grp.i, now + K.CAPTURE_TIME + 3)
        S["target"] = None
        claim(None)
        return go_bank(me) if me.gem_count() >= C.BANK_AT else True
    if C.CONTEST_MAX and capture_contested(grp, now):
        # P23: move only for advantage. fight() already took the fight if it was ours; an enemy on
        # the tiles stops the capture for both sides [rules], so holding on earns nothing.
        S["skip"] = (grp.i, now + C.CONTEST_SKIP)
        S["target"] = None
        claim(None)
        return True
    if grp.tiles.is_set(pos):
        return True     # capturing: stand still [rules: 5 rounds uncontested]
    return step_field(me, nav)


# ---------------------------------------------------------------- the turn

def trace(me, now, *extra):
    tgt = S["target"]
    print(f"T|{now}|{cambc.ChampionType.to_string(int(me.champion_name()))}|"
          f"hp={int(me.health()) if me.is_alive() else 0} gems={me.gem_count()} gold={me.gold_count()} "
          f"mode={S['mode']} tgt={None if tgt is None else (tgt.i, tgt.state, tgt.gems, tgt.gold)} "
          f"pos={me.position() if me.is_alive() else None} fuel={cambc.fuel_remaining()} {' '.join(map(str, extra))}",
          flush=True)


def play_turn():
    me = cambc.me()
    now = cambc.round_number()
    if C.TRACE and now % C.TRACE == 0:
        trace(me, now)
    if not GROUPS:
        f0 = cambc.fuel_remaining()
        init_world()
        init_rank()
        S["slot"] = my_slot(me)
        if C.TRACE:
            trace(me, now, "init_fuel", f0 - cambc.fuel_remaining())
    if not me.is_alive():
        if C.TRACE and S.get("last"):
            print(f"T|{now}|death|{S['last']}", flush=True)     # the turn before we died
            S["last"] = None
        shop(me)
        S["target"] = None
        S["mode"] = "farm"
        return
    if me.is_recalling() or me.is_submitting_gems() or me.is_teleporting():
        return
    pos = me.position()
    sense(me, now)
    if SPAWN.is_set(pos):
        shop(me)
        if S["mode"] == "heal" and me.health() >= me.max_health() * 0.95:
            S["mode"] = "farm"

    gems = me.gem_count()
    hp, maxhp = me.health(), me.max_health()
    enemies = [e for e in seen_champions(ENEMY) if e.is_visible() and cheb(e.position(), pos) <= C.FIGHT_RADIUS]
    if enemies:
        enemies = reachable(me, pos, enemies)
    camps = awake_camps_near(me, pos, now)
    # R8: a monster an ally is nearer hits that ally, so it doesn't make us retreat; but if we do, we
    # step away from all of them.
    hitters = hitting_me(me, pos, camps) if C.GROUP_TAKE and camps else camps
    incoming = sum(c.strength() for c in hitters) + sum(e.strength() for e in enemies)
    shield_if_hurt(me, incoming > 0)
    if C.TRACE:
        S["last"] = (f"{cambc.ChampionType.to_string(int(me.champion_name()))} r{now} hp={int(hp)} gems={gems} "
                     f"mode={S['mode']} pos=({pos.x},{pos.y}) tgt={None if S['target'] is None else S['target'].i} "
                     f"camps={[(c.position().x, c.position().y, int(c.health())) for c in camps]} "
                     f"en={[(e.position().x, e.position().y, int(e.health())) for e in enemies]}")

    # Survive first (P3): don't stand in damage we can't take; never die with gems.
    if incoming and hp < incoming * C.RETREAT_ROUNDS + 0.1 * maxhp:
        S["mode"] = "heal"
        if step_away(me, [c.position() for c in camps] + [e.position() for e in enemies]):
            return
    if S["mode"] == "heal":
        threats = [c.position() for c in camps] + [e.position() for e in enemies]
        if enemies and gems:
            hold_altars(enemies, now)
        bank = altar_field(pos, now)
        if threats:
            # Recall is cancelled by any damage [rules]: get out of reach first.
            if not step_away(me, threats) and enemies:
                fight(me, enemies, now)
        elif gems and bank is not None and bank.at(pos.x, pos.y) <= C.BANK_NEAR + 2:
            go_bank(me, bank)
        else:
            go_heal(me)
        return

    if enemies and fight(me, enemies, now):
        if gems:
            hold_altars(enemies, now)
        return

    # Bank (P: one currency; tributed gems are the only score).
    left = K.MAX_ROUNDS - now
    must = left <= ALTAR_FIELD.at(pos.x, pos.y) + gems // 10 + C.END_MARGIN or \
        gems + cambc.global_submitted_gems(ALLY) >= K.WINNING_GEMS
    bank = altar_field(pos, now, must)
    alt = bank.at(pos.x, pos.y) if bank is not None else C.UNREACHED
    tgt = S["target"]
    capturing = tgt is not None and tgt.tiles.is_set(pos) and tgt.state in ("alive", "reward") and not any(h > 0 for h in tgt.hp)
    if gems and not capturing and (
            gems >= C.BANK_AT
            or alt <= C.BANK_NEAR
            or must):
        if alt < C.UNREACHED:
            go_bank(me, bank)
            return

    # Low and idle: heal before the next camp.
    if hp < 0.5 * maxhp and not camps:
        S["mode"] = "heal"
        go_heal(me)
        return

    farm(me, now)
    if S["target"] is not None and S["target"].state == "resp" and S["target"].back_at - now > C.WAIT_RESPAWN_MAX:
        S["target"] = None
