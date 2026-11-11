# mono: monolith sieges as a team job (`bots/_mono`, switch `monox`), 10 Nov

Agent `mono`. Copy: `bots/_mono` (from `bots/_stkA5`). Scripts: `~/tzunami_data/analysis_10nov/mono/`
(`mono.py` / `msum.py` / `mextra.py` = band replay anatomy; `bandcount.py` = captures from band match summaries;
`mkpi.py` = monolith KPIs of a kept local judge dir; `localsieges.py` = siege anatomy of local judge replays).

## The question

The orchestrator counted monolith-size captures on the band panel (64 monolith-map games a 195-game run): v281 46 v the
opponents' 84, A5 57 v 78. Both sides take ~1 monolith a game while it respawns 150 rounds after each capture. How and
when are monoliths taken, why does our bot skip them, and does a team siege (crew, rotating tank) pay?

## Short answer

- **cmp [measured]:** `_mono` with `monox=0` at A5's settings (`robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11
  endx=3`) builds a release wasm **byte-identical** to `bots/_a5r` (3,700,981 bytes; rechecked after the last change).
  The band-line build (`monox=95` with the value.h defaults) is byte-identical to the judged `_mono_N0` (3,711,195 bytes).
- **The gap is mostly closed already.** Counted per capture (not per 90-gem entry), v281 took 27 monoliths to the
  panel's 63 in 64 monolith-map games, but **A5 takes 49 to their 50** [measured]. Both sides still leave a monolith alive
  and untaken in ~90 % of rounds.
- **How the top does it [measured, band replays]:** 3-4 bodies for ~30 rounds with a rotating tank (main tank loses
  ~1,160 HP), mostly after a won fight (enemy at 3 or fewer bodies 64 %) or while ahead (+210). We siege with one
  HP-stacked Vesper for 87 rounds in 2.7 episodes; 57 % of our 3,000+ damage sieges fail and we give the enemy ~1,500
  monolith HP a game. Our bot skips monoliths because `farm_vt` prices them per body against the 25 % HP floor.
- **Built `monox`** (bits 1 crew job + 2 finish / steal + 4 respawn + 8 enemy down + 16 the top's trigger + 64 crew =
  bodies near it; 32 = biggest tanks, tested and left off). Final **`monox=95`**.
- **Local v A5 (`_a5r`):** monolith maps (80 games a seed) **50.0 / 52.5 / 46.2 / 43.8 % (mean 48.1 %, 320 games)**;
  monolith captures **1.08 v 0.88 a game (+0.20, +23 %)**, monolith gems **254 v 201 (+53)**, tributed gems level (832 v
  833), gold +68, deaths +0.28 (6.88 v 6.60). All 256 games: **50.4 % (seed 0), 52.0 % (seed 1)**; the 176 games on
  maps without a monolith 50.6 / 51.7 %, no faults, no missing games.
- **Verdict:** the KPI moves (captures +0.20 a game, +23 %; damage left to the enemy 4,044 v 5,158 HP a game) at a
  level local win rate. Locally it is not a win: the six builds judged on 4 seeds sit at 46.2-50.6 % on monolith maps
  (the noise of a 4-seed mean is +-2.8 points), and the first whole-team builds lost (33.8-43.8 %, one seed each). It
  can only show on the band [guess]: it encodes the top's measured pattern (short crew sieges, mostly after a won fight
  or while ahead), and the local opponent is A5 itself, whose sieges are our old ones.

## 1. The measured picture

### 1.1 The panel count, recounted per capture [measured, `bandcount.py`, match summaries]

The first count took every `gemCollection` entry of 90+ gems. That also counts big non-monolith groups (the band's
entries >= 90 on f89_v278: 63, its monolith-size captures: 23). Counted per capture (one team, one group, one round,
summed gems >= 150):

| Panel run (64 monolith-map games) | Our captures (gems) | Theirs (gems) | Our wins |
|---|---|---|---|
| p83_m2 (v281 = `_m2`) | 27 (7,538) | 63 (14,702) | 12 |
| tz182_big (A2) | 33 (8,628) | 58 (14,116) | 19 |
| tz183_big (B) | 27 (7,219) | 65 (15,314) | 18 |
| tz184_big (A3) | 41 (10,701) | 49 (12,140) | 19 |
| **tz186_big (A5)** | **49 (13,013)** | **50 (11,749)** | 23 |

- The gap was real for v281 (27 v 63) and closed step by step with A3 and A5: **A5 is level with the panel on monolith
  captures (49 v 50)**. A5's bigger team (sizex) is the likely cause [guess on the cause; the counts are measured].
- 96 % of captures go to one body on both sides (takers per capture: us 47 of 49 single, them 44 of 50).
- About 0.77 captures per side per game, while maps hold ~2 monoliths and 2.5-2.75 lives a game: a monolith stands
  alive and untaken in 88-92 % of game rounds [measured, replays below].

### 1.2 How they are taken: decoded band replays [measured, `mono.py` + `msum.py`; 159 games on monolith maps]

Ours = tzmega_big + n47_tz116 (106 side-games v the band); top = top_v_band (41) and top5_9nov (24).

| Per side-game | Us (v band) | Band (v us) | Top (v band) | Band (v top) | Top v top |
|---|---|---|---|---|---|
| Captures / game | 0.67 | 0.53 | 0.63 | 0.27 | 0.71 |
| Captures by round <300 / 300-600 / 600-900 / 900+ | 0 / 0.24 / 0.25 / 0.18 | 0 / 0.03 / 0.25 / 0.25 | 0 / 0.17 / 0.32 / 0.15 | 0 / 0 / 0.10 / 0.17 | 0 / 0.17 / 0.33 / 0.21 |
| Median first capture | r724 | r818 | r592 | r755 | r662 |

Per kill (medians unless noted):

| | Us | Band v us | Top v band | Top v top |
|---|---|---|---|---|
| Rounds first damage -> death | 87 | 88 | 30 | 28 |
| Siege episodes (gap > 15 rounds = new) | 2.72 | 1.95 | 1.46 | 1.22 |
| Own bodies hitting it (mean) | 1.74 | 3.25 | 3.75 | 2.89 |
| Main tank | Vesper 63 of 72 | Vendetta 19, Marcella 11, Varg 10 | HoR 11, Vendetta 7, Vesper 5, Marcella 4 | mixed |
| Tank max HP / HP the main tank lost | 3,250 / 3,232 | 3,000 / 2,835 | 2,600 / 1,157 | 3,900 / 1,512 |
| Tanks per kill / tank swaps | 1.75 / 1.7 | 2.93 / 8.3 | 2.89 / 6.7 | 2.76 / 5.1 |
| Deaths within 8 per kill, own / enemy | 0.28 / 0.32 | 0.46 / 0.39 | 0.14 / 0.21 | 0.29 / 0.24 |
| Sieges of 3,000+ damage that failed (share) | 57 % | 39 % | 24 % | 15 % |

At the start of the final siege: round us r696 / top r740; enemy bodies alive us 4.4 / top 3.0 (top: 64 % of its
sieges start with the enemy at 3 or fewer); tributed lead us +0 (ahead 46 %) / top +210 (ahead 75 %).

- **We siege with one body.** 40 of our 72 kills had a single hitter, nearly always a Vesper with bought HP; 69 of 71
  captures went to one body (Vesper 67). The top uses 3-4 bodies for ~30 rounds and rotates the tank (~3 tanks, the
  main one loses ~1,160 HP). The last push is the same for all: 900-1,000 monolith HP a round.
- **The top siege after a won fight or while ahead** (enemy down to 3 or fewer 64 %, lead +210). We start level, with
  the enemy at full strength.
- **The monolith never heals** (412 lives, not one HP gain): damage carries over. We put 1,486 HP a game into lives the
  enemy captured (top 433) and 1,957 into lives nobody killed.
- **Respawns:** the side that took a monolith retakes its respawn (us 24 of 24, top 11 of 12), 0-16 rounds after it
  reappears.

### 1.3 Why our bot skips most of them [read: `bot.cpp` `farm_vt`]

- `farm_vt` prices a group per body: the incoming damage is the group's Strength x `hit_frac` x the clear time x the
  body's share, and a group whose incoming would take the body below `hp_floor` (25 %) prices at 0. A monolith alone
  takes a body 80-100 rounds: only a 4,000+ HP Vesper passes, so she soloes it (the 87-round, 2.7-episode sieges).
- The pack price shares the incoming evenly, but a camp hits only the nearest body: no rule makes a crew rotate the tank.
- The existing `siege` (150 gems, `siege_hp` 5) only applies to groups that wall in an altar (02guardians).

## 2. What is built: `monox` in `bots/_mono`

Files touched: `bots/_mono/src/value.h` (`monox` and the `mono_*` knobs at the end of `Params`, with the bit list),
`bots/_mono/src/bot.cpp` (`MX()` beside `EX()`; `MxSt` + templates `mx_pick` / `mx_goal` / `mx_farm` / `mx_dbg` just
above `act_farm`; one hook in `act_farm` before its target search; one hook in `play_turn` after the goal choice).
Everything is in templates behind `if constexpr`: at `monox=0` nothing is instantiated.

| Bit | What it does | Why (measured) |
|---|---|---|
| 1 | **The crew job.** Once a round each body prices every monolith group with the team's camp damage D (me + the allies whose comms slot says FARM / FIGHT): it is the job when it dies within `mono_tmax` rounds at `mono_eff` x D and its hits (200 x those rounds) fit in `mono_pool` x the team's max HP above the leave line. Vetoed by 2+ enemies seen within 10 in `mono_eage` rounds (then off `mono_vban` rounds); the current job is held (no flip between two monoliths). Members: walk <= `mono_walk`, bag < `mono_bag`, HP above the leave line (max(`mono_out` x max HP, 500)). At it: melee members hit from beside it, ranged members from 3 (a ranged one nearer steps back), so the melee bodies tank in turn (a camp hits the nearest, ties to the lowest id); the hits start when the members present kill what is left within `mono_tgo` rounds, else they wait at 6 (outside its reach 5) and drop it after `mono_hold`; a member under its leave line walks out, heals at the spawn and rejoins at `mono_back`. The crew that killed it holds the job through the capture. | Top: 3-4 bodies, ~30 rounds, ~3 tanks; ours: one Vesper, 87 rounds |
| 2 | **Finish / steal.** A monolith at or below `mono_steal` (5,000) HP is the job without the time / pool tests (veto only by our bodies - 1 enemies); at or below max(2,500, 8 rounds of the crew present) the hits start at once. | HP never heals; we give ~1,500 HP a game to the enemy |
| 4 | **Respawn.** A respawning monolith back within `mono_pre` (25) rounds is the job (the crew waits by it). | The taker retakes the respawn 0-16 rounds after it reappears |
| 8 | **Enemy down** (2+ enemies dead): the tests relax x1.5, the veto needs bodies - 1 enemies. | Top: 64 % of sieges with the enemy at 3 or fewer |
| 16 | **The top's trigger.** A fresh monolith (>= 90 % HP) is started only with 2+ enemies dead or a tributed lead of 50; a siege under way or a near-dead one goes on. | Top: ahead 75 %, median lead +210; us +0 |
| 32 | (off) The biggest member tanks from beside it; melee members with a lower id guard at 2. | Tested: captures fell (0.93 v 0.98), 49.7 % |
| 64 | **The crew is the bodies near it.** The time test counts only the bodies within `mono_walk` (me by my walk; an ally by its position when seen, else its farm target's centre, or home). | Whole-team pricing sent bodies 20-45 tiles to wait at 6 |

Final knobs (value.h defaults): `mono_r0 300, mono_eff 0.7, mono_tmax 40, mono_pool 1.6, mono_out 0.35, mono_back 0.85,
mono_start 0 (off), mono_tgo 40, mono_walk 20, mono_bag 50, mono_eage 20, mono_vban 60, mono_hold 15, mono_steal 5000,
mono_pre 25, mono_down 2, mono_relax 1.5, mono_lead 50`. Fuel: one pass over the monolith groups and six slots a turn
(no fields built); fuelEx level (18.0-18.2 a game on monolith maps v the base runs 15-16 under the same load; 28.0 over
all 256 both seeds).

**It fires [measured, `mono_dbg` build, 8 games on 00monolith / 04keyhole / 02famine / 04wilds, both sides]:** member
body-turns 137 a game, of which hitting the monolith 27, waiting at 6 for the crew 43, walking / other camps of the
group 43; the job changed 23 times a game per team; 5 hold drops and 5 heal trips in 8 games; won 6 of 8.

## 3. Local results [measured: `judge.py` v `bots/_a5r` (A5 at its settings), monolith maps = the 40 maps with
n_mono >= 1, both sides = 80 games a seed]

Each row is 80 games a seed (40 maps x 2 sides) v `bots/_a5r`; KPIs from the match summaries (`mkpi.py`): monolith
captures = one team, one group, one round, 150+ gems; deaths = all deaths (camp included). A null run (A5 with
`seed=1` v A5) scored 53.8 % with captures 0.96 v 0.89: one 80-game run swings +-11 points, a 4-seed mean +-2.8.

| Build (all with A5's settings) | Win % by seed | Mean | Captures a game, us v them | Monolith gems | Deaths | Gold | Tributed gems |
|---|---|---|---|---|---|---|---|
| v7: bits 1+2+4, whole team (walk 45), hits from 0.5 x team damage, from r120 (leave line bug) | 33.8 | - | 1.24 v 0.93 | 298 v 205 | 7.42 v 6.56 | 4,635 v 5,377 | 731 v 903 |
| v15: + bit 8, from r300, leave-line fix | 43.8 | - | 1.12 v 0.94 | 268 v 208 | 6.65 v 5.96 | 4,860 v 5,184 | 794 v 855 |
| v31: + bit 16, walk 35 | 38.8 | - | 1.00 v 1.01 | 242 v 227 | 6.84 v 5.85 | 4,948 v 5,195 | 783 v 879 |
| b: v15 + walk 20, veto ban 60, job lock | 41.2 / 51.2 | - | 0.91 v 1.01 / 1.02 v 0.94 | 220 v 231 / 244 v 217 | | | |
| f: b + tmax 25, start only if the present crew finishes in 25 | 46.2 / 56.2 / 48.8 / 51.2 | 50.6 | 1.02 v 0.95 | 244 v 215 | 6.86 v 6.42 | 5,186 v 5,126 | 833 v 833 |
| g: f + bit 16 (monox 31) | 45.0 / 55.0 / 48.8 / 51.2 | 50.0 | 1.01 v 0.95 | 244 v 216 | 6.86 v 6.41 | 5,184 v 5,124 | 830 v 834 |
| h: finisher only (monox 3, tmax 12) | 42.5 / 47.5 / 48.8 / 46.2 | 46.2 | 0.96 v 0.95 | 228 v 219 | 6.77 v 6.54 | 5,169 v 5,099 | 826 v 837 |
| k: f + bit 32 big tank (monox 47) | 45.0 / 53.8 / 48.8 / 51.2 | 49.7 | 0.93 v 0.98 | 221 v 225 | 6.83 v 6.28 | 5,110 v 5,132 | 820 v 834 |
| m: g with tmax 35 | 42.5 / 52.5 / 45.0 / 46.2 | 46.5 | 1.02 v 0.87 | 243 v 202 | 6.76 v 6.63 | 5,149 v 5,040 | 822 v 814 |
| **n = final: monox 95 (g + bit 64), tmax / tgo 40, hold 15** | **50.0 / 52.5 / 46.2 / 43.8** | **48.1** | **1.08 v 0.88** | **254 v 201** | 6.88 v 6.60 | 5,146 v 5,078 | 832 v 833 |
| p: n with mono_out 0.45 (leave earlier) | 50.0 / 51.2 / 50.0 / 47.5 | 49.7 | 0.97 v 1.01 | 224 v 232 | 6.93 v 6.76 | 5,166 v 5,131 | 827 v 848 |

**All 256 games (final build `_mono_N`, monox 95) [measured]:**

| Seed | All 256 | 95 % CI | Monolith maps (80) | Other maps (176) | Deaths other maps, us v them | Faults / missing |
|---|---|---|---|---|---|---|
| 0 | **50.4 %** | 44-56 | 50.0 % | 50.6 % | 6.55 v 6.43 | 0 / 0 |
| 1 | **52.0 %** | 46-58 | 52.5 % | 51.7 % | 7.02 v 6.62 | 0 / 0 |

Held-out quarter: 50.0 % (seed 0), 51.2 % (seed 1). On maps without a monolith `monox` changes no decision (no group,
early return): those games move only with the changed binary.

**Siege anatomy, local [measured, `localsieges.py` on decoded judge replays; per kill, A = the judged build, B = A5 in
the same games]:**

| | v15 (A) | A5 v v15 | f seed 0 (A) | A5 v f | f seed 1 (A) | A5 v f | **n seed 0 (A)** | **A5 v n** |
|---|---|---|---|---|---|---|---|---|
| Captures a game | 1.11 | 0.84 | 0.85 | 0.94 | 1.00 | 0.81 | **0.96** | **0.80** |
| Rounds first damage -> death (median) | 141 | 87 | 106 | 101 | 126 | 97 | 124 | 87 |
| Own bodies hitting (mean) | 3.03 | 2.51 | 2.26 | 2.23 | 2.26 | 2.12 | 2.35 | 2.20 |
| Tanks a kill (mean) | 2.89 | 2.16 | 2.12 | 1.97 | 2.08 | 1.94 | 2.22 | 2.12 |
| Deaths within 8 a kill, own / enemy | 0.62 / 0.44 | 0.46 / 0.67 | 0.38 / 0.43 | 0.53 / 0.64 | 0.50 / 0.74 | 0.57 / 0.37 | 0.66 / 0.69 | 0.56 / 0.53 |
| Steals (the other side put in more) | 18 | 10 | 10 | 8 | 14 | 7 | 13 | 9 |
| Lives with 3,000+ of our damage taken by them or never killed, a game (HP) | 0.44 (4,824) | 0.50 (5,768) | 0.42 (4,694) | 0.47 (4,618) | 0.35 (4,001) | 0.55 (5,458) | **0.35 (4,044)** | **0.50 (5,158)** |

- The final build takes more monoliths than A5 in the same games (0.96 v 0.80 decoded, 1.08 v 0.88 over 4 seeds), steals
  more, and leaves less damage behind (4,044 v 5,158 HP a game).
- Its sieges still last long from the first hit (124 rounds median): most start as Vesper's solo damage (as before) and
  the crew joins when the time test passes. Pushing the crew in earlier (v7 / v15: whole team, start at half the team's
  damage) took the most monoliths (1.24 / 1.12 a game) but lost 300-700 gold and 0.7-0.9 more deaths a game and the
  win rate (33.8 / 43.8 %).

## 4. What the band should show

- Monolith captures (per capture: one team, group, round, 150+ gems): A5 49 v the panel's 50 in 64 monolith-map
  games; the build should take more (locally +23 %) and give less damage away (sieges of 3,000+ that end in the
  enemy's capture or no kill).
- Short crew sieges after a won fight or while ahead (bit 16), the respawn retaken (bit 4), near-dead monoliths finished
  or stolen (bit 2). Read with `bandcount.py LABEL` (captures and takers per capture) and `mono.py LABEL` + `msum.py`
  (siege rounds, hitters, tanks, failed sieges) on the decoded band games.
- Watch deaths: locally +0.28 a game on monolith maps (all causes). If the band's share falls with deaths rising near
  monoliths, the cost is the crew's exposure: `mono_vban` / the veto (`mono_eage`) are the knobs.
- `monox` acts only on maps with a monolith (31 % of the pool); the class is `all` because it is inert elsewhere.

## 5. What did not work / caveats

- **Not a local win.** Nine builds over the session: none beat A5 on monolith maps beyond the noise (best 4-seed means
  50.6 % f, 50.0 % g; final 48.1 %). The local opponent is A5 itself (a mirror): its sieges are our old ones, and our
  crews meet a team that fights like ours. The mechanism the top uses (siege after a won fight, short crew push) needs
  the band to show.
- **The whole-team version cost more than it brought** (v7 / v15 / v31): bodies walked 20-45 tiles, waited for a crew
  that did not come, and toggled the job on each enemy sighting (up to 39 job changes a body a game). The fixes (crew =
  bodies near it, veto ban 60, job lock, start only when the present crew finishes in time) made it level.
- A leave line at 45 % (p) kept the win rate level but removed the capture gain: the captures come with the exposure.
- **Biggest-body tank (bit 32) did not help:** Vesper tanking costs her farming and heal trips; the melee supports
  rotating by the tie rule did as well (0.93 v 0.98 captures, 49.7 %).
- Fresh monoliths still start mostly as Vesper's solo damage: our crew's damage (300-600 a round present) is below the
  top's last push (900-1,000), so the time test rarely passes on a full monolith.
- The orchestrator's first count (gemCollection entries of 90+) also counted big non-monolith groups; per capture A5 is
  level with the panel. The v281 gap (27 v 63) was real and A3 / A5 closed most of it.
- Debug counters (`mono_dbg`) are scratch only. Tie order: the build reads the champion handle as the id for bit 32
  only (off in the final).

## Cleanup
Scratch bots and match outputs deleted. Kept: `bots/_mono` (switches at 0 by default; `monox=95` with the defaults is
the final). Scripts in `~/tzunami_data/analysis_10nov/mono/`.

## Band line
`monox 95: monolith crew siege, finish/steal, respawn, top trigger|_mono|robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11 endx=3 monox=95|all`
