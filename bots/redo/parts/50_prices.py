"""Sense (Snap) and price the options (strat/PRICES.md) in team gems per round; 70_updaters chooses. The 8 shared
bytes are read and written by Comms (40_comms).
"""

KEEP_HP = 0.4               # [guess] the hit body keeps >= 40 % of max HP (KEEP_FRAC)
HYST = 1.2                  # switch only when a new option beats the current one by 20 %
KILL_PL_POWS = {0.6: 0.756, 0.95: 0.231}    # KILL value x (1 - pl) ** pow, pow = ln(0.5) / ln(1 - kill_plose): the factor
KILL_PL_POW = 0.756                         # is 0.5 at pl = kill_plose (no math module: precomputed; other kp -> this)
EXCL = 20                   # rounds an (option, target) is excluded after a timeout / failure
DENIAL = 24                 # default of the profile key `denial` (Vesper 60, 20_champs); [measured-ish] their farm rate 0.4 g/r x 60 rounds out (PRICES KILL)
THEIR_RATE = 0.4            # [guess] their gems per round per body (HOLD value 30 x 0.4)
P_NEAR = 0.5                # [guess] P(lose the bag) with an enemy within 8
DANGER_W = 0.2              # [guess] P(lose the bag) per unit of draft danger (cell value / 14)
SHOP_RETURN = True          # [deviation] SHOP rounds include the walk back from spawn to where I am
SURVIVE = 0.6               # [tuned] k bodies are enough if the most-hit body keeps > 40 % of its current HP
WAIT_PARTNER = 15           # [guess] rounds added to a pair take while the partner is not committed
# Group game [user plan 15 Oct, game type + pair/trio opener; all guess]: while stack_mode() (round < GROUP_UNTIL and the
# draft's solo share <= GROUP_SOLO_MAX) the team opens in subgroups (70_updaters opening_slots: trio + pair / two pairs /
# pair + solo), prices groups for its subgroup without the per-body split and never waits at a camp (60_behaviors Farm).
# One body captures in every mode (60_behaviors handoff, 06 section 1.2). GROUP_UNTIL 0 = off (behaviour unchanged).
OPEN_END = 100              # GUESS 06 section 4.1: before this round the whole team is one subgroup on every map (stack rules)
GROUP_UNTIL = 300           # rounds; group mode is on while s.r < this (0: never) [measured 15 Oct: bench open-groupG, 6/6 group-map games won]
GROUP_SOLO_MAX = 0.4        # [guess] group game when the draft's solo share (groups needing 1 body / all) <= this
GROUP_GEMS_MIN = 0.7        # [user decision 15 Oct; guess] ... or when the share of gems in groups needing >= 2 >= this (> 1: off)
BODY_EXP = 1.0              # FARM value / bodies ** this outside stack mode (1.0 = per-body split, today)
STACK_BODY_EXP = 0.0        # the same exponent in stack mode (0.0: value not split, the stack clears 5x faster)
STACK_WAIT_PARTNER = 0      # replaces race()["wait"] (WAIT_PARTNER) in farm_price in stack mode
GROUP_BANK_BAG = 100        # [guess] group mode: a bag >= this banks at x GROUP_BANK_X x bag / GROUP_BANK_BAG (the carry
GROUP_BANK_X = 12.0         # holds the subgroup's gems and its farm prices are unsplit; rows: 396 carried at r300)
                            # [user decision 15 Oct; was 4.0] ladder 173c26eb: Vesper held 66 -> 264 gems r75-r203, BANK 4.5-39 < FARM 49-65
SHOP_MUST = 300             # 06 section 4.5 (user): a body must shop at this gold; below it SHOP waits for the next emblem
SHOP_MUST_X = 3.0           # GUESS: SHOP x this from SHOP_MUST gold (was group mode only; ladder 173c26eb: 1128 gold at r245 unspent)
STACK_FOLLOW = 3.0          # in group mode FARM x this on a group a LOWER slot of my subgroup farms (UPD.lowsub)
JUNGLE_MIT = 0.3            # [rules] a finished Jungle emblem (any stat): 30 % less damage from camps
RECALL_HOME = 3             # [rules] a Home emblem: "five turn ends become three" (06 section 1.3)
SHIELD_COVER = 0.6          # [measured 17 Oct, A59] the shield took every camp hit in its window (0 HP lost to 273 hits); its 5
                            # turns per 8-turn cooldown covered 59 % of Varg's hit rounds (62.5 % at most)
SPAWN_KILL_R = 2            # [user decision 15 Oct] KILL / JOIN a fight / HUNT price 0 on targets within this of an enemy
                            # spawn tile (it heals to full at turn end [rules], camps ring it); Kill fails there (-1: off)
FUEL_FLOOR = 400_000        # after sensing: below this skip pricing, repeat the executor step
DECIDE2_FUEL = 1_500_000    # GUESS 08 section 5.1: a second decide in one turn only above this (was 900k: fight turns rolled over)
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
SCAN_FUEL = 900_000         # [guess] no scan ward below this fuel left
BANK_NEAR = 8               # [guess] walk to the altar at or below which BANK gets the tempo bonus
BANK_NEAR_BONUS = 1.0       # [guess] BANK x (1 + this) when the altar is near: a 22-gem bag next to an altar banks now
KILL_PER_SHARD = 0.15       # [guess] KILL multiplier = prof kill + this x shards owned (emblems count their shards)
SIGHT_FRESH = 8             # rounds a sighting drives posture (defend / punish) and the stack terms
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
GROUP_KILL_X = 2.0          # [user decision 15 Oct afternoon; guess] group mode: the main carry's fight multiplier x this
REWARD_X = 1.0              # [measured 15 Oct] FARM on a cleared group (reward waiting) x this; 2.0 lost the r300 bench (8/18 vs 11/18, -242 vs +806 summed)
FLIP_WINDOW = 10            # [user decision 15 Oct afternoon] farm target A -> B -> A within this many rounds ...
FLIP_LOCK = 30              # ... excludes B for this many rounds (trace `flip lock`)
LANCH_R = 8                 # [rule, 15 Oct ladder 3] Lanchester bodies: everyone within this of ME (was: within 5 of
                            # the target; kills were approved, then 3 enemies arrived from 6-8 tiles)
DUEL_EXP = 2                # GUESS 08 section 5.1: P(lose) = x^2 / (1 + x^2), x = their square-law strength / ours
STUN_F = 0.3                # GUESS 08 section 5.1: a one-round stun per 8 turns ~ 0.3 x Focus of damage (a lost enemy turn)
REN_RET = 0.2               # [rules] Ren retaliates 0.2 x Focus when damaged (counted as one hit taken a turn)
# 08 section 5.1, M5: ChampionType -> (attack reset, ability damage in Focus per 8 turns, shield in Focus per 8 turns) [rules
# kits]: Varg (shield 2.5 F), Vesper, Ren (1.25 F + stun, retaliation), Ryth (1 F + stun), Vendetta, Marcella (2 F + stun)
FKIT = {10: (1, 0.0, 2.5), 1: (1, 0.0, 0.0), 9: (0, 1.25 + STUN_F + 8 * REN_RET, 0.0), 0: (1, 1.0 + STUN_F, 0.0),
        2: (1, 0.0, 0.0), 7: (1, 2.0 + STUN_F, 0.0)}
FIGHT_FARM = 2              # 08 F1: with an enemy within 8, FARM prices only the current target + this many nearest groups
HEAL_LOW = 0.3              # [guess] below this HP fraction with an enemy within 8, HEAL P(die) >= HEAL_FLOOR
HEAL_FLOOR = 0.8            # [guess] whatever plose says (ladder: farm 3.34 beat heal 2.96 at 10 HP, 44 bag, 2 enemies)
HEAL_WB = 15                # [guess] HEAL divisor uses min(walk back, this): far from spawn must not zero the heal
# [IMPROVEMENTS 2, 15 Oct night] sunk progress: the current job's price in the switch test is curp x max(hy, 1 + SUNK_K
# x w.prog) (w.prog 0..1 from 60_behaviors prog_update), except against HEAL or under retreat_now.
SUNK_K = 2.0                # [guess] a job 80 % done needs a 2.6x better alternative
PROG_STALL = 8              # [guess] rounds without a rise of w.prog (going, not attacking / capturing / waiting /
                            # recalling / channelling) -> the choice fails like the stuck guard (`failed stall`)
HUNT_BAG = 30               # [guess] expected bag of a sighted enemy (sighting hunt value)
HUNT_REVISIT = 150          # [guess; 60 -> 150 user plan 15 Oct, ladder 5: chain patrol] rounds before a patrol hunt goes back to an enemy altar I reached
ROAM_STACK = 60             # [guess] rounds a >= 3-enemy sighting halves the no-sighting hunt
HUNT_MAX = 40               # rounds a sighting hunt walks before it gives up


KILL_G = 100                # X4 [sdk 3.0.1]: gold for a kill (50 before 3.0); base_init re-reads constants.KILL_GOLD
KILL_PRICE = 1.0            # share of the kill gold the fight prices count: 1 since 08_FIGHT F6 re-priced P(lose) (duel);
                            # 0.5 was a stopgap while the old optimistic Lanchester took lost fights (07 section 14, X4)
                            # (module level cannot: the game API is unavailable while modules preload [measured])
G2G_K = 0.5                 # [tuned 15 Oct; PRICES guess 1.5] gems per gold at round 0
SHUT_GATE = 500             # GUESS 06 section 1.4: a gate group's value while every altar is gated (the gems it unlocks)


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


SPLASH_K = 1.0              # [user decision 15 Oct] splash champions (profile `splash`, Varg): live clear model Strength x
                            # 1 + SPLASH_K x (min(3, max over live monsters of 1 + live neighbours within 1) - 1); 0 = off
SPLASH_M = {}               # (group, round) -> splash count this round (splash_m cache)


def splash_m(w, s, h):
    """[user decision 15 Oct, Varg's splash, rules: Strength onto every other monster within radius 1 of the target]
    Damage multiplier of MY basic attack on group h: 1 + SPLASH_K x (min(3, m) - 1), m = max over its live monsters
    (visible ones, else the group's spawn tiles) of 1 + live neighbours within Chebyshev 1. 1.0 without the flag."""
    if SPLASH_K <= 0 or not ME["prof"].get("splash"):
        return 1.0
    key = (h, s.r)
    m = SPLASH_M.get(key)
    if m is None:
        lv = s.live.get(h)
        pts = [p for _c, hp, p, _st in lv if hp > 0] if lv else w.G[h].tiles
        m = 1
        for p in pts:
            n = 0
            for q in pts:
                if q.chebyshev_distance(p) <= 1:
                    n += 1
            if n > m:
                m = n
        if len(SPLASH_M) > 64:
            SPLASH_M.clear()
        SPLASH_M[key] = m
    return 1.0 + SPLASH_K * (min(3, m) - 1)


def s_eff(w, s, h, k):
    """Per-body Strength of k bodies on group h for clear_dmg: me with my splash multiplier, the k - 1 others plain
    (only I splash): s.S x (splash_m + k - 1) / k."""
    m = splash_m(w, s, h)
    return s.S if m == 1.0 else s.S * (m + k - 1) / max(1, k)


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
# farm -> farm switch while not engaged, wait = WAIT_PARTNER, bank_ret = BANK rounds count the walk back (2 x walk).
# "race": regime many, or pick with >= RACE_RICH groups per body; "base" (few, other pick, unknown): the old numbers.
RACE = {"race": dict(walk_w=2.0, farm_hyst=2.0, wait=30, bank_ret=2),
        "base": dict(walk_w=1.0, farm_hyst=HYST, wait=WAIT_PARTNER, bank_ret=1)}
RACE_RICH = 4


def group_map(w):
    """[user plan 15 Oct, game type] the draft's solo share <= GROUP_SOLO_MAX or [user decision 15 Oct] its group-gem
    share ggems >= GROUP_GEMS_MIN: the team plays in subgroups after the opening (70_updaters group_slots)."""
    return bool(w.d) and (w.d.get("solo", 1.0) <= GROUP_SOLO_MAX or w.d.get("ggems", 0.0) >= GROUP_GEMS_MIN)


def stack_mode(w, r):
    """Stack rules (subgroup pricing, no waiting, STACK_FOLLOW): the opening on every map (r < OPEN_END, 06 section
    4.1, P9 concentrate), then on a group map while r < GROUP_UNTIL; cached per round on w, traces `stack on/off` on
    each change. Depends on the draft summary and r only: every champion agrees."""
    if getattr(w, "sm_r", -1) == r:
        return w.sm
    on = r < OPEN_END or r < GROUP_UNTIL and group_map(w)
    if on != getattr(w, "sm", False):
        trace("stack", f"on solo={w.d.get('solo', 1.0):.2f} ggems={w.d.get('ggems', 0.0):.2f} open={OPEN_END} "
                       f"until={GROUP_UNTIL if group_map(w) else OPEN_END}" if on else "off")
    w.sm, w.sm_r = on, r
    return on


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


def sub_size(w):
    """[user plan 15 Oct, pair/trio opener] my opening subgroup's size (70_updaters opening_slots: w.subs), the team if
    unknown."""
    sb = getattr(w, "subs", None)
    return len(sb[w.slot]) if sb and w.slot in sb else max(1, len(w.roster))


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


CLEAR_MEMO = {}


class Snap:
    __slots__ = ("r", "st", "shut", "alive", "recalling", "submitting", "can_move", "can_attack", "pos", "hp", "maxhp",
                 "bag", "gold", "S", "enemies", "allies", "live", "vis", "mem", "slots", "spawn", "near_e", "P", "walt", "edps", "plose",
                 "sc", "sa", "sage", "stack", "dead_g", "dcost", "attacker", "trapped", "ba", "bwk", "sap")


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
    s.enemies, s.allies, s.live, s.near_e = [], [], {}, 99
    s.dcost = 0.0
    s.attacker, s.trapped = None, False
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
    # 08 F5 (M1, M2): a melee attacker only; a ranged one at d <= 2 costs (4 - d) shots to leave, then none
    if s.hp < (getattr(w, "hp_alive", 0) or 0):
        hit = [e for e in s.enemies if e[4] <= arng(e[0]) + 1]
        if hit:
            s.attacker = e = min(hit, key=lambda x: x[4])
            wb = fget(w.nav.F_home, pos) if w.nav.F_home is not None else pos.chebyshev_distance(w.sp0)
            s.trapped = arng(e[0]) <= 1 and e[4] <= 2 and wb > 6 and not any(a[1].chebyshev_distance(pos) <= 6 for a in s.allies)                 and not (w.nav.dash_ab is not None and w.nav.dash_ab.is_ready())
    s.vis = None
    hs = list(w.nav.near6)
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
    if s.attacker is None and s.hp < (getattr(w, "hp_alive", 0) or 0) and not any(
            p.chebyshev_distance(pos) <= crng(c) for lv in s.live.values() for c, _hp, p, _st in lv):
        w.uhit = r                              # 08 F4 (M4, P-a): hit by nobody I can see (a bush): no recall for a while
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
    order = sorted((i for i in range(len(w.apos)) if w.altar_open(i)), key=lambda i: w.nav.ad[i])
    if not order:
        return 0, FAR                           # X8: every altar gated (the gate camps' unlock value, farm_price)
    a = order[0]
    if w.aside[a] == 2 and w.bank < len(w.apos) and w.altar_open(w.bank):
        a = w.bank
    if sap is not None:
        # [deviation] spec: "the altar farthest from the sighting among safe ones". Here safe = draft side 0/1,
        # reachable and more than STACK_R from the stack's altar, and the nearest such by walk wins (the
        # farthest can be across the map); none safe: the one farthest from the stack.
        ok = [i for i in order if w.aside[i] <= 1 and w.nav.ad[i] < FAR]
        away = [i for i in ok if w.apos[i].chebyshev_distance(sap) > STACK_R]
        if away:
            a = away[0]
        elif ok:
            a = max(ok, key=lambda i: w.apos[i].chebyshev_distance(sap))
    wk = w.nav.walk_to(f"a{a}", s.pos)
    if wk is None or wk >= FAR:
        wk = max(0, w.nav.ad[a] - 1)
    return a, wk


def my_dmg(dmg, k, clear):
    """Camp damage I take in a k-body take dealing dmg over clear rounds: tank(k) of it (TANK_SHARE); [K3] less
    my Jungle emblem's 30 % [rules] and what my shield absorbs: SHIELD_COVER of it, at most its amount per cast, one cast
    per 8 rounds (cooldown [rules]; A59 measured)."""
    d = dmg * tank(k)
    d *= ME.get("jmit", 1.0)
    sa = ME.get("shield_amt", 0)
    if sa:
        d -= min(SHIELD_COVER * d, sa * (1 + clear // 8))
    return d


def mit_refresh(w):
    """[K3] ME['jmit'] (0.7 with a Jungle emblem of any stat) and ME['shield_amt'] (the shield slot's amount
    now: it grows with Focus; 0 without KIT_ON) for my_dmg; ME['recall'] (RECALL_HOME with a Home emblem, else 5
    [rules]) for HEAL and SHOP. Every 20 rounds and after a buy."""
    j, rc = 1.0, 5
    try:
        n = w.me.item_count()
        for it in (cambc.ItemType.JUNGLE_EMBLEM_OF_STRENGTH, cambc.ItemType.JUNGLE_EMBLEM_OF_FOCUS,
                   cambc.ItemType.JUNGLE_EMBLEM_OF_HEALTH):
            if n[int(it)] > 0:
                j = 1 - JUNGLE_MIT
        for it in (cambc.ItemType.HOME_EMBLEM_OF_STRENGTH, cambc.ItemType.HOME_EMBLEM_OF_FOCUS,
                   cambc.ItemType.HOME_EMBLEM_OF_HEALTH):
            if n[int(it)] > 0:
                rc = RECALL_HOME
    except Exception:
        pass
    ME["jmit"], ME["recall"] = j, rc
    a = w.kit.shield_ab
    try:
        ME["shield_amt"] = a.shield_amount() if a is not None else 0
    except Exception:
        ME["shield_amt"] = 0


def farm_price(w, s, h, bodies, walk, c=None):
    o = w.G[h]
    if o.st == "resp" and o.until > s.r:
        return 0.0
    rc = race(w)
    walk *= rc["walk_w"]
    prof = ME["prof"]
    value = o.gems + g2g(s.r) * o.gold * prof["gold"]
    if s.shut:
        # X8 (06 section 1.4): no altar open, so gems bank nowhere until a gate group falls; a 0-0 game goes to
        # lifetime gold earned [rules], so every body prices gold at the round-0 rate (P5: know the ground)
        value = G2G_K * o.gold + (SHUT_GATE if h in w.gates else 0)
    sm = stack_mode(w, s.r)
    bx = STACK_BODY_EXP if sm else BODY_EXP     # [user plan 15 Oct, stack opener] value / bodies ** bx
    div = max(1, bodies) if bx == 1.0 else max(1, bodies) ** bx
    if o.st == "reward":
        return value / div / (walk + 5) * REWARD_X     # [user decision 15 Oct afternoon] free gems beat a clear
    Se = s_eff(w, s, h, bodies)                 # [user decision 15 Oct] my Strength x my splash (50_prices s_eff)
    if o.hp is None:                            # full HP: cached per (group, bodies, my Strength)
        key = (h, bodies, Se)
        cd = CLEAR_MEMO.get(key)
        if cd is None:
            if len(CLEAR_MEMO) > 400:
                CLEAR_MEMO.clear()
            cd = CLEAR_MEMO[key] = clear_dmg(o.mons, Se, bodies)
        clear, dmg = cd
    else:
        mons = [m for m in o.hp if m[0] > 0]
        if not mons:
            return value / div / (walk + 5)
        clear, dmg = clear_dmg(mons, Se, bodies)
    per = my_dmg(dmg, bodies, clear) + s.edps * min(clear + 5, 10)    # [tuned] + enemies hitting me; TANK_SHARE [15 Oct afternoon]
    if per >= s.hp:
        return 0.0                              # [deviation] certain death is not a price
    miss = bodies - 1 - (UPD.claims.get(h, 0) if c is None else c)
    if miss > 0:
        walk += (STACK_WAIT_PARTNER if sm else rc["wait"]) * miss                 # [guess] partners not committed yet
    risk = 0 if s.shut else s.bag if s.hp - per < KEEP_HP * s.maxhp else s.P * s.bag   # [tuned] bag exposure (danger_p)
    if s.hp - per < KEEP_HP * s.maxhp:
        # [user decision 15 Oct afternoon] the clear leaves me below KEEP_HP: a recall (5) + the walk back out follow it
        walk += 5 + min(fget(w.nav.F_home, o.anchor) if w.nav.F_home is not None else 20, 20)
    detour = 0
    if o.near < len(w.apos):
        detour = max(0, o.anchor.chebyshev_distance(w.apos[o.near]) - s.walt)
    return value / div / (walk + clear + 5 + detour) - risk


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
    sm = stack_mode(w, s.r)
    if sm and UPD.seed is not None:
        return max(1 + c, sub_size(w))          # [user plan 15 Oct, pair/trio opener] seed: my subgroup takes it
    T = max(1, len(w.roster))
    floor = s.hp * SURVIVE                      # survival, as FARM's own zero rule (KEEP_HP stays a risk term)
    for k in range(1 + c, T + 1):
        Se = s_eff(w, s, h, k)                  # [user decision 15 Oct] splash (50_prices s_eff)
        key = (h, k, Se) if o.hp is None else None
        cd = CLEAR_MEMO.get(key) if key else None
        if cd is None:
            cd = clear_dmg(mons, Se, k)
            if key:
                CLEAR_MEMO[key] = cd
        if my_dmg(cd[1], k, cd[0]) + s.edps * min(cd[0] + 5, 10) <= floor:   # [15 Oct afternoon] TANK_SHARE; [K3] mitigation
            return min(k, max(1 + c, sub_size(w))) if sm else k   # group mode: capped at my subgroup's size
    return None


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


FK = {}                     # champion id -> (reset, ability damage F, shield F, Focus, round read); Focus re-read every 20 rounds


def fkit(c, r):
    """FKIT row of champion c with its live Focus (any other type: its attack reset as before, no ability term)."""
    k = int(c)
    v = FK.get(k)
    if v is None or r - v[4] >= 20:
        try:
            kit = FKIT.get(int(c.champion_name()))
        except Exception:
            kit = None
        if kit is None:
            kit = (1 if rmul(c) > 1 else 0, 0.0, 0.0)
        try:
            f = c.focus()
        except Exception:
            f = 100.0
        v = FK[k] = (kit[0], kit[1], kit[2], f, r)
    return v


def duel(s):
    """08 M5: P(I lose) by the square law on damage per turn. Bodies within LANCH_R of me, weight lw(d) (as before):
    H = health + shield F x Focus / 2 (the shield covers 5 of 8 turns, half of it soaked: guess), D = Strength x
    (1 + reset / 8) + ability damage F x Focus / 8 (FKIT). M3: the nearest enemy's free shots on approach, (d - 1) x
    the ranged side's D off the melee side's H. x = H_them D_them / (H_us D_us); P(lose) = x^E / (1 + x^E)."""
    r = s.r
    rs, fd, sh, f, _r = fkit(WORLD.me, r)
    hu, du = s.hp + sh * f / 2, s.S * (1 + rs / 8) + fd * f / 8
    mr = ME.get("range", 1)
    for c, p, hp, st in s.allies:
        d = p.chebyshev_distance(s.pos)
        if d <= LANCH_R:
            rs, fd, sh, f, _r = fkit(c, r)
            k = lw(d)
            hu += k * (hp + sh * f / 2)
            du += k * (st * (1 + rs / 8) + fd * f / 8)
    ht = dt = 0.0
    e0 = None
    for e in s.enemies:
        dd = e[4]
        if dd <= LANCH_R:
            rs, fd, sh, f, _r = fkit(e[0], r)
            k = lw(dd)
            ht += k * (e[2] + sh * f / 2)
            de = e[5] * (1 + rs / 8) + fd * f / 8
            dt += k * de
            if e0 is None or dd < e0[0]:
                e0 = (dd, arng(e[0]), de)
    if dt <= 0:
        return 0.0
    if e0 is not None and e0[0] >= 2:
        if mr <= 1 < e0[1]:
            hu = max(0.1 * hu, hu - (e0[0] - 1) * e0[2])      # I walk into its range: it shoots, I cannot
        elif e0[1] <= 1 < mr:
            ht = max(0.1 * ht, ht - (e0[0] - 1) * s.S)          # it walks into mine
    x = ht * dt / max(1.0, hu * du)
    x = x ** DUEL_EXP
    return x / (1 + x)


def engaged(s, h):
    """A live monster of group h is within its attack range (X1) of me (the camp is hitting me / I am attacking it)."""
    return any(hp > 0 and p.chebyshev_distance(s.pos) <= crng(c) for c, hp, p, _st in s.live.get(h, ()))


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


def price_all(w, s, cl, by):
    """[(price, option, target)] for every option this turn (multipliers: champion row x posture column)."""
    prof, r = ME["prof"], s.r
    pm = posture(w, s)
    sm = stack_mode(w, r)
    out = []
    # FARM over the ~6 nearest groups by F_me (+ the current target, + cleared groups seen)
    cand = list(w.nav.near6)
    fight = s.near_e <= 8
    if fight:
        cand = cand[:FIGHT_FARM]                # 08 F1 (M6): a fight turn keeps its fuel; the rest keep last turn's price
    cur = w.cur
    if cur[0] in ("farm", "join") and cur[1] is not None:
        hh = cur[1] if cur[0] == "farm" else None
        if hh is not None and hh not in cand:
            cand.append(hh)
    for h in s.live:
        if h in w.G and h not in cand and len(cand) < (FIGHT_FARM + 1 if fight else 9):
            cand.append(h)
    s.P = danger_p(w, s)
    s.edps = sum(e[5] for e in s.enemies if e[4] <= 4)
    s.walt = fget(w.nav.F_alt, s.pos)
    s.plose = duel(s) if s.enemies else 0.0
    dead_g = s.dead_g
    sap = w.apos[s.sa] if s.stack else None
    s.sap = sap
    s.shut = bool(w.apos) and not any(w.altar_open(i) for i in range(len(w.apos)))   # X8
    s.ba, s.bwk = bank_altar(w, s, sap) if w.apos else (0, FAR)
    update_groups(w, s, cand)
    rawb = 0.0
    for h in cand:
        o = w.G[h]
        c = cl.get(h, 0)
        # [rule, 15 Oct ladder 3] one-way yield on need-1 groups: only a LOWER slot's claim zeroes it (UPD.lowcl), and
        # a higher slot's claim is never a partner for me (it yields), so c = 0 (was: its claim made k = 2 with no
        # WAIT_PARTNER, pulling the lower slot onto the higher slot's group every 2 rounds: a 30-round A,B,A,B swap
        # on a 40x40 ladder map). Engaged on h (a live monster of h within its range): never yield it.
        call = c
        if o.need <= 1:
            if not sm and h in UPD.lowcl and not (cur == ("farm", h) and engaged(s, h)):   # stack mode: no yield
                continue
            c = 0
        else:
            # [user decision 15 Oct afternoon, ladder cd737718: a pair swapped g0/g2 every 2 rounds, each counting the
            # other's claim as a partner] only LOWER slots' claims are partners: the lower slot leads, higher slots join
            c = UPD.lowcn.get(h, 0)
        k = need_k(w, s, h, c)                  # bodies the live clear model needs, me + c claimants at least
        if k is None or (call == 0 and k >= 2 and r < FARM.pair_until and not sm):   # stack mode: k is the team
            continue
        # One claimant per SOLO group: an ally broadcasts farm on a group the draft says needs 1 body -> 0 for me
        # (user's plan, 15 Oct late). Groups needing >= 2 keep the per-body split (value / bodies). History: the gate
        # on ALL groups (fix7/fix8) lost rows A and raised elkring deaths 5 -> 17-19 (elks under-bodied). Tried with
        # "and my live model could solo it": the weaker champion joined the stronger one's group and the stronger
        # one then left it (collision A, open1), so the draft's need decides alone.
        # [rule, 15 Oct ladder phase 1] tie-break by roster slot: only an ally with a LOWER slot zeroes it (the lower
        # slot keeps it); a higher slot sees mine and yields, so simultaneous choices settle in one turn.
        if h == dead_g or (s.plose > FARM_PLOSE and s.near_e <= 5):
            continue                            # an ally died farming it recently, or outnumbered here
        wk = w.nav.walk_to(f"g{h}", s.pos)
        if wk is None or wk >= FAR:
            wk = w.nav.gd.get(h, FAR)
        if wk >= FAR:
            continue
        fp = farm_price(w, s, h, k, wk, c)
        if fp > rawb:
            rawb = fp                           # death_cost: the best farm price before multipliers
        p = fp * prof["farm"] * pm["farm_their_side" if o.side == 2 else "farm"]
        if sap is not None:                     # smooth: x0.29 at the altar, x0.6 at STACK_R, x0.96 at 40 tiles
            p *= 1 - (1 - STACK_FARM) * sig((STACK_R - o.anchor.chebyshev_distance(sap)) / 3)
        if sm and h in UPD.lowsub:
            p *= STACK_FOLLOW                   # [user plan 15 Oct, pair/trio opener] follow my subgroup's lower slots
        out.append((p, "farm", h))
    # BANK
    if s.bag > 0 and w.apos:
        a, wk = s.ba, s.bwk                     # bank_altar(): nearest / our bank / away from a stack
        if wk < FAR:
            P = s.P
            # [deviation] the risk of holding the bag is ADDED to BANK (PRICES: "at bag >= 20 with an enemy
            # within 8, risk dominates and BANK wins"); subtracting it would stop every bank near an enemy.
            # BANK_NEAR_BONUS [guess]: tempo, a bag next to an altar banks now (ladder: 22 gems carried 40 rounds)
            near = 1 + BANK_NEAR_BONUS if wk <= BANK_NEAR else 1
            bp = s.bag * (1 + P) * near / (wk * race(w)["bank_ret"] + max(1, -(-s.bag // 10))) * prof["bank"] * pm["bank_risk"]
            if sm and GROUP_BANK_BAG and s.bag >= GROUP_BANK_BAG:
                bp *= GROUP_BANK_X * s.bag / GROUP_BANK_BAG     # the carry banks its lump
            bp *= sig((s.near_e - 4) / 1.5)     # smooth: x0.5 enemy at 4, x0.12 at 1, x0.88 at 7 (Bank still refuses <= 3)
            out.append((bp, "bank", a))
    # KILL: closable targets only
    reach = ME.get("range", 1) + 1 + (2 if ME.get("has_dash") else 0)
    kmul = prof["kill"] + KILL_PER_SHARD * w.shards     # scales with shards owned (read every 20 rounds, 90_main)
    # [user plan 15 Oct, ladder 3; numbers guess] appetite: hurt or loaded champions bank / heal first. kmul carries
    # it into KILL, JOIN a fight and the sighting hunt alike (checked 15 Oct, ladder 4: all three multiply by kmul)
    kmul *= min(1.0, s.hp / s.maxhp / 0.6) * max(0.5, 1 - s.bag / 200)   # bag term [ladder 5: was max(0.3, 1 - bag/100)]
    fights = []                                 # (value, rounds, multiplier, P(lose), option, target): risk added below
    kp = prof.get("kill_plose", KILL_PLOSE)     # [user plan 15 Oct, ladder 6] per-champion / phase kill gate
    kpow = KILL_PL_POWS.get(kp, KILL_PL_POW)    # smooth: kill value x (1 - pl) ** kpow, 0.5 at pl = kp
    dn = prof.get("denial", DENIAL)             # [user decision 15 Oct afternoon] per-champion denial term (Vesper 60)
    if sm and w.slot == w.main:
        kmul *= GROUP_KILL_X                    # [user decision 15 Oct afternoon] her kill must beat an unsplit farm
    pat = prof.get("patrol", prof.get("hunt", 0) > 0)   # sighting hunt / patrol switch (Vesper: from 15 shards only)
    for c, p, hp, bag, dd, st in s.enemies:
        ttk = -(-int(hp) // int(s.S))
        fin = ttk <= 2                          # finisher: dies in <= 2 of my hits
        if r < w.kh_until and not fin:
            continue
        if KILL.kfail.get(int(c), -1) > r:
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
        # walk is in rounds below and Kill gives up after the phase's `chase` rounds without closing
        hr = reach + prof.get("hunt", 0)
        if not (chan or stun or dd <= hr or (fin and dd <= reach + 2 * ttk + 2)):
            continue
        value = bag + KILL_PRICE * KILL_G * g2g(r) + dn
        rounds = max(0, dd - ME.get("range", 1)) + ttk
        pl = s.plose
        value *= (1 - pl) ** kpow               # smooth gate: x0.5 at pl = kp; risk pl x fcost unchanged below
        if fin:
            w.excl.pop(("kill", int(c)), None)  # finishers ignore the kill exclusion (P(lose) vs ~0 HP is ~0)
        # [deviation] (value - risk) / rounds: PRICES' value / rounds - risk subtracts gems from gems/round, so an
        # even fight never priced and farmers took hits without answering. Risk P(lose) x death_cost, added below.
        am = ATTACKER_BONUS if s.attacker is not None and int(s.attacker[0]) == int(c) else 1.0
        fights.append((value, max(1, rounds), kmul * pm[e_side(w, p)] * am, pl, "kill", int(c)))
    # HUNT a sighting [rule, 15 Oct ladder 3]: hunt phase only, nobody visible, fresh byte 5 -> walk to its altar.
    # value = HUNT_BAG + KILL_PRICE KILL_G g2g + DENIAL [guess bag], rounds = walk + 5; Lanchester vs s.sc enemies at my base stats.
    if (pat and not s.enemies and s.sc and s.sage <= SIGHT_FRESH and s.sa < len(w.apos)
            and r >= w.kh_until):
        a = s.sa
        wk = w.nav.walk_to(f"a{a}", s.pos)
        if wk is None or wk >= FAR:
            wk = s.pos.chebyshev_distance(w.apos[a])
        if near_espawn(w, w.apos[a]):
            wk = FAR                            # [user decision 15 Oct] kill exclusions: no hunt onto their spawn
        us = s.hp * s.S + sum(x[2] * x[3] * lw(x[1].chebyshev_distance(s.pos)) for x in s.allies
                                 if x[1].chebyshev_distance(s.pos) <= LANCH_R)
        th = s.sc * ME.get("hp", s.maxhp) * ME.get("strength", s.S)
        pl = th / max(1.0, us + th)
        if pl <= kp and wk < FAR:               # risk P(lose) x death_cost [user plan 15 Oct, ladder 4]
            fights.append((HUNT_BAG + KILL_PRICE * KILL_G * g2g(r) + dn, wk + 5, kmul, pl, "hunt", a))
    if s.sc >= 3 and s.sage < SIGHT_LIVE:
        w.big3 = max(w.big3, r - s.sage)
    if pat and not s.enemies and r >= w.kh_until and not (s.sc and s.sage <= SIGHT_FRESH):
        # [user plan 15 Oct, ladder 4] patrol: no fresh sighting -> the nearest enemy-side altar (aside 2) I have not
        # reached in HUNT_REVISIT rounds; none reachable -> the enemy-side group with the most gems (target 100 + h)
        al = [(w.nav.walk_to(f"a{i}", s.pos) or s.pos.chebyshev_distance(w.apos[i]), i) for i in range(len(w.apos))
              if w.aside[i] == 2 and w.nav.ad[i] < FAR
              and r - HUNT.hvis.get(i, -999) >= HUNT_REVISIT]
        gs = [(o.gems, h) for h, o in w.G.items() if o.side == 2 and w.nav.gd.get(h, FAR) < FAR] if not al else []
        tgt = min(al) if al else (None, 100 + max(gs)[1]) if gs else None
        if tgt is not None and near_espawn(w, w.apos[tgt[1]] if tgt[1] < 100 else w.G[tgt[1] - 100].anchor):
            tgt = None                          # [user decision 15 Oct] kill exclusions: no patrol onto their spawn
        if tgt is not None:
            wk = tgt[0] if al else w.nav.gd[tgt[1] - 100]
            us = s.hp * s.S + sum(x[2] * x[3] * lw(x[1].chebyshev_distance(s.pos)) for x in s.allies
                                 if x[1].chebyshev_distance(s.pos) <= LANCH_R)
            th = 2 * ME.get("hp", s.maxhp) * ME.get("strength", s.S)         # assumed 2 enemies at my base stats
            pl = th / max(1.0, us + th)
            # roam only with a strength lead [user plan 15 Oct; guess]: x clamp(S / 100 - 1, 0, 2); x 0.5 while a
            # sighting of >= 3 enemies is <= ROAM_STACK rounds old (a hunting team: don't wander)
            w.roam = min(2.0, max(0.0, s.S / 100 - 1)) * (0.5 if r - w.big3 <= ROAM_STACK else 1.0)
            if pl <= kp and w.roam > 0:
                fights.append((HUNT_BAG + KILL_PRICE * KILL_G * g2g(r) + dn, wk + 10, kmul * w.roam, pl, "hunt", tgt[1]))
    # HOLD: contested altar, stun or lock gold, a fresh sighting there
    if s.sc and s.sage < SIGHT_LIVE:
        a = s.sa
        # spec: stun OR lock gold; we never buy or place locks, so only a stun counts [deviation]
        if a < len(w.apos) and w.aside[a] == 1 and ME.get("has_cc") and                 r >= w.kh_until and s.plose <= HOLD_PLOSE:
            wk = w.nav.walk_to(f"a{a}", s.pos)
            if wk is None or wk >= FAR:
                wk = max(0, w.nav.ad[a] - 1)
            out.append((30 * THEIR_RATE / (wk + 30) * prof["hold"] * pm["hold"], "hold", a))
    # JOIN a fight [rule, 15 Oct ladder 2: nobody converged]: an ally within JOIN_FIGHT_R broadcasting kill (code 3) ->
    # KILL's price with the ally and me in the Lanchester bodies, x POSTURE["defend"]["join"] whatever my posture.
    # Target not in my vision: its spot = the ally's, bag 0, ttk JOIN_TTK. Join walks to the ally; KILL takes over.
    for c, p, hp, st in s.allies:
        k = w.ally_slot(c)
        op, tg = by.get(k, (0, 0))
        if op != 3 or not 2 < p.chebyshev_distance(s.pos) <= JOIN_FIGHT_R or r < w.kh_until:    # <= 2: there, KILL
            continue
        e = next((x for x in s.enemies if int(x[0]) & 31 == tg), None)
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
            fights.append(((pl0 - pl) * (eb + KILL_PRICE * KILL_G * g2g(r) + dn),
                           max(1, max(0, s.pos.chebyshev_distance(ep) - ME.get("range", 1)) + ttk),
                           kmul * POSTURE["defend"]["join"], pl, "join", k))
    # [user plan 15 Oct, ladder 4] one currency for a death: death_cost = min(DCOST_CAP, 60 rounds x max(MY_RATE, my
    # best raw price this turn among FARM, KILL, JOIN a fight and HUNT)) + my bag. Raw = value / rounds, no multipliers
    # and no risk term (not circular). With the multipliers (Vesper kill ~7.6) it reached 4,600 and stopped all fights.
    if fight:
        rawb = max(rawb, w.rawb)                # 08 F1: the death cost keeps the last full turn's best farm
    else:
        w.rawb = rawb
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
    if s.attacker is not None and s.plose > HEAL_PLOSE and not s.trapped:
        pdie = max(pdie, s.plose)               # 08 F3 (M1): hit by a fight I lose: leave at the first hit, at any HP (P9)
    hc = dcost
    if not ne8:
        # [user plan 15 Oct, ladder 6] no enemy within 8: HEAL 0 at hp >= HEAL_NOENEMY_HP, below that the death cost
        # is capped at HEAL_NOENEMY_CAP (ladder: 64 % HP and nobody in sight chose heal 15 over farm 10)
        if s.hp >= HEAL_NOENEMY_HP * s.maxhp:
            pdie = 0
        hc = min(HEAL_NOENEMY_CAP, dcost)
    if pdie > 0 and flee_ok(s):
        wb = fget(w.nav.F_home, s.pos) if w.nav.F_home is not None else s.pos.chebyshev_distance(w.sp0)
        # posture heal (economy 0.7) on regime many only [user plan 15 Oct, ladder 6]
        hm = pm["heal"] if w.d and w.d.get("regime") == 2 else 1.0
        out.append((pdie * hc / (ME.get("recall", 5) + min(wb, HEAL_WB)) * prof.get("heal", 1.0) * hm, "heal", 0))
    # SHOP, 06 section 4.5: a trip only once my gold finishes the next emblem (ME["need"], buy_all; only the whole emblem
    # grants its passive [rules]), x SHOP_MUST_X from SHOP_MUST. On spawn the reflex buys any shard (no trip).
    item = ME.get("target") or prof["item"]      # current build target (set by buy_all), else the first entry
    try:
        cost = item.cost()
    except Exception:
        cost = 30
    if s.gold >= max(cost, min(ME.get("need", 5 * cost), SHOP_MUST)):
        n = s.gold // cost
        rounds = 1 if s.spawn else ME.get("recall", 5) + 1
        if SHOP_RETURN and not s.spawn:
            rounds += fget(w.nav.home_field(), s.pos) if w.nav.F_home is not None else 20
        gx = SHOP_MUST_X if s.gold >= SHOP_MUST else 1.0
        out.append((g2g(r) * n * cost / rounds * prof["shop"] * pm["shop"] * gx, "shop", 0))
    # JOIN: an ally farming a group that needs >= 2
    for k, (op, tg) in by.items():
        if op != 1 or tg not in w.idx:
            continue
        h = w.idx[tg]
        o = w.G[h]
        if o.need < 2:
            continue
        wk = w.nav.gd.get(h, FAR)
        if wk >= FAR:
            continue
        if min(t.chebyshev_distance(s.pos) for t in o.tiles) <= 4:
            continue                            # there: FARM(g) prices itself
        b = cl.get(h, 1)
        bx = STACK_BODY_EXP if sm else BODY_EXP     # [user plan 15 Oct, stack opener] same exponent as farm_price
        lo = farm_price(w, s, h, b, wk) * (b if bx == 1.0 else b ** bx) if b >= o.need else 0.0
        gain = farm_price(w, s, h, b + 1, wk) * ((b + 1) if bx == 1.0 else (b + 1) ** bx) - max(0.0, lo)
        if gain > 0:
            out.append((gain / max(1, wk) * prof["join"] * pm["join"], "join", k))
    return out


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
    return str(tg)
