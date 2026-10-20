# strat: our bot

## What is here now (19 Oct, read this first)

- **`bots/strat` is the bot we build.** The ladder entry is `submissions/strat-sw.zip`, with a frozen copy in
  `bots/strat-sw`. That copy is **the bar**: the next strat must beat it.
- **Next build: `TEAM_LOOP.md`.** The farm decision is rewritten as a team decision (crews by group size, opening
  ball, gather, respawn timing, recall at 50 %, C&I). Step 0 deletes every off flag's code. We work by redesign, not by
  flags, and judge by games won vs strat-sw plus the replay numbers (`TEAM_LOOP.md` → How we judge).
- History: `docs/archive/strat/` (HANDOVER, IMPROVEMENTS, STRAT2, DECISIONS, LADDER_NOTES, SCENARIOS, PORTFOLIO,
  ROUTE) and `docs/archive/HANDOFF_to_19oct.md`.
- Workspace on cambc 2.2.4, the ladder's version.

| what | where |
| --- | --- |
| source, in numbered parts (edit these) | `bots/strat/parts/00_base.py` (trace, constants), `10_model.py` (draft: map model, 1,024-byte memory, `bodies_needed`), `20_champs.py` (roster, profiles, phases, builds), `30_world.py` (per-turn world, dash, cast, reset), `40_prices.py` (the price list: FARM / BANK / KILL / JOIN / HUNT / HEAL / SHOP / WARD / HOLD, posture, `choose`, comms), `50_exec.py` (one executor per option), `90_main.py` (turn loop, stall guards, ticks) |
| the file the engine runs | `bots/strat/src/main.py`, generated: `python3 -I tools/assemble.py --bot strat` after every edit to a part, then a separate `python3 -I tools/assemble.py --bot strat --check`. **Single file:** the split build (`--split`) measured worse on the same code (`docs/FARM_18OCT.md` → Ladder review round 2), so it is not shipped |
| run one game | `cambc run bots/strat bots/strat-sw --map collision` (`cambc run strat` does not resolve) |
| judge a build | `python3 -I tools/arena.py strat strat-sw --jobs 2` (17 maps × 2 sides), then the replay numbers (`TEAM_LOOP.md` → How we judge) |
| read a trace | `python3 -I tools/plog.py <bundle.repl26a or logs dir> [TAG ...]`; lines look like `P|round|team|champ|tag|text` |
| replay numbers | `tools/replay/farm/README.md`: decode, `farm.py`, `cohesion.py`, `phase.py`, `ladder_sum.py` |
| upload | zip `src/main.py` (e.g. `submissions/strat-sw.zip`); the user uploads in the browser; `TRACE` stays 1 (the ladder logs are how we learn) |
| comms and draft memory | `MEMORY_LAYOUT.md` (1,024 draft bytes; the 8 shared bytes) |
| fuel | `FUEL_MODEL.md` |
| roles | `ROLES.md`: a role per champion; `KIT_ON`, `ROLE_BUILD`, `LIVE_STEP`, `ROLE_PRICE` are on |
| map types | `MAPTYPES.md`: the 17-map survey, gem-gated maps |
| the numbers | every tunable is a one-line constant in the parts, tagged [rules] / [measured] / [guess] / `PROVISIONAL A#`; `PRICES.md` is the original price list (partly stale: the code is the reference) |
| field of opponents | `field.txt` for `tools/field.py` (strat, strat-sw, tzunami-lite, tzunami444, starter, two strat proxies) |

Flags still in the parts (all 1, kept from strat-sw; delete one when its behaviour is redesigned, never add new
ones): `KIT_ON`, `SMOOTH_ON`, `SUNK_ON`, `ROLE_BUILD`, `ROLE_PRICE`, `LIVE_STEP`, `SCAN_WARD`, `RECALL_COST`,
`PEEK_ON`, `SPLASH_ON`. Step 0 deleted every off flag; step 1 deleted `GROUP_HANDOFF` (handoff is unconditional) and
`ONEWAY_PARTNERS` (replaced by crews, `TEAM_LOOP.md` T1–T3).

## The idea in three lines

1. Each turn a champion answers one question: which option is worth the most **team gems per round** over the next
   ~10 rounds? The options are: farm a group, bank, kill a carrier, hold an altar, shop, join an ally.
2. Each option has a price: a short formula from the rules and measured numbers. Roles (per champion) and modes (per
   map, per game state) are multipliers on prices.
3. Dumb executors with timeouts.

**What changes with the team loop:** the farm price becomes a crew's team rate, and the bodies are assigned to crews
through the slot bytes instead of each choosing alone (`TEAM_LOOP.md`).

## Two layers: baseline and posture

**Baseline** (from the map, computed at draft, fixed for the game). The draft computes:
- ownership of every altar and group: ours / theirs / contested, by margin = D_them − D_us against a reaction
  distance of 8;
- bodies needed per group;
- chokes and ward tiles;
- recall-or-walk blocks;
- the static danger map;
- the regime.

`tools/mapmodel.py` prints and draws it (`runs/mapmodel/`).

**Posture** (from enemy signals): a column of multipliers over the prices. It never overrides a price, only scales
it. Every champion computes the same posture from the same inputs. The inputs are:
- the score gap (`global_submitted_gems()` [sdk]);
- enemy sightings in shared bytes 5–6;
- enemy bags seen (`gem_count` [sdk]);
- the death balance.
