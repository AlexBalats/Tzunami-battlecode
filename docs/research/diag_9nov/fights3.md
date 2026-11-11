# fights3: where our fight quality still loses to the top's (9 Nov, agent)

**Question.** In the fights that do happen, where does our play lose to the top's? Then build the biggest quality fix
behind `fb3` (no extra fights or presence: better play inside fights we are already in, or ability readiness).

## Data and method

- **Band games (decoded):** `tz107_big` (tz-107 v the six band teams, 150, 8 Nov), `tz126_big` (tz-126 = tz-117 + fb2 3,
  150, seed-29 maps, 9 Nov; downloaded for this study), `top_v_band` (the top four v the same six, 119, 7 Nov bots;
  reweighted to our opponent mix, each band team equal).
- **Scripts:** `~/tzunami_data/analysis_9nov/fq/` (`python3 -I`, one process):
  - `fq.py LABEL` -> `fq_LABEL.pkl`: every champion hit with the hpk nominal damage model (Strength for a basic,
    coef x Focus for a cast, shields, Marcella's enhanced basic stuns, HoR's missing-HP bonus); fights = clusters of
    champion hits of both teams (gap <= 4 rounds, victim within 7: the hpk definition); per fight and side the start
    state (bodies within 6 of the first hit, HP, max HP, cooldowns), the first hit, stuns and their follow-up, hitters
    per target per round, kills, and per body every fight round (HP, nearest enemy, in reach, cast ready, action).
  - `fqsum.py` (fight tables), `fq2.py` (turn use per body-round), `fq3.py` (what a body does with a cast ready and an
    enemy in that cast's reach), `hor.py` (HoR by HP and distance), `idle.py` (what idle in-reach turns are).
  - Outputs: `sum_all.txt`, `sum3.txt` (with tz126_big), `turns_all.txt`, `cast_use.txt`, `cast3.txt`.
- **"Real" fight:** both sides land a hit, or someone dies (15.4 a game for us, 18.6 for the top).
- **Snapshot timing check [measured]:** a decoded `round r` line is the state at the start of round r, taken after
  its first step (moves / dashes of the first actor already applied: 59 of 59 checked). The hpk extractor's use is right.
- Turn order inside a round makes "in reach at the round's start" noisy; it is the same noise for both sides.
- Tags: [measured] from the replays; [rules] GameRules.md; [code] bots/_fb3; [guess].

## 1. The gaps, ranked [measured; per game, us tz107 / tz126 v the top]

| # | Gap | Us (tz-107) | Us (tz-126) | Top |
| --- | --- | --- | --- | --- |
| 1 | **HoR's landing dash** (1.75 x Focus + a one-round stun, radius 1 [rules]): dash landed on a champion with it ready and an enemy within 3 | **32 %** | 38 % | **68.5 %** |
| | ... below half HP (HoR's passive: +up to 50 % damage [rules]) | **4 %** | | **56 %** |
| | ... at >= half HP, adjacent | 44 % | | 76 % |
| | ... the same rounds spent on a basic only | 27 % | 22 % | 9 % |
| | HoR ready at a fight's start | 37 % | 34 % | 57 % |
| | HoR ready-and-in-range rounds a game | 3.4 | 2.8 | 7.5 |
| | HoR stuns a game | **2.1** | 2.2 | **10.4** |
| | HoR's share of our fight damage | 6 % | 6 % | 21 % |
| | HoR first hitter of a fight | 6 % | 7 % | 20 % |
| 2 | **Opening:** our damage share in a fight's first two rounds | **0.43** | 0.49 | **0.68** |
| | we land the first hit | 40 % | 42 % | 59 % |
| | ... with a stun / cast / basic | 13 / 20 / 67 % | 15 / - / - | 36 / 26 / 39 % |
| | ... by Vesper | 48 % | 45 % | 11 % |
| | band hits first and we never answer (it kills us untouched) | 18 % | | 3 % |
| 3 | **Cast use** (any damage / stun cast ready, enemy in its reach): cast at a champion | 36.5 % | 41.8 % | 62 % |
| | ... stepped away instead | 24 % | 20 % | 11 % |
| | ... below half HP: cast | 13.5 % | 19.5 % | 44 % |
| | Marcella / Cassi cast | 36 / 38 % | 42 / 43 % | 62 / 53 % |
| 4 | **Supports' share of the fight:** support damage dealt a body a fight | 199 | | 550 |
| | ... hit rate in a fight's first 3 rounds (per body-round) | 0.30 | 0.33 | 0.44 |
| | ... stepped away in those rounds | 0.28 | 0.25 | 0.17 |
| | Vesper's share of our fight damage | **59 %** | 57 % | 15 % |
| | Vesper bodies in a fight (near at start) | 0.49 | 0.49 | 0.14 |
| 5 | **Outcomes:** fights won (kills ours > theirs) / lost | 19 / 28 % | 22 / 25 % | 39 / 9 % |
| | even when we start with > 1.25x their HP nearby: won / lost | 35 / 14 % | | 54 / 4.5 % |
| | with < 0.8x: won / lost | 6 / 44 % | | 23 / 16 % |
| 6 | **Disengage:** a body below 40 % HP in contact dies | 44 % | 39 % | 27 % |
| | ... it stays in contact after going low (rounds) | 2.6 | | 3.2 |
| | outnumbered by 2+ in contact: dies | 32 % | 30 % | 14 % |

**Not gaps** [measured]:
- **Cast readiness overall at a fight's start** is level (any damage / stun slot ready 72 v 72 %; Cassi 91 v 90,
  Marcella 82 v 76): HoR is the exception.
- **Focus fire** is level: hitters per hit-round 1.26 v 1.26; rounds with 2+ hitters 21 v 21 %, all on one target in
  84 v 84 %.
- **Stun follow-up** is level or better: damage after our stun 0.094 of the victim's max HP v 0.077; stuns with no
  follow-up 30 v 35 %. We stun 3x less, we don't waste the stuns we land.
- **Idle turns in reach** are recall channels on both sides (`idle.py`: 306 of 368 sampled ours, 326 of 378 the top's).
- **Leaving early is not it:** our low bodies stay in contact *less* (2.6 v 3.2 rounds) and still die more; survivors
  leave at the same HP (0.67 v 0.69). The top's low bodies survive because the other side is losing the fight (gap 1-4).

**Reading.** The top wins fights in the first two rounds: a stun or a spell opens (61 % of its first hits), the
supports land it (HoR, Marcella, Ryth, Vendetta ~ evenly), and the band's bodies lose 15 % of max HP in the opening
round (hpk) before they can answer. Our fights open with Vesper's basic and our supports arrive late or step away.
Our HoR is the clearest single hole: it is the top's best opener (20 % of first hits, 10.4 stuns a game, 21 % of fight
damage) and ours lands its dash on a champion in a third of the chances, almost never when hurt. fb2 3 (tz-126) moved
cast use (+5 points) and the opening share (0.43 -> 0.49) but not HoR (stuns 2.1 -> 2.2; ready at start 37 -> 34 %).

## 2. Why our HoR doesn't land the dash [code: bots/_fb2]

- `act_fight`'s pounce (`roles` 4) and the no-stance `fb_cast_first` both need **HP >= 50 %**; below it HoR only
  basics (74 % of hurt adjacent rounds) though its passive makes the hurt dash its hardest hit.
- **Breaking** bodies never land it: `fb_break_cast` casts targeted spells only; `act_flee` spends the dash on a flee
  dash away (no damage on a champion).
- The **travel dash** (`dash_field`) spends it outside fights: HoR is ready at 34-37 % of fight starts (top 57 %).
  `dash_keep` 2 (queued as part of dash_keep 15) stops all of HoR's travel dashes; fb3 8 only near enemies.

## 3. The build: `bots/_fb3` = bots/_fb2 + `fb3` (static constexpr, default 0)

| Bit | What | Where |
| --- | --- | --- |
| 1 | The fight dash (act_fight's pounce, the no-stance cast-first dash) needs HP >= `fb3_hor_hp` (0.0) instead of 0.5 | `act_fight`, `fb_cast_first` |
| 2 | A breaking HoR (not fed, HP >= stance_low) next to a chaser lands its dash on it from a tile no farther from home (damage + a one-round stun that covers the run), then `act_flee` runs as before | BREAK block, `fb3_hor_land(true)` |
| 4 | A committed HoR whose pounce did not fire lands it after its hit on the team target (else least team rounds-to-kill) within 3; landing tile hits the most enemies, then nearest home | `act_fight` in-reach branch, `fb3_hor_land(false)` |
| 8 | HoR's travel dash (`dash_field`) waits while an enemy champion off its spawn is within `fb3_keep_r` 8 (seen this round or the last) | `dash_field`, `fb3_keep()` |

None of the bits makes a body commit, hold or approach: they change what HoR does on turns it already spends in
contact (bits 1, 2, 4) or keep the dash for them (8).

**fb3 = 0 check [measured]:** release and debug wasm of bots/_fb3 are byte-identical (`cmp`) to bots/_fb2's.

## 4. Local results (v tz = tz-117, 256 games each, seed 0; base = `fb2=3` = tz-126) [measured]

Paired by (map, side) with the base (`pair.py`). Local v tz is a sanity screen only: it does not predict the band.

| Build | Win v tz | Paired diff | Deaths diff | Games changed |
| --- | --- | --- | --- | --- |
| base fb2 3, fb3 0 | 53.9 % | | | |
| fb3 5 (bits 1 + 4) | 53.9 % | +0.0 ± 1.2 | +0.08 | 10 |
| **fb3 7 (bits 1 + 2 + 4)** | **54.3 %** | **+0.4 ± 2.1** (held −1.2 ± 2.7) | **+0.00** | 29 |
| fb3 13 (1 + 4 + 8) | 50.0 % | −3.9 ± 3.0 (held −6.0) | +0.28 | 58 |
| fb3 15 (all) | 48.8 % | −5.1 ± 3.0 (held −4.8) | +0.55 | 61 |

No faults or missing games (fb3 7).

**Bit 8 is the cost, and it breaks the brief.** HoR's travel dash kept near enemies hardly moves readiness at fight starts
(42 -> 44 %), but a ready dash switches on the `roles` 4 opener (`role_opener` needs `landing_dash_ready`). So it opens
fights: deaths +0.28 to +0.55. Keep it off; `dash_keep` 2 (queued) has the same risk.

**In-bot view** (fb_dbg counters, HoR only, r <= 600, fb3 5): HoR's turns with the dash ready and an enemy within 3 at
its own turn are 0.1 a game in no stance (91 % land it), 0.5 committed (87 %) and **0.7 breaking (2 %)**. So the
committed path already works at the moment HoR acts. Much of the replay-measured miss at >= 50 % HP comes from movement
inside the round: the enemy is within 3 at the round's start but not by HoR's turn. This noise is the same for the top
[guess: its HoR may act earlier in the team order]. The real in-bot holes are breaking turns (bit 2) and hurt HoR
(bit 1).

**Decoded KPIs** (side a, 128 games, whole game; r <= 600 in brackets; the band columns from `hkpi.py` are unweighted,
so they differ slightly from §1):

| KPI | base (fb2 3) | fb3 7 | fb3 15 | band tz-126 | band top |
| --- | --- | --- | --- | --- | --- |
| HoR dash landed (ready, enemy <= 3), HP >= 50 % | 43 % (51) | **57 % (55)** | 58 % | 46 % | 70 % |
| ... HP < 50 % | 4 % (5) | **26 % (30)** | 21 % | 14 % | 52 % |
| HoR stuns a game | 2.05 | **2.87** | 2.89 | 2.16 | 8.8 (raw) |
| HoR share of fight damage | 9.4 % | 10.8 % | 11.4 % | 6.2 % | 19 % |
| Opening (first 2 rounds) damage share | 0.483 | **0.510** | 0.480 | 0.489 | 0.672 |
| We land the first hit | 48.9 % | 51.1 % | 49.1 % | 42 % | 60 % |
| Fights a game | 12.3 | 12.6 | 13.1 | 14.8 | 17.6 |
| Fights won / lost | 22.8 / 23.6 % | **25.0 / 22.3 %** | 23.6 / 24.4 % | 21.8 / 24.6 % | 40.5 / 10.0 % |
| Kills a game / our deaths a game | 3.49 / 5.62 | **3.90 / 5.47** | 3.80 / 6.10 | | |
| HoR deaths a game | 0.80 | 0.76 | 0.77 | 0.81 | 0.47 |

fb3 7 moves what it targets: HoR's dash use, HoR stuns +0.8 a game, the opening share +0.03, fights won +2 points and
lost −1. It does this without more fights (12.3 -> 12.6) or deaths (−0.15).

## 5. Band queue

- `??|fb3 7 HoR lands its stun dash in fights (any HP; breaking: on an adjacent chaser, toward home; after the hit)|_fb3|fb2=3 fb3=7 fb=1`
- Not queued: fb3 8 / 15 (adds fights through the opener); fb3 5 (barely fires locally).

**Expected on the band** [guess]: HoR there is hurt more often (0.66-0.79 hurt ready rounds a game v 0.67-0.93 locally)
and breaks more, so bits 1 and 2 should fire at least as often. The gain is capped by HoR's readiness and presence (2.8
ready-in-range rounds a game v the top's 7.5); +0.8 HoR stuns a game is a tenth of the gap to the top.

**Stop rule:** HoR deaths or our deaths per fight up. Bit 2 is the only part that keeps HoR next to a chaser for a turn.

## 6. What is left (ranked; not built)

1. **Opening = supports' first rounds.** Our supports hit 0.30 a body-round in a fight's first 3 rounds (top 0.44) and
   step away 0.25-0.28 (0.17); Vesper deals 57-59 % of our fight damage (top 15 %) and is in a fight 3.5x as often.
   The top's Vesper is rarely near a fight; its supports open them. Every "fight more" rule has lost, so the open
   question is target choice inside the fight: who stands in front.
2. **Cast use while breaking:** with a cast ready and an enemy in range, our bodies step away 20-24 % of the time (top
   11 %). Walk-excluding casts are the hole; `fb_bc_k` lost locally on 8 Nov.
3. **HoR readiness / presence:** ready at 34-37 % of fight starts (top 57 %). This needs a travel-dash budget that
   does not also arm the opener (fb3 8 and dash_keep 2 do).
4. **Turn order** [guess]: `set_priority` decides who acts first within a team [rules]. Openers acting first would
   turn round-start positions into hits.

## 7. Files

- Scripts and outputs: `~/tzunami_data/analysis_9nov/fq/` (`fq.py`, `fqsum.py`, `fq2.py`, `fq3.py`, `hor.py`,
  `idle.py`, `hkpi.py`, `hkpi_r.py`, `pair.py`; `sum_all.txt`, `sum3.txt`, `turns_all.txt`, `cast_use.txt`,
  `cast3.txt`, `j_fb3*.txt`, `j_dbg.txt`; `fq_tz107_big.pkl`, `fq_tz126_big.pkl`, `fq_top_v_band.pkl`).
- Decoded band games: `~/tzunami_data/replays/tz126_big/` (150, new).
- Bot: `bots/_fb3` (no `.cambc`). The scratch variants, judge dirs and local decodes are deleted.
