"""Sense, price the six options (strat/PRICES.md) in team gems per round, choose with hysteresis, broadcast.

Option codes (shared byte, low 3 bits): 0 idle (also heal: recalling to heal, no target, nothing for allies to read),
1 farm, 2 bank, 3 kill, 4 hold, 5 shop, 6 join, 7 dead; target in the high 5 bits (group index in draft-memory order, altar index, enemy handle & 31, ally slot for join).
Byte 5: enemy sighting on our half, high nibble = altar index + 1 (0 none), low nibble = (round // 2) & 15 when seen;
a reader treats age >= SIGHT_AGE half-rounds as stale and clears it (~30 rounds, no writer needed to decay it).
"""

KEEP_HP = 0.4               # [guess] the hit body keeps >= 40 % of max HP (KEEP_FRAC)
HYST = 1.2                  # switch only when a new option beats the current one by 20 %
EXCL = 20                   # rounds an (option, target) is excluded after a timeout / failure
DENIAL = 24                 # [measured-ish] their farm rate 0.4 g/r x 60 rounds out (PRICES KILL)
THEIR_RATE = 0.4            # [guess] their gems per round per body (HOLD value 30 x 0.4)
P_NEAR = 0.5                # [guess] P(lose the bag) with an enemy within 8
DANGER_W = 0.2              # [guess] P(lose the bag) per unit of draft danger (cell value / 14)
SIGHT_AGE = 15              # half-rounds (~30 rounds) a sighting stays live
SHOP_RETURN = True          # [deviation] SHOP rounds include the walk back from spawn to where I am
SURVIVE = 0.6               # [tuned] k bodies are enough if the most-hit body keeps > 40 % of its current HP
WAIT_PARTNER = 15           # [guess] rounds added to a pair take while the partner is not committed
FUEL_FLOOR = 400_000        # after sensing: below this skip pricing, repeat the executor step
P_LOSE_MAX = 0.5            # [guess] FARM / BANK / KILL price 0 when the local Lanchester P(lose) exceeds this
FARM_PLOSE = 0.99           # [tuned] off: 0.65 (2 v 1) lost corners and interlock (we must contest the centre)
HOLD_PLOSE = 0.3            # [guess] HOLD needs a clearly safe altar
KILL_PLOSE = 0.45           # [tuned] fight only when locally stronger (0.5 = even; 0.99 lost 9 champions in kills)
DEATH_EXCL = 100            # rounds a death excludes its (option, target), and kill/hold after a kill/hold death
DEATH_MARK = 100            # rounds the team avoids a group an ally died farming (bytes 6-7)
HEAL_K = 1.5                # [guess] HEAL: P(die) = clamp((1 - hp/maxhp) x (1 + enemies within 8) x HEAL_K, 0, 1)
MY_RATE = 0.4               # [guess] my gems per round, x 60 rounds out = what a death costs beyond the bag
HOLD_TURNS = 2              # a new (option, target) is kept this many turns (unless done/failed, HEAL, retreat)
OPT = ("idle", "farm", "bank", "kill", "hold", "shop", "join", "dead", "fall")
CODE = {o: i for i, o in enumerate(OPT)}
CODE["heal"] = 0            # broadcast as idle: the byte has no free code (7 is dead)
CLEAR_MEMO = {}


class Snap:
    __slots__ = ("r", "st", "alive", "recalling", "submitting", "can_move", "can_attack", "pos", "hp", "maxhp",
                 "bag", "gold", "S", "enemies", "allies", "live", "vis", "mem", "spawn", "near_e", "P", "walt", "edps", "plose")


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


def price_all(w, s, cl, by):
    """[(price, option, target)] for every option this turn (multipliers applied)."""
    prof, r = ME["prof"], s.r
    out = []
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
    if s.mem[6] and (((r // 8) - s.mem[7]) & 255) * 8 < DEATH_MARK:
        dead_g = w.idx.get(s.mem[6] - 1)
    update_groups(w, s, cand)
    for h in cand:
        o = w.G[h]
        c = cl.get(h, 0)
        k = need_k(w, s, h, c)                  # bodies the live clear model needs, me + c claimants at least
        if k is None or (c == 0 and k >= 2 and r < w.pair_until):
            continue
        # [deviation] spec: "claimants >= bodies needed prices 0 for me". Measured 15 Oct (bench fix7/fix8 vs fix6):
        # that gate, even for solo groups only, lost rows A and raised elkring deaths 5 -> 17-19 (elks taken by too
        # few bodies). Extra bodies instead price value / bodies, which already makes crowding unattractive.
        if h == dead_g or (s.plose > FARM_PLOSE and s.near_e <= 5):
            continue                            # an ally died farming it recently, or outnumbered here
        wk = w.walk_to(f"g{h}", s.pos)
        if wk is None or wk >= FAR:
            wk = w.gd.get(h, FAR)
        if wk >= FAR:
            continue
        p = farm_price(w, s, h, k, wk) * prof["farm"]
        out.append((p, "farm", h))
    # BANK
    if s.bag > 0 and w.apos:
        order = sorted(range(len(w.apos)), key=lambda i: w.ad[i])
        a = order[0]
        if w.aside[a] == 2 and w.bank < len(w.apos):
            a = w.bank
        wk = w.walk_to(f"a{a}", s.pos)
        if wk is None or wk >= FAR:
            wk = max(0, w.ad[a] - 1)
        if wk < FAR and not (s.near_e <= 4 and s.plose > P_LOSE_MAX):
            P = s.P
            # [deviation] the risk of holding the bag is ADDED to BANK (PRICES: "at bag >= 20 with an enemy
            # within 8, risk dominates and BANK wins"); subtracting it would stop every bank near an enemy.
            out.append((s.bag * (1 + P) / (wk + max(1, -(-s.bag // 10))) * prof["bank"], "bank", a))
    # KILL: closable targets only
    reach = ME.get("range", 1) + 1 + (2 if ME.get("has_dash") else 0)
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
        out.append(((value - risk) / max(1, rounds) * prof["kill"], "kill", int(c)))
    # HOLD: contested altar, stun or lock gold, a fresh sighting there
    sb = s.mem[5]
    if sb >> 4:
        a = (sb >> 4) - 1
        age = ((r // 2) - (sb & 15)) & 15
        # spec: stun OR lock gold; we never buy or place locks, so only a stun counts [deviation]
        if age < SIGHT_AGE and a < len(w.apos) and w.aside[a] == 1 and ME.get("has_cc") and                 r >= w.kh_until and s.plose <= HOLD_PLOSE:
            wk = w.walk_to(f"a{a}", s.pos)
            if wk is None or wk >= FAR:
                wk = max(0, w.ad[a] - 1)
            out.append((30 * THEIR_RATE / (wk + 30) * prof["hold"], "hold", a))
    # HEAL: what a death costs (bag + 60 rounds of my farming) x P(die), over a recall (5) + the walk back out.
    # 0 at full HP. P(die) = (1 - hp/maxhp) x (1 + enemies within 8) x HEAL_K, clamped to [0, 1].
    if s.hp < s.maxhp:
        ne8 = 0
        for e in s.enemies:
            if e[4] <= 8:
                ne8 += 1
        pdie = min(1.0, (1 - s.hp / s.maxhp) * (1 + ne8) * HEAL_K)
        wb = fget(w.F_home, s.pos) if w.F_home is not None else s.pos.chebyshev_distance(w.sp0)
        out.append((pdie * (s.bag + 60 * MY_RATE) / (5 + wb) * prof.get("heal", 1.0), "heal", 0))
    # SHOP
    item = prof["item"]
    try:
        cost = item.cost()
    except Exception:
        cost = 30
    if s.gold >= cost:
        n = s.gold // cost
        rounds = 1 if s.spawn else 6
        if SHOP_RETURN and not s.spawn:
            rounds += fget(w.home_field(), s.pos) if w.F_home is not None else 20
        out.append((g2g(r) * n * cost / rounds * prof["shop"], "shop", 0))
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
            out.append((gain / max(1, wk) * prof["join"], "join", k))
    return out


def choose(w, s):
    """Argmax with a HOLD_TURNS hold, then hysteresis; returns True when the choice changed.
    HEAL in progress is locked until its executor reports done/failed (a recall cancelled by a flip is the worst
    outcome). HEAL is never excluded (a death or timeout while healing must not forbid the next heal)."""
    cur = w.cur
    if cur[0] == "heal" and w.status == "going":
        return False
    cl, by = claims(w, s)
    w.claims = cl
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
                        f"{t2[0]:.2f} cur={curp if curp is None else round(curp, 2)}")
    return True


def tname(w, op, tg):
    if tg is None:
        return "-"
    if op == "farm":
        o = w.G.get(tg)
        return f"g{tg}@{o.anchor.x},{o.anchor.y}" if o else str(tg)
    if op in ("bank", "hold"):
        return f"A{tg}"
    return str(tg)


def tbits(w, op, tg):
    if tg is None:
        return 0
    if op == "farm":
        return w.G[tg].mi if tg in w.G else 31
    return int(tg) & 31


def broadcast(w, s, code):
    """My byte (slot) when it changed; byte 5 sighting on our half."""
    b = code | (tbits(w, OPT[code], w.cur[1]) << 3 if 0 < code < 7 else 0)
    if b != w.sent:
        try:
            cambc.shared_memory[w.slot] = b
            w.sent = b
        except Exception:
            pass
    if not s.alive:
        return
    sb = s.mem[5]
    if sb >> 4 and (((s.r // 2) - (sb & 15)) & 15) >= SIGHT_AGE:
        try:
            cambc.shared_memory[5] = 0
        except Exception:
            pass
    if s.enemies and w.apos:
        hf = w.F_home
        for _c, p, _hp, _b, _d, _st in s.enemies:
            de = fget(w.F_enemy, p)
            ours = (fget(hf, p) < de) if hf is not None else                 p.chebyshev_distance(w.sp0) < p.chebyshev_distance(w.esp0)
            if ours:
                a = min(range(len(w.apos)), key=lambda i: p.chebyshev_distance(w.apos[i]))
                if a < 15:
                    try:
                        cambc.shared_memory[5] = (a + 1) << 4 | ((s.r // 2) & 15)
                    except Exception:
                        pass
                break
