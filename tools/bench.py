"""Tweak-and-compare harness: play BOT against each opponent on every map, both sides, in parallel.

Usage (from the repo root):
    python -I tools/bench.py BOT [--vs OPP1,OPP2,...] [--maps m1,m2,...] [--jobs N]
                                 [--label NAME] [--baseline RUN_DIR_OR_LABEL] [--fresh] [--rounds N]

Defaults: --vs starter-python,tzunami444; every maps/**/*.map26a; --jobs = CPU count - 1.
BOT/OPP are folders in bots/ (or NAME@REV, as in tools/arena.py). An opponent that doesn't
exist or doesn't build is reported and skipped.

Games are deterministic [measured], so each is cached in runs/bench/cache/<key>.json, key =
cambc version + both bots' source hashes + map file hash + side + --rounds; cached games aren't
replayed (capped and full games never share an entry).
Output: runs/bench/<label or time>/<opp>/<map>-<A|B>/ (replay bundle, stats.json, cli.log),
plus results.csv (one row per game) and summary.md in the run folder.

From the stats JSON: winner, end round, gems both teams, kills, deaths, gold earned, crashes
(botFaults). From our stdout trace (P|round|team|champ|tag|text, if present): errs (`err` lines
+ raw Traceback lines), `death` and `stuck` lines, median/max `fuel=` on `tick` lines; score at
each round in SCORE_ROUNDS (`score=A-B` on `tick` lines: s<R> ours, o<R> theirs) and team shares of
turns attacking/waiting/dead over ticks up to the last SCORE_ROUNDS round (`act=` on `tick` lines).
Also written as results.json (list of row dicts).

Opening bench: --rounds N cuts every game at round N (`cambc run --rounds N`). A capped game has
no stats JSON, so it is judged on the trace: cap_round = last tick round <= N, cap_margin = ours -
theirs there; res is W/L/D by the sign of cap_margin, and gems/opp_gems/margin are the scores at
cap_round, so win counts, worst map and --baseline diffs use the capped margin.
"""
import argparse, concurrent.futures, csv, datetime, glob, hashlib, json, os, statistics
import re, subprocess, sys, time, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arena import ROOT, BOTS, MAPS, RUN_FLAGS, find_cambc, load_stats, resolve_bot, source_hash, file_hash  # noqa: E402

OUT = os.path.join(ROOT, "runs", "bench")
CACHE = os.path.join(OUT, "cache")
CACHE_VERSION = 2
SCORE_ROUNDS = [100, 200, 300]  # rounds whose score is read from the tick lines (s<R>/o<R>)
SHARES = ["atk", "wait", "dead"]  # act= index 1, 4, 6 (move/attack/capture/channel/wait/idle/dead)
SHARE_TAG = SCORE_ROUNDS[-1]  # shares sum the ticks at rounds <= this
SCORE_FIELDS = [k % r for r in SCORE_ROUNDS for k in ("s%d", "o%d")]
SHARE_FIELDS = ["%s%d" % (k, SHARE_TAG) for k in SHARES]
FIELDS = ["opp", "map", "side", "res", "round", "gems", "opp_gems", "margin", "gpr", "opp_gpr",
          "kills", "deaths", "gold", "crashes", "opp_crashes", "errs", "death_lines", "stuck_lines",
          "fuel_med", "fuel_max"] + SCORE_FIELDS + SHARE_FIELDS + ["cap_round", "cap_margin",
          "secs", "cached", "bundle"]
FUEL = re.compile(r"\bfuel=(\d+)")
SCORE = re.compile(r"\bscore=(\d+)-(\d+)")
ACT = re.compile(r"\bact=(\d+(?:/\d+){6})\b")


def trace(bundle, team_letter):
    """Counts from our team's stdout in the replay bundle; empty values if there is none."""
    out = {"errs": 0, "death_lines": 0, "stuck_lines": 0, "fuel_med": "", "fuel_max": ""}
    out.update({k: "" for k in SCORE_FIELDS + SHARE_FIELDS})
    out["scores"] = {}  # round -> (ours, theirs); popped by play()
    try:
        with zipfile.ZipFile(bundle) as z:
            text = z.read("team-%s.stdout" % team_letter.lower()).decode("utf-8", "replace")
    except (OSError, KeyError, zipfile.BadZipFile):
        return out
    fuels, acts = [], [0] * 7
    for line in text.replace("\x00", "\n").splitlines():
        line = line.strip()
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
            try:
                rnd = int(parts[1])
            except ValueError:
                continue
            m = SCORE.search(line)
            if m:  # the last tick line of the round wins
                out["scores"][rnd] = (int(m.group(1)), int(m.group(2)))
            m = ACT.search(line)
            if m and rnd <= SHARE_TAG:
                acts = [a + int(b) for a, b in zip(acts, m.group(1).split("/"))]
    if fuels:
        out["fuel_med"], out["fuel_max"] = int(statistics.median(fuels)), max(fuels)
    for r in SCORE_ROUNDS:
        if r in out["scores"]:
            out["s%d" % r], out["o%d" % r] = out["scores"][r]
    if sum(acts):
        for k, i in zip(SHARES, (1, 4, 6)):
            out["%s%d" % (k, SHARE_TAG)] = round(100 * acts[i] / sum(acts))
    return out


def play(cambc, job):
    """Run one game and return its row (or {'error': ...}); cache it if it finished."""
    t0 = time.time()
    os.makedirs(job["dir"], exist_ok=True)
    stats_path = os.path.join(job["dir"], "stats.json")
    cmd = [cambc, "run", "bots/" + job["blue"], "bots/" + job["red"], "--map", job["map_path"], "-o", job["dir"],
           "--statistics", stats_path] + RUN_FLAGS + (["--rounds", str(job["rounds"])] if job["rounds"] else [])
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=job["timeout"])
        log = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired as e:
        log = "TIMEOUT after %ss\n%s" % (job["timeout"], e.stdout or "")
    with open(os.path.join(job["dir"], "cli.log"), "w", encoding="utf-8") as f:
        f.write(log)
    if os.path.exists(stats_path) and os.path.getmtime(stats_path) < t0 - 1:
        os.remove(stats_path)  # stale, from an earlier run in this folder
    bundles = [b for b in glob.glob(os.path.join(job["dir"], "*.repl26a")) if os.path.getmtime(b) >= t0 - 1]
    bundle = max(bundles, key=os.path.getmtime) if bundles else ""
    us, them = job["side"], 1 - job["side"]
    tr = trace(bundle, "AB"[us]) if bundle else {}
    scores = tr.pop("scores", {})
    if job["rounds"]:  # opening bench: judge on the score at the last tick round <= the cap
        at = [r for r in scores if r <= job["rounds"]]
        if not at:
            return {"error": "no score= tick at or before round %d (%s)" % (
                job["rounds"], log.strip().splitlines()[-1] if log.strip() else "no output")}
        cap = max(at)
        gems, opp_gems = scores[cap]
        m = gems - opp_gems
        row = {"res": "D" if m == 0 else "WL"[m < 0], "round": cap, "gems": gems, "opp_gems": opp_gems,
               "margin": m, "gpr": round(gems / cap, 3), "opp_gpr": round(opp_gems / cap, 3),
               "cap_round": cap, "cap_margin": m, "secs": round(time.time() - t0, 1),
               "bundle": os.path.relpath(bundle, ROOT)}
        if os.path.exists(stats_path):  # the game ended before the cap: keep the per-champion counts
            s = load_stats(stats_path)
            mine = [c for c in s["champions"] if c["team"] == us]
            row.update(kills=sum(c["kills"] for c in mine), deaths=sum(c["deaths"] for c in mine),
                       gold=sum(c["earnedGold"] for c in mine), crashes=s["botFaults"][us],
                       opp_crashes=s["botFaults"][them])
        row.update(tr)
        with open(job["cache"], "w") as f:
            json.dump(row, f)
        return row
    if not os.path.exists(stats_path):
        return {"error": log.strip().splitlines()[-1] if log.strip() else "no output"}
    s = load_stats(stats_path)
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
    row.update(tr)
    with open(job["cache"], "w") as f:
        json.dump(row, f)
    return row


def load_rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def num(v):
    return float(v) if v not in ("", None) else 0.0


def score_str(rows, r):
    """'ours-theirs' at round r (mean over the rows that have it), '' if none do."""
    have = [x for x in rows if x.get("s%d" % r) not in ("", None)]
    if not have:
        return ""
    if len(have) == 1:
        return "%d-%d" % (num(have[0]["s%d" % r]), num(have[0]["o%d" % r]))
    return "%.0f-%.0f" % (sum(num(x["s%d" % r]) for x in have) / len(have),
                          sum(num(x["o%d" % r]) for x in have) / len(have))


def share_str(rows, k):
    have = [num(x[k]) for x in rows if x.get(k) not in ("", None)]
    return "%.0f%%" % (sum(have) / len(have)) if have else ""


def summary(bot, rows, skipped, rounds=None):
    lines = ["# Bench: %s%s" % (bot, " (opening bench: games cut at round %d, judged on the score at "
                                "the last tick <= %d)" % (rounds, rounds) if rounds else ""), ""]
    for opp, why in skipped:
        lines.append("- SKIPPED %s: %s" % (opp, why))
    if skipped:
        lines.append("")
    extra = ["r%d" % r for r in SCORE_ROUNDS] + ["%s r<=%d" % (k, SHARE_TAG) for k in SHARES]
    lines += ["| opponent | %s | maps won both sides | gems/round us | gems/round them "
              "| deaths | errs | crashes | worst map (mean margin) | %s |" % (
                  "ahead at cap/games" if rounds else "wins/games", " | ".join(extra)),
              "|" + "---|" * (9 + len(extra))]
    for opp in dict.fromkeys(r["opp"] for r in rows):
        rs = [r for r in rows if r["opp"] == opp and "error" not in r]
        errored = sum(1 for r in rows if r["opp"] == opp and "error" in r)
        if not rs:
            lines.append("| %s | no finished games (%d errored) |" % (opp, errored) + "|" * (7 + len(extra)))
            continue
        per_map = {}
        for r in rs:
            per_map.setdefault(r["map"], []).append(r)
        margin = {m: sum(num(r["margin"]) for r in v) / len(v) for m, v in per_map.items()}
        swept = sum(1 for v in per_map.values() if len(v) == 2 and all(r["res"] == "W" for r in v))
        worst = min(margin, key=margin.get)
        mean = lambda k: sum(num(r[k]) for r in rs) / len(rs)
        lines.append("| %s | %d/%d%s | %d/%d | %.2f | %.2f | %d | %d | %d | %s (%+.0f) | %s |" % (
            opp, sum(r["res"] == "W" for r in rs), len(rs), " (%d errored)" % errored if errored else "",
            swept, len(per_map), mean("gpr"), mean("opp_gpr"), sum(num(r.get("deaths")) for r in rs),
            sum(num(r.get("errs")) for r in rs), sum(num(r.get("crashes")) for r in rs), worst, margin[worst],
            " | ".join([score_str(rs, r) for r in SCORE_ROUNDS] + [share_str(rs, k) for k in SHARE_FIELDS])))
    if rounds:
        lines += ["", "Per game (capped at round %d):" % rounds, "",
                  "| opponent | map | side | res | cap round | cap margin | %s |" % " | ".join(extra),
                  "|" + "---|" * (6 + len(extra))]
        for r in rows:
            if "error" in r:
                lines.append("| %s | %s | %s | error: %s |" % (r["opp"], r["map"], r["side"], r["error"]))
                continue
            lines.append("| %s | %s | %s | %s | %s | %+d | %s |" % (
                r["opp"], r["map"], r["side"], r["res"], r.get("cap_round", ""), num(r["margin"]),
                " | ".join([score_str([r], x) for x in SCORE_ROUNDS] + [share_str([r], k) for k in SHARE_FIELDS])))
    return lines


def game_str(r):
    """One-line console summary of a finished game."""
    extra = " ".join("r%d=%s" % (x, score_str([r], x) or "-") for x in SCORE_ROUNDS)
    extra += " " + " ".join("%s=%s" % (k, share_str([r], k) or "-") for k in SHARE_FIELDS)
    return "%s %+d @%s %s (%.0fs)" % (r["res"], r["margin"], r["round"], extra, r["secs"])


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
    ap.add_argument("--vs", default="starter-python,tzunami444")
    ap.add_argument("--maps", help="comma-separated map names (default: all in maps/)")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--label", help="run folder name under runs/bench/ (default: timestamp)")
    ap.add_argument("--baseline", help="previous run folder or label to diff against")
    ap.add_argument("--timeout", type=int, default=900, help="wall-clock seconds per game")
    ap.add_argument("--fresh", action="store_true", help="ignore the cache")
    ap.add_argument("--rounds", type=int, help="cut every game at this round (opening bench); judged on "
                    "the score at the last tick round <= N instead of the game result")
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
        b = subprocess.run([cambc, "build", "--release", "bots/" + name], cwd=ROOT, capture_output=True, text=True)
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
                key = hashlib.sha256(("v%d|%s|%s|%s|%s|%d|r%s" % (
                    CACHE_VERSION, version, hblue, hred, file_hash(all_maps[name]), side,
                    args.rounds or "full")).encode()).hexdigest()[:24]
                jobs.append({"opp": opp, "map": name, "side": side, "blue": blue, "red": red,
                             "map_path": all_maps[name], "cache": os.path.join(CACHE, key + ".json"),
                             "dir": os.path.join(run_dir, opp, "%s-%s" % (name.replace("/", "_"), "AB"[side])),
                             "timeout": args.timeout, "rounds": args.rounds})
    todo = [j for j in jobs if args.fresh or not os.path.exists(j["cache"])]
    print("cambc %s | %s (%s) vs %s | %d maps x 2 sides | %d to play, %d cached, %d at once%s"
          % (version, bot, hb, ",".join(opps) or "nobody", len(names), len(todo), len(jobs) - len(todo), args.jobs,
             " | capped at round %d" % args.rounds if args.rounds else ""), flush=True)

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
                  r.get("error") or game_str(r)), flush=True)
    wall = time.time() - t0

    rows = [dict(results[id(j)], opp=j["opp"], map=j["map"], side="AB"[j["side"]]) for j in jobs]
    os.makedirs(run_dir, exist_ok=True)
    with open(os.path.join(run_dir, "results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS + ["error"], extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(run_dir, "results.json"), "w") as f:
        json.dump(rows, f, indent=1)
    played = [r for r in rows if not r.get("cached") and "secs" in r]
    lines = summary(bot, rows, skipped, args.rounds)
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
