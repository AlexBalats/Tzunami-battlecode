#!/usr/bin/env python3
"""How each side fights, from decoded replays (tools/replay/decode.mjs output).

  python3 -I tools/replay/fights.py OUR_TEAM_INDEX game1.jsonl [game2.jsonl ...]
  (OUR_TEAM_INDEX: 0 = team A, 1 = team B; or a file list "path:team" per game)

Per champion turn: actions taken (move / attack / cast / dash) and the nearest living enemy at turn start. A "fight
turn" has an enemy champion within 4 tiles (off its spawn). Reports per side and per champion type:
  attack share on fight turns, idle share, average distance to the nearest enemy, attack-then-move and
  move-then-attack patterns, focus fire (distinct champion targets per side per round), first hits, and kills
  (attackers of the victim in the 3 rounds before it died).
"""
import collections, gzip, json, sys

TYPES = ["Ryth", "Vesper", "Vendetta", "Cassi", "Issac", "Stellar", "Prism", "Marcella", "Willow", "Ren", "Varg", "Tavi", "HoR"]
RANGED = {1, 3, 5, 6, 8, 11}
MOVE, ATTACK, CAST, END = 4, 5, 6, 8


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def analyse(path, us, S):
    lines = [json.loads(l) for l in (gzip.open(path, 'rt') if path.endswith('.gz') else open(path)) if l.strip()]
    team, ty = {}, {}
    pos, hp, alive = {}, {}, {}
    spawn = {}
    turn = collections.defaultdict(list)  # actor -> actions this turn
    turn_start = {}
    last_hits = collections.defaultdict(list)  # victim -> [(round, attacker)]
    round_targets = collections.defaultdict(set)
    r_now = 0
    for x in lines:
        if x["t"] == "round":
            r_now = x["r"]
            for c in x["ch"]:
                i = c["i"]
                team[i], ty[i] = c["tm"], c["ty"]
                was = alive.get(i, 1)
                if was and not c["al"] and i in pos:
                    # a death: who hit the victim in the last 3 rounds
                    hitters = {a for (r, a) in last_hits[i] if r >= r_now - 3}
                    side = "us" if team[i] == us else "them"
                    S[side]["deaths"] += 1
                    S[side]["death_attackers"][len(hitters)] += 1
                    if hitters:
                        S["us" if side == "them" else "them"]["kills_by_group"][len(hitters)] += 1
                alive[i] = c["al"]
                hp[i] = c["hp"]
                if c["al"] and c["x"] >= 0:
                    pos[i] = (c["x"], c["y"])
                    if r_now <= 2:
                        spawn.setdefault(team[i], set()).add(pos[i])
            for side_targets in round_targets.values():
                pass
            for (side, rr), tg in list(round_targets.items()):
                if rr < r_now - 1:
                    if tg:
                        S[side]["focus_rounds"] += 1
                        S[side]["focus_targets"] += len(tg)
                    del round_targets[(side, rr)]
            continue
        a = x["a"]
        if a not in team:
            continue
        side = "us" if team[a] == us else "them"
        k = x["k"]
        if a not in turn_start:
            # turn start: nearest enemy
            me = pos.get(a)
            near = 99
            if me:
                for j, p in pos.items():
                    if team.get(j) != team[a] and alive.get(j) and min((cheb(p, s) for s in spawn.get(team[j], {(-99, -99)})), default=99) > 2:
                        near = min(near, cheb(me, p))
            turn_start[a] = (near, me, hp.get(a))
        if k == ATTACK:
            tgt = tuple(x["to"])
            victim = next((j for j, p in pos.items() if p == tgt and alive.get(j) and team.get(j) != team[a]), None)
            turn[a].append("A" if victim is not None else "a")  # A = champion target, a = camp
            if victim is not None:
                last_hits[victim].append((x["r"], a))
                round_targets[(side, x["r"])].add(victim)
        elif k == MOVE:
            turn[a].append("M")
        elif k == CAST:
            turn[a].append("C" if x.get("at") != 6 else "D")
            at = x.get("at")
            if at in (2, 3, 4, 6):  # damage, area, stun, dash (HoR's lands with damage): count as hits on champions there
                tgt = tuple(x["to"])
                rad = 0 if at in (2, 4) else 1
                for j, p in pos.items():
                    if alive.get(j) and team.get(j) != team[a] and cheb(p, tgt) <= rad:
                        last_hits[j].append((x["r"], a))
                        if at != 4:
                            round_targets[(side, x["r"])].add(j)
        if x.get("pos"):
            pos[a] = tuple(x["pos"])
        if x.get("hp") is not None:
            hp[a] = x["hp"]
        if k == END:
            near, me, h0 = turn_start.pop(a, (99, None, None))
            acts = "".join(turn.pop(a, []))
            if near <= 4 and alive.get(a):
                key = (side, TYPES[ty[a]] if 0 <= ty[a] < 13 else str(ty[a]))
                d = S["types"][key]
                d["turns"] += 1
                d["dist"] += near
                d["attack"] += "A" in acts
                d["camp"] += "a" in acts and "A" not in acts
                d["cast"] += "C" in acts
                d["idle"] += acts == ""
                d["move_only"] += set(acts) <= {"M", "D"} and acts != ""
                d["AM"] += "AM" in acts or "AD" in acts
                d["MA"] += "MA" in acts or "DA" in acts
                d["dist1"] += near <= 1
                d["dist3"] += near <= 3


def main():
    us_default = sys.argv[1]
    S = {s: dict(deaths=0, death_attackers=collections.Counter(), kills_by_group=collections.Counter(), focus_rounds=0,
                 focus_targets=0) for s in ("us", "them")}
    S["types"] = collections.defaultdict(collections.Counter)
    args = sys.argv[2:]
    if len(args) == 1 and args[0].endswith("manifest.txt"):
        args = [l.strip() for l in open(args[0]) if l.strip()]
    for arg in args:
        path, _, t = arg.rpartition(":") if ":" in arg else (arg, "", "")
        analyse(path, int(t or us_default), S)
    for side in ("us", "them"):
        s = S[side]
        print(f"{side}: deaths {s['deaths']}, attackers on our victims {dict(sorted(s['death_attackers'].items()))}, "
              f"kills by group size {dict(sorted(s['kills_by_group'].items()))}, "
              f"targets per round when hitting {s['focus_targets'] / max(1, s['focus_rounds']):.2f}")
    print("\nfight turns (enemy within 4): side type n | attack% camp% cast% idle% moveonly% | atk-then-move% move-then-atk% | dist avg, <=1 %, <=3 %")
    for (side, t), d in sorted(S["types"].items()):
        n = max(1, d["turns"])
        print(f"{side:4s} {t:9s} {d['turns']:5d} | {100*d['attack']/n:4.0f} {100*d['camp']/n:4.0f} {100*d['cast']/n:4.0f} {100*d['idle']/n:4.0f} {100*d['move_only']/n:4.0f} | "
              f"{100*d['AM']/n:4.0f} {100*d['MA']/n:4.0f} | {d['dist']/n:4.2f} {100*d['dist1']/n:4.0f} {100*d['dist3']/n:4.0f}")


if __name__ == "__main__":
    main()
