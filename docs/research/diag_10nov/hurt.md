# hurt: hurt bodies that die without a recall (`bots/_hurt`, switch `hurtx`), 10 Nov

Agent `hurt`, 10 Nov (16:31-17:15). Copy: `bots/_hurt` (from `bots/_s2b`). Scripts (no data):
`~/tzunami_data/analysis_10nov/hurt/`:
- `hd.py`: hurt deaths on a band label: hurt window, what blocked a recall each round, activity. `HD_TY=3,4` keeps the twins only.
- `hstate.py`: hurt rounds per nearest-enemy bucket, us v them: next action, dead within 10 rounds.
- `hs2.py`: hurt rounds in contact: action and outcome.
- `dboth.py`: deaths by kind, us v them.
- `twin.py`: twin pair deaths.
- `sumdeaths.py`: deaths by champion and twin pairs from the platform summaries.
- `lhurt.py` + `dec.sh`: the same KPIs on kept local judge games.

## The question

The emb agent measured on `tiny_m2` / `a1_m2` (the base v281, before the escape recall) that about 4.1 of our 8.6-9.6
deaths a game are hurt bodies that never start a recall. In 1.7-1.9 of them the nearest enemy was still 4+ tiles away
7 rounds before the death.
- Which branch keeps them from recalling?
- Can a rule (`hurtx`) save them on v306?

## Short answer

1. **On v306's ancestors the gap is gone [measured].** On A3's 195 band games (`tz184_big` = v306 minus sizex / endx /
   s2b) our hurt deaths without a recall are **3.85 a game, the band's 3.99**. On the base (`p83_m2`, same games, no
   escape recall) they are 4.57 v 3.16. The escape recall (bankx 2) closed it. Per hurt round our bodies die exactly as
   often as the band's (table 2).
2. **Cause 1, contact (77 %) [measured].** 77 % of these deaths start below 50 % HP with an enemy within 3. In 74 % of
   the hurt-window rounds an enemy is within its reach + 1, or within 3. There a recall cannot land: damage cancels it
   [rules], and the guards (`bkx_recall_unsafe`, the dth-2 abort) are right to refuse it. Only 1 % of those rounds are
   "25-50 % HP, no enemy within 9", where no rule acts. The branch that holds these bodies in contact is the fight itself:
   - a COMMIT holds until stance_low 0.3 or the end of the 6-round hold, because engx bit 4 (the leave test) is off;
   - after a BREAK, the flee does not outrun the chaser.
3. **Cause 2, the twins [measured].** 1.02 twin pair deaths a game (2 bodies, 2 bags each) start with a hurt twin that
   never recalled. All twin pair deaths: 2.30 a game.
   - The raw-death gap on v306's band games (`tz189_big`: 9.83 v 7.65) is mostly the twins' link. We draft them every
     game, the band in 71 of 195.
   - Per game where they draft them, the band's twins die as a pair 1.96 times v ours 2.43.
   - Deaths without the twin collateral: 7.40 v 6.93.
4. **Built `hurtx` (bits 1 / 2 / 4) and judged it locally: every bit is level.**
   - **1 (twins: a life worth two):** 50.4 / 49.2 %. The hurt twin pair deaths fall 0.17 a game in both seeds, total
     deaths are level.
   - **2 (leave a commit below 50 % HP):** 50.0 %, **deaths +0.8 (6.1 v 5.3)**: breaking off kills more bodies than
     fighting on.
   - **4 (recall when hurt with nobody near):** 50.4 %, gold300 -34.
   - **1+4:** 49.2 %.
5. **Recommendation:** do not spend band quota on hurtx. If a slot is spare, hurtx 1 fits the 49 % rule (below). The
   death gap that is left is in the fights (twins after r300, +0.47 non-twin deaths), not in recalls.

## 1. Measured on the band [measured: decoded replays; `tz184_big` = A3 (v304) and `p83_m2` = v281, 195 paired games; `tz189_big` = v306 summaries]

**Deaths by kind, per game** (`dboth.py`):
- low3 = at least 3 of the 7 rounds before the death below 50 % HP;
- hnr = low3 with no real recall (a recall channel that survived a turn start);
- far4 = the nearest enemy was 4+ tiles away 7 rounds before;
- fast = at or above 50 % HP 3 rounds before the death;
- twin_hi = a twin dying at or above 50 % HP, which is the link.

| Label | Side | Deaths | low3 | **hnr** | hnr far4 | fast | twin_hi | fast, non-twin |
|---|---|---|---|---|---|---|---|---|
| p83_m2 (v281) | us | 8.92 | 4.65 | **4.57** | 1.87 | 4.30 | 2.35 | 1.95 |
| | band | 5.92 | 3.37 | **3.16** | 1.27 | 2.55 | 0.72 | 1.85 |
| **tz184_big (A3)** | us | 9.42 | 4.52 | **3.85** | 1.31 | 4.91 | 2.66 | 2.28 |
| | band | 7.27 | 4.23 | **3.99** | 1.43 | 3.06 | 0.75 | 2.31 |
| tiny_m2 (v281) | us / band | 9.60 / 5.02 | 4.32 / 2.80 | 4.14 / 2.67 | 1.93 / 1.27 | | 2.96 / 0.47 | 2.39 / 1.76 |
| a1_m2 (v281) | us / band | 8.64 / 5.02 | 4.35 / 3.04 | 4.23 / 2.80 | 1.70 / 1.08 | | 2.18 / 0.76 | 2.11 / 1.25 |

**Per hurt round**: HP < 50 %, more than 6 from home, not in a live recall. A3's games, us v the band in the same
games (`hstate.py`):

| Nearest enemy | Rounds a game (us / band) | Recall live next round | Dead within 10 rounds (us / band) | Home within 15 |
|---|---|---|---|---|
| <= 3 | 49.9 / 48.9 | 0.01 / 0.01 | **0.33 / 0.32** | 0.42 / 0.36 |
| 4-6 | 42.0 / 40.4 | 0.21 / 0.07 | **0.12 / 0.12** | 0.68 / 0.54 |
| 7-9 | 15.5 / 26.9 | 0.30 / 0.13 | **0.04 / 0.04** | 0.80 / 0.58 |
| 10+ | 67.2 / 88.3 | 0.13 / 0.08 | 0.01 / 0.01 | 0.78 / 0.58 |

- A hurt body of ours is as safe as a band body in the same state, and it recalls and reaches home more often.
- Only the contact rows kill.

**Hurt deaths without a recall: what the body was doing** (A3, 750 deaths, `hd.py`):
- The hurt window runs back from the death while below 50 % HP, up to 15 rounds.
- When the body first fell below 50 %, the nearest enemy was within 3 in 580 deaths, at 4-6 in 111, at 7-9 in 17 and
  at 10+ in 42.
- The body was more than 6 from home in 715, carried 20+ gems in 128, and was below 25 % HP in 83.
- What blocked a recall in each window round, the first that applies, as a replay-side approximation of v306's rules
  (true positions, no fog):

| Blocker | A3 | v281 base | A3, twins only |
|---|---|---|---|
| Within 6 of home (escape recall excluded) | 0.06 | 0.05 | 0.11 |
| **An enemy within its reach + 1, or within 3 (no recall can land)** | **0.74** | 0.61 | 0.70 |
| At a camp (in its reach, or hitting it) | 0.05 | 0.06 | 0.05 |
| 25-50 % HP, no enemy within 9 (no rule fires) | 0.01 | 0.02 | 0.01 |
| Enemy at 4-6, out of reach (s2b closing, stance) | 0.10 | 0.18 | 0.10 |
| Enemy at 7-9, free (the escape recall's state) | 0.03 | 0.07 | 0.03 |

- Activity in the window: hitting champions 26 %, stepping toward home 34 %, away from home 19 %, standing 24 %, hit
  by a champion 33 %, hitting camps 1 %, tributing 0 %.
- A3's escape recall turned most of the base's free 4-9 rounds (0.25 -> 0.13) into recalls.
- By champion (A3, a game): Marcella 0.83, HoR 0.67, Vendetta 0.66, Cassi 0.60, Vesper 0.50, Issac 0.47, Prism 0.11.

**In contact while hurt** (`hs2.py`, A3, enemy within 3):

| Action next round, dead within 10 | Us | Band |
|---|---|---|
| Step toward home | 0.37 of rounds; 0.30 | 0.32; 0.36 |
| Step away from home | 0.15; 0.42 | 0.13; 0.36 |
| Stand, no hit | 0.13; **0.47** | 0.18; 0.35 |
| Stand and hit | 0.10; 0.36 | 0.13; 0.34 |
| 2+ enemies within 3 | 0.31; 0.47 | 0.32; 0.53 |

- Standing without hitting is our worst choice (0.47). In A3 part of it is the escape recall started into a chaser and
  cancelled a turn later, which s2b bit 1 (in v306) removes [session2b].

**Twins** (`twin.py`, A3; `sumdeaths.py` and the summaries of the v306 band games `tz189_big`):

| A game | Ours | Band (games where they draft the twins) |
|---|---|---|
| Twin pair deaths, A3 / v306 | 2.30 / 2.43 | 2.00 / 1.96 |
| ... after r300, A3 / v306 | 1.82 / 1.98 | 1.69 / 1.58 |
| A3: the killed twin had been hurt with no recall | 1.02 | |
| A3: the killed twin was Cassi / Issac | 1.28 / 1.02 | |

- v306 band deaths by champion, a game: Cassi 2.44, Issac 2.43, Marcella 1.35, HoR 1.30, Vendetta 1.19, Vesper 0.93.
- Deaths without the twin collateral: 7.40 v the band's 6.93. To camps: 1.01 v 0.66.

## 2. What I built: `hurtx` in `bots/_hurt` (base `bots/_s2b`)

Files touched:
- `src/value.h`: `hurtx`, `hurt_tw_hs` 0.65, `hurt_tw_low` 0.5, `hurt_tw_esc` 0.65, `hurt_tw_floor` 0.4,
  `hurt_free_hp` 0.45, `hurt_free_dh` 12, `hurt_dbg`, at the end of `Params`.
- `src/bot.cpp`: `HX()` and the `hx_st<>` counters after `Body me`. Hooks in `bkx_escape_ok()`, `eng_go()`, the `hurt`
  flag, the contact stance decision (`low`, `event`), the stun follow-up gate, and a bit-4 block before HURTREC. Also a
  `HURTDBG` print (only with hurt_dbg 1). No lambdas.

| Bit | What |
|---|---|
| 1 | The twins price their life x2, since one twin's death kills both. Cassi and Issac: commit (eng_go and the stun follow-up) only at >= 0.65 HP; break below 0.5 (stance low; others 0.3); escape-recall below 0.65 (others 0.5); go home (HURTREC / BRKREC) below 0.4 (others 0.25). |
| 2 | A COMMIT whose body fell below its commit HP (eng_hs 0.5; twins 0.65) is decided again, as an event. The commit test then fails unless a kill lands this round, so the body breaks and may escape-recall. |
| 4 | Hurt and free: below 0.45 HP, more than 12 from home, not damaged, no threat, not on a capture in progress. The body recalls; do_recall's guard still refuses with an enemy seen within 9 in 8 rounds, or a camp in reach. |

**cmp [measured]:**
- `_hurt` at v306's settings with hurtx 0 (and v306's TZ_STAMP "tz-189") gives a release `bot.wasm` and
  `bot-injected.wasm` byte-identical to `bots/_v306`'s (3,701,340 bytes).
- `_hurt` at its defaults gives a release wasm byte-identical to `bots/_s2b`'s.
- hurtx 1, 2, 3, 4, 5 and 7 all build. No missing games or bot faults in any run.

## 3. Local results [measured: `judge.py` v `bots/_v306`, 256 games a run (128 maps x 2 sides)]

- KPIs marked † come from 64 decoded games a run (`lhurt.py`). Those are every 4th kept replay, all from side a: a
  biased subset, so read them as directions only.
- The firing counts come from the in-bot counters over all 256 games.

| hurtx | Seed | Win % (95 % CI) | Deaths us v them | gold300 us v them | † hnr us v them | † twin pair deaths | † killed twin hurt, no recall | † real recalls (below 50 %) / home / cancelled | Fires |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 50.4 (44-56) | 5.8 v 5.7 | 1,496 v 1,483 | 3.52 v 3.70 | 1.59 v 1.58 | **0.89 v 1.06** | 48.9 (20.4) / 42.8 / 5.7 v 49.2 (23.7) / 43.2 / 5.5 | by r1000: twin escape tries 21 a game, twin homes 0.5 |
| 1 | 1 | 49.2 (43-55) | 6.1 v 5.9 | 1,479 v 1,499 | 3.66 v 3.89 | 1.53 v 1.72 | **0.95 v 1.12** | 48.5 (20.3) / 42.5 / 5.5 v 49.1 (23.5) / 43.3 / 5.4 | same |
| 2 | 0 | 50.0 (44-56) | **6.1 v 5.3** | 1,494 v 1,482 | 3.64 v 3.56 | 1.73 v 1.44 | 1.00 v 0.89 | 48.5 (21.7) / 42.8 / 5.2 v 48.2 (22.9) / 42.3 / 5.5 | by r1000: re-decisions 4.1 a game |
| 4 | 0 | 50.4 (44-56) | 5.9 v 5.8 | **1,467 v 1,501** | 3.44 v 4.12 | 1.61 v 1.69 | 1.03 v 1.23 | 47.9 (21.6) / 42.6 / 4.9 v 47.8 (22.9) / 42.2 / 5.1 | by r1000: free recalls 1.8 a game |
| 5 (1+4) | 0 | 49.2 (43-55) | 5.8 v 5.8 | 1,504 v 1,485 | | | | | |

- Bag lost at death (†, a game): 82 v 74 (1 s0), 63 v 69 (1 s1), 87 v 84 (2), 73 v 64 (4).
- fuelEx 25.6-27.8 in every run, as v306 itself.

What the numbers say:
- **Bit 1 moves its own KPI and nothing else.** Pair deaths that start from a hurt twin fall 0.17 a game in both seeds,
  and twins recall above 50 % HP more often (real recalls below 50 %: 20.3-20.4 v 23.5-23.7). Total deaths and wins
  are level: mean 49.8 % over 2 seeds.
- **Bit 2 is harmful:** deaths +0.8 a game, twin pair deaths +0.3. A hurt body that breaks off in contact is chased and
  killed while it no longer hits back. The code's old note says the same: in fights, breaking died 9 %, committing 5 %.
  engx 63 (59 + the team disengage) was 50.0 % on 9 Nov too.
- **Bit 4 fires 1.8 times a game and costs gold** (gold300 -34). It cuts hurt deaths in the decoded subset, but total
  deaths and wins are level.

## 4. What the band should show, and what did not work

- **No hurtx build passes the 53 % gate.** The band evidence says the recall side of hurt deaths is already at the
  band's level (A3: 3.85 v 3.99), so I do not expect a band gain.
- Bit 1's case is band-only. Our twins die as a pair 0.4 more a game than the band's twins after r300 (1.98 v 1.58 per
  drafted game), against bigger enemies [twin.md]. Leaving and recalling at a higher HP share could matter more there
  than against our own bot [guess]. Its KPI moved in both local seeds (-0.17 hurt twin pair deaths a game). On the 49 %
  rule (mean 49.8 %) it is a weak candidate: rank it behind any build that passed the local gate.
- Not fixable by a recall rule: 74 % of hurt-window rounds are in an enemy's reach. The deaths that are left come from
  fights: non-twin deaths +0.47 a game on v306's band games, the twins' late pair deaths +0.4, deaths to camps 1.01 v
  0.66.
- Not tested: a hurt body that walks toward allies rather than home when shadowed by a chaser at 4 (3 of 12 sampled
  far4 deaths). These are small.

**Band line (only if a slot is spare; not recommended):**
`hurt 1: twins commit/break/recall from higher HP (death x2)|_hurt|robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11 endx=3 s2b=1 hurtx=1|all`
