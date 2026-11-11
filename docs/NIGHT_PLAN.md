# NIGHT PLAN (written 10 Nov ~01:00, extended ~02:15): from half-built levers to one locked bot

**For whoever picks this up:** this file and `docs/research/diag_10nov/FINDINGS.md` are self-contained. The game is
Cambridge Battlecode 2026 (rules: `GameRules.md`; C++ API: `sdk/cpp/cambc.h`). Our bot is C++ in `bots/`; `CLAUDE.md`
lists every tool. The work is: finish each lever below in its own copy of the base, prove it on the platform against
the six UK band teams ("the band"), merge the winners, and put the result live before the lock.

**Lock: Tuesday 10 Nov 23:59.** The qualifier (11 Nov) is a tournament among UK teams on unseen maps. The evidence
behind every item here is in `docs/research/diag_10nov/FINDINGS.md`; read that first, then this, then
`docs/research/diag_10nov/AGENT_RULES.md` (the rules every builder follows).

## 1. Where things stand

- **Live:** v280 (tz-mega). `tools/restore93.sh` restores it (LIVE_VER 280). v281 = tz-mega2 = the build of `bots/_m2`.
- **Base for all new work: `bots/_m2`** (never edit it). Its band records, all v the six band teams:
  - `tz174_big`: the general set (the n47 games, 150, 33 wins);
  - `a1_m2`: one-altar maps only (120 games, seed 71, 29 wins);
  - `tiny_m2`: tiny maps with 2+ altars (120 games, seed 73, 18 wins).
  Decoded replays of all three sets are in `~/tzunami_data/replays/` (`a1_m2`, `tiny_m2`; n47 as `n47_tz116` / `tzmega_big`).
- **Eight builders stopped mid-work at the usage limit (9 Nov ~23:20).** Their code and notes are on disk. Nothing has
  been sent to the band yet. Each build sits behind a `static constexpr` switch whose comment in `value.h` lists its bits.

| Lever | Copy | Switch | Lines changed v `_m2` | State when it stopped | Local result so far (v `_m2`) |
|---|---|---|---|---|---|
| Prism draft on one-altar maps | `bots/_draft` | `draftx` | draft.cpp 32 + bot.cpp | **READY for the band (10 Nov ~04:00, `draft.md`)**: cmp identical at 0; no Prism fuel fault (see L15) | `draftx=1` 48.3 % of 118 non-frozen games (2 seeds), share 0.50, fuel at base level |
| Double turn (priority flip) | `bots/_prio` | `priox` | bot.cpp 48 | decode done (`prio.md`); the agent was in the middle of the code edits | none; `scratchpad/prio/` has m2.wasm and prio0.wasm for the cmp |
| One-altar locks | `bots/_a1` | `alt1x` | bot.cpp 123, world.cpp 8 | built; variants `_a1_7`, `_a1_7b`, `_a1_15`, `_a1_111` judged | 7: 43.8 %; **7b: 53.1 / 50.0 %**; 15: 42.2 %; 111: 32.8 % (64 games each) |
| Tiny-map contact | `bots/_tiny` | `tinyx` | bot.cpp 166 | built; variants `_tiny_1`, `_tiny_5`, `_tiny_7`, `_tiny_b` were being judged (`scratchpad/tiny/*.log`) | unread |
| Posture at 4-12 tiles | `bots/_post` | `postx` | bot.cpp 144 | built; a first judge was running | none |
| Kit use | `bots/_kit` | `kitx` | bot.cpp 109 | built; a first judge was running | none |
| Class profiles | `bots/_cls` | `clsx` | bot.cpp 56, value.h 42, `cls.h` new | classifier + six rows written; edits unfinished | none |
| Opening | `bots/_open` | `openx` | 0 | analysis only (`~/tzunami_data/analysis_10nov/open/`) | - |

**Added during the night of 10 Nov (after the table above was first written):**

| Lever | Copy | Switch | State | Report |
|---|---|---|---|---|
| Spawn fortress + twin link (L10, L11) | `bots/_surv` | `fortx`, `twinx` | **`fortx=3 twinx=11`: 59 / 57 % v `_m2` on the tiny maps (2 seeds x 100 games), deaths 7.2 v 8.4**; `twinx=11` alone 55 / 54 / 52 %; `fortx=3` alone 51 / 51 %; cmp identical at 0; no decoded KPIs, no 256-game run, burst guard not built | `diag_10nov/surv.md` |
| Cluster timetable + Marcella banker (L14, L13) | `bots/_econ` | `clusx`, `marcx` | `clusx` built, 37.9 % v `_m2` (lost); `marcx` built, compiles, never run; a respawn-deadlock fix inside `clusx` bit 1 | `diag_10nov/econ.md` |
| Double turn (L2) | `bots/_prio` | `priox` | **`priox=23`: 57.0 % v `_m2` (256 games, seed 0; seed 1 unfinished; 1 bot fault to trace)**; `priox=19` 51.2 / 53.5 %; `priox=87` 54.7 %; cmp identical at 0; 80-98 doubles a game (base 4-6), 19-30 % of our kills on a double's second turn | `diag_10nov/prio.md` Part 2 |
| Prism draft (L1) | `bots/_draft` | `draftx` | ready: `draftx=1` | `diag_10nov/draft.md` |
| Engine probes | none (probe sources in `~/tzunami_data/analysis_10nov/mech/`) | - | done | `diag_10nov/mech.md`, FINDINGS §13 |

**No build of this session has been uploaded or played on the band** (the user's decision on 10 Nov: this session
documents; the next one builds and tests). Every band command below is for the next session, after agreeing the live
version with the teammate (see Hazards).

The scratchpad of the old session (judge outputs, logs) is
`<scratchpad>/NAME/`.
A variant's settings: `diff bots/_NAME/src/value.h bots/_NAME_x/src/value.h`.

## 2. How to work through the night

1. **You (the orchestrator) run the band and merge. Builders finish one lever each.** Keep at most 3 builders running
   at once (usage and the laptop: `tools/jslot.sh` gives 3 local-judge slots). Give each builder `AGENT_RULES.md`, its
   section below, its copy, and the instruction to hand back a band line fast.
2. **Every lever follows the same five steps:**
   1. it compiles; with the switch at 0 the release wasm is byte-identical to `_m2`'s (`cmp`);
   2. the behaviour fires (a debug counter or decoded local games) and its KPI moves;
   3. a crash and fuel screen: one local judge v `_m2` on the lever's maps (`--only` class file) or all 256; fuel cuts
      and deaths must not rise. The local win rate is a filter for breakage only (>= 45 %), not a gate;
   4. **the band decides:** a stage paired with the right base (below); judge gem share, then wins;
   5. a winner is confirmed on a FRESH set of the same class where both builds play, before it joins the stack.
3. **The band stage:** append a line to a queue file and run the queue runner once in the background:
   ```
   echo 'N|note|_DIR|BASE|k=v k=v' >> ~/tzunami_data/scrims/queue_10nov.txt
   zsh tools/bandq3.sh ~/tzunami_data/scrims/queue_10nov.txt >> ~/tzunami_data/scrims/runner_10nov.log 2>&1   # background
   ```
   - N starts at **175**. BASE = `a1_m2` for one-altar levers, `tiny_m2` for tiny-map levers, `tz174_big` for the rest.
   - A stage uploads the variant, plays base groups 0-1 (60 games), continues to the rest only if the paired share
     is > 0, restores v280, and writes `~/tzunami_data/scrims/res_tzN.txt`. About 15-25 minutes each; quota is 100
     groups an hour.
   - Paired numbers: `python3 -I tools/scrim.py metrics BASE tzN_big | tail -13`. On the class sets 120 games give a
     95 % interval of about +-0.05 share; on stage 1 alone about +-0.07. Stage-1 numbers run hot: never adopt on 60 games.
   - To pause for the teammate: put `!until [[ -f ~/tzunami_data/scrims/RESUME ]]; do sleep 30; done` at the queue head.
   - Stop the runner at the end: `touch ~/tzunami_data/scrims/queue_10nov.txt.stop`.
4. **Confirmation on a fresh class set** (both builds play; v281 is `_m2`'s build, CANDVER is the candidate's upload):
   ```
   # general maps:
   zsh ~/tzunami_data/scrims/fresh2.sh SEED 4 281 fS_m2 CANDVER fS_tzN
   # a map class: play the base first with the class file, then pair the candidate with it
   LIVE_VER=281 zsh tools/restore93.sh
   python3 -I tools/scrim.py run a1b_m2 --seed 79 --groups 4 --only-maps ~/tzunami_data/scrims/cls_alt1.txt
   .venv/bin/cambc submissions activate CANDVER && python3 -I tools/scrim.py run a1b_tzN --pair-with a1b_m2
   zsh tools/restore93.sh; python3 -I tools/scrim.py metrics a1b_m2 a1b_tzN | tail -13
   ```
   Unused seeds: 79, 83, 89, 97, 101. Tiny class file: `cls_tiny_multi.txt`. A class base can be reused for several
   candidates of that class, but not for the one that was selected on it.
5. **Adopt rule:** paired share > +0.02 over the full stage AND share >= 0 on the fresh set with wins not down. For a
   class lever, read the class set; for a general lever, also check it does not lose on `a1_m2` / `tiny_m2` if it could
   act there.
6. **Log every stage** in `docs/BUILD_LOG.md` (one line: N, what, base, n, wins, share diff with interval, verdict).

## 3. The levers, in the order to run them (expected value x readiness)

### Where each lever stood at the end of the research session (10 Nov ~06:30)
| Ready for a band stage | Built, needs local work first | Built, lost or unproven | Idea only |
|---|---|---|---|
| L1 `draftx=1` (Prism); L2 `priox=23` / `19` (double turn); L3 `alt1x=7` + `a1x_buy=1` (locks; check the ally-channel bug first) | L11 + L10 `fortx=3 twinx=11` (59 / 57 % on tiny maps; add the burst guard, run 256 games); L13 `marcx` (never run); L4 `tinyx`, L5 `postx`, L6 `kitx` (first judges unread or unfinished) | L14 `clusx` (37.9 %); L9 `clsx` rows (hypotheses) | L12 die fighting / finisher / bag denial; L15 crowd fuel and the two freezes; L7 opening; L3b locks everywhere; the boundary tribute |

### Order of work (if short of time, stop at the line)
1. L1 Prism draft, L3 locks (both nearly ready; one-altar maps = 25 % of the pool).
2. L2 the double turn with the stun bits, L6 kit with focus-the-stunned (fights: the largest gap).
3. L13 Marcella as taker and banker (income and size; built, never run).
4. L4 tiny-map contact, L10 the spawn fortress, L11 the twin link (tiny and close maps = 39 % of the pool, deaths 10 a game).
5. -------- the line: everything below is second wave --------
6. L15 fuel in crowds and the stand-off breaker (a robustness fault: do it before the lock whatever else happens).
7. L14 the cluster timetable (lost locally: Vendetta runner and islands only), L12 die fighting + support lines, L5 posture, L7 opening, L8 tribute hygiene, L3b locks on every map, L9 class rows.

### L1. Prism for Vendetta on one-altar maps (`bots/_draft`, `draftx 1`)  [ready after one fix]
- Evidence: +12 +- 3 win points on one-altar maps across 15 of 16 ladder teams, team strength held fixed; nothing on
  2+-altar maps. One-altar maps are 25 % of the pool and our second-worst class.
- Done (`docs/research/diag_10nov/draft.md`): there is no Prism fuel fault. The high fuel numbers came from 3-5 games a
  run that froze into a stand-off until r2000 (see L15: a base fault, also with the Vendetta draft). Prism's play code
  is complete (item line Prospector / Treasure / Durability in Health, generic casts, squad with Vesper). Locally
  `draftx=1` is level with the base (48 %); the ladder's +12 can only show on the band.
- Do NOT send `draftx` bits 64 (Prism takes) or 128 (Prism as its own squad): 128 costs 11-19 points locally.
- Band: `175|draftx 1: Prism for Vendetta on 1-altar maps|_draft|a1_m2|draftx=1`. If it wins, also try the
  Vesper swap (`draftx=32`: Prism for Vesper, +17 on the ladder) and `draftx=3`.
- Prism's play to copy from the top [measured]: it works alone (solo on 42-54 % of its visits), takes gem clusters first
  (35-39 % of its 2nd-3rd visits), is the taker (64-74 % of captures); BattleCats' Prism buys Prospector, Treasure,
  Tribute (Health).

### L2. The double turn (`bots/_prio`, `priox`)  [finish the build]
- Evidence: stellar, Fish, policy wonk and NEETCoders flip the fighter's priority with the round parity; Fish lands 32 %
  of its kills on the second turn of a double; we land none and policy wonk does it to us.
- Mechanism [measured]: team A starts odd rounds, team B even rounds; `set_priority` applies next round. At the end of
  each turn, a body with an enemy within `priox_r` sets +m if we start the next round, -m if we go second. The body
  with the largest m is last in the round we go second and first in the round we start.
- Bits as designed: 1 the flip; 2 a body below 40 % HP does not flip (fixed +300: always first, to flee); 4 on the
  second turn of a double the threat test uses the enemy's two-turn reach; 8 fight opens wait for the first turn of a
  double; 16 the striker gets +40 magnitude so it holds the exact last / first slots.
- Finish: make it compile, cmp at 0, then check in decoded local games (the decoder now writes priorities) that we get
  >= 20 doubles and >= 3 double strikes a game (`~/tzunami_data/analysis_10nov/prio/order.py`, `dblk.py`). Add: on the
  SECOND turn of a double attack whenever a target is in reach (the flippers attack on 53-59 % of those turns); and
  count the mirror (the enemy's two turns against that body) in its flee test before it steps in.
- **State at the end of the session (`prio.md` Part 2):** bits 1 / 2 / 16 work; bit 4 (on the second turn of a double a
  body with a champion in reach strikes first; a ranged body holds if the enemies' two turns would kill it) is the one
  bit with a local gain: `priox=23` 57.0 % (seed 0). Bit 32 (Cassi on the boundary, stun kept off camps) moved little
  (camp-or-miss stuns 34.2 -> 31.8 a game); bit 64 (hit the stunned body first) did NOT move the damage on stunned
  bodies (93 v the base's 96, the band's 274): the follow-up needs bodies already in reach, so it is a positioning
  problem, not a targeting one; bit 128 (mirror veto) costs strikes. Left: seed 1 of 23 and 87, the bot fault of 23, a
  seed-1 fuel reference, skip stuns on already-stunned bodies, the boundary tribute (not built).
- Band lines, best first: `priox=23`, `priox=19`, `priox=87`. The local opponent never flips, so the cost against a
  flipper (policy wonk) shows only on the band.
- **Probe results to build in (FINDINGS §13):** a stun always costs exactly the victim's next turn, so never stun a
  body that is already stunned and stagger two stuns one round apart; a visible enemy's NEXT-round priority and its
  cooldowns are readable, so we can tell whether it will act before us and whether its stun is ready; a <= 10 gem
  tribute started as our last actor of a round we go second cannot be interrupted (set the carrier's priority low
  for that round, high for the next).
- One more bit to add (FINDINGS §11 row 3): **the stunner on the boundary.** Cassi takes the first slot of a round we
  start (or the last slot of a round we go second) when a stun target is in reach, so the team gets two volleys on a
  body that loses its turn. And a bank idea: a bag <= 10 gems started as our last actor of a round we go second
  completes before any enemy turn.
- Band: `176|priox 19: parity flip double turn + low-HP first + striker slot|_prio|tz174_big|priox=19`, then 23 / 27.
  Also run the winner once paired on `tiny_m2` (fights decide tiny maps).

### L3. One-altar locks as a toll gate (`bots/_a1`, `alt1x`)  [ready: pick the variant]
- Evidence: stellar and Fish keep their lock on the altar 48-58 % of rounds 100-400; the band locks 3.1 times a game
  against us and we never lock; the 9 Nov build `alt1 6` was 55.5 % on these maps locally and never reached the band.
- Use bits 1 + 2 + 4 (buy a lock from r30, lock before our own tribute, any passing lock-holder re-locks) as variant
  `7b` (53.1 / 50.0 % locally; find its knob with the diff). Leave bits 32 and 64 OFF: `111` lost badly (deaths 9.4 v 6.4).
- **Probe results (FINDINGS §13):** placing our lock CANCELS OUR OWN ALLY'S TRIBUTE at that altar: before placing, check
  no ally is channelling there (the base's own lock code too). A second lock while ours stands fails. Attack-reset
  bodies (Vesper, Vendetta, Issac) hit a lock twice a turn: send them to break enemy locks. A visible enemy's carried
  lock is readable.
- Two refinements from the replays, small: place the lock from 2 tiles away on the approach and tribute the next turn
  (stellar / Fish form), and never place while ours stands.
- Bank rule to add only as a cap: a bag above 80 goes to the altar now; with an enemy within 4 of the altar and a bag
  over 20, wait or come with an ally.
- Band: `177|alt1x 7b: own lock before tribute + keep locked (1-altar maps)|_a1|a1_m2|alt1x=7 <the 7b knob>`.
  KPIs in its games (`~/tzunami_data/analysis_10nov/a1/lockkpi.py`, `q3.py`): our locks a game >= 3, lock cover
  r100-400 >= 0.4, enemy turns spent hitting locks. Watch for 2,000-round stand-offs (seen once locally).
- L1 and L3 act on the same maps: after each passes alone, test them together on a fresh one-altar set.

### L3b. The lock toll on every map (a knob on `bots/_a1`)
- Evidence: the band's locks cost us 10.6 carrier turns a game on maps with 2+ altars too, and 98 % of the top's locks
  are at mid altars. We place none.
- Add a knob `a1x_all`: with it on, bits 1 / 2 / 4 also run on maps with 2+ altars, but only at an altar where an enemy
  has been seen within 4 (or tributing) in the last ~100 rounds. The 9 Nov `lockown` build did this without the
  "enemy seen" test and was 48 % locally, never on the band (the local opponent never banks at our altars).
- Band, after L3 passes: `|alt1x 7 a1x_all: lock shared altars on every map|_a1|tz174_big|alt1x=7 a1x_all=1`.

### L4. Tiny-map contact (`bots/_tiny`, `tinyx`)  [read the judges, then band]
- Evidence: tiny maps are 39 % of the pool, share 0.34, deaths 10.3 v kills 4.7; the top converges on a hit ally
  (arrives in 6 rounds 0.56 v 0.43), spaces Vesper (12 v 24 HP a contact round), and engages 0.69 of entries into its
  own third (we 0.40).
- Bits: 1 converge on the enemy that hit an ally when our live HP near it is >= theirs; 2 Vesper spacing; 4 home
  defence. Active while open tiles < 1,500 and round <= 200.
- Read `scratchpad/tiny/v1.log`, `v5.log`, `v7.log`, `base.log` first. Band on `tiny_m2`:
  `178|tinyx 7: converge + Vesper spacing + home defence (tiny maps, r<=200)|_tiny|tiny_m2|tinyx=7`, then 5 and 1.
  KPIs: our deaths by r150 (now ~1 a game in blowouts), blowout rate (0.59), first-fight trade.

### L5. Posture (`bots/_post`, `postx`)  [first judge, then band]
- Evidence: FINDINGS §5. The clear, untested parts are "work through" and "no sidestep"; the press is the risky part
  (every earlier "fight more" build lost on the band).
- Order: `postx=14` first (2 work through an enemy 7+ tiles away that is no size threat; 4 no sidestep; 8 stay for the
  capture), then `postx=15` (adds 1: press at a live-HP ratio >= 1.4 with an ally, from no stance or a break).
- Band: `179|postx 14: work through distant enemies, no sidestep, stay to capture|_post|tz174_big|postx=14`.
  KPIs (re-run `~/tzunami_data/analysis_10nov/disc/ext.py` + `disc.py` on its decoded band games): camp-hit share with
  an enemy at 7-12 (0.36 -> 0.5), sidestep share (0.15 -> 0.09), deaths not up.

### L6. Kit use (`bots/_kit`, `kitx`)  [first judge, then band]
- Bits: 1 walk in and cast once in reach (casts from range cost the step); 2 HoR's landing dash on camps; 4 last-leg
  dash then the hit; 8 a stunned enemy is no threat.
- Add two bits from FINDINGS §11 (the band turns a stun on us into 274 damage and a kill 17 % of the time; we turn
  ours into 128 damage and 8 %): **focus the stunned body** (any enemy with stun time left is the first target of every
  body that can reach it this turn, and a commit on it is allowed: it cannot act or flee), and **stun the channeler** (an
  enemy tributing or recalling in Cassi's reach is stunned before anything else).
- Add one more bit: **Cassi's stun is kept for champions** (not cast on camps or while travelling unless no enemy has been
  seen within 12 for ~10 rounds): ours goes on camps twice as often as the top's.
- Band: `180|kitx 15: cast in reach, HoR camp dash, last-leg dash, stunned = no threat|_kit|tz174_big|kitx=15`.
  KPIs: damage per camp hit-round, stuns landed per fight (0.17 -> 0.4), kills.

### L10. The spawn fortress (new copy `bots/_fort`, switch `fortx`)  [new, small, untested idea]
- Mechanic [sdk]: a body on its own spawn tile heals to full at every turn end and enemies cannot step there. Nobody
  uses it. We spend 130 body-rounds a game within 8 of our spawn with an enemy within 6, and 17 % of our deaths by r600
  happen there; on close-spawn maps (37 % of the pool) we die 10 times a game.
- Bits: 1 a body below `fort_hp` (0.5) with an enemy within 6 and a spawn tile within `fort_walk` (8) steps walks onto
  the nearest free spawn tile instead of recalling or fleeing elsewhere; 2 a body on a spawn tile with an enemy within 6
  stays (no goal move) and uses basic attacks and casts on anything in reach until it is full and the enemy is gone or
  weaker; 4 enemies seen within `fort_walk` of our spawn while we are outmatched locally: healthy bodies nearby fall
  back to spawn tiles and fight from them (ranged bodies first).
- **Probe result (FINDINGS §13):** the tile is not a safe zone: every attack lands and a body can be burst there in
  one round (Cassi died on it). The heal is full at the body's own turn end and enemies cannot enter. So the rule is
  for bodies whose max HP exceeds what the enemies in reach can deal in one round; Cassi and other small bodies flee
  or recall as before. Home camps can be farmed from a spawn tile at full HP.
- **State at the end of the session (`surv.md`):** bits 1 / 2 / 4 built and fire (bit 2 only twice a game locally: our
  own bot rarely dives into our home, the band does). `fortx=3` alone is level locally (51 / 51 %), `fortx=7` 50 / 45 %;
  with the twin link it adds (see L11). The burst guard above is NOT built yet: build it before any band stage.
- Check locally (decoded games): deaths within 8 of our spawn, HP lost at home before r200, body-rounds on spawn with an
  enemy near (now 1.5 %). Guard: bodies must not sit at home when no enemy is within 8.
- Band: `|fortx 3: hurt bodies near home use the spawn tile, fight from it|_fort|tiny_m2|fortx=3` and the same on
  `tz174_big`.

### L11. The twin link (`bots/_surv`, switch `twinx`; an agent started it at ~02:45 on 10 Nov)
- Evidence (FINDINGS §12.2): twin-death events are 1.93 a game on tiny maps (the top 1.20) = 40 % of our body deaths
  there; in 90 % the other twin was healthy; the top's Issac fronts and is 300 HP bigger.
- Bits: 1 shared fate (each twin acts on the LOWER of the two HP shares; the partner's state travels in free bits of
  the shared memory); 2 Cassi is never the front twin and keeps 4 tiles from the nearest enemy; 4 Issac buys Health
  first; 8 the healthy twin peels (hits / stuns the chaser of the low twin).
- **State at the end of the session (`surv.md`):** `twinx=11` (bits 1 + 2 + 8) 55 / 54 / 52 % v `_m2` on the tiny maps
  (3 seeds x 100 games); with `fortx=3`: **59 / 57 %**, deaths 7.2 v 8.4, fuel unchanged. Single twin bits lose without
  bit 1 (bit 2 alone 37 %, bit 8 alone 44 %): use the set. Bit 4 was not built: Issac's line is ALREADY all Health (his
  gap to the top's Issac is income, about 4x the shards, not the line). Cassi's step-back branch never fired: find why.
  Left: decoded KPIs (`~/tzunami_data/analysis_10nov/surv/kpi.sh`), a 256-game run, runs off the tiny maps.
- Band: on `tiny_m2` first, then `tz174_big`.

### L12. Die fighting, and supports that grow (small, in any copy; class all)
- Evidence (FINDINGS §12.1, §12.4): in 60-67 % of our deaths the body never hits a champion (the top 43 %); our
  supports hold half the top's stats: Issac never buys Strength, Cassi and HoR hold half the top's Focus.
- Rule 1 (die fighting): a body that cannot get out of every enemy's reach this turn and the next (no safe tile, no
  spawn tile, recall would be cancelled) attacks the lowest-HP enemy in reach every turn instead of stepping or idling.
- Rule 3 (the finisher): the top's Vendetta lands 2.6 killing blows a game, ours 0.5; her kills reset both her
  cooldowns [rules]. When an enemy's HP is within Vendetta's reach-and-burst (dash 2 + step + hit, hit again with the
  reset), she takes the kill before other bodies spend casts on it, then turns to the next target. Her item line buys
  the STRENGTH variant of every emblem (ours holds +31 Strength at r600, the top's +127; BattleCats' Vendetta buys
  Prospector / Treasure / Jungle all in Strength).
- Rule 4 (enemy twins): an enemy Cassi is the first target whenever she is in reach: one kill removes two bodies and
  takes two bags (Rogue Lock Pickers pick the twins in 45 % of games, Kungarna 33 %, Claudus 20 %).
- Rule 5 (bag denial, FINDINGS §13): a camp's last hit destroys the bag and pays the attacker nothing. A carrier that
  cannot escape steps next to an awake camp as its nearest body; when WE chase a low carrier near a camp, the body with
  the kill in reach hits first.
- Rule 2 (item lines, a table change): Issac's line is all Health and he holds ~10 gold, so his line is not the problem (income is); Vendetta buys Strength variants; Cassi
  and HoR put every second shard into Focus (their camp damage is Focus casts). Earlier line swaps were neutral on the
  band, so send this only as part of a stack, and watch deaths.

### L13. Marcella takes the gems and banks them (new copy `bots/_marc`, switch `marcx`)  [new; a whole-role change]
- Evidence (FINDINGS §12.5): Marcella gains 2 gold per gem she tributes and cannot be stunned. The band's Marcella
  banks 270 gems a game (540 gold), holds 44-49 % of their camp and banking gold and is their biggest body. Our
  Vesper banks 52 % of our gems with a mean bag of 39 and loses 31 a game; our Marcella banks 72.
- Bits: 1 the taker rule: at a dead group whose reward is mostly gems (gems x 2 > the gold bonus Vesper would get),
  Marcella takes when she is within reach of the tile in time; Vesper keeps gold clusters and wolves; 2 the planner
  prices gem clusters, elk and golems higher for Marcella and gold clusters higher for Vesper, so their routes
  separate (Marcella works with the supports; Vesper needs fewer helpers); 4 Marcella banks at ~25-30 gems, and a
  support carrying 10+ gems next to her at an altar banks too; 8 Marcella's line: Health and Strength first (her
  Focus shards pay least), as the band's and the top's Marcella.
- **State (`econ.md`): all four bits are written in `bots/_econ` (`marcx`), compile, cmp identical at 0, but NO game
  was played.** Next: `marcx=15` with `marc_dbg=1` v idle on ~43 maps (do the bits fire; Marcella's banked gems 125 ->
  200+, her gold 368 / 816 at r300 / r600, Vesper's mean bag 36.6 -> ~25), then bit by bit, then v `_m2` on 2 seeds.
  It differs from the old `marcella_taker` (tz-9, off since tz-20), which made her first taker of EVERY capture: this
  splits captures by reward kind.
- Find the taker logic (`i_take`, `hand_take`, `role_*`, `marc_bank`) and BUILD_LOG's notes on "Marcella taker"
  (tz-9, tz-20) before changing it: say why this differs (the bank passive was never the reason before).
- KPIs in decoded local games: gems banked by Marcella (72 -> 200+), her gold by r300 / r600, Vesper's mean bag
  (39 -> 25), bag lost on death, team gold. Band: `tz174_big`, then the class sets.

### L14. The cluster timetable (`bots/_econ`, switch `clusx`)  [built; LOST locally; second wave]
- State (`docs/research/diag_10nov/econ.md`): bits 1 / 2 / 4 / 8 / 16 / 32 built, cmp identical at 0, fires. v idle the
  clears rose (own-zone gem 3.2 -> 4.6) but team income did not (1,000th gem r872 v r860). v `_m2`: **37.9 %** (256
  games, one seed), deaths 6.4 v 5.9.
- Why the first estimate was too high: 24 % of pure gem groups are islands with no walking path, and the mean walk to
  a pure group in our half is 43-44 tiles; a runner (mostly Issac) leaves its squad a body short and splits the twins.
- What is still worth one try each: `clus_who=2` (Vendetta runs: one tile a turn, FINDINGS §13) without bit 2
  (`clusx=13`); and the islands by crystal (a quarter of all pure gem groups; the 9 Nov `tele` build).
- **A base fault found on the way, worth its own small switch:** bodies waiting for a respawn stood on ANOTHER
  group's spawn tile, which freezes that group's respawn, and each waited on the other: on one map side the whole team
  froze from r700 to r2000. `act_farm`'s wait branch only steps off its own target's tiles. The fix (a waiting body
  steps off any spawn tile) is in `_econ` under `clusx` bit 1: move it out under its own switch (see L15).

### L7. Opening: gems before gold, fewer bodies per group (`bots/_open`, `openx`)  [small new build]
- Evidence: FINDINGS §7. In the first wave the top takes gem clusters 11 % (we 2 %) and gold clusters 14 % (we 25 %);
  it puts 2.33 bodies on a first group (we 2.71, 2.96 on big maps) and 3.67 hitters on mid-strength camps (we 4.16).
- Build it in the planner's pricing, not as a draft-turn solver (no time): until r100, 1 gold counts half its usual
  weight against gems in the group price; cap the bodies committed to one group by its strength (clusters 1,
  Str <= 20: 2, Str <= 60: 3); when a group is full the next body takes its next-best group.
- Measure v idle on all maps (gems collected at r100 / r150 / r300 must rise; the 1,000th gem must not come later),
  then band: `181|openx: gems over gold to r100, group caps by camp strength|_open|tz174_big|openx=3`.

### L8. Tribute hygiene  [demoted: the "restarts" reading was wrong]
- A direct count shows our channels are not restarted more than the top's (FINDINGS §5, correction). What is left:
  an enemy lock lands during 13-17 % of our channels above 80 gems (top 7 %): the bag cap in L3 covers it. From the web
  only: starting the tribute on the turn of arrival gained another team 11 wins in 100; check ours does (the turn it
  first stands within 1 of the altar with a bag over the threshold) before building anything.

### L9. Class rows from the band archive (`bots/_cls`, `clsx`)  [lowest priority: hypotheses]
- Re-run `~/tzunami_data/analysis_10nov/cls/mine.py` to print the numbers behind each row, finish the edits, cmp at 0.
- Test single rows on the class sets that exist: row 2 (support Health lines) on `a1_m2` and `tiny_m2`; row 4 (fb2 off)
  on `tiny_m2`; row 32 (dth 0) on `a1_m2`. Rows 1, 8, 16 need new class sets (4-pick, big, mid-heavy): only if time is left.

## 3b. Tuning (hill climbing): only after a lever passes the band

- Local hill climbs v our own bot found nothing that carried to the band on 9 Nov (17 knobs). Do not climb on local
  win rate.
- What to climb: the 2-3 threshold knobs of a lever that has already won on the band (`priox_r`, `post_k`, `tiny_hr`,
  `a1x_lbag`, `fort_hp`), one knob at a time, two values each side.
- The score: the lever's own KPI in decoded local games first (doubles and double strikes a game, deaths by r150, lock
  cover), to throw out settings that break the behaviour; then ONE band stage for the best setting, paired with the
  lever's own band run (not with the base), on a fresh seed.
- Budget: at most 4 band stages on tuning in total. A new lever is worth more than a tuned one tonight.

## 4. Building the final bot

1. **Merge** each band-confirmed lever into one copy (`python3 -I tools/variant.py _m2 _fin`), 3-way against the
   untouched base: `git merge-file bots/_fin/src/bot.cpp bots/_m2/src/bot.cpp bots/_X/src/bot.cpp` (same for value.h,
   world.cpp, draft.cpp; copy new headers). Set the confirmed switch values as defaults. Check: with all new switches at
   0, `_fin` is byte-identical to `_m2`.
2. **Crash and fuel screen:** `tools/jslot.sh python3 -I tools/judge.py _fin --opp _m2 --jobs 2` (256 games) and
   `--opp idle`: no rise in fuel cuts, no body that stops acting, banks on every map. Check the odd map kinds named in
   FINDINGS §9 still work (islands, walled altars).
3. **Band check of the stack:** paired with `tz174_big` (150), `a1_m2` and `tiny_m2` (120 each). The stack must be >=
   each single lever's gain on its class and not negative on the general set. If a lever turns negative inside the
   stack, drop it and re-check.
4. **Fresh confirmation** of the stack v v281 on a new general seed (fresh2.sh, 150 games each).
5. **Decision order for what goes live:** the confirmed stack; else the best single confirmed lever on `_m2`; else
   v281 (tz-mega2) or v280 as now. Never put an unconfirmed build live for the lock.

## 5. Lock checklist (start by 21:00 on 10 Nov; nothing new after 22:30)

- [ ] `.venv/bin/cambc submissions list --json` works (the login was renewed 9 Nov ~23:00; it lasts 7 days).
- [ ] Fuel on heavy maps: in the final build's 256-game screen, no map with more than ~150 fuel cuts a team-game above
      the base; if a camp-heavy map chokes, turn on the governor (`pathx` bit 8) and re-screen.
- [ ] The final source builds clean; `TZ_STAMP` set (e.g. `tz-fin`); the crash and fuel screen passed.
- [ ] `cambc submit` the final build, wait for the compile, `submissions activate V`, play one unranked group, and
      read back `active V selected V`.
- [ ] Set `LV` in `tools/restore93.sh` to V. Copy the final source into `bots/tz`. Stop the queue runner.
- [ ] `docs/BUILD_LOG.md`: a handoff block with the final build, every stage's numbers and what was dropped;
      update the `bots/` row of `CLAUDE.md`; update the resume note in memory.
- [ ] Delete scratch copies (`bots/_tzN`, unused `_X_variant` dirs) and scratchpad match outputs. Disk is 94 % full.

## 6. Hazards

- **iCloud:** copied files can arrive as 0 bytes; `tools/variant.py` checks sizes; after any manual copy run `wc -c`.
- **Map names:** the platform uses underscores, local files hyphens. The class lists hold both spellings.
- **A test build left live:** every band script ends with `restore93.sh`; if a run dies, run it by hand and check
  `active 280 selected 280`.
- **Login loss mid-run** (it happened on 9 Nov at ~21:38 during a ladder list pull): if `cambc` answers "Sign in
  first", stop the runner and ask the user to run `! .venv/bin/cambc login`. Do not pull ladder lists in bulk tonight.
- **Selection bias:** a base set that picked a winner is worn for that winner. Confirm on a fresh seed.
- **The teammate** also uses the band: pause the runner when asked. **At 02:45 on 10 Nov the teammate's v283 ("n5: v278
  + team takes") was active and selected.** `tools/restore93.sh` and `tools/band3.sh` restore v280 by default: before any
  band stage, agree with the teammate which version must be live afterwards and set `LIVE_VER` to it
  (`LIVE_VER=283 zsh tools/bandq3.sh ...` passes it through), or wait until they are done.
- Never read `bots/v93`. No map names or coordinates in code. No other team's code.
