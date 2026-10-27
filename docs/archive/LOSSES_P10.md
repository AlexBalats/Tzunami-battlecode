# cpp-p10's ladder losses (48 games, 25 Oct): how we lost, what the winners did, what to build

Source: `replays_from_others/p10/` (48 losses, every one ours; we are side A in 33). Each game was decoded one at a
time. Every bundle holds our own `team-*.stdout` and `.fuel`, so `flip.py` makes **us team 0** with nothing touched;
"us" below is p10 and "them" the team that beat us.

The tools:
- the R2/R3 battery (`q/battery_us.sh`: every farm script plus the side session's queries);
- new one-offs in the session scratchpad `q/`: `deathctx.py` (the context of each champion kill) and `expo.py`
  (monster exposure at big-camp hits).

Tags:
- [measured]: these replays;
- [code]: `bots/cpp` = `bots/cpp-p10`, read 25 Oct;
- [rules] or [sdk]: the handbook or the SDK;
- [web]: the sources listed at the end;
- [guess]: unconfirmed.

**The overlap fools gold numbers for us** (TOP_P9 §9.4): the capture reward pays on the round the body lands at spawn,
often the round it shops. So our gold from per-round rises (`goldsrc.py`, the per-game table) is **a floor**: the
reward and the buy net out. There is no `stats.json` for ladder replays. Gems are not affected.

---

## 1. Who beat us [measured, by signature as in TOP_TEAMS_R2/R3]

- **Team 5** (Ves HoR Vdt Tav Mar, no pre-charge, locks, wards 234–658): 5 games (00corners, 01big-world,
  01starvation, 00interlock, 01gold-rush).
- **Team 4** (pre-charge, Ves Vdt Ryt Tav Mar): 4 games (00lost-world, 00split, 01boss-battle, 01corridors).
- **Team 6: none. Team 7's exact draft: none**; one Marcella-first pre-charger (00rows 0374ed94) may be it.
- **39 others**, many of them drafts no earlier round read:
  - Ren teams (Mar Ryt Var Ren Ven);
  - Prism + Ryth (Ves Ven Mar Ryt Pri);
  - Tavi + Willow with 78–101 rollovers;
  - Stellar + Prism + Willow + Ren;
  - Cassi + Willow.

So most losses are to the broad ladder, not to the four top teams. What follows is what **every** winner does against
us.

## 2. Three ways we lose [measured]

A fixed rule split the 48 games:
- **C**: the game reaches r2000;
- **A**: our earned gold by r300 < 0.75 × theirs, or we die 10+ times and 1.5× as often as they do;
- **B**: the rest.

| Mode | Games | Maps | Deaths us / them | Gold r300 us / them (a floor for us) | Gems: our side / contested / their side (us v them) | Max HP r1000 us / them |
| --- | --- | --- | --- | --- | --- | --- |
| **A. Crushed early** | 27 | 01gold-rush ×3, 01concentrated-wealth ×3, 01starvation ×2, 01boss-battle ×2, 01elk-arena ×2, 00gemfight ×2, 00swirl, 01starfish, 00reverse-spiral, 00rushbait-v2, 00lost-world, 00split, 00quadrants, 00interlock, 00corners, 01big-world, 01corridors, 01shortcut, 00lanes | **14.1 / 6.0** | 680 / 1,394 | 280 v 30 / **191 v 818** / 2 v 321 | 1,600 / 2,400 |
| **B. A farm race lost** | 17 | 00rows ×3, 00road-of-riches ×2, 00expanse, 00elkring, 00monolith, 00gem-fields, 00packs, 00collision, 00rushbait-v2, 01broken-curve, 01gold-rush, 01hooks, 01islands, 01corridors | 4.4 / 5.0 | 1,155 / 1,035 | 574 v 20 / **151 v 460** / 7 v 624 | 2,100 / 2,600 |
| **C. Gem-starved to r2000** | 4 | 00stampede ×2, 01starvation, 01concentrated-wealth | 5.2 / **15.8** | – | 165 v 0 / 175 v 254 / 6 v 287 | 2,000 / 1,400 |

- Mode A is two-thirds of the losses. The contested middle goes 191 v 818 and we die 2.3× as often.
- Mode B is the cleanest lesson. 00rows ×3 had 0 deaths on either side: on the **same mirrored half** they took
  965–1,017 gems to our 726–906.
- Mode C: we out-earned them on gold (00stampede: 5,437 vs 2,184 by r1000) and killed them 23 times, and still lost
  0–320 and 160–480 at r2000 on the gem tiebreak [rules].

## 3. Headline numbers, all 48 [measured]

| Measure | p10 (us) | Winners | Top teams' own wins (R2/R3) |
| --- | --- | --- | --- |
| Gems gained a game: our side / contested / their side | 375 / **175** / 4 | 24 / **644** / 425 | contested 492–694 |
| Deaths; share of body-rounds dead | 9.9; 10.1 % | 6.5; 6.6 % | 3.2–6.9; 3.8–7.4 % |
| Champion-kill deaths: HP share 5 rounds before (median) | **0.63** | 0.47 | 0.32–0.48 |
| Champion-kill deaths outnumbered (enemies > allies + 1 within 5) | **37 %** | 22 % | 26–35 % |
| HP lost an engaged round (enemy within 3), by champion | **62–93** | 38–63 | – |
| Ally within 5, off spawn, r300–1000 | **45 %** | 53 % | T6 64, T4 52, T7 50, T5 44 % |
| Bodies within 6 at contact (us v them); more / fewer | 1.49 v 1.62; 23 / 31 % | – | T6 2.00 v 1.57; 42 / 19 % |
| Time: hitting camps / walking / dead | 9.2 / 54.3 / 10.1 % | 11.6 / 52.6 / 6.6 % | 12.7–16.7 / 47–53 / 3.8–7.4 % |
| Camp hits per 100 live rounds | 12.0 | 14.7 | 16.2–20.6 |
| Elk kills a game; hitters; HP lost a kill | 12.4; 2; 336 | **20.2**; 2; 378 | 20–27 |
| Multi-big takes a game (2+ elk/golems) | 2.4 | 4.9 | 3.4–6.6 |
| **Monolith hits in 22 games with a monolith** | **13** | 1,793 (0.5 kills a game, 3+ hitters at ~4,200 max HP) | – |
| Gems by kind: elk / wolf / cluster / monolith | 266 / 184 / 57 / **0** | 508 / 267 / 126 / **104** | elk 510–600 |
| Contested group lives: hit first / captured | **52 % / 37 %** | 48 % / 63 % | 30–43 % / 62–74 % |
| Steals (captured a group the other team cleared) | 64 (1.3 a game) | **130** (2.7) | 2.1–2.7 a game |
| First hit on any contested camp (median round) | r63 (never in 8 games) | r40 (never in 2) | – |
| Banks a game; median bag; banked | 18.1; 15; 418 | 30.6; 22; 984 | 24–31; 22–30 |
| Gems lost on death a game | 93 | 57 | 14–49 |
| Rollovers a game (our fuel logs) | 5.4 (worst: 01corridors 72) | – | 0–31 |

## 4. Findings

**L1. We lose the contested middle, and we are the ones it is stolen from** [measured].
- Contested gems: 175 vs 644 a game, the single biggest gap (−469). It holds in mode A (191 vs 818) and mode B (151 vs
  460).
- We hit first in 52 % of contested group lives and capture 37 %; they hit first 48 % and capture 63 %. They steal
  130 groups we cleared (2.7 a game), and we steal 64.
- So we play the top teams' opponents' role: we pay the clear (HP, time), then they arrive, fight a hurt clearer and
  take the capture. All four top teams do this to their opponents: they hit first only 30–43 % of the time and capture
  62–74 % (TOP_TEAMS_R3, "What four of four share").
- We also arrive later: our first contested hit is a median r63, theirs r40.

**L2. We get collapsed on: deaths from healthy HP while outnumbered** [measured, `q/deathctx.py`].
- A median 63 % HP five rounds before the kill (winners 47 %, top teams 32–48 %).
- Outnumbered in 37 % of our deaths (theirs 22 %), and alone (no ally within 5) in 46 %.
- In engaged rounds we lose 62–93 HP a round per body (Vesper 90, Vendetta 93) against their 38–63.
- In the fights table: outnumbered fights 74–96 in kills, but also even fights 87–116 and **fights where we outnumber
  them 71–107**.
- Cohesion is the same story as TOP_TEAMS_R3's S1, measured on our own losses this time. From r300 to r1000 we have an
  ally within 5 in 45 % of off-spawn body-rounds (winners 53 %, T6 64 %).
- At contact we have more bodies 23 % of the time and fewer 31 %.
- [guess] Two to three bodies arrive on one of ours. p9's stance breaks below 45 % HP or above P(lose) 0.7, too late at
  ~150–250 HP a round of focus. A recall can't save it: damage interrupts it [rules].

**L3. On a mirrored half with no fights, the winners farm as a pack and stand on the respawn** [measured, 00rows ×3,
0 deaths].
- Time on camps 21.4 % vs our 13.8 %; walking 54 % vs our 64 %. Camp hits per 100 live rounds 25.1 vs 15.8.
- **They are within 5 of an ally 73 % of the time from r300 (we: 40 %).** All 4–5 bodies work the same 2–3 core groups
  together.
- **First hit after a respawn: a median 1 round (we: 12).** They make 65 group moves (79 % repeat pairs); we make 103
  (58 %).
- Each of their bodies makes 330–566 camp hits; ours make 190–280.
- So the pack is a **farming** edge, not only a fighting one: a stacked group dies in a few rounds, the next respawn is
  stood on, and nobody walks alone between groups.
- In all mode B games: camp hits 18.5 vs 14.9 per 100 live rounds; an ally within 5 56 % vs 47 %.

**L4. High-need maps are where we lose, and on gem-starved maps we take no gems at all** [measured, sdk-derived dump].
- The draft's own record (`maps_dump.json`, `need` at draft-time stats) shows maps where most gems sit in groups that
  need more bodies than we have:
  - 00stampede 0 % of the gems in groups we can take;
  - 01starvation 8 %;
  - 00rows 20 %;
  - 00swirl 23 %;
  - 00monolith and 01boss-battle 24 %;
  - 00interlock 19 %.
  Every one is in this loss list, several of them repeatedly (00contest, 0 %, is not: p10 already handles it).
- **00stampede, the extreme case.**
  - The only gems on the map are one contested group of 6 elk + 2 gem clusters (160 gems, `need 6`, equal walk from
    both spawns). `need_k_r9` searches k = 1 … roster (5) and finds none [code, `prices.cpp:217–240`]. We never price
    it, and we lose 0–320 at r2000.
  - The winners of 93d9773f took it with **3–4 bodies at 650–1,700 max HP, r543–627**. They killed the elk one by one
    over ~85 rounds and banked 160 three times.
  - A camp stays damaged [measured, CLAUDE.md], and the group sleeps after 2 rounds with no champion in range [rules],
    so a big group can be cleared **over several sessions**. elkkill's "sessions > 1" is 19–20 % of elk kills for
    both sides, and 46 % for the winners' monoliths.
- This extends TOP_P9 §0/§3: the need model is ~0.6× too pessimistic, and `DMG_X` 0.6 raised deaths and was dropped
  (§8). New here: **where no group is affordable, the bot takes no gems at all**, and the game goes to the gem
  tiebreak.

**L5. We never take monoliths** [measured].
- 22 of the 48 games had a monolith. We hit monoliths 13 times in all; the winners hit them 1,793 times and took 104
  gems a game from them (75 after r700), with 3+ hitters (73 %) at ~4,200 max HP over ~40 rounds (46 % over several
  sessions).
- We still die to monoliths 21 times [measured, death cause `Attack:2:<monolith>`]. That is mostly bodies in range of
  one the winners had woken [guess].

**L6. The same elk efficiency, half the elk** [measured].
- Elk kills: 12.4 vs 20.2 a game, with the same 2 hitters, 10 rounds and 336 vs 378 HP lost a kill.
- Multi-big takes: 2.4 vs 4.9.
- It's what we choose to take, not how well we take it: TOP_P9's diagnosis again. The pack (L3) and the need floor (L4)
  are the two levers on it.

**L7. Gem clusters: we take half** [measured, code].
- Gem-cluster kills: mode B 451 vs 764, and all 48 games 57 vs 126 gems a game. We kill more gold clusters (00rows
  321 vs 248).
- [code] `farm_price` values a group at gems + `g2g(r)` × gold × `prof.gold` (`prices.cpp:263`; `G2G_K` 0.5;
  `ROLE_GOLD` main 3.0, others 1.0, `champs.h:13`):
  - for the main, a gold cluster (20 gold) is worth 30 at r0 and 15 at r1000, against a gem cluster's 7;
  - for the crew, 10 against 7.
- A gem cluster is the cheapest gem source in the game (120 HP, no damage, 7 gems, 50-round respawn [rules]).
- [guess] Worth a test, but it trades gold, and R9's gold redesign lost (`10_GOLD_ITEMS.md` §4.1). Low priority.

**L8. Checked and refuted, or not ours to fix** [measured].
- **Exposure positioning (refuted).** Standing so fewer awake monsters reach you is not a lever. Every team's hitter is
  in range of every live big monster of its group 96–99 % of the time (`q/expo.py`); the groups are too compact for
  range 4.
- **Casting (a draft difference).** Casts in fights look 4× lower for us (`fightctx`: 0.3–0.5 vs 1.3–1.6). Per engaged
  round, our "any cast" share is the same (12–25 % vs 17–24 %). The gap is damage-dealing spells on champions: their
  rosters carry Prism (17 % of engaged rounds), Stellar (13 %), Tavi (11 %) and Ren (9 %); our kits are resets, dashes
  and shields.
- **Camp deaths (small).** 1.5 a game vs their 1.1.
- **Rollovers (small).** 5.4 a game; worst 01corridors 72 and 01boss-battle 22–23.

## 5. What the web adds [web]

- **Lanchester's square law, in practice** (Battlecode 2024 winner, "cout for clout").
  - Their "squadron" system sends units to the combat location so they arrive together: "adding one duck increases the
    power of a large army by a lot, but a small army by a little".
  - A 47 vs 50 test lost 90 % of games.
  - Our fight model replaced Lanchester with a `duel` P(lose) (08_FIGHT); the numbers-at-contact gap (L2) is what
    Lanchester punishes.
- **"Friendliness" as one cheap scalar** (Halite III, mlomb, rank 18).
  - Per tile: Σ over distance 0–3 of (4 − d) × (allies − enemies), with high-cargo ships counting less.
  - Moves into a tile an enemy can reach are vetoed when it is below a threshold, and ramming is allowed only above
    another.
  - Their mining-target score **adds a little for nearby allies and subtracts more for nearby enemies** (2-player
    games): the pack term, from a different game.
- **Return paths that avoid tiles next to enemies** (Halite III, teccles, 1st). The shortest path avoiding enemy-adjacent
  tiles is used unless the direct path is x times shorter.
- **Economy first, and idle time** (Battlecode 2025, The Kragle).
  - "Battlecode games are often snow-bally": optimise the opening for resources.
  - Fixing "inefficiencies in resource management and idle time" took them to top level.
  - Not copying other teams left them "lacking obvious features".

## 6. What to build: additions to the p11 plan (`NEXT_PROMPT_P11.md` P1–P5)

The p11 session is building P1 (crew shop gate), P2 (the pack), P3 (crystals), P4 (the banker) and P5 (arrive second).
The losses rank them, and add four pieces. Every rule reads game state or the map at runtime. None is per-map.

| Rank | Piece | Fixes | Evidence here | Measures (target) |
| --- | --- | --- | --- | --- |
| 1 | **P2, the pack (S1–S3), now with farming as the main payoff** | L2, L3, L6, part of L1 | ally within 5 45 % (winners 53, T6 64); on 00rows the winners' pack farms 1.6× our camp hits; deaths outnumbered 37 % | ally within 5 r300–1000 ≥ 55 %; camp hits / 100 live ≥ 15; respawn first-hit latency on own groups (00rows 12 → ≤ 5); deaths outnumbered ≤ 25 %; elk kills ≥ 16 |
| 2 | **N1. The need floor: never a gemless plan** (new) | L4, mode C, part of B | 00stampede 0 and 160 gems in 2,000 rounds; winners did `need 6` with 3–4 bodies at ≤ 1,700 HP | gems on the high-need maps (00stampede, 01starvation, 00rows, 00swirl, 00monolith, 01boss-battle); no r2000 game at 0 gems |
| 3 | **N2. Hold what you clear** (new; P5's mirror image) | L1 | we hit first 52 %, capture 37 %; steals against us 130 vs 64 | contested gems (175 → 300+); our capture share of the contested groups we hit first (37 → 55 %+) |
| 4 | **N3. Break by numbers, not only by HP** (new) | L2 | deaths from 63 % HP, outnumbered 37 %, HP lost 62–93 a round | HP share 5 rounds before a death (0.63 → ≤ 0.5); deaths a game; trades |
| 5 | **N4. Monoliths by pack, late** (new; needs rank 1) | L5 | 13 hits vs 1,793; 104 gems a game | monolith gems a game on the 22 monolith maps; deaths to monoliths (21 → ≤ 5) |
| 6 | P1, P3, P4, P5 as planned | – | – | as in NEXT_PROMPT_P11 |
| 7 | N5. Gem-cluster value (test only) | L7 | 57 vs 126 cluster gems | gem-cluster takes; gold by r600 must not drop |

**N1. The need floor** (a map-free trigger: the live `need_k` of every known gem group).
- Rule: if no group with gems is takeable by the bodies available (`need_k` = 0 for all of them, or the best gem price
  is 0) for ~50 rounds, price the cheapest-by-gems-per-HP group for **the whole pack**: k = all live bodies, `need_k`'s
  floor relaxed, and the take split into sessions.
- A session means:
  - hit only while the tank holds above the floor;
  - when it falls below, all step out of range until the group sleeps (2 rounds [rules]), heal by recall, and return
    (the damage stays [measured]);
  - the group's memory keeps the monsters' HP, as `take_mons` already reads it.
- Trace proof: the group's HP is unchanged after a 2-round sleep, and a session ends with no deaths.
- Unknowns:
  - can the bot hold a "session" goal across a recall (state, comms code 4)?
  - does a woken group re-wake on the next hit at full aggression (yes [rules])?
  - does the opponent steal the last camp (N2 covers it)?

**N2. Hold what you clear** (reads the enemy count in sight and the capture rounds left).
- Before opening a contested group, price P(we capture) = P(no enemy arrives in clear rounds + 5) or P(we win the
  fight then). Open it only if (gems × P) beats the next option. Otherwise wait in reach (P5) or take another group.
- While capturing a contested group with an enemy in sight: stay with an ally (the pack) or leave early, before the
  clear's HP cost turns into a death.
- Measure: our capture share of contested groups we hit first (37 → 55 %+), and steals against us (2.7 → ≤ 1.5 a game).

**N3. Break by numbers** (reads allies and enemies within 5: Halite's friendliness [web]).
- Add the count term to p9's stance (`upd_stance`): break early (HP < 70 %) when enemies within 5 exceed allies within
  5 + 1, and step **toward the nearest ally** rather than straight home.
- Keep it one scalar: Σ (6 − d) × (allies − enemies) over d ≤ 5.
- Measure: the HP share 5 rounds before a death, and deaths outnumbered.
- Risk: p8's flee lessons (LADDER_P8: moving away 38–48 % lost fights). So break toward an ally, not away from the
  fight.

**N4. Monoliths by pack** (reads the group's HP and the pack's total max HP).
- A monolith group is priced for the pack when Σ max HP of the bodies within 5 ≥ the clear's damage at the 0.6×
  correction (TOP_P9 §0). The winners clear at 3+ bodies × ~4,200 max HP, ~4,800 HP lost, over sessions (N1's machinery).
- Separately, keep bodies out of range 5 of an awake monolith we aren't hitting (21 deaths). The camp-danger board in
  `nav.cpp` already marks awake camps; check why it misses these [code: `nav.cpp:160–170`].

**N5. Gem clusters** (test only): lower the main's gold weight on clusters (or `G2G_K`) and read cluster gems and gold
by r600. Keep it only if gold doesn't drop.

**Not to build**: exposure positioning (L8, refuted); "cast more" (L8: a roster difference, not a bug).

## 6b. After p11 (26 Oct): the pack drops to last; N1, N2 and N4 lead

p11 (TOP_P9 §10.5) built P1–P4. Every piece lost to p10 head to head except the teleport crystal (P3c, kept in
`bots/cpp`). The pack moved cohesion (47 → 55 %) but not bodies at contact, and it cost the open maps. The same
measure on these 48 ladder losses (`q/contactact.py`) [measured] shows why:

| At a contact episode, our nearest body is… | p10 (us) | Winners vs us | T6 | T7 |
| --- | --- | --- | --- | --- |
| hitting a camp | 10 % | 13 % | 16 % | 12 % |
| walking outward | 45 % | 41 % | 42 % | 48 % |
| walking home | 25 % | 24 % | 25 % | 24 % |
| with no ally within 5 | **62 %** | **57 %** | 45 % | 54 % |

- Every team meets the enemy mostly on walks.
- Being alone at contact barely separates us from the teams that beat us (62 vs 57 %). Only T6 is far apart (45 %).
- **So U-T10.8 is answered: against the ladder the pack is a T6 trait, not our gap.**
- U-L1 is answered too: p10's ally within 5 in arena games is 47 % (TOP_P9 §10.1), the same as the 45 % on the ladder.

New order:
1. **N1, the need floor**: no gemless plan; the whole-pack take in sessions.
2. **N2, hold what you clear.**
3. **N4, monoliths as the endgame take** (needs N1's sessions).
4. **N3, break by numbers.**
5. N5, gem clusters (test only).

The pack (P2) stays parked; TOP_P9 §10.6 item 2 (legs walked together) is its only open form.

Map sets for judging, read from the draft-time dump. Each is a runtime feature, not a map list in code:
- **High-need maps** (≥ 75 % of the map's gems in groups whose draft-time `need` > roster), 13 of 40: 00contest,
  00fragment, 00great-wall, 00interlock, 00monolith, 00rows, 00stampede, 00swirl, 01boss-battle, 01broken-curve,
  01gold-rush, 01starvation, 01the-farm.
- **Monolith maps**, 15 of 40: 00contest, 00great-wall, 00lost-world, 00monolith, 00rows, 00split, 01big-world,
  01boss-battle, 01broken-curve, 01corridors, 01fracture, 01gold-rush, 01shortcut, 01starvation, 01the-farm.

## 7. Unknowns to check when building

- U-L1 (answered 26 Oct, §6b): p10's ally within 5 in arena games is 47 %, the same as on the ladder.
- U-L2 (answered, §8.3): the live per-body trigger fired on every map. A draft fact (the gem share in groups the roster
  takes at once) is stable and free.
- U-L3 (answered, §8.1): no monolith was hit before any of the 21 deaths. 11 were a camp the 8-camp cut hid; 10 were
  bodies in range of an awake monolith of their own farm group.
- U-L4: why 8 games had no contested hit at all (reach, near6, or a choice).
- U-L5: the per-mode gold for us is a floor (the overlap). Re-measure from arena `stats.json` before any gold claim.

## 8. Built (after the round-3 build): the group fix kept as `cpp-p11` (not uploaded) (= P3c + the fix); N1, N2, N3, N5 lost; N4 not built

Judged over 8 jitters (640 games) **vs `bots/cpp-p10` only** (user, this session: "no point wasting time on any of the
older stuff"), and each N piece **head to head vs the build before it** (`bots/_fix`, null 48.0 %). Per-map-set splits
use `split.py` sets: high-need and monolith (§6b), walled (TOP_P9 §10.5), big8 (the 18 maps with a group over 8 camps).
Patches of everything not kept: `docs/redo/patches/P12_*`. [measured] unless tagged.

### 8.1 Checked before building

- **The local baseline** (cpp-p10 vs cpp-p9, 16 decoded games: 00stampede, 01starvation, 00monolith, 01boss-battle,
  00packs, 01starfish, 00rows, 00expanse):
  - contested lives hit first 47 %, captured 58 % (mirror; the ladder's 52 / 37 % does not show locally);
  - steals 27 v 29;
  - 0.2 monolith kills a game a side;
  - death HP share 5 rounds before 0.75, outnumbered 21 % (the ladder's 0.63 / 37 %);
  - 00stampede 0-0 at r2000 from both sides, so L4 holds locally too.
- **The two facts N1 rests on, on cambc 3.0.5** (probe bot + replay `campHp`, 3 games):
  - a damaged camp never regains HP: every rise is a respawn from 0, and damaged camps held their HP 30+ rounds;
  - a damaged camp sleeps 2–3 rounds after the last champion is in its range (8 transitions), and its HP holds while
    asleep (43 of 43).
- **U-L3 answered** (`q/monodeath`-style read of the 48 losses): all 21 monolith deaths came with **no hit on the
  monolith** in the 20 rounds before.
  - 11 on 00road-of-riches: its group is 8 gem clusters + 1 monolith and **the bot saw only 8 camps** (next item). We
    hit the clusters and woke a monolith we didn't know about.
  - 10 on 01gold-rush / 01shortcut: a monolith already damaged and kept awake by bodies walking through range 5. The
    danger board skips the farm target's own group (`nav.cpp ch_build`, `skip_g`).
- **A bug, not in the plan: `MAXCG = 8` cut every group to 8 camps** [code, `types.h`; measured on all 40 maps with a
  boot probe].
  - 19 maps have bigger groups, up to 30 camps (01yellow-brick-road; 00stampede and 00great-wall 20,
    01concentrated-wealth 21).
  - Effects: the missing camps were unpriced (00road-of-riches: 400 gems hidden), and a group could look cleared while
    camps lived, so the capture never came. 00stampede: we killed the 6 elk, then stood beside 12 live camps we couldn't
    see until the enemy took the group.

### 8.2 Kept: the group fix (`submissions/cpp-p11.zip`, not uploaded: the user wants a bigger gain first)

- `MAXCG` 8 → 32 and `MAXLIVE` 24 → 48 (`types.h`); `sense` reads the current group's camps first.
- **The fuel it cost, and the fix:** rollovers rose to **21–24 a game** (01concentrated-wealth ~300). One body's turns
  ran out at exactly 100,000: Varg's `splash_m` is quadratic in the camps and `need_k` calls it for every body count.
  Fixed: `splash_m` once a round per group, stopping at its cap; `clear_model` sorts only the hitters (clusters add
  rounds only); the JOIN loop prices a group once a turn. Rollovers **0.9–4.1 a game** (p10 4.6).
- **Results vs cpp-p10** (final build, rollovers fixed):

  | | default seeds | fresh seeds (J = 50 … 2200) |
  | --- | --- | --- |
  | win % (null) | **52.3 % ± 0.8** (49.2), margin +73 | **53.8 % ± 1.2** (47.7), margin +84 |
  | walled maps | 63.6 % | 62.5 % |
  | big8 maps | 59.0 % | 60.4 % |
  | high-need maps | 43.3 % | 45.2 % |
  | worst maps | 00lost-world 1 / 16, 00expanse 3, 00great-wall 4 | 00expanse, 00monolith 3 / 16 |

  The same build before the fuel fix scored 53.8 / 55.3 %; the gap is inside one SE.
- **p11's null** (a jittered `cpp-p11` vs `cpp-p11`): 49.8 % ± 1.7 (default seeds), 48.3 % ± 1.3 (fresh).
- **The high-need maps lose** (43–45 % vs the null's 50 %): the full groups price the big takes as dear as they are,
  and N1 (below) didn't win them back.

### 8.3 Not kept

| Piece | Form | vs cpp-p10 | Head to head vs `_fix` (null 48.0) | Why it lost |
| --- | --- | --- | --- | --- |
| N1 | sessions on any group, `SESS_MAX` 8, team rule on 50 rounds without a one-session gem take | 55.5 % | – | 00contest 0 / 16 (−988): the team opened the monoliths at r50 with 1,000-HP bodies, a 7-session plan |
| N1b | the same, `SESS_MAX` 4 | 54.4 % (high-need 57.2) | **47.3 %** (high-need 52.9, other 44.7) | the team rule fired 2–12 times a game on every map; sessions on every group cost the open maps (00lanes 8 → 3, 01fracture 10 → 3 of 16) |
| N1c | sessions only on groups with draft need > roster | 53.1 % | – | lost the 00elkring / 01hooks gains |
| N1d | team rule: no gem group the full team finishes at once | – | 44.4 % | switched off on 00stampede once the camps were hurt; the five never met (3 / 16) |
| N1f | sessions only for the team's group; team rule from the draft (under 25 % of gems in groups the roster takes at once) | – | 48.3 % | 00stampede 14 / 16, 01the-farm +4, but 00monolith 9 → 3, 01boss-battle 6 → 3 |
| N1g | N1f, never a monolith's group | – | **48.8 %** (high-need 50.0) | level: 00stampede holds at 14 / 16; 00monolith 2 / 16, 00rows 5 / 16 |
| N2 | contested group not yet opened: price × k² / (k² + e²), e = enemies seen within 12 in 6 rounds | – | **42.2 %** | avoiding contested groups costs more than the steals it saves |
| N3 | break when HP < 70 % and F = Σ (6 − d)(allies − enemies) < 0, step toward an ally | – | 46.2 % | deaths 8.7 → 8.1, kills 7.6 → 6.3 |
| N3b | the break without the step | – | 44.2 % | breaking early at all costs fights |
| N5 | the main's gold weight 1.0 on cluster-only groups | – | 43.6 % | the main's gold is worth more than the cluster gems |

- **N1 is the right idea on 00stampede** (0-0 → 480-0 vs cpp-p10, three takes of 160 from r1259, as the winners'
  three) but never won head to head over its null. Its best form is `P12_N1_sessions.diff` (N1g).
- **N4 was not built:** it needs N1's sessions.

### 8.4 What this says about the ladder losses

- The plan's pieces copy what the winners do against us (take big groups, hold contested ones, break early). Locally,
  against our own p10, each costs more than it saves.
- The one clear win was a bug: the bot was blind to 12 of 20 camps in its biggest groups. **Read the bot's own model of
  the map against the engine** (camps per group, gems per group, need) before designing around a behaviour.
- **Open:** the danger board ignores awake camps of the farm target's own group (`skip_g`). That is half the monolith
  deaths (01gold-rush). The fix is a check in the farm itself: don't stand in range of an awake camp of my group that
  my company can't take.

## Sources [web]

- [teccles-halite/halite3-bot](https://github.com/teccles-halite/halite3-bot): Halite III 1st place; the target score in
  turns, return thresholds, the collision formula, return paths avoiding enemy-adjacent tiles.
- [mlomb, Halite III post-mortem](https://mlomb.dev/blog/halite-iii-postmortem): friendliness = Σ (4 − d)(allies −
  enemies); ally/enemy terms in the mining score; parameters copied from the top players' replays.
- [Battlecode 2024 postmortem, cout for clout](https://battlecode.org/assets/files/postmortem-2024-cout-for-clout.pdf):
  XSquare-style micro; the squadron system from Lanchester's square law; 47 vs 50 loses 90 %.
- [Battlecode 2025 postmortem, The Kragle](https://battlecode.org/assets/files/postmortem-2025-the-kragle.pdf): economy
  first (games snowball), idle-time fixes, copy the top teams.
