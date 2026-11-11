# Catch-up: everything we know, as of 28 Oct 2026 (night)

For a teammate (human or Claude Code) picking the project up cold. A map of what is known, measured and tried, not a
plan. Every number is from our own matches or decoded replays unless tagged [rules] (the handbook, `GameRules.md`) or
[guess]. Deeper notes are linked; `CLAUDE.md` holds the working rules and the full file index.

## 1. Where we stand

- **Live:** v62 = `bots/cpp-p17` (the teammate builds on `bots/cpp` from here; v63 uploaded 28 Oct, listed inactive).
  Ladder rank **86, 1,886** (28 Oct night). Reference points: #1 Mite 2,433, #2 fish 2,400, #10 2,255, #30 2,072,
  #50 ~2,000. ~800 teams.
- **Calendar:** sprint lock 31 Oct; international qualifiers 4 Nov; UK qualifiers 11 Nov; finals 18 Nov. Tournaments use
  **unseen maps**: nothing map-specific in code, ever.
- **Patch:** cambc 4.0.0 / engine 2.0.0, 70 maps (`docs/redo/00_PATCH_4_0.md` lists every 4.0 change). After any SDK
  update wipe every `bots/*/.cambc` (stale wasm idles the bot).
- **Nothing from the last two sessions was kept.** All experiments are reproducible from patches in `docs/redo/patches/`.

## 2. The game, the parts that decide it

Draft 3–5 champions; kill monster camps, stand on a cleared group's spawn tile 5 rounds to capture its gold and gems
(split among allies there); tribute gems at altars (channel ceil(gems/10) rounds); first to 1,000 tributed wins, else
most at round 2,000 [rules]. A death drops your bag to the killer (+100 gold) and benches you 60 rounds; camp kills
destroy carried gems. Damage wakes a whole group; monsters hit the nearest champion in range and don't chase. Shared team
memory is **8 bytes** at runtime (+1,024 written in the draft). Vision isn't shared. Compute is fuel-capped per turn
(~100k for C++, unfinished turns roll over). Dashes cross holes, never walls; teleport crystals cross anything.

## 3. The repo

| Where | What |
| --- | --- |
| `bots/cpp/src/` | The bot (C++, ~4.8k lines). `main.cpp` loop → `sense` (snapshot) → `prices` (every option priced in team gems a round) → `upd` (choose, with hysteresis, the fight stance) → `beh` (execute) → `nav` (every move and dash: distance fields, windows, danger boards). `model` = clear model (rounds and damage to take a group with k bodies). `draft` = picks + map model + the 1,024-byte record. `comms` = the 8 bytes (each body's slot code + target). `kit`/`champs` = per-champion abilities and profiles. |
| `bots/cpp-p13/15/16/17` | Frozen past entries (p17 = live). `bots/spar-*` = style sparring bots made from our own code (`// SPARRING` edits). |
| `tools/arena.py` | A v B on all 70 maps, both sides (140 games, ~40 s). `tools/tune.py` = paired, jittered judge and constant overrides (`build`, `full`, `--fresh`). `tools/spsa.py` = SPSA tuner. `tools/lab.py` = fight lab. |
| `tools/replay/` | `decode.mjs` (replay → JSON), `arena_dec.sh` (decode + flip an arena run), `dash.py` (the KPI dashboard). `tools/replay/farm/` = ~125 query scripts; `README.md` there lists them by topic. |
| `tools/ladder/` | CLI ladder access: match lists and downloads of **any** team's games, scrims v any team's live bot (50 groups of 5 an hour, they always play our live bot), `perf.py` (ladder rating per submitted version). Needs `.venv/bin/cambc login`. |
| `docs/HANDOFF.md` | Session log, newest on top. `other_stuff_for_now/*.md` = the recent notebooks (below). `docs/archive/` = history. `docs/Champions/` is the user's; don't edit. |

Build `.venv/bin/cambc build cpp`; play `python3 -I tools/arena.py cpp cpp-p17 --jobs 2`; judge
`python3 -I tools/tune.py full NAME --base cpp-p17 --opp cpp-p15` (1,120 paired games, ~10 min; `--fresh` = held-out
seeds). A TRACE build (`#define TRACE 1` in `types.h`) prints decision lines into the replay bundle's stdout
(`tools/replay/farm/tusum.py`, `wander.py` read them). Keep `--jobs 2`; delete `runs/` and `bots/_*` when done.

## 4. How the bot got here (ladder performance per version, `tools/ladder/perf.py`)

| Version | Ladder | What it added |
| --- | --- | --- |
| p4 (v52) → p6 (v54) | 1,592 → 1,713 | Routing pieces (respawn timing, altar on the way, capture guard); Bruiser builds, melee move+attack in one turn, ranged safe shots, Vesper farms all game |
| p8 (v55), p9 (v56) | 1,751, 1,725 | Dash on every cooldown, the draft Varg / Vesper / Marcella / Heart of Ruin / Vendetta; the engagement stance (commit / break held 6 rounds) |
| p10 (v57) | 1,817 | Capture + recall overlap, Treasure → Jungle items |
| p12 (v58), p13 (v59) | 1,849, 1,848 | The gate fix, group fix; SPSA over 12 constants |
| p15 (v60) | 1,870 | Draft by team size (Vesper > Vendetta > Heart of Ruin, + Marcella on 4, + Varg on 5); the parting shot (a melee leaving a fight swings first) |
| p16 (v61), p17 (v62) | 1,884, 1,893 | Marcella as nuker-banker, the ladder's item builds, shared big groups; team-Strength need model, end-race bank |

The big gains came p4 → p10, mostly fights and per-body strength. Since p12 the gains have been small.

## 5. The judge (read before trusting any number) — `other_stuff_for_now/JUDGE.md` §7–8

- **Local results predict the ladder, compressed.** Every shipped version replayed v fixed references (spar-fight,
  spar-fish): local Elo correlates with ladder performance at r = 0.96–0.98, slope **~0.3**. So +20 on the ladder ≈ +70
  local Elo ≈ +10 win points v a 50 % opponent. Most single pieces we try read ±2–5 points: below ladder visibility.
- **Noise:** one 140-game run swings ±5 games; paired SE on 1,120 games ≈ 1.5–2.7 win points (map-clustered). A
  same-bot scrim A/B of 245 games swung 113 v 98. Head-to-head v the previous version is non-transitive (p15 beat p13
  88–52 by punishing a p13-only habit).
- Per-map outcomes are near-fixed per build; any code edit reshuffles them (fuel changes timing). Rollovers matter:
  check `Turn rollover` events when a change adds per-turn work.

## 6. What the gap is, measured — `other_stuff_for_now/TEAMFIGHT.md`, `SQUAD.md`, `LOSSES_P15.md`

Three data sets: the top 7's ranked games, v62's 150 scrims v the top three (11 wins), 245 scrims v ranks 45–99 ("our
band", ~46 % wins), plus 240 v NEETCoders / Claudus (17 wins).

- **Against our band the game is nearly level.** Camp damage 70k v 73k a game, captured gems 783 v 853, we win fights at
  every engagement size, deaths 7.0 v 9.7. The one consistent hole: the **middle** (same share of rounds there, 15 v 24
  gems per 100 body-rounds; v ranks 31–48 by r300, 34 v 109 middle gems).
- **Against the top three everything is 2–3× and it compounds.** Captured gems per body-round 3×: 1.6× from camp damage
  a round, 2× from damage per gem. Their bodies in fights: +20 % max HP, +30 % damage a hit, +16 % hits a round (level at
  r ≤ 150, diverging with their economy).
- **Fight coordination is not the gap.** Focus fire (2+ hitters on one target 75–77 % ours, 72–86 % theirs), commit
  spread, time to kill: level with the top 7.
- **Big groups:** 5+ camp groups are 36–44 % of the top three's camp hits, 22–28 % of ours. Per map, whole groups we
  never take (middle and own side), taken by them in one visit with more bodies (2.25–2.52 v 1.95–2.07). Our clear model
  overstates monster damage ~2.3× (monsters land ~0.55 × Strength in range; our lone clears lose ~0.4 of predicted), so
  big groups price out. **But** correcting it lost: that overstatement is the bot's only margin against enemies arriving
  mid-take (deaths rose +0.4–0.7).
- **Movement:** total waste beyond the shortest walk is level (~160–190 rounds a body-game, both sides). Top teams hop
  holes with the dash 1.6–2.3× as often (Claudus ~7×); we built hop routes that reached Claudus's hop rate, and they
  lost (the real saving on our maps is a few rounds a trip). Our home exits are a little slower; we loop home → home
  with nothing done more (23–26 v 9–17 rounds a body-game).
- **The squad (fish, Mite):** a squad = a shared take of a big group (49–61 % of their hits after r300 have an ally on
  the same group, ours 32 %); they arrive at contact outnumbering (fewer bodies 17–23 % of contacts, ours 31 %).
- **Smaller signals:** their tribute bags are 36–64 gems, ours 28 (more income between trips, same trip count); their
  Marcella earns ~4× our gold and nukes ~650 late; dead time 11 % of our body-rounds v 5 % in ladder losses.

## 6a. The 28 Oct analysis (all our ranked games, the climbers, the top 10) — `other_stuff_for_now/ANALYSIS.md`

Read from the platform's match summaries (`cambc matches summary`: any game's per-champion stats in 0.3 s) and the top 160
teams' match lists at five time points; supersedes parts of §6 where they disagree.

- **The opening is the gap** (29 Oct correction: *not* walking; map-matched, it is parallelism: r0–100 takes 4.0 v 7.1, groups in
  work 0.77 v 1.04–1.09; our stack mode; a stack-off build lost −7.4 locally, ANALYSIS §7). Camp damage by r300 −26 % v the top two, −10 % v our band (in every era
  since 21 Oct); gems by r300 127 v 180–220 (top). Our crew moves 58–70 % of r0–300 and hits camps 8–15 % (Mite's 37–49 %
  and 12–22 %). Our losses are decided by r300 (their gold 1,200 v our 818). Deaths before r300 are level.
- **Vesper is fine; the crew is not.** Our Vendetta / Heart of Ruin collect a third to a half of the top two's gems a live
  round and spend 30–90 gold by r300 (theirs 120–225); captures and gold go to Vesper and Marcella.
- **Big / long maps: contested big groups never visited** (00expanse 0 / 68 since 24 Oct: the opponent takes 704 of its
  1,004 gems from two corner 5-camp groups our bodies never go near). S5 and 5,000+ tile maps have been our weakest in every
  era (S5 −25 to −30, 5,000+ −60 to −130 relative). The local mirror can't see it.
- **The climbers** (+200–370 in 1–3 days, several from below us) gained evenly on every map type, mostly in the opening or
  in deaths. Three switched every farming body Treasure → Prospector at their jump; measured, Prospector pays only ~+4.5 % a
  capture.
- **The draft outlier:** Ryth is in 61–77 % of every band's S5 games; we never draft it (Varg 100 %, others 12–25 %).

## 7. What was tried and lost (so it isn't redone blind; "lost" = in that form, on that day's judge)

| Idea | Result | Our reading |
| --- | --- | --- |
| Four squad forms (follow the leader, priced follow, big takes only, + fight joins), SQUAD §7–8 | −30 games of 140 v p17; one that didn't lose made no squad | +2 deaths a game for every champion; the squad arrived as separate fights |
| Calibrated clear model (`MON_HIT` 0.5 / 0.65) + SPSA re-tune | −3.2 / −0.4 / −5.7 win pts | the overstatement doubles as the exposure margin |
| Dash held for hops; portal routes (3 forms, `P18_portals_v2.diff`) | −3.0; −5.8 / −4.0 / −3.3 | mechanism landed, saving small, costs (waits, held dashes) larger |
| Exposure price on routes (6 forms, ROUTING §5), session takes, hold-what-you-clear, cluster gold | all lost | — |
| Pack farming, Cassi & Issac, fish's bank rule, Prism / Willow / stun lines, Tavi, team-6 fight builds | level or lost | — |
| Provoke guard, siege, opening discipline, reach by rate, far-bank, brave farming | lost or neutral | — |

Patches: `docs/redo/patches/` (names match the notebooks). Some of these may be right ideas built wrong; the notebooks
say how each was built.

## 8. Open questions (unranked, unsolved)

- What would let a big take be safe without the inflated damage, i.e. what does an exposure estimate need to know,
  given vision isn't shared and memory is 8 bytes?
- Why does our per-body damage on camps fall behind from r150 on: items, gold flow (the capture handoff puts gold on
  Vesper), or the champions' builds? *(28 Oct: it's the crew, from the opening: walking and gold flow, ANALYSIS §3.)*
- Why does the middle convert worse against our band when time spent there is equal?
- Is there a draft or team shape we haven't tried that turns the 2–3× compounding around, rather than chasing it?
- What do top teams do in the first 150 rounds that we don't (the opening funnel, early fights: P14 Part 3)? *(28 Oct:
  they walk less and hit more; early fights are level now, ANALYSIS §3.5.)*
- Anything nobody has looked at: the decoder and the CLI give every team's replays; scrims can target any style.

## 9. Conventions (from the user; `CLAUDE.md` has all of them)

- **Never upload or activate a bot** without the user saying so. The user commits.
- Generalise: no map names, coordinates or per-map policies. No other teams' code (replays and scrims are fine).
- Redesign pieces that are wrong by construction instead of stacking flags; delete dead code (git has it).
- Tag claims [rules] / [sdk] / [measured] / [guess]; keep docs and code in sync; cite Art of War principles (`P#`,
  `docs/ART_OF_WAR.md`) on strategic code.
- Be gentle with the laptop: `--jobs 2`, one judge at a time, clean `runs/` and `bots/_*` after.
- iCloud drops `* 2.cpp`-style copies into the repo: `find bots -name '* [0-9]*'` before building.
