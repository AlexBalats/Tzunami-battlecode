# strat: the price-list bot, thinking first

## What is here now (15 Oct, read this first)

**The bot that is on the ladder is `bots/strat`.** `bots/strat-imp` is a frozen copy of the build uploaded on
15 Oct evening as the ladder entry "strat imp" (`submissions/strat-imp.zip`): only `src/main.py`, no parts, do not
edit it; rebuild it from `bots/strat` when the next version goes up. Everything older (`bots/tzunami444`, `tzu`,
`core`, `v2`, `strat2`) is kept for history and is not developed (`docs/HANDOFF.md`, 14 Oct entries, say why).

| what | where |
| --- | --- |
| source, in numbered parts (edit these) | `bots/strat/parts/00_base.py` (trace, constants), `10_model.py` (draft: map model, 1,024-byte memory), `20_champs.py` (roster, profiles, phases, builds), `30_world.py` (per-turn world, dash, cast, reset), `40_prices.py` (the price list: FARM / BANK / KILL / JOIN / HUNT / HEAL / SHOP / WARD / HOLD, posture, `choose`, comms), `50_exec.py` (one executor per option), `90_main.py` (turn loop, stall guards, ticks) |
| the single file the engine runs | `bots/strat/src/main.py`, generated: `python -I tools/assemble.py --bot strat` after every edit to a part |
| run one game | `cambc run bots/strat tzunami444 --map collision` (`cambc run strat` does not resolve) |
| the light check (house rule) | `python -I tools/bench.py strat --vs tzunami444 --maps collision,corners,packs --rounds 300 --label X` and the same without `--rounds` for full games; `--baseline` diffs two labels; outputs in `runs/bench/<label>/` (git-ignored) |
| a parameter variant without editing | `python -I tools/variant.py strat NAME KEY=VALUE` makes `bots/_var-NAME` (git-ignored) |
| read a trace | `python -I tools/plog.py <bundle.repl26a or logs dir> [TAG ...]`; ladder logs are downloaded to `runs/ladder/` (git-ignored); lines look like `P|round|team|champ|tag|text` |
| upload | zip `src/main.py` only (`submissions/strat.zip`), upload in the browser; `TRACE` stays 1 (the ladder logs are how we learn) |
| how we change things | `HANDOVER.md` section "how we tweak": numbers first, rules only for something missing, one change per commit behind a constant, light check, the ladder decides |
| where we are | `HANDOVER.md` (dated entries, newest last), `LADDER_NOTES.md` (what the opponents do), `IMPROVEMENTS.md` and `STRAT2.md` (plans and their status) |
| the numbers | every tunable is a one-line constant in the parts, tagged [rules] / [measured] / [guess]; `PRICES.md` is the original price list (partly stale: the code is the reference) |

Feature flags in `40_prices.py` as of the last commit: `SMOOTH_ON` 1, `SUNK_ON` 1 (shipped 15 Oct night);
`CHAIN_ON` 0, `CENTRE_ON` 0, `SMOOTH_CHASE` 0 (built, off: did not beat the previous build locally). Each has its
HANDOVER entry with the check numbers.

Started 14 Oct 2026. Everything about the new strategy lives here: thinking, priorities, decisions, measurements,
and later the bot itself. Nothing in `bots/tzu` or `bots/core` is a reference; only their failures are
(`docs/HANDOFF.md`, 14 Oct entries).

## The idea in three lines

1. Each turn a champion answers one question: which of six options is worth the most **team gems per round**
   over the next ~10 rounds? Farm a group, bank, kill a carrier, hold an altar, shop, join an ally.
2. Each option has a price: a short formula from the rules and measured numbers. Roles (per champion) and
   modes (per map, per game state) are multipliers on prices, never new code paths.
3. Six dumb executors with timeouts. No stored intent beyond the current choice. Re-evaluate every turn.

## Files

| File | What |
| --- | --- |
| `README.md` | this: the idea, the procedure, where we are |
| `PRICES.md` | the six price formulas, their inputs, and every number's tag ([rules]/[measured]/[guess]) |
| `SCENARIOS.md` | single questions a price depends on, each answered by a scenario run, with the result |
| `DECISIONS.md` | dated log: what we decided, why, what it changed |
| `LADDER_NOTES.md` | what the bots that beat us actually do, classified by the six options |

## Two layers: baseline and posture

**Baseline** (how we treat the game, from the map, computed at draft, fixed for the game): ownership of every
altar and group (ours / theirs / contested by margin = D_them - D_us against a reaction distance of 8: vision 8
and a 5-turn recall mean an enemy seen at 8 is 7 rounds from touching us), bodies needed per group, chokes and
ward tiles from the enemy's shortest paths, recall-or-walk blocks, the static danger map, the regime
(few / many / pick altars relative to team size). `tools/mapmodel.py` prints and draws it (`runs/mapmodel/`).

**Posture** (how we respond, from enemy signals): a column of multipliers over the six prices. Postures never
override a price, only scale it (a zero stays zero: no chasing, no holding an empty altar). Every champion
computes the same posture from the same inputs, or the team splits. Signals must be observable with vision 8
and fit in the 8 shared bytes:

| Signal | Source | Says |
| --- | --- | --- |
| score gap | both teams' tributed gems [sdk] | ahead / behind, by how much |
| enemy presence on our half | sightings in shared bytes, decayed | farming our side or hunting us |
| enemy bags seen | gem_count of visible enemies [sdk] | fat carriers: kills worth more |
| death balance | our deaths vs theirs | losing fights or winning them |

Postures to start: **economy** (open maps, default), **punish** (fat carriers, we win fights), **defend**
(contested bank, or losing fights), **deny** (behind late: their tributes are the target). Tuning for a new
opponent = editing a column or a threshold.

## Build order

1. Map model at draft (`tools/mapmodel.py`, the user checks it against the visualiser).
2. The turn loop: six price functions, six dumb executors with timeouts, one broadcast byte per champion,
   the stuck backstop. Placeholder numbers. Judged vs tzu, every map, both sides.
3. The user's values become posture columns and per-champion multipliers; watch replays, adjust numbers.
4. Mode detection (regime from step 1, score from play).
5. Draft picks from the map model, last.

## Procedure

1. Price list on paper (`PRICES.md`).
2. Scenario harness answers the open numbers (`SCENARIOS.md`, `tools/scenario.py`).
3. The bot is the argmax over prices + one 8-byte broadcast of (option, target) per champion.
4. Learning loop: for every bad outcome, which price was wrong in hindsight; fix the number, never add a rule.
5. Specialise per champion only after the argmax bot beats tzu on every map, and only as price terms.

## Status

- Steps 1-4 done (14-15 Oct), see HANDOVER.md; step 5 (draft picks from the map model) not started.
