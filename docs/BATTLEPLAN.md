# Battle plan: the five pillars

The master plan for our bot, written 13 Oct 2026 for `bots/tzunami444`. **Since 14 Oct the plan of record is the v2 section just below** (`bots/tzunami-lite`); the five pillars after it are the background it draws on. It turns the five pillars agreed with the team into rules we can build and test:

1. draft and opening;
2. general behaviour rules;
3. per-champion kits;
4. communication through 8 bytes;
5. split-second reflexes.

`STRATEGY.md` holds the game model and the principle table. This file is the **plan of record for what we build, in what order, and how each piece is tested**.

Tags as everywhere: **[rules]**, **[sdk]**, **[measured]**, **[provisional A#]**. Principles are cited as P# (`ART_OF_WAR.md`). Every rule below is a config switch and gets an arena A/B: all maps, both sides, worst map included.

---

## v2: `bots/tzunami-lite` (agreed 14 Oct; ship candidate since 14 Oct late)

**Why a v2.** tzunami444 beats the starter 18W/0L, but it did poorly on the ladder (no numbers to hand, so the reasons below are judgement, not measurements). The ladder map pool is byte-identical to our 9 local maps (sha256, 14 Oct), so the losses come from opponents, not maps. tzunami444 is ~1,100 lines of special cases, and every fix interacts with the others (only 10W/8L vs its own no-take version). v2 is a **rewrite from a simple core, built up one measured layer at a time**. It reuses the proven parts of tzunami444 (cached distance fields, `seen_champions`, `reachable`, spawn-tile and contested-capture lessons). tzunami444 stays as the sparring partner.

**HFT framing.** Latency is rounds: every round a body stands still or walks without purpose is money lost. Hot path (walk, hit, capture) is tiny and fixed-cost. Cold path (fights, endgame) is small. Precompute in the draft (24.6M fuel on turn 1 [measured]). Measure boot round, fuel per turn, idle rounds and walking rounds.

**2.1.6 changed the boot cost (A48).** The engine now pre-loads every module except `main.py` before the game starts, so tzunami444 boots inside round 1 instead of round 57 [measured locally, 14 Oct]. Code size no longer costs boot. It still costs reading and bugs, so v2 stays small, but per-turn fuel is now what counts. Module top-level code runs at build time: no game calls at import, and `main.py` holds only the entry loop.

### The layers (each one kept only if it beats the previous one in the arena)

| Layer | Rule | Principle |
| --- | --- | --- |
| **L0 core** | Each body goes to its best camp by gems per round (gems ÷ (walk + clear + capture rounds)). Gem clusters first (500 HP, 0 damage), soloable wolves second, never elk or monolith alone. Cached distance fields | P2 speed, P9 easy targets |
| **L1 spread + swarm** | One claim byte per body splits bodies over different camps. If a live camp is within a few tiles of several allies, they all hit it; the body on the spawn tile captures and the others leave the moment it dies (the reward is split among those present, so staying wastes 5 rounds) | P10 concentrate, P13 |
| **L2 banking** | No fixed bag size. Bank when the detour via the altar (me → altar → next target, minus me → next target) is ≤ ~6–7 tiles. Always bank when carried + tributed ≥ 1,000 (instant win), when carrying a big bag and an enemy was seen recently, and in the endgame before round 2,000 | P2, P11 |
| **L3 recall, never walk home** | Threat radius is **7**, not 3: spells reach 4 (Cassi, Stellar, Marcella, Tavi, Prism, Ren, Ryth's stun) plus 1 walk plus a 2-tile dash. Start a recall when no enemy is within 7 and no awake camp within 3; `cancel_recall()` if an enemy comes within 7. Walk home only if spawn is ≤ 5 tiles away. Triggers: low HP, gold ≥ one item, a big bag with an altar next to spawn | P4 make yourself invincible first |
| **L4 shop** | Buy whenever at spawn or dead and gold allows. One stat per champion: farmers Strength (camp damage), tanks Health, Cassi Focus. **Measured 14 Oct: one DUAL build (5 Monster Strength + 5 Jungle Health, then Power Strength) on every body but Cassi beats the per-role builds** (A14) | P2 |
| **L5 fight** | Fight an enemy at ≤ 70% HP. Guards: always take a kill we can finish this turn; never fight outnumbered in view; fight back against a melee champion that is hitting us (walking away from melee fails) | P8 strike the weak, P4 |

**Status (14 Oct): L0–L5 all built**, each a switch in `config.py`. Measured changes to the plan above: L5 fights at any HP within 6 tiles when we win the race (≤ 70% HP and radius 4 were worse), we **flee** when outnumbered, and we do **not** fight back at adjacent melee (+6 deaths/game). Hot-camp memory keeps a healing body out of an awake camp's range. Results: vs starter 18W/0L; vs tzunami444 9W/9L. The remaining gap is farming speed on elk maps (`HANDOFF.md`).

**Status (14 Oct, night): new ship candidate** with the `stand_tile` fuel fix and `TAKE_OVER_TRIPS` on: vs tzunami444 **62W/10L, +335 ± 34**, worst map expanse +103; vs the starter 72W/0L (`HANDOFF.md` → 14 Oct (night)). **Status (14 Oct, late): ship candidate.** Pairs are built (`SQUADS`, `LAYOUT = "pairs"`), pairs capture together and split the reward (`SQUAD_SPLIT`, A53), and L4 is now one build for every body but Cassi (`DUAL`, A14). Over 4 salts (`tools/seeds.py`, 72 games): vs tzunami444 **61W/11L, +297 ± 32**, worst map elkring +27 (it was 9W/9L in one arena run this morning, 53W/19L +100 seeded before DUAL). Measured worse and switched off: `ENGAGE` (A54), `ESCAPE` (A56), trios on CONTEST maps, a draft opening per squad. Full table: `HANDOFF.md` → 14 Oct (late).

**Death is the costliest event** [rules]: 60 rounds out, the killer takes every carried gem + 50 gold. Every layer is judged on deaths and gems lost as well as gems per round.

### Draft (1,024 bytes) and the three opening strategies

The draft instance picks **first** on every draft turn (a draft that runs out of fuel before picking gets random picks), then plans with what fuel is left. The plan module must not be named `draft` (A27).

**Picks.** Cassi & Issac are in every comp (user's call, 14 Oct). Rules arithmetic per body on a gem cluster: Vendetta ~79 camp DPS, 12 rounds clear + capture, 2.0 gems/round; Cassi ~47, 16 rounds, 1.5; Issac ~45, 17 rounds, 1.4. Split, the pair makes ~2.9 gems/round on clusters; together they take wolves (Cassi alone on a wolf ends at ~140 of 700 HP, and their deaths are linked), Issac tanks. Default comps, to A/B:
- size 3: Cassi & Issac, Vendetta, Ryth;
- size 4: + Varg;
- size 5: + Stellar or Marcella.

**Map strategy, one byte, chosen from map features in the draft** (user's design, 14 Oct). Each strategy is a parameter set in `config.py` keyed by the strategy id:
- **FARM:** an altar is close to our spawn and clearly nearer us than them, with camps near it. Spread out, farm our side first (P9), bank at the home altar.
- **CONTEST:** the only altars are central or equidistant (e.g. one altar in the middle). Move in pairs, farm near the centre, bank together, looser fight threshold around the altar; altar locks later (P10, P11).
- **ROAM:** altars and camps are scattered or far (big maps where every group is far from spawn). Maximum spread, bank at any altar en route with a bigger detour allowance, recall-heavy.

The thresholds come from dumping the features of all 9 maps; then each strategy is forced on all maps in the arena to check the classifier picks the best one. No map names or coordinates in code (rule 8): only features.

**Draft memory layout (1,024 bytes, read-only after the draft).** Header: version, number of bodies, picks, strategy id. Per camp group (~8 bytes): anchor tile, gems, gold, HP, walking distance from our spawn, nearest altar and its distance, which side it's on. Opening targets per body: the first 2–3 groups, no overlap, our side first. **As built (14 Oct, `plan.py`):** version, group count, strategy, n, sorted body types, one opening group per body. Each draft turn calls `submit()` **before** `pick()`: submit after pick raises *"Memory access requires the owning team's input boundary"* [measured, 2.1.6].

### Shared memory (8 bytes, live)

- Bytes 0–5: one per body: 6-bit target group + 2-bit status (farm / home / fight / dead).
- Bytes 6–7: one beacon: 2-bit kind (SOS / prey / danger), 2-bit round stamp, 12-bit cell (x//2 + (y//2)×50).

### Testing

Arena vs `starter-python`, vs `tzunami444`, and later a small "hunter" sparring bot that chases carriers. Old versions via `NAME@REV`. Metrics: boot round, gems by round 300, deaths, gems lost, and the worst map. Each layer stays only if it beats the previous one.

### Build order

1. L0 core + picks + strategy byte (strategy not yet used): beat the starter on 9/9 maps, both sides.
2. L1, L2, L3, L4 one at a time, each A/B'd.
3. L5 fights. Then comp A/B and strategy thresholds. Done 14 Oct (1–3 built; comp and strategy A/B still to do).
4. **Pairs and engagement (agreed 14 Oct, next).** See below.

### Pairs and engagement (agreed 14 Oct)

**Status (14 Oct, late):** pairs built and kept, with the pair capturing together (`SQUAD_SPLIT`). Engagement as built (`ENGAGE`: fight or retreat to the team by a strength comparison) lost badly (salt 0: 5W/13L, −164) and is off; it needs a new design, ideally after watching the ladder's best teams fight. The draft still picks FARM/CONTEST/ROAM; a separate opening per pair was worse (45W/27L vs 53W/19L) and was dropped. Trios on CONTEST maps (`STRAT_LAYOUT`) were worse too.


- **Pairs are the basic unit.** Cassi & Issac always together (Issac tanks, Cassi hits from range; they die together [rules]). Other bodies pair as tank + damage; an odd body plays solo. The tank leads: it chooses the target with the pair's combined dps and its own HP; the partner reads the tank's claim byte and follows. Group takes (`take()`, tank pulls, stand tiles) become the pair's normal way of clearing. If the partner is dead or home, play solo. **Elks are team jobs**, never solo grinds with heal trips (on elkring a half-cleared solo elk gets finished and captured by the enemy).
- **Engagement.** 1v1: the stronger side fights, the weaker retreats. If they are grouped and we are solo, retreat **towards our team**, then re-evaluate together: fight, or at least trade deaths (a kill pays their bag + 50 gold [rules]). A side's strength is to be defined from what a body sees (e.g. sum of dps x sum of HP, Lanchester-style) plus the value of the bags at stake: provisional, A/B it.
- **Draft.** FARM/CONTEST/ROAM is still chosen per map; the draft also plans the pairs and an opening per pair.

---

## 0. What the numbers say (read this first)

Everything below rests on these facts. All are [rules] arithmetic unless tagged otherwise.

1. **The starter is fast.** Starter vs starter, both teams together, reaches 1,000 gems between rounds 492 and 1,404, at 0.7–2.1 tributed gems per round per team **[measured]** (`ECONOMY.md` → Baseline). Our v1 makes 0.62 per round and wins 7 of 18 **[measured]**. **Farming throughput is the first battle.** Fights only pay if they beat farming (P2).
2. **Monsters hit the nearest champion** **[rules]** (ties go to the lowest unit id **[measured A2]**). In a group take, only the champion closest to each monster takes its damage. Ranged allies take none as long as the melee tank is **strictly** nearer to every awake monster.
3. **Range 4 out-ranges every camp.** All camps have attack range 3 **[measured A31]**. These spells reach 4:
   - Cassi 2×F;
   - Stellar 2×F, and 1.4×F in an area;
   - Marcella 2×F;
   - Tavi 2.2×F;
   - Prism 1.5×F, and 1×F in an area;
   - Ren 1.25×F;
   - Ryth's ground stun.

   Cast from range 4, they are free damage on a camp. Whether area spells hit camps at all is **[provisional A22]**.
4. **Packs punish solo champions.** A pack of n wolves, killed one at a time by team damage D per round, deals `20 × (1350 / D) × (n + (n−1) + … + 1)` to the nearest champion:
   - 3 wolves at D = 210 (3 champions): ~770, survivable for a 1,200-HP tank;
   - 3 wolves at D = 69 (solo Ryth): ~2,350, death.

   That is the v1 loss on packs and rows **[measured]**. It is a P10 problem.
5. **Varg's splash is made for packs.** Basic attacks splash Strength onto everything within radius one of the target **[rules]**. Monsters in a group are cardinally connected **[rules]**, so the middle wolf of a line of three touches the other two. Hitting it deals 3 × 50 per attack: ~168 per round, against ~56 on a single target.
6. **A dash is 25% faster travel.** Walk 1 plus dash 2 ("Walking: Compatible") is 3 tiles in one turn every 8, so 10 tiles per 8 rounds instead of 8. On big maps (lanes: every group ≥ 31 tiles from spawn **[measured]**), the dashers are Vendetta, Ren, Vesper Vale and Issac.
7. **The draft cannot deny.** Both teams may pick the same champion **[rules]**. There is no value in "taking a champion away". We draft for our own fit, plus counters in the late picks.
8. **Kills are worth the bag.** The killer gets the victim's bag plus 50 gold, and the victim sits out 60 rounds **[rules]**. An empty kill is worth ~13–18 gems of tempo (60 rounds × 0.22–0.3 gems per round alive **[measured A12]**); a 60-gem carrier ~75. **Hunt carriers, not champions** (P8, P13).
9. **Channels are windows:**
   - any damage cancels a recall;
   - a stun cancels a tribute or a teleport;
   - a new altar lock cancels a tribute **[rules]**.

   A champion channelling is a champion that can't fight back (P15, P20).
10. **Fights are long and hard to escape.** Base HP is 700–1,200 and damage per round 50–80, so 1v1 time-to-kill is ~9–15 rounds. Everyone walks at 1, and ranged champions can't move and attack in one turn. Once engaged, only a dash or a stun gets you out. **Numbers decide** (P11): in the Lanchester square-law model of focus fire, a side's strength grows with the square of its numbers, so 2v1 is not "a bit better", it is a rout. That model is our working assumption **[provisional A39]**, to be checked against arena fights.

---

## Pillar 1: draft and opening (P1, P5, P6, P12, P14, P17, P18)

### What the draft bot has [rules] [sdk] [measured]

- The whole map: walls, holes, bushes, altars, `spawn_region(team)` for both teams, `symmetry()`, and `camp_groups()` (since 2.1.4, A19).
- `draft.team_size()` (3–5), `current_draft(Team.ALLY / ENEMY)`, and `pick(champion)`. Picks are simultaneous and revealed as they go, so in later rounds we see the enemy's earlier picks.
  - **[provisional A38]**: whether the enemy's same-round pick is visible depends on turn order. Measure it.
- **~24.6M fuel on the first draft turn [measured]**, ten times a play turn. Spend it on map analysis.
- **1,024 bytes of draft memory**: `cambc.draft_memory.submit(bytes)`, last submit wins. It becomes read-only for every champion in play.
- Missing a pick means random picks **[rules]**. Always pick something, inside a `try`.

### Draft method

Draft by **score, not a fixed list**. Each candidate gets:

```
score(c) = Σ_features w_f × fit(c, f)  +  counter(c, enemy picks so far)  +  synergy(c, our picks so far)
```

**Map features**, all computed from `camp_groups()` and distance fields on the first draft turn:

| Feature | Read from the map | Favours |
| --- | --- | --- |
| Pack share: groups with ≥ 2 striking monsters | group sizes | Varg (splash), Stellar (area), a tank (Ryth, Marcella) |
| Gem-cluster share, many small groups | camp kinds | Cassi & Issac (2 bodies = 2 parallel captures), Vendetta |
| Mean walking distance to groups and altars | distance fields | dashers: Vendetta, Ren, Vesper Vale, Issac |
| Elk share | camp kinds | tank + DPS pair, Jungle emblem |
| Team size 3 | `team_size()` | Cassi & Issac (4 bodies from 3 picks) |
| Contested centre (groups at equal distance from both spawns) | both spawn fields | fight power: Tavi, Ryth, Vendetta |

**Counters**, from enemy picks already revealed:

- ≥ 2 enemy stunners (Cassi, Ryth, Prism, Tavi, Ren, Marcella's enhanced attack) → Marcella (stun-immune) as our carrier.
- Enemy Cassi & Issac → burst (Tavi, Stellar). Killing Cassi (700 HP) kills both and pays both bags.
- Enemy basic-attack heavy (Vendetta, Varg, Vesper Vale, Issac) → Ren (retaliation).

**Synergy**:

- one tank per team (Ryth or Marcella) for group takes;
- at most two "spell-only" ranged champions;
- at least one stunner, for denial (tribute and recall breaking).

**The weights are provisional [A39]** and the draft is the most measurable thing we have. Matches are deterministic, so a fixed draft gives a fixed game. **Before tuning weights**, A/B whole compositions in the arena, using every map from both sides, against the starter and against each other.

| Candidate comp (first picks first) | Idea |
| --- | --- |
| **A** Vendetta, Ryth, Marcella, Varg, Stellar | current v1 |
| **B** Varg, Ryth, Stellar, Vendetta, Tavi | packs and group takes |
| **C** Cassi & Issac, Ryth, Vendetta, Varg, Stellar | bodies: parallel captures |
| **D** Ryth, Vendetta, Tavi, Stellar, Ren | fight-ready |

The winner becomes the default order. The score function then only overrides it when a map feature or a counter is strong.

### Draft memory layout (v1, 1,024 bytes)

The draft does the expensive map analysis once, for every champion. In play, each body would otherwise redo it on its own first turn.

| Bytes | Content |
| --- | --- |
| 0 | layout version (reject unknown versions, fall back to computing in play) |
| 1–2 | team size; number of bodies (Cassi & Issac = 2) |
| 3–8 | our picks (`ChampionDraft` ints), in slot order |
| 9–14 | enemy picks as last seen |
| 15 | plan flags: aggression level 0–3, "contest centre" bit |
| 16–21 | opening target per body slot (group index, 255 = none) |
| 22 | number of groups G (cap 192) |
| 24 … 24 + 4G | per group, in `camp_groups()` order: our walking distance (capped at 254, 255 = unreachable); their distance; value byte (gems + gold value per round of clear, scaled); flags (side ours/contested/theirs, pack, monolith, near-altar) |

That fills ~800 bytes for 192 groups. The remaining space holds an altar table: nearest altar per group, and altar distances from both spawns.

### Opening (P12 tempo, P9 attack where they are not)

- **Turn 1:** each body heads straight to its pre-assigned group from draft memory, with no search on the first play turn.
- The opening targets are **gem clusters on our side first**: 24 gems in 500 HP, no damage taken, ~6–10 rounds solo.
  - Then wolves on our side; packs go to two bodies.
  - **Contested centre groups only with ≥ 2 bodies** (P10), and only if the plan flag says contest.
- **No opening group closer to the enemy spawn than to ours**, unless the map has nothing on our side (P9).
- Ward (free, permanent) at the first fork towards the enemy half: early warning (P6).

**Test:** gems at round 300; first-blood rate; opening vs no opening.

---

## Pillar 2: general behaviour rules (P2, P3, P4, P8, P10–P15, P19–P21)

### Utility, not a script

Each turn, each body scores its candidate goals and runs the best one. Principles are score terms or vetoes, so each can be switched off and measured (CLAUDE.md, rule 4). Order of evaluation:

```
0. REFLEX     split-second overrides (Pillar 5); may end the turn
1. SURVIVE    flee / heal / recall          (P3)
2. BANK       go tribute                    (P3, P12)
3. HELP       answer an ally's SOS          (P10, P19)
4. HUNT       strike a visible enemy        (P4, P8, P13, P15)
5. TAKE       group take of a strong camp   (P10)
6. FARM       best group by gems per round  (P2, P12)
7. ALWAYS     shop on spawn; place ward; write comms   (P6, P19)
```

### The rules

The user's examples are R1–R4. The rest come from the numbers in section 0.

| # | Rule | Principle | Status |
| --- | --- | --- | --- |
| R1 | **No enemy in vision → farm** the best group by `(gems + GOLD_VALUE × gold) / (travel + clear + capture)`, skipping groups an ally has claimed | P2, P12 | built (v1) |
| R2 | **An ally is fighting nearby → help**, if the SOS cell is ≤ `HELP_RADIUS` tiles away and the fight is winnable with us added (Lanchester check below) | P10, P19 | to build |
| R3 | **Enemy with the biggest bag in view and our team around → focus it**. Target score = `(bag + kill tempo) / rounds to kill`, gated by local strength | P8, P13 | partly (v1 fights single targets) |
| R4 | **Low HP with many gems → bank.** Go to the altar if it is closer than the threat; recall only when nothing can hit us (damage cancels it) | P3 | built (v1) |
| R5 | **Never start a recall** within reach of an awake camp or a visible enemy | P3 | built |
| R6 | **Clear only what we can capture.** Don't start a camp we can't finish and hold for 5 rounds: the enemy captures it **[measured A7]** | P13 | built |
| R7 | **Capture alone.** After the last monster dies, one body captures and the others move on (the reward is split among those present **[rules]**). Exception: an enemy is in view, so stay and hold | P12 | built (`GROUP_TAKE`): the claimer nearest a spawn tile captures (ties to pick order). A capture an enemy contests for `CONTEST_MAX` rounds is dropped for `CONTEST_SKIP` [provisional A47] |
| R8 | **Group take for packs and elks:** the tank stands nearest every monster, ranged allies stand at 2–3 behind, and everyone hits **the same monster**, the lowest HP first, so the incoming damage drops fastest | P10 | built (`GROUP_TAKE`): tank = the highest-HP ally on the group. Others pick a tile no monster targets them on (nearest champion, ties by pick order [measured A2]); ranged allies prefer far tiles. Focus = most strength per HP first (Smith's rule); range-4 spells on the focus |
| R9 | **Vulture.** An enemy fighting a camp nearby → wait outside camp range (4+). Strike when the camp dies (they're hurt, and the capture is ours) or when their HP falls below our burst | P13, P15, P20 | to build |
| R10 | **Contest captures.** An enemy capturing in reach, and we are safe → step onto the region: their 5-round timer resets **[rules]** | P13 | to build |
| R11 | **Break channels:** stun a tribute, hit a recall, place a lock on an altar with an enemy channelling | P15, P20 | to build |
| R12 | **No chasing** past `CHASE_MAX` tiles, into bushes, or within `SPAWN_AVOID` of their spawn | P16, P21, P23 | partly |
| R13 | **Score-aware endgame** (`global_submitted_gems` for both teams): ahead → bank everything, avoid fights; behind late → hunt carriers; enemy within one bag of 1,000 → everyone denies (stun, lock, contest) | P15, P18 | partly (end margin) |
| R14 | **Victory sprint:** our score + team bags ≥ 1,000 → everyone banks now | P12 | to build |
| R15 | **Avoid known danger:** the farm score is discounted near a DANGER beacon or the last-seen enemy position, and on their half | P9 | to build |
| R16 | **Shop whenever on spawn** (including while dead); consumables when gold > build needs | P12 | built (shards) |

### Fight check: Lanchester, not vibes (P1, P4, P11)

Use only what this body sees. Let `D` be damage per round, averaged over the 8-round cycle with abilities that are ready counted in, and `H` be current HP plus shield.

```
strength_us   = (Σ D_us)   × (Σ H_us)        allies within FIGHT_RADIUS (+ an SOS-bound ally arriving in ≤ 2 rounds)
strength_them = (Σ D_them) × (Σ H_them)      + awake camp Strength hitting us if we stand in their range
fight         if strength_them ≤ FIGHT_EDGE × strength_us   and   kill value > time lost farming
```

For 1v1 this is exactly v1's rule (`bot.py` → `fight`): fight when the rounds we need to kill them are ≤ `FIGHT_EDGE` × the rounds they need to kill us, since `(H_them / D_us) ≤ e × (H_us / D_them)` ⇔ `D_them·H_them ≤ e × D_us·H_us`. So `FIGHT_EDGE` (0.8) keeps its meaning. A stun of d rounds removes d rounds of the stunned unit's damage. Kill value = bag + 60 × their income per round + 50 gold × `GOLD_VALUE` **[rules]** structure, **[measured A12]** income.

**Test:** K/D and gems lost, with each rule on vs off (R2, R3, R9–R11 separately).

---

## Pillar 3: per-champion kits (P5 know yourself)

### Generic first, then specials

Every ability is described by the SDK: `is_damage`, `is_cc`, `is_dash`, `is_attack_reset`, `is_shield`, `is_heal`, `is_aoe_damage`, `damage_amount()` and range **[sdk]**. One generic engine drives all 11 champions from those flags. Per-champion code only exists where a passive changes the decision. So a champion we never tested still plays sensibly, and drafting any champion is safe.

Generic ability use:

| Kind | On camps | On champions |
| --- | --- | --- |
| Attack reset | right after a basic attack, if the target is still in range (+1 attack per 8 rounds) | same; time it so the burst kills |
| Single-target damage (range 4) | from range 4 when possible: free damage (section 0.3) | to secure a kill or open a won fight |
| Area damage | on the tile that hits the most monsters, if A22 says it hits camps | on the tile that hits the most enemies |
| Stun | hold it if any enemy has been seen in the last `STUN_HOLD` rounds. Otherwise use it on a camp only if A23 says a stunned monster skips its hit | first: break a channel (R11). Then stop an escape or a burst |
| Dash | travel: on cooldown when the path is long and no enemy has been seen (+25% speed) | escape when the reflex says danger; chase only to secure a kill |
| Shield (Varg) | when taking camp damage | when an enemy can hit us next round |
| Heal (Willow) | the most-missing-HP ally in range 4, when missing ≥ heal amount | same; priority to the carrier |

### Specials (only these need their own code)

| Champion | Role in our plan | Special rule |
| --- | --- | --- |
| Vendetta | assassin and farmer, top camp damage (~79 per round) | a kill resets her ability cooldowns, camp monsters included **[rules]**. So spend the reset and dash freely when a kill is one or two hits away: the kill refunds them for the next monster or an escape |
| Ryth | tank, area stunner | Health shards also add Strength (1% of bonus HP) **[rules]**, so build Health. Area stun on packs if A22/A23 hold |
| Marcella | stun-immune carrier and anchor | the enhanced reset stuns: **save it for champions** (channel breaks, peels). Our designated big-bag carrier against stunner comps |
| Varg | pack farmer | target the monster with the most living neighbours (splash). Shield on camp damage |
| Stellar | ranged nuker | single 2×F on camps from range 4. Area 1.4×F on the most-monsters tile |
| Tavi | striker, stunner | **buys shards anywhere** **[rules]**: buy the moment gold ≥ 30, no trip home. 2.2×F stun is our best channel breaker |
| Ren | skirmisher | retaliation 0.2×F per hit taken. If A24(a) holds (camps trigger it), Ren tanks packs: +20 damage per wolf hit |
| Cassi & Issac | two bodies | **split** on zero-damage targets (gem and gold clusters) for parallel captures. **Together** near enemies or on wolves (Issac tanks, Cassi behind). Linked death: both retreat when either is low; the pair's danger is Cassi's HP |
| Vesper Vale | farmer, gold | Treasure emblem (20% + 20%). Dash for travel |
| Prism | controller | +0.2 Focus per carried gem: bigger bag, bigger spells. Still banks on the normal rule |
| Willow | healer | stays with the tank on group takes: 3×F heal per 8 rounds (~39 HP per round) offsets most of a pack's damage |

### Builds [provisional A14]

- Farmers: Monster emblem (+10% camp damage), then Strength.
- Tanks: Jungle emblem (−30% camp damage), then Health; Ryth gains Strength from Health anyway.
- After that, Power shards (6 shards' stats for 5).
- A/B against the current build (5 Monster Strength + 5 Jungle Health) per role.
- **Measured 14 Oct (tzunami-lite, 4 salts vs tzunami444):** the DUAL build (5 Monster Strength + 5 Jungle Health, then Power Strength) on every body but Cassi (Focus) took the record from 53W/19L, +100 to 60W/12L, +241. The per-role build left the tanks with no extra damage. Shipped: `BUILD_DEFAULT = DUAL`.

**Test:** per-champion gems per round and deaths across comps. Each special is a switch.

---

## Pillar 4: communication in 8 bytes (P19 unity, P6 foreknowledge)

### Constraints [rules] [sdk]

- 8 bytes per team, readable and writable all match; each team has its own.
- Each body runs its own bot with no shared vision, so champions act on what's in shared memory.
- Writes are seen by teammates who act later, in the same round or the next.

Up to 6 bodies: 5 picks, with Cassi & Issac counting as 2.

### Layout v1 (64 bits)

```
byte 0..5   one byte per body slot (slot = draft order; Cassi & Issac take two)
            bits 7-6  status   0 farm/travel · 1 bank/heal · 2 fighting · 3 dead
            bits 5-0  target   0 none · 1..63 = group index + 1 (draft-memory ranking if > 63 groups)

byte 6..7   the team beacon (16 bits)
            bits 15-14  kind    0 none · 1 SOS (I'm fighting, come) · 2 PREY (carrier or channeller seen) · 3 DANGER (enemy group, avoid)
            bits 13-12  stamp   round & 3
            bits 11-0   cell    (x // 2) + (y // 2) × 50   (100×100 → 2,500 cells < 4,096)
```

Rules:

- **Freshness.** A beacon counts only if `(round − stamp) & 3 ≤ 1`, so the writer must refresh it every turn while the event lasts. A dead or busy writer's beacon fades by itself.
- **Priority.** Overwrite a live beacon only with a higher kind (SOS > PREY > DANGER) or your own refresh.
- **Claims.** The target byte replaces v1's claim byte. Status lets a body see that an ally is banking or dead, and re-plan their group.
- **Cost.** One 8-byte read per turn, one write of our byte, and the beacon only when needed.

Later, once v1 is measured:

- an aggression "mode" set by the lead body from the score (R13);
- each body's bag size, coarse (2 bits), so the team knows who carries what (R14);
- a rally cell for group takes.

**[provisional A37]**: which fields of an out-of-vision ally are readable. `cambc.champions(Team.ALLY)` lists them, but `champion_name()` raises **[measured]**. If `is_alive()`, `priority()` or `gem_count()` read, they are free information outside the 8 bytes. Measure before using.

**Test:** comms on vs off (each body sees only its own state). Count duplicate camp targets and the SOS response time.

---

## Pillar 5: split-second decisions, the reflex layer (P3, P14, P15, P20)

### Idea

Before the planner runs, a cheap check looks for moments that win or lose the game. This is the FPS "clutch": a kill confirm, a peel, a disengage. **Fast path:** if no enemy is in vision and no camp is hitting us, the reflex costs one `vision.champions(ENEMY)` call and returns.

Reflexes, first match wins:

| # | Trigger (all from visible state) | Action | Principle |
| --- | --- | --- | --- |
| X1 | **Lethal:** an enemy's HP ≤ our burst this turn (basic + reset + ready damage spell, in range now or after one step) | kill it. Its bag is ours | P8, P13 |
| X2 | **Channel window:** an enemy recalling within our reach (any damage cancels it), or tributing within stun range | hit / stun. Lock the altar if we have one | P15, P20 |
| X3 | **We die next round:** incoming burst (enemy reach + awake camps) ≥ our HP + shield | shield, then dash away / step to the safest tile. Never recall here | P3 |
| X4 | **Bag at risk:** carrying ≥ `BAG_GUARD` and an enemy we can't beat (Lanchester) is within 6 | disengage towards the altar or spawn; DANGER beacon | P3, P9 |
| X5 | **Peel:** a visible ally below 35% HP being hit, and we can stun or kill the attacker | stun / strike the attacker | P10, P19 |
| X6 | **Bait refusal:** the target is in a bush, or the chase leads into an awake camp's range or past `CHASE_MAX` | let it go | P16, P21 |

### Micro: score the 9 tiles

In any fight, score each candidate tile (stay + 8 moves) and take the best. This is XSquare's method, and MIT Battlecode teams still use it in 2026 (Generalized Stroke's Theorem postmortem). Per tile:

- expected damage next round: each enemy's reach (melee 1 + move 1 or dash 2; ranged 3, or 4 for spells) and awake camps (range 3);
- can we hit our focus target from there;
- distance to allies (cohesion, P10);
- bush (hidden, P17);
- distance to our altar or spawn when carrying.

Nine tiles × a few units should be cheap; measure it with `TRACE`.

### Turn order as a weapon (P14)

- Champion turns alternate between the teams, and the team that goes first swaps every round **[rules]**. So each body can work out, every round, which enemies act before it and which after.
- `set_priority` (effective next round **[rules]**) sets our order. Put the body that must act first (stunner breaking a channel, low body escaping) first.
- A tribute completes at our *next turn start* **[rules]**. Start channels on rounds where the enemy can't act in between, when that matters.

**Test:** each reflex on vs off. Measure kills, deaths and gems lost per game, and the enemy tributes we cancel.

---

## Fuel: how we stay inside 2.5M per turn

Facts **[measured]** (cambc 2.1.5, `ARCHITECTURE.md`; 2.1.6 moved the boot cost out of the game, A48):

| Cost | Fuel |
| --- | --- |
| Compiling source | **~55k per line of code, ~6k per comment line** (A29). tzunami444 (~1,100 lines) boots round 1 → 57. No precompiled bytecode in submissions (`GETTING_STARTED.md`), so code size costs rounds |
| `camp_groups()` | ~0.74M per call: once per game |
| `DistanceField` | 80×80 ~285k; 100×100 ~450k (scaled, not measured) |
| `move_towards()` | ~100k: we use our own cached fields instead |
| `vision.camps()` | 20–31k; host reads a few k each |
| `import traceback` | freezes a champion ~136 rounds: never |

Budgets [rules]: 2.5M per turn for Python, 2× on the first play turn, 10× on the first draft turn. An overrun suspends the bot mid-turn and it resumes next round, so it loses a turn.

Practices:

1. **Precompute in the draft:** group table and opening (Pillar 1). Every body inherits it for free.
2. **Cache per game:** walls, the camp table, the altar field and the spawn field. Distance fields to targets are built lazily and bounded (LRU), and **only with spare fuel**: check `fuel_remaining()` before optional work, and defer it to next turn when it's below `FUEL_RESERVE`. This is XSquare's end-of-turn use of spare bytecode.
3. **Let the host do loops:** `Bitboard` ops, `DistanceField`, `shadow_cast`, `reachable_tiles` cost fixed host fuel; Python loops over tiles cost per bytecode.
4. **Fast paths:** no enemy in view means no reflex and no micro. A body walking a cached field does one lookup per step.
5. **Hot loops:** local aliases, no attribute chains, no `try` inside loops, no per-turn allocation.
6. **Measure, don't guess:** `TRACE` logs fuel per phase. **[provisional A39 part b]**: interpreter cost per simple Python op on the engine; measure it once with a probe loop.

---

## How we test (from the competition literature)

- **One change at a time**, behind a config switch, judged by the arena: all maps, both sides, against the previous version (`tzunami444@REV`) and the starter. Keep it if the total is better and the worst map is not worse. A near-50% result on a change we believe in: keep it, but check for bugs first.
- **Watch replays of every loss.** Follow single units into fights and ask why they chose that. Both the XSquare guide and the Generalized Stroke's Theorem postmortem name this as a main source of improvement.
- **Feature maps:** once the map generator exists, use small open maps to test micro and pack-heavy maps to test group takes.
- **Generalise:** no map names, coordinates or routes. Tournaments use unseen maps.
- **Copy what works:** once the ladder opens, watch top teams' replays and adopt their macro (P6).

---

## Build order to the Sprint 1 lock (17 Oct; submit by 16 Oct)

| # | Item | Fixes / adds | Done when |
| --- | --- | --- | --- |
| 1 | **Group takes** (R8, R7) + generic range-4 spells | packs and rows losses | packs and rows won from at least one side; nothing else worse. **Done 13 Oct** [measured]: 18W/0L vs the starter, 9/9 maps both sides, 1.73 gems/round, source only (no bytecode, boot to round 57; 1.94 with bytecode). Switch off: 15W/3L, rows lost. Open: 10W/8L against itself with the switch off; packs lost from both sides there (see `HANDOFF.md`) |
| 2 | **Draft memory v1** (group table, opening targets) + comms layout v1 (status + target bytes) | turn-1 search; duplicate targets | gems at round 300 up |
| 3 | **Draft comp A/B** (A–D above) | composition | best comp chosen by arena |
| 4 | **Reflex X1–X3** + Lanchester fight check | free kills, deaths to burst | K/D up, gems lost down |
| 5 | Endgame R13, R14 | close games | no loss with more gems carried than the margin |

Then for the 24 and 31 Oct locks, roughly in order:

- the beacon (SOS / PREY / DANGER) and R2, R9, R10;
- micro tile scoring;
- the draft score function with counters;
- wards;
- altar locks and R11;
- per-champion specials;
- builds A/B;
- A37–A39.

**Set `TRACE = 0` before every submission. Submit source only: no `.bin` or other generated files in `bots/tzunami444/`.**

---

## Open assumptions raised by this plan

Registered in `ASSUMPTIONS.md`:

- **A36**: v1 thresholds (`HP_RESERVE`, `MAX_TRIPS`, `RETREAT_ROUNDS`, `FIGHT_EDGE`).
- **A37**: readable fields of out-of-vision allies.
- **A38**: when the enemy's draft picks become visible.
- **A39**: draft weights and the interpreter's fuel per op.
- **A46**: held altars (`ALTAR_GUARD`, `ALTAR_AVOID`).
- **A47**: group-take knobs and the cross-team monster tie.

Already open and needed here:

- A22 (area spells hit camps);
- A23 (stunned monsters skip their hit);
- A24 (Ren's retaliation on camps);
- A25 (ranged dash + attack).

**What we won't do:** read engine internals that bypass the SDK's vision checks (e.g. raw `_bc` calls), or hard-code anything about a map.

## Sources

- XSquare (Ivan Geffner), [Battlecode guide](https://battlecode.org/assets/files/battlecode-guide-xsquare.pdf): modular primitives, test against old versions on both sides, one upgrade at a time, simple beats complex, don't overfit maps, use engine-provided fixed-cost methods, spend spare compute at turn end.
- Generalized Stroke's Theorem, [MIT Battlecode 2026 postmortem](https://battlecode.org/assets/files/postmortem-2026-generalized-strokes-theorem.pdf):
  - state updater + behaviour classes;
  - bit-packed messages with a type header;
  - "XSquare-style" 9-tile micro scoring;
  - sharing health and nearest-enemy data every turn in fights;
  - improve micro by watching games;
  - copy top teams' macro.
- [5 Musketeers 2022 postmortem](https://battlecode.org/assets/files/postmortem-2022-5-musketeers.pdf) and [Cout for Clout 2024 postmortem](https://battlecode.org/assets/files/postmortem-2024-cout-for-clout.pdf): comms and micro patterns (attacker/healer micro).
- [Cambridge Battlecode](https://battlecode.cam/) and [olifog.com/projects/battlecode](https://www.olifog.com/projects/battlecode): event infrastructure (no gameplay tips published).
- Lanchester's laws (square law for aimed fire): the basis of the fight check.
