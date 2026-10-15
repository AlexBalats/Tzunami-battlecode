"""Danger and fight maths, from what this champion sees (docs/STRATEGY.md -> Fight value)."""
import cambc

import config as C

FAR = 65535


def ability_burst(u, target=None):
    """Best ready damage ability of a champion, after mitigation if we can name the target."""
    best = 0.0
    try:
        for a in u.abilities():
            if a.is_damage() and a.is_ready():
                best = max(best, a.damage_amount(target) if target is not None else a.damage_amount())
    except cambc.Error:
        pass
    return best


def enemy_dpr(e, me):
    """Damage per round one enemy can put on us: a basic attack plus a ready ability, spread over its cycle."""
    return e.strength + ability_burst(e.u, me) / 2.0


def camp_dpr(w):
    """Damage per round from awake monsters in range of us (range 3 [rules])."""
    total = 0.0
    for gr in w.groups:
        if gr.state != "alive" or not gr.awake(w.rnd):
            continue
        if gr.center.chebyshev_distance(w.pos) > 6:
            continue
        for i, p in enumerate(gr.spawns):
            if p.chebyshev_distance(w.pos) <= 3 and (gr.hp[i] is None or gr.hp[i] > 0):
                total += gr.str_each[i] if gr.kind_known else 20.0
    return total


def incoming(w, me):
    """Expected damage per round on us. Ranged enemies must choose move or attack [rules],
    so only enemies already within range + 1 count."""
    d = camp_dpr(w)
    for e in w.enemies:
        if e.pos.chebyshev_distance(w.pos) <= e.range + 1:
            d += enemy_dpr(e, me)
    return max(d, w.dmg_taken)


def ttd(w, me):
    """Rounds until death at the current damage rate."""
    d = incoming(w, me)
    return FAR if d <= 0 else w.hp / d


def our_dpr(me):
    return me.strength() + ability_burst(me) / 4.0


def fight(w, me, e):
    """Fight value of attacking enemy e, in gems (STRATEGY formula, gain uses race arithmetic L3).
    Returns (value, p_win, rounds)."""
    r = w.income()
    ally_help = 0.0
    try:
        for a in cambc.vision.champions(cambc.Team.ALLY):
            if a.position().chebyshev_distance(e.pos) <= 3 and a.position() != w.pos:
                ally_help += 0.5 * a.strength()      # they may not commit: half weight
    except cambc.Error:
        pass
    ttk_us = e.hp / max(1.0, our_dpr(me) + ally_help)
    their = camp_dpr(w)
    for o in w.enemies:
        if o.pos.chebyshev_distance(e.pos) <= 4:
            their += enemy_dpr(o, me)
    ttk_them = w.hp / max(1.0, their)
    if ttk_us * C.TTK_RATIO <= ttk_them:
        p = C.P_WIN_GOOD
    elif ttk_them * C.TTK_RATIO <= ttk_us:
        p = C.P_WIN_BAD
    else:
        p = C.P_WIN_EVEN
    # L3: their bag counts twice (they lose it, we bank most of it); 60 rounds of their income [rules].
    gain = e.gems * (1 + C.P_BANK_OURS) + 60 * r + 50 * C.GOLD_TO_GEM
    loss = w.gems * 2 + 60 * r
    walk = max(0, e.pos.chebyshev_distance(w.pos) - me.attack_range())
    rounds = walk + ttk_us
    value = p * gain - (1 - p) * loss - rounds * r
    return value, p, rounds
