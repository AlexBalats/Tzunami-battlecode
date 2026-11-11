# Death anatomy: tz-32b v the UK band, contrasted with the top 3 (7 Nov)

Data: `tz32b_band` + `tz32b_s7` (our current bot v the band, 120 games, every game both sides) and `top3_6nov`
(150 games of the top 3 teams; "top team" = the label's team, "their opps" = whoever they played). `tz28_band` is used
only as a check. A **death event** merges the twins: Cassi and Issac die together and give one kill [rules], so one
twin death is one event and the gems are summed. Scripts are in `scratchpad/diag/deaths/` (listed at the end).
Tags: [measured] = counted from the decoded replays; [rules]/[code] = GameRules.md or bots/tz source; [guess] = an
inference.

## 0. Headline

- [measured] We have **5.42 death events a game** (twins counted as 2 bodies, that is 7.3 bodies), and the band has
  3.48. We lose **73.9 gems a game in bags**, the band 42.6. The two tz32b labels agree: 5.25 and 5.60 a game for
  us, 4.08 and 2.87 for the band. tz-28 was worse at 8.63.
- [measured] **The gap to the band is three causes:**

  | Cause | Us (a game) | Band (a game) |
  | --- | --- | --- |
  | Recall under fire | 1.32 | 0.24 |
  | Burst from high HP by a fed body | 0.75 | 0.11 |
  | Killed by camps | 0.61 | 0.19 |

  Together that is +2.14 deaths a game, more than the whole gap of +1.94, because we die *less* than the band while
  fleeing (0.87 v 1.36).
- [measured] **Bags:** deaths carrying 40 or more gems are only 0.49 a game but cost **51 gems a game, 69 % of
  everything we lose**. The band loses 0.24 such deaths and 23 gems.
- [measured] **Context:** the top team dies as often as we do (5.61 events a game). Its death rates per body by type
  are almost ours:

  | Type | Us | Top team |
  | --- | --- | --- |
  | Vesper | 0.79 | 0.79 |
  | HoR | 1.18 | 1.18 |
  | Marcella | 1.25 | 1.19 |
  | Vendetta | 0.98 | 0.91 |
  | Twins | 1.85 | 2.15 |

  The difference is that they kill 7.76 a game and we kill 3.48. So cutting deaths is only half of what separates us
  from the top 3; the other half is kills, which is outside this report. Against the band, which is who we must beat
  on 11 Nov, the excess deaths are concentrated and avoidable.

## 1. Method (what a death record holds)

For each champion that is alive in round snapshot D and dead in D+1 (`extract.py`):

- **Killer:** the enemy whose gold rose by at least 100 that round [rules: a kill gives 100 gold]; otherwise the last
  enemy that hit the victim.
- **Engagement start (es):** the earliest enemy-champion hit on the victim, chained backwards with gaps of at most 4
  rounds. Hits are basic attacks, plus damage, area and stun casts resolved to the champion standing on (or within 1
  of, for area) the target tile, using live positions step by step.
- **First hit:** the first champion-on-champion hit among bodies within 7 of the victim, from es−6 onwards.
- **Features at es:**
  - HP share, max HP, and the killer's max HP;
  - nearest ally, allies and enemies within 5, and both sides' summed max HP within 6;
  - map third (distance to the two spawns' centroids, split into thirds);
  - farming (hit a camp in the 5 rounds before), camps within 3.
- **The victim's own turns from es−3 to death:** moves toward, away or sideways relative to the nearest enemy, hits
  on a champion, hits on a camp, casts, recall start or cancel (step kinds 11 and 16), tribute, stun (buff type 1).
  Stun is [measured]: 63 of 87 stun casts were followed by buff type 1 on the target.
- **HP path** over the 10 rounds before death.

A **kept recall** is a turn with a recall start (11) whose next own turn has no cancel and no action. In our bot that
is exactly the channel: `play_turn` returns early on `is_recalling()` with no pre-recall flag [code]. Our bodies
pre-start a recall at the end of every turn (`end_turn`) and cancel it at the start of the next. The death-round turn
is excluded, because a body that died before its own turn still logs an end-turn or shop step.

**Causes**, taking the first rule that applies (`analyze.py: classify`):

1. **Camp / unattributed:** no champion hit in the last 5 rounds and no killer.
2. **Recall under fire:** a kept recall started from es−5 onwards.
3. **Tribute under fire.**
4. **Burst from high HP:** dead within 1 round of the first hit, with at least 70 % HP at es.
5. **Fled, chased down:** at least half of its turns after es stepped away.
6. **We engaged, lost:** the victim or an ally hit first.
7. **Caught, stood and fought:** everything else (the enemy hit first and the victim did not flee).

## 2. The anatomy (death events a game)

| cause | **ours** | band v us | top team | top's opps | ours: gems a game / bag | ours: alone / farming / outsized (≥1.9× max HP within 6) / outnumbered | ours: HP at es (median) |
|---|---|---|---|---|---|---|---|
| recall under fire | **1.32** | 0.24 | 1.91* | 1.56* | 10.8 / 8.2 | 41 % / 4 % / 46 % / 19 % | 0.89 |
| caught, stood and fought | 1.12 | 1.03 | 1.01 | 1.81 | **26.9 / 23.9** | 43 % / 7 % / 43 % / 19 % | 0.67 |
| fled, chased down | 0.87 | 1.36 | 0.99 | 1.55 | 8.4 / 9.7 | 46 % / 12 % / 36 % / 29 % | 0.82 |
| burst from high HP (≤1 round) | **0.75** | 0.11 | 0.35 | 0.90 | 6.7 / 8.9 | 41 % / 10 % / **93 %** / 18 % | 1.00 |
| camp / unattributed | **0.61** | 0.19 | 0.27 | 0.32 | 7.1 / 11.7 | 48 % / 44 % / – / – | 0.40 |
| we engaged, lost | 0.50 | 0.47 | 0.71 | 1.23 | 10.5 / 21.0 | 18 % / 8 % / 38 % / 12 % | 0.76 |
| unattributed champion kill (dash damage) | 0.20 | 0.01 | 0.22 | 0.17 | 1.8 / 8.8 | | |
| tribute under fire | 0.05 | 0.06 | 0.15 | 0.23 | | | |
| **total** | **5.42** | 3.48 | 5.61 | 7.76 | **73.9 gems** | | |

\* The top 3's "kept recall" counts are noisy. Their bots can idle with a recall running (47 % of their "kept
recalls" end neither home nor dead, even with no enemy within 12), so their recall row is an upper bound. For us and
for the band the detection is clean: 95 % and 92 % of the kept recalls with no enemy within 12 reach spawn.

**Engaged deaths of ours (554)** [measured]:

- **First hit:** the enemy hits first in 72 % (band 70 %, top team 58 %).
- **Engagement length:** median 3 rounds from the first enemy hit to death (band 4, top 4).
- **Hitters:** 1.60 enemies hit the victim on average (band 1.80, top 1.94).
- **Support:**
  - at es, no ally within 5 in 40 % (band 56 %, top 33 %);
  - nearest ally median 4 (band 7, top 3).
- **Size:** the victim's max HP is 0.56 of the killer's (median).
- **HP:** 0.87 at es (median); 22 % below 0.5.
- **Who closed the gap** in the 6 rounds before es: the enemy did (−3.2 tiles; the victim −0.6). We are hunted, not
  diving.
- **Stun:** 34 % had a stun on them during the engagement (top 45 %).
- **When:** 151 before r300, 288 in r300–800, 212 after r800.
- **Victims:**

  | Victim | Events |
  | --- | --- |
  | Twins | 222 |
  | Marcella | 125 |
  | HoR | 114 |
  | Vesper | 95 |
  | Vendetta | 95 |

- **Killers:**

  | Killer | Kills |
  | --- | --- |
  | Marcella | 151 |
  | Vesper | 126 |
  | HoR | 112 |
  | Vendetta | 93 |

**Where:** 82 % of our deaths are in the middle third and 6 % in theirs. Diving deep is not the problem [measured].

### 2a. Recall under fire (1.32 a game, the biggest excess)

- [measured] **At the recall start:**
  - HP median 0.46 (non-twins 0.23, twins 0.64);
  - **nearest enemy median 3 tiles, within 3 in 61 %, within 5 in 94 %;**
  - already hit by a champion before the recall in 62 %;
  - dead 3 rounds later (median).
- [measured] **Every kept recall of ours (6,131), by the nearest enemy at the start** (`recalls.py`):

  | nearest enemy | n | home | broken | died within 8 |
  |---|---|---|---|---|
  | 0–2 | 403 | 25 % | 35 % | **40 %** |
  | 3–4 | 555 | 32 % | 39 % | **29 %** |
  | 5–6 | 490 | 43 % | 41 % | **16 %** |
  | 7–8 | 588 | 84 % | 10 % | 6 % |
  | 9–11 | 602 | 91 % | 4 % | 5 % |
  | 12+ | 3493 | 95 % | 3 % | 1 % |

  24 % of our kept recalls start with an enemy within 6 (12 a game). The band: 13 % (6 a game), and at 5–6 tiles the
  band reaches home 88 % of the time (they chase; we do not).
- [measured] **The same situation, recall v walk** (`outcome.py`). These are turns with an enemy within 6, and the
  table gives P(death within 8 rounds) after each choice:

  | HP | start a kept recall | step away |
  |---|---|---|
  | < 0.3 | 56 % | 37 % |
  | 0.3–0.5 | 33 % | 12 % |
  | 0.5–0.7 | 23 % | 7 % |
  | ≥ 0.7 | 17 % | 3 % |
  | fed enemy within 6 | **51 %** | 8 % |

  Recalling is the deadliest choice in every HP band, and the gap holds for the band (52 % v 30 % below 0.3) and for
  the top 3. A recall is 5 turn ends and is cancelled by any damage [rules], so with an enemy within 6 it buys a
  standing target.
- [measured] **Low-HP contact:** in contact below 30 % HP, **43 % of our turns are recall channels or recall starts**
  (band 18 %). Our step-away share there is 48–54 % and our hit share 11–13 %; the band and the top 3 step away 59–63 %
  and hit about 19 %.
- [code] **Why the bot does it:**
  - The BREAK branch recalls on `!L.threat && !me.damaged && hurt`, and the hurt-recall path tests the same `L.threat`.
    `L.threat` is "within its range + 2", that is 3 tiles for a melee enemy: a 5-turn channel is started with a melee
    enemy at 4.
  - `act_home` recalls on `L.nearest > 7`, and `L.nearest` only counts enemies the body saw in the last 3 rounds.
- [guess] **The full-HP recalls with an enemy at 3:** vision is per body and bushes block it [rules], so many of these
  are probably enemies the body could not see.

### 2b. Burst from high HP (0.75 a game; band 0.11, top 0.35)

- [measured] **Who:** in 93 % of these deaths an enemy with at least 1.9× the victim's max HP was within 6, and the
  killer had **4.1×** the victim's max HP (median). Victims: Twins 47, HoR 18, Marcella 16, Vendetta 6, Vesper 3.
- [measured] **The killer was in view earlier:** **4 rounds before the first hit it was 7 tiles away (median), within
  8 in 76 %**; 1 round before, 5 tiles.
- [measured] **Exposure** (`fed.py`):

  | Enemy within d tiles | Us (rounds a game) | Top team | Band v us |
  | --- | --- | --- | --- |
  | ≥3× my max HP, d ≤ 8 | **120** | 65 | 19 |
  | ≥3× my max HP, d ≤ 4 | 16.8 | 12.8 | – |
  | ≥1.9×, d ≤ 8 | 308 | 218 | – |

  - Our risk within 4 of a ≥3× enemy: P(death within 2 rounds) is 21 %.
  - **Only 2 % of our rounds near a ≥3× enemy are farming rounds.** Keeping away from them costs almost no farming.
- [code] **Why the fed break comes too late:** it fires only within `reach_of(e) + fed_margin (2)`. `reach_of` drops
  abilities on cooldown, so a carry whose dash is cooling counts as reach range + 1, a 4-tile break. It also fires only
  on an enemy visible this turn.

### 2c. Camp deaths (0.61 a game; band 0.19, top 0.27)

- [measured] **Which camps** (`campdeaths.py`): 73 events. An awake camp had the victim in reach in 63 of them: golem
  20, monolith 20 (+5 shared), elk 14 (+10 shared). Victims: HoR 22, Cassi 21, Marcella 13.
- [measured] **How long:** the victim stood in a camp's reach for **10 rounds or more (median)**, having entered at
  **full HP** (median 1.00). In its last 6 turns it made **4.2 recall starts** and only **1.6 steps away**.
- [rules] **Why the recalls fail:** camp damage cancels a recall, so every attempt is wasted while in reach.
- [measured] **Example:** a HoR (1,000 HP) wandered within 1–4 tiles of an awake monolith (strength 200, range 5
  [rules]) and lost exactly 20 % each round for 5 rounds while pre-recalling. It never left its reach.
- [code] **What exists today:** `act_bank` has the right reflex (step to the neighbour tile with the fewest awake camps
  in reach). It runs only on the way to an altar.

### 2d. Big bags (0.49 deaths a game with ≥40 gems, 51 gems a game, 69 % of the gems we lose)

- [measured] **Who and how:** causes are stood-and-fought 21, recall 11, we-engaged 8. Victims: Vesper 19, Vendetta
  15, Twins 12. **Our big-bag victims were at 0.59 HP when first hit (median); the band's were at 0.96.**
- [measured] **Risk with a bag of 40 or more off spawn** (`bag.py`), as P(death within 15 rounds):

  | Situation | Us | Band | Top team |
  | --- | --- | --- | --- |
  | Enemy within 8, HP ≥ 0.7 | 4.0 % | 2.4 % | 2.6 % |
  | Enemy within 8, HP < 0.7 | 13.7 % | 10.1 % | 11.4 % |
  | No enemy within 8, HP < 0.7 | 1.8 % | 0.2 % | 0.8 % |

  We spend 59 rounds a game with a bag of 40+ below 0.7 HP; 26 of them have an enemy within 8.
- [code] **What exists today:** `carry_safe` only applies to the top carry (`taker_rank >= 6`) and is set to 1.0
  (off).

## 3. The same situations for the top 3: what they do instead

**Exposure per 1,000 body-rounds off spawn** (`analyze.py` exposure; P(die) = death within 10 rounds of entering the
situation):

| situation | ours (P die) | band (P die) | top team (P die) | top's opps (P die) |
|---|---|---|---|---|
| any contact (enemy within 5) | 91 (7 %) | 96 (4 %) | **152 (5 %)** | 167 (7 %) |
| alone v 2+ (no ally within 5) | 6.1 (**19 %**) | 10.6 (12 %) | 10.3 (15 %) | 14.2 (20 %) |
| outnumbered by 2+ | 7.6 (**20 %**) | 15.1 (11 %) | 16.0 (15 %) | 22.7 (19 %) |
| outsized (≥1.9× within 5) | 21.9 (15 %) | 6.9 (23 %) | 23.0 (14 %) | 33.7 (17 %) |
| farming with an enemy within 5 | 1.6 (7 %) | 5.7 (3 %) | 7.4 (4 %) | 8.7 (6 %) |

[measured] **What the top 3 do differently**, in order of size:

1. **They fight more, closer together.**
   - They are in contact 60 % more than we are, yet die less per contact.
   - In contact their nearest ally is within 3 in 61 % of rounds (ours 56 %, band 44 %), and they are alone in 26 %
     (ours 32 %).
   - Near a fed enemy (≥1.9× within 4–8), they have an ally within 3 in 67–71 % of rounds; we have one in 60–65 %.
2. **At low HP they walk and hit; they do not channel.** P(step away) by HP share:

   | HP | Top team | Us |
   | --- | --- | --- |
   | < 0.2 | 59 % | 48 % |
   | 0.2–0.3 | 63 % | 54 % |
   | 0.3–0.4 | 50 % | 52 % |
   | 0.4–0.5 | 42 % | 50 % |
   | 0.8–1.0 | 27 % | 32 % |

   - Their curve crosses 50 % at about 0.35–0.4 HP and keeps falling above it. Ours flattens at 50 % below 0.5,
     because recall channels replace the steps.
   - They hit in 19 % of their contact turns below 0.3 HP; we hit in 11–13 %.
   - At full HP we step away *more* than they do (32 % v 27 %).
3. **Their recalls in contact die less:** P(death within 8 rounds) after starting a kept recall with an enemy within 6:

   | HP | Top team | Us |
   | --- | --- | --- |
   | ≥ 0.7 | 9 % | 17 % |
   | 0.5–0.7 | 16 % | 23 % |
   | 0.3–0.5 | 26 % | 33 % |
   | Fed enemy within 6 | 35 % | 51 % |

4. **Fed contact: they trade back.** Their fed-contact turns are 36 % step away, 11 % hit and 13 % recall; ours are
   44 %, 5 % and 8.5 %. They spend half as many rounds as we do within 8 of a ≥3× enemy (65 v 120 a game). Their
   per-round risk there is the same as ours (P(death within 2 rounds) 5.0 % v 4.9 %), so the gain is the exposure.
5. **Their bags are safer:** with a bag of 40+ and an enemy within 8, P(death within 15 rounds) is 2.6 % at HP ≥ 0.7
   (ours 4.0 %). They carry 40+ for 507 rounds a game, we for 299.

## 4. Changes most likely to cut deaths without cutting farming

| # | Change | Where (bot.cpp) | Decision rule (thresholds from §2–3) | Deaths it addresses | Farming cost |
|---|---|---|---|---|---|
| 1 | **No recall with an enemy near; walk first** | `do_recall()`, the single choke point, so it covers the BREAK branch (`!L.threat && !me.damaged && hurt`), the hurt-recall path, `act_home` (`L.nearest > 7`), `act_bank`'s camp escape and the kept `pre_live` recall | Refuse (return false, so the caller falls through to `act_flee` / `step_field(home_field)`) when any of these holds: an enemy remembered within the last 5 rounds is within **7** (Chebyshev, enemies on their spawn excepted); I lost HP to a champion in the last 2 turns; an awake camp has me in reach. Also cancel a running pre-recall (`release_pre`) under the same test. Data: kept recalls from 7+ tiles reach home 84–95 % of the time, from 5–6 tiles 43 % and from ≤4 tiles 25–32 %. Stepping away instead of recalling cuts P(death within 8) from 56/33/23/17 % to 37/12/7/3 % by HP band. | recall under fire: 1.32 a game (band 0.24). Expected −0.6 to −0.9 a game [guess on transfer; the rates are measured] | none: recalls from 7+ tiles are untouched; the rest walk home, which is 5 turns either way |
| 2 | **Fixed-radius fed break for ≥3× enemies** | `play_turn`, the fed-break loop (`cheb(e.pos, me.pos) > reach_of(e, i) + fed_margin`), plus `choose()` / `farm_vt` pricing (`big_k`) | For an enemy with **≥3.0× my max HP**: break within **8** tiles whatever its cooldowns, and use the posted `comms::big` position (fresh within 10 rounds) when it is not visible. Keep reach + 2 for the 1.9–3× tier and keep the `fed_gang` exception. In `farm_vt`, price ×`big_k` for groups within 8 of a posted ≥3× body. Data: killers were 7 tiles away (median) 4 rounds before the first hit, within 8 in 76 %. We spend 120 rounds a game within 8 of ≥3× enemies (top 3: 65); 2 % of those rounds are farming. | burst from high HP: 0.75 a game (band 0.11), 93 % by ≥1.9× and a median 4.1× ratio. Expected −0.3 to −0.5 [guess] | ~2 % of 120 rounds a game, about 2–3 farming rounds |
| 3 | **Leave awake camps' reach before anything else** | a new early block in `play_turn` (after `sense_me`, before the stance), generalising `act_bank`'s `inreach` step over `awake_snap()`; plus the `do_recall` guard from #1 | If I took damage this turn, no enemy champion is in reach, and awake camps reach me: unless I am that group's farmer with HP > 4 × (the summed strength of camps in reach) × (1 − durability), step to the neighbour tile with the fewest camps in reach (tie-break on `dist_home`). Never start a recall in reach (damage cancels it [rules]). Data: 63 of 73 camp deaths had an awake golem, monolith or elk in reach, for 10+ rounds, entered at full HP, with 4.2 recall starts and 1.6 steps away in the last 6 turns. | camp: 0.61 a game (band 0.19, top 0.27). Expected −0.3 to −0.4 [guess] | none for the group's farmer above the HP test; others are not farming that camp |
| 4 | **Bag-aware stance: a carrier with 40+ gems does not take even fights** | `assess()`: extend the `carry_safe` bias from `taker_rank >= 6` to any body with `me.gems >= 40` and set `carry_safe` to about 0.7. `play_turn` contact block: with gems ≥ 40 and HP < 0.7, BREAK unless `execute_target()` lands. `choose()`: price BANK above FARM when gems ≥ 40 and HP < 0.7. | Data: big-bag deaths are 0.49 a game and cost 51 gems (69 % of our bag losses); the band's are 0.24 and 23 gems. Our victims were at 0.59 HP when first hit; the band's at 0.96. With an enemy within 8, P(death within 15 rounds) is 4.0 % at HP ≥ 0.7 and 13.7 % below (band 2.4 % / 10.1 %, top 2.6 % / 11.4 %). | about −0.15 deaths but **about −15 to −25 gems a game** [guess] | the 59 rounds a game a 40+ bag spends below 0.7 HP turn into banking trips, which also score |
| 5 | **When refused a recall at low HP: step, then shoot** | `play_turn` BREAK branch / `act_flee` (with `break_act`, `kite`) | Below 0.3 HP in contact, after #1 refuses the recall: take `find_escape()`'s step if one exists, then `weakest_in_reach()` swing or cast (the top 3 hit in 19 % of these turns, we in 11–13 %; they step away 59–63 %, we 48–54 %). | part of #1's 1.32 a game, and the low-HP share of "caught, stood" | none |

**Tuning order.** #1 and #3 are bug-shaped and have no farming cost: do them first. #2's radius (8) and ratio (3.0)
should go into `value.h` (`fed_far_k`, `fed_far_r`) for SPSA. #4 trades a little farming time for banking. Judge
on 4 seeds, all maps and both sides, as usual.

**Not proposed.** The twins are 1.85 death events a game, and half of the burst victims. The top team's twins die
2.15 a game, so this is a draft choice, not a bot.cpp defect; it stays out of these changes. `twin_tether` is 0, so
the twins are not recalling together by design.

## 5. Caveats

- **What counts as a hit:** dash damage (cast kind 6) is not counted, so 0.20 a game of our deaths are "unattributed
  champion kills". Area hits use radius 1 around the target tile [guess on the radius].
- **The cause rules are heuristics.** A death fits one bucket; flags such as alone, farming and outsized overlap.
- **The top 3's recall row is noisy** (see the note under the §2 table). Their behaviour rows (steps, hits, ally
  distances) are clean.
- **Causality:** the outcomes after "recall v step away" are conditional rates, not controlled experiments. Bodies
  that recall may already be in worse spots, so the expected cuts above are [guess]. Only an A/B decides.
- **Bushes:** the bot's own view is unknown (vision is per body and bushes occlude [rules]). The distances here are
  true positions, which is why #1 and #2 use memory (`seen_round` within 5 rounds, and `comms::big`), not
  visible-now enemies.

## Scripts (`<scratchpad>/diag/deaths/`)

- `extract.py LABEL OUT.json`: death records (both teams) plus exposure and contact-response rows.
- `analyze.py A.json[+B.json]`: the anatomy, the cause table and the exposure tables (outputs in `out_ours.txt`,
  `out_top3.txt`).
- `recalls.py LABEL…`: every kept recall, by the nearest enemy distance (`out_recalls_*.txt`).
- `outcome.py DEATHS.json LABEL…`: action in contact against P(death within 8), and the killer's distance before the
  first hit (`out_outcome_*.txt`).
- `fed.py LABEL…`: fed exposure by distance, bag exposure, deaths per body by type (`out_fed_*.txt`).
- `campdeaths.py`, `bag.py`: camp deaths by camp kind; big-bag risk by HP and enemy distance.
