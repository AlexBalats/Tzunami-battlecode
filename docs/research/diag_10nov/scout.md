# scout: what the top does against the same band that we do not (10 Nov, replay analyst)

**Question.** Against the same six UK band teams, what do the top teams (stellar best girl, Mite, Intercontinental
Fish, BattleCats; plus Ad Astra and Vvvvv in `uk3band`) do that we do not, that FINDINGS.md has not covered, and that
fits in a few hours as a rule in `bots/_m2`? Look where the score is decided (the banked-gem timeline), then pick the
2-3 largest new gaps.

**Short answer, ranked by expected gem-share gain.**

1. **Threat bank (new, the largest clean gap).** A carrier with 20+ gems that comes within 6 tiles of an altar while
   an enemy is within 12 starts a tribute within 10 rounds **0.31** of the time for us. The rate is **0.64** for the
   top and **0.62** for the band against us. With no enemy near we are level (0.77 v 0.80). The gap holds for all six
   of our champions, every map class, both phases and both of our builds. Our carry episodes end in death 12.9 % of
   the time (top 3.5 %, band v us 4.2 %). We lose 50 gems a game in bags by r600; the top loses 17 [measured]. **Rule:**
   in that state, bank: raise `bank_rate()`, end the WORK hold, and have a breaking carrier walk to the altar instead
   of home.
2. **Escape recall at 4-6 tiles (new).** The top finishes **3.5** recalls a game that started with the nearest enemy
   4-6 tiles away; the band v us finishes 2.2 and we finish **0.6**. At 7+ tiles we are level [measured]. Our
   `recall_unsafe()` refuses any recall with an enemy seen within 9 tiles in the last 8 rounds, and our hurt recalls
   wait for HP < 25 %. The top starts these at ~45 % HP. A hurt body (HP < 50 %) with the enemy at 4-6 tiles reaches
   home within 30 rounds 0.56 of the time for us against 0.66 for the top and 0.67 for the band v us. It dies within
   30 rounds 0.16 of the time against 0.11 and 0.13 [measured]. **Rule:** allow the recall when no visible enemy can
   reach the body on its next turn, from HP < 50 %. Keep the existing dth-2 abort.
3. **The frame and the negatives (where NOT to look).** The banked-gem gap opens steadily from r100. No single event
   opens it. Banking efficiency is level for all four sides (0.75-0.78 of collected gems banked). 84 % of the r600
   swing is capture income (the mid, already covered by suppression.md / early_income.md / respawn.md) and 16 % is bags
   lost to kills. The strongest single precursor of a bad 30-round window is one of our carriers dying with 20+ gems,
   which is what rule 1 attacks. Six of the orchestrator's candidate areas measured level or small. They are listed
   in §5 with numbers.

Expected size, all of it [guess] built on the measured rates: rule 1 is about +0.01 to +0.02 gem share (+1.5 to +3 win
points on FINDINGS §0's scale), and rule 2 about +0.005 to +0.01. Neither touches the main gap (mid capture income).

Data: decoded band replays already on disk. Top: `top_v_band` (119) + `uk3band` (24) = 143 games. Us: `tzmega_big`
(150) + `n47_tz116` (150) = 300 games, plus `a1_m2` (119) and `tiny_m2` (120) as class checks. "Opp-matched" = our
per-opponent means weighted by the top's opponent mix (Kungarna 38, policy wonk 51, Claudus 24, :3 15, QS2isLaw 10,
RLP 5). Rounds r1-600 unless stated. Caveat [guess]: the top played the band's 7 Nov bots; we played its 8-10 Nov bots.

## 1. Where the score is decided: the banked-gem timeline [measured, `timeline.py`, `window.py`]

| Banked gems, focus minus band (opp-matched) | r100 | r150 | r200 | r300 | r400 | r600 | r900 |
|---|---|---|---|---|---|---|---|
| Top v band (143) | +14 | +26 | +40 | +88 | +126 | +245 | +319 |
| Us v band (300) | -7 | -22 | -40 | -83 | -125 | -198 | -292 |

- **The gap is a steady rate, not an event.** It is mirror-symmetric: from r100 it grows at about 0.3-0.4 gems a
  round for the top and against us.
- The last round the eventual loser was level or ahead has a median of r157 in the top's wins (n 116; quartiles r72 /
  r436). In our losses the median is r230 (n 234; quartiles r101 / r597).
- **Gem flow to r600** (opp-matched; a capture is a rise in a living body's bag with no enemy death that round):

  | Per game | Captured | Stolen by kills | Banked / collected |
  |---|---|---|---|
  | Top | 607 | 66 | 0.76 |
  | Band v top | 389 | 18 | 0.75 |
  | Us | 392 | 26 | 0.76 |
  | Band v us | 591 | 50 | 0.78 |

  **Conversion is level for every side**, so altar choice, tribute success and bank-trip shape are not where the gap
  is (§5 has the direct checks). The swing is about 84 % captures (top +218, us -199) and 16 % kill steals (top +48,
  us -24).
- **30-round windows, r60-600** (5,200 of ours, 2,422 of the top's). The next 30 rounds go -40 or worse in 24 % of our
  windows and 11 % of the top's; they go +40 or better in 11 % of ours and 21 % of the top's.
  - Before our worst windows (n 1,230), against all windows:
    - our bag lost 5.8 v 2.6 gems;
    - our deaths 0.25 v 0.20;
    - band body-rounds in the mid 41 v 35;
    - band tribute starts 0.98 v 0.76.
  - Before the top's best windows (n 508):
    - band deaths 0.42 v 0.28;
    - band bag lost 7.6 v 3.5;
    - the top's mid body-rounds 49 v 42.
  - The single strongest event: one of our deaths with 20+ gems is followed by a 30-round change of **-43** (v -9
    with none). A band death with 20+ to the top is followed by **+44** (v +11).
- So the event-level gap is **bags**: who dies carrying. Everything else is a rate (the mid, covered elsewhere).

## 2. Finding 1: the threat bank [measured: `carry.py`, `carry3.py`, `carry4.py`, `carry5.py`, `carry6.py`, `carry7.py`, `robust.py`]

**Carry episodes** (a body's bag reaches 20 until it falls below 20 by a tribute, or the body dies; opp-matched):

| Per game, r1-600 | Episodes | Banked | Died | Rounds held | Bag lost to deaths |
|---|---|---|---|---|---|
| Top | 10.3 | 0.75 | **0.035** | 58 | **17** |
| Band v top | 7.1 | 0.66 | 0.156 | 69 | 60 |
| Us | 6.8 | 0.63 | **0.129** | 77 | **50** |
| Band v us | 10.8 | 0.74 | 0.042 | 63 | 23 |

**The trigger.** A body carrying 20+ is within 6 tiles of an altar for the first time in the episode. The table gives
P(it starts a tribute within 10 rounds), raw counts, with n in brackets:

| Nearest enemy at that round | Top | Band v us | Us |
|---|---|---|---|
| none within 12 | 0.80 (656) | 0.78 (1,222) | **0.77** (821) |
| 9-12 tiles | 0.77 (293) | 0.71 (744) | **0.42** (386) |
| within 8 | 0.55 (399) | 0.55 (1,055) | **0.24** (620) |
| I am nearer the altar than every enemy | 0.74 (376) | 0.70 (970) | **0.47** (432) |
| an enemy is as near the altar or nearer | 0.52 (316) | 0.52 (829) | **0.19** (574) |
| an enemy within 2 of the altar | 0.40 (116) | 0.43 (296) | **0.13** (244) |

- **Every one of our champions does it** (enemy within 12):
  - ours: Vesper 0.32 (419), Marcella 0.26 (154), Vendetta 0.33 (161), HoR 0.33 (115), Cassi 0.32 (88), Issac 0.26 (69);
  - the top's non-Prism bodies: 0.60-0.73;
  - with no enemy near, ours are 0.70-0.89 against the top's 0.76-0.91.
  - The gap is the same at r<=300 (0.31 v 0.65) and r>300 (0.31 v 0.63), and for 20-39-gem bags (0.32 v 0.65) and
    40+ (0.29 v 0.62).
- **Both builds and every class base** (the first enemy sighting within 8, altar within 6, tribute within 10 rounds,
  bootstrap 95 % CI):
  - tzmega_big 0.32 [0.26, 0.39];
  - n47_tz116 0.34 [0.25, 0.41];
  - a1_m2 0.34;
  - tiny_m2 0.30;
  - against top 0.52 [0.46, 0.58] and band v us 0.54 [0.51, 0.58].
  - By class, top v us: tiny 0.53 v 0.35, one altar 0.37 v 0.29, other 0.56 v 0.32.
  - By opponent, top v us: Claudus 0.58 v 0.36, QS2isLaw 0.53 v 0.30, RLP 0.50 v 0.24, Kungarna 0.54 v 0.31, policy
    wonk 0.53 v 0.19. The exception is :3, 0.30 (n 33) v 0.45 (n 114).
- **What comes first in the 15 rounds after the first enemy sighting** (within 8) of a carry episode:
  - altar within 6: a tribute 0.55 (top) / 0.56 (band v us) / **0.38** (us);
  - altar 7-12: a tribute 0.33 / 0.34 / **0.13**;
  - the episode then ends in death 0.050 / 0.039 / **0.110** (altar within 6) and 0.091 / 0.067 / **0.175** (7-12).
    Our carriers take 45 rounds from that sighting to end the episode; the top takes 32 and the band 29.
- **What our non-banking carriers do instead.** Over the next 10 rounds, in our 694 cases:
  - camp hits 13 % of rounds, champion hits 8 %;
  - steps toward the altar 28 %, steps toward home 20 %, other steps 22 %, standing still 9 %.
  - The top's non-bankers do the same mix: the difference is how many bank at all.
  - Not locks: these carriers hit a lock in 4 % of cases.
  - Not contact: the enemy was within 5 in only 24 % of them.
  - **So the goal choice is what keeps them off the altar.**
- **Is banking under threat safe?** Death within 30 rounds after the trigger, enemy within 8: top 0.073, us 0.071.
  The top banks twice as often at no higher death rate. Damage does not interrupt a tribute; stun, death or a lock
  does [rules]. With an enemy within 4 of the altar, our tributes still complete 0.71-0.86 of the time (`altar.py`).

**Mechanism [read in `bots/_m2/src/bot.cpp`].** Nothing in the code refuses the altar under threat; the bank simply
loses the goal choice:
- `bank_rate()` (bot.cpp:791) adds only `gems x bank_threat (0.01) x min(3, threat)` for a bag at risk. A 40-gem bag
  gains at most +1.2. The bonuses that do decide a bank are +20 (`bag_cap`, the runner, roles), and `bag_cap` = 0
  (value.h:282).
- With an enemy in sight, a held WORK job is not re-planned (`plan_stale()`, bot.cpp:1551, p1 bit 1). The WORK hold
  (bot.cpp:4939-4970) ends for a carrier only when it is out-sized (`work_bag_stop`, bot.cpp:4949).
- A breaking body runs home: `act_flee()` (bot.cpp:3174) scores tiles by `-0.5 x dist_home`. That is true even when
  an altar is 3 tiles away and no enemy stands nearer to it.

**Rule (one switch, e.g. `tbank`, bits):**
- **Trigger:** `me.gems >= tb_bag` (20); an enemy off its spawn seen this round within 12; the nearest reachable altar
  `a` at walk `d_a <= tb_r` (8); HP >= 30 %; and `a` is safe:
  - no visible enemy within 2 of `a`;
  - and either no visible enemy nearer `a` than `d_a - 1`, or (bit 8) any carrier when our live HP within 8 is >= theirs.
- **bit 1, `bank_rate()`:** add +20 under the trigger, the same size as the `bag_cap` bonus. The threat term stays.
- **bit 2:** under the trigger, the WORK hold ends (`real = true` at bot.cpp:4949) and `plan_stale()` does not keep
  the held job (bot.cpp:1555).
- **bit 4, the BREAK branch** (bot.cpp:5481): under the trigger, and when I am nearer `a` than every visible enemy,
  call `act_bank()` instead of `act_flee()`. The body then walks there and tributes on arrival.
- Never place our own lock on that altar while an ally is tributing there (mech.md: our lock cancels an ally's tribute).
- **Zero-code first test:** `bag_cap=999 bag_near=20`. This turns on the existing "+20 with 20+ gems and an altar
  within 6" (bot.cpp:820) with no enemy condition. Our rate with no enemy near is already level, so it mostly acts on
  the threat case. It does not pass the WORK hold or the contact stance, which bits 2 and 4 do.
- **KPIs** (re-run `carry3.py` / `carry.py` with `SCOUT_US=<label>` after `ext.py <label>`):
  - P(tribute in 10 | 20+, altar within 6, enemy within 12): 0.31 -> >= 0.55;
  - carry-episode death: 0.129 -> <= 0.07;
  - bag lost per game r1-600: 50 -> <= 30;
  - deaths within 30 rounds of the trigger must not rise (0.07).
- **Expected gain [guess]:**
  - Converting a third of our 3.35 triggers a game to banks: kept episodes end in death about 16 % of the time, so
    about 0.18 fewer carrier deaths a game x ~50 gems.
  - Those gems are banked, and the band does not get them (the killer takes the bag [rules]): about 20 gems of swing
    a game, +0.01 to +0.02 share.
  - It also removes the strongest single precursor of our bad windows (§1).

## 3. Finding 2: the escape recall at 4-6 tiles [measured: `recall2.py`, `recall4.py`, `hurt.py`, `robust.py`]

Completed recalls (a jump onto an own spawn tile; the channel start is the last recall start with no cancel or action
after it), per game, by the nearest enemy at the start (opp-matched):

| Nearest enemy at the channel start | Top | Band v top | Us | Band v us |
|---|---|---|---|---|
| within 3 | 0.70 | 0.27 | 0.36 | 0.41 |
| **4-6** | **3.47** [2.91, 4.04] | 2.55 | **0.60** [0.48, 0.73] | 2.19 [1.95, 2.43] |
| 7-9 | 3.15 | 2.72 | 3.39 | 3.24 |
| 10+ | 16.5 | 11.4 | 18.8 | 13.3 |

- At 4-6 tiles, about two thirds of the top's arrivals start below 50 % HP (2.17 of 3.47), at a mean HP of 0.45
  and a mean bag of 17. Ours start at a mean of 0.57.
- Deaths inside a kept recall channel are rare for everyone: us 0.21 a game, top 0.08 (`recall2.py`).
- **Hurt bodies** (HP < 50 %, nearest enemy 4-6, not on spawn, r60-600):

  | Hurt bodies, enemy at 4-6 | Top | Band v us | Us |
  |---|---|---|---|
  | n | 912 | 1,475 | 1,758 |
  | home within 30 rounds | 0.66 | 0.67 | **0.56** |
  | died within 30 rounds | 0.11 | 0.13 | **0.16** |

  - By class, top v us: tiny maps home 0.66 v 0.49, died 0.11 v 0.17; one altar home 0.70 v 0.51, died 0.13 v 0.18.
  - All six opponents: the top finishes 2.75-6.9 recalls a game from 4-6, we finish 0.38-0.74.
- With the enemy within 3, we die more as well: died within 12 rounds 0.35 v the top's 0.24, recalled 0.09 v 0.22
  (`hurt.py`). A recall there is not the answer: the dth-2 abort is right to cancel it.

**Mechanism [read in `bots/_m2/src/bot.cpp`].**
- `recall_unsafe()` (bot.cpp:4266) refuses any recall with an enemy seen in the last `dth_rg_age` = 8 rounds within
  `dth_rg_r` = 9 tiles (value.h:491-492). It came from an older study, "kept recalls from 7+ tiles reach home 84-95 %,
  from <= 4 tiles 25-32 %".
- The hurt recalls need HP < `hp_floor` = 0.25 (BRKREC bot.cpp:5488, HURTREC bot.cpp:5530; value.h:35).
- The abort already exists: `dth & 2` (bot.cpp:4810) cancels a running recall when a visible enemy is within its
  reach + 1.
- The top and the band start recalls at 4-6 tiles and 45 % HP, and the enemy usually does not follow: the band
  finishes 2.2-2.6 such recalls a game against both us and the top.

**Rule (switch, e.g. `escrec`):**
- **bit 1, the escape recall:** HP < `er_hp` (0.5); not on home, home walk > 6; no camp in reach; and every visible
  enemy (off its spawn) is beyond `reach_of(e) + 1` and at least 4 away. Then `do_recall()`. Put it in the BREAK
  branch before `act_flee()`, and in the HURTREC test with `er_hp` in place of `hp_floor`.
- **bit 2:** `recall_unsafe()` uses the same reach test (enemies seen this round), not the 9-tile / 8-round memory.
- The dth-2 abort stays: when an enemy closes into reach + 1, the body cancels and flees with no turn lost (the cancel
  and the turn's action fit in one turn [rules]).
- **Zero-code first test:** `dth_rg_r=4 dth_rg_age=1`. This opens the existing recall paths to enemies 5+ tiles away.
  It does not lower the 25 % HP trigger, which bit 1 does.
- **KPIs:**
  - completed recalls from 4-6: 0.6 -> >= 2 a game (`recall4.py`);
  - hurt at 4-6, died within 30: 0.16 -> <= 0.13; home within 30: 0.56 -> >= 0.64 (`robust.py`);
  - deaths in kept channels must stay < 0.3 a game (`recall2.py`).
- **Expected gain [guess]:** about 0.2-0.3 fewer deaths a game (5.9 hurt-at-4-6 events x 0.03-0.05), with bags of
  ~15, plus a heal and a shop sooner. About +0.005 to +0.01 share. Local games will show little: the mechanism needs
  the band's habit of not chasing a recaller, so judge it on the band.

## 4. Smaller, consistent with known levers [measured, `altar.py`, `carry.py`]

- **Carriers (10+) killed within 6 of an altar without a tribute start (on the way in):**

  | Map class | Us | Top | Band v top |
  |---|---|---|---|
  | One altar | 0.53 a game, bag 97 | 0.24, bag 35 | 0.71, bag 53 |
  | 2+ altars | 0.34, bag 41 | 0.18, bag 33 | 0.52, bag 37 |

  This is FINDINGS §3's "bank at ~30, never above 80" plus rule 1. It is not a separate rule.
- **Far carriers.** With an enemy sighted and no altar within 12 (1.3 a game), our carry episodes end in death 0.25
  of the time; the top's 0.07, the band v us 0.10. The first action does not separate us: a recall home 0.09 v 0.14,
  a walk 0.07 v 0.04. **No clean rule found.**

## 5. Checked and NOT levers (negative results) [measured]

| Candidate (from the brief) | Top | Us | Verdict |
|---|---|---|---|
| Captures stolen: the capturer's side landed < 30 % of the hits on the group in the 60 rounds before (`steal.py`) | steals 18 gems a game of the band's work; the band steals 7 of the top's | steals 8; the band steals 16 of ours | 2-3 % of capture gems, about 10 gems net. Not a lever |
| Clear -> capture (`clear.py`) | 38.0 clears a game, 95 % captured by the clearer, lag 4.8, 4 % left uncaptured 60 rounds | 31.8, 95 %, lag 5.5, 1 % | Level. The clear gap is the mid: 12.0 v 5.7 (own zone 23.6 v 23.9). Covered |
| Bag targeting: 2+ enemies within 3, bags differ by 10+ (`probe.py`) | picks the bigger bag 0.45 (chance 0.44) | 0.47 (0.43) | Nobody targets bags. Lowest-HP choice is level too (0.60 v 0.62) |
| Hunting carriers: an enemy within 6, hit within 5 rounds (`hunt.py`) | 20+ bag 0.29, others 0.28 | 0.14 v 0.16 | Nobody hunts bags. The top is more aggressive with everyone (FINDINGS §5) |
| Lone band body (no mate within 6, 2+ hunters within 6), kill within 10, by our live-HP ratio (`lone.py`) | <2: 0.03, 2-4: 0.17, >=4: 0.43; 1.08 kills a game | 0.02 / 0.12 / 0.34; 0.44 a game | Conversion per state is close. The gap is the ratio mix (size) and the count (7.1 v 5.7). Covered by support_size / §12.4 |
| Band invasions of our third (`zones.py`) | entries 1.16 (r60-150) / 1.72 (r151-300); per entry the band gains 2.2-2.7 gems and the invader dies 0.09-0.15 | 1.63 / 2.60; 2.9-3.7 gems, 0.06-0.08 | Per-entry outcomes are close, about 3-5 gems a game. The cause is placement: the top keeps 2.04 bodies in the mid at r60-150 (us 1.53) and 2.70 at home (us 3.29). Mid ownership, covered |
| Altar choice on 2+-altar maps (`altar.py`) | nearest altar 0.86; tributes complete 0.97 | 0.88; 0.98 | Level. The top tributes more often (17.8 v 10.5 a game, same bag ~32): that is income |
| Altar bag denial (tributes under an enemy, `altar.py`) | 9 % of starts with an enemy within 4 of the altar; 0.83 complete | 2 %; 0.86 | Rare and level. One-altar maps: a1_reverse.md |
| Recall deaths in a kept channel (`recall2.py`) | 0.08 a game | 0.21 | Small. The recall gap is rule 2 (we do not start them), not deaths in them |
| Time budget r60-300 (`budget.py`) | home zone 650 body-rounds, mid 486 | 813, 367 | At home we spend +52 camp-hit rounds for the same own-zone clears, +81 walking, +28 still: the mid gap again, covered |

Not re-measured (covered): first recall and shop timing and first buy (early_income.md, top_tricks.md,
top5_fresh.md), ward placement (vision.md), contested mid respawns (suppression.md, respawn.md).

## 6. Caveats

- Replays show what bodies did, not why. The code paths named in §2 and §3 are the ones that fit the measured
  behaviour; I did not trace a live turn [guess on the exact share each path causes].
- The top's games are against the band's 7 Nov bots and ours against 8-10 Nov bots [guess: the band changed little].
- The share estimates are back-of-envelope [guess]. Measure the KPIs on the band before trusting them.

## Scripts (`~/tzunami_data/analysis_10nov/scout/`, `python3 -I`, one at a time)

- `ext.py LABEL..` writes compact per-game pickles (about 1 min for all 6 sets). Set `SCOUT_OUT` to the pickle folder;
  `lib.py` defaults it to this session's scratchpad, which is deleted at the end, so re-run `ext.py` first.
- Every script takes `SCOUT_US` / `SCOUT_TOP` (comma label lists) to compare a new build's band games.
- Frame: `timeline.py`, `window.py`, `early.py`.
- Rule 1: `carry.py`, `carry2.py`-`carry7.py`, `robust.py`.
- Rule 2: `recall2.py`, `recall4.py`, `hurt.py`, `robust.py`.
- Negatives: `steal.py`, `clear.py`, `probe.py`, `hunt.py`, `lone.py`, `zones.py`, `altar.py`, `budget.py`.
- `recall.py` and `recall3.py` are superseded. Their kept-channel counts mix in stunned pre-started recalls (every
  team pre-starts recalls); use `recall2.py` / `recall4.py`.
