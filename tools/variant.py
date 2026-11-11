#!/usr/bin/env python3
"""Make a scratch copy of a bot with parameter overrides in its value.h (struct Params defaults).

  python3 -I tools/variant.py tz _tz_noopen opening_end=0 fight_ratio=2.0
  python3 -I tools/variant.py --clean          # delete every bots/_* scratch bot

Only `name = value` defaults inside value.h are touched; unknown names are an error.
"""
import os, re, shutil, sys

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def make(src, dst, overrides):
    s, d = os.path.join(REPO, "bots", src), os.path.join(REPO, "bots", dst)
    shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(s, d, ignore=shutil.ignore_patterns(".cambc"))
    # 9 Nov: the Desktop is iCloud-synced; evicted ("dataless") files can copy as 0 bytes under disk pressure. Verify every
    # source file copied at full size (retry, then fail) so an empty bot.cpp never reaches an upload.
    for root, _, files in os.walk(os.path.join(s, "src")):
        for f in files:
            a = os.path.join(root, f); b = os.path.join(d, os.path.relpath(a, s))
            for _ in range(5):
                if os.path.exists(b) and os.path.getsize(b) == os.path.getsize(a) and os.path.getsize(a) > 0:
                    break
                with open(a, "rb") as fa:
                    data = fa.read()
                with open(b, "wb") as fb:
                    fb.write(data)
            else:
                sys.exit(f"copy of {a} failed (size {os.path.getsize(a)})")
    p = os.path.join(d, "src", "value.h")
    text = open(p).read()
    for k, v in overrides.items():
        pat = re.compile(r"(\b(?:float|int)\s+" + re.escape(k) + r"\s*=\s*)([-0-9.e]+)(f?)")
        if not pat.search(text):
            sys.exit(f"unknown parameter {k}")
        text = pat.sub(lambda m: m.group(1) + v + ("f" if (m.group(3) or "." in v) and "." in v else ""), text, count=1)
    open(p, "w").write(text)
    return d


if __name__ == "__main__":
    if sys.argv[1:] == ["--clean"]:
        for n in os.listdir(os.path.join(REPO, "bots")):
            if n.startswith("_"):
                shutil.rmtree(os.path.join(REPO, "bots", n))
        sys.exit()
    src, dst, *kv = sys.argv[1:]
    assert dst.startswith("_"), "scratch bots start with _"
    make(src, dst, dict(x.split("=", 1) for x in kv))
    print(f"bots/{dst}")
