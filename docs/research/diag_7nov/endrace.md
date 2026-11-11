# How tz-38's band games end, banking and the end race (7 Nov, night)

Data: decoded replays + platform summaries of `tz38_big` (150 games of tz-38 v the six UK band teams); the same
analyses on `big32`, `tz39_big`, `tz40_big` (450 more, other builds, same groups) as a robustness check. The numbers
are for tz38_big unless marked "600" (all four). Scripts: `scratchpad/diag/endrace/` (`cache.py` builds per-game
pickles in 40 s; `ends.py`, `banking.py`, `tributes.py`, `endrace.py`, `race.py`, `channels.py`, `locks.py`,
`lag.py`, `close.py`, `their_close.py`, `timeline.py LABEL MATCH_SUFFIX`). Outputs `*.txt` beside them.

Method notes [measured unless tagged]:
- Step kinds come from the visualiser's own name table (`PanelChrome-*.js`, `vr`): 9 = set priority, **20 = place
  altar lock**, 21 = teleport channel, 23 = movement blocked, 12 = tribute start ("Submit gems"), 16 = cancel
  channel. Worth adding to `tools/replay/README.md`.
- Tribute completions come from the summaries' `gemSubmission` events (round, bag, altar tile); a start with no
  completion within ceil(bag/10)+3 rounds is "failed", by cause in this order: death, an enemy lock (step 20) on that
  altar, a stun buff, the body's own cancel (step 16), unknown.
- Lock hits = basic attacks (step 5) aimed at an altar tile.
- **The killer takes the victim's whole bag** [measured: 15 of 15 checked kills, e.g. our Vesper killed a Prism and
  went 24 -> 178 gems].
- Some band games are exact repeats (same map, side, opponent: deterministic bots), e.g. 00stampede and 04lines appear
  twice; they are counted twice.

## (1) How the games end

| | tz-38 (150) | all four builds (600) |
| --- | --- | --- |
| Results | 25 W / 125 L; 144 end at 1,000 gems, 6 at r2000 (tiebreak) | 87 W / 513 L |
| Our final score in losses, p10/25/50/75/90 | 0 / 119 / **326** / 616 / 739 | similar |
| Margin in losses (theirs minus ours) | 259 / 416 / **694** / 927 / 1035 | median 651-694 |
| Losses within 100 / 200 / 300 gems | 5 / 11 / 16 | 20 / 44 / 80 |
| End round of losses | p10 544, median 876, p90 1462 | similar |

**When the loss is decided.** A logistic P(win) per 100-round bin (banked difference, carried difference, both
totals; fitted in-sample on the 600 games) gives, for losses, the last round with P(win) >= 0.10: median **r463**,
**400 rounds before the end** (p25 253, p75 550). 46 of 125 losses are below 10 % for good by r300 and 69 by r500
(600 games: 32 % and 54 %). Only **19 of 125** are still above 10 % 150 rounds from the end, and 8 have P(win) >= 0.25
at some point in the last 200 rounds. 65 of 125 losses never lead in banked score after r100.

So **most losses are blowouts settled by economy and fights**, not by the end race. The end race matters in a minority
of games, but in that minority we do badly:

**Close races** (600 games; both sides banked >= 800 within 150 of each other at some round): 66 games, we won 19.
**When we led at that moment we won 14 of 32 (44 %); when they led they won 29 of 34 (85 %).** With both >= 600 and a
gap <= 150: 136 games, we won 31; when ahead 19 of 56.

**Losses we held the gems to win** (gems carried but never banked):
- tz-38: 3 losses where banked + carried >= 1,000 before they finished; 600 games: 23.
- After reaching 900 banked, we fail to reach 1,000 in 5 of 22 games (600: 16 of 49); they fail in 3 of 99 (9 of 302).
  In 13 of the 21 games we didn't finish, the gems we carried at the end exceeded the shortfall.

Examples (tz38_big; `timeline.py tz38_big <suffix>`):
- `c6fe-786d…` 04gem_caverns v Rogue Lock Pickers, **910-1005**: from r730 we sat at 910 for 180 rounds. Cassi (80
  gems) and Issac (91: 910 + 91 wins) went back and forth 7-16 tiles from the single altar for 130 rounds (Issac at 532
  of 1,140 HP; enemies 3-9 tiles away) and never tributed. Meanwhile their **700-max-HP Prism tributed 357 gems in a
  36-round channel** (r782-818) at that altar, with our twins 7-10 tiles away. Killing it would have taken the 357 gems
  and the game. After that they banked 7-8-gem bags every few rounds to 1,005.
- `ab7a-726d…` 00collision v policy wonk, **976-1008**: we stood at 976 from r1144 (24 short; Cassi held 12). Their
  Vendetta channelled 92 gems for 10 rounds at the single altar with our four bodies 16-20 tiles away; then HoR and
  Marcella finished.
- `b919-7cab…` 04gap v Rogue Lock Pickers, **900-1007**: at 900 from r1220 with 163 carried (Vesper 41, Vendetta 45,
  Marcella 41) on a big two-altar map; Vesper took 140 rounds to walk 45 tiles to the altar. Their Vesper banked 200
  in a 20-round channel at r1269.
- `c254-7f61…` 00swirl, 991-1010; `f1ce-78db…` 04barbell, 784-1016 with 242 carried (their lock on the only altar,
  our Marcella and Vesper hit it for 20 rounds before tributing).

## (2) Banking, ours v theirs

| Per game (tz-38, 150) | Us | Them |
| --- | --- | --- |
| Tributes completed (started) | 13.2 (13.7) | 22.1 (22.6) |
| Gems tributed | 475 | 948 |
| Bag at tribute p10/25/50/75/90 | 7 / 12 / **23** / 44 / 80 | 11 / 17 / **30** / 50 / 78 |
| Bag in the last 150 rounds, median | 26 | 35 |
| Rounds between a body's tributes, median | 98 | 83 |
| Last gem gain to tribute start, median (p75) | **20 (45)** | **11 (26)** |
| Distance to the altar at that gain, median | 11 | 9 |
| **Excess rounds** (that lag minus the Chebyshev walk), median / mean | **6 / 22.7** | **0 / 9.0** |
| Same altar as the nearest one at the gain | 81 % | 81 % |
| Carried per alive body-round | 9.7 | 20.8 |
| Gems lost at death (median game) | 59.7 (20) | 48.7 (4) |
| Tributes failed: enemy lock / stun / death / own cancel | **0.18** / 0.17 / 0.03 / 0 | 0 / 0.13 / 0.05 / 0.11 |
| Bags lost to those failures | lock: median 99, mean ~170 (31 gems/game); stun: median 94 (21/game) | stun 18/game |
| **Altar locks bought / placed** | **0 / 0** | **5.0 / 2.1** |
| Hits on altar locks | 5.5 | 0 (we never place one) |

The same holds on the 450 other games (our excess mean 21.0 v 9.2; locks 0 v 2.1-2.3; lock cancels 0.15-0.21 a game).

- **Excess walk by body** (our median / mean): Cassi 25 / 45, Issac 11 / 39, HoR 11 / 32, Vendetta 8 / 24, Marcella
  8 / 20, Vesper 3 / 15. Theirs are 0-2 / 6-15 except Willow. So about 13 tributes x ~14 extra rounds = ~180
  body-rounds a game carrying a bag that's on its way to the altar but not there yet. [measured; the cause (BANK/FARM
  flips, BREAK and flee, pack following) is a guess: the replays don't show the goal]
- **We never hold an altar lock: a code bug.** `shop()` (bot.cpp ~2020) buys the lock only after the shard loop, which
  spends gold until `gold < 30` (~1971); the lock then needs `gold_count() >= 40`. 0 buys in 600 games [measured +
  code].
- **Their locks** (600 games, 2.16 a game): **1.48 are placed just before their own tribute at that altar** (within
  2 rounds; those bags median 44-46 v 29 for unlocked tributes), 0.16 cancel one of our channels (that bag median
  **158**), 0.52 are pure denial (0.30 on an altar we had used in the previous 200 rounds). 70 % land on altars on our
  half of the map. Placed from r183 (p10) to r1085 (p90), median r530.

## (3) The end race

**What they do as they close** (from their first banked >= 900; 600 games):
- 900 -> 1,000 in a median of **43-46 rounds** (ours: 62).
- 5.8-6.4 tributes per 100 rounds (ours 4.0), bags median 23-24 (ours 21-25): the same bag size, more often.
- **27-31 % of their alive body-rounds are within 3 tiles of an altar** (19 % mid-game; ours 16-18 %).
- In the last 30 rounds 2.3 distinct bodies tribute (ours 0.3 when losing, 1.9 when winning).
- From their 850 to the end (median 71 rounds), 15 % of their body-rounds stand empty-handed within 3 of an altar
  (guards). They lock little in this phase (0.19 a game, mostly before their own tribute).

**The tribute that crosses 1,000** (393 of their wins, 600 games): bag median 73 (p75 200, p90 385). A channel of
8+ rounds in 193; 153 bags >= 100. One of our bodies came within 6 tiles during it in 136 and within 2 in 18.
The Prism hoard: an enemy Prism is in 148 of 600 games (mostly :3 and Kungarna). Its peak bag has a median of 292,
it channels **298 gems over 30 turns** (median of its 176 channels of 100+ gems), and it has 0.74 escorts within 4.
One of our bodies came within 8 during 108 of those channels, within 4 during 44 and within 2 during 26, and we
stopped 31 (14 of them because the Prism cancelled itself). 03homonoliths is a one-bag map: a 600-gem bag and a
60-round channel. In two of our losses there our body was 1-2 tiles from that channel.

**What we do as they close** (their 850 to the end, 422 losses): our median banked then is 332, so most are lost
already. We tribute 1.5 times per 100 rounds, our bodies are within 4 of the altars they use 7 % of the time, 17 % of
our body-time is dead, and we stopped 9 of their channels in 422 games.

**Channels as targets** (channels of 40+ gems, 150 games):

| | Their channels | Our channels |
| --- | --- | --- |
| Per game | 8.6 (bag median 58, 6 turns) | 4.1 (bag median 68, 7 turns) |
| With an opposing body within 6 during it | 32 % (2.7 a game) | 33 % |
| ... of which the channeler was hit | **11 %** (0.3 hits) | **33 %** (1.6 hits) |
| ... denied (lock / stun / death / cancel) | 9 % | 24 % |
| Gems banked with an opposing body within 6 | **34,235 = 228 a game** | 97 a game |

[rules] A channel blocks the channeler's other actions until it ends or is cancelled. Damage does not interrupt a
tribute; stun, death or a new lock does. A kill takes the whole bag [measured]. **A tributing enemy is a defenceless
target carrying its bag, and we ignore it.**

## (4) Proposed rules (in priority order; none tested)

**R1. Buy the altar lock (bug).** In `shop()` (bot.cpp 2020-2026), move the lock purchase **before** the shard loop:
`count()==0 && gold >= 10 && round >= 30` (a lock costs 10 [rules]; the band buys 5 a game). Expect about 2
placements a game once R2/R3 exist. Today `try_lock()` and the call at 2824-2828 never fire.

**R2. Lock an altar the enemy has locked too, if the engine allows it.** `try_lock()` (2044-2046, 2055-2057) skips any
altar where `has_altar_lock(a)` is true, and that is true for either team's lock. The band locks its own altar before
1.48 tributes a game, so our lock would never cancel those channels. The SDK keeps lock occupancy per team
(`altar_lock_tiles(team)`), and `altar_lock_at` says "prefer the allied lock if both teams have a lock on this altar"
[sdk], so two locks may coexist [guess]. The error `altar_lock_already_locked` may be per team or per altar
[unknown]. **Probe it on one map first**: an idle-style scratch bot that locks and tributes, against a tz copy that
tries to lock. If locks can coexist, skip only when **our** lock is there (`altar_lock_tiles(team::ally)`). If only one
lock fits, their self-lock is a shield: copy it (R6), and against it only stuns and kills are left.

**R3. Deny channels (the biggest measured gap).** In `play_turn`, after the lock block (2824-2828) and before the fed
break (2926), look for a visible enemy `e` with `e.h.is_submitting_gems()`, `e.gems >= 40` (>= 20 when
`their_score >= 800`), off its spawn, at altar `a`, with turns left estimated as `ceil(e.gems / 10)` (the start bag is
unknown; this is the ceiling):
- With a lock, `cheb(me, a) <= 8` and the walk `cheb - 2` shorter than the turns left: move toward `a` and lock it at
  range 2. This ignores the fed break against the channeler itself, which can't act [rules], but keeps it for escorts
  (`fed_k` against bodies within 4 of `a` other than `e`). Data: within 4 during 216 of 836 channels of 100+ gems
  (600 games), within 8 during 511.
- Without a lock: COMMIT on `e` when our bodies within 6 can deal its HP before the channel ends and at most one escort
  is within 4. Price its kill at `value::kill(r) + e.gems * value::carried(...)`: the bag changes hands [measured].
  Stunners first: a stun cancels the channel [rules], so HoR's dash stun and Marcella's enhanced attack.
  Where: `assess()` target scoring (260-330) and `execute_target()` (397); a `chan_target` in the stance block next
  to `hunting` (2971).
- Target KPI: the gems they bank with our body within 6 (228 a game) and our hit share on their channels (11 %, theirs
  on ours 33 %).

**R4. Close the race ourselves.** In `bank_rate()` (680-718), using `our_score` / `their_score` (2739):
- `our_score >= 850`: +20 for any bag >= 10 with an altar within 12 (their stretch bags have a median of 23, at 5.8-6.4
  tributes per 100 rounds).
- `our_score >= 900`: +20 for any bag with an altar within 20.
- A bag that wins (`our_score + me.gems >= 1000`, +1000 at 699, already there) or a **close race** (both >= 700 and
  `|our - their| <= 150`): set a `win_bank` flag that the fed break (2962) and the BREAK branch (3077) respect when
  `cheb(altar) <= 10` and `hp >= 0.4 max_hp`. Damage doesn't interrupt the channel [rules]; only stun, death and locks
  do. With R6 it also gets a lock.
- `act_bank()` (2388) keeps its altar choice, but on `win_bank` it takes the altar with the fewest seen enemies within
  4 when the walk is no more than 6 tiles longer.

Data: 900 -> 1,000 takes us 62 rounds v their 43-46, and we fail to close 23-33 % of the time (they 3 %), in most of
those failures holding enough gems. We win 44 % of the close races we lead, they win 85 %. If we converted them at
their rate it would be about +13 wins in 600 games (~+2 pp) [guess].

**R5. Deny their finish when we can't win first.** If `their_score >= 850` and we are in a close race (our >= 700,
or their lead <= 200), the bodies without a winning bag hold the altar nearest their carriers. That altar is the one
they last tributed at (remember it in `World`, from seeing `is_submitting_gems()` or from the score jumping), or else
the one nearest the enemy spawn among those on our half. Stand within 2 with a lock (R1), lock on the first channel
seen (`try_lock`'s `race` branch at 2037, with `lock_race 850`), and keep bodies 3-4 tiles off (they keep 15 % of
their body-rounds there as guards). Gate it on a close race: in most games that reach their 850 we are at ~330 and the
bodies are better spent farming.

**R6. Shield our big tributes (needs R1; copy of the band's habit).** In `act_bank()` before `submit_gems` (2399): if
`me.gems >= 40`, we hold a lock and the altar has no lock of ours, place ours first, as the band does before 1.48
tributes a game (bag median 44-46). Their locks cancel 0.15-0.21 of our channels a game (bags median 99-158) and stuns
0.17. If R2's probe shows one lock per altar, this blocks their cancel-lock and also their tributes there [guess on
the mechanics].

**R7. Commit to a bank trip.** Once BANK is chosen with `gems >= 20` and an altar within 15, keep it until the
tribute (a stronger hysteresis than 1.2456 for BANK in `choose()`'s `offer`, 931-939). Exceptions: a BREAK or a
winning farm step on the way. This cuts the excess walk (ours median 6 / mean 22.7 v 0 / 9.0) and the bag exposure
(we lose 60-90 gems a game at deaths v their 48). Cassi and Issac first (excess means 45 / 39).

What not to expect: the end race is a minority lever. 54 % of losses are below 10 % P(win) for good by r500, and the
median loss is by 694. R3 is the only rule here that also works mid-game (the Prism hoards, 228 gems a game banked
next to us). R1 is a plain bug and the cheapest test. Judge R1+R3 together, since a lock in the bag is useless
without a rule to use it, on the 150-game band stage against tz38_big, paired.
