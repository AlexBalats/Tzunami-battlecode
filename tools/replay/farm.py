#!/usr/bin/env python3
"""How each side farms, from decoded replays with camp state (decode.mjs after 6 Nov).

  python3 -I tools/replay/farm.py ~/tzunami_data/replays/LABEL/manifest.txt [--to 300]

Per side ("us" = the manifest's team index): camp kills by type up to round --to (per game and per body), the bodies
that hit each camp, rounds from first hit to death, and the share of hits on camps whose group still has other
living camps (splitting fire).
"""
import argparse, collections, gzip, json, statistics as st

CT = ["wolf", "elk", "gem", "gold", "mono", "golem", "c6", "c7"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--to", type=int, default=300)
    a = ap.parse_args()
    kills = collections.defaultdict(collections.Counter)
    bodies = collections.defaultdict(list)
    dur = collections.defaultdict(list)
    first = collections.defaultdict(list)
    nb = collections.defaultdict(list)
    games = 0
    for line in open(a.manifest):
        line = line.strip()
        if not line:
            continue
        path, _, t = line.rpartition(":")
        us = int(t)
        games += 1
        team = {}
        hp_prev = {}
        hitters = collections.defaultdict(set)
        first_hit = {}
        firsts = {"us": None, "them": None}
        for l in gzip.open(path, "rt"):
            x = json.loads(l)
            if x["t"] == "round":
                r = x["r"]
                if r > a.to:
                    break
                for c in x["ch"]:
                    team[c["i"]] = c["tm"]
                if r == 1:
                    for tm in (0, 1):
                        nb["us" if tm == us else "them"].append(sum(1 for c in x["ch"] if c["tm"] == tm))
                alive = {(c[0], c[1]): (c[2], c[3]) for c in x.get("cp", [])}
                for p, (hp0, ty) in list(hp_prev.items()):
                    if p not in alive and hitters.get(p):
                        sides = collections.Counter("us" if team[h] == us else "them" for h in hitters[p])
                        side = sides.most_common(1)[0][0]
                        kills[side][CT[ty] if 0 <= ty < 8 else str(ty)] += 1
                        bodies[side].append(len([h for h in hitters[p] if (team[h] == us) == (side == "us")]))
                        dur[side].append(r - first_hit.get(p, r))
                        if firsts[side] is None:
                            firsts[side] = r
                        hitters.pop(p, None)
                        first_hit.pop(p, None)
                hp_prev = alive
                continue
            if x["k"] == 5 or (x["k"] == 6 and x.get("at") in (2, 3, 6)):
                p = tuple(x["to"])
                for q in ([p] if x["k"] == 5 or x.get("at") == 2 else [(p[0] + dx, p[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]):
                    if q in hp_prev:
                        hitters[q].add(x["a"])
                        first_hit.setdefault(q, x["r"])
        for s in ("us", "them"):
            if firsts[s] is not None:
                first[s].append(firsts[s])
    print(f"{games} games, camp kills up to r{a.to}")
    for s in ("us", "them"):
        b = st.mean(nb[s]) if nb[s] else 1
        tot = sum(kills[s].values())
        print(f"{s:4s} bodies {b:.2f}  kills/game {tot / games:5.1f}  per body {tot / games / b:4.1f}  "
              + "  ".join(f"{k} {v / games:4.1f}" for k, v in kills[s].most_common())
              + f"  | bodies per kill {st.mean(bodies[s]):.2f}  rounds first-hit..death {st.median(dur[s]) if dur[s] else 0}"
              + f"  | first kill r{st.median(first[s]) if first[s] else 0}")


if __name__ == "__main__":
    main()
