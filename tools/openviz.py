"""Build runs/openviz.html from opening-bench runs (tools/bench.py --rounds 300).

Usage: python -I tools/openviz.py LABEL_GLOB [LABEL_GLOB ...]   e.g. "open-stack*"
Reads runs/bench/<label>/results.json, adds the OTHER team's turn shares from its stdout in the replay bundle
(the bench only parses our side), embeds the rows as JSON into tools/viz/openviz.html and writes runs/openviz.html.
The page is a static artifact: all data inline.
"""
import glob
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(ROOT, "tools", "viz", "openviz.html")
OUT = os.path.join(ROOT, "runs", "openviz.html")
ACT = re.compile(r"\bact=(\d+)/(\d+)/(\d+)/(\d+)/(\d+)/(\d+)/(\d+)")


def base_shares(row, cap=300):
    """attacking / waiting / dead as % of all the other team's champion-turns up to cap."""
    bundle = os.path.join(ROOT, row.get("bundle", "").replace("\\", os.sep))
    other = "b" if row.get("side") == "A" else "a"
    try:
        with zipfile.ZipFile(bundle) as z:
            text = z.read("team-%s.stdout" % other).decode("utf-8", "replace")
    except (OSError, KeyError, zipfile.BadZipFile):
        return {}
    tot = [0] * 7
    for line in text.replace("\x00", "\n").splitlines():
        parts = line.strip().split("|", 5)
        if len(parts) > 5 and parts[4] == "tick" and parts[1].isdigit() and int(parts[1]) <= cap:
            m = ACT.search(line)
            if m:
                for i in range(7):
                    tot[i] += int(m.group(i + 1))
    n = sum(tot)
    if not n:
        return {}
    return {"base_atk300": round(100 * tot[1] / n), "base_wait300": round(100 * tot[4] / n),
            "base_dead300": round(100 * tot[6] / n)}


def main():
    runs = {}
    for pat in sys.argv[1:] or ["open-stack*"]:
        for d in sorted(glob.glob(os.path.join(ROOT, "runs", "bench", pat))):
            p = os.path.join(d, "results.json")
            if os.path.exists(p):
                with open(p) as f:
                    rows = json.load(f)
                for r in rows:
                    r.update(base_shares(r))
                runs[os.path.basename(d)] = rows
    if not runs:
        sys.exit("no results.json found")
    with open(TPL, encoding="utf-8") as f:
        tpl = f.read()
    a, b = tpl.index("/*DATA*/"), tpl.index("/*END*/")
    page = tpl[:a] + "/*DATA*/" + json.dumps(runs) + tpl[b:]
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    print(OUT, {k: len(v) for k, v in runs.items()})


if __name__ == "__main__":
    main()
