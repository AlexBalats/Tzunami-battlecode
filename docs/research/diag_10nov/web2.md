# web2: second web study, aimed at the last 24 hours (10 Nov, agent `web2`)

**Question.** Which public methods (other contests' winners, this season's public team notes) can we copy in one day
for: map-aware play, turn order, underdog play in a bracket, small-fight micro, deposit timing, and what is known
about the qualifier?

**Short answer.**
1. The one finding with a measured gap and a small build is the **double turn across the round boundary**: the top
   teams give one body two turns in a row (no enemy turn between) 5.7-9.0 times a game with hits in both; we do it 0.0
   times [measured here, 40 games a label].
2. **Map-class "experts" did not pay for the teams that tried them on this game** (two teams at ~2,100 and ~1,750
   measured it). What paid were feasibility switches for degenerate map kinds, a draft table by map kind / pick count,
   and size -> tempo. The upsets in MIT qualifiers came from bots that simply kept working on new maps.
3. **The qualifier** [web, third-party tool + one team's report]: double elimination, no bracket reset, top 8 qualify;
   Sprint 3 was single elimination with **15 games per pairing on unseen maps**. At 15 games a 25 % per-game team wins a
   series 1.7 % of the time: variance play does not rescue us, only a higher mean does.
4. On the newest map family (`04*`) we already score share 0.42 / 38 % wins against the band, against 0.33 / 17 % on
   the older families [measured here]. New maps are our better ground.

**Tags.** [web] = the linked source says it ([web-measured] = the source measured it; [web-opinion] = its view).
[measured] = I counted it today. [guess] = my mapping, untested. No other team's code was read: READMEs, notes and
postmortems only. One file (`TWWT-ai .../analysis/ming-study.md`) turned out to be a study of another team's bot
source; it was not read past its first lines and nothing from it is used.

**Known, not repeated** (one line each): the eight levers of `web_levers.md`; local-superiority commit, hold at the
edge, per-move worst case, shared-clock arrival, claims by ETA, summon, decision locks, heal together
(RESEARCH_WINNERS §3); act-first priority while fighting (`prio_fight`: James 87/160 self-play, BestCody's tier table);
lock own altar before tributing (`lockown`, `alt1`; dpark B49 54 % self-play); `altar_lock_at` prefers the allied lock
(BUILD_LOG `_lock`); the pre-recall trick (Mite / Trzy Kwaterki start a recall at 90 % / 76 % of turn ends; James's
copy was neutral 73/140; our pre-recall exists); spawn-tile respawn blocking; primed tribute; one capturer per kill and
same-turn step onto the reward tile (`i_take`, snipe); bigger bank bags (lost for every team that tried: BestCody 40 /
80, dpark 28-42, James 45 / 20).

---

## 0. The qualifier and the platform: what is public

| Fact | Source | Tag |
| --- | --- | --- |
| Sprints are single elimination; **qualifiers and finals are double elimination with no bracket reset**; the top 8 of each qualifier go to the finals; the tool models series of bo5 to bo21 | `secret pantheon tech` README (a tournament predictor by a spring finalist): https://github.com/yufanwang07/secret-pantheon-tech | [web] third party, not the organisers |
| **Sprint 3: single elimination, 713 teams, 15 games per pairing, on unseen maps (not the ladder pool)**, seeded by ladder rank; the entry is a snapshot of the live bot at the lock | dpark2380 `bots/daniel/docs/sprint3-report.md`, `CHANGELOG.md`: https://github.com/dpark2380/cambridge-battlecode | [web-measured] (they played it: bye, 9-6, 1-14) |
| Spring 2026: finals = 16 teams (top 8 international + top 8 UK), double elimination, seeded by Elo | https://luma.com/a1jsj4wq ; Pantheon postmortem (https://github.com/HerbertTheBird/Cambridge-Battlecode) | [web] |
| An upload is used for games as soon as it compiles (~19 s; build queue 3-25 min), before its "active" time | jamesrdainton-jpg `DEVLOG.md` rows 170-171: https://github.com/jamesrdainton-jpg/Cambridge-Battlecode | [web-measured], 4.0 era: re-check before relying on it at the lock |
| `cambc match-groups create TEAM --source-group UUID` plays an opponent's **historical** version | same repo, `research/2026-10-26/PATCH-NOTES-4.0.md` | [web] organiser text: gives a pinned benchmark (EvilMangohh judged on pinned opponent versions, same maps and sides) |
| A patch that breaks compilation marks the bot invalid; 24 h grace before automatic losses | DeySag `docs/cambc2026a/PATCH-NOTES.md`: https://github.com/DeySag/Cambridge-Battlecode | [web] |
| Engine 3.0.0 (cambc 5.0.0) went live 4 Nov 23:00Z; one team's same bot fell 51 -> 39 wins of 80 across the switch, gold per clear 149 -> 130; cause unresolved; no non-numeric 5.0 change found by anyone | dpark2380 `backlog.md` B154 | [web-measured] |

**Series arithmetic [measured: binomial].** P(win a series) at per-game p:

| p | bo1 | bo5 | bo9 | first to 8 of 15 |
| --- | --- | --- | --- | --- |
| 0.25 (us v the band today) | 0.25 | 0.10 | 0.05 | 0.017 |
| 0.30 | 0.30 | 0.16 | 0.10 | 0.05 |
| 0.40 | 0.40 | 0.32 | 0.27 | 0.21 |
| 0.55 (us v a lower seed) | 0.55 | 0.59 | 0.62 | 0.65 |

Unknown: the series length of the UK qualifier and the number of UK entrants. Not found in public.

---

## 1. Ranked levers

| # | Lever | Replaces (our terms) | Evidence | One-day value |
| --- | --- | --- | --- | --- |
| 1 | Double turn across the round boundary (priority by round parity) | `prio_fight` priority rule; bank start timing | [measured] gap 0.0 v 5.7-9.0 a game; [web] probe by another team | **High** |
| 2 | Unseen-map robustness screen + feasibility switches for degenerate map kinds | the judge; draft-time map model | [web-measured] MIT upsets; CAMBC teams; our `04*` numbers | **High** (cheap, tournament-specific) |
| 3 | Map class -> draft table and tempo only; judge classes with shrinkage | draft; opening assignment | [web-measured] 3 CAMBC teams, 3 MIT teams, Steamhammer | **Medium-high** (and a warning) |
| 4 | Tribute turn hygiene: start in the walking turn; 1-tick tributes on our boundary; small bags late | bank rule | [web-measured] EvilMangohh 18 -> 29 of 100 on the platform; dpark | **Medium** |
| 5 | Stance by evidence inside the game (after early losses, raise the engage bar) | engage test | [web-measured, weak] dpark +12 ± 14; our blowouts.md | **Medium** |
| 6 | Judge on P(share > 0.5) = Φ((mean - 0.5) / sd), with pinned opponent versions | band gate | [measured] fits our data; Skinner 2011 | **Medium** (free) |
| 7 | Escort / hold rule for very large bags on contest and monolith maps | bank rule on one map kind | [web-measured] EvilMangohh 12 of 25 stolen | Low-medium |
| 8 | Roster slot count: Cassi & Issac's extra body acts in a run at the end of every round | draft | [measured] order only; results elsewhere are mixed | Hypothesis |

---

## 2. The levers in detail

### L1. The double turn across the round boundary

**Sources.**
- TWWT-ai `analysis/mechanics.md` (probe, engine 2.x) [web-measured]: "The starting team alternates each round", so
  acting second in round r then first in r+1 gives back-to-back turns; a 1-tick tribute (<= 10 gems) started on a round
  where we act second cannot be interrupted. https://github.com/TWWT-ai/Cambridge-Battlecode
- jamesrdainton-jpg `research/2026-10-25/VS-TOP5.md`, `DEVLOG.md` row 170 [web-measured from replays]: all top five
  call `set_priority` every round, three use negative values, and Mite and Trzy Kwaterki change the value every turn
  (the author guessed "a message channel").
- MIT Battlecode 2021, 3 Musketeers (https://battlecode.org/assets/files/postmortem-2021-musketeers.pdf) [web]: "The
  key to this strategy working relied on turn order": two units built back to back act in succession, so the first
  clears the way and the second lands the hit. 2019, Oak's Last Disciple
  (https://battlecode.org/assets/files/postmortem-2019-oak.pdf): "because of how the turn queue worked, your prophet
  gets to attack first"; the "church lightning" of that year was a pure turn-queue attack that surprised the eventual
  winner (smite: "We had given some thought to turn order queues, but never quite figured this out").

**The mechanism on 5.0 [rules + sdk + measured].**
- Turns alternate champion by champion and the starting team swaps each round (mechanics.md §2.5). Team A starts odd
  rounds [measured: two decoded games, rounds 200-205].
- So the team that acts second in round R acts first in R+1: its last body of R and its first body of R+1 act with no
  enemy turn between. `set_priority` applies from the next round [sdk line 4055], so a body that sets LOW for rounds
  where we go second and HIGH for rounds where we start is that last and that first body: **two full turns in a row,
  every second round**. The price: the enemy then has two rounds of turns before that body acts again.
- A side effect seen in the trace [measured]: a team with more bodies (Cassi & Issac = 2 bodies on 1 pick) takes all its
  extra turns in a run at the end of every round (L8).

**Top v us [measured, `~/tzunami_data/analysis_10nov/web2/dbl.py`, first 40 games of each label; a "boundary" = the
last step of round R and the first step of R+1 belong to one team].**

| Label, side | Same body on both sides of its team's boundary | Double strikes a game (that body hits a champion or casts damage / stun in both turns) | Two different bodies both hit across the boundary, a game |
| --- | --- | --- | --- |
| n47_tz116, us | 0.0 % | **0.0** | 28.9 |
| n47_tz116, the band | 1.5 % | 0.15 | 7.8 |
| top_v_band, the top | 5.2 % | **5.7** | 31.6 |
| top5_9nov, focus team | 7.7 % | **9.0** | 30.8 |
| top5_9nov, opponent | 3.0 % | 2.1 | 26.7 |

Caveat: bodies that take no step in a turn are invisible to this count, and I have not yet tied double strikes to
kills. The priority value itself is not in the decode (only that step kind 9 happened).

**What a double turn buys [rules, guess on size].**
- Melee: hit, then hit again (or stun, then burst) before the victim can flee, recall, shield or finish a tribute.
- Ranged (move OR attack per turn): shoot, then step out; or step in, then shoot: the missing half of a ranged turn.
- Dash in at the end of R, full turn at the start of R+1: the victim sees nothing between.
- Bank: a <= 10 gem tribute started as our last actor completes at our next turn start with no enemy turn between: no
  stun, kill or lock can stop it. Any tribute loses one enemy window.
- Defence: the enemy's window is the other parity. On rounds where they hold the boundary, a body at low HP should be
  outside their two-turn reach (move + dash + range, twice), not their one-turn reach.

**Measure before building.** Extend `dbl.py`: kills that land in the second turn of a double, by team; share of our
deaths that fall inside an enemy double; how often our tributes <= 10 gems are cancelled.

**Build sketch (switch `dblx`, bits).**
1. `we_start(r)`: from our team id and round parity (assert it against `has_completed_turn` of a visible enemy once).
2. Bit 1, striker: the body with a fight target whose live HP <= two turns of its damage (or a stun ready + burst) sets
   `set_priority(we_start(r+1) ? +200 : -200)`; every other body keeps the `prio_fight` value shifted inside (-100, 100).
3. Bit 2: when I am my team's last actor this round and we start the next, open (step or dash into reach, stun) now.
4. Bit 4, bank: a carrier next to an altar with <= 10 gems and an enemy within 6 delays the start to our boundary turn.
5. Bit 8, defence: on enemy-boundary rounds the flee test uses their two-turn reach.
6. Only one body can hold the double: choose it by (kill within two turns) > (stun ready) > (carrier under threat);
   post the choice in a comms bit so two bodies do not both go low.
Local judging will under-read it against a tz opponent that does not flee or cast between turns [guess]; hand it over
with the KPI (double strikes a game, kills inside doubles).

### L2. Robustness on unseen maps: where qualifier upsets came from

**Sources.**
- MIT 2023, "Don't @ Me" (7th; https://battlecode.org/assets/files/postmortem-2023-dont-at-me.pdf) [web]: seeded 25th,
  they beat the 8th seed in Sprint 1 because "a lot of teams had hardcoded values according to the three original game
  maps ... our more generalized code ... meant that our bot could compete and even beat upper level teams". In the
  qualifier the 1st seed lost to the 16th. The organisers built island-heavy qualifier maps to push against the ladder's
  rush meta.
- MIT 2020, The High Ground (https://battlecode.org/assets/files/postmortem-2020-the-high-ground.pdf) [web]: "the devs
  indirectly nerfed rush through large and hard-to-path maps in the seeding tournament. Some very strong rush teams
  were knocked out pretty early."
- CAMBC 2026a, EvilMangohh (peak rank 22; https://github.com/toyeshhm/cambridge-battlecode-2026) [web-measured]: a map
  generator made 30 fair unseen maps to check gains; a gate of "win all 70 v the starter with zero faults" once caught
  a build that banked nothing in 2,000 rounds; "many late wins came from maps where a general rule broke" (altar ringed
  by camps, altar sealed by monoliths, contest maps, stalls).
- dpark2380 [web-measured]: on the 42 new `04*` maps they scored 30-43 % ranked against 55-70 % on every other family
  until they fixed map-kind rules (gem-less groups' gold capped; island groups reached by teleport crystal 48/72 on 4
  maps; sealed spawn 18/18; ringed elk / golem groups worked from outside 59 % on 8 maps).
- jamesrdainton-jpg [web-measured]: "gold mode" on maps whose altar is sealed behind a boss, 19/24.

**Ours [measured, n47_tz116 + tzmega_big + tz174_big, 450 band games; the three builds share maps, so the effective n
is about a third].** Family 00: share 0.33, wins 19 % (102 games); 01: 0.31, 17 % (72); 02: 0.33, 14 % (51); 03: 0.33,
17 % (60); **04: 0.42, 38 % (141)**; other names: 0.25, 4 % (24). Confound: the `04*` maps may differ in size or gem
layout (regimes.md says we do better on large and home-rich maps) [guess].

**Mapping.** Two cheap things: a screen, and feasibility detectors computed at the draft.
- Screen: every candidate plays `idle` on map variants nobody tuned on. Unseen variants can be made from the pool by
  transposing or mirroring a map file [guess: check the map format first]. Pass = zero faults, banked > 0 on every map,
  no body stationary > 100 rounds, fuel cuts not above the base.
- Detectors (features, no names): altar unreachable without killing a camp (ring / seal); every gem inside groups we
  cannot tank; groups unreachable on foot; one altar; gem-less gold groups. For each, check that the bot has a plan.

**Measure first.** v `idle` on all 128 maps: maps where we bank < 50 % of the best build's gems by r600; list their
features. One run, no band time.

### L3. Map classes: what switched, what paid, and how to judge it

**What other teams switched on, with results.**

| Team (level) | Features computed at the draft | What it switches | Result |
| --- | --- | --- | --- |
| EvilMangohh (peak 22, 4.0) | camp layout -> Normal / Contest (every gem in a monolith) / Boss (80 %+ of gems in groups too strong to tank, 3-4 picks) / Open (large 3-pick, 80+ camp gems) | a fixed draft table per kind; squads on normal maps, solo loops on big open maps | [web-opinion] kept all season; "the wrong draft table on one map type" was a fix they kept |
| dpark2380 (~1,750, 5.0) | pick count | draft: 3 = HoR / Marcella / Vendetta; 4 = HoR / Ryth / Marcella / Varg; 5 = Marcella / HoR / Vendetta / Ryth / Varg, no Vesper | [web-measured] 60 / 60 / 57 % head to head locally; Vesper back in: margin -24 / -42 |
| BestCody (~2,100, 4.0) | gold-heavy / career / gem-rush / mid classes from the camp list | a behaviour "expert" per class | [web-measured] **"no alternative was significantly better than baseline in any class, so no mixture of experts is justified"**; a no-fight harvest mode lost everywhere (118 v 163 of 280) and won only on 12 hand-picked maps; a feature tree found one robust class (own-half gold > ~1,360 with 5 picks) |
| TWWT-ai (low, 2.x) | home camps / sparse / central / monolith shapes; solos = min(n - need, floor(light groups / 2)) | split v squad | [web-opinion] untested |
| MIT 2023 4 Musketeers (3rd) | map size; which resource is seen near home | small map: all four first workers on the rush resource; ratio 2:1 else | [web-opinion] https://battlecode.org/assets/files/postmortem-2023-4-musketeers.pdf |
| MIT 2025 Just Woke Up (1st) | map size -> one threshold computed at the start | small maps: towers first (or "we'll get rushed"); big maps: economy pattern first | [web-opinion] https://battlecode.org/assets/files/postmortem-2025-just-woke-up.pdf |
| Steamhammer (StarCraft) | declared per-opening `Require` / `Avoid` on map features (island, ramp, choke width; rush distance planned) + per-map win records blended with the all-map record | opening choice | [web] the author: "So far, the data doesn't seem too helpful"; 14 maps were too many to learn per map https://www.satirist.org/ai/starcraft/blog/archives/570-this-opening-requires-that-map-feature.html , .../564-Steamhammer-1.4.2-opening-selection-by-the-opponent-model.html |
| RAISocketAI (microRTS 2023 winner) | exact map, else size band (<= 16, 17-32, > 32) | a policy per map / size, general net as the fallback | [web-measured] map-specific nets > 90 % where the general one was < 10 %; on the largest map it won 0 % v the two best scripts; hidden maps not reported https://arxiv.org/html/2402.08112v1 |
| Pantheon (spring 2026 winner) | BFS distance to the enemy core <= 1.5x own | attack routing; chokepoint detection added a day before the lock "greatly improved our win rate" | [web-opinion] |

**Reading.**
- What paid: (a) switches that make an impossible map possible (L2); (b) the draft by map kind or pick count; (c) map
  size -> tempo, as ONE threshold computed at the start.
- What did not: a different behaviour per class of ordinary maps. Per-class samples are 10-20 maps, and one 256-game
  run swings ±4, so a class effect below ~10 points cannot be seen (BestCody's verdict; Steamhammer's too).
- Nobody validated a class rule on unseen maps except through the tournament itself.

**Mapping.** Keep `cls.md`'s classes for the draft table and for size -> tempo. Write every class rule as Steamhammer's
`Require` / `Avoid` on features with the general bot as the default, so an unseen map that fits no class plays the
confirmed build. Judge a class rule on its class shrunk toward the all-map result:
`est = (n_c × d_c + k × d_all) / (n_c + k)`, k ≈ 60 games [guess], and require the off-class games byte-identical.

**Measure first.** Per class, top v band and us v band share (regimes.md has it): build a switch only where the top's
behaviour differs by class, not only its result.

### L4. Tribute turn hygiene

**Sources [web-measured].**
- EvilMangohh: "Walk into range and start the tribute in the same turn. We had been wasting a turn next to the altar on
  every tribute. Shipped with the end-game bag cap, this took the benchmark from 18 wins in 100 to 29" (pinned top-10
  opponents on the platform). Their caps: <= 25 gems after r600, on small maps, and once the enemy has banked 700; any
  carrier with 20+ gems banks when an altar is within 10. A channel is cancelled only if visible enemies can kill
  through it ("damage alone never interrupts a tribute").
- dpark2380 B175: bank from 20 gems for 30 rounds after seeing an enemy: 52 % over 3,328 local games, gems +22.5 ± 8.2;
  removing it -24 ± 17. Lost: bank within 15 tiles (48 %), late bank from 10 gems, carriers skipping fights (-79 ± 28).
- TWWT simulator: "bank whenever an altar is within 6" is worse than a plain threshold.

**Mapping.** Our `bank2` (race banking) was 49.3 % locally and `sb` exists; what is new is the wasted turn and L1's
boundary timing.

**Measure first.** In our decoded band games: rounds between first standing within 1 of an altar with gems and the
tribute start step (0 = no waste); our channels cancelled by stun / lock / death, by bag size; bags lost within 6 of
an altar after r600 v the top.

**Build sketch.** (1) In the move step toward an altar, if the step lands within 1, call tribute in the same turn.
(2) After r600 or enemy tributed >= 700: bank at >= 20 whenever an altar is within 10 walk. (3) <= 10 gems: start on
our boundary turn (L1 bit 4). (4) Keep a channel under damage unless the visible burst kills before completion.

### L5. Stance by evidence inside the game

**Sources.**
- dpark2380 B224 [web-measured, weak]: after 3+ deaths, engage only at a 1.5x edge: +12 ± 14 margin, deaths -0.3.
- Steamhammer [web]: epsilon-greedy over openings per opponent, exploration 5 % when always winning to 15 % when always
  losing; the AIIDE 2019 table shows rush openings beating lower bots (90-100 %) and failing against the top four
  (3-28 %), where slow macro openings did best
  (https://www.satirist.org/ai/starcraft/blog/archives/856-AIIDE-2019-what-Steamhammer-learned.html).
- Skinner, "Scoring Strategies for the Underdog" (https://arxiv.org/abs/1111.0693) [web]: maximise
  Z = (μ_us - μ_them) / sqrt(σ²_us + σ²_them); with many plays left maximise the mean, with few plays left and a deficit
  take variance; the leader does the reverse.
- Ours: on small maps a fight by r150 goes to a blowout 0.51 of the time v 0.25 without one (blowouts.md).

**Mapping [guess].** One byte of team memory already carries events: count our deaths and theirs. After 2 early deaths
with no kill, raise the engage bar and price mid groups down for N rounds (the opponent is stronger here: farm the far
side). In the last ~150 rounds or when their projected finish beats ours: take variance (contest their altar, even
fights for bags). Ahead: bank small, no even fights. The score-state half is web_levers L5 (known); the death-count
trigger is new.

**Measure first.** In n47: P(final share < 0.3 | we lose the first two deaths) and where the later deaths happen
(mid v home).

### L6. Judge on the win probability the share distribution implies; pin the opponents

- **[measured]** Our band games: mean share 0.35, sd 0.21, wins 25.3 % (n47_tz116); the normal model
  Φ((0.35 - 0.5) / 0.21) gives 23.6 %. tz-mega: 0.35 / 0.19 -> predicted 21.6 %, actual 20.7 %. So Skinner's Z fits.
- At our numbers +0.02 mean share is worth ~+3 win points; +0.02 sd is worth ~+1.5. A change that lowers the spread
  (safer, flatter games) at the same mean LOSES wins while we are the underdog; a change that widens it wins some.
  tz-mega v tz-116 is that case: same mean, sd 0.19 v 0.21, 31 v 38 wins.
- **Rule:** rank candidates by Φ((mean - 0.5) / sd) per opponent, not by mean share alone; against lower seeds (where
  we are the favourite) the same formula prefers the low-spread build. With 15-game series only the mean matters (§0).
- **Pinned opponents:** `match-groups create TEAM --source-group UUID` [web, 4.0 notes; check it on 5.0.1] replays an
  opponent's historical version, so two builds can meet the same opponent version on the same maps and sides
  (EvilMangohh's method; they also found a week-old pinned set flattered them: 17 of 90 v 4 of 100 against current bots).

### L7. Escort / hold for very large bags (contest and monolith maps)

EvilMangohh [web-measured]: a 200-gem bag takes 20 turns at the central altar; "walked there alone it was stolen in
12 of 25 local tests. The carrier now waits at spawn for two escorts." Our facts: enemy locks cancel 0.31 of our
channels a game at a median bag of 154 (BUILD_LOG). Mapping: a bag >= 100 does not start a channel with an enemy
within reach of the altar unless two allies are within 4, and locks the altar first. Measure: our bags >= 100 lost
within 6 of an altar, a game, by map kind. Narrow: build only if that count is > 0.3 a game.

### L8. Hypothesis: the roster's slot count (Cassi & Issac)

[measured: turn order in two decoded games] With 6 bodies against 5 (or 4 v 3), the larger team's surplus bodies act in
a run at the end of every round, and on rounds where that team starts next it has three consecutive turns across the
boundary. Evidence on drafting the pair is mixed: HighCortisol's pair work was their first fight gain (web_levers);
EvilMangohh drafts the pair first on open maps; dpark (+8-11 deaths a game) and BestCody (46 v 56 of 100) lost with
it. Measure before anything: in top5_9nov, kills by the pair inside those runs v outside, and the pair's pick rate by
team size among the top 5 now. Not a one-day build unless that is large.

---

## 3. Small checks worth ten minutes each (from other teams' bug lists) [web-measured by them]

- Stun scoring should skip stun-immune Marcella and targets already stunned; basic attacks into a high-Focus Ren trade
  badly through her retaliation (DeySag, 28 Oct review).
- After a kill, the dead enemy stays in the vision cache and a same-turn query on it throws (DeySag).
- A logging build scored 63 where the same logic scored 78; on fight maps two identical platform runs agreed on only 15
  of 25 games (BestCody): fuel differences re-roll games, so compare paired and on two fuel samples (EvilMangohh: two
  builds with identical logic differed by up to 15 games in 1,692).
- In 32 % of one team's champion-kill deaths the killer was hidden in a bush (dpark): our `bushw` is the answer already.
- Removing "recall home after a capture" was BestCody's biggest ablation loss (57 v 81 of 140); retreat at low health
  off: 67 v 81, deaths 13.1 v 8.4.
- "Actions before contact helped (a shield cast before the fight). Changing behaviour inside fights almost never did,
  and every 'play safer, back off' rule cost kills" (EvilMangohh): the same as our band ledger.

## 4. What does not transfer (said plainly)

- **Per-map learning** (Steamhammer's per-map records, RAISocketAI's per-map nets): needs repeated games on the same
  map; ours are unseen. Only the fallback structure (specific rule, else general) transfers.
- **Opening bandits across games** (UCB over build orders per opponent): no memory between games here.
- **Variance as a plan against the band over a long series**: at 15 games it is arithmetic noise (§0). It still holds
  inside one game when behind late (L5), and for choosing between equal-mean builds (L6).
- **Rushes as the underdog's weapon**: in the one table found (Steamhammer, AIIDE 2019) rushes beat weaker bots and
  lost to the top four; every CAMBC team that measured a whole-team rush or deathball lost with it (BestCody 81 v 107 of
  140; James 47-50 of 140).
- **Battlecode turn-order tricks that rely on spawn order** (2019 church chains, 2021 rush buddies): our order comes
  from priority and the round parity instead; the idea transfers (L1), the mechanism does not.
- **Map-analysis libraries (BWTA / BWEM chokepoints)**: found only as declared features in Steamhammer's plan; no
  source reported a measured gain from choke features. Pantheon's one-line claim is the only positive.
- Nothing new was found on focus-fire assignment or stun chaining beyond RESEARCH_WINNERS; the searches for scripted
  target-selection results returned nothing usable.

## 5. Sources

- CAMBC 2026a team notes (notes only): EvilMangohh https://github.com/toyeshhm/cambridge-battlecode-2026 ; dpark2380
  https://github.com/dpark2380/cambridge-battlecode ; BestCody https://github.com/BestCody/cambridge-battlecode
  (`docs/macro-experiments.md`, `docs/design-notes.md`, `docs/baseline-ablations.md`, `NIRVAN_CLAUDE.md`,
  `analysis/*/summary.md`); jamesrdainton-jpg https://github.com/jamesrdainton-jpg/Cambridge-Battlecode ; TWWT-ai
  https://github.com/TWWT-ai/Cambridge-Battlecode (`analysis/mechanics.md`, `forensics.md`, `maps.md`); DeySag
  https://github.com/DeySag/Cambridge-Battlecode ; predictor https://github.com/yufanwang07/secret-pantheon-tech ;
  Pantheon https://github.com/HerbertTheBird/Cambridge-Battlecode ; spring finals page https://luma.com/a1jsj4wq
- MIT Battlecode postmortems: 2019 Oak's Last Disciple, 2019 smite, 2020 The High Ground, 2020 Java Best Waifu, 2021
  3 Musketeers, 2022 5 Musketeers, 2023 4 Musketeers, 2023 Don't @ Me, 2025 Just Woke Up, 2025 confused: all under
  https://battlecode.org/assets/files/postmortem-YEAR-NAME.pdf
- Steamhammer blog: https://www.satirist.org/ai/starcraft/blog/archives/564-Steamhammer-1.4.2-opening-selection-by-the-opponent-model.html ,
  /570-this-opening-requires-that-map-feature.html , /856-AIIDE-2019-what-Steamhammer-learned.html
- microRTS: https://arxiv.org/html/2402.08112v1
- Skinner, Scoring Strategies for the Underdog: https://arxiv.org/abs/1111.0693
- Our measurements: `~/tzunami_data/analysis_10nov/web2/dbl.py` (double turns); share spread and map-family numbers
  from `~/tzunami_data/scrims/{n47_tz116,tzmega_big,tz174_big}.jsonl` + `sum/`.
