# 6. Macro: two carries, open together, then the main carry captures alone

> MACRO: two carries, a main (e.g. Vesper Vale) and a second (e.g. Ren). The initial camps are taken together, then
> the main carry solo-captures. At 150–300+ gold they recall to buy emblems; the main carry buys Home. The others
> capture and group, buying ~4–5 emblems a game. (user, 19 Oct, paraphrased from the redo brief)

This document checks the plan against the rules and our numbers, says why the one time we tried something like it
(A80–A82, session 3) is not the answer, and lays it out as State Updaters (doc 03) over Nav (doc 05).

## 1. Why it works, from the rules

### 1.1 A capture's gold is split; an emblem only pays once whole

- "Rewards are shared among allies present when it finishes" [rules]. The capture takes 5 rounds whatever the number
  of bodies: "More allies do not speed it up" [rules].
- Shards cost 30; **5 make an emblem (150 gold), and only the completed emblem grants its passive** [rules]. Stats
  stack per shard, passives don't stack per family [rules].

So gold is **convex**: 150 gold in one body buys a passive; 150 gold over four bodies buys four shards' stats and no
passive. And the capture is the one place we choose who gets it.

| One lone wolf's 40 gold [sdk 3.0.1; 90 before 3.0] | Gold per body | Wolf captures to a first emblem |
| --- | --- | --- |
| Shared by 4 | 10 | 15 per body (60 team captures for 4 emblems) |
| Shared by 2 | 20 | 7.5 |
| Solo, any champion | 40 | 3.8 |
| Solo, Vesper (+33 %) [sdk 3.0.1; 20 % before 3.0] | 53 | 2.8 |
| Solo, Vesper with Treasure (+53 %) [sdk, rules: bonuses add] | 61 | 2.5 |

Since 3.0 a capture pays less gold (wolf 40, elk 90 [sdk]) and nothing is given at the start (start and passive gold
0 [measured, 00_PATCH_3_0]), so who gets the gold matters more, not less.

Two more facts make the carry worth more:
- **"Gold bonuses add"** [rules]: Vesper's +33 % [sdk 3.0.1] only applies to gold Vesper captures. Gold captured by the others
  never gets it.
- **The gold tiebreak counts all gold earned** [rules]. Vesper's bonus counts there too.

### 1.2 The capture body is the one body that has to wait

- Clearing needs many bodies: the HP model prices it (`bodies_needed`). Capturing needs one, standing on a spawn tile
  for 5 rounds, uncontested [rules].
- The #1 team's cycle, measured 14 Oct (`docs/archive/REPLAYS.md` §3): "the squad clears, **one** body stays to capture
  (5 rounds) and the rest walk on to the next group at once; the capturer banks … and rejoins" [measured].
- So capture-and-leave is not a cost: the others save 5 rounds a take, and the capturer gets the whole reward.
- Gems split the same way, but gems are team currency once tributed. A solo capture puts the whole bag on one body.
  That is the risk the macro must pay for: the carry banks more often and must not die with a bag (§4.3, doc 07).

### 1.3 Home cuts every recall by 2 rounds

- Home: "50 % shorter recall: five turn ends become three" [rules]; recall is 5 in 3.0.1 [measured]. A recall is interrupted by damage [rules], so a
  shorter recall is also fewer broken recalls.
- We make ~18 recall trips a game per team [measured, FARM_18OCT]; the carry makes most of its shop and bank trips by
  recall. At ~6–10 recalls a game for the carry, Home saves 12–20 carry-rounds a game directly, plus the broken ones.
  That is small next to Treasure (+20 % gold on everything after) unless the carry recalls very often. **This is what
  §6 measures before we fix the order.**

### 1.4 A gated altar (00_PATCH_3_0 X8, built session 3)

- Tribute needs a tile within range 1 of an altar [rules]; a live monster holds its spawn tile. On 01boss-battle the
  only altar's ring is holes and walls but for one tile, a monolith's spawn tile (probe `bots/_altarprobe`: ring
  `hh#/cA#/hh#`, two monoliths at distance 1 and 2) [measured]. strat-sw collected ~2,400 gems there and tributed 0.
- **Rule (generic):** at boot, a distance field from our spawn with the camp tiles blocked; an altar none of whose
  ring tiles is reached is **gated** by the groups with a spawn tile within 2 of it (`World.gate_init`, 10_model). It
  opens when a gate group is not alive. Bank uses open altars only.
- **When every altar is gated** gems bank nowhere, and a 0–0 game goes to lifetime gold earned, then kills [rules]:
  farm prices `G2G_K × gold` for every body (no role multiplier, no bag risk) plus `SHUT_GATE` on the gate groups
  (`# GUESS` 500). The live clear model still refuses a take it can't survive, so the monoliths are only tried late.

## 2. What we tried, and why it doesn't close the question [measured, `docs/archive/strat/TEAM_LOOP.md` session 3]

| Build | Carries | W/L vs strat-sw | g/r |
| --- | --- | --- | --- |
| `_s4` (the team-loop bar) | none | 16/18 | 0.92 |
| `_bD` | Vendetta + Ren | 10/24 | 0.82 |
| `_bE` | Vendetta + Vesper | 13/21 | 0.89 |
| `_cx3` | Vendetta + Ren + Home + heal first | 9/25 | 0.78 |

What it showed:
- **It wins open farm maps:** rows 0.90 → 1.37 g/r; expanse and rushbait-v2 won from both sides, which every other
  build lost.
- **It loses brawl maps:** swirl, fragment, pilgrimage and ambush, from both sides. "There the spread-out gold buys the
  team's fights."
- **Vesper is worth ~3 wins over Ren** as a carry.

Why it isn't a refutation of the user's plan:
1. **The wrong main carry.** Vendetta was the main. The user's plan (and the rules, §1.1) say Vesper: her bonus only
   pays on gold she captures.
2. **Flags on the solo loop.** A80 changed price weights (`gold` 1.6 / 1.3 / 0.5) and a `handoff` ("the first carry
   present takes" a shared capture). There was no opening together, no capture-and-leave (the crew stood on the
   capture), and no crew that keeps its own gold. The weights moved *every* gold capture to the carries, so the crew
   starved. That is the brawl-map loss.
3. **The bodies didn't walk well** (doc 05). A carry economy needs a carry who walks off a take and a crew that
   arrives together.

What we keep from it: **the crew must keep enough gold to fight.** On brawl maps the crew's emblems (Power,
Durability, Jungle) win the fights that protect the bag. The user's own wording already says this: "the others
capture and group, buying ~4–5 emblems a game".

## 3. Roles

### 3.1 Who

| Role | Champion | Why |
| --- | --- | --- |
| **Main carry** | Vesper Vale (draft id 1) | +33 % gold, +53 % with Treasure [sdk 3.0.1, rules]. Ranged 3: but camps hit at range 3–5 since 3.0 [sdk], so she still tanks. Dash 2 to escape [rules]. 900 HP: fragile, so she must not hold a bag in a fight. |
| **Second carry** | Ren (draft id 8), per the user | Stun 1.25 × Focus at range 4, dash 2, retaliation [rules]. Can clear smaller groups alone and escape. **Not in strat-sw's roster** (`ROSTER = (9, 1, 0, 2, 6)`: Varg, Vesper, Ryth, Vendetta, Marcella). We add him: the roster grows, nobody is dropped (§3.2). |
| **Crew** | the rest, each its own build (§4.6) | Clear the groups that need ≥ 2 bodies; capture and keep their own takes; fight. The user's examples: the 3rd body in 3v3 (e.g. Cassi & Issac), the 3rd and 4th in 4v4 (e.g. Ryth and Cassi & Issac). |

What the #1 team does (A80's source, user observation 19 Oct): Stellar main, Ren second, whatever the team size.

### 3.2 Draft (team size S = 3, 4 or 5 [rules])

The draft picks in order, and the S first picks play [rules, `bots/strat-sw` draft]. So the carries must be in the
first picks:
- **S = 3:** Vesper, Ren, plus one crew body (e.g. Cassi & Issac, the user's example). 2 carries + 1 crew.
- **S = 4:** + one more crew (e.g. Ryth and Cassi & Issac). **S = 5:** + two.
- **The roster grows (user, 20 Oct).** We build support for Vesper *and* Ren *and* the crew champions (Cassi & Issac,
  Ryth, and strat-sw's Varg, Vendetta, Marcella), so the draft has more champions it can play well. Nobody is dropped
  to make room: each new champion needs its kit (profile, abilities) before the draft may pick it, and the pick order
  is then judged in matches.
- **If the enemy takes Vesper or Ren first:** the backup list as now. The main carry is then the next best gold body
  (Vendetta: resets on kills, dash), and the second the next. The roles are written in the draft record (doc 04 §3),
  so every body agrees.
- **If the main carry is dead:** the second takes the main's job until she respawns. Everyone computes the same answer
  from the slot bytes (code 7 = dead), Gone Fishin's trick (doc 04 §3).
- **Built (session 3):** the roles are computed on every body from the draft roster alone, so no byte is needed
  (`10_model` `MAIN_PREF = (1, 2)`, `SECOND_PREF = (8, 2, 1)`): Vesper main, else Vendetta, else slot 0; the second is
  Ren, then Vendetta, then the lowest other slot. With the current roster that is Vesper main, Vendetta second. The
  dead-main hand-over is not built (the capture hand-off below already falls to the second when she is not there).

## 4. The phases, as State Updater rules

### 4.1 P0: the opening, together

- **Rule:** all bodies take the first groups together: the 1–2 best groups by `d_us` vs `d_them` and gem value
  (the draft already computes these). This is `docs/archive/strat/TEAM_LOOP.md` T4's opening ball, now with the byte-7 crew call
  (built, doc 04 §5.1) to name the group.
- **Capture:** after the last monster dies, **the main carry captures alone**. The others walk to the next group as
  soon as the last monster dies, so the respawn and the next clear start 5 rounds earlier (§1.2).
- **When it ends:** when the main carry's first emblem is done (or her gold reaches the next emblem's cost and she
  shops), or at round `OPEN_END` (~100), whichever comes first. The top teams' first emblem is r44–93; ours r71–112
  [measured, FARM_18OCT per-opponent table].
- **Why together:** the first takes have no items; a group that 1 body clears in 30 rounds 3 bodies clear in ~10,
  with less damage each [measured, `docs/archive/strat/TEAM_LOOP.md`]. And the first enemy contact is usually early.
- **Built (session 3):** before `OPEN_END` (100, a GUESS constant in `50_prices`) the stack rules hold on every map
  (`stack_mode`): the whole team is one subgroup seeded on the richest group (`70_updaters` `group_slots`), prices
  groups without the per-body split and never waits at a camp. At `OPEN_END` `decide` re-splits once: the old
  subgroups on a group map, none elsewhere. The end is the round only; "her first emblem is done" is not a trigger
  (her median first emblem is r75, §10).

### 4.2 P1: the main carry solo-captures

The main carry's updater (CarryUpdater, doc 03) prices, in order:
1. **Solo takes she can clear** (wolves, gold and gem clusters, small elk groups once she has items), priced at
   `gold × her multiplier + gems × the gem value`, over the walk and the clear. Her multiplier is 1.33 (1.53 with
   Treasure) [sdk 3.0.1, rules]. Prices stay in team gems per round (CLAUDE.md rule 2).
2. **Captures of crew clears** when the crew calls and she is the nearest free body (§4.4).
3. **Shop** by the §4.5 rule.
4. **Bank** her bag: she carries every gem she captures, so her bank threshold is lower than the crew's
   (§4.3).
- She **does not fight** unless doc 07's matrix says she can win the exchange and she carries no bag worth more than
  the kill.

### 4.3 The bag

A solo capture gives the carry all the gems. Two rules:
- **Bank sooner than the crew:** her bag threshold is lower, and it grows with the walk to the altar and shrinks with
  enemy sightings (central-place foraging, `docs/archive/REPLAYS.md`).
- **Recall with the bag, then tribute from home**, when an altar is 5–8 tiles from spawn: the #1 team did this on
  lanes B for 18 of 27 tributes [measured, `docs/archive/REPLAYS.md`]. With Home the recall is 3 turns.

### 4.4 The second carry

Two jobs, priced by its updater (SecondUpdater):
- **A second solo region:** solo takes on the far side of the map from the main carry. Each carry claims its groups
  through the slot byte, so they don't overlap.
- **Capture stand-in:** when a crew clear finishes and the main carry is more than ~8 rounds away (shopping, banking,
  dead), the second captures it.
- Ren's stun breaks tribute channels [rules], so the second is also the first answer to an enemy channelling (event
  type 5, doc 04 §5.1).
- **Built (session 3), and what it measured:** only the capture stand-in, through the hand-off (`60_behaviors`
  `handoff`: the main if she is among the bodies at the group, else the second, else the lowest slot). The second
  solo region was tried as the second's gold multiplier 1.0 (it then prices gold like a carry): on the 7 maps that
  build lost from both sides it went 0/14 against 5/14 with 0.05 (mean margin −574 vs −122 vs `_r2`) [measured,
  20 Oct]. The second keeps the crew's 0.05; a real second region needs the slot-byte claim above and Ren, whose stun
  lets one body clear (§9).

### 4.5 Shopping: recall at 150–300 gold

- **The window:** a body may shop when its gold ≥ the cost to **finish its next emblem** (150 for a fresh one, less
  if shards are started). **It must shop at 300.** Emblems are convex (§1.1); buying shards one by one wastes trips.
- **How:** recall if spawn is farther than the recall time (5 turns, 3 with Home), else walk. Combine trips: if the
  bag is over half the bank threshold, tribute first (altar on the way) or recall and tribute from home. If HP is
  below 50 %, the same trip heals [rules: spawn heals].
- **Dead bodies shop** [rules], so a body that dies spends its gold at once (strat-sw does this already).
- Evidence: the top teams recall with ≥ 150 gold 124 times against our 75 [measured, FARM_18OCT].
- **Built (session 3):** `50_prices` SHOP prices a trip only once gold ≥ what finishes the next emblem (`ME["need"]`,
  set by `buy_all`), capped at `SHOP_MUST = 300`, where SHOP is × `SHOP_MUST_X` (3.0, GUESS; it was group mode only).
  The trip is `ME["recall"] + 1` rounds: 5 + 1, or 3 + 1 with any Home emblem; HEAL uses the same recall time. The
  spawn-tile reflex still buys any shard (no trip, strat-sw's K2).

### 4.6 Builds

| Body | Order | Why |
| --- | --- | --- |
| Main carry | **Home** first (user, confirmed 20 Oct), then **Treasure**, then **Monster** / **Power** | Home: shorter recalls; Treasure: +20 % gold on every later capture; Monster: +10 % camp damage, faster solo clears. §6 still records both so we see what Home buys. |
| Second carry | Power (Focus: stun damage), then Jungle | Faster solo clears and fewer heal trips. |
| Each crew body | **Jungle** (30 % less camp damage), then **Power**, then Durability | The top teams: Power 70 %, Jungle 54 % of their emblems [measured, FARM_18OCT]; Jungle first on farmers, Durability first on fight-heavy small maps [measured, `docs/archive/REPLAYS.md`]. |

The stat in each family stays the champion's main stat (as strat-sw's profiles do).

**Built (session 3)** as `20_champs` `ROLE_BUILD`, by role, replacing the per-champion builds and the tanks' Jungle
prefix (`TANK_IDS`): main Home, Treasure, Monster, Power; second Power, Jungle; crew Jungle, Power, Durability; then
each alternates Durability / Power. All Strength but Durability (Health): our roster are basic attackers. The FARM
gold multiplier moved from the profile rows to the role too (`ROLE_GOLD`: main 3.0, second and crew 0.05, the crew's
spike shift unchanged). Base HP / Strength are read from the SDK (`Champion.design`, X2), not a table.

**"~4–5 emblems a game" (user, confirmed 20 Oct): per individual crew champion**, not for the crew as a whole.
That is about 600–750 gold each over a game, a target §6 measures. Each crew body shops for itself by §4.5.

### 4.7 P2: the crew

The crew's updater (CrewUpdater) is strat-sw's farm/fight/heal with three changes:
- **Groups by size:** crew takes are groups the carries can't solo (need ≥ 2). The crew captures **its own takes**
  and keeps the gold (§2's lesson), unless the main carry is within ~3 rounds when the clear ends and calls for it.
- **Together:** the crew walks as a group between takes (doc 05's ring tiles, team order and arrival spread), and
  regroups after a fight on the highest-HP ally nearest the objective (Gone Fishin §5.6).
- **Shops by §4.5.**

## 5. Generic over maps

No map names or numbers. What changes per map is read at runtime:
- **How much the carries solo:** from the draft's `solo` share (groups needing 1 body over all groups,
  `strat/MAPTYPES.md`). On maps with few soloable groups (stampede-like), the carries join the crew more.
- **The brawl/farm split** (the untried idea from session 3): a contact rate in the first ~100 rounds (enemies seen per
  body-round) moves the crew's capture share up and the carry's down when contact is high. Start without it, measure
  where we lose, then add it as a score term, not a flag.
- **Home:** the user says Home on the main carry. A82 gated it on the mean walk to the groups (≥ 20). Start with the
  user's rule; the replay metric (§6) tells us if the gate is needed.

## 6. What to measure

A new replay script, `tools/replay/farm/carry.py` (from `decode.mjs`'s per-round gold, captures and shop events):
- **Gold share per champion** at r300 and at the end (ours and the top teams').
- **Solo vs shared captures**, and who captures a crew clear (carry / crew / second).
- **Round of the first emblem per body**, and emblems per body per game (the "4–5").
- **Gold at recall** (the 150–300 window), and recalls per body.
- **Home's saving:** recall rounds per carry per game, with and without Home; broken recalls.
- **Bags lost by the carry** (deaths with gems).

Gate (session 3, CLAUDE.md rule 5's exception for a partial redo): the main carry's first emblem earlier than
strat-sw's; captured g/r up; gold share toward the top teams; no regression in session 2's Nav numbers
(`tools/navstats.py`); faults 0/0. Win rates vs `_r2` and vs strat-sw are reported, not gated. Also watched: **no
brawl map lost from both sides that the before build wins** (A80's failure). swirl and pilgrimage are no longer in
the 3.0 pool, so the brawl maps are derived from it: the third of the 21 maps with the most champion deaths per game
(both teams) in `_r2` vs strat-sw [measured, `runs/arena/_r2-vs-strat-sw-20261020-133230`]: 01hooks 56, 00eight 54,
01elk-arena 50, 00contest 39.5, 00fragment 39, 00ambush 28.5, 00interlock 28 (the pool's median is 21.5).

## 7. Build order inside R3

1. Roles from the draft record (§3.2) with the **current** roster: Vesper main, Vendetta second. One change at a time.
2. Capture-and-leave after crew clears (§1.2), the carry captures (§4.1–4.2).
3. The shopping window (§4.5) and the builds (§4.6), Home first on the carry.
4. The opening together (§4.1).
5. The roster grows: Ren's kit, then Cassi & Issac's, each added to the draft once it plays (§3.2).

Session 3 built 1–4 in that order (§3.2, §4.1, §4.4–§4.6 say what each became); 5 is not built (§9).

## 8. Unknowns to check when building

Checked in session 3 (numbers in §10):
- **P-g** (the main carry's capture after a team clear raises team g/r): supported, not isolated. With the hand-off on
  every map, the main's first emblem moved r110 → r75 and captured g/r 0.366 → 0.425 (§10) [measured]; the four steps
  were judged together, so the share of each is not known.
- **The shop window** (a trip only when gold finishes the next emblem; must shop at 300): built; median gold at a
  recall 61 → 90, still under the 150 the window aims at, because most buys are the spawn-tile reflex and recalls
  also heal and bank [measured]. Whether a trip window beats one-shard buys is still open.
- **"4–5 emblems" per crew body:** the crew finish ~9.4 emblems each a game (carry.py `emb/body`, repeats counted;
  `_r2` 8.6), so the target is passed on these 3.0 maps, but late: their first emblem is at median r420 (`_r2` r470),
  because the crew price gold at 0.05 until the spike shift (r300 or the main at 120 Strength) [measured].
- **The second's gold 1.0** (a second solo region): measured worse, 0/14 vs 5/14 on 7 maps (§4.4).
- **Broken recalls** (carry.py `broken/g` ~18–27 a game in every build, strat-sw too): they are `safe_recall`
  re-issuing and then cancelling the recall when the danger is gone, not lost channels [measured, traces]. Home's
  saving is real: ~11 recalls a game with Home, ~23 rounds a game.

Still guesses (constants marked `# GUESS`):
- `OPEN_END = 100` (`50_prices`): the opening's length. The main's first emblem is ~r75, so it covers it.
- `SHOP_MUST_X = 3.0`: SHOP's multiplier from 300 gold.
- `SHUT_GATE = 500` (§1.4): a gate group's value while every altar is gated.
- Heart of Ruin's place as the first backup pick (`80_draft` `BACKUP`, X6).
- Home's gate on the walk (A82, §5): not needed so far; the user's rule (Home first, always) stands.

## 9. The roster grows: named, not built (session 3)

**Built in session 5 (§11):** Ren drafted third and the second's gold kept; Cassi & Issac built, lost, not picked.

Session 3 ran out of room for §7 step 5, so the draft still picks strat-sw's roster (`10_model` `ROSTER` and
`80_draft` `PICKS` = Varg, Vesper, Ryth, Vendetta, Marcella; Heart of Ruin is now the first backup, X6). What is
already in place for it:
- The roles do not depend on the roster: `SECOND_PREF` already puts Ren first, so drafting him makes him the second
  with no other change. With S = 3 the picks are Varg, Vesper, Ryth, so the second is Varg (the lowest other slot).
- Builds are by role, so a new champion gets its role's build; base stats come from the SDK (X2).

What each new champion still needs before the draft may pick it (each its own measured change):
1. **Ren (8):** a PROFILES row (now neutral), his kit in the Kit layer (stun 1.25 × Focus at range 4, dash 2,
   retaliation [rules]): a stun on a camp's hardest hitter, a dash out; then the second solo region (§4.4) with a
   slot-byte claim so the carries do not overlap. Then PICKS / ROSTER order, judged in matches.
2. **Cassi & Issac (3):** a profile row and kit (`docs/Champions/Cassi&Issac.md`); the crew role and its build need
   nothing more. Then the S = 3 pick order (Vesper, Ren, Cassi & Issac, §3.2).
3. Heart of Ruin's backup rank (X6) is a GUESS until a draft that loses Varg or Vesper is played.

## 10. Results (session 3, 20 Oct, cambc 3.0.1, 21 maps × 2 sides)

Runs: `runs/arena/redo-vs-_r2-20261020-165852` (the before / after on the same games) and
`runs/arena/redo-vs-strat-sw-20261020-165440` (+ the 6 cached games in `...-165246`; merged view
`...-170000`). Before = `bots/_r2` (session 2's build, git-ignored). `carry.py` and `navstats.py` numbers [measured].

| Measure (06 §6 gate) | `_r2` | redo | |
| --- | --- | --- | --- |
| Main carry's first emblem, median round | r110 | **r75** | met (strat-sw r130–136) |
| Captured gems per round | 0.366 | **0.425** | met |
| Top earner's share of team gold at r300 (top teams 0.35–0.38 on the 2.2 ladder) | 0.62 | 0.61 | **missed**: not toward the top teams |
| Main carry's share at r300 / at the end | 0.58 / 0.30 | 0.59 / 0.34 | the gold goes to her, by design |
| Team gold earned per game | 7266 | 7855 | |
| Crew clears captured by one body | 57 % | 97 % | the hand-off works |
| Crew emblems per body / first crew emblem | 8.6 / r470 | 9.4 / r420 | |
| Median gold at a recall | 61 | 90 | |
| Recalls with Home / rounds saved, per game | 0 / 0 | 11.4 / 22.7 | |
| Bags lost by the main carry per game (gems) | 1.43 (40) | 1.48 (61) | worse: she carries more (07) |
| Nav, redo vs `_r2` run: direct / moving rounds per tile | 2.17 / 1.29 | 2.00 / 1.25 | no regression |
| walk excess / crew spread (median) | 1.33 / 7 | 1.29 / 7 | |
| stuck / osc / stall per game | 1.19 / 0 / 46.9 | 0.71 / 0 / 35.0 | stall down: X8 |
| calm deaths / deaths to camps per game | 2.21 / 1.60 | 1.33 / 1.38 | |
| Faults | 0/0 | 0/0 | met |

Win rates (reported, not gated):
- **redo vs `_r2`: 21W / 21L**, 6/21 maps won from both sides, mean margin +37. Lost from both sides: 00contest,
  00eight, 00fragment (all brawl maps), 01corridors, 01gold-rush, 01islands.
- **redo vs strat-sw: 25W / 17L (60 %)**, 7/21 from both sides, margin +65, deaths 15.0 (`_r2` vs strat-sw: 23W / 19L,
  6/21, +100, deaths 13.2). Lost from both sides: 00contest, 00interlock, 01gold-rush. **Brawl watch:** 00interlock
  is now lost from both sides where `_r2` won one side; 00ambush and 01elk-arena went from lost both sides to
  split; 01hooks from won both sides to split.
- **01boss-battle (X8):** `_r2` drew 0–0 from both sides; redo wins 1237–0 from side A (the team breaks the gate and
  banks) and 0–0 on gold from side B. A stall found while measuring: Fall walked at the gated altar (96 of 135
  `failed stuck` in a run before the fix); Fall now walks only to an open altar (4 after).

What it says: the macro pieces work as built (earlier first emblem, more captured gems, one body captures, Home
used, Nav steady). It does not close the gap to the top teams: they spread gold, we concentrate it, and the losses
are on brawl maps (00contest 0 gems both sides, fight deaths up 11.5 → 13.6 a game vs strat-sw), which is 07's job.


## 11. Session 5: roster growth, design (20 Oct, written before the build)

The order is §9's: Ren first, then Cassi & Issac, each its own measured change on `bots/redo` (R4). Fuel (07 §14): no
new per-turn search; every piece below is a table row, a boot-time mapping or one comparison per turn.

### 11.1 What the code already does for a new champion [code read]

- **Kit** (`20_champs` `Kit`) sorts the slots by the SDK's flags, not by champion: a slot that damages and can target
  camps is a camp spell (Farm casts it on the monster it just hit), one that damages or stuns and can target enemies is a
  fight spell (Kill, Hold), an attack reset fires after the basic attack, a dash is Nav's (05 L4).
  - Ren slot 0 (1.25 × Focus damage + 1-round stun, enemy or camp, range 4 [rules]) is both a camp and a fight spell;
    slot 1 (dash 2) is Nav's. Retaliation is a passive: nothing to cast.
  - Cassi slot 0 (2 × Focus, enemy or camp, range 4) is a camp and fight spell; slot 1 (stun only) is a fight spell
    (it is not cast on camps: `on_camp` needs damage). Issac slot 0 is an attack reset, slot 1 a dash.
- **Roles** (`10_model` `SECOND_PREF = (8, 2, 1)`) already make Ren the second when drafted; builds and gold are by role
  (`ROLE_BUILD`, `ROLE_GOLD`), base stats from the SDK (X2). Ren's Strength shard (+5 a hit, every turn) beats his Focus
  shard (+9 Focus = +11 nuke per 8 turns + 1.8 per retaliation) [rules-derived, 3.0 numbers from 00_PATCH_3_0 §1], so
  the second's Strength build fits him.
- **What breaks with Cassi & Issac:** the slots. `World.slot_init` maps each body to its *draft id*; Cassi and Issac are
  both draft id 3 (`_TYPE_TO_DRAFT`), so both get the same slot, write the same shared byte and read each other's
  claims as their own. With 5 picks they are 6 bodies and there are only 5 slot bytes (bytes 5–7 are the sighting and
  the death mark, 04).

### 11.2 Step 1: Ren (R5a)

- **PROFILES row 8** (GUESS, like every row): farm 1.1 (the nuke + stun on the monster he hits; retaliation on camps
  unknown), bank 1.0 (dash 2 escapes), kill 1.2 (stun at 4 holds the target, dash closes), hold 1.5 (a stun at 4
  breaks a channel [rules], Ryth's value), join 1.1.
- **Draft:** Ren the third pick: `PICKS = ROSTER = (9, 1, 8, 0, 2, 6)`. He plays at every team size and is always the
  second. What drops: S = 3 Ryth, S = 4 Vendetta, S = 5 Marcella (5 picks on 14 of the 19 maps in the last full
  run, 4 on 2, 3 on 3 [measured, draft lines of `runs/arena/redo-vs-_r3-20261020-191100`]).
- **Then, if Ren plays:** the second's own region (§4.4) retried as `ROLE_GOLD["second"] = 1.0` with Ren (it lost with
  Vendetta, 0/14 vs 5/14). One constant; the farm claims already keep two bodies off one group (lower slot keeps it).

### 11.3 Step 2: Cassi & Issac (R5b)

- **Body slots** (`World.slot_init`): order the *bodies*, not the draft ids. The pick list expands draft id 3 into
  Cassi then Issac (ChampionType 3, 4 [sdk]); a body's slot is its index among the bodies present. A sixth body (5
  picks with Cassi & Issac) has slot 5: it writes no byte and reads the other five; nobody can see its claim, so it
  yields like the highest slot already does (lower slots keep groups).
- **Two rows** (they are two champions with one draft id): rows by ChampionType for these two only (`TYPE_ROWS`).
  Cassi, 600 HP and the pair's life (if either dies both die, both bags are lost, one kill gold [rules]): heal 2.0,
  bank 1.2, farm 1.1 (nuke 2 × Focus at 4), kill 1.0, hold 1.5 (stun at 4), join 1.0. Issac: farm 1.1 (reset), bank
  1.0, kill 1.1, hold 0.5 (no stun), join 1.1. All GUESS.
- **Draft:** the user's examples (§3.2): S = 3 Vesper, Ren, Cassi & Issac; S = 4 + Ryth; S = 5 + Varg:
  `PICKS = (1, 8, 3, 0, 9, 2, 6)`. Then Vesper is slot 0 and leads the claims (the lowest slot keeps a group).
- **Not built:** a split-or-together rule for the pair (`docs/Champions/Cassi&Issac.md`'s open question). They are two
  crew bodies; monsters hit the nearest champion [rules], so when they farm together Issac (melee) tanks for Cassi.

### 11.4 Measures (session 5)

- **Per champion** (`tools/champstats.py RUN_DIR`, new: the stats JSON's per-champion metrics): collected and
  submitted gems, earned gold, deaths, kills, monster damage done / taken, per game, our team only. Ren and Cassi &
  Issac against the champion they replace.
- **Team (06 §6):** captured g/r, the main's first emblem, deaths a game, faults 0/0 (`carry.py`, `navstats.py`).
- **Fuel:** turn rollovers must not rise (07 §14).
- **The arena vs strat-sw** (CLAUDE.md rule 5, reported) and vs R4 (`bots/_r4`).

### 11.5 Unknowns to check when building

- Does Ren's retaliation fire on camp hits? (`docs/Champions/Ren.md` "To test".) If yes his farm row is low.
- Cassi & Issac: are gold and the shop per body? [rules say the bodies have separate bags; gold not stated] Read
  from the per-champion `earnedGold` / `itemsBought`.
- Do six bodies with five slot bytes collide anywhere else (opening seeds, group subgroups)? Read the traces.

### 11.6 Results (session 5, 20 Oct, cambc 3.0.1, 21 maps × 2 sides) [measured]

**Step 0, the R4 baseline** (07 §14 left it open): R4 vs strat-sw **17W/25L**, margin −49
(`runs/arena/redo-vs-strat-sw-20261020-200426` + 8 cached games in `...-195129`), against R3's 25W/17L. R4 with
session 4's X8 gate on Hunt / HOLD removed (the boot-time `gate_init`, Bank and Fall gates stay): **22W/20L**, margin
+29 (`runs/arena/_x8off-vs-strat-sw-20261020-200936`). That gate was deleted; this build is the base of the session
and the rollback **`bots/_r4`** (git-ignored).

**The steps**, each a full arena vs strat-sw (the head-to-head vs `_r4` of 11.4 was not run: every step was compared
on the same 42 strat-sw games instead, one run at a time); per champion by `tools/champstats.py` (means per game played):

| Build | Record | Margin | Deaths/g | Team tributed/g | Run |
| --- | --- | --- | --- | --- | --- |
| base (`_r4`) | 22W/20L | +29 | 14.2 | 598 | `_x8off-vs-strat-sw-20261020-200936` |
| + Ren third (R5a) | 17W/25L | +42 | 12.5 | 608 | `redo-vs-strat-sw-20261020-201531` |
| + `ROLE_GOLD["second"] = 1.0` | 21W/21L | +147 | 11.2 | 656 | `_gold-vs-strat-sw-20261020-202926` |
| + Cassi & Issac (R5b, `PICKS = (1, 8, 3, 0, 9, 2, 6)`) | 15W/27L | −40 | 22.8 | 527 | `_ci-vs-strat-sw-20261020-203455` |
| **final R5** (gold step + the body slots, Cassi & Issac not picked) | **20W/22L** | **+105** | **10.8** | 622 | `redo-vs-strat-sw-20261020-205000` |

- **Ren:** as the second he collects about as much as Vendetta did in that role (287 vs 288 gems a game) with less
  monster damage (30k vs 41k a game); what he adds is Vesper's (gold 2724 → 2926, kills 9.7 → 12.0) and fewer deaths.
  The second's own gold (§4.4: 0/14 with Vendetta) **wins with Ren**: one constant, kept.
- **Cassi & Issac lost and are not picked.** Cassi 73 / Issac 56 gems collected a game (Varg 282 in the slot they
  took), **5.8 deaths each** (a Cassi death kills Issac [rules], so pair deaths count twice). Deaths by cause
  (`tools/microstats.py`): heal 9.4 vs 5.67 a game (Cassi's `heal 2.0` sends her home sooner and she is caught on the
  way), walk 4.21 vs 0.95, camp 3.14 vs 1.31. Varg in the silent slot 5 (no byte) collected 108 vs 282. Kept: the
  **body slots** (`10_model` `body_of`, `nbody`, `ISSAC_B`; `40_comms` slot 5 writes no byte; `70_updaters` 6 seeds,
  two trios) and `TYPE_ROWS`: boot-only, and correct for any roster, so a backup pick of the pair no longer shares a
  byte. Rebuilding the pair would start from their deaths (the split-or-together rule, `docs/Champions/Cassi&Issac.md`),
  which is 08's area.

**06 §6 measures, final R5 vs the base** (`carry.py`, `navstats.py`, `microstats.py`):

| Measure | base `_r4` | R5 | |
| --- | --- | --- | --- |
| Captured gems per round | 0.402 | 0.404 | steady |
| Team gold earned per game | 7891 | 8120 | up |
| Main's first emblem, median round | r86.5 | r90.5 | steady (strat-sw r116) |
| Main's emblems at the end | 16.7 | 17.7 | up |
| Top earner's share at r300 (top teams 0.35–0.38) | 0.62 | 0.64 | **missed**, as in session 3 |
| Deaths a game (by champion) | 14.2 (12.7) | **10.8 (9.6)** | down; heal deaths 8.1 → 5.4, trade 0.93 → 1.34 |
| Main's lost bags, gems a game | 45 | 52 | worse |
| Turns per 50 rounds (fuel rollovers) | 49.9 | 50.0 | no rollovers added (07 §14) |
| Stuck / osc a game, faults | 0.95 / 0.02, 0/0 | 0.62 / 0.0, 0/0 | |

**Answered unknowns (11.5):** Cassi & Issac's gold is per body (`earnedGold` 859 / 693 a game) [measured]; six
bodies with five bytes ran with faults 0/0 and no new turn error (only the known `SCAN.post` ward error, 07's open
item, in every build), but the silent body's claims are invisible, and Varg there
collected 108 [measured]. **Still open:** whether Ren's retaliation fires on camp hits (the SDK has only
`REN_RETALIATION_FOCUS_RATIO = 0.2`; the engine is compiled), so his farm row stays a GUESS.

R5 vs strat-sw is 20W/22L: below the bar, **no candidate zipped**. The fight deep dive (08) comes next.
