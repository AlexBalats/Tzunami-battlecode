"""Print the probe bot's log lines (P|round|team|body|tag|json) from a replay bundle.

Usage: python3 -I tools/plog.py <bundle.repl26a or directory> [TAG ...]
A directory means its newest bundle. Bots' stdout is only saved for games that finish
(not with --rounds), and it holds one null byte per turn, which this strips.
"""
import glob
import os
import sys
import zipfile

path = sys.argv[1]
if os.path.isdir(path):
    path = max(glob.glob(os.path.join(path, "*.repl26a")), key=os.path.getmtime)
tags = set(sys.argv[2:])
bundle = zipfile.ZipFile(path)
for name in ("team-a.stdout", "team-b.stdout"):
    if name not in bundle.namelist():
        continue
    text = bundle.read(name).decode("utf-8", "replace").replace("\x00", "\n")
    for line in text.splitlines():
        if not line.startswith("P|"):
            if line.strip() and not tags:
                print("RAW", name, line[:300])
            continue
        if not tags or line.split("|")[4] in tags:
            print(line)
