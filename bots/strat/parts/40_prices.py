"""Sense, price the six options (strat/PRICES.md) in team gems per round, choose with hysteresis, broadcast.

Option codes (shared byte, low 3 bits): 0 idle (also heal: recalling to heal, target 0; and ward: target = ward
index + 1, so a byte of 8/16/24 is "walking to place ward 0/1/2"), 1 farm, 2 bank, 3 kill, 4 hold, 5 shop, 6 join,
7 dead; target in the high 5 bits (group index in draft-memory order, altar index, enemy handle & 31, ally slot for join).
Byte 5: enemy sighting, high 3 bits = enemies seen together (within SIGHT_R of one of them, capped 7; 0 = none), low
5 bits = (round // 4) & 31 when seen. Byte 6: the sighting's region, index of the altar nearest the cluster.
A reader treats age >= SIGHT_LIVE rounds as stale and clears byte 5. Byte 7: group death marker (90_main).
Layout: strat/MEMORY_LAYOUT.md, "Shared 8 bytes".
"""

KEEP_HP = 0.4               # [guess] the hit body keeps >= 40 % of max HP (KEEP_FRAC)
HYST = 1.2                  # switch only when a new option beats the current one by 20 %
EXCL = 20                   # rounds an (option, target) is excluded after a timeout / failure
DENIAL = 24                 # [measured-ish] their farm rate 0.4 g/r x 60 rounds out (PRICES KILL)
THEIR_RATE = 0.4            # [guess] their gems per round per body (HOLD value 30 x 0.4)
P_NEAR = 0.5                # [guess] P(lose the bag) with an enemy within 8
DANGER_W = 0.2              # [guess] P(lose the bag) per unit of draft danger (cell value / 14)
SHOP_RETURN = True          # [deviation] SHOP rounds include the walk back from spawn to where I am
SURVIVE = 0.6               # [tuned] k bodies are enough if the most-hit body keeps > 40 % of its current HP
WAIT_PARTNER = 15           # [guess] rounds added to a pair take while the partner is not committed
FUEL_FLOOR = 400_000        # after sensing: below this skip pricing, repeat the executor step
P_LOSE_MAX = 0.5            # [guess] FARM / BANK / KILL price 0 when the local Lanchester P(lose) exceeds this
FARM_PLOSE = 0.99           # [tuned] off: 0.65 (2 v 1) lost corners and interlock (we must contest the centre)
HOLD_PLOSE = 0.3            # [guess] HOLD needs a clearly safe altar
KILL_PLOSE = 0.45           # [tuned] fight only when locally stronger (0.5 = even; 0.99 lost 9 champions in kills)
DEATH_EXCL = 100            # rounds a death excludes its (option, target), and kill/hold after a kill/hold death
DEATH_MARK = 100            # rounds the team avoids a group an ally died farming (byte 7)
HEAL_K = 2.0                # [guess] (1.5 -> 2.0, 15 Oct ladder phase 1) HEAL: P(die) = clamp((1 - hp/maxhp) x (1 + enemies within 8) x HEAL_K, 0, 1)
MY_RATE = 0.4               # [guess] my gems per round, x 60 rounds out = what a death costs beyond the bag
HOLD_TURNS = 2              # a new (option, target) is kept this many turns (unless done/failed, HEAL, retreat)
WARD_VALUE = 4.0            # [guess] g/r of a ward placed at once (8 -> 4: at 8 it outranked every farm, 1-5 g/r)
WARD_FROM = 10              # [guess] no ward option before this round (round 3: every idle champion chose a ward)
WARD_WALK = 30              # [guess] WARD price = WARD_VALUE x WARD_WALK / (WARD_WALK + walk): 4 here, 1.7 at 40 tiles
WARD_TRIES = 3              # choices of one ward tile per champion before I give it up (timeouts / stuck re-choose it)
WARD_DETOUR = 5             # [guess] WARD prices only when walk(me->ward) + walk(ward->goal) - walk(me->goal) <= this
BANK_NEAR = 8               # [guess] walk to the altar at or below which BANK gets the tempo bonus
BANK_NEAR_BONUS = 1.0       # [guess] BANK x (1 + this) when the altar is near: a 22-gem bag next to an altar banks now
KILL_PER_SHARD = 0.15       # [guess] KILL multiplier = prof kill + this x shards owned (emblems count their shards)
SIGHT_LIVE = 32             # rounds a sighting stays in byte 5 (readers clear it after; the stamp wraps at 128)
SIGHT_FRESH = 8             # rounds a sighting drives posture (defend / punish) and the stack terms
SIGHT_OVER = 12             # a weaker sighting overwrites a stronger one older than this
SIGHT_R = 8                 # enemies within this of each other count as seen together
STACK_N = 3                 # a fresh sighting of >= this many enemies is "the stack"
STACK_N_FEW = 2             # [guess] regime few (small / one-choke maps): a pair already counts as the stack
STACK_R = 10                # FARM of groups within this of the stack's altar x STACK_FARM
STACK_FARM = 0.2            # [guess] don't walk into the stack
PUNISH_LEAD = 50            # ahead by more than this on score + a fresh small sighting -> punish
STACK_HEAL = 0.6            # [guess] HEAL P(die) floor with >= 3 enemies within 8 and no ally within 5
# Posture columns: multipliers over the options (price *= POSTURE[col][key]), neutral 1.0, all [guess].
# Selection (posture(), every champion locally, same inputs, no byte): draft regime few -> defend, pick / many /
# unknown -> economy; a fresh sighting (<= SIGHT_FRESH rounds) of >= STACK_N enemies -> defend; a fresh one of <= 2
# while we lead by > PUNISH_LEAD -> punish. Our side of an enemy: its nearest altar has draft side 0 or 1; theirs: 2.
_PK = ("farm", "farm_their_side", "bank_risk", "kill_our_side", "kill_their_side", "hold", "shop", "join", "ward")


def _col(**kw):
    c = dict.fromkeys(_PK, 1.0)
    c.update(kw)
    return c


POSTURE = {
    "economy": _col(),                          # open maps: the baseline prices as they are
    # defend [guess all]: farm_their_side 0.3 their half is where the stack lives; bank_risk 1.5 cash the bag before
    # it is caught; kill_our_side 1.3 intruders on our half are near help; kill_their_side 0.5 no dives into them;
    # hold 1.3 deny tributes at contested altars; join 1.3 move in pairs.
    # join 2.0 [guess, 15 Oct ladder phase 1; was 1.3]: on few maps move in pairs.
    "defend": _col(farm_their_side=0.3, bank_risk=1.5, kill_our_side=1.3, kill_their_side=0.5, hold=1.3, join=2.0),
    # punish [guess all]: a small group seen while we lead: fight it, mostly on our half; bank a bit sooner.
    "punish": _col(kill_our_side=1.4, kill_their_side=1.1, bank_risk=1.2),
}
OPT = ("idle", "farm", "bank", "kill", "hold", "shop", "join", "dead", "fall")
CODE = {o: i for i, o in enumerate(OPT)}
CODE["heal"] = 0            # broadcast as idle: the byte has no free code (7 is dead)
CODE["ward"] = 0            # idle code with target = ward index + 1 (see broadcast)
CLEAR_MEMO = {}


class Snap:
    __slots__ = ("r", "st", "alive", "recalling", "submitting", "can_move", "can_attack", "pos", "hp", "maxhp",
                 "bag", "gold", "S", "enemies", "allies", "live", "vis", "mem", "spawn", "near_e", "P", "walt", "edps", "plose",
                 "sc", "sa", "sage", "stack")


def sense(w):
    me, r = w.me, cambc.round_number()
    s = Snap()
    s.r = r
    s.st = st = int(me.state())
    s.alive = bool(st & 1)
    s.recalling, s.submitting = bool(st & 2), bool(st & 4)
    s.can_move, s.can_attack = bool(st & 8), bool(st & 16)
    try:
        s.gold = me.gold_count()
    except Exception:
        s.gold = 0
    try:
        w.score = (cambc.global_submitted_gems(Team.ALLY), cambc.global_submitted_gems(Team.ENEMY))
    except Exception:
        pass
    s.mem = bytearray(8)
    try:
        cambc.shared_memory.read(0, s.mem)
    except Exception:
        pass
    sb = s.mem[5]                               # sighting: count, region altar, age in rounds (4-round stamp)
    s.sc, s.sa = sb >> 5, s.mem[6]
    s.sage = (((r // 4) - (sb & 31)) & 31) * 4 if s.sc else 999
    s.stack = s.sc >= stack_n(w) and s.sage <= SIGHT_FRESH and s.sa < len(w.apos)
    s.enemies, s.allies, s.live, s.near_e = [], [], {}, 99
    if not s.alive:
        s.pos, s.hp, s.maxhp, s.bag, s.S, s.vis, s.spawn = w.pos, 0, 1, 0, 1, None, False
        return s
    s.pos = pos = me.position()
    s.hp, s.maxhp, s.bag, s.S = me.health(), me.max_health(), me.gem_count(), max(1.0, me.strength())
    s.spawn = w.sp.is_set(pos)
    for c in champs(Team.ENEMY):
        try:
            p = c.position()
            dd = pos.chebyshev_distance(p)
            s.enemies.append((c, p, c.health(), c.gem_count(), dd, c.strength()))
            if dd < s.near_e:
                s.near_e = dd
        except Exception:
            pass
    for c in champs(Team.ALLY):
        try:
            p = c.position()
            if p != pos:
                s.allies.append((c, p, c.health(), c.strength()))
        except Exception:
            pass
    s.vis = None
    hs = list(w.near6)
    cur = w.cur
    if cur[0] == "farm" and cur[1] not in hs and cur[1] in w.G:
        hs.append(cur[1])
    for h in hs:                                # boot Camp objects: no vision.camps() (~540k on 2.1.4)
        o = w.G[h]
        if o.anchor.chebyshev_distance(pos) > 11:
            continue
        lv = []
        for c, t in zip(o.camps, o.tiles):
            try:
                if c.is_visible():
                    lv.append((c, c.health(), t, G_HP[int(c.kind())][1]))
            except Exception:
                pass
        if lv:
            s.live[h] = lv
    return s


def champs(team):
    """vision.champions, with a per-tile fallback when the list read raises (docs/HANDOFF.md)."""
    try:
        return vision.champions(team)
    except Exception:
        out = []
        try:
            for p in vision.champion_tiles(team).positions():
                try:
                    out.append(vision.champion_at(p))
                except Exception:
                    pass
        except Exception:
            pass
        return out


def visible(w, s, o):
    if s.vis is None:
        s.vis = vision.visible_tiles()
    return not (s.vis & o.obj.spawn_tiles()).is_empty()


def update_groups(w, s, hs):
    """Refresh the remembered state of groups hs from what I see (state() only when no live camp is visible)."""
    for h in hs:
        o = w.G[h]
        lv = s.live.get(h)
        if lv:
            o.st, o.seen = "alive", s.r
            cur = [(hp, st) for _c, hp, _p, st in lv]
            if len(lv) < len(o.camps) and not visible_all(w, s, o):
                cur += o.mons[:len(o.camps) - len(lv)]        # unseen camps: assume alive, full HP
            o.hp = cur
            continue
        if o.seen == s.r or not visible(w, s, o):
            continue
        try:
            gs = o.obj.state()
        except Exception:
            continue
        o.seen = s.r
        if isinstance(gs, game_map.CampGroupRewardAvailable):
            o.st, o.hp = "reward", []
        elif isinstance(gs, game_map.CampGroupRespawning):
            o.st, o.hp = "resp", None
            try:
                o.until = s.r + int(gs.cooldown) + 1
            except Exception:
                o.until = s.r + o.resp
        else:
            o.st = "alive"


def visible_all(w, s, o):
    if s.vis is None:
        s.vis = vision.visible_tiles()
    t = o.obj.spawn_tiles()
    return (s.vis & t) == t


def claims(w, s):
    """{group handle: allies broadcasting farm/join on it}, {slot: (opt, tgt)}."""
    cl, by = {}, {}
    for k in range(5):
        if k == w.slot:
            continue
        b = s.mem[k]
        op, tg = b & 7, b >> 3
        by[k] = (op, tg)
        if op == 1 and tg in w.idx:
            h = w.idx[tg]
            cl[h] = cl.get(h, 0) + 1
    return cl, by


def danger_p(w, s):
    if s.near_e <= 8:
        return P_NEAR
    d = w.d
    if d and d.get("danger"):
        v = d["danger"][(s.pos.y * GRID // w.Hm) * GRID + s.pos.x * GRID // w.Wm]
        if v < 15:
            return DANGER_W * v / 14
    return 0.0


def farm_price(w, s, h, bodies, walk):
    o = w.G[h]
    if o.st == "resp" and o.until > s.r:
        return 0.0
    prof = ME["prof"]
    value = o.gems + g2g(s.r) * o.gold * prof["gold"]
    if o.st == "reward":
        return value / max(1, bodies) / (walk + 5)
    if o.hp is None:                            # full HP: cached per (group, bodies, my Strength)
        key = (h, bodies, s.S)
        cd = CLEAR_MEMO.get(key)
        if cd is None:
            if len(CLEAR_MEMO) > 400:
                CLEAR_MEMO.clear()
            cd = CLEAR_MEMO[key] = clear_dmg(o.mons, s.S, bodies)
        clear, dmg = cd
    else:
        mons = [m for m in o.hp if m[0] > 0]
        if not mons:
            return value / max(1, bodies) / (walk + 5)
        clear, dmg = clear_dmg(mons, s.S, bodies)
    per = dmg / bodies + s.edps * min(clear + 5, 10)    # [tuned] + visible enemies hitting me (within 4)
    if per >= s.hp:
        return 0.0                                  # [deviation] certain death is not a price
    miss = bodies - 1 - w.claims.get(h, 0)
    if miss > 0:
        walk += WAIT_PARTNER * miss                 # [guess] partners not committed yet
    risk = s.bag if s.hp - per < KEEP_HP * s.maxhp else s.P * s.bag   # [tuned] bag exposure (danger_p)
    detour = 0
    if o.near < len(w.apos):
        detour = max(0, o.anchor.chebyshev_distance(w.apos[o.near]) - s.walt)
    return value / bodies / (walk + clear + 5 + detour) - risk


def need_k(w, s, h, c):
    """Smallest k >= 1 + c (claimants + me), at most the team, whose most-hit body keeps KEEP_HP (live clear model:
    my HP and Strength, monsters' remembered HP); None if no team size does. Pair takes price with this k and pay
    WAIT_PARTNER per body not yet committed, so the first champion claims and the second sees one claimant."""
    o = w.G[h]
    if o.st != "alive":
        return 1 + c
    mons = o.mons if o.hp is None else [m for m in o.hp if m[0] > 0]
    if not mons:
        return 1 + c
    T = max(1, len(w.roster))
    floor = s.hp * SURVIVE                      # survival, as FARM's own zero rule (KEEP_HP stays a risk term)
    for k in range(1 + c, T + 1):
        key = (h, k, s.S) if o.hp is None else None
        cd = CLEAR_MEMO.get(key) if key else None
        if cd is None:
            cd = clear_dmg(mons, s.S, k)
            if key:
                CLEAR_MEMO[key] = cd
        if cd[1] / k + s.edps * min(cd[0] + 5, 10) <= floor:
            return k
    return None


def lanchester(s, e_pos):
    """P(we lose) from sum(hp x str) within 5 of the target on each side [guess, PRICES S2]."""
    us = s.hp * s.S if s.pos.chebyshev_distance(e_pos) <= 5 else 0
    for _c, p, hp, st in s.allies:
        if p.chebyshev_distance(e_pos) <= 5:
            us += hp * st
    th = 0
    for _c, p, hp, _b, _d, st in s.enemies:
        if p.chebyshev_distance(e_pos) <= 5:
            th += hp * st
    return th / max(1.0, us + th)


def stack_n(w):
    """STACK_N, or STACK_N_FEW on a regime-few map (draft) [guess]."""
    d = w.d
    return STACK_N_FEW if d and d.get("regime") == 0 else STACK_N


def posture(w, s):
    """Posture column (see POSTURE); traces `posture` when mine changes."""
    d = w.d
    col = "defend" if d and d.get("regime") == 0 else "economy"
    if s.sc and s.sage <= SIGHT_FRESH:
        if s.sc >= stack_n(w):
            col = "defend"
        elif w.score[0] - w.score[1] > PUNISH_LEAD:
            col = "punish"
    if col != w.post:
        w.post = col
        trace("posture", f"{col} sight={s.sc}@A{s.sa if s.sa < 255 else '-'} age={s.sage if s.sc else '-'} "
                         f"score={w.score[0]}-{w.score[1]} regime={d.get('regime') if d else '-'}")
    return POSTURE[col]


def e_side(w, p):
    """POSTURE key for a kill at p: kill_their_side if the altar nearest p has draft side 2, else kill_our_side."""
    if not w.apos:
        return "kill_our_side"
    a = min(range(len(w.apos)), key=lambda i: p.chebyshev_distance(w.apos[i]))
    return "kill_their_side" if w.aside[a] == 2 else "kill_our_side"


def ward_seen(w, s):
    """Drop pending ward tiles that already have an ally ward within 2 (seen when the tile is within vision 8)."""
    near = [j for j in w.ward_pending if w.wtiles[j].chebyshev_distance(s.pos) <= 8]
    if not near:
        return
    try:
        wt = vision.ward_tiles(Team.ALLY)
    except Exception:
        return
    if wt.is_empty():
        return
    for j in near:
        if not (wt & disk(w.wtiles[j], 2)).is_empty():
            w.ward_pending.discard(j)
            trace("ward", f"seen W{j}@{w.wtiles[j].x},{w.wtiles[j].y} placed by an ally")


def ward_goal(w, by):
    """(goal field or None, goal tile) of my current executor; (None, None) = no goal (idle / fall: wards are free);
    False = no ward now (kill, or a goal I cannot place)."""
    op, tg = w.cur
    if op in ("idle", "fall", "dead", "ward") and cambc.round_number() >= WARD_FROM:
        return None, None                       # ward: only the tile I am walking to prices (ward_prices)
    if op == "farm" and tg in w.G:
        return f"g{tg}", w.G[tg].anchor
    if op == "join" and tg in by:
        bo, bt = by[tg]
        h = w.idx.get(bt) if bo == 1 else None
        return (f"g{h}", w.G[h].anchor) if h in w.G else False
    if op in ("bank", "hold") and tg is not None and tg < len(w.apos):
        return f"a{tg}", w.apos[tg]
    if op in ("shop", "heal"):
        return "home", w.sp0
    return False                                # incl. idle / fall before WARD_FROM: never free then


def ward_prices(w, s, by, pm, out):
    """WARD price per pending tile j: WARD_VALUE x WARD_WALK / (WARD_WALK + walk to it) [guess], only on the way:
    detour = walk(me->ward) + walk(ward->goal) - walk(me->goal) <= WARD_DETOUR (walks from the cached goal fields
    and F_me, Chebyshev where none is cached). Skips tiles an ally is walking to (code 0, target j + 1)."""
    ward_seen(w, s)
    g = ward_goal(w, by)
    if g is False:
        return
    gkey, gt = g
    going = {tg - 1 for op, tg in by.values() if op == 0 and 1 <= tg <= 3}
    gf = w.nav.get(gkey) if gkey else None
    if gkey == "home" and gf is None:
        gf = w.F_home
    dmg = None
    if gt is not None:
        dmg = fget(gf, s.pos) if gf is not None else FAR
        if dmg >= FAR:
            dmg = s.pos.chebyshev_distance(gt)
    for j in w.ward_pending:
        if j in going or w.ward_tries.get(j, 0) >= WARD_TRIES or (w.cur[0] == "ward" and w.cur[1] != j):
            continue
        t = w.wtiles[j]
        cw = max(0, s.pos.chebyshev_distance(t) - 2)       # placement reach 2 [rules]
        if w.cur != ("ward", j) and gt is not None:
            # Chebyshev prefilter (a lower bound on the detour), then exact walks from the goal fields: the ward
            # field "w<j>" is built here on first need (~280k at 80x80, LRU-cached with the other goal fields).
            # A Chebyshev-only estimate sent Varg 13 rounds round a wall on collision (open1).
            if cw + max(0, t.chebyshev_distance(gt) - 2) - dmg > WARD_DETOUR:
                continue
        wk = fget(w.goal(f"w{j}"), s.pos)
        if wk >= FAR:                           # standing on a blocked tile (camp spawn): the F_me bound
            wk = max(cw, fget(w.F_me, t) - 2 - w.fme_root.chebyshev_distance(s.pos))
            if wk >= FAR - 4:
                continue
        if w.cur != ("ward", j) and gt is not None:
            dwg = fget(gf, t) if gf is not None else FAR
            if dwg >= FAR:
                dwg = t.chebyshev_distance(gt)
            if wk + dwg - dmg > WARD_DETOUR:
                continue
        out.append((WARD_VALUE * WARD_WALK / (WARD_WALK + wk) * pm["ward"], "ward", j))


def price_all(w, s, cl, by):
    """[(price, option, target)] for every option this turn (multipliers: champion row x posture column)."""
    prof, r = ME["prof"], s.r
    pm = posture(w, s)
    out = []
    # WARD: on the way, not first. A pending draft ward tile prices only when its detour from my current goal is
    # <= WARD_DETOUR, or when I am idle / falling back (or already walking to it); 0 once my ward is placed
    # [rule, 15 Oct ladder] price 0 while carrying gems (a 72-gem bag walked into 2 enemies for a ward) and none
    # before WARD_FROM (round 3: every idle champion's first choice was a ward)
    if not w.ward_done and w.ward_pending and s.bag == 0 and r >= WARD_FROM:
        ward_prices(w, s, by, pm, out)
    # FARM over the ~6 nearest groups by F_me (+ the current target, + cleared groups seen)
    cand = list(w.near6)
    cur = w.cur
    if cur[0] in ("farm", "join") and cur[1] is not None:
        hh = cur[1] if cur[0] == "farm" else None
        if hh is not None and hh not in cand:
            cand.append(hh)
    for h in s.live:
        if h in w.G and h not in cand and len(cand) < 9:
            cand.append(h)
    s.P = danger_p(w, s)
    s.edps = sum(e[5] for e in s.enemies if e[4] <= 4)
    s.walt = fget(w.F_alt, s.pos)
    s.plose = lanchester(s, s.pos) if s.enemies else 0.0
    dead_g = None
    b7 = s.mem[7]                               # death marker: group index + 1 (low 5 bits), (round // 32) & 7 stamp
    if b7 & 31 and (((r // 32) - (b7 >> 5)) & 7) * 32 < DEATH_MARK:
        dead_g = w.idx.get((b7 & 31) - 1)
    sap = w.apos[s.sa] if s.stack else None
    update_groups(w, s, cand)
    for h in cand:
        o = w.G[h]
        c = cl.get(h, 0)
        k = need_k(w, s, h, c)                  # bodies the live clear model needs, me + c claimants at least
        if k is None or (c == 0 and k >= 2 and r < w.pair_until):
            continue
        # One claimant per SOLO group: an ally broadcasts farm on a group the draft says needs 1 body -> 0 for me
        # (user's plan, 15 Oct late). Groups needing >= 2 keep the per-body split (value / bodies). History: the gate
        # on ALL groups (fix7/fix8) lost rows A and raised elkring deaths 5 -> 17-19 (elks under-bodied). Tried with
        # "and my live model could solo it": the weaker champion joined the stronger one's group and the stronger
        # one then left it (collision A, open1), so the draft's need decides alone.
        # [rule, 15 Oct ladder phase 1] tie-break by roster slot: only an ally with a LOWER slot zeroes it (the lower
        # slot keeps it); a higher slot sees mine and yields, so simultaneous choices settle in one turn.
        if o.need <= 1 and h in w.lowcl:
            continue
        if h == dead_g or (s.plose > FARM_PLOSE and s.near_e <= 5):
            continue                            # an ally died farming it recently, or outnumbered here
        wk = w.walk_to(f"g{h}", s.pos)
        if wk is None or wk >= FAR:
            wk = w.gd.get(h, FAR)
        if wk >= FAR:
            continue
        p = farm_price(w, s, h, k, wk) * prof["farm"] * pm["farm_their_side" if o.side == 2 else "farm"]
        if sap is not None and o.anchor.chebyshev_distance(sap) <= STACK_R:
            p *= STACK_FARM                     # the stack was just seen there
        out.append((p, "farm", h))
    # BANK
    if s.bag > 0 and w.apos:
        order = sorted(range(len(w.apos)), key=lambda i: w.ad[i])
        a = order[0]
        if w.aside[a] == 2 and w.bank < len(w.apos):
            a = w.bank
        if sap is not None:
            # [deviation] spec: "the altar farthest from the sighting among safe ones". Here safe = draft side 0/1,
            # reachable and more than STACK_R from the stack's altar, and the nearest such by walk wins (the
            # farthest can be across the map); none safe: the one farthest from the stack.
            ok = [i for i in order if w.aside[i] <= 1 and w.ad[i] < FAR]
            away = [i for i in ok if w.apos[i].chebyshev_distance(sap) > STACK_R]
            if away:
                a = away[0]
            elif ok:
                a = max(ok, key=lambda i: w.apos[i].chebyshev_distance(sap))
        wk = w.walk_to(f"a{a}", s.pos)
        if wk is None or wk >= FAR:
            wk = max(0, w.ad[a] - 1)
        if wk < FAR and not (s.near_e <= 4 and s.plose > P_LOSE_MAX):
            P = s.P
            # [deviation] the risk of holding the bag is ADDED to BANK (PRICES: "at bag >= 20 with an enemy
            # within 8, risk dominates and BANK wins"); subtracting it would stop every bank near an enemy.
            # BANK_NEAR_BONUS [guess]: tempo, a bag next to an altar banks now (ladder: 22 gems carried 40 rounds)
            near = 1 + BANK_NEAR_BONUS if wk <= BANK_NEAR else 1
            out.append((s.bag * (1 + P) * near / (wk + max(1, -(-s.bag // 10))) * prof["bank"] * pm["bank_risk"],
                        "bank", a))
    # KILL: closable targets only
    reach = ME.get("range", 1) + 1 + (2 if ME.get("has_dash") else 0)
    kmul = prof["kill"] + KILL_PER_SHARD * w.shards     # scales with shards owned (read every 20 rounds, 90_main)
    for c, p, hp, bag, dd, st in s.enemies:
        ttk = -(-int(hp) // int(s.S))
        fin = ttk <= 2                          # finisher: dies in <= 2 of my hits
        if r < w.kh_until and not fin:
            continue
        try:
            chan = c.is_submitting_gems() or c.is_recalling()
            stun = (not chan) and dd <= reach + 3 and c.buffs().has_stun()
        except Exception:
            chan = stun = False
        # P8 finisher: a recall / tribute pins >= 5 turn ends and a walker gains <= 1 tile/turn [rules], so a
        # near-dead target within reach + 2 ttk + 2 is closable (ladder: a 1-HP enemy recalled 3 tiles away)
        if not (chan or stun or dd <= reach or (fin and dd <= reach + 2 * ttk + 2)):
            continue
        value = bag + 50 * g2g(r) + DENIAL
        rounds = max(0, dd - ME.get("range", 1)) + ttk
        pl = lanchester(s, p)
        if pl > KILL_PLOSE:                     # tried 15 Oct: x min(1, hp/maxhp/0.5), x0.67 carrying > 40 [measured: worse]
            continue
        if fin:
            w.excl.pop(("kill", int(c)), None)  # finishers ignore the kill exclusion (P(lose) vs ~0 HP is ~0)
        risk = pl * (s.bag + 60 * THEIR_RATE)
        # [deviation] (value - risk) / rounds: PRICES' value / rounds - risk subtracts gems from gems/round, so an
        # even fight never priced and farmers took hits without answering
        out.append(((value - risk) / max(1, rounds) * kmul * pm[e_side(w, p)], "kill", int(c)))
    # HOLD: contested altar, stun or lock gold, a fresh sighting there
    if s.sc and s.sage < SIGHT_LIVE:
        a = s.sa
        # spec: stun OR lock gold; we never buy or place locks, so only a stun counts [deviation]
        if a < len(w.apos) and w.aside[a] == 1 and ME.get("has_cc") and                 r >= w.kh_until and s.plose <= HOLD_PLOSE:
            wk = w.walk_to(f"a{a}", s.pos)
            if wk is None or wk >= FAR:
                wk = max(0, w.ad[a] - 1)
            out.append((30 * THEIR_RATE / (wk + 30) * prof["hold"] * pm["hold"], "hold", a))
    # HEAL: what a death costs (bag + 60 rounds of my farming) x P(die), over a recall (5) + the walk back out.
    # P(die) = (1 - hp/maxhp) x (1 + enemies within 8) x HEAL_K, clamped to [0, 1]; at least STACK_HEAL with >= 3
    # enemies within 8 and no ally within 5, even at full HP (HEAL is then "go home": the executor walks while an
    # enemy is within 6 and recalls only once clear).
    ne8 = 0
    for e in s.enemies:
        if e[4] <= 8:
            ne8 += 1
    pdie = min(1.0, (1 - s.hp / s.maxhp) * (1 + ne8) * HEAL_K)
    if ne8 >= 3 and not s.spawn and not any(a[1].chebyshev_distance(s.pos) <= 5 for a in s.allies):
        pdie = max(pdie, STACK_HEAL)
    if pdie > 0:
        wb = fget(w.F_home, s.pos) if w.F_home is not None else s.pos.chebyshev_distance(w.sp0)
        out.append((pdie * (s.bag + 60 * MY_RATE) / (5 + wb) * prof.get("heal", 1.0), "heal", 0))
    # SHOP
    item = ME.get("target") or prof["item"]      # current build target (set by buy_all), else the first entry
    try:
        cost = item.cost()
    except Exception:
        cost = 30
    if s.gold >= cost:
        n = s.gold // cost
        rounds = 1 if s.spawn else 6
        if SHOP_RETURN and not s.spawn:
            rounds += fget(w.home_field(), s.pos) if w.F_home is not None else 20
        out.append((g2g(r) * n * cost / rounds * prof["shop"] * pm["shop"], "shop", 0))
    # JOIN: an ally farming a group that needs >= 2
    for k, (op, tg) in by.items():
        if op != 1 or tg not in w.idx:
            continue
        h = w.idx[tg]
        o = w.G[h]
        if o.need < 2:
            continue
        wk = w.gd.get(h, FAR)
        if wk >= FAR:
            continue
        if min(t.chebyshev_distance(s.pos) for t in o.tiles) <= 4:
            continue                            # there: FARM(g) prices itself
        b = cl.get(h, 1)
        lo = farm_price(w, s, h, b, wk) * b if b >= o.need else 0.0
        gain = farm_price(w, s, h, b + 1, wk) * (b + 1) - max(0.0, lo)
        if gain > 0:
            out.append((gain / max(1, wk) * prof["join"] * pm["join"], "join", k))
    return out


SEED_UNTIL = 40             # [rule, 15 Oct ladder phase 1] the opening seed holds to this round (was round 1 + 2)


def seeded(w, s):
    """True while the opening seed holds: until SEED_UNTIL, while I still execute it (going), and the seeded group is
    not cleared / respawning (seen taken on arrival: exec_farm returns done) and no reward came in yet (bag or gold
    above what I held when it was set: a capture; a fast respawn otherwise kept me re-farming it). Clears w.seed and traces once on end."""
    sd = w.seed
    if sd is None:
        return False
    o = w.G.get(sd)
    if s.r <= w.seed_until and w.cur == ("farm", sd) and w.status == "going" and o is not None \
            and not (o.st == "resp" and o.until > s.r) and s.bag <= w.lastbag and s.gold <= w.lastgold:
        return True
    w.seed = None
    trace("choice", f"seed end {tname(w, 'farm', sd)} cur={w.cur[0]} status={w.status} st={o.st if o else '-'} "
                    f"bag={s.bag} gold={s.gold}")
    return False


def choose(w, s):
    """Argmax with a HOLD_TURNS hold, then hysteresis; returns True when the choice changed.
    HEAL is locked only while actually recalling (90_main does not call choose during a channel); while it walks
    away from enemies it is re-priced like any option. HEAL is never excluded (a death or timeout while healing
    must not forbid the next heal)."""
    cur = w.cur
    cl, by = claims(w, s)
    w.claims = cl
    w.lowcl = {w.idx[tg] for k, (op, tg) in by.items() if k < w.slot and op == 1 and tg in w.idx}
    ps = price_all(w, s, cl, by)
    r = s.r
    ps = [t for t in ps if t[1] == "heal" or w.excl.get((t[1], t[2]), -1) <= r]
    ps.sort(key=lambda t: -t[0])
    curp = None
    for t in ps:
        if t[1] == cur[0] and t[2] == cur[1]:
            curp = t[0]
            break
    best = ps[0] if ps else (0.0, "fall", None)
    if best[0] <= 0:
        best = (0.0, "fall", None)
    if seeded(w, s) and best[1] != "heal" and not retreat_now(s):
        return False                            # the opening seed holds (only HEAL / retreat break it)
    going = curp is not None and curp > 0 and w.status == "going"
    held = going and r - w.started < HOLD_TURNS and best[1] != "heal" and not retreat_now(s)
    keep = held or (going and best[0] <= curp * HYST) or \
           (cur[0] == "fall" and best[1] == "fall" and w.status == "going")
    if keep:
        return False
    new = (best[1], best[2])
    if new == cur and w.status == "going":
        return False
    w.set_cur(new, r, s)
    if TRACE:
        t2 = ps[1] if len(ps) > 1 else (0.0, "-", None)
        trace("choice", f"{new[0]} {tname(w, new[0], new[1])} {best[0]:.2f} | {t2[1]} {tname(w, t2[1], t2[2])} "
                        f"{t2[0]:.2f} cur={curp if curp is None else round(curp, 2)} bag={s.bag}")
    return True


def tname(w, op, tg):
    if tg is None:
        return "-"
    if op == "farm":
        o = w.G.get(tg)
        return f"g{tg}@{o.anchor.x},{o.anchor.y}" if o else str(tg)
    if op in ("bank", "hold"):
        return f"A{tg}"
    if op == "ward" and tg is not None and tg < len(w.wtiles):
        return f"W{tg}@{w.wtiles[tg].x},{w.wtiles[tg].y}"
    return str(tg)


def tbits(w, op, tg):
    if tg is None:
        return 0
    if op == "farm":
        return w.G[tg].mi if tg in w.G else 31
    return int(tg) & 31


def broadcast(w, s, code):
    """My byte (slot) when it changed; bytes 5-6 sighting (count | stamp, region altar); stale bytes 5 and 7 cleared."""
    if w.cur[0] == "ward" and w.cur[1] is not None:
        b = ((w.cur[1] + 1) & 31) << 3         # code 0, target = ward index + 1
    else:
        b = code | (tbits(w, OPT[code], w.cur[1]) << 3 if 0 < code < 7 else 0)
    if b != w.sent:
        try:
            cambc.shared_memory[w.slot] = b
            w.sent = b
        except Exception:
            pass
    if not s.alive:
        return
    try:
        if s.sc and s.sage >= SIGHT_LIVE:
            cambc.shared_memory[5] = 0
            s.sc, s.sage = 0, 999
        b7 = s.mem[7]
        if b7 & 31 and (((s.r // 32) - (b7 >> 5)) & 7) * 32 >= DEATH_MARK:
            cambc.shared_memory[7] = 0
    except Exception:
        pass
    es = s.enemies
    if len(es) >= 2 and w.apos:
        # enemies seen together (my vision + my ward's): the largest count within SIGHT_R of one of them
        best, bp = 0, None
        for e in es:
            p = e[1]
            n = 0
            for f in es:
                if p.chebyshev_distance(f[1]) <= SIGHT_R:
                    n += 1
            if n > best:
                best, bp = n, p
        best = min(7, best)
        if best >= 2 and (best >= s.sc or s.sage > SIGHT_OVER):
            a = min(range(len(w.apos)), key=lambda i: bp.chebyshev_distance(w.apos[i]))
            nb = best << 5 | ((s.r // 4) & 31)
            if nb != s.mem[5] or a != s.mem[6]:
                try:
                    cambc.shared_memory[5] = nb
                    cambc.shared_memory[6] = min(a, 254)
                except Exception:
                    pass
