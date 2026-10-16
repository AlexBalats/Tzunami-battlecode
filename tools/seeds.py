"""Judge a bot over several seeds: the arena on every map, both sides, once per salt.

Usage (from the repo root):
    python3 -I tools/seeds.py BOT OPP [--salts 0,1,2,3] [--set KEY=VALUE ...] [--maps a,b] [--jobs 4]

Why: matches are deterministic, and one changed tie-break can swing a map by +-400 gems, so
one arena run (18 games) can't tell a +-100 change from noise [measured 14 Oct]. A bot whose
config.py has SALT jitters its choices a little per salt (SALT 0 = the real bot), which plays
different games; averaging over salts measures the change, not the luck of one trajectory.

For each salt the bot is copied to bots/_snap-seed-<BOT>[-<tag>]-s<salt>/ (git-ignored) with
SALT and every --set KEY=VALUE written into its config.py, then tools/arena.py plays it
(cached, so re-runs are free). Errored games are retried once. Prints, per map, the mean
margin over salts and sides, then the record, mean margin +- its standard error, gems/round,
deaths, and the worst map.
"""
import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOTS = os.path.join(ROOT, "bots")


def variant(bot, salt, sets):
    tag = ""
    if sets:
        tag = "-" + hashlib.sha256(" ".join(sets).encode()).hexdigest()[:6]
    name = "_snap-seed-%s%s-s%d" % (bot.replace("_snap-", ""), tag, salt)
    dst = os.path.join(BOTS, name)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(os.path.join(BOTS, bot), dst, ignore=shutil.ignore_patterns("__pycache__", ".cambc", "build"))
    cfg = os.path.join(dst, "src", "config.py")
    with open(cfg) as f:
        text = f.read()
    for kv in ["SALT=%d" % salt] + sets:
        key, val = kv.split("=", 1)
        text, n = re.subn(r"^%s = .*$" % re.escape(key), "%s = %s" % (key, val), text, count=1, flags=re.M)
        if n != 1:
            sys.exit("no line '%s = ...' in %s/src/config.py" % (key, bot))
    with open(cfg, "w") as f:
        f.write(text)
    return name


def arena(a, b, args):
    cmd = [sys.executable, "-I", os.path.join(ROOT, "tools", "arena.py"), a, b, "--jobs", str(args.jobs)]
    if args.maps:
        cmd += ["--maps", args.maps]
    for attempt in range(2):
        out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True).stdout
        m = re.search(r"^saved (.+summary\.json)$", out, re.M)
        if not m:
            sys.exit("arena failed:\n" + out[-2000:])
        with open(os.path.join(ROOT, m.group(1))) as f:
            rows = json.load(f)["rows"]
        if all("res" in r for r in rows) or attempt:
            return rows
        print("  retrying %d errored game(s)" % sum("res" not in r for r in rows), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bot")
    ap.add_argument("opp")
    ap.add_argument("--salts", default="0,1,2,3")
    ap.add_argument("--set", action="append", default=[], help="KEY=VALUE written into config.py")
    ap.add_argument("--maps")
    ap.add_argument("--jobs", type=int, default=4)
    args = ap.parse_args()
    salts = [int(s) for s in args.salts.split(",")]

    per_map, all_rows = {}, []
    for salt in salts:
        name = variant(args.bot, salt, args.set)
        rows = [r for r in arena(name, args.opp, args) if "res" in r]
        w = sum(r["res"] == "W" for r in rows)
        mean = sum(r["margin"] for r in rows) / max(1, len(rows))
        print("salt %d: %2dW/%2dL  margin %+5.0f" % (salt, w, len(rows) - w, mean), flush=True)
        for r in rows:
            per_map.setdefault(r["map"], []).append(r["margin"])
        all_rows += rows

    print("\n%s%s vs %s over salts %s\n" % (args.bot, "".join(" " + s for s in args.set), args.opp, args.salts))
    print("%-12s %6s %6s %6s  %s" % ("map", "mean", "min", "wins", "margins"))
    for m, ms in per_map.items():
        print("%-12s %+6.0f %+6d %3d/%-2d  %s" % (m, sum(ms) / len(ms), min(ms), sum(x > 0 for x in ms), len(ms),
                                              " ".join("%+d" % x for x in ms)))
    n = len(all_rows)
    ms = [r["margin"] for r in all_rows]
    mean = sum(ms) / n
    se = math.sqrt(sum((x - mean) ** 2 for x in ms) / max(1, n - 1) / n)
    w = sum(r["res"] == "W" for r in all_rows)
    worst = min(per_map, key=lambda k: sum(per_map[k]) / len(per_map[k]))
    print("\nRecord     %d W / %d L of %d (win rate %.0f%%)" % (w, n - w, n, 100.0 * w / n))
    print("Margin     %+.0f +- %.0f (standard error)" % (mean, se))
    print("gems/round %.2f   deaths %.1f   lost %.0f" % (sum(r["gpr"] for r in all_rows) / n,
                                                       sum(r["deaths"] for r in all_rows) / n,
                                                       sum(r["lost"] for r in all_rows) / n))
    print("Worst map  %s (mean %+.0f)" % (worst, sum(per_map[worst]) / len(per_map[worst])))


if __name__ == "__main__":
    main()
