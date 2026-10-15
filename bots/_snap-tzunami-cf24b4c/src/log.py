"""One parseable line per fact: P|round|team|body|tag|json (read with tools/plog.py)."""
import json

import cambc

_ME = []


def log(tag, **data):
    if not _ME:
        _ME.append("AB"[cambc._bc.my_team()])
        from world import cname
        _ME.append(cname(cambc.me()))
    try:
        text = json.dumps(data, default=repr)
    except Exception:
        text = repr(data)
    print(f"P|{cambc.round_number()}|{_ME[0]}|{_ME[1]}|{tag}|{text}", flush=True)
