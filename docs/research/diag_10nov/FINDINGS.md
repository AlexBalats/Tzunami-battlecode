# FINDINGS: what the replays, the ladder and the web told us (session of 9-10 Nov)

One place for everything measured this session. Tags: [measured] replays / ladder / local games, [rules] / [sdk],
[web] a public write-up, [guess]. The plan that uses this is `docs/NIGHT_PLAN.md`. Detail reports sit beside this
file (`prio.md`, `a1_reverse.md`, `cls.md`, `disc.md`, `web2.md`); scripts are in `~/tzunami_data/analysis_10nov/NAME/`.

## The picture on one page (read this if nothing else)

Against the six UK band teams we win about one game in five. Four things explain it, in order of size. Each has a
lever in `docs/NIGHT_PLAN.md` (L-numbers).

1. **Their team grows and ours does not (§12.4, §12.5).** Our Vesper is as big as the top's Vesper; every other body
   of ours holds about half the stats of its counterpart. By r600 the band has bought 4,483 max HP to our 2,626 with
   fewer bodies. Causes, all measured: our supports earn half the camp gold of the top's supports; the band banks its
   gems through Marcella (2 gold per gem banked: 540 gold a game) while we bank through Vesper, whose passive pays
   nothing on gems; we take fewer cluster tiles (5x the gold and 20x the gems per camp HP of a wolf), and pure gem-cluster groups stand
   unharvested two thirds of the time for every team (§12.7; but a quarter of them are islands and a first timetable
   build did not raise team income: see the correction there); our Vendetta,
   Issac, Cassi and HoR buy almost no damage stats. -> L13 (Marcella takes and banks), L14 (the cluster timetable), L7 (clusters first, fewer bodies
   per group), L12 (support item lines).
2. **They convert fights and we do not (§2, §5, §11, §12.1).** Kills a game: the top 8.9, the band on us 6.5, us 4.3.
   Three mechanisms we lack: the double turn across the round boundary (Fish lands 32 % of its kills on it; we 0);
   hitting the stunned body (274 damage and a kill 17 % of the time for the band, 128 and 8 % for us); a finisher
   (the top's Vendetta lands 2.6 killing blows a game, ours 0.5). And one habit: in two of three of our deaths the body
   never hits back. -> L2, L6, L12.
3. **We die at home and in pairs on small maps (§1, §12.1, §12.2, §12.6).** Tiny maps are 39 % of the pool: 9.6 deaths
   a game, a third of them within 8 tiles of our own spawn (a tile that heals to full every turn and that enemies
   cannot enter), 40 % of them twin deaths where the partner was healthy. -> L10 (spawn fortress), L11 (twin link), L4.
4. **One-altar maps (§3).** 25 % of the pool, share 0.36. The winners there draft Prism instead of Vendetta (+12 win
   points across 15 of 16 teams) and keep their lock on the altar half the time; we do neither. -> L1, L3.

What does NOT separate teams (measured, so do not spend time there): who hits first, sharing captures, item-line swaps
alone, ward counts, endgame play, path efficiency, how fast locks are broken.

## 0. The frame

- **The qualifier is a tournament among UK teams on unseen maps, not ladder-seeded.** Beating the UK band
  (Kungarna, QS2isLaw, policy wonk, Rogue Lock Pickers, :3, Claudus Maximus; 2,250-2,420) is the objective itself.
  Format [web, a third-party predictor's README, not the organisers]: double elimination, top 8 through.
- **Series arithmetic [measured, binomial]:** at 25 % a game a best-of-5 is won 10 % of the time; at 40 % it is 32 %.
  Variance play does not help; only a higher mean does. Gem share predicts wins: win rate = Phi((mean share - 0.5) / sd);
  on our data +0.02 mean share is about +3 win points.
- **Every version of our bot is level on the band** (tz-116 38/150, tz-mega 31/150, tz-mega2 33/150 on the n47 games).
  Local tz-v-tz wins do not predict the band.

## 1. Where we lose, by map class [measured: 1,710 band games of the level builds; `cls.md`]

| Class | Pool | Share | Win | Blowouts | Our deaths | Our kills | Cost (pool x (0.5 - share)) |
|---|---|---|---|---|---|---|---|
| All | 1.00 | 0.413 | 0.20 | 0.42 | 7.2 | 4.3 | 0.087 |
| Tiny (< 1,500 open tiles) | 0.39 | 0.341 | 0.17 | 0.59 | 10.3 | 4.7 | **0.062** |
| One altar | 0.25 | 0.359 | 0.19 | 0.53 | 7.6 | 4.3 | **0.035** |
| One altar and tiny | 0.12 | **0.283** | 0.13 | | | | 0.025 |
| 2+ altars and tiny | 0.27 | 0.365 | 0.19 | | | | 0.037 |
| Mid-size (1,500-2,500) | 0.25 | 0.464 | 0.25 | 0.33 | 5.9 | 5.0 | 0.009 |
| Big (>= 2,500) | 0.36 | 0.453 | 0.20 | 0.31 | 4.9 | 3.4 | 0.017 |
| Close spawns (walk < 40) | 0.37 | 0.390 | 0.23 | 0.55 | 10.0 | 5.8 | 0.040 |
| Mid-heavy gems | 0.48 | 0.371 | 0.18 | 0.51 | 8.7 | 5.0 | 0.063 |
| 4 picks | 0.20 | 0.383 | 0.23 | 0.52 | 9.3 | 4.3 | 0.024 |

- Tiny maps and one-altar maps hold about 80 % of the total cost. On tiny maps we die 10.3 times a game against 4.9 on
  big maps, with the same kills.
- By opponent: policy wonk and Kungarna beat us worst on one-altar maps (share 0.27 / 0.29) and policy wonk on tiny
  maps (0.29).
- Fresh m2 bases on the class sets: `a1_m2` 29/120 wins (Kungarna 0/20); `tiny_m2` 18/120 (policy wonk 0/20, Kungarna 1/20).

## 2. Turn priority: the double turn [measured; `prio.md`, 234 games re-decoded with priority values]

- **Team A starts every odd round, team B every even round** (217,079 of 217,079 round changes). `set_priority`
  applies from the next round. So a body can be our LAST actor of a round we go second in and our FIRST actor of the
  next round, which we start: two turns with no enemy turn between, every second round, against every enemy body.
- **Who does it:** stellar best girl (rank 1), Intercontinental Fish, policy wonk (band), NEETCoders. They set the
  fighter's priority to +m for rounds they start and -m for rounds they go second (Fish: +-(700 + k) at the end of every
  fight turn; policy wonk: +-(100 + k) with an enemy within ~5, and a fixed 200 below ~20 % HP = always first).
- **What it buys:** Fish lands 32 % of its kills on the second turn of a double (3.4 kills a game), stellar 15 %,
  policy wonk 13 %, we 0 %. Flippers attack on 53-59 % of those second turns against 27-32 % of other fight turns. A
  flipper also dies less to enemy doubles (stellar 0 %, Fish 4 %; non-flippers 7-27 %).
- **What does not matter:** who hits first. First-hit share in mutual-hit rounds: BattleCats 0.38, Mite 0.36, stellar
  0.46, Fish 0.48, us 0.57. Mite (nearest first) and BattleCats (fighters last) kill 8 a game with opposite rules.
  Our `prio_fight` rule wins first hits and no more fights: consistent.
- Dead bodies keep their (empty) turn slots. A tribute started as the round's last actor loses one enemy window [rules].

## 3. One-altar maps [measured; `a1_reverse.md`, 144 games; draft study on ~15,000 ladder games]

- **The lock is a toll gate, not a channel breaker.** stellar and Fish place it from 2 tiles away on the way in to
  bank and tribute the next turn; 97 % of their tributes after the first lock start under their own lock; a third of
  their locks come with no tribute at all (a passing body re-locks). Only 3-7 % of locks cancel a channel. A lock stands
  54-71 rounds because nobody hits it until they need to bank; then it costs the enemy carrier 5 turns. Lock cover of
  rounds 100-400: stellar 0.58, Fish 0.48, band v us 0.27, us 0.
- **Facing a lock we already do what the top does** (the carrier hits it 5 times, then banks). The band locks 3.1
  times a game against us and 1.0-1.9 against stellar / Fish. We pay the toll and charge none.
- **Bank at about 30 gems, never above 80.** stellar's bag is 26-42 whatever the walk or the lead. 21 % of our tributes
  carry <= 10 gems (top 6-10 %). Lock cancels by bag: 1 % (<= 40), 4 % (41-80), 13 % (81-160), 25 % (> 160; ours).
  With an enemy within 4 of the altar and a bag over 20, 21-36 % of tributes fail (0-3 % with nobody near).
- **Camps within 4 of the altar are a farm.** There our first tribute is r242-272 against r89-135; we take a third of
  the altar camps the top takes. On bare altars we are level (r94). Camps do not kill carriers there (< 0.25 deaths a
  game); enemies do.
- **Mid walks (18-28 tiles to the altar):** the top keeps 1.7-2.2 bodies within 8 of the altar at r100-200; we 1.0-1.1.
- **Draft: Prism for Vendetta on one-altar maps is +12 +- 3 win points** with team strength held fixed (15 of 16 teams
  positive; +14 against the Vendetta line, +17 against the Vesper line; the same in the 5 Nov and the 7-10 Nov halves).
  On 2+-altar maps Prism is +1 +- 2. C&I +6, Ryth +5 on one-altar maps; Vesper -5, Varg -4.
  [sdk] Prism: +0.2 Focus per carried gem. Locally v _m2 on the one-altar maps `draftx 1` is level (48.3 % of 118
  non-frozen games, share 0.50; `draft.md`). The high fuel numbers of the first runs were frozen stand-off games, a
  base fault: with 12 bodies in sight a turn costs 140-160k fuel and every body is cut every second round.
- Local results of the lock build (64 games on the one-altar maps v _m2): `alt1x 7` 43.8 %, `7b` 53.1 / 50.0 % (2 seeds),
  `15` 42.2 %, `111` (with the bank rule and camp-farm bits) 32.8 % with deaths 9.4 v 6.4. The local opponent places no
  locks and never has to pay the toll, so the band is the test.

## 4. Tiny maps, the first 200 rounds [measured; the `tiny` agent's notes in `bots/_tiny/src/value.h`, blowouts.md]

- 55 of 112 band losses are blowouts; a death by r150 or fewer than 40 gems collected by r150 catches 39 of them.
- **Converging:** bodies 6-14 tiles away at the first hit arrive within 6 rounds 0.56 of the time for the top, 0.43
  for us. Our answered fights at a live-HP ratio >= 1: kills 0.37 v deaths 0.23; below 1: 0.22 v 1.11.
- **Vesper spacing:** the top's Vesper takes 12 HP a contact round, ours 24; she is the front body 53 % v 67 %.
- **Home defence:** the top engages 0.69 of enemy entries into its own third, we 0.40. 40 % of our early deaths are in
  our own third.
- For us any early fight is worse than none (win 0.16-0.20 after a fight v 0.34 with none); for the top a fight helps.

## 5. Posture at 4-12 tiles from an enemy [measured; `disc.md`, 410k top v 899k of our body-rounds]

| State | Top | Us |
|---|---|---|
| Enemy at 4-6, all | advance .31, retreat .24, sidestep .08, idle .14 | advance .20, retreat .32, sidestep .12, idle .17 |
| Enemy at 4-6, we are stronger (live HP within 8 > 1.41x), ability ready | advance .39 | advance .20 |
| Enemy at 7-12, standing at a camp | keeps hitting .53 | .36 (sidestep .16 v .07) |
| Enemy within 12, not at a camp, slot 1 ready (Vesper, Issac, Vendetta) | idle .23, advance .22-.25 | idle .35-.39, advance .10-.12 |
| After a camp dies, no enemy near | stays (captures) .18-.20 | .07-.08, walks off, parks later |
| Carrying >= 15 at an altar | tribute starts .04 of rounds | .12 (smaller bags = shorter channels; NOT restarts, see the note) |

- The top's advance share rises smoothly with the live-HP ratio: 0.17 below 0.5, 0.29 at parity, 0.36-0.39 at
  1.4-2, 0.49 above 3.5. Ours is 0.11 / 0.18 / 0.23-0.27 / 0.36: the same shape, a third lower everywhere.
- What follows within 6 rounds, stronger side at 4-6 (the `post` agent's follow-up):
  - top after an advance: a champion hit 0.47, died 0.0068; after a retreat: hit 0.20, died 0.0043;
  - us after an advance: hit 0.42, died 0.0105; after a retreat: hit 0.10, died 0.0092; **after idling: died 0.0121**.
  Retreating and idling do not save us: we die as often as when we advance, and we land half the hits.
- Death rate per body-round with an enemy within 3: top 0.010, us 0.021.
- **Correction (10 Nov ~02:30):** the first reading of the altar row was "our tribute channels restart 3x as often". A
  direct count (`~/tzunami_data/analysis_10nov/loop/trib.py`) does not support it: a second start by the same body
  within 6 rounds is 1 % of our starts (top 4 %). The row only shows shorter channels. What does hold: an enemy lock
  lands during 13-17 % of our channels above 80 gems (top 7 %), and the top starts 25.6 tributes a game to our 16.

## 6. Kit use [measured; `disc.md` casts, the `kit` agent's notes in `bots/_kit/src/value.h`]

- Per 100 body-rounds with an enemy within 6, top v us: Cassi damage 8.3 v 4.7, Marcella damage 9.0 v 6.4, Vesper
  reset 8.1 v 5.6, Vendetta reset 6.8 v 4.7.
- Cassi's stun goes on camps 7.2 v 3.5 per 100 camp rounds (and 2.2 v 1.1 travelling): it is on cooldown when fights start.
- A cast from range costs the step: camp hit-rounds with a cast and no basic attack are 15-18 % for us, 5-9 % for the top.
- HoR's landing dash is ready and unused in 38 camp hit-rounds a game (top 12).
- A last-leg dash that brings the farm target into basic reach, then the hit: top 5-6 a body-game, ours 0.
- A stunned enemy skips its next turn [measured]; our threat tests still count it.
- Dashes while travelling are level (10 v 11 per 100), except Vesper (9.0 v 12.1; she stands still 28 % of travel rounds v 23 %).

## 7. The opening [measured; the `open` agent's `rules.py`: 292 top games v ours v idle on 170 map-sides]

| | Top (v live opponents) | Us (v idle: an upper bound) |
|---|---|---|
| Distinct first groups / bodies per first group | 2.20 / 2.33 | 1.96 / 2.71 (big maps 1.84 / 2.96) |
| First-wave group kinds | wolf .38, elk .37, gold cluster .14, **gem cluster .11** | wolf .37, elk .32, **gold cluster .25, gem cluster .02** |
| When not the nearest group: gems / gold of the chosen group | 26.7 / 96 | 17.8 / 115 |
| Clusters captured by r150 (hitters) | 4.31 a game (1.19) | 3.66 (1.03) |
| Hitters on mid-strength camps (Str <= 60) | 3.67 | 4.16 |
| Team's first tribute / tributes by r150 | r84 / 2.55 | r86 / 2.01 |

- The top walks past the nearest group 62 % of the time for a group with 3x the gems; a simple "rate x nearness" rule
  with gold priced at half predicts 46 % of its first choices.
- We open on gold clusters where the top opens on gem clusters, and we stack more bodies on fewer groups, most on big maps.
- By its 2nd-3rd visit 39-46 % of the top's work is in the mid zone or beyond (Varg 68 %, Ryth 59 %, Cassi 50 %).

## 8. Class rows mined from the band archive [the `cls` agent's survivors; listed in `bots/_cls/src/value.h`, table not written up]

Rows the agent kept after mining ~100 past paired band runs per class (each is one bit of `clsx`, acting only in its class):
1 four-pick maps: the mega2 layers off (tz-116 play); 2 one altar or tiny: support Health lines (eco 2, HoR all Health);
4 tiny with 2+ altars: fb2 off; 8 big maps: no Capture emblem on Vesper; 16 mid-heavy and not tiny: the tz-66 stops off;
32 one altar: dth 0. The supporting numbers are in `~/tzunami_data/analysis_10nov/cls/` (`mine.py`, `pairs.pkl`): re-run
`mine.py` to print them before trusting a row. Treat every row as a hypothesis for a fresh class set.

## 9. From the web [`web2.md`]

- Tribute hygiene [web, another team's measurement]: start the tribute the same turn as the walk into range, with a bag
  cap late (<= 25 gems after r600 or once the enemy has banked 700): their pinned benchmark went from 18 to 29 wins in 100.
- A warning [web]: one ~2,100 team measured four draft-time map classes and found no class strategy better than its
  baseline; what paid elsewhere was the draft by map kind, feasibility switches and one size threshold.
- Unseen-map robustness: qualifier upsets came from bots that kept working on odd maps (sealed or ringed altars,
  islands). On the newest `04*` maps we score share 0.42 against 0.33 on older families [measured, 450 games].
- Two platform notes from other teams (4.0 era, unverified on 5.0): an upload is used for games as soon as it
  compiles; `--source-group` plays an opponent's historical version (we use this for pairing).
- Bug checks from other teams' lists: stun scoring on stun-immune Marcella and on already-stunned targets; a dead enemy
  left in the vision cache throws on a same-turn query.

## 11. Mechanics worth abusing (a rules read-through plus replay checks, 10 Nov ~02:00)

Source: GameRules.md end to end, the engine tables in `diag_9nov/mechanics.md`, and
`~/tzunami_data/analysis_10nov/loop/stun_spawn.py LABEL` (80 games each of `top_v_band` and `n47_tz116`).
Ranked by expected value for one night.

| # | Mechanic [rules / sdk] | What the replays show [measured] | The exploit | Status |
|---|---|---|---|---|
| 1 | The starting team swaps every round; priority applies next round | §2: the flip gives a body two turns running against every enemy; Fish 32 % of kills on the second turn | The double turn | `bots/_prio` (L2) |
| 2 | **A stun makes the victim skip its next turn** and cancels recall, tribute and crystal channels | Stuns landed on champions: top 12.5 a game, us 5.5, the band on us 6.0. Damage on the stunned body by the next round: **top 273, band on us 274, us 128**. A kill within 3 rounds: top 18 %, band on us 17 %, **us 8 %**. 25 of our 31 stuns a game go on camps or miss (top 35 of 47, with 2.3x our champion stuns) | Keep Cassi's stun for champions; every body in reach hits the STUNNED body (it cannot act or flee); stun a tributing or recalling carrier | partly in `bots/_kit` (bit 8); the focus-the-stunned rule and the camp ban are NEW (L6) |
| 3 | Stun + the double turn | A stun cast before the victim has acted that round kills more often (top 24 % v 15 % after) | Cassi stuns first in a round we start, or last in a round we go second: the team then gets two volleys while the victim loses its turn | NEW: a `priox` bit for the stunner (L2) |
| 4 | **Own spawn tiles heal to full at every turn end; enemies cannot step on them** [sdk: spawn healing 1.0] | With an enemy within 6, bodies stand on their own spawn tile 0.4-1.5 % of the time: nobody uses it. We spend **130 body-rounds a game within 8 of our spawn with an enemy within 6** (the top 67) and die there 0.55 times a game by r600 (17 % of our deaths). Below half HP there, we step toward home only 47 % of the time | The spawn as a fortress: a hurt body within ~8 of home walks onto a spawn tile instead of recalling or fleeing elsewhere; a body on a spawn tile stays and hits whatever is in reach (it cannot be killed unless one round's damage exceeds its max HP); home camps in range of a spawn tile are farmed from it | NEW (L10). Biggest on close-spawn maps (37 % of the pool, deaths 10.0 a game) |
| 5 | An altar lock costs 10 gold and takes 5 enemy basic hits; it also cancels channels at placement | The band's locks cost us 12.8 carrier turns a game on one-altar maps and **10.6 on maps with 2+ altars**; we place none anywhere. 98 % of the top's locks are at mid altars | The toll gate on EVERY map: lock any altar an enemy has been seen near (or tributing at) before our own tribute, and re-lock in passing | `bots/_a1` covers one-altar maps (L3); extending it to shared altars is a knob (L3b) |
| 6 | Tribute length is fixed by the bag at the start (1 tick per 10 gems); completion banks the whole bag; a tick lands at turn end, completion at the next turn start | Lock cancels by bag: 1 % (<= 40 gems), 13 % (81-160), 25 % (> 160). A <= 10 gem tribute started as the round's last actor completes with no enemy turn in between | Bank small bags on the boundary turn (uninterruptible); never start a channel above ~8 ticks with an enemy lock-holder or stunner in sight | the cap is in L3; the boundary start is a `priox` idea (L2) |
| 7 | Captures resolve before channels; a capture during a channel is banked with it | not measured (rare) | On camps touching an altar: start a 1-tick tribute the round before the capture lands; the reward is banked the round it is captured | idea only |
| 8 | Camps hit only the nearest champion in range, of either team; they act at round start | 1,162 of 1,162 clean cases | A Jungle / Durability body stands nearest; a body on a spawn tile as the nearest takes the hits for free | `home_farm` exists; check it uses spawn tiles |
| 9 | A fuel-exhausted turn is lost and resumes next round | Our cuts are ~31 a team-game but 880 on the worst map (camp-heavy maps: bodies cut every second round late) | A governor: below ~55k fuel before the goal choice keep the current goal (`pathx` bit 8 exists, off). An unseen camp-heavy map could cost a whole game | check before the lock (plan §5) |
| 10 | Both drafts are revealed pick by pick | not studied beyond pick order | Counter-pick on the later picks | no time |
| 11 | Greed: 25 plain shards become a 40-shard emblem (750 gold); buffed in 5.0 | The top barely buys it (5 champion-games) | Only for a body that spends 750+ gold in one stat; our supports never have it | skip |

Notes:
- The stunned-body numbers are the cleanest new gap: the band converts a stun on us into 274 damage and a kill 17 % of
  the time; we convert ours into 128 damage and 8 %. Same champions, same stun.
- The spawn fortress is unused by every team measured, so there is no replay proof that it wins. The mechanic itself is
  [sdk] and was read from the engine's settings table. Treat it as a hypothesis with a cheap local check: deaths within 8
  of our spawn and HP lost at home before r200.

## 12. v280 / mega2 against the band, body by body (10 Nov ~03:00; scripts in `~/tzunami_data/analysis_10nov/loop/`)

### 12.1 How we die [measured: `deaths.py` on `tiny_m2` (120 games), `tzmega_big` (150), `top_v_band` as the reference]

| | Us, tiny maps | Us, general (v280) | The top v the same band |
|---|---|---|---|
| Deaths a game | 9.6 | 6.8 | 3.7 |
| ... after r400 | 6.6 (69 %) | | |
| ... in our own third | 4.1 (42 %) | | |
| ... within 8 tiles of our own spawn | 3.3 (34 %) | 1.1 (16 %) | 0.4 (11 %) |
| Killer's side has a body >= 1.5x our max HP within 6 | 61 % | 50 % | 42 % |
| The dying body never hit a champion in the whole episode | **67 %** | **60 %** | 43 % |
| Idle share of its turns in the episode | 30 % | 30 % | 20 % |
| Alone (no ally within 6) | 31 % | 35 % | 33 % |
| Victims | Cassi 26 %, Issac 26 %, Vesper 14 %, Vendetta 12 %, HoR 12 %, Marcella 10 % | | |

- An "episode" runs from the first round an enemy is within 6 until the death (median 8-9 rounds).
- Two in three of our deaths come with no hit back. The top's bodies fight back in 57 % of theirs.
- Deaths with no enemy within 6 (1.6 a game on tiny maps) are almost all the OTHER twin dying with its partner
  (1.3 a game); true camp deaths are 0.28 a game, 94 % of them a body below 30 % HP starting a recall inside a camp's reach.

### 12.2 The twins [measured: `twins.py`]

| | Us, tiny maps | Top, tiny maps | Us, other maps | Top, other maps |
|---|---|---|---|---|
| Twin-death events a game (each = 2 bodies, 2 bags) | **1.93** | 1.20 | 0.79 | 0.82 |
| The other twin above 60 % HP at the death | 90 % | 83 % | 89 % | 87 % |
| With an enemy within 6: Cassi is the nearer twin | 40 % | 31 % | 45 % | 43 % |
| ... an enemy within 3 of Issac / of Cassi | 13 % / 11 % | **25 % / 11 %** | 17 % / 12 % | 22 % / 14 % |
| Issac's max HP in those rounds | 1,043 | **1,344** | 1,118 | 1,168 |

Twin deaths are 40 % of all our body deaths on tiny maps. The top's Issac stands in front and is 300 HP bigger; ours
does not front. In nine of ten twin deaths the partner was healthy: its HP did not matter.

### 12.3 The six band teams against us [measured: `opp.py` on `tzmega_big` + `tiny_m2` + `a1_m2`, 64-65 games each]

| Opponent | Our win | Our deaths a game (by r150 / r300) | Their usual picks | Nearest enemy at our deaths | Mean max HP, us v them: r300 / r600 | Banked, us v them: r300 / r600 |
|---|---|---|---|---|---|---|
| Team Kungarna | **0.08** | **12.0** (1.36 / 3.17) | Marcella 1.00, HoR .92, Ryth .67, Vendetta .50, Prism .41 | Marcella 26 %, HoR 21 %, Vendetta 19 % | 1,041 v 1,293 / 1,327 v 2,070 | 78 v 158 / 261 v 386 |
| policy wonk | 0.12 | 9.0 (1.11 / 2.49) | HoR 1.00, Marcella 1.00, + two of types 9 / 11 / 8, Vendetta .38 | **Marcella 41 %**, type 9 19 %, HoR 18 % | 1,045 v 1,365 / 1,275 v 2,101 | 91 v 171 / 290 v 462 |
| Claudus Maximus | 0.15 | 4.4 (0.89 / 1.83) | type 10 .95, Ryth .83, Marcella .82, Vendetta .63 | Ryth 23 %, Marcella 20 %, Vendetta 20 % | 1,061 v 1,398 / 1,474 v 2,274 | 114 v 216 / 328 v 445 |
| QS2isLaw | 0.28 | 6.7 (0.85 / 1.48) | Vendetta, type 10, Marcella 1.00, HoR .82 | Marcella 35 %, Vendetta 32 % | 1,117 v 1,535 / 1,429 v 2,266 | 83 v 171 / 312 v 450 |
| Rogue Lock Pickers | 0.28 | 9.5 (0.85 / 1.88) | Vesper .82, Ryth .77, Vendetta .75, Marcella .68 | Vesper 31 %, Vendetta 19 % | 1,075 v 1,285 / 1,362 v 1,837 | 90 v 158 / 259 v 412 |
| :3 | 0.29 | 7.7 (0.58 / 1.51) | HoR .92, Vesper .86, Marcella .63, Prism .57 | Vesper 33 %, HoR 18 % | 1,045 v 1,342 / 1,389 v 1,913 | 133 v 124 / 330 v 371 |

(Types 8-11 are champions our name table does not cover; `opp.py` prints the ids.)
- **Marcella is the band's carry**: every band team but one plays her in most games, she is the nearest enemy at 26-41 %
  of our deaths against the three teams that beat us worst, and their Marcella has +535 max HP and +106 Focus by r300
  (ours: +12 and +61). Marcella is immune to stuns [web note; check in the SDK] and earns 2 gold per gem she banks.
- Kungarna kills us early and often (3.2 deaths by r300); Claudus wins without killing (4.4 deaths a game): it out-farms us.
- Every band team has banked about twice our gems by r300 except :3.

### 12.4 Size and income [measured: `size.py`, `share.py`, `campdmg.py`, 80-100 games each]

| Per game | Us (v280) | The band v us | The top v the band |
|---|---|---|---|
| Bodies | 5.6 | 4.8 | 5.5 |
| Team max HP bought by r150 / r300 / r600 | 256 / 993 / 2,626 | 500 / 1,518 / 4,483 | 319 / 1,338 / 4,573 |
| Team Focus bought by r300 / r600 | 76 / 183 | 194 / 475 | 170 / 393 |
| Team Strength bought by r300 / r600 | 124 / 279 | 64 / 177 | 107 / 298 |
| Unspent gold held at r300 | 174 | 182 | 201 |
| Camp and banking gold by r300 / r301-600 (kills left out) | 507 / 493 | 693 / 894 | 835 / 988 |
| Captures by r300 / r301-600 | 11.2 / 10.8 | 14.6 / 15.7 | 18.4 / 17.8 |
| Camp HP removed by r150 / r151-300 / r301-600 | 12.3k / 13.1k / 27.2k | 13.7k / 14.0k / 33.0k | 13.8k / 14.9k / 34.3k |
| Camp HP removed per living body-round, r<=150 | 15.5 | 19.7 | 17.2 |
| Gold per 1,000 camp HP removed, r<=300 | 20 | 25 | 29 |
| Cluster share of camp damage, r<=150 | 18 % | 20 % | 24 % |
| Bodies sharing a capture | 1.04 | 1.06 | 1.06 |

- **Our Vesper is as big as the top's; everyone else is not.** Max HP / stat bought by r600, ours v the top's:
  Vesper +1,471 HP +251 Str v +1,772 +230; Marcella +179 HP +144 Focus v +1,241 +226; HoR +56 HP +63 Focus v +909 +105;
  Vendetta +535 HP +31 Str v +1,082 +127; Issac +275 HP +0 Str v +508 +13; Cassi +215 HP +1 Focus v +141 +75.
- Camp gold by r300 per champion (share x total): Vesper 193 (us) v 184 (top); Vendetta 76 v 150; Marcella 101 v 142;
  HoR 56 v 134; Issac 35 v 67; Cassi 46 v 50. **Our supports earn half of what the top's earn; the Vespers are level.**
- Nobody shares captures (1.04-1.06 bodies per capture for every team): the top's supports are not fed by standing on
  Vesper's tiles; they capture camps of their own, and more of them (18.4 captures by r300 v our 11.2).
- The gap opens in the first 150 rounds, before items: the band removes 27 % more camp HP per body-round than we do
  with the same kind of champions, and each 1,000 camp HP earns the top 45 % more gold than us (more cluster tiles: a
  120-HP cluster tile pays 5x a wolf's gold per HP and 20x its gems per HP; plus Treasure / Prospector passives).
- Damage per camp hit-round by champion and phase (the `kit` agent's table, `~/tzunami_data/analysis_10nov/kit/sum_band.txt`):
  our Issac's Strength stays 45-47 all game (top 120, band 88 in the last phase); our Cassi and HoR hold Focus ~104-125
  where the top's hold 222-233 by the third phase; our Vendetta's Strength is 127 v 244. Vesper is level or ahead.

### 12.5 Who banks the gems: Marcella's passive [rules: Marcella is immune to stuns and gains 2 gold per gem she tributes; measured: `banker.py`, 100 games each, to r900]

| Per game | Banks (gems) | Share of the team's bank | Mean bag carried | Deaths | Bag lost |
|---|---|---|---|---|---|
| **Our Vesper** | 229 | **0.52** | **39** | 0.84 | 31 |
| Our Marcella | 72 | 0.16 | 7 | 1.09 | 11 |
| Our Vendetta / HoR / Cassi / Issac | 69 / 46 / 29 / 23 | 0.16 / 0.10 / 0.06 / 0.05 | 9 / 5 / 4 / 4 | | |
| **The band's Marcella (v us)** | **270** | 0.37 | 16 | 0.52 | 9 |
| The band's Vendetta / HoR / Ryth | 148 / 124 / 95 | 0.20 / 0.17 / 0.13 | 10 / 11 / 7 | | |
| The top's Vesper / Vendetta / Marcella / HoR | 253 / 208 / 225 / 147 | 0.34 / 0.28 / 0.30 / 0.20 | 25 / 18 / 18 / 14 | 0.25-0.51 | 4-11 |

- **The band funnels gems through Marcella:** 270 banked a game = 540 gold from her passive alone, and she takes 44-49 %
  of all camp and banking gold on her side. She cannot be stunned, so only a lock or her death (1,200 HP) stops her
  channel. That is why she is their biggest body and the nearest enemy at 26-41 % of our deaths.
- **We funnel gems through Vesper** (900 HP, ranged): she banks half our gems, walks with a mean bag of 39 and loses 31
  gems a game on death. Her gold passive pays nothing on gems. Our Marcella banks 72.
- Per capture, the taker's bonus: an elk group (15 gems, 90 gold) gives Marcella +30 gold at the bank against Vesper's
  +18 to +30 (her 20-33 % gold bonus: the two rule exports disagree); a gem-cluster tile (7 gems, no gold) gives
  Marcella +14 and Vesper nothing; a golem (36 gems) +72 against +32-53. Gold clusters and wolves favour Vesper.
- The top spreads the bank over four bodies with bags of 14-25.
- Prism, in the band and in the top, walks with a bag of 140-185 gems and tributes less than once a game (her passive:
  +0.2 Focus per carried gem). Note for the Prism draft: do not copy that with our banking code until measured.
- Vendetta [measured, the `kit` agent's table]: killing blows a game 0.5 (ours) v 2.6 (the top's); a dash followed by a
  champion hit 2.1-2.4 v 4.0; dashes onto camps 0 v 6.3. Her Strength bought by r600: +31 v +127.
- Kits [rules, `docs/Champions/`]: Marcella's slot 0 is an attack reset whose next hit STUNS for one round (we have two
  stunners, not one); Cassi's stun has range 4 and does no damage; Prism's slot 0 is damage plus a stun at range 4;
  Vendetta's kills (camps included) reset her cooldowns.

### 12.6 Invasions of our third [measured: `invade.py`, the same games; "third" = nearer our spawn than 0.4 of the way]

| Opponent | First entry (median) | Their body-rounds in our third, r1-150 / r151-300 | The same against the top |
|---|---|---|---|
| policy wonk | r91 | 56 / 58 | first entry after r300; 18 / 23 |
| Team Kungarna | r97 | 34 / 46 | r97; 25 / 16 |
| QS2isLaw | r92 | 30 / 41 | after r300; 4 / 17 |
| Claudus Maximus | r125 | 23 / 24 | r140; 24 / 23 |
| Rogue Lock Pickers | r173 | 19 / 62 | r203; 1 / 12 |
| :3 | r199 | 14 / 19 | r192; 11 / 13 |

- They come 1.4-1.9 bodies at a time. We meet them with 1.5-2.0 bodies of about the same total live HP (r151-300:
  1,090-1,580 v their 1,240-1,670); the top meets the same invaders with 1,300-2,270 HP against 950-1,390.
- policy wonk and QS2isLaw enter our third 200 rounds earlier than they enter the top's: they come because it pays.

### 12.7 Free gems left standing: pure cluster groups [measured: `uptake2.py`, `uptake3.py`, 80 games each; r60-600]

A "pure" group holds only gem or gold cluster tiles (120 HP each, 0 Strength: they never hit back) and respawns 50
rounds after its capture, so it can be cleared about 9 times between r60 and r600.

| Pure GEM groups, per game | Groups | Gems a clear | Cleared by r600 (either team) | Never cleared | Stands alive |
|---|---|---|---|---|---|
| Our own zone (our games) | 1.3 | 13.2 | **2.9 of ~9** | 28 % | 65 % of rounds |
| Mid zone (our games) | 2.3 | 21.9 | **2.8 of ~9** | 36 % | 67 % |
| The top's own zone (its games) | 1.6 | 12.1 | 3.3 | 30 % | 68 % |
| Mid zone (the top's games) | 2.7 | 24.1 | 2.5 | 27 % | 72 % |

- Pure GOLD groups are cleared more (own zone 4.2 for us, 5.1 for the top; never cleared 10-17 %): every team values
  gold clusters above gem clusters.
- Where a team does bother, 6+ clears happen (22-27 % of pure gem groups), so the cycle is achievable.
- **Nobody harvests these on their timer, the top included.** Between r60 and r600 the pure gem groups in our own zone
  and the mid hold about 640 gems of harmless income (1.3 x 13.2 x 9 + 2.3 x 21.9 x 9); both teams together take about
  a third of it. A game is won at 1,000.
- A clear is cheap: a 2-tile group is ~6 hits and a 5-round capture (3 with the Capture emblem) for 13 gems; a 3-tile
  mid group ~9 hits and the capture for 22. At the site that is over 1 gem a body-round, against our team average of
  0.12 a body-round.
- About 10 % of maps have clusters no body can walk to (islands); a teleport crystal reaches them (FINDINGS §11).
- [sdk] A group's state is readable as alive / reward available / respawning with a timer (`camp_group_state`), but
  only in sight; vision is not shared.
- **Correction after building it (`econ.md`, 10 Nov ~06:00): the 640-gem pool overstates what can be reached.**
  - 24 % of pure gem groups and 18 % of pure gold groups have NO walking path from our spawn (islands): that is most of
    the "never cleared" share. The mean walk from our spawn to a pure group in our half is 43-44 tiles.
  - The timetable (`clusx`) did raise clears v idle (own-zone gem 3.2 -> 4.6, gold 3.0 -> 4.5, mid gem 3.0 -> 3.8), but
    team income did not rise (1,000th gem r872 v r860; team gold at r600 -4 %): the runner's gain is the squads' loss.
  - v `_m2` it lost: 37.9 % over 256 games (one seed), deaths 6.4 v 5.9. Sending Issac alone splits the twins.
  - What is left of the idea: islands by crystal (a quarter of all pure gem groups, reachable only that way), and
    Vendetta as the runner (one tile a turn), neither tested.

## 13. Engine probes: what the real engine does at the rule edges (10 Nov ~05:00; full tables in `mech.md`)

One scripted probe bot on hand-built maps, 13 scenarios, ~20 single games; all [measured] on the 5.0 engine. Probe
sources for re-runs: `~/tzunami_data/analysis_10nov/mech/`.

**Usable, ranked:**
1. **A boundary tribute cannot be interrupted.** A carrier with <= 10 gems starts the tribute as our last actor of a
   round we go second and sets a high priority the same turn; it completes as the first actor of the next round. A
   ready enemy stunner in range never got a turn. The control (started in a round we go first) was stunned and cancelled.
2. **A camp's last hit destroys the bag.** A carrier at 10 HP died to a wolf: its 14 gems vanished and the attacker
   got nothing, no gold either. A doomed carrier should end next to an awake camp as its nearest body; as attackers we
   must land the last hit ourselves.
3. **A stun always costs exactly one turn**, the victim's next, whether or not it had acted that round. A second stun
   before that lost turn is wasted; after it, it costs another turn. Rule: never stun a body whose stun buff shows
   duration >= 1; stagger stuns one round apart. (This withdraws §11 row 3's "stun before the victim acts" as a
   source of an extra lost turn: the double-turn part of row 3 still holds.)
4. **Enemy state is readable for visible enemies** through the public SDK: ability cooldowns, the lock / crystal it
   carries, items, gems, channel time left, its priority now and NEXT round, whether it is on its spawn. Not readable:
   its gold, its wards. So we can see who will act first next round, whether its stun is ready, and whether a carrier
   holds a lock.
5. **Locks.** Placing our lock cancels our OWN ally's tribute at that altar (check every lock build for this). A lock
   can be placed from 2 tiles through a wall without sight of the altar. Both teams can lock one altar; a second lock
   by the same team fails. A tribute attempt at an enemy lock is one hit and spends the basic attack; ranged bodies hit
   it from 3 tiles; attack-reset bodies hit it twice a turn (Vesper, Vendetta, Issac break a lock in 3 turns). Locks do
   not expire and are visible only with the altar tile in vision.
6. **The team that starts the round wins a same-round finish.** Both final tributes due in one round: the starter's
   completes first and the game ends.
7. **Camp ties go against team A.** At equal distance the camp hits the lowest champion id, so the team A body takes
   every hit. When we are team B, standing at equal distance to an enemy puts the camp on them.
8. **Vendetta's cluster chain.** Hit, reset, hit kills one 120-HP cluster tile a turn at 65 Strength and the kill
   re-arms the reset: 8 tiles in 8 turns. She is the natural cluster runner (§12.7).
9. **Ground spells need no vision** and the altar tile is a legal target: an area stun cast on the altar from 4 tiles
   stunned the carrier beside it and cancelled its tribute; radius 1 covers all 8 tribute tiles. (Prism's slot 1 is an
   area DAMAGE spell, her slot 0 stun is single-target; area stuns belong to champions we do not draft.)
10. **A ward placed through a wall gives sight for attacks across it**: basic attacks and a single-target cast landed
    across the wall for 7 rounds and the victim never saw the attacker.
11. **A capture can land inside a tribute channel**: bag 7, a 1-tick tribute started the turn before the capture
    landed, 14 banked.

**Corrections to earlier claims:**
- **The spawn tile is not a safe zone.** Attacks, casts and stuns all land on a body standing there, and Cassi died on
  her own spawn tile to a four-body burst inside one window. What holds: the heal is full at the body's own turn end,
  enemies cannot step on the tile (they can stand next to it), a recall lands on the first free spawn tile, and a home
  camp targets a body on a spawn tile (it was farmed from the tile at 980-1,000 HP). So the fortress (L10) saves a body
  that would die over several rounds, not one that can be burst in a single round: big bodies yes, Cassi no.
- Standing on a tile before the last kill gives no head start on the capture; the reward arrives 6 rounds after the
  body stands on the tile.
- The Tribute emblem saves nothing up to 30 gems (ticks = ceil(0.67 x base)).
- A ward on a camp's spawn tile does not delay its respawn.
- Body-blocking an altar is not a lever: 283 of 380 altars have all 8 adjacent tiles free; only 2 of 128 maps have an
  altar with <= 2.
- Marcella's stun needs attack, reset, attack in ONE turn at melee range (the reset cannot come first and the buff does
  not carry over). It also stuns camps; a stun on a camp skips one camp attack (60 HP saved on an elk).
- Live stats differ from `GameRules.md` (Cassi 100 Focus, Tavi 900 HP; `prism_focus_per_gem` is 1.5 in the SDK
  constants): bots must read live values.

## 10. Known not to work (do not repeat)

Fighting, holding or pushing more without a condition (commit_outnumber, engx open at parity, fedh, tdeny, rshop);
re-assigning income between bodies; item-line swaps; small early banks as a rule (sbank, bank small on one-altar maps);
hole-dash routing; more wards than `bushw`; the whole-team rush (every team that measured it lost) [web + measured].
