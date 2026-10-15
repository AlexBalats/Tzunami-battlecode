"""mapdump: picks a champion on every draft turn, then on the FIRST draft turn prints one line
    MAPDUMP {json}
with the static map (walls/bushes/holes, spawns, altars, camp groups, team size) for tools/mapmodel.py.
Play turns do nothing. No `import json` (costs ~35 rounds [measured A29]): the JSON is built by hand.
camp_groups() works during the draft since cambc 2.1.4 [measured A19]: called once. Camp.max_health() and
strength() raise "Initialize the game" during the draft; Camp.base_stats() works [measured 14 Oct].
Run: cambc run mapdump starter-python --map NAME --rounds 2, then
     python -I tools/mapmodel.py --extract <bundle or dir> runs/mapmodel/NAME.json
(tools/plog.py shows the line too, but cuts non-trace lines at 300 chars.)
"""
import cambc
from cambc import game_map

Team = cambc.Team
# ChampionDraft values [sdk] (as bots/core/parts/90_main.py): RYTH 0, VENDETTA 2, VARG 9, MARCELLA 6, STELLAR 4
PICKS = (0, 2, 9, 6, 4)
BACKUP = PICKS + tuple(d for d in range(11) if d not in PICKS)


def xy(p):
    return f"[{p.x},{p.y}]"


def pts(bb):
    return "[" + ",".join(xy(p) for p in bb.positions()) + "]"


def dump(f0):
    W, H = game_map.width(), game_map.height()
    grid = [["."] * W for _ in range(H)]
    # '#' wall, 'h' hole (blocks movement, not sight [rules]), 'b' bush (walkable, blocks sight [rules]);
    # altars and camps are listed separately (both block movement).
    for ch, fn in (("b", "bushes"), ("h", "holes"), ("#", "walls")):
        try:
            bb = getattr(game_map, fn)()
        except Exception as e:
            print(f"P|0|?|draft|err|{fn}:{type(e).__name__}:{e}", flush=True)
            continue
        for p in bb.positions():
            grid[p.y][p.x] = ch
    rows = ",".join('"' + "".join(r) + '"' for r in grid)
    f_geo = cambc.fuel_remaining()
    groups = []
    for g in game_map.camp_groups():           # the only call (~0.74M)
        cs = []
        for c in g.camps():
            p = c.spawn_position()
            b = c.base_stats()     # max_health()/strength() raise during the draft; base_stats() works [measured]
            cs.append(f'{{"x":{p.x},"y":{p.y},"kind":{int(c.kind())},"max_hp":{float(b.base_health)},'
                      f'"strength":{float(b.base_strength)},"range":{int(b.base_attack_range)}}}')
        groups.append(f'{{"handle":{int(g)},"gems":{int(g.gem_value())},"gold":{int(g.gold_value())},'
                      f'"respawn":{int(g.max_respawn_timer())},"camps":[{",".join(cs)}]}}')
    f_cg = cambc.fuel_remaining()
    try:
        sym = int(game_map.symmetry())
    except Exception:
        sym = -1
    try:
        ts = int(cambc.draft.team_size())
    except Exception:
        ts = -1
    body = (f'{{"width":{W},"height":{H},"team_size":{ts},"symmetry":{sym},'
            f'"our_spawn":{pts(game_map.spawn_region(Team.ALLY))},'
            f'"enemy_spawn":{pts(game_map.spawn_region(Team.ENEMY))},'
            f'"altars":{pts(game_map.altars())},'
            f'"groups":[{",".join(groups)}],"rows":[{rows}]}}')
    f1 = cambc.fuel_remaining()
    print(f"MAPDUMP {body}", flush=True)
    print(f"P|0|?|draft|fuel|start={f0} geometry={f0 - f_geo} "
          f"camp_groups={f_geo - f_cg} rest={f_cg - f1} total={f0 - f1}", flush=True)


if cambc.is_draft():
    done = False
    while True:
        try:
            ours = [int(p) for p in cambc.draft.current_draft(Team.ALLY)]
            cambc.draft.pick(next((d for d in BACKUP if d not in ours), PICKS[0]))   # FIRST
        except Exception as e:
            print(f"P|0|?|draft|err|pick:{type(e).__name__}:{e}", flush=True)
        if not done:
            done = True
            f0 = cambc.fuel_remaining()
            try:
                dump(f0)
            except Exception as e:
                print(f"P|0|?|draft|err|dump:{type(e).__name__}:{e}", flush=True)
        cambc.end_turn()
else:
    while True:
        cambc.end_turn()
