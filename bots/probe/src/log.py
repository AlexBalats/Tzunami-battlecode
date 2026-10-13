"""One parseable line per fact: P|round|team|body|tag|json."""
import json

import cambc

_TEAM = None


def team_letter():
    global _TEAM
    if _TEAM is None:
        try:
            _TEAM = "AB"[cambc._bc.my_team()]
        except Exception as e:
            return "?" + type(e).__name__
    return _TEAM


def rec(obj):
    """Turn an SDK record into plain data for logging."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj if not isinstance(obj, float) else round(obj, 3)
    if isinstance(obj, (list, tuple)):
        return [rec(x) for x in obj]
    if isinstance(obj, cambc.Vec2):
        return [obj.x, obj.y]
    out = {}
    for name in dir(obj):
        if name.startswith("_"):
            continue
        try:
            value = getattr(obj, name)
        except Exception:
            continue
        if callable(value):
            continue
        out[name] = rec(value)
    return out or repr(obj)


def log(tag, **data):
    try:
        rnd = cambc.round_number()
    except Exception:
        rnd = -1
    body = "draft"
    try:
        if not cambc.is_draft():
            body = str(cambc.me().champion_name()).replace("ChampionType.", "")
    except Exception:
        pass
    try:
        text = json.dumps(data, default=repr)
    except Exception as e:
        text = repr(data)
    print(f"P|{rnd}|{team_letter()}|{body}|{tag}|{text}", flush=True)
