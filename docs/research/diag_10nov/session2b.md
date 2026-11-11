# session2b: where stack A3 still dies and still loses share (10 Nov, round 2)

Research-and-design session for the lock day. No tests, uploads or merges were made from here. Tags: [measured] =
decoded band replays; [code] = read in `bots/_stkA5`; [rules] / [sdk]; [guess].

**Final version (16:00).** A3 (`tz184_big`), A2 (`tz182_big`) and the base (`p83_m2`, v281) are decoded in full:
**195 paired games** each (82 tiny). v1 (15:22) used 90 pairs. On 195 every direction held and the sizes moved
slightly. A2 is in §8.

## Short answer

| # | Cause (A3 v base, 195 paired band-panel games) | Size [measured] | Fix (`bots/_s2b`, switch `s2b`) |
|---|---|---|---|
| 1 | **Escape recalls into a chaser** (new with `bankx 2`). A3 starts a recall with an enemy within 6 **11.9 times a game** (base 3.9). When an enemy within 6 was closing (6.2 starts a game), only 16-33 % arrive; 66-80 % are cancelled a turn later by the dth-2 abort, and the hurt body has stood still beside its chaser. | **Died recalling 0.04 → 0.49 a game (+0.46 ± 0.07, sig)**, tiny 0.07 → 0.54. That is all of A3's rise in deaths (+0.28 episodes, +0.49 raw, n.s.). | **Bit 1:** no escape recall while a visible enemy within 6 is closing on me. The body flees that turn and may recall on a later one. |
| 2 | **Chip and leave in the mid, and the "leave to fight" part no stack has touched** (0.76 a game in the base and in A2). We hit live contested mid groups, leave them, and the opponent captures them: **2.2 groups and 84 gems a game** (base 2.4 / 89). A3 cut the fleeing leaves (−0.28, sig); the leaves to fight an enemy went 0.76 → 0.95 a game (+0.18 ± 0.11, n.s.), those with the enemy more than 3 tiles away 0.49 → 0.65; tiny maps 0.62 → 0.89. | Mid captures, A3: ours 316 v theirs 458 gems a game. Tiny: 330 v 456. On tiny maps that gap is **6x the bag gap** (98 v 77). A3 moved them +38 (sig) / −21. | **Bit 2, "work through":** a body holding its live group in contact keeps the hold when a join / answer / opener / hunt commit targets an enemy out of its attack range. Finisher, stunned-target and execute commits still fire. |

**Code:** both bits are in `bots/_s2b` (`_stkA5` + `s2b`).
- At `s2b=0` the release `bot.wasm` is **byte-identical to `bots/_stkA5`'s** (cmp).
- `s2b=3` compiles (`bots/_s2b_3`).
- Nothing was run.

**Band lines** (`<A5>` = `robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11 endx=3`):
- `s2b 1: no escape recall with a closing chaser|_s2b|<A5> s2b=1|all` (the safer one: a fix of a measured fault)
- `s2b 3: + work through (no chase off a held group)|_s2b|<A5> s2b=3|all`. Bit 2 changes fights: read **kills**
  along with share, since A3's kills were +1.35 (sig) and bit 2 sends fewer bodies to fights.

## 1. Data and definitions

| Label | Build | Decoded | Wins |
|---|---|---|---|
| `tz184_big` | stack A3 (v304) | 195 / 195 | 69 |
| `p83_m2` | base v281 (`_m2`) | 195 / 195 | 49 |
| `tz182_big` | stack A2 (v302) | 195 / 195 | 63 |

**Pairs:** same opponent, group, map and side. Paired sanity check against the platform metrics: share +0.08 (sig),
win +0.10, kills +1.35 (sig). These match BUILD_LOG's stage 184.

**Definitions:**
- **Episode:** a death's episode starts at the first round of the unbroken run, going back from the death, with an
  enemy within 8 (capped at 40 rounds). The **engagement** is the first round of it with an enemy within 5.
  "Walked in" means the victim's own move closed the gap at the engagement; "they walked in" means the enemy's did.
- **Twins:** Cassi and Issac die together [sdk: "dies when Issac dies"]. A twin death counts as one episode, with
  both bags. Raw deaths (the platform metric) count both bodies.
- **Channels:** decoded round lines carry `chy` (1 = recall, 2 = tribute) and `cht` (turns left) [measured].
  - `cht 4` is the end-of-turn pre-start, cancelled at the next turn's start.
  - A real recall is `chy 1` with `cht <= 3`. It arrives 3-4 rounds after its start [measured].
- **Zones:** own / mid / their = the share of the way from our spawn to theirs: < 0.4 / 0.4-0.6 / > 0.6.
- **Tiny:** `cls_tiny.txt` (< 1,500 open tiles), 82 of the 195 games.

## 2. Where A3 still loses share (A3 games, us v them) [measured]

| Gems a game (A3, 195) | All | Tiny (82) | Non-tiny (113) | Tiny losses (55) |
|---|---|---|---|---|
| Share | 0.52 | **0.48** | 0.55 | 0.23 |
| Banked, us / them | 570 / 767 | 536 / 800 | 595 / 743 | 335 / 952 |
| Captures, own zone, us / them | 309 / 285 | 255 / 223 | 348 / 331 | 225 / 254 |
| Captures, **mid**, us / them | **316 / 458** | **330 / 456** | 305 / 459 | **198 / 525** |
| Captures in the taker's far zone, us / them | 26 / 38 | 38 / 58 | 16 / 24 | 28 / 77 |
| Bag lost at death, us / them | 87 / 92 | **98 / 77** | 79 / 103 | 106 / 49 |
| Lead (banked + carried), r150 / r300 / r600 | −22 / −69 / −80 | −39 / −98 / −150 | −10 / −48 / −29 | −62 / −143 / −283 |
| Team max HP minus theirs, r300 / r600 | −39 / −525 | −227 / −753 | +98 / −359 | −604 / −1,962 |

**A3 minus base, paired** (* = beyond 2 se):

| | All (195) | Tiny (82) | Non-tiny (113) |
|---|---|---|---|
| Share | **+0.08*** | +0.08 (se 0.04) | **+0.08*** |
| Win | **+0.10*** | **+0.11*** | +0.10 |
| Our mid captures (gems) | **+38*** | +56 (se 32) | +25 |
| Their mid captures | −21 | **−51*** | +2 |
| Their deaths (raw) | **+1.35*** | **+1.90*** | +0.96 |
| Their bags lost (gems) | **+32*** | +16 | +44 |
| Our deaths raw / episodes | +0.49 / +0.28 (n.s.) | +0.65 / +0.39 | +0.38 / +0.21 |

- **Tiny maps:** the mid capture gap (−126 gems a game) is 6x the bag gap (−21). Tiny losses are decided by r300:
  the mid is 198 v 525 and team max HP is −604.
- A3's gain comes from kills (their bags +32) and from the mid.

## 3. Cause 1: escape recalls into a chaser

**Real recalls, by nearest enemy at the start** [measured]:

| A game: n; arrived / cancelled / died | A3 (195) | Base (195) | Their bodies, A3 games |
|---|---|---|---|
| Enemy <= 4 | **3.80**; 0.27 / 0.70 / 0.03 | 1.03; 0.28 / 0.72 / 0 | 2.85; 0.26 / 0.73 / 0.01 |
| Enemy 5-6 | **8.10**; 0.49 / 0.50 / 0 | 2.92; 0.25 / 0.75 / 0 | 7.39; 0.42 / 0.58 / 0 |
| Enemy 7-9 | 7.71; 0.85 / 0.15 | 5.31; 0.74 / 0.26 | 13.88; 0.53 / 0.47 |
| Share of the <= 6 starts below 50 % HP | 0.77 | 0.14 | 0.25 |

**A3's escape-type recalls (enemy within 6), split by whether an enemy within 6 was closing over the last 2 rounds**
[measured, 195 games, `escape.py`]:

| | Starts a game | Arrived | Cancelled | Dead within 15 rounds |
|---|---|---|---|---|
| Closing, nearest <= 4 | 2.65 | 0.16 | **0.80** | **0.27** |
| Closing, nearest 5-6 | 3.57 | 0.33 | 0.66 | 0.08 |
| Not closing, <= 4 | 1.15 | 0.51 | 0.47 | 0.08 |
| Not closing, 5-6 | 4.53 | 0.62 | 0.38 | 0.03 |
| Base, closing (<= 4 / 5-6) | 0.69 / 1.43 | 0.19 / 0.21 | 0.81 / 0.79 | 0.16 / 0.06 |

- **How they fail:** 895 of 1,313 cancels (68 %) came one round after the start. In an 80-game sample the nearest
  enemy was then 3-6 tiles away. That is a ranged body's reach + 1, the dth-2 abort's test [code: `play_turn`, "dth 2: abort a real
  recall channel"]. HP lost during the channel was ~0, so the abort works. The loss is the turn spent standing, after
  which the chaser is closer.
- **Death situations, paired:** died recalling **+0.46 ± 0.07** (sig). They walked in on us −0.16, other −0.08. Net
  episodes +0.28 (n.s.).
- **Branch** [code]: `bkx_escape_ok()` allows the recall when no visible enemy can strike next turn (beyond reach + 1,
  and at least 4 away). It never asks whether that enemy is still coming.

## 4. Cause 2: chip and leave in the mid, and what makes our bodies leave

**Mid groups the opponent captured after we hit them, a game** [measured]:

| | Base (195) | A3 (195) | A3, tiny (82) |
|---|---|---|---|
| We left a live group (our last hit > 2 rounds before its last camp died) | 2.36 (89 gems; 35 of our hits) | **2.23 (84 gems; 29 hits)** | 2.39 (81 gems) |
| We hit at the kill; they captured | 0.37 (9 gems) | 0.56 (15 gems) | 0.84 (25 gems) |

In the second row, the kill-to-capture gap was a median 14 rounds and our nearest body was 5.5 tiles away at their
capture. Nobody of ours stayed to capture.
- Our hitters at those kills then fought 0.24 a game, fled 0.23 and stayed without capturing 0.17 (base 0.17 / 0.12 /
  0.10), mostly at ≥ 50 % HP with an enemy 5-8 tiles away.
- Bit 2 also covers the fight case for the taker: `g_working` includes a REWARD group when `i_take(g)` [code].

**Does A3 change round 1's pattern?** Paired, 195 games: our bodies' leaves from live contested mid groups the
opponent then captured, a game.

| What the body did in the 8 rounds after its last hit | Base | A3 | A3 − base (se) | Tiny: base → A3 |
|---|---|---|---|---|
| All leaves | 4.21 | 4.03 | −0.18 (0.28) | 5.29 → 4.73 |
| Our hits on those groups | 36.0 | 31.2 | −4.7 (2.7) | 49.0 → 35.4 (**−13.7, sig**) |
| **Went to fight an enemy** | 0.76 | **0.95** | **+0.18 (0.11)** | 0.94 → 1.21 (+0.27) |
| ... the enemy > 3 tiles away at the last hit | 0.49 | **0.65** | **+0.16 (0.09)** | 0.62 → 0.89 (+0.27) |
| Fled | 1.69 | 1.42 | **−0.28 (0.14)** | 1.76 → 1.28 (**−0.48**) |
| Walked off / stayed without hitting | 0.68 / 0.68 | 0.54 / 0.65 | −0.14 / −0.03 | |
| Recalled / died | 0.19 / 0.14 | 0.24 / 0.16 | | |

So A3 chips less (−14 hits a game on tiny maps) and flees less, but it pulls more bodies off live groups to fight.

**What makes them leave.** The state at the body's last hit, mapped to the bot branch that state triggers. A3, 195
games, leavers of live mid groups the opponent captured, a game. Tags: [measured] state, [code] branch.

| State at the last hit | A game | Then | Branch it matches |
|---|---|---|---|
| Enemy within 8; our live HP within 10 ≥ 0.8x theirs; no fed enemy | **1.41** | **fight 0.42**, flee 0.31, stay 0.16 | Contact → COMMIT (engx 16 `eng_go`: HP ≥ 0.5 and ratio ≥ 0.8), or a commit override after the WORK hold: engx 2 joins a posted fight "over a WORK hold"; engx 32 answers the opener (no hold check); the RL 4 opener acts "from farming / WORK"; hunt |
| Our live HP within 10 below 0.8x theirs | 0.93 | flee 0.50, fight 0.25 | Contact → `eng_go` fails → BREAK → `act_flee` |
| No enemy within 8 | 0.63 | walk off 0.37, stay 0.31 | Planner re-plan (`farm_vt` flat danger x0.6 / x0.85, threat discount) |
| A fed enemy (≥ 1.9x my max HP) within 6 | 0.58 | flee 0.51 | `fed_break` (fed_k 1.9, within reach + 2) |
| Died there | 0.16 | | |
| HP < 0.5, with / without an enemy within 9 | 0.13 / 0.11 | flee, recall / walk off | stance_low / HURTREC |
| Their max HP within 6 ≥ 1.15x ours | 0.08 | flee, fight | WORK hold `work_out_k` |

- **The hold:** `work_hold` should keep a body on its group [code: within `role_work_r` 4 of a live group, no `real`
  threat]. The commit overrides evaluated after it can still take the body off the group to `act_fight` an enemy
  4-8 tiles away, and the group is then lost.
- **Not changed:** the flee branches (fed break, `eng_go` fails) are the bot working as built in weaker spots.
- **Base for comparison:** in the base, the first row was 1.40 a game, with fight 0.34 and flee 0.40.

## 5. Deaths: what A3 still dies of (195 games, twins merged) [measured]

| Situation (the victim's view) | Us, A3 (bag) | Them, A3 games | Us, tiny | A3 − base, paired (se) |
|---|---|---|---|---|
| Walked into contact at full HP | **3.36** (25) | 3.20 (36) | **4.45** | +0.00 (0.19) |
| They walked in on us | 1.72 (25) | 1.32 (18) | 2.22 | −0.16 (0.17) |
| Walked in hurt | 1.01 (16) | 1.04 (18) | | +0.06 |
| **Died recalling** | **0.49** (8) | 0.39 (5) | 0.54 | **+0.46 (0.07)** |
| Died tributing | 0.12 (8) | 0.16 (11) | 0.15 | +0.02 |
| No enemy within 8 / other | 0.42 | 0.43 | | −0.12 |
| **All episodes** | **7.11 (87)** | 6.54 (92) | **9.04 (98)** | +0.28 (0.30); bag −6 (11) |

- **Twins:** 2.3 episodes a game are twin deaths (3.2 on tiny maps), about a third of our episodes, and each counts
  as 2 platform deaths. Paired: +0.21 (n.s.). This is known (FINDINGS L11), and the twin link lost on the band
  (v293), so there is no new lever here.
- **By body (paired):** Vesper −0.34 (sig; bag 41 → 29). Prism +0.24 (A3's draft adds Prism). The rest is level.
- **"Walked in at full HP"** is the largest class, unchanged by A3, and **symmetric**: their bodies die that way 3.20
  times a game. We trade back 0.18 kills a death, they 0.23. In 53 % of these deaths (59 % on tiny maps) the biggest
  enemy had ≥ 1.5x our max HP, against 44 % for theirs. This is the size gap that A5's `sizex` targets, so it is not a
  new lever.
- **By zone (paired):** mid 4.2 a game (+0.21), own 2.0, their 1.0. About half of the deaths come after r600.

## 6. The patches (`bots/_s2b` = `_stkA5` + `s2b`; files `src/value.h`, `src/bot.cpp`)

```cpp
// value.h, end of struct Params (with a comment block describing the bits)
static constexpr int s2b = 0;
static constexpr int s2b_er = 6;
```

**Bit 1, in `bkx_escape_ok()`** (bot.cpp), right after `if (bkx_recall_unsafe()) { ...; return false; }`:

```cpp
    if constexpr ((value::Params::s2b & 1) != 0) {
        for (const auto& e : W.enemies) {
            if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos)) continue;
            const int d = cheb(e.pos, me.pos);
            if (d <= value::Params::s2b_er && e.prev_round == W.round - 1 && e.prev_pos.x >= 0 && cheb(e.prev_pos, me.pos) > d) return false;
        }
    }
```

- **Trigger:** the escape-recall state, plus a visible enemy within 6 that is nearer my tile than it was at its last
  sighting, one round ago. `prev_pos` / `prev_round` are set at each sighting [code: `world.cpp`].
- **Action:** no escape recall this turn.
  - In the BREAK branch (`ESCREC`) the body goes on to `act_flee`.
  - Before HURTREC (`ESCREC2`) it continues as before; HURTREC's own guard refuses a recall near an enemy.
- **Should change** [guess, from §3]:
  - Closing-chaser escape starts: 6.2 → ~0 a game. Died recalling: 0.49 → ~0.15.
  - Escape arrivals: ~4.97 → ~3.3 a game from the not-closing starts (kept), plus later starts once a chaser stops.
- **Fuel:** one pass over the enemy list, only when the escape test is reached.

**Bit 2, work through.** In `play_turn`, inserted just before `if (FB(32) && stance == Stance::NONE ...)`, which
comes after every commit override (stun follow-up, assist, engx 2 / 32, opener, hunt, finisher, the gate, the fb
no-chase rules):

```cpp
    if constexpr ((value::Params::s2b & 2) != 0) {
        if (work_hold && stance == Stance::COMMIT && stance_target != NONE && !fin_commit && !stun_commit && !fed_break &&
            (assisting || hunting || role_open) && execute_target() == NONE) {
            const auto& e = W.enemies[stance_target];
            if (!(e.alive && e.seen_round == W.round && cheb(e.pos, me.pos) <= me.range)) {
                stance = Stance::NONE; stance_target = NONE; stance_until = W.round; farming_now = true;
                assisting = hunting = role_open = false;
            }
        }
    }
```

- **Trigger:** a WORK hold that passed the threat checks (`work_hold`), then turned into a COMMIT by a join (assist /
  engx 2), an answer (engx 32, which sets `assisting`), an opener (RL 4) or a hunt, on an enemy beyond my attack range.
- **Action:** the hold stays.
  - The ranged free hit below still fires on any enemy in range (it runs with stance NONE).
  - The farming turn goes on.
  - A finisher (`fin_commit`), a stunned target (`stun_commit`) or an execute still commits.
  - A melee worker with an enemy in range still commits.
- **Should change:** fight-leaves from live mid groups, 0.95 a game (1.21 tiny), toward the base's 0.5 or below; our
  mid captures up, most on tiny maps [guess].
- **Risk** [guess]: fewer joins mean fewer kills. A3's kills (+1.35) and their bags (+32) are part of its gain, so
  read kills next to share.
- **Fuel:** a few compares.

**cmp** [measured]: `.venv/bin/cambc build _s2b --release` with `s2b=0` gives `bot.wasm` byte-identical to
`bots/_stkA5/.cambc/build-release/bot.wasm` (3,663,504 bytes; re-checked after bit 2). `bots/_s2b_3` (made with
`tools/variant.py _s2b _s2b_3 s2b=3`) compiles.

## 7. KPIs for the band read (scripts in `~/tzunami_data/analysis_10nov/session2b/`)

- **Bit 1:** `escape.py LABEL` (closing-chaser starts, 6.2 a game in A3) and `recall.py LABEL`. Then
  `sum2b.py BASE LABEL`, row `sit:1 died recalling` (A3 0.49).
- **Bit 2:** `leave2.py BASE LABEL` (row `fight` 0.95, `fight_far` 0.65). `sum2b.py` rows "captures by us / them in
  mid zone" (A3 316 / 458) and `their deaths (raw)` (A3 7.27).
- **Pipeline:** `tools/replay/fetch.py LABEL`, then `python3 -I parse2b.py LABEL`, then any of
  - `sum2b.py BASE LABEL [LABEL2]` (`CLASS=tiny|nontiny`),
  - `anat.py LABEL [tiny]`, `flow.py LABEL`, `chip.py LABEL`, `kill.py LABEL`, `trade.py LABEL`, `leave2.py BASE LABEL`.
  - Outputs for this report: `out/`.
- `fetch3.py LABEL...` is `fetch.py` with ≥ 3 s between calls and a 2-minute pause on a real 429. Its first version
  mistook a match ID containing "429" for a rate limit; that is fixed.

## 8. A2 (`tz182_big`, 195 pairs) and what A3 added [measured]

| Paired v base | A2 − base (all) | A3 − base (all) | A2 − base (tiny 82) | A3 − base (tiny 82) |
|---|---|---|---|---|
| Share | **+0.05*** | **+0.08*** | +0.04 (se 0.04) | +0.08 (se 0.04) |
| Win | **+0.07*** | **+0.10*** | +0.06 | **+0.11*** |
| Our deaths raw / episodes | +0.66 / +0.35 | +0.49 / +0.28 | **+1.35 / +0.84** | +0.65 / +0.39 |
| Their deaths (raw) | **+0.96*** | **+1.35*** | +1.35 | **+1.90*** |
| Their bags lost (gems) | +5 | **+32*** | +5 | +16 |
| Our / their mid captures (gems) | +24 / −13 | **+38*** / −21 | +24 / −31 | +56 / **−51*** |
| **Died recalling** | +0.04 (0.02) | **+0.46 (0.07)** | +0.04 | **+0.46** |
| They walked in on us | +0.17 | −0.16 | +0.49 (0.25) | −0.23 |
| Twin deaths | **+0.31*** | +0.21 | **+0.51*** | +0.26 |
| Leaves from live mid groups to fight / with the enemy > 3 away | +0.00 / +0.01 | +0.18 / +0.16 | +0.02 / +0.04 | +0.27 / +0.27 |
| Leaves then fled | −0.14 | **−0.28** | −0.23 | **−0.48** |

- **Cause 1 is `bankx 2`.** A2 has no rise in deaths while recalling; A3 (= A2 + `bankx 2` + `s2end 1`) has +0.46.
  A3 also cut "they walked in" (−0.16 v A2's +0.17) and twin deaths on tiny maps (+0.26 v +0.51), so the escape recall
  does save bodies. Bit 1 keeps those (the not-closing starts) and drops the closing-chaser ones.
- **Cause 2's "leave to fight" is a base behaviour.** It is 0.76 a game in the base and in A2. A3's rise (+0.18) is
  within 1.6 se. Neither stack touched it; bit 2 is the first change aimed at it.
- **A2 on tiny maps:** +0.04 share. Its tiny-map deaths rose (+1.35 raw), mostly twins (+0.51, sig) and enemies
  walking in on us (+0.49). The extra mid presence of `openx` costs bodies there. A3 took back about half of that.

## What I could not show

- **No runs:** neither patch was run (the session's rules). The effects in §6 are [guess] sizes from the counts.
- **Branches:** the branch in §4 is inferred from the state at the last hit. The replay has no branch log, so
  "matches" is a mapping [code + measured], not a trace.
- **Escape recall net effect:** whether escape recalls save more bodies than they lose cannot be split from the
  paired totals (episodes +0.28, n.s.). Bit 1 removes only the case that fails 66-80 % of the time.
- **Fight-leave sizes:** the A3 − base differences there are 1.6-1.8 se. The direction is clear; the size is not.
