#!/usr/bin/env python3
"""Per-team statistics from platform match summaries (see tools/ladder_pull.py).

  python3 -I tools/ladder_stats.py rows            # summaries -> rows.jsonl (one row per game x focus team)
  python3 -I tools/ladder_stats.py report          # rows.jsonl -> markdown tables on stdout

A "focus team" is one of the teams named in TEAMS; each game is seen from each focus team that played it.
"""
import bisect, collections, glob, json, math, os, statistics, sys

ROOT = os.path.expanduser("~/tzunami_data/ladder_5_0")
TEAMS = ["Intercontinental Fish", "Mite", "Pantheon"]
SHORT = {"Intercontinental Fish": "Fish", "Mite": "Mite", "Pantheon": "Pantheon"}
# LADDER_TEAMS="A|B|C" focuses on other teams; LADDER_ROWS names the rows file (default rows.jsonl)
if os.environ.get("LADDER_TEAMS"):
    TEAMS = os.environ["LADDER_TEAMS"].split("|")
    SHORT = {t: t[:14] for t in TEAMS}
ROWS = os.path.join(ROOT, os.environ.get("LADDER_ROWS", "rows.jsonl"))
CHECK = [100, 200, 300, 500, 750, 1000, 1500]
PHASES = [(0, 300), (300, 1000), (1000, 2001)]


def cum_at(runs, r):
    """Value of a run-length timeline at round r (runs start at round 0)."""
    t, v = 0, 0
    for x in runs:
        if t > r:
            break
        v = float(x["value"])
        t += x["duration"]
    return v


def expand(runs):
    out = []
    for x in runs:
        out += [float(x["value"])] * x["duration"]
    return out


def game_rows(meta, s):
    """Rows for each focus team in one game. meta = list entry, s = summary JSON."""
    rows = []
    side_of = {t["name"]: ("teamA" if t["side"] == "a" else "teamB") for t in meta["teams"]}
    final = {t["team"]: int(t["submittedGems"]) for t in s["teams"]}
    tl = {t["owner"]: t["runs"] for t in s["teamTimelines"] if t["metric"] == "submittedGems"}
    champs = {c["id"]: c for c in s["champions"]}
    ctl = collections.defaultdict(dict)
    for t in s["championTimelines"]:
        ctl[t["owner"]["id"]][t["metric"]] = t["runs"]
    ev = collections.defaultdict(list)  # kind -> [(owner, entry)]
    for e in s["events"]:
        for x in e["entries"]:
            ev[e["kind"]].append((e["owner"], x))
    rounds = s["match"]["roundsCompleted"]
    engagements = find_engagements(s, ctl, champs)

    for tm in meta["teams"]:
        if tm["name"] not in TEAMS:
            continue
        me = side_of[tm["name"]]
        op = "teamB" if me == "teamA" else "teamA"
        opp = [t for t in meta["teams"] if t is not tm][0]
        r = dict(match=meta["matchId"], group=meta["groupId"], t=meta["createdAt"], map=meta["map"],
                 team=tm["name"], opp=opp["name"], side=tm["side"], result=tm["result"],
                 end=meta["endReason"], rounds=rounds, w=s["match"]["width"], h=s["match"]["height"],
                 gems=final[me], ogems=final[op], faults=s["diagnostics"]["botFaults"][me])
        r["draft"] = [c["name"] for c in s["roster"]["champions"] if c["team"] == me]
        r["odraft"] = [c["name"] for c in s["roster"]["champions"] if c["team"] == op]
        r["picks"] = [d["champion"] for d in s["roster"]["draft"] if d["team"] == me]
        for c in CHECK:
            r[f"g{c}"], r[f"og{c}"] = cum_at(tl[me], c), cum_at(tl[op], c)
        # economy at checkpoints (sum over champions)
        for side, key in ((me, ""), (op, "o")):
            ids = [i for i, c in champs.items() if c["team"] == side]
            for c in (150, 300, 600):
                r[f"{key}gold{c}"] = sum(cum_at(ctl[i]["earnedGold"], c) for i in ids)
                r[f"{key}coll{c}"] = sum(cum_at(ctl[i]["collectedGems"], c) for i in ids)
        # gem sources and losses
        src = collections.Counter()
        for owner, x in ev["gemCollection"]:
            if owner["team"] == me:
                src["cap" if x["context"] == "campGroup" else "bag"] += int(x["value"])
        for owner, x in ev["gemLoss"]:
            side = "me" if owner["team"] == me else "op"
            src[f"lost_{side}_{x['context']}"] += int(x["value"])
        r.update({k: src[k] for k in ("cap", "bag", "lost_me_champion", "lost_me_camp", "lost_op_champion", "lost_op_camp")})
        subs = [int(x["value"]) for o, x in ev["gemSubmission"] if o["team"] == me]
        r["tributes"], r["bag_mean"] = len(subs), (sum(subs) / len(subs) if subs else 0)
        r["first_tribute"] = min([x["timestamp"]["round"] for o, x in ev["gemSubmission"] if o["team"] == me] or [None]) if subs else None
        # deaths and kills by phase and killer kind
        for side, key in ((me, "d"), (op, "od")):
            for a, b in PHASES:
                for ctx in ("champion", "camp"):
                    r[f"{key}_{ctx}_{a}"] = sum(1 for o, x in ev["death"] if o["team"] == side and x["context"] == ctx
                                                 and a <= x["timestamp"]["round"] < b)
        r["kills_by"] = collections.Counter(o["name"] for o, x in ev["kill"] if o["team"] == me)
        r["kill_pairs"] = collections.Counter(f'{o["name"]}>{x["target"]["name"]}' for o, x in ev["kill"] if o["team"] == me)
        r["death_pairs"] = collections.Counter(f'{o["name"]}>{x["target"]["name"]}' for o, x in ev["kill"] if o["team"] == op)
        r["first_blood"] = None
        kills = sorted((x["timestamp"]["ordinal"], o["team"]) for o, x in ev["kill"])
        if kills:
            r["first_blood"] = "me" if kills[0][1] == me else "op"
            r["first_blood_round"] = next(x["timestamp"]["round"] for o, x in ev["kill"] if x["timestamp"]["ordinal"] == kills[0][0])
        # shop: first purchase round per champion, final emblems
        first_buy = {}
        for o, x in ev["buyItem"]:
            if o["team"] == me:
                first_buy[o["id"]] = min(first_buy.get(o["id"], 9999), x["timestamp"]["round"])
        r["first_buy"] = {champs[i]["name"]: v for i, v in first_buy.items()}
        r["emblems"] = {c["name"]: [it["item"] for it in c["items"] if "Emblem" in it["item"]]
                        for c in s["champions"] if c["team"] == me}
        r["consumables"] = collections.Counter(x["target"]["name"] for o, x in ev["buyConsumable"] if o["team"] == me)
        r["fuel_ex"] = sum(1 for o, x in ev["fuelExhausted"] if (o.get("team") if isinstance(o, dict) else None) == me)
        r["camp_clears"] = sum(1 for o, x in ev["campClear"] if o.get("team") == me)
        r["champ_stats"] = {c["name"]: {k: float(v) for k, v in c["metrics"].items()} for c in s["champions"] if c["team"] == me}
        r["eng"] = [dict(e, me_first=(e["first"] == me), n_me=e["n"][me], n_op=e["n"][op],
                         k_me=e["k"][me], k_op=e["k"][op]) for e in engagements]
        for e in r["eng"]:
            for k in ("first", "n", "k"):
                e.pop(k, None)
        rows.append(r)
    return rows


def find_engagements(s, ctl, champs, gap=6):
    """Fights = runs of rounds where some champion deals champion damage, split by gaps > `gap` rounds.

    For each: start round, the team that dealt the first damage, bodies of each team that dealt or took champion
    damage, kills by each team."""
    hits = []  # (round, team, champion id, kind)
    for i, c in champs.items():
        for metric, kind in (("championDamageDone", "dealt"), ("championDamageTaken", "took")):
            vals = expand(ctl[i].get(metric, []))
            for rd in range(1, len(vals)):
                if vals[rd] > vals[rd - 1]:
                    hits.append((rd, c["team"], i, kind))
    hits.sort()
    kills = []
    for e in s["events"]:
        if e["kind"] == "kill":
            for x in e["entries"]:
                kills.append((x["timestamp"]["round"], e["owner"]["team"]))
    out, cur = [], []
    for h in hits + [(10 ** 9, None, None, None)]:
        if cur and h[0] - cur[-1][0] > gap:
            a, b = cur[0][0], cur[-1][0]
            dealt = [x for x in cur if x[3] == "dealt"]
            n = {t: len({x[2] for x in cur if x[1] == t}) for t in ("teamA", "teamB")}
            k = {t: sum(1 for kr, kt in kills if kt == t and a <= kr <= b + 1) for t in ("teamA", "teamB")}
            out.append(dict(r0=a, r1=b, first=dealt[0][1] if dealt else None, n=n, k=k))
            cur = []
        cur.append(h)
    return out


def build_rows():
    metas = {}
    for f in glob.glob(f"{ROOT}/lists/*.json"):
        for m in json.load(open(f)):
            metas[m["matchId"]] = m
    out = open(ROWS, "w")
    n = 0
    for f in sorted(glob.glob(f"{ROOT}/summaries/*.json")):
        mid = os.path.basename(f)[:-5]
        if mid not in metas:
            continue
        s = json.load(open(f))
        for r in game_rows(metas[mid], s):
            out.write(json.dumps(r) + "\n")
            n += 1
    print(f"{n} rows -> {ROWS}")


# ---------------------------------------------------------------- report helpers
def pct(a, b):
    return f"{100 * a / b:.0f} %" if b else "-"


def mean(xs):
    xs = [x for x in xs if x is not None]
    return statistics.mean(xs) if xs else float("nan")


def med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else float("nan")


def wilson(k, n):
    if not n:
        return (0, 0)
    z, p = 1.96, k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (100 * (c - h), 100 * (c + h))


def load(last=None):
    rows = [json.loads(l) for l in open(ROWS)]
    by = collections.defaultdict(list)
    for r in rows:
        by[r["team"]].append(r)
    for t in by:
        by[t].sort(key=lambda r: r["t"], reverse=True)
        if last:
            by[t] = by[t][:last]
    return by


def report(last=100):
    by = load(last)
    P = print
    P(f"Sample: each team's last {last} ranked 5.0 games with a summary.\n")
    for t in TEAMS:
        rs = by[t]
        P(f"{SHORT[t]}: n={len(rs)}, {rs[-1]['t'][:16]} .. {rs[0]['t'][:16]}")
    P()
    # 1. endings
    P("## Endings\n")
    P("| Team | n | Win % (95 % CI) | win by 1,000 gems | win at r2000 | median end round (wins) | median margin (wins) | loss by 1,000 | median end (losses) | median margin (losses) | our gems in losses |")
    P("|---|---|---|---|---|---|---|---|---|---|---|")
    for t in TEAMS:
        rs = by[t]; W = [r for r in rs if r["result"] == "win"]; L = [r for r in rs if r["result"] == "loss"]
        lo, hi = wilson(len(W), len(rs))
        P(f"| {SHORT[t]} | {len(rs)} | {pct(len(W), len(rs))} ({lo:.0f}-{hi:.0f}) | {pct(sum(r['end']=='gems' for r in W), len(W))} | "
          f"{pct(sum(r['end']!='gems' for r in W), len(W))} | {med([r['rounds'] for r in W]):.0f} | {med([r['gems']-r['ogems'] for r in W]):.0f} | "
          f"{pct(sum(r['end']=='gems' for r in L), len(L))} | {med([r['rounds'] for r in L]):.0f} | {med([r['gems']-r['ogems'] for r in L]):.0f} | {med([r['gems'] for r in L]):.0f} |")
    P("\nEnd reasons:", {SHORT[t]: dict(collections.Counter(r['end'] for r in by[t])) for t in TEAMS})
    # by opponent
    P("\n## Results by opponent (summary sample)\n")
    for t in TEAMS:
        c = collections.defaultdict(lambda: [0, 0])
        for r in by[t]:
            c[r["opp"]][0] += r["result"] == "win"; c[r["opp"]][1] += 1
        P(f"- {SHORT[t]}: " + ", ".join(f"{o[:14]} {w}/{n}" for o, (w, n) in sorted(c.items(), key=lambda x: -x[1][1])))
    # 2. draft
    P("\n## Draft\n")
    for t in TEAMS:
        rs = by[t]
        pk = collections.Counter(p for r in rs for p in r["picks"])
        size = collections.Counter(len(r["picks"]) for r in rs)
        first = collections.Counter(r["picks"][0] for r in rs)
        comps = collections.Counter(" / ".join(r["picks"]) for r in rs)
        P(f"**{SHORT[t]}** (n={len(rs)}): team size {dict(sorted(size.items()))}; pick rate " +
          ", ".join(f"{k} {pct(v, len(rs))}" for k, v in pk.most_common()))
        P(f"  first pick: {dict(first.most_common())}")
        P("  comps: " + "; ".join(f"{k} ({v}, win {pct(sum(r['result']=='win' for r in rs if ' / '.join(r['picks'])==k), v)})" for k, v in comps.most_common(6)))
    P("\nEmblems on each champion at the end (share of that champion's games):")
    for t in TEAMS:
        em = collections.defaultdict(collections.Counter); nch = collections.Counter()
        for r in by[t]:
            for ch, es in r["emblems"].items():
                nch[ch] += 1
                for e in set(es):
                    em[ch][e] += 1
        P(f"- {SHORT[t]}: " + " | ".join(f"{ch} (n={nch[ch]}): " + ", ".join(f"{e.replace(' Emblem of ', ' ')} {pct(v, nch[ch])}" for e, v in em[ch].most_common(4))
                                     for ch in sorted(nch, key=lambda c: -nch[c])))
    P("\nFirst shop round (median per champion):")
    for t in TEAMS:
        fb = collections.defaultdict(list)
        for r in by[t]:
            for ch, v in r["first_buy"].items():
                fb[ch].append(v)
        P(f"- {SHORT[t]}: " + ", ".join(f"{ch} r{med(v):.0f}" for ch, v in sorted(fb.items(), key=lambda x: med(x[1]))))
    P("\nConsumables bought per game:", {SHORT[t]: {k: round(sum(r['consumables'].get(k, 0) for r in by[t]) / len(by[t]), 2)
                                              for k in sorted({k for r in by[t] for k in r['consumables']})} for t in TEAMS})
    # 3. tempo
    P("\n## Tempo\n")
    P("| Team | " + " | ".join(f"gems r{c} (us-them)" for c in CHECK) + " |")
    P("|---|" + "---|" * len(CHECK))
    for t in TEAMS:
        rs = by[t]
        P(f"| {SHORT[t]} | " + " | ".join(f"{med([r[f'g{c}'] for r in rs]):.0f}-{med([r[f'og{c}'] for r in rs]):.0f}" for c in CHECK) + " |")
    P("\nTributed-gem lead at round R -> win rate of the side ahead (ties dropped), all three teams' games pooled per team:")
    for t in TEAMS:
        rs = by[t]; parts = []
        for c in CHECK:
            ahead = [r for r in rs if r[f"g{c}"] != r[f"og{c}"]]
            k = sum((r[f"g{c}"] > r[f"og{c}"]) == (r["result"] == "win") for r in ahead)
            parts.append(f"r{c}: {pct(k, len(ahead))} (n={len(ahead)}, {SHORT[t]} ahead {pct(sum(r[f'g{c}'] > r[f'og{c}'] for r in ahead), len(ahead))})")
        P(f"- {SHORT[t]}: " + "; ".join(parts))
    P("\nCollected gems (bags, not yet tributed) and gold earned, medians, us-them:")
    for t in TEAMS:
        rs = by[t]
        P(f"- {SHORT[t]}: " + "; ".join(f"r{c} gold {med([r[f'gold{c}'] for r in rs]):.0f}-{med([r[f'ogold{c}'] for r in rs]):.0f}, gems {med([r[f'coll{c}'] for r in rs]):.0f}-{med([r[f'ocoll{c}'] for r in rs]):.0f}" for c in (150, 300, 600)))
    P("\nAhead on collected gems at r300 -> win rate (ties dropped); and on gold at r300:")
    for t in TEAMS:
        rs = by[t]
        for key in ("coll300", "gold300"):
            ahead = [r for r in rs if r[key] != r["o" + key]]
            k = sum((r[key] > r["o" + key]) == (r["result"] == "win") for r in ahead)
            P(f"- {SHORT[t]} {key}: side ahead wins {pct(k, len(ahead))} (n={len(ahead)}); {SHORT[t]} ahead in {pct(sum(r[key] > r['o'+key] for r in ahead), len(ahead))}")
    P("\nFirst tribute round (median), tributes per game, mean tribute size:")
    for t in TEAMS:
        rs = by[t]
        P(f"- {SHORT[t]}: first r{med([r['first_tribute'] for r in rs]):.0f}, {mean([r['tributes'] for r in rs]):.1f} tributes, {mean([r['bag_mean'] for r in rs]):.0f} gems each")
    # 4. gem sources
    P("\n## Where the gems come from\n")
    P("| Team | games | captured | bags taken (kills) | bag share | own gems lost to champions | to camps | enemy gems destroyed by camps |")
    P("|---|---|---|---|---|---|---|---|")
    for t in TEAMS:
        for lab, rs in (("all", by[t]), ("wins", [r for r in by[t] if r["result"] == "win"]), ("losses", [r for r in by[t] if r["result"] == "loss"])):
            cap, bag = mean([r["cap"] for r in rs]), mean([r["bag"] for r in rs])
            P(f"| {SHORT[t]} {lab} | {len(rs)} | {cap:.0f} | {bag:.0f} | {100*bag/(cap+bag):.0f} % | {mean([r['lost_me_champion'] for r in rs]):.0f} | {mean([r['lost_me_camp'] for r in rs]):.0f} | {mean([r['lost_op_camp'] for r in rs]):.0f} |")
    P("\nWin rate by bag-swing (bags we took - bags we lost to champions) tercile:")
    for t in TEAMS:
        rs = sorted(by[t], key=lambda r: r["bag"] - r["lost_me_champion"]); n = len(rs)
        parts = []
        for i in range(3):
            q = rs[i * n // 3:(i + 1) * n // 3]
            parts.append(f"swing {q[0]['bag']-q[0]['lost_me_champion']}..{q[-1]['bag']-q[-1]['lost_me_champion']}: win {pct(sum(r['result']=='win' for r in q), len(q))}")
        P(f"- {SHORT[t]}: " + "; ".join(parts))
    P("\nWin rate by capture-margin (our captured - their captured) tercile: (their captured = gems collected minus bags)")
    # 5. fights
    P("\n## Fights\n")
    P("| Team | deaths r0-300 (champ/camp) | r300-1000 | r1000+ | enemy deaths r0-300 | r300-1000 | r1000+ | first blood ours | median first-blood round |")
    P("|---|---|---|---|---|---|---|---|---|")
    for t in TEAMS:
        rs = by[t]
        cells = [f"{mean([r[f'{k}_champion_{a}'] for r in rs]):.1f}/{mean([r[f'{k}_camp_{a}'] for r in rs]):.1f}" for k in ("d", "od") for a, _ in PHASES]
        fb = [r for r in rs if r["first_blood"]]
        P(f"| {SHORT[t]} | " + " | ".join(cells) + f" | {pct(sum(r['first_blood']=='me' for r in fb), len(fb))} | {med([r.get('first_blood_round') for r in fb]):.0f} |")
    P("\nFirst blood -> win rate of the side that drew it:", {SHORT[t]: pct(sum((r['first_blood']=='me') == (r['result']=='win') for r in by[t] if r['first_blood']), sum(1 for r in by[t] if r['first_blood'])) for t in TEAMS})
    P("\nEngagements (champion-damage clusters, gap > 6 rounds splits): per game, who deals the first hit, numbers, kills.")
    for t in TEAMS:
        E = [e for r in by[t] for e in r["eng"]]
        bloody = [e for e in E if e["k_me"] + e["k_op"] > 0]
        first = [e for e in bloody]
        P(f"- {SHORT[t]}: {len(E)/len(by[t]):.1f} engagements/game, {len(bloody)/len(by[t]):.1f} with a kill. In bloody ones: {SHORT[t]} hits first {pct(sum(e['me_first'] for e in first), len(first))}; "
          f"kills {sum(e['k_me'] for e in bloody)} v {sum(e['k_op'] for e in bloody)}; kill ratio when hitting first {sum(e['k_me'] for e in bloody if e['me_first'])}:{sum(e['k_op'] for e in bloody if e['me_first'])}, when hit first {sum(e['k_me'] for e in bloody if not e['me_first'])}:{sum(e['k_op'] for e in bloody if not e['me_first'])}")
        nd = collections.defaultdict(lambda: [0, 0, 0])
        for e in bloody:
            d = max(-2, min(2, e["n_me"] - e["n_op"]))
            nd[d][0] += e["k_me"]; nd[d][1] += e["k_op"]; nd[d][2] += 1
        P("    by body difference (us - them, clipped ±2): " + ", ".join(f"{d:+d}: n={v[2]} kills {v[0]}:{v[1]}" for d, v in sorted(nd.items())))
        ph = collections.defaultdict(lambda: [0, 0])
        for e in bloody:
            p = 0 if e["r0"] < 300 else (1 if e["r0"] < 1000 else 2)
            ph[p][0] += e["k_me"]; ph[p][1] += e["k_op"]
        P("    kills by phase (r0-300, r300-1000, r1000+): " + ", ".join(f"{v[0]}:{v[1]}" for p, v in sorted(ph.items())))
    P("\nKills and deaths per champion per game (K/D), and the commonest kill pairs:")
    for t in TEAMS:
        rs = by[t]; kd = collections.defaultdict(lambda: [0, 0, 0])
        for r in rs:
            for ch, st in r["champ_stats"].items():
                kd[ch][0] += st["kills"]; kd[ch][1] += st["deaths"]; kd[ch][2] += 1
        P(f"- {SHORT[t]}: " + ", ".join(f"{ch} {v[0]/v[2]:.1f}/{v[1]/v[2]:.1f}" for ch, v in sorted(kd.items(), key=lambda x: -x[1][2])))
        kp = collections.Counter(); dp = collections.Counter()
        for r in rs:
            kp.update(r["kill_pairs"]); dp.update(r["death_pairs"])
        P(f"    kills: {kp.most_common(6)}; died to: {dp.most_common(6)}")
    P("\nPer-champion economy (mean per game): gold earned, gems submitted, monster damage, champion damage:")
    for t in TEAMS:
        rs = by[t]; st = collections.defaultdict(lambda: collections.defaultdict(float)); nn = collections.Counter()
        for r in rs:
            for ch, m in r["champ_stats"].items():
                nn[ch] += 1
                for k in ("earnedGold", "submittedGems", "collectedGems", "monsterDamageDone", "championDamageDone"):
                    st[ch][k] += m[k]
        P(f"- {SHORT[t]}: " + "; ".join(f"{ch} gold {st[ch]['earnedGold']/nn[ch]:.0f}, coll {st[ch]['collectedGems']/nn[ch]:.0f}, sub {st[ch]['submittedGems']/nn[ch]:.0f}, mon {st[ch]['monsterDamageDone']/nn[ch]/1000:.0f}k, champ {st[ch]['championDamageDone']/nn[ch]/1000:.1f}k" for ch in sorted(nn, key=lambda c: -nn[c])))
    # 6. exploitable
    P("\n## Weak spots\n")
    for t in TEAMS:
        rs = by[t]
        sz = collections.defaultdict(lambda: [0, 0])
        for r in rs:
            a = r["w"] * r["h"]; b = "small <2k" if a < 2000 else ("mid 2-4k" if a < 4000 else "big 4k+")
            sz[b][0] += r["result"] == "win"; sz[b][1] += 1
        side = collections.defaultdict(lambda: [0, 0])
        for r in rs:
            side[r["side"]][0] += r["result"] == "win"; side[r["side"]][1] += 1
        ts = collections.defaultdict(lambda: [0, 0])
        for r in rs:
            ts[len(r["picks"])][0] += r["result"] == "win"; ts[len(r["picks"])][1] += 1
        ots = collections.defaultdict(lambda: [0, 0])
        for r in rs:
            ots[len(set(r["odraft"]) - {"Issac"}) if "Cassi" in r["odraft"] else len(r["odraft"])][0] += r["result"] == "win"; ots[len(set(r["odraft"]) - {"Issac"}) if "Cassi" in r["odraft"] else len(r["odraft"])][1] += 1
        P(f"- {SHORT[t]}: by map area " + ", ".join(f"{k} {v[0]}/{v[1]}" for k, v in sorted(sz.items())) +
          "; by side " + ", ".join(f"{k} {v[0]}/{v[1]}" for k, v in sorted(side.items())) +
          "; by own team size " + ", ".join(f"{k} {v[0]}/{v[1]}" for k, v in sorted(ts.items())) +
          f"; fuel-exhausted turns/game {mean([r['fuel_ex'] for r in rs]):.1f}; bot faults {sum(r['faults'] for r in rs)}")
        mp = collections.defaultdict(lambda: [0, 0])
        for r in rs:
            mp[r["map"]][0] += r["result"] == "win"; mp[r["map"]][1] += 1
        bad = sorted([(v[0] / v[1], m, v) for m, v in mp.items() if v[1] >= 2])[:8]
        P(f"    worst maps (>=2 games): " + ", ".join(f"{m} {v[0]}/{v[1]}" for _, m, v in bad))


if __name__ == "__main__":
    if sys.argv[1:2] == ["rows"]:
        build_rows()
    elif sys.argv[1:2] == ["report"]:
        report(int(sys.argv[2]) if len(sys.argv) > 2 else 100)
    else:
        sys.exit(__doc__)
