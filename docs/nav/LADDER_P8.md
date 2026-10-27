# cpp-p8 on the ladder: 67 losses read two ways (24 Oct, analysis only)

> "cpp-p8 gained ~+100 Elo on the ladder. Against teams near our Elo we win and lose about evenly. Against the very top
> teams we still get crushed." (user, 24 Oct)

`submissions/cpp-p8.zip` lost the 68 games in `replays_from_others/cpp-p8`. Each loss is read twice: for our mistakes,
and as a worked example of how the winner beats us. **No bot code changed.** The build comes next session (§7).

Team 0 is us. Numbers are per loss (per game) unless a line says otherwise. Tags as in CLAUDE.md:
- [measured]: counted in these replays;
- [code]: read in `bots/cpp`;
- [rules] / [sdk]: from `GameRules.md` / `cambc.h`;
- [guess]: not confirmed.

Our losses are their wins, so part of every gap is the result itself; read the gaps that are too large for that.

## 0. Summary

**The losses split cleanly by margin, and the two halves need different fixes** [measured]:
- **20 close losses** (we bank ≥ 65 % of their score; 19 of 20 against teams with no top-team signature) are an
  economy race. We die *less* than them (2.1 vs 3.1 a game), earn *more* gold (8,104 vs 6,991) and have the same max HP.
  But we gain 832 gems a game to their 1,035. Two thirds of that gap is the **contested groups** (153 vs 286 gems).
  The rest is our crew: their Marcella gains 197 gems a game, ours 80, and their crew hits elk, ours wolves.
  Three were lost in the last rounds of a race we could have won. In two of them our bags held the win when they
  finished.
- **33 crushed losses** (we bank < 35 %; all 9 T1 / T3 games are here) are fights. We die 16.6 times a game, they 4.3.
  The gap opens at a median r315, after an even start: at r100 we hold 29 gems to their 18, at r200 32 to 90.
  We lose the early fights **at equal max HP**: they land 15.1 hits and 1.9 casts a fight to our 8.7 and 0.6.
  - When an enemy is within 3, our melee bodies hit a champion on 16–24 % of rounds and move away on 38–48 %. Theirs
    hit on 31–48 % and move away on 21–26 %.
  - The same numbers held for p6's losses with a different crew (Ren, Ryth), so this is how our fight decision is
    built, not a draft effect.
  - Our "mixed" responses (a hit or two, then walking without getting away) die 32–84 % of the time.
- **Dash hops.** Holes can be dashed over, walls can't [rules]. On 13 of the 30 maps in these losses, a dash over a
  one-tile hole strip brings 21–100 % of the value 10+ rounds closer, even with the 8-round cooldown [measured, map
  study]. Our walk fields don't know this [code]. 25 of the 67 losses were on maps where that share is ≥ 40 %; only 4
  of those 25 were close.
- **Code found:**
  - `Kit::stun_enemy` has no caller (kit.cpp:122), so Heart of Ruin's stun dash is never aimed at a champion [code].
  - Our Heart of Ruin buys Strength shards; the winners' buys Focus, which its dash and shield scale with [measured,
    rules].
  - Our crew's first buy is at r282–r427, theirs at r87–r202 [measured].
- **U8–U10** (LADDER_P4): see §4.5–§4.7.
  - U8: the bank cap is not punished. Hoards fell from 8 of 38 losses to 4 of 67.
  - U9: opening fights is not the lever; answering the fights they open is. Those go 67 kills to 352.
  - U10: the dash's saved rounds go into more small takes.

The build plan (§7), in order:
1. Heart of Ruin's kit: the stun dash on champions, and a Focus build.
2. The engagement stance (decide once and hold; fleeing only when it gets away).
3. A dash-hop distance for dash bodies.
4. The crew's shop priced by the takes the purchase unlocks.
5. The closing race.
6. Contested groups priced as a race.

## 1. Method

### 1.1 Data and decoding

- **The replays.** `replays_from_others/cpp-p8` holds 68 bundles, every one a loss.
  - `c3a85ef1` and `ef2b26fa` are the same game: same map, picks, score and end round, and their decodes differ only in
    the file name. That leaves **67 distinct losses**.
- **Decoding.** Each bundle was unzipped, decoded with `decode.mjs` and flipped with `flip.py`, using the bundle's
  `team-a/b` logs (`tools/replay/farm/README.md`). We were side B in 18 of the 67.
- **Map grids.** These came from a scratch `bots/_mapdump` (`tools/mapdump.inc`; deleted after) on the 30 maps in the
  losses, then went through `tools/mapstudy.py`.
- **The p6 comparison.** cpp-p6's 38 losses were decoded the same way for the like-for-like rows in §3.
- **Scripts:**
  - the existing ones (`kpi`, `bagrisk`, `stuck`, `stall`, `fights`, `freehit`, `goldsrc`, `timeuse`, `elk`, `shop`,
    `tele`, `deaths`, `hpdeath`, `mvatt`, `noback`, `hitshare`, `agg`);
  - six new ones in `tools/replay/farm/` (Appendix B);
  - one-off queries in the session scratchpad.

### 1.2 Tiers: opponent families and margins

The bundles carry no team names, so opponents were identified by **draft and behaviour** (`oppsig.py`: recalls,
locks, wards, teleports and rollovers a game).

| Family | Signature [measured] | Losses | Margin |
| --- | --- | --- | --- |
| **T1** = TOP_TEAMS team 1 | Prism, Vesper, Marcella, (Willow), Heart of Ruin; pre-charged recall (1,970–3,470 recalls a game); 1–4 locks | 5 | 4 crushed, 1 mid |
| **T3** = TOP_TEAMS team 3 | Vesper, Heart of Ruin, Vendetta, Tavi, Marcella (3 bodies: the first three); 0 rollovers; 2–5 locks; 240–780 wards | 5 | 5 crushed |
| **PC** | pre-charged recall (1,340–4,340 a game), Marcella / Vendetta / Ryth / Vesper / Heart of Ruin, no Prism | 9 | 4 crushed, 4 mid, 1 close |
| other | none of the above; drafts vary (Stellar, Tavi, Willow, Cassi & Issac, Varg …); 20–120 recalls | 48 | 20 crushed, 9 mid, **19 close** |

- **Margin** = our banked score ÷ theirs at the end:
  - close ≥ 0.65 (20 games);
  - mid 0.35–0.65 (14);
  - crushed < 0.35 (33).
- **The gap-open round** is the last round at which their banked + carried total led ours by ≤ 100 (`oppsig.py`
  gapT). Medians: close r880, mid r531, crushed r315.
- **Reading.** The user's two groups line up with the margins.
  - "Top teams": T1 and T3 crushed us in 9 of 10 games, and the other was mid.
  - "Near our Elo": 19 of the 20 close losses are against "other" [measured].
  - Some "other" families crushed us every time we met them, so they are likely top teams without a known signature
    [guess]:
    - Vesper, Vendetta, Heart of Ruin, Cassi & Issac, Ryth: 5 of 6 crushed, every time on 00eight, 01starfish and
      01concentrated-wealth;
    - Vesper, Ryth, Vendetta, Tavi, Marcella: 3 of 4.
  - Below, **"top" = crushed** and **"similar" = close**. The family is kept per game in Appendix A.

### 1.3 A tool fault: farm.py's capture gems over-count

On 18 of the 67 games, `farm.py`'s `caps` give the winner up to 2–5× the gems it banked [measured]:
- 01corridors: 2,012 captured, 1,022 banked, with 1 death;
- 00lost-world: 5,525 captured, 1,113 banked.

So every gem total built on `caps` or `takes[].gem` is unreliable on some maps, and so are the take types. The scripts
affected are `stall` (capgems), `takes`, `elk` (types), `hpb` and `agg`.
- The likely cause is that the `Group` event's index doesn't match `farm.py`'s own components (`gem_of[g]`,
  farm.py:95) [guess].
- This report uses real bag increments instead (`gain.py`), which can't over-count.
- **Withdrawn:** a first pass said their takes were 40 % richer in gems (22.4 vs 16.0 a take). The bag increments show
  equal gain sizes: median 15 vs 15 in close losses.
- Older docs that quote `stall.py` capgems (LADDER_P4 §10.1: "contest 0–800 captured, stampede 0–1,920") may be off too.
- Fixing `farm.py` is a tool task (U-P8.1).

## 2. The 67 losses at a glance

| Decided by | Losses | Margin | Gap opens (median) | Top families (T1 / T3 / PC) | On hop maps (≥ 40 %) |
| --- | --- | --- | --- | --- | --- |
| **Fights**: our deaths ≥ 2× theirs + 3, or ≥ 1.5× + 3 with 8+ | 28 | 25 crushed, 3 mid | **r309** | 12 | 14 |
| **Farm**: fewer gems gained with level deaths (contested groups, crew) | 33 | 17 close, 11 mid, 5 crushed | r541 | 4 | 11 |
| **End race**: our banked + carried reached their final or 1,000 within the last rounds | 3 | 3 close | r1103 | 1 | 0 |
| **Gem-gated** (00stampede ×2, 01boss-battle: 0–150 banked) | 3 | 3 crushed | r748 | 2 | 0 |

[measured; the kinds are this report's rules, applied per game in Appendix A]

**Map features** [measured, `mapstudy.py` on the dumps]:
- **Team size.** S5 had 19 crushed and 13 close. S3 had 6 crushed and 2 close. S4 had 8 crushed and 5 close.
- **Map size:**
  - small (< 1,500 tiles, 19 losses): deaths 15.7 vs 5.3, banks 18.6 vs 37.0;
  - large (≥ 3,600 tiles, 21 losses): deaths 5.1 vs 2.6, banks 16.3 vs 29.6. The 100×100 losses (00ambush ×3,
    01big-world ×4) are all close or mid. There we die less than they do and lose the race.
- **Dash-hop maps.** On the 25 losses where ≥ 40 % of the value is 10+ rounds closer by a hop, we gain 410 gems a game
  to their 1,036. On the other 42 we gain 542 to 1,076.

## 3. Us vs the winners, by tier, against p6 and the top teams

Per 100 live body-rounds, or per game [measured, `kpi.py` and the scripts named]. "TT" = TOP_TEAMS §11, the three top
teams in their own wins.

| Measure | Close: us / them | Mid | Crushed | All p8 losses | All p6 losses | TT (T1 / T2 / T3) |
| --- | --- | --- | --- | --- | --- | --- |
| Camp hits | 16.0 / 18.6 | 12.8 / 17.0 | 10.4 / 15.0 | 12.9 / 16.6 | 9.3 / 13.4 | 18.3 / 16.2 / 16.5 |
| Champion hits | 0.6 / 0.7 | 1.6 / 1.8 | 3.0 / 4.1 | 1.8 / 2.5 | 2.1 / 2.8 | 3.0 / 4.0 / 4.2 |
| Banks a game; median bag | 25.1; 26 / 32.5; 26 | 20.6; 15 / 31.1; 23 | 8.0; 12 / 28.8; 28 | 15.7; 21 / 30.4; 26 | 14.3; 14 / 29.5; 26 | 31.9; 21 / 29.6; 23 / 28.9; 26 |
| Altar locks | 3.0 / 0.0 | 3.1 / 0.8 | 3.0 / 1.5 | 3.0 / 0.9 | 0 / 1.7 | 3.8 / 0 / 4.2 |
| Deaths | **2.1 / 3.1** | 6.8 / 5.1 | **16.6 / 4.3** | 10.2 / 4.1 | 12.1 / 8.2 | 4.9 / 6.7 / 4.9 |
| Dead, share of body-rounds | 2.2 / 3.2 % | 7.2 / 5.3 % | 18.8 / 4.8 % | 11.1 / 4.4 % | 10.7 / 7.0 % | |
| Fights opened | 2.6 / 4.8 | 5.3 / 7.1 | 6.3 / 13.3 | 5.0 / 9.5 | 9.7 / 12.2 | 9.1 / 10.3 / 7.7 (theirs) |
| Vesper casts (dash) | | | | 10.8 (7.0) / 11.3 (7.2) | 6.4 (2.9) | 12.1–12.7 (7.3–7.4) |
| Gold earned | **8,104 / 6,991** | 5,554 / 7,654 | 3,129 / 8,010 (kill 1,778) | 5,121 / 7,631 | 5,828 / 8,182 | |
| Max HP r300 / 600 / 1000 | 1,200 / 1,500 / 2,100 both | 1,150 / 1,500 / 1,700 vs 1,200 / 1,728 / 2,200 | 1,000 / 1,300 / 1,500 vs 1,200 / 1,700 / 2,350 | | 1,100 / 1,500 / 1,750 vs 1,200 / 1,500 / 1,800 | |
| Gems gained (bag increments) | 832 / 1,035 | 537 / 1,027 | 268 / 1,091 | | | |
| Lost holding 100+ | 3 of 20 | 0 of 14 | 1 of 33 | **4 of 67** | 8 of 38 | |

- **What p7 → p8 fixed on the ladder** [measured]:
  - the casts: Vesper's dash 2.9 → 7.0, level with every winner;
  - camp hits 9.3 → 12.9;
  - the median bag 14 → 21;
  - locks 0 → 3.0;
  - hoards 8 of 38 losses → 4 of 67.
- **What did not move:**
  - banks a game (14.3 → 15.7) and deaths (12.1 → 10.2);
  - the share of losses that are crushed (42 % → 49 %).
- **The close losses are near parity on every rate except gems gained** [measured]:
  - camp hits 16.0 vs 18.6;
  - banks 25 vs 32;
  - fewer deaths and more gold than them.
- **The crushed losses are a snowball** [measured]. Their kill gold is 1,778 a game. Their max HP leads by r300
  (+20 %), and by r1000 it is +57 %.
- **We start fewer fights and kill less than p6 did** [measured, `fights.py`]:
  - our kills in fights fell from 5.1 a game (195 in 38) to 2.5 (167 in 67);
  - theirs fell from 8.6 to 7.2;
  - their deaths fell from 8.2 to 4.1 a game. p6's Vesper hunted. p8's farms and dashes,
  and the dash is held only while an enemy is in sight (LADDER_P4 §11).

## 4. Our mistakes, by kind

### 4.1 Fights (28 losses decided; the gap opens at a median r309)

- **When** [measured]:
  - our deaths in crushed losses: 1.6 before r150, 1.6 in r150–300, 4.2 in r300–600, 9.1 after;
  - theirs: 0.5, 0.9, 1.1, 1.8.
- **Where:** 12.2 of our 16.6 deaths a game are on our own half (nearer our spawn), and theirs too are on our half (3.0
  of 4.3). They come to us.
- **How we die early** (108 deaths before r300 in crushed losses, `farm.py` deaths):
  - 78 % while walking;
  - 60 % with no ally within 5;
  - 53 % outnumbered;
  - 2.28 enemies near against 0.54 allies;
  - 20 to camps.
- **The fight itself** (`fightctx.py`; crushed, r < 300, 163 fights):
  - bodies 2.20 vs 2.38;
  - **max HP ratio 1.00**, current HP ratio 0.93;
  - hits a fight 8.7 vs 15.1, casts 0.6 vs 1.9;
  - focus (share of a side's hits on its most-hit target) 0.63 vs 0.73;
  - kills 34 vs 92.
  We lose 3:1 at equal HP and bodies.
- **Who starts it** (all 67 losses): they start 680 fights and we lose them 67 kills to 352; we start 394 and lose
  them 100 to 130.
  - When they start and our current HP is ≥ 1.25× theirs, we still lose: crushed, r300+, 14 kills to 44.
  - Even when we outnumber them, we lose 54 to 161.
- **What our bodies do in contact** (`engage.py`, an enemy champion within 3; p8 losses, p6 in brackets):

| Body | Hit a champion | Moved | Moved away | HP lost a round |
| --- | --- | --- | --- | --- |
| our Vesper | 48 % (50) | 44 % (42) | 29 % (24) | 79 (74) |
| our Marcella / Heart of Ruin / Varg / Vendetta | 23 / 24 / 16 / 20 % (Ren 22, Ryth 16, Varg 19, Vendetta 24) | 75–78 % | 38–48 % | 62–81 |
| their Vesper (crushed) | 60 % | 31 % | 18 % | 25 |
| their Heart of Ruin / Vendetta / Marcella / Ryth (crushed) | 48 / 45 / 31 / 33 % | 66–75 % | 21–26 % | 24–46 |

- **Flee or fight when hit** (`flee.py`, all 67 losses; % = the body died within 20 rounds / an enemy within 5 died):

| | Fight (hits in 2+ of the next 3 rounds) | Flee (no hit, gets farther) | Mixed (the rest) |
| --- | --- | --- | --- |
| our melee, HP > 70 % | n 188: 27 % / 24 % | n 289: 13 % / 11 % | n 280: **32 %** / 9 % |
| our melee, HP 40–70 % | n 66: 29 % / 18 % | n 158: 32 % / 8 % | n 168: **58 %** / 10 % |
| our melee, HP < 40 % | n 11: 55 % / 27 % | n 85: 31 % / 9 % | n 130: **84 %** / 10 % |
| their melee, HP > 70 % | n 316: 10 % / **47 %** | n 124: 5 % / 27 % | n 201: 10 % / 36 % |

  - Our worst outcome is the **mixed** one: a hit or two, then walking that doesn't get away. It is ~40 % of our
    melee responses and dies 32–84 % of the time.
  - Their healthy melee commits 1.7× as often as ours (316 vs 188) and trades 4.7:1; ours trades 0.9:1.
  - p6's numbers are the same shape (mixed: 36 / 58 / 83 % died), so this is structural.
  - Why we go "mixed", from the code [guess until traced]:
    - a melee chasing a kiting ranged body bans its target after `chase` rounds (3 for the crew) with no gain
      (beh.cpp:399) and drops to Heal or Farm while still in reach;
    - Heal takes P(lose) as its price the moment an attacker shows (prices.cpp:460), so Kill and Heal can flip from
      turn to turn;
    - the kill price falls linearly below 60 % HP (prices.cpp:402).
- **Melee move + attack in one round** (`mvatt.py`, crushed): ours 7–13 % of attack rounds (Varg 7, Vendetta 8,
  Marcella 9, Heart of Ruin 13); theirs 18–20 % (Heart of Ruin 20, Marcella 18, Ryth 20, Vendetta 19).

### 4.2 Farm: contested groups and the crew (33 losses decided; the gap opens at a median r541)

- **Gems gained, from bag increments** (`gain.py`; contested = the walk from our spawn and from theirs within 8 of each
  other):

| Gems a game, us / them | Our side | Contested | Their side | Total |
| --- | --- | --- | --- | --- |
| Close | 673 / 2 | **153 / 286** | 5 / 747 | 832 / 1,035 |
| Mid | 465 / 28 | 66 / 349 | 4 / 647 | 537 / 1,027 |
| Crushed | 164 / 54 | 99 / 704 | 4 / 328 | 268 / 1,091 |

  - In close losses, contested groups are 133 of the 203-gem gap, and their own-side rate the other 74.
  - Neither team takes the other's side.
  - Before r300 the contested split is close (25 vs 38). The gap builds after r300.
- **Presence** (`contest.py` in the scratchpad: body-rounds within 3 of a contested group; the 3 over-counted maps left
  out):
  - close 585 vs 854;
  - crushed 1,019 vs 1,975.
  - In both teams' takes there, the other team was near at the start only 11–23 % of the time. **They go there more;
    it is not a fight at the camp.**
- **The crew** (close losses, gems gained a game):

| | Vesper | Varg | Vendetta | Marcella | Heart of Ruin | Ryth |
| --- | --- | --- | --- | --- | --- | --- |
| Us | **393** | 176 | 118 | 80 | 56 | |
| Them | 259 | | 158 | **197** | 106 | 141 |

  - Our Vesper out-gains theirs; our crew falls short.
  - The gains are the same size (median 15–22 a round) and equally shared (an ally within 2 on 12–28 % of gains for
    both), so it's not crews or take size. Our crew takes fewer.
  - Camp-hit share r0–300 (`hitshare.py`): our Heart of Ruin 15 % vs 20 %, our Vendetta 12 % vs 24 %.
  - **Elk:** their Marcella, Ryth and Heart of Ruin put 53 / 60 / 43 % of their camp hits on elk. Ours put 30 / – / 27 %
    on elk and 59–64 % on wolves.
  - In crushed losses, elk is 47 % of their camp hits and 28 % of ours [measured: attack events by camp type].
- Gold is not the lever in close losses. We earn more (8,104 vs 6,991). Our pockets are near empty (median 3–15 gold
  carried at r300 / 600 / 1000) [measured], so the gold is spent, mostly by our Vesper (3,530 by r1000).

### 4.3 End race (3 losses, all close; the gap opens in the last ~100 rounds)

- **e7b1e911, 01broken-curve, 986–1020.**
  - At r1056 we stood at 986 of 1,000 with 4 + 4 gems in bags. Their three bodies carried 44 each in sight, so
    932 + 132 put them past 1,000.
  - Our Marcella then captured a 200-gem group at r1096, which is a 21-turn channel [rules: ceil(gems/10)]. Their
    Vesper finished its 44 at r1103.
- **dd99fc94, 00quadrants, 976–1008.**
  - At r714 we held 926 banked plus 43 + 25 + 25 in bags (1,019). No two of those bodies were within 8 of each other,
    so the win line (score + the bags *in sight*, prices.cpp:396) never fired.
  - Varg recalled home with 43 at 58 % HP (r711).
  - They banked 80 in 14 rounds.
- **426c7253, 01yellow-brick-road, 991–1036.** We reached 1,006 banked + carried at r1217; they finished at r1222.
- An ally's bag out of vision can't be read [measured: error 97, LADDER_P4 §11.1]. So no one body knows the team's
  bags.
- In dd99fc94 and 426c7253, the team's banked + carried passed 1,000 before they finished. In e7b1e911 it was 6 gems
  short at r1056.

### 4.4 Gem-gated (3 losses)

00stampede ×2 (0–1,120, 150–810) and 01boss-battle (0–1,396) are the old gated maps (LADDER_P4 §10.1, §11.4). Nothing
new was found there in this pass. They are left to their own design.

### 4.5 Hoards (U8)

- **Ended holding 100+:** 4 of 67 losses, against 8 of 38 for p6 [measured]:
  - 4379938e: 108;
  - 7b16f3c7: 104;
  - d08c1f1f: 266;
  - e7b1e911: 252.
  - Only e7b1e911 was decided by it (§4.3).
- **Bags:**
  - the median bag is 21 (close losses: 26, theirs 26);
  - banks a game are 25 vs 32 in close losses;
  - the death rate per 1,000 live rounds doesn't rise with the bag (`bagrisk.py`, close: 0.45 at bag 0, 0.18 at 20–49).
- **Failed tributes:** 0.1–0.3 a game on both sides [measured]. Banks are not being punished.
- **U8 answered:** the ladder does not punish the bank cap. The hoards that remain come from the end race (§4.3), not
  from the cap.

### 4.6 Fights opened (U9)

- **Fights we open:**
  - close losses: at a current-HP ratio ≥ 1.25, 29 fights, 14 kills to 2; at 0.8–1.25, 13 fights, 6 to 2;
  - crushed losses: at 0.8–1.25, 67 fights, 26 to 34; at ≥ 1.25, 60 fights, 19 to 12 [measured].
- **Fights they open:** 680, which we lose 67 to 352.
- **U9 answered:** opening even fights is not the lever (it was level locally too). The lever is how we answer the
  fights they start (§4.1), and the per-hit gap: casts and focus.

### 4.7 Walking and idle rounds (U10)

- **Time use** (`timeuse.py`, r150–600; farm.py's classes, which come from positions and are not hit by §1.3):
  - us: take 31.2 %, walk 48.1 %, still 14.1 %;
  - them: take 43.6 %, walk 40.6 %, still 10.5 %.
- **Close losses:** camp hits 16.0 vs 18.6 and banks 25 vs 32.
- **U10 answered** [guess from the replay; the TRACE `tu.py` split was not run]:
  - the dash's saved rounds became more trips and more small takes, not longer takes;
  - the remaining walking gap sits on the dash-hop maps (§5.2) and in the crew's wolf habit (§4.2).

### 4.8 Deaths and their causes (all losses)

- **Who dies, a game:** Marcella 2.4, Vesper 2.4, Varg 2.3, Heart of Ruin 1.9, Vendetta 1.2 [measured]. In crushed
  losses Marcella dies 4.0 a game, Varg 3.8 and Vesper 3.8.
- **Our killers in crushed losses:**
  - Vendetta 111, Vesper 94, Marcella 86, Heart of Ruin 71;
  - camps 55.
- **The fatal fight:** a median 8 rounds from the first hit to the death; the victim hit back 56 % of the time; 60 % of
  its moves were away from the nearest enemy.
- **Gems lost on death, a game:** close 14, mid 29, **crushed 87** (theirs 12–33).

### 4.9 Stuck bodies

- 6 stands of 40+ rounds on one spot, 404 body-rounds, against 11 for p6 [measured].
- The worst: 01big-world, Marcella, 174 rounds at 70 % HP with no bag; 00ambush, Marcella, three stands at 36–50 %.
- No game was decided by it.

### 4.10 Failed banks and contested takes

- **Failed banks:** tribute channels that didn't land: 0.1–0.3 a game on both sides (§4.5).
- **Steals:** captures of a group the other team cleared: 1.1 a game by us, 3.2 by them in crushed losses (`side.py`
  in the scratchpad; the counts come from positions, not the gem totals).
- Contested takes are lost by absence, not by contest (§4.2).

## 5. The winners, reverse-engineered, mechanic by mechanic

Each entry gives what they do, the size of the gap [measured], why it works ([guess] until checked), and what doesn't
transfer.

### 5.1 Draft, builds and shop

- **Draft.** Their picks across the 67 losses:
  - Vesper 55, Marcella 48, Vendetta 44, Ryth 42, Heart of Ruin 34, Tavi 24, Prism 15, Willow 13, Cassi & Issac 11;
  - **Varg 5** (we draft Varg every game).
  - Ryth is in 42 drafts and in none of ours. Its ground-target area stun (radius 1, from 4) is the stun that breaks
    channels and opens fights [rules].
  - Doesn't transfer: Prism's gem battery needs Prism and a closing rule. Cassi & Issac is two bodies.
- **Heart of Ruin's build.**
  - Theirs: Bruiser Focus 56 %, Power Focus 26 % (close losses); Bruiser Focus 38 %, Bruiser Health 25 % (crushed).
  - Ours: Bruiser Health 0.45–0.56, then **Power Strength 0.44–0.55** [measured]. That's the crew default
    (champs.cpp:41) [code].
  - Heart of Ruin gains 15 Focus a shard and 5 Strength [rules]. Its shield (1.5 × Focus) and stun dash (1.75 × Focus,
    radius 1) scale with Focus.
  - In contact, their Heart of Ruin loses 24 HP a round; ours loses 67 [measured, crushed].
  - **Copy it.** It's a kit fix.
- **Marcella's build.** Theirs is Bruiser Strength 56 %, Bruiser Health 17 % (close losses). Ours is Bruiser Strength
  36 %, Bruiser Health 32 %, Treasure Strength 16 % and Jungle Strength 15 %. Close enough; not a priority.
- **Shop timing:**
  - our crew's first buy (median): Varg r282–r347, Marcella r242–r299, Heart of Ruin r403–r427, Vendetta r196–r216;
  - theirs: r87–r202 for every crew body;
  - our Vesper buys first, at r72–r84 [measured].
  - In crushed losses our crew is at base HP at r300 (Heart of Ruin, Varg, Vendetta 1,000). Theirs is at 1,200–1,700.
  - Our shop price is g2g × gold ÷ (recall + walk home), about 2 a round against farm prices of 5–15
    (prices.cpp:480–491) [code]. The crew goes home only when hurt.
  - Why theirs works [guess]: Health early lets a lone crew body pass the need test on elk groups (§4.2) and survive the
    first contact (§4.1).
  - The crew's early shop lost locally in p6 as "recall at 2 shards" (`_cs`, 47 % vs p6). §6 N4 prices it
    differently.

### 5.2 Route: dash hops and teleports

- **Dash hops.**
  - A dash moves 2 tiles and may cross holes, not walls [rules].
  - On the maps in these losses, dash bodies crossed a hole tile 10.0 times a game for them and 6.0 for us
    (`hops.py`) [measured].
    - On 01fracture, 70 vs 14.
    - On 00gem-fields, 34 vs 3.
    - On 00gemfight, 14–27 vs 3–6.
    - On 01big-world, 13–28 vs 6–11.
  - `hopmap.py` (8-round cooldown modelled; ring of each group from our spawn) gives the share of value 10+ rounds
    closer by hops:
    - 01starvation 100 %;
    - 00reverse-spiral 98 %;
    - 01gold-rush 89 % (the 200-gem group: 26 → 9);
    - 01fracture 85 %;
    - 00gem-fields 79 % (71 gems: 22 → 3);
    - 01concentrated-wealth 71 % (the 71-gem centre: 90 → 29);
    - 01islands 65 % (groups no walk reaches: unreachable → 28);
    - 00gemfight 61 % (78 gems: 29 → 9);
    - 00rushbait-v2 50 %, 00swirl 46 %, 00pilgrimage 41 %, 00ambush 29 %, 00split 21 %.
  - **01concentrated-wealth, f5e0d518, read by hand:**
    - Their Vesper went from spawn to the 71-gem centre in 40 rounds, dashing over the one-tile hole row.
    - Our five walked the outer edge to the north for 100 rounds, 22 gems in the Vesper's bag.
    - We reached the centre at r121 and lost three bodies there by r163 (Marcella, Vendetta, Varg); they lost Cassi &
      Issac and their Vesper.
  - **Why it works:** the centre is 90 walking rounds away and 29 with hops. Our prices and the draft read walk-only
    distance fields (nav.cpp:341, prices.cpp:362) [code], so the centre is never chosen.
  - Our dash picks the lowest walk-field value in reach (nav.cpp:364). It hops only when the walk field already leads
    across the holes.
  - Doesn't transfer: Varg and Marcella have no dash [rules]. A route through hops splits the crew unless the
    non-dash bodies take the walk side.
- **Teleports.** Crystals were used in 6 of 67 losses: 00reverse-spiral 21 jumps, 00ambush 15, 01big-world 15,
  00pilgrimage 14, 00gemfight 6, 01corridors 5 [measured].
  - The walks saved: 17–105 tiles (pilgrimage 94–105, reverse-spiral 34–52).
  - The planner is parked (LADDER_P4 §10.4, U6). It is the same "jump" structure as the dash hop (§6 N3).

### 5.3 The opening

- **Even at first.** In crushed losses we were level or ahead at r100 (29 vs 18 gems held; first capture r38 vs r36).
  The first 150 rounds aren't lost by route.
- **Then the first contact** (r100–r200) turns it: 1.6 deaths a game before r150 and 1.6 more by r300.
- **Exception: the hop maps.** On 01concentrated-wealth they banked the centre (71) at r90, before any fight.
- Cohesion in the opening is equal: allies within 5 were 1.33 vs 1.31 in crushed losses before r300. With an enemy
  within 8 it was 1.35 vs 1.61 allies, and 28 % vs 22 % alone [measured]. Not the main gap.

### 5.4 Crews, stacking and contested groups

- **Contested presence** is 1.5–1.9× ours (§4.2). Their own side's rate is also higher (747 vs our 673 in close
  losses).
- **Why it works** [guess]: our farm price is value ÷ bodies ÷ (walk + clear + 5 + detour) (prices.cpp:284). It has
  no term for the race, so a contested group is priced like one of ours. When an enemy is seen, the risk terms cut its
  price (prices.cpp:367, 280). But they rarely take our side (2–54 gems a game), so a contested group taken by them is
  lost twice: once to us, once added to them.
- **Doesn't transfer:** their stacking in the T3 / T1 games comes with their fight strength. Going to the contested
  groups without the fight fixes (§6 N1, N2) would feed them kills [guess].

### 5.5 Fights

- **Who opens:** they open 9.5 fights a game to our 5.0; 13.3 to 6.3 in crushed losses.
- **Distance:** the median first hit comes from 3 tiles on both sides.
- **HP ratio when they open:** spread evenly. They open at 0.8–1.25 and at ≥ 1.25 alike (crushed, r300+: 107 and 92
  fights) and win both.
- **Focus:** 0.73–0.80 for them, 0.63–0.69 for us.
- **Casts a fight:** 1.9 vs 0.6 early, 1.2 vs 0.2 later.
- **Stuns on channels:** failed tributes are 0.1–0.3 a game (§4.10), so there's nothing to see there.
  - The stuns are in the fights: Ryth's area stun, Tavi's, Marcella's enhanced reset, Heart of Ruin's dash landing.
  - The engine logs don't mark a stunned round, so stuns weren't counted [measured: absent from the decode].
- **Commitment:** their healthy melee commits 1.7× as often as ours and trades 4.7:1 (§4.1).
- **Their Vesper:**
  - in contact it hits 60 % of rounds and moves away 18 %; ours 48 % and 29 %;
  - it loses 25 HP a round in contact; ours 75–79.

### 5.6 Banking and altar locks

- **Banks:** they bank 29–33 times a game at a median bag of 22–28, against our 25 at 26 in close losses. Banking
  follows gains; it's not a separate gap.
- **Locks:** we place 3.0 a game, they 0.9 (T3 2–5, T1 1–4, most others 0). No tribute of ours failed to a lock
  (§4.10).
- **The close:** the winners finished the race while our bags were split and out of sight (§4.3).
  - T1's closing rule (TOP_TEAMS §0 item 1) is "banked + carried ≥ 1,000, then all tribute".
  - It is team-level. Our win line is per body (prices.cpp:394–396).

### 5.7 How they punish us specifically

- **Our Vesper:** 3.8 deaths a game in crushed losses (killers: Vesper 22, Vendetta 21, Marcella 20, Heart of Ruin 16
  of 126). Close losses: 0.4.
  - It dies in long fights (median 12 rounds, hit back 91 %, alone 42 %). That's a kite that runs out, not an ambush
    [guess].
- **Our bags:** 87 gems a game lost on death in crushed losses, and 48 deaths with 20+ gems.
- **Our banks:** not punished (§4.10).
- **Our crew:** in crushed losses they kill Marcella 4.0 times a game, Varg 3.8 and Heart of Ruin 3.1.
  - These are the bodies that move away 38–48 % of contact rounds (§4.1), so they take hits without returning them.

### 5.8 Marcella and Heart of Ruin: theirs vs ours

| | Their Marcella | Ours | Their Heart of Ruin | Ours |
| --- | --- | --- | --- | --- |
| Casts / 100 live (slot 0 / 1) | 2.8 / 3.7 | 2.6 / 2.5 | 5.0 / 9.6 | 3.0 / 9.3 |
| Gems gained a game (close) | 197 | 80 | 106 | 56 |
| Gold a game (all; Marcella incl. tribute gold) | 1,697 | 581 | 712 | 286 |
| Camp hits on elk (close) | 53 % | 30 % | 43 % | 27 % |
| In contact: hit a champion / HP lost a round (crushed) | 31 % / 44 | 21 % / 74 | 48 % / **24** | 23 % / 67 |
| Build | Bruiser Strength 56 % (close) | Treasure / Jungle Strength, Bruiser | **Bruiser Focus, Power Focus** | Bruiser Health, Power Strength |
| Deaths a game (crushed) | 0.4 | 4.0 | 0.5 | 3.1 |

[measured]
- Heart of Ruin's slot-0 shield: 5.0 casts vs 3.0. Ours shields only after a hit (main.cpp:112) [code].
- Its dash: 9.3 vs 9.6, about equal in count. Ours lands on camps (`dash_camp`, p8) and never on a champion: there is no
  caller for `Kit::stun_enemy`. `cast_fight` uses only unit-target slots (kit.cpp:111–120) [code].

## 6. New approaches for the biggest gaps

Each entry gives the rule written map-free, what it reads at runtime, the code it would touch, the measure, and its
unknowns.

### N1. The engagement stance: decide once, hold it, flee only when it gets away *(changes how the fight decision is made)*

- **Today.** Every turn re-prices Kill, Heal and Farm on their own. A body in contact flips between them and ends
  "mixed" (§4.1).
- **The new rule.** On contact, the body chooses a **stance**, COMMIT or BREAK, and holds it for `STANCE_HOLD` rounds
  [guess 6]. Contact = an enemy champion hits me, I hit one, or one is within its reach + 1.
  - It re-decides only on an event: a body dies on either side, a new enemy comes within 5, an ally arrives within 3,
    or my HP crosses `STANCE_LOW` [guess 0.25].
- **BREAK only when the escape works**, read from the state:
  - I'm ranged and every enemy in reach is melee without its dash ready;
  - or my dash is ready and theirs isn't;
  - or the walk to safety (spawn, or an ally group) takes fewer rounds than they need to kill me (HP ÷ their DPS in
    reach).
- **Otherwise COMMIT,** even at a high P(lose). Fleeing at equal speed costs HP without returning damage: mixed dies
  32–84 %, fight 27–55 % [measured].
- **A committed body:**
  - opens with its control (N2), then hits every round it can (move + attack for melee);
  - broadcasts C_KILL + its target. Allies within `JOIN_FIGHT_R` price the join with a commit bonus and **hit the same
    target** (their focus 0.73–0.80, ours 0.63–0.69).
- **The commit/break choice is team-level:** our bodies within 5 vs theirs within 5 plus fresh sightings, strength
  Σ HP × DPS with the kits (`fkit`), the same inputs `duel` reads.
- **Reads:** `s.e[]`, `s.a[]` (HP, range, dash ready), my HP, dash cooldown, walk home, the slot codes.
- **Code:**
  - prices.cpp:300–312 (`pre_turn`: `trapped` becomes the stance), 400–445 (Kill, Join), 446–473 (Heal's pdie);
  - upd.cpp:180–200 (the hold logic: `HOLD_TURNS`, `chase`);
  - beh.cpp:366–420 (`kill_fight`: drop the ban at :399 while committed; walk + hit);
  - beh.cpp:457 (`fall`);
  - state.h (`stance`, `stance_until`).
  The flags it replaces (`trapped`, the chase ban inside a fight) are deleted, not kept beside it (rule 3).
- **Measures:**
  - in contact, melee hit share 16–24 % → ≥ 35 % and move-away 38–48 % → ≤ 25 % (`engage.py`);
  - the mixed share and its death rate (`flee.py`);
  - HP lost a contact round 62–81 → ≤ 50;
  - kills in fights they start (`fights.py`);
  - deaths a game, against both bars.
- **Unknowns:**
  - Is "mixed" Kill ↔ Heal flips, the chase ban, or `NAV.near` in Fight mode failing to close? Run the TRACE `flee`
    line (upd.cpp:184) on a local game first.
  - Does BREAK's test need the enemy's dash cooldown? It isn't in vision [guess: it can be tracked from seen casts].

### N2. Heart of Ruin's stun dash on champions, and its Focus build (a kit fix)

- **The rule.** In `kill_fight`, a Heart of Ruin whose dash is ready and whose target is within 3 dashes to a tile
  adjacent to the target. That stuns everything within 1 and deals 1.75 × Focus [rules], before the walk or the hit.
  - The same entry gives any ground stun (`stun_ground`) a caller: `Kit::stun_enemy`, which exists and is never called
    (kit.cpp:122).
- **Build.** Bruiser Focus, then Power Focus, as the winners' (§5.1).
- **Reads:** the target's position, the stun slot's cooldown, the free tiles next to the target.
- **Code:**
  - kit.cpp:111–135 (`cast_fight` / `stun_enemy`);
  - beh.cpp:376–411 (`kill_fight` before `NAV.near`);
  - champs.cpp:38–45 (the build: a Heart of Ruin row, like Marcella's at :45).
  - Checklist: `docs/CHAMPIONS.md` "Swapping a champion" (kit first; swap rarely).
- **Measures:**
  - Heart of Ruin's HP lost a contact round, 67 → ≤ 35;
  - its hit share in contact;
  - casts per fight (ours 0.6 vs 1.9);
  - deaths;
  - both bars.
- **Unknowns:**
  - Does a landing tile need to be free of the target's allies?
  - Does the stun stop the target's move + attack that round [rules: a one-turn stun]?
  - Is Focus worth it while its dash also farms camps [guess yes: the dash's camp damage is 1.75 × Focus over radius 1]?

### N3. A dash-hop distance for dash bodies (changes the walk model the prices read)

- **The rule.** A dash body's distance to a group, an altar or home is the shorter of:
  - the walk;
  - the walk to a **hop portal** + 1 + the walk from its far side.
  The dash runs on an 8-round cooldown, so each extra hop on a route adds the rest of the cooldown.
- **Portals** are found once at boot from the terrain: pairs of free tiles at Chebyshev 2 with a hole between and a
  legal 2-step dash path [rules]. Neighbouring pairs are merged into one portal per hole strip.
- **Per portal side,** one distance field is computed at boot: the draft turn gets 10× fuel and the first turn 2× [sdk].
  Keep the K portals with the biggest value saving if there are many [guess K = 8].
- **Nav.** When the chosen goal's best route uses a portal, step to its near side (a `NavKey::Tile` goal, as the parked
  teleport planner did) and dash across: `dash_pick`, allowing the landing across the hole.
- **The crew.** Non-dash bodies (Varg, Marcella) keep the walk distance. A goal whose cheap route needs a hop is priced
  for the dash bodies only.
- **Reads:** the hole and wall bitboards (w.holes, w.walls), `has_dash`, the dash cooldown, the portal fields.
- **Code:**
  - world.cpp boot (the portal scan);
  - nav.cpp:330–347 (gd / ad after `F_me`: take the min with the portal routes), 364 (the dash pick);
  - prices.cpp:362 (`wk`);
  - the draft's d_us (draft.cpp) and upd.cpp's seed (:19–30) for the opening.
  - One "jump" structure serves both the dash hop and the parked crystal teleport (U6): a crystal is a portal with cost
    3-turn channel + 10 gold + a spawn visit.
- **Measures:**
  - hole hops a game, 6 → ≥ 10 (`hops.py`);
  - per-map margins on the 11 hop maps (≥ 40 %) against both bars, all of them in the local 40-map pool;
  - contested gems gained (`gain.py`);
  - the walk share.
- **Unknowns:**
  - Fuel for K portal fields on 100 × 100.
  - An unseen unit on the landing tile makes the dash return false (no cooldown spent) [rules]: retry the other
    landings.
  - Does splitting the crew around hop routes cost more than the hop saves on maps with few hop groups?

### N4. The crew's shop priced by the takes the purchase unlocks *(changes the gold currency)*

- **Today.** The shop price is gold × g2g ÷ round trip, about 2 (prices.cpp:490). Gold has no use in the price until
  it is spent.
- **The rule.** The value of a shop trip = the farm-price gain of the groups the purchase makes takeable:
  - re-run `need_k` with the bought HP (Health growth × the shards in reach of my gold [sdk: `item.cost()`, the champion
    growth]);
  - sum the farm prices of the groups that go from 0 to > 0;
  - add the death cost the extra HP saves in the fights seen in the last 50 rounds.
  - Compare it with the farm rate lost to the trip (recall + walk back).
  - When a bank or a heal already passes the spawn, the shop is free.
- **Reads:** `s.gold`, `ME.target`'s cost and growth, `need_k_r9` (prices.cpp:216–240) at hp + ΔHP, the nearby groups'
  prices, the enemies' HP seen.
- **Code:** prices.cpp:480–491 (Shop), :216 (`need_k_r9`: an hp argument); champs.cpp:38–45 (Bruiser Health first on
  the crew, as now).
- **Measures:**
  - the crew's first buy, r282–r427 → ≤ r160 (`shop.py`);
  - crew max HP at r300 (`hpdeath.py`);
  - the crew's elk share of camp hits, 27–30 % → ≥ 40 % (the attack-event query);
  - crew gems gained a game (Marcella 80, Heart of Ruin 56 → ≥ 120 / 90; `gain.py` per champion);
  - both bars.
- **Unknowns:**
  - Is the crew's elk avoidance `need_k`'s HP floor (`KEEP_HP`) or the claim rules [guess: the floor, LADDER_P4 §10.4]?
  - `_cs` (recall at 2 shards) lost 47 % vs p6. Does pricing by unlocked takes avoid its farm-time cost?

### N5. The closing race *(a team-level mode switch)*

- **The rule.** Enter closing mode when the race can end soon: score_us + my bag + B̂ ≥ 1,000 − Δ, or score_them ≥
  1,000 − Δ.
  - B̂ is the expected bag of the allies I can't see: the median bag × their count [guess 21 each].
  - Δ is about one median bank cycle [guess 60].
- **In closing mode:**
  - every body with a bag banks at the nearest open altar now;
  - no take is priced whose walk + clear + channel (ceil(gems/10)) [rules] ends after the enemy's ETA;
  - the enemy's ETA is score_them + their bags in sight, at their bank rate. If it comes before ours, the Kill price of
    a **channelling** enemy (`e.submitting`, prices.cpp:416) rises: a stun or a death stops a tribute [rules].
- The mode is shared through the event byte (byte 7, comms.h), so out-of-sight bodies switch too. The win line can't see
  them [measured: error 97].
- **Reads:** `global_submitted_gems` both sides [sdk], my bag, the bags in sight, the enemies channelling, altars.
- **Code:** prices.cpp:380–397 (Bank, the win line), :258 (farm value: the channel term near the end), :405–420 (Kill
  of channelling enemies); comms.cpp byte 7.
- **Measures:**
  - local games lost by < 60;
  - losses ending with ≥ 50 carried;
  - ladder: the 3 end-race losses (§4.3).
- **Unknowns:**
  - Δ and B̂.
  - Does the byte-7 event collide with the death mark (`mark_death`)?

### N6. Contested groups priced as a race *(changes what a group is worth)*

- **The rule.** A group's value counts what the take does to the **gem difference**, not just our gems:
  - a contested group taken by us is gems × (1 + P(they take it otherwise));
  - an own-side group is gems × (1 + small), since they take our side rarely: 2–54 gems a game [measured].
  - Respawn timing then orders the route: contested groups while they're up, our own side while the contested ones
    respawn (mem.until).
  - P(they take it otherwise) is read from the side (world.cpp:70: |d_us − d_them| ≤ 8), the respawn timer and the
    sightings near the group [guess: start at 1 for contested, 0.05 for ours].
- **Reads:** `o.side`, d_us / d_them, `mem.st` / `mem.until`, sightings.
- **Code:** prices.cpp:258 (value), :372 (posture `farm_their_side`).
- **Measures:**
  - contested gems gained a game, close losses 153 vs 286 (`gain.py`);
  - presence;
  - own side unchanged;
  - deaths at contested groups;
  - both bars.
- **Unknowns:**
  - Without N1 / N2, going there may feed kills: build it after them.
  - Was this tried? ROUTING piece 5 priced exposure on the legs (lost), not the race value of a group.

### Considered and dropped

- **A gold exchange rate tied to purchases.** Dropped: gold isn't hoarded (3–15 in pocket), and in close losses we
  out-earn them. N4 covers the useful part.
- **"Their takes are richer":** withdrawn (§1.3).
- **Pre-charged recall** (T1, PC): it saves one recall turn [rules]. It's small next to N1–N6.

## 7. Build plan for the next session (ranked)

Judged as usual: against `bots/cpp-p8` and `bots/spar-meta`, 8 fuel jitters each (`OPP=cpp-p8 sh tools/jitter.sh cpp`,
`OPP=spar-meta sh tools/jitter.sh cpp`). A piece stays only if it wins more than it loses against **both**, and any
head to head against `cpp` is read against the 43 % null (LADDER_P4 §11.2).

| # | Piece | Why first | Decides (ladder) | Local measures beside the win rate |
| --- | --- | --- | --- | --- |
| 1 | **N2 Heart of Ruin kit**: stun dash on champions + Focus build | Small, a missing caller and a build row; feeds N1's opener | part of the 28 fight losses | Heart of Ruin HP lost a contact round, casts a fight, deaths |
| 2 | **N1 engagement stance** (commit / break, held; team focus) | The biggest gap (28 losses, gap r309), structural since p6 | 28 fight losses, the crushed tier | `engage.py` hit / move-away shares, `flee.py` mixed share, deaths, kills in their fights |
| 3 | **N3 dash-hop distance** | 25 losses on hop maps, 21 of them mid / crushed; map-derived, generic | hop-map losses | hops a game, per-map margins on the 11 hop maps, contested gems |
| 4 | **N4 crew shop by unlocked takes** | The crew's elk and HP gap; the close losses' crew deficit | 17 close farm losses, early fights | crew first buy, crew HP r300, elk share, crew gems |
| 5 | **N5 closing race** | Cheap, 3 close losses, team-level | 3 end-race losses | games lost by < 60 |
| 6 | **N6 contested race value** | The close losses' main gem gap, but risky before 1–2 | 17 close + 11 mid farm losses | contested gems, deaths at contested groups |

- **Before building:**
  - trace one local game with the TRACE `flee` line to name the "mixed" cause (N1's unknown);
  - fix `farm.py`'s capture gems (U-P8.1), so `stall` / `takes` / `elk` can be trusted again.
- **Order of the pieces:**
  - N2 and N1 need each other (the opener and the commit), so build them together and judge them as one piece
    (rule 3);
  - N3 is independent;
  - N4 before N6, since N6 sends the crew where the fights are.

## 8. Unknowns to check when building

- **U-P8.1:** why `farm.py`'s `caps` over-count. The `Group` index vs `gem_of` (farm.py:95) [guess]. Until it's fixed,
  use `gain.py` for gem totals.
- **U-P8.2 (answered, §9.1):** Kill ↔ Heal flips on P(lose) near 0.5; 71 of 101 local deaths came in Heal. Not the
  chase ban, not `NAV.near`.
- **U-P8.3 (answered, §9.1):** an enemy's dash readiness is readable in vision [sdk]; the BREAK test that used it lost
  and was deleted.
- **U-P8.4:** the portal count and fuel on the hop maps (N3). A legal dash path over two-wide holes is not possible
  [rules: 2 steps], so only one-wide strips count. The cheap field form lost (§9.5); the portal form is unbuilt.
- **U-P8.9:** does the stance's `STANCE_PL` 0.7 / `STANCE_LOW` 0.45 hold against the ladder's stronger fighters, or
  does it over-commit (deaths a game in the p9 ladder losses vs p8's 16.6 crushed)?
- **U-P8.10:** the Heal deaths with bags (§9.4): would a break that banks or goes to the nearest ally beat the recall
  walk?
- **U-P8.5:** is the crew's elk avoidance `KEEP_HP` in `need_k`, or the claims (N4)?
- **U-P8.6:** the "other" families that crush us every time (Vesper, Vendetta, Heart of Ruin, Cassi & Issac, Ryth;
  Vesper, Ryth, Vendetta, Tavi, Marcella): are they known ladder top teams? [guess: yes; names would settle it]
- **U-P8.7:** the end-race constants Δ and B̂ (N5).
- **U-P8.8:** was ROUTING piece 5's loss (exposure) a sign that N6 will feed kills? Build N6 only after N1 / N2.

## 9. Built (24 Oct, late): N1 + N2 kept as cpp-p9; N3 tried and parked

### 9.1 The trace first (U-P8.2 answered)

A TRACE copy of `bots/cpp` (= p8) with a per-round contact line (`cx`: choice, decided, attacked, moved, distance
before and after, P(lose)) on 01starfish and 00gemfight vs spar-meta and cpp-p8 (4 games) [measured]:
- **The cause is Kill ↔ Heal flips.** Kill → Heal was the most common switch in contact (109). 205 of 222 Heal entries in
  contact had P(lose) > 0.5, and 79 of them were at HP > 70 % (prices.cpp `pdie = plose` once an attacker shows).
- **Heal is the walk away.** 35–47 % of our melee contact rounds were Heal, with ~0 hits; **71 of 101 deaths came in
  Heal**.
- The chase ban (beh.cpp:399) held a contact target on 2–42 rounds per body, and Kill rounds moved away ~0 times, so
  neither the ban nor `NAV.near` Fight mode is the cause.
- **U-P8.3 answered:** an enemy's dash readiness is in vision (sense.cpp: `ab.cooldown()` on its abilities within 6)
  [sdk, code]. No tracking needed.

### 9.2 What was built (`bots/cpp`, = `submissions/cpp-p9.zip`)

- **N1, the stance** (upd.cpp `upd_stance`, run each turn before the reflexes):
  - **Contact** (`contact`, prices.cpp): an enemy champion hit me, I can hit one, or one can step and hit me next round
    (its reach + 1; reach = 2 melee, its range ranged, +2 with its dash ready). Not near their spawn.
  - On contact the body decides **COMMIT** or **BREAK** and holds it `STANCE_HOLD` 6 rounds. It re-decides on an event:
    the count of enemies within 5 changes, an ally comes within 3, HP crosses `STANCE_LOW`, or the target is gone.
  - **BREAK** = Heal (the recall walk) when P(lose) > `STANCE_PL` 0.7 or HP < `STANCE_LOW` 0.45 of max. Otherwise
    **COMMIT** = Kill on one target: the one an ally broadcasts (C_KILL), else the fewest hits + the walk.
  - A commit that neither hurt its target nor closed on it over a full hold bans the target. That is the chase ban
    moved into the stance; the hunt (a priced Kill out of contact) keeps its own.
  - A committed body dashes into reach every time it can, shields as it closes (`Kit::shield`'s `fight`), and
    `Kit::stun_enemy` now has a caller (ground stuns first, then `cast_fight`).
  - **Deleted:** `trapped`, `flee_ok`, Fall's trapped fight, the in-fight chase hold in `upd_decide` (`prof.chase`
    rounds), `retreat_now` in `upd_decide`, Heal's `pdie = plose` line, the Fall-only Kill state (`fkd`, `fkn`, `kz`).
- **N2, Heart of Ruin:**
  - `Nav::dash_land`: in `kill_fight`, before the hit, the landing dash onto the free tile within 1 of the target that
    touches the most enemies (never next to a camp);
  - the build: Bruiser Focus, then Power Focus (champs.cpp).
- **Not kept on the way** (8 jitters each vs cpp-p8 unless noted):
  - **the design's own rule, "commit even at a high P(lose) when the escape fails" (`escape_ok`): 28W/52L on one run.**
    Locally a commit at P(lose) > 0.5 died within 10 rounds 87 of 244 times (36 %), a break 9 of 447 (2 %), a commit at
    P(lose) ≤ 0.5 20 of 852. Deleted.
  - `STANCE_PL` 0.4 / 0.5 / 0.6 / **0.7** / 0.8 = 48.6 / 53.1 / 55.9 / **56.7** / 52.0 % (with `STANCE_LOW` 0.25);
    0.6 / 0.8 again with `STANCE_LOW` 0.45: 56.2 / 60.9 %.
  - `STANCE_LOW` 0.15 / 0.25 / 0.35 / **0.45** / 0.55 = 50.8 / 56.7 / 61.1 / **62.8** / 61.4 %.
  - `STANCE_HOLD` 3 / **6** / 10 = 53.1 / 53.1 / 48.9 % (at `STANCE_PL` 0.5).
  - contact without the passers-by (only "hit me or I can hit it"): 52.5 %;
  - BREAK as Fall instead of Heal: 55.3 %.

### 9.3 Results

- **vs cpp-p8: 62.8 % ± 1.3, margin +124, deaths 6.7 vs kills 11.1** (402W/238L). An exact jittered copy scores ~43 %
  (LADDER_P4 §11.2).
- **vs spar-meta: 91.7 % ± 0.5, margin +456, deaths 4.5, kills 13.7** (p8: 90.0 % ± 1.2, +414).
- **Fresh seeds (selection check, J = 50 200 400 600 800 1200 1800 2200): 57.7 % ± 2.3, margin +100 vs cpp-p8**, deaths
  6.9 vs kills 10.7. The 62.8 % was the best of ~12 variants on one seed set, so about 5 points of it was luck; still
  ~15 over the 43 % null. 27 of 40 maps won at least half. Worst: 01big-world 2 / 16, 00packs 5 / 16 (−473),
  00expanse, 00lanes, 00rushbait-v2 and 01fracture 4 / 16.
- **Contact measures**, one unjittered run vs cpp-p8 (80 games, `engage.py`, `flee.py`, `fightctx.py`; p8 in brackets):

| Measure | Target | p9 | p8 side |
| --- | --- | --- | --- |
| melee hit share in contact (Heart of Ruin / Vendetta / Varg / Marcella) | ≥ 35 % | 47 / 42 / 35 / 32 % | 29 / 29 / 22 / 25 % |
| melee move-away share | ≤ 25 % | 23 / 25 / 28 / 27 % | 39 / 36 / 46 / 43 % |
| Heart of Ruin HP lost a contact round | ≤ 35 | **32** | 68 |
| other melee HP lost a contact round | ≤ 50 | 62–81 | 79–96 |
| mixed share, melee HP > 70 % | down | 28 % (420 / 1,523) | 37 % (571 / 1,547) |
| focus (fights before r300 / after) | up | 0.78 / 0.81 | 0.75 / 0.73 |
| kills in fights before r300 / after | | 88 / 623 | 57 / 429 |

  The Heart of Ruin target is met; Marcella's hit share and the other melee bodies' HP lost a round are not. Casts a
  fight: 0.6 vs 0.5 early, so the ladder's 1.9 is still far off.

### 9.4 The user's question: do weak bodies die banking late and hand the bags over?

A TRACE copy vs cpp-p8, 80 games, every death with its behaviour and bag [measured]:
- **Outside 01boss-battle:** 15 of 601 deaths were while banking, losing 262 gems. The bags handed over die in **Heal**:
  2,134 gems in 520 deaths. That's a break walking home with a bag; 15 deaths carried 40+ gems, all after r500 except
  two.
- **01boss-battle is the exception.** Our Vesper and Varg died at the altar holding 535–3,683 gems. A tribute channels
  ceil(gems / 10) turns and damage doesn't stop it [rules], so a 2,500-gem bag channels 250 turns and is taken. The
  score stays 0–0.
- **A candidate, not built:** cancel a tribute (`cancel_submit_gems` [sdk]) when the turns left × the enemy damage in
  reach exceed my HP. Then the stance decides. It's small locally; LADDER_P8 §4.10 counted 0.1–0.3 failed banks a game.

### 9.5 N3 (dash-hop distance): two forms built, both lost, parked

The cheap form: no portal fields. A dash body's fields (F_me, F_home, AW, the goal fields, the window) let "thin" holes
through: a hole with two free neighbours 2 apart [rules]. Nav crosses one with the dash (`hop`), or stands until the
dash is back. The prices then read hop distances for free. Patch: `docs/redo/patches/P9_N3_hop_fields.diff`.
- Every thin hole: **44.8 % ± 2.1, margin −35, deaths 11.6 vs cpp-p9**. The 11 hop maps went 41 / 176, margin −227;
  the rest 246 / 464, +38.
  - The trace (01starvation): most hops were corner cuts saving 2 steps (v 24 → 22). The next hole then waited out the
    8-round cooldown, and a goal flip across the hole cost 7 rounds of waiting.
- Holes saving ≥ `HOP_MIN` 10 steps on the walk from our spawn (or reaching what no walk does): **43.9 % ± 1.2, margin
  −43**. Hop maps 57 / 176, margin −132.
  - On 01islands, 105 hop failures (no free landing tile below my field value: camps on the far side) and 220 waits.
- **Why** [guess]:
  - a unit-weight field can't price the cooldown or a blocked landing;
  - groups only a hop reaches pull the dash bodies away from the crew, which has no dash.
  The doc's portal design (§6 N3: per-portal fields, the cooldown in the price, the crew on the walk side) is the
  form to build next time. Measure `hops.py` with a fresh `MAPS_DUMP` (`tools/mapdump.inc`).

## Appendix A: every loss

Contested gems are `farm.py` caps, over-counted on some maps (§1.3; use `gain.py` for totals). Hop value is the share
of the map's value a dash hop brings 10+ rounds closer (`hopmap.py`). Hole hops are per game, us / them (`hops.py`).
The family is in brackets: T1, T3, PC, or – (other).

| Match | Map (size, S) | Opponent (family) | Margin | Score | Gap opens | Deaths us / them | Contested gems us / them | Hop value | Hole hops us / them | Decided by |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1c0f6a2b | 01gold-rush (31x31, 3) | Tavi,Vesp,Stel (–) | mid | 662-1172 | r1481 | 13 / 6 | 800 / 800 | 89 % | 7 / 8 | fights |
| 819364b4 | 01gold-rush (31x31, 3) | Hear,Ryth,Stel (–) | mid | 358-1012 | r854 | 17 / 2 | 0 / 1200 | 89 % | 3 / 11 | fights |
| 4e45353f | 01islands (60x60, 5) | Marc,Vend,Ryth,Vesp,Hear (PC) | mid | 388-1028 | r403 | 6 / 0 | 58 / 638 | 65 % | 8 / 9 | fights |
| 021a3e5e | 00collision (41x41, 3) | Marc,Vend,Ryth (PC) | crushed | 273-1006 | r417 | 7 / 2 | 54 / 324 | 0 % | 0 / 0 | fights |
| 5456c9dd | 00eight (41x30, 5) | Vesp,Vend,Hear,Cass,Ryth (–) | crushed | 117-1028 | r280 | 24 / 0 | 48 / 56 | 0 % | 4 / 15 | fights |
| bf1f3058 | 00eight (41x30, 5) | Vesp,Vend,Marc,Ryth,Pris (–) | crushed | 352-1068 | r707 | 23 / 9 | 72 / 80 | 0 % | 0 / 0 | fights |
| c5822102 | 00gem-fields (50x40, 5) | Vesp,Hear,Vend,Tavi,Marc (T3) | crushed | 74-1016 | r97 | 21 / 3 | 71 / 788 | 79 % | 3 / 34 | fights |
| 0108efa3 | 00gemfight (30x30, 4) | Marc,Hear,Vesp,Ryth (–) | crushed | 225-1025 | r159 | 9 / 3 | 156 / 1439 | 61 % | 3 / 27 | fights |
| 64ff2d20 | 00gemfight (30x30, 4) | Hear,Vesp,Marc,Vend (PC) | crushed | 181-1018 | r264 | 11 / 0 | 156 / 1248 | 61 % | 6 / 24 | fights |
| c3a85ef1 | 00gemfight (30x30, 4) | Pris,Vesp,Marc,Ryth (–) | crushed | 153-1055 | r303 | 13 / 4 | 7 / 1574 | 61 % | 5 / 14 | fights |
| 191abbc7 | 00interlock (40x40, 4) | Pris,Vesp,Marc,Hear (T1) | crushed | 139-1007 | r435 | 14 / 2 | 118 / 602 | 0 % | 0 / 5 | fights |
| 50516313 | 00packs (31x31, 3) | Vesp,Vend,Marc (–) | crushed | 142-1020 | r278 | 16 / 1 | 114 / 876 | 0 % | 0 / 0 | fights |
| bd7d1f68 | 00packs (31x31, 3) | Vesp,Hear,Vend (T3) | crushed | 176-1010 | r108 | 10 / 1 | 116 / 822 | 0 % | 0 / 0 | fights |
| 8f801980 | 00pilgrimage (50x65, 5) | Vesp,Hear,Vend,Tavi,Marc (T3) | crushed | 337-1004 | r830 | 20 / 5 | 0 / 1408 | 41 % | 19 / 14 | fights |
| 856b0247 | 00swirl (45x30, 4) | Pris,Vesp,Marc,Hear (T1) | crushed | 30-1027 | r234 | 26 / 3 | 30 / 1027 | 46 % | 0 / 4 | fights |
| 5a698db9 | 01concentrated-wealth (61x61, 5) | Vesp,Vend,Hear,Cass,Ryth (–) | crushed | 68-1052 | r141 | 12 / 0 | 0 / 1536 | 71 % | 3 / 15 | fights |
| f53844bf | 01concentrated-wealth (61x61, 5) | Vesp,Ryth,Vend,Tavi,Marc (–) | crushed | 90-1016 | r269 | 9 / 1 | 8 / 1540 | 71 % | 0 / 0 | fights |
| f5e0d518 | 01concentrated-wealth (61x61, 5) | Vesp,Vend,Hear,Cass,Ryth (–) | crushed | 74-1030 | r280 | 15 / 4 | 0 / 1468 | 71 % | 3 / 7 | fights |
| 9a168d07 | 01corridors (51x40, 5) | Marc,Vend,Ryth,Vesp,Hear (PC) | crushed | 186-1022 | r387 | 8 / 1 | 560 / 2012 | 0 % | 0 / 0 | fights |
| daedff10 | 01corridors (51x40, 5) | Vesp,Marc,Ryth,Tavi,Ren (–) | crushed | 93-1072 | r286 | 7 / 1 | 520 / 2024 | 0 % | 6 / 14 | fights |
| 069e5f77 | 01hooks (31x31, 4) | Ryth,Vend,Pris,Ren (–) | crushed | 176-1001 | r1006 | 46 / 10 | 286 / 946 | 0 % | 0 / 0 | fights |
| 8d8efff9 | 01starfish (50x50, 5) | Marc,Cass,Tavi,Will,Stel (–) | crushed | 80-1029 | r299 | 26 / 7 | 20 / 1392 | 0 % | 0 / 0 | fights |
| cbb98ab8 | 01starfish (50x50, 5) | Vesp,Vend,Hear,Cass,Ryth (–) | crushed | 44-1027 | r536 | 35 / 18 | 40 / 1604 | 0 % | 5 / 7 | fights |
| fd0d1aa2 | 01starfish (50x50, 5) | Marc,Vend,Ryth,Vesp,Hear (PC) | crushed | 194-1048 | r315 | 24 / 13 | 20 / 1786 | 0 % | 0 / 0 | fights |
| 0dfe1f92 | 01starvation (80x80, 5) | Vesp,Hear,Vend,Tavi,Marc (T3) | crushed | 222-1010 | r687 | 16 / 3 | 320 / 2004 | 100 % | 64 / 52 | fights |
| 1237de7b | 01starvation (80x80, 5) | Vesp,Ryth,Vend,Tavi,Marc (–) | crushed | 84-1008 | r533 | 18 / 1 | 160 / 1908 | 100 % | 0 / 0 | fights |
| 9696ac01 | 01the-farm (50x40, 3) | Pris,Vesp,Hear (T1) | crushed | 128-1127 | r162 | 8 / 0 | 35 / 299 | 0 % | 0 / 0 | fights |
| 9abf93e1 | 01yellow-brick-road (40x30, 5) | Vesp,Ryth,Vend,Tavi,Marc (–) | crushed | 168-1041 | r674 | 29 / 6 | 0 / 570 | 0 % | 0 / 0 | fights |
| 9263e551 | 00ambush (100x100, 5) | Pris,Vesp,Marc,Ryth,Hear (–) | close | 695-1021 | r1048 | 0 / 4 | 0 / 98 | 29 % | 3 / 6 | farm choice |
| de288874 | 00ambush (100x100, 5) | Pris,Vesp,Marc,Ryth,Hear (–) | close | 746-1035 | r1095 | 0 / 0 | 0 / 98 | 29 % | 0 / 0 | farm choice |
| 3facd656 | 00expanse (80x80, 5) | Ryth,Vesp,Vend,Marc,Hear (–) | close | 722-1035 | r880 | 0 / 0 | 0 / 132 | 2 % | 0 / 0 | farm choice |
| a8fe9294 | 00lost-world (35x31, 5) | Vesp,Vend,Cass,Marc,Ryth (–) | close | 878-1113 | r1019 | 13 / 14 | 761 / 5525 | 17 % | 9 / 25 | farm choice |
| aeb60c2e | 00pilgrimage (50x65, 5) | Tavi,Vesp,Ryth,Will,Vend (–) | close | 536-727 | r1768 | 6 / 9 | 352 / 704 | 41 % | 16 / 21 | farm choice |
| 21975852 | 00rows (50x50, 4) | Vesp,Vend,Marc,Varg (–) | close | 776-1008 | r1095 | 1 / 0 | 0 / 0 | 0 % | 0 / 0 | farm choice |
| 3d9249ea | 00rows (50x50, 4) | Varg,Hear,Vend,Marc (–) | close | 799-1019 | r898 | 0 / 1 | 0 / 0 | 0 % | 0 / 0 | farm choice |
| 5fb343d0 | 00rows (50x50, 4) | Vesp,Vend,Hear,Varg (–) | close | 711-1000 | r541 | 0 / 1 | 0 / 0 | 0 % | 0 / 0 | farm choice |
| 60353377 | 00rows (50x50, 4) | Cass,Varg,Vend,Will (–) | close | 799-1000 | r631 | 0 / 0 | 0 / 0 | 0 % | 0 / 0 | farm choice |
| 54af302e | 00rushbait-v2 (30x80, 4) | Tavi,Vesp,Ryth,Will (–) | close | 735-1006 | r600 | 2 / 3 | 690 / 1066 | 50 % | 0 / 0 | farm choice |
| 4379938e | 01big-world (100x100, 5) | Pris,Vesp,Marc,Ryth,Hear (–) | close | 715-1002 | r350 | 1 / 0 | 60 / 378 | 2 % | 9 / 26 | farm choice |
| dedf036c | 01big-world (100x100, 5) | Vesp,Ryth,Vend,Tavi,Marc (–) | close | 685-1011 | r329 | 3 / 0 | 45 / 75 | 2 % | 11 / 13 | farm choice |
| ff608f66 | 01big-world (100x100, 5) | Pris,Vesp,Marc,Ryth,Hear (–) | close | 674-1002 | r350 | 1 / 0 | 60 / 357 | 2 % | 7 / 28 | farm choice |
| 7b16f3c7 | 01broken-curve (40x40, 3) | Vesp,Hear,Vend (–) | close | 674-1010 | r448 | 0 / 4 | 44 / 304 | 0 % | 0 / 0 | farm choice |
| f4563f50 | 01fracture (61x71, 5) | Vesp,Marc,Ryth,Tavi,Ren (–) | close | 810-1052 | r1106 | 1 / 4 | 104 / 284 | 85 % | 14 / 70 | farm choice |
| 8bb6dc14 | 01islands (60x60, 5) | Vesp,Vend,Marc,Ryth,Pris (–) | close | 714-1004 | r228 | 0 / 0 | 174 / 464 | 65 % | 9 / 17 | farm choice |
| 3bd7c3be | 01yellow-brick-road (40x30, 5) | Vesp,Vend,Cass,Marc,Ryth (–) | close | 808-1003 | r634 | 3 / 5 | 75 / 230 | 0 % | 0 / 0 | farm choice |
| 5e28e23f | 00ambush (100x100, 5) | Hear,Ryth,Marc,Vend,Vesp (–) | mid | 537-1030 | r585 | 2 / 6 | 0 / 70 | 29 % | 0 / 12 | farm choice |
| 06288b29 | 00expanse (80x80, 5) | Vesp,Vend,Ryth,Tavi,Marc (PC) | mid | 487-1042 | r609 | 0 / 1 | 0 / 440 | 2 % | 0 / 0 | farm choice |
| 0ca8e869 | 00pilgrimage (50x65, 5) | Vesp,Vend,Marc,Ryth,Pris (–) | mid | 536-1022 | r845 | 10 / 5 | 176 / 1353 | 41 % | 14 / 25 | farm choice |
| a9335f53 | 00pilgrimage (50x65, 5) | Vesp,Vend,Hear,Cass,Ryth (–) | mid | 360-594 | r1628 | 21 / 24 | 0 / 528 | 41 % | 14 / 59 | farm choice |
| f06dd704 | 00split (45x35, 5) | Ryth,Stel,Tavi,Will,Marc (–) | mid | 586-1003 | r374 | 1 / 0 | 107 / 25 | 21 % | 0 / 0 | farm choice |
| 25bc8a56 | 01big-world (100x100, 5) | Hear,Ryth,Marc,Vend,Vesp (–) | mid | 611-1002 | r531 | 1 / 0 | 60 / 97 | 2 % | 6 / 13 | farm choice |
| da6843a8 | 01broken-curve (40x40, 3) | Marc,Vend,Tavi (PC) | mid | 520-1016 | r345 | 1 / 1 | 32 / 252 | 0 % | 0 / 0 | farm choice |
| 518f8e54 | 01concentrated-wealth (61x61, 5) | Vesp,Vend,Marc,Varg,Will (–) | mid | 358-1016 | r404 | 7 / 10 | 40 / 1492 | 71 % | 0 / 0 | farm choice |
| efe0b92d | 01islands (60x60, 5) | Vesp,Vend,Ryth,Tavi,Marc (PC) | mid | 594-1030 | r421 | 4 / 5 | 174 / 580 | 65 % | 0 / 0 | farm choice |
| f17df9f4 | 01islands (60x60, 5) | Hear,Ryth,Cass,Will,Tavi (–) | mid | 480-1030 | r207 | 6 / 8 | 120 / 580 | 65 % | 6 / 5 | farm choice |
| 1d6b1698 | 01yellow-brick-road (40x30, 5) | Pris,Vesp,Marc,Will,Hear (T1) | mid | 404-1008 | r287 | 6 / 3 | 67 / 382 | 0 % | 0 / 0 | farm choice |
| e6eb721c | 00packs (31x31, 3) | Tavi,Vesp,Marc (–) | crushed | 276-1006 | r206 | 5 / 3 | 176 / 910 | 0 % | 0 / 0 | farm choice |
| db5f914b | 00reverse-spiral (30x30, 4) | Vesp,Vend,Hear,Cass (–) | crushed | 204-1045 | r471 | 13 / 8 | 361 / 988 | 98 % | 10 / 26 | farm choice |
| d53b0178 | 01concentrated-wealth (61x61, 5) | Tavi,Vesp,Ryth,Will,Vend (–) | crushed | 315-1021 | r493 | 6 / 7 | 182 / 1086 | 71 % | 0 / 0 | farm choice |
| 6993a130 | 01hooks (31x31, 4) | Tavi,Vesp,Ryth,Will (–) | crushed | 132-1001 | r596 | 15 / 11 | 110 / 1056 | 0 % | 0 / 0 | farm choice |
| d08c1f1f | 01the-farm (50x40, 3) | Marc,Vend,Tavi (–) | crushed | 345-1007 | r316 | 5 / 1 | 16 / 432 | 0 % | 0 / 0 | farm choice |
| dd99fc94 | 00quadrants (45x45, 5) | Ryth,Stel,Tavi,Will,Marc (–) | close | 976-1008 | r734 | 3 / 4 | 730 / 587 | 0 % | 0 / 0 | end race |
| e7b1e911 | 01broken-curve (40x40, 3) | Vesp,Vend,Marc (–) | close | 986-1020 | r1103 | 3 / 2 | 284 / 210 | 0 % | 0 / 0 | end race |
| 426c7253 | 01yellow-brick-road (40x30, 5) | Marc,Vend,Ryth,Vesp,Hear (PC) | close | 991-1036 | r1222 | 6 / 11 | 167 / 442 | 0 % | 0 / 0 | end race |
| 33a5e2ff | 00stampede (60x50, 5) | Vesp,Hear,Vend,Tavi,Marc (T3) | crushed | 0-1120 | r748 | 34 / 2 | 0 / 2560 | 0 % | 9 / 44 | gated |
| 68a4247b | 00stampede (60x50, 5) | Ryth,Stel,Will,Marc,Pris (–) | crushed | 150-810 | r786 | 18 / 12 | 0 / 1920 | 0 % | 0 / 0 | gated |
| 0bdb1daa | 01boss-battle (50x41, 5) | Pris,Vesp,Marc,Will,Hear (T1) | crushed | 0-1396 | r306 | 5 / 0 | 800 / 400 | 0 % | 0 / 0 | gated |

## Appendix B: the scripts

New in `tools/replay/farm/` (run on flipped games; README there):
- `oppsig.py`: the opponent's signature and the gap-open round, per loss;
- `gain.py MAPS_DUMP decu/*`: gems gained from bag increments, by side;
- `engage.py`: what each champion does with an enemy within 3;
- `flee.py`: flee, fight or mixed when hit, and the outcome;
- `fightctx.py`: fights with the HP ratio, focus and casts at the start;
- `hops.py MAPS_DUMP decu/*`: dash hops over holes per team;
- `hopmap.py MAPS_DUMP`: per map, the value a hop brings closer.

`MAPS_DUMP` = `{map: {"a": dump, "b": dump}}` from a scratch `bots/_mapdump` (`tools/mapdump.inc`).
