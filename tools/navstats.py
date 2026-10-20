"""Nav numbers of both bots in an arena run (docs/redo/05_PATHFINDING.md, results).

    python3 -I tools/navstats.py runs/arena/<A>-vs-<B>-<time>

For each game folder <map>-<A|B> (in -B the first bot played team B): unzips the bundle, decodes the replay
(node tools/replay/decode.mjs; map grids by tools/replay/farm/mapjson.mjs), then per bot:
  direct     rounds per walk tile on direct trips between takes (tools/replay/farm/legs.py's rule: consecutive hits
             on different groups, no death / bank / recall / spawn visit in between); median over all trips
  moving     the same trips, rounds with a move only (still rounds out: waits are macro, not Nav): detours, blocks, dashes
  excess     tiles walked on those trips / their BFS distance (05 section 6: the detour, dashes count 2-3 tiles); median, p90
  spread     arrival spread of multi-body takes: a team's hits on one group, split at gaps > TAKE_GAP rounds; the
             spread is the last body's first hit minus the first body's first hit; median
  stuck osc stall   Behaviors failed per game (exec traces: strat-sw's guards `failed stuck`, `failed stall` and its
             `osc|x,y<->` trace; redo: `failed stuck|osc` from a Nav failure, `failed stall`)
  stay       `stay` traces (30 still turns) per game
  idle%      idle turns / (move + idle turns) from the tick lines (not moved, attacked, captured, waited, channelled)
  turns/50r  turns finished per 50 rounds (tick lines): below 50 = turns lost to fuel overruns (Nav's cost)
  calm_d     deaths with no enemy seen on the last turn alive (`death|... enemies=0`) per game
  by camp / by champ   deaths per game by killer (replay Death events: an empty killer list = a monster)
  faults     bot faults (stats.json)
Decoded files are kept in runs/navstats/<run>/ (re-runs skip the decode).
"""
import json, os, re, statistics as st, subprocess, sys, zipfile
from collections import defaultdict, deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tools", "replay"))
from arena import load_stats  # noqa: E402
import report  # noqa: E402

TAKE_GAP = 30


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def bfs(grid, w, h, srcs):
    dist = [[-1] * w for _ in range(h)]
    q = deque(srcs)
    for x, y in srcs:
        dist[y][x] = 0
    while q:
        x, y = q.popleft()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and dist[ny][nx] < 0 and grid[ny][nx] not in "#o":
                    dist[ny][nx] = dist[y][x] + 1
                    q.append((nx, ny))
    return dist


def replay_nums(d, grid, W, H):
    """Per team: direct-trip rounds/tile list, multi-body arrival spreads."""
    team = report.team_of(d["champs"])
    R = d["rounds"]
    spawn = defaultdict(list)
    for ch in R[1]["champs"]:
        spawn[team[ch[0]]].append((ch[1], ch[2]))
    comps = report.full_groups(d["scamps"])
    cpos = {c[0]: (c[2], c[3]) for c in d["scamps"]}
    camp_g = {c: g for g, cs in enumerate(comps) for c in cs}
    hit = defaultdict(list)
    for e in d["events"]:
        if e[1] in ("Attack", "Cast ability") and e[3] == "M" and isinstance(e[2], int) and e[4] in camp_g:
            hit[e[2]].append((e[0], camp_g[e[4]]))
    recall = defaultdict(set)
    for e in d["events"]:
        if e[1] == "Recall":
            recall[e[2]].add(e[0])
    pos = defaultdict(dict)
    for row in R:
        for ch in row["champs"]:
            pos[ch[0]][row["r"]] = (ch[1], ch[2], ch[3], ch[4], ch[6])
    eff, mov, exc, spread, gd = ([], []), ([], []), ([], []), ([], []), {}
    killed = ([0, 0], [0, 0])                   # team -> [by a monster, by a champion]
    for e in d["events"]:
        if e[1] == "Death":
            killed[team[e[2]]][1 if e[6] else 0] += 1
    for i, hs in hit.items():
        t = team[i]
        hs.sort()
        for (r0, g0), (r1, g1) in zip(hs, hs[1:]):
            if g0 == g1 or r1 - r0 < 3:
                continue
            seg = [pos[i].get(r) for r in range(r0, r1 + 1)]
            if any(s is None for s in seg) or any(not s[3] for s in seg):
                continue
            if seg[-1][4] < seg[0][4] or any(r in recall[i] for r in range(r0, r1 + 1)):
                continue
            if any(min(cheb(s[:2], p) for p in spawn[t]) <= 2 for s in seg[1:]):
                continue
            if g0 not in gd:
                gd[g0] = bfs(grid, W, H, [cpos[c] for c in comps[g0]])
            dist = min(gd[g0][cpos[c][1]][cpos[c][0]] for c in comps[g1])
            if dist > 0:
                eff[t].append((r1 - r0) / dist)
                still = sum(1 for a, b in zip(seg, seg[1:]) if a[:2] == b[:2])
                mov[t].append((r1 - r0 - still) / dist)
                exc[t].append(sum(cheb(a[:2], b[:2]) for a, b in zip(seg, seg[1:])) / dist)
    by = defaultdict(list)                      # (team, group) -> [(round, body)]
    for i, hs in hit.items():
        for r, g in hs:
            by[(team[i], g)].append((r, i))
    for (t, g), hs in by.items():
        hs.sort()
        takes, cur = [], [hs[0]]
        for a, b in zip(hs, hs[1:]):
            if b[0] - a[0] > TAKE_GAP:
                takes.append(cur)
                cur = []
            cur.append(b)
        takes.append(cur)
        for tk in takes:
            first = {}
            for r, i in tk:
                first.setdefault(i, r)
            if len(first) >= 2:
                spread[t].append(max(first.values()) - min(first.values()))
    return eff, mov, exc, spread, killed


TICK_ACT = re.compile(r"\|tick\|.* act=(\d+)/(\d+)/(\d+)/(\d+)/(\d+)/(\d+)/(\d+)")
NAV = re.compile(r"\|tick\|.* nav=([\d/]+)")


def log_nums(text):
    c = defaultdict(int)
    c["stuck"] = len(re.findall(r"\|exec\|.* failed stuck", text))     # strat-sw's guard; redo: act on a Nav failure
    c["osc"] = len(re.findall(r"\|osc\|\d", text)) + len(re.findall(r"\|exec\|.* failed osc", text))
    c["stall"] = len(re.findall(r"\|exec\|.* failed stall", text))
    c["stay"] = text.count("|stay|")
    c["calm_d"] = len(re.findall(r"\|death\|.*enemies=0", text))
    for m in TICK_ACT.finditer(text):
        c["mv"] += int(m.group(1))
        c["idle"] += int(m.group(6))
        c["turns"] += sum(int(x) for x in m.groups())
        c["ticks"] += 1
    nav = [0] * 8
    for m in NAV.finditer(text):
        for k, v in enumerate(m.group(1).split("/")[:8]):
            nav[k] += int(v)
    c["nav"] = nav
    return c


def decoded(run, work):
    """Yield (game folder name, first bot's team, decoded replay, unzip dir, game dir, map grid) per arena game in run;
    decodes into work/<game>/dec.json once (re-runs reuse it)."""
    os.makedirs(os.path.join(work, "maps"), exist_ok=True)
    for g in sorted(os.listdir(run)):
        gdir = os.path.join(run, g)
        if not os.path.isdir(gdir) or g[-2:] not in ("-A", "-B"):
            continue
        bundles = [f for f in os.listdir(gdir) if f.endswith(".repl26a")]
        if not bundles:
            continue
        first = 0 if g.endswith("-A") else 1     # the first bot's team in this game
        out = os.path.join(work, g)
        dec = os.path.join(out, "dec.json")
        if not os.path.exists(dec):
            os.makedirs(out, exist_ok=True)
            with zipfile.ZipFile(os.path.join(gdir, bundles[0])) as z:
                z.extractall(out)
            subprocess.run(["node", os.path.join(ROOT, "tools/replay/decode.mjs"), os.path.join(out, "replay.repl26a"),
                            dec], cwd=ROOT, check=True, capture_output=True)
        d = json.load(open(dec))
        mname = d["meta"]["map"]
        mj = os.path.join(work, "maps", mname + ".json")
        if not os.path.exists(mj):
            subprocess.run(["node", os.path.join(ROOT, "tools/replay/farm/mapjson.mjs"), ROOT,
                            os.path.join(work, "maps"), os.path.join(ROOT, "maps", mname + ".map26a")],
                           cwd=ROOT, check=True, capture_output=True)
        yield g, first, d, out, gdir, json.load(open(mj))


def main():
    run = os.path.abspath(sys.argv[1])
    work = os.path.join(ROOT, "runs", "navstats", os.path.basename(run))
    m = re.match(r"(.+)-vs-(.+)-\d{8}-\d{6}$", os.path.basename(run))
    names = (m.group(1), m.group(2)) if m else ("first", "second")
    acc = [defaultdict(list), defaultdict(list)]   # bot index (0: first bot) -> metric -> values
    games = [0, 0]
    wins = [0, 0]
    for g, first, d, out, gdir, mp in decoded(run, work):
        mname = d["meta"]["map"]
        eff, mov, exc, spread, killed = replay_nums(d, mp["rows"], mp["w"], mp["h"])
        sts = load_stats(os.path.join(gdir, "stats.json"))
        gems = {t["team"]: t["submittedGems"] for t in sts["teams"]}
        for team in (0, 1):
            b = 0 if team == first else 1
            a = acc[b]
            a["direct"] += eff[team]
            a["moving"] += mov[team]
            a["excess"] += exc[team]
            a["spread"] += spread[team]
            a["by_camp"].append(killed[team][0])
            a["by_champ"].append(killed[team][1])
            a["faults"].append(sts["botFaults"][team])
            raw = open(os.path.join(out, "team-%s.stdout" % "ab"[team]), "rb").read().decode("utf-8", "replace")
            c = log_nums(raw)
            for k in ("stuck", "osc", "stall", "stay", "calm_d", "mv", "idle", "turns", "ticks"):
                a[k].append(c[k])
            a["nav"].append(c["nav"])
            games[b] += 1
            if gems[team] > gems[1 - team]:
                wins[b] += 1
            a["map_faults"].append((mname, g[-1], sts["botFaults"][team]))
    print("run", os.path.basename(run), "| games per bot", games)
    hdr = ("bot", "direct r/tile", "moving r/tile", "trips", "excess med", "excess p90", "spread med", "spread mean", "stuck/g", "osc/g", "stall/g", "stay/g",
           "idle%", "turns/50r", "calm deaths/g", "by camp/g", "by champ/g", "faults", "wins")
    print(" | ".join(hdr))
    for b in (0, 1):
        a, n = acc[b], max(1, games[b])
        med = lambda v: round(st.median(v), 2) if v else "-"
        p90 = lambda v: round(sorted(v)[9 * len(v) // 10], 2) if v else "-"
        idle = sum(a["idle"]) / max(1, sum(a["mv"]) + sum(a["idle"]))
        print(" | ".join(map(str, (
            names[b], med(a["direct"]), med(a["moving"]), len(a["direct"]), med(a["excess"]), p90(a["excess"]), med(a["spread"]),
            round(st.mean(a["spread"]), 1) if a["spread"] else "-",
            round(sum(a["stuck"]) / n, 2), round(sum(a["osc"]) / n, 2), round(sum(a["stall"]) / n, 2),
            round(sum(a["stay"]) / n, 2), "%.1f%%" % (100 * idle),
            round(sum(a["turns"]) / max(1, sum(a["ticks"])), 1), round(sum(a["calm_d"]) / n, 2),
            round(sum(a["by_camp"]) / n, 2), round(sum(a["by_champ"]) / n, 2),
            sum(a["faults"]), "%d/%d" % (wins[b], games[b])))))
        nav = [sum(x[k] for x in a["nav"]) for k in range(8)]
        if any(nav):
            print("   nav counters (steps fast window pass>1 unit-on-step bush dash failed):", nav,
                  "| unit-on-step per 100 steps %.1f" % (100 * nav[4] / max(1, nav[0])))
        bad = [(m, s, f) for m, s, f in a["map_faults"] if f]
        if bad:
            print("   faults on:", bad)


if __name__ == "__main__":
    main()
