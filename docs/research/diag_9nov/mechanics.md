# Engine mechanics we can exploit or use better (9 Nov, agent)

Sources: GameRules.md end to end, sdk/cpp/cambc.h end to end, bots/tz/src grepped, the engine's own tables (a
settings / item dump probe), and four two-team local experiments (`bots/_mpA` v `bots/_mpB`, 02fields; deleted after).
Replay counts come from the decoded band sets `top_v_band` (119 games, the top teams v the band) and `tz126_big` (150,
tz-126 v the band), with each local map's bushes and camps dumped from the engine (all 269 games matched a local
map). Tags: [rules] GameRules.md, [sdk] cambc.h or the engine tables, [measured] probes or replays, [guess].

## 0. Engine numbers (dumped from `game_settings` and `item_type::info()`) [sdk, measured 9 Nov]

capture 5 rounds, camp sleep 2, respawn 60, recall 5, tribute = max(1, ceil(0.1 x bag)), tribute range 1 (Chebyshev),
max rounds 2,000, win 1,000, kill gold 100, **assist gold 0, passive gold 0, spawn healing 1.0 (full HP each turn
end on spawn)**, 1 ward, ward recharge 10, ward lifetime -1 (permanent), ward vision 6, placement 2, lock hits 5,
crystal channel 3, shared memory 8 bytes, draft memory 1,024 bytes, collision reveal 1 round. Both consumables cost
10 gold, carry 1.

Emblem passives. Magnitudes come from the engine and the wording from the visualiser's own `itemPassiveDescription`:

| Family | Passive [sdk] | tz uses |
| --- | --- | --- |
| Monster | +15 % monster damage (rules say 10) | item lines |
| Durability | 10 % less damage from all sources | supports (eco 2 / dur) |
| Treasure | +10 % gold (rules say 20) | some lines |
| Jungle | 30 % less damage from monsters | lines |
| Home | 50 % shorter recall (5 -> 3) | no |
| **Tribute** | **33 % shorter tribute channel** (rounded up, min 1) | **no** |
| Capture | captures in **3** turns instead of 5 | Vesper only (`cap_emb`) |
| Prospector | +25 % of your share of cluster rewards | first emblem |
| **Hunter** | **+50 gold per champion kill** | in tables 0 / 1 only |
| **Skirmish** | **+10 % damage to champions** | **no** |
| Collectors | +1 % damage per unique emblem family owned | table 1 only |
| Power / Bruiser | 6 shards / 5 + 1 + 1 for 5 | lines |
| **Greed** | shards are plain (30 gold, 1 shard); **25 combine into a 40-shard emblem** (750 gold -> +15 free shards) | **no** |

## 1. Every mechanic, and whether bots/tz uses it

| Mechanic | Rule | tz |
| --- | --- | --- |
| Camp targeting | the nearest champion **of either team** in range, whoever hit it [rules + **measured**, §2.1] | threat model assumes every awake camp hits every tile in range (`camp_dmg_at`, `reach_count`) |
| Camp sleep | awake while **any champion is in range**; sleeps 2 rounds after the last one leaves, damage or not [**measured**] | camp_path BAD tiles; `stuck_rounds` |
| Camp HP | no regen observed while asleep; a dead member stays dead until the group is captured [measured, 02fields] | ok |
| Respawn | timer counts down after the capture; **an occupied spawn tile freezes it at 0 indefinitely; the group appears the round after the tile is vacated** [rules + **measured**, §2.3] | explicitly avoided (`act_farm` WAITR: "never on a spawn tile") |
| Capture | 5 rounds uncontested (3 with Capture); any enemy on the region resets it; the reward is split, lowest ID gets the remainder [rules]; `capture_state()` shows ally / enemy / contested **without seeing the champion** [sdk] | world.cpp contested only |
| Last hit | gives nothing on camps (the capture is by occupancy); champion kill = bag + 100 gold (+50 Hunter); a camp kill destroys the bag [rules] | priced |
| Bush | from outside you cannot see in; **a champion in a bush who attacks stays invisible to its victim** (30+ hits, never seen); **a ward placed in the bush reveals it** [**measured**, §2.2]; camps see through bushes [rules] | bushes only as a tie-break in two step scores; no reactive ward, no bush positions |
| Hidden blocker | a move onto an unseen occupant returns false, reveals the tile for the round, keeps the allowance [rules] | handled (`step_field`) |
| Wards | permanent, personal vision (not shared), one per body, recharge 10, place within 2 [sdk] | `maybe_ward` toward the farm group |
| Turn order | **champion by champion, alternating teams (A0 B0 A1 B1 ...), the starting team swaps every round** [rules + **measured**: `has_completed_turn` of the facing Tavi alternated 1 / 0 by round; Marcella (slot 0) was always done before slot 2]; `set_priority` reorders within a team from the next round [rules] | `prio_fight` exists, off |
| Spawn | full heal every turn end; enemies cannot step on it; dead bodies shop [sdk / rules] | `home_farm`, shops when dead |
| Recall | 5 ticks, cancelled by damage or stun; one start + one cancel a turn [rules] | pre-recall spam (`pre_recall 1`), `dth 2` |
| Tribute | duration from the bag at start, **completion tributes the whole bag then** (captures land first); stun / death / new lock cancel it, damage does not [rules] | banking; `tdeny` (locks) tested, lost |
| Altar lock | 10 gold; placed within 2; cancels channels there; 5 hits clear it; tributing at it becomes attacks on it [rules] | buys one; pre-emptive / intercept variants lost on the band |
| Crystal | 3-tick channel, then a 3-tile hop ignoring terrain; damage does not stop it, stun does [rules] | never bought (top 5.4 a game) |
| Dash | 2 steps along a legal path, **crosses holes** [rules] | fights / `dash_field` |
| Vendetta | any credited kill, **camps included**, resets both cooldowns [rules / sdk] | not used for camp last hits |
| Fuel | 100k a turn; **the first draft turn gets 100x (the SDK says 100x, the rules 10x)**, a champion's first turn 2x; a suspended bot resumes next round [sdk] | the draft writes **no draft memory** |
| Game end | 1,000 tributed wins at once; at r2000 tributed, then lifetime gold, then kills, then Team B [rules] | `winning_gems` in pricing |

## 2. Ranked: exploitable or under-used

### 2.1 Camps hit the nearest champion of either team, and stay awake while anyone is in range [measured]

**Probe** (02fields; A = team A, B = team B):
- A's Marcella stood next to a wolf at (21,29).
- B's Vesper stood 3 tiles from it, inside wolf range 3, and hit it 6 times.
- Vesper took 0 damage. Marcella took 20 a round.
- In a second run B's last hit was at r43 and B then walked away. Marcella, who never hit the camp, kept taking 20 a
  round from r41 to r96 and died to it. A camp kill destroys the carried gems [rules].
- So "wakes until no damage for 2 turns" (one rules sentence) is wrong. The SDK's "rounds without an in-range champion"
  is right.

**What tz does:**
- Every awake camp counts against every tile in its reach: `camp_dmg_at`, `camp_exit_at`, `build_cthreat` and
  `refresh_awake` / `reach_count`.
- Nothing ever wakes a camp onto an enemy.

**Expected effect:**
- Defence (pricing): stepping into the reach of a camp that a teammate or an enemy stands nearer to costs nothing.
  Supports can join the group's tank, and fights next to camps stop treating that ground as BAD.
- Offence (a "pull"): an enemy that is the nearest champion to an elk / golem / monolith takes 60 / 120 / 200 a round
  while it stays in reach, and its recall is cancelled. If the camp kills it, its bag is destroyed.
- One hit from outside its reach costs us nothing.
- Fights at camps are common: the band's first hits land while we walk to a camp or hit one in 41 % of cases
  (firsthit.md).
- [guess] about +0.1-0.3 kills / -0.1-0.3 deaths a game.

**Build spec:**
- `bot.cpp` `build_cthreat()` and `camp_dmg_at()`: for each awake camp, keep its strength on tile t only if t is
  strictly nearer to it than every other visible champion (allies from `W.allies`, enemies seen this round from
  `W.enemies`). Ties count as hitting me: the tie rule is unknown [guess].
- `refresh_awake()`: drop camps whose nearest visible champion is another body, from `awake`.
- New `camp_pull()`, called in `play_turn` before the stance actions (beside the `fb_strike` / `act_fight` entry). It
  fires when all of these hold:
  - a visible enemy e (off its spawn) is in a living camp c's reach (`camp_range`);
  - e is strictly nearer to c than any of our bodies, and nearer than me after my move;
  - c is not a group an ally is farming (comms target).
  Then hit c once (a basic attack in reach, else a damage cast). Prefer golem / monolith / elk over a wolf, and enemies
  carrying 20+ gems or channelling.
- Gate: `value.h` `pull` (0 = byte-identical).
- `micro_eval()`: a tile where I would become the nearest champion to an awake camp gets that camp's strength as
  danger; a tile that leaves an enemy nearest gets no camp danger.

### 2.2 Bush concealment: hits from a bush are invisible; a ward reveals them [measured]

**Probe:**
- B's Tavi stood in a bush at (23,23) and hit A's Tavi at (21,22), 2 tiles away, every third round from r39.
- A's Tavi never saw it: `in_vision(bush)` was 0 and B was absent from `vision::champions`, for 20+ rounds and 8+
  hits. With no visible target it could not answer.
- At r60 A placed its ward on a bush tile of the same cluster, (23,22). From then on it saw B (vis 1) and hit back
  every turn from r90.

**Replays [measured]:** hidden hits are champion hits whose attacker stands in a bush the victim is not in (wards
ignored).

| Team | Hidden hits a game | Share of its champion hits |
| --- | --- | --- |
| Top | 12.0 | 7.3 % |
| Band v top | 7.0 | 5.3 % |
| **Us (tz-126)** | **5.2** | **4.5 %** |
| Band v us | 8.0 | 7.2 % |

- The top lands 2.3x our hidden hits. The band lands 1.5x more on us than we do on it.
- The top is also the victim in a bush more often (10.5 v our 3.2 hits a game).
- Body-rounds in bushes are close (top 6.0 %, us 4.8 %), so the gap is where they stand when they hit.

**What tz does:** bushes appear only as a tie-break in `maybe_ward` (-3) and the blind-approach step (-6). There is no
reactive ward and no bush poke positions.

**Expected effect:** small but one-sided.
- About 3-7 more free hits a game for us, plus counter-wards on the band's 8.
- [guess] +0.05-0.15 kills a game, and fewer bad openings.

**Build spec:**
- `world.cpp` `init()`: label 8-connected bush clusters (`bush_cid`) from `bush_lin`.
- `maybe_ward()`: a new first branch for when I was damaged this turn (`me.damaged`) and no seen enemy and no awake
  camp has me in reach.
  - Place the ward on the reachable bush tile (`ward_placement_tiles`) with the most bush tiles within 4 of me that I
    don't see.
  - Keep the charge by not re-placing for the farm while an enemy was seen in the last 10 rounds (`ward_refresh`).
- `micro_eval()` / `kite_step()` / the WAITR wait spot in `act_farm`: ranged bodies (Vesper, Cassi, Tavi) add a bonus
  for a bush tile in a cluster that neither the target nor any seen enemy stands in. The target must stay in reach and
  the tile must not be BAD.
- Gate: `value.h` `bushp` bits (1 ward, 2 positions).

### 2.3 Respawn hold: standing on a spawn tile freezes the respawn at 0 [measured]

**Probe** (A's Vendetta on a lone gem cluster):
- Captured at r33. The timer ran resp50 down to resp0 at r83 and stayed at 0 while she stood on the spawn tile, until
  r123.
- She stepped off at r123. The cluster respawned at the start of r124 and she hit it that same round (120 -> 55): the
  holder sets the time and is adjacent when it spawns.
- An enemy who sees the group sees `resp0` and the holder, but cannot take the group without moving the holder.

**Replays [measured]:** nobody uses it.
- Body-rounds on an overdue dead group (dead longer than its respawn + 6): top 7.1, band 3.2; us 9.2, band 9.7.
- Holds released into a respawn: 0.21 a game for the top, 0.30 for us.

**What tz does:** WAITR steps off spawn tiles on purpose (`act_farm` RESPAWN branch, bot.cpp ~3607) and wards avoid
them.

**Expected effect:**
- It aims at the lever the respawn study named: at contested mid groups ownership is decided after arrival (we capture
  0.32 of band-held groups we attend; the top 0.68). A hold turns "arrived first" into "spawns when we choose, first
  hit ours, and the enemy cannot farm it meanwhile".
- Risk: the holder stands still in the middle, so it must be our durable body and must keep the BREAK logic.
- [guess] +0.02-0.05 gem share; it needs a band test.

**Build spec:**
- In `act_farm`'s RESPAWN branch, with `value.h` `hold` (0 = byte-identical): when `g.ready_round - W.round <= 2` and
  this body is the group's reserved taker (`plan_claimed` / `i_take(g)`), step onto a free spawn tile of g and stand.
- Release (step to the best adjacent tile, then hit on the respawn round) when:
  - the allies committed to g (`committed(g.id, ...)`, `ally_eta(g) <= 1`) can clear it with me, by `farm_rate` with
    helpers; or
  - no enemy has been seen within 8 for 3 rounds.
- Keep holding while a seen enemy group would out-farm us there. The hold denies them the group, and the existing
  BREAK / `dth` logic still fires on damage.
- `World` group state: a respawning group whose timer is 0 with an ally on its tile is "held". `plan_build` prices it
  as ours (no race term).
- Counter: a group seen at `resp0` with an enemy on its tile is a target (fight price) or a skip, never a wait.

### 2.4 Capture emblem on the supports (3-round captures)

**Rule:** "Capture in 3 turns" [sdk].

**Evidence:**
- On Vesper alone it was the clearest single adoption (tz-117: n19 +0.03 share, deaths -0.36).
- The top builds it first or second on its supports: Vendetta Capture H first; HoR Capture H second; Marcella Capture
  F (TOP3.md). Fish: Capture H on 74 % (support_size.md).
- Contested captures reset when any enemy enters the region [rules]. A 40 % shorter window is fewer resets and fewer
  rounds standing still in the middle: the conversion gap again.

**What tz does:** `cap_emb` covers Vesper only (bot.cpp 3328).

**Unknown:** whether the capture shortens when any capturing ally holds the emblem, or only when all of them do. A
16-game probe can tell: log `capture_state().timer` with and without the emblem holder on the region.

**Build spec:**
- `cap_emb` bit 2: Vendetta / HoR / Marcella line index `cap_emb_pos` gets Capture in the line's stat (Health for
  Vendetta and HoR, Focus for Marcella).
- `i_take()`: prefer the present body with a Capture emblem as the taker (`has_emblem(..., item_family::capture)`).
- [guess] +0.01-0.03 share.

### 2.5 Priority: who acts first inside the alternation [measured order]

**Rule:**
- Turns go A0 B0 A1 B1 ..., and the starting team flips each round.
- Priority, then draft order, sets our slot order. `set_priority` takes effect next round [rules].
- Our top-priority body acts first or second in every round, before 4 of the 5 enemy bodies.

**What tz does:** `prio_fight` (bot.cpp ~4360) is off. Its only measurement was an old local number (57.0 %, BUILD_LOG
1370); it was never run on the band.

**Expected effect:**
- Kills land before the victim's own turn (a flee, a recall or a tribute completion).
- A body in lethal reach moves before the enemy's next actor. A tributer completes at its turn start, earlier in the
  round.
- [guess] +0.1 kills a game.

**Build spec:** in `play_turn` where `prio_fight` sets `pr`:
- 200 when `fb_target()` exists and `fb_live_hp(e) <= my burst` (`burst_on`);
- 150 when HP < 40 % with an enemy in reach;
- 120 when channelling a tribute with an enemy within 6;
- else 0.

Set it every turn (priority applies next round). Gate: `prio_fight 2`.

### 2.6 Smaller or niche

**Skirmish (+10 % to champions) and Hunter (+50 gold a kill) [sdk]:** cheap fight stats for the fight bodies. The top
barely buys Skirmish (165 of 2,572 champion-games, LADDER_5_0). Try one Skirmish on Vendetta / HoR in `shop()` lines
only if fights remain the lever (hpk: damage a hit 82.7 v 106.9).

**Tribute emblem (33 % shorter channel) [sdk]:** a 60-gem bank takes 6 -> 4 turn ends. It suits a Vesper / carry that
banks big bags under threat. Unused by tz and rare in the top's lines.

**Greed [sdk]:**
- Greed shards are plain shards, and 25 combine into a 40-shard emblem: +15 free shards (+1,500 HP on a 100-growth body)
  at 750 gold.
- That beats 5 Power emblems (30 shards for 750) by 10 shards, with nothing paid out before the end.
- Only a body that spends 750+ by mid-game (Vesper) would use it, and it costs the Prospector / Monster / Capture
  passives. Low.

**Vendetta camp last hits [rules]:** any credited kill resets her dash and reset. On multi-camp groups, and in fights
beside gem clusters (120 HP), the last hit re-arms her. Spec: in `act_farm`, Vendetta targets the lowest-HP camp she can
kill this turn. Low.

**Draft memory and 100x draft fuel [sdk]:**
- tz writes no draft memory. The draft could precompute group-to-group / group-to-altar / spawn walk distances (uint8,
  ~800 bytes) for `plan_build`.
- That would cut in-game field building (fuel cuts 21 a game; field_est notes).
- `draft.cpp` `play_draft()` writes, and `World::init()` reads. Medium effort, low-medium value.

**Ward the mid respawns [sdk]:**
- Group state is visible when any spawn tile is in your own vision, a ward's included, and wards never expire. A body
  with no sight of a group since its capture attends 3-4 % of its respawns (respawn.md).
- A ward on the contested mid group a body owns gives that body the exact timer. Vision is not shared, so the
  information stays with the warder; use 2 spare bits in comms bytes 6-7 for "group X respawns soon".
- Spec: `maybe_ward` aims at the last-captured mid group (not on a spawn tile). Low-medium.

**Crystal [rules]:**
- 3-tick channel; damage does not stop it. The top buys 5.4 a game; tz buys none.
- Uses: wall shortcuts to altars and mid groups, and escapes from melee behind a wall.
- Pathing over crystal hops needs a second distance field; skipped as too costly for the lock window.

**Spawn healing 100 % [sdk]:** a body at 1 HP on its spawn is full next turn end. Retreat to the spawn rather than
recall when the chaser is within 7 (`dth` already prefers walking). An enemy on or next to its own spawn is never worth
a chase (`espawn_ignore 1` already).

## 3. Checked and not exploitable

- **Altar locks.** Pre-emptive and intercept variants lost on the band (tz-92 / tz-93), and charging tributers costs
  deaths (tz-53).
- **Tribute-includes-later-captures.** The bag at completion includes gems captured during the channel [rules]. It
  pays only where an altar touches a capture region: map-specific, so skip.
- **Recall-spam detection.** Already modelled (`fb_recalling`, kept-recall filter).
- **Assist gold.** It is 0, so supports get nothing for assists: price kills to the body that takes the last hit (the
  bag goes there too).
- **Tiebreaks at r2000.** Lifetime gold, then kills; games rarely go that long.

## 4. Suggested band queue (one stage each, on the unselected base)

1. `pull 1` + the nearest-champion `camp_dmg_at` fix (§2.1);
2. `hold 1` (§2.3);
3. `bushp 3` (§2.2);
4. `cap_emb 3` (§2.4);
5. `prio_fight 2` (§2.5).

Each defaults to 0 = byte-identical wasm; crash-screen them with `tools/seeds.sh` first.
