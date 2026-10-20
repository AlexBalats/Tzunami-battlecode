"""Per-champion means of one arena run, bot A's team only (06_MACRO.md section 11.4).

Usage (from the repo root):
    python3 -I tools/champstats.py RUN_DIR [RUN_DIR ...]

RUN_DIR is a runs/arena/<A>-vs-<B>-<time>/ folder: each <map>-A / <map>-B game folder holds the engine's stats.json.
A game folder ending in -A had bot A as team A (blue), -B as team B. Several RUN_DIRs are merged (a run that reused
cached games keeps those games in the older folder). Columns, means per game the champion played:
    games    games the champion played for A
    coll     gems collected        sub    gems submitted (tributed)    gold   gold earned
    deaths   deaths                kills  champion kills
    mdone    monster damage done   mtaken monster damage taken
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arena import load_stats  # noqa: E402

COLS = (("coll", "collectedGems"), ("sub", "submittedGems"), ("gold", "earnedGold"), ("deaths", "deaths"),
        ("kills", "kills"), ("mdone", "monsterDamageDone"), ("mtaken", "monsterDamageTaken"))


def main():
    games = {}
    for run in sys.argv[1:]:
        for g in sorted(os.listdir(run)):
            p = os.path.join(run, g, "stats.json")
            if os.path.isfile(p) and g[-2:] in ("-A", "-B"):
                games.setdefault(g, p)          # the first RUN_DIR that has a game wins
    tot, n = {}, {}
    for g, p in games.items():
        side = 0 if g.endswith("-A") else 1
        for c in load_stats(p)["champions"]:
            if c["team"] != side:
                continue
            t = tot.setdefault(c["name"], [0.0] * len(COLS))
            for i, (_k, key) in enumerate(COLS):
                t[i] += c.get(key, 0)
            n[c["name"]] = n.get(c["name"], 0) + 1
    print(f"{len(games)} games")
    print(f"{'champion':<14}{'games':>6}" + "".join(f"{k:>8}" for k, _ in COLS))
    for name in sorted(tot, key=lambda x: -n[x]):
        print(f"{name:<14}{n[name]:>6}" + "".join(f"{v / n[name]:>8.0f}" if i >= 5 else f"{v / n[name]:>8.1f}"
                                                for i, v in enumerate(tot[name])))


if __name__ == "__main__":
    main()
