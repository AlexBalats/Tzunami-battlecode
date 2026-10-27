# cpp-p4 on the ladder: what the routing bought, and where we still lose (23 Oct)

> "uploaded the new bot and its still bad … it seems we lose out on fights and perform only better on specific maps"
> (user, 23 Oct)

The routing build (ROUTING pieces 1, 2 and 4) went up as `submissions/cpp-p4.zip`. Its 23 ladder losses are in
`replays_from_others/cpp-p4`. They were decoded with `tools/replay/decode.mjs` and `farm/flip.py`, and set against
cpp-port's 57 losses (REPLAYS.md), re-decoded with the same scripts. Team 0 is us; the numbers are means per loss
unless a line says otherwise. All [measured] unless tagged. The measure scripts are in `tools/replay/farm/`
(`freehit`, `mvatt`, `noback`, `goldsrc`, `timeuse`, `takes`; usage in its README).

## 1. Did the routing gains reach the ladder? Yes, and they were not the gap

| Measure | cpp-port losses (57) | cpp-p4 losses (23) | Their side (p4 games) |
| --- | --- | --- | --- |
| Takes started at a respawn (body at the Ring when it comes back) | 12 % | **24 %** | 24 % |
| First hit after a respawn, median rounds | | **22** | 26 |
| Capture wait, median rounds | | 7 | 7 |

Piece 1 did what it was built to do: we now meet respawns as often as the teams that beat us. The games were still
lost, so routing was never where most of the gap was. Before this deep dive, REPLAYS §6 ranked respawn waiting first;
the ladder says it was real but small.

## 2. Where we lose: the economy chain, the same in both loss sets

| Measure (per game) | Us (p4 / port) | Them (p4 / port) |
| --- | --- | --- |
| Camp gems gained | 398 / 357 | 1,040 / 976 |
| Banked | 264 | 985 |
| Banked ÷ gained | 64 % / 65 % | 92 % / 94 % |
| Gold earned | ≈3.7k | ≈8.3k |
| Gold spent on items | 3,566 / 3,502 | 8,970 / 8,409 |
| Max HP per body, median | 1,500 | 2,900 |
| Deaths | 15.5 | 4.2 |
| Hit back when hit by a champion | 32 % | 65 % |
| Deaths in an isolated 1v1 | 34 % of ours | 5 % of theirs |

The chain is: they earn about 2.2× our gold, so they hold about 2× our HP, so they win the fights, so they take the
kill gold (100 a kill since 3.0) and the gems on the body, so they earn still more. The gap opens around r100–300,
before deaths diverge. The bodies first differ in what they buy, then in how they fight.

- **Builds.** Ours: Power Strength ≈50 shards a game, Durability Health 40, Jungle Strength 14, no Bruiser anywhere
  (`bots/cpp/src/champs.cpp:37-41`). Theirs (p4): Bruiser Health 87, Power Strength 48, Bruiser Strength 42, Bruiser
  Focus 40. Bruiser = 5 shards of the stat + 1 of each other stat, 1.4× stats per gold [sdk]; Power is 1.2×, the
  passive emblems 1.0× + a passive. Heart of Ruin and Marcella stack Bruiser Health and Focus. Between the cpp-port
  games and the cpp-p4 games the ladder moved further toward Bruiser Health.
- **Takes.** r0–150: 5.1 vs 7.2 takes (they take more lone clusters). r300–600: elk 1.0 vs 3.9. r600 on: elk 3.1 vs
  9.1, and 14 vs 27 gems a take. They farm elk because their bodies can tank elk; ours can't.
- **Drafts.** Ours is always Varg / Vesper / Ren / Ryth (/ Vendetta). Theirs: Heart of Ruin 17/23 games and Marcella
  13/23 (p4), 43/57 and 40/57 (port). Our kills of their Heart of Ruin are rare; it and Marcella are the top two
  killers of our bodies, with their Vesper third.
- **Fights.** Vesper is our main victim. We hit back half as often. A third of our deaths are a lone body caught by one
  enemy, which almost never happens to them.

## 3. A bug: no long bank ever finished (fixed 23 Oct)

Two of the 23 losses are pure banking failures: **00road-of-riches 0–1009** (we carried 53 gems a body on average,
max 191) and **01shortcut 0–501** (79 a body, max 483). Locally the same happens: cpp vs cpp-port on 01shortcut as
team A banks 0–184.

Trace (`TRACE 1` copy, 01shortcut): Bank is chosen at a price of 4–10, and 8–13 rounds later the body walks back to a
farm worth 0.1–0.5, with Bank gone from the list. The trace shows `2:0 failed stall` **115 times in one game, and the
bank never finished once.** The cause: `walkf` (`bots/cpp/src/beh.cpp`) measured walk progress as Chebyshev distance
to the target. On a maze the path first leads away from the altar, the straight-line distance doesn't shrink for 8
rounds (`PROG_STALL`), the stall guard fails the bank and excludes the altar for `EXCL` rounds, and the body goes back
to farming with the bag. It hit Farm walks too.

**Fix:** progress is the walk left on the goal's distance field (`NAV.walk_to`), Chebyshev only when the field isn't
cached. On the four long-walk maps vs cpp-p4: 7W/1L, 01shortcut 687–110 as A, 00road-of-riches 1027–0 by r1191.
The full judge is in §5.

A first try, a bank deadline (force Bank once the rounds left ≤ walk + channel + 40, or when the bag wins the game),
changed nothing: the bank still failed by stall. It is not kept.

This is a nav bug, not routing, and it hides on our self-play bar: cpp-port has the same bug, so a game where both
sides fail to bank looks normal.

## 4. Why self-play misled us (the judging lesson)

The kept routing build scored 59.2 % over 22 jitters against cpp-port and lost on the ladder at about the same rate as
cpp-port did. The bar is inbred: same draft, same builds, same fights, same bugs. A change that helps us against a copy
of ourselves (wait at the Ring a little better, choose the altar a little better) is worth a few gems a game. Against a
team with 2× our HP, those few gems don't change a single game. And a bug both sides share (§3) is invisible.

What follows from it:
- The measures that matter are the ladder gaps in §2, read from replays. A jitter win over cpp-port is necessary,
  not enough.
- We need a bar that plays like the ladder. Either unranked games vs real teams (`cambc match-groups create`, after
  `cambc login`), or a sparring bot with the meta draft (Heart of Ruin, Marcella) and Bruiser HP builds.

## 5. Results

| Build | vs cpp-p4, 8 jitters (640 games) | Notes |
| --- | --- | --- |
| walk-progress fix (`_wf` = cpp-p4 + `walkf`) | **358W/282L, 55.9 % ± 1.7, margin +87 ± 15** | **kept** (= `bots/cpp`); runs from 37W to 50W; gems 694 vs 607, deaths 12.4, banks 29.8 a game |
| Bruiser builds (`_br` = cpp + `champs.cpp` builds: main Home, Treasure, Bruiser Health; second Power Str, Bruiser Health; others Bruiser Health, Power Str; alt Bruiser Health / Power Str) | 359W/281L, 56.1 % ± 0.8, margin +97 ± 11 | level with `_wf` on wins; deaths 12.4 → 10.9, their gems 607 → 575. Against a bar that also lacks HP, HP only shows as fewer deaths |

**Against `bots/spar-meta`** (the sparring bar: `_brfk` with the ladder's draft, Heart of Ruin / Vesper / Marcella /
Ryth / Vendetta / Ren, `draft.h` `PICKS`). It kills us more than cpp-p4 does, so it is a better bar for fights,
but it is not stronger: our behaviours likely play Heart of Ruin and Marcella poorly [guess]. 8 jitters each, same sets:

| Build | vs spar-meta | Deaths |
| --- | --- | --- |
| `cpp` (walk fix only) | 356W/284L, 55.6 % ± 0.9, margin +28 ± 17 | 14.5 |
| `_br` (+ Bruiser builds) | 408W/232L, 63.8 % ± 2.3, margin +107 ± 21 | 12.1 |
| `_brfk` (+ Bruiser builds + fight kits for Willow, Tavi, Heart of Ruin in `fkit`) | 419W/221L, 65.5 % ± 1.1, margin +118 ± 12 | 11.5 |
| `_bff` (`_brfk` + the follow-up hit, §8) | **447W/193L, 69.8 % ± 1.8, margin +184 ± 16** | 10.8 (kills 12.7) |

Against a bar with HP, the builds are worth 8 points; the fight kits add about 2 and fewer deaths; the follow-up hit
adds 4 more, +66 margin and 1.6 kills a game.

**`_bff` vs cpp-p4:** 409W/231L, **63.9 % ± 1.5, margin +221 ± 11** (the walk fix alone: 55.9 %, +87); gems 741 vs
520, deaths 9.1, kills 13.9, banks 32.4 a game. **Kept: `bots/cpp` = `_bff` (23 Oct).**

Checked in 12 decoded games of `_bff` vs cpp-p4 (`mvatt.py`, `freehit.py`): our melee bodies now move and
hit in the same round on 15–18 % of their attacks (Ryth 318 of 1,758; cpp-p4's: 1 of 1,817), Vesper walks then hits
with its reset 624 times, and with an enemy champion in reach we hit it 49 % of the time (ladder losses: 40 %; the
ladder teams: 68 %).

## 6. What to build next, in order (each judged on its own)

Done 23 Oct (all in `bots/cpp`, §5): the walk fix (§3); Bruiser builds (Bruiser Health on every body beside Power
Strength, the main's gold passives first, `champs.cpp`); fight kits for Willow, Tavi and Heart of Ruin (`fkit`,
`prices.cpp`; `HOR_DMG_X` is a GUESS); the sparring bar `bots/spar-meta`; the follow-up hit (`follow_hit`,
`main.cpp`). Next, each judged vs **both** cpp-p4 and spar-meta on 8+ jitters:

**Status after the third pass (23 Oct late, §9.4):** item 1 done (safe-only kite, kept); Vesper's hunt phase
deleted (kept, the biggest single gain); crew gold 1.0 kept; item 2 tried twice, lost both times (`_md`, `_md2k`): with our behaviours the draft is not the gap; item 3 came with the Vesper fix (no piece
needed). The new order: (a) spar-meta gets the farming Vesper and `cpp` is re-judged against it; (b) the teleport
shortcut (§9.4); (c) the crew's early shop (§9.2 items 3–4; crew gold is in); then item 4 and item 5 below.

1. **Ranged hits** (§8): with an enemy champion in reach our Vesper still walks instead of hitting 1,036 times in 12
   games. Is it kiting on purpose (a Heal / Fall walk) or a Farm / Bank walk that ignores the enemy? Trace it first.
2. **The draft**: Heart of Ruin and Marcella, the ladder's top two. Judge by swapping our draft for spar-meta's on the
   same build (U2). spar-meta loses to us, so this is open.
3. **Elk farming**, now that the bodies carry Bruiser HP (U1; the need / clear model with the new HP).
4. **Death time** (§8: 13 % of our body-rounds vs their 4 %): no lone bodies near enemies.
5. **Bank legs** (§8): detour 8 vs 1 tile, bag 15 vs 22; smaller than the fight gap.

## 7. Reinforcement learning (asked by the user)

Not now:
- **Too few games.** A local run plays about 100 games a minute, so a week gives a few hundred thousand: far too few
  to train a policy over a 2,000-round game.
- **No room to run it.** The policy has to fit 100k fuel a turn.
- **The rules.** Weights baked into the source come close to "no generated binaries" (`docs/GETTING_STARTED.md`).
- **Time.** The finals are on 18 Nov.

The gap in §2 is plain economics and builds, which hand-written rules copy faster. Tuning a few constants by search
(the jitter harness already does it, slowly) is the only learning that pays here.

## 8. Where the time and the hits go (the second pass, 23 Oct)

**Time use, r150–600, share of body-rounds** (`timeuse.py`: take = within reach of a live camp of a group or
on its spawn tile; walk = moving otherwise):

| | take | walk | still | dead/spawn | tribute |
| --- | --- | --- | --- | --- | --- |
| Us (ladder losses) | 28 % | 53 % | 13 % | 5 % | 0.9 % |
| Them | 44 % | 39 % | 12 % | 2.6 % | 1.9 % |
| Both of our builds, local (`_wf` vs cpp-p4) | ~35 % | ~47 % | | | |

**Legs between takes** (`tools/replay/farm/legs.py`, ladder losses): our legs are direct 57 %, recall 24 %, bank 5 %,
dead 10 % (mean 206 rounds dead per body); theirs bank 10 %, dead 3 %. Bank bag median 15 vs 22 (≥30 gems: 16 % vs
30 %); bank detour median 8 tiles vs 1; altar → next group walk median 10 vs 4. We bank small bags often, far off
the route, and we are dead three times as long.

**Hits.** Rounds where an enemy champion stood within our attack range (`freehit.py`), and what the body did:

| | hit the champion | moved instead | nothing | cast only |
| --- | --- | --- | --- | --- |
| Us (3,068 rounds) | 40 % | 38 % | 12 % | 8 % |
| Them (3,074 rounds) | 68 % | 21 % | 5 % | 2 % |

The mechanic behind most of it: **melee bodies may move and attack in the same turn**; only ranged champions share one
allowance between them [rules, GameRules "Each turn…"]. Their melee bodies move and hit in the same round on 25–30 %
of their attacks (Ryth 840 of 2,990, Vendetta 706 of 1,659, Heart of Ruin 1,363 of 4,473); ours almost never do
(Ryth 1 of 2,449, Varg 1 of 3,416). Their Vesper moves and then hits with its attack reset (513). Our behaviours
attack only from where the turn started: a body that steps into reach waits a round, and a fleeing enemy is never hit
by a chasing melee body. This is the plainest form of "we lose the fights".

**Built: the follow-up hit** (`follow_hit`, `bots/cpp/src/main.cpp`, after the behaviour's move). If the body moved and
can still attack, it hits an enemy champion now in reach: the Kill target first, then the lowest HP. Otherwise it
hits a damaged camp of the group it farms, and it never wakes a fresh one, so a take can still wait for its crew. A
ranged body that spent its allowance on the walk uses its attack reset instead. Results are in §5.

**Time dead.** Our dead legs add up to about 13 % of our body-rounds in the ladder losses (137 legs × 206 rounds in 23
games); theirs are about 4 %. Their legs are no shorter than ours: they make 55 % more of them (2,139 vs 1,377),
mostly because they are alive more (a take lasts the same, median ~15 rounds). So most of the walking gap is the fight gap.

## 9. cpp-p5 on the ladder (23 Oct, third pass)

`submissions/cpp-p5.zip` (= §5's `_bff`) lost 19 games, most of them to top teams, in `replays_from_others/cpp-p5`.
They were decoded the same way and measured with the same scripts (`hpdeath`, `deaths`, `fights`, `goldsrc`,
`freehit`, `mvatt`, `noback`, `timeuse`, `takes`, `legs`). Team 0 is us; per loss unless a line says otherwise;
cpp-p4's 23 losses in brackets. All [measured].

### 9.1 What moved

| Measure | Us p5 (p4) | Them p5 (p4) |
| --- | --- | --- |
| Max HP per body, median r300 / r600 / r1000 | 1,150 / 1,500 / 1,900 (1,000 / 1,100 / 1,500) | 1,200 / 1,500 / 1,850 |
| Deaths a game | 14.2 (15.5) | 7.0 (4.2) |
| Dead, share of body-rounds | 13.9 % (16.2 %) | 6.5 % |
| Banked a game | 349 (264) | 994 (985) |
| Gold earned a game; by r300 | 4,045 (3,722); 821 | 10,532 (8,273); 1,591 |
| Hit an enemy champion in reach (`freehit`) | 43 % (40 %) | 62 % |
| Melee move + attack, share of melee attacks | 9–17 % (~0) | 25–30 % |
| Fights of 3+ hits (`fights`): kills | 63 | 201 |
| Fights: we hit first | 50 % (28 %) | |

**HP is closed.** The Bruiser builds put our bodies level with theirs at every round. The follow-up hit shows up (melee
move + attack from 0 to 9–17 %), and we start half the fights. Deaths fell a little and banking rose a little.
**Gold is not closed:** they still earn 2.6× ours, and the gap has opened by r300 (821 vs 1,591).

### 9.2 Where we still lose

**1. Our Vesper hunts alone and dies.** It dies 5.9 times a game (theirs 1.3), 112 of our 270 deaths, and only 9 of
those before r300. Its deaths: 66 % alone (no ally within 5 tiles), farming just before in 5 %, hit back 85 %.
It loses the fight it picked, against their Vendetta (28), Vesper (23) and Heart of Ruin (23). Theirs dies to camps
while farming (11 of 25, 64 % farming). Their Vesper has *less* HP than ours at r300 (1,000 vs 1,500), so this is
behaviour, not HP. The cause is our Vesper's hunt phase (`champs.cpp` `apply_phase`: from 15 shards farm 0.4, kill
2.5, hunt 20, patrol; R9 user plan 15 Oct). Share of live rounds hitting camps / champions (`hitshare.py`):

| | r0–300 | r300–700 | r700+ |
| --- | --- | --- | --- |
| Our Vesper | 14 % / 3 % | **4 % / 6 %** | 2 % / 6 % |
| Their Vesper | 24 % / 3 % | 16 % / 2 % | 9 % / 2 % |
| Our other bodies | 13–16 % | 9–15 % | 9–10 % |
| Their other bodies | 20–25 % | 13–23 % | 7–13 % |

Their Vesper earned 64k gold over the 19 games, ours 24k. Their Vesper took an elk 121 times, ours 8.

**2. Elk is farmed by bodies that farm, not by bodies with more damage.** Damage per basic attack on camps
(`campdmg.py`: camp HP drop in rounds with exactly one hit on that camp), median:

| | r0–300 | r300–600 | r600–1000 | r1000+ |
| --- | --- | --- | --- | --- |
| Us, all | 55 | 70 | 105 | 130 |
| Them, all | 55 | 70 | 95 | 105 |
| Vesper us / them | 85 / 65 | 105 / 105 | 160 / 155 | 240 / 250 |

Our hits are as strong as theirs. Elk takes at r300+: 4.5 a game vs 16.3. Our Vesper hits camps 84 times at
r300–600 to their Vesper's 449. U1 is answered: the HP was there; the bodies were not.

**3. Crew bodies don't take gold.** r0–150 takes 4.4 vs 7.5 a game; lone gold clusters (120 HP, 40 gold) 23 vs 57;
solo takes 28 vs 55. Our crew prices gold at `ROLE_GOLD` 0.05 (`champs.h`), so to Varg / Ryth / Vendetta a 40-gold
cluster is worth one gem. Every ladder body earns gold: their Vendetta 39k over the 19 games (ours 5.6k), Heart of
Ruin 32k, Marcella 28k. Their Vendetta carries 1,500 HP at r300, ours 1,000, and their Vendetta is the top killer of
our bodies (74 of 270). Time use r0–150: take 37 % vs 48 %, walk 48 % vs 40 %.

**4. Builds.** Their first three shard families (p4 + p5 losses): Vesper Treasure Str → Bruiser Str → Durability HP;
Ryth Treasure Str → Power Str → Durability HP; Vendetta / Cassi / Issac Jungle Str → Treasure Str → Durability HP;
Marcella Treasure Str → Bruiser Str → Power Focus; Heart of Ruin Treasure Focus → Power Focus → Durability HP. Treasure
(+20 % gold) comes first on nearly every body, by r25–r200. Ours: main Home → Treasure → Bruiser HP; others Bruiser HP
/ Power Str; no Jungle, no Durability, no Bruiser Str. Both sides buy an altar lock early; they also buy teleport
crystals.

**5. Fights we start, they finish.** Killers of our bodies: Vendetta 74, Heart of Ruin 55, Vesper 50, Marcella 25.
106 of our 270 deaths came outnumbered (enemies within 5 > allies + 1), 19 of their 133. 152 of ours had no ally within
5 tiles.

### 9.3 The Vesper trace (LADDER_P4 §6 item 1)

A copy with a `V|` printf trace on every Vesper turn with an enemy champion in attack range (`bots/_vtrace`, 6 maps ×
2 sides vs spar-meta, a one-off scratch copy, deleted), joined with the replay. Before: hit 56 %, moved 26 %, nothing 8 %. The moves
were Heal walking away through `safe_recall` (294 turns, often at HP ≥ 0.5), Farm standing at a capture or a respawn
with its attack unused (144, full HP), and Kill walking to an out-of-reach target past an enemy already in reach
(126). Their Vesper also moves on 37 % of its in-range rounds (ours 35 %), but ours stands in reach twice as often
(2,334 vs 1,043 rounds), so the shot lost per round counts twice.

Built in `bots/cpp`:
- `follow_hit` (`main.cpp`) also fires when the body stood still with its attack unused: an enemy champion in reach is
  hit (Kill target first, then the lowest HP).
- `kite_shot` (`beh.cpp`, in `safe_recall` and `fall`): a ranged body shoots instead of stepping away when no enemy can
  hit it this round if it stands. Reach = a melee enemy's move + range (2), a ranged enemy's range, +2 with its dash
  ready. (First built as "safe *or* the step is futile": it lost, §9.4.)
- `kill_fight`: a ranged body walking to an out-of-reach target shoots the enemy already in reach.

Local: in-range turns hit 56 → 90 %, moved 26 → 3 % (the first, safe-or-futile form).

### 9.4 Results of the third pass (23 Oct)

Each against **both** bars, 8 jitters (640 games) each, same jitter sets. [measured]

| Build | vs cpp-p4 | vs spar-meta | Verdict |
| --- | --- | --- | --- |
| `cpp` = p5 (`_bff`, §5) | 63.9 %, +221, deaths 9.1 | 69.8 %, +184, 10.8 | the base |
| + ranged hits, safe-or-futile kite (§9.3) | 66.1 %, +219, 11.0 | 69.7 %, +208, 12.6 | kept for one step |
| + ranged hits, safe-only kite (`_v2`) | 76.1 % ± 1.7, +297, 7.8 | 76.4 % ± 1.4, +268, 9.1 | better than the futile form: shooting while in reach costs 2 deaths a game |
| + meta draft, Str builds (`_md`: spar-meta's `PICKS`) | 57.8 % | 59.4 % | lost: Heart of Ruin and Marcella on our Str builds play worse than our draft |
| **+ Vesper farms all game** (`_vf`: hunt phase, patrol and `Beh::Hunt` deleted, §9.2 item 1) | **80.3 % ± 1.2, +325, 7.3** | **79.2 % ± 1.3, +308, 8.7** | **kept** |
| **`_vf` + safe-only kite** (`_k`) | **83.8 % ± 1.7, +382 ± 12, 5.0** | **85.5 % ± 0.8, +377 ± 10, 6.0** | **kept** |
| `_k` + meta draft, Focus builds (`_md2k`: Heart of Ruin Treasure Focus → Power Focus → Durability HP, Marcella Treasure Str → Bruiser Str → Power Focus) | 75.0 % ± 1.6, +286, 5.7 | 84.7 % ± 2.1, +308, 6.2 | lost (−9 points vs cpp-p4): the meta draft is not our gap with our behaviours (diff: `docs/redo/patches/LADDER_P4_meta_draft_focus.diff`) |
| `_k` + crew gold (`_gck`: `ROLE_GOLD` crew 0.05 → 1.0, §9.2 item 3) | **85.8 % ± 1.0, +418 ± 13, 4.8** | **87.0 % ± 2.5, +395 ± 19, 5.5** | **kept: `bots/cpp` = `_gck`** (a small edge, ~1 SE, but ahead on both bars and on margin) |
| `_k` + the ladder's builds (`_blk`: main Treasure Str → Bruiser Str → Durability HP; second Treasure Str → Bruiser HP → Durability HP; crew Jungle Str → Durability HP → Bruiser HP; §9.2 item 4) | 81.4 % ± 1.0, +358, 5.3 | 84.1 % ± 1.6, +371, 5.8 | lost to `_k` on both bars: copying their families onto our behaviours does not pay (diff: `docs/redo/patches/LADDER_P4_ladder_builds.diff`) |

**p6 vs p5 head to head** (`cpp` vs an unzip of `submissions/cpp-p5.zip`, 8 jitters): **475W/165L, 74.2 % ± 1.4,
margin +245 ± 13**, deaths 6.3. [measured]

**What this pass taught.**
- **The biggest lever was a behaviour, not a number.** Deleting Vesper's hunt phase (R9's user plan of 15 Oct)
  and the safe-only kite together took us from 64–70 % to 84–86 % and halved deaths (9.1 → 5.0 vs cpp-p4).
- **Elk farming came for free (§6 item 3).** With Vesper farming, the new bot takes 22.2 elk a game after r300 vs
  spar-meta (148 of them solo, max HP median 2,950, a body loses 14 % HP on a take; `elk.py`); spar-meta takes 13.2.
  On the ladder, p5 took 4.5 and the top teams 16.3. No separate elk piece is needed: U1 is answered (the HP was
  there; the bodies weren't).
- **Gold.** Against spar-meta, locally, the new bot earns 10.9k a game to spar-meta's 6.8k. Vesper earns 100.8k over
  16 games, Varg 26.5k, Ren 25.2k, Ryth 12k, Vendetta 9.9k. The crew still earns little (item 3 above).
- **spar-meta still hunts with its Vesper** (6.3 deaths a game), so it is now weaker than the ladder's. Next session:
  give spar-meta the farming Vesper (allowed: it may be edited to play more like the ladder, `bots/README.md`), and
  re-judge against it.

**Read from the p5 ladder losses, not built yet.**
- **Shop** (`shop.py`): by r1000 the two sides spend about the same (median 520 a body vs 555); their gold lead comes
  late. Their Vendetta makes its first buy at r70 and has spent 150 by r300; ours waits until r330 and has spent 0 by
  r300. They buy 2.6 teleport crystals and 4.5 altar locks a game; we buy 4.1 locks and no crystals.
- **Teleports**: 42 by them in 19 games, all on 00swirl, 00pilgrimage and 01islands. The walk between the two ends has
  a median of 26 tiles (up to 106; 2 could not be walked at all), and the same shortcuts repeat. A crystal costs 10
  gold; the channel lasts 3 turns, then the body jumps up to 3 tiles ignoring terrain; only a stun cancels it [sdk]. The
  design for next session: in `Nav::step`, while carrying a crystal with no enemy in sight, scan the 7×7 tiles around
  the body for a free landing tile outside `camp_hit` whose walk to the goal + 3 beats ours by a margin, then use the
  crystal; buy one on spawn when none is carried; skip moves while channelling. The derivation is runtime-only (goal
  field lookups), so it carries to unseen maps.
- **Recall cancels**: we cancelled 104 recalls in 19 games (median 1 round after starting, 80 with no enemy within 5,
  often at low HP), from `safe_recall`'s uhit and camp/enemy cancels (`beh.cpp`). Locally both sides cancel ~8.5 a
  game. Small; not chased.

## 10. cpp-p6 on the ladder (24 Oct, fourth pass)

`submissions/cpp-p6.zip` (§9.4's `_gck`) lost 38 games in `replays_from_others/cpp-p6`, most to top teams. They were
decoded and flipped the same way and measured with §9's scripts. They are set against p5's 19 losses, re-measured
from the same decodes. Team 0 is us; per loss unless a line says otherwise. All [measured].
New scripts in `tools/replay/farm/`: `bagrisk.py` (carried at the end, death rate by bag), `stuck.py` (bodies held on
one spot), `stall.py` (capture droughts), `tele.py` (teleports and the walk they save).

### 10.1 What moved (p5 → p6)

| Measure | Us p5 → p6 | Them p5 → p6 |
| --- | --- | --- |
| Vesper deaths a game | **5.9 → 2.6** | 1.3 → 0.7 |
| Deaths a game | 14.2 → 12.1 | 7.0 → 8.2 |
| Dead, share of body-rounds | 13.9 → 10.7 % | 6.5 → 7.0 % |
| Gold earned a game | **4,045 → 5,828** | 10,532 → 8,182 |
| Gold ratio (them ÷ us) | 2.6 → **1.4** | |
| Vesper gold a game | 1,250 → 3,115 | their Vesper 3,310 |
| Crew gold a game, p6 | Ren 930, Varg 870, Ryth 650, Vendetta 350 | Marcella 2,030, Vendetta 1,760, Heart of Ruin 1,470, Ryth 1,360 |
| Banked a game | 349 → 360 | 994 → 932 |
| Elk takes r300+ a game | 4.5 → 7.2 | 16.3 → 15.8 |
| Hit an enemy champion in reach | 43 → 48 % | 62 → 64 % |
| Their deaths to our Vesper | 57 of 133 | 181 of 313 |
| Fights we start: kills us / them | 48 / 78 | 137 / 99 |
| Fights they start: kills us / them | 15 / 123 | 58 / 226 |

- **Vesper's deaths closed** (5.9 → 2.6; 42 % alone, was 66 %), and it is now our killer: 181 of their 313 deaths. Its
  gold matches theirs.
- **Gold mostly closed** (2.6× → 1.4×). The rest is the crew: theirs earns 1.5–6× ours.
- **The crew dies more.** Ren 1.7 → 2.3, Vendetta 1.3 → 2.2 a game: crew gold 1.0 sends it after lone gold clusters.
  Half our deaths come with no ally within 5 tiles; 201 of 458 outnumbered. We win the fights we start (137 kills to
  99) and lose the ones they start (58 to 226).
- **Gems did not move.** Banked 360 vs their 932. The 38 losses fall into five kinds:

| Kind | Losses | What happens |
| --- | --- | --- |
| Hoard | 8 | We end holding 100+ gems: 01the-farm 25–1012 **holding 980**; 00corners 956–1012 holding 108 (both would have won if banked); 01shortcut 70–1028 holding 505; 00great-wall 476–1027 holding 453 |
| Economy | 14 | Slower takes and banks, no single fault |
| Small-map fights | 6 | 01hooks, 00packs, 00reverse-spiral, 01elk-arena, 00eight, 01starfish: dead 27–41 % of body-rounds, 0–162 banked |
| Gem-gated | 6 | 00contest ×2, 00stampede ×2, 00pilgrimage ×2: they take the big group, we don't (contest 0–800 captured, stampede 0–1,920) |
| 01islands | 4 | We bank 30–684; on 17af3f42 our team stood near spawn from r100 to r825 (30–1030, no deaths) |

### 10.2 Where we still lose

**1. The hoard (new in p6).** Our Vesper carried 980 gems at the end of 01the-farm. The loop is in the replay and in a
local trace (`TRACE 1`, 01the-farm as B vs spar-meta: it banked 111 at r308, then nothing until 907 at r1435):
capture → recall to shop (Shop prices 9–38 with gold) → walk out → capture → recall. Bank never won:
- **The Bank price is a rate**: bag × (1 + P) / (walk × 2 + bag / 10). The channel grows with the bag, so the price
  can never exceed ~11 a round, whatever the bag.
- **The main's farm price counts gold at 3×** (`prof.gold` 3.0), so the nearby groups score 5–17.
- **Nothing prices the bag's risk when no enemy is in sight** (`P = 0`).
- At bag 235 and walk 26, Bank scored 3.4.
- **What a carried gem costs** (`bagrisk.py`): our death rate per live body-round is about 2 per 1,000 at every bag
  size (0.0 at 400+, where the Vesper hid near spawn). So the bag is rarely lost to a death. It is lost when the game
  ends. 8 of 38 p6 losses ended with 100+ in our bags; 1 of 19 p5 losses did. p5's Vesper banked because it hunted.

**2. Stuck bodies.** 11 stands of 40+ rounds on one spot (1,724 body-rounds; p5: 2). The worst: on 01shortcut, Ren
stood at 120 HP (10 %) in a corner for 884 rounds holding 47 gems, never recalling. `safe_recall` (`beh.cpp`) steps
away from any live camp in range before it recalls, asleep or awake. A sleeping 4-elk group was 4 tiles away; no step
got farther (the corner), so the step was Blocked and the recall never started. Only an awake camp hits [rules].

**3. 00pilgrimage: the teleport.** Their bodies teleported 23 times in the game you sent (d28e4f90 = "c2d5"), every
time from (39,27) to (35,31) or (33,33): **each jump saves a 112-tile walk** across the hole river to the centre
lane (`tele.py`). Our team spent r0–300 walking the west strip between gold clusters (banked 0 by r300), and our
Vesper recalled to spawn twice holding 30 and 60 gems and walked back out without banking. The north altar is 13
tiles from spawn as the crow flies, but it is across the river. In the other p6 losses, teleports were seen only on
00pilgrimage (29). In p5's: 00swirl (19–26 tiles saved), 00pilgrimage (94–106) and 01islands (unwalkable).

**4. 01islands: the crew idles.** The winners took **all** their gems (1,030 on 17af3f42) from groups we can walk to
(the outer ring), our side's included. Of 46 groups our map dump can walk to 8; the elk groups among them need 5
bodies. In a local trace the crew sits in Fall (no farm price above 0): `need_k` prices the 5-body elk groups at 0
for a crew of 3, and the Vesper holds the other one alone.

**5. Draft (asked by the user).** Their picks in the 38 losses: Heart of Ruin 28, Vendetta 27, Vesper 26, Ryth 23,
Marcella 23, Tavi 11, Ren 10, **Varg 9**. Varg is rotating out and Marcella is in. Marcella killed 60 of our bodies (22
of our Vesper's 98 deaths); our Varg earns 870 gold a game and hits camps for 40–115.

**6. The crew's shop.** First buy: Varg r368, Vendetta r334, Ryth r263; theirs r107–r136. Unchanged from p5.

### 10.3 Results of the fourth pass (24 Oct)

**The bars changed** (user, 24 Oct): `bots/cpp-p6` (frozen = `submissions/cpp-p6.zip`, the ladder entry) replaces
cpp-p4. spar-meta's Vesper now farms all game (`champs.cpp` `apply_phase`, as the ladder's does): `cpp` scores **75.5 %
± 2.8, margin +260** against it (87.0 % against the hunting one), so U5 is answered: the bar got harder. Against
cpp-p6, `cpp` is 50 % by construction. Each piece below: 8 jitters per bar, the same J set. [measured]

| Build | vs spar-meta | vs cpp-p6 | Verdict |
| --- | --- | --- | --- |
| `cpp` (= p6) | 75.5 % ± 2.8, +260, deaths 5.4 | 50 % | the base |
| `_bk` bank by order size (B* = ρ√(2D/h), h 0.004) + end-aware | 73.1 %, +216 | (vs cpp-p4 83.3 %, cpp 85.8 %) | lost: banks every ~15 gems (38 banks a game vs 30), farm time lost |
| `_bkh` the same, h 0.001 (bags 2×) | 73.4 %, +182 | 45.3 %, −23 | lost |
| `_bke` end-aware only (bank when the bag wins, or the game may end first) | 78.9 %, +285 | 48.4 %, −16 | level |
| `_bke2` `_bke`, bags 30+ only | 78.3 %, +281 | 48.6 %, −15 | level |
| `_bkw` bank when the bag wins the game (score + bag ≥ 1,000) | 78.4 %, +283 | 49.1 %, −4 | level |
| `_rc` safe_recall fears awake camps only (§10.2 item 2) | 74.5 %, +265 | **51.2 %, +8** | **kept** |
| `_cs` crew recalls to shop at 2 shards (`CREW_SHOP_SHARDS`) | 78.1 %, +278, deaths 4.9 | 47.2 %, −9 | level |
| `_mv` Varg → Marcella (`PICKS` 6, 1, 8, 0, 2, 9) | 65.8 %, +166 | **35.3 %, −155** | lost (`docs/CHAMPIONS.md` "Swapping a champion") |
| `_k1` = `_rc` + `_cs` | 78.0 %, +281 | 47.3 %, −33 | |
| `_k2` = `_rc` + `_cs` + `_bkw` | **79.2 % ± 1.0, +275**, deaths 5.0 | 48.8 %, −20 | not kept (user: a piece must beat p6) |
| null: `cpp` on 8 fresh jitters (200 … 2200) | 73.4 % ± 1.7, +236 | | `cpp`'s level vs spar-meta is ~74.5 %, +248 over both sets |
| **`_ih` = `_rc` + a hurt body with nothing to take heals** (§10.4) | **81.4 % ± 1.0, +318**, deaths 5.0 | **53.0 % ± 0.9, +39 ± 10** | kept |
| `_ih`, `HEAL_NOENEMY_HP` 0.5 → 0.4 | 77.8 %, +258 | 51.9 %, +44 | lost to 0.5 |
| `_ih`, `HEAL_NOENEMY_HP` 0.5 → 0.65 | 81.6 % ± 1.4, +299, deaths 4.4 | 57.7 % ± 2.0, +78 ± 20 | kept for one step |
| **`_ih`, `HEAL_NOENEMY_HP` 0.5 → 0.8** | **82.3 % ± 1.5, +326**, deaths 4.2 | **57.8 % ± 1.2, +71 ± 16** | **kept: `bots/cpp` = p6 + `_rc` + `_ih` at 0.8 = `submissions/cpp-p7.zip`** (a plateau with 0.65 vs p6; fewer deaths, better vs spar-meta) |

The bank, crew-shop and draft pieces are in `docs/redo/patches/LADDER_P4_{bank_eoq,bank_win,crew_shop,marcella}.diff`.

### 10.4 The idle crew (01islands), found by trace

`TRACE 1` games of `cpp` vs cpp-p6 on 8 maps, share of `tick` lines whose goal is Fall (nothing priced above 0):
01islands 23 % (crew bodies 16–39 %), 01elk-arena 8 %, the other six 0–5 %. The idle bodies stood at 51–58 % HP:
- too hurt for `need_k` to price any take (it needs HP above `KEEP_HP` after the clear, so 0 = no take);
- above `HEAL_NOENEMY_HP` (0.5), so Heal was priced 0 with no enemy in sight;
- HP only comes back at spawn, so they waited for good.

**Rule** (`price_all`, the no-enemy heal branch): the heal price is zeroed above `HEAL_NOENEMY_HP` only while some take
is priced (`rawb > 0`); a hurt body with nothing to take goes home. On 01islands vs cpp-p6 it won as B 1040–30 by r1247
(`cpp` 1018–268 by r1660) and lost as A 984–1016 (`cpp` 748–1016).

**01elk-arena, side A** (not built): both teams seed all 5 bodies on the centre group (2 elks, 72 gems, 7 tiles from
each spawn) at r1. In the mirror side A loses it every time (Ren dies at r17, Vesper at r28; 9 deaths to camps, all
with no enemy in sight, mostly in Heal), and the game goes to side B by ~800. The ladder loss there was 36–1008 with
35 deaths. A contested-opening rule is its own design.

**The teleport (§10.2 item 3), built and parked.** A takeoff planner in `Nav::step`
(`docs/redo/patches/LADDER_P4_tp_planner_patch.py`): it scans tiles along walls and holes (over several turns, under a
fuel reserve) for the takeoff T minimising walk(me, T) + 4 + walk(landing, goal), walks there on a new `NavKey::Tile`
field, and jumps; one crystal is bought first on a spawn visit. On 00pilgrimage it finds takeoffs (walk 61 → 32 via
(9,49) → (12,52)). But no goal ever ran through the big shortcut (the centre lane, 112 tiles around): the farm prices
read the walk without the jump, so the centre groups are never chosen. To pay off, the plan's cost must feed the walk
estimates in `price_all` (gd' = min(walk, plan)). U4 stays open.

## 11. p8: playing like the top teams (24 Oct, fifth pass)

The plan was `docs/archive/COPY_PLAN.md`, items 1–6, from the side study of three top teams' 78 wins
(`docs/archive/TOP_TEAMS.md`). No ladder replays were read in this pass: every number is from local arena runs,
8 fuel jitters × 80 games, against the bars `bots/cpp-p7` (frozen = `submissions/cpp-p7.zip`) and `bots/spar-meta`
[measured]. New scripts (README): `kpi.py` (the TOP_TEAMS §11 numbers on decoded games), `arena_kpi.sh` (decode an
arena run two at a time, flip, kpi), `tu.py` (time use from a `TRACE 1` run: the `tu` line in `main.cpp`), `duel1.py`
(even 1v1s from a trace copy).

### 11.1 Measured before building

- **p7 vs spar-meta, 80 games** (`kpi.py`): camp hits 12.4 per 100 live body-rounds (the ladder losses: 9.3; the top
  teams 16–18); champion hits 2.3; **30 banks a game at a median bag of 18** (the ladder losses: 15 at 15); altar locks
  0; Vesper casts 3.8 / 2.2 (reset / dash) per 100 live rounds (top teams' dash 7.3–7.4). Banking frequency is not a
  local gap; the ladder's low count comes with its losses and the hoard games.
- **Where the body-rounds go** (`tu.py`, a TRACE copy vs spar-meta, 80 games): Farm walking **40 %**, attacking camps
  12.5 %, capturing 5.4 %, waiting at a Ring 5.8 %, idle in Farm 2.8 %; Bank walk 7 %; Heal 7.6 % (walk 4.2, recall
  2.2); dead 4.4 %. So camp-hit time is mostly a walking problem. Resets already fire once per ~8 camp hits (every
  cooldown while a body hits); the casts are bounded by hit time, except the dash.
- **`gem_count()` on an ally out of vision throws** "engine error 97: Unit is not in vision" (probe, 01the-farm). The
  win line can count only my bag and the allies I see.
- **The fight gate** (`duel1.py`, a TRACE copy vs cpp-p7): in even 1v1s (one enemy within 6, no ally within 6, me at
  ≥ 80 % HP and ≥ 1.13× its HP), `duel`'s P(lose) had a median of 0.00–0.09. The gate that refused was the reach: a
  dashless melee body priced only an enemy within 2, so Ryth's were Kill candidates 8 % of the time, Varg's 12 %
  (Vendetta 47 %, Ren 41 %, Vesper 100 %).
- **Bodies leaving spawn with a bag** (p7 vs spar-meta): they gained more gems before banking 1,244 times, banked
  first 828 times (median bag 23).

### 11.2 The judging lesson: a head to head needs a null

A jittered copy burns up to 2,500 loop steps a turn, and in C++ that is real fuel: **an exact copy of `cpp` scores
43.1 % ± 1.9, margin −54, head to head against `cpp`** (its J = 0 run is 40W/40L exactly; every jittered run loses).
The 23 Oct calibration (49.8 %) was cpp-port, which used less of its turn. So a head to head against the current
build is read against 43.1 %, not 50 %. Runs against the bars are unaffected (every candidate is jittered the same way
against the same unjittered opponent).

### 11.3 Results

Bars: 8 jitters each. "H2h" = 8 jitters against the current `bots/cpp` (read against the 43.1 % null).

| Build (each on the last kept) | vs cpp-p7 | vs spar-meta | H2h | Verdict |
| --- | --- | --- | --- | --- |
| p7 (= `cpp` at the start) | 50 % | 82.3 %, +326 (§10.3) | | the base |
| **1. dash on every cooldown** (`nav.cpp` L4: bag or not, Safe walks too, held only while an enemy is in sight, never into camp / enemy reach) + the reset after a walk onto a hurt camp (`follow_hit`) | **61.6 % ± 1.6, +114** | **86.6 % ± 1.6, +364**, deaths 4.8 | | **kept** |
| 1, the dash held only within 6 of an enemy | 62.0 %, +82 | 87.0 %, +401 | | level: the simpler rule kept |
| **4. our own altar lock** just before our tribute (`beh.cpp` `place_lock`, within 2) | 60.6 % ± 2.3, +90 | **90.0 % ± 1.6, +425**, lost 96 | | **kept** (level on p7, +3.4 on spar-meta) |
| 3. bank: cap 50 + win line + fold (out of spawn, added walk ≤ 12) | 58.4 %, +68 | 85.6 %, +348 | | lost (on 1, no lock) |
| 3. fold + win line | 54.2 %, +27 | | | lost: the fold costs farm time |
| 3. cap 50 + win line | 60.8 %, +78, lost 120 | 88.4 %, +378 | | level |
| 3. cap + win line + fold (bag ≥ 20, added walk ≤ 6) | 60.9 %, +70 | | | level: the fold adds nothing |
| 3. win line alone | 60.9 %, +81 | 89.2 %, +408 | | level |
| 5. open the fight: an enemy within 6 is a Kill candidate at P(lose) ≤ 0.3, not outnumbered within 8 | 61.2 % ± 3.1, +88, deaths 7.7 | 88.8 %, +404 | | level, deaths +1.3: not kept |
| 5. the same, ≥ 1.13× the target's HP and ≥ 80 % HP | 58.4 %, +55 | | | lost |
| 6. Varg → Marcella with her kit (bank 1.3 + 2 gold a gem tributed, Treasure → Jungle Strength → Bruiser, slot 1 opens from 4) | 55.8 %, +53 | 82.7 %, +312, deaths 3.6 | | lost: Varg's splash clears go (gems 793 → 735) |
| 6. Ryth → Marcella (kit as above) | 59.4 %, +90 | | | level |
| 6. Ryth → Heart of Ruin (landing dash on camps every cooldown; travel dashes never land next to a camp) | 62.0 % ± 2.2, +93 | 88.9 %, +404 | 52.8 %, −4 (null +9.7) | a win head to head |
| **6. both: Varg, Vesper, Marcella, Heart of Ruin, Vendetta** (`_mh`, both kits) | **61.6 % ± 2.9, +120** | **88.4 % ± 1.5, +412**, deaths 4.1 | **61.4 % ± 2.4, +129** (null +18) | **kept** |
| `_mh`, Marcella's bank 1.0 / 1.6 | | | 46.2 / 46.4 % (null +3) | level: 1.3 kept |
| `_mh`, Ren in Varg's place | | | 41.4 %, −99 (null −2) | level: Varg kept |
| **3. `_mh` + cap 50 + win line** (`_mb`) | **65.0 % ± 1.6, +147** | **89.8 % ± 1.6, +422**, deaths 4.0, lost 105 | 41.6 %, −84 (null −1.5) | **kept**: better on both bars, level in the mirror |
| `_mh` + win line alone / + cap alone | | | 46.7 % (null +3.6) / 39.5 % (null −3.6) | |
| `_mb`, `BAG_CAP` 35 / 80 | 62.2 %, +114 / 61.6 %, +123 | | | 50 kept |
| **Final = `bots/cpp` = `submissions/cpp-p8.zip`** (the dead fold code removed) | **64.8 % ± 1.4, +144 ± 16** (415W/225L; won all 8 runs, margins +70 to +232) | **90.0 % ± 1.2, +414 ± 22**, deaths 4.1 | | **shipped** |

### 11.4 The study's numbers, p7 → p8 (80 games each, J = 0, `kpi.py`)

| Per 100 live body-rounds, or per game | p7 vs spar-meta | p8 vs spar-meta | p8 vs cpp-p7 | Top teams (TOP_TEAMS §11) |
| --- | --- | --- | --- | --- |
| Camp hits | 12.4 | 12.9 | 12.7 | 16.2–18.3 |
| Vesper casts (reset / dash) | 6.0 (3.8 / 2.2) | **10.2 (4.0 / 6.2)** | 10.3 (4.0 / 6.4) | 12.1–12.7 (dash 7.3–7.4) |
| Vendetta casts (reset / dash) | 8.4 (3.3 / 5.1) | 9.9 (3.0 / 6.9) | 10.2 (3.0 / 7.2) | 10.7–12.7 |
| Heart of Ruin; Marcella | | 12.1; 5.3 | 12.2; 5.2 | |
| Banks a game; median bag | 30.0; 18 | 32.4; 21 | 29.7; 19 | 29–32; 21–26 |
| Altar locks a game | 0 | **4.8** | 4.9 | 3.8–4.2 (team 2: 0) |
| Deaths a game | 3.6 | 3.9 | 6.9 | 4.9–6.7 |
| Games lost holding 100+ | 1 of 14 | 0 of 5 | 3 of 29 (01boss-battle ×2: the gated altar; 01shortcut) | |

- The casts moved most (Vesper's dash ×2.8), and the locks are at the top teams' rate. Camp hits barely moved: the
  dash shortens walks, but the bodies spend the saved rounds on more walks, not on longer takes. The ≥ 15 target is
  not met; the walking share (40 %) is still where it would come from.
- The hoards that remain are 01boss-battle (no altar until a monolith dies, `gate_init`) and 01shortcut (a long bent
  bank walk): the win line can't help where the bank can't be reached.

## Unknowns to check when building

- U1 (answered §9.4): elk takes after r300 lifted once Vesper farmed (22.2 a game locally); the HP was already there.
- U2: is the fight gap HP alone, or HP and target choice? Swapping the draft with our Str builds lost (`_md`, §9.4);
  the Focus-build form is also lost (`_md2k` 75.0 / 84.7 %): with our behaviours the draft is not the gap.
- U4: is a teleport shortcut worth its 3-turn channel off the three maps where the ladder used one? (see U6) [guess: worth it
  only on walls/islands maps; the margin keeps it off elsewhere]
- U5 (answered §10.3): no. With a farming Vesper, spar-meta holds `cpp` (= p6) to 73–76 % (87 % before).
- U6: does a teleport pay once the farm prices see the jump (gd' = min(walk, plan))? The planner alone never ran a goal through the 00pilgrimage river (§10.3).
- U7: is 01elk-arena's side-A loss turn order in a contested r1 opening, and does skipping a contested seed help? [guess]
- U3: how many of the ladder's maps have a long or bent altar walk (the §3 bug)? Two of 23 losses showed it plainly.
- U8 (p8): do the ladder's opponents punish the bank cap the way the mirror does (h2h −1.5 against the null) or reward it as
  both bars did? Read cpp-p8's ladder losses with `kpi.py`: banks, median bag, games lost holding 100+.
- U9 (p8): does opening even fights pay against the ladder's teams (it was level locally, deaths +1.3, §11.3)? The top
  teams win the fights they start; ours start where `duel` is near 0, so the price, not the gate, decides.
- U10 (p8): where do the dash's saved rounds go? Camp hits 12.4 → 12.9 only; trace `tu.py` on p8.
- U8–U10 are answered on the ladder in `docs/nav/LADDER_P8.md` §4.5–§4.7 (24 Oct). Its §8 holds the next unknowns.
