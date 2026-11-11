#!/usr/bin/env python3
"""Download and decode the replays of a scrim label's games (one cambc call at a time).

  python3 -I tools/replay/fetch.py LABEL [--limit N]

For each game in ~/tzunami_data/scrims/LABEL.jsonl: `cambc matches download` into
~/tzunami_data/replays/LABEL/<match>.zip, then decode its replay.repl26a with tools/replay/decode.mjs into
<match>.jsonl.gz (the visualiser assets are in ~/tzunami_data/vis; see tools/replay/README.md). Prints a manifest line
"path:our_team_index" per game for tools/replay/fights.py.
"""
import argparse, gzip, json, os, subprocess, sys, time, zipfile

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CAMBC = os.path.join(REPO, ".venv", "bin", "cambc")
DATA = os.path.expanduser("~/tzunami_data")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("label")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--redecode", action="store_true", help="decode again from the kept zips (after a decoder change)")
    a = ap.parse_args()
    out = f"{DATA}/replays/{a.label}"
    os.makedirs(out, exist_ok=True)
    rows = [json.loads(l) for l in open(f"{DATA}/scrims/{a.label}.jsonl")]
    if a.limit:
        rows = rows[: a.limit]
    man = []
    for r in rows:
        m = r["match"]
        z, dec = f"{out}/{m}.zip", f"{out}/{m}.jsonl.gz"
        if a.redecode and os.path.exists(z) and os.path.exists(dec):
            os.remove(dec)
        if not os.path.exists(dec):
            if not os.path.exists(z):
                for attempt in range(5):
                    p = subprocess.run([CAMBC, "matches", "download", m, "-o", z], capture_output=True, text=True)
                    if p.returncode == 0 and os.path.exists(z):
                        break
                    time.sleep(5 * (attempt + 1))
                else:
                    print(f"download failed {m}: {p.stderr.strip()[:200]}", file=sys.stderr)
                    continue
                time.sleep(0.8)
            inner = f"{out}/{m}.repl26a"
            try:
                with zipfile.ZipFile(z) as zf:
                    name = next(n for n in zf.namelist() if n.endswith("replay.repl26a"))
                    with zf.open(name) as src, open(inner, "wb") as dst:
                        dst.write(src.read())
            except Exception as e:  # noqa: BLE001
                print(f"bad bundle {m}: {e}", file=sys.stderr)
                continue
            p = subprocess.run(["node", f"{REPO}/tools/replay/decode.mjs", f"{DATA}/vis", inner], capture_output=True)
            os.remove(inner)
            if p.returncode != 0:
                print(f"decode failed {m}: {p.stderr.decode()[-300:]}", file=sys.stderr)
                continue
            with gzip.open(dec, "wb") as f:
                f.write(p.stdout)
        man.append(f"{dec}:{0 if r['side'] == 'a' else 1}")
    with open(f"{out}/manifest.txt", "w") as f:
        f.write("\n".join(man) + "\n")
    print(f"{len(man)} games -> {out}/manifest.txt")


if __name__ == "__main__":
    main()
