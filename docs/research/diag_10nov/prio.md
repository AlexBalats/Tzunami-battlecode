# prio: what the top and the band do with `set_priority` (10 Nov, agent `prio`)

**Question.** What priority values do the top and band teams set, when, and what acting order pays? Then build it.

**Short answer (Part 1, decode).**
1. The priority value is in the replay [measured]: the step carries it (`pv` on step kind 9) and every champion's
   state carries `priority`, `nextPriority`, `draftOrder` (`pr`, `npr`, `dro` in round lines). `tools/replay/decode.mjs`
   now writes them (added fields only). 234 games re-decoded into `~/tzunami_data/replays/prio_sample/`.
2. **Team A starts every odd round, team B every even round** [measured: 217,079 of 217,079 round changes flip; first
   actor by parity in 20 games, 18,814 rounds, no exception]. So "do we start next round" is known from the team id and
   the round number, with no vision.
3. **Four teams flip the sign of their fighters' priority with the round parity**: high (+) for rounds they start,
   low (-) for rounds they go second. That makes the fighter the last actor of round R and the first of R+1 = two
   turns with no enemy turn between, every second round. They are **stellar best girl (rank 1), Intercontinental Fish,
   policy wonk (band) and NEETCoders**. Fish lands **32 %** of its kills on the second turn of such a double; stellar
   15 %, policy wonk 13 %; we land 0 %.
4. The other top teams do **not** flip, and they differ from each other: Mite = nearest-first (100 - distance, like our
   `prio_fight`), BattleCats = fighters act **last** (negative values), Vvvvv = static draft order with a flag for the
   body in contact, Ad Astra = fighter first. All of them fight well (kills 8 a game, deaths 3-5). **So acting order
   is not what separates the top from us; the flip is the only order trick with a measurable kill share.**
5. "Hitting first" does not rank teams [measured]: first-hit share in mutual-hit rounds is BattleCats 0.38, Mite 0.36,
   stellar 0.46, Fish 0.48, against us 0.57 (tz-mega, kills 3.5 v deaths 5.3 a game). This agrees with the band result
   that `prio_fight` raised first hits but not fights won.

## 1. Team: values set, when [measured; games in the sample]

"Fighter first" = in rounds where some but not all of a team's living bodies have an enemy within 3, the share where
the team's first actor is one of them (start rounds / second rounds; chance ~0.30). "Fighter last" likewise.
Doubles = same body is the last actor of round R and the first of R+1.

| Team (games) | Values set | When / rule that fits | Fighter first: start / second | Fighter last: start / second | Doubles a game | Double strikes a game |
| --- | --- | --- | --- | --- | --- | --- |
| **stellar best girl** (34) | 47,000 distinct packed ints, re-set every turn (4,700 calls a game); low 16 bits change every call (noise or a message); high bits = class | non-fighters: positive class by slot; **fighters: a negative class (-0x208.....) for rounds they go second, a high positive one (0x543...., 0x28c....) for rounds they start** | 0.60 / 0.40 | 0.43 / 0.57 | 24.4 | 7.1 |
| **Intercontinental Fish** (31) | -2..-12 by slot outside fights; **+-(700 + k), k 0-110** in fights; small positive (19-31) when fleeing at low HP | set at the END of the turn, every turn in a fight; **sign = + if they start next round, - if not**; the same body keeps the largest magnitude both ways (716 -> -712 -> 744 -> -719), so it is last then first | 0.67 / 0.15 | 0.19 / 0.65 | 43.7 | 13.4 |
| **Mite** (34) | 1020 / 1019 at the start; **94-99 in contact = 100 - distance to the nearest enemy**; 3,000 + that when attacking with a cast; 0 when leaving; 18,965 one special state | end of turn, every turn; no parity flip | 0.42 / 0.38 | 0.32 / 0.35 | 18.6 | 2.3 |
| **BattleCats** (41) | 8-20 by body outside fights; **negative in fights (-22 down to -159, in steps of 7 / 14)**; 35 and 40 for a body in contact at low HP or after being hit | start of turn; fighters act LAST except the 40s; no parity flip | 0.45 / 0.43 | 0.54 / 0.55 | 26.6 | 3.1 |
| **Vvvvv** (31) | (6 - slot) x 2^25 = static draft order, re-sent every turn (6,400 calls a game); + 2^28 / 2^29 / 2^30 flags | flag set for the body next to an enemy (acts first); 87 % of rounds are plain draft order | 0.66 / 0.61 | 0.26 / 0.27 | 7.7 | 1.8 |
| **Ad Astra** (23) | packed: byte 3 = body id + flag 0x10 / 0x20, byte 2 = state code 1-7, low 16 bits a score | start of turn; the flag goes on in melee contact (acts first) | 0.70 / 0.67 | 0.18 / 0.19 | 2.4 | 0.9 |
| **policy wonk** (47, band) | 0 or 4-8 by slot outside fights; **+-(100 + k), k 0-16** with an enemy within ~5; **200 fixed below ~20 % HP** | end of turn; **sign = + if they start next round, - if not** (the cleanest flip) | 0.76 / 0.13 | 0.07 / 0.73 | 40.3 | 5.3 |
| **Team Kungarna** (47, band) | 15-20 by body; 35 / 39 / 40 with an enemy near | start of turn; act first near an enemy; 9 distinct values in all | 0.58 / 0.57 | 0.20 / 0.20 | 3.6 | 0.3 |
| **QS2isLaw** (18, band) | 700-1,500 by slot; ~99,000 in contact; -500,000 / -1,000,000 for some states | end of turn; fighter first | 0.73 / 0.72 | 0.21 / 0.22 | 5.4 | 0.3 |
| **Claudus Maximus** (34, band) | 0 / 1 mostly; INT_MAX - x in contact; INT_MIN | end of turn; fighter first; 73 % plain draft order | 0.77 / 0.74 | 0.09 / 0.12 | 0.3 | 0.0 |
| **Rogue Lock Pickers** (15, band) | only 0, -10, +10 | start of turn; fighters mostly act LAST (-10) | 0.24 / 0.22 | 0.58 / 0.60 | 2.9 | 0.1 |
| **:3** (18, band) | k x 2^28 by slot + a small low field | end of turn; near chance order | 0.43 / 0.41 | 0.28 / 0.32 | 0.2 | 0.0 |
| NEETCoders (5) | **+-1,400, +-1,060..1,260** in fights; 35-60 by slot | **parity flip** | 0.66 / 0.28 | 0.04 / 0.46 | 97.8 | 6.2 |
| test4 (15) | slot 1-3 + 100 x level (101-303), 151 | end of turn; fighter first | 0.79 / 0.70 | 0.07 / 0.11 | 4.1 | 1.5 |
| **us, tz-mega** (60, `prio_fight 1`) | 0; 102-108 = 100 + (8 - distance); +50 below 40 % HP | start of turn; fighter first | 0.83 / 0.82 | 0.04 / 0.04 | 3.5 | **0.0** |

Static or dynamic: every team is dynamic (re-set in fights); only Vvvvv is close to static (draft order 87 % of rounds).

## 2. Why the flip is a double turn against EVERY enemy [rules + measured order]

Turn slots in a round: the starting team's rank i acts at slot 2i, the other team's rank j at 2j + 1.
- Static ranks: my rank i against an enemy rank j: if i < j I always act before them, if i > j always after
  (strict alternation). Only against the enemy of EQUAL rank do I get the pattern me-me-them-them.
- Flip (first when we start, last when we go second): me-me-them-them against every enemy body, whatever its rank.
  The price is the mirror: each enemy then has two turns in a row against that body.

## 3. What order pays [measured, 234 games]

| Team | Kills / deaths a game | First-hit share (mutual-hit rounds) | Kills landed on the 2nd turn of a boundary double | ... and the 1st turn hit the same victim | Own deaths on an enemy's 2nd double turn |
| --- | --- | --- | --- | --- | --- |
| Intercontinental Fish | 10.6 / 4.7 | 0.48 | **32 %** | 16 % | 4 % |
| stellar best girl | 8.3 / 2.3 | 0.46 | **15 %** | 6 % | 0 % |
| policy wonk | 4.7 / 10.7 | 0.45 | **13 %** | 7 % | 11 % |
| NEETCoders | 6.4 / 4.4 | 0.36 | 38 % | 25 % | 0 % |
| Mite | 8.0 / 3.0 | 0.36 | 6 % | 4 % | 7 % |
| BattleCats | 8.5 / 3.5 | 0.38 | 7 % | 3 % | 12 % |
| Vvvvv | 8.2 / 5.1 | 0.60 | 3 % | 1 % | 13 % |
| Ad Astra | 6.7 / 6.7 | 0.64 | 0 % | 0 % | 27 % |
| Team Kungarna | 4.3 / 7.2 | 0.50 | 3 % | 0 % | 8 % |
| Claudus Maximus | 1.6 / 4.7 | 0.60 | 0 % | 0 % | 19 % |
| us (tz-mega v the band) | 3.5 / 5.3 | 0.57 | **0 %** | 0 % | 0 % (60 games v the band: policy wonk is 10 of them) |

- The flip teams turn doubles into kills: Fish 3.4 kills a game on a double's second turn. A team that flips also
  dies less on enemy doubles (stellar 0 %, Fish 4 %): the enemy cannot hold the boundary against it, because the
  flipper is always last / first.
- No order rule explains fight strength on its own: Mite and BattleCats kill as much without the flip, with opposite
  rules (nearest first v fighters last). [measured]
- What flip teams do on the two turns: they attack more on the second turn (the first actor of the start round):
  Fish attacks on 53 % of those turns v 27-31 % on its other fight turns; stellar 59 % v 28-32 %. Steps into contact
  are not concentrated on the first turn (Fish 8 % first turn, 14 % second).

## 4. Order outside fights

- Tribute: a channel of N turn ends started as the round's last actor loses one enemy window (the next turn comes
  with no enemy turn between) [rules]. Not measured as a separate effect here.
- Dead bodies still take (empty) turns in the order, so they count for rank [measured in traces].

## Scripts

`~/tzunami_data/analysis_10nov/prio/`: `mkidx.py`, `dec1.sh` (sample + decode), `lib.py`, `calls.py`, `summ.py`
(values per team), `order.py` (fighter first / last, doubles), `kills.py`, `dblk.py` (kills on doubles), `t1t2.py`,
`trace.py TEAM GAME` (round-by-round priorities).

## Part 2: build

**Short answer.** The double turn is built, compiles and fires: 80-98 doubles a game (base 4-6), 13-17 double
strikes a game (base 0.1-0.3), 19-30 % of our kills on a double's second turn (base 0-1 %). Locally v `_m2` the flip
alone (`priox=19`) is 51.2 % and 53.5 % (2 seeds); the flip + the second-turn strike (`priox=23`) is 57.0 % on one seed
(the second seed was stopped at the wrap-up). The stun bits compile and fire but have no local win yet.

### What was built (`bots/_prio`: `src/bot.cpp`, `src/value.h`; switch `priox`, static constexpr)

Parity [sdk + measured]: `detail::absolute_team(team::ally)` (= `sdk_my_team`) 0 is team A; A starts odd rounds. Checked
in decoded local games on both sides (the doubles appear as side a and as side b).

| Bit | What it does | Compiles | Fires [measured, local] |
| --- | --- | --- | --- |
| 1 | A body with an enemy within `priox_r` (6) sets +m if we start the next round, -m if not; m = 100 + (8 - distance) | yes | 80-98 doubles a game |
| 2 | Below `priox_low` (40 %) HP: fixed +300 (always first) | yes | counted in the debug line, not measured apart |
| 4 | **Changed from the first design.** On the second turn of a double, a body with a champion in reach strikes it first (cast + basic); a ranged body not when the enemies' two turns would kill it | yes | hit share on second turns 0.47 -> 0.52; kills on a second turn 1.34 -> 1.62 a game (32 games each) |
| 8 | Priced opens (engx 8) wait at the second turn. The first build tested the phase after the new priority was set, so it never fired; fixed | yes | no visible effect: 127 v 119 gave the same games bar 1-2 |
| 16 | The striker (quick_kill) gets +40 magnitude | yes | in every run below, not measured apart |
| 32 | Cassi with her stun ready now or next turn gets +60 magnitude (the boundary slot); her stun stays off camps while an enemy was seen within `priox_camp_r` (12) in the last `priox_camp_t` (10) rounds | yes | camp-or-miss stuns 34.2 -> 31.8 a game, champion stuns 8.5 -> 8.2: small |
| 64 | A body with stun time left is hit first by every body that reaches it; a commit on it is allowed over a break, a fed break and the gate, unless the other enemies in reach kill me this turn | yes | champion stuns 9.1 a game, damage by the next round 93 (base 96): not moved |
| 128 | The mirror: on a double a commit that is not a kill, a finish or a stunned target is dropped when the enemies' two turns after it would kill me (`priox_mirror_k`); the recall threat test uses the two-turn reach (the old bit 4) | yes | double strikes 16.8 -> 13.7 a game, kills 4.7 -> 4.1 (32 games): it costs strikes |

**cmp:** `priox = 0`, release wasm v `bots/_m2`: byte-identical (checked after the last edit).

### Local results v `_m2` (the base sets priority with the old rule)

Full judges, 128 maps x 2 sides:

| Setting | Seed | Wins | Deaths us v them | Fuel cuts a game | Note |
| --- | --- | --- | --- | --- | --- |
| priox=19 | 0 | 51.2 % (256) | 6.6 v 6.2 | 34.9 | |
| priox=19 | 1 | 53.5 % (256) | 6.3 v 6.5 | 64.5 | |
| priox=23 | 0 | **57.0 %** (256) | 6.4 v 6.5 | 36.2 | 1 bot fault in 256 games, not traced |
| priox=23 | 1 | not finished | | | stopped at the wrap-up |
| priox=55 | 0 | 51.2 % (256) | 6.4 v 6.2 | 40.6 | |
| priox=87 | 0 | 54.7 % (256) | 6.2 v 6.1 | 88.8 | |
| priox=87 | 1 | not started | | | |

Fuel cuts swing between seeds with no code change (19: 34.9 v 64.5), so 88.8 for 87 is not proof of a cost, but bit 64
does add one buff read per visible enemy a turn: check it before use. The base's own fuel cuts on seed 1 were not measured.

KPIs from decoded games (16 maps x 2 sides = 32 games each; `lkpi.py`). "Base" = `_m2` in the same games.

| Setting | Wins /32 | Doubles a game | Double strikes | Hit share: 2nd / 1st / other fight turns | Kills a game (on a 2nd turn) | Deaths a game | Champion stuns | Damage on the stunned by next round |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base (mean) | | 4.6 | 0.2 | 0.31 / 0.19 / 0.33 | 4.8 (0.0) | 7.7 | 8.5 | 92 |
| 19 | 16 | 98.1 | 17.0 | 0.47 / 0.41 / 0.29 | 5.2 (1.34) | 6.8 | 8.5 | 84 |
| 23 | 20 | 90.1 | 16.4 | 0.52 / 0.42 / 0.29 | 5.4 (1.62) | 7.3 | 8.5 | 94 |
| 55 | 16 | 87.9 | 16.3 | 0.51 / 0.41 / 0.29 | 5.1 (1.16) | 7.4 | 8.2 | 82 |
| 119 | 14 | 83.3 | 16.8 | 0.52 / 0.45 / 0.30 | 4.7 (0.91) | 9.1 | 9.1 | 93 |
| 247 | 15 | 87.4 | 13.7 | 0.47 / 0.38 / 0.30 | 4.1 (0.78) | 8.7 | 7.8 | 121 |
| 127 | 14 | 84.1 | 16.7 | 0.51 / 0.44 / 0.30 | 4.8 (0.91) | 9.1 | 9.1 | 95 |

Our deaths on an enemy's second turn are 0-1 % (the base does not flip, so this says nothing about the band).
Targets met: doubles >= 20 and double strikes >= 3 a game.

### Two probe results

- **A stun costs exactly the victim's next turn** [measured, 16 local games, 179 stuns on champions]: cast before the
  victim's turn in the round, it acted later that round 12 % of the time and the next round 98 %; cast after its turn,
  it acted the next round 21 % and the round after 88 %. So "stun before the victim acts" gives no extra turn, and
  there is no better slot for Cassi's cast: the boundary slot only helps because the strikers' two turns then fall on
  a body that cannot move. **Never stun a body that already has stun time left** (it deletes the same turn).
- **A visible enemy's priority and cooldowns are readable** [sdk]: `champion::priority()` (next round) and
  `prev_priority()` (this round) go through `sdk_bc_champion_priority` for any visible champion; ability `cooldown()`
  is already read for enemies in `reach_of`. Not used yet: we could see which enemy bodies flip and who acts first.

### What did not work / does not transfer

- Bits 32 and 64 show no gain locally (55: 51.2 %; 87: 54.7 % v 23's 57.0 %, one seed each). Our stun conversion did not
  move (damage on the stunned body 82-95 v the band's 274). The mirror opponent stuns like us, so the band may differ.
- Bit 128 lowers strikes and kills in 32 games; no full judge. Bit 8 does nothing measurable.
- The local opponent never flips, so the cost of the flip against a flipper (policy wonk) can only show on the band.

### Left to do

1. Seed 1 of `priox=23` and `priox=87`; trace the one bot fault of 23 (run 23 with `--keep` and read the faulting game).
2. Fuel: `_m2` with `seed=1` as the reference for the 64.5 / 88.8 readings.
3. Bit 64: skip a stun cast on a body with stun time left (the probe above); measure the commit count from the debug line
   (`priox_dbg=1` prints 12 counters at r600 / r1000).
4. The small-bag tribute on the boundary turn (FINDINGS §11 row 6) is not built.

Scripts: `~/tzunami_data/analysis_10nov/prio/lkpi.py JUDGEDIR` (decodes a kept judge dir, prints the KPIs above).
Scratch variants are deleted (also the earlier agent's `bots/_prio1`).

### Band lines (best first)

```
priox 23: parity flip + low-HP first + striker slot + second-turn strike|_prio|priox=23|all
priox 19: parity flip double turn + low-HP first + striker slot|_prio|priox=19|all
priox 87: 23 + stunned body first and commit|_prio|priox=87|all
```

## Part 3 (10 Nov day)

### The bot fault of `priox=23` (seed 0): a heap corruption in the BASE code, not in the priox paths

**Short answer.** The one fault in 256 games (seed 0) is game `00elkring`, side b, Heart of Ruin (slot 2), round 611:
a wasm trap `uninitialized element` in `seen_camps()` called from `awake_snap()` [measured: re-run alone, same trap at
the same place, debug and release]. The cause is 73 rounds earlier and sits in `_m2`'s own code:

1. Round 538: Heart of Ruin's turn runs out of fuel (`fuelExhausted` r538) and is suspended; the body dies the same
   round (`death` r538) [measured, game summary]. A suspended turn resumes in the next round where it stopped [rules,
   GameRules "Fuel"], so the rest of the old turn runs with the body dead.
2. The resumed code does `me.pos = h.position()` (a dead champion reports (-1,-1)) and `W.refresh_occ(me.pos)` ->
   `World::clear_occ((-1,-1))`: tile index -31, byte `occ_lin[-4]`, bit 1 [measured: debug-only trace printed
   `OOBCLR r538 p(-1,-1) i-31 byte-4`]. That byte is the low byte of the malloc chunk header of `occ_lin` itself, and
   bit 1 is its in-use flag [sdk/libc layout; consistent with what follows].
3. The allocator then treats `occ_lin`'s live block as free. At round 610 `vision::camps()` got a buffer that overlaps
   it (camps at 0x1aac0, `occ_lin` at 0x1aad0) [measured], so at round 611 `export_linear_buffer(occ_lin)` wrote the
   occupancy bits over the camps' vtable pointers [measured: the check after `export_linear_buffer` is the first that
   fails], and `camps_cache.clear()` called a destructor through a zeroed vtable -> trap. After the trap the body's bot
   restarts (state lost, plus a fuel cut on the restart turn).

So any build can hit it, `_m2` included: it needs a fuel cut and a death in the same round, then a heap reuse
pattern that turns the bad flag into an overlap. Seed 1 of `priox=23` also had 1 fault in 256 games (not traced; the
same mechanism is the likely one [guess]). In the 256 games of `priox=279` below, neither side faulted. Even when it
does not trap, the corruption can silently overwrite live data, so it may cost play before any fault shows [guess].

**The fix (a pure guard):** `World::clear_occ` returns for an off-map tile. For every on-map tile the code does exactly
what it did; it only removes an out-of-bounds write (undefined behaviour). It changes the wasm, so fuel per call moves
by a few instructions and games are not byte-identical with the old build, but no decision changes. Built in
`bots/_prio` as **`priox` bit 256** (`src/world.h`, which now includes `value.h`; `src/value.h` comment):

```cpp
void clear_occ(vec2 p) {
    if constexpr ((value::Params::priox & 256) != 0) if (!in_map(p)) return;
    const int i = p.y * w + p.x; occ_lin[i >> 3] &= std::uint8_t(~(1u << (i & 7)));
}
```

cmp [measured]: `priox=0` release wasm v `bots/_m2`: byte-identical. `priox=23` release wasm v the build of `priox=23`
from before the change: byte-identical (the band build is untouched). **Recommendation:** put the one-line guard in
the final bot unconditionally (`if (!in_map(p)) return;` in `World::clear_occ`), whatever else is merged; it is a fix
for the base, not a priox feature. The same guard belongs in every copy that keeps `World::clear_occ` (`_a1`, `_surv`,
`_m2`).

### Seeds of `priox=23` and the fixed build, v `_m2` (128 maps x 2 sides each)

| Setting | Seed | Wins | Deaths us v them | Fuel cuts a game (judge fuelEx): us / the base in the same games | Bot faults (ours / theirs) |
| --- | --- | --- | --- | --- | --- |
| priox=23 | 0 | 57.0 % (51-63) | 6.4 v 6.5 | 36.2 / not kept | 1 / not counted |
| priox=23 | 1 | **52.3 %** (46-58) | 6.6 v 6.4 | 40.9 / not kept | 1 / not counted |
| priox=279 (23 + the guard) | 0 | 55.9 % (50-62) | 6.4 v 6.5 | 38.3 / 37.5 | 0 / 0 |

- Two seeds of `priox=23`: 54.7 % mean (57.0 / 52.3). Seed 0 was re-run with `--keep` and gave the same 57.0 % and the
  same fault (the judge is deterministic).
- Fuel: in the same 256 games the fixed build cuts 38.3 turns a game and the base 37.5: the double turn does not add
  fuel cuts [measured]. (fuelEx counts the round-1 cuts too; without round 1: 34.2 v 33.4.)
- 279 differs from 23 only by the guard, so 55.9 v 57.0 % is the trajectory noise a few instructions of fuel make.

### Band lines

```
priox 279: parity flip + strike on 2nd turn + clear_occ fault guard|_prio|priox=279|all
priox 23: parity flip + low-HP first + striker slot + second-turn strike|_prio|priox=23|all
```

Scripts: `~/tzunami_data/analysis_10nov/finish/faults.py JUDGEDIR` (faults and fuel cuts per side in a kept judge dir).
