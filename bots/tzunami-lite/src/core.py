"""tzunami-lite play: each body farms its best camp group by gems per round, banks, heals, shops.

Turn: sense -> channels -> shop -> survive -> bank -> farm. Plan: docs/BATTLEPLAN.md -> v2.
Fuel [measured 14 Oct, 2.1.6]: every Python op costs ~1k and built-ins are no cheaper, so the hot
path does less work: one camp_tiles() diff per turn (~7k) instead of vision.camps() (~12k per camp),
g.state() (~15k) only on a change or for the target, a distance field per group prebuilt with
spare fuel, clear costs cached at 1 dps, and a pruned choice.
"""
import cambc
from cambc import vision, Team

import config as C
import plan
import world
from world import cheb_xy

ALLY, ENEMY = Team.ALLY, Team.ENEMY
K = cambc.constants
GAlive, GReward = cambc.game_map.CampGroupAlive, cambc.game_map.CampGroupRewardAvailable

S = {
    "ready": False,
    "slot": None,       # our byte in shared memory
    "me": None,         # our ChampionType id
    "types": [],        # our team's ChampionType ids, sorted: slot order
    "opening": None,    # first target from the draft
    "strategy": C.FARM,
    "target": None,     # Group we farm
    "target_d": 65535,  # walking distance to it when chosen
    "take": False,      # the target is a group take (L1): several bodies, the tank pulls
    "take_since": None, # round we reached a take and started waiting for helpers
    "skip": (-1, 0),    # (group, until round): a group we just left
    "mode": 0,          # 0 farm | 1 heal
    "bought": 0,
    "hp_last": 0.0,
    "hit_round": -99,   # last round we damaged a camp
    "still": (None, 0), # (tile, round we got there): the stuck detector
    "banking": False,   # L2: committed to tribute the bag we carry
    "bank_best": (65535, 0, 0),     # (closest altar walk, round we got there, last round walking): stall watchdog
    "enemy_seen": -99,  # last round an enemy was within WATCH_RADIUS
    "flee": None,       # (first round, gap then, last round) of a flight from enemy champions (DESPERATE)
    "build": None,      # L4: (first shards, then this shard) for our champion
    "no_trip": False,   # L4: the shop refused an item we could afford: no more shop trips
    "last": None,       # trace of the previous turn (printed on death)
    "hot": {},          # (x, y) of a camp that hit us -> round (C.HOT_MEMORY)
    "leader": None,     # squad mate: our leader's ChampionType (C.LAYOUTS); None if we lead or play solo
    "mates": (),        # squad leader: our mates' ChampionTypes; () if we follow or play solo
    "following": None,  # mate: group index of the leader's take we joined
    "ties": False,      # mate: the leader was an earlier, separate pick, so it wins monster ties [measured A2]
    "linked": False,    # Cassi or Issac: one death kills both [rules], so the safer profile (C.LINKED_*)
    "reserve": C.HP_RESERVE,
    "trips": C.MAX_TRIPS,
    "retreat": C.RETREAT_ROUNDS,
    "idle": {},         # TRACE: rounds alive with no move, attack or channel, by situation
    "fuel_max": 0,
}
T = {}                  # this turn only: camp tiles, visible tiles, occupied tiles, camp objects
KNOWN = None            # camp tiles we believe hold a live camp
SPAWN_FIELD = ALTAR_FIELD = None
THEM = None             # Field to the enemy spawn, built with spare fuel after the groups (side_of)
SPAWN_IDX = ()          # linear indices of our spawn tiles
HOME_ALT = 65535        # walk from our spawn to the nearest tribute tile (recall-to-bank, L3)
P = C.STRAT[C.FARM]     # this map's strategy parameters (set in init)
TODO = []               # groups still to prepare (field + altar distance), nearest last


def init(me):
    global SPAWN_FIELD, ALTAR_FIELD, KNOWN, SPAWN_IDX, HOME_ALT, P
    world.load()
    SPAWN_FIELD = world.Field(world.SPAWN, world.BLOCKED)
    ALTAR_FIELD = world.altar_field()
    KNOWN = world.CAMPTILES | cambc.Bitboard()
    sp = world.SPAWN.positions()
    SPAWN_IDX = tuple(p.y * world.W + p.x for p in sp)
    HOME_ALT = min([ALTAR_FIELD.d[i] for i in SPAWN_IDX])
    s0 = sp[len(sp) // 2]
    TODO.extend(sorted(world.GROUPS, key=lambda g: -cheb_xy(g.center.x, g.center.y, s0.x, s0.y)))
    mine = S["me"] = int(me.champion_name())
    memo = plan.read()
    if memo is not None and mine in memo[1]:
        S["strategy"], S["types"], opening = memo
        gi = opening.get(mine)
        S["opening"] = world.GROUPS[gi] if gi is not None and gi < len(world.GROUPS) else None
    else:
        # No draft memory: rank our type among the allies we see on turn 1 (all on spawn).
        types = {mine}
        for a in cambc.champions(ALLY):
            try:
                if a.is_visible():
                    types.add(int(a.champion_name()))
            except cambc.Error:
                pass
        S["types"] = sorted(types)
    P = C.STRAT.get(S["strategy"], C.STRAT[C.FARM])
    S["build"] = C.BUILDS.get(mine, C.BUILD_DEFAULT)
    if C.LINKED and mine in (int(cambc.ChampionType.CASSI), int(cambc.ChampionType.ISSAC)):
        S["linked"] = True
        S["reserve"], S["trips"], S["retreat"] = C.LINKED_RESERVE, C.LINKED_MAX_TRIPS, C.LINKED_RETREAT
    if C.SQUADS:
        for sq in C.LAYOUTS[C.STRAT_LAYOUT.get(S["strategy"], C.LAYOUT)]:
            here = [t for t in sq if t in S["types"]]
            if mine in here and len(here) > 1:
                if mine == here[0]:
                    S["mates"] = tuple(here[1:])
                else:
                    S["leader"] = here[0]
        if S["leader"] is not None:
            S["trips"] = min(S["trips"], C.MATE_TRIPS)
            # Pick order is COMPS order (plan.draft_turn); Cassi & Issac are one pick, order unknown.
            order = [int(p) for p in C.COMPS[5]]
            pa, pm = plan.pick_of(S["leader"]), plan.pick_of(mine)
            S["ties"] = C.SQUAD_TIES and pa in order and pm in order and order.index(pa) < order.index(pm)
    k = S["types"].index(mine)
    S["slot"] = k if k < 6 else None    # bytes 0-5: one per body; 6-7: beacon (BATTLEPLAN v2)
    S["ready"] = True


# ---------------------------------------------------------------- shared memory: claims

FARMING, HOME, TAKING, DEAD = 0, 1, 2, 3     # 2-bit status in our byte


def claim(grp, status=None):
    """Our byte: 2-bit status and 6-bit target group + 1 (BATTLEPLAN v2 -> Shared memory)."""
    if status is None:
        status = TAKING if S["take"] else FARMING
    if S["slot"] is not None:
        gi = grp.i + 1 if grp is not None and grp.i < 63 else 0
        cambc.shared_memory[S["slot"]] = (status << 6) | gi


def board():
    """Allies' bytes: (groups they claim, {group: [types taking it]}, types free to help)."""
    taken, takes, free = set(), {}, []
    types = S["types"]
    for k in range(min(6, len(types))):
        if k == S["slot"]:
            continue
        v = cambc.shared_memory[k]
        st, gi = v >> 6, (v & 63) - 1
        if gi >= 0:
            taken.add(gi)
        if st == TAKING and gi >= 0:
            takes.setdefault(gi, []).append(types[k])
        elif st != DEAD:
            free.append(types[k])
    return taken, takes, free


def status_of(t):
    """(status, group) in the byte of the ally of ChampionType t; (DEAD, -1) if it has none."""
    types = S["types"]
    k = types.index(t) if t in types else 6
    if k >= 6:
        return DEAD, -1
    v = cambc.shared_memory[k]
    return v >> 6, (v & 63) - 1


def mates_seen(pos, want):
    """{type: unit} for allies of the given types we see within C.SQUAD_NEAR."""
    out = {}
    for p in vision.champion_tiles(ALLY).positions():
        if cheb_xy(p.x, p.y, pos.x, pos.y) <= C.SQUAD_NEAR and (p.x != pos.x or p.y != pos.y):
            try:
                u = vision.champion_at(p)
                t = int(u.champion_name())
                if t in want:
                    out[t] = u
            except cambc.Error:
                pass
    return out


def mates_up():
    """Our mates that can join a take now: not dead and not home (healing or shopping)."""
    return [t for t in S["mates"] if status_of(t)[0] not in (DEAD, HOME)]


def claim_of(t):
    """Group the ally of ChampionType t claims, or -1."""
    types = S["types"]
    if t not in types:
        return -1
    k = types.index(t)
    return (cambc.shared_memory[k] & 63) - 1 if k < 6 else -1


# ---------------------------------------------------------------- sensing

def sense(me, now):
    """Diff the visible camp tiles against what we believed: only changes cost Python work."""
    global KNOWN
    ct = T["ct"] = vision.camp_tiles()
    vis = T["vis"] = me.visible_tiles()
    groups, by_tile = world.GROUPS, world.BY_TILE
    back = ct & ~KNOWN
    if not back.is_empty():
        for p in back.positions():
            key = by_tile.get((p.x, p.y))
            if key is not None:
                grp = groups[key[0]]
                if grp.state:
                    grp.state = 0
                    grp.hp = list(grp.maxhp)    # respawned at full HP
                else:
                    grp.hp[key[1]] = grp.maxhp[key[1]]
                world.recost(grp)
        KNOWN = KNOWN | back
    gone = KNOWN & vis & ~ct
    if not gone.is_empty():
        touched = set()
        for p in gone.positions():
            key = by_tile.get((p.x, p.y))
            if key is not None:
                groups[key[0]].hp[key[1]] = 0
                touched.add(key[0])
        KNOWN = KNOWN & ~gone
        for gi in touched:
            if not any(groups[gi].hp):
                refresh(groups[gi], now)
            world.recost(groups[gi])


def refresh(grp, now):
    """Ask the engine for the group's state (~15k fuel): alive, reward waiting, or respawning."""
    try:
        st = grp.g.state()
    except cambc.Error:
        return
    if isinstance(st, GAlive):
        grp.state = 0
    elif isinstance(st, GReward):
        grp.state = 1
        grp.hp = [0] * len(grp.hp)
    else:
        grp.state = 2
        grp.back_at = now + st.timer
        grp.hp = list(grp.maxhp)
    world.recost(grp)


def camp(p):
    """The visible camp on tile p, or None; cached for the turn (camp_at ~14k)."""
    k = (p.x, p.y)
    c = T["camps"].get(k)
    if c is None:
        try:
            c = vision.camp_at(p)
        except cambc.Error:
            c = False
        T["camps"][k] = c
    return c or None


def occupied():
    o = T.get("occ")
    if o is None:
        o = T["occ"] = vision.champion_tiles() | T["ct"]
    return o


def hot_camps(pos, hurt):
    """(tile, camp, strength) for camps that can hit us now (range 3 [rules]): damaged ones, and
    every one with strength if we lost HP with no enemy in view (an ally may have woken it). P3."""
    box = cambc.Bitboard()
    box.draw_chebyshev(pos, C.CAMP_RANGE)
    near = T["ct"] & world.STRONG & box
    out = []
    if near.is_empty():
        return out
    for p in near.positions():
        key = world.BY_TILE.get((p.x, p.y))
        c = camp(p)
        if key is None or c is None:
            continue
        grp = world.GROUPS[key[0]]
        try:
            if hurt or c.health() < grp.maxhp[key[1]]:
                out.append((p, c, grp.str[key[1]]))
        except cambc.Error:
            pass
    return out


def enemies_near(pos, r):
    """Visible enemy champions within Chebyshev r (champion_tiles ~10k; champion_at only for those)."""
    out = []
    et = vision.champion_tiles(ENEMY)
    if et.is_empty():
        return out
    for p in et.positions():
        if cheb_xy(p.x, p.y, pos.x, pos.y) <= r:
            try:
                out.append(vision.champion_at(p))
            except cambc.Error:
                pass
    return out


# ---------------------------------------------------------------- estimates

def camp_dps(me):
    """Damage per round on camps: basic attack, plus resets and damage spells every 8 rounds [rules]."""
    s = me.strength()
    dps = s
    best = 0.0
    for ab in me.abilities():
        try:
            if ab.is_attack_reset():
                v = s
            elif ab.is_damage() and (ab.can_target_camps() or ab.can_target_ground()):
                v = ab.damage_amount()
            else:
                continue
            best += v / 8
        except cambc.Error:
            pass
    return max(dps + best, 1.0)


def prepare(grp):
    """Build the group's field and the distances score() needs: our spawn and the nearest altar."""
    nav = world.nav(grp).d
    grp.home = min([nav[i] for i in SPAWN_IDX])
    grp.alt = min([ALTAR_FIELD.near(p) for p in grp.cells])
    grp.fixed = K.CAPTURE_TIME + 1 + grp.alt * grp.gems / max(C.BANK_AT, grp.gems)


def prebuild():
    """Prepare groups with the fuel this turn leaves (spare fuel is lost [rules]), nearest first,
    so a retarget turn never pays for a field. ~0.25-0.4M per group [measured 14 Oct]. Then the
    field to the enemy spawn (side_of)."""
    global THEM
    while TODO and cambc.fuel_remaining() > C.PREBUILD_RESERVE:
        grp = TODO.pop()
        if grp.fixed is None:
            prepare(grp)
    if not TODO and THEM is None and cambc.fuel_remaining() > C.PREBUILD_RESERVE:
        es = cambc.game_map.spawn_region(ENEMY)
        THEM = world.Field(es, world.BLOCKED & ~es)
        if C.TRACE:
            print(f"T|{cambc.round_number()}|prebuilt|{len(world.GROUPS)}", flush=True)


def side_of(grp):
    """P9 (attack where they are not): a group nearer their spawn than ours is worth
    P["their_side"] of its value; 1 until the enemy field is built."""
    if grp.side is None:
        if THEM is None or grp.fixed is None:
            return 1.0
        dt = min([THEM.near(p) for p in grp.cells])
        grp.side = P["their_side"] * (C.LINKED_THEIR_SIDE if S["linked"] else 1.0) if dt < grp.home else 1.0
    return grp.side


def score(grp, d, dps, hp, maxhp, now, team=False):
    """Gems per round for taking this group now, or None if we shouldn't (P2, P3, P13). A team
    take (dps = the team's) needs no heal trips: team_need already checked the tank."""
    if d >= C.UNREACHED or grp.alt >= C.UNREACHED:
        return None
    wait = 0
    if grp.state == 2:
        wait = max(0, grp.back_at - (now + d))
        if wait > C.WAIT_RESPAWN_MAX:
            return None
    dmg = grp.dmg / dps         # P13: a cleared group (state 1) costs nothing to capture
    res = S["reserve"]
    budget = hp - res * maxhp
    trips = 0
    if dmg > budget and not team:
        trips = int((dmg - budget) // ((1 - res) * maxhp)) + 1
        if trips > S["trips"]:
            return None
    trip_time = 2 * min(grp.home, 60) + K.RECALL_TIME + 2
    rounds = d + wait + grp.work / dps + trips * trip_time + grp.fixed
    if now + rounds + min(grp.alt, 200) + C.END_MARGIN > K.MAX_ROUNDS:
        return None
    return grp.val * side_of(grp) / rounds


def team_need(grp, dps, maxhp, helpers):
    """(bodies, team dps) for a group take (L1, P10): us, the toughest helper as tank, then the
    fastest, until the tank can soak the whole clear (monsters hit the nearest champion [rules]).
    None if every helper together is not enough."""
    if not helpers:
        return None
    hs = sorted(helpers, key=lambda t: -plan.TYPE_HP[t])
    hs = hs[:1] + sorted(hs[1:], key=lambda t: -plan.TYPE_DPS[t])
    d, tank = dps, maxhp
    for k, t in enumerate(hs):
        d += plan.TYPE_DPS[t]
        if plan.TYPE_HP[t] > tank:
            tank = plan.TYPE_HP[t]
        if grp.dmg / d <= (1 - C.HP_RESERVE) * tank:
            return k + 2, d
    return None


def choose(me, now):
    """(group, take?) with the best gems per round per body; groups an ally claims only if nothing
    else is left. Groups are scored in order of an upper bound (exact walk from the prebuilt field,
    exact clear time, no waits or heal trips), stopping once no remaining bound beats the best score.
    A group we can't solo even with every heal trip is a candidate group take (L1) instead (P3, P10).
    A squad leader also scores every group as a squad take: the dps of every mate that is up, no
    heal trips while the pooled HP budgets cover the clear, the reward over the bodies (P10, P19)."""
    pos = me.position()
    pi = pos.y * world.W + pos.x
    dps, hp, maxhp = camp_dps(me), me.health(), me.max_health()
    idps = 1.0 / dps
    res = S["reserve"]
    cap0 = (hp - res * maxhp) * dps     # damage (at 1 dps) a solo takes with no heal trip
    cap = cap0 + S["trips"] * (1 - res) * maxhp * dps
    taken, takes, free = board()
    skip = S["skip"][0] if now < S["skip"][1] else -1
    # Takes: join an unfilled one; call a new one only if none is waiting for bodies.
    tcap = tdps = 0.0
    calling = False
    if C.TAKE:
        tdps = dps + sum(plan.TYPE_DPS[t] for t in free)
        tcap = (1 - C.HP_RESERVE) * max([maxhp] + [plan.TYPE_HP[t] for t in free]) * tdps
        calling = True
        for gi, ts in takes.items():
            need = team_need(world.GROUPS[gi], dps, maxhp, free + ts)
            if need is not None and len(ts) + 1 <= need[0]:
                calling = False
    # Squads: the leader scores squad takes with the mates that are up (not dead, not home).
    pdps = pcap = 0.0
    pk = 1
    pgather = C.TAKE_GATHER
    up = mates_up() if S["mates"] else ()
    if up:
        seen = mates_seen(pos, up)
        if len(seen) == len(up):
            pgather = 0
        pool = hp - res * maxhp
        pdps = dps
        for t in up:
            mhp = plan.TYPE_HP[t]
            try:
                mhp = seen[t].health() if t in seen else mhp
            except cambc.Error:
                pass
            pdps += plan.TYPE_DPS[t]
            pool += C.SQUAD_POOL * max(0.0, mhp - res * plan.TYPE_HP[t])
        pk = 1 + len(up)
        pcap = pool * pdps
    floor = K.CAPTURE_TIME + 1
    U = C.UNREACHED
    ubs = []
    for grp in world.GROUPS:
        gi = grp.i
        if gi == skip:
            continue
        cands = []
        if grp.dmg < cap:
            cands.append((grp.work * idps, 0))
        if grp.dmg < pcap:
            cands.append((grp.work / pdps + pgather, 2))
        # A take is also a candidate when a solo needs a heal trip (TAKE_OVER_TRIPS): a tank soaks
        # the hits, the clear is faster, and a half-cleared group is not left for them to finish (P10).
        if (grp.dmg >= cap0 if C.TAKE_OVER_TRIPS else grp.dmg >= cap) and \
                (gi in takes or (calling and grp.dmg < tcap)):
            cands.append((grp.work / tdps + C.TAKE_GATHER, 1))
        if not cands:
            continue
        if grp.fixed is None:
            # Not prepared yet: Chebyshev lower bound on the walk.
            c = grp.center
            d = cheb_xy(c.x, c.y, pos.x, pos.y) - grp.rad
            d = (d if d > 0 else 0) + floor
        else:
            d = grp.nav.d[pi]
            if d >= U:
                continue
            d += grp.fixed
        for w, mode in cands:
            ubs.append((grp.val / (d + w) / (pk if mode == 2 else 2 if mode else 1), gi, mode))
    ubs.sort(reverse=True)
    groups = world.GROUPS
    salt = C.SALT
    for shared in (False, True):
        f = 0.5 if shared else 1.0      # the reward is split with the ally there [rules]
        if salt:
            f2 = f * (1 + C.SALT_EPS)
        else:
            f2 = f
        best, best_s, best_d, best_m = None, 0.0, 65535, 0
        for ub, gi, mode in ubs:
            if ub * f2 <= best_s:
                break
            if mode == 2:
                if shared or gi in taken:
                    continue
                k, d_team = pk, pdps
            elif mode:
                if shared:
                    continue
                ts = takes.get(gi, [])
                need = team_need(groups[gi], dps, maxhp, free + ts)
                if need is None or len(ts) + 1 > need[0]:
                    continue
                k, d_team = need
            else:
                if (gi in taken) != shared:
                    continue
                k, d_team = 1, dps
            grp = groups[gi]
            if grp.fixed is None:
                prepare(grp)
            d = grp.nav.d[pi]
            s = score(grp, d + (pgather if mode == 2 else C.TAKE_GATHER if mode else 0), d_team, hp, maxhp, now, mode)
            if s is not None and salt:
                s *= 1 + C.SALT_EPS * (((salt * 7919 + gi * 104729 + S["me"] * 31) % 997) / 997 - 0.5)
            if s is not None and s * f / k > best_s:
                best, best_s, best_d, best_m = grp, s * f / k, d, mode
        if best is not None:
            S["target_d"] = best_d
            return best, bool(best_m)
    return None, False


# ---------------------------------------------------------------- movement

def step_field(me, field):
    """One move down a field, around units; sidestep at equal distance if every better tile is taken."""
    if not me.can_move():
        return False
    pos = me.position()
    if field.roots.is_set(pos):
        return False
    occ = occupied()
    moves = list(field.f.next_moves_from(pos))
    here = field.at(pos)
    if not moves:
        # On a tile the field treats as blocked (a camp tile after a capture): step off it.
        cands = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                x, y = pos.x + dx, pos.y + dy
                if (dx or dy) and 0 <= x < world.W and 0 <= y < world.H:
                    q = cambc.Vec2(x, y)
                    if not field.blocked.is_set(q):
                        cands.append((field.at(q), cambc.Vec2(dx, dy)))
        cands.sort(key=lambda c: c[0])
        moves = [d for v, d in cands if v < C.UNREACHED or here >= C.UNREACHED]
    for delta in moves:
        dest = pos + delta
        if occ.is_set(dest):
            continue
        try:
            if me.move_absolute(dest):
                return True
        except cambc.Error:
            continue
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            x, y = pos.x + dx, pos.y + dy
            if not (0 <= x < world.W and 0 <= y < world.H) or field.d[y * world.W + x] != here:
                continue
            q = cambc.Vec2(x, y)
            if field.blocked.is_set(q) or occ.is_set(q):
                continue
            try:
                if me.move_absolute(q):
                    return True
            except cambc.Error:
                pass
    return False


def step_off(me, field):
    """Step to the free neighbour nearest the field's roots without standing on one."""
    if not me.can_move():
        return False
    pos = me.position()
    occ = occupied()
    best, best_d = None, 65535
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            x, y = pos.x + dx, pos.y + dy
            if not (0 <= x < world.W and 0 <= y < world.H) or (dx == 0 and dy == 0):
                continue
            d = field.d[y * world.W + x]
            q = cambc.Vec2(x, y)
            if 0 < d < best_d and not field.blocked.is_set(q) and not occ.is_set(q):
                best, best_d = q, d
    if best is None:
        return False
    try:
        return me.move_absolute(best)
    except cambc.Error:
        return False


def step_away(me, threats, friends=()):
    """Move to the free neighbour farthest from every threat; ties go towards spawn. With friends
    (ally positions), retreat towards the team (BATTLEPLAN -> Engagement): beyond C.SAFE_GAP of
    every threat, extra distance counts for nothing and nearness to the nearest friend decides."""
    if not me.can_move() or not threats:
        return False
    pos = me.position()
    occ = occupied()
    pts = [(t.x, t.y) for t in threats]
    if friends:
        fr = [(f.x, f.y) for f in friends]
        best, best_key = None, None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                x, y = pos.x + dx, pos.y + dy
                if not (0 <= x < world.W and 0 <= y < world.H):
                    continue
                q = cambc.Vec2(x, y)
                if (dx or dy) and (world.STATIC.is_set(q) or occ.is_set(q)):
                    continue
                gap = min(cheb_xy(x, y, a, b) for a, b in pts)
                key = (min(gap, C.SAFE_GAP), -min(cheb_xy(x, y, a, b) for a, b in fr), -SPAWN_FIELD.d[y * world.W + x])
                if best_key is None or key > best_key:
                    best, best_key = q, key
        if best is None or best == pos:
            return False
        try:
            return me.move_absolute(best)
        except cambc.Error:
            return False
    best, best_key = None, None
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            x, y = pos.x + dx, pos.y + dy
            if not (0 <= x < world.W and 0 <= y < world.H):
                continue
            q = cambc.Vec2(x, y)
            if (dx or dy) and (world.STATIC.is_set(q) or occ.is_set(q)):
                continue
            key = (min(cheb_xy(x, y, a, b) for a, b in pts), -SPAWN_FIELD.d[y * world.W + x])
            if best_key is None or key > best_key:
                best, best_key = q, key
    if best is None or best == pos:
        return False
    try:
        return me.move_absolute(best)
    except cambc.Error:
        return False


def exit_tile(pos, pts):
    """(steps, tile) of the nearest walkable tile out of range of every camp in pts, or None.
    Candidates are each camp's four sides and corners just outside its square [rules: range 3],
    so a body on an edge or in a pocket between camps finds the real way out, not the locally
    farthest neighbour (elkring 14 Oct: Ryth slid along the edge inside a camp's range and died).
    Walls between are ignored: a Chebyshev estimate."""
    R = C.CAMP_RANGE + 1
    W, H = world.W, world.H
    sd = SPAWN_FIELD.d
    best = None
    for cx, cy in pts:
        for x, y in ((cx - R, pos.y), (cx + R, pos.y), (pos.x, cy - R), (pos.x, cy + R),
                     (cx - R, cy - R), (cx + R, cy - R), (cx - R, cy + R), (cx + R, cy + R)):
            if not (0 <= x < W and 0 <= y < H) or sd[y * W + x] >= C.UNREACHED:
                continue
            for ax, ay in pts:
                if cheb_xy(x, y, ax, ay) < R:
                    break
            else:
                key = (cheb_xy(x, y, pos.x, pos.y), sd[y * W + x], x, y)
                if best is None or key < best:
                    best = key
    return None if best is None else (best[0], (best[2], best[3]))


def escape(me, pts):
    """Step towards the nearest tile out of every camp's range; step_away if there is none."""
    pos = me.position()
    ex = exit_tile(pos, pts)
    if ex is not None and ex[0] > 0 and step_to(me, ex[1], None):
        return True
    return step_away(me, [cambc.Vec2(x, y) for x, y in pts])


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
                val, use = 1.0, target
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
    tp = target.position()
    pos = me.position()
    if me.can_attack() and cheb_xy(pos.x, pos.y, tp.x, tp.y) <= me.attack_range():
        try:
            me.attack(target)
            hit = True
        except cambc.Error:
            pass
    if target.is_visible() and cast_best(me, target, is_camp):
        hit = True
    if me.can_attack() and target.is_visible() and cheb_xy(pos.x, pos.y, tp.x, tp.y) <= me.attack_range():
        try:
            me.attack(target)
        except cambc.Error:
            pass
    return hit


# ---------------------------------------------------------------- group takes (L1: P10, P19)

def leave(grp, now, rounds):
    """Drop the target and keep away from it for a while."""
    S["skip"] = (grp.i, now + rounds)
    S["target"] = None
    S["take"] = False
    claim(None)


def squad(grp):
    """[(position, type, max HP, HP)] of visible allies claiming grp near it: the take squad."""
    out = []
    c = grp.center
    for p in vision.champion_tiles(ALLY).positions():
        if cheb_xy(p.x, p.y, c.x, c.y) > C.TAKE_RADIUS:
            continue
        try:
            u = vision.champion_at(p)
            t = int(u.champion_name())
            if t != S["me"] and claim_of(t) == grp.i:
                out.append((p, t, u.max_health(), u.health()))
        except cambc.Error:
            pass
    return out


def stand_tile(pos, rng, focus, cells, hitters, tank_xy, ties=False):
    """The tile to fight from: free, standable, within rng of a live camp (the focus first).
    Tank (tank_xy None): nearest to every monster. Others: the least strength whose nearest
    champion is us (ties count against us, A2/A47, unless `ties`: the tank was picked before us
    and wins them [measured A2]), then reach the focus, then fewest steps.
    Whole-board Bitboard ops find the best level (no exposure; for the tank, the least distance to
    its farthest monster) and Python ranks only that level's tiles: a tile-by-tile scan cost
    ~1.5-2.4M fuel, a whole turn, and Cassi rolled over every other round on rows [measured 14 Oct]."""
    mine = cambc.Bitboard()
    mine.draw_chebyshev(pos, 0)
    cand = cambc.Bitboard()
    for cx, cy in cells:
        cand.draw_chebyshev(cambc.Vec2(cx, cy), rng)
    cand = cand & ~(world.BLOCKED | (occupied() & ~mine))
    reach = cambc.Bitboard()
    reach.draw_chebyshev(cambc.Vec2(focus[0], focus[1]), rng)
    if tank_xy is None:
        k = 1
        while True:
            lvl = cand
            for hx, hy, st in hitters:
                disk = cambc.Bitboard()
                disk.draw_chebyshev(cambc.Vec2(hx, hy), k)
                lvl = lvl & disk
            best = nearest_tile(lvl, reach, pos)
            if best is not None or (cand & ~lvl).is_empty():
                return best
            k += 1
    lim = []
    exposed = cambc.Bitboard()
    for hx, hy, st in hitters:
        # Our exposure: within its range and nearer to it than the tank (ties too, unless `ties`).
        td = cheb_xy(tank_xy[0], tank_xy[1], hx, hy)
        r = min(C.CAMP_RANGE, td - 1 if ties else td)
        lim.append((hx, hy, st, r))
        if r >= 0:
            exposed.draw_chebyshev(cambc.Vec2(hx, hy), r)
    best = nearest_tile(cand & ~exposed, reach, pos)
    if best is not None:
        return best
    if len({st for hx, hy, st, r in lim}) == 1:
        # Every tile is exposed, all monsters equally strong (the usual group): exposure counts
        # the monsters that reach a tile. at[j]: the tiles at least j of them reach.
        at = [cand]
        for hx, hy, st, r in lim:
            disk = cambc.Bitboard()
            if r >= 0:
                disk.draw_chebyshev(cambc.Vec2(hx, hy), r)
            at.append(cambc.Bitboard())
            for j in range(len(at) - 1, 0, -1):
                at[j] = at[j] | (at[j - 1] & disk)
        for j in range(1, len(at)):
            best = nearest_tile(at[j] & ~at[j + 1] if j + 1 < len(at) else at[j], reach, pos)
            if best is not None:
                return best
        return None
    # Every tile is exposed, mixed strengths: rank them all by exposure.
    W = world.W
    sd = SPAWN_FIELD.d
    fx, fy = focus
    best_key = None
    for p in cand.positions():
        x, y = p.x, p.y
        if sd[y * W + x] >= C.UNREACHED:
            continue
        exp = 0
        for hx, hy, st, r in lim:
            if cheb_xy(x, y, hx, hy) <= r:
                exp += st
        key = (exp, cheb_xy(x, y, fx, fy) > rng, cheb_xy(x, y, pos.x, pos.y), y, x)
        if best_key is None or key < best_key:
            best, best_key = (x, y), key
    return best


def nearest_tile(tiles, reach, pos):
    """Of `tiles` we can walk to, the nearest that reaches the focus (in `reach`), else the nearest
    (ties: lowest row, then column, as a row-by-row scan; positions() comes column by column)."""
    W = world.W
    sd = SPAWN_FIELD.d
    for part in (tiles & reach, tiles & ~reach):
        best, best_s = None, (65535,)
        for p in part.positions():
            x, y = p.x, p.y
            if sd[y * W + x] >= C.UNREACHED:
                continue
            s = (cheb_xy(x, y, pos.x, pos.y), y, x)     # ties: lowest row, then column
            if s < best_s:
                best, best_s = (x, y), s
        if best is not None:
            return best
    return None


def step_to(me, q, nav):
    """One step that brings us nearer tile q; down the group's field if none does."""
    if not me.can_move():
        return False
    pos = me.position()
    d0 = cheb_xy(pos.x, pos.y, q[0], q[1])
    if d0 == 0:
        return False
    occ = occupied()
    W = world.W
    best, best_key = None, None
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            x, y = pos.x + dx, pos.y + dy
            if not (0 <= x < W and 0 <= y < world.H) or SPAWN_FIELD.d[y * W + x] >= C.UNREACHED:
                continue
            d = cheb_xy(x, y, q[0], q[1])
            if d >= d0:
                continue
            v = cambc.Vec2(x, y)
            if occ.is_set(v):
                continue
            key = (d, abs(x - q[0]) + abs(y - q[1]))
            if best_key is None or key < best_key:
                best, best_key = v, key
    if best is not None:
        try:
            return me.move_absolute(best)
        except cambc.Error:
            pass
    return step_field(me, nav) if nav is not None else False


def take(me, grp, live, now):
    """L1 group take (P10: concentrate; P19: the snake's head and tail). Wait off the group until
    the squad has the dps and the HP for it; the tank (most max HP) pulls and stands nearest every
    monster; the others strike only once the group is awake, from tiles the tank shields."""
    pos = me.position()
    nav = world.nav(grp)
    cells = grp.cells
    camps = []
    for j in live:
        c = camp(cells[j])
        if c is not None:
            try:
                h = c.health()
                if h != grp.hp[j]:
                    grp.hp[j] = h
                    world.recost(grp)
                camps.append((j, c, h))
            except cambc.Error:
                pass
    sq = squad(grp)
    mine = S["me"]
    here = [t for p, t, mh, h in sq]
    tank = None
    paired = False
    if S["leader"] in here:
        tank = sq[here.index(S["leader"])]  # our squad's leader tanks
        paired = True
    elif S["mates"] and any(t in here for t in S["mates"]):
        up = mates_up()
        paired = all(t in here for t in up)
    else:
        my_key = (me.max_health(), -mine)
        for p, t, mh, h in sq:
            if (mh, -t) > my_key and (tank is None or (mh, -t) > (tank[2], -tank[1])):
                tank = (p, t, mh, h)
    awake = now - S["hit_round"] <= 2 or any(h < grp.maxhp[j] for j, c, h in camps)
    if not awake:
        # Ready when the squad's dps lets its tank soak the whole clear, or our squad is here (the
        # leader chose the take for all of us: choose() checked the pooled HP budgets).
        d = camp_dps(me) + sum(plan.TYPE_DPS[t] for p, t, mh, h in sq)
        tank_hp = me.health() if tank is None else tank[3]
        tank_max = me.max_health() if tank is None else tank[2]
        if not paired and grp.dmg / d > tank_hp - C.HP_RESERVE * tank_max:
            if nav.at(pos) > C.TAKE_WAIT_DIST:
                return step_field(me, nav)
            if S["take_since"] is None:
                S["take_since"] = now
            if now - S["take_since"] > C.TAKE_WAIT_MAX:
                leave(grp, now, C.TAKE_SKIP)
            return True
        if tank is not None:
            # The tank pulls (it takes the first volley); wait near the group meanwhile.
            if nav.at(pos) > C.TAKE_WAIT_DIST:
                return step_field(me, nav)
            return True
    if not camps:
        return step_field(me, nav)
    strs = grp.str
    j, focus, fh = min(camps, key=lambda c: (strs[c[0]] <= 0, -strs[c[0]] / max(c[2], 1), c[2], c[0]))
    fp = cells[j]
    xy = [(cells[j2].x, cells[j2].y) for j2, c, h in camps]
    hitters = [(cells[j2].x, cells[j2].y, strs[j2]) for j2, c, h in camps if strs[j2] > 0]
    rng = me.attack_range()
    ties = S["ties"] and tank is not None and tank[1] == S["leader"]
    dest = stand_tile(pos, rng, (fp.x, fp.y), xy, hitters, None if tank is None else (tank[0].x, tank[0].y), ties)
    if dest is not None and (dest[0] != pos.x or dest[1] != pos.y):
        step_to(me, dest, nav)
        pos = me.position()
    inr = [(j2, c, h) for j2, c, h in camps if cheb(cells[j2], pos) <= rng]
    if inr:
        tgt = focus if any(j2 == j for j2, c, h in inr) else min(inr, key=lambda c: (strs[c[0]] <= 0, c[2]))[1]
        try:
            if tgt.is_visible() and strike(me, tgt, True):
                S["hit_round"] = now
        except cambc.Error:
            pass
    return True


def capture_left_to_ally(grp, pos):
    """R7: only allies on the region split the reward [rules], so one body captures and the others
    move on. The capturer is the claimer nearest a spawn tile (ties: lowest type); squad mates
    (SQUAD_SPLIT) capture together, so the tank earns gold for items too. Not with an
    enemy in view: then bodies stay to hold the capture."""
    if not vision.champion_tiles(ENEMY).is_empty():
        return False
    cells = grp.cells
    mine = (min(cheb(c, pos) for c in cells), S["me"])
    ours = (S["leader"],) + tuple(S["mates"]) if C.SQUAD_SPLIT else ()
    for p, t, mh, h in squad(grp):
        if t not in ours and (min(cheb(c, p) for c in cells), t) < mine:
            return True
    return False


# ---------------------------------------------------------------- actions

def next_item():
    first, after = S["build"]
    return first[S["bought"]] if S["bought"] < len(first) else after


def shop(me):
    """L4: spend all gold on our champion's build (on spawn or while dead [rules]). P2."""
    while True:
        item = next_item()
        try:
            if me.gold_count() < item.cost() or not me.can_buy(item):
                return
            me.buy(item)
        except cambc.Error:
            return
        S["bought"] += 1


def go_bank(me):
    """Walk to the nearest altar and tribute."""
    pos = me.position()
    for a in world.ALTARS:
        if cheb_xy(a.x, a.y, pos.x, pos.y) <= K.SUBMIT_GEMS_RANGE and not vision.has_altar_lock(a):
            try:
                me.submit_gems(a)
                return True
            except cambc.Error:
                pass
    return step_field(me, ALTAR_FIELD)


def go_heal(me, safe=True):
    """Go home: spawn heals and is the shop [rules]. L3: recall unless spawn is within
    P["recall_walk"], but only when safe (any damage cancels a recall [rules]); else walk."""
    pos = me.position()
    if world.SPAWN.is_set(pos):
        return True
    far = SPAWN_FIELD.at(pos) > (P["recall_walk"] if C.RECALL else K.RECALL_TIME + 1)
    if far and safe:
        try:
            me.recall()
            claim(S["target"], HOME)
            return True
        except cambc.Error:
            pass
    return step_field(me, SPAWN_FIELD)


def bank_due(me, pos, gems, alt, now):
    """L2 (P2, P11): start a bank trip? No fixed bag: bank when the altar is on the way to the
    target (detour <= P["detour"] tiles), between targets, with a big bag, or with a bag worth
    guarding and an enemy seen lately. Not in the middle of a clear."""
    if not C.BANK_DETOUR:
        return gems >= C.BANK_AT or alt <= C.BANK_NEAR
    if gems >= C.BANK_MAX or alt <= C.BANK_NEAR:
        return True
    if gems >= C.BANK_DANGER_BAG and now - S["enemy_seen"] <= C.ENEMY_MEMORY:
        return True
    if now - S["hit_round"] <= 2 or gems < C.BANK_MIN:
        return False
    tgt = S["target"]
    if tgt is None or tgt.nav is None:
        return True
    d = tgt.nav.d[pos.y * world.W + pos.x]
    return d >= C.UNREACHED or alt + tgt.alt - d <= P["detour"]


def stalled(alt, now):
    """Bank-walk watchdog: True once the walk to the altar has got no closer for C.BANK_STALL rounds.
    A camp or an enemy on the way turns us back each time (collision 14 Oct: Vendetta spent 75
    rounds in a 2-tile loop by the altar with 305 HP and 22 gems); home heals, then we try again."""
    best, since, last = S["bank_best"]
    if alt < best or now - last > C.BANK_STALL:     # closer, or a new walk (steps away don't count)
        S["bank_best"] = (alt, now, now)
        return False
    S["bank_best"] = (best, since, now)
    return now - since > C.BANK_STALL


def go_bank_trip(me, pos, alt, safe):
    """Bank, recalling first when spawn's altar via a recall beats the walk (L3)."""
    if C.RECALL and safe and alt > K.RECALL_TIME + HOME_ALT + C.RECALL_MARGIN and \
            SPAWN_FIELD.at(pos) > P["recall_walk"]:
        try:
            me.recall()
            claim(S["target"], HOME)
            return True
        except cambc.Error:
            pass
    return go_bank(me)


# ---------------------------------------------------------------- fights (L5: P4, P8)

def burst(me, e, d):
    """Damage we can deal e this turn at Chebyshev distance d: basic attack plus the best ready
    spell (a reset counts as a second basic attack)."""
    s = me.strength()
    rng = me.attack_range()
    b = s if me.can_attack() and d <= rng else 0.0
    if me.can_cast():
        best = 0.0
        tp = e.position()
        for ab in me.abilities():
            try:
                if not ab.is_ready():
                    continue
                if ab.is_attack_reset():
                    v = s if d <= rng else 0.0
                elif ab.is_damage() and (ab.can_target_enemies() or ab.can_target_ground()) \
                        and ab.valid_tiles().is_set(tp):
                    v = ab.damage_amount(e)
                else:
                    continue
                if v > best:
                    best = v
            except cambc.Error:
                pass
        b += best
    return b


def sides(me, pos, foes):
    """(our strength, theirs, ally positions) over the bodies seen within WATCH_RADIUS. Strength =
    summed dps x summed HP: Lanchester's square law for focus fire (P11, provisional A39). Allies'
    dps from their type (plan.TYPE_DPS), enemies' from strength x C.ENEMY_SPELLS."""
    dps, hp = camp_dps(me), me.health()
    pts = []
    for p in vision.champion_tiles(ALLY).positions():
        if (p.x != pos.x or p.y != pos.y) and cheb_xy(p.x, p.y, pos.x, pos.y) <= C.WATCH_RADIUS:
            try:
                u = vision.champion_at(p)
                dps += plan.TYPE_DPS[int(u.champion_name())]
                hp += u.health()
                pts.append(p)
            except cambc.Error:
                pass
    edps = ehp = 0.0
    for e in foes:
        try:
            edps += e.strength() * C.ENEMY_SPELLS
            ehp += e.health()
        except cambc.Error:
            pass
    return dps * hp, edps * ehp, pts


def gems_of(e):
    try:
        return e.gem_count()        # any visible champion's real bag [sdk] [measured A18]
    except cambc.Error:
        return 0


def fight(me, now, foes, camps, hp, maxhp, gems, took_dmg):
    """L5. Reflexes first: a kill we can finish this turn (P15, P13: their bag and 50 gold
    [rules]); hit back a melee champion that is hitting us (walking away from melee fails).
    Then fight an enemy at <= P["fight_frac"] HP, only if not outnumbered in view, our bag is
    small, and we win the race (P4: only fight battles already won; P8: strike the weak).
    Returns True if it used the turn."""
    pos = me.position()
    near = []
    for e in foes:
        try:
            ep = e.position()
            near.append((cheb_xy(ep.x, ep.y, pos.x, pos.y), e.health(), e))
        except cambc.Error:
            pass
    if not near:
        return False
    for d, eh, e in sorted(near, key=lambda n: n[1]):
        if d <= 4 and eh <= burst(me, e, d):
            strike(me, e, False)
            return True
    if took_dmg and C.FIGHT_BACK:
        for d, eh, e in near:
            try:
                if d <= 1 and e.attack_range() <= 1:
                    strike(me, e, False)
                    return True
            except cambc.Error:
                pass
    if S["mode"] or gems >= C.FIGHT_BAG_MAX:
        return False
    allies = focus = 1
    for p in vision.champion_tiles(ALLY).positions():
        if p.x != pos.x or p.y != pos.y:
            d = cheb_xy(p.x, p.y, pos.x, pos.y)
            if d <= C.WATCH_RADIUS:
                allies += 1
            if d <= C.FIGHT_RADIUS:
                focus += 1      # close enough to hit the same target with us (P10)
    if C.ENGAGE:
        ours, theirs = T["sides"][:2]
        if ours < C.ENGAGE_FIGHT * theirs:
            return False
    elif len(near) > allies:
        return False
    their = sum(c[2] for c in camps)
    for d, eh, e in near:
        try:
            their += e.strength()
        except cambc.Error:
            pass
    best = None
    dps = camp_dps(me) * focus
    # P8: the weakest or the most loaded first (a kill pays their whole bag [rules]).
    for d, eh, e in sorted(near, key=lambda n: n[1] - 10 * gems_of(n[2])):
        try:
            if d > C.FIGHT_RADIUS or eh > P["fight_frac"] * e.max_health():
                continue
        except cambc.Error:
            continue
        t_kill = eh / dps
        t_die = hp / max(their, 1.0)
        if t_kill <= C.FIGHT_EDGE * t_die:
            best = (d, e)
            break
    if best is None:
        return False
    d, e = best
    if d > me.attack_range():
        ep = e.position()
        step_to(me, (ep.x, ep.y), None)
    strike(me, e, False)
    return True


def desperate(me, now, enemies, took):
    """P21 / XI.14 (on desperate ground, fight): a flight from enemy champions that has not widened
    the gap in C.DESPERATE_ROUNDS while we keep taking damage cannot escape; turn and strike the
    weakest enemy we can reach, bag or not (a death loses it anyway [rules]). True if it struck."""
    pos = me.position()
    near = []
    for e in enemies:
        try:
            ep = e.position()
            near.append((cheb_xy(ep.x, ep.y, pos.x, pos.y), e.health(), e, ep))
        except cambc.Error:
            pass
    if not near:
        return False
    gap = min(n[0] for n in near)
    f = S["flee"]
    if f is None or now - f[2] > 1:
        S["flee"] = (now, gap, now)
        return False
    S["flee"] = (f[0], f[1], now)
    if not took or now - f[0] < C.DESPERATE_ROUNDS or gap > f[1]:
        return False
    rng = me.attack_range()
    reach = rng + (1 if rng <= 1 else 0)    # melee may step and hit in one turn [rules]
    cand = [n for n in near if n[0] <= max(reach, 4)]
    if not cand:
        return False
    d, eh, e, ep = min(cand, key=lambda n: (n[0] > reach, n[1]))
    if d > rng and rng <= 1:
        step_to(me, (ep.x, ep.y), None)
    return strike(me, e, False)


def parting_shot(me):
    """A melee body walks and attacks in one turn [rules]: with the attack unused, hit the weakest
    enemy champion in range (fleeing, healing or banking alike). P8."""
    if not me.can_attack():
        return
    pos = me.position()
    rng = me.attack_range()
    best = None
    for e in enemies_near(pos, rng):
        try:
            h = e.health()
            if best is None or h < best[0]:
                best = (h, e)
        except cambc.Error:
            pass
    if best is not None:
        try:
            me.attack(best[1])
        except cambc.Error:
            pass


def shop_trip_due(me, now):
    """L3 + L4: between targets with an emblem's worth of gold, go home to shop (P2: stats
    speed every later clear). Not late in the game, not with gems (bank first)."""
    if not C.RECALL or S["no_trip"] or me.gem_count() or K.MAX_ROUNDS - now <= C.SHOP_TRIP_LAST or \
            world.SPAWN.is_set(me.position()):
        return False
    try:
        return me.gold_count() >= max(C.SHOP_TRIP_GOLD, next_item().cost())
    except cambc.Error:
        return False


def follow(me, now):
    """Squad mate (P10: concentrate): join the take our leader claims, once we are not mid-clear or
    capturing. If the leader drops the take we joined, keep a group already started (solo), else
    choose again."""
    st, gi = status_of(S["leader"])
    want = gi if st == TAKING and 0 <= gi < len(world.GROUPS) else None
    if want is not None and S["skip"][0] == want and now < S["skip"][1]:
        want = None     # we gave up waiting there (TAKE_WAIT_MAX): don't rejoin and wait again
    grp = S["target"]
    if want is not None and grp is not None and grp.i == want and S["take"]:
        S["following"] = want
        return
    if want is None and S["following"] is None:
        return
    busy = grp is not None and (now - S["hit_round"] <= 2 or
                                (grp.state == 1 and grp.tiles.is_set(me.position())))
    if want is None:
        S["following"] = None
        if grp is not None and S["take"]:
            S["take"] = False
            if not busy and grp.state != 1 and all(h == m for h, m in zip(grp.hp, grp.maxhp)):
                S["target"] = None      # untouched: choose again
            claim(S["target"])
        return
    if busy:
        return
    grp = world.GROUPS[want]
    S["target"], S["take"], S["take_since"], S["following"], S["opening"] = grp, True, None, want, None
    S["target_d"] = 65535
    claim(grp)


def farm(me, now, safe=True):
    if S["leader"] is not None:
        follow(me, now)
    grp = S["target"]
    if grp is None or (grp.state == 2 and grp.back_at - now > C.WAIT_RESPAWN_MAX):
        if shop_trip_due(me, now) and (safe or SPAWN_FIELD.at(me.position()) <= P["recall_walk"]):
            S["target"] = None
            S["take"] = False
            claim(None, HOME)
            return go_heal(me, safe)
        grp = S["opening"]
        S["opening"] = None
        S["target_d"] = 65535
        S["take"] = False
        if grp is None or grp.i in board()[0]:
            grp, S["take"] = choose(me, now)
            mark("choose")
        S["target"] = grp
        S["take_since"] = None
        claim(grp)
        if grp is None:
            return go_bank(me) if me.gem_count() else go_heal(me, safe)
    if grp.state == 0 and now - max(S["still"][1], S["hit_round"]) > C.STUCK_ROUNDS:
        # Neither moved nor hit a camp for a while on a live group: something we don't model
        # blocks us (P18: adapt, don't repeat). Drop it and choose again.
        leave(grp, now, C.TAKE_SKIP)
        S["still"] = (S["still"][0], now)
        return False
    pos = me.position()
    ct = T["ct"]
    cells = grp.cells
    live = [j for j, p in enumerate(cells) if ct.is_set(p)]
    nav = world.nav(grp)
    mark("nav")
    if live and S["take"]:
        return take(me, grp, live, now)
    if live:
        rng = me.attack_range()
        cand = [j for j in live if cheb(cells[j], pos) <= rng]
        if not cand:
            # Near the group, walk to the nearest live camp: the field ends on any spawn tile, and
            # a melee body on a cleared one can be out of reach of the rest [measured 14 Oct, rows].
            if nav.at(pos) <= 2:
                p = cells[min(live, key=lambda j: cheb(cells[j], pos))]
                step_to(me, (p.x, p.y), nav)
            else:
                step_field(me, nav)
            pos = me.position()
            cand = [j for j in live if cheb(cells[j], pos) <= rng]
        targets = []
        for j in cand:
            c = camp(cells[j])
            if c is not None:
                try:
                    h = c.health()
                    if h != grp.hp[j]:
                        grp.hp[j] = h
                        world.recost(grp)
                    targets.append((j, c))
                except cambc.Error:
                    pass
        if targets:
            # P8 + Smith's rule: most strength per HP first, clusters last.
            strs, hps = grp.str, grp.hp
            j, c = min(targets, key=lambda t: (strs[t[0]] <= 0, -strs[t[0]] / max(hps[t[0]], 1), hps[t[0]]))
            if strike(me, c, True):
                S["hit_round"] = now
        return True
    if not (grp.tiles & T["vis"]).is_empty():
        refresh(grp, now)       # the target only: catches our own capture and enemy steals
    if grp.state == 1:
        if C.TAKE and capture_left_to_ally(grp, pos):
            leave(grp, now, K.CAPTURE_TIME + 3)
            return True
        if grp.tiles.is_set(pos):
            return True         # capturing: stand still [rules: 5 rounds uncontested]
        return step_field(me, nav)
    if grp.state == 2:
        # Never wait on a spawn tile: "any occupied spawn tile delays the entire group" [rules].
        if grp.tiles.is_set(pos):
            return step_off(me, nav)
        if nav.at(pos) <= C.RESPAWN_WAIT_DIST:
            return True
    return step_field(me, nav)


def cheb(a, b):
    return cheb_xy(a.x, a.y, b.x, b.y)


# ---------------------------------------------------------------- the turn

def trace(me, now, *extra):
    tgt = S["target"]
    print(f"T|{now}|{cambc.ChampionType.to_string(int(me.champion_name())).rsplit('.', 1)[-1]}|"
          f"hp={int(me.health()) if me.is_alive() else 0} gems={me.gem_count()} gold={me.gold_count()} "
          f"mode={S['mode']} tgt={None if tgt is None else (tgt.i, tgt.state)} take={int(S['take'])} "
          f"bank={int(S['banking'])} idle={S['idle']} "
          f"pos={me.position() if me.is_alive() else None} fuelmax={S['fuel_max']} "
          f"{' '.join(map(str, extra))}", flush=True)


def idle(me, now, p0):
    """Count rounds we did nothing useful (every round should farm, bank, heal or fight)."""
    if me.is_recalling() or me.is_submitting_gems() or me.is_teleporting() or not me.can_attack() \
            or me.position() != p0 or world.SPAWN.is_set(p0):
        return
    tgt = S["target"]
    if S["mode"]:
        why = "heal"
    elif tgt is None:
        why = "none"
    elif tgt.state == 1 and tgt.tiles.is_set(p0):
        return          # capturing: standing still is the work [rules]
    elif S["take"]:
        why = "take"
    else:
        why = ("farm", "cap", "resp")[tgt.state]
    S["idle"][why] = S["idle"].get(why, 0) + 1


PROF = []


def mark(label):
    """Fuel checkpoint for the per-turn profile line (TRACE only)."""
    if C.TRACE:
        PROF.append((label, cambc.fuel_remaining()))


def turn():
    f0 = cambc.fuel_remaining()
    me = cambc.me()
    now = cambc.round_number()
    if not S["ready"]:
        init(me)
        if C.TRACE:
            trace(me, now, "init", f0 - cambc.fuel_remaining(), C.STRATEGY_NAMES[S["strategy"]], S["types"])
    elif C.TRACE and now % C.TRACE == 0:
        trace(me, now)
    PROF.clear()
    PROF.append(("start", f0))
    T.clear()
    T["camps"] = {}
    p0 = me.position() if me.is_alive() else None
    play(me, now)
    if C.PARTING_SHOT and p0 is not None:
        try:
            if me.is_alive() and me.attack_range() <= 1 and not (me.is_recalling() or me.is_submitting_gems()):
                parting_shot(me)
        except cambc.Error:
            pass
    if C.TRACE and p0 is not None:
        idle(me, now, p0)
    used = f0 - cambc.fuel_remaining()
    if (TODO or THEM is None) and S["ready"]:
        prebuild()
    if used > S["fuel_max"] and now > 1:
        S["fuel_max"] = used
    if C.TRACE and used > C.PROFILE_OVER and now > 1:
        PROF.append(("end", f0 - used))
        print(f"T|{now}|fuel|{used}|" + " ".join(f"{PROF[i][0]}={PROF[i - 1][1] - PROF[i][1]}"
                                                 for i in range(1, len(PROF))), flush=True)


def play(me, now):
    if not me.is_alive():
        if C.TRACE and S["last"]:
            name = cambc.ChampionType.to_string(int(me.champion_name())).rsplit('.', 1)[-1]
            print(f"T|{now}|death|{name} {S['last']}", flush=True)     # the turn before we died
            S["last"] = None
        shop(me)
        S["target"] = None
        S["mode"] = 0
        S["take"] = False
        S["banking"] = False
        claim(None, DEAD)
        return
    if me.is_submitting_gems() or me.is_teleporting():
        return
    if me.is_recalling():
        # L3: any damage cancels a recall [rules]; cancel it ourselves while we can still act.
        if not (C.RECALL and enemies_near(me.position(), C.WATCH_RADIUS)):
            return
        try:
            me.cancel_recall()
        except cambc.Error:
            return
    pos = me.position()
    if S["still"][0] != (pos.x, pos.y):
        S["still"] = ((pos.x, pos.y), now)
    sense(me, now)
    mark("sense")
    hp, maxhp = me.health(), me.max_health()
    if world.SPAWN.is_set(pos):
        shop(me)
        try:
            if me.gold_count() >= next_item().cost():
                S["no_trip"] = True     # the shop won't sell to us: never recall to shop again
        except cambc.Error:
            S["no_trip"] = True
        hp, maxhp = me.health(), me.max_health()
        S["bank_best"] = (65535, 0, 0)
        if S["mode"] and hp >= maxhp * 0.95:
            S["mode"] = 0
            claim(S["target"])
    gems = me.gem_count()
    if not gems:
        S["banking"] = False
        S["bank_best"] = (65535, 0, 0)
    foes = enemies_near(pos, C.WATCH_RADIUS)
    if foes:
        S["enemy_seen"] = now
    enemies = [e for e in foes if cheb(e.position(), pos) <= 4]
    if not enemies:
        S["flee"] = None
    took = hp < S["hp_last"] - 0.5
    hurt = took and not enemies
    S["hp_last"] = hp
    camps = hot_camps(pos, hurt)
    hot = S["hot"]
    for c in camps:
        hot[(c[0].x, c[0].y)] = now
    if hot:
        for k in [k for k, r in hot.items() if now - r > C.HOT_MEMORY]:
            del hot[k]
    safe = not foes and not camps      # L3: nothing can interrupt a recall (P4)
    if S["take"] and camps:
        # R8: in a take a monster hits its nearest champion [rules]; one with an ally strictly
        # nearer is not ours to retreat from (the tank soaks it).
        mates = [(p.x, p.y) for p in vision.champion_tiles(ALLY).positions() if p.x != pos.x or p.y != pos.y]
        camps = [c for c in camps
                 if not any(cheb_xy(c[0].x, c[0].y, a, b) < cheb_xy(c[0].x, c[0].y, pos.x, pos.y) for a, b in mates)]
    mark("seen")
    incoming = sum(c[2] for c in camps) + sum(e.strength() for e in enemies)
    threats = [c[0] for c in camps] + [e.position() for e in enemies]
    if C.TRACE:
        S["last"] = (f"r{now} hp={int(hp)} gems={gems} mode={S['mode']} pos=({pos.x},{pos.y}) "
                     f"tgt={None if S['target'] is None else S['target'].i} bank={int(S['banking'])} "
                     f"camps={[(p.x, p.y, s) for p, c, s in camps]} "
                     f"en={[(e.position().x, e.position().y, int(e.health())) for e in foes]}")

    # Survive first (P4): don't stand in damage we can't take; never die with gems.
    if incoming:
        rounds = S["retreat"]
        if C.ESCAPE and camps:
            ex = exit_tile(pos, [(c[0].x, c[0].y) for c in camps])
            if ex is not None and ex[0] + 1 > rounds:
                rounds = ex[0] + 1      # the rounds we keep taking hits on the way out
        if hp < incoming * rounds + 0.1 * maxhp:
            S["mode"] = 1
    # L5: kills we can finish, hitting back at melee, and fights already won (P4, P8).
    if C.ENGAGE and foes:
        T["sides"] = sides(me, pos, foes)
    if C.FIGHT and foes and fight(me, now, foes, camps, hp, maxhp, gems, took):
        return
    if C.FLEE and foes and not world.SPAWN.is_set(pos):
        allies = 1
        for p in vision.champion_tiles(ALLY).positions():
            if (p.x != pos.x or p.y != pos.y) and cheb_xy(p.x, p.y, pos.x, pos.y) <= C.WATCH_RADIUS:
                allies += 1
        if C.ENGAGE:
            ours, theirs, friends = T["sides"]
            outn = ours < C.ENGAGE_FLEE * theirs
        else:
            friends = ()
            outn = len(foes) > allies or (S["linked"] and len(foes) >= allies)    # the pair: even is too risky
        if outn:
            # Outnumbered (P4: don't fight battles not already won; P9: farm where they are not).
            # Don't wait to be hit: leave the group to them and get clear while we still can.
            if C.DESPERATE and enemies and desperate(me, now, enemies, took):
                return
            tgt = S["target"]
            if tgt is not None and world.nav(tgt).at(pos) <= C.WATCH_RADIUS:
                leave(tgt, now, C.TAKE_SKIP)
            step_away(me, threats + [e.position() for e in foes], friends)
            return
    if S["mode"]:
        if S["slot"] is not None and cambc.shared_memory[S["slot"]] >> 6 != HOME:
            claim(S["target"], HOME)    # mates stop waiting for us (elkring 14 Oct: 55 rounds)
        if not threats and hot:
            # A camp that just hit us is still awake [rules]: don't walk back into its range on the
            # way home (Issac bounced in and out of a wolf pack's range and died, elkring 14 Oct).
            threats = [cambc.Vec2(x, y) for (x, y) in hot if cheb_xy(x, y, pos.x, pos.y) <= C.CAMP_RANGE + 1]
            if C.ESCAPE and safe and SPAWN_FIELD.at(pos) > P["recall_walk"]:
                threats = []            # out of range and recalling, not walking: monsters don't chase [rules]
        if C.DESPERATE and enemies and desperate(me, now, enemies, took):
            return
        if threats and C.ESCAPE and not enemies:
            escape(me, [(t.x, t.y) for t in threats])
        elif threats:
            step_away(me, threats)      # recall is cancelled by any damage [rules]: get clear first
        elif gems and ALTAR_FIELD.at(pos) <= C.BANK_NEAR + 2 and not stalled(ALTAR_FIELD.at(pos), now):
            go_bank(me)
        else:
            go_heal(me, safe)
        return

    # Bank (L2): tributed gems are the only score. Once started, a bank trip runs to the altar.
    alt = ALTAR_FIELD.at(pos)
    must = K.MAX_ROUNDS - now <= alt + gems // 10 + C.END_MARGIN or \
        gems + cambc.global_submitted_gems(ALLY) >= K.WINNING_GEMS
    tgt = S["target"]
    capturing = tgt is not None and tgt.tiles.is_set(pos) and tgt.state < 2 and not any(h > 0 for h in tgt.hp)
    # P10: a take in progress keeps its bodies; leaving the tank alone mid-clear wastes both
    # (elkring 14 Oct: Vendetta went to bank, Ryth tanked alone 1200 -> 180 and the group stayed).
    mid_take = S["take"] and tgt is not None and tgt.state == 0 and \
        any(h < m for h, m in zip(tgt.hp, tgt.maxhp)) and not world.nav(tgt).at(pos) > C.TAKE_RADIUS
    if gems and not capturing and alt < C.UNREACHED:
        if not S["banking"] and (must or (not mid_take and bank_due(me, pos, gems, alt, now))):
            S["banking"] = True
        if S["banking"]:
            if stalled(alt, now) and not must:
                S["mode"] = 1       # blocked on the way: heal, then come back stronger (P4)
                go_heal(me, safe)
            else:
                go_bank_trip(me, pos, alt, safe)
            return

    # Low and idle: heal before the next camp.
    if hp < 0.5 * maxhp and not camps:
        S["mode"] = 1
        go_heal(me, safe)
        return

    farm(me, now, safe)
