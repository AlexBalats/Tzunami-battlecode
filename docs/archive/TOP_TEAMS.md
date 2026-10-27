# Three top teams, reverse-engineered from 78 of their wins (23 Oct)

The goal: watch a top team's own games (not our losses to it), pattern-match what it does, and set each habit
against how our bot (`bots/cpp`, = cpp-p6 plus the other session's work) does the same thing, to find what we can
copy. **No code was written**. Replays: `other_stuff_for_now/team1/`, `team2/`, `team3/`. The winner of each replay is the team studied. Replays were read with the existing decoder (`tools/replay/decode.mjs`) and scripts
(`tools/replay/farm/*.py`, plus one-off queries); scratch files are in the session scratchpad.

Tags as in CLAUDE.md: **[measured]** = counted in these replays; **[rules]/[sdk]** = from `GameRules.md` / `cambc.h`;
**[guess]** = my reading of why, not confirmed. "Top" = the top team, "opp" = its opponents in these games (mostly
meta drafts and other strong teams: they also use some of the same tricks).

## A. All three teams together (the collation)

**78 wins read**:
- team 1: a fixed Prism draft, 18 wins (§0–§8);
- team 2: a different draft every game, 24 wins (§9);
- team 3: a fixed draft with no Prism, 36 wins on 24 maps (§10).

§11 sets our own numbers (cpp-p6's 38 ladder losses) beside theirs. A habit in all three is a rule of good play, not
one team's style. Every rule is written to read the game state (score, bags, walks, HP, cooldowns), never a map, so
it carries to unseen maps (CLAUDE.md rule 10). The action plan for the main session is in
`docs/archive/COPY_PLAN.md`.

| # | Rule, written map-free | T1 | T2 | T3 | Us (p6 losses) |
| --- | --- | --- | --- | --- | --- |
| 1 | **Bank small and often** | 32 banks a game, bag 21 | 30, bag 23 | 29, bag 26; a tribute next 93 % once the bag is ≥ 50 | **15 banks**, bag 15; a rate price |
| 2 | **Keep hitting camps**: camp hits per 100 live rounds | 18.3 | 16.2 | 16.5 | **9.3** (our opponents 13.4) |
| 3 | **Use every ability on cooldown** (Vesper casts per 100 live rounds; Vesper's dash) | 12.7 | 12.4; 7.3 | 12.1; 7.4 | **6.4; 2.9** |
| 4 | **Start the fight: nearest enemy, when you outweigh it (max HP ≈ 1.13–1.15×) and aren't outnumbered** | 199 of 290 started, 154–72; nearest 88 % | 361 of 523, 331–98; 92 % | 423 of 739, 455–123; 91 %; ratio 1.13 | Open 8.1 a game, they open 10.0 on us; deaths 12.1 |
| 5 | **Closing rule** (banked + carried ≥ 1,000 → all tribute) | Clear (the Prism dump) | Reached 5–60 rounds before the end | 25 rounds before the end | None; lost holding 980 |
| 6 | **Own altar lock just before your own tribute** | 68 locks, half 0–1 rounds before | 0 | 152 locks, 93 within 6 rounds of their own tribute | Bought, never placed |
| 7 | **Draft core: Heart of Ruin + Marcella + Vesper** | 18/18 all three | Heart of Ruin 17, Marcella 14, Vesper 11 of 24 | Heart of Ruin, Vesper 36/36, Marcella in every 5-body game | Vesper only |
| 8 | **Bruiser builds, Treasure early** | Yes | Bruiser Health melee, Power damage | Bruiser Strength on Vesper / Vendetta | Bruiser Health + Power Strength |
| 9 | Teleport on long walls / rivers | 0 | 218, median 78 tiles saved | 0 | 0 |
| 10 | Pre-charged recall | Every turn | No | No | No |

**Not gaps** [measured, §11]: wards (we place 169 a game; they place 88–431), recall HP (we 0.45, they ~0.40),
spreading out (everyone has about half their body-rounds alone), fuel (team 2 rolls over 21 times a game and wins).

## 0. Team 1: what to copy, ranked

| # | Their habit [measured] | What we do now | Copy? |
| --- | --- | --- | --- |
| 1 | **Closing rule**: once team banked + gems carried by the whole team reaches ~1,000, **every carrier tributes at once**. Banked + carried at that moment: 910–1,063 in all 16 games where Prism dumped | No end-game rule: `score_us` only sets the posture (`prices.cpp:68`). p6's hoard losses (LADDER_P4 §10: 01the-farm 25–1012 **holding 980**, 00corners 956–1012 holding 108) are exactly this | **Yes, first.** Cheapest, and it turns some losses straight into wins |
| 2 | **Small, frequent banks** by the non-Prism bodies: 549 tributes, median bag **21** (p25 8–11, p75 33–37), a median 15 rounds after the last gem gain; 32 banks a game vs opp 12.7; first bank r70 vs opp r134 | Bank priced as a rate `bag·(1+P)/(walk·ret + chan)` (`prices.cpp:386`), which can't rise past ~11 a round whatever the bag (LADDER_P4 §10.2) | Yes, but as a cycle, not a threshold: after 88 % of gem gains the next stop is a tribute, at any bag and walk (§2) |
| 3 | **Own altar lock before tributing**: 68 locks; 61 placed with no enemy tribute within 3 rounds; the most common case is 1 round before their own tribute at that altar (26 of 68; 0–6 rounds: 43 of 68). Altar lock is among their first buys (31 in the early items) | We **buy** a lock (`champs.cpp:130`, 10 gold) and **never place it** | Yes. [sdk] one lock per altar (`invalid_action_altar_lock_already_locked`), so our own lock means no enemy lock can cancel our channel [rules], and the enemy can't tribute there until it has hit the lock 5 times |
| 4 | **Recall late**: completed recalls peak at **30 % HP** (156 of 682 at 0.3; median 0.5 because shop trips at full HP count too); 0 gems in the bag (they bank first); 73 % shop within 3 rounds | `RETREAT_HP 0.6` [R9 guess] (`champs.h`) | Test: 0.6 → 0.35. Risky without their fight strength; judge on deaths too |
| 5 | **Pre-charged recall**: every turn, cancel last turn's recall → act → start a new recall. 3,982 recalls a game; two opp teams do it too | Recall only when we decide to go home (`safe_recall`, `beh.cpp:56`) | Yes, cheap: one turn off every recall (5 → 4) [rules: the starting turn counts; damage cancels it anyway] |
| 6 | **They start the fights, at full HP**: 163 fight openings after 15 quiet rounds vs opp's 65; hit first in 68–72 % of fights; even fights 57 kills to 24, **outnumbered fights 64 to 31**. Target = the **nearest** enemy (88 %), not the lowest HP (45 %, about chance) | `duel` P(lose) gate + `KILL_PRICE`; p6 lost the fights the enemy started (58 kills vs 226) | Yes, and it does not need Prism: without Prism they kill 91 and lose 24 (§3). Rule: attack the nearest enemy you outweigh (max HP ≥ ~1.15×) when not outnumbered |
| 7 | **Prism is a gem battery**: solo farmer, banks almost nothing until the close, then dumps 66–624 gems (up to 60 % of the 1,000) in one tribute (two games: 8–23, where the others had banked) | We don't draft Prism | Only with a draft change (§4) |
| 8 | **Marcella is a top gem earner**: most gems of any body (5,699 over 18 games), banks the most often (164), earns 904 gold a game from her passive (2 gold per gem tributed) | Marcella is our 6th pick, so in a 5-body game she's **never drafted** (`draft.h:5`) | With the draft (§4) |
| 9 | **No teleports at all** (0 in 18 games); opp use 9.3 crystals a game | LADDER_P4 §10 queued a teleport shortcut | Lower priority: the best team wins without it |
| 10 | Fuel: 7 rollovers a game vs opp 37 | p6: ~6 a game locally | Fine as is |

Gold is **not** their edge any more: top 5,734 a game vs opp 5,135 (p6 in its losses: 5,828). Their extra is kill
gold (1,412 vs 540): a fight result, not a farm result.

## 1. The team and the record

- **Fixed draft** [measured]: Prism, Vesper, Marcella, Willow, Heart of Ruin; with 4 bodies Willow is dropped. Same
  list in all 18 games, whatever the opponent picks (both teams may pick the same champion [rules]; the mirror
  games had Prism on both sides).
- **18 wins, side A 6, side B 12.** Several were close: 00rows 1000–948, 00gem-fields 1024–749, 00lanes 1010–769,
  00ambush 1033–750, 00pilgrimage 1012–871.
- Deaths 4.9 a game (6.1 % of body-rounds dead) vs opp 12.9 (15.5 %). Max HP medians are about equal (r600 1,550 vs
  1,700): **they don't win on HP**.

| Match | Map | Top side | Bodies | Opponent | Score | End | Deaths top/opp |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2858bcf5 | 00swirl 45x30 | A | 4 | VesperVale, Vendetta, HeartOfRuin, CassiAndIssac | 1065-333 | r1105 | 25/25 |
| 28dd3670 | 00corners 71x71 | A | 5 | VesperVale, Vendetta, HeartOfRuin, CassiAndIssac, Ryth | 1011-187 | r1007 | 6/35 |
| 31a27b61 | 01fracture 61x71 | A | 5 | Marcella, HeartOfRuin, Ryth, Willow, Ren | 1027-358 | r1141 | 4/16 |
| 349d13fa | 00pilgrimage 50x65 | A | 5 | Prism, VesperVale, Marcella, Ryth, HeartOfRuin | 1012-871 | r1801 | 13/14 |
| 36f21e0a | 00eight 41x30 | B | 5 | HeartOfRuin, Marcella, VesperVale, Ryth, Vendetta | 1005-59 | r920 | 0/23 |
| 39a01dc9 | 00reverse-spiral 30x30 | B | 4 | HeartOfRuin, Vendetta, VesperVale, Marcella | 1049-165 | r1202 | 6/26 |
| 40abe1b6 | 01boss-battle 50x41 | B | 5 | VesperVale, Vendetta, HeartOfRuin, Tavi, Marcella | 1226-0 | r852 | 4/16 |
| 58dd7354 | 00split 45x35 | B | 5 | Prism, VesperVale, Marcella, Ryth, HeartOfRuin | 1019-324 | r583 | 1/1 |
| 5c846f37 | 00pilgrimage 50x65 | B | 5 | HeartOfRuin, Prism, Ryth, VesperVale, Marcella | 1007-546 | r1491 | 3/5 |
| 61c86a1c | 00lost-world 35x31 | B | 5 | HeartOfRuin, Marcella, VesperVale, Ryth, Vendetta | 1008-234 | r415 | 2/5 |
| 6c080df4 | 00lanes 90x30 | B | 5 | VesperVale, Vendetta, HeartOfRuin, Tavi, Marcella | 1010-769 | r976 | 0/6 |
| 752ace4a | 00ambush 100x100 | B | 5 | HeartOfRuin, Prism, Vendetta, VesperVale, Marcella | 1033-750 | r1054 | 2/4 |
| a82e867b | 01shortcut 40x40 | B | 4 | HeartOfRuin, Marcella, VesperVale, Ryth | 1018-403 | r1012 | 1/5 |
| a8b520dc | 00split 45x35 | B | 5 | VesperVale, Vendetta, HeartOfRuin, Tavi, Marcella | 1075-501 | r683 | 2/7 |
| a8cfc19e | 00rows 50x50 | B | 4 | HeartOfRuin, Prism, Vendetta, VesperVale | 1000-948 | r1242 | 0/0 |
| afc0bcff | 00eight 41x30 | A | 5 | Prism, Marcella, Vendetta, HeartOfRuin, VesperVale | 1005-208 | r808 | 8/11 |
| b9a9b9f1 | 00gem-fields 50x40 | B | 5 | HeartOfRuin, Marcella, VesperVale, Ryth, Vendetta | 1024-749 | r629 | 1/7 |
| f87007a5 | 01starfish 50x50 | A | 5 | Prism, Marcella, Vendetta, HeartOfRuin, VesperVale | 1028-147 | r1095 | 10/27 |

(Deaths here are death events; the `hpdeath.py` averages above use its own count.)

## 2. Gems: who gathers, who banks, and the close

**Per body, over 18 games** [measured]:

| Body | Tributes | Bag at tribute: median (p25–p75), max | Gems gained |
| --- | --- | --- | --- |
| Marcella | 164 | 22 (11–37), 505 | 5,699 |
| Prism | 26 | **216** (100–279), 624 | 5,161 |
| Vesper | 144 | 21 (8–37), 584 | 4,631 |
| Heart of Ruin | 172 | 21 (11–33), 270 | 4,556 |
| Willow | 69 | 8 (7–21), 88 | 1,083 |

- **Everyone but Prism banks small and often.** The big maxima (505, 584) are the close (below).
- Bank trips: 297 of 549 non-Prism tributes came straight from the field, 252 after a spawn visit in the last 40
  rounds. 432 of 549 had no enemy within 6 tiles.
- Gems lost on death: 108 a game (opp 220). Their death rate per 1,000 live rounds is ~1 at every bag size (opp
  2–6): they don't treat a big bag as more dangerous; they're just rarely caught.

**The bank trigger is a cycle, not a threshold** [measured, team 1, non-Prism bodies, 629 gem gains]: after a gem
gain, the body's next stop is a tribute **88 % of the time**, at every bag size and almost every walk:

| Bag after the gain | Walk to the nearest altar ≤ 10 | 11–20 | 21–35 | 36+ | All |
| --- | --- | --- | --- | --- | --- |
| 1–9 | 90 % (93) | 93 % (29) | 87 % (23) | 88 % (16) | 90 % |
| 10–19 | 93 % (68) | 91 % (45) | 57 % (14) | 84 % (19) | 88 % |
| 20–39 | 92 % (91) | 80 % (40) | 79 % (28) | 71 % (31) | 84 % |
| 40–79 | 88 % (50) | 85 % (27) | 90 % (10) | 93 % (15) | 88 % |
| 80+ | 90 % (10) | 42 % (19) | – | – | 57 % |

- So: **take → tribute → next take.** The median bag of 21 is simply one capture's worth.
- Of the 540 gain → tribute trips, 295 walked straight to an altar (median 7 rounds from the gain to the tribute
  start) and 245 went through spawn first (median 23 rounds: recall, heal, shop, then the altar). They fold the
  shop/heal trip and the bank trip into one.
- Tributes happen a median 18 tiles from their own spawn (quartiles 13–29).
- For us [guess]: "bank after every capture unless the next take is right here" is map-free (it reads only the
  bag and the walks), and it would replace the rate price that never fires.

**Prism, the battery** [measured]:
- It gains its gems **alone**: at 164 of 226 gem gains (73 %, 15 games) no ally stands within 2 tiles, so it gets the full capture
  share [rules: the reward is split between allies present].
- It works far from spawn (median 12–48 tiles away by map). It hits camps: 2,500+ basic attacks on monsters in 15 games; slot 0
  (1.5 × Focus damage + stun) mostly on camps, slot 1 (area, radius 1) mostly on ground tiles (camp clusters).
- [rules, sdk 3.0.5] Prism gets 1.5 Focus per carried gem: at 300 gems, +450 Focus, so slot 0 does ~800 damage
  plus a stun. **The bag is the build.**
- Deaths 1.3 a game (the most of their bodies); in 10 of 15 games it never died.

**The close** [measured]: in every game where Prism dumped, the dump started when team banked + team carried was
≈1,000, and the other carriers tributed in the same few rounds. Example 00rows (they were behind 408–924):
- Prism held 522 from r1162; at r1189–1198 Prism (522), Heart of Ruin (26), Marcella (25) and Vesper (19) all started
  tributes: 408 + 522 + 26 + 25 + 19 = **exactly 1,000**.
- Prism's 522-gem channel took 53 turns (r1189 → r1242) [rules: ceil(gems/10), damage doesn't interrupt]. The opponent
  sat on 924–948 and lost.
- Banked + carried at the dump: 00swirl 998, 00corners 995, 01fracture 964, 00eight 1,005, 00reverse-spiral 1,049,
  01boss-battle 1,063, 00split 979 / 982, 00pilgrimage 992, 00lost-world 910, 00lanes 988, 00ambush 982,
  01shortcut 989, 00rows 1,000, 00gem-fields 967, 01starfish 969.
- Timing [measured]: Prism's first tribute starts after banked + carried first reaches 900 in 16 of 18 games, and
  before it reaches 1,000 in 14 of 18 (the other 4: 1, 3, 17 and 64 rounds after). [guess] The trigger is about 900–1,000,
  so that Prism's long channel (ceil(bag/10) turns) ends as the team reaches 1,000. For us, with no 500-gem
  battery, "banked + carried ≥ 1,000 → everyone tributes" is the simple form.
- [guess] Holding the gems hides the score: the opponent sees a small banked count and may not race.

**For us**: the closing rule needs the team's carried total. A visible ally's bag can be read with `gem_count()`
[sdk]; for allies out of sight it needs a field in the 8 shared bytes (`strat/MEMORY_LAYOUT.md`, `04_COMMS.md`).

## 3. Fights

[measured, `fights.py` / `freehit.py` / one-off counts]
- 290 fights; kills **154 top / 72 opp**. They start 199 of them (111 kills to 39); the opp starts 91 (43 to 33).
- Even fights 57–24; when **they are outnumbered, still 64–31**; they hit first in 68–72 % of every kind.
- Openers (first champion hit after 15 quiet rounds), top: Vesper basic 53, **Marcella slot 1** (single-target
  damage) 51, Heart of Ruin basic 29, Prism slot 0 (damage + stun) 20. Opp: Vesper 24, Marcella 17, Ryth 7.
- They open at **full HP** (opener HP share median 1.0) onto targets at 0.9 HP: they don't wait for a weak target.
- Target with 2+ enemies in reach: the nearest 88 %, the lowest HP 45 %, the biggest bag 20 %.
- Kills by body: Heart of Ruin 80, Marcella 50, Vesper 50, Prism 30, Willow 2.
- With an enemy champion in reach: hit it 55 %, recall/tribute 31 % (mostly the pre-charged recall plus channels),
  nothing 9 %.
- Move + attack in one turn: Heart of Ruin 853 of 4,029 attacks (21 %), Marcella 543 of 3,046 (18 %); ranged 0.
- Camp damage per hit by phase (r<300 / r300–700 / r700+ / r1000+): Vesper 55 / 115 / 185 / 315; Marcella 45 / 95 /
  125 / 105.

**Fights without Prism** [measured; a fight = 3+ champion hits, hits ≤ 10 rounds and ≤ 8 tiles apart; "Prism in
it" = their Prism hit someone or stood within 5 tiles]. The fight edge is **not** Prism's:

| | Fights | Top kills | Top deaths | Top hit first |
| --- | --- | --- | --- | --- |
| Prism in it | 105 | 85 | 48 | 70 % |
| No Prism | 141 | **91** | **24** | 70 % |

In the Prism-free fights they opened (99), at the first hit:
- **Small and even or better**: 1v1 43, 2v1 22, 3v1 6, 1v2 7, 2v3 4 (top bodies within 5 tiles of the opener vs
  opp bodies). Kills 62, deaths 12.
- **Bigger than the target**: the opener's max HP / the target's, median **1.15** (mean 1.49).
- **Both healthy**: opener HP share 0.95, target 0.93. They don't wait for a weak target.
- Bags: the target's median 0 (mean 31). They don't hunt carriers.
- Openers: Vesper 35, Heart of Ruin 32, Marcella 30.
- [guess] So the rule we can copy needs no Prism: **attack an enemy you outweigh (max HP, here ≥ ~1.15×) when you
  are not outnumbered**, at full HP, nearest target first. It's close to what `duel` already prices; the thing to
  check is whether our gate refuses these even 1v1s.

**Willow** [measured]: a support. Slot 1 (attack reset on itself) 516 times; slot 0 (ally heal, 3 × Focus) 388
times, spread over Vesper 112, Marcella 109, Heart of Ruin 93, Prism 74. About half its time no ally is within 3
tiles; when one is, it's most often Prism. It earns the least gold (4,959 over 14 games) and buys last (r362).

## 4. Draft and builds

- Draft: Prism, Vesper, Marcella, Willow, Heart of Ruin, every game (§1). Ours is Varg, Vesper, Ren, Ryth, Vendetta
  (Marcella 6th: `draft.h:5`). The meta draft lost twice in our tests (LADDER_P4 §9.4), but **without** the Prism
  battery and the closing rule, which are what make this draft work [guess].
- First buy (median): Marcella r106, Prism r118, Vesper r124, Heart of Ruin r130, Willow r362. Opp r117–r319.
- Early items (top): altar lock 31, Treasure emblem 23, Treasure shard 20, Bruiser shard 7, Jungle shard 6. The
  opp's early items include teleport crystals (10).
- Shard families by body:
  - Prism: Bruiser Focus 47 %, Jungle Health 17 %, Monster Focus 16 %;
  - Vesper: Bruiser Strength 46 %, Power Strength 16 %, Jungle Strength 12 %, Treasure Strength 10 %;
  - Marcella: Bruiser Strength 40 %, Bruiser Focus 21 %, Bruiser Health 17 %;
  - Heart of Ruin: Bruiser Focus 39 %, Bruiser Health 28 %, Jungle Focus 13 %, Treasure Focus 10 %;
  - Willow: Treasure Strength 28 %, Bruiser Strength 28 %, Jungle Strength 23 %.
- Gold: 5,734 a game (camp 3,419, kill 1,412, Marcella's tribute 904). By body (all games): Marcella 31.8k, Vesper
  25.7k, Prism 21.4k, Heart of Ruin 19.4k, Willow 5.0k.

## 5. Movement, the opening, recalls

- **Spread, not crews** [measured, `cohesion.py`]: half of their body-rounds are in a "cluster" of one; 2.8 clusters
  a round; after a multi-body take, the bodies split to different next takes 79 % of the time. Bodies per gem take
  r<100 2.6, r100–300 2.0, r300+ 1.8 (opp 2.9 / 2.3 / 2.0). Elk with 1.8 bodies after r300.
- **Opening** (to r300): 33.9 takes vs opp 27.9; first take r9.5 (median), first gem capture r36, first bank r70
  (opp r134). Holdings at r300: 221 vs 144. Their top gatherer by r300 is Heart of Ruin in 7 games, Marcella 5,
  Prism 4, Vesper 2.
- **Recalls that complete**: 38 a game (opp 38). Before the jump: HP share mode 0.3 (median 0.5 with the shop
  trips), bag 0, gold 26, no enemy within 6 in 631 of 682. Shop within 3 rounds 73 %.
- **Pre-charged recall**: on ~86 % of champion-turns. In-turn order (game 1 trace): Cancel channel → move/attack/ward
  → Recall. The Recall event shows the position after the move.
- Wards: 2–280 a game (map-dependent); game 1: 65 of 280 within 3 tiles of an altar, 162 within 3 of a camp.

## 6. What a replay shows, and what it doesn't

- Shows: every round's state (each champion's tile, HP, max HP, gold, gems, kills; camp HP; captures; wards;
  banked), every action (attacks and targets, casts, recalls, cancels, tributes, buys, wards, consumables, deaths
  and killers), and fuel rollovers.
- Doesn't show: team names, logs, shared bytes, fuel use. Debug dots/lines may be stored, but our decoder doesn't
  read them (open).
- Gotchas for our scripts: the pre-charged recall makes `legs.py` call every leg a recall leg and `farm.py`'s
  body-round shares say "channel" 92 %; ignore those two for this team.

## 7. Open questions for the next batch

- The bank trigger: is it a bag size, a bag × walk rule, or "after each capture if an altar is within N"?
- The closing rule: is the trigger banked + carried ≥ 1,000, or is it also a round or the opponent's score?
- Prism: how does it pick its camps (far ones, uncontested)? Does it avoid enemies on purpose?
- Their losses: we have only wins. A few losses would show where this plan breaks (e.g. Prism caught with 500).

## 8. Marcella spec, for the Varg → Marcella swap (`docs/CHAMPIONS.md` "Swapping a champion")

The swap lost on 24 Oct (35.3 % vs cpp-p6) because our code had no real Marcella. This is what the top team's
Marcella does over 18 games [measured], set against each item of the swap checklist and our code today.

**Kit** [rules]: passive stun-immune, **2 gold per gem tributed**; slot 0 (self) resets the basic attack, and the next
enhanced attack stuns 1 round; slot 1 does 2 × Focus to an enemy **or camp at range 4** (excludes walking); melee;
HP 1,200 (+100 a Health shard), Strength 45 (+5), Focus 60 (+15).

**What theirs does:**
- **Slot 0 is a farm tool first**: 507 casts, 431 with no enemy champion within 3; the next attack hits a camp 304
  times, a champion 75. So: reset on camps for an extra hit, and on a champion when one is in reach.
- **Slot 1, 650 casts**:
  - camps 320;
  - champions 231, from **range 4** (median) at targets with a median HP share 0.52: a poke / finisher before
    the melee arrives, and their most common fight opener after Vesper's attack (51 of 163 openings);
  - ground 99.
- **Banks often**: median 10 tributes a game, one every ~72 rounds, median bag 22. The most gems gained of any body
  (5,699 over 18 games), and 904 gold a game from the passive (16 % of the team's gold).
- **Build in time** (median round of each buy):
  1. Treasure shards (Strength / Focus) r102–110, Treasure emblem of Focus r128 or Strength r152;
  2. Jungle shards r133–181, Jungle emblems r297–396;
  3. Durability Health r454;
  4. Bruiser Health, Strength, Focus from r546 (the Bruiser Strength emblem is her most bought item).
  An altar lock on almost every shop visit (33 buys).
- **Survives**: deaths 0.6 a game (median 0); max HP 1,350 at r300, 2,150 at r600. Alone (no ally within 5) 42 % of
  her live time.
- Move + attack in one turn: 18 % of her attacks.

**Our code today, item by item:**
1. `draft.h` `PICKS`: Marcella is 6th, so never drafted in a 5-body game.
2. `champs.cpp:17` `base_row` (body id 6): bank weight **0.8, below average**. Theirs banks the most; and nothing
   prices her passive. A Marcella tribute of 22 gems is also 44 gold, so her Bank price should carry a gold term
   (bag × 2 gold, priced at the role's gold weight) [guess at the form].
3. `champs.cpp` `Me::init` builds: generic Bruiser Health + Power Strength by role. Theirs: Treasure → Jungle →
   Bruiser, Strength and Focus both (slot 1 scales with Focus).
4. `prices.cpp:85` `fkit` type 7: `fd = 2.0 + STUN_F` with the attack reset. It matches the kit, but it doesn't count
   that slot 1 lands from range 4, before contact.
5. `kit.cpp` `Kit::init`: slot 0 → `reset_slot` (+ `stun_slot`, enhanced), slot 1 → `camp_slot` + `fight_slot`.
   - On camps, `beh.cpp:245` tries the reset first, then slot 1: the same as theirs.
   - To check: does `kill_fight` cast slot 1 from range 4 while closing in, or only once in reach? Theirs opens with
     it from 4.
   - `stun_enemy` returns false when `stun_slot == reset_slot`, so Marcella can't stun a channelling enemy
     except through her enhanced hit. Fine for her, but note it for tribute denial.

**What the swap needs, in short:** draft her (in Varg's slot), raise her bank weight and add the tribute-gold term,
give her a Treasure → Jungle → Bruiser build with Focus, and let slot 1 fire from range 4 as an opener. Then judge
the swap alone on both bars. Varg's splash carries our crew's clears today (`draft-swaps`): watch the crew's clear
times when he goes.

**Team 2's Marcella** (14 games) [measured] matches team 1's on use:
- slot 0 mostly on camps (339 of 566 led into a camp hit, 140 into a champion);
- slot 1 on champions from range 4 (348 casts);
- 10.5 tributes a game.

The build differs:
1. Jungle / Treasure Strength (r54–147);
2. Durability Health (r217–255);
3. Bruiser Health from r556 (her most bought item);
4. Power Strength late.

Max HP 2,700 at r300 (team 1's: 1,350). Two working builds, then: Strength first (Treasure / Jungle) in both, then
Health (team 2) or Strength (team 1).

## 9. Team 2: 24 wins (`other_stuff_for_now/team2/`)

**Identity** [measured]: the winner of every replay has the same signature: no pre-charged recall (16–106 recalls
a game), **no altar locks**, 140–600 wards a game, teleports on wall / river maps, 1–63 rollovers. Its draft changes
every game. 6 of its wins came against teams that do pre-charge their recalls.

| Match | Map | Side | Team 2 picks | Opponent | Score | End | Deaths t2/opp |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 21ee13fb | 00collision 41x41 | B | Marcella, HeartOfRuin, VesperVale | HeartOfRuin, Vendetta, VesperVale | 1044-611 | r1400 | 3/9 |
| 24801e5b | 00reverse-spiral 30x30 | B | VesperVale, CassiAndIssac, Tavi, Prism | HeartOfRuin, Marcella, Vendetta, VesperVale | 1019-250 | r1379 | 16/34 |
| 26c94fa9 | 01hooks 31x31 | A | Marcella, HeartOfRuin, Willow, Prism | HeartOfRuin, Marcella, Vendetta, VesperVale | 1012-22 | r1241 | 4/27 |
| 2fdf70a9 | 01corridors 51x40 | B | Marcella, Varg, HeartOfRuin, Ryth, CassiAndIssac | VesperVale, Vendetta, Marcella, Ryth, Prism | 1004-8 | r1425 | 6/17 |
| 3301fa6b | 01big-world 100x100 | B | Varg, HeartOfRuin, VesperVale, Tavi, Stellar | VesperVale, Vendetta, Marcella, Ryth, Prism | 1025-479 | r1073 | 1/2 |
| 3ae126a3 | 00swirl 45x30 | B | Marcella, HeartOfRuin, Tavi, Stellar | VesperVale, Vendetta, Marcella, Ryth | 1005-210 | r1358 | 14/38 |
| 58be2cbb | 00lost-world 35x31 | B | Marcella, HeartOfRuin, Ryth, Willow, Prism | VesperVale, Vendetta, HeartOfRuin, Marcella, Tavi | 1002-148 | r599 | 6/21 |
| 5fb06a9e | 00contest 50x50 | B | HeartOfRuin, Ryth, Willow, Ren, Tavi | VesperVale, Vendetta, HeartOfRuin, Tavi, Marcella | 1000-0 | r1617 | 5/51 |
| 64031d72 | 01corridors 51x40 | A | Marcella, Varg, VesperVale, CassiAndIssac, Tavi | VesperVale, Vendetta, HeartOfRuin, CassiAndIssac, Ryth | 1007-948 | r1651 | 20/30 |
| 68dda16f | 00rushbait-v2 30x80 | A | Vendetta, VesperVale, Ryth, Tavi | HeartOfRuin, Marcella, Vendetta, VesperVale | 1010-602 | r1251 | 4/12 |
| 6af2030d | 00split 45x35 | B | HeartOfRuin, CassiAndIssac, Ren, Stellar, Prism | VesperVale, Vendetta, Marcella, Ryth, Prism | 1019-371 | r867 | 5/24 |
| 6e230a70 | 01elk-arena 50x50 | B | HeartOfRuin, VesperVale, Willow, Tavi, Stellar | HeartOfRuin, Marcella, Ryth, Vendetta, VesperVale | 1008-0 | r1326 | 11/34 |
| 8127845b | 00monolith 50x50 | B | Marcella, Vendetta, VesperVale, CassiAndIssac, Willow | Marcella, VesperVale, Tavi, Willow, HeartOfRuin | 1125-567 | r1064 | 6/4 |
| ae5ddbc6 | 00pilgrimage 50x65 | A | Varg, HeartOfRuin, Ryth, Willow, Prism | VesperVale, CassiAndIssac, Varg, Vendetta, HeartOfRuin | 1012-233 | r1434 | 1/18 |
| b5a2a4ce | 00gem-fields 50x40 | B | Marcella, Vendetta, Ryth, CassiAndIssac, Willow | Marcella, VesperVale, Tavi, Willow, HeartOfRuin | 1006-743 | r758 | 6/11 |
| c568b022 | 01boss-battle 50x41 | B | Marcella, Vendetta, VesperVale, Willow, Stellar | VesperVale, Vendetta, Marcella, Ryth, Prism | 1136-0 | r1616 | 5/15 |
| c61cb88d | 01concentrated-wealth 61x61 | B | Marcella, Varg, VesperVale, CassiAndIssac, Stellar | VesperVale, Vendetta, Marcella, Ryth, Prism | 1045-67 | r1090 | 2/24 |
| ccd474bb | 00fragment 30x30 | B | HeartOfRuin, Marcella, Willow | Prism, VesperVale, HeartOfRuin | 1000-100 | r1818 | 4/21 |
| d8dc16e7 | 00rushbait-v2 30x80 | B | HeartOfRuin, Vendetta, VesperVale, Prism | VesperVale, Vendetta, Marcella, Ryth | 1042-504 | r1419 | 8/11 |
| e19a78d8 | 00pilgrimage 50x65 | B | HeartOfRuin, Vendetta, VesperVale, Ren, Tavi | VesperVale, Vendetta, HeartOfRuin, Tavi, Marcella | 1009-950 | r1645 | 8/8 |
| e309c939 | 00rows 50x50 | A | Varg, HeartOfRuin, Ryth, Tavi | HeartOfRuin, Prism, Vendetta, VesperVale | 1188-836 | r1178 | 1/0 |
| f0411494 | 00lost-world 35x31 | B | Marcella, HeartOfRuin, Ryth, Willow, Prism | Marcella, VesperVale, Tavi, Willow, HeartOfRuin | 1001-174 | r419 | 7/8 |
| f705a46d | 01islands 60x60 | A | Marcella, HeartOfRuin, Ryth, Willow, Prism | HeartOfRuin, Vendetta, VesperVale, Ren, Marcella | 1002-804 | r856 | 7/2 |
| f740d777 | 01fracture 61x71 | A | Marcella, HeartOfRuin, Vendetta, Willow, Ren | VesperVale, CassiAndIssac, Varg, Vendetta, HeartOfRuin | 1051-832 | r1534 | 11/9 |

**Headline numbers** [measured, team 2 vs its opponents, per game]:

| Measure | Team 2 | Opp |
| --- | --- | --- |
| Captured gems | 1,562 | 1,078 |
| Takes (gold-only) | 60.9 (16.7) | 36.5 (10.0) |
| Banks; bag at bank, mean | 29.6; 40.5 (median 23) | 11.3; 40.5 |
| First bank (median) | r164 | r200 |
| Deaths; share of body-rounds dead | 6.7; 6.5 % | 17.9; 17.9 % |
| Gold (camp / kill / Marcella's tribute) | 6,551 (4,041 / 1,709 / 801) | 4,742 (3,978 / 563 / 202) |
| Max HP median r600 / r1000 | 1,500 / 2,000 | 1,250 / 1,700 |
| Fights (3+ hits): started; kills | 361 of 523; 331–98 | 162; 98 |
| With an enemy in reach: hit it | 63 % | 52 % |
| Rollovers | 21 | 25 |

**Fights** [measured]: kills are 145–52 in even fights, **86–11 when they outnumber**, and 100–35 when outnumbered.
They hit first in 61–79 % of fights. Kills come early too: r0–300 75–15. Move + attack: Heart of Ruin 1,112 of
5,268 attacks (21 %), Marcella 663 of 3,137 (21 %), Ren 341 of 1,084, Ryth 343 of 1,445.

**Builds** [measured]:
- **Power** for the damage dealers: Vesper Power Strength 74 %, Tavi Power Focus 51 %, Prism Power Focus 67 %.
- **Bruiser Health** for the melee: Marcella 62 %, Heart of Ruin 64 %, Ryth 46 %, Vendetta 46 %, Varg 41 %.
- First buys: Marcella r69, Ren r86, Heart of Ruin r95, Vendetta r115, Vesper r128.
- Teleport crystals: 9.5 a game on the maps where they jump.

**Teleports** [measured, `tele.py`]: 218 jumps, all on 00pilgrimage (58), 00split (47), 01fracture (43),
01concentrated-wealth (42) and 01big-world (28). Median walk saved 78 tiles (p25 19). 121 of 218 carried gems. Team 1
played 00pilgrimage, 00split and 01fracture without a single jump and still won, so it's one way, not the only way.

**Banks** [measured]: after a gem gain the next stop is a tribute 55 % of the time (1–19 gems: 51 %, 20–49: 58 %,
50–99: 71 %, 100+: 30 %). Bag at tribute by body (n, median): Marcella 161, 26; Heart of Ruin 150, 22; Vesper 71, 49;
Ryth 56, 21; Prism 45, 14; Willow 44, 17; Vendetta 39, 46; Varg 38, 42.

**Recalls** [measured]: 1,159 completed. HP share before them: 0.3–0.5 for 360, full HP (shop trips) for 282; bag 0.

**Wards** [measured]: a median 24 per 100 rounds (opp 11), i.e. about every body every cooldown.
- Tiles: 1–4 from the nearest camp for 4,231 of 7,044; within 3 of an altar 1,070.
- Plain tiles 4,441, bushes 2,461.
- Placed 1–3 tiles from the placer.

**Targets** [measured]: with 2+ enemies in reach, the nearest 92 %, the lowest HP 50 % (about chance).

**Open** (team 2): how the draft is chosen. Two 00pilgrimage games had different drafts, so it isn't the map alone.
[guess: counter-picks; the decoder doesn't give the pick order by round.] Their losses would show where its plan breaks.

## 10. Team 3: 36 wins on 24 maps (`other_stuff_for_now/team3/`), no Prism

**Identity** [measured]:
- **Fixed draft**: Vesper, Vendetta, Heart of Ruin, Tavi, plus Marcella with 5 bodies; Vesper and Heart of Ruin only
  with 3 bodies. It shares Vesper and Vendetta with ours.
- **0 fuel rollovers in 36 games.**
- No pre-charged recall (20–79 recalls a game) and no teleports.
- 2–9 altar locks a game, and 240–960 wards.
- It beat Varg / Ryth / Ren / Tavi drafts badly: 1065–48, 1015–64, 1045–301.

| Match | Map | Side | Bodies | Opponent | Score | End | Deaths t3/opp |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 05cc3fa9 | 01big-world 100x100 | B | 5 | HeartOfRuin, Marcella, VesperVale, Ryth, Vendetta | 1004-787 | r1120 | 1/2 |
| 1c45524c | 00gemfight 30x30 | A | 4 | HeartOfRuin, VesperVale, Marcella, Ryth | 1021-138 | r782 | 0/11 |
| 1f471706 | 00ambush 100x100 | B | 5 | HeartOfRuin, Ryth, Vendetta, VesperVale, Marcella | 1034-461 | r1191 | 3/8 |
| 22091b83 | 01islands 60x60 | A | 5 | VesperVale, HeartOfRuin, Vendetta, Ryth, Marcella | 1014-989 | r990 | 6/4 |
| 287123dc | 00swirl 45x30 | B | 4 | HeartOfRuin, Marcella, VesperVale, Ryth | 1055-252 | r883 | 5/19 |
| 2b285e60 | 00quadrants 45x45 | B | 5 | Varg, Ryth, Ren, Tavi, Marcella | 1045-301 | r560 | 2/11 |
| 3080c081 | 00gem-fields 50x40 | B | 5 | HeartOfRuin, Marcella, VesperVale, Ryth, Vendetta | 1018-456 | r872 | 12/14 |
| 317a8315 | 00reverse-spiral 30x30 | B | 4 | Prism, Ryth, Stellar, Tavi | 1015-7 | r1059 | 4/20 |
| 358a856f | 00gemfight 30x30 | B | 4 | Varg, Ryth, Ren, Tavi | 1015-64 | r839 | 8/16 |
| 394ba2f8 | 00monolith 50x50 | B | 5 | HeartOfRuin, Marcella, VesperVale, Ryth, Vendetta | 1035-742 | r1030 | 2/6 |
| 425e584e | 00pilgrimage 50x65 | B | 5 | Ren, Varg, Ryth, Stellar, CassiAndIssac | 1072-443 | r1742 | 2/28 |
| 42703b9a | 00gemfight 30x30 | A | 4 | HeartOfRuin, VesperVale, Marcella, Ryth | 1008-247 | r1011 | 5/16 |
| 491e5fc9 | 00elkring 30x30 | B | 5 | HeartOfRuin, VesperVale, Marcella, Ryth, Vendetta | 1012-264 | r711 | 5/16 |
| 5469b55e | 01shortcut 40x40 | B | 4 | VesperVale, HeartOfRuin, Ryth, Marcella | 1006-42 | r855 | 5/4 |
| 5c252e39 | 01corridors 51x40 | A | 5 | HeartOfRuin, VesperVale, Marcella, Ryth, Vendetta | 1026-756 | r1618 | 8/16 |
| 614ee893 | 00stampede 60x50 | B | 5 | Stellar, Prism, Willow, Ryth, Tavi | 1120-0 | r1631 | 6/44 |
| 62cebc65 | 00swirl 45x30 | A | 4 | HeartOfRuin, VesperVale, Marcella, Ryth | 1015-76 | r985 | 8/28 |
| 6c92b09c | 01shortcut 40x40 | B | 4 | Ren, Prism, HeartOfRuin, VesperVale | 1092-0 | r764 | 2/8 |
| 7371490e | 00gemfight 30x30 | A | 4 | HeartOfRuin, Marcella, Vendetta, VesperVale | 1066-62 | r787 | 4/11 |
| 765dbe8e | 00road-of-riches 40x40 | B | 5 | Prism, Vendetta, Marcella, Ryth, VesperVale | 1161-0 | r719 | 1/3 |
| 7727fb65 | 00swirl 45x30 | B | 4 | HeartOfRuin, VesperVale, Marcella, Ryth | 1040-121 | r921 | 4/19 |
| 8d16ba16 | 01gold-rush 31x31 | A | 3 | HeartOfRuin, VesperVale, Marcella | 1009-242 | r1106 | 2/10 |
| 8ef38dcf | 00eight 41x30 | B | 5 | Varg, Ryth, Ren, Tavi, Marcella | 1065-48 | r783 | 0/32 |
| 9a1efc42 | 01starvation 80x80 | A | 5 | HeartOfRuin, VesperVale, Marcella, Ryth, Vendetta | 1058-254 | r1599 | 7/24 |
| a73baf7b | 00rushbait-v2 30x80 | A | 4 | VesperVale, HeartOfRuin, Vendetta, Ryth | 1016-713 | r1045 | 6/8 |
| ab2d26d7 | 00swirl 45x30 | A | 4 | VesperVale, HeartOfRuin, Vendetta, Ryth | 1011-46 | r837 | 7/24 |
| ab3708bd | 00road-of-riches 40x40 | B | 5 | HeartOfRuin, Ryth, Vendetta, VesperVale, Marcella | 1082-0 | r592 | 1/5 |
| c2c503a6 | 00great-wall 50x40 | B | 5 | Prism, Vendetta, Marcella, Ryth, VesperVale | 1243-155 | r896 | 6/5 |
| d108eb4d | 01elk-arena 50x50 | B | 5 | HeartOfRuin, Marcella, Vendetta, VesperVale, Ryth | 1008-0 | r1068 | 8/7 |
| d993b5e9 | 00reverse-spiral 30x30 | A | 4 | VesperVale, HeartOfRuin, Vendetta, Ryth | 1037-744 | r1566 | 19/21 |
| e823e1a6 | 01fracture 61x71 | B | 5 | Prism, Ryth, Ren, Tavi, VesperVale | 1078-4 | r977 | 1/13 |
| e8d49c8d | 00corners 71x71 | B | 5 | HeartOfRuin, VesperVale, Marcella, Ryth, Vendetta | 1044-257 | r968 | 4/17 |
| ec7837be | 00pilgrimage 50x65 | B | 5 | HeartOfRuin, Marcella, Vendetta, VesperVale, Ryth | 1004-676 | r1608 | 5/3 |
| f1681be9 | 00stampede 60x50 | A | 5 | HeartOfRuin, Marcella, Vendetta, VesperVale, Ryth | 960-320 | r2000 | 3/10 |
| f1fe0b62 | 00monolith 50x50 | A | 5 | HeartOfRuin, VesperVale, Marcella, Ryth, Vendetta | 1090-645 | r1032 | 5/8 |
| f69fc75c | 00contest 50x50 | B | 5 | HeartOfRuin, Marcella, Vendetta, VesperVale, Ryth | 1000-0 | r1183 | 9/25 |

**Headline numbers** [measured, per game]:

| Measure | Team 3 | Opp |
| --- | --- | --- |
| Captured gems | 1,392 | 416 |
| Takes (gold-only) | 46.7 (12.1) | 35.4 (14.3) |
| Banks; median bag | 28.9; 26 | 10.1; – |
| First bank (median) | r78 | r154 |
| Deaths; share of body-rounds dead | 4.9; 5.9 % | 14.3; 17.0 % |
| Gold (camp / kill / Marcella's tribute) | **8,566** (6,704 / 1,638 / 225) | 2,638 |
| Max HP median r300 / r600 / r1000 | 1,300 / 2,000 / 2,800 | 1,200 / 1,500 / 2,000 |
| Fights started; kills | 423 of 739; 455–123 | 316; 123 |
| Gem take: HP cleared per round per body | 116 | 79 |
| Rollovers | **0** | 2 |

- **Gold is its edge**: 3.2× its opponents. Gold over the 36 games: Vesper 108k, Vendetta 96k, Heart of Ruin 60k,
  Marcella 33k, Tavi 11k. Vendetta's first buy is r76.
- **Builds**: Bruiser Strength on Vesper (50 %), Vendetta (44 %) and Marcella (42 %); Bruiser Focus on Heart of Ruin
  (47 %); Bruiser Strength + Treasure on Tavi. Early items: altar lock 58, Treasure shard 56, Treasure emblem 45.
- **Fights**: even fights 196–42; when it outnumbers, 98–7; when outnumbered, 161–74.
  - Openers: Tavi slot 1 (damage + stun) 91, Vesper 79, Vendetta 37, Heart of Ruin 32, Marcella slot 1 25.
  - At the opening hit: max HP ratio median **1.13**; own HP 0.95; target HP 1.0; allies minus enemies within 5 is 0
    or more in 246 of 277.
  - Targets: the nearest 91 %, the lowest HP 59 %.
- **Banks**:
  - After a gem gain, the next stop is a tribute 64 % of the time: **93 % once the bag is 50–99**, 90 % at 100+,
    55–61 % below 50.
  - Bag at tribute: Vesper 37, Vendetta 29, Marcella 30, Heart of Ruin 22, Tavi 15.
- **The close**: banked + carried reaches 1,000 a median 25 rounds before the end. The last 150 rounds bring a median
  6.5 tributes and 324 gems.
- **Altar locks**: 152. 93 of them came within 6 rounds of their own tribute by the same body (38 within 1), and only
  4 while an enemy was tributing nearby. **The same habit as team 1.**
- **Recalls**: HP share before them 0.3–0.5 for 467; full HP (shop) 358.
- **Abilities**: Vendetta's passive resets her cooldowns on every kill, monsters included [rules]. She casts slot 0
  (attack reset) and slot 1 (dash) 12.7 times per 100 live rounds; move + attack on 1,011 of 8,082 attacks.

## 11. Us against all three (cpp-p6's 38 ladder losses, same scripts) [measured]

Ours are losses and theirs are wins, so part of every gap is the result itself, not the cause. Read it for the gaps
that are too big to be only that.

| Per game, or per 100 live body-rounds | Us (p6 losses) | Team 1 | Team 2 | Team 3 |
| --- | --- | --- | --- | --- |
| Banks a game; median bag | 15.0; 15 | 31.9; 21 | 29.6; 23 | 28.9; 26 |
| Next stop after a gem gain is a tribute | 47 % | 86 % | 55 % | 64 % |
| **Camp hits per 100 live rounds** | **9.3** (our opponents: 13.4) | 18.3 | 16.2 | 16.5 |
| Champion hits per 100 live rounds | 2.1 | 3.0 | 4.0 | 4.2 |
| Vesper: slot 0 / slot 1 (dash) casts per 100 live rounds | 3.5 / **2.9** | – | 5.0 / 7.3 | 4.7 / 7.4 |
| Vendetta: slot 0 / slot 1 (dash) | 2.8 / 4.8 | – | 4.1 / 6.6 | 5.3 / 7.4 |
| All casts per 100 live rounds: Vesper, Vendetta | 6.4, 7.6 | 12.7, – | 12.4, 10.7 | 12.1, 12.7 |
| Ren, Ryth, Varg | 4.1, 3.5, 5.2 | – | 12.0, 8.7, 14.8 | – |
| Recall HP (median, shop trips left out) | 0.45 | 0.40 | 0.40 | 0.39 |
| Fights opened a game: us / opp | 8.1 / 10.0 | 9.1 / 3.6 | 10.3 / 4.6 | 7.7 / 5.8 |
| Altar locks; wards a game | 0; 169 | 3.8; 88 | 0; 294 | 4.2; 431 |
| Deaths a game | 12.1 | 4.9 | 6.7 | 4.9 |

- **Not gaps after all**: wards (we place 169 a game) and recall HP (we recall at 0.45, they at ~0.40).
- **Gaps that are too big to be just "we lost"**:
  - **we hit camps half as often while alive** (9.3 vs 16–18; even the teams that beat us hit 13.4);
  - **we use abilities half as often** (Vesper's dash 2.9 vs 7.3–7.4);
  - **we bank half as often** (15 vs 29–32).
