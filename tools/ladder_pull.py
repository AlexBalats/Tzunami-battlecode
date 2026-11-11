#!/usr/bin/env python3
"""Pull ranked match lists and match summaries from the CAMBC platform (patch 5.0 only).

Raw data lives outside the repo (default ~/tzunami_data/ladder_5_0/).

  python3 -I tools/ladder_pull.py lists "Intercontinental Fish" Mite Pantheon
      pages each team's ranked games back to the patch (platform engineVersion 3.0.0 = cambc 5.0)
  python3 -I tools/ladder_pull.py summaries --last 100 "Intercontinental Fish" Mite Pantheon
      fetches the JSON summary of each team's last N 5.0 games (skips ones already on disk)

Gentle on the API: one request at a time, a pause between requests.
"""
import argparse, json, os, subprocess, sys, time

CAMBC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".venv", "bin", "cambc")
ROOT = os.path.expanduser("~/tzunami_data/ladder_5_0")
ENGINE = "3.0.0"
PAUSE = 1.0


def slug(team):
    return team.replace(" ", "_")


def run(args, cwd=None):
    for attempt in range(6):
        out = subprocess.run([CAMBC] + args, cwd=cwd, capture_output=True, text=True)
        if out.returncode == 0:
            return out.stdout
        if "429" not in out.stderr:
            break
        time.sleep(5 * (attempt + 1))  # rate limited: back off
    sys.exit(f"cambc {' '.join(args)} failed: {out.stderr.strip()}")


def split(team):
    """'Name=UUID' (for names the platform calls ambiguous) -> (name, query)."""
    return tuple(team.split("=", 1)) if "=" in team else (team, team)


def pull_lists(team):
    """All ranked games of `team` on the 5.0 engine, newest first -> lists/<team>.json."""
    team, query = split(team)
    games, cursor = [], None
    while True:
        args = ["matches", "list", "--team", query, "--kind", "ranked", "--limit", "50", "--json"]
        if cursor:
            args += ["--cursor", cursor]
        page = json.loads(run(args))
        new = [m for m in page["matches"] if all(t["engineVersion"] == ENGINE for t in m["teams"])]
        games += new
        cursor = page.get("nextCursor")
        if len(new) < len(page["matches"]) or not cursor:
            break
        time.sleep(PAUSE)
    os.makedirs(f"{ROOT}/lists", exist_ok=True)
    with open(f"{ROOT}/lists/{slug(team)}.json", "w") as f:
        json.dump(games, f)
    print(f"{team}: {len(games)} games on {ENGINE}, {games[-1]['createdAt']} .. {games[0]['createdAt']}")


def pull_summaries(team, last):
    team = split(team)[0]
    games = json.load(open(f"{ROOT}/lists/{slug(team)}.json"))[:last]
    d = f"{ROOT}/summaries"
    os.makedirs(d, exist_ok=True)
    got = 0
    for m in games:
        path = f"{d}/{m['matchId']}.json"
        if os.path.exists(path):
            continue
        run(["matches", "summary", m["matchId"], "--json"], cwd=d)  # writes match-<id>.json
        os.replace(f"{d}/match-{m['matchId']}.json", path)
        got += 1
        time.sleep(PAUSE)
    print(f"{team}: {len(games)} wanted, {got} fetched")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["lists", "summaries"])
    ap.add_argument("teams", nargs="+")
    ap.add_argument("--last", type=int, default=100)
    a = ap.parse_args()
    for t in a.teams:
        pull_lists(t) if a.what == "lists" else pull_summaries(t, a.last)
