"""Carry economy of both bots in an arena run, or of us and them in ladder bundles (docs/redo/06_MACRO.md section 6).

    python3 -I tools/replay/farm/carry.py runs/arena/<A>-vs-<B>-<time>
    python3 -I tools/replay/farm/carry.py replays_from_others/<bot>        # ladder zips: first = us, second = them

Gold earned by a champion up to round r = its gold at r + what it spent by r (shop events: 30 a shard, 10 a
consumable [sdk 3.0.1]); start and passive gold are 0 [measured 20 Oct, bots/_macroprobe]. Per bot:
  share300 / share_end   the top earner's share of its team's earned gold at r300 / at the end; `main` = the main
                         carry's (VesperVale) share, when the team has her
  caps/g solo% bodies    captures per game (a round where a team's champions gain gold or gems with no kill: one
                         capture per cluster of gainers within 6 tiles), share with one recipient, mean recipients
  crew clear -> main/sec/crew/solo%   captures of groups 2+ of our bodies hit in the 60 rounds before: captured by
                         the main carry (VesperVale), the second (Ren, else Vendetta: 06 sections 7, 11), other bodies; solo share
  cap g/r                gems from captures per round (all bodies)
  emb1 main / crew       median round of the first finished emblem (main carry / other bodies; bodies without one
                         are left out, `n` counts them)
  emb/body               finished emblems per body at the end (main / others)
  gold@recall            median gold carried at a recall start; recalls per body per game (main / others)
  home                   recalls started with a Home emblem; rounds saved (2 each [rules]); broken = recall chain
                         (the replay has a Recall event each turn a recall is re-issued: one chain) not followed by
                         a spawn arrival within 6 rounds (7 without Home) of its last event
  bags lost              main carry deaths carrying gems per game, and the gems
Decoded files go to runs/carry/<run>/ (arena runs reuse runs/navstats/<run>/ when it exists).
"""
import json, os, re, statistics as st, subprocess, sys, zipfile
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from navstats import decoded  # noqa: E402

SHARD, CONS = 30, 10                     # [sdk 3.0.1] ItemType.cost(), ConsumableType.cost()
MAIN, SECOND = "VesperVale", ("Ren", "Vendetta")   # the bots' SECOND_PREF order (10_model)
CLEAR_WIN = 60                           # rounds before a capture that count as its clear


def ladder(folder, work):
    """Ladder zips: yield like navstats.decoded, `first` = our team (team-a.stdout in the bundle = team A)."""
    for f in sorted(os.listdir(folder)):
        if not f.endswith(".zip"):
            continue
        out = os.path.join(work, f[:-4])
        dec = os.path.join(out, "dec.json")
        with zipfile.ZipFile(os.path.join(folder, f)) as z:
            names = z.namelist()
            if not os.path.exists(dec):
                os.makedirs(out, exist_ok=True)
                z.extractall(out)
                subprocess.run(["node", os.path.join(ROOT, "tools/replay/decode.mjs"), os.path.join(out, "replay.repl26a"),
                                dec], cwd=ROOT, check=True, capture_output=True)
        yield f, 0 if "team-a.stdout" in names else 1, json.load(open(dec)), out, None, None


def game_nums(d):
    """Per team: a dict of this game's carry numbers."""
    team = {c["i"]: c["team"] for c in d["champs"]}
    name = {c["i"]: c["name"] for c in d["champs"]}
    R = d["rounds"]
    end = d["meta"]["endRound"] or len(R)
    spent = defaultdict(int)          # champ -> spent so far (walking the events in round order)
    spent_at = defaultdict(dict)      # champ -> round -> spent by the end of that round
    emb1 = {}
    home_from = {}
    recalls = []                      # [first round, last round, champ]: a Recall event every turn the recall is re-issued
    last_rec = {}                     # (a camp's hit interrupts it [rules]) is one recall chain
    hits = defaultdict(list)          # camp idx -> [(round, champ)]
    deaths = []
    for e in d["events"]:
        r, k = e[0], e[1]
        if k == "Shop" and len(e) >= 5:
            it = e[3]
            spent[e[2]] += CONS if it in ("Teleport crystal", "Control ward", "Altar lock", "TP scroll") else SHARD
            spent_at[e[2]][r] = spent[e[2]]
            if "Emblem" in it:
                emb1.setdefault(e[2], r)
                if it.startswith("Home"):
                    home_from.setdefault(e[2], r)
        elif k == "Recall":
            ch = last_rec.get(e[2])
            if ch is not None and r - ch[1] <= 1:
                ch[1] = r
            else:
                ch = last_rec[e[2]] = [r, r, e[2]]
                recalls.append(ch)
        elif k == "Attack" and len(e) >= 5 and e[3] == "M":
            hits[e[4]].append((r, e[2]))
        elif k == "Death":
            deaths.append(e)

    def spent_by(c, r):
        s = 0
        for rr, v in spent_at[c].items():
            if rr <= r:
                s = max(s, v)
        return s

    by_r = {x["r"]: x for x in R}
    pos = lambda c, r: next(((ch[1], ch[2]) for ch in by_r.get(r, R[-1])["champs"] if ch[0] == c), None)
    spawn = defaultdict(list)
    for ch in R[1]["champs"] if len(R) > 1 else R[0]["champs"]:
        spawn[team[ch[0]]].append((ch[1], ch[2]))
    at_spawn = lambda t, p: p is not None and any(max(abs(p[0] - s[0]), abs(p[1] - s[1])) <= 2 for s in spawn[t])

    # captures: gold or gem gains without a kill, per round and team
    caps = []                         # (round, team, [champs], gold, gems, (x, y))
    prev = None
    for x in R:
        if prev is not None:
            pm = {ch[0]: ch for ch in prev["champs"]}
            gain = defaultdict(list)
            for ch in x["champs"]:
                p = pm.get(ch[0])
                if p is None or ch[7] > p[7] or not ch[4]:
                    continue
                dg = ch[5] - p[5] + spent_by(ch[0], x["r"]) - spent_by(ch[0], prev["r"])
                dm = ch[6] - p[6]
                if dg > 0 or dm > 0:
                    gain[team[ch[0]]].append((ch[0], max(0, dg), max(0, dm), (ch[1], ch[2])))
            for t, gs in gain.items():
                while gs:                   # cluster gainers within 6 tiles: one capture each
                    c0 = gs.pop(0)
                    cl = [c0]
                    for g in gs[:]:
                        if max(abs(g[3][0] - c0[3][0]), abs(g[3][1] - c0[3][1])) <= 6:
                            cl.append(g)
                            gs.remove(g)
                    caps.append((x["r"], t, [g[0] for g in cl], sum(g[1] for g in cl), sum(g[2] for g in cl), c0[3]))
        prev = x

    scamps = d.get("scamps") or []
    out = {}
    for t in (0, 1):
        mine = [c for c in team if team[c] == t]
        main = next((c for c in mine if name[c] == MAIN), None)
        sec = next((c for s in SECOND for c in mine if name[c] == s), None)
        o = {"mine": len(mine), "main": main is not None}

        def earned(r):
            row = by_r.get(r, R[-1])
            return {ch[0]: ch[5] + spent_by(ch[0], r) for ch in row["champs"] if team[ch[0]] == t}

        for tag, r in (("300", min(300, end)), ("end", end)):
            e = earned(r)
            tot = sum(e.values())
            o["share" + tag] = max(e.values()) / tot if tot else 0
            o["main" + tag] = e.get(main, 0) / tot if tot and main is not None else None
            o["gold" + tag] = tot
        tc = [c for c in caps if c[1] == t]
        o["caps"] = len(tc)
        o["solo"] = sum(1 for c in tc if len(c[2]) == 1)
        o["bodies"] = sum(len(c[2]) for c in tc)
        o["capgems"] = sum(c[4] for c in tc)
        o["end"] = end
        cc = defaultdict(int)
        for r, _, who, g, m, p in tc:
            near = [s for s in scamps if max(abs(s[2] - p[0]), abs(s[3] - p[1])) <= 2]
            hitters = set()
            for s in near:
                for rr, c in hits.get(s[0], ()):
                    if r - CLEAR_WIN <= rr <= r and team.get(c) == t:
                        hitters.add(c)
            if len(hitters) < 2:
                continue
            cc["n"] += 1
            cc["solo"] += len(who) == 1
            cc["main" if main in who else "sec" if sec in who else "crew"] += 1
        o["cc"] = dict(cc)
        o["emb1_main"] = emb1.get(main) if main is not None else None
        o["emb1_crew"] = [emb1[c] for c in mine if c != main and c in emb1]
        o["emb1_none"] = sum(1 for c in mine if c != main and c not in emb1)
        fin = {c["i"]: c["items"] for c in d["champs"]}
        nemb = lambda c: sum(v for k, v in fin.get(c, {}).items() if "Emblem" in k)
        o["emb_main"] = nemb(main) if main is not None else None
        o["emb_crew"] = [nemb(c) for c in mine if c != main]
        rg = []
        nrec = defaultdict(int)
        home = saved = broken = 0
        for r, r1, c in recalls:
            if team.get(c) != t:
                continue
            nrec["main" if c == main else "crew"] += 1
            row = by_r.get(r)
            if row:
                g = next((ch[5] for ch in row["champs"] if ch[0] == c), None)
                if g is not None:
                    rg.append(g)
            hm = c in home_from and home_from[c] <= r
            home += hm
            saved += 2 * hm
            lim = 6 if hm else 7
            if not any(at_spawn(t, pos(c, r1 + k)) for k in range(1, lim + 1)):
                broken += 1
        o["rgold"], o["rec_main"], o["rec_crew"] = rg, nrec["main"], nrec["crew"]
        o["home"], o["saved"], o["broken"] = home, saved, broken
        bl = [e for e in deaths if e[2] == main and e[3] > 0]
        o["bags"], o["baggems"] = len(bl), sum(e[3] for e in bl)
        out[t] = o
    return out


def main():
    src = os.path.abspath(sys.argv[1])
    base = os.path.basename(src.rstrip("/"))
    nav = os.path.join(ROOT, "runs", "navstats", base)
    work = nav if os.path.isdir(nav) else os.path.join(ROOT, "runs", "carry", base)
    m = re.match(r"(.+)-vs-(.+)-\d{8}-\d{6}$", base)
    if m:
        names, games = (m.group(1), m.group(2)), decoded(src, work)
    else:
        names, games = (base + " (us)", "opponents"), ladder(src, work)
    acc = [defaultdict(list), defaultdict(list)]
    for g, first, d, *_ in games:
        nums = game_nums(d)
        for t in (0, 1):
            acc[0 if t == first else 1]["g"].append(nums[t])
    med = lambda v: round(st.median(v), 2) if v else "-"
    mean = lambda v: round(st.mean([x for x in v if x is not None]), 2) if any(x is not None for x in v) else "-"   # None: no team gold yet
    print("source", base)
    hdr = ("bot", "games", "share300", "shareend", "main300", "mainend", "gold300", "goldend", "caps/g", "solo%",
           "bodies", "crew clear main/sec/crew", "cc solo%", "cap g/r", "emb1 main", "emb1 crew (n none)",
           "emb/body main", "emb/body crew", "gold@recall", "rec/body main", "rec/body crew", "home rec/g", "saved r/g",
           "broken/g", "bags lost/g", "bag gems/g")
    print(" | ".join(hdr))
    for b in (0, 1):
        G = acc[b]["g"]
        n = max(1, len(G))
        mains = [o for o in G if o["main"]]
        cc = defaultdict(int)
        for o in G:
            for k, v in o["cc"].items():
                cc[k] += v
        caps = sum(o["caps"] for o in G)
        crew_bodies = sum(o["mine"] - o["main"] for o in G)
        row = (names[b], len(G), mean([o["share300"] for o in G]), mean([o["shareend"] for o in G]),
               mean([o["main300"] for o in mains]), mean([o["mainend"] for o in mains]),
               round(mean([o["gold300"] for o in G])), round(mean([o["goldend"] for o in G])),
               round(caps / n, 1), "%.0f%%" % (100 * sum(o["solo"] for o in G) / max(1, caps)),
               round(sum(o["bodies"] for o in G) / max(1, caps), 2),
               "%d/%d/%d" % (cc["main"], cc["sec"], cc["crew"]), "%.0f%%" % (100 * cc["solo"] / max(1, cc["n"])),
               round(sum(o["capgems"] for o in G) / max(1, sum(o["end"] for o in G)), 3),
               med([o["emb1_main"] for o in mains if o["emb1_main"] is not None]),
               "%s (%d)" % (med([x for o in G for x in o["emb1_crew"]]), sum(o["emb1_none"] for o in G)),
               mean([o["emb_main"] for o in mains]), mean([x for o in G for x in o["emb_crew"]]),
               med([x for o in G for x in o["rgold"]]),
               round(sum(o["rec_main"] for o in mains) / max(1, len(mains)), 1),
               round(sum(o["rec_crew"] for o in G) / max(1, crew_bodies), 1),
               round(sum(o["home"] for o in G) / n, 1), round(sum(o["saved"] for o in G) / n, 1),
               round(sum(o["broken"] for o in G) / n, 1),
               round(sum(o["bags"] for o in mains) / max(1, len(mains)), 2),
               round(sum(o["baggems"] for o in mains) / max(1, len(mains)), 1))
        print(" | ".join(map(str, row)))


if __name__ == "__main__":
    main()
