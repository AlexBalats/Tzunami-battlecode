"""Draft: read the map, choose the strategy and the opening, write it to draft memory, then pick.

Never name this module `draft`: a module of that name kills the draft instance (A27).

Draft memory layout (C.MEMO_VERSION = 1):
  0 version   1 number of groups (mod 256, a check)   2 strategy id   3 n = number of bodies
  4 .. 4+n    our ChampionType ids, sorted: a body's slot is its index here
  4+n .. 4+2n opening group per slot (group index + 1, 0 = none)
"""
import cambc
from cambc import Team

import config as C
import world

# Per ChampionType [rules arithmetic, GameRules.md -> Champion roster]: camp damage per round
# (basic + reset/8 + best camp spell/8) and base HP. Only used for the opening; play reads live stats.
TYPE_DPS = (68.8, 50.6, 78.8, 47.5, 45.0, 60.0, 50.0, 63.1, 50.6, 55.6, 56.3, 66.9)
TYPE_HP = (1200, 900, 800, 700, 900, 750, 700, 1200, 700, 900, 1000, 750)

S = {"plan": None}


def types_of(pick):
    """ChampionDraft -> ChampionType ids: Cassi & Issac (3) is two bodies, 3 and 4; later ids shift by one [sdk]."""
    return (pick,) if pick < 3 else (3, 4) if pick == 3 else (pick + 1,)


def pick_of(t):
    """ChampionType id -> ChampionDraft id (inverse of types_of)."""
    return t if t < 3 else 3 if t <= 4 else t - 1


def draft_turn():
    """Plan, submit, then pick. submit() after pick() raises "Memory access requires the owning
    team's input boundary" [measured, 2.1.6], so the pick comes last; the plan costs ~7.5M of the
    first turn's ~24.6M fuel [measured], and later turns reuse it."""
    ours = [int(p) for p in cambc.draft.current_draft(Team.ALLY)]
    n = cambc.draft.team_size()
    comp = [int(p) for p in C.COMPS.get(n, C.COMPS[3 if n < 3 else 5])]
    choice = next((p for p in comp + [int(p) for p in C.FALLBACK] if p not in ours), None)
    if len(ours) >= n:
        choice = None
    if S["plan"] is None:
        f0 = cambc.fuel_remaining()
        planned = ours + [p for p in comp if p not in ours]
        S["plan"] = analyse(planned[:n])
        if C.TRACE:
            print(f"T|draft|plan|fuel {f0 - cambc.fuel_remaining()}|{S['plan'][3]}", flush=True)
    strategy, opening, n_groups, _ = S["plan"]
    picks = ours + ([choice] if choice is not None else [])
    types = sorted(t for p in picks for t in types_of(p))
    body = [C.MEMO_VERSION, n_groups & 255, strategy, len(types)] + types
    body += [opening.get(t, 0) for t in types]
    try:
        cambc.draft_memory.submit(bytes(body))      # the last submit wins [measured]
    finally:
        if choice is not None:
            cambc.draft.pick(choice)


def analyse(picks):
    """(strategy id, {type: group + 1}, number of groups, features string) from the map (P1: reckon first)."""
    world.load()
    blocked = world.BLOCKED
    us = world.Field(world.SPAWN, blocked)
    them = world.Field(cambc.game_map.spawn_region(Team.ENEMY), blocked & ~cambc.game_map.spawn_region(Team.ENEMY))
    alt = world.altar_field()
    altars = [(us.near(a), them.near(a)) for a in world.ALTARS]
    groups = []
    for grp in world.GROUPS:
        du = min(us.near(p) for p in grp.cells)
        dt = min(them.near(p) for p in grp.cells)
        da = min(alt.near(p) for p in grp.cells)
        groups.append((grp, du, dt, da))
    span = min(us.near(p) for p in cambc.game_map.spawn_region(Team.ENEMY).positions())   # enemy spawn is blocked
    strategy = classify(altars, max(span, 1))

    # Opening (P9, P2): greedy over (body, group) pairs by gems per round from spawn, each body and
    # group used once, groups on our side preferred. A body skips a group it can't clear alone.
    types = [t for p in picks for t in types_of(p)]
    pairs = []
    for t in types:
        for grp, du, dt, da in groups:
            if du >= C.UNREACHED or da >= C.UNREACHED:
                continue
            rounds, dmg = world.clear_cost(grp, grp.maxhp, TYPE_DPS[t])
            if dmg > (1 - C.HP_RESERVE) * TYPE_HP[t]:
                continue
            value = (grp.gems + C.GOLD_VALUE * grp.gold) / (du + rounds + cambc.constants.CAPTURE_TIME)
            if du > dt:
                value *= 0.8
            pairs.append((value, t, grp.i))
    pairs.sort(reverse=True)
    opening, used = {}, set()
    for value, t, gi in pairs:
        if t not in opening and gi not in used:
            opening[t] = gi + 1
            used.add(gi)

    feats = (f"{world.W}x{world.H} span={span} strat={C.STRATEGY_NAMES[strategy]} altars={sorted(altars)} "
             f"groups={len(groups)} ours={sum(1 for g in groups if g[1] < g[2])} "
             f"near20={sum(1 for g in groups if g[1] <= 20)} min_du={min((g[1] for g in groups), default=0)} "
             f"kinds={sorted(set(str(k).rsplit('.', 1)[-1] for g in groups for k in g[0].kinds))} "
             f"opening={opening}")
    return strategy, opening, len(groups), feats


def classify(altars, span):
    """FARM / CONTEST / ROAM from the altars' walking distances (ours, theirs), scaled by the
    spawn-to-spawn distance so it works on any map size (rule 8). P1, P9, P11.
    FARM: we own a near altar. CONTEST: every altar is central, so the altar is the battle.
    ROAM: anything else (mixed or no reachable altar). Walls make central altars sit at ~0.6-0.8
    SPAN, so absolute distance is not used: only who is nearer."""
    reach = [a for a in altars if a[0] < C.UNREACHED]
    if not reach:
        return C.ROAM
    for du, dt in reach:
        if du <= C.HOME_ALTAR_MAX * span and dt - du >= C.HOME_ALTAR_EDGE * span:
            return C.FARM
    if all(abs(du - dt) <= C.CONTEST_EDGE * span for du, dt in reach):
        return C.CONTEST
    return C.ROAM


def read():
    """Play side: (strategy, types, opening per type) from draft memory, or None if missing or stale."""
    m = bytes(cambc.draft_memory)
    if len(m) < 4 or m[0] != C.MEMO_VERSION or m[1] != len(world.GROUPS) & 255:
        return None
    n = m[3]
    types = list(m[4:4 + n])
    opening = {t: m[4 + n + k] - 1 for k, t in enumerate(types) if m[4 + n + k]}
    return m[2], types, opening
