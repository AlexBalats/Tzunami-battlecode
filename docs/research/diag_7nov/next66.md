# next66: the biggest remaining lever for tz-66 against the UK band (8 Nov)

**Data.**
- `tz66_big`: tz-66 against the six band teams, 150 games, all decoded.
- `top_v_band`: the top teams against the same six, 119 games (stellar best girl 33, Mite 33, Fish 23, BattleCats 30).
  Every top row is reweighted to tz-66's opponent mix (or to the class's mix) unless marked otherwise.
- `tz55_big`: a paired check.
- Classes come from 27 band labels on the same 150 games (`*_big` + `big32`): won by tz-66 **32**, swing (won by some
  other build) **57**, never won **61**. Four wins are tz-66's alone.

**Rules followed.** I read only `bots/tz` (our code). I read no other team's code and no v93 code. I ran no games or
judges and edited no bots. Light python only.

**Scripts and outputs** are in `scratchpad/diag/next66/`:
- `ext.py` (planloss `extract2.py` plus per-body curves every 25 rounds and gold spent);
- `cycles.py` / `cycles_all.py` (planloss cycles, unchanged; to r600 and to the end);
- one script per question, outputs in `out_*.txt`.

**Definitions.**
- mid = t 0.33–0.67 on the spawn-to-spawn axis.
- A contact is a group cycle that both sides reach (a body within 2).
- One-sided means only the capturing side ever came within 2 of the group.
- Margin = our collected gems (banked + carried) minus the band's.

**Tags.** [measured] = counted from the replays; [code] = read in bots/tz; [guess] = inference or model.

## 0. Answer

1. **The r600 deficit is mostly the middle of the map, and the fights decide it.** [measured]

   tz-66's r600 margin is **−193** (final −330). The top's is **+330** against the same opponents. That leaves a gap of
   523 gems at r600:

   | Mechanism | Gap to the top (gems) | tz-66 | Top |
   | --- | --- | --- | --- |
   | Mid race | 213 | −94 | +119 |
   | Contact | 143 | −76 | +67 |
   | Kill / bag exchange | 103 | −11 | +92 |
   | Uncontested farming, net | 67 | −13 | +54 |

   After r600 we lose another **−203 capture gems** (race −100, contact −82). We also lose **3.8 death events a game
   after r600**; the top loses 1.0.
2. **Racing first does not win a contact for us.** [measured]
   - When we arrive 5+ rounds first we still take only **30 %** of contacts. The top takes 67–74 % whatever the
     arrival order.
   - In the first-arrival contacts we lose (3.1 a game, 18 gems each), 44 % of our bodies walk away within 5 rounds,
     and we are outsized 67 % of the time.
   - **At equal size the top lands 29.3 champion hits per contact to our 19.9.** It kills at 1.8× our rate per hit.
     The band needs only 39 hits to kill one of ours, against 114 to kill one of the top's.
   - Size explains +6 points of contact take. Behaviour explains +33.
3. **"Fewer, bigger bodies" is half right.** [measured]
   - Per body, the band is 26 % / 42 % bigger at r300 / r600 (1,377 / 2,030 v 1,092 / 1,418 max HP).
   - That per-body gap splits about **half body count, half item choice.** We buy **1.03 HP per gold** spent by r600;
     the band buys 1.48 and the top 1.21.
   - **The twins are not the gold sink.** They take ~10–14 % of our gold, about the top's share, and are the same
     size as the top's twins. The top drafts them in 49 % of its games and wins 89 %+.
   - The starved bodies are **Vendetta, HoR and Marcella**: 40–55 % of the band's gold for the same champions at
     r600. HoR buys 9 % Health shards; the band's HoR buys 37 % and the top's 41 %.
   - At contacts we bring *more* bodies (2.03 v 1.92), but each is 17 % smaller. The top brings bodies the band's size
     (1,318 v 1,297), and more of them.
4. **Recommendations** (§4):
   - **R1, a late hunter break:** new, never tested on the band. +20–35 final margin [guess].
   - **R2, Ryth for the twins:** the queued tz-67. 0 to +25 final margin, about −1.5 dead bodies a game [guess]. It
     needs Ryth's area stun wired into conversion.
   - **R3, fight volume at held contacts:** the largest lever. Not reachable with a knob.
   - **Do not build race pricing (P2) before the contact fight is fixed.**

## 1. Decomposition of the r600 margin by class [measured; `decomp.py` → `out_decomp600.txt`, `out_decomp300.txt`]

Components sum to the margin; the residual is ≤ 3 gems.
- Race = mid captures in cycles only one side reached.
- Contact = captures in cycles both sides reached, in any zone.
- Home / far = one-sided captures in our third / their third.
- Kill = (our kill gems − our bags lost) − (theirs − theirs).

| r600, per game | tz-66 won (32) | swing (57) | never (61) | all (150) | Top (all, mix-weighted) |
| --- | --- | --- | --- | --- | --- |
| **Margin** | +73 | −182 | **−343** | **−193** | **+330** |
| Mid race | +19 | −87 | **−161** | −94 | +119 |
| Contact | −22 | −60 | **−120** | −76 | +67 |
| ... of which mid contact | −5 | −52 | −110 | −65 | +53 |
| Home (own third, one-sided) | +269 | +181 | +169 | +195 | +232 |
| Far (their third, one-sided) | −262 | −199 | −187 | −208 | −178 |
| Kill / bag exchange | **+69** | −18 | −46 | −11 | +92 |
| Final banked margin | +281 | −449 | −540 | −330 | +382 |
| Gold earned, us − band | +1,457 | −994 | −1,178 | −546 | +1,239 |
| Contact take % (contacts a game) | 43 % (11.3) | 35 % (9.5) | **21 % (9.2)** | 32 % (9.8) | **69 % (8.3)** |
| Mid one-sided gems, us / them | 123 / 105 | 80 / 167 | 74 / 235 | 87 / 181 | 233 / 114 |

- **The never-won games** lose 161 in the race, 120 in contact and 46 in the exchange; home and far farming net −18.
- **The won games** are won by the exchange (+69) and by the home / far balance (+7). They are level in the middle.
- **Against each opponent** (`out_byopp.txt`), the mid race is negative against all six (−17 policy wonk to −146
  Claudus). Contact is worst against QS2isLaw (−139). The exchange is worst against Kungarna (−66).
- **r300 is half of r600** in every row: margin −102 = race −47, contact −34, uncontested −17, exchange −5.

### Paired tz-66 − tz-55, 150 games (`decomp.py`)

| r600 margin | Race | Contact | Home / far | Exchange | Final |
| --- | --- | --- | --- | --- | --- |
| **+18** | +17 | **+25** | −3 | **−21** | +30 |

The exchange leak that transfer.md found is still there.

### By phase, whole game (`phases.py` → `out_phases.txt`; capture margin only)

| | r0–300 | r300–600 | r600–end |
| --- | --- | --- | --- |
| tz-66: race / contact | −47 / −34 | −47 / −42 | **−100 / −82** |
| tz-66: contact take | 34 % | 30 % | 31 % |
| tz-66: deaths within 6 per contact, us / them | 0.46 / 0.26 | 0.53 / 0.28 | 0.68 / 0.37 |
| Top: race / contact | +34 / +22 | +85 / +46 | +106 / +34 |
| Top: contact take | 67 % | 71 % | 70 % |

**52 % of our whole-game capture deficit (−203 of −387) comes after r600.**

### After r600 (`late.py` → `out_late.txt`)

| After r600 | tz-66 | Top |
| --- | --- | --- |
| Margin path | −193 at r600 → −247 r750 → −284 r900 → −330 final | +330 → +382 |
| Capture gems, us / them | 240 / 444 | 361 / 196 |
| Our death events | **5.1** | 1.1 |
| Kills | 2.3 | 4.5 |

In won games our late captures are 457 v 358. In never-won games they are 150 v 465.

### Mechanism shares of tz-66's own r600 deficit

| Mechanism | Share | How measured |
| --- | --- | --- |
| Mid race | ~49 % | one-sided mid captures |
| Contact | ~39 % | 34 % of it at mid groups |
| Kill / bag exchange | ~6 % | |
| Uncontested | ~7 % | |
| Banking / end race | not a separate mechanism | unbanked carry at the end 60 v 147, in our favour; the final deficit grows by the captures and deaths after r600, not by failed banking |

### Deaths (`deaths.py` → `out_deaths.txt`; twin pairs merged)

| Death events a game | r0–300 | r300–600 | r600–end |
| --- | --- | --- | --- |
| tz-66 | 1.53 | 1.53 | **3.79** |
| Top | 0.74 | 0.88 | 0.96 |
| Band v us | 1.03 | 1.06 | 2.09 |

Late killers are much bigger: **42 % of our late deaths are to a killer with ≥ 1.9× our max HP** (median 2.36×), and
only 21 % have 2+ hitters.

## 2. Contrast with the top teams against the same six

| | tz-66 | Top | Band v us | Band v top |
| --- | --- | --- | --- | --- |
| Body-rounds, r0–600: dead / own third / mid (`zones.py`) | 7.2 / 56.7 / 28.9 % | 3.9 / 51.1 / 37.5 % | 4.8 / 48.9 / 37.1 % | **11.5** / 53.3 / 29.0 % |
| Camp-hit rate in the middle | 17.2 % | 23.1 % | 20.7 % | 18.1 % |
| Mid camp hits per body-game | 28.8 | 50.2 | 44.7 | 30.4 |
| Mid cycles reached, r0–600 (`midrace.py`) | **55 %** | **72–76 %** | 66–75 % | 48–52 % |
| Reached first | 41–46 % | 58–61 % | | |
| Mid one-sided takes where we came within 8 at the capture | 28–32 % | | | |
| Contact take when 5+ rounds first (`firstarr.py`) | **30 %** | **67 %** | | |
| Contact take when 5+ rounds second | 39 % | 74 % | | |
| Gold r600: captures (mid) / kills ×100 (`goldsrc.py`) | 2,638 (929) / 2.2 | 2,836 (1,280) / 5.3 | 2,938 (1,327) / 3.9 | 1,963 (615) / 2.0 |

- **The race is presence plus suppression, not speed.** The band reaches 74 % of mid cycles against us but only 50 %
  against the top: against the top it is dead 11.5 % of the time and keeps to its own third.
- In 70 % of the band's one-sided mid takes, no body of ours was within 8.
- Arrival time after respawn is the same (median 6–9 rounds).
- So the top wins the race largely through the fights.

**Contact fights, r ≤ 600** (`fight.py` → `out_fight.txt`; champion hits within 6 of the group during the cycle, by
size bucket = our max HP within 6 / theirs):

| Bucket | Our contacts | tz-66: hits us / them | Deaths us / them | Take | Top: hits us / them | Deaths us / them | Take |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Outsized (< 0.85) | 46 % | 13.2 / 15.9 | 0.53 / 0.17 | **16 %** | 20.5 / 17.2 | 0.22 / 0.54 | **54 %** |
| Parity | 17 % | 19.9 / 22.9 | 0.59 / 0.30 | 28 % | **29.3 / 21.6** | 0.19 / 0.79 | **71 %** |
| Bigger (> 1.15) | 36 % | 19.9 / 16.5 | 0.41 / 0.38 | 53 % | 20.6 / 16.4 | 0.18 / 0.59 | 79 % |

- **Hits per kill:** ours ~66 v the top's ~37.
- **Band hits per kill:** on us 39, on the top 114.
- At equal size the top out-hits the band 1.36:1, kills 2.6× more and dies 3× less.
- **Reweighting** (`contact.py`): our take is 31.8 %. With the top's size mix and our rates it would be 37.8 % (+6.0).
  With the top's rates and our size mix it would be 65.2 % (+33.4).
- In planloss (tz-55) the size share was +3.6. With tz-66 size matters a little more (take 13 % → 60 % across the
  buckets), but behaviour is still about 85 % of the contact gap.

## 3. "Fewer, bigger bodies": per-body gold, max HP and the twins

### Per body (`bodies.py` → `out_bodies.txt`)

| | Bodies (picks) | Gold / body r300 / r600 | Gold / pick r600 | Max HP / body r300 / r600 | 2nd-biggest body r600 | Team max HP r600 | HP per 100 gold spent r300 / r600 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tz-66 | 5.40 (4.40) | 257 / 531 | 655 | 1,092 / 1,418 | 1,470 | 7,688 | **70 / 96** |
| Band v us | 4.46 (4.40) | 334 / 779 | 791 | 1,377 / 2,030 | 2,249 | 9,017 | **131 / 146** |
| Top | 4.99 (4.50) | 311 / 732 | 806 | 1,184 / 1,745 | 1,964 | 8,548 | 93 / 121 |
| Band v top | 4.52 | 248 / 509 | 509 | 1,288 / 1,690 | 1,856 | 7,652 | 140 / 183 |

**Shapley split of the per-body max HP gap** (`sizedec.py`):

| | Gap | Body count | HP per gold | Gold spent | Base HP |
| --- | --- | --- | --- | --- | --- |
| r300 | +281 | +235 | +141 | +13 | −108 |
| r600 | +598 | **+325** | **+265** | +116 | −108 |

- **Team max HP is a different matter.** The gap there (−1,329 at r600) comes from items and gold, not from the 6th
  body: the extra body adds base HP.
- The top's bodies are *smaller* than the band's at r300 (1,184 v 1,288). **The top does not beat the band by
  out-sizing it.**

### By champion, r600 (`items.py` → `out_items_all.txt`; per body-game)

| | Gold earned | Shards Health / Strength / Focus | Max HP | Capture gems | Kill part. | Deaths |
| --- | --- | --- | --- | --- | --- | --- |
| Our Vesper | **1,626** | 14.8 / 43.8 / 0.7 | 2,479 | 179 | 1.09 | 0.55 |
| Band Vesper | 1,491 | 18.1 / 32.1 / 4.4 | 2,809 | 175 | 1.09 | 0.26 |
| Top Vesper | 1,685 | 13.7 / 44.5 / 1.8 | 2,370 | 160 | 1.60 | 0.19 |
| Our Vendetta | **368** | 4.1 / 7.6 / 0 | 1,312 | 57 | 0.59 | 0.70 |
| Band Vendetta | 764 | 11.1 / 13.7 / 1.0 | 2,011 | 122 | 1.01 | 0.48 |
| Top Vendetta | 977 | 9.3 / 23.5 / 0.5 | 1,825 | 144 | 2.13 | 0.19 |
| Our HoR | **248** | **0.7** / 0.1 / 6.9 | **1,073** | 34 | 0.55 | 0.76 |
| Band HoR | 532 | 6.4 / 0.5 / 10.2 | 1,642 | 81 | 0.94 | 0.57 |
| Top HoR | 542 | 7.5 / 0.7 / 10.0 | 1,751 | 84 | 1.90 | 0.33 |
| Our Marcella | 588 | 2.8 / 0.1 / 15.8 | 1,480 | 71 | 0.60 | 0.57 |
| Band Marcella | 1,064 | 12.9 / 3.7 / 20.3 | 2,490 | 160 | 0.98 | 0.40 |
| Top Marcella | 881 | 7.4 / 1.2 / 19.6 | 1,941 | 148 | 2.56 | 0.34 |
| **Our twins (pair)** | **302** | 8.6 H | 893 + 1,227 | 44 | 1.32 | 0.87 pair-events |
| **Top twins (pair)** | 509 | 7.4 H, 5.1 F | 735 + 1,325 | 132 | 2.61 | 0.75 pair-events |
| Band Ryth (their 5th pick) | 516 | 11.5 / 2.1 / 1.0 | 2,352 | 77 | 1.03 | 0.48 |
| Band Prism | 795 | | 1,977 | 260 | | 0.14 |
| Band Varg | 438 | | 1,403 | 83 | | 0.67 |

- **Share of our gold:** Vesper **56 %**, the twins ~10.5 % (bodies.py's mean of ratios is 13–14 %), the three
  supports ~34 %.
- **Our Vesper earns what the top's does.** The top's extra team gold (+655 at r600) sits in its supports, who earn it
  themselves: Vendetta 144 capture gems and 2.1 kill participations v our 57 and 0.6.
- Feeding does not take gold *from* the supports relative to the top. Their missing gold is the mid takes and the
  kills they never make.
- **The twins are the same size as the top's twins** (r300: Cassi 733 v 655, Issac 1,074 v 1,099). They already buy
  90 % Health.
- They take the same share of the contact bodies (36 % of ours; 36 % of the top's in games where it has twins;
  `contact3.py`).
- **Where our twins fall short of the top's:** output (gold ×0.6, capture gems ×0.33, kill participations ×0.5) and
  late deaths.

**Twin deaths** (`twins.py`, `latebody.py`, `approach.py`):

| | By r600 | After r600 | All game | Gold handed to the band |
| --- | --- | --- | --- | --- |
| Our twins, pair-death events | 0.89 | **1.46** (top's twins 0.53) | 2.18 (bags 15 gems) | 218 |
| Share of our death events | 29 % | | | |

- **The twins' late deaths are hunts.**
  - After r600 our deaths to ≥ 1.9× killers come to **2.0 a game**, and 44 % of the victims are twins.
  - The killer closes 5.8 tiles over the 12 rounds before the kill, from 9.6 tiles away. The victim is at 0.80 HP
    6 rounds before. The killers are mostly the band's Vesper and Marcella.
  - After r600 the twins are dead 17 % of the time and produce 270 gold and 30 capture gems as a pair. The band's
    Ryth produces 748 gold and 60 capture gems with 0.62 deaths.

**Would a 5-pick draft without the twins (Ryth) help?** [guess, from the rows above]
- Our bot pays supports about 50–60 % of the band's same-champion gold. A Ryth here would therefore earn about
  ~650–700 gold and ~70 capture gems over the game, about the twin pair's 572 / 74. So production is level.
- It would be one body of ~2,000 HP at r600 instead of 893 + 1,227. Its killers would be ~1.3–1.8× its size, not
  2.4–3.7×.
- Its deaths would be ~1.3–1.5 a game (our supports die 1.4–1.6× the band's same champion; the band's Ryth dies 1.1)
  against 2.18 pair-events. That is ≈ −0.7 events and about **−1.5 dead bodies a game**, worth ~+15–25 final margin.
- The cost: Cassi's stun, which is the conversion opener, and one parallel farmer.
- Precedent: tz-7 (v151, Ryth for C&I plus other changes) gave deaths −3.9 a game, gold r300 −67 and share level.
- **Net: 0 to +25 final margin, not a size lever.**

## 4. Recommendations (generalisable: rules only from what a body sees; no map or opponent terms)

### R1. Late hunter break (new; never tested on the band)

**Evidence** [measured]: the late death stats above (2.0 deaths a game to ≥ 1.9× killers, the closing pattern). These
are 82 % solo kills. In 55 % the victim also stepped toward the killer.

**Why the current rules miss them** [code]:
- **The fed break** fires only within the enemy's reach + `fed_margin` 2 (`bot.cpp` ~l.3760–3772). `fed_far_k` is 0,
  so the far branch is off (`value.h` l.86–87).
- **The WORK hold** stops for a fed enemy only within reach + 2 (`bot.cpp` l.3658).
- **The planner** discounts groups near the posted big enemy only ×`big_k` 0.5 within `big_r` 8 (`bot.cpp`
  l.704–716).

**Build:**
- In the `fed_break` block, add a closing hunter: an enemy seen this round with max HP ≥ `fed_k` × mine, within 9,
  that closed on me last round (`e.prev_pos` / `e.prev_round` exist; see the `closing` test at l.3657). When it
  fires, BREAK toward the nearest ally or spawn.
- Extend the same rule to the posted big sighting while it is approaching.
- Use the same rule as a WORK stop.
- Optionally, `big_k` 0.5 → 0.25 for bodies the posted big enemy out-sizes by 2×.
- Requiring "closing" is the difference from the `fed_far_k 3` that lost locally (56.0 % v 63.3 %). v93 does not hunt
  late, so that local result says little about the band.

**Expected** [guess]:
- Halve the hunted deaths: −1.0 event (−1.4 bodies) a game after r600.
- Per event that saves ~7 farm gems (65 dead rounds × 0.106 gems per alive body-round), ~10 bag gems, and 100 gold
  that would have grown their carry.
- Total **+20–35 final margin**, about the size of the whole tz-55 → tz-66 step (+30).
- Judge it on deaths after r600 and the final margin.

### R2. Ryth for the twins (tz-67, queued)

**Expected:** as in §3 — **−1.5 dead bodies a game, final margin 0..+25** [guess].

**Before reading its result**, check the draft.cpp and bot.cpp details [code]:
- `draft.cpp` l.39–41: `draft_table` 6 = Ryth on 5 picks, 7 = C&I. 3–4 picks keep C&I in both tables.
- Ryth gets `b_ryth` (all Health, `bot.cpp` l.2675/2685) and taker rank 1, so it is fed as a support. That matches
  the model above.
- **Conversion** (`bot.cpp` ~l.2242–2330) fires only for HoR and Cassi. **A Ryth comp has no stun opener**
  (kills.md: a stun-type hit lands in 4.1 of the top's 7.4 kills a game). Ryth's slot-0 area stun (range 4, radius
  1, excludes walking) should be added as an opener on a target an ally can hit. Otherwise tz-67 measures Ryth
  without its stun.

**How to judge:**
- Judge on deaths and the late margin, not on r300 gold (tz-7 lost 67 gold at r300).
- If tz-67 is level on share with fewer deaths, then Ryth plus the stun wiring is the next stage.
- 3–4 picks are a separate question. There the twins are 35–45 % of our deaths (draft.md V3).

### R3. Fight volume at held contacts (the largest lever; needs a redesign, not a knob)

**Evidence** [measured]: the contact-fight table in §2 and the first-arrival rows above. The top in the same
first-arrival spot stays (16 % leave) and wins 67 %.

**Size of the prize:**
- Contact + the race it drives + the exchange ≈ 450 of the 523-gem r600 gap to the top.
- Each +5 points of contact take ≈ **+14 gems at r600** (9.8 contacts a game × 0.05 × 2 × 14 gems) [guess on the
  swing].
- History: WORK / p1 / p3 moved take 27 → 32 %. One more step of that size is worth ~+15 gems at r600.

**Concrete first step** [code]: at a held group with an enemy champion in basic reach, the holder attacks the champion
and uses its move to stay on the group. That is strike-and-farm with the attack spent on the champion first.
- **`work_out_k`** (`bot.cpp` l.3649) counts only bodies (`L.ohp.size() <= L.n_enemy`). It should count the allies
  within 6 and their max HP. Our losing holds are 1.18 v 1.60 bodies; the winning ones are 1.84 v 1.33.
- **The supports' first hits.** kills.md: Marcella and HoR are 60 % of the first-hit gap. `role_mask` bit 8 (the
  Marcella poke) "barely fires" (role_build.md).
- **Measure locally** on champion hits per contact at parity (target ≥ 25) and hits per kill (target ≤ 45). v93 loses
  contacts by itself, so its win rate cannot show this.

### Not recommended now

- **Race pricing (P2).** Arriving first wins only 30 % of our contacts. More races now mean more lost contacts.
  Revisit once the contact take is ≥ 45 %.
- **Health item lines for HoR / Marcella** (`sup_lines`). HoR's 9 % Health is real (top 41 %), but HoR earns only
  248 gold by r600. Switching would add ~+200–300 HP per support, which moves the contact size ratio by a few
  percent (≈ +1–2 points of take) [guess]. `sup_lines` already stopped once (tz-36b).
- **Fewer bodies for size's sake.** The top wins with bodies the band's size. Our size deficit at contacts (−14 %
  local max HP) is worth +6 points of take, about +17 gems at r600 [guess on the swing].

## 5. Caveats

- `top_v_band` games are 7 Nov scrims against the band's bots of that evening. `tz66_big` plays the frozen source
  groups, so the opponent versions may differ.
- The top set includes BattleCats (73 % wins), and its comps differ from ours. Per-champion rows pool different
  comps.
- **Kill participation** credits every hitter within 3 rounds. **Killer / victim ratios** use the biggest hitter.
- "Champion hits near the group" counts hits on the champion's tile within 6 of the group, including hits that
  missed the group's fight.
- Stats from `bc` are sampled every 25 rounds. Shard counts come from stat deltas divided by the measured growth
  (`growth.py`). Power and Bruiser emblems make them approximate (±1 shard).
