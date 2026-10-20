"""Sense, price the six options (strat/PRICES.md) in team gems per round, choose with hysteresis, broadcast.

Option codes (shared byte, low 3 bits): 0 idle (also heal: recalling to heal, target 0; and ward: target = ward
index + 1, so a byte of 8/16/24 is "walking to place ward 0/1/2"), 1 farm, 2 bank, 3 kill, 4 hold, 5 shop, 6 join,
7 dead; target in the high 5 bits (group index in draft-memory order, altar index, enemy handle & 31, ally slot for join).
Byte 5: enemy sighting, high 3 bits = enemies seen together (within SIGHT_R of one of them, capped 7; 0 = none), low
5 bits = (round // 4) & 31 when seen. Byte 6: the sighting's region, index of the altar nearest the cluster.
A reader treats age >= SIGHT_LIVE rounds as stale and clears byte 5. Byte 7: the crew call, (caller slot + 1) << 5 |
group index (0 = none; call_of). A dead body's slot byte is code 7 with target = the group it died on (31: none).
Layout: strat/MEMORY_LAYOUT.md, "Shared 8 bytes".
"""

KEEP_HP = 0.4               # [guess] the hit body keeps >= 40 % of max HP (KEEP_FRAC)
HYST = 1.2                  # switch only when a new option beats the current one by 20 %
SMOOTH_ON = 1               # [user plan 15 Oct night, IMPROVEMENTS change 1] smooth factors instead of the KILL pl / closable,
                            # BANK near-enemy and STACK_R cliffs (0: the old gates exactly)
KILL_PL_POWS = {0.6: 0.756, 0.95: 0.231}    # KILL value x (1 - pl) ** pow, pow = ln(0.5) / ln(1 - kill_plose): the factor
KILL_PL_POW = 0.756                         # is 0.5 at pl = kill_plose (no math module: precomputed; other kp -> this)
EXCL = 20                   # rounds an (option, target) is excluded after a timeout / failure
DENIAL = 24                 # default of the profile key `denial` (Vesper 60, 20_champs); [measured-ish] their farm rate 0.4 g/r x 60 rounds out (PRICES KILL)
THEIR_RATE = 0.4            # [guess] their gems per round per body (HOLD value 30 x 0.4)
P_NEAR = 0.5                # [guess] P(lose the bag) with an enemy within 8
DANGER_W = 0.2              # [guess] P(lose the bag) per unit of draft danger (cell value / 14)
SHOP_RETURN = True          # [deviation] SHOP rounds include the walk back from spawn to where I am
SURVIVE = 0.6               # [tuned] k bodies are enough if the most-hit body keeps > 40 % of its current HP
# Crews [strat/TEAM_LOOP.md T1-T3]: a group I can't clear alone is taken by a crew of need + CREW_PLUS bodies (the top
# teams put 3.8-4 bodies on big groups, we put 2.8); claims are the slot bytes, the lowest slots keep a full crew.
CREW_PLUS = 1               # PROVISIONAL A76 bodies over the draft's need on a group one body can't clear
CREW_MAX = 4                # PROVISIONAL A76 crew cap (one body stays free for the rest of the map)
RESP_LOOK = 40              # PROVISIONAL A78 [T6] a group respawning within this many rounds prices with eta = time to respawn
ROLE_BUILD = 1              # [strat/ROLES.md K2] 1: the tanks' builds (TANK_IDS) start with Jungle Strength (30 % less damage from
                            # camps [rules]; the top teams' first emblem, r42-119), and every body buys along its build on any turn
                            # on the spawn tiles with >= 30 gold, not only on a SHOP trip; 2: Jungle first for all but Vesper
                            # (_dev-strat JUNGLE_FIRST=1 + SPAWN_BUY). 0 = off
TANK_IDS = (9, 0)           # draft ids of the tanks, in tank order: Varg, Ryth (ROLES.md)
ROLE_PRICE = 1              # [strat/ROLES.md K3] 1: the camp damage a take costs me is priced after my mitigation (my_dmg): a
                            # finished Jungle emblem, and with KIT_ON my shield. 0 = off (tank(k) of the damage, as before)
JUNGLE_MIT = 0.3            # [rules] a finished Jungle emblem (any stat): 30 % less damage from camps
SHIELD_COVER = 0.6          # [measured 17 Oct, A59] the shield took every camp hit in its window (0 HP lost to 273 hits); its 5
                            # turns per 8-turn cooldown covered 59 % of Varg's hit rounds (62.5 % at most)
LIVE_STEP = 1               # [_dev-strat, 17 Oct] 1: at a take under way, a body out of range of every live monster steps to a free
                            # tile in range of one (step_near); the group field also counts dead camps' tiles, so melee bodies
                            # ping-ponged between the two rules (rows: 26 % idle at takes). 0 = off
SPAWN_KILL_R = 2            # [user decision 15 Oct] KILL / JOIN a fight / HUNT price 0 on targets within this of an enemy
                            # spawn tile (it heals to full at turn end [rules], camps ring it); exec_kill fails there (-1: off)
FUEL_FLOOR = 400_000        # after sensing: below this skip pricing, repeat the executor step
P_LOSE_MAX = 0.5            # [guess] FARM / BANK / KILL price 0 when the local Lanchester P(lose) exceeds this
FARM_PLOSE = 0.99           # [tuned] off: 0.65 (2 v 1) lost corners and interlock (we must contest the centre)
HOLD_PLOSE = 0.3            # [guess] HOLD needs a clearly safe altar
KILL_PLOSE = 0.6            # [user plan 15 Oct, ladder 2; was 0.45 tuned] fight even and slightly worse local fights
                            # [user plan 15 Oct, ladder 6] default of the profile / phase key `kill_plose` (Vesper hunt phase 0.95)
                            # (ladder: nobody fought back; 0.5 = even; 0.99 lost 9 champions in kills)
DEATH_EXCL = 100            # rounds a death excludes its (option, target), and kill/hold after a kill/hold death
HEAL_K = 1.5                # [guess] (2.0 -> 1.5, 15 Oct ladder 2: 11 of 27 deaths healing at 316-644 HP) HEAL: P(die) = clamp((1 - hp/maxhp) x (1 + enemies within 8) x HEAL_K, 0, 1)
MY_RATE = 0.4               # [guess] floor of my gems per round in death_cost (60 x max(this, best FARM now) + bag)
DEATH_OUT = 60              # [rules] rounds out after a death
DCOST_CAP = 300             # [guess] cap on death_cost before the bag (heal ~12 at low HP: 0.8 x 300 / 20)
DCOST_FIGHT_CAP = 150       # [guess, user plan 15 Oct ladder 5] death cost in fight risk terms (KILL/JOIN/HUNT); HEAL keeps DCOST_CAP
                            # [user plan 15 Oct, ladder 6] default of the profile / phase key `dcost_fight` (Vesper hunt phase 30)
HEAL_NOENEMY_CAP = 150      # [user plan 15 Oct, ladder 6; guess] HEAL with no enemy within 8 and hp < HEAL_NOENEMY_HP: death cost cap
HEAL_NOENEMY_HP = 0.5       # [user plan 15 Oct, ladder 6; guess] HEAL with no enemy within 8 prices 0 at hp >= this x maxhp
ATTACKER_BONUS = 1.5        # [guess, user plan 15 Oct ladder 5] KILL multiplier on the enemy that just hit me (s.attacker)
HOLD_TURNS = 2              # a new (option, target) is kept this many turns (unless done/failed, HEAL, retreat)
WARD_VALUE = 4.0            # [guess] g/r of a ward placed at once (8 -> 4: at 8 it outranked every farm, 1-5 g/r)
WARD_FROM = 10              # [guess] no ward option before this round (round 3: every idle champion chose a ward)
WARD_WALK = 30              # [guess] WARD price = WARD_VALUE x WARD_WALK / (WARD_WALK + walk): 4 here, 1.7 at 40 tiles
WARD_TRIES = 3              # choices of one ward tile per champion before I give it up (timeouts / stuck re-choose it)
WARD_DETOUR = 5             # [guess] WARD prices only when walk(me->ward) + walk(ward->goal) - walk(me->goal) <= this
SCAN_WARD = 1               # [B1, docs/LADDER_18OCT.md] 1: the free ward is re-placed every round (50_exec scan_ward) on an
                            # unseen bush tile within 2, nearest my goal; the draft ward tiles are dropped. 0 = off (draft wards)
SCAN_FUEL = 900_000         # [guess] no scan ward below this fuel left (as the executor loop's 900k)
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
STACK_HEAL = 0.6            # [guess] HEAL P(die) floor with >= 3 enemies within 8, no ally within 5 and plose > HEAL_PLOSE
HEAL_PLOSE = 0.5            # [user plan 15 Oct, ladder 2] HEAL prices 0 with an enemy within 8 while my local plose <= this
JOIN_FIGHT_R = 10           # [user plan 15 Oct, ladder 2] allies within this of a fighting ally price JOIN on its fight
JOIN_TTK = 3                # [guess] my hits to finish a fight target I cannot see (JOIN on a fight)
JOIN_NEED = 0.3             # [user plan 15 Oct, ladder 6; guess] JOIN a fight only when the ally's P(lose) without me > this
LANCH_NEAR = 4              # [user decision 15 Oct afternoon] Lanchester bodies within this of me weigh 1.0 ...
LANCH_FAR_W = 0.5           # ... and LANCH_NEAR+1 .. LANCH_R this (enemies and allies alike; guess)
KFAIL_ROUNDS = 6            # [user decision 15 Oct afternoon; was EXCL 20] a failed / timed-out kill bans that target this long
KFAIL_MAX = 48              # [ladder 6774ff6a, 15 Oct night] the ban doubles per consecutive failure on the same target (6, 12, 24, 48):
                            # Vesper re-chased one uncatchable enemy 25 times in 300 rounds (chase 6 = ban 6: a 50 % duty cycle)
RECALL_COST = 1             # [user decision 15 Oct afternoon] FARM adds 5 + min(walk home, 20) rounds when the clear leaves me < KEEP_HP
REWARD_X = 1.0              # [measured 15 Oct] FARM on a cleared group (reward waiting) x this; 2.0 lost the r300 bench (8/18 vs 11/18, -242 vs +806 summed)
FLIP_WINDOW = 10            # [user decision 15 Oct afternoon] farm target A -> B -> A within this many rounds ...
FLIP_LOCK = 30              # ... excludes B for this many rounds (trace `flip lock`)
LANCH_R = 8                 # [rule, 15 Oct ladder 3] Lanchester bodies: everyone within this of ME (was: within 5 of
                            # the target; kills were approved, then 3 enemies arrived from 6-8 tiles)
HEAL_LOW = 0.3              # [guess] below this HP fraction with an enemy within 8, HEAL P(die) >= HEAL_FLOOR
HEAL_FLOOR = 0.8            # [guess] whatever plose says (ladder: farm 3.34 beat heal 2.96 at 10 HP, 44 bag, 2 enemies)
HEAL_WB = 15                # [guess] HEAL divisor uses min(walk back, this): far from spawn must not zero the heal
ENGAGED_HYST = 3.0          # [guess] farm -> another farm while a live monster of mine is within CAMP_R: needs 3x
                            # (SUNK_ON 1 replaces it: engaged ~ prog >= 0.5)
# [IMPROVEMENTS 2, 15 Oct night] sunk progress: the current job's price in the switch test is curp x max(hy, 1 + SUNK_K
# x w.prog) (w.prog 0..1 from 90_main prog_update), except against HEAL or under retreat_now. 0: behaviour as before.
SUNK_ON = 1
SUNK_K = 2.0                # [guess] a job 80 % done needs a 2.6x better alternative
PROG_STALL = 8              # [guess] rounds without a rise of w.prog (going, not attacking / capturing / waiting /
                            # recalling / channelling) -> the choice fails like the stuck guard (`failed stall`)
HUNT_BAG = 30               # [guess] expected bag of a sighted enemy (sighting hunt value)
HUNT_REVISIT = 150          # [guess; 60 -> 150 user plan 15 Oct, ladder 5: chain patrol] rounds before a patrol hunt goes back to an enemy altar I reached
ROAM_STACK = 60             # [guess] rounds a >= 3-enemy sighting halves the no-sighting hunt
HUNT_MAX = 40               # rounds a sighting hunt walks before it gives up


def sig(x):
    """Rational sigmoid (no exp): 0.5 at 0, -> 0 / 1 at -inf / +inf."""
    return x / (1 + abs(x)) * 0.5 + 0.5


# Posture columns: multipliers over the options (price *= POSTURE[col][key]), neutral 1.0, all [guess].
# Selection (posture(), every champion locally, same inputs, no byte): draft regime few -> defend, pick / many /
# unknown -> economy; a fresh sighting (<= SIGHT_FRESH rounds) of >= STACK_N enemies -> defend; a fresh one of <= 2
# while we lead by > PUNISH_LEAD -> punish. Our side of an enemy: its nearest altar has draft side 0 or 1; theirs: 2.
_PK = ("farm", "farm_their_side", "bank_risk", "kill_our_side", "kill_their_side", "hold", "shop", "join", "ward", "heal")


def _col(**kw):
    c = dict.fromkeys(_PK, 1.0)
    c.update(kw)
    return c


POSTURE = {
    # heal 0.7 [user plan 15 Oct, ladder 6; guess]: applied on regime many only (HEAL in price_all), x the profile heal
    "economy": _col(heal=0.7),                  # open maps: the baseline prices as they are
    # defend [guess all]: farm_their_side 0.3 their half is where the stack lives; bank_risk 1.5 cash the bag before
    # it is caught; kill_our_side 1.3 intruders on our half are near help; kill_their_side 0.5 no dives into them;
    # hold 1.3 deny tributes at contested altars; join 1.3 move in pairs.
    # join 2.0 [guess, 15 Oct ladder phase 1; was 1.3]: on few maps move in pairs.
    "defend": _col(farm_their_side=0.3, bank_risk=1.5, kill_our_side=1.3, kill_their_side=0.5, hold=1.3, join=2.0),
    # punish [guess all]: a small group seen while we lead: fight it, mostly on our half; bank a bit sooner.
    "punish": _col(kill_our_side=1.4, kill_their_side=1.1, bank_risk=1.2),
}
# Farm-race numbers by draft regime [user plan 15 Oct, ladder 4; guess all]: walk_w x FARM walk rounds, farm_hyst =
# farm -> farm switch while not engaged, bank_ret = BANK rounds count the walk back (2 x walk).
# "race": regime many, or pick with >= RACE_RICH groups per body; "base" (few, other pick, unknown): the old numbers.
RACE = {"race": dict(walk_w=2.0, farm_hyst=2.0, bank_ret=2),
        "base": dict(walk_w=1.0, farm_hyst=HYST, bank_ret=1)}
RACE_RICH = 4


def near_espawn(w, p):
    """[user decision 15 Oct, kill exclusions] p is within SPAWN_KILL_R (Chebyshev) of an enemy spawn tile (w.esp,
    dilated once into w.espz)."""
    if SPAWN_KILL_R < 0:
        return False
    z = getattr(w, "espz", None)
    if z is None:
        z = Bitboard()
        for q in w.esp.positions():
            z.draw_chebyshev(q, SPAWN_KILL_R)
        w.espz = z
    return z.is_set(p)


def race(w):
    """The RACE row for this map, from the draft summary (cached on w.race)."""
    rc = getattr(w, "race", None)
    if rc is None:
        d = w.d or {}
        g, S = d.get("regime"), max(1, d.get("S") or 1)
        rc = w.race = RACE["race" if g == 2 or (g == 1 and d.get("rich", 0) / S >= RACE_RICH) else "base"]
        trace("race", f"regime={g} rich={d.get('rich')}/{S} -> {'race' if rc is RACE['race'] else 'base'} "
                      f"solo={d.get('solo', 1.0):.2f} ggems={d.get('ggems', 0.0):.2f}")
    return rc


OPT = ("idle", "farm", "bank", "kill", "hold", "shop", "join", "dead", "fall")
CODE = {o: i for i, o in enumerate(OPT)}
CODE["heal"] = 0            # broadcast as idle: the byte has no free code (7 is dead)
CODE["ward"] = 0            # idle code with target = ward index + 1 (see broadcast)
CODE["hunt"] = 3            # sighting hunt: broadcast as kill with target 31
CLEAR_MEMO = {}


class Snap:
    __slots__ = ("r", "st", "alive", "recalling", "submitting", "can_move", "can_attack", "pos", "hp", "maxhp",
                 "bag", "gold", "S", "enemies", "allies", "live", "vis", "mem", "spawn", "near_e", "P", "walt", "edps", "plose",
                 "sc", "sa", "sage", "stack", "dcost", "attacker", "trapped", "ba", "bwk", "sap", "carry",
                 "cdec", "cpl", "nus", "ghosts", "nlive", "call")


def sense(w):
    me, r = w.me, cambc.round_number()
    s = Snap()
    s.r, s.nlive, s.call = r, None, None
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
    s.dcost = 0.0
    s.attacker, s.trapped = None, False
    s.cdec, s.cpl, s.nus = None, 0.0, 0
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
    # [user plan 15 Oct, ladder 5] attacker: my HP dropped and an enemy is within its attack range + 1 (nearest).
    # trapped: it is within 2 and no flee can end (spawn > 6, no ally within 6, no dash ready) -> flee_ok() gates
    if s.hp < (getattr(w, "hp_alive", 0) or 0):
        hit = [e for e in s.enemies if e[4] <= arng(e[0]) + 1]
        if hit:
            s.attacker = e = min(hit, key=lambda x: x[4])
            wb = fget(w.F_home, pos) if w.F_home is not None else pos.chebyshev_distance(w.sp0)
            s.trapped = e[4] <= 2 and wb > 6 and not any(a[1].chebyshev_distance(pos) <= 6 for a in s.allies)                 and not (w.dash_ab is not None and w.dash_ab.is_ready())
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
        if k == w.slot and not w.twin:          # [C6] Issac reads Cassi's byte (same slot) as an ally's
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
    return dz(w, s.pos)


def dz(w, p):
    """The draft's danger at p's cell as P(lose the bag) (DANGER_W per 14ths; unreached cell 0)."""
    d = w.d
    if d and d.get("danger"):
        v = d["danger"][(p.y * GRID // w.Hm) * GRID + p.x * GRID // w.Wm]
        if v < 15:
            return DANGER_W * v / 14
    return 0.0


def bank_altar(w, s, sap):
    """(altar index, walk) BANK would use now: nearest by walk, our bank if that one is on their side; with a fresh
    stack sighting the nearest safe one (draft side 0/1, > STACK_R from the stack), else the farthest from it."""
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
    return a, wk


def my_dmg(dmg, k, clear):
    """Camp damage I take in a k-body take dealing dmg over clear rounds: tank(k) of it (TANK_SHARE); [K3 ROLE_PRICE] less
    my Jungle emblem's 30 % [rules] and what my shield absorbs: SHIELD_COVER of it, at most its amount per cast, one cast
    per 8 rounds (cooldown [rules]; A59 measured)."""
    d = dmg * tank(k)
    if ROLE_PRICE:
        d *= ME.get("jmit", 1.0)
        sa = ME.get("shield_amt", 0)
        if sa:
            d -= min(SHIELD_COVER * d, sa * (1 + clear // 8))
    return d


def mit_refresh(w):
    """[K3 ROLE_PRICE] ME['jmit'] (0.7 with a Jungle emblem of any stat) and ME['shield_amt'] (the shield slot's amount
    now: it grows with Focus; 0 without KIT_ON) for my_dmg. Every 20 rounds and after a buy."""
    if not ROLE_PRICE:
        return
    j = 1.0
    try:
        n = w.me.item_count()
        for it in (cambc.ItemType.JUNGLE_EMBLEM_OF_STRENGTH, cambc.ItemType.JUNGLE_EMBLEM_OF_FOCUS,
                   cambc.ItemType.JUNGLE_EMBLEM_OF_HEALTH):
            if n[int(it)] > 0:
                j = 1 - JUNGLE_MIT
    except Exception:
        pass
    ME["jmit"] = j
    a = getattr(w, "shield_ab", None)
    try:
        ME["shield_amt"] = a.shield_amount() if KIT_ON and a is not None else 0
    except Exception:
        ME["shield_amt"] = 0


def living(w, s):
    """Bodies alive: the roster minus the other slots broadcasting dead (code 7); cached on s."""
    n = s.nlive
    if n is None:
        n = max(1, len(w.roster))
        for k in range(min(5, len(w.roster))):
            if k != w.slot and (s.mem[k] & 7) == 7:
                n -= 1
        n = s.nlive = max(1, n)
    return n


def crew(w, s, h):
    """[T2] Bodies for a take of h: 1 when h has no live monster left or the draft model says one body clears it
    (o.need, roster mean Strength / min HP: the same number on every body), else min(living, need + CREW_PLUS,
    CREW_MAX). Not my own live model: Varg soloes what Vesper can't, and a crew only forms when every body counts it
    the same (packs, 19 Oct: Varg saw crew 1 on Vesper's crew-3 group, read her claim as full, and she waited alone).
    P10: concentrate force; over-bodying a big group clears it faster, spreads the hits and starts its respawn sooner."""
    o = w.G[h]
    if o.st != "alive" or o.need <= 1 or o.mi >= 31:
        return 1                                # (mi 31: past the 31 claimable groups, no claim or call can name it)
    return min(living(w, s), max(1, o.need) + CREW_PLUS, CREW_MAX)


def claimants(w, s, mi):
    """Slots whose byte is farm on group index mi (me included: my byte as sent last)."""
    return sum(1 for k in range(min(5, len(w.roster))) if s.mem[k] == 1 | mi << 3)


def call_of(w, s):
    """[T3] The live crew call (caller slot, group handle) or None. Byte 7 = (caller slot + 1) << 5 | group index; live
    while the caller's byte is farm on that group and its claimants are short of the crew (a full crew frees the
    call for the next one). P10: one crew forms at a time, so the bodies meet on one group instead of five."""
    b = s.mem[7]
    k, mi = (b >> 5) - 1, b & 31
    h = w.idx.get(mi)
    if k < 0 or h is None or s.mem[k] != 1 | mi << 3:
        return None
    return (k, h) if claimants(w, s, mi) < crew(w, s, h) else None


def farm_price(w, s, h, k, walk, div):
    """[T1] My share of the team rate of a take of h by a crew of k: value / div / (walk + clear(k) + 5 + detour),
    less my bag's risk. One currency: team gems per round, split per body so it compares with bank, kill and heal.
    div = k, or for a crew still forming the bodies it still needs (price_all)."""
    o = w.G[h]
    if o.st == "resp" and o.until > s.r:
        # [T6] arrive at the respawn: priced as a full group whose eta is the later of my walk and its respawn
        # (P14 be first to the field: the top teams retake 20 rounds after the respawn timer, we waited for it to show)
        if o.until - s.r > RESP_LOOK:
            return 0.0
        walk = max(walk, o.until - s.r)
    rc = race(w)
    walk *= rc["walk_w"]
    prof = ME["prof"]
    # P2 one currency: a crew take is priced in team value (gold weight 1), so every body ranks it the same; my
    # profile's gold weight only on a solo take, whose gold is all mine (packs, 19 Oct: Vesper's x3 gold put her
    # alone on a 180-gold crew-3 group that Varg and Ryth priced below their solo groups)
    value = o.gems + g2g(s.r) * o.gold * (prof["gold"] if k <= 1 else 1.0)
    if o.st == "reward":
        return value / div / (walk + 5) * REWARD_X     # [user decision 15 Oct afternoon] free gems beat a clear
    Se = s_eff(w, s, h, k)                      # [user decision 15 Oct] my Strength x my splash (30_world)
    if o.hp is None:                            # full HP: cached per (group, bodies, my Strength)
        key = (h, k, Se)
        cd = CLEAR_MEMO.get(key)
        if cd is None:
            if len(CLEAR_MEMO) > 400:
                CLEAR_MEMO.clear()
            cd = CLEAR_MEMO[key] = clear_dmg(o.mons, Se, k)
        clear, dmg = cd
    else:
        mons = [m for m in o.hp if m[0] > 0]
        if not mons:
            return value / div / (walk + 5)
        clear, dmg = clear_dmg(mons, Se, k)
    per = my_dmg(dmg, k, clear) + s.edps * min(clear + 5, 10)    # [tuned] + enemies hitting me; TANK_SHARE [15 Oct afternoon]
    if per >= s.hp:
        return 0.0                              # [deviation] certain death is not a price
    risk = s.bag if s.hp - per < KEEP_HP * s.maxhp else s.P * s.bag   # [tuned] bag exposure (danger_p)
    if RECALL_COST and s.hp - per < KEEP_HP * s.maxhp:
        # [user decision 15 Oct afternoon] the clear leaves me below KEEP_HP: a recall (5) + the walk back out follow it
        walk += 5 + min(fget(w.F_home, o.anchor) if w.F_home is not None else 20, 20)
    detour = 0
    if o.near < len(w.apos):
        detour = max(0, o.anchor.chebyshev_distance(w.apos[o.near]) - s.walt)
    return value / div / (walk + clear + 5 + detour) - risk


RESET_X = {}                # champion id -> 2 with an attack-reset ability (double hit), else 1; cached per id
_NO_RESET_T = (3, 5, 6, 9)  # ChampionType CASSI, STELLAR, PRISM, REN: no attack reset [rules roster]


def rmul(c):
    k = int(c)
    if k not in RESET_X:
        try:
            RESET_X[k] = 2 if any(a.is_attack_reset() for a in c.abilities()) else 1
        except Exception:
            RESET_X[k] = 1 if int(c.champion_name()) in _NO_RESET_T else 2
    return RESET_X[k]


ARNG = {}                   # champion id -> attack range (cached)


def arng(c):
    k = int(c)
    if k not in ARNG:
        try:
            ARNG[k] = c.attack_range()
        except Exception:
            ARNG[k] = 1
    return ARNG[k]


def flee_ok(s):
    """[user plan 15 Oct, ladder 5] HEAL / the fallback retreat only when a flee can end: not trapped (see sense), or
    HP < retreat_hp and P(lose) > 0.7 (dying either way: try the recall)."""
    return not s.trapped or (s.hp < ME["prof"].get("retreat_hp", RETREAT_HP) * s.maxhp and getattr(s, "plose", 1.0) > 0.7)


def lw(d):
    """[user decision 15 Oct afternoon] Lanchester weight of a body at Chebyshev d from me: 1.0 within LANCH_NEAR,
    LANCH_FAR_W beyond (up to LANCH_R)."""
    return 1.0 if d <= LANCH_NEAR else LANCH_FAR_W


def lanchester(s, e_pos=None):
    """P(we lose) = T^2 / (U^2 + T^2) (square law) [user plan 15 Oct, ladder 5; was T / (U + T)]. U, T = sum of
    hp x dps of me + allies / enemies within LANCH_R of ME; dps = strength x 2 with an attack reset (rmul) [guess,
    PRICES S2]. [rule, 15 Oct ladder 3] centred on me, not the target (e_pos is ignored, kept for callers)."""
    us = s.hp * s.S * (2 if ME.get("attack_reset") else 1)
    for c, p, hp, st in s.allies:
        d = p.chebyshev_distance(s.pos)
        if d <= LANCH_R:
            us += hp * st * rmul(c) * lw(d)
    th = 0
    for c, _p, hp, _b, dd, st in s.enemies:
        if dd <= LANCH_R:
            th += hp * st * rmul(c) * lw(dd)
    return th * th / max(1.0, us * us + th * th)


def engaged(s, h):
    """A live monster of group h is within CAMP_R of me (the camp is hitting me / I am attacking it)."""
    return any(hp > 0 and p.chebyshev_distance(s.pos) <= CAMP_R for _c, hp, p, _st in s.live.get(h, ()))


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
    # groups an ally died on: its slot byte is code 7 with the group as target while it is out (60 rounds [rules])
    dead_g = {w.idx[s.mem[k] >> 3] for k in range(min(5, len(w.roster)))
              if k != w.slot and s.mem[k] & 7 == 7 and s.mem[k] >> 3 in w.idx}
    s.call = call_of(w, s)
    sap = w.apos[s.sa] if s.stack else None
    s.sap = sap
    s.ba, s.bwk = bank_altar(w, s, sap) if w.apos else (0, FAR)
    s.carry = True
    update_groups(w, s, cand)
    rawb = 0.0
    # [T3] P19 a crew member stays with its crew: while another body claims my crew take, I start no other farm
    mine = cur[1] if cur[0] == "farm" and cur[1] in w.G and w.ncrew >= 2 and \
        claimants(w, s, w.G[cur[1]].mi) >= 2 else None
    # [T3] allies claiming a crew take (crew >= 2) are committed to it: they can't answer another crew's call
    busy = sum(n for g, n in cl.items() if g in w.G and crew(w, s, g) >= 2)
    for h in cand:
        o = w.G[h]
        # [T3] assignment through the slot bytes (CBBA-style). A one-body group is exclusive: claimed by an ally it
        # prices 0, and with two claimants the higher slot leaves (rank by slot, so simultaneous choices settle in a
        # turn; engaged on h, a live monster within CAMP_R, I stay). A crew group past its crew takes one more body
        # at the share of all its claimants, kk = allies claiming + 1 (P10; elkring 19 Oct: the fifth body over a crew of
        # 4 had nothing priced and fell back for 12 rounds, as the top teams put all five on the first big group).
        k = crew(w, s, h)
        kk = max(k, 1 + cl.get(h, 0)) if k >= 2 else 1
        if k == 1 and (w.lowcn.get(h, 0) >= 1 and not engaged(s, h) if cur == ("farm", h) else cl.get(h, 0) >= 1):
            continue
        if k >= 2 and cur != ("farm", h) and not cl.get(h, 0) and s.call is not None and s.call[1] != h:
            continue                            # a crew is being called elsewhere: join it, don't start another
        if (mine is not None and h != mine) or h in dead_g or (s.plose > FARM_PLOSE and s.near_e <= 5):
            continue                            # in a crew elsewhere, an ally died farming it, or outnumbered here
        if k >= 2 and cur != ("farm", h):
            # [T3] P10 start or join a crew take only if the bodies free to come reach its need (me, its claimants,
            # the allies not in another crew) or my live model says those survive it (elkring 19 Oct: with four
            # bodies on one group the fifth walked alone to three need-3 groups in turn and failed at each)
            av = living(w, s) - busy + cl.get(h, 0)
            if av < min(k, o.need) and not live_ok(w, s, h, av):
                continue
        wk = w.walk_to(f"g{h}", s.pos)
        if wk is None or wk >= FAR:
            wk = w.gd.get(h, FAR)
        if wk >= FAR:
            continue
        # [T3] P19 a crew forming here is shared by the bodies it still needs: the claimants are committed, so the last
        # body it needs sees the whole take (packs 19 Oct: a call with one claimant priced value / 3 lost to every
        # solo group and the caller waited alone)
        div = max(1, k - cl.get(h, 0)) if kk == k >= 2 and cur != ("farm", h) else kk
        fp = farm_price(w, s, h, kk, wk, div)    # [C2b] a price <= 0 here is no miss: my bag's risk or enemies near
        if fp > rawb:
            rawb = fp                           # death_cost: the best farm price before multipliers
        p = fp * prof["farm"] * pm["farm_their_side" if o.side == 2 else "farm"]
        if sap is not None:
            if SMOOTH_ON:                       # smooth: x0.29 at the altar, x0.6 at STACK_R, x0.96 at 40 tiles
                p *= 1 - (1 - STACK_FARM) * sig((STACK_R - o.anchor.chebyshev_distance(sap)) / 3)
            elif o.anchor.chebyshev_distance(sap) <= STACK_R:
                p *= STACK_FARM                 # the stack was just seen there
        out.append((p, "farm", h))
    # BANK
    if s.bag > 0 and w.apos:
        a, wk = s.ba, s.bwk                     # bank_altar(): nearest / our bank / away from a stack
        if wk < FAR and (SMOOTH_ON or not (s.near_e <= 4 and s.plose > P_LOSE_MAX)):
            P = s.P
            # [deviation] the risk of holding the bag is ADDED to BANK (PRICES: "at bag >= 20 with an enemy
            # within 8, risk dominates and BANK wins"); subtracting it would stop every bank near an enemy.
            # BANK_NEAR_BONUS [guess]: tempo, a bag next to an altar banks now (ladder: 22 gems carried 40 rounds)
            near = 1 + BANK_NEAR_BONUS if wk <= BANK_NEAR else 1
            bp = s.bag * (1 + P) * near / (wk * race(w)["bank_ret"] + max(1, -(-s.bag // 10))) * prof["bank"] * pm["bank_risk"]
            if SMOOTH_ON:
                bp *= sig((s.near_e - 4) / 1.5)     # x0.5 enemy at 4, x0.12 at 1, x0.88 at 7 (exec_bank still refuses <= 3)
            out.append((bp, "bank", a))
    # KILL: closable targets only
    reach = ME.get("range", 1) + 1 + (2 if ME.get("has_dash") else 0)
    kmul = prof["kill"] + KILL_PER_SHARD * w.shards     # scales with shards owned (read every 20 rounds, 90_main)
    # [user plan 15 Oct, ladder 3; numbers guess] appetite: hurt or loaded champions bank / heal first. kmul carries
    # it into KILL, JOIN a fight and the sighting hunt alike (checked 15 Oct, ladder 4: all three multiply by kmul)
    kmul *= min(1.0, s.hp / s.maxhp / 0.6) * max(0.5, 1 - s.bag / 200)   # bag term [ladder 5: was max(0.3, 1 - bag/100)]
    fights = []                                 # (value, rounds, multiplier, P(lose), option, target): risk added below
    kp = prof.get("kill_plose", KILL_PLOSE)     # [user plan 15 Oct, ladder 6] per-champion / phase kill gate
    kpow = KILL_PL_POWS.get(kp, KILL_PL_POW)    # SMOOTH_ON: kill value x (1 - pl) ** kpow, 0.5 at pl = kp
    dn = prof.get("denial", DENIAL)             # [user decision 15 Oct afternoon] per-champion denial term (Vesper 60)
    pat = prof.get("patrol", prof.get("hunt", 0) > 0)   # sighting hunt / patrol switch (Vesper: from 15 shards only)
    for c, p, hp, bag, dd, st in s.enemies:
        ttk = -(-int(hp) // int(s.S))
        fin = ttk <= 2                          # finisher: dies in <= 2 of my hits
        if r < w.kh_until and not fin:
            continue
        if w.kfail.get(int(c), -1) > r:
            continue                            # [bug fix 15 Oct, ladder 4] a chased-out kill: no finisher exemption
        if near_espawn(w, p):
            continue                            # [user decision 15 Oct] on / next to their spawn: heals to full, finishers too
        try:
            chan = c.is_submitting_gems() or c.is_recalling()
            stun = (not chan) and dd <= reach + 3 and c.buffs().has_stun()
        except Exception:
            chan = stun = False
        # P8 finisher: a recall / tribute pins >= 5 turn ends and a walker gains <= 1 tile/turn [rules], so a
        # near-dead target within reach + 2 ttk + 2 is closable (ladder: a 1-HP enemy recalled 3 tiles away)
        # [rule, 15 Oct ladder 3] HUNT: a phase's `hunt` tiles extend the reach (Vesper 12 from 15 shards); the
        # walk is in rounds below and exec_kill gives up after the phase's `chase` rounds without closing
        hr = reach + prof.get("hunt", 0)
        far = 0
        if not (chan or stun or dd <= hr or (fin and dd <= reach + 2 * ttk + 2)):
            continue
        value = bag + 50 * g2g(r) + dn
        rounds = max(0, dd - ME.get("range", 1)) + ttk + far
        pl = s.plose
        if SMOOTH_ON:
            value *= (1 - pl) ** kpow           # smooth gate: x0.5 at pl = kp; risk pl x fcost unchanged below
        elif pl > kp:                           # tried 15 Oct: x min(1, hp/maxhp/0.5), x0.67 carrying > 40 [measured: worse]
            continue
        if fin:
            w.excl.pop(("kill", int(c)), None)  # finishers ignore the kill exclusion (P(lose) vs ~0 HP is ~0)
        # [deviation] (value - risk) / rounds: PRICES' value / rounds - risk subtracts gems from gems/round, so an
        # even fight never priced and farmers took hits without answering. Risk P(lose) x death_cost, added below.
        am = ATTACKER_BONUS if s.attacker is not None and int(s.attacker[0]) == int(c) else 1.0
        fights.append((value, max(1, rounds), kmul * pm[e_side(w, p)] * am, pl, "kill", int(c)))
    # HUNT a sighting [rule, 15 Oct ladder 3]: hunt phase only, nobody visible, fresh byte 5 -> walk to its altar.
    # value = HUNT_BAG + 50 g2g + DENIAL [guess bag], rounds = walk + 5; Lanchester vs s.sc enemies at my base stats.
    if (pat and not s.enemies and s.sc and s.sage <= SIGHT_FRESH and s.sa < len(w.apos)
            and r >= w.kh_until):
        a = s.sa
        wk = w.walk_to(f"a{a}", s.pos)
        if wk is None or wk >= FAR:
            wk = s.pos.chebyshev_distance(w.apos[a])
        if near_espawn(w, w.apos[a]):
            wk = FAR                            # [user decision 15 Oct] kill exclusions: no hunt onto their spawn
        us = s.hp * s.S + sum(x[2] * x[3] * lw(x[1].chebyshev_distance(s.pos)) for x in s.allies
                                 if x[1].chebyshev_distance(s.pos) <= LANCH_R)
        th = s.sc * ME.get("hp", s.maxhp) * ME.get("strength", s.S)
        pl = th / max(1.0, us + th)
        if pl <= kp and wk < FAR:               # risk P(lose) x death_cost [user plan 15 Oct, ladder 4]
            fights.append((HUNT_BAG + 50 * g2g(r) + dn, wk + 5, kmul, pl, "hunt", a))
    if s.sc >= 3 and s.sage < SIGHT_LIVE:
        w.big3 = max(w.big3, r - s.sage)
    if pat and not s.enemies and r >= w.kh_until and not (s.sc and s.sage <= SIGHT_FRESH):
        # [user plan 15 Oct, ladder 4] patrol: no fresh sighting -> the nearest enemy-side altar (aside 2) I have not
        # reached in HUNT_REVISIT rounds; none reachable -> the enemy-side group with the most gems (target 100 + h)
        al = [(w.walk_to(f"a{i}", s.pos) or s.pos.chebyshev_distance(w.apos[i]), i) for i in range(len(w.apos))
              if w.aside[i] == 2 and w.ad[i] < FAR and r - w.hvis.get(i, -999) >= HUNT_REVISIT]
        gs = [(o.gems, h) for h, o in w.G.items() if o.side == 2 and w.gd.get(h, FAR) < FAR] if not al else []
        tgt = min(al) if al else (None, 100 + max(gs)[1]) if gs else None
        if tgt is not None and near_espawn(w, w.apos[tgt[1]] if tgt[1] < 100 else w.G[tgt[1] - 100].anchor):
            tgt = None                          # [user decision 15 Oct] kill exclusions: no patrol onto their spawn
        if tgt is not None:
            wk = tgt[0] if al else w.gd[tgt[1] - 100]
            us = s.hp * s.S + sum(x[2] * x[3] * lw(x[1].chebyshev_distance(s.pos)) for x in s.allies
                                 if x[1].chebyshev_distance(s.pos) <= LANCH_R)
            th = 2 * ME.get("hp", s.maxhp) * ME.get("strength", s.S)         # assumed 2 enemies at my base stats
            pl = th / max(1.0, us + th)
            # roam only with a strength lead [user plan 15 Oct; guess]: x clamp(S / 100 - 1, 0, 2); x 0.5 while a
            # sighting of >= 3 enemies is <= ROAM_STACK rounds old (a hunting team: don't wander)
            w.roam = min(2.0, max(0.0, s.S / 100 - 1)) * (0.5 if r - w.big3 <= ROAM_STACK else 1.0)
            if pl <= kp and w.roam > 0:
                fights.append((HUNT_BAG + 50 * g2g(r) + dn, wk + 10, kmul * w.roam, pl, "hunt", tgt[1]))
    # HOLD: contested altar, stun or lock gold, a fresh sighting there
    if s.sc and s.sage < SIGHT_LIVE:
        a = s.sa
        # spec: stun OR lock gold; we never buy or place locks, so only a stun counts [deviation]
        if a < len(w.apos) and w.aside[a] == 1 and ME.get("has_cc") and                 r >= w.kh_until and s.plose <= HOLD_PLOSE:
            wk = w.walk_to(f"a{a}", s.pos)
            if wk is None or wk >= FAR:
                wk = max(0, w.ad[a] - 1)
            out.append((30 * THEIR_RATE / (wk + 30) * prof["hold"] * pm["hold"], "hold", a))
    # JOIN a fight [rule, 15 Oct ladder 2: nobody converged]: an ally within JOIN_FIGHT_R broadcasting kill (code 3) ->
    # KILL's price with the ally and me in the Lanchester bodies, x POSTURE["defend"]["join"] whatever my posture.
    # Target not in my vision: its spot = the ally's, bag 0, ttk JOIN_TTK. exec_join walks to the ally; KILL takes over.
    for c, p, hp, st in s.allies:
        k = w.ally_slot(c)
        op, tg = by.get(k, (0, 0))
        sos = None
        if op != 3:
            continue
        if not 2 < p.chebyshev_distance(s.pos) <= JOIN_FIGHT_R or r < w.kh_until:    # <= 2: there, KILL
            continue
        e = sos or next((x for x in s.enemies if int(x[0]) & 31 == tg), None)
        ep, eb, ttk = (e[1], e[3], -(-int(e[2]) // int(s.S))) if e else (p, 0, JOIN_TTK)
        if near_espawn(w, ep):
            continue                            # [user decision 15 Oct] kill exclusions: the target is on their spawn
        th = sum(x[2] * x[5] for x in s.enemies if x[1].chebyshev_distance(ep) <= 5)
        uo = sum(a[2] * a[3] for a in s.allies if a[0] == c or a[1].chebyshev_distance(ep) <= 5)
        pl0 = th / max(1.0, uo + th)            # the ally's P(lose) without me
        pl = th / max(1.0, s.hp * s.S + uo + th)
        # [user plan 15 Oct, ladder 6] only when the ally needs me (P(lose) without me > JOIN_NEED), and the value is
        # marginal: (P(win) with me - P(win) without me) x the fight value (ladder: joins priced like the kill itself,
        # ~30, so three champions ran to fights Vesper already won alone). Rounds and the join multiplier unchanged.
        if pl0 > JOIN_NEED and pl <= kp:
            fights.append(((pl0 - pl) * (eb + 50 * g2g(r) + dn),
                           max(1, max(0, s.pos.chebyshev_distance(ep) - ME.get("range", 1)) + ttk),
                           kmul * POSTURE["defend"]["join"], pl, "join", k))
    # [user plan 15 Oct, ladder 4] one currency for a death: death_cost = min(DCOST_CAP, 60 rounds x max(MY_RATE, my
    # best raw price this turn among FARM, KILL, JOIN a fight and HUNT)) + my bag. Raw = value / rounds, no multipliers
    # and no risk term (not circular). With the multipliers (Vesper kill ~7.6) it reached 4,600 and stopped all fights.
    bf = rawb
    for v, rd, _m, _pl, _o, _t in fights:
        if v / rd > bf:
            bf = v / rd
    s.dcost = dcost = min(DCOST_CAP, DEATH_OUT * max(MY_RATE, bf)) + s.bag
    fcost = min(prof.get("dcost_fight", DCOST_FIGHT_CAP), dcost)   # [user plan 15 Oct, ladder 5/6] fights risk at most 150 (key dcost_fight); HEAL keeps dcost
    for v, rd, m, pl, o, tg in fights:
        out.append(((v - pl * fcost) / rd * m, o, tg))
    # HEAL: what a death costs (death_cost: bag + 60 rounds of my best farm price) x P(die), over a recall (5) + the walk back out.
    # P(die) = (1 - hp/maxhp) x (1 + enemies within 8) x HEAL_K, clamped to [0, 1]; at least STACK_HEAL with >= 3
    # enemies within 8 and no ally within 5, even at full HP (HEAL is then "go home": the executor walks while an
    # enemy is within 6 and recalls only once clear), but only while s.plose > HEAL_PLOSE.
    # [rule, 15 Oct ladder 2] an enemy within 8 and s.plose <= HEAL_PLOSE: HEAL 0, I can win or trade, fight instead
    # (ladder: healthy champions ran from one enemy and took free hits). No enemy within 8: camp damage heals as before.
    ne8 = 0
    for e in s.enemies:
        if e[4] <= 8:
            ne8 += 1
    # [user plan 15 Oct, ladder 5] near enemies I beat (plose < 0.3) are not danger: the (1 + ne8) factor is 1
    pdie = min(1.0, (1 - s.hp / s.maxhp) * (1 + (ne8 if s.plose >= 0.3 else 0)) * HEAL_K)
    if ne8 >= 3 and s.plose > HEAL_PLOSE and not s.spawn and not any(a[1].chebyshev_distance(s.pos) <= 5 for a in s.allies):
        pdie = max(pdie, STACK_HEAL)
    if ne8 and s.plose <= HEAL_PLOSE:
        pdie = 0
    if ne8 and s.hp < HEAL_LOW * s.maxhp:
        pdie = max(pdie, HEAL_FLOOR)            # [rule, 15 Oct ladder 3] low HP near an enemy: whatever plose says
    hc = dcost
    if not ne8:
        # [user plan 15 Oct, ladder 6] no enemy within 8: HEAL 0 at hp >= HEAL_NOENEMY_HP, below that the death cost
        # is capped at HEAL_NOENEMY_CAP (ladder: 64 % HP and nobody in sight chose heal 15 over farm 10)
        if s.hp >= HEAL_NOENEMY_HP * s.maxhp:
            pdie = 0
        hc = min(HEAL_NOENEMY_CAP, dcost)
    if pdie > 0 and flee_ok(s):
        wb = fget(w.F_home, s.pos) if w.F_home is not None else s.pos.chebyshev_distance(w.sp0)
        # posture heal (economy 0.7) on regime many only [user plan 15 Oct, ladder 6]
        hm = pm["heal"] if w.d and w.d.get("regime") == 2 else 1.0
        out.append((pdie * hc / (5 + min(wb, HEAL_WB)) * prof.get("heal", 1.0) * hm, "heal", 0))
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
    return out


SALT = 0                    # tools/field.py --salts: per-salt jitter on prices (0 = off, the real bot)
SALT_EPS = 0.02             # [guess, as tzunami-lite] jitter size: only near-ties change


def salt_j(r, slot, o, t):
    """SALT jitter factor in [1 - SALT_EPS, 1 + SALT_EPS) (deterministic; no hash(): str hashes are salted per run)."""
    v = (SALT * 1000003 + r * 7919 + slot * 104729 + ord(o[0]) * 131 + len(o) * 17 + (t if isinstance(t, int) else 0)) \
        * 2654435761 & 0xFFFF
    return 1.0 + SALT_EPS * (v / 32768.0 - 1.0)


def choose(w, s):
    """Argmax with a HOLD_TURNS hold, then hysteresis; returns True when the choice changed.
    [rule, 15 Oct ladder 3] the HOLD_TURNS hold applies to HEAL too (ladder: heal/kill/heal/bank/heal dither with a
    44 bag); only retreat_now breaks it. Farm -> another farm while engaged (a live monster of my group within
    CAMP_R) needs ENGAGED_HYST, not HYST. HEAL is never excluded (a death or timeout while healing must not forbid
    the next heal)."""
    cur = w.cur
    cl, by = claims(w, s)
    w.claims = cl
    lo = w.slot + 1 if w.twin else w.slot       # [C6] Issac ranks just after Cassi (her slot counts as lower)
    w.lowcn = {}                                # [T3] group -> claimants with a lower slot than mine (my crew rank)
    for k, (op, tg) in by.items():
        if k < lo and op == 1 and tg in w.idx:
            w.lowcn[w.idx[tg]] = w.lowcn.get(w.idx[tg], 0) + 1
    ps = price_all(w, s, cl, by)
    r = s.r
    if SALT:
        ps = [(t[0] * salt_j(r, w.slot, t[1], t[2]), t[1], t[2]) for t in ps]    # tools/field.py --salts
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
    if TRACE and s.attacker is not None and w.cur[0] in ("heal", "fall") or TRACE and s.attacker is not None and best[1] in ("heal", "fall"):
        trace("flee", f"{w.cur[0]}->{best[1]} att={int(s.attacker[0])} d={s.attacker[4]} trapped={int(s.trapped)} "
                      f"ok={int(flee_ok(s))} hp={s.hp / s.maxhp:.2f} pl={s.plose:.2f}")
    going = curp is not None and curp > 0 and w.status == "going"
    held = going and r - w.started < HOLD_TURNS and not retreat_now(s)
    # [user plan 15 Oct, ladder 5] a KILL on a still-visible target, or a HUNT on a fresh sighting while it prices,
    # holds for the phase's `chase` rounds (default 3) whatever its price, unless hp < 30 % or retreat_now (ladder:
    # Vesper chose a kill, stepped once, it priced negative and she dropped it, 4 times in one game)
    if (w.status == "going" and s.hp >= 0.3 * s.maxhp and not retreat_now(s)
            and r - w.started < ME["prof"].get("chase", 3)
            and ((cur[0] == "kill" and any(int(e[0]) == cur[1] for e in s.enemies))
                 or (cur[0] == "hunt" and curp is not None and cur[1] == s.sa and s.sc and s.sage <= SIGHT_FRESH))):
        held = True
    hy = HYST
    if cur[0] == "farm" and best[1] == "farm" and best[2] != cur[1]:
        hy = race(w)["farm_hyst"] if SUNK_ON or not engaged(s, cur[1]) else ENGAGED_HYST
    if SUNK_ON and best[1] != "heal" and not retreat_now(s):
        hy = max(hy, 1.0 + SUNK_K * w.prog)     # [IMPROVEMENTS 2] sunk progress; HYST / farm_hyst stay the floor
    keep = held or (going and best[0] <= curp * hy) or \
           (cur[0] == "fall" and best[1] == "fall" and w.status == "going")
    if keep:
        return False
    new = (best[1], best[2])
    if new == cur and w.status == "going":
        return False
    hit, pg = w.hit, w.prog
    w.set_cur(new, r, s)
    if TRACE:
        t2 = ps[1] if len(ps) > 1 else (0.0, "-", None)
        bfi = max((t[0] for t in ps if t[1] in ("kill", "hunt") or (t[1] == "join" and by.get(t[2], (0,))[0] == 3)),
                  default=0.0)
        trace("choice", f"{new[0]} {tname(w, new[0], new[1])} {best[0]:.2f} | {t2[1]} {tname(w, t2[1], t2[2])} "
                        f"{t2[0]:.2f} cur={curp if curp is None else round(curp, 2)} bag={s.bag} "
                        f"hp={s.hp / s.maxhp:.2f} fight={bfi:.2f} dcost={s.dcost:.0f} pl={getattr(s, 'plose', 0):.2f} ne={s.near_e} "
                        f"d={w.G[new[1]].anchor.chebyshev_distance(s.pos) if new[0] == 'farm' and new[1] in w.G else '-'} "
                        f"from={cur[0]}:{cur[1]} hit={int(hit)} prog={pg:.2f}"
                        + (f" crew={w.ncrew} cl={w.claims.get(new[1], 0)} live={living(w, s)} call={s.call}" if new[0] == "farm" else "")
                        + (f" roam={w.roam:.2f}" if new[0] == "hunt" and new[1] != s.sa else "")
                        + "".join(f" tp={e[1].x},{e[1].y} desp={min(e[1].chebyshev_distance(q) for q in w.esp.positions())}"
                                  for e in s.enemies if new[0] == "kill" and int(e[0]) == new[1]))
    return True


def tname(w, op, tg):
    if tg is None:
        return "-"
    if op == "farm":
        o = w.G.get(tg)
        return f"g{tg}@{o.anchor.x},{o.anchor.y}" if o else str(tg)
    if op == "hunt" and tg >= 100:
        return f"g{tg - 100}"
    if op in ("bank", "hold", "hunt"):
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
    """My byte (slot) when it changed; the crew call (byte 7); bytes 5-6 sighting (count | stamp, region altar)."""
    if w.cur[0] == "ward" and w.cur[1] is not None:
        b = ((w.cur[1] + 1) & 31) << 3         # code 0, target = ward index + 1
    elif code == 7:
        b = 7 | w.dead_mi << 3                  # dead: the group I died on (the team avoids it while I am out)
    else:
        hb = 31                                 # hunt: 31 = sighting / patrol
        b = code | ((hb if w.cur[0] == "hunt" else tbits(w, OPT[code], w.cur[1])) << 3 if 0 < code < 7 else 0)
    if b != w.sent and not w.twin:              # [C6] Issac shares Cassi's slot: only Cassi writes it
        try:
            cambc.shared_memory[w.slot] = b
            w.sent = s.mem[w.slot] = b
        except Exception:
            pass
    if w.twin:
        return
    # [T3] the crew call: a crew take with no live call and claimants short of the crew calls it; my call
    # ends when my byte leaves its group
    b7, me = s.mem[7], w.slot + 1
    h = w.cur[1] if w.cur[0] == "farm" else None
    c7 = b7
    if h in w.G and w.ncrew >= 2 and s.call is None and claimants(w, s, w.G[h].mi) < w.ncrew:
        c7 = me << 5 | w.G[h].mi
    elif b7 >> 5 == me and b != 1 | (b7 & 31) << 3:
        c7 = 0
    if c7 != b7:
        try:
            cambc.shared_memory[7] = c7
            s.mem[7] = c7
        except Exception:
            pass
    if not s.alive:
        return
    try:
        if s.sc and s.sage >= SIGHT_LIVE:
            cambc.shared_memory[5] = 0
            s.sc, s.sage = 0, 999
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
