# regimes: map-feature regimes where tz-66 loses gem share, what the band and the top do there, and rules (8 Nov)

**Data.**
- Outcomes come from the platform summaries, cached in `scrims/sum/`. They cover:
  - tz66_big, tz55_big, tz64_big, tz62_big, tz38_big and big32: 6 × 150 games on the band map set;
  - f13_tz66, f13_tz55, f13_tz64, f13_tz69 and f13_tz38: 5 × 90 games on the fresh map set.
- Where there is no summary I used the decoded-replay summaries (next66 `ext.py`): top_v_band (119 games) and
  top3_6nov (150 games, extracted for this study).
- Behaviour comes from the decoded replays of tz66_big, top_v_band and top3_6nov.
- Map features come from two sources:
  - the map files, read through the engine WASM (`mapfeat.mjs`: size, picks, walls, holes, altars, spawn area);
  - the r0 `cp` of a decoded replay of each map. The map file stores only half the camps on symmetric maps.
- All 128 pool maps are covered.

**Rules followed.** No games, no judges, no bot edits. I read only `bots/tz/src` (draft.cpp, value.h, and parts of
bot.cpp and world.cpp) and no other team's code. Tags: [measured] = counted here; [guess] = inference or estimate.

**Shares.**
- `fin` = our tributed share at the end (ours / both). `c300` = our collected-gem share at r300.
- Means across labels: tz-66 band fin 0.33, fresh 0.34; the top v band fin 0.69.

## 0. Headline

1. **Map identity matters for us, and it is our weakness, not the band's strength** [measured].
   - Per-map, opponent-adjusted share is reliable for our builds. On the 44 maps in both sets, the band-set mean and
     the fresh-set mean correlate at Spearman 0.65 for c300 and 0.62 for fin.
   - It is anti-correlated with the top's per-map share against the same band: −0.30 for c300, −0.31 for fin.
   - The maps where we fall behind are maps where the top beats the band most easily. Simple features explain only
     ~5–15 % of game-level variance (opponents dominate), but the map-level signal is stable.
2. **Two physical axes predict our deficit.** Both hold on the 22 fresh-only maps, which no tz build ever played on
   the band set [measured, `mapfit.py`, map-level Spearman with fin; columns all / band / fresh / fresh-only].

   | Axis | Feature | Spearman: all / band / fresh / fresh-only |
   | --- | --- | --- |
   | (a) Where the gems are | `home_gem_frac` (share of the map's gem rate in groups nearer our spawn: walking distance d_own / (d_own + d_opp) < 0.42) | +0.32 / +0.29 / +0.39 / +0.38 |
   | | `home_gold_frac` | +0.26 / +0.16 / +0.37 / +0.53 |
   | | `mid_gem_frac` | −0.29 / −0.26 / −0.41 / −0.21 |
   | (b) Map size | `sd_cheb` (spawn distance; c300) | +0.31 / +0.24 / +0.43 / +0.41 |
   | | `open_per_body` (fin) | +0.29 / +0.30 / +0.21 / +0.19 |

   - The top's per-map share runs the other way on size: −0.25 to −0.34.
   - The **count of pure gem groups is not robust.** It is −0.24 overall but +0.07 on fresh-only maps, so rules keyed
     on it (`gem_map_n`, `gem_runner`, `gem_marcella`) used the wrong feature: what matters is *where* the gems are,
     not how many groups there are.
3. **The worst regimes** (cuts at pool medians; fin share) [measured]:

   | Regime (pool maps) | tz-66 band | tz-66 fresh | tz builds band | tz builds fresh | top v band |
   | --- | --- | --- | --- | --- | --- |
   | **B: home-poor (`home_gem_frac` < 0.25) & compact (`sd_cheb` < 45)** (41) | **0.20** | **0.31** | **0.21** | **0.27** | 0.73 |
   | C: home-poor & large (24) | 0.31 | 0.30 | 0.34 | 0.30 | 0.71 |
   | D: home-rich & compact (41) | 0.39 | 0.37 | 0.33 | 0.33 | 0.72 |
   | E: home-rich & large (22) | 0.45 | 0.37 | 0.40 | 0.41 | 0.60 |
   | **A4: 4 picks & map gold < 1,400** (21) | **0.23** | 0.34 | **0.18** | **0.26** | **0.78** |
   | A5: 5 picks & map gold < 1,400 (38) | 0.30 | 0.33 | 0.30 | 0.32 | 0.66 |
   | B ∩ gold-poor (26) | 0.18 | 0.31 | 0.19 | 0.27 | 0.78 |

   - "Map gold" = Σ `gold_value` over camp groups with no monolith, both halves.
   - In C our c300 is fine (0.43). C is a late fade.
   - tz-66 on the fresh set is flatter than the other builds: gold-poor 0.34 v rest 0.34, A4 0.34. The A evidence for
     tz-66 itself is weak; see §3.
4. **What the band and the top do differently** (detail in §2):
   - **Drafts.** Every top team uses one map rule, and we break it:
     - on gold-poor maps they draft **Marcella, not Vesper**;
     - on gold-rich maps they draft Vesper, not Marcella;
     - they rarely take both;
     - the rule separates their Vesper-only from their Marcella-only drafts at AUC 0.82 on all team sizes, 0.92 on
       4 picks;
     - we always draft Vesper, and on 3 and 5 picks Marcella as well.
   - **In B they go to the middle early and take the big mid gem groups:**
     - their first mid capture comes at r73 (band) and r78 (top3), ours at r123;
     - their first 6 captures hold 149 / 153 gems, ours 70;
     - by r600 the band takes 219 gems a game from mid groups we never reach, plus 145 from mid groups we reach
       first and then lose;
     - we hold 21 % of the mid groups we reach first; the top holds 68 %.
   - **In C the top out-farms on tempo and gold:**
     - 25 captures by r300 v our 17;
     - 4,000 gold by r600 v our 2,627;
     - max HP 10.0k v 7.8k at r600.
5. **Proposals** (§3):
   - **Rule 1 (draft): the carry by map gold** (the top's rule, one cut). Cleanest and cheapest; test the 4-pick half
     first.
   - **Rule 2: B-maps (home-poor and compact) open to the middle's gem groups** (opening target, gold priced lower
     before r300, mid gem jobs as pack jobs).
   - **Rule 3 (C, lower confidence): tempo on large home-poor maps.**
   - Expected sizes are small [guess]: +0.005–0.015 overall share each, concentrated on 16–32 % of maps.
   - Validation uses the determinism of band games: a regime-gated rule leaves every other game bit-identical.

## 1. Features and the fit (`features.py`, `fit.py`, `buckets.py`, `model.py`, `mapfit.py`, `twoway.py`)

**Features**, all computable at the draft or at r0 from `cambc::map`:
- picks; area; open tiles per body;
- spawn distance, both walking and Chebyshev;
- altars: count, walking distance from spawn, nearer-mine count;
- group counts by kind (gold, gem, mix, wolf, elk, golem, monolith);
- gem and gold rate per round, value / (respawn + 10), by zone. A zone is the walking-distance ratio from both
  spawns: home < 0.42, mid 0.42–0.58, far > 0.58. Monolith groups are excluded;
- gem-cluster gem rate v monster gem rate;
- gems and gold within 12 and 20 walking tiles;
- biggest pure gem group.

**Game level** [measured, `out_fit_*.txt`]:
- The best single features reach |ρ| ≈ 0.2–0.3 for tz-66 on the band set, and somewhat less on fresh.
- Fit on the band set and tested on the fresh set, linear models reach out-of-sample R² ≈ 0.0 on c300 and ≈ 0.06 on fin.
- The coefficients keep their sign on the fresh set but shrink. For fin with `midgem + log(open per body)`:
  `midgem` −0.18 on the band set v −0.12 fresh, `lopb` +0.069 v +0.061.
- Game noise (the opponent, the side) dominates. Regimes are a level effect of ~0.1–0.2 share, not a predictor of
  single games.

**Map level** (opponent-adjusted residual, mean over 11 tz labels; `out_mapfit_*.txt`) [measured]:
- c300: `mid_gem_frac` −0.32 and `sd_cheb` +0.31, both holding on fresh-only maps (−0.39, +0.41).
- fin: `home_gem_frac` +0.32, `goldrate_home` +0.30, `open_per_body` +0.29. Fresh-only: +0.38, +0.41, +0.19.
- The top's per-map residual has the opposite sign on size (`open_per_body` −0.31, area −0.34) and none on home gems
  (+0.01).
- The two axes are nearly independent: Spearman(`mid_gem_frac`, `sd_walk`) = −0.09.

**Monotone checks**, tertiles of `home_gem_frac` (fin, low → high) [measured]:
- tz-66 band 0.21 / 0.35 / 0.43; tz-66 fresh 0.31 / 0.36 / 0.35;
- builds band 0.25 / 0.33 / 0.36; builds fresh 0.28 / 0.32 / 0.35;
- top v band 0.74 / 0.64 / 0.71.

Small maps (`sd_walk` < 39) give c300 0.35 / 0.40 / 0.31 / 0.35 against 0.41–0.43 on large maps. The top is at 0.63
on small maps and 0.57 on large ones.

## 2. The worst regimes: us v the band v the top

### 2.1 Regime B: home-poor & compact (41 pool maps; tz66_big 42 games, top_v_band 33, top3 46)

Per game, by r300 (`compare.py 300` → `out_compare300.txt`) [measured]:

| | us tz-66 | band v us | top v band | top3 |
| --- | --- | --- | --- | --- |
| Capture gems | **122** | 326 | 338 | 281 |
| ... mid third | **56** | 232 | 191 | 166 |
| ... from pure gem groups | **47** | 216 | 196 | 110 |
| Capture gold | 1,123 | 1,071 | 992 | 1,203 |
| ... own third | **814** | 518 | 616 | 656 |
| Captures | 13.5 | 17.1 | 14.4 | 15.8 |
| First mid capture (round) | **123** | 73 | 116 | 78 |
| Gems from the first 6 captures (`opening.py`) | **70** | 149 | 153 | 130 |
| Gem-group captures among the first 6 | **0.5** | 1.1 | 1.4 | 1.1 |
| Banked by r300 | 67 | 235 | 282 | 193 |
| Deaths (bodies) r300 / r600 | **3.2 / 5.8** | 1.5 / 2.6 | 1.9 / 3.5 | 2.8 / 6.3 |
| Our deaths in our own third by r600 | **1.8** | 0.6 | 1.0 | |
| Camp-hit % with an enemy 5–8 away | **12.4** | 21.6 | 17.2 | 20.3 |
| Walk-away % with an enemy 5–8 away | 26.0 | 21.8 | 21.2 | 20.0 |

- **On these maps the value sits in the middle's pure gem clusters (120 HP a tile), and they go there first.**
  - The band's opening is gold at home plus gem groups in mid.
  - Ours is gold and wolves at home; we reach mid 50 rounds later.
  - Big pure gem groups (≥ 40 gems) in mid by r300: band 0.6 captures for 136 gems a game, us 0.0 for 11
    (`biggem.py`).
- **Mid cycles by r600** (`race.py` → `out_race600.txt`; per game; win % in brackets; gems ours / theirs) [measured]:

  | Cycle type | Us v band, R1 | Top v band, R1 |
  | --- | --- | --- |
  | Only we reach | 5.8 [100 %], 58 / 0 | 8.2, 199 / 0 |
  | We first | **5.9 [21 %], 36 / 145** | 4.5 [68 %], 156 / 60 |
  | They first | 3.6 [30 %], 17 / 46 | 3.0 [75 %], 69 / 20 |
  | Only they reach | **13.0, 0 / 219** | 4.7, 0 / 120 |

  - In B the race (only-they cycles) and contact (we-first-and-lose cycles) cost about equal amounts: 219 and 145 gems.
  - The race share here is larger than in D or E (only-they 11.2 and 9.7). Contact is general (24–38 % across
    regimes) but costs most here, because B has the most contact body-rounds: 193 within 5–8 and 197 within 5, v
    95 / 101 in E.
- **Deaths.** Our twins carry 1.26 twin deaths a game by r600, and our home is invaded: 1.8 deaths a game in our own
  third v the band's 0.6.

### 2.2 Regime A: gold-poor maps, and the drafts (`drafts.py`, `carry.py`, `carryauc.py`, `bodies.py`)

**The top's carry rule** (top_v_band + top3_6nov; Vesper-only v Marcella-only drafts) [measured]:
- It holds on all team sizes. Each team switches at about this cut:
  - Fish: M100 below a gold rate of 16, V100 at ≥ 34;
  - Mite: V from a gold rate of ~10;
  - stellar best girl: V from ~16;
  - BattleCats: Marcella throughout on gold-poor maps.
- One cut on total map gold (Σ `gold_value` over non-monolith groups) of **1,300–1,500 separates them**, with
  accuracy 0.71 on 5 picks, 0.87 on 4 and 0.76 on 3.
- AUC: 0.76 on 5 picks, 0.91 on 4 picks, 0.82 on all.
- The band shares the rule (Spearman of Vesper with the map's gold rate +0.33 on 5 picks, +0.30 on 4), but always
  takes Marcella on 5 picks.

**Modal top drafts:**
- 4 picks, gold-poor: **C&I / HoR / Marcella / Vendetta** (16 of 47).
- 4 picks, gold-rich: C&I / HoR / Vendetta / Vesper (6 of 8; this is our table-7 draft).
- 5 picks, gold-poor:
  - C&I / HoR / Marcella / Vendetta / Willow (10 of 69), or C&I / HoR / Marcella / Prism / Willow (8);
  - Vesper with Tavi still appears (13: Mite).
- 5 picks, gold-rich: C&I / HoR / Tavi / Vendetta / Vesper (31 of 107), or Vesper with Willow (19).
- The top almost never has both carries on 5 picks: VM 8–16 % for sbg and Mite. We always do.

**Per champion, 4-pick gold-poor maps** (cap gems all game / by r300; gold all game) [measured]:
- our Vesper 159 / 50, 1,427 gold;
- the band's Marcella 412 / 203, 2,172 gold;
- the top's Marcella 315 / 110, 1,993 gold;
- Prism (band 430 / 247, top 448 / 223) is the best farmer per pick there.

On 5-pick gold-poor maps our Marcella takes 103 gems (the band's 282) because Vesper is the first taker.

**Our results** [measured]:
- Builds on the band set: gold-poor fin 0.26 v rest 0.36. Builds on fresh: 0.30 v 0.34.
- tz-66: 0.30 v 0.36 on the band set, but 0.34 v 0.34 on fresh.
- A4 is the worst cell for builds on the band set (0.18) and the best for the top (0.78). tz-66 fresh A4 is 0.34
  (12 maps, 18 games).

### 2.3 Regime C: home-poor & large (24 pool maps; tz66_big 30 games)

By r600 [measured, `out_compare600.txt`]:

| | us tz-66 | band | top v band | top3 |
| --- | --- | --- | --- | --- |
| Gold earned | 2,627 | 2,922 | 4,000 | 4,619 |
| Gold-group captures | 20.7 | 21.5 | 32.0 | 21.1 |
| Team max HP | 7,780 | 8,750 | 10,008 | 10,171 |
| Capture gems | 218 | 312 | 366 | 478 |

By r300:
- captures 17.3 v the top's 25.1;
- first mid capture r118 v r72;
- mid groups only the focus reached by r600: ours 9.2 a game, the top's 16.6.

This is tempo and coverage, not contact: contact cycles are rare here (2.7 + 1.6 a game). Deaths 2.6 by r600,
level with the top's 2.7. Map gold is not low here (median 1,630).

## 3. Rules (regime-conditional; each computable at the draft or r0)

### Rule 1: the carry by map gold (`draft.cpp`)

- `map_gold` = Σ over `cambc::map::camp_groups()` with no monolith camp of `gold_value()`. This is the whole map,
  both halves; draft.cpp already loops over the groups.
- If `map_gold < 1400`: no Vesper. Then:
  - **4 picks:** Marcella / Vendetta / HoR / C&I (the top's modal; our table 7 is the gold-rich version).
  - **5 picks:** Marcella / Vendetta / HoR / C&I / Willow (the top's modal Marcella comp). Variant: keep Marcella /
    Vendetta / HoR / C&I + Prism.
  - **3 picks:** unchanged (Vesper / Marcella / C&I). Our 3-pick gold-poor fin is 0.38, and the top's 3-pick rule is
    mixed.
- With Vesper absent, Marcella must get `taker_rank` 6: the Vesper-only tweaks (`carry_bias`, `carry_safe`) test
  `>= 6`, and the feed rule needs a carry. Implement it as `marcella_taker` set automatically when Vesper is not drafted.
- **Physical motivation.**
  - Vesper's edge is +33 % camp gold, which scales with map gold.
  - Marcella's gold comes from tributed gems (2 per gem [rules, per the code comment in bot.cpp]), which does not.
  - The cut is the top teams' own (one parameter, not fitted on our results).
- **Expected [guess]:**
  - A4 (21 maps, 16 % of the pool): +0.03–0.06 fin share if our Marcella-carry reaches half of the band's Marcella
    output over our Vesper's (+120 gems a game);
  - A5: ±0.02 (Willow has failed as a global swap before; untested gold-conditioned);
  - overall about +0.005–0.015 share.
  - Risk: our support line farms a third of the top's per pick. The carry swap does not fix that.

### Rule 2: B-maps open to the middle's gem groups (planner / `value.h`)

- **Regime test at r0.**
  - `home_gem_frac` = Σ gem_value / (respawn + 10) over non-monolith groups with d_own / (d_own + d_opp) < 0.42, over
    the same sum for all groups.
  - Use walking distances: Chebyshev agrees on only 101 of 128 maps at the 0.25 cut (Spearman 0.71). d_own comes from
    the home field; d_opp needs one BFS from `ehome`, or the group fields.
  - B = `home_gem_frac < 0.25` and Chebyshev spawn distance < 45.
- **In B, before r300:**
  - (a) The opening pack target (`opening_end`) is the best mid pure-gem group by value / ETA, not the nearest home
    group.
  - (b) Gold is priced ×0.6 (`gold_r150` 0.55 → 0.33), so a gem cluster (7) outranks a gold cluster (20 × 0.33 = 6.6).
    Revealed preference: in every regime the top's first 6 captures hold 1.3–1.6 gem groups to our 0.3–1.0 (B 1.4 v 0.5).
  - (c) Mid gem jobs ≥ 25 gems are pack jobs (`p2_mask` 4, `race_gems`), so the first arrival is not a lone body.
    We win 21 % of mid groups we reach first; the top wins 68 %.
- **Physical motivation.** On a map whose gems sit between the spawns and whose spawns are close, every gem is
  contested. Arriving first with company is the only way to take it. Home gold is safe but does not score.
- **Expected [guess].**
  - Halving the race loss (only-they 219 → ~110 gems by r600) at our current contact rate is about +0.03–0.05 fin share
    on B (32 % of maps), so ~+0.01–0.015 overall.
  - It will not transfer fully without better contact behaviour: we die 2.2× the band's rate in B (5.8 v 2.6 a game by
    r600).
  - p2 (race pricing) lost locally in every form as a global switch. B is where it should pay, and where the race loss
    is largest.

### Rule 3 (lower confidence): tempo on C-maps (home-poor & large)

- C = `home_gem_frac < 0.25` and spawn distance ≥ 45. There the top captures +45 % more groups by r300 and earns +52 %
  gold by r600.
- Candidate levers: a weaker `plan_near` (value over nearness) and more independent farmers (no squads) while no enemy
  has been seen.
- I have no direct measurement that the top splits more there. bodies-per-capture is ~1.02 for everyone, so this is a
  [guess] and the last to test.

### What not to do

- No rule keyed on the *count* of gem groups (its sign flips on fresh-only maps).
- No per-map tuning of the 0.25 / 45 / 1,400 cuts against our own results. They come from pool medians and the top's
  draft behaviour.

## 4. Validation without overfitting

1. **Band games are deterministic** (BUILD_LOG). A regime-gated rule leaves every out-of-regime game bit-identical to
   tz66_big's.
   - Check that the non-regime games replay identically: a free null test of the gating.
   - Test the paired share only on the regime's games: A4 25, A5 36 and B 42 games in tz66_big. That is less noise
     than a 150-game CI diluted by unchanged games.
2. **Then the fresh set.** f13_tz66 regime games: A4 18, A5 24, B 31.
3. **Then fresh-only maps**, which no band-set game saw: A4 4 maps, B 9.
4. **Then the 19 pool maps** that no band label has played. Local judge only, as a sanity check (it does not predict
   the band).
5. **Monotone check.** A real rule's gain should grow as the feature moves into the regime:
   - Rule 2: larger at `home_gem_frac` < 0.15 than at 0.15–0.25;
   - Rule 1: larger at map gold < 900 than at 900–1,400.
6. **Run one rule per stage.** Rule 1's 4-pick half is the cleanest first test: one draft line, 21 maps, the top's own
   rule. Keep a rule only if its regime-games share CI clears 0 on the band set and is not negative on the fresh set.
7. **Thresholds are not re-tuned after seeing results.** If the cut needs moving, move it to a pool quantile, not to the
   best value on our games.

## 5. Scripts and outputs (`scratchpad/diag/regimes/`)

| Kind | Files |
| --- | --- |
| Map reading | `mapfeat.mjs` (map files through the engine WASM → `mapfile.jsonl`); `features.py` (→ `feats.json`, `groups.json`) |
| Game outcomes | `outcomes.py` (→ `games.json`) |
| Fits | `fit.py`, `buckets.py`, `model.py`, `mapfit.py`, `twoway.py`, `regtab.py` |
| Behaviour | `compare.py` (`compare_300.pkl`, `compare_600.pkl`), `opening.py`, `race.py`, `biggem.py`, `deaths.py` |
| Drafts | `drafts.py`, `draftfeat.py`, `carry.py`, `carryauc.py` (→ `extra.json`), `bodies.py` |
| Outputs | `out_*.txt` |
| Inputs reused | The top3_6nov summary pickle was extracted with `../next66/ext.py` (→ `../next66/summ_top3_6nov.pkl`). |
