"""Play bot A against bot B on every map, from both sides, and print how A did.

Usage (from the repo root):
    python3 -I tools/arena.py BOT_A BOT_B [--maps lanes,packs] [--jobs 3] [--fresh]

BOT is a folder name in bots/ (e.g. starter-python), or NAME@REV to play the version of
bots/NAME at git revision REV (e.g. v1@HEAD~1); that version is exported to bots/_snap-NAME-REV/.

Each map is played twice: A as team A (blue) and A as team B (red). Matches are
deterministic [measured], so a result is cached under runs/arena/cache/ by the cambc version,
the hash of both bots' sources, the map file and the side, and is only replayed when one of
those changes (or with --fresh). Set CAMBC=/path/to/cambc to use another engine version. Replays, stats JSON and a summary.json land in runs/arena/<A>-vs-<B>-<time>/.

Columns (all from A's point of view):
    res     W / L / D from the engine's outcome (a tie on gems at round 2,000 still gets a winner on 2.2.x)
    round   round the game ended
    gems    gems A tributed; opp = gems B tributed; margin = gems - opp
    g/r     A's tributed gems per round
    deaths  A's deaths (Cassi & Issac count as two bodies); kills = A's champion kills
    lost    gems A collected but never tributed or kept: collected - tributed - carried at
            the end. Mostly gems dropped on death [provisional A33].
    faults  bot faults (crashes) for A / B; anything but 0/0 is a bug.
"""
import argparse
import concurrent.futures
import datetime
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOTS = os.path.join(ROOT, "bots")
MAPS = os.path.join(ROOT, "maps")
OUT = os.path.join(ROOT, "runs", "arena")
CACHE = os.path.join(OUT, "cache")
CACHE_VERSION = 1  # bump when the stored record format changes
# --json: since cambc 2.2.0 --statistics writes binary without it. --release: run as on the platform
# (debug_block skipped, fuel pause imports not linked); same games as debug mode for our bots [measured 16 Oct].
RUN_FLAGS = ["--json", "--release"]


def find_cambc():
    for path in (os.environ.get("CAMBC"), shutil.which("cambc"), os.path.join(ROOT, ".venv", "bin", "cambc")):
        if path and os.path.exists(path):
            return path
    sys.exit("cambc not found: install it (README quick start) or set CAMBC=/path/to/cambc")


def resolve_bot(spec):
    """Return the folder name in bots/ for BOT or NAME@REV (exported from git)."""
    if "@" not in spec:
        if not os.path.isdir(os.path.join(BOTS, spec, "src")):
            sys.exit("no bot at bots/%s/src" % spec)
        return spec
    name, rev = spec.split("@", 1)
    sha = subprocess.run(["git", "rev-parse", "--short", rev], cwd=ROOT, capture_output=True, text=True)
    if sha.returncode:
        sys.exit("unknown git revision %r" % rev)
    folder = "_snap-%s-%s" % (name, sha.stdout.strip())
    dest = os.path.join(BOTS, folder)
    if not os.path.isdir(dest):
        tar = subprocess.run(["git", "archive", "--format=tar", rev, "bots/%s" % name], cwd=ROOT, capture_output=True)
        if tar.returncode:
            sys.exit("bots/%s doesn't exist at %s" % (name, rev))
        tmp = dest + ".tmp"
        shutil.rmtree(tmp, ignore_errors=True)
        with tarfile.open(fileobj=io.BytesIO(tar.stdout)) as archive:
            archive.extractall(tmp)
        os.rename(os.path.join(tmp, "bots", name), dest)
        shutil.rmtree(tmp)
    return folder


def source_hash(folder):
    """Hash of a bot's source files, so the cache notices any edit."""
    h = hashlib.sha256()
    src = os.path.join(BOTS, folder)
    for path in sorted(glob.glob(os.path.join(src, "**", "*"), recursive=True)):
        rel = os.path.relpath(path, src)
        if os.path.isdir(path) or rel.startswith(".cambc") or "__pycache__" in rel:
            continue
        h.update(rel.encode() + b"\0")
        with open(path, "rb") as f:
            h.update(f.read() + b"\0")
    return h.hexdigest()[:16]


def file_hash(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def load_stats(path):
    """Read a --statistics --json file in the flat pre-2.2 shape every tool uses: outcome, round,
    botFaults [A, B], teams [{team, submittedGems}], champions [{team, name, kills, deaths, ...}]
    (team as 0/1, counts as ints). cambc 2.2.x nests these under match/diagnostics/metrics."""
    with open(path) as f:
        s = json.load(f)
    if "match" not in s:  # written by cambc 2.1.x
        return s
    side = {"teamA": 0, "teamB": 1}
    num = lambda v: float(v) if isinstance(v, float) else int(v)
    champs = []
    for c in s["champions"]:
        row = {k: num(v) for k, v in c["metrics"].items()}
        row.update(team=side[c["team"]], name=c["name"])
        champs.append(row)
    faults = s["diagnostics"]["botFaults"]
    return {"outcome": s["match"]["outcome"], "round": s["match"]["roundsStarted"],
            "botFaults": [faults["teamA"], faults["teamB"]],
            "teams": [{"team": side[t["team"]], "submittedGems": int(t["submittedGems"])} for t in s["teams"]],
            "champions": champs}


DRAFT_LINE = re.compile(r"^\s+([AB])\s+\S+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+(.+?)\s*$")


def play(cambc, job):
    """Run one match with --statistics and return the raw record (or an error record)."""
    os.makedirs(job["dir"], exist_ok=True)
    stats_path = os.path.join(job["dir"], "stats.json")
    cmd = [cambc, "run", "bots/" + job["blue"], "bots/" + job["red"], "--map", job["map_path"], "-o", job["dir"], "--statistics", stats_path] + RUN_FLAGS
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=job["timeout"])
        log = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired as e:
        log = "TIMEOUT after %ss\n%s" % (job["timeout"], e.stdout or "")
    with open(os.path.join(job["dir"], "cli.log"), "w") as f:
        f.write(log)
    if not os.path.exists(stats_path):
        return {"error": log.strip().splitlines()[-1] if log.strip() else "no output"}
    stats = load_stats(stats_path)
    drafts = {m.group(1): m.group(2) for m in map(DRAFT_LINE.match, log.splitlines()) if m}
    return {"stats": stats, "drafts": drafts}


def summarise(record, a_side):
    """Turn one match's stats into numbers from bot A's point of view (a_side 0 = blue)."""
    if "error" in record:
        return {"error": record["error"]}
    s = record["stats"]
    b_side = 1 - a_side
    teams = {t["team"]: t for t in s["teams"]}
    mine = [c for c in s["champions"] if c["team"] == a_side]
    gems, opp = teams[a_side]["submittedGems"], teams[b_side]["submittedGems"]
    winner = {"teamA": 0, "teamB": 1}.get(s["outcome"])
    res = "D" if winner is None else ("W" if winner == a_side else "L")
    rnd = max(s["round"], 1)
    return {
        "res": res,
        "outcome": s["outcome"],
        "round": s["round"],
        "gems": gems,
        "opp": opp,
        "margin": gems - opp,
        "gpr": gems / rnd,
        "deaths": sum(c["deaths"] for c in mine),
        "kills": sum(c["kills"] for c in mine),
        "lost": sum(c["collectedGems"] - c["submittedGems"] - c["gems"] for c in mine),
        "faults": "%d/%d" % (s["botFaults"][a_side], s["botFaults"][b_side]),
        "fault_a": s["botFaults"][a_side],
        "draft": record["drafts"].get("AB"[a_side], ""),
        "opp_draft": record["drafts"].get("AB"[b_side], ""),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bot_a")
    ap.add_argument("bot_b")
    ap.add_argument("--maps", help="comma-separated map names (default: every maps/**/*.map26a)")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 4) // 3), help="matches at once (each uses ~3 cores)")
    ap.add_argument("--timeout", type=int, default=900, help="wall-clock seconds per match")
    ap.add_argument("--fresh", action="store_true", help="ignore the cache and replay everything")
    ap.add_argument("--drafts", action="store_true", help="also print each game's drafts")
    args = ap.parse_args()

    cambc = find_cambc()
    version = subprocess.run([cambc, "--version"], capture_output=True, text=True).stdout.split()[-1]
    a, b = resolve_bot(args.bot_a), resolve_bot(args.bot_b)
    all_maps = {os.path.splitext(os.path.relpath(p, MAPS))[0]: p
                for p in sorted(glob.glob(os.path.join(MAPS, "**", "*.map26a"), recursive=True))}
    names = args.maps.split(",") if args.maps else list(all_maps)
    missing = [n for n in names if n not in all_maps]
    if missing:
        sys.exit("unknown maps: %s (have: %s)" % (", ".join(missing), ", ".join(all_maps)))

    # Build each bot once up front, so parallel matches don't race to rebuild it.
    for bot in dict.fromkeys((a, b)):
        built = subprocess.run([cambc, "build", "--release", "bots/" + bot], cwd=ROOT, capture_output=True, text=True)
        if built.returncode:
            sys.exit("build failed for %s:\n%s%s" % (bot, built.stdout, built.stderr))

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = os.path.join(OUT, "%s-vs-%s-%s" % (a, b, stamp))
    os.makedirs(CACHE, exist_ok=True)
    ha, hb = source_hash(a), source_hash(b)

    jobs = []
    for name in names:
        path = all_maps[name]
        for a_side in (0, 1):
            blue, red = (a, b) if a_side == 0 else (b, a)
            hblue, hred = (ha, hb) if a_side == 0 else (hb, ha)
            key = "v%d-%s-%s-%s-%s" % (CACHE_VERSION, version, hblue, hred, file_hash(path))
            jobs.append({
                "map": name, "map_path": path, "a_side": a_side, "blue": blue, "red": red,
                "cache": os.path.join(CACHE, key + ".json"),
                "dir": os.path.join(run_dir, "%s-%s" % (name.replace(os.sep, "_"), "AB"[a_side])),
                "timeout": args.timeout,
            })

    todo = [j for j in jobs if args.fresh or not os.path.exists(j["cache"])]
    print("cambc %s | %s (%s) vs %s (%s): %d maps x 2 sides, %d to play, %d cached, %d at once"
          % (version, a, ha, b, hb, len(names), len(todo), len(jobs) - len(todo), args.jobs), flush=True)

    records = {}
    for j in jobs:
        if j not in todo:
            with open(j["cache"]) as f:
                records[id(j)] = json.load(f)
    # A mirror match (A == B) plays the same game from both sides: run each cache key once.
    unique = list({j["cache"]: j for j in todo}.values())
    with concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
        futures = {pool.submit(play, cambc, j): j for j in unique}
        for done, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            j = futures[fut]
            record = fut.result()
            for other in todo:
                if other["cache"] == j["cache"]:
                    records[id(other)] = record
            if "error" not in record:  # never cache a failed run
                with open(j["cache"], "w") as f:
                    json.dump(record, f)
            print("  [%d/%d] %s, %s blue: %s" % (done, len(unique), j["map"], j["blue"],
                                                record.get("error") or record["stats"]["outcome"]), flush=True)

    rows = []
    for j in jobs:
        row = summarise(records[id(j)], j["a_side"])
        row.update(map=j["map"], side="AB"[j["a_side"]])
        rows.append(row)
    report(a, b, rows, args.drafts)

    os.makedirs(run_dir, exist_ok=True)
    with open(os.path.join(run_dir, "summary.json"), "w") as f:
        json.dump({"cambc": version, "bot_a": a, "bot_b": b, "hash_a": ha, "hash_b": hb, "rows": rows}, f, indent=1)
    print("\nsaved %s" % os.path.relpath(os.path.join(run_dir, "summary.json"), ROOT))


def report(a, b, rows, show_drafts):
    print("\n%s vs %s, from %s's side\n" % (a, b, a))
    head = "%-12s %4s %3s %5s %5s %5s %6s %5s %6s %5s %5s %6s" % (
        "map", "side", "res", "round", "gems", "opp", "margin", "g/r", "deaths", "kills", "lost", "faults")
    print(head)
    print("-" * len(head))
    for r in rows:
        if "error" in r:
            print("%-12s %4s ERROR %s" % (r["map"], r["side"], r["error"]))
            continue
        print("%-12s %4s %3s %5d %5d %5d %+6d %5.2f %6d %5d %5d %6s" % (
            r["map"], r["side"], r["res"], r["round"], r["gems"], r["opp"], r["margin"], r["gpr"],
            r["deaths"], r["kills"], r["lost"], r["faults"]))
        if show_drafts:
            print("%17s us: %s | them: %s" % ("", r["draft"], r["opp_draft"]))

    ok = [r for r in rows if "error" not in r]
    errors = len(rows) - len(ok)
    if not ok:
        print("\nno finished games")
        return
    w = sum(r["res"] == "W" for r in ok)
    l = sum(r["res"] == "L" for r in ok)
    d = len(ok) - w - l
    mean = lambda key: sum(r[key] for r in ok) / len(ok)

    # Per map, both sides together: a map is only "won" if A wins from both sides.
    per_map = {}
    for r in ok:
        per_map.setdefault(r["map"], []).append(r)
    map_margin = {m: sum(r["margin"] for r in rs) / len(rs) for m, rs in per_map.items()}
    swept = [m for m, rs in per_map.items() if len(rs) == 2 and all(r["res"] == "W" for r in rs)]
    worst = min(map_margin, key=map_margin.get)

    print("\nRecord     %d W / %d L / %d D  (win rate %.0f%%)%s" % (
        w, l, d, 100.0 * (w + 0.5 * d) / len(ok), ("   %d ERRORED" % errors) if errors else ""))
    print("Maps won from both sides  %d / %d" % (len(swept), len(per_map)))
    print("Mean       margin %+.0f   gems/round %.2f   deaths %.1f   lost %.0f   kills %.1f" % (
        mean("margin"), mean("gpr"), mean("deaths"), mean("lost"), mean("kills")))
    print("Worst map  %s (mean margin %+.0f)" % (worst, map_margin[worst]))
    faults = sum(r["fault_a"] for r in ok)
    if faults:
        print("FAULTS     %s crashed %d times" % (a, faults))


if __name__ == "__main__":
    main()
