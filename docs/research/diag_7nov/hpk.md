# hpk: why tz-66 needs ~1.8x the top's hits per kill (8 Nov)

**Data.**
- `tz66_big`: tz-66 against the six UK band teams, 150 games.
- `top_v_band`: the top four against the same six, 119 games, reweighted to tz-66's opponent mix.
- Window: r <= 600 unless stated (it is next66's window). Whole-game rows are given where they differ.

**Rules followed.** I read only `bots/tz` (a few functions) and the SDK header. I read no v93 code and no other team's code,
ran no games, and edited no bots. Light python only.

**Scripts** are in `scratchpad/diag/hpk/`:
- `ext.py LABEL` writes `hpk_LABEL.pkl`;
- `a1.py` … `a17.py` are the analyses, with outputs in `out_a*.txt`;
- `lib.py` holds the loaders and the opponent-mix weights.

**Model and definitions** [rules / measured]:
- **Every champion hit** of both sides is resolved on live in-round positions. The kinds are basic, Varg splash and every
  damaging or stun cast; HoR's dash is resolved at its landing.
- **Nominal damage** is Strength for a basic and coef × Focus for a cast, per the GameRules kits. HoR's missing-HP bonus is
  applied. Shields come from the `bf` type-0 buffs plus shield casts, and they absorb first.
- **Calibration** against the observed HP drop off spawn: median 0.92 of nominal after shields. That is about Durability's
  −10 %. The model reads damage, not hits.
- **Victim episode:** our hits on one enemy body, with gaps of 5 rounds or less. A death or a recall arrival ends it. It
  is converted if it ends in our kill, or if the same life later dies to us before a full heal.
- **How an unconverted episode ends:**

  | End | Meaning |
  | --- | --- |
  | recall | a recall arrival within 8 rounds |
  | spawn | the victim reaches its spawn within 5 rounds |
  | ran / we_left | 5 rounds after the last hit, every attacker is more than 4 tiles away; the side that moved apart decides which |
  | stopped | attackers still within 4, but no more hits |
  | attackers_dead | every attacker is dead |

Tags: [measured] = counted from the replays; [code] = read in `bots/tz`; [sdk] = `sdk/cpp/cambc.h`;
[guess] = model or inference.

## 0. Answer

1. **The "66 v 37" metric counted actions, not hits** [measured, `a16`].
   - next66's "champion hits" were every basic or cast step not aimed at a camp tile. That includes our 253 dashes,
     142 resets and 41 shields a game, so about 75 % of the count was self-casts.
   - Real champion hits per kill are **41.9 v 23.5** to r600 and 32.4 v 19.8 over the whole game. Within 6 of contested
     groups they are 37.7 v 19.1.
   - **The ratio, 1.78, is the same,** so the finding stands.
2. **Hits per kill = damage per kill ÷ damage per hit.** Both halves are worse [measured, `a1`/`a2`].
   - Damage per hit: **82.7 v 106.9 (top +29 %)**, worth 44 % of the log gap.
   - Damage per kill: **3,467 v 2,512**, worth 56 %.
   - The kill itself costs the same (1,054 v 1,134 nominal per kill episode). What differs is the damage **wasted on
     bodies that get away: 2,185 v 1,142 per kill.** We convert 37 % of our damage into kills; the top converts 55 %.
3. **It is not spread, target choice, spawn hits, overkill or burst alignment** [measured, `a6`]. On each of these we are
   equal to or better than the top:
   - We focus more: 86 % of a fight's damage is on its top target, v 82 %.
   - Only 15 % of hits had another enemy in reach, and only 3 % had a lower-HP one.
   - 1.1 % of hits land near the enemy spawn.
   - Overkill is 2.6 % of damage v 4.8 %.
   - Rounds with 2+ hitters on one target carry 33 % of our damage v 26 %.
   - Our stun follow-up is better: 2.05 hits after a stun v 1.30.
4. **The start of an engagement is not the problem either** [measured, `a7`].
   - A logistic model on start features predicts conversion from: first-2-round burst, attackers, stun, local numbers
     and power, victim HP, max HP, spawn distance and contact.
   - Our episodes put through the top's coefficients convert at 34.8 %, against the top's 36.6 % (ours are 23.9 %).
   - So our engagements start as well as the top's. **We lose them afterwards.**
5. **A race model splits the gap** [measured inputs, model `a11`/`a14`]. It runs each round by victim HP: P(hit),
   damage drawn from each side's own hit-rounds, and the per-round end hazard.
   - Swap in the top's **damage per hit-round: hits per kill ×0.725.** The top's opening round deals 15.5 % of the
     victim's max HP; ours deals 9.5 %.
   - Swap in the top's **end hazard: ×0.763.** Of that:
     - victim ran ×0.897
     - recall ×0.944
     - we left ×0.962
     - our attackers died ×0.966
     - spawn ×0.974
     - stopped ×0.990
   - **Both together: ×0.587.**
6. **Damage per hit is 72 % stats, 28 % cast use** [measured, `a13`/`a17`]. Our champion mix with the top's
   per-champion damage per hit gives 106.2, so the comp explains nothing. By champion:
   - **Strength** for Vendetta (basic 87 v 128) and Vesper (126 v 139).
   - **Focus** for Marcella's cast (253 v 316), Cassi's and HoR's.
   - **Cast use.** With a damaging cast ready and an enemy within 3, **Marcella casts at a champion 19 % of the time
     (top 43 %), HoR 21 % (53 %), Cassi 25 % (48 %).** In those rounds we step instead: 64–70 % of them v ~50 %.
   - Our stuns land 6.1 times a game against the top's 20.5. HoR's dash-stun alone is 1.2 v 6.3.

**Worth, at our hit volume** [guess, from the race-model multipliers]:

| Fix | Hits per kill | Kills a game to r600 | Gain |
| --- | --- | --- | --- |
| Now | 41.9 | 1.77 | |
| Top's damage only | 30.4 | 2.44 | +0.67 |
| Top's end hazard only | 32.0 | 2.32 | +0.55 |
| **Both** | **24.6** | **3.02** | **+1.25** |

- Over the whole game, both fixes give 3.77 → **~6.4 kills a game (+2.6)**.
- At 14 bag gems + 100 gold + ~7 denied farm gems a kill, that is **≈ +55 gems and +260 gold a game**, before any
  contact-take effect.
- The rest of the top's 9.65 kills a game is volume: 191 v 122 champion hits a game.

## 1. Where the damage goes (a, d, e) [measured, `a2` → `out_a2.txt`; whole game in `out_a2_all.txt`]

Per game, r <= 600, nominal damage on enemy champions. "Per kill" is divided by the side's kills.

| Episode end | tz-66 dmg share | per kill | hits / kill | Top dmg share | per kill | hits / kill |
| --- | --- | --- | --- | --- | --- | --- |
| **kill** | 30.4 % | 1,054 | 11.7 | **45.1 %** | 1,134 | 9.6 |
| kill later (same life) | 6.6 % | 228 | 3.1 | 9.4 % | 236 | 2.3 |
| **victim ran** | 22.1 % | **766** | 8.7 | 16.5 % | 415 | 4.3 |
| **we left** | 11.3 % | **393** | 5.8 | 5.9 % | 148 | 1.6 |
| stopped (still within 4) | 11.7 % | 405 | 5.2 | 12.2 % | 306 | 3.1 |
| **recall** | 9.9 % | **344** | 4.3 | 6.2 % | 156 | 1.5 |
| spawn | 5.0 % | 175 | 1.2 | 3.5 % | 88 | 0.7 |
| **attackers dead** | 2.9 % | 102 | 1.8 | 1.1 % | 29 | 0.4 |
| **Total** | 6,126 a game | **3,467** | **41.9** | 13,045 a game | **2,512** | **23.5** |

- **Kill episodes cost the same.**
  - Ours: 1,054 = start HP 890 (0.74 of 1,230 max) + shield 49 + overkill 87.
  - The top's: 1,136 = start HP 970 (of 1,281) + 38 + 121.
  - Kills take 2.43 attackers and 6.3 rounds (top: 2.15 and 5.9).
- **Per episode, the endings that are ours more often than the top's:**

  | Ending | tz-66 | Top |
  | --- | --- | --- |
  | We left | 18.5 % | 11.9 % |
  | Attackers dead | 6.8 % | 2.6 % |
  | Recall | 7.7 % | 5.7 % |
  | Kill | 14.5 % | 23 % |

  Episodes a game: 12.2 (ours) v 22.5 (top).
- **Finishing** (`a9`). Of episodes that took the victim below 30 % HP:
  - we finished 47 % (top 63 %);
  - **1.00 such bodies got away per kill (top 0.49),** wasting 866 v 374 damage per kill;
  - they got away by running 45 %, recalling 22 %, standing off 11 %, reaching spawn 9 %, or us leaving 8 %.
- **Per-round end hazard at equal victim HP is ours ×1.3–1.7** (`a10`). By victim HP band:

  | Victim HP | tz-66 hazard | Top hazard |
  | --- | --- | --- |
  | 15–30 % | 16.1 % | 9.6 % |
  | 30–50 % | 17.4 % | 12.3 % |
  | 50–70 % | 15.5 % | 12.8 % |
  | 70–90 % | 14.1 % | 11.0 % |

  Our damage per hit-round is 9–10 % of the victim's max HP against the top's 10.5–11.5 %. On a fresh target it is
  8.5 % v 13.4 %.
- **Recall escapes** (`a4`): 0.94 a game. In 35 % of them one of our attackers was within 4 tiles during the 5-round
  channel. Any damage cancels a recall [rules].
- **Shields** take 8.0 % of our damage (top 6.1 %). Overkill is 2.6 % (top 4.8 %). Neither explains the gap.
- **Mirror:** the band needs 32 hits to kill one of ours and 70 for one of the top's. It wastes 70 % of its damage on
  the top and the same 70 % on us.

## 2. Spread, target choice, timing (b, c, f) — not the gap [measured, `a6`, `a8`, `a12`]

| | tz-66 | Top |
| --- | --- | --- |
| Fights with >= 4 of our hits, a game | 5.2 | 8.1 |
| Distinct targets per fight / >= 2 targets | 1.56 / 40 % | 1.75 / 48 % |
| Top target's share of a fight's damage | **86 %** | 82 % |
| Fights with a kill / damage on bodies killed | 27 % / **35 %** | 43 % / **51 %** |
| Hits with another enemy in reach / a lower-HP one / a killable one | 15 % / 3 % / 0.1 % | 17 % / 5 % / 0.3 % |
| Hits on a victim within 2 of its spawn | 1.1 % | 1.0 % |
| Hits on a stunned victim | 13.5 % | 14.7 % |
| Damage in rounds with 1 / 2 / 3+ of our hitters on that target | 67 / 23 / 10 % | 74 / 20 / 6 % |
| P(target dies that round) with 1 / 2 / 3+ hitters | 3.1 / 4.6 / 6.6 % | **5.6 / 6.9 / 13.1 %** |
| Stuns landed a game | **6.1** | **20.5** |
| Hits / damage in the stun round + next | **2.05** / 157 | 1.30 / 93 |
| Kill within 3 rounds of a stun | 13.5 % | 16.9 % |
| Openers with a damaging cast / with a stun | **28 % / 20 %** | **61 % / 39 %** |
| Opening-round damage (share of the victim's max HP) | **9.5 %** | **15.5 %** |

- **Our spread, focus and multi-hitter timing are as good as the top's or better.** The same number of hitters simply
  kills less often, because each hit is smaller.
- **Stuns:** our follow-up is better; we just land a third as many.
- **Conversion by start features** (`a3`; share of episodes, then P(convert)):
  - The top converts more at every level.
  - 1 attacker: 62 % at 16.9 % for us, v 64 % at 28.7 %.
  - 3+ attackers: 45 % v 71 %.
  - Victim ≥ 1,800 max HP: 14.5 % v 31.5 %.
  - Contact: 21.8 % v 38.4 %.
  - Mix-and-rate counterfactual (cells = attackers × burst × stun): ours 23.9 %, top 36.6 %. Our mix with the top's
    rates gives 31.1 %; the top's mix with our rates gives 28.8 %.
- **The top fights worse local numbers than we do** (`a7` means). Edge −0.40 v −0.11; log power −0.48 v −0.18.

## 3. Per champion (g) [measured, `a5`, `a13`, `a17`]

| Champion | Share of our hits | Damage per hit, ours / top | Basic, ours / top | Cast share | Cast dmg, ours / top | Gap points (basic + cast share + cast power) |
| --- | --- | --- | --- | --- | --- | --- |
| Vesper | 26.9 % | 126 / 139 | 126 / 139 | 0 | | +3.5 (Str) |
| Marcella | 17.2 % | 86 / 126 | 40 / 42 | 22 / 31 % | 253 / 316 | +6.8 (0.2 + 3.3 + 3.3) |
| Issac | 15.4 % | 46 / 49 | | | | +0.4 |
| HoR | 14.2 % | 54 / 82 | 34 / 35 | 11 / 21 % | 207 / 256 | +3.9 (0.1 + 2.4 + 1.5) |
| Vendetta | 13.3 % | 87 / 128 | 87 / 128 | 0 | | +5.5 (Str) |
| Cassi | 12.9 % | 59 / 86 | 30 / 30 | 54 / 58 % | 84 / 125 | +3.4 (cast mix + Focus) |
| **Sum** | | **82.7 / 106.9** | | | | **+23.5 = basic 9.6 + cast share 6.0 + cast power 7.9** |

**Fight behaviour, with a damaging cast ready and an enemy within 3** (`a17`):

| Champion | Rounds a game, ours / top | Cast at a champion | Any champion hit | Moved |
| --- | --- | --- | --- | --- |
| Marcella | 7.8 / 7.5 | **19 % / 43 %** | 37 / 52 % | 64 / 51 % |
| HoR | 4.0 / 6.5 | **21 % / 53 %** | 47 / 61 % | 53 / 51 % |
| Cassi | 8.4 / 2.9 | **25 % / 48 %** | 25 / 56 % | 67 / 50 % |
| Top's Ryth / Prism | | 60 % / 58 % | | |

- **Attack resets are not the issue.** On a round with a champion hit in range and the reset ready, every reset champion
  uses it 90–98 % of the time, ours and the top's alike.
- **Vesper hits less often.** P(a champion hit | an enemy within 4) is 0.34 v the top's 0.46, but its damage per hit is
  close (126 v 139).
- **Melee hit rate** with an enemy within reach + 1: ours 0.54–0.66 v the top's 0.61–0.72.

## 4. Factor table [model on measured inputs; kills a game at our 74.3 hits a game, r <= 600]

| Factor (swap to the top's) | Hits / kill multiplier | Kills a game | Share of the gap | What it is |
| --- | --- | --- | --- | --- |
| **Damage per hit-round** | **×0.725** | +0.67 | **~54 %** | 72 % stats (feeding), 28 % cast use; opener 9.5 → 15.5 % of max HP |
| Victim ran | ×0.897 | +0.21 | ~18 % | no closing / stun on fleeing low-HP targets |
| Recall | ×0.944 | +0.11 | ~10 % | recalls not cancelled; 35 % had an attacker within 4 |
| We left | ×0.962 | +0.07 | ~7 % | BREAK of bodies that were hitting (melee 19–20 % of episodes v 9 %) |
| Attackers dead | ×0.966 | +0.07 | ~6 % | our hitters die first (12 % when outnumbered v 5 %) |
| Spawn | ×0.974 | +0.05 | ~4 % | |
| Stopped | ×0.990 | +0.02 | ~2 % | |
| **All** | **×0.587** | **+1.25** (whole game +2.6) | | |

The model reproduces the gap only roughly: 33.4 v 20.2 hits per kill (ratio 1.65), against the real 41.9 v 23.5 (1.78).

## 5. Rules (implementable; nothing per map or per opponent)

### R1. Cast before you step (largest combat-side lever)

**The rule.** Apply it on a turn where:
- a damaging or stun cast is ready;
- a visible enemy champion is in that cast's reach (Marcella slot 1, range 4; Cassi slot 0 / slot 1, range 4; HoR
  slot 1, a landing tile within 2 that is adjacent to the target; Ryth slot 0 if drafted);
- and no fed break or stance_low flee applies.

Then cast at the fight target *before* moving. For casts that exclude walking, the cast replaces the step. Keep the
existing "no damaging cast on a camp with an enemy champion within 5".

**Expected** [guess]:
- It closes the cast-share part of damage per hit (+6.0 of 24.2).
- It raises the opener toward the top's 61 % with a cast.
- Our stuns rise from HoR's dash: 1.2 → ~4 a game.
- About **+0.25 kills a game by r600.**

**KPI:** P(cast at a champion | ready, enemy ≤ 3) ≥ 40 % for Marcella, HoR and Cassi.

### R2. A posted finish target (focus via comms)

**Which enemy.** Each body picks the visible enemy with the least (HP + shield) ÷ (the damage our bodies within 5 can
put on it this round and next, casts included). It must be at ≤ 40 % max HP, or at ≤ 1.2 × that damage.

**How it spreads.** The body posts it in its comms slot (enemy id + round). An ally adopts a posted target seen within
the last round when it can reach it within 2 moves.

**What adopting bodies do:**
- no BREAK and no farm hold;
- stun first if a stun is ready (extend `stun_target`'s follow test to "is the finish target");
- close with a dash if the landing puts it in reach;
- then cast and hit.

**Exclusions:**
- the target is within 1 of its spawn and not killable this round (keep `near_espawn`);
- the fed break fires;
- my HP is below stance_low.

**Evidence:** finish rate 47 % v 63 %; 1.0 low-HP escapes per kill v 0.49; end hazard at 15–30 % HP 16 % v 10 % a round.

**Expected:** most of the ran + recall swap, ×0.85 hits per kill → **+0.3 kills a game by r600** [guess on how
attainable it is].

### R3. Cancel recalls

**The rule.** Hit a visible enemy that is recalling and at < 60 % HP when it is within any body's reach (cast reach 4
counts). Damage cancels a recall [rules]. Give it priority over farm.

**The check** [sdk]: `champion::is_recalling()` exists. Whether it reads on enemy handles is **unverified**.

**The band's pre-recall:** the band starts a recall at the end of most turns and cancels it next turn (README). That is
why the HP filter is needed. Hitting a pre-recall wastes nothing anyway.

**Expected:** recall escapes 0.94 a game, with 35 % in reach → about **+0.1 kills a game** [guess].

### R4. No unforced break-off from a body we are hitting

**The rule.** A body that hit an enemy champion in the last 2 rounds does not take the stance BREAK or a WORK-hold
walk-away while all of these hold:
- its HP ≥ 50 %;
- our bodies within 5 of the target ≥ theirs, counting the target;
- no fed enemy is within reach + 2.

**Evidence** [measured]:
- 18.5 % of our episodes end with us leaving, v 11.9 %.
- At a +1 / +2 local edge we leave 18.5 % / 12.9 % of the time (top 8.3 % / 1.2 %).
- 57 % of our leaves come with all attackers ≥ 50 % HP.
- Our melee leave 19–20 % of their episodes (top 9 %).
- r3.md: 48 % of contact turns are break-offs, and 61 % of those are at ≥ 50 % HP.

**Expected:** **+0.07 kills a game** directly, plus contact take (not modelled).
- This is r3 bit 64 ("commit when winning") made a rule for every body, not only holders.
- `break_closing` stays: it covers the opposite case.

### R5. Not a "don't hit" rule

The data argue against suppressing pokes:
- **Pokes are not where we differ.** Solo episodes are 62 % of ours and 64 % of the top's. The top converts its solo
  episodes at 29 % against our 17 %.
- **Hit volume is the other half of the kill gap** (122 v 191 hits a game).

Keep only these exclusions:
- **Spawn:** don't start on a target within 1 of its spawn unless it can be killed this round (1 % of hits).
- **Shields:** count shield as HP in the ranking, since shields take 8 % of our damage.
- **Outnumbered:** with power < 0.6 and our side down in numbers, hit from a tile no more enemies reach (r3 bit 4). Do
  not stand. Our attackers die in 15 % of such episodes v 5 %.

### R6. Feeding

72 % of the damage-per-hit gap is Strength and Focus on Vendetta, Vesper, Marcella, Cassi and HoR. That is next66's
support-gold finding seen in the fights, and no targeting rule fixes it.

- With R1, Focus on Marcella and HoR pays twice: bigger casts that are actually cast.
- Expected: the stats part of the ×0.725 → about **+0.45 kills a game by r600** [guess].

### Stun–burst sequencing

No new protocol is needed. Follow-up is already better than the top's (2.05 hits, 41 % of stuns with 2+ follow-up
hitters). The gap is the number of stuns, which R1 fixes for HoR's dash and Cassi.

### KPIs to watch (from `ext.py` on a local or band label)

| KPI | Now | Top |
| --- | --- | --- |
| Real champion hits per kill (r <= 600) | 41.9 | 23.5 |
| Damage per hit | 82.7 | 106.9 |
| Converted damage share | 37 % | 55 % |
| Finish rate below 30 % HP | 47 % | 63 % |
| Low-HP escapes per kill | 1.0 | 0.49 |
| "We left" share of episodes | 18.5 % | 11.9 % |
| Stuns a game | 6.1 | 20.5 |
| Cast use when ready | 19–25 % | 43–53 % |

## 6. Caveats

- **The band may be weaker against the top.** The top's games are 7 Nov scrims against that evening's band, and the
  band is starved against the top: dead 11.5 % of the time, ~35 % less gold per body (next66). That can inflate the
  top's conversion "rates". Against it: the victims' max HP in episodes is equal (1,294 v 1,325) and the top's kills
  cost more damage (1,134 v 1,054).
- **The damage model is nominal.** Durability is not modelled (calibration 0.92), nor are Prism's gem Focus or camp
  damage on champions. Victim HP between its own steps is estimated.
- **Episode and fight definitions are heuristic:**
  - episodes use a 5-round gap;
  - "ran" v "we left" is decided by which side moved apart over 5 rounds;
  - fight clusters use 4 rounds and 7 tiles.
- **The race model is memoryless within HP buckets.** It reproduces the gap only roughly (1.65 v 1.78), so the
  multipliers are ratios, not forecasts.
- **Hazard swaps assume the top's rates are reachable.** Running away is partly the victim's code. R2's +0.3 assumes
  about half of it.
- `tz55_big` was not used.
