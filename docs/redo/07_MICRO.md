# 7. Micro: XSquare's tile compare, fed by an information matrix built from our raycast vision

> **Status (20 Oct): built and scrapped in session 4; see §14.** The design below is kept as history for 08_FIGHT.
>
> MICRO: "definitely follow the XSquare Style Micro … peep 6.1 and you can see how they are utilising the information
> they get to the absolute max via a matrix so we should use the same as the vision we see is raycasted." (user, 19 Oct)

## 1. What XSquare micro is [pm]

From GST §6–6.1 (read in doc 02, with their code):
- **Every candidate square is scored on a set of facts** (passable, safety tier, in range of a target, enemies near,
  allies near, forward), and **a chain of if/else compares decides whether square A is better than square B**. It is
  lexicographic: the first fact that differs decides. There is no weighted sum to tune.
- **Modes change the chain:** `bold` (allies − enemies ≥ 2, or a health ratio > 2) steps closer; `inRetreat`
  (a big bag, or allies − enemies ≤ −2) steps away.
- **§6.1 the matrix:** the facts come from *everything the team knows*, not just this unit's sight. Their rats
  squeaked HP and the nearest enemy every turn, even over budget, "a very worthy tradeoff".

The same idea in the other two postmortems:
- **Gone Fishin §5.2 kiting:** after attacking, move to the tile **the fewest enemies can see**, and always kite back.
  "Macro +5 %, micro 30–50 %". §5.3: chase only with no other target, or when up 2+. §5.5: one-shot targets first,
  counting how many allies can hit each. §5.7: guess where unseen attackers are.
- **Om Nom §12:** step in and out of range to land 2 hits per hit received; judge by net damage.

## 2. What strat-sw does today [code, measured]

| Piece | What it does | What is missing |
| --- | --- | --- |
| `exec_kill` (l. 4345) | In range: attack (+ cast). 1–2 beyond: dash in if ttk ≤ `CLOSE_TTK` and not outnumbered by > 1. Else `step_near` the target. | No tile is scored. It never asks "can they hit me there next round?" It never steps back after a hit. |
| `retreat_now` (l. 4546) | Enemies within 4 outnumber allies + 1 and P(lose) > 0.5, or HP < `retreat_hp`. | A yes/no gate. Then `step_flee` goes by Chebyshev distance, so a wall counts for nothing. |
| `lanchester` (l. 2712) | Square law over HP × strength within `LANCH_R`, centred on me. | Good input for the mode. No tile in it. |
| `aggro_step` (l. 4072) | During a take, the tile among mine + free neighbours by expected monster hits (nearest-champion rule, A2). Tank takes the most. | A second, separate tile scorer for camps. Should be the same engine. |

What it costs [measured]:
- **15 deaths a game** against the top-5 Tavi team (CLAUDE.md, Later).
- **64 % of our deaths happen in `heal`**, walking home hurt (FARM_18OCT). Victims are alone, low on HP from camps,
  sometimes mid-recall, often with a bag (`docs/archive/REPLAYS.md` §5).
- **We hit back in 7 % of the rounds** an enemy was on us (`docs/archive/REPLAYS.md`): 36 of 483.

## 3. Our vision, and what the matrix can know

### 3.1 The rules of vision [rules]

- **Symmetric shadowcasting, radius 8.** Walls and bushes block sight; holes don't.
- **Bushes:** you can't see into a bush from outside. From inside, you see across that bush and out.
- **A ward adds its own vision.** **Vision is not shared** between our champions.
- **Monsters see through bushes** [rules] and don't chase.

### 3.2 What "raycast" gives us: symmetry

Symmetric shadowcasting means **if I can see tile e from q, a unit on e can see q**. Bushes are the exception: a unit
in a bush sees out, but it can't be seen from outside.

So the question "**who can see me if I stand on q?**" is answered from my side: `visible_tiles_from(q)` [sdk]
(hypothetical vision from q) and the enemies in it. For each enemy in that set, it sees me at q. Add the enemies in
bushes we have seen (they see out), and exclude q if q is a bush and the enemy is outside it (P-a).

That is GST §6.1's "spreadsheet", without a single byte: the engine has already cast the rays, and we evaluate them
from each candidate tile.

### 3.3 Sources, best first

| Source | What | Cost |
| --- | --- | --- |
| Own vision | Every visible enemy: tile, HP, bag (`gem_count`, real [measured A18]), state flags (recall, tribute [sdk, P-i]) | Already sensed |
| Ward | The ward's own vision [rules]: enemies near our camps or altars | `Ward.visible_tiles_from` [sdk] |
| Memory (`Mem`) | Enemies seen in the last 1–2 rounds, with their tile; where they could be now (walk reach grown by the rounds since) | Bitboards, ~6k per enemy |
| Bytes | The sighting byte (count + where), the fight event (doc 04 §5.1) | 1 read |
| Failed moves | A move into a bush returned False: an enemy is there [rules] (doc 05 L5) | Free |
| HP lost with no visible attacker | Someone in a bush or out of sight within their range hit me. Mark the bushes within 3 of me as suspect (Gone Fishin §5.7 "guess attacks") | Free |
| Allies | Exact tiles and HP [rules]. Their slot byte says what they're doing | Already sensed |
| Enemy kit | Ranges, damage, dash from `docs/CHAMPIONS.md`. Cooldowns: read them if the SDK shows enemy abilities (P-h), else track casts we saw (8-turn cooldown [rules]) | Constant table |

## 4. The matrix

**Candidates:** the 9 tiles (8 neighbours + stay), plus the dash landings when the dash is ready (`valid_tiles()`,
~up to 24). Illegal tiles are dropped first (walls, holes, altars, enemy spawn, occupied [rules]).

**Shared boards** (built once a turn when a threat is in sight; doc 05 L2 uses the same ones):
- `reach_e[i]` = enemy i's walk reach next round (1 step, or 1 + 2 if its dash may be ready):
  `reachable_tiles(e, 1 or 3)` ~6k.
- `hit_e[i]` = `reach_e[i]` dilated by its attack range (1 melee, 3 ranged), plus its spell range if the spell may be
  ready. Shifts and ORs, ~20–40k.
- `camp_hit` = tiles within 3 of an awake monster where I'd be the nearest champion (A2 tie rule) [rules, measured A2].
- `bush` = bush tiles (static).

**Per candidate tile q** (each a bit test or a short sum, so 9–33 tiles are cheap):

| Field | Meaning | From |
| --- | --- | --- |
| `legal` | can I land here | passability, occupancy |
| `dmg_in` | damage I can take here next round: Σ over i with `hit_e[i]` ∋ q of i's hit (+ spell) | boards + kit table |
| `lethal` | `dmg_in ≥ my HP` | |
| `n_threat` | how many enemies can hit q | boards |
| `seen_by` | how many enemies see q (§3.2) | `visible_tiles_from(q)` ∩ enemy tiles, minus the bush case |
| `camp` | an awake monster will hit me here | `camp_hit` |
| `can_hit` | the best target I can hit **this turn** after moving to q (melee: move + attack; ranged: only q = here, or a dash landing if P-c holds) | `attack_tiles` from q, or the Chebyshev box |
| `allies2` | allies within 2 of q | ally tiles |
| `bush` | q is a bush (hidden from outside, P-a) | `bush` |
| `exits` | free neighbours of q (not cornered) | `reachable_tiles(q, 1)` count |
| `goal` | Nav's global value at q towards the Behavior's goal (or home in retreat) | doc 05 L0 |

## 5. Mode (once a turn)

- **bold:** allies − enemies ≥ 2 within 6, **or** P(lose) < 0.2 (`lanchester`).
- **retreat:** allies − enemies ≤ −2, **or** P(lose) > 0.6, **or** HP < 40 % with an enemy in reach, **or** the
  body is a carry with a bag worth more than the kill (doc 06 §4.3).
- **normal:** otherwise.

These are GST's numbers (± 2) on our counts, and our existing `lanchester`. The thresholds are provisional.

## 6. The compare: is tile A better than tile B?

Lexicographic, first difference wins (GST §6's chain, our facts):

1. **legal** over not.
2. **not lethal** over lethal, unless bold and the target dies first (a trade we win).
3. **If my attack is ready: can hit the best target** (§7) over can't.
4. **Lower `n_threat`**, then **lower `dmg_in`**. Enemies before camps: "enemies behave more predictably and
   smarter" (GST §6.2).
5. **Not `camp`** over `camp`, unless the Behavior is a take and I'm its tank (doc 06's crew; this is `aggro_step`'s
   rule, folded in).
6. **Mode:** bold → closer to the target; retreat → lower `goal` towards home or the nearest ally group, not alone
   (FARM_18OCT: hunted bodies that walk home alone die).
7. **Lower `seen_by`** (Gone Fishin's kite rule), and `bush` over not when it hides me (P-a).
8. **More `allies2`** (don't fight alone; `docs/archive/REPLAYS.md` §5 "we die alone").
9. **More `exits`** (don't get cornered against a wall or the edge).
10. **Lower `goal`** (progress on the Behavior's own goal).
11. **Stay**, then **orthogonal** over diagonal.

### 6.1 The order of actions in a turn

- **Melee** can move and attack [rules]. If a target is in range now: **attack first, then move** to the best tile
  (hit and step back: Om Nom's in-and-out). If not: move to the best tile (step 3 prefers tiles where I can hit),
  then attack if something is in range.
- **Ranged** moves *or* attacks [rules]. If a target is in range and `here` is not lethal: attack. Else move to the
  best tile, preferring tiles where the target is in my range **next** round and I'm out of its reach (`hit_e`).
  That is kiting with one action a turn.
- **Vesper:** attack, then dash out, if the dash is an ability and not the move (P-c). That would be Gone Fishin's
  launcher kite exactly.
- **Post pass** (doc 03): if the attack is still ready at the end of the turn, attack anything in range.

## 7. Targets

In order (Gone Fishin §5.5, GST, our economy):
1. **Dies this round:** its HP ≤ the damage the allies who can reach it this round will deal, counting only allies
   who act after me (doc 05 L3: the finisher acts last).
2. **Channelling a recall:** damage interrupts a recall [rules]. A tribute is not interrupted by damage, only by stun,
   death or an altar lock [rules], so a tributing enemy is a stun target (Ryth, Ren, Marcella), not a damage target.
3. **The bag:** a kill gives its gems + 100 gold (`constants.KILL_GOLD`; 50 before 3.0) [sdk 3.0.1]. Value = bag + 100 gold in gems (`KILL_G * g2g(r)`).
4. **Lowest HP / my damage** (fewest hits to kill).

**Chase** (Gone Fishin §5.3): follow a target out of range only if there's no other target and we're bold, or it
dies to the next hit. Never past an enemy's spawn (it heals to full there; strat-sw's `near_espawn` already handles
this).

**After a fight** (Gone Fishin §5.6): for 10 rounds, the updater walks the body to the highest-HP ally nearest the
objective; the lower-HP of two bodies that meet stops behind.

## 8. One engine for fights and camps

`aggro_step` (the take's tile scorer) and the fight scorer become one: the camp is a threat board (`camp_hit`) with
its own rule, and the tank role flips step 5. Same candidates, same compare. This also removes the bug class where a
body fighting next to an awake camp scores the fight and ignores the camp.

## 9. When the micro runs (the gate, doc 03)

The micro Behavior is chosen by the updater's gate when any of these holds: an enemy within 8 (vision), a fresh
memory of one within 10, a failed bush move this round, unexplained HP loss, or an awake camp within 4 that isn't my
take. Otherwise no boards are built and the turn costs nothing extra.

## 10. Fuel (estimates to measure)

| Work | Fuel |
| --- | --- |
| Boards for 4 enemies | ~100–150k |
| `visible_tiles_from` on 9 tiles (P-e) | ~80k (9k each [measured, shadow_cast]) |
| Matrix rows for 9–33 tiles, ~10 field tests each | ~100–300k |
| The compare (≤ 33 × ~10) | ~30k |
| **Total** | **~0.3–0.5M of 2.5M** |

If it runs over: drop the dash landings to the 4 best by `goal`, and compute `seen_by` only for the tiles that tie
up to step 6.

## 11. What we will measure

- **Deaths a game**, by cause: enemy (in a fight / walking / in heal / mid-recall) vs camp.
- **Rounds we hit back** while an enemy hits us (7 % today).
- **Trade ratio:** HP dealt to enemy champions / HP taken from them, per fight (Om Nom's net damage).
- **Bags lost** (gems carried at death) and **kills' bags gained**.
- **Single-body reviews** (GST §6.4): for each change, the 3 worst deaths of 3 games, from the replay and the trace:
  what the matrix said, and whether the new compare would have chosen another tile.
- Then the gate: more wins than losses vs strat-sw on the full arena from both sides, worst map included.

## 12. Build order inside R4

1. The boards (shared with Nav, doc 05 L2) and the mode. No behaviour change: trace only, and check the boards on 2
   maps against the replay.
2. The compare for **retreat** (heal walks, hunted bodies): the 64 %.
3. The compare for **fights** (replacing `exec_kill`'s walk-in), with the action order (§6.1) and targets (§7).
4. Fold `aggro_step` in (§8).
5. The fight event byte (doc 04 §5.1), if the reviews show bodies dying with allies 10 tiles away.

## 13. Unknowns to check when building

Checked in session 4 (20 Oct) with a probe bot (`redo` + hooks, git-ignored, deleted) against strat-sw on 00ambush ×3,
00contest and 01boss-battle, cambc 3.0.1, and on 15 decoded 3.0.1 replays (redo vs strat-sw, session 3's run).

| # | Question | Answer |
| --- | --- | --- |
| P-a | Can a champion outside every bush see an enemy standing in one? | **No, except through a ward.** ~800 sightings of an enemy in a bush while the viewer stood outside every bush; each had one of the viewer's wards within 8 [measured]. So the bush hides you from anyone without a ward on it, as the rules say. |
| P-c | Vesper: dash and basic attack in one turn? | **Yes, both orders.** Attack then dash: the dash succeeds (state after the attack keeps CAN_CAST). Dash then attack: state after the dash is ALIVE + CAN_MOVE + CAN_ATTACK, the attack lands [measured]. The dash is a cast: it costs neither the move nor the attack. |
| P-d | Monster nearest-champion tie with an enemy at the same distance? | **No reliable rule.** Clean ties (no champion hit on the tied bodies that round): same-team ties went to the lower index 330 vs 272; cross-team ties 18 vs 18 (team A 20, team B 16) [measured]. So a tank must be **strictly** nearest, and a tie counts as the monster hitting me (the safe side). |
| P-e | Cost of `visible_tiles_from(q)`? | **~13k a call** (9 calls 120–126k; `_into` 115–122k); own `visible_tiles()` ~12k [measured]. 9 calls a turn are affordable inside the gate, not every turn. |
| P-h | Are an enemy's ability cooldowns visible? | **Yes:** `enemy.abilities()[i].cooldown()` reads 0–7 on a visible enemy; both cooldowns ~27k fuel per enemy [measured]. `remaining_channel_time()` raises on a body not channelling (~50k for the exception): call it only when the state says RECALLING or SUBMITTING_GEMS. |
| P-i | Are an enemy's RECALLING / SUBMITTING_GEMS flags readable? | **Yes:** `enemy.state()` shows both (SUBMITTING_GEMS seen on enemies at an altar, the channel time readable while channelling) [measured]. |
| — | The mode thresholds (± 2, P(lose) 0.2 / 0.6, HP 40 %) | **[guess]**, GST's numbers: `# GUESS` constants in `35_info`. |

## 14. Session 4 result (20 Oct): built, measured, scrapped

**Verdict: the compare was built and wired, lost to the build before it, and was deleted** (user, 20 Oct: "if we are
using too much fuel then scrap everything and only keep a little bit"). `bots/redo` is R3 again plus the keepers
below. `55_micro.py` was never committed; a copy of the last version sat in the session scratchpad only.

**What it did** [measured, cambc 3.0.1, every run vs `_r3` = the session 3 build unless named]:

| Build | Games | Record | Deaths/g | Kills/g | Run |
| --- | --- | --- | --- | --- | --- |
| Micro wired (retreat, fight, take, post), after the retreat fixes | 42 | 12W/30L | 15.6 | 6.0 | `runs/arena/redo-vs-_r3-20261020-191100` |
| Same, retreat back on strat-sw's escape/away (`_abA`) | 42 | 10W/32L | 14.8 | 5.3 | `runs/arena/_abA-vs-_r3-20261020-192016` |
| Micro wired, 4 brawl maps (00eight, 00fragment, 00elkring, 00monolith) | 8 | 1W/7L | 27.2 | 4.0 | `runs/arena/redo-vs-_r3-20261020-192943` |
| … without `post` (`_abB`) | 8 | 0W/8L | 38.1 | 1.6 | `runs/arena/_abB-vs-_r3-20261020-193043` |
| … kill gold priced 50 (`_abC`) | 8 | 1W/7L | 29.2 | 2.9 | `runs/arena/_abC-vs-_r3-20261020-193144` |
| … `Kill.fight` back on strat-sw's chase / CLOSE (`_abD`) | 8 | **4W/4L** | 22.2 | **21.5** | `runs/arena/_abD-vs-_r3-20261020-193306` |
| … without `take` (`_abE`) | 8 | 0W/8L | 34.4 | 2.6 | `runs/arena/_abE-vs-_r3-20261020-193406` |

microstats on the 42-game run: redo 14.3 deaths/g, **heal 9.0** (`_r3` 2.5), hit back 35 % (28.7), trade 0.96
(1.04), bag lost 105/g (42), bag won 27/g (103). The micro fight was the fault: with it our bodies stopped killing.

**Faults found** (each fixed in turn, the fight never recovered: kills 2.8, 6.1, 1.8/g on the 4 maps, runs not kept):
1. **The micro overruled the macro.** In a Kill the mode could say retreat (carry rule, P(lose) > 0.6, HP < 40 %):
   the body walked in through Nav and backed out every turn. The macro prices a fight; the micro must not re-decide it.
2. **Ranged reach counted the step.** A ranged champion moves *or* attacks [rules], so its hit next round needs no
   step (a dash is a cast: P-c). `danger` counted range + 1 move for everyone: every tile near a fight looked lethal,
   heal walks froze (stand and shoot forever) and fights never closed. Right rule: hit reach = range + moves for melee,
   range + dash only for ranged. **Check strat-sw's own danger tests for the same error in 08** (Nav's L2 walls,
   `enemy_hit`).
3. **Reloading stepped to the safest tile** anywhere: the target walked off and the chase ban fired. Keep the target in
   range while reloading (07 §6.1 says so; the build didn't).
4. **Fuel.** The compare costs ~1k fuel per Python op [measured]: `rank` median 360k, p90 900k, max 1.6M; leaned to
   median 230k, p90 431k, max 1.1M (ties only for steps 7–11, `TIE_FUEL`). strat-sw's turn is already ~1.5M at p90, so
   fight turns ran over 2.5M: in one game (00elkring, 4-map run) redo had **182 turn rollovers vs `_r3`'s 100**, the
   Vesper 69 of them, 50 in rounds 100–199 (the fights). A body that rolls over acts every other round. [measured, one
   game: the run-wide count was not finished.]
5. Smaller: an off-map `is_set` raised and killed the turn (bounds check needed); the retreat goal "towards the
   nearest ally" walked bodies back into the fight (home only).

**Lessons for 08_FIGHT:** the macro decides fight or not; a fight turn has ~1M of fuel left, not 2.5M, so any per-tile
compare must be a handful of tiles with precomputed boards; test 8-game subsets only for big effects (the same idea
swung 1.8–6.1 kills/g between runs).

**Kept** (in `bots/redo`, R4):
- X4: `KILL_G` read from `constants.KILL_GOLD` at boot (never at preload: the game API is not up), and
  **`KILL_PRICE = 0.5` GUESS** on it in the four fight values. At the real 100 the bot took fights it lost (vs `_r3` on
  the 4 maps: 1W/7L, 29.8 deaths/g, `runs/arena/redo-vs-_r3-20261020-194747`); at 0.5, 4W/4L, 20.6
  (`runs/arena/_k50-vs-_r3-20261020-195001`, the same arithmetic as the final build). 08 re-prices P(lose), then 1.
- ~~X8 on Hunt (sighting and patrol) and HOLD: no walk to a gated altar; `Hold.execute` fails on one.~~ **Removed
  in session 5** (06 §11.6): the full arena of R4 was 17W/25L vs strat-sw (R3 25W/17L); without this gate 22W/20L.
- `err_text` gives the 3 innermost frame lines; the tick traces `errs=N` (all turn errors, the text deduplicated).
- `tools/microstats.py` (deaths by cause, hit back, trade, bags) and the probe answers in §13.

**Final build vs strat-sw** on the 4 maps: 3W/5L, margin −182 (`runs/arena/redo-vs-strat-sw-20261020-195129`);
session 3's build had 5W/3L on the same 8 games inside its full run. Head-to-head vs `_r3` it is even, so this may be
noise or the X8 Hunt/HOLD gate: **the full arena vs strat-sw is the first thing next session.** No candidate zipped.
Session 5 ran it: 17W/25L (`runs/arena/redo-vs-strat-sw-20261020-200426` + 8 cached in `...-195129`); with the
Hunt/HOLD gate removed 22W/20L (`runs/arena/_x8off-vs-strat-sw-20261020-200936`), so the gate went (06 §11.6).
The fight byte (04) is not needed: the reviews showed retreat and macro faults, not deaths with allies 10 tiles away.
