"""Tweak-and-compare harness: play BOT against each opponent on every map, both sides, in parallel.

Usage (from the repo root):
    python -I tools/bench.py BOT [--vs OPP1,OPP2,...] [--maps m1,m2,...] [--jobs N]
                                 [--label NAME] [--baseline RUN_DIR_OR_LABEL] [--fresh]

Defaults: --vs starter-python,tzu; every maps/**/*.map26a; --jobs = CPU count - 1.
BOT/OPP are folders in bots/ (or NAME@REV, as in tools/arena.py). An opponent that doesn't
exist or doesn't build is reported and skipped.

Games are deterministic [measured], so each is cached in runs/bench/cache/<key>.json, key =
cambc version + both bots' source hashes + map file hash + side; cached games aren't replayed.
Output: runs/bench/<label or time>/<opp>/<map>-<A|B>/ (replay bundle, stats.json, cli.log),
plus results.csv (one row per game) and summary.md in the run folder.

From the stats JSON: winner, end round, gems both teams, kills, deaths, gold earned, crashes
(botFaults). From our stdout trace (P|round|team|champ|tag|text, if present): errs (`err` lines
+ raw Traceback lines), `death` and `stuck` lines, median/max `fuel=` on `tick` lines.
"""
import argparse, concurrent.futures, csv, datetime, glob, hashlib, json, os, statistics
import re, subprocess, sys, time, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arena import ROOT, BOTS, MAPS, find_cambc, resolve_bot, source_hash, file_hash  # noqa: E402

OUT = os.path.join(ROOT, "runs", "bench")
CACHE = os.path.join(OUT, "cache")
CACHE_VERSION = 1
FIELDS = ["opp", "map", "side", "res", "round", "gems", "opp_gems", "margin", "gpr", "opp_gpr",
          "kills", "deaths", "gold", "crashes", "opp_crashes", "errs", "death_lines", "stuck_lines",
          "fuel_med", "fuel_max", "secs", "cached", "bundle"]
FUEL = re.compile(r"\bfuel=(\d+)")


def trace(bundle, team_letter):
    """Counts from our team's stdout in the replay bundle; empty values if there is none."""
    out = {"errs": 0, "death_lines": 0, "stuck_lines": 0, "fuel_med": "", "fuel_max": ""}
    try:
        with zipfile.ZipFile(bundle) as z:
            text = z.read("team-%s.stdout" % team_letter.lower()).decode("utf-8", "replace")
    except (OSError, KeyError, zipfile.BadZipFile):
        return out
    fuels = []
    for line in text.replace("\x00", "\n").splitlines():
        if not line.startswith("P|"):
            out["errs"] += "Traceback" in line
            continue
        parts = line.split("|", 5)
        tag = parts[4] if len(parts) > 4 else ""
        if tag == "err":
            out["errs"] += 1
        elif tag == "death":
            out["death_lines"] += 1
        elif tag == "stuck":
            out["stuck_lines"] += 1
        elif tag == "tick":
            m = FUEL.search(line)
            if m:
                fuels.append(int(m.group(1)))
    if fuels:
        out["fuel_med"], out["fuel_max"] = int(statistics.median(fuels)), max(fuels)
    return out


def play(cambc, job):
    """Run one game and return its row (or {'error': ...}); cache it if it finished."""
    t0 = time.time()
    os.makedirs(job["dir"], exist_ok=True)
    stats_path = os.path.join(job["dir"], "stats.json")
    cmd = [cambc, "run", "bots/" + job["blue"], "bots/" + job["red"], "--map", job["map_path"], "-o", job["dir"],
           "--statistics", stats_path]
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=job["timeout"])
        log = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired as e:
        log = "TIMEOUT after %ss\n%s" % (job["timeout"], e.stdout or "")
    with open(os.path.join(job["dir"], "cli.log"), "w", encoding="utf-8") as f:
        f.write(log)
    if not os.path.exists(stats_path):
        return {"error": log.strip().splitlines()[-1] if log.strip() else "no output"}
    with open(stats_path) as f:
        s = json.load(f)
    bundles = glob.glob(os.path.join(job["dir"], "*.repl26a"))
    bundle = max(bundles, key=os.path.getmtime) if bundles else ""
    us, them = job["side"], 1 - job["side"]
    teams = {t["team"]: t for t in s["teams"]}
    mine = [c for c in s["champions"] if c["team"] == us]
    winner = {"teamA": 0, "teamB": 1}.get(s["outcome"])
    rnd = max(s["round"], 1)
    gems, opp_gems = teams[us]["submittedGems"], teams[them]["submittedGems"]
    row = {"res": "D" if winner is None else "WL"[winner != us], "round": s["round"],
           "gems": gems, "opp_gems": opp_gems, "margin": gems - opp_gems,
           "gpr": round(gems / rnd, 3), "opp_gpr": round(opp_gems / rnd, 3),
           "kills": sum(c["kills"] for c in mine), "deaths": sum(c["deaths"] for c in mine),
           "gold": sum(c["earnedGold"] for c in mine),
           "crashes": s["botFaults"][us], "opp_crashes": s["botFaults"][them],
           "secs": round(time.time() - t0, 1),
           "bundle": os.path.relpath(bundle, ROOT) if bundle else ""}
    row.update(trace(bundle, "AB"[us]) if bundle else {})
    with open(job["cache"], "w") as f:
        json.dump(row, f)
    return row


def load_rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def num(v):
    return float(v) if v not in ("", None) else 0.0


def summary(bot, rows, skipped):
    lines = ["# Bench: %s" % bot, ""]
    for opp, why in skipped:
        lines.append("- SKIPPED %s: %s" % (opp, why))
    if skipped:
        lines.append("")
    lines += ["| opponent | wins/games | maps won both sides | gems/round us | gems/round them "
              "| deaths | errs | crashes | worst map (mean margin) |", "|" + "---|" * 9]
    for opp in dict.fromkeys(r["opp"] for r in rows):
        rs = [r for r in rows if r["opp"] == opp and "error" not in r]
        errored = sum(1 for r in rows if r["opp"] == opp and "error" in r)
        if not rs:
            lines.append("| %s | no finished games (%d errored) |||||||" % (opp, errored))
            continue
        per_map = {}
        for r in rs:
            per_map.setdefault(r["map"], []).append(r)
        margin = {m: sum(num(r["margin"]) for r in v) / len(v) for m, v in per_map.items()}
        swept = sum(1 for v in per_map.values() if len(v) == 2 and all(r["res"] == "W" for r in v))
        worst = min(margin, key=margin.get)
        mean = lambda k: sum(num(r[k]) for r in rs) / len(rs)
        lines.append("| %s | %d/%d%s | %d/%d | %.2f | %.2f | %d | %d | %d | %s (%+.0f) |" % (
            opp, sum(r["res"] == "W" for r in rs), len(rs), " (%d errored)" % errored if errored else "",
            swept, len(per_map), mean("gpr"), mean("opp_gpr"), sum(num(r["deaths"]) for r in rs),
            sum(num(r["errs"]) for r in rs), sum(num(r["crashes"]) for r in rs), worst, margin[worst]))
    return lines


def diff(rows, base, label):
    key = lambda r: (r["opp"], r["map"], r["side"])
    before = {key(r): r for r in base if r.get("res") not in ("", None)}
    lines = ["", "## Diff vs %s" % label, "", "| opponent | map | side | gems before -> after "
             "| margin before -> after | change |", "|---|---|---|---|---|---|"]
    better = worse = same = 0
    worst = None
    for r in rows:
        b = before.get(key(r))
        if not b or "error" in r:
            continue
        d = int(num(r["margin"]) - num(b["margin"]))
        better, worse, same = better + (d > 0), worse + (d < 0), same + (d == 0)
        if d < 0 and (worst is None or d < worst[0]):
            worst = (d, "%s %s vs %s" % (r["map"], r["side"], r["opp"]))
        lines.append("| %s | %s | %s | %d -> %d | %+d -> %+d | %+d |" % (
            r["opp"], r["map"], r["side"], num(b["gems"]), num(r["gems"]), num(b["margin"]),
            num(r["margin"]), d))
    n = better + worse + same
    lines += ["", "Verdict: better on %d/%d, worse on %d, same on %d; worst regression: %s" % (
        better, n, worse, same, "%s %+d" % (worst[1], worst[0]) if worst else "none")]
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bot")
    ap.add_argument("--vs", default="starter-python,tzu")
    ap.add_argument("--maps", help="comma-separated map names (default: all in maps/)")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--label", help="run folder name under runs/bench/ (default: timestamp)")
    ap.add_argument("--baseline", help="previous run folder or label to diff against")
    ap.add_argument("--timeout", type=int, default=900, help="wall-clock seconds per game")
    ap.add_argument("--fresh", action="store_true", help="ignore the cache")
    args = ap.parse_args()

    cambc = find_cambc()
    version = subprocess.run([cambc, "--version"], capture_output=True, text=True).stdout.split()[-1]
    bot = resolve_bot(args.bot)
    all_maps = {os.path.splitext(os.path.relpath(p, MAPS))[0].replace(os.sep, "/"): p
                for p in sorted(glob.glob(os.path.join(MAPS, "**", "*.map26a"), recursive=True))}
    names = args.maps.split(",") if args.maps else list(all_maps)
    if [n for n in names if n not in all_maps]:
        sys.exit("unknown maps: %s (have: %s)" % (", ".join(n for n in names if n not in all_maps),
                                                    ", ".join(all_maps)))

    def build(name):
        b = subprocess.run([cambc, "build", "bots/" + name], cwd=ROOT, capture_output=True, text=True)
        return None if b.returncode == 0 else (b.stdout + b.stderr).strip().splitlines()[-1:] or ["build failed"]

    err = build(bot)
    if err:
        sys.exit("build failed for %s: %s" % (bot, err[0]))
    opps, skipped = [], []
    for spec in args.vs.split(","):
        if not os.path.isdir(os.path.join(BOTS, spec.split("@")[0], "src")):
            skipped.append((spec, "no bots/%s/src" % spec.split("@")[0]))
            continue
        try:
            opp = resolve_bot(spec)
        except SystemExit as e:
            skipped.append((spec, str(e)))
            continue
        err = build(opp)
        if err:
            skipped.append((spec, "build failed: %s" % err[0]))
        else:
            opps.append(opp)
    for spec, why in skipped:
        print("SKIPPING %s: %s" % (spec, why))

    label = args.label or datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = os.path.join(OUT, label)
    os.makedirs(CACHE, exist_ok=True)
    hb = source_hash(bot)
    jobs = []
    for opp in opps:
        ho = source_hash(opp)
        for name in names:
            for side in (0, 1):
                blue, red = (bot, opp) if side == 0 else (opp, bot)
                hblue, hred = (hb, ho) if side == 0 else (ho, hb)
                key = hashlib.sha256(("v%d|%s|%s|%s|%s|%d" % (
                    CACHE_VERSION, version, hblue, hred, file_hash(all_maps[name]), side)).encode()).hexdigest()[:24]
                jobs.append({"opp": opp, "map": name, "side": side, "blue": blue, "red": red,
                             "map_path": all_maps[name], "cache": os.path.join(CACHE, key + ".json"),
                             "dir": os.path.join(run_dir, opp, "%s-%s" % (name.replace("/", "_"), "AB"[side])),
                             "timeout": args.timeout})
    todo = [j for j in jobs if args.fresh or not os.path.exists(j["cache"])]
    print("cambc %s | %s (%s) vs %s | %d maps x 2 sides | %d to play, %d cached, %d at once"
          % (version, bot, hb, ",".join(opps) or "nobody", len(names), len(todo), len(jobs) - len(todo), args.jobs),
          flush=True)

    t0 = time.time()
    results = {}
    for j in jobs:
        if j not in todo:
            with open(j["cache"]) as f:
                results[id(j)] = dict(json.load(f), cached=1)
    with concurrent.futures.ThreadPoolExecutor(max(1, args.jobs)) as pool:
        futs = {pool.submit(play, cambc, j): j for j in todo}
        for n, fut in enumerate(concurrent.futures.as_completed(futs), 1):
            j = futs[fut]
            r = results[id(j)] = dict(fut.result(), cached=0)
            print("  [%d/%d] %s %s %s: %s" % (n, len(todo), j["opp"], j["map"], "AB"[j["side"]],
                  r.get("error") or "%s %+d (%.0fs)" % (r["res"], r["margin"], r["secs"])), flush=True)
    wall = time.time() - t0

    rows = [dict(results[id(j)], opp=j["opp"], map=j["map"], side="AB"[j["side"]]) for j in jobs]
    os.makedirs(run_dir, exist_ok=True)
    with open(os.path.join(run_dir, "results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS + ["error"], extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    played = [r for r in rows if not r.get("cached") and "secs" in r]
    lines = summary(bot, rows, skipped)
    lines += ["", "cambc %s, %s hash %s; %d games, %d played, %d cached; wall %.0fs with %d jobs%s" % (
        version, bot, hb, len(rows), len(played), len(rows) - len(played), wall, args.jobs,
        ", %.0fs per game" % (sum(r["secs"] for r in played) / len(played)) if played else "")]
    if args.baseline:
        base = args.baseline if os.path.isdir(args.baseline) else os.path.join(OUT, args.baseline)
        path = os.path.join(base, "results.csv")
        if os.path.exists(path):
            lines += diff(rows, load_rows(path), args.baseline)
        else:
            lines += ["", "baseline not found: %s" % path]
    text = "\n".join(lines) + "\n"
    with open(os.path.join(run_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print("\n" + text + "saved %s" % os.path.relpath(run_dir, ROOT))


if __name__ == "__main__":
    main()
