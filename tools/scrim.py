#!/usr/bin/env python3
"""Paired platform scrims: the same opponents, maps and sides for each live bot we compare.

  python3 -I tools/scrim.py run LABEL [--groups 4] [--seed 1] [--teams "Name=UUID" ...]
      queues GROUPS five-game unranked groups against each team (our LIVE bot plays them), waits for them,
      and appends one row per game to ~/tzunami_data/scrims/LABEL.jsonl
  python3 -I tools/scrim.py run LABEL --pair-with BASE
      replays every group of label BASE with the opponent's frozen bot from that group (--source-group), the same maps
      and sides: an exact pairing even if the opponent has since changed its live bot
  python3 -I tools/scrim.py report LABEL [LABEL ...]
      win rate per opponent and overall, per label
  python3 -I tools/scrim.py metrics LABEL [LABEL ...]
      fetches each game's summary (cached in ~/tzunami_data/scrims/sum/) and prints medians of continuous measures:
      gem share, gold / monster damage / collected gems at r150 and r300, deaths, tributed by r750; with two labels,
      the paired difference game by game (same opponent bot, map and side) -- far more sensitive than wins at 2-6 %

The plan (maps, sides) depends only on --seed, the team and the group index, so two labels run with the same seed
and teams are paired game for game. Quota: 50 groups per rolling hour, shared with the website.
"""
import argparse, collections, json, os, random, subprocess, sys, time

CAMBC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".venv", "bin", "cambc")
ROOT = os.path.expanduser("~/tzunami_data/scrims")
US = "9a848453-f90f-4e97-988f-367378a79d1b"
# The UK band around the top-8 cut (docs/research/LADDER_5_0.md §9), 5 Nov.
BAND = [
    "Team Kungarna=62270180-b974-4f66-9bca-3ff6a25940c3",
    "QS2isLaw=",
    "policy wonk=",
    "Rogue Lock Pickers=ff9d7df3-6308-4dbd-a440-40835248d86a",
    ":3=bbe481a7-4575-4826-9a3e-f81c28205de8",
    "Claudus Maximus=ad5474c2-784c-4f91-b8da-5fec554e4de4",
]


def cambc(args):
    out = None
    for attempt in range(6):
        try:
            out = subprocess.run([CAMBC] + args, capture_output=True, text=True, timeout=180)
        except subprocess.TimeoutExpired:  # network hang (8 Nov night): retry
            time.sleep(10 * (attempt + 1)); continue
        if out.returncode == 0:
            return json.loads(out.stdout)
        if "429" not in out.stderr:
            break
        time.sleep(10 * (attempt + 1))
    sys.exit(f"cambc {' '.join(args)} failed: {out.stderr.strip() if out else 'timeout'}")


def team_ids(specs):
    """'Name=UUID' or 'Name=' (looked up on the ladder) -> [(name, uuid)]."""
    need = [s.split("=", 1)[0] for s in specs if s.endswith("=") or "=" not in s]
    found = {}
    if need:
        for page in range(1, 9):
            for t in cambc(["ladder", "--limit", "100", "--page", str(page), "--json"])["teams"]:
                if t["name"] in need and t["name"] not in found:
                    found[t["name"]] = t["teamId"]
    out = []
    for s in specs:
        name, _, uid = s.partition("=")
        out.append((name, uid or found[name]))
    return out


def plan(seed, name, g, maps):
    rng = random.Random(f"{seed}/{name}/{g}")
    ms = rng.sample(maps, 5)
    sides = ["a", "b", "a", "b", "a"] if g % 2 == 0 else ["b", "a", "b", "a", "b"]
    return ms, sides


def run(a):
    os.makedirs(ROOT, exist_ok=True)
    maps = sorted(m["name"] for m in cambc(["match-groups", "quota", "--json"])["maps"])
    if a.only_maps:  # a map class (10 Nov): a file of map names; the plan samples from those only
        keep = {l.split()[0] for l in open(os.path.expanduser(a.only_maps)) if l.strip()}
        maps = [m for m in maps if m in keep]
        assert len(maps) >= 5, "fewer than 5 platform maps in the class file"
    teams = [] if a.pair_with else team_ids(a.teams or BAND)
    groups = []
    if a.pair_with:
        base = collections.OrderedDict()
        for l in open(f"{ROOT}/{a.pair_with}.jsonl"):
            r = json.loads(l)
            base.setdefault((r["opp"], r["group"]), []).append(r)
        uid_of = dict(team_ids([f"{n}=" for n in {k[0] for k in base}]))
        only = {int(x) for x in a.only_groups.split(",")} if a.only_groups else None
        for (name, g), rs in base.items():
            if only is not None and g not in only:
                continue
            src = rs[0].get("group_id") or cambc(["matches", "show", rs[0]["match"], "--json"])["matches"][0]["groupId"]
            ms = [r["map"] for r in rs]
            sides = [r["side"] for r in rs]
            r = cambc(["match-groups", "create", uid_of[name], "--source-group", src, "--maps", ",".join(ms),
                       "--sides", ",".join(sides), "--json"])
            groups.append((name, g, r["groupId"]))
            time.sleep(1.0)
    done = set()
    if os.path.exists(f"{ROOT}/{a.label}.jsonl") and not a.pair_with:  # top up a label cut short (10 Nov)
        done = {(r["opp"], r["group"]) for r in map(json.loads, open(f"{ROOT}/{a.label}.jsonl"))}
    for name, uid in ([] if a.pair_with else teams):
        for g in range(a.groups):
            if (name, g) in done:
                continue
            ms, sides = plan(a.seed, name, g, maps)
            r = cambc(["match-groups", "create", uid, "--maps", ",".join(ms), "--sides", ",".join(sides), "--json"])
            groups.append((name, g, r["groupId"]))
            time.sleep(1.0)
    print(f"queued {len(groups)} groups", flush=True)
    path = f"{ROOT}/{a.label}.jsonl"
    with open(path, "a") as f:
        for name, g, gid in groups:
            for _ in range(60):
                d = cambc(["match-groups", "show", gid, "--json"])
                if all(m["status"] == "finished" for m in d["matches"]):
                    break
                time.sleep(10)
            for m in d["matches"]:
                us = next(t for t in m["teams"] if t["teamId"] == US)
                f.write(json.dumps(dict(label=a.label, opp=name, group=g, group_id=gid, map=m["map"], side=us["side"],
                                        result=us["result"], end=m.get("endReason"), match=m["matchId"],
                                        status=m["status"])) + "\n")
            time.sleep(0.5)
    print(f"-> {path}")


def report(a):
    for label in a.labels:
        rows = [json.loads(l) for l in open(f"{ROOT}/{label}.jsonl")]
        by = collections.defaultdict(lambda: [0, 0])
        for r in rows:
            by[r["opp"]][0] += r["result"] == "win"
            by[r["opp"]][1] += 1
        w = sum(v[0] for v in by.values()); n = sum(v[1] for v in by.values())
        print(f"{label}: {w}/{n} = {100 * w / max(1, n):.0f} %  |  " + ", ".join(f"{o} {v[0]}/{v[1]}" for o, v in by.items()))


def summary(match):
    d = f"{ROOT}/sum"
    os.makedirs(d, exist_ok=True)
    p = f"{d}/{match}.json"
    if not os.path.exists(p):
        for attempt in range(5):
            try:  # an uncapped call hung the metrics step at the 8 Nov handoff
                out = subprocess.run([CAMBC, "matches", "summary", match, "--json"], cwd=d, capture_output=True, text=True, timeout=90)
            except subprocess.TimeoutExpired:
                time.sleep(5 * (attempt + 1)); continue
            if out.returncode == 0 and os.path.exists(f"{d}/match-{match}.json"):
                break
            time.sleep(5 * (attempt + 1))
        os.replace(f"{d}/match-{match}.json", p)
        time.sleep(0.8)
    return json.load(open(p))


def cum_at(runs, r):
    t, v = 0, 0.0
    for x in runs:
        if t > r:
            break
        v = float(x["value"])
        t += x["duration"]
    return v


def game_metrics(row):
    s = summary(row["match"])
    me = "teamA" if row["side"] == "a" else "teamB"
    op = "teamB" if me == "teamA" else "teamA"
    tl = {t["owner"]: t["runs"] for t in s["teamTimelines"] if t["metric"] == "submittedGems"}
    def tm(team, metric, r):
        ids = {c["id"] for c in s["champions"] if c["team"] == team}
        return sum(cum_at(t["runs"], r) for t in s["championTimelines"] if t["owner"]["id"] in ids and t["metric"] == metric)
    g = {t["team"]: int(t["submittedGems"]) for t in s["teams"]}
    m = dict(win=float(row["result"] == "win"), share=1.0 if row["result"] == "win" else g[me] / max(1, g[me] + g[op]))
    for r in (150, 300):
        m[f"gold{r}"] = tm(me, "earnedGold", r)
        m[f"mon{r}"] = tm(me, "monsterDamageDone", r) / 1000
        m[f"coll{r}"] = tm(me, "collectedGems", r)
    m["deaths"] = sum(float(c["metrics"]["deaths"]) for c in s["champions"] if c["team"] == me)
    m["kills"] = sum(float(c["metrics"]["deaths"]) for c in s["champions"] if c["team"] == op)
    m["trib750"] = cum_at(tl[me], 750)
    m["their750"] = cum_at(tl[op], 750)
    return m


def metrics(a):
    import statistics as st
    per = {}
    for label in a.labels:
        rows = [json.loads(l) for l in open(f"{ROOT}/{label}.jsonl")]
        per[label] = {(r["opp"], r["group"], r["map"], r["side"]): game_metrics(r) for r in rows}
    keys = list(next(iter(per.values())).values())[0].keys()
    print("| label | n | " + " | ".join(keys) + " |")
    print("|---|---|" + "---|" * len(keys))
    for label, d in per.items():
        print(f"| {label} | {len(d)} | " + " | ".join(f"{st.mean(m[k] for m in d.values()):.2f}" for k in keys) + " |")
    if len(per) >= 2:
        la, A = list(per.items())[-1]
        lb, B = list(per.items())[-2]
        common = [k for k in A if k in B]
        print(f"\npaired {la} - {lb} (n={len(common)}): mean difference (95 % CI)")
        for k in keys:
            d = [A[c][k] - B[c][k] for c in common]
            mu = st.mean(d); se = st.stdev(d) / len(d) ** 0.5 if len(d) > 1 else 0
            print(f"  {k:9s} {mu:+8.2f}  ({mu - 1.96 * se:+.2f} .. {mu + 1.96 * se:+.2f})")


def gate(a):
    """After a first stage of paired games: STOP when the candidate is clearly worse, else CONTINUE (6 Nov). Past
    rejections at 120 games had share -0.02..-0.03 with wins -0.04..-0.06 (tz-16, tz-17, tz-22)."""
    import statistics as st
    rows = {}
    for label in (a.base, a.label):
        rows[label] = {(r["opp"], r["group"], r["map"], r["side"]): game_metrics(r)
                       for r in (json.loads(l) for l in open(f"{ROOT}/{label}.jsonl"))}
    common = [k for k in rows[a.label] if k in rows[a.base]]
    dw = st.mean(rows[a.label][k]["win"] - rows[a.base][k]["win"] for k in common)
    ds = st.mean(rows[a.label][k]["share"] - rows[a.base][k]["share"] for k in common)
    verdict = "STOP" if (ds <= -0.015 or dw <= -0.05) else "CONTINUE"
    print(f"{verdict} n={len(common)} win {dw:+.3f} share {ds:+.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("label")
    r.add_argument("--groups", type=int, default=4)
    r.add_argument("--seed", type=int, default=1)
    r.add_argument("--teams", nargs="*")
    r.add_argument("--pair-with", default=None)
    r.add_argument("--only-groups", default=None, help="with --pair-with: only these base group numbers, e.g. 0,1")
    r.add_argument("--only-maps", default=None, help="a file of map names: fresh sets sample from these maps only")
    p = sub.add_parser("report")
    p.add_argument("labels", nargs="+")
    q = sub.add_parser("metrics")
    q.add_argument("labels", nargs="+")
    gt = sub.add_parser("gate")
    gt.add_argument("base")
    gt.add_argument("label")
    a = ap.parse_args()
    {"run": run, "report": report, "metrics": metrics, "gate": gate}[a.cmd](a)
