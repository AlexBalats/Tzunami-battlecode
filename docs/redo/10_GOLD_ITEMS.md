# 10. R9: the draft fuel crash, then gold & items (21 Oct)

Session 8. Part 1 fixes a crash that lost R8 games outright. Part 2 is the gold & items design, decided with the
user before any code. Tags as in `CLAUDE.md`; **[model]** marks a calculation from our own numbers, not a game fact.

## 1. The draft fuel crash (Part 1)

### 1.1 What happened [measured, game 2458999d, 01shortcut]

- Draft turn 1 used 23.83M of its 23.84M fuel; 10.9M of that went to the `altar` stage.
- The turn ran out, so only pick 1 was ours (the engine made the rest) and the draft memory was never written.
- In play, `w.d = None` made `stack_mode` raise on every turn: the team stood still until round 101 and lost 0–1019.

**Cause.** 01shortcut has 2 altars and 21 groups. The nearest altar of a tile was found by descending the all-altar
field with `next_move_from`, step by step: 14 groups needed a descent, 903 steps at ~10k fuel each [measured].

### 1.2 The fix (`80_draft.py`, `10_model.py`)

1. **Nearest altar without a descent.**
   - `cands(e, d)` finds the altars within Chebyshev d + 1 of a tile with 16-bit-lane int arithmetic; one or none
     is the answer.
   - On a tie, `altar_raw(k)` computes one DistanceField per tied altar from its approach ring. It is lazy and
     cached, so each altar's field is computed once.
   - `label` picks the tied altar with the lowest own-field distance, and the lowest id when those are equal. The
     old descent could give a different altar only on exact ties [model].
2. **Stages that span turns.** `own`, `altar`, `paths` and `chokes` are generators that yield per unit (a group, a
   tied field, 16 choke candidates) and resume on the next draft turn.
   - Each turn stops while `fuel − DRAFT_RESERVE` (0.5M) still covers the largest unit measured so far, with a
     floor of half the hint.
   - A plain stage whose estimate cannot fit even a fresh later turn (`FRESH` 2.4M) is dropped and traced, not run.
   - Estimates (`est`, `unit_hint`) are fitted to the maxima over all 35 maps.
3. **Encode at the start of the next turn.** `draft_main` encodes when the model changed (`dirty`), then submits and
   picks. Every turn's submit carries all the work of the turns before it. Work on the last draft turn is never
   submitted [sdk: submit before pick, in the same turn].
4. **Play without draft memory.** `w.d = d or {}`. Every reader uses `.get` with defaults, and `if d:` still picks
   the fallback world (`10_model`). Every `w.d.` use was checked.

### 1.3 Results [measured]

Draft sweep: all 35 maps, R9 as team A, 3 rounds each.

| | R8 | R9 |
| --- | --- | --- |
| 01shortcut `altar` stage | 10.93M (crash) | 1.65M |
| 01shortcut turn 1 left | — (the turn ran out) | 5.98M |
| Maps with every pick ours | 34 / 35 | **35 / 35** |
| Final memory complete (flags 239) | 34 / 35 (01shortcut: no memory after turn 1) | **35 / 35** |
| Least fuel left at a draft turn's end | — | 0.74M (01big-world, turn 3) |

- Draft memory is unchanged on the other maps, except where groups are exactly tied between two altars. Those now
  take the lowest id.
- **Cost.** Exact ties make `altar` dearer on a few maps (big-world 3.5 → 6.2M, ambush 1.2 → 3.5M). That still fits
  turn 1's 23.8M.
- **01shortcut in the arena vs strat-sw.**
  - Both sides boot with `mem=ok`. Faults 0/0, `err` lines 0.
  - Rollovers after round 1: 4–5 a game for us, 33–46 for strat-sw.
  - Each body's boot rolls over once on round 1 (3.3M boot against 3.7M fuel). R8 does the same [measured on
    00lanes], so this is not new.

## 2. What gold is worth (Part 2, the measurements)

### 2.1 What gold buys [rules]

- A shard is 30 gold; 5 shards make an emblem (150). Power counts as 6 shards and has no passive. Passives don't
  stack; stats do.
- **A Power emblem is +30 Strength**: +60 % for Vesper (50), +86 % for Ren (35).
- **A Durability emblem is +500 HP and −10 % damage taken**: about +73 % effective HP for Vesper (900 HP).
- A second Durability adds 5 shards of HP and no passive; Power at the same price adds 6 shards.
- Monster (+10 % camp damage) beats Power on camps by ~6 % at Strength 110 [model], but Power gives +5 Strength more
  in a fight.

### 2.2 The ladder [measured, 3 R8 ladder games, 21 Oct]

| | Opponents | Us |
| --- | --- | --- |
| Gold earned | 7.5k / 14.4k / 3.2k | 3.9k / 4.6k / 2.7k |
| Largest one-body share of team gold | ≤ ~29 % | 54 % (Vesper; over all 35 local maps R8's is 36 %: §4.1) |
| Dead time (share of rounds) | 12–14 % | 23–44 % |

- On contest, ~7.1k of the opponent's gold came from 71 kills (kill gold is 100 since 3.0 [sdk]).
- **When we die, the killer has 5–43 more shards than our dead body.**
- **Their builds:** one Durability, one Jungle or Bruiser, then Power of their main stat for the rest of the game.

### 2.3 Gold for farming [model]

- One Power on an elk pair take cuts the clear from 52 to 32 rounds: about +33 % gem rate on such takes.
- But our bodies hit camps on only ~9 % of rounds [measured], so the farm gain realised is ~0.04 gems per gold.

**Conclusion.** Gold's value is mostly fight power. It keeps a body alive, and the top teams turn kill gold into more
Power (P8, P11). Gold held by one carry while four bodies stay at base stats is the opposite of that.

## 3. The design (user, 21 Oct; built, lost to R8, not shipped: §4.1)

1. **Every body values gold.** The FARM gold term's weight (`ROLE_GOLD`) changes:

   | Role | Before | Now |
   | --- | --- | --- |
   | Main | 3.0 | 1.5 |
   | Second | 1.0 | 1.0 |
   | Crew | 0.05 | 1.0 |

   - The main's 1.5 is about Vesper's real bonus with Treasure (×1.53).
   - The crew's weight was 1.0 only after the spike shift (round 300, or the main at 120 Strength). The shift is
     deleted: `SPIKE_STR`, `SPIKE_ROUND`, `SPIKE_GOLD`, `SPIKE_SHOP`, `w.spike`, and the reflex block in `90_main`.
   - The others' `shop` weight is the old post-spike 1.5 from round 0 (`ROLE_SHOP`); the main keeps her profile's.
2. **Each passive once, then Power forever** (`ROLE_BUILD`). The Durability / Power alternation is gone.
   - Main: Home, Treasure, Durability, then Power. Monster is dropped.
   - Second and crew: Durability, Jungle, then Power.
3. **Shop trips are unchanged** (06 §4.5): a body shops when its gold finishes its next emblem, and must shop at 300.
   With gold weight 1.0, the crew simply shop more often.

### 3.1 What it does to H4 (09 §3)

- **H4.4 (crew gold weight 0.05 → 0.3) would be folded in** (the crew at 1.0 from round 0). Since §3 lost (§4.1), H4.4
  stays open.
- **H4.1–H4.3 still stand:** the tank share by k, the nearest takeable candidates, and the Fall rewrite (escort,
  never stand at an altar). The gold design does not touch idle rounds. A crew body with gold now has a shop trip on
  offer more often, which fills some idle rounds, but not the Fall's altar wait.

### 3.2 Unknowns to check when building

- **U-g1 [guess]:** the main's gold share falls from 0.54 toward the opponents' ~0.3 without slowing her first
  emblem (r75 in 06 §10).
- **U-g2 [guess]:** crews shop for real, about 4–5 emblems each a game (the user's target, 06 §4.6).

## 4. Results

### 4.1 The gold design (§3): built, lost to R8, not shipped [measured, 21 Oct]

The build had the draft fix plus §3. Its diff is in `patches/R9_gold_items.diff`.

| | vs strat-sw (70 games) | vs `_r8` head to head (70 games) |
| --- | --- | --- |
| Record | 51W/19L (R8: 51W/19L) | **24W/46L** |
| Maps won from both sides | 20 / 35 (R8: 19) | 2 / 35 |
| Mean margin | +201 (R8: +217) | −178 |
| Deaths a game | 9.1 (R8: 9.0) | 15.5 |

Gold went where §3 wanted (vs strat-sw, 68 games):

| Body | Emblems a game | Share of team gold | First emblem (median round) |
| --- | --- | --- | --- |
| Vesper | 24.2 | **0.40** | r94 |
| Ren | 13.6 | 0.24 | r337 |
| Varg | 12.5 | 0.21 | r448 |
| Ryth | 5.9 | 0.10 | r502 |
| Vendetta | 4.1 | 0.09 | r634 |

**The head to head, side by side [measured, 70 games, both bots in the same games]:**

| | Gold build | `_r8` |
| --- | --- | --- |
| Gold earned (all games) | **479k** | 568k |
| Deaths a game | **15.5** | 13.6 |
| Bags lost a game | 226 | 193 |
| K/D | 0.88 | 1.14 |
| Vesper: gold share, emblems a game, first emblem | 0.40, 16.6, r83 | **0.36**, 18.7, r103 |
| Varg / Ren / Ryth / Vendetta gold share | 0.20 / 0.26 / 0.10 / 0.08 | 0.25 / 0.27 / 0.11 / 0.08 |

**Why it lost (to check next session).**
- **The split was not the problem: R8 already spreads its gold** (Vesper 0.36 over all 35 maps). The 0.54–0.61 we
  used were 3 ladder games and 2 games on one map: too few, and a wrong base for §3.1's "every body values gold".
- **The gold build earned 16 % less gold and died more.** The changes that can do that are the builds and the main's
  weight, not the split:
  - The main dropped Monster (slower solo clears).
  - The main's gold weight fell 3.0 → 1.5 (fewer gold groups priced for her).
  - The crews bought Durability before Jungle (more camp damage, more heal trips).
- **Next:** ablate one at a time on top of R9: (a) the main's weight back to 3.0, (b) Monster back on the main,
  (c) Jungle before Durability on the crews. Only after gold income (§5).

### 4.2 R9 as shipped = R8 + the draft fix (§1) [measured, 21 Oct]

| | R8 (09 §7) | **R9** |
| --- | --- | --- |
| vs strat-sw | 51W/19L | **52W/18L** |
| Maps won from both sides | 19 / 35 | **21 / 35** |
| Mean margin | +217 | **+234** |
| Deaths a game | 9.0 | 9.0 |
| Worst map | broken-curve −540 | broken-curve −430 |
| vs `_r8` head to head | — | 33W/36L (1 errored: the CLI's `expected at least one module field` before round 1, 00reverse-spiral A) |

- **Faults:** 0/0 in all 139 games.
- **01shortcut:** R9 drafts in full there now and won 49–0 from side A vs strat-sw. It lost 28–163 from B.
- **Zipped:** `submissions/redo-r9.zip` = `bots/redo/src` byte for byte (`main.py` + `bot.py`, no bytecode).
- The head to head is a coin flip, as expected for a draft-only change: any edit moves some games through fuel
  timing (`judging-changes`). The fix matters on the ladder, where a lost draft loses the game outright.

## 5. Next session: the gold tiebreak and big-map gold (user, 21 Oct; design notes only, not built)

The user's point: on some maps neither side tributes gems, so the round-2000 tiebreak is **gold earned** [rules:
"counts all gold earned, not what is left to spend"; then kills, then Team B]. The newer, bigger maps pay more for
gold farming, and we farm gold poorly.

### 5.1 What R9's arena shows [measured, R9 vs strat-sw, 70 games]

| | Us | strat-sw |
| --- | --- | --- |
| Gold earned, all games | 644k | 424k (×1.52 to us) |
| Kill gold (100 a kill) | 140k | 52k |

Camp gold per game (earned minus kill gold), by map area:

| Map area | Games | Us | strat-sw |
| --- | --- | --- | --- |
| Big, ≥ 3,600 tiles (ambush, big-world, expanse, starvation, islands, corners, fracture, concentrated-wealth) | 16 | **6.5k** | 4.7k |
| Mid, 1,600–3,599 | 34 | 7.3k | 6.7k |
| Small, < 1,600 | 20 | 7.7k | 3.6k |

- **Games that end on the tiebreak or near it.** Both teams tributed < 300 gems in 9 games, and we led on gold in 7.
  - 00stampede (0–0) was won on gold from both sides.
  - **01boss-battle (0–0): lost from side A, 21.9k vs 23.0k gold; won from B, 31.0k vs 27.2k.** No kills there, so
    camp gold alone decided it.
- **Big maps give us the least camp gold**, although they have the most camps. strat-sw is no bar for this: it farms
  worse than we do.
- **On the ladder the opponents out-earned us** 7.5k / 14.4k / 3.2k vs 3.9k / 4.6k / 2.7k (§2.2), so the real gap is
  against the top teams, not strat-sw.

### 5.2 What to design next session (ideas to check, [guess] until measured)

1. **Measure first:** camp gold per round per body on big maps, ours vs the top teams' ladder replays
   (`tools/replay/`), and how much of a game's camp gold sits in gold-only groups. `tools/replay/farm/mapjson.mjs`
   needs the deleted `tools/mapgen`: fix or replace it before any map-level farm script runs.
2. **Tiebreak mode.** When no side can reach 1,000 gems by round 2000, gold earned decides. The bot can tell this
   from the map and from `global_submitted_gems()`: every altar gated (X8 already prices gold at the round-0 rate
   then), or both scores low late. In that mode, price gold at full weight to the end instead of
   `g2g(r) = 0.5 × (2000 − r) / 2000`, which falls to 0 at round 2000 (`50_prices.py`).
3. **Gold-only groups on big maps:** the crews (gold weight 1.0 since R9) could take the near gold-only groups the
   carries pass by. That ties into H4.2 (the nearest takeable candidates) and H4.3 (escort / never idle).
4. **Kills are gold too:** 100 a kill since 3.0 [sdk], and kills are the second tiebreak.
