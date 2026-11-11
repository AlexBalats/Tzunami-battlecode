#!/usr/bin/env python3
"""Feasibility check: can P(win) be read from the state at round R, using platform summaries alone?

  python3 -I tools/ladder_value.py          # logistic P(team A wins | diffs at round R), map-grouped CV

Features are team A minus team B, at round R: tributed gems, gems carried, gold earned, kills, champions dead
(died in the last 60 rounds), monster damage. Fitted per checkpoint. Reports held-out log loss / accuracy / AUC
against the "tributed lead" baseline, and the fitted exchange rates (gems per unit of each feature).
"""
import collections, glob, json, math, os, random

import numpy as np

ROOT = os.path.expanduser("~/tzunami_data/ladder_5_0")
CHECK = [150, 300, 500, 750]
FEATS = ["tributed", "carried", "gold", "kills", "dead", "mondmg"]


def expand(runs, n):
    out = []
    for x in runs:
        out += [float(x["value"])] * x["duration"]
    return (out + [out[-1] if out else 0.0] * n)[:n]


def game_features(s):
    n = s["match"]["roundsCompleted"] + 2
    tl = {t["owner"]: expand(t["runs"], n) for t in s["teamTimelines"] if t["metric"] == "submittedGems"}
    team_of = {c["id"]: c["team"] for c in s["champions"]}
    agg = {t: collections.defaultdict(lambda: np.zeros(n)) for t in ("teamA", "teamB")}
    for t in s["championTimelines"]:
        if t["metric"] in ("gems", "earnedGold", "kills", "deaths", "monsterDamageDone"):
            agg[team_of[t["owner"]["id"]]][t["metric"]] += np.array(expand(t["runs"], n))
    rows = {}
    for r in CHECK:
        if r >= n - 1:
            continue
        f = []
        for t in ("teamA", "teamB"):
            d = agg[t]["deaths"]
            f.append([tl[t][r], agg[t]["gems"][r], agg[t]["earnedGold"][r], agg[t]["kills"][r],
                      d[r] - d[max(0, r - 60)], agg[t]["monsterDamageDone"][r] / 1000])
        rows[r] = np.array(f[0]) - np.array(f[1])
    return rows


def fit_logistic(X, y, l2=1e-2, iters=3000, lr=0.1):
    w = np.zeros(X.shape[1] + 1)
    Xb = np.hstack([X, np.ones((len(X), 1))])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-Xb @ w))
        g = Xb.T @ (p - y) / len(y) + l2 * np.r_[w[:-1], 0]
        w -= lr * g
    return w


def predict(w, X):
    return 1 / (1 + np.exp(-(np.hstack([X, np.ones((len(X), 1))]) @ w)))


def auc(p, y):
    pos, neg = p[y == 1], p[y == 0]
    if not len(pos) or not len(neg):
        return float("nan")
    return float(np.mean([(a > b) + 0.5 * (a == b) for a in pos for b in neg]))


def main():
    data = collections.defaultdict(list)  # r -> [(map, feats, y)]
    maps = {}
    for f in glob.glob(f"{ROOT}/lists/*.json"):
        for m in json.load(open(f)):
            maps[m["matchId"]] = m["map"]
    only = set(os.environ["LADDER_TEAMS"].split("|")) if os.environ.get("LADDER_TEAMS") else None
    names = {}
    for f in glob.glob(f"{ROOT}/lists/*.json"):
        for m in json.load(open(f)):
            names[m["matchId"]] = {t["name"] for t in m["teams"]}
    for f in glob.glob(f"{ROOT}/summaries/*.json"):
        if only and not (names.get(os.path.basename(f)[:-5], set()) & only):
            continue
        s = json.load(open(f))
        if s["match"]["outcome"] not in ("teamA", "teamB"):
            continue
        y = 1 if s["match"]["outcome"] == "teamA" else 0
        for r, x in game_features(s).items():
            data[r].append((maps[os.path.basename(f)[:-5]], x, y))
    print(f"games: {len(glob.glob(f'{ROOT}/summaries/*.json'))}; folds grouped by map (5 folds)\n")
    print("| round | n alive | baseline acc (tributed lead) | model log loss | model acc | model AUC | exchange rates, gems per unit (carried, gold, kill, dead, 1k monster dmg) |")
    print("|---|---|---|---|---|---|---|")
    for r in CHECK:
        rows = data[r]
        X = np.array([x for _, x, _ in rows]); y = np.array([y for *_, y in rows], float)
        # symmetrise: add the flipped game (B's view) so the model has no side term
        X = np.vstack([X, -X]); y = np.r_[y, 1 - y]; mp = [m for m, *_ in rows] * 2
        sd = X.std(0) + 1e-9
        Xs = X / sd
        ms = sorted(set(mp)); random.Random(0).shuffle(ms)
        fold = {m: i % 5 for i, m in enumerate(ms)}
        P = np.zeros(len(y))
        for k in range(5):
            tr = np.array([fold[m] != k for m in mp]); te = ~tr
            w = fit_logistic(Xs[tr], y[tr])
            P[te] = predict(w, Xs[te])
        ll = -np.mean(y * np.log(P + 1e-9) + (1 - y) * np.log(1 - P + 1e-9))
        base = X[:, 0]
        bacc = np.mean([(b > 0) == (t == 1) for b, t in zip(base, y) if b != 0])
        w = fit_logistic(Xs, y) / np.r_[sd, 1]  # raw-unit weights
        rate = [w[i] / w[0] for i in range(1, len(FEATS))]
        print(f"| {r} | {len(rows)} | {bacc:.2f} | {ll:.3f} | {np.mean((P > .5) == (y == 1)):.2f} | {auc(P, y):.2f} | "
              + ", ".join(f"{v:+.2f}" for v in rate) + " |")


if __name__ == "__main__":
    main()
