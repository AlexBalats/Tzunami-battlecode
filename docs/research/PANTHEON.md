# Pantheon (1st, Cambridge Battlecode spring 2026): what transfers to CAMBC 2026a (2 Nov)

Source: the public repo `HerbertTheBird/Cambridge-Battlecode` (README + `postmortem/postmortem.tex`), read at the user's
request on 2 Nov ("look at the readme to see what bot they used and lets mimic ours with theirs ... adapting"). Their
final bot is `bots/Khaos` (finals), `bots/Lethe` (international qualifiers). Their game was a different one (a core,
builder bots, conveyors, harvesters, turrets, launchers; markers for comms; maps ≤ 50×50), so **no mechanic transfers;
the decision architecture does.** We read the postmortem, not their code, and copy methods, not code (CLAUDE.md:
follow the postmortems, converted).

## 1. What they did [their postmortem]

1. **Rewrite at the plateau.** Demeter "hit a plateau due to overcomplicated code and strategies"; Lethe kept only the map
   info and pathfinding and rewrote the rest. That rewrite is what "finally started winning games against top teams".
2. **Memoryless scored states.** Every turn each builder recomputes from global map knowledge and scores 7 states; the
   best runs. No state transitions, no stale goals. "Long-term behaviour emerges from every builder acting optimally on its
   current local knowledge"; less overfitting, dynamic, hard to counter.
3. **Ceilings = priority bands.** Each state's score is strictly below a fixed ceiling: attack 9 > heal 8 > route 7.75 >
   secure 7.5 > harvest 4 > disrupt 2 > explore 1. Scored in descending ceiling order with an early exit (a lower
   ceiling can't beat the best found). A state's score can drop below a lower band (route 5 normally, 7.75 when an
   enemy is near).
4. **The state pattern.** `score()` builds the state's candidate targets, **intersects them with a Voronoi claim
   partition** (simultaneous flood fills from me v every other ally: I keep only targets I reach first), caches them for
   `run()`. This, not markers, is how builders split work (the marker claims were retired: other teams disrupted them).
5. **Small persistence only:** TTL failure caches per state (a target that failed is skipped for N rounds); the first few
   bots get an initial plan (the core encodes each one's direction in its spawn tile); a guard bot stays home.
6. **Local superiority gates.** Attack a healable target only when we locally outnumber the threat (2+ allies within r
   v 1 enemy within 2 steps), or a turret supports, or the target is sealed.
7. **Soft threat in pathing:** a step into a soft threat costs 20 (normal 1), not a wall.
8. **Chase:** drop enemies another ally is strictly closer to; prefer the closest left.
9. **Comms supplementary only** (map sharing); bots never depend on it.
10. **Stuck jitter:** a random step after 2 + (id mod 8) no-progress turns, so bots don't sync.
11. Offence late: "attack route" (extend toward the enemy when nearer to them than 1.5× our own distance) won the final.

## 2. The mapping to our game [guess until measured on the ladder]

| Pantheon | CAMBC 2026a | Our code now |
| --- | --- | --- |
| memoryless scored states, ceilings | each turn every body scores ESCAPE > FIGHT > HEAL > BANK-due > YIELD > TAKE > CREW > SHOP > IDLE, highest band first, early exit | one currency (`price_all`) with hacks to force order (`BANK_DUE_X`, `SHOP_MUST_X`, the stance overriding, the seed hold) and hysteresis / sunk progress (`SUNK_K`) holding stale goals |
| Voronoi claim partition | a group is mine if I'm the nearest body to it among the allies whose positions we know: visible allies' tiles, out-of-sight allies' broadcast targets (slot bytes) as their positions (ally positions out of vision are unreadable, error 97 [measured]) | lower-slot claims (`CL.lowcl`): slot order, not distance; the cause of "skips the nearest live group for a smaller, farther one" (LADDER_P18 §13) |
| local superiority gate | commit / provoke only with numbers × strength ahead; otherwise yield | `STANCE_PL` 0.69 commits at 2:1 against (REBUILD_V2 §12.1); x1's yield is the first form |
| soft threat cost 20 | Nav's goal fields with visible / remembered enemy reach as a high cost (not a first-pass wall that relaxes) | `enemy_hit` board as walls in pass 1, dropped in later passes |
| TTL failure caches | `ST.exclude` (EXCL 15, DEATH_EXCL 100): already ours | kept |
| initial plan for the first bots | the opening seeds / stack (`opening_slots`) | kept |
| rewrite keeping map info + pathfinding | keep World, Sense, Mem, Nav, Kit, beh executors, the draft; rewrite the chooser | REBUILD_V2 §2 says the same |

What does not transfer: turrets, conveyors, launchers, ore hopping / seeding (no buildings here); the bit-sliced score
planes (our candidates are ≤ 64 groups, not 2,500 tiles); markers (we have 8 bytes).

## 3. The plan (the x line, REBUILD_V2 §12)

- x1 (judging): crews + leash + yield on the old chooser.
- **x3 = the Pantheon chooser:** banded states scored every turn from the current Snap (no hysteresis beyond the TTL
  caches and a short commit hold in a fight), the Voronoi claim on farm candidates, the superiority gate for FIGHT,
  YIELD above TAKE. The prices stay as each state's score inside its band (the danger economics stay: REBUILD_V2 §11
  lesson 1).

## 4. pn1 = the Pantheon core as one piece (`bots/lad-pn1`, from x6 = r2 + yield; 2 Nov, the user: "test out the winning stuff")

1. **The nearest-body claim** (`pn_rank` / `pn_slots`, prices.cpp): group g is mine only if fewer than `pn_slots(g)` known
   allies are nearer (need from the record, +1 for a group with more HP than 30 × my Strength); known = visible allies at
   their tiles (only those whose byte shows farm / capture / join), unseen allies at their farm / capture target's anchor,
   an unseen claimant of g itself at ≥ 9 − my distance. It replaces the lowest-slot claim for every group size (stack mode
   keeps no claims, as before).
2. **Memoryless:** the sunk-progress hold (`SUNK_K`) is gone; only `HYST` within a band and the TTL exclusions stay.
3. **Bands:** urgent heal (hurt below `HEAL_LOW` with an enemy within 8) > due bank > the economy (farm / join / bank /
   shop / hunt / heal in team gems a round) > idle; the stance's fight / escape sits above all; zero prices are no option.
4. **The superiority gate:** `STANCE_PL` 0.69 → 0.5; with yield (x6) a healthy break backs off toward allies.
5. **Anti-oscillation:** P(lose) decays from its recent peak (×0.8 a turn): traced locally, the raw value went 0.97 → 0.15
   → 0.50 → 0.13 on four turns and the choice flipped Heal ↔ Kill ↔ Farm (the 24 Oct Kill ↔ Heal flip pattern).
Local smoke: runs, no errors; local results swing 0 ↔ 1,008 on the same map pairing (01elk-arena), so they judge nothing.
Judged on both ladder panels v v93.

### 4.1 pn1 on the ladder (2 Nov, 13:13)
- **Band (115 v v93ref): 31 v 42 (−11.0 ± 5.7)**, flips +11 / −22; deaths −0.9 ± 0.6, theirs −1.7; kills −1.4; middle −36, theirs
  +30; gold −694; r300 −8.5. Lost.
- **Top 20 (100 v orig): 4 v 3 wins; deaths 12.0 → 8.9 (−3.1 ± 0.5)**, r300 deaths −0.3; final gems +42 ± 21; kills +0.5;
  their gems −12. The first build that cuts the top's death gap clearly.
- Read: the core's caution (yield + the 0.5 commit gate) saves bodies v the top and gives up ground and gold v the band.
  pn2 (rich takes, no yield) and pn3 (+ the Lanchester commit band) follow.

### 4.2 pn2 on the ladder (2 Nov, 14:17) and the switch to SPSA
- **pn2 (core without yield + rich takes + `G2G_K` 0.25): band 23 v 42 (−19.0 ± 4.9)**, flips +4 / −23; gold −1,401, kills
  −2.0, their deaths −2.3, middle −39; **top 20: 8 v 3 wins (+5.0 ± 2.6)**, deaths −1.8 ± 0.5, middle +17, r500 +18.
- The new pieces help v the top and hurt v the band in every form (pn1 −11 / pn2 −19 on the band; deaths −3.1 / −1.8 v the
  top). Cutting gold costs items, and items decide the band's fights. pn5 / pn6 / pn1b (all on pn2) dropped; pn3 runs (band).
- **t2 = v93 + every new piece as a knob, neutral at v93's values** (`bots/lad-t2`: the nearest-body claim `CLAIM_NEAR`, rich
  takes `RICH_X` / `RICH_DIV`, the commit band `COMMIT_PL` / `BREAK_PL`, `PL_DECAY`, yield `YIELD_PL` on 2,500+ tiles, the fight
  call `SUMMON_W`, `PROVOKE_K`, `SUNK_K`, `G2G_K`); **ladder SPSA `t2a`** on the band panel (`tools/lspsa_t2.json`, 10
  iterations, ~1 h each: `python3 -I tools/ladder/lspsa.py show t2a`). lspsa now runs through `runs/ab/judge.sh`.

### 4.3 The SPSA start was not v93; the null; v3 (2 Nov, 16:00)
- **t2a round 0: both sides 30 v 42** (t2a0p / t2a0m, deaths +0.5 / +1.0, gold −380 / −540; J+ − J− −0.01, wins equal).
  θ0 in `tools/lspsa_t2.json` had five pieces partly on (`CLAIM_NEAR` 2, `PROVOKE_K` 0.3, `YIELD_PL` 0.95, `SUMMON_W` 0.15,
  `PL_DECAY` 0.2): the start sat ~12 below v93 and the gradient was noise. SPSA stopped after t2a1p.
- **The null** (`bots/_t_null` = lad-t2 at its code defaults = v93, stamp `t2-null`), band panel: is v93ref's 42 still the
  ladder's? **Result (16:52): 44 v 42 (+2.0 ± 3.2), flips +6 / −4, every KPI within 1 SE: the baseline holds.** Today's
  losses are real (x6 37, pn1 31, pn2 23, pn3 23, t2a θ0 30). A same-code copy moves ±3; a code change ±6.
- **v3 = pn1b (the Pantheon core without yield) + the top's opening rule** (`bots/lad-v3`, `provoke_ok`): a first hit (hunt,
  free shot, commit) only when I'm the bigger body (maxHP ≥ `OPEN_BIG` × the target's) or an ally is within 3, the target's
  supporters within 8 ≤ mine, and our HP near it ≥ `OPEN_HP_K` × theirs (§12.6: their opener 1,600 v 1,300 maxHP, the target
  0.80 v 1.22 supporters; our opener dies 0.34-0.44 at every head count; Vesper's free shot is 263 of our 554 openers).
  Judged on both panels after the null.

### 4.4 v3 lost; the behind switch (v5) (2 Nov, evening)
- **v3 (pn1b + the opening rule), band stage 1 (60 games): 12 v 24 (−12 ± 4.0), stopped.** Deaths −2.9 ± 0.9, their deaths
  −3.9, **kills −3.7, gold −1,367**, their r300 +27. Against the band, v93's edge is its fights: every cautious form today
  (x6, pn1, pn2, pn3, v3) traded kills and gold for deaths and lost. v4 (v3 + rich takes) cancelled before upload.
- **The item lead decides the game** (v93's decoded games, team mean maxHP / the design's base HP, `scratchpad hpx*.py`):
  top 20: r600 us 1.51 v them 1.90, r1000 1.97 v 2.88; band r600 1.61 v 1.72. **Type-matched (their Vesper v ours) at r600:
  ratio ≥ 1.3 in 42 of 107 band games, v93 wins 14 % of them (49 % below); 45 of 86 top games, 2 % (5 % below).**
- **v5 = v93 (lad-t2 at its defaults, the null = 44 v 42) + the caution package only when behind** (`bots/lad-v5`,
  `upd_behind` in prices.cpp): each body keeps the latest maxHP / base of every type it sees on each side; the switch is
  the type-matched ratio averaged over shared types (≥ 2), smoothed (`BEHIND_A` 0.03 a round), on at 1.3, off below 1.15,
  from r300. Behind: the top's opening rule in `provoke_ok`, the 0.5 commit line, yield at P(lose) ≥ 0.45 on every map,
  the P(lose) decay 0.8. Traced v lad-r2 (4 maps): fired in the 3 games where the replay shows v5 truly behind (r600 q
  1.38-1.58, all lost), not in the one it led (0.87, won). Judged with the staged judge (`runs/ab/judge2.sh`).
