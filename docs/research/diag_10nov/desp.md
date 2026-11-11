# desp: desperation mode when the game is clearly lost late (`bots/_desp`, switch `despx`), 10 Nov

## Question
Our live bot v306 loses about 56 % of band games. The idea: in a game that is clearly lost late, variance only helps,
because we lose anyway. Does a mode that fires only then flip lost games, without costing games we would have won?

- **The trigger:** their banked gems >= `desp_their` (700) and ours <= theirs - `desp_gap` (200). Both scores are
  public [sdk: `global_submitted_gems`].
- The mode does nothing in a game we lead or are level in.

## Short answer
- **cmp:** `_desp` at v306's settings with `despx=0` (TZ_STAMP "tz-189") builds release and debug wasms
  **byte-identical** to `bots/_v306`'s (3,701,340 bytes) [measured: `cmp`, rechecked after every code change].
- **The mode fires often and gains nothing locally.**
  - It fires in ~105 of 256 games against v306.
  - Over 3 seeds the clean pairs hold ~260 desperate games a build. Of these, despx 7 turned **1 lost game into a
    win** and despx 2 none.
  - The control's comebacks in those pairs fell 21 -> 15 (despx 7) and 21 -> 17 (despx 2), which is within noise. The
    same fragile comebacks flip in most variants and seeds: 02uncharted-lands b, adgato-gemcombat4 b, 02stalactites a.
  - Overall: **despx 7 383 v 384 (49.9 %), despx 2 390 v 384 (50.8 %)** over 768 games, against the mirror.
- **The premise is wrong locally.**
  - In the v306 mirror, 115 / 118 / 118 of 256 sides reach the trigger (seeds 0 / 1 / 2), and **6 / 9 / 9 of those
    come back to win** (5-8 %) [measured].
  - Those comebacks come from normal farm-and-bank play. Desperation spends bodies, turns and fuel on denial, which
    breaks a few of them and has never yet bought one back.
- **KPIs move a little** (per fired game, despx=7, seeds 0 / 1 / 2):
  - our locks placed: 1.1, of which on an enemy channel (so it cancels): 0.30 / 0.27 / 0.24;
  - instant stuns on channellers: 0.05-0.09; converge stuns or locks landed: 0.34 / 0.33 / 0.28;
  - delay of the opponent's finish in clean games lost both ways: **+5.3 / +2.0 / +1.7 rounds on average (median 0)**;
  - deaths: +1.5 a game in the fired games (9.6-10.0 v 8.1-8.4).
- **The tight trigger** (their >= 800, ours <= theirs - 300) meets 2-4 comebacks a seed instead of 6-9:
  - **258 v 256 (50.4 %) over 2 seeds** (512 games);
  - 0 flips either way in 128 clean desperate games (section 5).
- **Recommendation:**
  - Do not ship on local evidence: it is null.
  - If the band has spare quota, test the tight trigger. It can only show against band behaviour, if at all: the band
    channels and locks differently from our own bot.

## 1. What was built (`bots/_desp`, `src/value.h` `despx`, code in `src/bot.cpp`, search `desp`)
`despx` is a `static constexpr int`. At 0 nothing compiles in: every function is a `template <int Z>`, and the three
hooks sit behind `if constexpr`. Bits:

- **1 lock their altars.**
  - In `shop()` (also the dead body's shop turn), while desperate, buy one altar lock (10 g) before the emblems.
  - A body holding a lock picks an altar with evidence:
    - a visible enemy channelling there (score 1,000 + bag);
    - else a visible enemy carrier with bag >= `desp_bag` (20) within 5 of it;
    - else the last altar this body saw an enemy channel at, within `desp_mem` (100) rounds.
  - It skips altars known to hold our lock: visible, or placed / seen by this body within 80 rounds. It walks there
    (the altar field, at most `desp_lr` walking tiles) and places the lock from 2.
  - Never where a visible ally of ours channels: our lock cancels our own ally's channel [measured mech.md].
  - It re-buys at the next spawn visit, which re-locks once a lock breaks.
  - While desperate, the base's `try_lock()` deny branch gets the same ally-channel guard.
- **2 stop the finish.**
  - A ready stun goes on the biggest visible channelling enemy within 6, of any bag (`s2_stun`: never on a body
    already stunned).
  - Then the body converges on one target: a channelling enemy with bag >= `desp_bag` (or a winning bag) that it can
    reach before the channel ends (`remaining_channel_time`), or a visible carrier off its spawn whose bag wins
    (>= 1,000 - their score).
  - The converge ignores the danger gates; HP must be >= `desp_hp` (0.15) of max. It stuns, else locks the channel's
    altar (with bit 1), else hits.
- **4 our race (exempt carriers).** A body with bag >= `desp_carry` (60), or whose bag closes the gap
  (our score + bag >= theirs), is not drafted by bits 1 / 2: it keeps the normal bank logic. The instant stun still
  fires.
- **8 (with 1) speculative locks.** With no evidence, target the altar nearest their spawn. This was the first build:
  see section 4.
- **16 (with 2) hunt.** The converge also takes a visible carrier with bag >= `desp_hunt` (50): a kill takes its bag
  [rules].

Knobs: `desp_their 700`, `desp_gap 200`, `desp_bag 20`, `desp_carry 60`, `desp_r 12`, `desp_hp 0.15`, `desp_lr 99`,
`desp_mem 100`, `desp_hunt 50`, `desp_dbg 0` (scratch only: DESPDBG counter lines in stdout).

Files touched:
- `bots/_desp/src/value.h`: the `despx` block after `s2b`.
- `bots/_desp/src/bot.cpp`:
  - three forward declarations after `EX()`;
  - one line in `shop()`;
  - two lines in `try_lock()`;
  - the `DespSt` / `desp_*` block before the endx section;
  - one hook in `play_turn` before `s2_end_turn`.
- `bots/_desp/src/common.h`: TZ_STAMP "tz-189", for the cmp. **Bump it for an upload.**

`_desp`'s value.h defaults are `_s2b`'s (stack switches 0); the band line sets v306's settings.

Fuel: when not desperate, one comparison a turn. When desperate, one pass over the visible enemies (a channel read
each) and, for a lock holder, the altar fields (cached).

## 2. Method: the paired mirror control
- **Control:** the v306 mirror (`_v306` v `_v306`, 128 maps x both sides, `judge.py --keep`). A mirror game is the
  same game from both sides, so every (map, side) has an exact control outcome.
- **Candidate:** `_desp_N` (v306's settings + `despx=N`, `desp_dbg=1`) v `_v306` on the same 256 map-sides.
- **Pairing** (`~/tzunami_data/analysis_10nov/desp/pair.py`):
  - a game "fired" when its replay stdout holds a DESPDBG line;
  - a pair is "clean" when both teams' banked timelines match the control's up to the trigger round.
- **Caveat:** any binary change shifts fuel-cut points, so ~16 % of games diverge before the trigger. That is the
  "fired all" minus "fired clean" rows, and the not-fired games' drift. After the trigger, every action perturbs the
  game chaotically. So a flip is only weak evidence on its own; the counts across seeds matter.
- **Seeds 1 / 2:** a fresh mirror `_v306sK` (`seed=K`) v itself, and `_desp_NsK` v `_v306sK`.

## 3. Results [measured]
Wins are the judged bot's, out of 256. "Fired" = games where desperation fired. Delay = mean change of the end round
in fired games lost both ways (the opponent's finish).

| Build | Seed | All: cand v control | Fired | Fired wins cand v ctrl | Clean flips L->W / W->L | Delay all / clean (rounds) | Deaths fired cand v ctrl |
|---|---|---|---|---|---|---|---|
| despx 2 (stop the finish) | 0 | 127 v 128 | 105 | 3 v 8 | 0 / 1 | +12.6 / +9.1 | 9.13 v 8.27 |
| despx 2 | 1 | 131 v 128 | 103 | 8 v 10 | 0 / 1 | -4.6 / -2.9 | 9.23 v 8.48 |
| despx 5 (targeted locks + exempt) | 0 | 126 v 128 | 107 | 3 v 9 | 0 / 1 | +9.6 / +7.2 | 8.90 v 8.14 |
| **despx 7 (1 + 2 + 4)** | 0 | 126 v 128 | 107 | 3 v 9 | 1 / 2 | +5.6 / +5.3 | 9.64 v 8.14 |
| **despx 7** | 1 | 128 v 128 | 104 | 6 v 11 | 0 / 2 | +1.9 / +2.0 | 9.96 v 8.40 |
| despx 23 (7 + hunt) | 0 | 126 v 128 | 107 | 3 v 9 | 0 / 2 | +0.7 / +1.2 | 10.11 v 8.14 |
| first build (= 15: speculative locks) | 0 | 126 v 128 | 107 | 3 v 9 | 0 / 2 | +2.8 / +2.6 | 10.23 v 8.14 |
| despx 2 | 2 | 132 v 128 | 105 | 8 v 11 | 0 / 2 | +6.8 / +5.5 | 9.35 v 8.39 |
| **despx 7** | 2 | 129 v 128 | 106 | 6 v 12 | 0 / 3 | +5.5 / +1.7 | 9.87 v 8.32 |
| **despx 2, 3 seeds** | | **390 v 384 (50.8 %)** | 313 | 19 v 29 | **0 / 4** | | |
| **despx 7, 3 seeds** | | **383 v 384 (49.9 %)** | 317 | 15 v 32 | **1 / 7** | | |

**Read the "fired" columns with care: they are biased against the candidate.**
- "Fired" is defined on the candidate's own game. When a game diverged before the trigger (fuel noise) and the candidate
  did worse, it becomes desperate and lands in "fired" as a loss. When it did better, it never fires and lands in
  "not fired" as a win.
- That is why the not-fired games drift +4 to +7 for the candidate in every seed, and the fired ones -5 to -6.
- The unbiased reads are:
  - the overall totals: **50.8 % (despx 2) and 49.9 % (despx 7) over 768 games**;
  - the clean pairs, where both teams' scores were identical up to the trigger, so both builds became desperate in
    the same state. Over 3 seeds there are ~260 of them a build.
- **In those clean pairs the mode turned 0 (despx 2) and 1 (despx 7) lost games into wins**, and the control's
  comebacks fell 21 -> 17 (despx 2) and 21 -> 15 (despx 7). That fall is within Poisson noise (+-4.6).
- Several W->L flips show all-zero action counters: the game diverged on the desperate turns' extra fuel alone, not
  on an action. A game the trailing side won against 5-8 % odds is fragile: any perturbation tends to undo it.

The control's comeback count, by trigger (seeds 0 / 1 / 2; out of the sides that reach it):

| Trigger (their >=, gap >=) | Sides that reach it | Comebacks |
|---|---|---|
| 600, 150 | 128 / - / - | 12 / - / - |
| **700, 200 (default)** | 115 / 118 / 118 | **6 / 9 / 9** |
| 800, 250 | 95 / 100 / 97 | 2 / 4 / 4 |
| **800, 300** | 85 / 86 / 88 | **2 / 3 / 4** |
| 900, 300 | 82 / 83 / 86 | 2 / 2 / 3 |

The median trigger round is 774 and the median end is 934, so the mode has ~160 rounds to act (700 / 200, seed 0).

Debug counters per fired game (despx=7, seed 0):
- desperate body-turns: 459;
- locks bought: 4.1; placed: 1.1; placed on an enemy channel: 0.30;
- instant stuns on channellers: 0.05;
- converge turns: 6.1, of which landed (stun or lock): 0.34;
- lock-walk turns: 16.4;
- refusals because an ally channelled at the altar: 0.02;
- exempt carrier turns: 20.

## 4. What did not work
- **Speculative locks (the first build, now bit 8).**
  - Every body with a lock walked to the altar nearest their spawn when it had no evidence: 82 lock-walk turns a
    fired game, 2.2 locks placed, only 0.15 of them on a channel.
  - Our final gems in fired games fell 552 -> 511. Deaths rose 8.1 -> 10.2. The finish moved +2.8 rounds.
  - With evidence only (bit 1 now): 16 walk turns, 1.1 placed, 0.30 on a channel.
- **Hunting carriers (bit 16).** It doubled the converge turns (6 -> 15.5) and raised deaths to 10.1 v 8.1 a fired
  game. It landed 0.48 a game and turned no game.
- **Why the finish is not delayed.**
  - A lock cancels one channel. After that it costs the enemy 5 basic hits: a carrier's tribute attempt is one hit
    [measured mech.md], and attack-reset bodies hit twice.
  - On 2+-altar maps they bank elsewhere.
  - Stuns cost one turn. The carrier keeps its gems and restarts.
  - In the 83 clean lost-both games (despx=7, seed 0), the end round moved by -240 to +132. 31 were unchanged,
    34 later and 18 earlier: chaos with a slight drift, not a delay.
- **One-altar maps** (`cls_alt1.txt`, 64 games, seed 0), where a lock should bite most:
  - despx=7: fired 26, wins 1 v 2; 0.38 locks on a channel a game; delay -9.6;
  - despx=2: 0 v 2.

## 5. Tight trigger (800 / 300) [measured]
Run with `despx=7 desp_their=800 desp_gap=300`, paired against the same mirrors.

| Seed | All: cand v control | Fired | Clean pairs | Clean wins cand v ctrl | Clean flips L->W / W->L | Delay clean (rounds) | Deaths fired cand v ctrl |
|---|---|---|---|---|---|---|---|
| 0 | 127 v 128 | 80 | 66 | 1 v 1 | 0 / 0 | +1.5 | 10.53 v 9.18 |
| 1 | 131 v 128 | 74 | 62 | 3 v 3 | 0 / 0 | +0.6 | 10.65 v 9.49 |
| **both** | **258 v 256 (50.4 %)** | 154 | 128 | 4 v 4 | **0 / 0** | | |

- It fires in ~30 % of games, against ~41 % for 700 / 200. In the 128 clean desperate games it neither won nor lost a
  game.
- Per fired game (seed 0 / 1):
  - locks placed 0.62 / 0.78, of which on a channel 0.23 / 0.26;
  - converge turns 5.8 / 6.9, of which landed 0.28 / 0.26;
  - lock-walk turns 8.6 / 8.2.
- Our final gems in the clean fired games are 7-14 lower (412 v 419, 425 v 439): bodies walk to lock instead of
  farming. Their finish is the same (1,027 v 1,027; 1,030 v 1,030).
- Of all the settings tried, this is the only one with no clean cost in either seed. It also has no gain.

## 6. What the band should show
- The band channels big bags and locks more than our bot does. Rogue Lock Pickers is named after it. The mode's
  per-game actions (~0.3 cancels by lock, ~0.3 converge cancels) are too few to move 60-150 band games measurably.
- Measure two things against v306 on the same games: wins in games where we trail by 200+ at their 700+, and their
  finish round.
- A band test reads mostly noise.
  - On local evidence, the 700 / 200 trigger costs ~1 % of games (the fragile comebacks). The 800 / 300 trigger costs
    nothing measurable.
  - Neither turned a lost game into a win by its actions (1 in ~390 clean desperate games over all settings and seeds).

## Band line
`despx 7: when lost late, lock their altars + stun their finisher|_desp|robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11 endx=3 s2b=1 despx=7 desp_their=800 desp_gap=300|all`

- The note is 64 characters.
- The build compiles at these settings with `desp_dbg 0`: release wasm 3,719,364 bytes. The scratch copy is deleted.
- Low priority: it is handed over at ~50 % with KPIs that barely move. The local null is the honest result.
- **The TZ_STAMP in `bots/_desp/src/common.h` is "tz-189" (for the cmp): bump it before an upload.**

## Scripts (`~/tzunami_data/analysis_10nov/desp/`)
- `trig.py JUDGE_DIR [THEIR GAP]`: per game, the first desperate round from `teamTimelines`, and the comebacks.
- `pair.py CAND_DIR MIRROR_DIR [THEIR GAP]`: the paired control, flips, delay and DESPDBG counters.
- `cls.py CAND_DIR MIRROR_DIR CLASSFILE`: the same, restricted to a map class.
- `agg.py SCRATCH`: the table over the pairing outputs.

## Cleanup
- Kept: `bots/_desp` (switch defaults 0).
- Kept: the pairing outputs and judge logs, in `~/tzunami_data/analysis_10nov/desp/runs/` (`p*.txt`, `trig_m*.txt`,
  `*.log`).
- Deleted: the scratch bots `_desp_*` and `_v306s*`, and all match outputs.
