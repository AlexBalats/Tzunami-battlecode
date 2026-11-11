# selection: do we ENTER bad fights, or fail to LEAVE them? (9 Nov, agent)

**Question.** Our band fights go bad (lost or bled) 31 % of the time; the top's go bad 12 %. Is that because we
enter fights we should avoid, or because we stay in them once they turn? Then: build the biggest lever as `sel` bits
in `bots/_sel`. A bit may cut bad fights; it may not add fights or presence.

**Short answer [measured]: neither.**
- **Entry states are about the same.** Our losing states at contact, and our size, explain 0 to 40 % of the gap,
  depending on how the states are binned.
- **Our exits match the top's.** We leave as often, as early and at the same HP.
- **The gap is what happens once the band hits first.** In the same entry state, those fights go bad for us 38 % of
  the time; for the top, 17 %.
- **tz-126 already breaks** on 82-95 % of the turns where a selection rule could fire (local v tz).
- **So the `sel` bits barely fire, and none is worth band time** except, perhaps, one probe (§5).

## Data and method

- **Band replays (decoded):**
  - `tz126_big`: 150 games, tz-126 v the six band teams.
  - `top_v_band`: 119 games, the top four v the same six. Reweighted so each band team counts equally.
  - `tz107_big`: 150 games, used as a check. It agrees with tz126_big within noise.
- **Fights:** the ones `fq.py` finds (fights3.md). A fight is "real" when both sides land a hit or someone dies.
  A fight's result is:
  - L: their kills > ours;
  - W: our kills > theirs;
  - B (bled): no kill either way, we took >= 25 % of our nearby max HP and >= 2x what we dealt;
  - E: everything else.
  - "Bad" means L or B.
- **Contacts (`contact.py`):** every time one of our bodies has its nearest enemy (alive, off its spawn) come within 6,
  after >= 5 rounds farther away. The state is taken within 6 of that body. The outcome is the next 15 rounds: the
  first real fight it is in, and whether it dies. A death is charged to the latest contact before it.
- **Leave window:** a free neighbour tile that is farther from the nearest enemy and out of every enemy's next-turn
  reach. Reach is melee 2, or 4 with a dash ready; ranged 3, or 4 with a damage cast ready. Walls are not decoded, so
  this test is wall-blind [measured, approximate].
- **Burst exposure (`expo.py`, `expo2.py`):**
  - K = the summed one-turn burst of the enemies within their next-turn reach + 1, divided by my HP.
  - Burst = Strength, + Strength again with a reset ready, + coef x Focus for the best ready damage cast (fq's table).
  - Every body-round off our spawn with an enemy within 7 is counted.
- **Scripts:** `~/tzunami_data/analysis_9nov/sel/` (`python3 -I`):
  - extractors: `sel.py`, `contact.py`, `expo.py`, `expo2.py`;
  - summaries: `selsum.py`, `exits.py`, `within.py`, `bytype.py`, `leave.py`, `selfights.py`, `exposum.py`, `peek.py`;
  - local KPIs: `lockpi.sh` + `lockpi.py`.

## 1. Entering [measured]

**Contacts a game** are close: 58.1 for us v 49.5 for the top. Per body-game they are about level: Vesper 12.3 v 9.9,
Vendetta 10.6 v 10.9, HoR 10.4 v 11.2, Marcella 10.2 v 11.8, Cassi 9.8 v 7.2.

**Deaths within 15 rounds of a contact:** 3.28 a game for us v 1.20 for the top. Splitting the 2.08 gap into "more
contacts in a bad state" (entry) and "worse per contact in the same state" (within):

| Binning of the contact state | Entry | Within |
| --- | --- | --- |
| bodies within 6 (ours − theirs) | +0.35 | +1.73 |
| live HP within 6 (ours / theirs) | +0.63 | +1.44 |
| both of the above | +0.84 | +1.24 |
| my max HP / their biggest | +0.88 | +1.20 |
| clearly losing (outnumbered by 2+, or < 0.6x their live HP) | +0.56 | +1.51 |

For bad fights rather than deaths, the within part is +2.2 to +3.0 of the +3.86 gap.

**Where entry does differ: size.**
- We have 19.8 contacts a game with an enemy of >= 1.67x our max HP within 6. The top has 7.0.
- Per contact we die after 8.6 % of these and 4.1 % of the rest (top: 5.4 % and 1.9 %).
- By body, the share of contacts with such an enemy:

  | Body | Us | Top |
  | --- | --- | --- |
  | Vendetta | 32 % | 10 % |
  | HoR | 40 % | 10 % |
  | Marcella | 22 % | 6 % |
  | Issac | 38 % | 12 % |
  | Cassi | 57 % | 56 % |

  This is the support-size gap from the economy studies (hp_per_gold.md, yield.md). It is not a choice made at
  contact.
- Clearly losing contacts: 5.6 a game v 2.0, with P(die) 0.125 v 0.087.
- **Upper bound:** if every clearly losing contact were avoided, at no cost elsewhere, we would lose 0.43 fewer deaths
  a game. Avoiding every contact with a >= 1.67x enemy would save at most 0.89.

**Who closes the gap at contact:** we do in 25 % of contacts that end in a death, the top in 30 %. They do in 27 % v
20 %; both sides move in about half the time. **We do not walk into fights more than the top.**

**State at the first contact of a fight** (`selfights.py`):

| Fights a game, and their state at contact | Ours, bad | Ours, other | Top's, bad | Top's, other |
| --- | --- | --- | --- | --- |
| fights a game | 4.67 | 10.16 | 2.31 | 16.27 |
| bodies ours − theirs within 6 | +1.00 | +1.17 | +0.72 | +0.83 |
| live HP ratio | 1.35 | 1.84 | 1.41 | 1.85 |
| contact body < 0.6x their biggest | 0.37 | 0.15 | 0.23 | 0.07 |
| our cast readiness | 0.65 | 0.65 | 0.65 | 0.60 |
| their cast readiness | 0.61 | 0.62 | 0.63 | 0.64 |
| within 10 of our spawn | 0.24 | 0.24 | 0.13 | 0.14 |
| round | 590 | 589 | 503 | 548 |
| clearly losing at contact | 0.23 | 0.06 | 0.18 | 0.07 |
| **we hit first** | **0.19** | 0.52 | **0.41** | 0.62 |

Our bad fights start from about the same states as the top's bad fights. The one big difference is who hits first.

## 2. Leaving [measured]

**Deaths charged to a contact**, ours v the top's:
- There was a leave window somewhere between the contact and the death in 97 v 97 %.
- There was one after the first HP drop in 48 v 54 %.
- The last window came 1.8 v 2.5 rounds before the death, at 42 v 46 % HP.
- In those windows the body stepped away on 40 v 35 % of rounds, stayed on 40 v 41 %, and stepped closer on 20 v 24 %.
- After the first HP drop, the dying body had no window at all in 22 v 30 % (trapped).

**Bodies in bad fights** (died, or lost >= 30 % HP):
- a window after the first drop: 0.75 v 0.85;
- 6.0 v 6.7 such rounds;
- stepped away on 0.44 v 0.44 of them.

**Every hurt contact** (`leave.py`): at the first window after the first damage, our bodies take it 33 % of the time
(top 27 %). Below 40 % HP: 61 v 60 %; at 40-70 % HP: 46 v 35 %. Bodies that took it died at the same rate as bodies
that stayed:

| | Took the window: P(die) | Stayed: P(die) |
| --- | --- | --- |
| Us | 0.079 | 0.068 |
| Top | 0.029 | 0.029 |

Leaving is not what saves the top's bodies: their hurt contacts end in death 4.2 % of the time, ours 9.4 %.

**Burst exposure** (`expo.py`, body-rounds a game, P(die within 3 rounds)):
- K >= 0.5 (the enemies in reach carry half my HP): 63.3 rounds for us v 39.8 for the top. P(die) is about the same:
  0.19 v 0.17. By band: K 0.5-1 0.093 v 0.088, K 1-2 0.32 v 0.27, K >= 2 0.55 v 0.53.
- With a safe step available, the reaction is the same too: away on 49 v 47 % of rounds (K 0.5-1).
- **The whole excess is next to a bigger enemy** (>= 1.5x my max HP within 10): 43.7 v 20.7 rounds. With smaller
  enemies it is level: 19.6 v 19.1.
- Most of the excess is at 3-5 tiles and at >= 70 % HP. Vesper accounts for 11.9 rounds v the top Vesper's 2.0.

## 3. What does differ: the band opens on us [measured]

**Fights by who hits first**, a game (bad / lost / won rates):

| First hit | Us: fights | bad | lost | won | Top: fights | bad | lost | won |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| we hit first | 6.23 | 0.14 | 0.10 | 0.35 | 10.95 | 0.09 | 0.06 | 0.44 |
| they hit first | 8.60 | **0.44** | 0.35 | 0.12 | 7.63 | **0.18** | 0.12 | 0.31 |
| they hit first, state OK | 7.25 | **0.38** | 0.30 | 0.14 | 6.81 | **0.17** | 0.11 | 0.32 |
| they hit first, clearly losing | 1.35 | 0.77 | 0.65 | 0.04 | 0.82 | 0.29 | 0.20 | 0.19 |

Split of the bad-fight gap (4.67 v 2.31 a game):
- how often each opening-and-state combination happens: **−0.15**;
- the bad rate inside each combination: **+2.51**.

**Per contact:** when the band hits first, we die 16.7 % of the time v 5.5 %. 46 % of our charged deaths dealt no
damage in their fight (top 17 %). This matches fights3.md: our opening damage share is 0.49 v 0.68, and HoR stuns
2.2 v 10.4 a game.

**What this means:** the gap is our answer to their opening (casts, stuns, focus), not whether we were there or stayed.

## 4. In-bot view: tz-126 already breaks in these states [measured, local v tz, 16 maps, `sel_dbg`]

Turns per body-game to r1000, and the share already in BREAK at the decision point:

| State | Turns | In BREAK | Committed | Farming |
| --- | --- | --- | --- | --- |
| burst >= HP with a >= 1.5x enemy ("lethal") | 1.4-2.8 | 94-95 % | 4-6 % | 0-1 % |
| burst >= 0.5 HP, with a >= 1.5x enemy | 4.5-6.5 | 89-90 % | 6-7 % | 3-4 % |
| clearly losing (`sel_losing`) | 10.1 | 95 % | 4 % | 1 % |

Most of the BREAKs come from the fed break or the contact sim. A pre-contact avoid or an earlier break only changes
the leftover 1-10 %. The exposed bodies are mostly breaking already: being chased.

## 5. The build: `bots/_sel` = tz-126 + `sel` (static constexpr, 0 = off)

| Bit | What |
| --- | --- |
| 1 | **Burst guard:** a body that is not committed breaks off (as the fed break: no hunt / opener / finish / break casts) when the one-turn burst of the visible enemies within `reach_of + sel_r` (1) covers `sel_k` (1.0) x its HP after Durability, and one of them has >= `sel_big` (1.5) x its max HP. A kill that lands this round overrides. |
| 2 | The same for a committed body whose team can't kill its target this turn (`fb_team_dmg` < live HP). |
| 4 | Bits 1 / 8 / 16 also end a WORK / p1 hold. Bit 1 alone leaves the hold to its own stops. |
| 8 | **Clearly losing local state** (`sel_losing`): within 6, our live HP < `sel_hp` (0.6) x theirs, or they have `sel_nd` (2) more bodies; not committed. |
| 16 | **Pre-contact:** a visible enemy (off its spawn) with >= `sel_big2` (1.67) x my max HP within `sel_far` (8), within its reach + `sel_far_m` (3) or closing, while our max HP within 5 is below `sel_gang` (1.0) x theirs within 6 of it; not committed. Twins excluded unless `sel_twins`. |

- `sel_dbg 1` prints counters (`SELDBG` at r1000) and each firing (`SELFIRE`). It is for scratch builds only.
- The helpers are static functions outside `play_turn`. A lambda inside `play_turn` renumbers the others in the wasm
  name section and broke byte identity.
- **sel 0 [measured]:** the release and debug wasm are byte-identical (`cmp`) to bots/tz's (a scratch copy built the
  same way).

### Local results (v tz, 256 games, seed 0; a sanity screen, not a predictor of the band) [measured]

| Build | Win | Paired diff v base | Games changed | Deaths | fuelEx | gold300 |
| --- | --- | --- | --- | --- | --- | --- |
| base (sel 0) | 50.0 % | | | 4.6 | 21.5 | 1537 |
| sel 1 | 49.6 % | −0.4 ± 2.6 | 43 | 4.7 | **46.2** | 1533 |
| sel 3 | 50.4 % | +0.4 ± 2.6 | 45 | 4.7 | **45.7** | 1536 |
| sel 8 | 48.8 % | −1.2 ± 1.6 | 17 | 4.6 | 21.1 | 1519 |
| sel 16 | 49.2 % | −0.8 ± 1.5 | 14 | 4.6 | 21.9 | 1525 |

- **Firing counts** (16 maps, `SELFIRE`): bit 8 fired about once in 32 games; bit 16 never fired. In a mirror the
  enemy is rarely 1.67x bigger with nothing of ours near, and the fed break or sim has broken already.
- **Fuel:** bits 1 / 2 double the fuel cuts (21 -> 46 a game). The cost is the ability scan of every enemy in reach,
  every turn. The paired changes in sel 1 / 3 come from the cuts, not the rule.
- **No faults or missing games** in any run.

Decoded KPIs from the kept games:

All 256 games, focus side only:

| KPI | base | sel 3 | sel 16 |
| --- | --- | --- | --- |
| fights a game | 12.79 | 13.21 | 12.89 |
| won / lost | 23.3 / 23.3 % | 23.4 / 22.7 % | 23.5 / 23.6 % |
| bad (L + B) | 30.5 % | 29.9 % | 30.4 % |
| kills / deaths a game | 3.69 / 5.79 | 3.83 / 5.88 | 3.71 / 5.82 |
| contacts a game | 68.1 | 69.8 | 67.9 |
| contacts with a >= 1.67x enemy | 9.8 | 9.8 | 9.9 |
| clearly losing contacts | 4.0 | 4.0 | 4.1 |
| P(die within 15 of a contact) | 0.041 | 0.039 | 0.042 |
| burst-exposed (K >= 0.5) rounds a game | 52.1 | 55.5 | 53.2 |
| gems banked / gold300 | 821 / 1537 | 825 / 1536 | 816 / 1525 |

All within noise. None of the bits moves bad fights, exposure or collection locally.

## 6. Verdict and band queue

- **Selection is not our fight-loss problem.** At contact we enter the same states as the top, and tz-126 already
  breaks on almost every turn a selection rule would test. Our exits are as frequent and as early as the top's, and
  leaving saves neither side's bodies.
- **The gap is the response once the band opens.** Their hits land first in 58 % of our real fights (top 41 %), and
  those fights go bad 44 % of the time v 18 %. The levers point at fights3.md §6: supports' first rounds, casts while
  breaking, HoR readiness, turn order (`set_priority`).
- **Band queue:** at most one cheap probe of the only bit that fires more on the band than locally. Bits 1 / 2 (fuel)
  and 8 (no-op) are not queued.
  - `??|tz-126 + sel 16 (pre-contact: break from a >= 1.67x enemy near when we're smaller locally; no-op locally)|_sel|sel=16`
  - Expect small: fed_far_k 3 lost locally (7 Nov) and hunt_brk was neutral on the band (tz-68). Stop if share <= 0.
- **If anything is built next:** the opening response. When the band lands the first hit and our side is not
  outnumbered, every body in reach answers that turn with its ready cast or stun on the hitter, instead of the break /
  sim re-deciding. That adds hits inside fights we are already in, not fights.
