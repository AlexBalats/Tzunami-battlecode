# The three ways to the top, measured (27 Oct, NEXT_PROMPT_TEAMFIGHT)

Tags: [measured] our matches or decoded replays; [calc] arithmetic on measured numbers; [rules] / [sdk]; [guess] unchecked.
Data: the top 7's ranked games (`runs/squad/top/*`, team 0 = them), v62's 150 scrims v the top three (`runs/squad/us`,
11 wins), v62's 245 A/B scrims v ranks 45–99 (`runs/squad/ab`, "the A/B band": our climb band), a TRACE build of p17
v spar-fish (140 games), 6,000 of our ranked games (match list only).

## 0. The judge, recalibrated (JUDGE.md §8)

- **Local results predict the ladder; they are over-scaled, not blind.** Every shipped version since p4 replayed locally
  v two fixed references (spar-fight, spar-fish; 140 games each) against its ladder performance rating
  (`tools/ladder/perf.py`: the Elo that fits each version's ranked games, opponents at today's rating):
  r = 0.96 over the 11 versions, 0.98 from p10 on; gems/round and deaths track as well (r 0.97 / −0.95).
  **Slope ~0.3**: a local Elo gain shows on the ladder at about a third of its size. p13 → p15: +94 local, +27
  predicted, +22 measured. So "+20 on the ladder" needs about +70 local Elo (~+10 win points v a 50 % reference).
- The earlier read "p13 = p15 on the ladder, so the mirror is blind" came from eyeballing ratings; the per-version
  perf says p15 was +22 ± 34 over p13, as the local gain predicted at slope 0.3.

## 1. The team fight: coordination is not the gap [measured, `tools/replay/farm/teamfight.py`]

Engagements = champion hits chained by shared bodies (area spells attributed to the enemies whose HP fell near the point).

| | v62 v top 3 (us / them) | v62 v the A/B band (us / them) | top 7 among themselves |
| --- | --- | --- | --- |
| rounds with 2+ hitters: all on one target | 75 / 80 % | 77 / 84 % | 72–86 % |
| commit spread (first to last mate's first hit), median | 5 / 4 rounds | 6 / 4 | 4–5 |
| time to kill (first hit to death), median | 8 / 7 rounds | 7 / 7 | 6–8 |
| first to leave strands a mate (dies within 10) | 11 / 3 % | 5 / 5 % | 4–10 % |
| per body in engagements: max HP, damage a hit, hits a body-round | **1,594 / 1,906, 103 / 135, 0.31 / 0.36** | 1,878 / 1,902, 133 / 126, 0.35 / 0.32 | — |
| 1v1, 2v1, 2v2 engagements: kills a 100, us / them | 4 / 8, 7 / 20, 11 / 30 | 9 / 4, 21 / 9, 27 / 20 | — |

- Focus, commit and time to kill are level with the top 7. Against the A/B band we win fights at every size.
- Against the top three we lose at every size, even 2v1, because each of their bodies is stronger (HP −16 %, damage a
  hit −24 %, hits a round −14 %; level at r ≤ 150, the gap grows with their economy). A shared target can't fix that.
- **Not built:** one target / one commit for the bodies in contact. The fight gap is strength, and strength is the farm.

## 2. Lone farming speed [measured, `farmeff.py`, `budget.py`, `bankleg.py`, `tusum.py`]

- Captured gems per 100 live body-rounds, r300–800: top three 30.1 v our 9.3 (1.6× from camp damage a round, 22.4 v
  13.8; 2.0× from damage per gem, 75 v 148). Against the A/B band the whole game is nearly level: camp damage 70.4k v
  72.8k a game, captured gems 783 v 853 (r100+); only the middle converts worse (r300–800: 14.6 v 27.0 gems / 100
  body-rounds, 83 v 55 damage a gem). Our damage is rarely stolen (3–5 %).
- Where the rounds go (r300–800, v the A/B band, us / them): hit 12.7 / 14.1 %, walk to farm 30.6 / 33.0, **walk home or
  to an altar 16.0 / 12.4**, still near a live camp 3.0 / 1.7, at a dead camp (capture / respawn wait) 10.5 / 11.3.
  Our Vesper hits 10.4 % of its rounds (theirs 13.1 %) and stands near live camps 4.1 % (2.1 %).
- Tributes: 19 v 18 a game with the same legs (out 29 / 26, back 20 / 19 rounds median), but **bags of 28 v 36**
  (fish 45, Mite 51, Trzy 46, NEET 57, Ad Astra 64): their bigger bags are more income between trips, not a different
  bank rule. Leg rounds a gem tributed 2.35 v 1.68.
- p17's own turns (TRACE v spar-fish): farm 60 % (moving 37, hitting 12.6, capturing 4.1, waiting 3.8, idle 1.2), heal
  10.9 % (walking home 6.2, recall 2.5), bank 10 %, kill 8.6 %, dead 7.9 %.

## 3. The big takes [measured, `bigmap.py`, `campsafe.py`, `visits.py`, `wake.py`, the TRACE `clear` lines]

- Camp damage on 5+ camp groups: top three 40 % of theirs, ours 28 %; the A/B band 38 % v ours 32 %. **Per map the gap is
  whole groups we never take**: middle 5+ groups (00stampede, 01elk-arena, 01gold-rush, 01corridors, 00ribs,
  00reverse-spiral, 02harvest, 00monolith, 01starfish, 00swirl, 00collision) and some own-side ones (00eight, 00expanse,
  02fields, 00great-wall): 20–127k damage a game by them, ~0 by us.
- How they take them: in one visit (2+ sessions 15–17 % of 5+ claims, ours the same), from inside monster range like us
  (3–5 % of hits out of every camp's range), one body tanking ~85–90 % of the damage like ours, **with more bodies**:
  5+ claims with 2.52 bodies (top three) / 2.25 (A/B band) v our 2.07 / 1.95; 8.9 / 8.1 such claims a game v 4.3 / 7.1.
  They accept more damage a hit on 5+ groups (1.64 % of max HP v 1.31 %).
- The rules say damage wakes the whole group [rules l.208]; the replays agree: a lone hitter's HP loss tracks the
  Strength of the group's live strikers in range (slope 0.46–0.55), undamaged ones beside damaged ones hit too.
- **Our clear model overstates monster damage about 2.3×.** Monsters land 0.53–0.58 of their Strength a round in range
  (item reductions: an elk's 60 lands as 37–42 on many bodies; 26–34 % of in-range rounds deal nothing). In p17's own
  clears (12,225, TRACE) a lone body loses 0.36–0.46 of the damage the model predicted (≤ 2 camps 153 v 336, 3–4 camps
  260 v 562, 5+ 376 v 1,048). The need model (`need_k_r9`) asks whether *each* body survives a `TANK_K / k` share of that
  overstated damage above `KEEP_HP`, so 5+ groups price out (k = 0: never taken) and every take asks for more bodies.

## 4. Built: the calibrated clear model (`MON_HIT`) [measured]

`model.h` `MON_HIT` (1.0 in `bots/cpp` = p17): a live monster's damage a round as a share of its Strength, in
`clear_model`. Variants `_t_mh5` (0.5) and `_t_mh65` (0.65).

- Mechanism, mh5 plain v p17 (140 games, decoded): 5+ groups 35.9 % of our camp damage (p17's side 32.3 %); 5+ hits 190
  v 150 a game; middle 5+ takes on 02harvest 22.5k v 9.2k, 02geodes 16.9 v 5.1, 02fields 17.6 v 0, 01starfish 81 v 7,
  00stampede 9.3 v 3.1; camp hits 14.0 v 13.1 per 100 live rounds; bodies per 5+ claim 1.99 v 1.89 (the top three 2.52);
  banked level (754 v 755), deaths 9.7 v 9.0.
- Plain single runs (inside noise): mh5 v p17 75–65, v spar-fish 81–59 (p17 86–54); mh65 74–66, 87–53.
- **Paired v p15 (1,120 games, base p17): mh5 −3.2 ± 2.7 win pts, rate −1.7 SE, deaths +0.53; mh65 −0.4 ± 2.3, rate
  −1.8 SE, deaths +0.42.** Under mh5 our deaths to monsters rose 1.04 → 1.48 a game, to champions 7.99 → 8.24.
- **SPSA re-tune** of the coupled constants (`MON_HIT`, `KEEP_HP`, `TANK_K`, `HEAL_NOENEMY_HP`, `HEAL_K`, `WAIT_MAX`,
  `BAG_CAP`, `WALK_OUT`; 40 iterations v p15, `runs/tf/spsa_mh.json`) → MON_HIT 0.61, KEEP_HP 0.29, TANK_K 1.18,
  HEAL_NOENEMY_HP 0.85, BAG_CAP 71: **confirmation seeds −5.7 ± 2.6 win pts, rate −2.3 SE, deaths +0.69. Not kept.**
- Reading: the 2.3× overstatement is a safety margin the bot needs, for enemies that arrive mid-take and for unlucky
  takes (the mean is right, the tail kills). A calibrated model needs an exposure term in the same change; alone it
  loses. `bots/cpp` = p17 (the constant removed).

## 5. Why their bodies are "so much more efficient": the walk, measured [measured]

`gaps.py` (every stretch between productive rounds, priced against the shortest walk), `trip.py`, `jumps.py`,
`wander.py` (the TRACE choices joined to the replay), on v62 v the top three, the A/B band, and 240 new scrims v
NEETCoders (9 / 120 won) and Claudus Maximus (8 / 120) (`runs/tf/s1`).

- **Total waste is level.** Rounds beyond the shortest walk a body-game (r100–1000): v the top three 160 / 156, the A/B
  band 189 / 181, Claudus 167 / 161 (us / them). Group-to-group trips: we walk the shortest path (1.06× v 1.00×) but
  stand 2.4 rounds a trip mid-way (them 0.9).
- **Ours alone:** home → home loops with nothing done (23–26 rounds a body-game v 9–17); the home exit (home → first
  camp hit) 0.8–3.2 rounds *over* the shortest walk for our dashers, 1–6 rounds *under* it for theirs.
- **The difference is the dash hop.** Jumps (2+ tiles) are equally frequent (~12 per 100 moving rounds, both sides: the
  dash on cooldown). But the share of jumps that **cross a hole** (or a tile nobody stands on): Claudus 17–20 %, the top
  three 11–13 %, the A/B band 10.7 %, **ours 7–8 %**. Walk rounds skipped by hops, a dasher-game: **Claudus ~180–197,
  ours 20–29 in the same games**; normalised per 100 moving rounds the top three save 2.3× ours (Vesper 13.6 v 6.0).
  (23–33 % of Claudus's hops have no walk found within 40 tiles of passable-by-observation tiles, v 7–10 % of ours: the
  proxy over-counts some, the direction holds.) Dashes cross holes, never walls [rules l.147–159].
- **Ours by construction:** Nav L4 spends the dash on every cooldown for a 2-tile gain on open ground (TOP_TEAMS §11),
  and every field is walk-only, so a route never goes to a hop and the dash is usually on cooldown when one is there.
  p17's TRACE: 206 dropped farm legs a game v 100 that arrive (117 farm → other farm switches a game), but the
  group-to-group walks they make are near shortest, so the retargets are not where the rounds go.
- **Built: hold the dash for a hop** (`hop_ahead`: look along the path for the dash's cooldown; hold when a step ahead
  drops the walk field `HOP_HOLD` 3 more than a dash now). Mechanism small (hops 0.96–1.06 v 0.93–0.97 per 100 moving
  rounds, walk saved 42–50 v 37–44 a dasher-game); **paired v p15 −3.0 ± 1.8, rate −1.5 SE. Not kept alone**; patch
  `docs/redo/patches/P18_hop_hold.diff` (it is half of the portal design).
- **Built after (27 Oct night): the portal routes** (§5.1); the fix described next was built and lost. The design as planned: portals found at boot (one-wide hole strips
  with a legal 2-step dash path), a field per portal side, routes = min(walk, walk to a portal + 1 + walk from its far
  side + the cooldown left), Nav walks to the portal's near side with the dash held (P18_hop_hold) and hops, prices read
  the portal distance, the crew without a dash keeps the walk. The cheap form (thin holes passable) lost twice because
  the dash was on cooldown at the hole (§9.5); holding it is the piece that was missing. Target: Claudus-level hops on
  hole maps (`jumps.py`), home exits at or under the shortest walk (`gaps.py`).

### 5.1 The portal routes, built and judged (27 Oct night) [measured]

Patch `docs/redo/patches/P18_portals_v2.diff` (on p17). Portals = free tile, hole, free tile in a line (a legal 2-step
dash [rules]), valued by the walk they cut on the home field and my field, `PORT_K` 6 kept `PORT_GAP` 3 apart, dash bodies
only. A route via a portal = my walk to its near side (`F_me`) + 1 + the goal field at its far side + the cooldown left;
taken when it beats the walk by `HOP_MARGIN` 3; Nav walks to the near side (`NavKey::Portal`) with the travel dash held
when it will be needed, then hops. v1 and v2 also priced takes and banks on the portal routes (`walk_to`, `gd` / `ad`
from one far-side field a portal side).

| form | v p15, paired (1,120 games, base p17) | deaths |
| --- | --- | --- |
| v1: as above | −5.8 ± 2.7 win pts, rate −0.8 SE | +0.76 |
| v2: + the scan spread over turns (v1's one-shot scan ran hole-heavy maps out of fuel: rollovers 4.5 → 12.1 a game, 1,187 of 1,700 before r100), hops only with no enemy in sight and never into an awake camp's reach | −4.0 ± 2.0, rate −0.8 SE | +0.33 |
| v3: v2 with the prices on walk distances (routes only) | −3.3 ± 1.4, rate −1.9 SE | +0.08 |

- **The mechanism landed** (v1 plain v p17, decoded): hops 17–19 % of our jumps (Claudus 17–20 %), 2.05–2.22 per 100
  moving rounds (Claudus 2.06–2.58); home exits under the shortest walk (Vendetta −1.7, Vesper −0.7 rounds; p17 +0.4 /
  +1.0).
- **But the saving is small:** total waste beyond the shortest walk 183 v 189 rounds a body-game; home → camp took the same
  17.5 rounds (v1 chose farther takes). `jumps.py`'s "walk rounds saved" over-counts: its walk-around uses the tiles
  anyone stood on, which misses walkable tiles nobody used, so a hop's saving looks bigger than it is (the comparison
  between teams on the same maps holds; the absolute ~190 a dasher-game does not).
- **Verdict: not kept.** The hop gap is real but worth a few rounds a trip on our 70 maps, and every form paid more
  (standing for the cooldown at the near side, held travel dashes, detours) than it saved. `bots/cpp` = p17.

## 6. What this session leaves [measured unless tagged]

- The judge: local paired runs against fixed references predict the ladder at slope ~0.3 (JUDGE §8); use them.
- The fights: coordination is level; strength is the gap, and strength is the farm (§1).
- The farm gaps, re-ranked after §5.1: the big takes (whole 5+ groups we never price, §3: needs an exposure-aware take
  model, not the calibration alone) and the per-round yield (damage a hit, gems a damage); the walk is level in total
  and the hop routes built lost (§5.1); home loops (§5) and bags (§2) are small.
- Not built: the team fight (no gap), the squad again (Step 4: it stands on the big takes).
- Everything this session built lost and is a patch: `P18_hop_hold.diff`, `P18_portals_v2.diff`; the clear-model
  calibration and its SPSA are numbers in §4 (one constant).
