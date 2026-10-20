# Farm study scripts (18 Oct)

These scripts produced the numbers in `docs/archive/FARM_18OCT.md`. They compare the two teams' farming in decoded ladder replays.
They are analysis scripts: nothing in the bot uses them.

## Steps

Run every step from the repo root. `W` is a scratch folder.

1. **Decode each replay** to `W/dec/<first 8 hex of the match id>.json`:

   ```
   for d in replays_from_others/us_against_top/match-*; do
     id=$(basename $d | cut -c7-14)
     node tools/replay/decode.mjs $d/replay.repl26a W/dec/$id.json
   done
   ```

2. **Dump the map grids** to `W/maps/<map>.json`:

   ```
   node tools/replay/farm/mapjson.mjs . W/maps maps/*.map26a
   ```

   The replays call `rushbait-v2` `rushbait`. The scripts handle this by trying `<map>-v2.json` when `<map>.json` is
   missing.

3. **Build the per-game table:**

   ```
   FARM_GROUPS=tools/replay/farm/groups_18oct.txt \
     python3 -I tools/replay/farm/farm.py . W/maps W/farm.json W/dec/*.json
   ```

   `FARM_GROUPS` is optional. It groups games by opponent; without it every game goes in group `-`.

4. **Read it out:**

   | Command | What it prints |
   | --- | --- |
   | `python3 -I tools/replay/farm/agg.py W/farm.json` | per game, all games, per group |
   | `python3 -I tools/replay/farm/fac.py . W/farm.json W/dec/*.json` | factor decomposition |
   | `python3 -I tools/replay/farm/rec.py . W/maps W/dec/*.json` | recall trips |
   | `python3 -I tools/replay/farm/legs.py . W/maps W/dec/*.json` | trips between takes |
   | `python3 -I tools/replay/farm/hpb.py W/farm.json` | takes by group HP |
   | `python3 -I tools/replay/farm/cohesion.py W/dec` | bodies out of spawn, cluster sizes, allies near, partner stability (19 Oct) |
   | `python3 -I tools/replay/farm/phase.py W/farm.json W/dec` | bodies per gem take by phase and big groups, arrival spread (19 Oct) |

## Conventions

- **Team A is us.** That is how the ladder downloads come.
- **Takes:**
  - A take goes to the team with most of the hits on that group of camps.
  - Its bodies are that team's champions who hit it.
- **Walking distance:** an 8-neighbour BFS where walls, holes and altars are blocked.
- **Body-round classes:** heuristic, read from the events and positions. See `farm.py`.

## Our own ladder games (19 Oct)

Ladder bundles (`replays_from_others/<bot>/match-*.zip`) hold our logs only, and we are team B in about a third of
them. Unzip each into `W/zips/match-<id>/`, decode as step 1, then make team 0 = us **before** step 3:

```
python3 -I tools/replay/farm/flip.py W/dec W/zips W/decu      # side from team-a/b.stdout in each bundle
FARM_GROUPS=... python3 -I tools/replay/farm/farm.py . W/maps W/farm.json W/decu/*.json
python3 -I tools/replay/farm/ladder_sum.py W/farm.json W/zips  # by map type, opponent, team size; death modes
```

## Our own arena games

`tools/arena.py` keeps each replay in `runs/arena/<run>/<map>-<A|B>/*.repl26a`. Decode them as step 1. In the `-B`
folders the first bot played team B; `flip.py` reads the side from ladder bundles, so for arena games swap the teams
by folder name (a small change to `flip.py`, not written yet) before `farm.py`, `cohesion.py` and `phase.py`.

The side-A games in one go (19 Oct): `sh tools/replay/farm/teamnums.sh runs/arena/<run> OUT_DIR` from the repo
root. Each arena `.repl26a` is a zip bundle: the script unzips the inner `replay.repl26a`, decodes it to
`dec/<map padded to 8 chars>.json` (farm.py keys games by `basename[:8]`), builds `farm.json` with an absolute
root (`$PWD`), then prints `phase.py` and `cohesion.py`. Side-B games still need the flip.
