"""Build a round-by-round game page from a traced game (bots with a per-round `pos` trace line).

Usage: python -I tools/gameviz.py GAME_JSON OUT_HTML      (GAME_JSON as written by the extractor in runs/viz_rows)
Embeds the JSON into tools/viz/gameviz.html.
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(ROOT, "tools", "viz", "gameviz.html")


def main():
    src, out = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as f:
        data = f.read()
    with open(TPL, encoding="utf-8") as f:
        tpl = f.read()
    a, b = tpl.index("/*DATA*/"), tpl.index("/*END*/")
    with open(out, "w", encoding="utf-8") as f:
        f.write(tpl[:a] + "/*DATA*/" + data + tpl[b:])
    print(out, len(data) // 1024, "KB of data")


if __name__ == "__main__":
    main()
