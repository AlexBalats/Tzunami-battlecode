# Yield per camp-hit round: why the top collects 2x our gems from the same camp time (9 Nov, agent)

**Question.** Against the same UK band the top teams collect about twice our gems (537 v 1,098 in losses on n29
[measured, summaries]), yet camp-hit time is close (22 / 18 / 16 % of body-rounds v 24.5 / 21 / 18.5 %). How much of
the gap is yield per camp-hit round, and why? Per champion, per camp type, per phase (r1-300, 301-600, 601-900).

**Answer in one line.** Yield, not time: gems per camp-hit round explain 83-105 % of the capture-gem gap in every
phase [measured]. In r1-600 the yield gap is **which tiles we hit**: gem-cluster tiles are 94 % / 68 % of it. In
r600-900 it is **damage per hit-round**: 121 v 174 [measured].

## Data and method

**Games** (decoded band replays already on disk, nothing downloaded):
- us: `tz107_big` (150) + `tz96_big` (150), v the six band teams on 8 Nov;
- top: `top_v_band` (119), the top four v the same six on 7 Nov.

`n23_tz107` is not decoded, so it isn't used.

**Caveats [guess]:**
- The top played the band's 7 Nov bots.
- The top's opponents skew to policy wonk and Kungarna. An opponent-weighted rerun (`--oppw`) gives the same picture.
- Robustness reruns: the 51 shared maps (`--shared`), and our losses only (`--loss`, 239 games).

**Scripts** are in `~/tzunami_data/analysis_9nov/yield/` (`python3 -I`, one process; ~60 s for all 419 games to r960):

| Script | What it does |
| --- | --- |
| `yield.py LABEL..` | every camp tile's HP drop each round, credited to the bodies that hit it that round (split by Strength / Focus); camp-hit body-rounds by champion and by the tile type hit; the fate of every unit of our damage; table rewards credited back to the damage on each captured tile; damage per attack ÷ Strength; per capture: first hit, kill, capture, hitters, hit body-rounds, active rounds, the taker's approach |
| `summ.py [--shared\|--loss\|--oppw] US.. - TOP` | the team, type, champion and capture tables, plus the log split → `all.txt`, `shared.txt`, `loss.txt`, `oppw.txt` |
| `split2.py [--shared\|--loss]` | additive split by group kind into time, speed and value per capture → `split_*.txt` |
| `pool.py` + `poolsum.py` | the gem-cluster pool: tiles taken by us / the band, tile-rounds sitting at full HP → `pool*.txt` |
| `pack.py` | heavy captures by number of hitters → `pack.txt` |
| `perteam.py` | key numbers per top team → `perteam.txt` |

**Decoder facts found here** [measured]:
- Round line `R[r]` is the state **before** round r's steps, and `R[r+1]` the state after them. `game.py`'s comment
  says the opposite. Scripts that pair round-r steps with `cp[r-1] → cp[r]` are off by one round.
- After the fix:
  - 1-1.5 % of HP drops match only a step labelled the next round (they are credited to it);
  - 0.1 % stay unexplained;
  - camps never heal while alive (0 HP rises in 10 games).
- Credited gems per 1,000 useful HP come out at the table values (wolf 3.0, elk 6.3, golem 7.4, gem cluster 59).
- Measured capture gems are 1.055x the table, from Prospector's +25 % on clusters.

**Definitions:**
- A camp-hit round follows `bodies.py`: a basic attack on a camp tile, or a damage / area / stun cast at or next to
  one.
- Phases are r1-300 / 301-600 / 601-900. Every figure is per game still running at the phase start.
- Gaps are top minus us.

## 1. The camp numbers

**[rules] GameRules.md table, [sdk] cambc.h:**

| Type | HP | Str | Gems | Gold | Respawn | Gems / 1k HP | Gold / 1k HP | Bot price r<150 (gems + 0.55 gold) | Price / 1k HP |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Wolf | 1,350 | 20 | 4 | 40 | 40 | 3.0 | 30 | 26 | 19 |
| Elk | 2,400 | 60 | 15 | 90 | 60 | 6.3 | 38 | 64.5 | 27 |
| Golem | 5,000 | 120 | 36 | 160 | 80 | 7.2 | 32 | 124 | 25 |
| Gem cluster | 120 | 0 | 7 | 0 | 50 | **58** | 0 | 7 | 58 |
| Gold cluster | 120 | 0 | 0 | 20 | 50 | 0 | **167** | 11 | 92 |
| Monolith | 20,000 | 200 | 200 | 300 | 150 | 10 | 15 | 365 | 18 |

**Rules that matter:**
- Captures take 5 rounds [rules]; 3 with the Capture emblem [BUILD_LOG engine facts].
- The SDK's Monster emblem is **+15 %** camp damage. The rules page says 10 %; the SDK wins.
- Prospector gives +25 % rewards from clusters [measured, BUILD_LOG].
- A gem-cluster tile carries ~20x a wolf's gems per HP.

## 2. The identity: time x yield [measured]

Capture gems = camp-hit body-rounds × gems per camp-hit round. The table is per game; cells read us / top.

| | r1-300 | r301-600 | r601-900 |
| --- | --- | --- | --- |
| Camp-hit body-rounds | 351 / 368 | 261 / 280 | 176 / 172 |
| Hit share of alive rounds | 0.231 / 0.243 | 0.185 / 0.202 | 0.150 / 0.169 |
| **Gems per camp-hit round** | **0.47 / 0.76** | **0.70 / 1.15** | **0.85 / 1.30** |
| Gold per camp-hit round | 3.0 / 3.3 | 3.7 / 4.9 | 3.9 / 6.9 |
| Capture gems (measured) | 157 / 286 | 200 / 355 | 186 / 268 |
| **Share of the log gap: hit time / yield** | 9 / 91 % | 12 / 88 % | −5 / 105 % |
| The same, losses only | 17 / 83 % | 20 / 80 % | 14 / 86 % |
| The same, shared maps | 13 / 87 % | 17 / 83 % | 1 / 99 % |

**Yield, split** (share of the log gap):

| Part | r1-300 | r301-600 | r601-900 |
| --- | --- | --- | --- |
| Damage per hit-round | 12 % | 34 % | 97 % |
| Share of our damage that ends in our captures | 8 % | 14 % | 25 % |
| Gems per useful HP (the type mix) | 72 % | 40 % | −16 % |

**Shift-share of gems per hit-round across tile types:**

| | r1-300 | r301-600 | r601-900 |
| --- | --- | --- | --- |
| Type mix | **+0.19** (gem tiles +0.20) | **+0.22** (gem +0.19) | +0.01 |
| Yield within type | +0.10 | +0.23 | **+0.43** (elk +0.13, gem +0.17, wolf +0.08) |

**Every top team shows it** (`perteam.txt`):

| | Top teams | Us |
| --- | --- | --- |
| Gem-tile share of hit-rounds, r1-300 | 9.7-14.1 % | 6.6 % |
| Gems per hit-round, r1-300 | 0.65-0.83 | 0.47 |
| Gem tiles taken, r1-300 | 21-34 a game | 10.8 |
| Damage per hit-round, r1-300 | 68-88 | 71 (level) |
| Damage per hit-round, r601-900 | 140-209 | 121 |

## 3. By camp type [measured]

Per game; cells read us / top. "Gems / hit" credits each captured tile's table reward back to the damage on it, so
wasted damage earns 0.

| r1-300 | Hit-rounds | Share | Dmg / hit | Dmg → our capture | Dmg → enemy capture | Gems / hit | Gold / hit | Credited gems |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Wolf | 179 / 170 | 51 / 46 % | 69 / 76 | 95 / 98 % | 5 / 2 % | 0.20 / 0.22 | 2.0 / 2.2 | 35 / 38 |
| Elk | 99 / 101 | 28 / 27 % | 72 / 75 | 96 / 99 % | 4 / 1 % | 0.44 / 0.47 | 2.6 / 2.8 | 44 / 48 |
| Golem | 8 / 13 | 2 / 4 % | | 86 / 95 % | 14 / 5 % | 0.61 / 0.50 | | 5 / 7 |
| **Gem cluster** | **23 / 43** | **6.6 / 11.8 %** | 69 / 75 | **83 / 97 %** | **16 / 3 %** | **3.4 / 4.3** | 0 | **79 / 187** |
| Gold cluster | 37 / 41 | 11 / 11 % | 73 / 77 | 92 / 98 % | 7 / 2 % | 0 | 11.2 / 12.7 | 0 (416 / 523 gold) |

| r301-600 | Hit-rounds | Share | Dmg / hit | Dmg → enemy capture | Gems / hit | Credited gems |
| --- | --- | --- | --- | --- | --- | --- |
| Wolf | 123 / 99 | 47 / 36 % | **91 / 124** | 6 / 2 % | 0.25 / 0.37 | 31 / 37 |
| Elk | 73 / 87 | 28 / 31 % | **110 / 136** | 7 / 1 % | 0.64 / 0.86 | 47 / 74 |
| Golem | 10 / 19 | 4 / 7 % | 183 / 141 | 19 / 2 % | 1.05 / 1.04 | 11 / 20 |
| **Gem cluster** | **23 / 38** | **9 / 14 %** | 74 / 84 | **13 / 3 %** | **3.6 / 4.7** | **84 / 179** |

| r601-900 | Hit-rounds | Dmg / hit | Gems / hit | Gold / hit | Credited gems |
| --- | --- | --- | --- | --- | --- |
| Wolf | 72 / 50 | **100 / 174** | 0.26 / 0.50 | 2.6 / 5.0 | 19 / 25 |
| Elk | 56 / 55 | **129 / 193** | 0.71 / 1.12 | 4.3 / 6.7 | 40 / 61 |
| Golem | 6 / 19 | 248 / 200 | 1.47 / 1.27 | | 10 / 24 |
| Gem cluster | 17 / 15 | 79 / 104 | 3.8 / 5.5 | | 66 / 85 |
| Gold cluster | 17 / 25 | 83 / 105 | | 11.3 / 16.6 | 187 / 419 gold |

**Where the credited-gem gap sits:**

| Phase | Gap | From gem tiles | From elk | Other |
| --- | --- | --- | --- | --- |
| r1-300 | +115 | **+108 (94 %)** | | wolves +3, golems +2 |
| r301-600 | +140 | **+95 (68 %)** | +27 | golems +9, wolves +6 |
| r601-900 | +73 | +19 | +22 | golems +14, monoliths +12, wolves +6 |

**What each side prioritises:**
- **The top swaps wolf hit-rounds for gem-tile hit-rounds:**
  - r1-300: wolves 46 v 51 %, gem tiles 11.8 v 6.6 %;
  - r301-600: wolves 36 v 47 %, gem tiles 14 v 9 %;
  - golems 4-11 v 2-4 %.
- **Value to time:** a gem-tile hit-round earns 3.4-5.5 gems, an elk hit-round 0.4-1.1, a wolf hit-round 0.2-0.5.
  Even with gold at the bot's price (0.55 gem early), a wolf hit-round is worth 1.3 and a gem-tile round 3.4+.
- **Gem tiles in heavy groups too:** the top's heavy captures hold 1.19 / 1.38 / 1.21 gem tiles v our 0.74 / 0.96 /
  1.11. Its elk groups with 4 hitters average 2.55 gem tiles in r1-300, ours 1.17. This is the "value per capture" gap
  below.

## 4. Damage per camp-hit round: stats, items, casts [measured]

| | r1-300 | r301-600 | r601-900 |
| --- | --- | --- | --- |
| Damage per hit-round | 71 / 76 | 100 / 122 | **121 / 174** |
| Strength at hit (team mean) | 52 / 50 | 78 / 81 | **94 / 122** |
| Focus at hit | 97 / 107 | 113 / 146 | 138 / 183 |
| Basic attacks per hit-round | 1.06 / 1.08 | 1.05 / 1.07 | 1.04 / 1.08 |
| Casts per hit-round | 0.095 / 0.086 | 0.100 / 0.086 | 0.102 / 0.078 |
| Overkill (estimate) | 7 / 11 % | 13 / 20 % | 18 / 27 % |

**By champion** (us / top, damage per hit-round and Strength at hit):

| | r1-300 | r301-600 | r601-900 |
| --- | --- | --- | --- |
| Vesper | 104 / 84, Str 94 / 77 | 246 / 224, Str 232 / 209 | 341 / 324 (level) |
| **Vendetta** | 85 / 100 | **112 / 187, Str 102 / 156** | **140 / 281, Str 131 / 248** |
| HoR | 64 / 69 | 67 / 86 | 75 / 115 |
| Marcella | 67 / 73 | 90 / 110 | 109 / 165 |
| Cassi | 57 / 59 | 58 / 73 | 59 / 89 |
| Issac | 52 / 53 | 52 / 61 | 53 / 82 |

**Monster emblem** [measured, inferred]: damage per single basic attack ÷ Strength, on single-hitter, non-kill rounds.
A ratio of 1.15 = the Monster emblem [sdk].

| Share of attacks at >= 1.12x Strength, r301-600 / r601-900 | Top | Us |
| --- | --- | --- |
| Vesper | 78 / 88 % | 45 / 63 % |
| Vendetta | 61 / 85 % | 7 / 20 % |
| Marcella | 39 / 70 % | 0 / 0 % |
| HoR | 44 / 67 % | 24 / 24 % (HoR's missing-HP passive) |
| Twins | 6-37 % | 0 % |

In the code: `item_table 3` puts Monster 5th on Vendetta, last on Vesper, and never on Marcella or HoR. `monster_early`
exists but is off.

**So:**
- **r1-300:** our damage is level (71 v 76).
- **r301-900:** we fall behind on Strength (Vendetta, the twins) and on Monster (×1.15). Vendetta's Strength gap is gold:
  our Vendetta earns 129 gold by r300 to the top's 417 (early_income.md).
- Casts and attacks per round are not the gap. Overkill is not ours: the top's is higher because it hits harder.

## 5. Waste: where our camp damage goes [measured]

| Our damage goes to | r1-300 | r301-600 | r601-900 |
| --- | --- | --- | --- |
| Our captures | 93.9 / 98.1 % | 89.5 / 96.9 % | 84.9 / 93.1 % |
| ... a capture by Vesper while another body hit | 35 / 13 % | 15 / 6 % | 11 / 6 % |
| **Enemy captures** | **5.8 / 1.7 %** | **7.7 / 2.1 %** | **8.1 / 3.0 %** |
| Killed, never captured | 0.1 / 0.0 % | 0.4 / 0.3 % | 1.9 / 0.7 % |
| Never killed (camp left unfinished) | 0.2 / 0.2 % | 1.5 / 0.3 % | 2.8 / 0.7 % |
| ... of that, at the game's end | 0.0 / 0.0 % | 0.8 / 0.3 % | 2.4 / 2.6 % |

- **The worst leak is gem tiles:** 16 % / 13 % / 10 % of our gem-tile damage ends in **band** captures (top 3-4 %).
  Golems leak 14-19 % (top 2-6 %).
- In total, waste is 8-25 % of the log gap. That is real, but it is not the main piece.
- The "to Vesper" row is a transfer inside the team, not waste. It is large on our supports in r1-300:

  | Body | Us | Top |
  | --- | --- | --- |
  | Vendetta | 48 % | 14 % |
  | HoR | 54 % | 17 % |
  | Marcella | 44 % | 4 % |
  | Cassi | 48 % | 23 % |
  | Issac | 46 % | 16 % |

## 6. Capture cycles: first hit to capture, hitters, whole-cycle value [measured]

Per game; medians where marked. All kinds:

| All kinds | Captures | Gems / capture | Hitters | Hit-rounds / capture | First hit → kill (med) | Kill → capture (med) | Taker's approach (med) | Gems per cycle body-round |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| r1-300 | 13.0 / 20.0 | 11.7 / 13.9 | 2.50 / 1.91 | 23.3 / 17.1 | 12 / 9 | 6 / 5 | 17 / 19 | 0.17 / 0.23 |
| r301-600 | 12.7 / 20.2 | 14.8 / 16.4 | 2.04 / 1.68 | 19.3 / 13.5 | 12 / 9 | 6 / 5 | 31 / 22 | 0.16 / 0.26 |
| r601-900 | 9.9 / 15.8 | 17.8 / 16.3 | 1.77 / 1.53 | 16.3 / 11.2 | 10 / 6 | 6 / 5 | 35 / 23 | 0.19 / 0.27 |

Gem-cluster groups:

| Gem-cluster groups | Captures | Hit-rounds / capture | Approach (med) | Cycle body-rounds | Gems per cycle body-round |
| --- | --- | --- | --- | --- | --- |
| r1-300 | **1.22 / 4.76** | 6.9 / 5.4 | **36 / 20** | 71 / 50 | 0.35 / 0.49 |
| r301-600 | **1.79 / 4.58** | 4.7 / 4.4 | **42 / 20** | 89 / 53 | 0.20 / 0.38 |

Wolf and elk groups:

| Wolf and elk groups | Wolf hit-rounds / capture | Elk hit-rounds / capture | Wolf gems / capture | Elk gems / capture |
| --- | --- | --- | --- | --- |
| r1-300 | 29.9 / 27.9 | 40.9 / 41.2 | 9.4 / 11.5 | 24.6 / 32.0 |
| r301-600 | 24.1 / 18.1 | 29.9 / 27.0 | 11.2 / 13.3 | 25.9 / 33.6 |
| r601-900 | 21.1 / 13.3 | 25.6 / 21.7 | 12.6 / 12.5 | 27.0 / 34.8 |

**What this shows:**
- **We walk twice as far to our gem clusters** (approach 36-42 v 20 rounds). The top chains clusters near where its
  bodies already are.
- The cycle is: the taker's approach + all hitters' hit-rounds + the wait × takers. Kill → capture is 6 v 5 rounds:
  the top's Vesper carries the Capture emblem. tz-117 has it now; these replays predate it.
- **Hitters:**
  - we put more bodies on each capture, and the kill is not faster. Wolves in r301-600 take 17-18 active rounds with
    1, 2, 3 or 4 of our hitters (bigger groups draw more hitters; `pack.txt`);
  - HP per body-round stays level as hitters are added: 72 / 68 / 67 / 69 on wolves, r1-300. Joining wastes little
    damage; the cost is what the joiner is not hitting.
- **Whole-cycle price:** at the bot's gold price (0.55 a gold early), a wolf cycle is worth ~0.72 gem-equivalents per
  cycle body-round, above the gem-cluster cycle's 0.35-0.49 [measured rates, bot price]. So the planner's choice is
  consistent with its own prices.
  - The wolf figure undercounts its cost: non-taker hitters' approach is not in it.
  - The top's twins earn the **same gold per hit-round as ours** (2.5 / 2.3 v 2.4 / 2.2) **and 60-90 % more gems**.
    The top did not pay gold for its gems.

## 7. The split of the gap [measured]

Additive (log-mean) split by group kind (`split2.py`): gems_k = hit-rounds on kind k × captures per hit-round ×
gems per capture. Table capture gems, r1-900 summed over phases.

**All games: 518 v 868 a game (+350, x1.68)**

| Part | Gems | Share | Where |
| --- | --- | --- | --- |
| More cycles, from more camp time | **+25** | 7 % | |
| More cycles, from camp time moved between kinds (the mix) | **+162** | 46 % | gem-cluster groups +116, golems +50, elk +25, wolves −24 |
| Capture speed (hit-rounds per capture within a kind) | **+86** | 25 % | wolves +50, gem +27 (our gem damage the band captures), elk +22; r301-900 damage per hit-round |
| Value per capture | **+77** | 22 % | elk +60, wolves +25: gem tiles attached to the heavy groups we pick |

**Losses only: 454 v 868 (+414, x1.91)**

| Part | Gems | Share | Where |
| --- | --- | --- | --- |
| More camp time | +72 | 17 % | |
| Mix | +186 | 45 % | gem +120 |
| Speed | +114 | 28 % | |
| Value per capture | +42 | 10 % | |

**Shared maps:** time + mix +204, speed +83, value +73 (gem +114). The same picture.

**So the 2x is:**
1. **More capture cycles**, ~55-60 %, nearly all **gem-cluster cycles** at level camp time.
2. **Capture speed**, ~25 %: mid/late damage per hit-round, and gem damage the band captures.
3. **Value per capture**, 10-22 %: gem tiles in the heavy groups we choose.

Gem tiles carry about **two thirds** of the whole gap: the mix, the gem speed term, and the gem-tile value in heavy
groups.

## 8. By champion: who makes the gap (gems per 100 alive body-rounds) [measured]

| | r1-300 | r301-600 | r601-900 | Gem-tile share of its hit-rounds | Its damage per hit-round |
| --- | --- | --- | --- | --- | --- |
| Vesper | 12.9 / 12.6 | 24.4 / 29.7 | 26.3 / 37.3 | 5-12 / 5-9 % | level until r600 |
| Vendetta | 10.9 / 18.3 | **12.6 / 30.5** | **12.9 / 32.9** | 6-8 / 7-9 % | **below from r300** |
| HoR | 13.0 / 18.9 | 12.0 / 19.2 | 9.5 / 17.8 | 6-7 / 7-8 % | below from r300 |
| **Marcella** | **8.3 / 15.1** | **8.9 / 17.7** | 10.3 / 15.6 | **6-10 / 12-19 %** | level until r300 |
| **Cassi** | **9.2 / 15.1** | **9.4 / 16.1** | 7.8 / 10.0 | **7-11 / 7-19 %** | **level** (57 / 59) |
| **Issac** | **10.2 / 18.9** | **9.1 / 16.9** | 7.9 / 13.3 | **8-12 / 14-20 %** | **level** (52 / 53) |

**Two separate problems:**

**1. The twins and Marcella, r1-600: target choice, not stats.**
- Their damage per hit-round equals the top's; their gem-tile share is half.
- Their camp damage ends in someone else's capture: 83-85 % for the twins in r1-300 (top 63-79 %).
- The twins alone are ~40 % of our camp-hit rounds, at 0.38 gems per hit-round (top 0.59-0.71).
- At the top's twins' rate they would add ~+75 gems by r600 and ~+95 by r900 [arithmetic on measured rates].

**2. Vendetta (and HoR), r301-900: damage.**
- Vendetta's Strength is 102-131 v 156-248, and she has no Monster emblem.
- At the top's rate she would add ~+70 gems r301-900 [arithmetic].

## 9. Gem clusters are new income, not a transfer [measured]

**The pool is far from used up** (`pool.txt`):
- In r1-300, gem-cluster tiles sit alive at full HP **64 % of all gem-tile rounds in our games, 63 % in the top's**
  (4,508 of 23.5 tiles × 300 v 5,231 of 27.6 × 300).
- Both teams together capture 33 gem tiles a game against us, 44 in the top's games.

**Who takes the gem tiles, r1-300 (tiles a game):**

| | Us | Top |
| --- | --- | --- |
| We / the top take | 10.8 | 27.5 |
| ... in the mid | 5.4 | 17.1 |
| The band takes | **22.3** | **16.2** |
| ... in the mid | **15.5** | **8.5** |

- Of the top's extra 16.7 tiles, ~6 come out of the band's share and ~11 come from tiles nobody took.
- r301-600 is the same: 12.9 v 27.4; the band 23.4 v 15.3.
- On shared maps: 10.8 v 27.8; the band 23.3 v 15.8.

**Vesper isn't on gem tiles** (5-12 % of her hit-rounds, the top's 5-9 %). A support gem loop does not take her
captures. `clu` bit 1 did take them: it moved Vesper's **gold** clusters 1.10 → 0.50.

## 10. The one change to build first: the twins' gem loop

**What.** Cassi and Issac stop following the crew. Each runs its own job on gem tiles: pure gem-cluster groups, and
the gem tiles of groups no ally targets. Every other body is unchanged.

**Where in bots/tz/src:**
- **`squad_of()`** (bot.cpp ~840). With `squad_table 1` and `RL(1)` off (`role_mask 6`), the twins sit in squad 0
  behind the crew leader (`pack_leader`). Give each twin its own squad, so `plan_build()` never reaches the follower
  branch for them: no leader target, no `follow_k` 1.5, no pack-share price.
- **`farm_vt()`.** For the twins, gold at a fraction of `value::gold(r)`, about 0.3. Their gold barely converts:
  Strength at hit is flat all game (Cassi 30 → 31, Issac 45 → 46), and they spent 29-51 gold by r300. Gems keep
  their full price, so gem tiles win their planner.
- **`hand_take_raw()`.** A gem group a twin cleared stays the twin's. No feed hand-off to Vesper for zero-Strength
  gem groups.

Everything sits behind one static constexpr switch, like `clu`.

**How it differs from `clu 9`** (queued). `clu` claims clusters, gold included, for every support. It keeps the
twins in the crew and their follow price on the leader's wolves.
- By the bot's own numbers, a twin follower's wolf price (pack share × 1.5) beats a solo gem cluster: about 1.2 v
  0.4-0.7 for a 2-tile cluster 5-15 tiles out [guess: a hand calculation through `farm_vt` / `plan_build`, not
  logged].
- Claims alone don't move the twins. This change does, and it leaves gold clusters to Vesper.

**KPIs** (`yield.py` + `summ.py` on the build's band replays):

| KPI | Now | Target | Top |
| --- | --- | --- | --- |
| **Twins' gem-tile share of hit-rounds, r1-600 (headline)** | 7-11 % | >= 15 % | 13-20 % |
| Twins' gems per 100 alive body-rounds, r1-300 / r301-600 | 9-10 / 9 | >= 14 | 15-19 / 16-17 |
| Team gem tiles captured, r1-300 | 10.8 | >= 18 | 21-34 |
| Team gems per camp-hit round, r1-300 | 0.47 | >= 0.60 | 0.65-0.83 |
| Gem-tile damage ending in band captures | 16 % | <= 8 % | 3 % |

**Guards:**
- The twins' gold per hit-round (2.2-2.4) and their deaths by r300 (0.55) must not get worse.
- Vesper's gems + gold per 100 alive body-rounds must stay within 10 % (else it is a transfer).
- The band's gem tiles against us (22.3 by r300) should fall.

**Rough size** [guess: measured rates applied to a +8-point mix shift]: ~11 twin hit-rounds a game moved to gem tiles
by r300. That is +35-40 gems by r300, about 30 % of the r1-300 capture gap.

**Second, separately: damage per hit-round in r301-900.** The Monster emblem early (`monster_early` 1, already built)
plus Strength on Vendetta. It targets the "speed" quarter. Vendetta's Strength is mostly an income problem, which the
gem loop feeds.

**Not tested** [guess]: whether it wins on the band. Mid gem tiles are where the band is. Our twins already die
0.49-0.55 times by r300, the same as the top's, but solo twins in the mid are the risk to watch.
