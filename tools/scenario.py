"""Run a bot against an opponent on every map (both sides) and score its turn trace.

Usage: python -I tools/scenario.py BOT [--opp null] [--maps lanes,rows] [--one-side] [--keep NAME] [--no-run]
                                       [--summary]

Reads trace lines from each replay's stdout (`P|round|team|champ|tag|text`; the t line is
"x,y fuel act.. k=v" (v2/tzu) or "x,y fuel=N act=<tokens> k=v" (INVARIANTS.md section 6)) and prints
per map and side: first round a champion acted, max/median fuel per turn, suspended turns (rounds with
no trace line), error turns; and for navigation (`leg` lines: "<goal> d0=<walking distance>
took=<rounds> <result>"): legs walked, share that arrived within d0+2 rounds, worst extra rounds, legs
ended "full" or "stuck", and back-and-forth steps (osc). Then these tables:
  clears  `clear` lines (S3): predicted vs actual clear rounds and damage.
  tasks   `task` lines ("<Name> <ok|fail|abort> why=.. g=.. r=.. cap=.. trib=.. carry=..") and `death`
          lines ("gems=<n> by=<camp|champ> task=<Name>"): captures, banks, gems tributed per round
          (g/r = per game round, g/r@500 = tributed by round 500 / 500, since games vs null can end
          early), deaths split by camp/champ, gems lost.
  fights  `fight|start vs=g<id>|c<id> pred_r= pred_dmg= ..` / `fight|end vs= <win|abort|died> r= dmg=`:
          per camp (g) and champion (c) fights: started, won, aborted, died, still open at game end,
          mean predicted/actual rounds and mean damage error (actual - predicted) over won fights.
  banks   `bank|start ticks=..` / `bank|end <done|broken|cancel> gems=..` and `cap|start/end/skip`.
  ints    `int|<EVENT> ..` lines counted per event.
--summary prints one line per (map, side) instead: g/r, deaths, gems lost, captures, banks, suspended
and error turns, and the invariants (tools/invariants.py) with the most violations.
Matches are deterministic, so one run per (map, side) is enough. --no-run re-scores runs/<keep>/ as is.
Needs a bot that prints a `t` line every turn (the retired tzu/v2 format). strat and tzunami-lite don't, so they show
"NO TRACE" [measured 16 Oct]: use tools/bench.py and tools/plog.py for them.
"""
import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUEL_BUDGET = 2_500_000     # per turn [rules]; the first play turn gets 2x
AT = 500                    # g/r@500 horizon: games vs null may end before round 2,000
EVENT_TAGS = ("fight", "bank", "cap", "int", "recall", "shop", "risk", "cast", "splash")
_LINES = {}


def lines_of(bundle, team):
    key = (bundle, team)
    if key not in _LINES:
        z = zipfile.ZipFile(bundle)
        name = f"team-{team.lower()}.stdout"
        if name not in z.namelist():
            _LINES[key] = []
        else:
            text = z.read(name).decode("utf-8", "replace").replace("\x00", "\n")
            _LINES[key] = [l.split("|", 5) for l in text.splitlines() if l.startswith("P|")]
    return _LINES[key]


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def inum(v, default=0):
    x = num(v)
    return default if x is None else int(x)


def kvb(text):
    """key=value fields (first wins) and the bare words, in order."""
    kv, bare = {}, []
    for w in text.split(" "):
        if "=" in w:
            k, v = w.split("=", 1)
            kv.setdefault(k, v)
        elif w:
            bare.append(w)
    return kv, bare


def score(rows):
    champs = {}
    for r in rows:
        if len(r) < 6:
            continue
        _, rnd, team, champ, tag, text = r
        try:
            rnd_i = int(rnd)
        except ValueError:
            continue
        c = champs.setdefault(champ, {"boot": None, "turns": [], "fuel": [], "acts": [], "qdone": None,
                                      "legs": [], "pos": [], "clears": [], "tasks": [], "deaths": [], "ev": {}})
        try:
            if tag == "boot":
                c["boot"] = rnd_i
            elif tag == "leg":            # "<key> d0=<dist> took=<rounds> <result>"
                f = text.split(" ")
                d0 = f[1].split("=")[-1]
                c["legs"].append((None if d0 in ("None", "-") else inum(d0), inum(f[2].split("=")[-1]), f[3]))
            elif tag == "clear":          # "<g> kind=.. pred=<r> took=<r> dpred=<d> dmg=<d> casts=n idle=a/b allies=n <res> .."
                kv = dict(x.split("=", 1) for x in text.split(" ") if "=" in x)
                res = text.split(" ")[9] if len(text.split(" ")) > 9 else "?"
                idle, turns = (int(x) for x in kv.get("idle", "0/0").split("/"))
                c["clears"].append((num(kv.get("pred")), inum(kv.get("took")), num(kv.get("dpred")),
                                    inum(kv.get("dmg")), idle, turns, inum(kv.get("allies")), res, inum(kv.get("sim"))))
            elif tag == "task":           # "<Name> <ok|fail|abort|start> why=.. g=.. r=.. cap=.. trib=.. carry=.."
                f = text.split(" ")
                kv = dict(x.split("=", 1) for x in f[2:] if "=" in x)
                c["tasks"].append((f[0], f[1] if len(f) > 1 else "", kv.get("why", ""), inum(kv.get("cap")),
                                   inum(kv.get("trib")), rnd_i))
            elif tag == "death":          # "gems=<n> by=<camp|champ> task=<Name or ->"
                kv, _ = kvb(text)
                c["deaths"].append((inum(kv.get("gems")), kv.get("task", "-"), kv.get("by", "?"), rnd_i))
            elif tag in EVENT_TAGS:       # "<verb> k=v .." (int: "<EVENT> k=v ..")
                kv, bare = kvb(text)
                c["ev"].setdefault(tag, []).append((rnd_i, kv, bare))
            elif tag == "t":              # "x,y <fuel|fuel=N> <act ..|act=..> tgt=.. q=.."
                kv, _ = kvb(text)
                parts = text.split(" ", 2)
                fuel = inum(kv["fuel"]) if "fuel" in kv else inum(parts[1] if len(parts) > 1 else 0)
                if " act=" in text:
                    act = text.split(" act=", 1)[1]
                else:
                    act = parts[2] if len(parts) > 2 else ""
                c["turns"].append(rnd_i)
                c["fuel"].append(fuel)
                c["acts"].append(act)
                c["pos"].append((parts[0], kv.get("tgt", "")))
                q = kv.get("q", "")
                if c["qdone"] is None and "/" in q and q.split("/")[0] == q.split("/")[1]:
                    c["qdone"] = rnd_i
        except (ValueError, IndexError):
            continue                  # a malformed line never stops the scoring
    out = {}
    for champ, c in champs.items():
        t = c["turns"]
        if not t:
            continue        # e.g. the draft's lines
        MOVES = ("mv", "gr", "dt", "sd")
        acted = [r for r, a in zip(t, c["acts"]) if a[:2] in MOVES]
        moved = sum(a[:2] in MOVES for a in c["acts"])
        pos = c["pos"]
        # Back-and-forth while walking to ONE target (A -> B -> A, same tgt on all three turns).
        osc = sum(1 for i in range(2, len(pos)) if pos[i] == pos[i - 2] and pos[i][0] != pos[i - 1][0]
                  and pos[i][1] == pos[i - 1][1])
        legs = c["legs"]
        timed = [(d0, took) for d0, took, res in legs if res == "here" and d0 is not None]
        fuel = sorted(c["fuel"][1:]) or [0]    # turn 1 has 2x fuel; judge the rest
        out[champ] = {
            "boot": c["boot"],
            "first_act": acted[0] if acted else None,
            "max_fuel": max(c["fuel"][1:] or [0]),     # turn 1 has 2x fuel: judged separately
            "t1_fuel": c["fuel"][0],
            "med_fuel": fuel[len(fuel) // 2],
            "suspended": (t[-1] - t[0] + 1 - len(t)) if t else None,
            "errors": sum(a.startswith("err") for a in c["acts"]),
            "last": c["acts"][-1] if c["acts"] else "-",
            "qdone": c["qdone"],
            "moved": moved / max(1, len(t)),
            "osc": osc,
            "legs": len(legs),
            "ontime": sum(took <= d0 + 2 for d0, took in timed),
            "timed": len(timed),
            "extra": max((took - d0 for d0, took in timed), default=0),
            "full": sum(res == "full" for _, _, res in legs),
            "stuck": sum(res == "stuck" for _, _, res in legs),
            "died": sum(res == "died" for _, _, res in legs),
            "clears": c["clears"],
            "tasks": c["tasks"],
            "deaths": c["deaths"],
            "ev": c["ev"],
        }
    return out


def game(rep, side):
    """(per-champion scores, game end round) of one replay side."""
    rows = lines_of(rep, side)
    end = max((inum(r[1]) for r in rows if len(r) >= 6), default=0)
    return score(rows), end


def evs(s, tag, verb=None):
    """Team-wide event lines (round, champ, kv, bare) of one tag, by round; verb = first bare word."""
    out = [(e[0], ch, e[1], e[2]) for ch, x in s.items() for e in x["ev"].get(tag, [])
           if verb is None or e[2][:1] == [verb]]
    return sorted(out, key=lambda e: e[0])


def trib_events(s):
    """(round, gems) tributed: from task trib=, or from bank|end gems= when no task carries trib."""
    t = [(task[5], task[4]) for x in s.values() for task in x["tasks"] if task[4]]
    if t:
        return t
    return [(r, inum(kv.get("gems"))) for r, _, kv, _ in evs(s, "bank", "end")]


def top_why(ws, k=3):
    n = {}
    for w in ws:
        w = (w or "-").split(":")[0] or "-"
        n[w] = n.get(w, 0) + 1
    return " ".join(f"{w}:{c}" for w, c in sorted(n.items(), key=lambda wc: -wc[1])[:k])


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def fmt(v, spec, width):
    return f"{'-':>{width}}" if v is None else f"{v:{width}{spec}}"


def nav_row(s):
    v = list(s.values())
    qd = [x["qdone"] for x in v]
    timed = sum(x["timed"] for x in v)
    return {
        "boot": max((x["boot"] or 0) for x in v), "first": max((x["first_act"] or 9999) for x in v),
        "maxf": max(x["max_fuel"] for x in v), "t1": max(x["t1_fuel"] for x in v),
        "medf": max(x["med_fuel"] for x in v), "susp": sum(x["suspended"] or 0 for x in v),
        "err": sum(x["errors"] for x in v), "legs": sum(x["legs"] for x in v),
        "ontime": sum(x["ontime"] for x in v) / max(1, timed), "extra": max(x["extra"] for x in v),
        "full": sum(x["full"] for x in v), "stuck": sum(x["stuck"] for x in v),
        "osc": sum(x["osc"] for x in v), "died": sum(x["died"] for x in v),
        "fields": "-" if all(q is None for q in qd) else ("never" if None in qd else max(qd)),
        "moved": min(x["moved"] for x in v),
    }


def flagged(n):
    return not (n["susp"] == 0 and n["err"] == 0 and n["maxf"] < FUEL_BUDGET and n["t1"] < 2 * FUEL_BUDGET)


def clear_table(games):
    """S3: predicted vs actual clear rounds and damage, solo clears only (allies=0)."""
    rows = []
    for m, side, rep in games:
        if not os.path.exists(rep):
            continue
        for champ, x in score(lines_of(rep, side)).items():
            for cl in x["clears"]:
                rows.append((m, side, champ) + cl)
    if not rows:
        return
    print("\nclears (solo = no ally next to the camp at the end)")
    print(f"{'map':10} {'side':4} {'clears':>6} {'solo':>4} {'ttk err%':>8} {'worst':>6} {'dmg err':>7} "
          f"{'idle':>9} {'died':>4} {'abort':>5} {'simfuel':>8}")
    for m, side, _ in games:
        rs = [r for r in rows if r[0] == m and r[1] == side]
        if not rs:
            print(f"{m:10} {side:4} {0:6}")
            continue
        solo = [r for r in rs if r[9] == 0 and r[10] == "done" and r[3] is not None]
        errs = [abs(r[4] - r[3]) / max(1, r[4]) for r in solo]
        derr = [r[6] - r[5] for r in solo if r[5] is not None]
        idle = sum(r[7] for r in rs)
        turns = sum(r[8] for r in rs)
        print(f"{m:10} {side:4} {len(rs):6} {len(solo):4} {(sum(errs) / max(1, len(errs))):8.1%} "
              f"{max(errs, default=0):6.0%} {(sum(derr) / max(1, len(derr))):7.0f} "
              f"{idle:4}/{turns:<4} {sum(r[10] == 'died' for r in rs):4} {sum(r[10] == 'abort' for r in rs):5} "
              f"{max(r[11] for r in rs):8,}")


def task_row(s, end):
    ts = [t for x in s.values() for t in x["tasks"]]
    ds = [d for x in s.values() for d in x["deaths"]]
    cc = [t for t in ts if t[0] == "ClearCamp"]
    tr = trib_events(s)
    trib = sum(g for _, g in tr)
    return {"caps": sum(t[1] == "ok" for t in cc), "capgems": sum(t[3] for t in ts),
            "banks": sum(t[0] == "Bank" and t[1] == "ok" for t in ts), "trib": trib,
            "gr": trib / max(1, end), "gr500": sum(g for r, g in tr if r <= AT) / AT, "end": end,
            "deaths": len(ds), "camp_d": sum(d[2] == "camp" for d in ds),
            "champ_d": sum(d[2] == "champ" for d in ds), "lost": sum(d[0] for d in ds),
            "cc_fail": sum(t[1] == "fail" for t in cc), "cc_abort": sum(t[1] == "abort" for t in cc),
            "top": top_why(t[2] for t in ts if t[1] in ("fail", "abort"))}


# (key, header, format, width); deaths not tagged by= count in neither camp_deaths nor champ_deaths
TASK_COLS = [("caps", "caps", "d", 4), ("capgems", "capgems", "d", 7), ("banks", "banks", "d", 5),
             ("trib", "trib", "d", 5), ("gr", "g/r", ".2f", 5), ("gr500", "g/r@500", ".2f", 7),
             ("end", "end", "d", 5), ("deaths", "deaths", "d", 6), ("camp_d", "camp_deaths", "d", 11),
             ("champ_d", "champ_deaths", "d", 12), ("lost", "lostgems", "d", 8), ("cc_fail", "cc_fail", "d", 7),
             ("cc_abort", "cc_abort", "d", 8)]
MEANED = ("gr", "gr500", "end")       # the TOTAL row shows the mean for these


def task_table(games):
    """S4: what the task layer achieved per (map, side), team totals."""
    print(f"\ntasks (g/r = gems tributed / game length; g/r@500 = tributed by round {AT} / {AT}; "
          "top why = commonest fail/abort reasons, detail after ':' dropped)")
    print(f"{'map':10} {'side':4} " + " ".join(f"{h:>{w}}" for _, h, _, w in TASK_COLS) + "  top why")
    tot, worst = [], None
    for m, side, rep in games:
        if not os.path.exists(rep):
            continue
        row = task_row(*game(rep, side))
        tot.append(row)
        if worst is None or row["gr"] < worst[2]:
            worst = (m, side, row["gr"], row["gr500"])
        print(f"{m:10} {side:4} " + " ".join(f"{row[k]:{w}{sp}}" for k, _, sp, w in TASK_COLS) + f"  {row['top']}")
    if not tot:
        return
    n = len(tot)
    s = {k: sum(r[k] for r in tot) for k, _, _, _ in TASK_COLS}
    total = []
    for k, _, sp, w in TASK_COLS:
        total.append(f"{s[k] / n:{w}.0f}" if k == "end" else (f"{s[k] / n:{w}{sp}}" if k in MEANED else f"{s[k]:{w}{sp}}"))
    print(f"{'TOTAL':10} {'':4} " + " ".join(total) + f"  (g/r, g/r@500, end = mean over {n} games)")
    means = []
    for k, _, sp, w in TASK_COLS:
        means.append(f"{s[k] / n:{w}.0f}" if k == "end" else f"{s[k] / n:{w}.{2 if sp == '.2f' else 1}f}")
    print(f"{'mean':10} {'':4} " + " ".join(means))
    print(f"worst: {worst[0]} {worst[1]} g/r={worst[2]:.2f} g/r@500={worst[3]:.2f}")


def fight_stats(s):
    st = {k: {"start": 0, "win": 0, "abort": 0, "died": 0, "open": 0, "pr": [], "ar": [], "derr": []}
          for k in ("g", "c")}
    kind = lambda vs: "c" if vs.startswith("c") else "g"        # vs=g<id> camp, vs=c<id> champion
    open_ = {}
    for rnd, ch, kv, bare in evs(s, "fight"):
        verb, vs = (bare[0] if bare else ""), kv.get("vs", "?")
        if verb == "start":
            st[kind(vs)]["start"] += 1
            open_[(ch, vs)] = kv
        elif verb == "end":
            res = next((b for b in bare[1:] if b in ("win", "abort", "died")), None)
            x = st[kind(vs)]
            if res:
                x[res] += 1
            sk = open_.pop((ch, vs), None)
            if sk is not None and res == "win":
                pr, ar = num(sk.get("pred_r")), num(kv.get("r"))
                if pr is not None and ar is not None:
                    x["pr"].append(pr)
                    x["ar"].append(ar)
                pd, ad = num(sk.get("pred_dmg")), num(kv.get("dmg"))
                if pd is not None and ad is not None:
                    x["derr"].append(ad - pd)
    for ch, vs in open_:
        st[kind(vs)]["open"] += 1
    return st


def fight_table(games):
    print("\nfights (camps: vs=g<id>, champs: vs=c<id>; r p/a = mean predicted/actual rounds, dmgerr = mean "
          "actual - predicted damage, both over won fights; open = no fight|end by game end)")
    sub = f"{'n':>4} {'win':>4} {'abt':>4} {'died':>4} {'open':>4} {'r p/a':>11} {'dmgerr':>6}"
    print(f"{'':10} {'':4} | {'camps':<{len(sub)}} | champs")
    print(f"{'map':10} {'side':4} | {sub} | {sub}")
    for m, side, rep in games:
        if not os.path.exists(rep):
            continue
        st = fight_stats(game(rep, side)[0])
        cells = []
        for k in ("g", "c"):
            x = st[k]
            pa = "-" if not x["pr"] else f"{mean(x['pr']):.1f}/{mean(x['ar']):.1f}"
            cells.append(f"{x['start']:4} {x['win']:4} {x['abort']:4} {x['died']:4} {x['open']:4} {pa:>11} "
                         f"{fmt(mean(x['derr']), '.0f', 6)}")
        print(f"{m:10} {side:4} | {cells[0]} | {cells[1]}")


def bank_stats(s):
    starts, ends = evs(s, "bank", "start"), evs(s, "bank", "end")
    res = lambda e, ws: next((b for b in e[3][1:] if b in ws), None)
    cap_end, skips = evs(s, "cap", "end"), evs(s, "cap", "skip")
    cr = [res(e, ("paid", "reset", "abort")) for e in cap_end]
    br = [res(e, ("done", "broken", "cancel")) for e in ends]
    ticks = [num(kv.get("ticks")) for _, _, kv, _ in starts if num(kv.get("ticks")) is not None]
    return {"starts": len(starts), "done": br.count("done"), "broken": br.count("broken"),
            "cancel": br.count("cancel"), "gems": sum(inum(kv.get("gems")) for _, _, kv, _ in ends),
            "ticks": mean(ticks), "cap_start": len(evs(s, "cap", "start")), "paid": cr.count("paid"),
            "reset": cr.count("reset"), "abort": cr.count("abort"), "skip": len(skips),
            "top": top_why([e[2].get("why") for e, r in zip(cap_end, cr) if r != "paid"]
                           + [e[2].get("why") for e in skips])}


def bank_table(games):
    print("\nbanks (bank|start/end; gems = sum of bank|end gems=) and captures (cap|start/end/skip; "
          "top why over reset/abort/skip)")
    print(f"{'map':10} {'side':4} {'banks':>5} {'done':>4} {'broken':>6} {'cancel':>6} {'gems':>5} {'ticks':>5} | "
          f"{'caps':>4} {'paid':>4} {'reset':>5} {'abort':>5} {'skip':>4}  top why")
    for m, side, rep in games:
        if not os.path.exists(rep):
            continue
        b = bank_stats(game(rep, side)[0])
        print(f"{m:10} {side:4} {b['starts']:5} {b['done']:4} {b['broken']:6} {b['cancel']:6} {b['gems']:5} "
              f"{fmt(b['ticks'], '.1f', 5)} | {b['cap_start']:4} {b['paid']:4} {b['reset']:5} {b['abort']:5} "
              f"{b['skip']:4}  {b['top']}")


def int_table(games):
    per = []
    for m, side, rep in games:
        if not os.path.exists(rep):
            continue
        n = {}
        for _, _, _, bare in evs(game(rep, side)[0], "int"):
            ev = bare[0] if bare else "?"
            n[ev] = n.get(ev, 0) + 1
        per.append((m, side, n))
    names = sorted({k for _, _, n in per for k in n})
    print("\nints (int|<EVENT> lines per game)" + ("" if names else ": none logged"))
    if not names:
        return
    print(f"{'map':10} {'side':4} " + " ".join(f"{k:>{max(4, len(k))}}" for k in names) + f" {'total':>5}")
    for m, side, n in per:
        print(f"{m:10} {side:4} " + " ".join(f"{n.get(k, 0):{max(4, len(k))}}" for k in names)
              + f" {sum(n.values()):5}")


def load_invariants():
    """tools/invariants.py as a module (python -I leaves the script's directory off sys.path)."""
    try:
        spec = importlib.util.spec_from_file_location("tzu_invariants", os.path.join(ROOT, "tools", "invariants.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception as e:                       # the summary still prints without the hint
        print(f"(invariants.py not loaded: {type(e).__name__}: {e})")
        return None


def worst_invariants(inv, rep, side, k=2):
    """The k invariants with the most violations in this game, e.g. 'I9=3,I15=2 (+1)'; 'ok' if none."""
    if inv is None:
        return "?"
    try:
        res = {}
        for g in inv.games_of(rep, side):
            for name, r in inv.analyse(g, set(inv.INV)).items():
                if r.n:
                    res[name] = res.get(name, 0) + r.n
    except Exception as e:
        return f"err:{type(e).__name__}"
    if not res:
        return "ok"
    top = sorted(res.items(), key=lambda kv: (-kv[1], int(kv[0][1:])))
    return ",".join(f"{name}={n}" for name, n in top[:k]) + (f" (+{len(top) - k})" if len(top) > k else "")


def summary(games):
    """One line per (map, side); returns the number of flagged games."""
    inv = load_invariants()
    print(f"{'map':10} {'side':4} {'g/r':>5} {'g/r@500':>7} {'end':>5} {'deaths':>6} {'camp/ch':>7} "
          f"{'lostgems':>8} {'caps':>4} {'banks':>5} {'susp':>5} {'err':>4}  worst invariants")
    bad = 0
    for m, side, rep in games:
        if not os.path.exists(rep):
            print(f"{m:10} {side:4}  NO REPLAY")
            bad += 1
            continue
        s, end = game(rep, side)
        if not s:
            print(f"{m:10} {side:4}  NO TRACE")
            bad += 1
            continue
        nv, t, b = nav_row(s), task_row(s, end), bank_stats(s)
        has_cap = b["cap_start"] or b["paid"] or b["reset"] or b["abort"] or b["skip"]
        caps = b["paid"] if has_cap else t["caps"]                                     # cap|end paid, else ClearCamp ok
        banks = b["done"] if (b["starts"] or b["done"] or b["broken"]) else t["banks"]  # bank|end done, else Bank ok
        flag = flagged(nv)
        bad += flag
        print(f"{m:10} {side:4} {t['gr']:5.2f} {t['gr500']:7.2f} {end:5} {t['deaths']:6} "
              f"{str(t['camp_d']) + '/' + str(t['champ_d']):>7} {t['lost']:8} {caps:4} {banks:5} {nv['susp']:5} "
              f"{nv['err']:4}  {worst_invariants(inv, rep, side)}{'  <-- check' if flag else ''}")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bot")
    ap.add_argument("--opp", default="null")
    ap.add_argument("--maps", default="")
    ap.add_argument("--one-side", action="store_true")
    ap.add_argument("--keep", default="scenario")
    ap.add_argument("--jobs", default="4")
    ap.add_argument("--no-run", action="store_true", help="re-score runs/<keep>/ without playing")
    ap.add_argument("--summary", action="store_true", help="one line per (map, side) instead of the tables")
    a = ap.parse_args()

    maps = a.maps.split(",") if a.maps else sorted(
        f[:-len(".map26a")] for f in os.listdir(os.path.join(ROOT, "maps")) if f.endswith(".map26a"))
    out = os.path.join(ROOT, "runs", a.keep)
    games = []
    if a.no_run:        # re-score what matches.txt lists (filtered by --maps / --one-side)
        with open(os.path.join(out, "matches.txt")) as f:
            for p in (l.split() for l in f):
                if len(p) < 4:
                    continue
                m, side = os.path.basename(p[2])[:-len(".map26a")], p[3][:-len(".repl26a")].rsplit("-", 1)[1]
                if (not a.maps or m in maps) and not (a.one_side and side != "A"):
                    games.append((m, side, os.path.join(out, p[3])))
    else:
        shutil.rmtree(out, ignore_errors=True)
        os.makedirs(out)
        with open(os.path.join(out, "matches.txt"), "w") as f:
            for m in maps:
                sides = ("A",) if a.one_side else ("A", "B")
                for side in sides:
                    first, second = (a.bot, a.opp) if side == "A" else (a.opp, a.bot)
                    rep = f"{m}-{side}.repl26a"
                    f.write(f"../../bots/{first} ../../bots/{second} ../../maps/{m}.map26a {rep}\n")
                    games.append((m, side, os.path.join(out, rep)))
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from arena import find_cambc
        r = subprocess.run([find_cambc(), "run-batch", os.path.join(out, "matches.txt"), "--jobs", a.jobs,
                            "--timeout", "900", "--release"], capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-2000:], r.stderr[-2000:])

    print(f"{a.bot} vs {a.opp}   (fuel budget {FUEL_BUDGET:,}/turn; boot/first = round)")
    if a.summary:
        bad = summary(games)
        print("replays:", out)
        sys.exit(1 if bad else 0)
    bad = 0
    print(f"{'map':10} {'side':4} {'boot':>5} {'first':>5} {'turn1':>9} {'maxfuel':>9} {'medfuel':>8} "
          f"{'susp':>5} {'err':>4} {'fields':>6} {'moved':>5} | {'legs':>5} {'ontime':>6} {'extra':>5} "
          f"{'full':>4} {'stuck':>5} {'died':>4} {'osc':>4}")
    for m, side, rep in games:
        if not os.path.exists(rep):
            print(f"{m:10} {side:4}  NO REPLAY")
            bad += 1
            continue
        s = score(lines_of(rep, side))
        if not s:
            print(f"{m:10} {side:4}  NO TRACE")
            bad += 1
            continue
        n = nav_row(s)
        flag = "  <-- check" if flagged(n) else ""
        bad += bool(flag)
        print(f"{m:10} {side:4} {n['boot']:5} {n['first']:5} {n['t1']:9,} {n['maxf']:9,} {n['medf']:8,} "
              f"{n['susp']:5} {n['err']:4} {n['fields']:>6} {n['moved']:5.0%} | {n['legs']:5} {n['ontime']:6.0%} "
              f"{n['extra']:5} {n['full']:4} {n['stuck']:5} {n['died']:4} {n['osc']:4}{flag}")
    print("replays:", out)
    clear_table(games)
    task_table(games)
    fight_table(games)
    bank_table(games)
    int_table(games)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
