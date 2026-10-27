# Routing design (23 Oct): the five pieces, in REPLAYS §7's order

> "Write the design doc for the pieces in REPLAYS §7's order: respawn timing first, then banking as a route leg
> (with every body capturing and shopping), then the corrected need, the capture guard and the exposure price."
> (user, 22 Oct)

This is phase 3's design for the deep dive (`docs/nav/README.md`). It was written from `bots/cpp/src` as it stands
(the C++ port of R9, = `bots/cpp-port`) and from the facts in `docs/nav/REPLAYS.md` §6 that held in **both halves**
of the 57 ladder losses. No bot code changed in this session.

Tags as in `CLAUDE.md`: **[rules] [sdk] [measured] [code] [guess] [pm]**. [code] means `bots/cpp/src` at
`cb8d6f3` plus the uncommitted `bots/cpp` tree; line numbers are from that tree. Each piece ends with
**"Unknowns to check when building"**. A guess in code is a one-line constant with a `// GUESS` comment. §10
collects every unknown.

**Status (23 Oct):** piece 1 is built on `bots/cpp` and beats the bar: 46W/34L vs `cpp-port` (§1.6). Its U1.1–U1.5 are answered there; U3.1 and
U3.5 were checked in the same session (§3.5): the clear rate is **not** 3× (RATE_X 3 is refuted), so piece 3's
premise needs a new look before it is built. **Piece 2 (23 Oct, §2.7):** the altar choice by least added walk is
kept (8 jitters: 59.1 % vs piece 1's 55.3 %, detour 6 → 4); the leg price and 2b's rotation lost and are scrapped.
Builds are judged over 8 fuel jitters (`tools/jitter.sh`, §9), not one run.
**Piece 3 (§3.6) and piece 5 (§5.6): not built**, every form lost. **Piece 4 (§4.6): kept in its smallest form**
(leave a capture only once an ally stands on a spawn tile; the claim spares a lone capturer): 59.2 % vs 57.2 % over
22 jitters. **The routing build is done (23 Oct):** `bots/cpp` = pieces 1, 2 and 4, shipped as `submissions/cpp-p4.zip`.

## 0. What the design rests on, and what it leaves out

### 0.1 The facts (all 57 games, us / them, held in both halves) [measured]

| # | Fact | Numbers | Piece |
| --- | --- | --- | --- |
| F1 | They stand at the camp when it respawns | a body there at 12 / 31 % of respawns; when there, hits first 74 / 92 %; waited 4 / 6 rounds (median); respawn → take 30 / 15 rounds; they reach 2948 respawns first to our 2045 | 1 |
| F2 | They kill more elk | 3.8× our elk kills | 1, 3 |
| F3 | Banking is a leg of their route | 10.5 / 30.1 banks a game; bag 16 / 26; detour 11 / 2 tiles (n = 310 / 841 walking banks); altar → next group 11 / 9 tiles; first bank r185 / r92 | 2 |
| F4 | Every one of their bodies captures and shops early | gems captured by r300, bodies 1–5: 59 / 25 / 6 / 2 / 0 vs 71 / 46 / 29 / 21 / 8; first shop r79 / 245 / 339 / 377 / 475 vs r79 / 91 / 110 / 130 / 239; takes by r300 18.5 / 27.9 | 2b, 3 |
| F5 | Our static need is too high at every need level | need-2 groups taken solo 36 / 59 %; groups we rate untakeable (S+1) taken 40 / 256 times; clear rate 160 / 194 HP a round per body (median, solo takes of groups ≥ 1400 HP, n = 448 / 782) | 3 |
| F6 | The model's damage is too high too | at the measured rate, real damage taken ≈ 0.6× the all-awake model (half 1 only); HP lost 196 / 276 (median, gross) | 3 |
| F7 | Their crews are a little bigger only on early elk | bodies per elk take r100–300: 3.3 vs 2.6–2.7; elsewhere crew size per take is about the same | 3 |
| F8 | They capture what is cleared | they capture 57 % of contested lives to our 41 %, and steal 123 cleared groups to our 72; arrival order does not decide it | 4 |
| F9 | We die walking, to champions | deaths 17.5 / 5.0 a game; 90 % of ours to champions; 82 % of ours while walking (47 % of theirs); gems lost 79 / 27; a dead trip lasts 196 / 136 rounds; being alone does not separate us (H2: 59 % of ours alone, 65 % of theirs) | 5 |

Rules the design uses [rules, `GameRules.md` §Camps & capture, §Turn order]:

- R1. "Occupy at least one of its spawn tiles uncontested. … a five-round timer … Leaving the region empty or
  admitting an enemy resets progress. More allies do not speed it up."
- R2. "Rewards are shared among allies present when it finishes; the lowest ID receives any integer remainder."
- R3. "The group respawns together after rewards are claimed, using the longest cooldown of its members. Any
  occupied spawn tile delays the entire group." Cooldowns are 50–60, the golem 80 [sdk].
- R4. Round start runs camp respawns, then camp captures; champion turns then alternate teams.
- R5. Monsters are friendly until hit and do not chase. The killer of a champion takes its whole bag.

What the SDK gives [sdk, `sdk/cpp/cambc.h`]:

- `camp_group::state()` returns `camp_group_respawning{timer}` with the rounds left, but only while one of the
  group's spawn tiles is in vision. Out of vision it throws ("remembered state outside current vision is not
  exposed").
- `max_respawn_timer()` is static per group, and `World` stores it as `o.resp` (`world.cpp:109`).
- `gem_count()` works on any visible champion. Ally gold is not visible.

### 0.2 What is out, and why

- **No tour planner and no better order.** Order is even (41 / 39 % nearest live, 2 / 2 tiles extra walk), and
  69 % of their moves are new pairs (REPLAYS §6, Q11) [measured].
- **No arrival-order rule.** "Contests go to the second arrival" flipped in half 2 (the first hitter took 54 % of
  theirs) [measured].
- **No cohesion or "stay together" term.** The stacking gap is small (.26 vs .19 of bodies in clusters of 3+) and
  sits in early elk crews, which the corrected need covers (F7).
- **No "alone" price.** F9.
- **No change to how gold is valued.** "Every body values gold" lost 24W/46L to R8 (`docs/redo/10_GOLD_ITEMS.md`
  §4.1) [measured]. Piece 2b changes **who captures**, not `ROLE_GOLD`.
- **No per-map anything.** Every number below is read at runtime from the map, the record or the SDK (`CLAUDE.md`
  rule 10).

### 0.3 One currency

Every price stays in **gems per round of the option** (`CLAUDE.md` rule 2): value ÷ (walk + wait + clear +
capture), minus risk. Piece 1 turns waiting into rounds, piece 2 turns the bank detour into rounds, and piece 5 turns
exposure into expected gems lost.

## 1. Respawn timing (P14 first to the field, P15 timing)

### 1.1 The gap

F1 and F2: a respawning group is the nearest free value on the map, and they are standing on it when it comes back.
We arrive late, or not at all.

### 1.2 Current code [code]

- **A respawning group prices 0.** `farm_price` returns 0 while `mem.st[g] == Resp && mem.until[g] > s.r`
  (`prices.cpp:237`). The body only picks the group after `Mem::update` flips it back to Alive at `until`
  (`memory.cpp:60`), and then it walks the whole way.
- **Arriving at a respawning group ends the goal.** If no camp of g is in vision and `observe_group` says Resp,
  `farm()` returns Done (`beh.cpp:207`). The body turns round and the trip is wasted.
- **The timer has two sources today:**
  - Our own capture. `until = r + o.resp` when the capturer's bag or gold rises (`beh.cpp:222`, `beh.cpp:229`).
  - Vision. `until = r + timer + 1` from `camp_group_respawning` (`memory.cpp:49`).
- **The handoff guesses the timer and excludes the group.** A body that hands the capture to the carry sets
  `until = r + o.resp` at once, before the capture finishes (up to 5 rounds early), and excludes the group for EXCL
  20 rounds (`beh.cpp:214–215`).
- **Groups unseen since the start are Alive by default.** A body walks to them, finds them respawning, and leaves:
  that is a dead trip.
- **Allies' captures are invisible.** A claim (`C_FARM` + mi) that disappears could be a capture or an abandoned
  goal, so readers can't tell.

### 1.3 Design

**Timer sources.** Three, best first:

1. **Vision.** Unchanged (`memory.cpp:49`). It is exact and corrects every estimate below.
2. **Our own capture.** Unchanged, plus one fix: the body **steps off the spawn tile** on the capture round (R3,
   an occupied spawn tile delays the group). The Ring goal already never roots on a spawn tile (`nav.cpp:283–285`).
3. **An ally's capture, broadcast with a new slot code `C_CAPT = 4`.** Code 4 is unused today (`comms.h:8`).
   - The capturer writes `4 | mi << 3` to its slot byte on the round its bag or gold rises at a capture, and holds
     it for `CAPT_HOLD` rounds [guess 2].
   - A reader that sees code 4 with target mi sets `st = Resp` and `until = r_read + o.resp − 1`. The −1 covers a
     read one round late; arriving early costs a round of waiting, arriving late loses the first hit.
   - The reader also records `lastcap[slot] = r_read` and adds `o.gold` to `capgold[slot]`, both for piece 2b.
   - The handoff body sets `until = r + CAPTURE_TIME + o.resp`, an upper estimate (it was 5 rounds early). The
     carry's code 4 replaces it.

**Price.** A respawning group is priced as a live one at full HP, with waiting counted as rounds:

```
wait  = max(0, (until − r) − walk)                // rounds stood at the Ring
price = value / div / (walk·walk_w + wait + clear + 5 + …) − risk
```

- The monsters are the group's start HP (`o.hp0`, `o.str0`). `live_mons` returns nothing for a non-Alive group, so
  add a `full_mons(g)`.
- Waiting is not multiplied by `walk_w`. It is plain rounds.
- No cap on the wait. A long wait prices itself out against farther live groups. A cap is a fallback if idle time
  rises (§1.5).
- `near6` already lists groups by walk regardless of state (`prices.cpp:269`), so respawning groups are already
  candidates.
- Delete the `return 0` at `prices.cpp:237`.

**Behaviour.** `farm()` on a group that is Resp:

- Replace `return Status::Done` at `beh.cpp:207`. Walk to the **Ring** (never a spawn tile, R3), stand, and set
  `ST.waiting`.
- When the group respawns (its camps are seen Alive), run the normal farm and hit first.
- The goal's work bound in `beh_enter` (clear rounds + 8, +10 if need ≥ 2) gets `wait` added, so the timeout
  doesn't fire while the body waits.
- Re-pricing every turn keeps the wait honest: if a better option appears, HYST decides as for any goal.
- A body standing at the Ring is safe from the camp: monsters are friendly until hit (R5).

**Delete:**

- The EXCL exclusion after a handoff (`beh.cpp:215`). The timer prices the group now, and excluding it for 20 rounds
  would stop the body waiting for it.
- The early `until` guess in the handoff (it becomes `r + CAPTURE_TIME + o.resp`).

### 1.4 What it should do to the numbers

Toward theirs:

- a body within 2 of the group at the respawn: 12 → toward 31 %;
- respawn → take: 30 → toward 15 rounds;
- elk kills up (F2);
- fewer dead trips (arrive at a Resp group, leave).

Watch for:

- idle body-rounds (waiting);
- takes by r300;
- deaths while waiting (piece 5 prices that later).

### 1.5 Unknowns to check when building

- U1.1 `CAPT_HOLD` 2 rounds [guess]. A reader whose turn rolls over (unfinished turns carry over) may miss a code 4.
  Count misses in the trace. A missed read is today's behaviour, no worse.
- U1.2 The off-by-one: `memory.cpp:49` adds +1 to the timer. Check in one arena trace that a group with
  `until = U` is Alive in vision on round U (R4: respawns run at round start).
- U1.3 Groups with record index ≥ 31 have `mi = 31` (`world.cpp:40`) and can't be named in a slot byte, so no
  code 4 and no claims. How many groups is that on the 40 maps (MAXG 64)? It is an existing limit, not a new one.
- U1.4 Whether a body passing over a spawn tile during the timer delays the respawn, or only one standing there at
  the respawn round (R3 says "occupied"). Nav never roots there; check that walks don't cross spawn tiles either.
- U1.5 Whether waiting costs takes elsewhere (REPLAYS §9, open for them too). Measure idle body-rounds; if they rise
  with no gain in takes, add a `WAIT_MAX` cap [guess 15].
- U1.6 Whether `walk_w` (Race) should apply to waiting. The design says no.
- U1.7 Enemy captures are known only from vision. Fine: the walk there sees the camp, and `observe_group` gives the
  exact timer.

### 1.6 Built (23 Oct): results [measured]

**Verdict: kept.** `cpp` (piece 1 + `WAIT_MAX`) vs `cpp-port`: **46W/34L, margin +72, g/r 0.39, deaths 10.4,
13/40 maps won from both sides, faults 0** (`runs/arena/cpp-vs-cpp-port-20261023-115529`). Unchanged `cpp` (the noise
floor) went 37W/43L, margin +19, g/r 0.38.

**What was built** (`bots/cpp/src`):

- `take_mons` (`model.cpp:39`): a Resp group's camps at start HP; `need_k_r9` and `farm_price` use it.
- `farm_price` (`prices.cpp:238–240`): `wait = max(0, until − r − walk)` in the denominator, not × walk_w (U1.6);
  `WAIT_MAX` 15 [guess] prices a longer wait 0. The Resp `return 0` is deleted.
- `farm()` (`beh.cpp:249`): a Resp group → `wait_ring` (`beh.cpp:99`): step off a spawn tile, else Nav to the Ring
  (Safe), `ST.waiting` when standing. `beh_enter` adds the wait to the work bound (`beh.cpp:444`).
- Capture detection moved to `Mem::update` (`memory.cpp:119`): bag or gold up while standing on a Resp group's
  spawn tile seen this round. In `farm()` it never fired: the capturer re-decides before `farm()` runs.
  `captured()` is deleted.
- **Code 4 = CAPT** (`comms.cpp:50`, `mark_capt`), held `CAPT_HOLD` 2 rounds [guess]. Readers (`memory.cpp:90`)
  call `note_capt`: Resp, `until = r + resp − 1` (`lastcap`, `capgold` for 2b were deleted with 2b, §2.7).
- The handoff sets `until = r + CAPTURE_TIME + resp` and excludes only the next round; the EXCL 20 is gone.
- `observe_group`'s timer: `until = r + timer` (the +1 is gone, U1.2).

**The cap was needed (U1.5).** Without it the build lost 35W/45L, margin −40. Bodies stood still 11 % of
body-rounds (5 % before), first shop r70 → r88, takes by r300 20.4 → 19.3, and gold-cluster kills 5,916 → 5,110.
With the cap every value from 8 to 25 wins: 8 44W, 10 47W, 15 46W, 20 45W, 25 47W (of 80). So it is the cap, not
one lucky value, and it stays at the doc's 15.

**§1.4's measures, us, base → no cap → cap** (arena replays via `tools/replay/farm/arena_decode.sh`; theirs from
REPLAYS where known):

| Measure | base | piece 1, no cap | piece 1 + cap | theirs (ladder) |
| --- | --- | --- | --- | --- |
| body within 2 at the respawn | 13 % | 27 % | **26 %** | 31 % |
| respawn → first hit, median (when we hit first) | 47 (33) | 31 (18) | **33 (22)** | — |
| elk kills (80 games) | 1,464 | 1,441 | **1,571** | 3.8× ours |
| takes / game | 60.8 | 61.0 | **64.2** | — |
| captured gems / game | 1,159 | 1,121 | **1,198** | — |
| takes / gems captured by r300 | 20.4 / 126 | 19.3 / 128 | **20.9 / 138** | — |
| first shop / first emblem (median) | r70 / r77 | r88 / r99 | **r73 / r90** | — |
| share still (body-rounds) | 0.05 | 0.11 | **0.07** | — |
| share dead | 0.10 | 0.08 | **0.08** | — |
| deaths / game | 12.9 | 10.9 | **10.4** | — |
| contested lives captured | 54 % | 44 % | **51 %** | — |
| turn rollovers / game | 3.0 | 3.7 | **4.0** | — |

- **Dead trips** (arrive at a Resp group, leave) are gone by construction: `farm()` no longer returns Done there.
  Not counted.
- **Watch:** rollovers +1 a game (cpp-port's side 3.4 in the same games). The new per-turn work is small (a code-4
  scan of 5 slots, one clear_model per Resp candidate), so this may be play, not fuel. Check in piece 2, whose AW
  fields are the real fuel risk (§7).
- **Worst map 00eight (−897; base won it from both sides).** A fight snowball: the enemy Vesper ended with 22 Power
  and 21 Durability emblems and made 42 of our 57 deaths (side A). The traced copy of the same build won 00eight from
  both sides (+812, +776), so it is the chaotic early-fight swing, not the respawn rule. Avoiding a giant enemy is
  piece 5 (exposure).
- **How chaotic the arena is:** the engine is deterministic and the arena caches by source hash, but any change
  flips about half the games (base vs piece 1: 44 of 80 the same result). One 80-game run moves by several games
  on any change. A sweep of a new constant's neighbours (as for WAIT_MAX) is the cheap check that a win is real.

**Traced run (`bots/_p1`, TRACE 1, capped build, 80 games; 49W/31L, but trace fuel changes play):**

- U1.1: 17,885 code-4 reads of 20,681 expected (captures × other bodies): **13.5 % missed**. The expected count
  includes dead bodies (8 % of body-rounds), so true misses are lower. A missed read is today's behaviour; CAPT_HOLD
  stays 2.
- U1.2: a group with `until = U` was first seen Alive on round U in **7,577 of 7,752 (97.7 %)**, U+1 in the rest. The
  +1 is removed.
- Waiting 5.1 % of body-rounds (10.2 % without the cap), idle 6.6 %. Deaths while waiting at a Resp group: **0.06 a
  game**. The Ring is safe (R5), so piece 5 need not price waiting.
- Deaths by goal at death, a game: heal 7.6 (most deaths happen on the way out to heal), kill 2.0, farm 0.55, bank 0.55.

**U1.3** [measured, MAPDUMP]: 50 of 836 groups (6 %) have mi ≥ 31, on 5 maps (00road-of-riches 20, 01islands 15,
00lanes 11, 00lost-world 3, 00split 1), holding 3.3 % of the gems; the most groups on a map is 51 (MAXG 64). They get
no code 4 and no claims. A small, existing limit; not worth a wider slot byte.

**U1.4** [rules]: only a champion standing on a spawn tile at the respawn round delays it. The Ring roots exclude
spawn tiles (`nav.cpp:283–285`), and the capturer steps off. Global paths may cross a dead camp's tiles, but only
standing there at the respawn round matters; not seen in the traces.

## 2. Banking as a route leg (P12 speed and tempo)

### 2.1 The gap

F3: they bank three times as often, with bigger bags, at an altar 2 tiles off their way. Ours are 11 tiles off,
and start 90 rounds later. MAPS §5.2: per-map median altar detours run from 1 to 95 tiles [measured].

### 2.2 Current code [code]

- **The altar is the nearest by walk from the body** (`bank_altar`, `prices.cpp:158–183`), with three switches:
  - our bank altar if the nearest is on their side;
  - away from a fresh enemy stack (`s.sap`, STACK_R);
  - closed altars skipped (`altar_open`).

  It never looks at where the body goes next.
- **The BANK price** is (`prices.cpp:359–366`):

  ```
  bag·(1+P)·near / (bwk·bank_ret + chan) · prof.bank · pm.bank_risk
  ```

  - `near` = 2 when the bank walk `bwk ≤ BANK_NEAR` 8 (`prices.h:29`);
  - ×`GROUP_BANK_X·bag/100` for a stack with bag ≥ 100;
  - ×`sig((near_e − 4)/1.5)`.
- **The farm price adds a detour term**: `cheb(group anchor, its nearest altar) − s.walt` (`prices.cpp:264–265`),
  where `s.walt` is the body's walk to its nearest altar. It is a fixed lean toward groups near altars, whoever
  carries the bag.
- **Walks the body can read now** (`nav.cpp:339–340`): `NAV.gd[g]` (me → group anchor) and `NAV.ad[a]` (me →
  altar), from the field F_me built at the body. There is **no altar → group walk**.

### 2.3 Design

**A static table of altar → group walks, `AW[a][g]`.**

- Each altar's goal field (NavKey::Altar), read at every group anchor.
- Built at runtime, **one altar per turn**, when the turn's ledger has room for one field (`field_cost`, measured
  in `build_fme`; FIELD_COST_100 = 31k at 100×100 [code]). It starts on the first play turn (2× fuel [sdk]).
- Stored in `World`, because the map is static. u16 × MAXA 32 × MAXG 64 = 4 KB.
- A row not built yet means that altar falls back to today's choice.
- **Why not the draft record:** it needs nA × nG bytes (up to 512 at 8 altars and 64 groups). The record already
  holds 16 + 3·nA + 6·nG + 3·nB + the tail, so the extra bytes may not fit in 1,024, and it would need a
  MEM_VERSION bump. The cost at runtime is one field per altar per body, spread over the first turns.

**The added walk of banking on the way to the next group:**

```
added(a, g) = NAV.ad[a] + AW[a][g] − NAV.gd[g]        // ≥ 0 up to field noise; clamp at 0
```

- `g` = **g_next**, the best-priced FARM candidate this turn. So `price_all` prices the FARM candidates before
  the bank (today `bank_altar` runs first, at `prices.cpp:333`).
- With no farm candidate, `added = NAV.ad[a]`, today's walk.

**`bank_altar` picks the open altar with the least `added(a, g_next)`.** It keeps today's switches, as filters:

- skip their-side altars (`aside == 2`) unless none of ours is open;
- skip altars within STACK_R of `s.sap` unless none is left;
- skip closed altars (`altar_open`).

**The BANK price uses the added rounds:**

```
bp = bag·(1+P) / (added·bank_ret + chan) · prof.bank · pm.bank_risk   [×GROUP_BANK term kept] [×sig kept until piece 5]
```

- A bank on the way costs only its channel, `ceil(bag/10)` rounds [rules], so it is taken whenever the body passes
  an altar with a bag.
- A bank far off the way costs its detour, as it should.

**The next group from the altar** needs no new code. After the tribute the body re-prices from the altar
(`near6`, F_me at the altar), so the next leg starts there.

**Delete:**

- BANK_NEAR and BANK_NEAR_BONUS (`prices.h:29`, `prices.cpp:361`). The added-walk denominator does the job the
  bonus approximated.
- The farm-price detour term (`prices.cpp:264–265`). The bank leg is priced where it is decided, and the carry risk
  of a big bag is piece 5's.

**Why it is sound in one currency.**

- Today a bank costs about `bwk + chan` rounds, and the bag rides at risk the whole time.
- With the leg, it costs `added + chan` rounds.
- With our death rate (~17.5 a game over 2000 rounds × 5 bodies ≈ 0.002 per body-round [measured, rough]), a
  26-gem bag carried 20 extra rounds loses about 1 gem in expectation. That is the order of a bank detour of 1–2
  rounds. So banking on the way at bags of ~10–30 is right, and the leg makes it cheap.

### 2.4 Piece 2b: every body captures and shops (alongside the bank leg)

A body that banks needs a bag of its own. Today one body takes almost everything in a crew.

**Current code [code].** `handoff()` (`beh.cpp:73–89`):

- The carry among the bodies claiming g within 4 tiles is: the main if present, else the second, else the lowest
  slot.
- The others step off the spawn tile and leave.
- Off group maps, crews are ad hoc via claims. On group maps after OPEN_END, `group_slots` makes fixed crews
  (`upd.cpp:166–172`).
- The main wins every crew capture it is in.

**Design: rotate the carry.**

- Among the crew present, the carry is the slot with the **oldest `lastcap`** (piece 1's code 4). Ties go to the
  lowest slot.
- **Main first until its first emblem.**
  - Readers can't see the main's gold, but they can add it up: `capgold[main]` = Σ `o.gold` over its code-4
    captures (static per group).
  - The main stays carry while `capgold[main] < EMBLEM_GOLD`. EMBLEM_GOLD is the first emblem's price; `ME.need`
    starts at 150 [code, champs.h:36]; read the item cost from the SDK when building.
  - This keeps session 3's gain (main's first emblem r110 → r75, 06 §10) and frees the others after it. Their main
    shops at r79, as ours does (F4).
- Two bodies can disagree about who is the carry (one missed a code 4).
  - If both stand, R2 splits the reward. That is harmless.
  - If both leave, nobody captures. Piece 4's rule stops this: a non-carry leaves only once an ally is on a spawn
    tile.
- **Unchanged:** `ROLE_GOLD`, the shop window, `buy_all`.
  - A body with gold shops on its next spawn visit (`main.cpp:80,87`).
  - Most of the funnel fix comes from piece 3: solo takes of need-2 groups give bodies 3–5 bags and gold of their
    own.

### 2.5 What it should do to the numbers

Toward theirs:

- banks a game: 10.5 → toward 30;
- detour: 11 → toward 2 tiles;
- first bank: r185 → toward r92;
- banks by body (all five bank);
- gems and first shop by body to r300 (F4).

Watch for:

- bag at death and gems lost (bigger bags carried longer);
- the main's first emblem round (must not slip past ~r100).

### 2.6 Unknowns to check when building

- U2.1 Fuel of the AW rows: one field per altar per body, and the altar count on the 40 maps. Check rollovers on the
  first 20 rounds of the biggest map with the most altars. If they rise, build the rows in the draft instead (bump
  MEM_VERSION, check the 1,024-byte fit).
- U2.2 Field noise: `added` can go a little negative because anchors and rings differ. Clamp at 0. Check that
  `NAV.ad` and `AW` both use the Altar goal's roots (`nav.cpp:288`, cheb 1 of the altar).
- U2.3 Whether g_next should be the best FARM candidate or the current FARM target when one is held. Start with the
  current target if held, else the best candidate.
- U2.4 Small bags at a zero-added altar: price ≈ bag / chan, so 2 gems ÷ 1 round can beat a farm at ~0.5 a round.
  It costs one round, so it is cheap. If the trace shows many 1–3 gem banks, add `BANK_MIN` [guess 5].
- U2.5 Deleting the farm detour term: check bag sizes at death don't rise before piece 5 lands.
- U2.6 `CAPTURE_TIME` and EMBLEM_GOLD from the SDK, not constants (`cambc::capture_time` [sdk]).
- U2.7 Whether rotation or a split (every crew body stands on a spawn tile, R2) spreads gold better. A split gives
  each body 1/k of the gems, so k small bags to bank. Rotation keeps bags whole. Rotation is the design; a split is
  the fallback if rotation mismatches are common.
- U2.8 What counts as "the region" in R2. If Ring tiles count as the region, a guard there splits the reward
  (piece 4). Check in one match: a body on the Ring during an ally's capture, and look at its bag at the claim.

### 2.7 Built (23 Oct): results [measured]

**Verdict: the altar choice is kept; the leg price and 2b's rotation are scrapped.** `cpp` = piece 1 + the AW rows
+ `bank_altar` by least added walk. Against `cpp-port` over 8 jitters (640 games, §9): **378W/262L (59.1 % ± 1.4),
margin +49 ± 12**. Piece 1 alone on the same 8 jitters: 354W/286L (55.3 %), margin +57. Faults 0. The as-designed
build (leg price + rotation, `docs/redo/patches/ROUTING_P2_leg_rotation.diff`) lost: 37W/43L, margin −32, in one run.

**How it was judged: jitters, not one run.** One 80-game run moves by ±5 wins on any change (§1.6). So each build ran
as 4 or 8 copies that burn J loop steps at the start of each play turn (`tools/jitter.sh`, J = 0 300 700 1500 100
500 1000 2500). The strategy is the same; the chaos differs. Per-run sd ≈ 4.5W, so 8 jitters give an SE of about 1.5
points of win rate. Calibration: jittered `cpp-port` vs `cpp-port` over 7 jitters went 279W/281L (49.8 %), margin
+9, so the method has no bias.

| Build (all on piece 1) | Jitters | Win % | Margin | Note |
| --- | --- | --- | --- | --- |
| piece 1 (`_ref`) | 8 | 55.3 | +57 | deaths 11.5, kills 12.8, gems lost 104 |
| leg price, as designed (bank_ret folded) | 4 | 54.1 | −16 | banks 24.5/game, first bank r162 |
| leg price + farm detour kept | 4 | 50.9 | −28 | so the leg price is the harm, not deleting the detour |
| leg price on min(added, walk) + BANK_NEAR kept | 8 | 56.2 | +49 | |
| **altar choice only (kept)** | 8 | **59.1** | **+49** | per run 45, 52, 42, 48, 50, 49, 47, 45 W |
| rotation, as designed | 4 | 51.6 | −25 | kills 12.8 → 8.9 |
| rotation, the main always carries when present | 4 | 55.3 | +37 | second body's gold by r300 194 → 136 |
| altar choice + that rotation | 8 | 56.6 | +58 | |
| leg price + that rotation | 4 | 49.4 | −45 | |

**What was built** (`bots/cpp/src`):

- `World::aw_build` (`world.cpp:195`): one AW row a turn, a field rooted on the altar tile over `blk_dist` (as F_me
  is), read at every group anchor. `main.cpp:210` builds it after F_home when the turn has room
  (`NAV.field_cost + 5000`). `AW[MAXA][MAXG]` u16 in `World` (`world.h:70`).
- `bank_altar(…, gn, …)` (`prices.cpp:161`): among the open altars (ours first; away from a fresh stack if any is),
  the one with the least `ad + AW[a][gn] − gd[gn] − 2` (≥ 0), where gn = the held FARM target, else the best-priced
  FARM candidate. With no gn, an unreachable gn or a missing row, the nearest (as before). The current target is held
  while banking.
- `price_all` prices the FARM candidates before the bank. The BANK price is unchanged: `bag·(1+P)·near /
  (bwk·bank_ret + chan)`, where bwk is the walk to the chosen altar.

**Why the leg price lost.** It made banks rarer and bags bigger, not the reverse: banks/game 27.3 → 24.5, first
bank r146 → r162, bags ≥ 60 6 → 9 % (`legs.py` on the first leg build: banks 2,162 → 1,951, bag mean 22.1 → 27.6,
≥ 60 5 → 10 %). An altar off the line to the next target is priced by its whole detour, so the body farms on with
its bag; deleting BANK_NEAR's flat bonus (bank when an altar is close) removed what kept bags small. Bigger bags
ride longer at risk. The added walk is the right **choice** among altars; the walk to the altar stays the right
**price**.

**Why rotation lost (U2.7).** Gold concentration wins fights. Rotating the carry gave bodies 3–5 gold of their own
(earned by r300: 107/66/49 vs 94/46/20), but took it from the second body (194 → 136) and the kills fell (12.8 →
8.9 as designed). This is 10_GOLD_ITEMS's finding again (spreading gold lost 24W/46L). The split (R2) would spread
gold more, so it was not tested. The carry stays main / second / lowest.

**§2.5's measures** (stats.json, 640 games of the kept build vs piece 1's 640; the detour from `legs.py` on the J0
run, 80 games):

| Measure | piece 1 | kept build | ladder (theirs) |
| --- | --- | --- | --- |
| banks / game | 27.3 | 27.4 | ~30 |
| bag at bank, median / mean / ≥ 60 | 15 / 23.2 / 6 % | 15 / 23.2 / 6 % | — |
| first bank (median) | r146 | r144 | r92 |
| detour to the altar, median tiles (legs.py) | 6 | **4** | 2 |
| walk banks / all banks (legs.py) | 1,435 / 2,162 | 1,531 / 2,247 | — |
| collected gems by r300, bodies by rank | 64 / 29 / 11 / 5 / 2 | 64 / 29 / 11 / 5 / 2 | — |
| deaths / kills / gems lost a game | 11.5 / 12.8 / 104 | 11.6 / 12.4 / 103 | — |
| turn rollovers / game (≤ r100) | 4.0 | 4.2 (0.8) | — |

- **The gap in §2.1 was smaller in the arena than on the ladder.** In the arena piece 1 already banks 27 times a
  game, and its altar was already the best on the way 84 % of the time (`legs.py`). So the measure that moves is the
  detour; banks and first bank do not.
- Bodies 3–5 still hold few gems by r300; that is piece 3's (the need, solo takes) now that rotation is out.

**Unknowns (§2.6), answered:**

- **U2.1** fuel: on the 6 maps with the most altars (00lanes 18, 00expanse, 01islands, 01yellow-brick-road,
  01big-world, 00ambush), both sides, J0: 4.5 rollovers a game (1.7 by r100) vs piece 1's 5.9 (1.8). Over all 80
  games 4.2 vs 4.0. Not up; rows stay at runtime, not in the draft. 01yellow-brick-road has ~20 a game in both
  builds (worth a look on its own).
- **U2.2** holds by construction: `AW` is rooted on the altar tile over the same `blk_dist` graph as F_me, so
  `ad + AW ≥ gd` up to the ring offset (the −2); clamped at 0.
- **U2.3** built as held target, else the best FARM candidate. Not swept.
- **U2.4** n/a: the price did not change, so no tiny banks were added (bag < 10: 30 % in both builds).
- **U2.5** the farm detour term is kept; deleting it was not the harm (the third row of the table), but it buys
  nothing either.
- **U2.6** `main_emblem_gold` was built for 2b and scrapped with it.
- **U2.7** rotation loses (above); split not tested.
- **U2.8** not checked; it belongs to piece 4.

No new GUESS constant in the kept build, so there is no sweep. Deleted with 2b: `Mem::lastcap` and `capgold`
(written by `note_capt`, never read).

## 3. The corrected need (P1 calculate, P5 know yourself)

### 3.1 The gap

F5, F6 and F7: we rate groups as needing more bodies than they do.

- Bodies wait for partners, or skip need-2 groups that one body clears.
- Bodies 3–5 stay in crews and capture almost nothing by r300 (F4).
- Groups rated untakeable (S+1) are left to them: 256 to our 40.

### 3.2 Current code [code]

**`clear_model(m, k, S)`** (`model.cpp:6–22`):

- k bodies hit for `k·S` HP a round.
- Monsters die in order of str/hp, and every monster hits until it dies (all-awake).

**Callers, each with its own Strength:**

| Caller | Strength used | Where |
| --- | --- | --- |
| `farm_price` | `s.S` (live), splash-adjusted | `prices.cpp:254–255` |
| `finish_dmg` → `can_finish_r9`, `need_k_r9` | `s.S` | `model.cpp:41–47`, `prices.cpp:198–232` |
| draft `bodies_needed` → record `need`, `solo`, `ggems` | `meanS` from base stats | `draft.cpp:146–148, 173–177, 309` |
| boot fallback `bodies_needed` | Str 50, HP 1000 | `world.cpp:73` |
| `rich_group`, `opening_slots` | `CHAMP_STR` 50, inline `hp/(Str·m)` | `upd.cpp:10, 25, 87` |
| `beh_enter` work | `Se` | `beh.cpp:422` |

**What the need gates:**

- `o.need` (the record's) gates the claim branch (`prices.cpp:340–346`: need ≤ 1 skips other claims, else
  `CL.lowcn`).
- It also gates the partner wait in `farm()` (`beh.cpp:123, 128`) and the +10 work.
- `solo` and `ggems` decide `group_map` (GROUP_SOLO_MAX 0.4, GROUP_GEMS_MIN 0.7), which turns on stack mode to
  r300 and `group_slots`' fixed 3+3 / 3+2 / 2+2 / 2+1 crews (`upd.cpp:37–74`, only on group maps, `upd.cpp:166–172`).

**Why it is off.** Basic attack damage is Strength [rules], and base Strength is 30–70 by champion. The measured
clear rate per body is 160 HP a round for us and 194 for them (F5): about 3× Str. The model leaves out abilities and
items, or how often a body really hits [guess: which of these is unmeasured].

### 3.3 Design

**One rate, in one place.** Inside `clear_model` (`model.cpp:12`):

```
kS = k · S · RATE_X          // RATE_X: fitted clear rate per point of Strength   // GUESS 3.0, fit first
dmg *= DMG_X                 // DMG_X: real damage vs all-awake                    // GUESS 1.0, test 0.6
```

- Every caller in the table is corrected at once: the record's need, the live `need_k_r9`, `can_finish_r9`, the
  farm price, the work bound and the boot fallback.
- **Fit RATE_X before building.** Log each solo clear in an arena trace (group HP, rounds from the first hit to the
  last kill, the body's Str, champion) and fit HP ÷ (rounds · Str).
  - If champions differ by more than ~20 %, make it a per-champion column in PROFILES (`clear_x`), read with `s.S`.
  - Otherwise one constant.
- **DMG_X starts at 1.0.** All-awake is the safe side, and the 0.6 is half 1 only (F6). Test 0.6 as a second build
  of this piece.

**Delete `CHAMP_STR`** (`upd.cpp:10`) and the inline `hp/(Str·m)` rounds in `rich_group` and `opening_slots`. They
call `clear_model(...).rounds` with the roster's mean Strength (the draft's `meanS`, written to the record header or
recomputed from the roster), so there is one model.

**Crews from the corrected need.** On group maps, `group_slots`' fixed sizes by S go. Each sub's size is the
corrected need of the group `rich_group` hands it, capped by the bodies left.

- On the 40 maps the corrected need should say 2+ only for early elk (F7) and for golems and monoliths where a map
  has them.
- There is no cohesion term (§0.2).

**What follows on its own:**

- More need-1 groups: no partner wait, no claim block, solo takes by bodies 3–5 (F4).
- Fewer S+1 groups, so the late game opens up.
- `solo` rises and `ggems` falls, so fewer maps are group maps, and stack mode shrinks to the r < 100 opening on
  most maps.

**Check before building, with no bot code.** Re-run `tools/mapstudy.py` and MAPDUMP's need with RATE_X 3 and count:

- groups per need level;
- group maps (of 40) before and after;
- S+1 groups.

This says how much of the stack logic is still live.

### 3.4 What it should do to the numbers

Toward theirs:

- need-2 groups taken solo: 36 → toward 59 %;
- S+1 groups taken: up;
- takes by r300: 18.5 → toward 27.9;
- gems by body 3–5 to r300 (F4);
- elk crews r100–300 near 3 on maps where elk need 2+ (F7).

Watch for:

- HP lost per solo take (theirs 276 median, so ours can rise);
- monster deaths (`microstats.py`);
- recalls.

### 3.5 Unknowns to check when building

- U3.1 RATE_X 3.0 [guess from 160 HP a round ÷ Str 30–70]. Fit it from arena traces, per champion and by item
  level (REPLAYS §9: "the right clear rate per champion and per item level"). Does it grow with shards, or is `s.S`
  enough?
  - **Checked 23 Oct [measured, traced arena of piece 1, 80 games, 3,412 solo clears].** A clear trace logs the
    group's HP, the rounds from the first hit to the group seen with no live camp, the body's `s.S` and base Str,
    and the allies within 4 at the first hit (solo = none). HP ÷ (rounds · Str):

    | | n | per base Str, median / pooled | per `s.S`, median / pooled | `s.S` ÷ base, median |
    | --- | --- | --- | --- | --- |
    | all | 3,412 | 2.04 / 1.88 | 1.05 / 0.68 | 2.22 |
    | Varg | 866 | 5.41 / 3.56 | 1.92 / 1.44 | 2.38 |
    | Ryth | 759 | 2.24 / 1.89 | 1.21 / 0.90 | 1.67 |
    | Ren | 849 | 1.73 / 2.20 | 0.80 / 0.69 | 2.57 |
    | Vendetta | 647 | 1.14 / 1.08 | 0.94 / 0.66 | 1.43 |
    | Vesper | 291 | 1.64 / 0.72 | 0.73 / 0.19 | 3.18 |

    By item level (`s.S` ÷ base): 1.0–1.2 gives 1.27 per base Str and 1.24 per `s.S` (n 806); above 2.5 it gives
    2.36 and 0.58 (n 1,379).
  - **So RATE_X 3 is refuted.** Today's model (rate = k · S) is about right with `s.S` (median 1.05). At the start
    (no items), the record's need runs at 1.2–1.3× base Str, not 3×. Late, `s.S` overstates the rate (0.58 at
    S/S0 > 2.5): items raise `s.S` faster than they raise clears.
  - Champions differ by more than 20 % (Varg ~2× Vendetta per `s.S`; Varg's splash is not in the fit, U3.3), so a
    per-champion column would be needed if a rate is added.
  - Caveats: the rounds include steps between camps and any time the body stops hitting, so the pooled numbers
    run low (Vesper 0.19 pooled is interrupted clears, likely recalls). Medians are the safer read.
  - **What it means for piece 3:** the clear rate is not why the need is too high. Look at the damage side
    (DMG_X, all-awake vs real, U3.2) and at `TANK_K` / KEEP_HP before building piece 3.
- U3.2 DMG_X 0.6 was measured on half 1 only [measured, n = 179 / 430]. Start at 1.0.
- U3.3 Splash champions: `splash_m` already scales Se. Check it isn't counted twice with RATE_X.
- U3.4 KEEP_HP 0.4 and `tank_share` stay. Do solo takes at the corrected need leave bodies under KEEP_HP more
  often (recalls up)?
- U3.5 How many maps stay group maps after the correction (the mapstudy check above). If none, delete
  `group_slots` and the subs path entirely (redesign, not flags).
  - **Checked 23 Oct [measured, MAPDUMP of the 40 maps, the dump's need reproduced exactly in Python].** Groups by
    need and group maps:

    | RATE_X | need 1 | 2 | 3 | 4 | 5 | 6 | group maps | S+1 groups |
    | --- | --- | --- | --- | --- | --- | --- | --- | --- |
    | 1 (today) | 440 | 83 | 125 | 71 | 60 | 57 | 35/40 | 114 |
    | 1.25 (fitted, U3.1) | 464 | 79 | 131 | 45 | 77 | 40 | 35/40 | 97 |
    | 2 | 464 | 174 | 59 | 88 | 28 | 23 | 35/40 | 54 |
    | 3 | 523 | 151 | 86 | 42 | 11 | 23 | 31/40 | 40 |

    - Even at 3.0 only four maps leave (00gem-fields, 01concentrated-wealth, 01starfish, 01yellow-brick-road).
      00lanes, 00lost-world and 00quadrants are not group maps at either rate.
    - Maps stay group maps mostly through `ggems ≥ 0.7`, not `solo ≤ 0.4` (01elk-arena: solo 0.97 but ggems
      1.0). So `group_slots` can't be deleted, and piece 3 has to rethink the `ggems` test itself.
- U3.6 The boot fallback (no record) uses HP 1000. Replace it with the body's own max HP when building.

### 3.6 Re-looked (23 Oct): results [measured]

**Verdict: piece 3 is not built. The need is right where it is; every way of moving it lost.** `bots/cpp` stays the
§2.7 build (J0 re-run 45W/35L, the same as before). Judged over 8 jitters against that build's 59.1 % (§9).

**The damage side (U3.2), measured.** The clear trace now logs the body's HP at the first hit and at the end, the
model's `finish_dmg` for k = 1 (`pred`), the raw `clear_model` damage (`raw`) and `need_k_r9` (TRACE only,
`beh.cpp:183`). Traced arena of the §2.7 build, 80 games, 7,620 clears; 1,285 solo (no ally within 4), no enemy in
sight, uninterrupted:

| | n | lost ÷ raw, p50 / p75 / p90 | lost ÷ pred, p50 | end HP ÷ max, median |
| --- | --- | --- | --- | --- |
| all | 1,249 | 0.54 / 0.66 / 0.80 | 0.73 | 0.82 (none below 0.4) |
| Ryth | 220 | 0.44 / 0.52 / 0.60 | 0.55 | |
| Vesper | 142 | 0.72 / 0.86 / 1.05 | 0.57 | |
| Vendetta | 164 | 0.64 / 0.75 / 0.86 | 0.77 | |
| Ren | 298 | 0.63 / 0.71 / 0.84 | 0.74 | |
| Varg | 425 | 0.42 / 0.54 / 0.63 | 1.14 | |

- So all-awake overstates a finished solo clear's damage about 2× (0.54), in line with F6's 0.6. But the sample is
  survivor-biased: it holds only clears that finished with no enemy near, and only 14 come before r150.
- On the 40 maps (MAPDUMP, the record's need in Python): DMG_X 0.6 cuts S+1 groups 114 → 67 and need-1 barely moves
  (440 → 464). **Group maps stay 35/40 at every DMG_X and TANK_K tried** (mean ggems 0.88 → 0.86): most gems sit in
  groups one body can't take at base stats, whatever the damage.

**The builds (8 jitters each, 640 games, vs `cpp-port`):**

| Build (on §2.7) | Win % | Margin | Deaths / kills / lost | Collected by r300, bodies by rank |
| --- | --- | --- | --- | --- |
| **§2.7 (kept)** | **59.1** | **+49** | 11.6 / 12.4 / 103 | 64 / 29 / 11 / 5 / 2 |
| DMG_X 0.6 in `clear_model` (every caller) | 55.9 | +47 | 12.2 / 11.8 / 118 | 62 / 29 / 12 / 6 / 2 |
| DMG_X 0.6 on the live take test only (`finish_dmg`) | 51.6 | −10 | 12.9 / 10.6 / 123 | 58 / 28 / 12 / 6 / 2 |
| live damage × 1.25 (the other way) | 53.9 | +21 | 11.4 / 12.3 / 102 | 63 / 28 / 12 / 6 / 2 |
| `GROUP_UNTIL` 300 → 200 | 54.2 | +14 | 12.4 / 11.2 / 109 | 60 / 27 / 12 / 6 / 2 |
| `GROUP_UNTIL` 300 → 100 (no stack after the opening) | 56.1 | +31 | 12.0 / 11.2 / 93 | 56 / 26 / 12 / 5 / 2 |

**What it means:**

- **Lowering the need gets bodies killed.** With the measured damage, bodies solo more, and deaths rise 11.6 → 12.9
  and gems lost 103 → 123. What the model's all-awake damage really pays for is the enemy who arrives mid-clear,
  which the clean sample leaves out. The margin it leaves is exposure, piece 5's job, not the need's.
- **Raising it loses too** (53.9 %). So ×1.0 is a local best; there is no RATE_X or DMG_X to build.
- **Bodies 3–5's low collection is not the lever here.** It is 12/6/2 by r300 in every build, with stack mode to
  r300, to r200, or with no stack mode at all. It comes from the carry rule (one body captures; rotating it lost,
  §2.7), not from the need or the crews. The ladder gap F4 is real, but in this arena spreading the takes costs
  more in deaths than it brings.
- U3.3–U3.6 are moot without a build. U3.6 (boot HP 1000) only matters with no draft record, which never happened
  on the 40 maps.

**Next is piece 4 (the capture guard) or piece 5 (exposure).** Every loss here ran through deaths, so piece 5 is
the better bet: price the leg's danger instead of keeping a high need as a blanket margin. Once exposure is priced,
re-test DMG_X 0.6, which could pay then.

## 4. The capture guard (P13 forage on the enemy)

### 4.1 The gap

F8: what gets cleared is not always ours. They capture 57 % of contested lives to our 41 %, and steal 123 cleared
groups to our 72.

### 4.2 Current code [code]

- **The Reward price is flat.** `value / div / (walk + 5) · REWARD_X` (`prices.cpp:250`). It ignores how far the
  capture has got.
- **Non-carries leave at once** at the Reward state (`handoff`, `beh.cpp:209–216`). They don't wait for the carry
  to reach a spawn tile, and they leave even if an enemy is close.
- **Reward groups are missed as candidates.** The candidates are near6, the current target and live groups seen
  (`price_all`). A group seen in the Reward state (cleared by someone, not captured) is a candidate only if it is in
  near6.
- **Enemies at our capture are priced as any enemy.** An enemy coming to our capture prices as an ordinary kill.
  The reward it would reset (R1) is not counted.

### 4.3 Design

**The Reward price counts progress:**

```
value / div / (walk + max(1, CAPTURE_TIME − stood)) · REWARD_X
```

- `stood` = rounds of our team's capture so far: our own `ST.capt` rounds, or an ally on a spawn tile in vision.
- The last rounds of a capture are worth the most, and HYST then holds them.

**A non-carry leaves only once an ally is on a spawn tile of g.** Until then it walks to the spawn tile itself.

- No round goes by with nobody capturing.
- It covers the rotation mismatches from 2b.

**Guard when an enemy is near.**

- An enemy is within GUARD_R [guess 4] of the group's spawn tiles while our capture runs.
  - The non-carries stay on the **Ring**, not on a spawn tile (U2.8 on whether that splits the reward).
  - The kill price of that enemy adds the group's reward value: if it reaches the region, the capture resets (R1),
    so killing or holding it saves the reward.
- The duel P(lose) and dcost still gate the fight (08 F2).
- With no enemy near, the non-carries leave as soon as the carry stands.

**Steal what is lying there.**

- Groups seen in the Reward state within REWARD_SEEN [guess 10] rounds join the FARM candidates.
- If an enemy is capturing (on a spawn tile in vision), walking into the region resets its progress (R1).
  - So the option is priced as the Reward price minus the leg's exposure (piece 5).
  - Until piece 5 is built, the current kill and plose gates decide.

**Hold a capture at low HP when no monster is left.**

- A capture with no live monster and no enemy within reach is not dangerous.
- The heal price must not pull a capturer off it in its last rounds.
- Check how heal and recall preempt Farm in `upd_decide` when building: heal at the first losing hit (08 F3)
  should not fire with no damage source.

### 4.4 What it should do to the numbers

- Our steals: 72 → toward 123.
- Contested captures: 41 → toward 57 %.
- Captures reset or abandoned by us: a trace count, which should fall.
- Watch: deaths at a guard (a guard is a fight).

### 4.5 Unknowns to check when building

- U4.1 GUARD_R 4 [guess] and REWARD_SEEN 10 [guess].
- U4.2 U2.8: does a Ring guard count as "present" and split the reward?
- U4.3 Whether an enemy standing in the region resets our progress even if our carry stays (R1 "admitting an enemy
  resets progress"), so a guard's job is to keep it out. Check how far "the region" reaches.
- U4.4 How often we leave a capture for heal or recall today (trace: capture abandoned with HP < KEEP_HP and no
  monster alive).
- U4.5 Whether Reward groups seen should also be shared. There is no byte for it; skip unless steals stay low.

### 4.6 Built (23 Oct): results [measured]

**Verdict: piece 4 is kept in its smallest form (C). The body that is capturing stays on the spawn tile, and a
non-carry leaves only once an ally stands on a spawn tile.** Over 22 jitters vs `cpp-port`, C wins 59.2 % (1042 of
1760, margin +71) and the §2.7 build 57.2 % (1007 of 1760, +48). The capture delay p90 drops from 15 to 9 rounds.
Deaths, rollovers and faults are flat or down. The progress price, the steal candidates and the guard all lost and
are dropped. Their diffs against the §2.7 build are `docs/redo/patches/ROUTING_P4_{A,B,D,E}.diff`. The ladder zip
is `submissions/cpp-p4.zip`, source only.

**What C changes (no new work on every `price_all`; a few tile compares, only for a cleared target):**

- **`farm()` at Reward** (`beh.cpp:253`). A body leaves a cleared group only if an ally stands on one of its
  spawn tiles (`allies_on_spawn`). It needs `handoff` (it is not the carry), or it is off the tiles while allies
  hold every one of them. Before this, non-carries left at once, and the region emptied whenever the carry was
  still walking.
- **The lower-slot claim** (`price_all`, `prices.cpp:358`). It no longer takes g from a body capturing it alone
  (`lone_capture`, `prices.cpp:235`: my target, Reward, I am on a spawn tile and no ally is). In the §2.7 build the
  claim pulled the lone capturer off when a lower slot claimed the group. That emptied the region and reset the
  timer.

**U4.3, answered [measured, 6 replays, before building].** The region is the spawn tiles. An enemy 1–3 tiles away
never reset a capture. Our own step-offs were about 2/3 of our resets. So the guard in §4.3 (hold the Ring, kill
the enemy before it reaches the region) defends against a reset that only happens when the enemy stands on a tile.

**The builds** (vs `cpp-port`; "orig" is the §2.7 build's own 8 jitters, J 0 300 700 1500 100 500 1000 2500;
captures from `tools/capstats.py`, per game, us / them):

| Build | Jitters | Win % | Margin | Deaths / kills / lost | Steals | Their clears | Delay p90, > 10 r | Rollovers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| §2.7 (kept) | orig 8 | 59.1 | +49 | 11.6 / 12.4 / 103 | 1.59 / 1.77 | 66.9 | 15, 15.4 % | 6.49 |
| A: as designed (progress price, REWARD_SEEN candidates, Reward groups take one body, heal hold, no timeout while capturing) | orig 8 | 49.1 | −30 | 13.4 / 10.6 / 127 | 2.12 / 1.26 | 70.8 | 9, 7.9 % | 6.32 |
| B: Reward groups take one body (the claim also at Reward), the capturer exempt, + the leave rule | orig 8 | 53.3 | +21 | 12.5 / 10.4 / 123 | 1.81 / 1.57 | 69.5 | 9, 8.8 % | 6.23 |
| B1: the leave rule alone | orig 8 | 58.9 | +74 | 11.2 / 12.0 / 115 | 1.87 / 1.73 | 68.1 | 12, 10.9 % | 6.58 |
| **C: the leave rule + the lone capturer exempt from the claim** | orig 8 | **59.1** | **+77** | 11.4 / 11.7 / 101 | 1.80 / 1.60 | 68.4 | **9, 7.9 %** | 6.59 |
| D: C + Reward groups seen ≤ REWARD_SEEN 10 rounds as candidates | 14 | 54.6 | +17 | 12.5 / 11.1 / 114 | 1.88 / 1.49 | 69.8 | 9, 8.2 % | 6.68 |
| E: C + the guard (GUARD_R 4: hold off the tiles; the enemy's kill price + the reward) | 14 | 57.1 | +34 | 12.1 / 11.3 / 109 | 1.88 / 1.61 | 68.9 | 9, 7.8 % | 6.62 |
| C vs the §2.7 build, both on the same fresh sets: 6 (J ≤ 2000) and 8 (J 150 … 1700) | 14 | 59.3 / 56.3 | | | | | | 6.1 / 6.2 |
| **C vs the §2.7 build, all 22 jitters** | 22 | **59.2 / 57.2** | **+71 / +48** | 11.4 / 11.8 deaths | 1.82 / 1.62 | 68.7 / 67.0 | 9 / 15 | 6.37 / 6.44 |

C beats the §2.7 build on every set: orig 59.1 = 59.1 (margin +77 vs +49), fresh 6 57.9 vs 56.2, new 8 60.3 vs
56.4. Faults: 0 in 1,760 games.

**What it means:**

- **The progress price outbids the fights (A).** At `max(1, 5 − stood)`, the last rounds of a capture were worth up
  to 5× the flat price. They outbid kill and heal (kills 12.4 → 10.6, deaths +1.8). They also raised `rawb` and so
  the death cost. A captured faster (p90 9) and stole more (2.12), but lost the game.
- **"A capture needs one body" ties bodies up (B).** Exempting the capturer from the claim at every Reward group
  held it there for good. The other team cleared more (66.9 → 69.5), so the gain went to them. C only exempts a
  capturer who is alone, and only until an ally stands. This keeps the handoff that the claim was doing. The claim
  was not a bug: it is how the crew moves on.
- **The steal candidates (D) and the guard (E) lose.** D's steals rise only 1.80 → 1.88 and its deaths rise by 1.1.
  Walking into an enemy's half-done capture is a fight we price badly. E's guard holds bodies near enemies (deaths
  +0.7). Since an enemy only resets a capture from a tile (U4.3), standing guard buys little.
- **Per-map outcomes are near-fixed per build, and a small change flips them [measured].** Over 22 jitters, C vs the
  §2.7 build (wins of 44):
  - Worse: 00packs 5 vs 31, 01hooks 13 vs 36, 00rows 11 vs 25.
  - Better: 00elkring 40 vs 16, 00fragment 36 vs 22, 00interlock 41 vs 30.
  - D, one line apart from C, wins 00packs-B 14 of 14, and C wins it 1 of 22.
  - In C's 00packs-B game, the two builds' games split at r22: C's first capture finishes 2 rounds sooner, so the
    capture works as intended. The loss comes at r147, when our Vesper walks into theirs with a 58-gem bag (a walking
    death, piece 5's ground).
  - So these maps are snowballs that tip on any change. Fuel jitter barely moves them, so a set of 8 jitters
    under-states how much a build's result moves. Judge on 14 or more jitters, compared on the same sets, and don't
    chase single maps.
- **Fuel:** rollovers are flat (6.37 vs 6.44 over 22). The new work is a few tile compares, only for a cleared
  target.

**Unknowns closed:**

- U4.1: REWARD_SEEN and GUARD_R are not kept (D, E lost).
- U4.2 / U2.8: not measured. The guard is gone, so no Ring body waits at a capture. U4.3 puts the region on the
  spawn tiles for resets, and the reward split is assumed to use the same region [guess].
- U4.4: A's heal hold went with A. Not traced on its own.
- U4.5: no (steals did not stay low enough to need a shared byte).

## 5. The exposure price (P3 unbeatable first, P8 avoid strength, P9 attack where they are not)

### 5.1 The gap

F9: we die walking, to champions, 3.5× as often. Being alone is not the difference. The route walks bags past
enemies.

### 5.2 Current code [code]

- **Danger is one flat number.** `P = P_NEAR 0.5` if the nearest visible enemy is within 8, else 0
  (`prices.cpp:301`; "the danger grid is not ported: 0 [deviation]"). P is used in two places:
  - the farm risk `P·bag` (`prices.cpp:262`);
  - the bank `(1+P)` (`prices.cpp:363`).
- **The bank price is also damped near enemies:** ×`sig((near_e − 4)/1.5)`.
- **Out of vision means safe.** An enemy out of vision counts as 0 danger. Enemy memory keeps 10 slots for MEM_FIGHT
  6 rounds (`memory.h:42`), and only for the fight estimate.
- **Team signals:** the sighting bytes (≥ 2 enemies near altar a, with an age) and the death mark (group mi, coarse
  round, which excludes that group, `s.dead_g`).
- **Units are mixed.** The farm risk subtracts gems from a price in gems per round, so P·bag acts as a veto within
  8 tiles of an enemy, and is nothing beyond that.

### 5.3 Design

**A leg's exposure is the expected gems lost on the leg me → target T:**

```
risk(leg) = EXPO_X · Σ_e  exp(−age_e / τ) · [dist(e, segment me→T) ≤ EXPO_R] · plose_e · dcost
```

- **The enemies:** the remembered ones, plus each fresh sighting (counted as 2 enemies at altar a, with its age).
  - Memory keeps its 10 slots for up to EXPO_AGE [guess 30] rounds for this use.
  - The fight estimate still uses only enemies ≤ MEM_FIGHT old.
- **`dist(e, segment)`** is the Chebyshev distance from the enemy's last tile to the straight segment.
  - It is cheap, with no field.
  - The real path bends, so this is a proxy [guess].
- **`plose_e`** is the `duel` P(lose) of me against that enemy's champion (08 F2), with its known stats.
- **`dcost`** is the death cost already in `price_all` (`prices.cpp:462`):
  `min(DCOST_CAP, DEATH_OUT·max(rate, MY_RATE)) + bag`.

**Prices in one currency.** The risk comes out of the value, not the rate:

```
farm:  (value − risk(me→g))                     / (walk + wait + clear + 5)
bank:  (bag − risk(me→a))                       / (added·bank_ret + chan)
wait:  the leg's risk + standing risk at the Ring = risk with the segment collapsed to the Ring, × wait / τ
```

- With no enemy remembered near the leg, `risk = 0` and the price is pieces 1–4's.
- Piece 1's respawn wait is priced here.

**Delete:**

- `P_NEAR` and `s.P` (`prices.h:13`, `prices.cpp:301, 330`).
- The `P·bag` farm risk; the `low ? bag` branch stays (low HP after the clear is a different risk).
- The bank's `(1+P)` and `sig(near_e)`.
- `bank()`'s hard fail (`near_e ≤ 3 && bag > 10`) stays: it is a reflex, not a price.

**No "alone" term (F9).** The death mark stays as it is.

**Fuel:** at most 10 enemies × ~10 options × one segment distance a turn. That is trivial.

### 5.4 What it should do to the numbers

- Deaths a game: 17.5 → down.
- Share of deaths while walking: 82 → toward 47 %.
- Gems lost: 79 → toward 27.
- Dead trips.
- **Takes must not fall.** Exposure that empties the map of options is a loss.

### 5.5 Unknowns to check when building

- U5.1 τ [guess 15] and EXPO_AGE 30: how long a sighting predicts an enemy's area.
- U5.2 EXPO_R [guess 8], the old P_NEAR radius.
- U5.3 EXPO_X [guess 1.0]: the right scale is unmeasured (REPLAYS §7). One constant, tuned in one sweep of 2–3
  values.
- U5.4 The straight-segment proxy vs the real path on maps with walls: compare on the 5 most walled maps.
- U5.5 Whether `duel` runs cheaply for remembered enemies whose HP is stale: use the last seen HP, or full HP when
  older than MEM_FIGHT.
- U5.6 Whether the flat P was doing work in the bank price that the leg risk misses (enemies at the altar). The
  sighting bytes cover the altar case.

### 5.6 Built and tested (23 Oct): results [measured]

**Verdict: piece 5 is not kept. Every form lost to the §2.7 build and deaths never fell. The null test (G: the kept
play plus only the machinery's fuel) scores the same as the best form, so the price itself adds nothing measurable.**
`bots/cpp` is back to the §2.7 build (byte-exact: its source hash re-hits the kept 8 runs' cache). All variants are in
`docs/redo/patches/ROUTING_P5_exposure.diff` (part 1: F against the kept build; part 2: A's `prices.cpp`).

**What was built (all variants share it):**

- `SeenEnemy` keeps type, HP, Strength, focus and range; memory keeps its 10 slots for EXPO_AGE 30 rounds, and a new
  sighting overwrites the oldest slot. Only Nav read `en` (≤ MEM_NAV 2 rounds old), and 5 enemy ids never fill 10
  slots, so at EXPO_X 0 (row G) the play is the kept build's; only the fuel differs.
- `leg_risk(a, b)`: for each threat, the exact Chebyshev distance to the segment (candidate t's: the ends, each
  term's zero, the equal-term points); within EXPO_R 8, `exp(−age/τ) · plose · XD`, with `plose` from the duel's x
  (08 F2) and `XD = EXPO_X · (min(DCOST_CAP, DEATH_OUT·max(rawb, MY_RATE)) + bag)`. The wait at the Ring adds
  `leg_risk(anchor, anchor) · wait/τ`.
- Threats are remembered enemies (age 1–30) and the sighting bytes' extras (base stats, count k, at the altar).

**The builds (8 jitters each, 640 games, vs `cpp-port`; rollovers by `fuelExhausted` entries a game):**

| Build | Win % | Margin | Deaths / kills / lost | Banks, first bank | Rollovers |
| --- | --- | --- | --- | --- | --- |
| **§2.7 (kept)** | **59.1** | **+49** | 11.6 / 12.4 / 103 | 27.4, r144 | 6.49 |
| A: as designed (P_NEAR deleted, risk out of the farm and bank value, me alone, EXPO_X 1.0) | 37.5 | −148 | 11.7 / 10.6 / 92 | 20.0, r210 | 7.40 |
| B: A at EXPO_X 0.3 | 49.5 | −27 | 12.0 / 11.3 / 126 | 24.0, r180 | 7.65 |
| C: B on farm legs only; bank keeps the flat `(1+P)` and `sig(near_e)` | 48.6 | −27 | 12.9 / 11.0 / 118 | 25.6, r162 | 7.48 |
| D: flat P kept everywhere; exposure from out-of-vision memory and sightings on farm legs, 0.3 | 49.5 | −17 | 12.7 / 11.1 / 112 | 26.6, r153 | 7.99 |
| E: D, and the death cost reads the risk-free farm price (no rawb → dcost → risk loop) | 51.9 | −3 | 13.0 / 10.9 / 105 | 26.4, r156 | 7.25 |
| F: E, with crew vs cluster (k = the take's bodies at the target, 1 on the way; enemies within LANCH_R summed) | 49.1 | −30 | 12.9 / 10.6 / 113 | 26.2, r156 | 7.32 |
| G: F at EXPO_X 0 (null test: the kept play + the machinery's fuel) | 51.9 | −4 | 12.7 / 11.0 / 114 | 26.9, r146 | 7.42 |
| §2.7 (kept) re-run on 8 fresh jitters (J 200 … 4000) | 50.9 | −11 | 12.8 / 11.1 / 109 | 25.8, r153 | 9.35 |
| the same, the six with J ≤ 2000 | 56.3 | | | | 6.15 |

**How much fuel the kept build can spare [measured].** Rollovers and wins of 80 by a flat burn of J loop steps at the
start of every play turn:

| J | 200 | 400 | 600 | 800 | 1200 | 2000 | 3000 | 4000 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rollovers / game | 4.25 | 4.08 | 5.60 | 5.09 | 7.10 | 10.80 | 16.12 | 21.75 |
| wins of 80 | 46 | 44 | 45 | 42 | 50 | 43 | 37 | 19 |

**What it means:**

- **The flat P does real work (U5.6, answered: yes, in both prices).** Deleting it (A, B) made banks rarer and later
  (27.4 → 20–24, first bank r144 → r180–210) and the margin collapsed; giving the bank its flat P back (C) did not
  recover it, so the veto on farming near a visible enemy matters too. A `P·bag` veto inside 8 tiles is crude, but
  it is decisive, and a priced danger is not.
- **The price adds nothing over its own machinery.** G plays exactly as the kept build (only the fuel differs) and
  scores 51.9 %, the same as E, with the same +0.9 rollovers a game. So E's price at 0.3 is about neutral; A, B and C
  lose beyond G: deleting the flat P is a real loss.
- **Why G loses to the kept build is open.** A flat burn costs no wins up to J2000 (rollovers 4 → 11), so it is not
  the amount of fuel. Either the machinery's cost, which grows with remembered enemies and options, lands on the
  fight turns where a skipped turn hurts most [guess], or a set of 8 jitters moves more than its ± 1.4 says: the
  kept play scored 59.1 % (its set), 56.3 % (six fresh J ≤ 2000) and 51.9 % (G). Both say: judge against the same
  J set, and treat a 4-point gap as uncertain.
- **The scale (U5.3):** 1.0 is far too strong (37.5 %); 0.3 is about neutral against G. Deaths do not fall at any
  scale (11.6 → 12–13; G has 12.7 too).
- **Per map, weak evidence:** G alone swings maps as much as any variant (vs kept, wins of 16: 00packs 11 → 4,
  00fragment 8 → 14, 00contest 15 → 10), so most per-map swings are chaos. What E changes against G: worse on
  00stampede 15 → 8, 00contest 10 → 4, 00fragment 14 → 4, 00monolith 8 → 5; better on 00elkring 4 → 12, 00interlock
  11 → 16, 00packs 4 → 9, 01shortcut 11 → 15. Exposure may suit spread maps and hurt contested single-prize ones,
  where a body hesitating alone breaks the crew's commitment [guess, not traced]; F's crew-vs-cluster duel did not
  fix the contest maps (00contest 7, 00stampede 8 of 16).
- **Rollovers rise about 1 a game** in every variant and in G, on maps already heavy (01corridors 55 → 61,
  01yellow-brick-road 22 → 28): `expo_init` (an `in_vision` call per remembered enemy) and `leg_risk` per option
  (≤ 16 threats × a segment distance) on every `price_all`. §7 called this trivial; it is not.
- **U5.1, U5.2, U5.4, U5.5** are moot without a kept build. Stale HP (U5.5) was handled by full HP when older than
  MEM_FIGHT.
- **The DMG_X 0.6 re-test (§3.6) was not run:** it was to sit on a kept piece 5, and there is none.

**Lessons for piece 4:**

- **Keep the fuel flat.** Piece 4 should add no work to every `price_all` (only to the few Reward candidates, §7),
  and its rollovers must not rise; enemy-dependent work may be the kind that hurts [guess, from G].
- **Judge on the same J set** as the kept build's 8 runs, and re-run the kept build on a fresh set if a result
  lands within ~4 points.
- Contested prizes want commitment, not caution [guess]: the guard should hold the crew on the prize.
- A fuel-free exposure (threats once a turn, only for the 2–3 best options) could be re-tested later; E = G says
  it would land near neutral.

## 6. Comms

One change to the 8 shared bytes (`strat/MEMORY_LAYOUT.md`, `docs/redo/04_COMMS.md`):

| Byte | Today | After |
| --- | --- | --- |
| 0–4 | slot code (3 bits) \| target mi (5 bits). Codes: IDLE 0, FARM 1, BANK 2, KILL 3, **4 unused**, SHOP 5, JOIN 6, DEAD 7 | **4 = CAPT** (captured mi this round, held CAPT_HOLD rounds). Built 23 Oct (§1.6) |
| 5–6 | sighting | unchanged (read by piece 5 too) |
| 7 | death mark | unchanged |

- **Writing:** `Comms::encode` writes the slot byte only on change (`comms.cpp:52–56`). A capture costs two writes:
  code 4, then the next goal's code. The capturer's code for those CAPT_HOLD rounds is 4, whatever it is doing.
- **Reading:**
  - Claims count only `C_FARM` (`comms.cpp:91`, `upd.cpp:130–141`).
  - The handoff checks `C_FARM` or `C_JOIN` (`beh.cpp:80`).
  - So a slot showing 4 is no claim and no crew member, which is true after a capture.
- **The 1,024-byte draft record is unchanged.** AW is built at runtime (§2.3), and the roster's mean Strength
  (§3.3) is recomputed from the roster, or written to a free header byte if one exists.

## 7. Fuel

| Piece | New work | Cost |
| --- | --- | --- |
| 1 | `full_mons`, one more clear_model per Resp candidate, code-4 decode | trivial |
| 2 | AW: one altar field per turn until all nA are built, per body; then reads | ≤ FIELD_COST_100 31k a turn for the first nA turns [code]; nA altars on the 40 maps [check] |
| 2 | `added` per altar for one g_next | trivial |
| 2b | rotation over ≤ 5 slots | trivial |
| 3 | none (a multiply in clear_model) | 0 |
| 4 | Reward groups seen join candidates (≤ a few) | one farm_price each |
| 5 | ≤ 16 threats × every option × a segment distance | **not trivial**: +0.9 rollovers a game (§5.6) |

The ledger is the H1 one (09 §7); the C++ turn is ~100k [guess until measured]. Only piece 2's fields are worth
watching for rollovers.

## 8. What is deleted or redesigned

| Code | Where | Becomes | Piece |
| --- | --- | --- | --- |
| Resp prices 0 | `prices.cpp:237` | priced with wait rounds, WAIT_MAX 15 (**done**, §1.6) | 1 |
| Resp at arrival returns Done | `beh.cpp:207` | wait at the Ring (**done**) | 1 |
| EXCL after a handoff | `beh.cpp:215` | deleted; the timer prices it (**done**) | 1 |
| Handoff `until = r + resp` | `beh.cpp:214` | `r + CAPTURE_TIME + resp`, replaced by code 4 (**done**) | 1 |
| Altar = nearest from the body | `bank_altar`, `prices.cpp:161` | least added walk to g_next (**done**, §2.7) | 2 |
| BANK_NEAR, BANK_NEAR_BONUS | `prices.h:20`, `prices.cpp:369` | **kept**: the added-walk price lost (§2.7) | 2 |
| Farm detour term | `prices.cpp:268` | **kept**: deleting it bought nothing (§2.7) | 2 |
| Carry = main / second / lowest | `handoff`, `beh.cpp:85–88` | **kept**: rotation lost (§2.7, U2.7) | 2b |
| Str 50 inline rounds, `CHAMP_STR` | `upd.cpp:10, 25, 87` | `clear_model` with the roster's Strength | 3 |
| Rate `k·S` | `model.cpp:12` | `k·S·RATE_X`, damage ×DMG_X | 3 |
| Boot need at Str 50 / HP 1000 | `world.cpp:73` | the same `bodies_needed`, corrected inside; HP from the body | 3 |
| Fixed crew sizes 3+3 … 2+1 | `group_slots`, `upd.cpp:37–74` | the corrected need of each sub's group (deleted if no group maps remain, U3.5) | 3 |
| Flat Reward price | `prices.cpp:250` | **kept**: the progress price outbid fights (A, §4.6) | 4 |
| Non-carries leave at Reward | `beh.cpp:253` | leave once an ally stands on a spawn tile (**done**, §4.6); the guard lost (E) | 4 |
| Lower-slot claim takes a Reward group | `prices.cpp:358` | not from a lone capturer (`lone_capture`, **done**, §4.6) | 4 |
| Flat P_NEAR 0.5 | `prices.cpp:301`, `prices.h:13` | **kept**: every leg exposure lost (§5.6) | 5 |
| `P·bag` farm risk, bank `(1+P)` and `sig(near_e)` | `prices.cpp:262, 363, 365` | **kept**: deleting them lost most (A, B in §5.6) | 5 |

Kept as they are: Nav's moving layer, `ROLE_GOLD`, the shop window, the duel, HYST and `farm_hyst`, the claims,
`GROUP_BANK_BAG` (until U3.5 says whether stack mode is still live), the death mark, `bank()`'s reflexes.

## 9. Build order and test plan

**Order:** 1 → 2 + 2b → 3 → 4 → 5, one session each (2 and 2b together: a body that banks needs a bag).

- Respawn timing is first: it is the clearest gap (F1), and it touches the fewest prices.
- The need is third, though it may be the largest change. It changes crews and stack mode, so it is easier to read
  after the route legs are in.
- The two checks with no bot code (U3.5 mapstudy and the RATE_X fit from piece 1's traces) can run in piece 1's
  session.

**Before piece 1:** run `cpp` vs `cpp-port` once unchanged, for the noise floor (the two bots are the same today).

**Each piece is judged the same way:**

1. **The bar.** `python3 -I tools/arena.py cpp cpp-port --jobs 2`: 40 maps, both sides, 80 games. It stays if it
   wins more than it loses (`CLAUDE.md` rule 5), worst map included. Otherwise it is scrapped; git holds it.
   **From piece 2 (23 Oct): over 8 jitters, against the previous build's 8.** One run moves by ±5 wins on any change.
   `sh tools/jitter.sh cpp` runs 8 copies that burn J loop steps a play turn (J = 0 300 700 1500 100 500 1000 2500;
   copies in `bots/_cpp_jJ`, delete after) and prints the total with `tools/jitter_sum.py` (win % ± SE, margin, the
   bank measures). About 6 min. It stays if it beats the bar over the 8 jitters and is not behind the previous
   build; a difference under about 2 points (one SE of a 640-game total) is noise, and then the simpler build stays.
   [measured: `cpp-port` vs itself over 7 jitters 49.8 %]
   **From piece 4 (§4.6): per-map outcomes are near-fixed per build and flip on small changes**, so 8 jitters
   under-state a build's spread; use 14+ jitters and compare builds on the same sets.
2. **Its own measures** (§1.4, §2.5, §3.4, §4.4, §5.4) must move toward theirs.
   - The arena saves replays in `runs/arena/<A>-vs-<B>-<time>/` [code, QUICKSTART].
   - Run the farm scripts there (`tools/replay/farm/`: `farm.py`, `order.py`, `legs.py`, `phase.py`, `hpb.py`) with
     our bot as team A or B. [measured, piece 1] They run on arena replays: decode each game, then
     `flip.py DEC --arena OUT` puts our bot on team A (the side comes from the `-A`/`-B` folder name).
     `farm.py` keys a game by the first 8 characters of its file name, so give it copies named with unique
     8-character ids (`g0000001.json`, ...); `order.py` reads the flipped files as they are.
     `sh tools/replay/farm/arena_decode.sh runs/arena/<run> W` does all of it (~30 min for 80 games;
     `tools/replay/farm/README.md`).
   - `tools/navstats.py` and `tools/microstats.py` cover traces, deaths and fuel.
3. **Faults 0, rollovers not up** (`keep-micro-simple`).

**Ship:** a ladder zip only after a piece beats the bar and its measures moved. Then tell the teammate (the
teammate TLDR).

## 10. All unknowns, collected

| # | Unknown | Start value | Check |
| --- | --- | --- | --- |
| U1.1 | CAPT_HOLD, missed reads on rollovers | 2 rounds | **done** §1.6: ≤ 14 % missed, dead bodies included |
| U1.2 | timer off-by-one (`+1`) | as now | **done** §1.6: +1 removed, 97.7 % exact |
| U1.3 | groups with mi ≥ 31 (no code 4, no claims) | existing limit | **done** §1.6: 50 of 836 groups, 5 maps, 3.3 % of gems |
| U1.4 | does crossing a spawn tile delay a respawn | Nav avoids | **done** §1.6: only standing there at the respawn round |
| U1.5 | waiting costs takes elsewhere | no cap | **done** §1.6: it did; WAIT_MAX 15 built |
| U1.6 | walk_w on waiting | no | — |
| U1.7 | enemy captures known only in vision | fine | — |
| U2.1 | AW fuel per body | runtime, one altar a turn | **done** §2.7: rollovers not up (6 most-altar maps 5.9 → 4.5) |
| U2.2 | field noise in `added` | clamp 0 | **done** §2.7: same roots and graph as F_me |
| U2.3 | g_next = held target or best candidate | held, else best | built; not swept |
| U2.4 | tiny banks | none | n/a: price unchanged (§2.7) |
| U2.5 | bag at death after deleting the detour | — | **done** §2.7: detour kept |
| U2.6 | CAPTURE_TIME, EMBLEM_GOLD | from SDK | scrapped with 2b |
| U2.7 | rotation vs split | rotation | **done** §2.7: rotation loses (gold concentration wins fights); split not tried |
| U2.8 | is the Ring "the region" (R2) | spawn tiles only | moot: no Ring guard kept (§4.6); spawn tiles for resets (U4.3) |
| U3.1 | RATE_X per champion / item level | 3.0 | **done** §3.5: ~1.25 per base Str at the start, ~1 per `s.S`; 3.0 refuted |
| U3.2 | DMG_X | 1.0, test 0.6 | **done** §3.6: solo clears lose 0.54× all-awake (survivor-biased); 0.6 lost (55.9 / 51.6 %); stays 1.0 |
| U3.3 | splash counted twice | — | check `splash_m` |
| U3.4 | KEEP_HP with the new need | 0.4 | recalls |
| U3.5 | group maps left after the correction | — | **done** §3.5, §3.6: 35/40 at the fitted rate, at every DMG_X and TANK_K |
| U3.6 | boot HP 1000 | body's max HP | — |
| U4.1 | GUARD_R, REWARD_SEEN | 4, 10 | **done** §4.6: both lost (E 57.1 %, D 54.6 %), not kept |
| U4.2 | Ring guard splits the reward | — | moot (§4.6) |
| U4.3 | how far "the region" reaches for a reset | — | **done** §4.6: the spawn tiles; enemies 1–3 tiles away never reset |
| U4.4 | captures abandoned for heal today | — | not traced; A's heal hold lost with A |
| U4.5 | share Reward sightings | no | no (§4.6) |
| U5.1 | τ, EXPO_AGE | 15, 30 | moot: piece 5 not kept (§5.6) |
| U5.2 | EXPO_R | 8 | moot (§5.6) |
| U5.3 | EXPO_X | 1.0 | **done** §5.6: 1.0 37.5 %, 0.3 49.5 %; both lose |
| U5.4 | segment proxy on walled maps | — | moot (§5.6) |
| U5.5 | duel on stale enemies | last seen HP | built as full HP past MEM_FIGHT; moot (§5.6) |
| U5.6 | flat P's altar role | sightings | **done** §5.6: the flat P works in both farm and bank |
| — | farm scripts on arena replays | — | **done** §9: `flip.py --arena`, unique ids for `farm.py` |
| — | C++ fuel per turn | ~100k | ledger |

Still open from REPLAYS §9 and MAPS §11, and not needed by this design: opponent names and top-5 status (the user
dropped it, 22 Oct), why half 2 has half the deaths, and Q5–Q10 on our own games (the measures above answer
most of them as each piece is built).

## 11. Principles (`docs/ART_OF_WAR.md`)

| Piece | Principle | In code |
| --- | --- | --- |
| 1 Respawn timing | P14 first to the field, P15 timing | `// P14: be at the camp when it returns` |
| 2 Bank leg | P12 speed and tempo | `// P12: bank on the way, not as a trip` |
| 2b Every body captures | P19 unity (the whole army fed) | `// P19: rotate the carry` |
| 3 Corrected need | P1 calculate, P5 know yourself | `// P5: our real clear rate` |
| 4 Capture guard | P13 forage on the enemy | `// P13: take what is cleared` |
| 5 Exposure | P3 unbeatable first, P8 avoid strength, P9 attack where they are not | `// P8: don't walk the bag past them` |
