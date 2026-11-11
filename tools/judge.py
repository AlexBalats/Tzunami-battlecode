#!/usr/bin/env python3
"""Judge a bot against opponents on every map, both sides, with the ladder KPIs.

  python3 -I tools/judge.py tz --opp v93 starter-cpp [--maps all|train|held] [--jobs 2] [--keep]

Each (map, side) is one deterministic game. Maps are split once by a hash of the name: a quarter is held out from
every tuning run ("held"); the rest is "train". Outputs go to a scratch dir and are deleted unless --keep.
Reports: wins / losses, win rate with a 95 % interval, median margin, and per-game KPIs (gold earned at r300 against
the opponent's, champion deaths, bag swing = enemy gems taken - own gems lost to champions), train v held, worst maps.
"""
import argparse, collections, glob, hashlib, json, math, os, shutil, subprocess, sys, tempfile

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CAMBC = os.path.join(REPO, ".venv", "bin", "cambc")


def held_out(name):
    return int(hashlib.md5(name.encode()).hexdigest(), 16) % 4 == 0


def maps(which):
    names = sorted(os.path.basename(p)[:-7] for p in glob.glob(os.path.join(REPO, "maps", "*.map26a")))
    if which == "train":
        return [m for m in names if not held_out(m)]
    if which == "held":
        return [m for m in names if held_out(m)]
    return names


def expand(runs, n):
    out = []
    for x in runs:
        out += [float(x["value"])] * x["duration"]
    return (out + [out[-1] if out else 0.0] * n)[:n]


def kpis(s, side):
    """KPIs for the team on `side` ('teamA'/'teamB') of one summary."""
    other = "teamB" if side == "teamA" else "teamA"
    n = s["match"]["roundsCompleted"] + 2
    team = {c["id"]: c["team"] for c in s["champions"]}
    gold300 = {"teamA": 0.0, "teamB": 0.0}
    mon300 = {"teamA": 0.0, "teamB": 0.0}
    gold150 = {"teamA": 0.0, "teamB": 0.0}
    for t in s["championTimelines"]:
        if t["metric"] in ("earnedGold", "monsterDamageDone"):
            v = expand(t["runs"], max(n, 302))
            (gold300 if t["metric"] == "earnedGold" else mon300)[team[t["owner"]["id"]]] += v[300]
            if t["metric"] == "earnedGold":
                gold150[team[t["owner"]["id"]]] += v[150]
    deaths = collections.Counter()
    bag = collections.Counter()
    for e in s["events"]:
        for x in e["entries"]:
            if e["kind"] == "death" and x["context"] == "champion":
                deaths[e["owner"]["team"]] += 1
            if e["kind"] == "death" and x["context"] == "camp":
                deaths[e["owner"]["team"] + "_camp"] += 1
            if e["kind"] == "gemCollection" and x["context"] == "champion":
                bag[e["owner"]["team"] + "_took"] += int(x["value"])
            if e["kind"] == "gemLoss" and x["context"] == "champion":
                bag[e["owner"]["team"] + "_lost"] += int(x["value"])
            if e["kind"] == "fuelExhausted":
                deaths[e["owner"]["team"] + "_fuel"] += 1
    trib750 = 0.0
    for tl in s.get("teamTimelines", []):
        if tl["metric"] == "submittedGems" and tl["owner"] == side:
            trib750 = expand(tl["runs"], 751)[750]
    return dict(trib750=trib750, gold150=gold150[side], gold300=gold300[side], ogold300=gold300[other], mon300=mon300[side] / 1000, deaths=deaths[side], camp_deaths=deaths[side + "_camp"],
                odeaths=deaths[other], fuel=deaths[side + "_fuel"], swing=bag[side + "_took"] - bag[side + "_lost"])


def run(bot, opps, which, jobs, keep, only=None):
    out = tempfile.mkdtemp(prefix="judge_", dir=os.environ.get("JUDGE_TMP"))
    rows, man = [], []
    keep_maps = {l.split()[0] for l in open(only) if l.strip()} if only else None
    for opp in opps:
        for m in maps(which):
            if keep_maps is not None and m not in keep_maps:
                continue
            for side in ("a", "b"):
                tag = f"{opp}_{m}_{side}"
                a, b = (bot, opp) if side == "a" else (opp, bot)
                man.append(f"{REPO}/bots/{a} {REPO}/bots/{b} {REPO}/maps/{m}.map26a {out}/{tag}.repl26a --statistics {out}/{tag}.json --json")
                rows.append((opp, m, side, f"{out}/{tag}.json"))
    with open(f"{out}/manifest.txt", "w") as f:
        f.write("\n".join(man) + "\n")
    subprocess.run([CAMBC, "build", bot], cwd=REPO, check=True, capture_output=True)
    for o in set(opps):
        subprocess.run([CAMBC, "build", o], cwd=REPO, check=True, capture_output=True)
    r = subprocess.run([CAMBC, "run-batch", f"{out}/manifest.txt", "--jobs", str(jobs), "--release"], cwd=REPO,
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-2000:])
    games = []
    for opp, m, side, path in rows:
        if not os.path.exists(path):
            games.append(dict(opp=opp, map=m, side=side, result="missing", held=held_out(m)))
            continue
        s = json.load(open(path))
        me = "teamA" if side == "a" else "teamB"
        gems = {t["team"]: int(t["submittedGems"]) for t in s["teams"]}
        oc = s["match"]["outcome"]
        res = "win" if oc == me else ("draw" if oc not in ("teamA", "teamB") else "loss")
        g = dict(opp=opp, map=m, side=side, result=res, gems=gems[me], ogems=gems["teamB" if me == "teamA" else "teamA"],
                 rounds=s["match"]["roundsCompleted"], held=held_out(m), faults=s["diagnostics"]["botFaults"][me])
        g.update(kpis(s, me))
        games.append(g)
    with open(f"{out}/games.json", "w") as f:
        json.dump(games, f)
    report(bot, games)
    if keep:
        print(f"kept: {out}")
    else:
        shutil.rmtree(out, ignore_errors=True)
    return games


def ci(k, n):
    if not n:
        return (0, 0)
    z, p = 1.96, k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - h), 100 * (c + h)


def report(bot, games):
    def line(label, gs):
        gs = [g for g in gs if g["result"] != "missing"]
        if not gs:
            return
        w = sum(g["result"] == "win" for g in gs)
        lo, hi = ci(w, len(gs))
        med = sorted(g["gems"] - g["ogems"] for g in gs)[len(gs) // 2]
        mean = lambda k: sum(g[k] for g in gs) / len(gs)
        print(f"{label:<22} n={len(gs):<4} win {100*w/len(gs):5.1f}% ({lo:.0f}-{hi:.0f})  margin med {med:+5d}  "
              f"gold150 {mean('gold150'):4.0f}  gold300 {mean('gold300'):5.0f} v {mean('ogold300'):5.0f}  mon300 {mean('mon300'):4.1f}k  deaths {mean('deaths'):4.1f} v {mean('odeaths'):4.1f}  "
              f"camp-deaths {mean('camp_deaths'):3.1f}  fuelEx {mean('fuel'):4.1f}  swing {mean('swing'):+5.0f}  trib750 {mean('trib750'):4.0f}  end r{mean('rounds'):4.0f}")
    print(f"== {bot}")
    for opp in sorted({g["opp"] for g in games}):
        og = [g for g in games if g["opp"] == opp]
        line(f"v {opp}", og)
        line(f"  train", [g for g in og if not g["held"]])
        line(f"  held", [g for g in og if g["held"]])
    line("all", games)
    miss = sum(g["result"] == "missing" for g in games)
    faults = sum(g.get("faults", 0) for g in games)
    if miss or faults:
        print(f"missing games {miss}, bot faults {faults}")
    bym = collections.defaultdict(lambda: [0, 0])
    for g in games:
        if g["result"] != "missing":
            bym[g["map"]][0] += g["result"] == "win"
            bym[g["map"]][1] += 1
    worst = sorted(bym.items(), key=lambda x: x[1][0] / x[1][1])[:10]
    print("worst maps: " + ", ".join(f"{m} {w}/{n}" for m, (w, n) in worst))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("bot")
    ap.add_argument("--opp", nargs="+", required=True)
    ap.add_argument("--maps", default="all", choices=["all", "train", "held"])
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--only", default=None, help="a file of map names (first word per line): judge only those")
    a = ap.parse_args()
    run(a.bot, a.opp, a.maps, a.jobs, a.keep, a.only)
