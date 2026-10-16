"""Count invariant violations (docs/archive/design/INVARIANTS.md, I1..I18) in replay bundles.

Usage: python -I tools/invariants.py RUN_DIR_OR_BUNDLE [more...] [--team A|B|both] [--only I1,I9]
                                     [--verbose] [--strict]
       python -I tools/invariants.py --selftest

Reads trace lines `P|round|team|champ|tag|text` from team-a/b.stdout inside each .repl26a (NUL bytes
are newlines) and counts, per (map, side), what INVARIANTS.md section 1(e) calls a violation, from the
facts in the lines, never from a bot verdict. "n/a" = no line of that kind seen at all (the feature is
not logged yet), which never passes as 0. Exit 1 if any count > 0 (--strict: also if any n/a).

 I1  recall|start with awake>0, camp<=5 or enemy<=10; every recall|end broken
 I2  death with gems>0 (--verbose splits them by=camp|champ); plus a flee line followed next round by a flee whose ttd did not improve
 I3  fight|start with pred_dmg*1.1 > hp - keep (needs keep= or keep_hp=+max_hp=) or ttk ours*1.3 > theirs;
     fight|end died; fight|end abort with dmg < the start's pred_dmg
 I4  cap|skip / cap|end abort with why outside {ally_on,enemy_on,danger,lowhp}; a t-line dead=<g> episode
     with no cap|start or cap|skip for g by that champion within 2 rounds
 I5  cap|start allies>0; two champions of one team with the same on_spawn=<g> in one round
 I6  cast|idle with why outside {excl_walk_flee,no_target,no_value}
 I7  shop with gold>=30, bought=- and why outside {save_lock,cap_limit}
 I8  t act=wait with no why, why=no_target, why=blocked beyond 2 rounds running, an unknown why,
     respawn_wait with r>5 (unless nowork=1), or an empty act; why=hold is allowed
 I9  a round with no t line for a living champion (first t line .. game end; dead spans excluded);
     fuel > 2.5M on any t line after the champion's first; any fuel|over line
 I10 t with inc>0, fight=- and no move token; or inc>0 fight=- on two consecutive rounds (step didn't leave)
 I11 risk with detour=none; death by=champ with gems>=bank_at_threat after a risk line in the last 10 rounds
 I12 t with on_spawn=<g> and gstate=respawning, except the round of that champion's cap|end paid
 I13 bank|start lock=enemy; bank|start with enemy<=5+ticks and a stunner (stunner=) in sight; bank|end broken
 I14 an act err mentioning a used allowance; >1 walk/dash/tp token in one act; displacement between
     consecutive rounds beyond the act's tokens (walk 1, dash 2, tp 3); osc (A->B->A with the same tgt)
 I15 tgt differs from the previous t line's with no task or int line by that champion in between
 I16 recall|start with no why, or spawn_d<=5
 I17 t hit=<g> with no open fight vs=<g> for that champion and no splash g=<g> that round (g7 = 7)
 I18 (Cassi & Issac only, found by type=/link= on boot/kit lines) a round both bodies die with summed gems>0
"""
import argparse
import os
import re
import sys
import tempfile
import zipfile

FUEL_TURN = 2_500_000         # per turn, Python [measured A16]; first play turn exempt (~4.6M) [measured]
R1 = 5                        # enemy reach next turn [measured A46]; INVARIANTS.md section 0
R_RECALL = 10                 # R1 + 5 recall ticks; I1 enemy bound [rules arithmetic]
CAMP_SAFE = 5                 # I1 camp<=5 bound: range 3, monolith treated as 5 [rules table; measured A31]
CAPTURE_GRACE = 2             # I4: cap|start or cap|skip within 2 rounds of seeing a dead group [INVARIANTS I4]
BLOCKED_MAX = 2               # I8: why=blocked at most 2 rounds in a row [INVARIANTS I8]
RESPAWN_WAIT_MAX = 5          # I8: respawn_wait only for r<=5 [INVARIANTS I8]
SPAWN_NEAR = 5                # I16: never recall with spawn_d<=5 [INVARIANTS I16]
BANK_AT_THREAT = 20           # I11 default card value [provisional A15/A40]; a risk line's bat= overrides
RISK_WINDOW = 10              # I11: rounds before a death in which a risk line counts [INVARIANTS I11]
DASH, TP = 2, 3               # extra displacement: dash 2 [rules], teleport crystal 3 [rules]; A46 combos

CAP_WHY = {"ally_on", "enemy_on", "danger", "lowhp"}
CAST_WHY = {"excl_walk_flee", "no_target", "no_value"}
SHOP_WHY = {"save_lock", "cap_limit"}
WAIT_WHY = {"capturing", "channel", "respawn_wait", "blocked", "dead", "endgame", "hold"}   # no_target is a violation
WALK = {"mv", "gr", "fl", "sd", "dt", "on", "sf", "ex"}   # mv per spec; the rest are v2-era walk tokens
CHANNEL = {"ch", "rec", "recall"}           # a channel (recall arrival) excuses a jump
ALLOWANCE = re.compile(r"already|allowance|twice|one (move|attack|cast)|can ?not (move|attack)", re.I)
INV = [f"I{i}" for i in range(1, 19)]


def lines_of(bundle, team):
    """Rows (round, team, champ, tag, text) of team-<team>.stdout; same reading as tools/scenario.py."""
    z = zipfile.ZipFile(bundle)
    name = f"team-{team.lower()}.stdout"
    if name not in z.namelist():
        return []
    text = z.read(name).decode("utf-8", "replace").replace("\x00", "\n")
    return parse_text(text)


def parse_text(text):
    out = []
    for l in text.splitlines():
        p = l.split("|", 5)
        if len(p) == 6 and p[0] == "P":
            try:
                out.append((int(p[1]), p[2], p[3], p[4], p[5]))
            except ValueError:
                pass
    return out


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def kv_of(text):
    """Fields of an event line: kv dict plus the bare words (verb, result) in order."""
    kv, bare = {}, []
    for w in text.split(" "):
        if "=" in w:
            k, v = w.split("=", 1)
            kv.setdefault(k, v)
        elif w:
            bare.append(w)
    return kv, bare


def parse_t(text):
    """A `t` line, spec form `x,y fuel=N act=<tokens> [why=..] tgt=.. inc=.. ...` or v2 `x,y N act.. k=v`."""
    words = text.split(" ")
    kv, _ = kv_of(text)
    t = {"kv": kv, "pos": None, "fuel": num(kv.get("fuel")), "err": None}
    m = re.match(r"^(-?\d+),(-?\d+)$", words[0]) if words else None
    if m:
        t["pos"] = (int(m.group(1)), int(m.group(2)))
    elif "pos" in kv and re.match(r"^-?\d+,-?\d+$", kv["pos"]):
        t["pos"] = tuple(int(x) for x in kv["pos"].split(","))
    if "act" in kv:
        act = kv["act"]
        if act.startswith("err"):
            act = text.split("act=", 1)[1]
    else:                                  # v2: "x,y fuel act words... k=v"
        if t["fuel"] is None and len(words) > 1:
            t["fuel"] = num(words[1])
        act = " ".join(w for w in words[2:] if "=" not in w) if len(words) > 2 else ""
        if act.startswith("err"):
            act = text.split(" ", 2)[2]
    if act.startswith("err"):
        t["err"], toks = act, ["err"]
    else:
        toks = [x.lower() for x in re.findall(r"[A-Za-z_]+", act)]
    t["toks"] = toks
    t["why"] = kv.get("why") or ("dead" if "dead" in toks else None)
    t["dead"] = t["why"] == "dead"
    t["wait"] = "wait" in toks or "idle" in toks or (t["dead"] and len(toks) <= 1)
    t["walks"] = sum(x in WALK for x in toks)
    t["move"] = t["walks"] > 0 or "dash" in toks or "tp" in toks
    return t


class Game:
    def __init__(self, label, side, rows, end):
        self.label, self.side, self.end = label, side, end
        self.t, self.ev = {}, {}
        for rnd, _team, champ, tag, text in rows:
            if tag == "t":
                self.t.setdefault(champ, []).append((rnd, parse_t(text)))
            else:
                self.ev.setdefault(tag, []).append((rnd, champ) + kv_of(text))
        for v in self.t.values():
            v.sort(key=lambda x: x[0])

    def tag(self, tag, verb=None):
        return [e for e in self.ev.get(tag, []) if verb is None or (e[3][:1] == [verb])]

    def has_field(self, f):
        return any(f in t["kv"] for v in self.t.values() for _, t in v)


def gid(x):
    """One group-id form for comparisons: 'g7' and '7' are the same camp group; 'c7' (a champion) stays."""
    return x[1:] if x and x[0] == "g" and x[1:].isdigit() else x


class Res:
    def __init__(self):
        self.n, self.off, self.notes, self.info = None, [], [], []

    def bad(self, rnd, champ, msg):
        self.n = (self.n or 0) + 1
        self.off.append((rnd, champ, msg))

    def seen(self):
        self.n = self.n or 0

    def note(self, msg):
        if msg not in self.notes:
            self.notes.append(msg)


def need(r, kv, field, tag):
    v = kv.get(field)
    if v is None:
        r.note(f"{tag} lacks {field}=")
    return v


def i1(g, r):
    for rnd, c, kv, bare in g.tag("recall", "start"):
        r.seen()
        aw, cp, en = (need(r, kv, f, "recall|start") for f in ("awake", "camp", "enemy"))
        if (num(aw) or 0) > 0 or (num(cp) is not None and num(cp) <= CAMP_SAFE) or \
                (num(en) is not None and num(en) <= R_RECALL):
            r.bad(rnd, c, f"recall start awake={aw} camp={cp} enemy={en}")
    for rnd, c, kv, bare in g.tag("recall", "end"):
        r.seen()
        if "broken" in bare:
            r.bad(rnd, c, f"recall end broken by={kv.get('by')}")


def i2(g, r):
    split = {}                                  # by=<camp|champ> (? = not logged): deaths with gems, gems lost
    for rnd, c, kv, bare in g.tag("death"):
        r.seen()
        gems = num(kv.get("gems")) or 0
        if gems > 0:
            by = kv.get("by", "?")
            n, lost = split.get(by, (0, 0))
            split[by] = (n + 1, lost + gems)
            r.bad(rnd, c, f"death gems={kv.get('gems')} by={by} task={kv.get('task')}")
    if split:
        r.info.append("deaths with gems by " + " ".join(f"{b}={n} ({lost:g} gems)"
                                                        for b, (n, lost) in sorted(split.items())))
    prev = {}
    for rnd, c, kv, bare in sorted(g.tag("flee"), key=lambda e: e[0]):
        r.seen()
        p = prev.get(c)
        if p and p[0] == rnd - 1 and num(kv.get("ttd")) is not None and num(p[1]) is not None \
                and num(kv["ttd"]) <= num(p[1]):
            r.bad(rnd, c, f"flee did not improve ttd {p[1]}->{kv['ttd']}")
        prev[c] = (rnd, kv.get("ttd"))


def i3(g, r):
    open_ = {}
    for rnd, c, kv, bare in sorted(g.tag("fight"), key=lambda e: e[0]):
        r.seen()
        verb = bare[0] if bare else ""
        if verb == "start":
            open_[(c, kv.get("vs"))] = kv
            pd, hp = num(kv.get("pred_dmg")), num(kv.get("hp"))
            keep = num(kv.get("keep"))
            if keep is None and num(kv.get("keep_hp")) is not None and num(kv.get("max_hp")) is not None:
                keep = num(kv["keep_hp"]) * num(kv["max_hp"])
            if keep is None:
                r.note("fight|start lacks keep=<HP floor> (or keep_hp= and max_hp=): pred_dmg check skipped")
            elif pd is not None and hp is not None and pd * 1.1 > hp - keep:
                r.bad(rnd, c, f"fight start vs={kv.get('vs')} pred_dmg={pd:g} hp={hp:g} keep={keep:g}")
            tk = kv.get("ttk", "").split("/")
            if len(tk) == 2 and num(tk[0]) is not None and num(tk[1]) is not None and num(tk[0]) * 1.3 > num(tk[1]):
                r.bad(rnd, c, f"fight start vs={kv.get('vs')} ttk={kv['ttk']}")
        elif verb == "end":
            st = open_.pop((c, kv.get("vs")), None)
            if "died" in bare:
                r.bad(rnd, c, f"fight end died vs={kv.get('vs')}")
            elif "abort" in bare and st and num(kv.get("dmg")) is not None and num(st.get("pred_dmg")) is not None \
                    and num(kv["dmg"]) < num(st["pred_dmg"]):
                r.bad(rnd, c, f"fight abort vs={kv.get('vs')} dmg={kv['dmg']} < pred_dmg={st['pred_dmg']}")


def i4(g, r):
    acts = {}
    for rnd, c, kv, bare in g.tag("cap"):
        r.seen()
        verb = bare[0] if bare else ""
        if verb in ("start", "skip"):
            acts.setdefault((c, gid(kv.get("g"))), []).append(rnd)
        if verb == "skip" and kv.get("why") not in CAP_WHY:
            r.bad(rnd, c, f"cap skip g={kv.get('g')} why={kv.get('why')}")
        if verb == "end" and "abort" in bare and kv.get("why") not in CAP_WHY:
            r.bad(rnd, c, f"cap abort g={kv.get('g')} why={kv.get('why')}")
    if not g.has_field("dead"):
        if g.t:
            r.note("t lines lack dead=<g>: ignored-dead-group check skipped")
        return
    for c, tl in g.t.items():
        last = {}
        for rnd, t in tl:
            r.seen()
            gs = [gid(x) for x in t["kv"].get("dead", "-").split(",") if x not in ("-", "")]
            for dg in gs:
                if last.get(dg) != rnd - 1:           # a new episode of seeing g dead
                    if not any(rnd - 1 <= x <= rnd + CAPTURE_GRACE for x in acts.get((c, dg), [])):
                        r.bad(rnd, c, f"dead group {dg} in reach, no cap start/skip within {CAPTURE_GRACE}")
                last[dg] = rnd


def i5(g, r):
    for rnd, c, kv, bare in g.tag("cap", "start"):
        r.seen()
        if (num(kv.get("allies")) or 0) > 0:
            r.bad(rnd, c, f"cap start g={kv.get('g')} allies={kv.get('allies')}")
    if not g.has_field("on_spawn"):
        return
    occ = {}
    for c, tl in g.t.items():
        for rnd, t in tl:
            r.seen()
            s = t["kv"].get("on_spawn", "-")
            if s != "-" and not t["dead"]:
                occ.setdefault((rnd, s), []).append(c)
    for (rnd, s), cs in sorted(occ.items()):
        if len(cs) > 1:
            r.bad(rnd, ",".join(cs), f"{len(cs)} champions on spawn of group {s}")


def i6(g, r):
    for rnd, c, kv, bare in g.tag("cast"):
        r.seen()
        if bare[:1] == ["idle"] and kv.get("why") not in CAST_WHY:
            r.bad(rnd, c, f"cast idle slot={kv.get('slot')} why={kv.get('why')}")


def i7(g, r):
    for rnd, c, kv, bare in g.tag("shop"):
        r.seen()
        if (num(kv.get("gold")) or 0) >= 30 and kv.get("bought", "-") == "-" and kv.get("why") not in SHOP_WHY:
            r.bad(rnd, c, f"shop gold={kv.get('gold')} bought=- why={kv.get('why')}")


def i8(g, r):
    for c, tl in g.t.items():
        run, prev = 0, None
        for rnd, t in tl:
            r.seen()
            why = t["why"]
            run = run + 1 if (why == "blocked" and prev == rnd - 1 and run) else (1 if why == "blocked" else 0)
            prev = rnd
            if t["err"]:
                continue                                   # counted by I14 / the error list
            if not t["toks"]:
                r.bad(rnd, c, "empty act")
            elif t["wait"]:
                if why is None:
                    r.bad(rnd, c, "wait with no why")
                elif why == "blocked" and run > BLOCKED_MAX:
                    r.bad(rnd, c, f"blocked {run} rounds running")
                elif why == "respawn_wait" and (num(t["kv"].get("r")) or 0) > RESPAWN_WAIT_MAX \
                        and t["kv"].get("nowork") != "1":       # nowork=1: no clearable group, bank or shop
                    r.bad(rnd, c, f"respawn_wait r={t['kv']['r']}")
                elif why not in WAIT_WHY:
                    r.bad(rnd, c, f"wait why={why}")


def i9(g, r):
    deaths = {}
    for rnd, c, kv, bare in g.tag("death"):
        deaths.setdefault(c, []).append(rnd)
    for rnd, c, kv, bare in g.tag("fuel", "over"):
        r.bad(rnd, c, f"fuel over est={kv.get('est')} job={kv.get('job')}")
    for c, tl in g.t.items():
        r.seen()
        if any(t["fuel"] is None for _, t in tl):
            r.note("some t lines lack fuel=")
        for rnd, t in tl[1:]:
            if t["fuel"] is not None and t["fuel"] > FUEL_TURN:
                r.bad(rnd, c, f"fuel {int(t['fuel']):,} > {FUEL_TURN:,}")
        rs = [x for x, _ in tl]
        stops = rs[1:] + [g.end]           # the last round may end mid-round (winning tribute): not counted
        for (a, ta), b in zip(tl, stops):
            if b - a <= 1 or ta["dead"] or any(a <= d < b for d in deaths.get(c, [])):
                continue
            for miss in range(a + 1, b):
                r.bad(miss, c, f"no t line (alive; last line r{a})")


def i10(g, r):
    if not (g.has_field("inc") and g.has_field("fight")):
        if g.t:
            r.note("t lines lack inc= and/or fight=")
        return
    for c, tl in g.t.items():
        prev = None
        for rnd, t in tl:
            r.seen()
            kv = t["kv"]
            hot = (num(kv.get("inc")) or 0) > 0 and kv.get("fight", "-") == "-" and not t["dead"]
            if hot and not t["move"]:
                r.bad(rnd, c, f"inc={kv['inc']} fight=- act={'+'.join(t['toks'])}")
            elif hot and prev == rnd - 1:
                r.bad(rnd, c, f"inc={kv['inc']} fight=- second round in range")
            prev = rnd if hot else None


def i11(g, r):
    risk = {}
    for rnd, c, kv, bare in g.tag("risk"):
        r.seen()
        risk.setdefault(c, []).append((rnd, num(kv.get("bat")) or BANK_AT_THREAT))
        if kv.get("detour") == "none":
            r.bad(rnd, c, f"risk detour=none bag={kv.get('bag')}")
    if "risk" not in g.ev:
        return
    for rnd, c, kv, bare in g.tag("death"):
        if "by" not in kv:
            r.note("death lacks by=<camp|champ>")
        gems = num(kv.get("gems")) or 0
        if kv.get("by") == "champ" and any(rnd - RISK_WINDOW <= x < rnd and gems >= bat for x, bat in risk.get(c, [])):
            r.bad(rnd, c, f"carrier death gems={gems:g} after a risk line")


def i12(g, r):
    if not (g.has_field("on_spawn") and g.has_field("gstate")):
        if g.t:
            r.note("t lines lack on_spawn= and/or gstate=")
        return
    paid = {(rnd, c) for rnd, c, kv, bare in g.tag("cap", "end") if "paid" in bare}
    for c, tl in g.t.items():
        for rnd, t in tl:
            r.seen()
            kv = t["kv"]
            if kv.get("on_spawn", "-") != "-" and kv.get("gstate") == "respawning" and (rnd, c) not in paid:
                r.bad(rnd, c, f"on spawn of group {kv['on_spawn']} while respawning")


def i13(g, r):
    for rnd, c, kv, bare in g.tag("bank", "start"):
        r.seen()
        if kv.get("lock") == "enemy":
            r.bad(rnd, c, f"bank start lock=enemy altar={kv.get('altar')}")
        en, tk = num(kv.get("enemy")), num(kv.get("ticks"))
        if "stunner" not in kv:
            r.note("bank|start lacks stunner=<d or ->: stunner check skipped")
        elif en is not None and tk is not None and en <= R1 + tk and kv["stunner"] != "-":
            r.bad(rnd, c, f"bank start enemy={en:g} ticks={tk:g} stunner={kv['stunner']}")
    for rnd, c, kv, bare in g.tag("bank", "end"):
        r.seen()
        if "broken" in bare:
            r.bad(rnd, c, f"bank end broken by={kv.get('by')}")


def i14(g, r):
    rec = {(rnd, c) for rnd, c, kv, bare in g.tag("recall", "end") if "done" in bare}
    for rnd, c, kv, bare in g.tag("err"):
        if ALLOWANCE.search(" ".join(bare + [f"{k}={v}" for k, v in kv.items()])):
            r.bad(rnd, c, "err line: " + " ".join(bare)[:80])
    for c, tl in g.t.items():
        for i, (rnd, t) in enumerate(tl):
            r.seen()
            if t["err"] and ALLOWANCE.search(t["err"]):
                r.bad(rnd, c, t["err"][:80])
            if t["walks"] > 1 or t["toks"].count("dash") > 1 or t["toks"].count("tp") > 1:
                r.bad(rnd, c, f"two move tokens: {'+'.join(t['toks'])}")
            if i == 0:
                continue
            pr, pt = tl[i - 1]
            if pr == rnd - 1 and pt["pos"] and t["pos"] and not (pt["dead"] or t["dead"]) \
                    and not (CHANNEL & (set(pt["toks"]) | set(t["toks"]))) and (rnd, c) not in rec \
                    and (rnd - 1, c) not in rec:
                d = max(abs(t["pos"][0] - pt["pos"][0]), abs(t["pos"][1] - pt["pos"][1]))
                allow = (1 if t["walks"] else 0) + (DASH if "dash" in t["toks"] else 0) + (TP if "tp" in t["toks"] else 0)
                if d > allow:
                    r.bad(rnd, c, f"moved {d} tiles with act={'+'.join(t['toks'])} (allowed {allow})")
            if i >= 2:
                (r2, a), (r1_, b) = tl[i - 2], tl[i - 1]
                ga, gb, gc = (x["kv"].get("tgt") for x in (a, b, t))
                if r2 == rnd - 2 and r1_ == rnd - 1 and a["pos"] and a["pos"] == t["pos"] \
                        and b["pos"] != t["pos"] and ga == gb == gc and gc is not None:
                    r.bad(rnd, c, f"osc {a['pos']}->{b['pos']}->{t['pos']} tgt={gc}")


def i15(g, r):
    if not g.has_field("tgt"):
        if g.t:
            r.note("t lines lack tgt=")
        return
    evr = {}
    for tag in ("task", "int"):
        for rnd, c, kv, bare in g.ev.get(tag, []):
            evr.setdefault(c, set()).add(rnd)
    for c, tl in g.t.items():
        for (pr, pt), (rnd, t) in zip(tl, tl[1:]):
            r.seen()
            a, b = pt["kv"].get("tgt"), t["kv"].get("tgt")
            if a is not None and b is not None and a != b and not any(pr < x <= rnd for x in evr.get(c, ())):
                r.bad(rnd, c, f"tgt {a} -> {b} with no task/int line")


def i16(g, r):
    for rnd, c, kv, bare in g.tag("recall", "start"):
        r.seen()
        if "why" not in kv:
            r.bad(rnd, c, "recall start with no why")
        if "spawn_d" not in kv:
            r.note("recall|start lacks spawn_d=")
        elif num(kv["spawn_d"]) is not None and num(kv["spawn_d"]) <= SPAWN_NEAR:
            r.bad(rnd, c, f"recall start spawn_d={kv['spawn_d']}")


def i17(g, r):
    if not g.has_field("hit"):                 # runs as soon as any t line of the game carries hit=
        if g.t:
            r.note("t lines lack hit=<g> on attack turns")
        return
    fights, splash = [], {(rnd, c, gid(kv.get("g"))) for rnd, c, kv, bare in g.tag("splash")}
    for rnd, c, kv, bare in g.ev.get("fight", []):
        fights.append((rnd, c, gid(kv.get("vs")), bare[0] if bare else ""))   # vs=g<id> camp, vs=c<id> champ
    for c, tl in g.t.items():
        for rnd, t in tl:
            r.seen()
            for h in [gid(x) for x in t["kv"].get("hit", "-").split(",") if x not in ("-", "")]:
                ev = [(fr, v) for fr, fc, vs, v in fights if fc == c and vs == h and fr <= rnd]
                open_ = bool(ev) and max(ev)[1] == "start" or any(fr == rnd and v == "end" for fr, v in ev)
                if not open_ and (rnd, c, h) not in splash:
                    r.bad(rnd, c, f"hit group {h} with no open fight")


def i18(g, r):
    types = {}
    for tag in ("boot", "kit"):
        for rnd, c, kv, bare in g.ev.get(tag, []):
            ty = (kv.get("type") or "").lower()
            if ty in ("cassi", "issac") or "link" in kv:
                types[c] = ty or "linked"
    if len(types) < 2:
        return
    r.seen()
    by_round = {}
    for rnd, c, kv, bare in g.tag("death"):
        if c in types:
            by_round.setdefault(rnd, []).append(num(kv.get("gems")) or 0)
    for rnd, gems in sorted(by_round.items()):
        if sum(gems) > 0:
            r.bad(rnd, "+".join(sorted(types)), f"linked bodies died with {sum(gems):g} gems")


CHECKS = [i1, i2, i3, i4, i5, i6, i7, i8, i9, i10, i11, i12, i13, i14, i15, i16, i17, i18]


def analyse(g, only):
    out = {}
    for name, f in zip(INV, CHECKS):
        if name in only:
            out[name] = Res()
            f(g, out[name])
    return out


def bundles(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, _, files in sorted(os.walk(p)):
                for f in sorted(files):
                    if f.endswith(".repl26a"):
                        yield os.path.join(root, f)
        elif p.endswith(".repl26a"):
            yield p


def games_of(path, team):
    try:
        z = zipfile.ZipFile(path)
        rows = {s: lines_of(path, s) for s in "AB" if f"team-{s.lower()}.stdout" in z.namelist()}
    except (zipfile.BadZipFile, OSError) as e:
        print(f"skip {path}: {e}")
        return
    stem = os.path.basename(path)[:-len(".repl26a")]
    m = re.match(r"^(.*)-([AB])$", stem)
    label = m.group(1) if m else stem
    if not m and os.path.basename(os.path.dirname(path)) not in ("", "."):
        label = os.path.basename(os.path.dirname(path)) + "/" + stem[:24]
    sides = "AB" if team == "both" else (team if team in "AB" else (m.group(2) if m else "AB"))
    end = max((x[0] for v in rows.values() for x in v), default=0)
    for s in sides:
        if rows.get(s):
            yield Game(label, s, rows[s], end)


def report(results, only, verbose):
    cols = [i for i in INV if i in only]
    cell = lambda v: "n/a" if v is None else str(v)
    print(f"{'map':24} {'side':4} " + " ".join(f"{c:>4}" for c in cols))
    tot = {c: None for c in cols}
    for g, res in results:
        print(f"{g.label[:24]:24} {g.side:4} " + " ".join(f"{cell(res[c].n):>4}" for c in cols))
        for c in cols:
            if res[c].n is not None:
                tot[c] = (tot[c] or 0) + res[c].n
    print(f"{'TOTAL':24} {'':4} " + " ".join(f"{cell(tot[c]):>4}" for c in cols))
    if verbose:
        for g, res in results:
            for c in cols:
                if res[c].off:
                    print(f"\n{g.label} {g.side} {c}: {res[c].n}")
                    for line in res[c].info:
                        print(f"   {line}")
                    for rnd, ch, msg in res[c].off[:5]:
                        print(f"   r{rnd:<5} c{ch:<4} {msg}")
    notes = {}
    for g, res in results:
        for c in cols:
            for n in res[c].notes:
                notes.setdefault((c, n), 0)
                notes[(c, n)] += 1
    if notes:
        print("\nnotes (checks that could not run: the field is not logged)")
        for (c, n), k in notes.items():
            print(f"  {c:4} {n}  [{k} game(s)]")
    return tot


def selftest():
    """One of each of I1, I2, I8, I9, I12, I13, I14, I15 in a synthetic bundle; the rest 0 or n/a."""
    def t(r, c, pos, act, tgt, extra=""):
        sp = extra or "on_spawn=- gstate=-"
        return f"P|{r}|A|{c}|t|{pos} fuel={3000000 if r == 1 else 100000} act={act} tgt={tgt} inc=0 fight=- {sp} dead=-"
    A = [t(1, 1, "5,5", "mv", "A"), t(2, 1, "6,6", "mv", "A"),
         t(3, 1, "6,6", "wait", "A"),                                     # I8 wait, no why; round 4 missing: I9
         t(5, 1, "7,7", "mv", "A"), t(6, 1, "9,9", "mv", "A"),           # I14 two tiles on one walk
         t(7, 1, "10,10", "mv", "B"),                                     # I15 tgt change, no event
         "P|8|A|1|int|BANK bag=40", t(8, 1, "11,11", "mv", "C"),
         "P|9|A|1|recall|start hp=100 bag=0 awake=1 camp=9 enemy=- why=heal spawn_d=20",   # I1
         t(9, 1, "11,11", "ch", "C"), "P|10|A|1|recall|end done by=-", t(10, 1, "0,0", "ch", "C"),
         t(11, 1, "1,1", "mv", "C"),
         "P|12|A|1|bank|start altar=1,1 gems=5 ticks=1 lock=enemy enemy=- stunner=-",      # I13
         t(12, 1, "1,1", "ch", "C"),
         t(1, 2, "21,21", "mv", "X"), "P|2|A|2|cap|end g=3 paid r=5 gems=10 gold=0",
         t(2, 2, "21,21", "cap", "X", "on_spawn=3 gstate=respawning"),
         t(3, 2, "21,21", "wait why=capturing", "X", "on_spawn=3 gstate=respawning"),   # I12
         t(4, 2, "22,22", "mv", "X"), "P|5|A|2|death|gems=12 task=Bank by=camp",       # I2; 6-8 dead
         t(9, 2, "22,23", "mv", "X"), t(10, 2, "22,24", "mv", "X"), t(11, 2, "22,25", "mv", "X"),
         t(12, 2, "22,26", "mv", "X")]
    # Champion 3, the section 6 fields: a dead group seen as dead=g4 and skipped as cap g=4 (I4 ok across
    # id forms); a camp fight vs=g7 whose hits are logged hit=7 / hit=g7 (I17 ok), then hit=9 with no
    # fight (I17); a champion fight vs=c12 that passes the gate but ends died (I3); death by=champ with
    # gems (I2, the second: by=camp above, by=champ here).
    sp = "on_spawn=- gstate=-"
    A += [t(1, 3, "30,30", "mv", "G", f"{sp} dead=g4"), "P|1|A|3|cap|skip g=4 why=ally_on",
          "P|2|A|3|fight|start vs=g7 pred_r=5 pred_dmg=20 hp=100 keep=30 ttk=- enemies=0",
          t(2, 3, "30,30", "at", "G", f"{sp} hit=7"),
          "P|3|A|3|fight|end vs=g7 win r=2 dmg=10 why=-", t(3, 3, "30,30", "at", "G", f"{sp} hit=g7"),
          t(4, 3, "30,30", "at", "G", f"{sp} hit=9"),                                       # I17
          "P|5|A|3|fight|start vs=c12 pred_r=3 pred_dmg=10 hp=100 keep=30 ttk=2/4 enemies=1",
          t(5, 3, "30,30", "at", "G"),
          "P|6|A|3|fight|end vs=c12 died r=1 dmg=100 why=stun",                             # I3
          t(6, 3, "30,30", "at", "G"), "P|6|A|3|death|gems=5 by=champ task=Hunt"]          # I2
    want = dict.fromkeys(["I1", "I3", "I8", "I9", "I12", "I13", "I14", "I15", "I17"], 1)
    want["I2"] = 2
    want.update(dict.fromkeys(["I4", "I5", "I10", "I16"], 0))
    want.update(dict.fromkeys(["I6", "I7", "I11", "I18"], None))
    with tempfile.TemporaryDirectory() as d:          # round-trip through a real bundle with NUL separators
        p = os.path.join(d, "fixture-A.repl26a")
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("team-a.stdout", chr(0).join(A) + chr(0))
            z.writestr("team-b.stdout", "")
        results = [(g, analyse(g, set(INV))) for g in games_of(p, "auto")]
    report(results, set(INV), True)
    got = {k: v.n for k, v in results[0][1].items()}
    bad = {k: (got[k], w) for k, w in want.items() if got[k] != w}
    print("\nselftest:", "PASS" if not bad else f"FAIL (got, want) {bad}")
    return 0 if not bad else 1


def main():
    ap = argparse.ArgumentParser(description="Count INVARIANTS.md violations in replay bundles.")
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--team", default="auto", choices=["A", "B", "both", "auto"],
                    help="which stdout to read; auto = the -A/-B suffix of the bundle name, else both")
    ap.add_argument("--only", default="", help="e.g. I1,I9")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--strict", action="store_true", help="n/a also fails")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not a.paths:
        ap.error("give a replay bundle or a directory")
    only = {x.strip().upper() for x in a.only.split(",") if x.strip()} or set(INV)
    results = [(g, analyse(g, only)) for p in bundles(a.paths) for g in games_of(p, a.team)]
    if not results:
        print("no bundles with trace lines found")
        sys.exit(1)
    tot = report(results, only, a.verbose)
    fail = any((v or 0) > 0 for v in tot.values()) or (a.strict and any(v is None for v in tot.values()))
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
