"""Micro numbers of both bots in an arena run (docs/redo/07_MICRO.md section 11).

    python3 -I tools/microstats.py runs/arena/<A>-vs-<B>-<time>

Decodes like tools/navstats.py (shares its cache in runs/navstats/<run>/), then per bot, per game:
  deaths      Death events of the bot's champions, split by cause:
                camp     no champion credited (a monster)
                recall   an enemy kill within RECALL_W rounds of the body's Recall event (mid-recall)
                heal     an enemy kill while the body's last trace said `cur=heal` (walking home to heal)
                fight    an enemy kill while `cur=` was kill / hunt / join / hold / fall
                walk     any other enemy kill (farm, bank, shop, ... : caught on the way)
              (the `death|` trace is matched to the Death event by team, tile within 2 and round within 2: the trace
              tile is the last turn's, before its move)
  hit back    of the (body, round) pairs where an enemy champion attacked or cast on the body, the share where the body
              attacked or cast on an enemy champion in the same round
  trade       HP lost by enemy champions in rounds our champions hit them / HP we lost in rounds theirs hit us
              (HP diffs between round rows; a kill counts the victim's HP before it; monster chip in those rounds
              counts too)
  bag lost    gems carried at death, per game;  bag won: gems carried by the enemies our champions killed, per game
  carry bag   bag lost per game by the main carry (Vesper Vale, 06 section 3), the 08_FIGHT measure
  K/D         enemy champions we killed / our champions they killed (camp deaths left out)
  roll near   docs/redo/08_FIGHT.md: the share of the bot's live champion-rounds with an enemy within 3 (Chebyshev)
              that are a Turn rollover (the turn ran out of fuel: the body skips a turn); roll far = no enemy within 8
"""
import os, re, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tools", "replay"))
from navstats import decoded  # noqa: E402
import report  # noqa: E402

RECALL_W = 12
FIGHT = ("kill", "hunt", "join", "hold", "fall")
DEATH = re.compile(r"P\|(\d+)\|[AB]\|\d+\|death\|bag=\d+ pos=(\d+),(\d+) .*?cur=(\w+)")


def game_nums(d, text_by_team):
    team = report.team_of(d["champs"])
    R = d["rounds"]
    hp = defaultdict(dict)
    for row in R:
        for ch in row["champs"]:
            if ch[4]:
                hp[ch[0]][row["r"]] = ch[3]
    out = [defaultdict(float), defaultdict(float)]
    traces = [[(int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)) for m in DEATH.finditer(text_by_team[t])]
              for t in (0, 1)]
    recall = defaultdict(list)
    hits = defaultdict(set)      # (target, round) -> attackers (champions only)
    acts = set()                 # (actor, round, target team) for champion-on-champion actions
    for e in d["events"]:
        if e[1] == "Recall":
            recall[e[2]].append(e[0])
        elif e[1] in ("Attack", "Cast ability") and isinstance(e[2], int) and len(e) > 4 and e[3] == "C" \
                and isinstance(e[4], int) and team.get(e[4]) is not None and team[e[4]] != team.get(e[2]):
            hits[(e[4], e[0])].add(e[2])
            acts.add((e[2], e[0]))
    name = {c["i"]: c["name"] for c in d["champs"]}
    roll = set((e[0], e[2]) for e in d["events"] if e[1] == "Turn rollover")
    for row in R:
        live = [c for c in row["champs"] if c[4]]
        for c in live:
            dm = min([max(abs(o[1] - c[1]), abs(o[2] - c[2])) for o in live if team.get(o[0]) != team.get(c[0])] or [99])
            k = "near" if dm <= 3 else "far" if dm > 8 else None
            if k and team.get(c[0]) is not None:
                out[team[c[0]]]["r_" + k] += 1
                out[team[c[0]]]["roll_" + k] += (row["r"], c[0]) in roll
    for e in d["events"]:
        if e[1] != "Death":
            continue
        v, t = e[2], team[e[2]]
        o = out[t]
        o["deaths"] += 1
        o["bag_lost"] += e[3]
        if name.get(v) == "VesperVale":
            o["carry_bag"] += e[3]
        killers = [k for k in e[6] if team.get(k) is not None and team[k] != t]
        if not killers:
            o["d_camp"] += 1
            continue
        out[1 - t]["kills"] += 1
        out[1 - t]["bag_won"] += e[3]
        if any(0 <= e[0] - r <= RECALL_W for r in recall[v]):
            o["d_recall"] += 1
            continue
        cur = None
        for r, x, y, c in traces[t]:
            if max(abs(x - e[4]), abs(y - e[5])) <= 2 and abs(r - e[0]) <= 2:
                cur = c
                break
        if cur == "heal":
            o["d_heal"] += 1
        elif cur in FIGHT:
            o["d_fight"] += 1
        else:
            o["d_walk"] += 1
    for (v, r), _ in hits.items():
        t = team[v]
        out[t]["hit_rounds"] += 1
        out[t]["hit_back"] += (v, r) in acts
        h0 = hp[v].get(r - 1)
        if h0 is None:
            continue
        h1 = hp[v].get(r, 0.0)
        out[t]["hp_taken"] += max(0.0, h0 - h1)
        out[1 - t]["hp_dealt"] += max(0.0, h0 - h1)
    return out


def main():
    run = os.path.abspath(sys.argv[1])
    work = os.path.join(ROOT, "runs", "navstats", os.path.basename(run))
    m = re.match(r"(.+)-vs-(.+)-\d{8}-\d{6}$", os.path.basename(run))
    names = (m.group(1), m.group(2)) if m else ("first", "second")
    acc = [defaultdict(float), defaultdict(float)]
    games = [0, 0]
    for g, first, d, out, gdir, mp in decoded(run, work):
        texts = [open(os.path.join(out, "team-%s.stdout" % "ab"[t]), "rb").read().decode("utf-8", "replace") for t in (0, 1)]
        nums = game_nums(d, texts)
        for t in (0, 1):
            b = 0 if t == first else 1
            games[b] += 1
            for k, v in nums[t].items():
                acc[b][k] += v
    print("run", os.path.basename(run), "| games per bot", games)
    hdr = ("bot", "deaths/g", "camp", "fight", "walk", "heal", "recall", "hit back %", "trade", "K/D", "bag lost/g",
           "carry bag/g", "bag won/g", "roll near", "roll far")
    print(" | ".join(hdr))
    for b in (0, 1):
        a, n = acc[b], max(1, games[b])
        pg = lambda k: round(a[k] / n, 2)
        print(" | ".join(map(str, (
            names[b], pg("deaths"), pg("d_camp"), pg("d_fight"), pg("d_walk"), pg("d_heal"), pg("d_recall"),
            "%.1f%%" % (100 * a["hit_back"] / max(1, a["hit_rounds"])),
            round(a["hp_dealt"] / max(1.0, a["hp_taken"]), 2), round(a["kills"] / max(1.0, a["deaths"] - a["d_camp"]), 2),
            pg("bag_lost"), pg("carry_bag"), pg("bag_won"),
            "%.1f%%" % (100 * a["roll_near"] / max(1, a["r_near"])), "%.1f%%" % (100 * a["roll_far"] / max(1, a["r_far"]))))))


if __name__ == "__main__":
    main()
