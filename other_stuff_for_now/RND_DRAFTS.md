# R&D toward p15: whole new drafts (lab notebook, started 26 Oct)

Brief: NEXT_PROMPT_RND_DRAFTS (a brief, deleted 27 Oct). One card per idea (§3). Spin-outs are `bots/rnd-<id>`, copied from
`bots/rnd-base` (§2). Every number is tagged: [measured] from our games or decoded replays, [sdk] from the SDK or a dump,
[rules] from the handbook, [guess] unchecked.

## 1. Step 1: the top-10 teams' games (`replays_from_others/p13-p3/`, 46 games, 4.0) [measured]

All 46 are cpp-p13 losses (4.0, engine 2.0.0), 7 on 30×30 maps, 23 on 40×40 to 51×51, 16 bigger. Decoded in the session
scratchpad (`decode.mjs` needed the engine 2.0.0 snapshot layout: 84 item types, champion records 420 bytes; fixed in
the repo, the 3.0.x layout still decodes), flipped (us = team 0), battery + `early_deaths`, `focus`, `helpfight`, and two
scratch scripts (`champecon`: gold / gems / tributes / kills by champion; `killkit`: the casts before each death). The
bundles don't name the opponent, so teams are grouped by draft.

### 1.1 What they draft (3 / 4 / 5 picks)

| Draft (pick order) | games | map sizes |
| --- | --- | --- |
| **Vesper > Vendetta > Heart of Ruin** (> Cassi & Issac / Tavi / Ryth > Marcella) | 14 | 30×30 to 100×80 (3, 4, 5 picks) |
| **Prism > Vendetta > Marcella > Willow > Heart of Ruin** | 5 | 45×45 to 100×100, all 5-pick |
| Prism + Vesper + Marcella / Heart of Ruin (+ Ryth, Vendetta) | 4 | 30×30 to 51×40 |
| Marcella > Vendetta > Ryth / Tavi / Vesper (+ Vesper, Heart of Ruin, Willow) | 11 | 30×30 to 61×61 |
| Vesper > Ryth > Vendetta > Tavi > Marcella | 3 | 40×40 to 79×80 |
| Heart of Ruin > Varg / Marcella / Ryth / Tavi ... | 7 | |
| Vesper > Cassi & Issac > Varg > Vendetta > Heart of Ruin | 2 | 61×71, 100×100 |

- Presence over 46 games: **Vendetta 39**, Vesper 37, Marcella 37, Heart of Ruin 36, Ryth 19, Cassi & Issac 10, Tavi 10,
  Prism 9, Willow 9, **Varg 5** (our first pick in all 46). On 3-pick maps they took Vesper + Heart of Ruin + Vendetta,
  Marcella + Vendetta + Ryth / Tavi, Prism + Vesper + Heart of Ruin; **Vendetta is in 3 of the 4 three-pick drafts** and
  ours never has it below 5 picks.
- Nobody drafts Ren, Stellar; Willow comes only with Prism or Marcella + Vendetta.

### 1.2 Who carries their gold and gems (`champecon`, per game the champion played)

| Champion | gold (r300) us | gold (r300) them | gems captured us / them | kills us / them | deaths us / them |
| --- | --- | --- | --- | --- | --- |
| Vesper | 1,234 (431) | 1,967 (471) | 170 / 286 | 0.91 / 1.76 | 1.28 / 0.27 |
| Vendetta | 430 (169) | 1,200 (285) | 138 / 272 | 0.26 / **2.41** | 1.29 / 0.28 |
| Marcella | 322 (92) | **1,592** (379) | 57 / 274 | 0.15 / 1.43 | 1.48 / 0.59 |
| Heart of Ruin | 211 (44) | 810 (177) | 49 / 180 | 0.24 / 0.81 | 1.50 / 0.42 |
| Varg (ours) / Prism (theirs) | 294 (70) | 1,301 (241) | 104 / **400** | 0.00 / 2.33 | 1.70 / 0.00 |

- Team gold a game 2,332 v **5,280** (camps 2,060 v 4,050, kills 168 v 712, Marcella's tribute gold 105 v 518).
- Their gold and gems are spread over **three** bodies (Vesper, Marcella, Vendetta), ours sit on Vesper. In the Prism
  family (big open maps, 0–9 deaths a game) every one of the five captures: 240 / 196 / 234 / 312 / 84 gems a body,
  ours 241 / 190 / 86 / 129 / 31. Those five games are a pure farm race lost 2 : 1 with no fights.
- Captures by group side (`captures`): contested elk 49 v 178 gems / 1,000 rounds, contested clusters 13 v 68; of 69
  contested elk groups they took 39 first, we 15.

### 1.3 What they buy (`shop`, spent by r150 / r300 / r600, median body)

They spend **less** and later than we do: all bodies 30 / 80 / 190 v ours 0 / 120 / 280 (our Vesper 190 / 420 / 775 takes
most). Their Vesper builds Bruiser of Strength (53 % of its shards), their Vendetta Bruiser Strength / Health, **their
Marcella Bruiser of Focus (47 %)**, Prism Bruiser Health / Focus, Tavi Treasure Health, Willow Power / Jungle / Capture
Strength. Ours: Power Strength + Bruiser Health on the carries, Treasure first everywhere. Items are not their edge.

### 1.4 Does §4.0 (early deaths at equal numbers) hold on 4.0, against all of them?

| r ≤ 300 unless noted, 46 games | us | them |
| --- | --- | --- |
| deaths a game (r ≤ 150) | 6.7 (0.8) | 2.1 (0.3) |
| dead % of body-rounds (r ≤ 300) | 7.2 | 3.0 |
| gems held + banked r100 / r300 | 53 / 146 | 74 / 291 |
| camp hits / 100 live (r ≤ 300) | 21.1 | 25.9 |
| kills per 1,000 champion hits (all game / r ≤ 150) | 3.5 / 1.4 | 11.9 / 7.2 |
| even fights (3+ hits), kills | 34 | 119 |
| 1v1 fights, kills | 19 | 41 |
| hits a fight, even fights (per champion) | 3.3–4.7 | 5.5–7.6 |
| contact rounds (enemy within 3): a melee hits a champion | 26–35 % | 40–51 % |

- Yes, and it is no longer only the opening: deaths are spread over the game (r ≤ 150 is 12 % of ours). By opponent
  family: Vesper > Vendetta > Heart of Ruin 9.3 v 2.6 deaths a game, Marcella + Vendetta 7.7 v 2.7, the Prism family 5.6
  v 1.2. By map size: **30×30 11.4 v 1.9** (gems at r300 41 v 564), 40–51 6.4 v 2.6, bigger 5.1 v 1.5.
- **Their Vendetta is the killer**: 94 of our 308 deaths (Vesper 65, Marcella 53); in 1v1 our Vesper v their Vendetta 0
  kills to 6 in 29 fights though we hit first in 82 %; in even fights their Vendetta dies 3 % of the time and is in 66
  kills. Their stuns: Marcella's spell is on the victim in 21 of our 72 deaths before r300, Tavi 7.
- Our Varg (first pick, every game): 0 kills in 46 games, the most deaths (1.7), 294 gold.
- The lift the draft can give is bounded: in contact our melee hits 26–35 % of rounds and theirs 40–51 % whatever the
  champion, the same structural gap since p8 (LADDER_P8 §5). A composition changes who is in the fight, not that.

### 1.5 Drafts to copy, converted to our code (seeds for §3)

1. **The Vendetta core on every pick count**: Vesper + Vendetta + Heart of Ruin on 3 picks (their most common team, all
   sizes), + Marcella on 4, + a stunner (Tavi / Ryth / Cassi & Issac) on 5. Our code has Vendetta as the 5th pick only.
2. **Three carriers**: their Marcella and Vendetta each earn 1,200–1,600 gold; ours 300–430. In our code only the main
   gets gold weight 3 and the captures (the handoff). A second carry role for Vendetta / Marcella is a role change.
3. **The every-body-captures Prism team** for the big open maps (Prism > Vendetta > Marcella > Willow > Heart of Ruin).
   Prism as our main lost −21.5 in Part 4 (700 HP, no Vesper gold); theirs never dies (0 deaths in 9 games) and captures
   400 gems: in their team Prism is a farmer beside four others, not the carry.
4. **Marcella as a Focus nuker** (Bruiser of Focus): her spell is 2.0 × Focus at range 4 on a champion, on the victim
   before 21 of our 72 early deaths.

## 2. The base for spin-outs: `bots/rnd-base`

`bots/rnd-base` = cpp-p13 + only the bug-class fixes from cpp-p14: `fkit_learn` (live kits), the engine's capture
countdown (`capture_state`), damaging stuns hit camps (`kit.cpp`), the gate news, `MAXCG` 64 / `MAXLIVE` 80, `spent()`,
the per-kind tank share (`hit_share`, `ROT_K`), the LAB flag (the fight lab), and two kit lines that run only when the
champion is drafted (Tavi's field shop and his Focus build). Not in it: Capture on the main, Bruiser for Power, Prospector,
the order draft, Tavi in the draft. p13's PICKS and builds.


**rnd-base is level with p13** [measured]: vs the pool, training seeds J 100000–1 (1,120 paired cells): win +1.0 ± 2.0,
`rate` +0.007 ± 0.015, deaths −0.30 ± 0.29, worst opponent spar-fight −1.4 ± 3.7. Sprint 2 maps vs cpp-p13, 4 hashed
seeds (120 paired cells, the base = p13 jittered vs p13): win +2.5 ± 7.3, `rate` +0.078 ± 0.090. **One stratum moved:
the big open maps** (pool `open` `rate` −0.036 ± 0.011, win −7.8 ± 5.5; sprint 2 `s2big` −0.124 ± 0.076, win −15 ± 13),
as p14's did (P14 §4.8: open −7 to −12). One of the fixes costs the open maps; bisected in §4.
- Added to the base after the check (neutral for p13's draft, needed by every spin-out): the roles come from one rule
  (`draft.h` `MAIN_PREF` / `SECOND_PREF`, `pick_roles` used by both `world.cpp` and `draft.cpp`; p13's Vesper else
  Vendetta / Ren else Vendetta); the main's farm-all-game profile is keyed on the main role, not on Vesper (`champs.cpp`);
  **Varg is drafted where every altar is camp-gated** (`choose_pick`: the draft's `aside` 3 on every altar once its own
  stage is done, from the second pick; 01boss-battle: Varg's splash opens both monoliths, P14 §1.2b).
- Tooling: `tune.py` reads `ARENA_MAPS` (the paired jittered check on `maps_sprint2`) and reports it by size
  (`s2small` 30×30–35×35, `s2mid` 41×41–51×51, `s2big` 60×60+); `decode.mjs` decodes engine 2.0.0 replays.

## 3. Cards

### Card VC: the top teams' core, Vesper > Vendetta > Heart of Ruin > Marcella > Tavi (`bots/rnd-vcore`)

**Idea** (§1.1, §1.5 item 1): copy the most common top-10 team: Vendetta on every pick count, Varg out (0 kills in 46
games, the most deaths). **Code:** `PICKS` 1, 2, 11, 6, 10 (+ Varg 6th); the gated-map Varg rule (now in the base).
Roles unchanged (Vesper main, Vendetta second as no Ren).

| Rung | Result |
| --- | --- |
| 1 smoke (4 games vs p13) | drafted as intended (3 picks Vesper, Vendetta, Heart of Ruin; Varg on 01boss-battle as the second pick), buys, farms, banks, 0 faults; 2–2 |
| 2 fight lab vs rnd-base (140 games) | **kill share 0.593 ± 0.018 = +5.1 SE** (kills 2,095 v 1,458), the lab's biggest reading (Tavi for Marcella was +3.4 SE). Varg's 683 deaths on the base side are the gap: our Vendetta 587 / 525, Heart of Ruin 517 / 382 |
| 3 sprint 2, 4 seeds (120 paired cells vs p13) | win −6.7 ± 8.8, `rate` −0.020 ± 0.104; s2small +3.1 ± 20.7, s2mid −2.1 ± 14.9, **s2big −20.0 ± 12.2** |
| 4 pool, J 100000–1 (1,120 cells vs p13's base) | win +1.8 ± 3.5, `rate` +0.021 ± 0.028, deaths −0.43, crushed 146 v 186; **open −25.8 ± 7.7**, highneed +11.1 ± 7.5. **By team size** (per-map deltas, the strongest map feature: corr −0.55 with win): **3 picks (12 maps) +33.4 win pts**, 4 picks (16) +7.8, 5 picks (42) −9.6. Area and elk count correlate only through it |

**v2: Varg fifth, Tavi out** (on 5 picks this is p13's roster; 3 picks Vesper, Vendetta, Heart of Ruin; 4 picks + Marcella).

| Rung | Result |
| --- | --- |
| 4 pool, J 100000–1 | **win +4.6 ± 3.0 (1.5 SE), every opponent positive** (cpp-p12 +5.4, spar-fight +1.4, spar-pack +4.6, spar-order +7.1), `rate` +0.026 ± 0.027, crushed 165 v 186; by team size 3 picks +33.4, 4 picks +7.8, 5 picks −4.8 (= the base's own open-map loss, §4: the same roster); walled +8.5, highneed +11.5, open −14.1 ± 6.4 |
| 3 sprint 2, 4 seeds | win −3.3 ± 8.7; s2small (30×30–35×35, 3–5 picks) +15.6 ± 18.7, s2mid +4.2 ± 14.7, **s2big −27.5 ± 4.7: all five are 5-pick maps, where the roster is p13's, so this is the base's regression** (§4) |

**The draft by team size** (`PICKS_S` in `draft.h`: the first S picks per team size, `pick_at` reads
`cambc::draft::team_size()`; now in every spin-out that needs it). Screened on the maps of that size only (the variants
differ nowhere else), vs v2, pool, J 100000–1:

| Team size | Variant | win | `rate` | deaths |
| --- | --- | --- | --- | --- |
| 3 (12 maps, 192 cells) | Vesper, Vendetta, Marcella | −16.2 ± 6.1 | −0.145 ± 0.043 | +2.1 |
| 3 | Vesper, Vendetta, Tavi | −19.8 ± 5.5 | −0.133 ± 0.041 | +2.1 |
| 3 | Vesper, Vendetta, Ryth | −14.6 ± 5.7 | −0.147 ± 0.047 | +2.1 |
| 3 | Marcella, Vendetta, Tavi (a top-10 3-pick team; Vendetta the main) | −40.1 ± 5.7 | −0.353 ± 0.065 | +5.4 |
| 4 (16 maps, 256 cells) | Cassi & Issac for Marcella | +7.0 ± 5.1 | +0.081 ± 0.063 | **+6.9** |
| 4 | Tavi for Marcella | +2.3 ± 5.1 | +0.081 ± 0.061 | −1.1 |

Heart of Ruin third is worth 15–20 win points on 3 picks over any other third. 4 picks: nothing beats Marcella beyond
noise (Cassi & Issac's two bodies die 6.9 times more a game). **v3 = v2 + `PICKS_S` {Ve, Vd, H} / {Ve, Vd, H, M} /
{Ve, Vd, H, M, Vg} + the tank-share revert (§4).**

| Rung (v3) | Result |
| --- | --- |
| 4 pool, J 100000–1 | **win +6.1 ± 2.9 (2.1 SE)**, `rate` +0.041 ± 0.026 (1.6 SE), deaths −0.46, crushed 154 v 186; by opponent cpp-p12 +5.7, spar-fight −1.8, spar-pack +12.9, spar-order +7.5; open −3.9 ± 6.5 (v2 −14.1), held-out maps +4.7 ± 11.1; by team size 3 picks +32.3, 4 picks +9.1, 5 picks −2.5 |
| 3 sprint 2, 4 seeds | win +1.7 ± 8.3; s2small +15.6 ± 21.3, s2mid +2.1 ± 14.9, s2big −10.0 ± 6.1 (`rate` −0.069 ± 0.029: p13's roster there; part of the base's big-map loss remains) |

**Step 5 on v3** [measured]:

| Check | Result |
| --- | --- |
| pool, confirmation seeds J 100002–3 (never used for VC) | win **+4.0 ± 2.5 (1.6 SE)**, `rate` +0.029 ± 0.020, deaths −0.48, crushed 156 v 197; every opponent ≥ +1.4 (spar-fight); highneed +11.1 ± 5.4, open −0.8 ± 6.6 |
| plain head to head vs cpp-p13, 70 maps × both sides | **74 W / 66 L, margin +58** (p14 was 68–72) |
| plain, sprint 2 maps | **11 W / 19 L**, margin −123 (p14 12–18): worst s2-41x41 (−1,139) |
| plain, 14 ladder maps | 14 W / 14 L, margin +72 |

Below the ship rule (+2 points at ≥ 2 SE on confirmation seeds; head to head won): the pool says +4 to +6 on both seed
sets, the head to head is won narrowly, the unseen sprint 2 maps are still lost. Not a p15 yet.

| More checks on v3 | Result |
| --- | --- |
| pool, J 100004–7 (2,240 cells; never used for VC) | **win +4.6 ± 2.3 (2.0 SE)**, `rate` +0.037 ± 0.023, crushed 343 v 400; every opponent positive (cpp-p12 +7.9, spar-fight +1.8, spar-pack +3.0, spar-order +5.7); held-out maps +9.4 ± 8.8 |
| held-out opponents, J 100000–1 (840 cells) | win +3.5 ± 2.6: spar-steal +3.6, cpp-p10 +4.3, cpp-p8 +2.5 |
| why sprint 2 loses (plain 11–19) | three maps crushed both sides. **s2-41x41 is monolith-gated, 4 picks**: the Varg rule took Varg as the second pick and pushed Marcella out (Vesper, Varg, Vendetta, Heart of Ruin), and that team tributed 0 and died 21–26 times to p13's 0–2 in both games; 0 of 8 jittered games won (p13's mirror 5 of 8). The other two (30×30 cluster map, 35×35) are single-game chaos the jittered check doesn't repeat (s2small +15.6) |

**v5 (v4 was the race, none kept): on a camp-gated map the rest of the draft is p13's** (`GATED_PICKS` Varg, Vesper,
Marcella, Heart of Ruin, Vendetta, after the Varg rule fires): 41×41 jittered 0/8 → 3/8; sprint 2 over 4 seeds
+3.3 ± 6.8 (v3 +1.7 ± 8.3), s2mid +6.2 (v3 +2.1). Elsewhere v5 = v3 (no other map in the 70 is gated on 3 or 4 picks).

**Step 5 on v5 (the ship check)** [measured]:

| Check | Result | Ship rule |
| --- | --- | --- |
| pool, **confirmation seeds JSF 100100–1** (never used by anyone; p13's base played fresh) | **win +6.1 ± 2.7 (2.2 SE)**, `rate` +0.043 ± 0.022, deaths −0.31, crushed 146 v 187; cpp-p12 +11.1, spar-fight +5.7, spar-pack +1.8, spar-order +5.7; open +0.8, highneed +12.0 | ≥ +2 at ≥ 2 SE: **pass** |
| worst pool member | spar-pack +1.8 ± 4.6 | none worse beyond 2 SE: **pass** |
| plain head to head vs cpp-p13, 70 maps × both sides | **76 W / 64 L, margin +57, 0 faults** | won: **pass** |
| plain, sprint 2 maps | 13 W / 17 L, margin −78 (p14 12–18; jittered over 4 seeds +3.3 ± 6.8) | not in the rule |
| plain, 14 ladder maps | 14 W / 14 L, margin +72 | not in the rule |

All seed sets for VC (v3 / v5, pool): J 100000–1 +6.1 ± 2.9, J 100002–3 +4.0 ± 2.5, J 100004–7 +4.6 ± 2.3, JSF +6.1 ± 2.7;
held-out opponents +3.5 ± 2.6. **Frozen as `bots/cpp-p15`, zipped `submissions/cpp-p15.zip`** (a clean unzip is identical
to `bots/rnd-vcore`, builds and won a check game, 0 faults). Uploading is the user's call: the plain sprint 2 run is 13–17,
about where p14's 12–18 was when its zip was deleted, though the jittered sprint 2 check reads level and the pool, held-out
opponents and the 70-map head to head all read better.

## 6. Team A v team B (the user's question after the zip) [measured]

Plain head to head p15 v p13: as team A 40–30 (+108), as team B 36–34 (+7); sprint 2 9–6 v 4–11.
- **p13 has the side bias itself**: against the pool over 10 seeds (2,800 games a side) p13 wins 54.7 % as A and 48.2 % as B;
  in the sprint 2 mirror team A wins ~56 %.
- **VC gains the same on both sides**: paired over all 10 seeds, +5.1 ± 2.7 as A, +5.2 ± 2.5 as B; the gap of the gains
  −0.1 ± 3.0 (map-clustered over 70 maps). The plain run's split is chaos on top of p13's bias.
- One code asymmetry found and removed as a test: `camp_groups()` comes in the same order for both teams, in mirror pairs
  with team A's member first [measured on all 70 maps], so every lowest-index tie-break picks own-side groups as A and
  enemy-side ones as B. Team B reordering its groups to the mirror of A's (`sym::mirror_order`, ~21k fuel once at boot;
  the transform among rotation and the two reflections that fits both spawns and the camps) left team A identical game for
  game and moved team B by −0.7 ± 1.4 (pool, JSF) and +3.3 ± 8.6 (sprint 2): no effect. Not kept; saved as
  `docs/redo/patches/RND_side_mirror_order.diff`. Left unexplained: the rest of the side bias (the engine's round order
  starts with team A [rules: the starting team swaps each round], the altars' scan order, the spawn's first tile used as
  the spawn point). It costs both of our versions alike and the ladder side is random.

## 7. Contact micro: we walk away from adjacent enemies without hitting [measured]

In contact (an enemy within 3) our melee hit a champion in 26–35 % of rounds on the ladder against the top 10 (§1.4) but in
40–48 % in our own games (VC v p13, 28 ladder-map games): the gap depends on the opponent, so the pool can't see it.
Split by the nearest enemy's distance at round start (`contactd`, `adjwhy`, scratch):

| melee, enemy at distance | ladder: us | ladder: them | arena (VC v p13): us |
| --- | --- | --- | --- |
| 1 (adjacent): hit a champion | **57.5 %** | **83.0 %** | 68.6 % |
| 2: hit a champion (move + attack) | 26.8 % | 46.7 % | 37.3 % |
| 3 | 5.7 % | 7.9 % | 9.9 % |
| adjacent rounds where we **moved away without hitting** | **25.2 %** | 3.0 % | 19.8 % |
| adjacent rounds doing nothing (stunned or idle) | 6.4 % | 5.3 % | 5.4 % |

Not stuns: our bodies leave (Heal, Fall, a broken stance) and walk off before swinging, though a melee's move and attack
are separate allowances [rules]. **Piece: the parting shot** (`main.cpp` `parting_shot`, before `act`): a melee not in a
Kill, a committed stance or a farm hits the weakest adjacent enemy (with its reset) and then moves.

| Check (parting shot v VC v5, paired) | Result |
| --- | --- |
| fight lab v rnd-vcore | **kill share 0.610 ± 0.013 = +8.6 SE** (the lab's biggest reading) |
| pool, JSF 100100–1 | **win +5.5 ± 2.0 (2.8 SE)**, `rate` +0.071 (3.5 SE), **deaths −1.55 (5.3 SE)**, crushed 106 v 146; every opponent positive |
| pool, J 100004–5 (fresh for it) | **win +8.8 ± 2.1 (4.3 SE)**, `rate` +0.093 (4.9 SE), deaths −1.97, crushed 102 v 167; every opponent ≥ +4.6 |
| sprint 2, 4 seeds | **win +19.2 ± 5.8 (3.3 SE)**; s2small +3.1, s2mid +20.8, s2big +30.0; **as A +13.3, as B +25.0** |
| plain head to head v cpp-p13 | **70 maps 88–52** (A 46–24, B 42–28, margin +192); sprint 2 **18–12** (9–6 both sides); ladder maps **21–7**; 0 faults |
| plain head to head v cpp-p15 (VC v5) | 79–61 (A 41–29, B 38–32) |

**After it (v6 v p13, 28 ladder-map games, decoded):** adjacent rounds hit a champion **87.0 %** (v5 68.6 %; the top 10
v p13 on the ladder 83.0 %), moved away unswung **2.7 %** (v5 19.8 %, the top 10 3.0 %); one step away hit 50.4 % (the top
10 46.7 %). The contact gap the replays showed is closed against p13.

**Kept: rnd-vcore v6 = v5 + the parting shot.** It fixes the unseen-map weakness too (sprint 2 13–17 → 18–12 v p13)
and the team B side (sprint 2 as B: 40 % → 65 % jittered). **`submissions/cpp-p15.zip` = `bots/cpp-p15` = v6** (re-frozen; the clean unzip is identical to
`bots/rnd-vcore`, builds, 0 faults). v5 = v6 minus `docs/redo/patches/RND_parting_shot.diff`.

## 8. Distance 2: we retreat, they step in or tribute [measured]

Our / their melee rounds that start one step from an enemy (ladder, `d2why`): hit a champion 26.7 v 46.4 %, **moved away
37.4 v 15.8 %**, moved without reaching 20.2 v 11.4 %, **recall or tribute 1.3 v 17.3 %**.
- **Committing harder loses** (fight lab v rnd-vcore v6): `STANCE_PL` 0.69 → 0.8 −3.1 SE, `STANCE_LOW` 0.45 → 0.35 −0.2 SE,
  both −4.5 SE. The break rule fits our micro; the retreats are not a threshold to loosen. Race stopped, variants deleted.
- **Tribute under pressure:** `bank()` aborted at the altar with any enemy within 3 and more than 10 gems, and the body walked
  off with its bag. Damage doesn't break a tribute, only a stun, death or a lock [rules]. Piece: abort only when my HP
  can't outlast the channel (ceil(bag / 10) turns) under the enemies' Strength within 4 × `BANK_SAFE` 1.5 [guess].
  **Inert:** 1 game of 1,120 changed on the pool, none of 120 on sprint 2: our bodies rarely *choose* Bank with an enemy
  near, so the top teams' tributes under pressure are a decision (price) difference, not the abort. Dropped.

## 9. The #1 team's habits (TOP_TEAMS_R5, "fish") on p15: `bots/rnd-p15b` [measured]

`bots/rnd-p15b` = a copy of cpp-p15 (rnd-vcore v6) to test R5 §7's F1–F5. Every variant is judged paired against p15
itself: its jittered copies play cpp-p15 and pair with rnd-p15b (= p15) playing cpp-p15 on the same cells (a mirror base).

**Where v6 stands on fish's measures** (28 decoded v6 v p13 games): crew at a camp hit 1.39 (fish 2.72), solo 74 % (25 %),
an ally within 5 59 / 40 / 47 % by phase (82 / 71 / 62 %); 35.7 banks a game, median bag 15 (fish 29.5, bag 26).

**F1, the pack, on the existing stack machinery** (stack mode = no per-body share, followers ×`STACK_FOLLOW` on a lower
slot's claim, the claim rule that spreads bodies off, one capturer by the handoff; it ended at r100 / r300). `PACK_SPLIT`:
one pack until then, two packs after (`group_slots` on every map).

| Variant (paired v p15) | 70 maps, J 0–1 | sprint 2, 4 seeds | deaths |
| --- | --- | --- | --- |
| P1 one pack all game | −7.1 ± 4.3 (`rate` −2.1 SE) | −10.8 ± 6.4 (s2big −32.5) | |
| P2 one pack, two from r300 | 0.0 ± 4.2 | −7.5 ± 6.1 (s2big −20.0) | |
| P2 + `STACK_FOLLOW` 8 (race seed 2) | −3.6 ± 4.6 | | −0.1 |
| P2 + F3 (race) | +0.4 ± 4.6 | | 0.0 |
| P2 + F2 + F3 | **−12.5 ± 4.6** | | **+6.1** |
| P2 + follow 8 + F2 + F3 | **−17.9 ± 4.1** | | **+6.5** |

- P2's pack is real but half fish's: crew at a camp hit 1.72 (p15 1.32), solo 51 % (78 %), an ally within 5 66 / 56 / 57 %.
- **Cassi & Issac lost a third time** (+6 deaths a game even in the pack): two 600 / 900-HP bodies die in our fights.
- More packing reads worse, P2 level. Caveat: no local opponent hunts lone walkers as fish does (its victims die walking
  83 %, alone 36 %), so the pack's defence is invisible here; only the ladder can price it.

**F3, F4, F5 on p15 alone** (paired v p15):

| Piece | J 0–1 (race) | J 2–5 | deaths | Verdict |
| --- | --- | --- | --- | --- |
| F3 bank due at walk ≤ bag / 2.5 (bag ≥ 8) | +1.8 ± 2.9 | −0.7 ± 2.1 | +0.1 / −0.05 | level: dropped (p15 already banks 35.7 times a game) |
| F5 Durability third, then Bruiser Strength on Vesper / Vendetta / Marcella, Bruiser Health on Heart of Ruin | +2.1 ± 3.4 | +1.6 ± 3.0 | **−0.49 / −0.80** | small and consistent (crushed 67 v 86 of 560); below the ship rule alone |
| F3 + F5 | +1.4 ± 3.4 | +1.3 ± 2.8 | −0.34 / −0.56 | as F5 |
| F4 Cassi & Issac first (stance target −6 hits, kill price ×1.6), fight lab v a Cassi & Issac drafter | kill share 0.499 v the control's 0.496 | | | no effect: dropped |

**spar-fish** (`bots/spar-fish`, a style bot, edits marked `// SPARRING`): p15 + the two-pack farm (P2) + spar-fight's
hunting edits (kill ×1.5, hunt reach +4, joins from 16, attacker bonus 2, `KILL_PLOSE` 0.8) + F5's builds; p15's draft
(Cassi & Issac die in our code) and stance (fish retreats as often as anyone, R5 §4.1). The local stand-in for an
opponent that runs down lone walkers.

| Against spar-fish (paired v p15 v spar-fish, J 0–1) | Result |
| --- | --- |
| p15 v spar-fish | p15 wins 56.4 % ± 3.5: a credible opponent |
| **P2 (the pack)** | **−9.3 ± 4.6 win pts, `rate` −2.9 SE, deaths +1.0**: the pack loses even against a hunting pack |
| F5 (items) | −0.7 ± 2.6: level |

**Verdict on R5's plan, as built on our code: don't ship any of it.** The pack loses or is level against p15 and against
spar-fish; Cassi & Issac lose a third time (+6 deaths); the bank rule and Cassi-first are level; F5 is small (+1.6 to +2.1
v p15 over six seeds, deaths −0.5 to −0.8, level v spar-fish). **`bots/rnd-p15b` = cpp-p15 + F5** (the one piece that
didn't lose, unproven: an alternative to try on the ladder, not a ship). Not built: a true fish pack (a leader's target
taken outright, bodies walking legs together, a new `pack.cpp`): every partial step toward it read worse here, so it is a
big rewrite with no local signal behind it. The ladder test of p15 against fish is the next evidence: whether fish still
kills our lone walkers now that our contact micro is fixed (§7). Patches: `docs/redo/patches/R5_*`.

## 10. The 27 Oct cleanup (before committing)

- Bots trimmed to `cpp` (the dev line, a copy of `cpp-p15`), `cpp-p15` (the ladder entry), `cpp-p13`, the style bots
  `spar-fight` / `spar-pack` / `spar-order` / `spar-steal` / `spar-fish`, and `mapdump`. Everything deleted is recoverable
  (bots/README.md: the zips in submissions/, patches in docs/redo/patches/, git history for the Python bots).
- The judge re-pointed: bar and base `cpp-p15`; `tune.POOL` = cpp-p13, spar-fight, spar-pack, spar-fish;
  `tune.HOLDOUT_OPP` = spar-steal, spar-order (cpp-p12 / p10 / p8 deleted). p13's base runs deleted (stale under the new
  base). The judge is due a rethink first thing next session (`NEXT_PROMPT_P15_LOSSES.md` Step 0).
- The scratch scripts that found this session's wins are in the repo: `tools/replay/farm/contactd.py`, `adjwhy.py`,
  `d2why.py`, `champecon.py`, `killkit.py`, `famsum.py`; `tools/sides.py`, `permap.py`, `featcorr.py`, `smoke.py`;
  `tools/replay/mapfeat.mjs`.

## 5. What this session says

- **The draft was the lever, and the biggest piece was the smallest pick count.** VC's 3-pick team (Vesper, Vendetta,
  Heart of Ruin, the top teams' most common) is worth ~+32 win points on the 12 three-pick maps; 4 picks +9; on 5 picks
  p13's roster stays (every swap there lost: Tavi −10, Willow −5, Cassi & Issac −5, the Prism team −30). Team size, not
  map size, was the feature that sorted the per-map deltas (corr −0.55).
- **A p14 "fix" was a bug:** the per-kind tank share cost the big open maps (bisect, §4). Measured shares from the top
  teams' replays don't transfer into constants climbed with the old model.
- **Copying their draft worked where copying their economy didn't:** their Vendetta's gold weight and build (§3 VC v4) did
  nothing for ours; the gap there is contact micro (our melee hits 26–35 % of contact rounds, theirs 40–51 %).
- Dropped: the stun chain (two iterations, lab level), the Prism team (losing on 5 picks), Willow as a separate line
  (equal to Marcella on 4 picks).
- Next: the contact-micro gap (§1.4), measured in the lab; the 5-pick big-map loss that remains (s2big −10 ± 6 with p13's
  roster; part of the base, not the draft); a 5-pick draft that beats p13's (none of four did).

**v4 tries (race, `race.py --base rnd-vcore --seeds 2`, pool, paired with v3's cells):** Vendetta's gold weight 1 → 2
(`ROLE_GOLD[1]`, three carriers as theirs) −0.1 ± 1.9 win, `rate` −0.008; Vendetta builds as theirs (Jungle → Bruiser
Strength → Bruiser Health) −0.8 ± 2.0, deaths +0.52; 5 picks Tavi for Marcella +0.4 ± 1.8, `rate` +0.005; 5 picks
Cassi & Issac for Marcella −4.7 ± 2.2, deaths +4.4 (dropped). **None kept: v3 stands.** Their Vendetta out-earns ours
3 : 1 (§1.2), but neither the gold weight nor their build moves ours; it is how it fights (in contact our melee hits
26–35 % of rounds, theirs 40–51 %), not what it owns.

### Card AC: the stun chain, Vesper + Tavi + Ren + Ryth + Marcella (`bots/rnd-stun`)

**Idea:** every body but the carry stuns (Tavi 1.6, Ren 1.1, Ryth area 1.0, Marcella's stun attack; stun-immune Marcella),
so a fight is a chain of one-round stuns [sdk]. **Code v1:** `PICKS` 1, 10, 8, 0, 6, 2; Ren is the second (`SECOND_PREF`).

| Rung | Result |
| --- | --- |
| 2 fight lab vs rnd-base, v1 (draft only) | kill share 0.507 ± 0.013 (+0.6 SE): level. Ren 356 / 536 and Ryth 322 / 529 die as Varg does; one-round stuns from bodies that each act alone don't chain |

**v2:** a body's stance target prefers a stunned enemy (`upd.cpp` `stance_target`, `STUN_PREF` 8 hits [guess]), and the
tank-share revert (§4).

| Rung | Result |
| --- | --- |
| 2 fight lab vs rnd-base, v2 | kill share 0.491 ± 0.013 (−0.7 SE): level again. Ren 346 / 555, Ryth 301 / 545 deaths |

**Verdict: dropped after two iterations.** A one-round stun every 8 rounds per body doesn't chain without timing across
bodies (the 8 shared bytes carry no cast clock), and the stunners we add are melee bodies with 900–1,200 HP that die as
Varg did; v1 → v2 changed who we hit, not the kill count. The stun that does pay is Tavi's on 4 picks (+2.3 in VC's
screen) and Heart of Ruin's landing, both already in VC.

### Card PR: the top-10 Prism team (`bots/rnd-prism`)

**Idea** (§1.2, §1.5 item 3): their big-map team, Prism > Vendetta > Marcella > Willow > Heart of Ruin, wins the farm race
2 : 1 without fights (0–9 deaths a game) with every body capturing; Prism 400 gems a game, 0 deaths in 9 games. On 3 and
4 picks their Prism + Vesper drafts: Prism, Vesper, Heart of Ruin / + Marcella. **Code:** `PICKS_S` {P, Ve, H} /
{P, Ve, M, H} / {P, Vd, M, W, H}; the area-spell kit (`P14_area_spell_kit.diff`: Prism's area on the tile covering most
of the group, her spells in the farm model as `Sc`); **Willow's heal** (new: `Kit::heal_ally`, the ally in range missing
the most HP once it misses a heal's worth, 3 × Focus, or is below `HEAL_ALLY_HP` 0.5 [guess]); Prism builds Focus
(Treasure → Jungle → Bruiser Focus); Vendetta is the main where there is no Vesper (`MAIN_PREF`).

| Rung | Result |
| --- | --- |
| 1 smoke (3 games vs p13) | drafted as intended, Willow heals 1,260–2,460 HP a game, Prism casts and farms (14–45k camp damage), 0 faults; 2–1 (lost 02harvest 554–1,040: their Vendetta 455 gems, ours 238) |
| 2 fight lab vs rnd-base | **kill share 0.546 ± 0.015 = +3.1 SE** (kills 2,085 v 1,756); Heart of Ruin 636 / 410, Vendetta 365 / 278; Prism dies most (367 / 666), Willow 160 / 356 |
| 4 pool, J 100000–1 | **win −14.1 ± 4.1**, `rate` −0.097 ± 0.033, deaths +1.6, crushed 243 v 186; **open −40.6 ± 7.2**; by team size 3 picks (P, Ve, H) +16.3, 4 picks +3.2, **5 picks (the Prism team) −29.3** |
| 3 sprint 2, 4 seeds | win −19.2 ± 8.1; s2big −35.0 ± 6.1 |

**v2:** 5 picks Prism, Vesper, Vendetta, Marcella, Willow (Vesper back as the main: the Vesper-less team has no bonus gold,
and our Vendetta main with gold weight 3 doesn't farm like theirs).

| Rung (v2) | Result |
| --- | --- |
| 4 pool, J 100000–1 | win −10.6 ± 3.8, `rate` −0.077 ± 0.030, deaths +1.3; open −30.5 ± 7.1; 5 picks −23.5 (v1 −29.3) |
| 3 sprint 2, 4 seeds | win −15.8 ± 8.3; s2big −32.5 ± 8.5 |

**Verdict: dropped after two iterations.** Losing. The 5-pick Prism team loses the big maps by ~30 points with or without Vesper; its
3-pick (Prism, Vesper, Heart of Ruin) +16 is half of VC's +32 on the same maps. Next iteration if kept: find why the five
farm slower on big maps (decode a game: Prism and Willow capture little in our handoff; theirs every body captures).

### Card HL: two carries and a healer, Vesper + Vendetta + Heart of Ruin + Willow (`bots/rnd-heal`)

**Idea** (brief's AE, after AC was dropped): VC's core, with Willow healing whichever carry is in a fight (3 × Focus =
420+ HP every 8 rounds at range 4 [sdk]). **Code:** VC v3 + Willow's heal (`Kit::heal_ally`, as in PR) + `PICKS_S`
{Ve, Vd, H} / {Ve, Vd, H, W} / {Ve, Vd, H, M, W} (Varg only on gated maps).

| Rung | Result |
| --- | --- |
| 1 smoke (2 games vs p13) | Willow heals 4,200–6,720 HP a game, 0 faults, 1–1 |
| 2 fight lab vs rnd-base | **kill share 0.589 ± 0.017 = +5.3 SE** (as VC's 0.593) |
| 4 pool, J 100000–1 | win **+5.1 ± 3.4**, `rate` +0.042 ± 0.027, **deaths −0.79 ± 0.39 (2.0 SE)**, crushed 137 v 186 (VC v3 154); highneed +13.9, **open −17.2 ± 9.0**; by team size 3 picks +34.9, 4 picks (Willow for Marcella) +9.4, 5 picks (Willow for Varg) −5.0 |
| 3 sprint 2, 4 seeds | win −4.2 ± 8.4; s2small +6.2, s2mid −2.1, s2big −15.0 ± 10.8 |

Level with VC v3 on the pool (+5.1 v +6.1 on the same seeds), fewer deaths and crushed losses, worse on the big maps
(Varg out on 5 picks costs again, as in VC v1). Next: Willow on 4 picks only, Varg back on 5 (= VC v3 with Willow for
Marcella on 4 picks).

**v2:** Willow on 4 picks only, Varg back on 5 (VC v3 with Willow for Marcella on 4 picks). Pool J 100000–1: win
+6.3 ± 3.0, `rate` +0.042, deaths −0.54 (VC v3 +6.1, +0.041, −0.46 on the same cells); 4 picks +9.4 (VC +9.1); sprint 2
−10.0 ± 8.8. **Verdict: merged into VC's line, not a separate bot.** Willow and Marcella are worth the same on 4 picks;
Willow on 5 picks costs Varg's big-map farm. The heal code (`Kit::heal_ally`) works (4,000–6,700 HP healed a game) and
stays in `bots/rnd-heal` for any later healer draft.

## 4. The big-map regression in the base (bisect) [measured]

rnd-base lost the big open maps against p13 with p13's own roster (pool `open` −7.8, sprint 2 `s2big` −15; VC v2's s2big
−27.5 on 5-pick maps, the same code there). Each fix taken out of rnd-base once, sprint 2 vs p13 over 4 hashed seeds (120
paired cells each; s2big = the five 60×60+ maps, all 5-pick):

| rnd-base minus | win | s2big win | s2big `rate` |
| --- | --- | --- | --- |
| nothing (rnd-base) | +2.5 ± 7.3 | −15.0 ± 12.7 | −0.124 ± 0.076 |
| `MAXLIVE` 80 → 48 | +0.0 ± 6.7 | −17.5 ± 12.9 | −0.137 ± 0.074 |
| **the per-kind tank share (`ROT_K` = `TANK_K`)** | **+8.3 ± 7.0** | **−5.0 ± 11.6** | **−0.032 ± 0.029** |
| the gate news | −2.5 ± 7.2 | −15.0 ± 14.5 | −0.128 ± 0.074 |
| the engine's capture countdown | +0.0 ± 6.3 | −20.0 ± 8.5 | −0.122 ± 0.064 |
| `fkit_learn` (p13's table) | −3.3 ± 6.0 | −22.5 ± 10.8 | −0.141 ± 0.059 |

Only the tank share moves it. `ROT_K` 1.5 (P14 §1.5, R4-1: the top hitter's share of a golem / monolith's hits in the
top teams' games) lowers the damage a body expects from a golem below what `TANK_K` 1.957 says, and `TANK_K` / `KEEP_HP`
were climbed (SPSA, p13) with the old share in place: our bodies take golems with fewer partners than our own tuned model
allows. **Pool check (J 100000–1, vs p13's base):** rnd-base minus the tank share: win **+3.1 ± 2.0** (rnd-base +1.0),
`rate` +0.019 ± 0.014, open +2.3 ± 5.4 (rnd-base −7.8), worst opponent spar-fight −1.8. **Reverted in the base and every
spin-out** (`hit_share`, `ROT_K`, `rotates()`, `Mons::rot`, `Clear::dmg_rot` deleted; p13's `tank_share` back).
