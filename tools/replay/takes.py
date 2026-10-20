"""Takes table from decoded replays: per clear, the group type/HP/gems, the clearing team, bodies, rounds."""
import json, sys, os, statistics
from collections import defaultdict, Counter
sys.path.insert(0, os.path.join(os.getcwd(), "tools", "replay"))
import report  # noqa

rows = []
for path in sys.argv[1:]:
    d = json.load(open(path))
    comps = report.full_groups(d["scamps"])
    gem_of = report.half_group_gems(d, comps)
    team = report.team_of(d["champs"])
    name = {c["i"]: c["name"] for c in d["champs"]}
    camp_g = {c: g for g, cs in enumerate(comps) for c in cs}
    hp0 = d["rounds"][1]["campHp"]
    ghp = [sum(hp0[c] for c in cs) for cs in comps]
    gtype = ["+".join(sorted({d["scamps"][c][1] for c in cs})) for cs in comps]
    hits = defaultdict(list)            # g -> [(r, actor)] since last clear
    clear_r = {}
    for e in d["events"]:
        r, k = e[0], e[1]
        if k in ("Attack", "Cast ability") and e[3] == "M" and isinstance(e[2], int) and e[4] in camp_g:
            hits[camp_g[e[4]]].append((r, e[2]))
        elif k == "Group":
            g, rb, ra, cb, ca = e[2], e[3], e[4], e[5], e[6]
            if not rb and ra:
                h = hits.pop(g, [])
                if not h:
                    continue
                by = Counter(team[a] for _, a in h)
                t = by.most_common(1)[0][0]
                last = h[-1][0]
                win = [x for x in h if x[0] >= last - 40]     # this attempt (ignore abandoned earlier pokes)
                bodies = {a for _, a in win if team[a] == t}
                rows.append(dict(map=d["meta"]["map"], team="AB"[t], g=g, type=gtype[g], hp=ghp[g], gem=gem_of[g],
                                 bodies=len(bodies), who=sorted(name[a] for a in bodies), start=win[0][0], clear=r,
                                 rounds=r - win[0][0] + 1, enemy_hits=sum(1 for _, a in win if team[a] != t)))
                clear_r[g] = (r, len(rows) - 1)
            if rb and not ra and g in clear_r:
                cr, i = clear_r.pop(g)
                rows[i]["cap_wait"] = r - cr
                rows[i]["capturer"] = "AB"[cb] if cb in (0, 1) else "-"

json.dump(rows, open(os.environ.get("OUT", "/dev/null"), "w"))
buckets = [("gold only", lambda x: x["gem"] == 0 and "MONOLITH" not in x["type"]),
           ("<=1000 HP gem", lambda x: x["gem"] > 0 and x["hp"] <= 1000),
           ("1001-1500", lambda x: x["gem"] > 0 and 1000 < x["hp"] <= 1500 and "ELK" not in x["type"]),
           ("1501-3000 no elk", lambda x: x["gem"] > 0 and 1500 < x["hp"] <= 3000 and "ELK" not in x["type"]),
           ("ELK groups", lambda x: "ELK" in x["type"]),
           (">3000 wolves", lambda x: x["gem"] > 0 and x["hp"] > 3000 and "ELK" not in x["type"] and "MONOLITH" not in x["type"]),
           ("MONOLITH", lambda x: "MONOLITH" in x["type"])]
print("%-18s %4s %8s %8s %8s %8s %8s  %s" % ("bucket", "n", "HP", "gems", "bodies", "rounds", "capwait", "maps"))
for lab, f in buckets:
    xs = [x for x in rows if f(x)]
    if not xs:
        continue
    md = lambda k: statistics.median([x[k] for x in xs if k in x]) if any(k in x for x in xs) else float("nan")
    print("%-18s %4d %8.0f %8.0f %8.1f %8.0f %8.0f  %s" % (lab, len(xs), md("hp"), md("gem"), statistics.mean(x["bodies"] for x in xs),
                                                 md("rounds"), md("cap_wait"), dict(Counter(x["map"] for x in xs))))
print()
for x in rows:
    if "ELK" in x["type"] or "MONOLITH" in x["type"]:
        print("  %-9s %s r%4d-%4d %-28s hp %5d gem %3d bodies %d %s capwait %s by %s enemy_hits %d" % (
            x["map"], x["team"], x["start"], x["clear"], x["type"][:28], x["hp"], x["gem"], x["bodies"], ",".join(x["who"]),
            x.get("cap_wait"), x.get("capturer"), x["enemy_hits"]))
