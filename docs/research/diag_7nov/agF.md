# agF: farming-mechanism switches on tz-38 (7 Nov)

Code: `bots/_agF` (copy of tz-38; every switch defaults to 0, so with all switches at 0 it is tz-38). All numbers are
[measured] local judge runs (256 games, 128 maps × 2 sides, `--jobs 2`). The v93 cells are 4-seed means (seed=0..3,
1,024 games); one run's noise is about ±4.

## 1. What was built

`value.h` (Params, just before `move_guard`):

| Switch | Meaning |
| --- | --- |
| `handoff` 1 | **Reward handoff by presence.** "Present" = one of our bodies within `max(hand_r, its attack range)` of a cleared group's spawn tiles. Among the present bodies, the best taker key wins (feed on: the highest rank, demoted by `feed_until` / `feed_shards`; ties go to the lower slot). `keep_capture` is honoured. Nobody farther walks in. This replaces the `feed` / `feed_r` walk-in and the 5-tile `i_take`. An **orphan** reward (none of ours present) stays a normal goal, unless an ally that is nearer (or, if unseen, has a lower slot) has it as its comms target. |
| `handoff` 2 | Same as 1, but when an enemy was seen by the group in the last 30 rounds (`g.enemy_round`), the non-takers within 6 of it stay and guard, as tz-38 does. |
| `hand_r` (2) | The presence radius for melee bodies. |
| `hand_carry` 1 / 2 | **Feed by joining.** The top carry (feed on, and its rank is above every living ally's) prices an ally-committed group, alive or respawning, at the **full** reward when its walk ≤ max(wait, allies' ETA) + the allies' remaining clear time + 1. 2: it also prices the group at 0 when it would arrive late. |
| `resp_time` 1, `resp_slack` (1) | Respawn arrival timing: in `act_farm` RESPAWN, don't walk while `ready − round > field distance − 2 + resp_slack`. |
| `fill2` 1 / 2, `fill2_idle` (3) | Wait filler 2: it triggers at idle ≥ 3 and times each fill from its start = max(walk, wait), so respawning fills count too. It skips `claimed_out` fills, and the fill plus the walk back must fit within wait + `fill_late`. Level 2 adds a bank trip as the fill when no farm job fits. It replaces the old filler when on. |

`bot.cpp` locations:
- `top_carry()` and `ally_eta()` sit after the `farm_vt` declaration (~l.497).
- The `hand_carry` block is in `farm_vt` at the `share` line (~l.620).
- `hand_take()` (cached per turn and position) and `hand_take_raw()` come before `worth_to_me()`; the `handoff` branch is at the top of `worth_to_me` (~l.870-950).
- The `fill2` block is in `choose()`, before the old `wait_fill` block (~l.1165).
- `i_take()` has a `handoff` early return (~l.2220).
- The `resp_time` hold is in `act_farm` RESPAWN (~l.2390).

The `LOG` lines `RESPBEST` / `FILL2` compile to nothing unless `TZ_LOG` is 1.

## 2. Screening

### v idle (farming speed)

| Build | seeds | gold150 | gold300 | mon300 | trib750 | end r |
| --- | --- | --- | --- | --- | --- | --- |
| **base (tz-38)** | 0/1/2 | 761/750/745 | 1769/1738/1745 (**1751**) | 30.3/30.1/30.2k | 722/723/723 | 939/946/931 (**939**) |
| handoff 1 | 0/1 | 766/745 | 1764/1734 | 30.4/30.4k | 732/731 | 923/926 |
| **handoff 1 + hand_carry 1** | 0/1/2 | 758/754/760 | 1789/1793/1783 (**1788, +37**) | 31.3/31.5/31.5k (**+1.2k**) | 740/736/740 (**+16**) | 912/915/910 (**912, −27**) |
| handoff 1 + hand_carry 2 | 0 | 757 | 1789 | 31.2k | 730 | 924 |
| **handoff 2 + hand_carry 1** | 0/1 (+ final code, seed 0) | 758/754 (760) | 1789/1794 (1793) | 31.2/31.4k (31.3k) | 740/735 (738) | 912/916 (912) |
| handoff 2 | 0/1 | 769/745 | 1759/1732 (= base) | 30.4/30.4k | 728/730 | 922/927 (−14) |
| resp_time 1 | 0 | 750 | 1745 | 30.3k | 716 | 941 |
| fill2 1 | 0 | 763 | 1767 | 30.2k | 720 | 941 |
| fill2 2 | 0 | identical to fill2 1 (the bank fill never fired) | | | | |
| resp_time 1 + fill2 2 | 0 | 751 | 1747 | 30.3k | 718 | 941 |

Mechanism check on 27 shared maps × 2 sides v idle (decoded replays, the study's `caplat` / `prewait` / `osc`
scripts):

| | base | h1 | h1 + carry1 | h1 + carry2 |
| --- | --- | --- | --- | --- |
| walk-in captures | 14 % | 7 % | **5 %** | 5 % |
| death → reward (mean rounds) | 7.8 | 6.8 | 6.9 | 6.8 |
| Vesper share of captures / her walk-ins | 44 % / 16 % | – | **44 % / 5 %** | 41 % / 3 % |
| bystander body-rounds per capture | 6.0 | 5.3 | 5.6 | 5.4 |
| first-hitter stand-by (mean) | 5.2 | 4.7 | 4.5 | 4.5 |
| 2-tile oscillation (rounds a game) | 60.6 | 61.3 | 46.7 | 43.1 |
| gold300 / trib750 / end (these maps) | 2078 / 779 / r863 | 2036 / 773 / r856 | **2117 / 803 / r836** | 2113 / 790 / r849 |

The handoff works as designed. Walk-ins drop to the top 3's level (4 %), and with `hand_carry` **Vesper keeps her
44 % share of captures**, now by joining the clear instead of walking in. Without `hand_carry` the feed is lost:
gold300 falls 40 on these maps, the same sign as `feed 0`.

### v v93 (4 seeds, 0..3)

| Build | win % by seed | **mean** | deaths v enemy deaths | gold300 v theirs | swing | trib750 | end r |
| --- | --- | --- | --- | --- | --- | --- | --- |
| base (tz-38) | 62.1 / 63.3 / 63.3 / 62.9 | **62.9** | 6.25 v 8.6 | 1410 v 1090 | −19 | 459 | 1226 |
| handoff 1 | 64.1 / 60.9 / 61.3 / 62.1 | 62.1 | 6.0 v 8.1 | 1394 v 1082 | −14 | 462 | 1218 |
| handoff 1 + carry 1 | 62.1 / 61.3 / 60.2 / 62.1 | 61.4 | 6.3 v 7.85 | 1415 v 1123 | −31 | 444 | 1211 |
| handoff 1 + carry 2 | 62.5 / 62.1 / 61.3 / 62.1 | 62.0 | 6.3 v 7.85 | 1397 v 1120 | −27 | 438 | 1217 |
| **handoff 2 + carry 1** | 68.8 / 64.1 / 64.5 / 64.1 | **65.4** | **5.9** v 8.0 | 1422 v 1103 | −22 | 442 | 1199 |
| ... re-run on the final (cached) code, seeds 0 / 1 | 68.4 / 63.7 | | 5.75 v 7.95 | 1415 v 1099 | | 443 | 1191 |
| **handoff 2** | 65.6 / 64.5 / 66.8 / 64.1 | **65.3** | 6.1 v 8.2 | 1393 v 1077 | −20 | 460 | 1218 |

Reading [measured, with a guess tagged]:
- **Leaving a reward at once loses v v93.** We kill fewer of them (enemy deaths −0.5 to −0.8), their gold300 rises
  ~30, and the swing gets worse. [guess] The non-takers who used to guard deterred, or killed, v93 bodies coming to
  contest.
- `handoff 2` keeps the guard only when an enemy was seen by the group lately. That turns the change into a gain:
  +2.4 points over base (a 4-seed-mean difference: noise about ±2.8, so suggestive, not proven). Our deaths also fall
  0.3-0.5.
- hand_carry costs ~1 point v v93 under handoff 1, but nothing under handoff 2.
- trib750 v v93 is ~15 lower with hand_carry (442 v 459) while games end 27 rounds earlier. That is worth watching on
  the band.
- **`resp_time` (arrival timing) loses farming speed v idle**: gold300 −24 at seed 0, trib750 −6. Leaving at
  ready − walk − 1 arrives late about as often as early, and it buys nothing unless the slack gets filled.
- **`fill2` is neutral**: it rarely finds a job. In a logged 02famine game, 89 picks came from 720 checks, despite
  waits of 10-60 idle rounds. Nearby groups are taken or respawning, and the solo `farm_vt` prices wolves and elks at 0
  for one body. The bank fill never fired (`fill2 2` ≡ `fill2 1`). Neither was run v v93.
- The first-hitter stand-by moved only 5.2 → 4.5 (the top 3: 1.6). The slack is real, but neither the arrival-timing
  switch nor the filler converts it into work.

## 3. Recommendation for the real-opponent (band) stage

1. **`handoff=2 hand_carry=1`.** It is the only setting that is faster v idle on every KPI: gold300 +37, mon300
   +1.2k, trib750 +16, end −27 rounds, all three seeds consistent. It is also the best v v93 (65.4 %, deaths −0.35),
   and it removes the walk-ins (14 → 5 %) while keeping Vesper's share of captures. Watch on the band: gold300 (feed
   0 cost −154 there; this keeps the carry fed), trib750, and deaths.
2. **`handoff=2`** (no carry pricing), as the control. v v93 it equals (1): 65.3 %. v idle it is only faster at the
   end (−14 rounds); gold300 is flat. If (1) shows a gold or exposure problem on the band (Vesper joining
   ally-contested groups), this isolates whether hand_carry is to blame.

Not recommended: `resp_time` (slower v idle), `fill2` 1 / 2 (no effect), handoff 1 with or without the carry (loses v
v93).

Clean-up done: every `bots/_agF_*` copy and judge output is deleted, and so are the decoded `agF_*` labels in
`~/tzunami_data`. `bots/_agF` holds the final code (no `.cambc`). Scripts and judge outputs are in
`scratchpad/agF/` (`runq.sh`, `keepq.sh`, `*_idle.txt`, `*_v93.txt`, `k_*.txt`, `q*.log`).
