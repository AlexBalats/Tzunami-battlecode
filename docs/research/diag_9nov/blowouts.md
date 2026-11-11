# Blowouts: what goes wrong in r0-300 (9 Nov, agent)

**Question.** 55 of tz-116's 112 band losses (n47_tz116) are blowouts (loss, share < 0.30). What predicts one by r150, and
what should our bodies do differently?

**Short answer [measured].**
1. **Blowouts are a small-map problem.**
   - On maps with < 2,500 open tiles: 41 of 95 games are blowouts (0.43). On larger maps: 14 of 55 (0.25).
   - Under 1,500 open tiles it is 32 of 59 (0.54). At 5,000 or more it is 2 of 30.
   - The top wins 0.90 of its small-map games against the same six teams.
2. **The cause is our income, not theirs.**
   - In blowouts we have 50 collected at r150, against 82-99 in other games.
   - The band has **109** at r150 in our blowouts, against 110 in our close losses and 95 in our wins.
   - On small maps our camp work yields **0.32 gems per camp-hit round** in blowouts. Other small-map losses yield 0.59 and
     the top 0.75.
3. **Early fights on small maps turn into blowouts, for us only.**
   - Small map with a fight by r150: 34 of 67 are blowouts (0.51). With no fight: 7 of 28 (0.25).
   - The top wins 0.95 of the early fights it wins on trade, and its win rate is higher with a fight than without.
   - In our blowouts we bring **more** bodies and HP to the first fight (2.7 v 2.2 bodies, 1.26x the HP) and still lose
     the trade, 900 HP against 676.
4. **Not the causes:**
   - one opponent's opening: Kungarna 12/25, policy wonk 10/25, the rest 8-9/25;
   - the draft;
   - splitting or stacking;
   - isolation;
   - being outnumbered by 2+;
   - rushes (only a weak signal).

## Data and method

- **Games.**
  - `n47_tz116`: 150 games of tz-116 v the six UK band teams.
  - The top v the same six: `top_v_band` (119) + `uk3band` (24: Vvvvv / Ad Astra v policy wonk / Kungarna) + the 5
    band games in `top5_9nov`. That makes 148 games, 126 of them top wins.
  - All were already decoded. [guess: small drift] The top played the band's 7 Nov bots.
- **Classes** (n47): B = blowout (loss, share < 0.30, n 55); M = loss 0.30-0.40 (22); C = close loss >= 0.40 (35); W = win (38).
- **Map features** come from `analysis_8nov/regimes/feats.json`; "open tiles" = area − walls − holes. Choke width is new:
  the narrowest BFS level among tiles on near-shortest spawn-to-spawn paths, in the 25-75 % band.
- **Scripts** are in `~/tzunami_data/analysis_9nov/blow/`. All run with `python3 -I`, in one process, about 2 minutes
  for everything.

  | Script | Outputs | What it does |
  | --- | --- | --- |
  | `open.py LABEL..` | `op_*.pkl` | r0-300 per game: collected / gold / max HP at r100-300; every death with round, axis position, nearest-killer type, foes / allies within 5; enemy body-rounds in our third; contact; groups hit; map features |
  | `use.py` | `use_*.pkl` | r1-150 body time use, HP lost / dealt in contact, gem gains |
  | `fight1.py` | `f1_*.pkl` | isolation and the first fight: the first round with HP lost while an enemy champion is within 3, followed for 20 rounds |
  | `f2.py` | | actions inside that fight |
  | `conv.py` | | camp-hit mix by kind and zone. Its conversion columns are broken; ignore them. |
  | `summ.py`, `strat.py`, `usum.py`, `f1sum.py`, `comb.py` | `summ.txt`, `strat.txt`, `usum.txt`, `f1sum.txt`, `comb.txt` | tables |

- **Caveat.** "HP lost in contact" also counts camp damage taken while an enemy champion is within 3, so it is
  contested-farming damage as well as fight damage.

## 1. Predictors of a blowout, ranked [measured, n47; AUC = blowout v all other games]

| # | Predictor (readable by r150) | Split | Blowouts | AUC |
| --- | --- | --- | --- | --- |
| 1 | **Our collected at r150** | < 40: **28 / 45 (0.62)**; 40-130: 25 / 81; >= 130: 2 / 24 | B 50 v M 99 / C 88 / W 82 (top 123) | **0.75** |
| 2 | **Our deaths by r150** | >= 1: **28 / 46 (0.61)**; 0: 27 / 104 (0.26) | B 1.13 v 0.21-0.50 | 0.67 |
| 3 | **Map size (open tiles)** | < 1,500: **32 / 59 (0.54)**; 1,500-2,500: 9 / 36; 2,500-5,000: 12 / 25; >= 5,000: **2 / 30** | B 1,884 v C 4,065 / W 3,477 | 0.66 |
| 4 | **A fight by r150** (small maps) | fight 34 / 67 (0.51); none 7 / 28 (0.25). Large maps: 6 / 18 v 8 / 37 | first fight r62 | |
| 5 | HP lost in contact r1-150 | >= 3,000: 9 / 14; < 300: 21 / 76 | B 1,411 v C 465 / W 485 (top 1,252) | 0.66 |
| 6 | Groups we hit r1-150 (fewer is worse) | | B 5.1 v C 6.2 / W 6.3 / top 6.2 | 0.61 |
| 7 | Enemy body-rounds in our third | r1-150: B 35 v 20-26; r151-300: 45 v 22-34. First entry r156 v 172-232 | | 0.58 / 0.60 |
| 8 | Opponent | Kungarna 12 / 25, policy wonk 10 / 25, :3 / Claudus / QS2 8 / 25, RLP 9 / 25 | | weak |
| 9 | Draft | Every one of our drafts has Vesper + C&I. Their picks: Ren 6 / 12, Tavi 12 / 27, the rest 0.31-0.39 (small n) | | none |

- **Combined rule at r150:** a death by r150 **or** collected < 40 catches **39 of 55 blowouts**: 39 / 68 games (0.57),
  against 16 / 82 (0.20) for the rest.
- **On small maps:** collected < 50 at r150 gives 29 / 43 blowouts (0.67).
- **Income without deaths:** with no death and collected < 40 it is still 11 / 22 (0.50). Low income predicts a blowout
  on its own, not only through deaths.

**Not predictors** [measured]:

| Feature | B | Other classes |
| --- | --- | --- |
| Distinct groups hit r1-60 | 3.5 | 3.6-4.2 |
| Supports opening on Vesper's first group | 2.7 | 2.9-3.2 |
| Isolated body-rounds (no ally within 5), small maps | 0.21 | 0.19-0.22 (top 0.22) |
| Outnumbered by 2+ within 6 | 2 % | 0.5-1.5 % |
| Max HP ratio at r150 | 1.03 | 1.01-1.03 |
| Spawn walking distance | | non-monotone |

Choke width runs 8 (B) against 13 (C), but it is confounded with map size: within a size band it adds nothing visible.

## 2. What happens in the blowouts, r0-300 [measured]

**First deaths.** Our deaths by r200: B 1.51 a game, other losses 0.61, wins 0.39, top 0.80.

| | Ours in blowouts | Top |
| --- | --- | --- |
| Where (own / mid / far third) | **40 %** / 43 % / 17 % | 29 % / 59 % / 12 % |
| Foes / allies within 5 | 2.1 / 1.1 | 1.7 / 1.1 |
| Victims | Cassi 19, Issac 19 (linked), **Vesper 16**, HoR 11, Vendetta 11, Marcella 7 | |
| Killers | HoR 17, camps 16, Varg 10, Marcella 9, Vendetta 9, Ryth 6 | |
| Enemy deaths by r200 (we kill) | 0.76 | 1.11 (by the top) |

- **Vesper dies early in blowouts.** When she is our first death by r150, 8 of 11 games are blowouts. Her small-map
  gems by r150 are 32, against 61 in other games.
- **Where our early kills happen.** In our wins, 45 % of the enemy deaths by r200 are in our third: they came to us and
  lost.

**Income, r1-150 on small maps** (usum.py, conv.py):

| | Blowout | Other loss | Win | Top |
| --- | --- | --- | --- | --- |
| Gems gained | **54** | 98-118 | 91 | 131 |
| Their gems gained | 108 | 122-190 | 111 | 84 |
| Camp-hit share of body-rounds | **0.21** | 0.21-0.26 | 0.30 | 0.23 |
| Dead share | **0.08** | 0.03-0.06 | 0.02 | 0.05 |
| Gems per camp-hit round | **0.32** | 0.59 | 0.38 | **0.75** |
| Hit mix: wolf / gem cluster / mid zone | **0.64 / 0.05 / 0.23** | 0.54 / 0.11 / 0.18 | 0.60 / 0.04 / 0.27 | 0.50 / 0.11 / 0.36 |

Per body, gems by r150 on small maps, blowouts against other games:

| Vesper | Marcella | Vendetta | HoR | Cassi | Issac |
| --- | --- | --- | --- | --- | --- |
| 32 v 61 | 10 v 18 | 11 v 10 | 5 v 7 | 3 v 9 | 1 v 6 |

The top's supports take 17-42 each.

**The first fight** (fight1.py, f2.py; it starts at r62 in blowouts, r53 for the top on small maps):

| | Ours in blowouts | Top |
| --- | --- | --- |
| Bodies near: ours / theirs | 2.7 / 2.2 | 2.3 / 2.3 |
| HP lost / dealt in 20 rounds | 900 / 676 | 790 / 862 |
| Deaths: ours / theirs | 0.50 / 0.33 | 0.26 / 0.42 |
| Trade won | 25 % | 58 % |

- **Actions inside the fight are alike.** Champion hits 3.9 (theirs 4.5), casts 7.2 v 6.2, camp hits 4.2 v 4.6. One of
  our 2.6 bodies never hits a champion, against 0.7 of their 2.2.
- **So the losing trade is size and target choice, not contact micro.** This matches the opn / trade studies: micro
  changes did not move the first-exchange death rate.
- **Win rate after the first fight:**

  | First fight | Ours | Top |
  | --- | --- | --- |
  | Trade won | 0.16 | 0.95 |
  | Trade lost | 0.20 | 0.80 |
  | No fight by r150 | **0.34** | 0.76 |

  For us, any early fight is worse than none.

**Rush.** The band does come into our third more in blowouts: 35 body-rounds r1-150 against 20-26, and its first entry
is ~30 rounds earlier. But this is ~5 % of their body-rounds. It is a side effect of small maps, not a rush strategy:
no team stands out.

## 3. Causes, ranked [measured unless tagged]

| # | Cause | Count | Reading |
| --- | --- | --- | --- |
| 1 | **Small map** | 41 / 55 blowouts on < 2,500 open tiles | General, readable at r0. The top wins 0.90 there. |
| 2 | **Slow early income** | 28 / 45 with collected < 40 at r150 | Wolf-heavy hit mix, half the top's yield per hit-round, Vesper 32 gems v 61 |
| 3 | **Early deaths** | 28 / 46 with >= 1 death by r150 | 40 % in our own third; Vesper 16 of 83; camps kill 19 % |
| 4 | **Early fights we cannot win** | 34 / 67 small-map games with a fight by r150 | More bodies, losing trade, 25 % won |
| 5 | Band presence in our third | AUC ~0.6 | Weak; a consequence of 1 |
| 6 | Opponent or draft specifics | Kungarna +0.12 over base | Not actionable |

## 4. Build spec: `smap` (small-map opening), bots/tz/src [spec; untested]

**Aim.** On small maps, before r150, earn instead of trading.
- Supports open on zero-Strength clusters: gem first, gold second.
- Every body gives ground in a contact it is not already winning, instead of farming wolves through it.
- Vesper does not stand in mid alone before her first bank.

**Switch.** `static constexpr int smap = 0` in value.h, plus its knobs. At 0 the default build is byte-identical.

**Detection** (world.cpp, at init; a general feature, no map names):
- `W.open = w*h − blocked tiles`;
- `small = W.open < smap_open` (2,500), **or** `W.open / bodies < smap_opb` (500).

**Bits** (active only while `small && round <= smap_until`, 150):

1. **`smap & 1`, cluster-first pricing.**
   - **Where:** `plan_build` / `plan_choose` (bot.cpp ~1561 / 1804) and `choose()`.
   - **Groups:** price groups whose strongest camp has Strength 0 (gem / gold clusters) x `smap_clu` (1.6). Price wolf
     groups x `smap_wolf` (0.7).
   - **Supports:** a support never takes Vesper's current target as a follow (`follow_k` → 1.0) while a cluster group in
     our half is unclaimed.
   - **Target:** gem-cluster share of hits 0.05 → >= 0.11; wolf share 0.64 → <= 0.50.
2. **`smap & 2`, no farming in contact.**
   - **Who:** a body, within `fb` / `play_turn` before the WORK / p1 hold (bot.cpp ~4760-4790).
   - **Trigger:** an enemy champion within `reach_of(e) + 1`, my team's local power (ours within 5 v theirs within 6, the
     same measure as the `gate`) < `smap_pow` (1.3), and no `fin_commit`.
   - **Action:** stop the camp hit and step to the nearest ally, or out of reach by `find_escape`.
   - **Stay:** stay only to commit when the power is >= `smap_pow`.
   - This replaces "strike-and-farm through contact" on small maps only. Its contact HP is 1,411 in blowouts v 485.
3. **`smap & 4`, Vesper anchor.**
   - **Rule:** before her first bank, Vesper's goal groups are limited to axis position <= 0.55 (ours 0, theirs 1)
     unless >= 1 ally is within 4 of the group.
   - **Why:** her early deaths are 16 of 83, and her small-map gems fall from 61 to 32 in blowouts.

**KPIs** (decoded band games, small maps; `blow/usum.py`, `strat.py`):

| KPI | Now | Target |
| --- | --- | --- |
| Gems gained r1-150 (team) | 81 (B 54) | >= 100 |
| Gems per camp-hit round | 0.45 (B 0.32) | >= 0.55 |
| Our deaths by r150 a game | 0.47 (B 1.13) | <= 0.30 |
| HP lost in contact r1-150 | 1,170 | <= 800 |
| Blowout rate | 0.43 | <= 0.30 |
| Blowout rate, all games | 0.37 | <= 0.28 |

**Guards:**
- large-map games must replay identically (the switch is off there);
- band share does not fall.

**Order:** test bit 1 alone first (an income lever, with the least fight risk); then 1 + 2.

**Judge:** the local 51 % gate, then the band runner. Read the per-size split with `strat.py` on the new label.
