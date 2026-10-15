"""The rule list (docs/design/CORE.md): every turn, walk P["order"] top to bottom; the first rule that acts wins.

play(w, s, team) -> (tag, claim_h, rally). The tag starts with the rule's name (logs compare profiles by it).
No tasks, no stored intent. The only memory between turns: my claim (rewritten every turn), groups marked
unreachable for UNREACH_FOR rounds, the capture start per group, and the round an enemy was last seen.
Every threshold lives in a profile; rules read P["..."], never a module constant. PROFILE selects one.
"""
import cambc

PROFILE = "farm"

_FARM = {
    "order": ["DEAD", "CHANNEL", "FINISH", "KILL", "RECALL", "RETREAT", "RALLY", "BANK", "CAMP", "CAPTURE",
              "PICK", "STATION"],
    "KILL_MIN_GEMS": 10,     # a carrier: worth the detour (the bag dominates a kill's value, ECONOMY.md)
    "KILL_RATIO": 1.5,       # our Lanchester power must beat theirs by this near the target (P11)
    "KILL_REACH": 5,         # champions within this of the target count towards a fight's power
    "KILL_CHASE": 5,         # only a target this close is worth leaving the farm for (opportunistic, never a hunt)
    "KILL_HP_HITS": 2,       # a target this many of my hits from death is vulnerable whatever the odds (P8)
    "ESPAWN_R": 3,           # never chase onto the enemy's doorstep (they heal and shop there)
    "CHANNEL_R": 2,          # enemies this close can break a channel by killing me
    "RECALL_HP": 0.35,       # below this fraction of max HP: go home (recall heals in full [rules])
    "RECALL_SAFE": 8,        # recall only with no enemy this close (damage cancels it [rules])
    "FLEE_R": 6,             # enemies this close are weighed for a retreat
    "FLEE_RATIO": 1.3,       # retreat when their power beats ours by this
    "FLEE_HP": 0.6,          # ... and I am below this HP fraction (or carry CARRY_FEAR gems)
    "CARRY_FEAR": 20,        # a bag this big is not risked in a fair fight (P3)
    "RALLY_AGE": 6,          # a rally older than this is stale
    "RALLY_D": 12,           # join a rally within this (Chebyshev; no field to an arbitrary tile)
    "RALLY_D_CONTEST": 20,   # contested bank: one point in the middle, rally from further (CORE.md Modes)
    "RALLY_HP": 0.5,         # join a rally only above this HP fraction
    "BANK_AT": 40,           # bank a bag this big
    "BANK_AT_THREAT": 20,    # ... or this big when an enemy was seen within THREAT_MEMORY rounds
    "THREAT_MEMORY": 10,     # rounds an enemy sighting counts as a threat
    "END_BANK": 30,          # within this of the last round, bank any bag (unbanked gems score nothing)
    "LAST_ROUND": 2000,      # the game's last round [rules]
    "CONTEST_X": 1.3,        # contested bank test (20_world computes w.contested with its own copy)
    "CALM": 30,              # contested bank: bank alone only after this many rounds without an enemy
    "BANK_BUDDY": 4,         # contested bank: an ally this close makes banking safe
    "KEEP_HP": 0.4,          # each champion's share of a clear stops at this HP fraction: just above RECALL_HP,
                             # where rule RECALL pulls it out anyway (never die to a camp: gems destroyed)
    "BANK_FORCE_X": 2,       # contested bank: a bag this many times BANK_AT banks even without a buddy
    "MID_SLACK": 4,          # a group is on our half if d(spawn) <= d(espawn) + this
    "UNREACH_FOR": 40,       # rounds a group with a blocked approach is skipped
    "PAIR_WAIT": 25,         # rounds to wait for partners at a group I cannot clear alone before chipping it
    "PAIR_WAIT_ALONE": 8,    # ... when nobody has claimed it yet: long enough for an ally's next pick to see mine
    "CHIP_ROUNDS": 8,        # chip a group alone only if its full damage takes this many rounds to bring me to
                             # KEEP_HP: damaged camps never regenerate [measured A28], so a chip is progress,
                             # but against a big hitter (monolith) a trip is too short to be worth the walk
    "JOIN_W": 2.0,           # pick weight of a group that allies claimed but cannot clear without me (P10)
    "TEAM_R": 2,             # an ally within CAMP_R + this of a live monster counts as present for a clear
    "CAPTURE_GIVEUP": 8,     # rounds on a spawn tile with no reward before the capture counts as contested
    "GOLD_W": 0.2,           # gold's weight against gems in a pick's reward (gems win games)
    "PICK_CHECKS": 6,        # gstate() costs ~27k out of vision: check only this many best candidates
    "SHOP_GOLD": 30,         # one shard's price [rules]: shop on spawn at or above it
}
_AGGRO = dict(_FARM, KILL_MIN_GEMS=0, KILL_RATIO=1.1, KILL_REACH=8, KILL_CHASE=8, RALLY_D=20, CARRY_FEAR=40,
              order=["DEAD", "KILL", "CHANNEL", "FINISH", "RECALL", "RETREAT", "RALLY", "BANK", "CAMP",
                     "CAPTURE", "PICK", "STATION"])
PROFILES = {"farm": _FARM, "aggro": _AGGRO}
assert all(set(p) == set(_FARM) for p in PROFILES.values()), "profiles must share one key set"
P = PROFILES[PROFILE]

REWARD = {0: (22, 90), 1: (36, 160), 2: (24, 0), 3: (0, 35), 4: (200, 300)}   # CampType -> (gems, gold) [rules]
CAMP_R = 3                                                                     # every monster's range [measured A31]

_M = {"claim": None, "guess": None, "blk": None, "unreach": {}, "cap": {}, "seen": -9999, "went": -1, "rally": None,
      "pairwait": {}, "nokill": {}, "stuck": (None, 0), "norally": -1, "chase": (None, 0, 0)}
STUCK_ROUNDS = 40                 # the backstop: same tile this long outside a deliberate stand -> drop everything
                                  # (a last resort: every wait has its own shorter exit; the pair wait is 25+25)
STUCK_OK = ("DEAD", "CHANNEL", "RECALL", "CAPTURE", "STATION")   # deliberate stands (each has its own exit)


def _unstick(w, s, tag):
    """The no-freeze guarantee (CORE.md rule 1): release the claim and rest it, forget the chase or rally that
    held me here, so next turn's rule walk starts from nothing."""
    h = _M["claim"]
    if h is not None:
        _M["unreach"][h] = s.rnd + P["UNREACH_FOR"]
    _M["claim"] = None
    _M["pairwait"].clear()
    _M["cap"].clear()
    if tag.startswith("KILL c"):
        try:
            _M["nokill"][int(tag.split()[1][1:])] = s.rnd + 20
        except Exception:
            pass
    if tag.startswith("RALLY"):
        _M["norally"] = s.rnd + 20
    _say("stuck", f"{tag} g={h}")


def cur_claim():
    """My claim, for the snapshot's target group (w.snapshot(rnd, target=cur_claim()))."""
    return _M["claim"]


# ------------------------------------------------------------------ helpers
def _cheb(a, b):
    return max(abs(a.x - b.x), abs(a.y - b.y))


def _say(tag, text):
    t = globals().get("trace")
    if t is not None:
        t(tag, text)


def _cid(c):
    try:
        return int(c.champion_name())
    except Exception:
        return -1


def _channelling(c):
    try:
        return c.is_submitting_gems() or c.is_recalling()
    except Exception:
        return False


def _ally_str(c):
    try:
        return float(c.strength())
    except Exception:
        return enemy_str(c)


def _ally_max(c):
    try:
        return float(c.max_health())
    except Exception:
        return 1000.0


def _per(s):
    """My HP above KEEP_HP: what I can spend on a clear."""
    return s.hp - P["KEEP_HP"] * s.max_hp


def _team_at(w, s, live):
    """Strengths and HP pool (above KEEP_HP) of me plus the allies within CAMP_R + TEAM_R of a live monster:
    who is actually here to share the clear, not who claims it (P10). Monsters hit the nearest champion, so the
    damage lands on whoever is in front; the pool model lets that one recall and the rest finish [rules]."""
    tiles = [c.spawn_position() for c, _, _ in live]
    strs, pool = [my_str()], _per(s)
    for p, hp, g, c in s.allies:
        if min(_cheb(p, t) for t in tiles) <= CAMP_R + P["TEAM_R"]:
            strs.append(_ally_str(c))
            pool += hp - P["KEEP_HP"] * _ally_max(c)
    return strs, pool


def _need(w, s, live, cap):
    """(k, rounds): the fewest champions like me (sustained Strength, my HP) whose pooled HP above KEEP_HP covers
    the clear's damage; (None, rounds with cap champions) if even cap of us cannot."""
    S, per = my_str(), _per(s)
    rounds = FAR
    for k in range(1, max(1, cap) + 1):
        rounds, dmg = clear_pred(live, [S] * k)
        if dmg <= k * per:
            return k, rounds
    return None, rounds


def _chippable(s, live):
    """Alone, with an empty bag (a camp kill destroys carried gems [rules]), and the group's full damage leaves me
    CHIP_ROUNDS of attacks before KEEP_HP: hit it, recall at RECALL_HP, come back (no regen [measured A28])."""
    hit = sum(st for _, _, st in live)
    return s.bag == 0 and (hit <= 0 or _per(s) >= P["CHIP_ROUNDS"] * hit)


def power(w, s, center, r, mine):
    """Lanchester power, sum of hp * Str within r of center (P11). mine: our side (me always counted)."""
    if mine:
        tot = s.hp * my_hit(w, s)
        for p, hp, _, c in s.allies:
            if _cheb(p, center) <= r:
                tot += hp * _ally_str(c)
        return tot
    return sum(hp * enemy_str(c) for p, hp, _, c in s.enemies if _cheb(p, center) <= r)


def _live(w, s, h):
    """[(camp, hp, Str)] of live monsters of group h. Unread camps: last-known HP, except camps within
    CAMP_R of me that read None (in vision and not visible: dead)."""
    rows, camps = group_comp(w, h), w.camps.get(h, ())
    read = s.camp_hp.get(h)
    out = []
    for j, row in enumerate(rows):
        if j >= len(camps):
            break
        x = read[j] if read is not None and j < len(read) else None
        if x is None:
            if read is not None and _cheb(camps[j].spawn_position(), s.pos) <= CAMP_R:
                continue
            x = w.hp_known(camps[j], row[1], s.rnd)
        if x > 0:
            out.append((camps[j], x, row[2]))
    return out


def _hits(w, s, p):
    """An awake monster with Strength has tile p in range."""
    for cp, h in w.near(p, CAMP_R):
        if h not in s.awake:
            continue
        for k, mx, st, x, y in group_comp(w, h):
            if x == cp.x and y == cp.y and st > 0:
                return True
    return False


def _near_enemies(s, r, skip_channel=False):
    return [e for e in s.enemies if _cheb(e[0], s.pos) <= r and not (skip_channel and _channelling(e[3]))]


def _my_slot(w, s, team):
    for o in (s, w, team):
        v = getattr(o, "slot", None)
        if v is not None:
            return v
    return None


def _ally_claims(team, me):
    """{group: [slots]} claimed by live allies other than me."""
    out = {}
    if team is None:
        return out
    alive = getattr(team, "alive", None)
    for sl, h in (getattr(team, "claims", None) or {}).items():
        if h is None or sl == me or (alive is not None and sl not in alive):
            continue
        out.setdefault(h, []).append(sl)
    return out


def _team_n(team):
    """Live champions on my team, me included (the most a group take can count on)."""
    return max(1, len(getattr(team, "alive", None) or ()))


def _goto(w, key, rnd):
    _M["went"] = rnd
    return w.nav.goto(key, rnd)


def _bank_key(w, s=None):
    """The home altar on a contested map (bank together, CORE.md Modes); else the nearest altar by field
    (Chebyshev until its field exists, queued with w.want): a trip is dead time, the closest altar ends it."""
    b = w.bank_altar
    if b is None:
        return None
    if w.contested or s is None:
        return f"a{b}"
    best = None
    for i in range(len(w.altar_pos)):
        d = w.dist(f"a{i}", s.pos)
        if d is None:
            w.want(f"a{i}")
            d = _cheb(w.altar_pos[i], s.pos)
        if d < FAR and (best is None or d < best[0]):
            best = (d, i)
    return f"a{b}" if best is None else f"a{best[1]}"


# ------------------------------------------------------------------ rules
def rule_dead(w, s):
    if s.alive:
        return None
    shop(w, s)
    _M["claim"] = None
    return "DEAD"


def rule_channel(w, s):
    if not (s.submitting or s.recalling):
        return None
    try:
        left = int(w.me.remaining_channel_time())
    except Exception:
        left = 5
    burst = sum(enemy_str(c) for p, hp, g, c in _near_enemies(s, P["CHANNEL_R"]))
    if burst > 0 and s.hp <= burst * max(1, left):
        _cancel(w, s)
        return None
    return f"CHANNEL {'sub' if s.submitting else 'rec'} {left}"


def _cancel(w, s):
    try:
        if s.submitting:
            w.me.cancel_submit_gems()
        if s.recalling:
            w.me.cancel_recall()
    except Exception:
        pass
    s.submitting = s.recalling = False


def rule_finish(w, s):
    if not s.can_attack:
        return None
    hit, rng = my_hit(w, s), hit_range(w)
    for p, hp, g, c in sorted(s.enemies, key=lambda e: -e[2]):
        if _cheb(p, s.pos) <= rng and hp <= hit and do_attack(w, s, c):
            return f"FINISH c{_cid(c)}"
    return None


def rule_kill(w, s):
    hit, reach, best = my_hit(w, s), P["KILL_REACH"], None
    carrying = s.bag >= P["CARRY_FEAR"]          # P3: my own bag is not risked on anything but a finisher
    for p, hp, g, c in s.enemies:
        if g < P["KILL_MIN_GEMS"] or _M["nokill"].get(_cid(c), -1) > s.rnd:
            continue
        d = _cheb(p, s.pos)
        if d > P["KILL_CHASE"]:
            continue
        # Vulnerable = cannot get away: channelling (tribute/recall) or stunned, or already in my face. A running
        # target is a chase we lose to the farm (user rule: opportunistic kills only, never a hunt).
        if not (_channelling(c) or d <= hit_range(w) + 1):
            continue
        if carrying and hp > P["KILL_HP_HITS"] * hit:
            continue
        de = w.dist("espawn", p)
        if de is not None and de <= P["ESPAWN_R"]:
            continue
        weak = hp <= P["KILL_HP_HITS"] * hit
        if not weak and power(w, s, p, reach, True) < P["KILL_RATIO"] * power(w, s, p, reach, False):
            continue
        if _hits(w, s, p):
            continue
        if best is None or g > best[2]:
            best = (p, hp, g, c)
    if best is None:
        return None
    if s.submitting or s.recalling:
        _cancel(w, s)                  # aggro order puts KILL above CHANNEL: break the channel to fight
    p, c = best[0], best[3]
    cid, d = _cid(c), _cheb(p, s.pos)
    pc, pd, pn = _M["chase"]
    pn = pn + 1 if pc == cid and d >= pd else 0
    _M["chase"] = (cid, d, pn)
    if pn >= 3:                        # three rounds without closing: it is getting away, back to the farm
        _M["nokill"][cid] = s.rnd + 20
        _M["chase"] = (None, 0, 0)
        return None
    _M["rally"] = p
    if _cheb(p, s.pos) <= hit_range(w) and s.can_attack and do_attack(w, s, c):
        return f"KILL c{_cid(c)} at"
    if s.can_move and w.nav.greedy(p) == "moving":
        return f"KILL c{_cid(c)} mv"
    return f"KILL c{_cid(c)} wait"


def rule_recall(w, s, force=False):
    if s.hp >= P["RECALL_HP"] * s.max_hp and not force:
        return None
    if w.spawn.is_set(s.pos):
        if s.gold >= P["SHOP_GOLD"]:
            shop(w, s)
        return "RECALL heal"           # spawn heals at turn end [rules]: stay
    if _near_enemies(s, P["RECALL_SAFE"], True):
        return None
    if _hits(w, s, s.pos):             # a camp's hit cancels the recall [rules]: step out of its range first
        tiles = [(t, 0, 0, None) for t, h in w.near(s.pos, CAMP_R) if h in s.awake] or                 [(t, 0, 0, None) for t, h in w.near(s.pos, CAMP_R)]
        return _flee_step(w, s, tiles, hit_back=False).replace("RETREAT", "RECALL out")
    try:
        w.me.recall()
    except Exception:
        return None
    _M["claim"] = None
    return "RECALL"


def rule_retreat(w, s):
    near = _near_enemies(s, P["RECALL_SAFE"], True)
    if not near:
        return None
    low = s.hp < P["RECALL_HP"] * s.max_hp
    if not low:
        close = [e for e in near if _cheb(e[0], s.pos) <= P["FLEE_R"]]
        if not close or not (s.bag >= P["CARRY_FEAR"] or s.hp < P["FLEE_HP"] * s.max_hp):
            return None
        theirs = sum(hp * enemy_str(c) for p, hp, g, c in close)
        if theirs <= P["FLEE_RATIO"] * power(w, s, s.pos, P["FLEE_R"], True):
            return None
    return _flee_step(w, s, near)


def _flee_step(w, s, near, hit_back=True):
    """One step: max (distance to the nearest enemy, -d(spawn)); never onto blocked or camp tiles, never into
    an awake camp's range from outside it. No better tile: stand, and hit back if anything is in range."""
    def score(q):
        ds = w.dist("spawn", q)
        return (min(_cheb(e[0], q) for e in near), -(FAR if ds is None else ds))
    here = score(s.pos)
    cand = []
    if s.can_move and w.blocked is not None:
        in_range = _hits(w, s, s.pos)
        for dv in DIRS:
            q = s.pos + dv
            if not (0 <= q.x < w.W and 0 <= q.y < w.H) or w.blocked.is_set(q)                     or (not in_range and _hits(w, s, q)):     # off the map: is_set raises [measured]
                continue
            sc = score(q)
            if sc > here:
                cand.append((sc, q))
    for sc, q in sorted(cand, key=lambda t: t[0], reverse=True):
        if w.nav.move(q):
            return f"RETREAT mv d={sc[0]}"
    for p, hp, g, c in sorted(near, key=lambda e: _cheb(e[0], s.pos)) if hit_back else []:
        if _cheb(p, s.pos) <= hit_range(w) and s.can_attack and do_attack(w, s, c):
            return f"RETREAT hit c{_cid(c)}"
    return "RETREAT stand"


def rule_rally(w, s, team):
    r = getattr(team, "rally", None) if team is not None else None
    if not r or r[0] is None or r[1] > P["RALLY_AGE"] or _M["norally"] > s.rnd:
        return None
    rp = r[0]
    lim = P["RALLY_D_CONTEST"] if w.contested else P["RALLY_D"]
    d = _cheb(rp, s.pos)
    if d > lim or d <= 1 or s.hp < P["RALLY_HP"] * s.max_hp or s.bag >= P["CARRY_FEAR"]:
        return None
    if not s.can_move or w.nav.greedy(rp) != "moving":
        return None
    return f"RALLY d={d}"


def rule_bank(w, s):
    key, rnd = _bank_key(w, s), s.rnd
    if key is None or s.bag <= 0:
        return None
    end = rnd >= P["LAST_ROUND"] - P["END_BANK"]
    threat = rnd - _M["seen"] <= P["THREAT_MEMORY"]
    if not (end or s.bag >= P["BANK_AT"] or s.bag >= P["BANK_AT_THREAT"] and threat):
        return None
    if w.contested and not end and s.bag < P["BANK_FORCE_X"] * P["BANK_AT"]:
        buddy = any(_cheb(p, s.pos) <= P["BANK_BUDDY"] for p, hp, g, c in s.allies)
        if not buddy and rnd - _M["seen"] < P["CALM"]:
            return None
    d = w.dist(key, s.pos)
    if d is not None and d >= FAR:
        return None                    # bank altar unreachable on foot [measured A13]: keep farming
    _M["claim"] = None
    if d == 0:
        try:
            w.me.submit_gems(w.altar_pos[int(key[1:])])
            return f"BANK {key} ch"
        except Exception:
            return f"BANK {key} lock"  # refused (an enemy lock, or a channel already on)
    res = _goto(w, key, rnd)
    return f"BANK {key} {'mv' if res == 'moving' else res}"


def rule_camp(w, s, team):
    h = _M["claim"]
    if h is None:
        return None
    live = _live(w, s, h)
    if not live:
        return None
    near = min(_cheb(c.spawn_position(), s.pos) for c, _, _ in live)
    engaged = h in s.awake and near <= CAMP_R   # already in the fight: no regen, so stay till RECALL_HP [A28]
    if not engaged:
        if _M["guess"] == h and w.dist(f"g{h}", s.pos) is not None:
            _M["claim"] = _M["guess"] = None    # picked on a straight-line guess; the real walk is known now
            return None
        strs, pool = _team_at(w, s, live)
        k = _need(w, s, live, _team_n(team))[0]
        # Engage when the pooled HP covers the clear, or when as many of us are present as the need estimate
        # says (the pool model is pessimistic; RECALL pulls each body out at RECALL_HP, the camp keeps no regen).
        if clear_pred(live, strs)[1] > pool and (k is None or len(strs) < k):
            t = _camp_wait(w, s, team, h, live)
            if t != "CHIP":
                return t
    tgt = min(live, key=lambda t: _cheb(t[0].spawn_position(), s.pos))[0]
    tp = tgt.spawn_position()
    if _cheb(tp, s.pos) <= hit_range(w):
        if h in s.awake:
            do_shield(w, s)
        if s.can_attack and do_attack(w, s, tgt):
            return f"CAMP g{h} at"
        return f"CAMP g{h} wait"
    return _camp_walk(w, s, h, tp)


def _camp_wait(w, s, team, h, live):
    """Not enough of us here. Wait outside the group's range for partners (P10; free allies weigh it JOIN_W in
    PICK), for PAIR_WAIT rounds counted from my arrival (the walk is not waiting); then chip it alone if that is
    safe, else release it. Returns a tag, "CHIP", or None (released)."""
    coming = 1 + len(_ally_claims(team, _my_slot(w, s, team)).get(h, ()))
    k = _need(w, s, live, _team_n(team))[0]
    since, first = _M["pairwait"].get(h, (s.rnd, s.rnd))
    if coming > 1 and s.rnd - since > P["PAIR_WAIT"] - 10 and s.rnd - first <= 2 * P["PAIR_WAIT"]:
        since = s.rnd - (P["PAIR_WAIT"] - 10)              # a claimant is on its way: keep waiting (capped)
        _M["pairwait"][h] = (since, first)
    limit = P["PAIR_WAIT"] if coming > 1 else P["PAIR_WAIT_ALONE"]
    if k is not None and s.rnd - since <= limit:              # partners may still pick it (JOIN_W)
        if min(_cheb(c.spawn_position(), s.pos) for c, _, _ in live) > CAMP_R + P["TEAM_R"]:
            res = _goto(w, f"g{h}", s.rnd)
            return f"CAMP g{h} pair:{res}"
        _M["pairwait"].setdefault(h, (s.rnd, s.rnd))
        if _hits(w, s, s.pos):
            return _flee_step(w, s, [(t, 0, 0, None) for t, g in w.near(s.pos, CAMP_R)], hit_back=False)                 .replace("RETREAT", f"CAMP g{h} pairwait")
        return f"CAMP g{h} pairwait {coming}/{k}"
    if _chippable(s, live):
        return "CHIP"
    _M["pairwait"].pop(h, None)
    _M["unreach"][h] = s.rnd + P["UNREACH_FOR"]
    _M["claim"] = None
    _say("claim", f"release g{h} k={k} coming={coming}")
    return None


def _camp_walk(w, s, h, tp):
    """Walk into attack range of tp. The field's goal is next to ANY camp of the group, so after a kill I can be
    "here" yet out of reach of the next monster: step towards it (sideways too, allies crowd the group). Only a
    blocked approach for GIVE_UP_ROUNDS rests the group (a wait while allies move is not a blocked approach)."""
    res = _goto(w, f"g{h}", s.rnd)
    if res == "moving":
        _M["blk"] = None
        return f"CAMP g{h} mv"
    if res == "here" and s.can_move and w.nav.greedy(tp, sideways=True) == "moving":
        _M["blk"] = None
        return f"CAMP g{h} mv:in"
    if res != "stuck":
        b = _M["blk"]
        if b is None or b[0] != h:
            _M["blk"] = b = (h, s.rnd)
        if s.rnd - b[1] < GIVE_UP_ROUNDS:
            return f"CAMP g{h} wait"
    _M["blk"] = None
    _M["unreach"][h] = s.rnd + P["UNREACH_FOR"]
    _M["claim"] = None
    _say("claim", f"unreach g{h} {res}")
    return None


def rule_capture(w, s):
    h = _M["claim"]
    if h is None:
        return None
    st = w.gstate(h)
    if st != "dead":
        if st in ("alive", "respawning"):
            _M["cap"].pop(h, None)
        return None
    tiles = [V(x, y) for k, mx, st, x, y in group_comp(w, h)]
    if any(t == s.pos for t in tiles):
        since, bag, gold = _M["cap"].setdefault(h, (s.rnd, s.bag, s.gold))
        if s.rnd - since >= P["CAPTURE_GIVEUP"] and s.bag == bag and s.gold == gold:
            _M["cap"].pop(h, None)
            _M["unreach"][h] = s.rnd + P["UNREACH_FOR"]
            _M["claim"] = None
            return None                # contested: someone else holds it; pick again
        return f"CAPTURE g{h} at {s.rnd - since}"
    _M["cap"].pop(h, None)
    if any(p == t for p, _, _, _ in s.allies for t in tiles):
        _M["claim"] = None             # an ally already holds a spawn tile: a second one only splits the reward
        return None                    # and speeds nothing [rules, Camps & capture]: go do something else
    if s.can_move:
        for t in sorted(tiles, key=lambda t: _cheb(t, s.pos)):
            if _cheb(t, s.pos) == 1 and w.nav.move(t):
                return f"CAPTURE g{h} on"
    res = _goto(w, f"g{h}", s.rnd)
    return f"CAPTURE g{h} {'mv' if res == 'moving' else res}"


def _on_our_half(w, h):
    """d(spawn) <= d(espawn) + MID_SLACK, measured at the group's anchor (Chebyshev: camp tiles are walls
    of every field, and a per-group field read at 60 groups would cost ~0.3M a pick)."""
    a = w.anchor.get(h)
    sp, ep = w.anchor.get("spawn"), w.anchor.get("espawn")
    if a is None or sp is None or ep is None:
        return True
    return _cheb(a, sp) <= _cheb(a, ep) + P["MID_SLACK"]


def _pick_cands(w, s, claims, n):
    """Groups on our half, not resting, with room for me, as (score, h, guessed walk), best first.
    score = reward per champion-round: (gems + GOLD_W * gold) / k / (walk + clear rounds + 1), with k the
    champions the clear needs (or n for a chip). A group accepts max(2, k) claimants (a pair speeds any clear;
    more only when the clear needs them); a group that allies claimed but cannot clear without me weighs JOIN_W."""
    cands = []
    for h in w.camps:
        if _M["unreach"].get(h, -1) > s.rnd or not _on_our_half(w, h):
            continue
        walk, guess = w.dist(f"g{h}", s.pos), False
        if walk is None:
            w.want(f"g{h}")
            walk, guess = _cheb(w.anchor[h], s.pos), True
        if walk >= FAR:
            continue
        live = _live(w, s, h)
        k, rounds = _need(w, s, live, n)
        if k is None:
            if not _chippable(s, live):
                continue
            k = n
        c = len(claims.get(h, ()))
        if c >= max(2, k):
            continue
        rw = sum(REWARD.get(r[0], (0, 0))[0] + P["GOLD_W"] * REWARD.get(r[0], (0, 0))[1] for r in group_comp(w, h))
        sc = rw / k / (walk + rounds + 1) * (P["JOIN_W"] if 0 < c < k else 1)
        cands.append((sc, h, guess))
    cands.sort(key=lambda t: -t[0])
    return cands


def rule_pick(w, s, team):
    claims = _ally_claims(team, _my_slot(w, s, team))
    pick = None
    for sc, h, guess in _pick_cands(w, s, claims, _team_n(team))[:P["PICK_CHECKS"]]:
        score = sc
        st = w.gstate(h)
        if st == "respawning" or st == "dead" and claims.get(h):
            continue                   # a capture needs one champion: an ally already holds it [rules]
        pick = h
        _M["guess"] = h if guess else None
        break
    if pick is None:
        return None
    if _M["claim"] != pick:
        _M["pairwait"].clear()
        d = w.dist(f"g{pick}", s.pos)
        _say("claim", f"g{pick} walk={d} score={score:.3f} guess={int(_M['guess'] is not None)}")
    _M["claim"] = pick
    if _M["went"] == s.rnd:
        return f"PICK g{pick} claim"   # the field walk was already asked for this turn (one goto per turn)
    res = _goto(w, f"g{pick}", s.rnd)
    return f"PICK g{pick} {'mv' if res == 'moving' else res}"


def rule_station(w, s):
    """Nothing to pick. Idle time is free healing and shopping: recall when hurt or holding a shard's gold
    (spawn heals in full and sells [rules]; a recall also re-runs PICK at full HP, which lowers every group's
    need); else walk to the bank altar's ring."""
    key = _bank_key(w)
    _M["claim"] = None
    if not w.spawn.is_set(s.pos) and (s.hp < s.max_hp or s.gold >= P["SHOP_GOLD"]):
        t = rule_recall(w, s, force=True)
        if t:
            return "STATION " + t
    if key is None or _M["went"] == s.rnd:
        return "STATION idle"
    res = _goto(w, key, s.rnd)
    return f"STATION {key} {'mv' if res == 'moving' else res}"


RULES = {"DEAD": rule_dead, "CHANNEL": rule_channel, "FINISH": rule_finish, "KILL": rule_kill,
         "RECALL": rule_recall, "RETREAT": rule_retreat, "RALLY": rule_rally, "BANK": rule_bank,
         "CAMP": rule_camp, "CAPTURE": rule_capture, "PICK": rule_pick, "STATION": rule_station}
_TEAM_ARG = ("RALLY", "CAMP", "PICK")


def play(w, s, team):
    """Walk P["order"]; the first rule returning a tag acted. Returns (tag, claim_h, rally)."""
    _M["rally"] = None
    if s.enemies:
        _M["seen"] = s.rnd
    if s.alive and s.gold >= P["SHOP_GOLD"] and w.spawn.is_set(s.pos):
        try:
            shop(w, s)                 # free action on spawn [rules]
        except Exception:
            pass
    tag = "IDLE"
    for name in P["order"]:
        fn = RULES[name]
        try:
            t = fn(w, s, team) if name in _TEAM_ARG else fn(w, s)
        except Exception as e:
            et = globals().get("err_text")
            _say("err", et(e) if et else f"err:{name}:{type(e).__name__}")
            continue
        if t:
            tag = t
            break
        if name == "CHANNEL" and (s.submitting or s.recalling):
            break                      # still channelling (nothing else can act until it ends)
    last, n = _M["stuck"]
    n = n + 1 if last == s.pos and not tag.startswith(STUCK_OK) and not tag.endswith(" at") else 0
    _M["stuck"] = (s.pos, n)
    if n >= STUCK_ROUNDS:
        _M["stuck"] = (s.pos, 0)
        _unstick(w, s, tag)
    rally = _M["rally"] if tag.startswith("KILL") else None
    return tag, _M["claim"], rally
