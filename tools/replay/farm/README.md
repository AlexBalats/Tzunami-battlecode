# Farm study scripts (18 Oct; extended 22 Oct)

These scripts produced the numbers in `docs/archive/FARM_18OCT.md`, `docs/nav/MAPS.md` §7 and `docs/nav/REPLAYS.md`.
They compare the two teams' farming in decoded ladder replays. They are analysis scripts: nothing in the bot uses them.

The engine wasm for `decode.mjs` is fetched by `tools/replay/fetch-engine.sh` (1.0.3 on 22 Oct; it decodes golems).

## Steps

Run every step from the repo root. `W` is a scratch folder.

1. **Decode each replay** to `W/dec/<first 8 hex of the match id>.json`:

   ```
   for d in replays_from_others/us_against_top/match-*; do
     id=$(basename $d | cut -c7-14)
     node tools/replay/decode.mjs $d/replay.repl26a W/dec/$id.json
   done
   ```

2. **Dump the map grids** to `W/maps/<map>.json` (`{"rows": [...], "w": W, "h": H}`; `#` wall, `o` hole, `A` altar).
   `mapjson.mjs` is dead (it needs the deleted `tools/mapgen`; `tools/navstats.py` and `teamnums.sh` still call it, so their map step fails too). Use the MAPDUMP grids: follow the steps in
   `tools/mapdump.inc` to get `W/maps_dump.json` (`{map: {"a": dump, "b": dump}}`), then

   ```
   python3 -I -c "import json,sys; d=json.load(open(sys.argv[1]))
   for m,v in d.items(): g=v['a']; json.dump({'rows':g['grid'],'w':g['W'],'h':g['H']}, open(sys.argv[2]+'/'+m+'.json','w'))" W/maps_dump.json W/maps
   ```

   Only the maps in `maps/` can be dumped; a ladder map not in the pool has no grid. The replays call `rushbait-v2`
   `rushbait`; the scripts try `<map>-v2.json` when `<map>.json` is missing.

3. **Build the per-game table:**

   ```
   FARM_GROUPS=tools/replay/farm/groups_18oct.txt \
     python3 -I tools/replay/farm/farm.py . W/maps W/farm.json W/dec/*.json
   ```

   `FARM_GROUPS` is optional: label files, each line `label id id ...` (first 8 hex of the match id). Without it
   every game goes in group `-`.
   - `order.py`, `legs.py` and `cohesion.py` (via `report.labels`) take several files, comma-separated. A game can
     then carry several labels (an opponent family, map-feature buckets, a half), and every table is printed for
     `ALL` and for each label.
   - `farm.py` takes **one** file only: it stores one label per game in `cl`, which `agg.py` splits on. A comma
     list fails with FileNotFoundError.
   - The 22 Oct files:
     - `groups_22oct.txt`: opponent families by draft;
     - `features_22oct.txt`: map buckets by size, contested share, groups per altar and need > S share, from
       `tools/mapstudy.py`, for all 57 games;
     - `halves_22oct.txt`: H1 / H2 of REPLAYS.

     To compare the halves, make one `farm.json` per half and run `agg.py`, `hpb.py` and `phase.py` on each. Run
     `order.py` and `legs.py` on all 57 with `FARM_GROUPS=…halves_22oct.txt,…groups_22oct.txt,…features_22oct.txt`.

4. **Read it out:**

   | Command | What it prints |
   | --- | --- |
   | `python3 -I tools/replay/farm/agg.py W/farm.json` | per game, all games, per group |
   | `python3 -I tools/replay/farm/fac.py . W/farm.json W/dec/*.json` | factor decomposition |
   | `python3 -I tools/replay/farm/rec.py . W/maps W/dec/*.json` | recall trips |
   | `python3 -I tools/replay/farm/legs.py . W/maps W/dec/*.json` | trips between takes; banks (bag, recall-bank, enemy near, channel broken, altar choice and detour; REPLAYS Q13) |
   | `python3 -I tools/replay/farm/order.py . W/maps W/decu/*.json` | next group vs the nearest live one, respawn latency, kills by camp type, circuits (Q11), waiting at respawns (Q12), damaged leaves (Q13), contests and steals (Q15) |
   | `python3 -I tools/replay/farm/hpb.py W/farm.json [W/maps_dump.json]` | takes by group HP and by kind × bodies, golem/monolith takes; with the dump, non-cluster takes by our `need` (REPLAYS §3) |
   | `python3 -I tools/replay/farm/cohesion.py W/dec` | bodies out of spawn, cluster sizes, allies near, partner stability (19 Oct) |
   | `python3 -I tools/replay/farm/phase.py W/farm.json W/dec` | bodies per gem take by phase and big groups, arrival spread; crews by kind × phase, how crews form and split (Q14), leg body-round mix, the opening per body to r300 |

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

`tools/arena.py` keeps each replay in `runs/arena/<run>/<map>-<A|B>/*.repl26a`. In the `-B` folders the first bot
played team B. Since 23 Oct (`docs/nav/ROUTING.md` §9) one script does steps 1 and 3 with the flip:

```
sh tools/replay/farm/arena_decode.sh runs/arena/<run> W          # W/dec, W/decu (us = team A), W/ren, W/farm.json
python3 -I tools/replay/farm/order.py . W/maps W/decu/*.json
python3 -I tools/replay/farm/agg.py W/farm.json
python3 -I tools/replay/farm/phase.py W/farm.json W/ren
```

- `flip.py DEC --arena OUT` reads the side from the `-A`/`-B` file name, so team A is always the arena's first bot.
- `farm.py` keys games by the first 8 characters of the file name, and `<map>-A`/`<map>-B` collide, so the script
  links the flipped games as `W/ren/g0000001.json` ... (`W/ren.txt` maps the ids back).
- About 20 s a game, so ~30 min for an 80-game run; a stopped run resumes where it left off.

The side-A games in one go (19 Oct): `sh tools/replay/farm/teamnums.sh runs/arena/<run> OUT_DIR` from the repo
root. Each arena `.repl26a` is a zip bundle: the script unzips the inner `replay.repl26a`, decodes it to
`dec/<map padded to 8 chars>.json` (farm.py keys games by `basename[:8]`), builds `farm.json` with an absolute
root (`$PWD`), then prints `phase.py` and `cohesion.py`. Side-B games still need the flip.

## Fight and economy measures (23 Oct, `docs/nav/LADDER_P4.md` §2, §8)

On flipped games (`decu`, team 0 = us) or `farm.json`, from the repo root:

```bash
python3 -I tools/replay/farm/freehit.py W/decu/*.json    # enemy champion in attack range: hit it / moved / nothing
python3 -I tools/replay/farm/mvatt.py W/decu/*.json      # move + attack in one round, per champion
python3 -I tools/replay/farm/noback.py W/decu/*.json     # hit by a champion and not hitting back: why
python3 -I tools/replay/farm/goldsrc.py W/decu/*.json    # gold income by source (camp, kill, tribute)
python3 -I tools/replay/farm/timeuse.py W/farm.json W/decu   # r150-600 body-rounds: take / walk / still / dead / tribute
python3 -I tools/replay/farm/takes.py W/farm.json        # takes by window and camp type
python3 -I tools/replay/farm/hpdeath.py W/decu/*.json    # max HP by round, deaths, time dead, banked (LADDER_P4 §9.1)
python3 -I tools/replay/farm/deaths.py W/decu/*.json [--list]  # each death's last 30 rounds: killers, alone, hit back
python3 -I tools/replay/farm/fights.py W/decu/*.json     # fights as episodes: bodies each side, who hit first, kills
python3 -I tools/replay/farm/campdmg.py W/decu/*.json    # damage per basic attack on camps, per champion and band
python3 -I tools/replay/farm/hitshare.py W/decu/*.json   # share of live rounds hitting a camp / a champion
python3 -I tools/replay/farm/elk.py W/farm.json W/decu   # elk takes r300+: bodies, clear rounds, HP lost, captured
python3 -I tools/replay/farm/shop.py W/decu/*.json       # first buy, gold spent by r150/300/600/1000, consumables, shard families
```

`hpdeath` and `deaths` need `decode.mjs` from 23 Oct: a champion row is `[idx, x, y, hp, alive, gold, gems, kills,
maxHp]` (index 8 is new). Re-decode older `dec/` files.

## Hoard, stuck and teleport measures (24 Oct, `docs/nav/LADDER_P4.md` §10)

```bash
python3 -I tools/replay/farm/bagrisk.py W/decu/*.json         # gems carried at the end; deaths per 1,000 live rounds by bag
python3 -I tools/replay/farm/stuck.py W/decu/*.json           # our bodies held within 1 tile for 40+ rounds, away from spawn
python3 -I tools/replay/farm/stall.py W/farm.json             # per game: gems captured each side, longest capture drought
python3 -I tools/replay/farm/tele.py W/maps W/decu/*.json     # each teleport: from, to, bag, the walk it saved
```

## The top-team KPIs and time use (p8, 24 Oct, `docs/nav/LADDER_P4.md` §11)

```bash
sh tools/replay/farm/arena_kpi.sh runs/arena/<run> W [MAX]    # decode 2 at a time (~3 s a game), flip, kpi.py
python3 -I tools/replay/farm/kpi.py W/decu/*.json              # camp / champion hits and casts per 100 live rounds, banks, bag, locks, opened fights, hoards
python3 -I tools/replay/farm/tu.py runs/arena/<run>             # TRACE 1 runs: body-rounds by goal x act (the `tu` line, main.cpp)
python3 -I tools/replay/farm/duel1.py runs/arena/<run>          # TRACE copy with the duel1 line: even 1v1s, candidate / chosen, P(lose)
```

`kpi.py` and `tu.py` need no map grids. `duel1.py` needs a copy whose `prices.cpp` Kill loop prints the `duel1` line
(the patch is in LADDER_P4 §11.1's description; it isn't in `bots/cpp`).


## cpp-p8's ladder losses: fights, gains by side, dash hops (24 Oct, `docs/nav/LADDER_P8.md`)

**`farm.py`'s capture gems over-count on some maps.** On 18 of 67 p8 losses, `caps` gave the winner 2–5× the gems it
banked (LADDER_P8 §1.3). The likely cause is the `Group` index vs `gem_of`, farm.py:95 [guess]. Until that's fixed,
read gem totals from `gain.py`, not from `stall` capgems, `takes`, `elk` types, `hpb` or `agg`.

```bash
python3 -I tools/replay/farm/oppsig.py W/decu/*.json              # per loss: opponent signature (recalls, locks, wards, teleports, rollovers), gap-open round
python3 -I tools/replay/farm/gain.py MAPS_DUMP.json W/decu/*.json # gems gained from bag increments, by side (ours / contested / theirs), gain size
python3 -I tools/replay/farm/engage.py W/decu/*.json              # per champion, an enemy within 3: hit a champion / cast / moved / moved away / idle, HP lost a round
python3 -I tools/replay/farm/flee.py W/decu/*.json                # hit with an enemy within 3: fight / flee / mixed next 3 rounds, died / killed within 20
python3 -I tools/replay/farm/fightctx.py W/decu/*.json            # fights with the HP ratio, bodies, focus, casts at the start; kills by starter and HP ratio
sh tools/replay/farm/cx_trace.sh cpp                           # TRACE copy bots/_trc with the per-round contact line cx (LADDER_P8 §9.1); cambc run _trc OPP --map M
python3 -I tools/replay/farm/cx.py team-a.stdout ...           # cx lines: contact rounds by choice, hits, moves away, switches, fight / flee / mixed runs
python3 -I tools/replay/farm/stance.py team-a.stdout ...       # stance lines: commit / break by P(lose) and odds, deaths within 10 rounds
python3 -I tools/replay/farm/hops.py MAPS_DUMP.json W/decu/*.json # dash hops over holes per team
python3 -I tools/replay/farm/hopmap.py MAPS_DUMP.json             # per map: the value a dash hop (8-round cooldown) brings 10+ rounds closer
```

- `MAPS_DUMP.json` = `{map: {"a": dump, "b": dump}}` from a scratch `bots/_mapdump` (steps in `tools/mapdump.inc`).
  The grid is in each dump.
- To split by tier, pass subsets of the files. LADDER_P8 §1.2 split them by margin: close = our score ≥ 0.65× theirs,
  crushed = below 0.35×.

## The top teams on our weak maps: group kinds, big takes, the wake test (24 Oct, `docs/nav/TOP_P9.md`)

On flipped games (`decu`, team 0 = us). They share `repcommon.py` (BFS walk fields, spawn sides); `pergame` needs the
`MAPS_DUMP`. To split by map feature, link the games of one feature into a folder and pass that folder's files.

```bash
python3 -I tools/replay/farm/gaintype.py W/decu/*.json             # gems by the kind of group taken (cluster / wolf / elk / golem / monolith), by phase
python3 -I tools/replay/farm/elkkill.py ELK W/decu/*.json          # each ELK (GOLEM, MONOLITH) kill: hitters, rounds, sessions, HP lost, max HP; by champion
python3 -I tools/replay/farm/bigtake.py W/decu/*.json              # whole takes of groups with 2+ elk/golems: hitters, rounds, HP lost, lowest HP share
python3 -I tools/replay/farm/wake.py W/decu/*.json                 # the wake test: HP lost a hitter-round by untouched big monsters alive in the group
python3 -I tools/replay/farm/campfocus.py W/decu/*.json            # monsters hit at once by 2+ bodies on one group; big monsters awake at once
python3 -I tools/replay/farm/crewhit.py W/decu/*.json              # crew size at camp hits per champion, work sites
python3 -I tools/replay/farm/clrcap.py W/decu/*.json               # main clearer -> capturer pairs, the capturer's share of its group's hits
python3 -I tools/replay/farm/spread.py MAPS_DUMP.json W/decu/*.json  # sites, walk from spawn and gems at r30..r600
python3 -I tools/replay/farm/pergame.py MAPS_DUMP.json W/decu/*.json # per game: tier, gains by side (own / contested / other), deaths, banks, pre-charged recall
python3 -I tools/replay/farm/idle.py MAPS_DUMP.json W/decu/*.json   # share of rounds each group stands alive and untouched, by kind and half (ours / contested / theirs)
python3 -I tools/replay/farm/banktrip.py MAPS_DUMP.json W/decu/*.json # tributes via spawn (recall-bank) vs direct, rounds from the last gain, shopped on the trip
python3 -I tools/replay/farm/front.py W/decu/*.json                 # Vesper with an enemy within 3: distance, a melee ally nearer, HP lost covered / uncovered
```

## The capture + recall overlap, emblems, the shop trigger, rollovers (25 Oct, `docs/nav/TOP_P9.md` §9)

`caprec`, `emb` and `shoptrig` are the side session's one-off queries (`docs/archive/TOP_TEAMS_R2.md`), copied
as they were. `fuelroll` reads the arena run folder, not decoded games.

```bash
python3 -I tools/replay/farm/caprec.py W/decu/*.json     # captures ending with the capturer home within 3 rounds (standing still: the overlap); recall arrivals
python3 -I tools/replay/farm/emb.py W/decu/*.json        # emblem completion rounds (1st..4th) and order per champion
python3 -I tools/replay/farm/shoptrig.py W/decu/*.json   # full-HP recall arrivals: gold deciles, share >= 120, rounds since the last gold rise
python3 -I tools/replay/farm/fuelroll.py runs/arena/RUN  # turn rollovers a game for the arena's first bot, from the bundles' fuel logs
```

## Round 3's queries and two new ones (26 Oct, `docs/nav/TOP_TEAMS_R3.md`, `docs/nav/TOP_P9.md` §10)

`cohes`, `contact`, `tbud`, `steal` and `killzone` are the round-3 side session's queries, copied as they were. All read
decoded games with team 0 = the studied team (`W/decu`, flipped). `egold` reads arena run folders.

```
python3 -I tools/replay/farm/cohes.py W/decu/*.json      # ally within 3 / 5 / 8 of live off-spawn bodies by phase; same nearest ally 10 rounds later (T6 64 % within 5 at r300-1000)
python3 -I tools/replay/farm/contact.py W/decu/*.json    # contact episodes: bodies within 6 of the first meeting point, more / equal / fewer, kills after (T6 2.00 v 1.57)
python3 -I tools/replay/farm/tbud.py W/decu/*.json       # time budget per live body-round (camp, cleared camp, walk, fight, tribute, dead); capture -> next camp hit
python3 -I tools/replay/farm/steal.py W/decu/*.json      # captures of groups the other team did most hits on (a capture = a gold rise off spawn: the overlap hides some)
python3 -I tools/replay/farm/killzone.py W/decu/*.json   # where kills happen (thirds of the spawn-to-spawn line), by phase
python3 -I tools/replay/farm/egold.py runs/arena/RUN     # earned gold r300 / r600 / r1000 and kills before r300 from stats.json (the overlap can't fool it); gold by body at r300
python3 -I tools/replay/farm/banker.py W/decu/*.json     # each body's share of the tributes (Submit gems), tributes, deaths, gems carried at death
```

## Teleport potential and contact rate (26 Oct, `docs/nav/TOP_P9.md` §10.5)

`portal_est` and `portal_greedy` read the 40 map grids (`maps_dump.json`, made with `tools/mapdump.inc`), not replays.
`hot` reads decoded games.

```
python3 -I tools/replay/farm/portal_est.py DIR                 # walk saved by the best single crystal jump per trip (spawn->group, group->altar), per map
python3 -I tools/replay/farm/portal_greedy.py DIR 8 m1,m2      # the same with the greedy local jump P3 uses (TP_GAIN 8 here; the bot uses 15)
python3 -I tools/replay/farm/hot.py W/decu/*.json              # contact rate per map: enemy within 8 of a live off-spawn body, r<150 / r<300 / all
```

## Our own ladder losses (26 Oct, `docs/archive/LOSSES_P10.md`)

`deathctx` and `contactact` read decoded games with team 0 = the studied team. `battery_us.sh` runs the whole battery on
our own ladder bundles (`flip.py` keeps us team 0 because each bundle holds our own stdout).

```
python3 -I tools/replay/farm/deathctx.py W/decu/*.json     # champion-kill deaths: allies / enemies within 5 the round before, HP share 5 rounds before, alone, outnumbered, camp hit / recall in the 10 rounds before, bag 20+
python3 -I tools/replay/farm/contactact.py W/decu/*.json   # at each contact episode: what our nearest body was doing (hitting a camp, walking outward / home, standing), alone or not
sh tools/replay/farm/battery_us.sh T MAPS_DUMP MAPS        # every farm script on T/dec + T/zips -> T/out/*.txt
```

## The p13 read's scripts (25 Oct, `docs/archive/LADDER_P13.md` §1.1)

After `lossmode.py` and `bands.py` (see their docstrings): `splitmech.py W` (the split mechanism per game, LADDER_P12
§3.2's rule as code plus "shut", and the family × stratum × mechanism clusters; writes `W/mech.json`), `early.py W` (the
first 300 rounds by result band, after splitmech), `matchup.py W/decu/*.json` (fights at equal numbers by champion
matchup). For an arena run, link `arena_decode.sh`'s `W/ren/*.json` into a `decu/` folder first (the arena names
`<map>-A.json` collide on their first 8 characters).

## Contact and economy splits (26 Oct, `other_stuff_for_now/RND_DRAFTS.md` §1, §7, §8)

On flipped games (team 0 = us), from the repo root:

```bash
python3 -I tools/replay/farm/contactd.py W/decu/*.json    # melee rounds by the nearest enemy's distance (1 / 2 / 3): share, and hit a champion
python3 -I tools/replay/farm/adjwhy.py W/decu/*.json      # adjacent and not hitting: moved away / nothing / left reach (found the parting shot)
python3 -I tools/replay/farm/d2why.py W/decu/*.json       # one step away: hit / moved away / tribute / chase
python3 -I tools/replay/farm/champecon.py W/decu/*.json   # per champion: gold (r300), gems captured, tributed, kills, deaths
python3 -I tools/replay/farm/killkit.py 300 W/decu/*.json # the enemy casts on each victim before its death (U = 300)
python3 -I tools/replay/farm/famsum.py W/decu             # losses by opponent draft family and map size
```

`decode.mjs` reads engine 2.0.0 (cambc 4.0) replays: 84 item types, 420-byte champion records. `tools/replay/mapfeat.mjs
ENGINE.wasm MAPDIR OUT.json` dumps every map's camps and groups (half map) for `tools/featcorr.py`.

## Group movement (27 Oct evening, `other_stuff_for_now/SQUAD.md` §6–8)

On flipped games (team 0 = the side to study; for other teams' ladder games flip with `tools/ladder/flip_team.py`):

```bash
python3 -I tools/replay/farm/squadmove.py W/decu LABEL [them]   # M1-M9: company by activity, linked groups, walking together, leads,
                                                               # joint arrivals, splits and rejoins, trips home, lone middle, contact,
                                                               # same-group share of camp hits by place (them = study team 1)
python3 -I tools/replay/farm/pairs.py W/decu                    # r300+: each champion's share alone and with each ally (within 6)
python3 -I tools/replay/farm/sharesize.py W/decu [them]         # r300+: camp hits by group size (1 / 2 / 3-4 / 5+ camps), share shared
python3 -I tools/replay/farm/timeact.py W/decu                  # r100+: per champion hit / walk / still / dead, both teams
```

## The three ways, the walk (27 Oct night, `other_stuff_for_now/TEAMFIGHT.md`)

On flipped games (team 0 = the side to study; `them` studies team 1). `grp.claims(d)` maps each capture to the camps near
the bodies that gained gems (`engine_groups` mislabels about half the groups).

```bash
python3 -I tools/replay/farm/teamfight.py W/decu LABEL [them] [U=R]   # engagements: size, focus, commit, time to kill, who leaves, per-body strength
python3 -I tools/replay/farm/farmeff.py W/decu LABEL [them] [champ|place]  # camp damage a round, damage a hit, captured gems, damage a gem
python3 -I tools/replay/farm/dmgfate.py W/decu LABEL [them]    # camp damage by fate (own / stolen / none), by place
python3 -I tools/replay/farm/budget.py W/decu LABEL [them] [champ]  # where live rounds go (hit, fight, camp, near, walk to farm / home / other)
python3 -I tools/replay/farm/bankleg.py W/decu LABEL [them]    # tributes: bag, out and back legs, leg rounds a gem
python3 -I tools/replay/farm/trips.py W/decu LABEL [them]      # walks home, recalls, tributes away from home
python3 -I tools/replay/farm/bigmap.py W/decu LABEL            # camp damage on 5+ groups by map and place, both teams
python3 -I tools/replay/farm/campsafe.py W/decu LABEL [them]   # hits from outside monster range, HP lost a hit, tank share
python3 -I tools/replay/farm/visits.py W/decu LABEL [them]     # sessions and bodies per claimed group
python3 -I tools/replay/farm/wake.py W/decu [them]             # HP lost v the group's Strength in range (which monsters hit)
python3 -I tools/replay/farm/trip.py W/decu LABEL [them]       # group-to-group trips v the shortest walk (passable = tiles anyone stood on)
python3 -I tools/replay/farm/gaps.py W/decu LABEL [them] [N=60]  # every stretch between productive rounds, waste beyond the shortest walk
python3 -I tools/replay/farm/jumps.py W/decu LABEL [them]      # jumps, hops over holes, walk rounds saved a game, per champion
python3 -I tools/replay/farm/tusum.py RUN BOT [champ]          # TRACE build: rounds per behaviour x activity
python3 -I tools/replay/farm/wander.py RUN W/decu BOT          # TRACE build: walking rounds by behaviour and how each leg ended
```
`trip.py` caches the passable tiles per map in `runs/tf/pass/` (built from every decoded game on disk).
