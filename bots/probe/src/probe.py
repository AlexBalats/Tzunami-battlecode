"""Gameplay phase of the probe: first-turn dumps, then the experiment named in plan.py."""
import cambc
from cambc import game_map, vision

import experiments
import plan
from log import log, rec, team_letter

Team = cambc.Team
STATE = {"turn": 0}


def blocked_static():
    return game_map.walls() | game_map.holes() | game_map.altars() | game_map.spawn_region(Team.ENEMY)


def safe(f):
    try:
        return rec(f())
    except Exception as e:
        return "ERR " + str(e)


def static_dump():
    """A4, A10, A11: engine constants, every champion and camp design, items and consumables."""
    from cambc import constants, _cache
    f = cambc.fuel_remaining()
    log("constants", **{n: rec(getattr(constants, n)) for n in constants._SETTINGS})
    for kind, design in enumerate(_cache.champion_designs):
        stats, passive, a0, a1 = design
        log("champ_design", kind=kind, stats=rec(stats), passive=rec(passive), slot0=rec(a0), slot0_type=type(a0).__name__,
            slot1=rec(a1), slot1_type=type(a1).__name__)
    for kind in range(5):
        log("camp_design", kind=kind, stats=safe(lambda: cambc._bc.camp_design(kind)))
    for i in range(cambc.ItemType.COUNT):
        it = cambc.ItemType(i)
        log("item", id=i, name=it.name, info=safe(it.info))
    for i in range(cambc.ConsumableType.COUNT):
        c = cambc.ConsumableType(i)
        log("consumable", id=i, name=c.name, info=safe(c.info))
    log("fuel_static_dump", fuel=f - cambc.fuel_remaining())


def map_dump():
    """A5, A13, A17: map summary and distance fields from both spawns."""
    walls = blocked_static()
    groups = game_map.camp_groups()
    log("map", w=game_map.width(), h=game_map.height(), sym=int(game_map.symmetry()),
        altars=rec(game_map.altars().positions()), spawn=rec(game_map.spawn_region(Team.ALLY).positions()),
        enemy_spawn=rec(game_map.spawn_region(Team.ENEMY).positions()),
        n_groups=len(groups), walls=game_map.walls().count(), holes=game_map.holes().count(),
        bushes=game_map.bushes().count(), n_allies=len(cambc.champions(Team.ALLY)))
    fields = {}
    for name, team in (("ally", Team.ALLY), ("enemy", Team.ENEMY)):
        roots = game_map.spawn_region(team)
        field = cambc.DistanceField()
        f = cambc.fuel_remaining()
        # Enemy spawn is blocked for us, but distances from it still tell us how contested a tile is.
        field.compute(game_map.walls() | game_map.holes() | game_map.altars(), roots, cambc.Bitboard(), 65535)
        log("fuel_full_distance_field", fuel=f - cambc.fuel_remaining(), roots=name)
        fields[name] = field
    STATE["groups"] = groups
    STATE["fields"] = fields
    STATE["walls"] = walls


def near_dist(field, tiles, walls):
    """Walking distance from a spawn to the nearest free tile next to (or on) any of tiles."""
    near = cambc.Bitboard()
    for p in tiles:
        near.draw_chebyshev(p, 1)
    near &= ~walls
    return min((d for d in (field.get(p) for p in near.positions()) if 0 <= d < 65535), default=-1)


def group_dump(lo, hi):
    groups, fields, walls = STATE["groups"], STATE["fields"], STATE["walls"]
    for i in range(lo, min(hi, len(groups))):
        g = groups[i]
        spawns = g.spawn_tiles().positions()
        log("group", i=i, kinds=[int(c.kind()) for c in g.camps()], gold=g.gold_value(), gems=g.gem_value(),
            respawn=g.max_respawn_timer(), spawns=[[p.x, p.y] for p in spawns],
            d_ally=near_dist(fields["ally"], spawns, walls), d_enemy=near_dist(fields["enemy"], spawns, walls))


def altar_dump():
    fields, walls = STATE["fields"], STATE["walls"]
    for a in game_map.altars().positions():
        log("altar", pos=[a.x, a.y], d_ally=near_dist(fields["ally"], [a], walls),
            d_enemy=near_dist(fields["enemy"], [a], walls))


def deadmem(me):
    """Can a dead champion write shared memory, and do living teammates see it the same round?

    Dead: write (round & 255) to byte 0 and log the result. Alive: log byte 0 whenever it changes.
    """
    rnd = cambc.round_number()
    if not me.is_alive():
        try:
            cambc.shared_memory.write(0, bytes([rnd & 255]))
            res = "ok"
        except Exception as e:
            res = "ERR " + type(e).__name__ + ": " + str(e)
        try:
            back = cambc.shared_memory[0]
        except Exception as e:
            back = "ERR " + str(e)
        log("deadmem", role="dead", wrote=rnd & 255, write=res, readback=back, can_move=me.can_move())
        return True
    try:
        v = cambc.shared_memory[0]
    except Exception as e:
        v = "ERR " + str(e)
    if v != STATE.get("mem0"):
        STATE["mem0"] = v
        log("deadmem", role="alive", byte0=v, expected_if_same_round=rnd & 255)
    return False


def play_turn():
    STATE["turn"] += 1
    t = STATE["turn"]
    me = cambc.me()
    if deadmem(me):
        return
    if t <= 6:
        log("fuel_turn_start", turn=t, fuel=cambc.fuel_remaining())
    if t == 1:
        log("me", pos=rec(me.position()), hp=me.health(), max_hp=me.max_health(), strength=me.strength(),
            focus=me.focus(), range=me.attack_range(), gold=me.gold_count(), gems=me.gem_count(),
            stats=rec(me.base_stats()), draft_mem=list(bytes(cambc.DraftMemoryBuffer()))[:4],
            n_allies_visible=len(cambc.champions(Team.ALLY)))
        return
    # One body per team (the first ally in the list) dumps the map, spread over turns.
    if cambc.round_number() >= 1995:
        log("late_round", turn=t)
    mapper = plan.EXPERIMENT in ("dump", "static") and int(me.champion_name()) == min(int(a.champion_name()) for a in cambc.champions(Team.ALLY))
    if mapper and plan.EXPERIMENT == "static":
        if t == 2:
            static_dump()
        return
    if mapper and t == 2:
        map_dump(); return
    if mapper and t == 3:
        altar_dump(); return
    if mapper and 4 <= t < 4 + 15:
        group_dump((t - 4) * 5, (t - 3) * 5); return
    getattr(experiments, plan.EXPERIMENT)(STATE)
