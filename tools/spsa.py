#!/usr/bin/env python3
"""SPSA over a bot's value.h constants (tools/variant.py), judged by paired games on the TRAIN maps only.

  python3 -I tools/spsa.py tz --opp _tz31f --space goal --iters 30 --maps-per-eval 48 [--out runs/spsa_<name>.json]

Fitness of a build = mean zero-sum gem share (ours / (ours + theirs)) over its games, both sides of each sampled map;
a win counts 1 (gems are the margin, wins dominate). Each iteration plays theta+ and theta- on the same sampled maps.
Gains: a_k = a / (A + k + 1)^0.602, c_k = c / (k + 1)^0.101 (Spall); parameters are scaled to [0, 1] by their bounds.
The held-out quarter of the maps (tools/judge.py held_out) is never played here: confirm on it with judge.py.
"""
import argparse, json, os, random, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import judge  # noqa: E402
import variant  # noqa: E402

# name: (low, high) - the start is the bot's current default
SPACE_ECON = {
    "hit_frac": (0.2, 0.8),
    "hysteresis": (1.0, 2.0),
    "shop_gold": (0.03, 0.25),
    "bank_k": (0.5, 2.0),
    "hp_floor": (0.2, 0.6),
    "gold_r150": (0.08, 0.35),
    "gold_r300": (0.06, 0.3),
    "retreat_rounds": (2.0, 9.0),
    "camp_retreat": (0.15, 0.5),
    "opening_end": (0.0, 400.0),
}
SPACE = {  # 6 Nov evening: the knobs of the tz-24 structure (feed, assist, free hits), bounds around the defaults
    "commit_bias": (0.7, 1.5),
    "enemy_dps_k": (0.9, 1.5),
    "stance_low": (0.15, 0.45),
    "threat_k": (0.05, 0.4),
    "hysteresis": (1.0, 1.6),
    "retreat_rounds": (2.0, 6.0),
    "camp_retreat": (0.15, 0.4),
    "gold_r150": (0.4, 0.7),
    "gold_r300": (0.2, 0.45),
    "feed_r": (5.0, 14.0),
    "assist_r": (4.0, 10.0),
    "assist_hp": (0.3, 0.8),
    "break_radius": (5.0, 10.0),
    "danger_multi": (0.4, 0.9),
    "execute_margin": (0.8, 1.4),
}

SPACE_GOAL = {  # 7 Nov (BUILD_LOG Next 3): the goal pick's weights; bounds around the tz-31 defaults
    "gold_r150": (0.35, 0.75),
    "gold_r300": (0.18, 0.46),
    "gold_r500": (0.06, 0.25),
    "gem_k": (0.8, 1.3),
    "danger_one": (0.6, 1.0),
    "danger_multi": (0.35, 0.85),
    "threat_k": (0.05, 0.4),
    "walk_k": (0.7, 1.4),
    "wait_pen": (0.0, 0.6),
    "carried_danger": (0.1, 0.4),
    "bank_k": (0.6, 1.1),
}


FITNESS = "share"


def defaults(bot):
    import re
    text = open(os.path.join(judge.REPO, "bots", bot, "src", "value.h")).read()
    out = {}
    for k in SPACE:
        m = re.search(r"\b(?:float|int)\s+" + k + r"\s*=\s*([-0-9.e]+)", text)
        out[k] = float(m.group(1))
    return out


def play(name, opp, maps, jobs, tmp):
    man, rows = [], []
    for m in maps:
        for side in ("a", "b"):
            a, b = (name, opp) if side == "a" else (opp, name)
            tag = f"{name}_{m}_{side}"
            man.append(f"{judge.REPO}/bots/{a} {judge.REPO}/bots/{b} {judge.REPO}/maps/{m}.map26a {tmp}/{tag}.repl26a "
                       f"--statistics {tmp}/{tag}.json --json")
            rows.append((side, f"{tmp}/{tag}.json"))
    mf = f"{tmp}/{name}.txt"
    open(mf, "w").write("\n".join(man) + "\n")
    subprocess.run([judge.CAMBC, "build", name], cwd=judge.REPO, check=True, capture_output=True)
    subprocess.run([judge.CAMBC, "run-batch", mf, "--jobs", str(jobs), "--release"], cwd=judge.REPO, capture_output=True)
    score, n, wins = 0.0, 0, 0
    for side, path in rows:
        if not os.path.exists(path):
            continue
        s = json.load(open(path))
        me = "teamA" if side == "a" else "teamB"
        g = {t["team"]: int(t["submittedGems"]) for t in s["teams"]}
        o = "teamB" if me == "teamA" else "teamA"
        win = s["match"]["outcome"] == me
        wins += win
        if FITNESS == "speed":
            score += (2000 - s["match"]["roundsCompleted"]) / 2000 if win else 0.0
        else:
            score += 1.0 if win else g[me] / max(1, g[me] + g[o])
        n += 1
        os.remove(path)
    for f in os.listdir(tmp):
        if f.endswith(".repl26a"):
            os.remove(os.path.join(tmp, f))
    return score / max(1, n), wins, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bot")
    ap.add_argument("--opp", required=True, help="never v93 (a benchmark): idle, starter-cpp or a frozen copy of our previous build")
    ap.add_argument("--iters", type=int, default=40)
    ap.add_argument("--maps-per-eval", type=int, default=24)
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--a", type=float, default=0.08)
    ap.add_argument("--c", type=float, default=0.12)
    ap.add_argument("--out", default=None)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--fitness", default="share", choices=["share", "speed"])
    ap.add_argument("--space", default=None, choices=["fight", "econ", "goal"])
    a = ap.parse_args()
    global FITNESS, SPACE
    FITNESS = a.fitness
    if a.opp == "v93":
        sys.exit("never tune against v93: it is the benchmark")
    if a.fitness == "speed":
        SPACE = SPACE_ECON
    if a.space:
        SPACE = {"fight": SPACE, "econ": SPACE_ECON, "goal": SPACE_GOAL}[a.space]
    rng = random.Random(a.seed)
    train = judge.maps("train")
    theta = defaults(a.bot)
    x = {k: (theta[k] - lo) / (hi - lo) for k, (lo, hi) in SPACE.items()}
    out = a.out or os.path.join(os.environ.get("JUDGE_TMP", tempfile.gettempdir()), f"spsa_{a.bot}.json")
    tmp = tempfile.mkdtemp(prefix="spsa_", dir=os.environ.get("JUDGE_TMP"))
    log = []
    A = a.iters * 0.1
    for k in range(a.iters):
        ak = a.a / (A + k + 1) ** 0.602
        ck = a.c / (k + 1) ** 0.101
        delta = {p: rng.choice((-1, 1)) for p in SPACE}
        maps = rng.sample(train, a.maps_per_eval)
        res = {}
        for sign, name in ((1, "_spsa_p"), (-1, "_spsa_m")):
            vals = {}
            for p, (lo, hi) in SPACE.items():
                xv = min(1.0, max(0.0, x[p] + sign * ck * delta[p]))
                v = lo + xv * (hi - lo)
                vals[p] = str(int(round(v))) if p in ("opening_end",) else f"{v:.4f}"
            variant.make(a.bot, name, vals)
            res[sign] = play(name, a.opp, maps, a.jobs, tmp)
        g = (res[1][0] - res[-1][0]) / (2 * ck)
        for p in SPACE:
            x[p] = min(1.0, max(0.0, x[p] + ak * g * delta[p]))
        cur = {p: round(lo + x[p] * (hi - lo), 4) for p, (lo, hi) in SPACE.items()}
        log.append(dict(k=k, plus=res[1], minus=res[-1], theta=cur, t=time.time()))
        json.dump(log, open(out, "w"), indent=1)
        print(f"k={k} plus {res[1][0]:.3f} ({res[1][1]}/{res[1][2]}) minus {res[-1][0]:.3f} ({res[-1][1]}/{res[-1][2]}) theta {cur}",
              flush=True)
    shutil.rmtree(tmp, ignore_errors=True)
    for n in ("_spsa_p", "_spsa_m"):
        shutil.rmtree(os.path.join(judge.REPO, "bots", n), ignore_errors=True)


if __name__ == "__main__":
    main()
