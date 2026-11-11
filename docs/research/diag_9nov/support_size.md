# support_size: where our supports' size goes, and the lever left (9 Nov, agent)

**Question.** Our fights go bad because our supports are small: we meet a >= 1.67x enemy within 6 about 20 times a
game, the top about 7-8 (selection.md). Already tested on the band:
- income re-assignment (a transfer);
- Fish item lines (neutral);
- Vesper Bruiser (lost);
- eco 2 support Health lines (+0.02);
- the Tavi and Ryth drafts (neutral).

What lever is left for support size and survivability?

**Short answer.**
1. **There are no levels or XP in CAMBC** [rules + sdk]. A body's size is its base stats plus shards and emblems.
   So the size gap is income x buy choice.
2. **The buy-choice part is almost all Heart of Ruin.** Our HoR holds 0.6 Health shards at r600 (the top's HoR holds
   8.7), because its line buys 15 Focus shards first and it spends only 222 gold by r600.
   - All-Health on its own gold takes it from 1,055 to ~1,740-1,880 HP at r600 (top's HoR: 1,869).
   - Its share of contacts with a >= 1.67x enemy falls from 39 % to 12-13 % (top: 9 %).
3. **Vendetta and the twins are short of income, not of good buys.** Items alone can't close their gap.
4. **The twins are half of our >= 1.67x contacts:** 10.0 a game of 20.2, against the top's 3.7.
5. **No top support is simply bigger.** The top's supports are big because they earn more.
6. **Built:** `bots/_size` = tz-126 + a two-line change, byte-identical wasm at the defaults. Under eco 2, a Health
   target >= 1 makes every buy Health, Prospector included.

## Data and method

- **Band replays (decoded):**
  - `tz126_big`: 150 games, tz-126 v the six band teams.
  - `top_v_band`: 119 games, the top four v the same six.
  - `top3_8nov`: 90 games, the top three v >= 2,450.
- **Summaries:** `~/tzunami_data/meta_8nov/summaries`, 8 Nov, with emblem completion events.
- **Scripts** are in `~/tzunami_data/analysis_9nov/size/` (run with `python3 -I`):
  - `size.py LABEL` -> `size_LABEL.pkl`: per body at r150 / 300 / 450 / 600 / 900, it records max HP, Strength and
    Focus, gold earned and spent, shard equivalents (stat gain / growth) and max HP over the biggest enemy's.
  - `sizesum.py LABEL us|opp`: the table below.
  - `emb.py TEAM...`: emblem timing from the summaries.
  - `cf.py`, `cf2.py`: counterfactual item plans on each body's own gold spent. `cf2.py` re-weights the contacts of
    `sel/contact_*.pkl` (selection.md's contact set) and fits a death model by size ratio.
- "Big contact" means an enemy within 6 with max HP >= 1.67x mine, at the contact round. The definition is
  selection.md's: 20.2 v 8.1 a game here, 19.8 v 7.0 there (the top's count differs a little because of weighting).

## (a) Size: base, growth, levels

**No levels or XP** [rules + sdk]:
- GameRules.md and `sdk/cpp/cambc.h` contain no level, experience or XP mechanic.
- Stats come only from:
  - base stats;
  - shards (30 gold, +growth);
  - emblem bonuses (Power: 6 shards' stats for 5; Bruiser: 5 + 1 of each other stat);
  - two champion passives: Ryth +1 % of bonus Health as Strength, and Prism +1 Focus per carried gem.

**Base stats on 5.0** [measured: round 0 of the decoded replays; GameRules.md is an older export].
Health growth per shard [measured, hp_per_gold.md].

| Champion | HP | Str | Focus | HP / Health shard |
| --- | --- | --- | --- | --- |
| Marcella, Ryth | 1,200 | 40 / 45 | 60 / 100 | 100 |
| HoR, Varg, Vesper | 1,000 | 30 / 50 / 35 | 80 / 100 / 100 | 100 |
| Vendetta, Ren | 900 | 65 / 35 | 100 | 100 |
| Issac | 900 | 45 | 100 | 80 |
| Tavi | 900 | 45 | 110 | 75 |
| Prism, Willow | 700 | 35 / 55 | 90 / 140 | 65 / 50 |
| Stellar | 650 | 30 | 85 | 75 |
| Cassi | 600 | 30 | 100 | 65 |

**Max HP, Health-shard equivalents, gold, by champion** [measured; band games; "HP/g" = HP gained per gold spent]:

| Body | Max HP r300 | Max HP r600 | H shards r600 | Gold earned r600 | HP/g r600 | Big-contact share |
| --- | --- | --- | --- | --- | --- | --- |
| **our HoR** | 1,001 | **1,055** | **0.6** (F 6.9) | 244 | **0.25** | **39 %** |
| top's HoR | 1,292 | 1,869 | 8.7 (F 11.3) | 604 | 1.53 | 9 % |
| our Marcella | 1,230 | 1,497 | 3.0 (F 15.5) | 584 | 0.55 | 22 % |
| top's Marcella | 1,488 | 2,224 | 10.2 (F 21.5) | 998 | 1.10 | 6 % |
| our Vendetta | 1,002 | 1,350 | 4.5 (S 8.0) | 392 | 1.22 | 32 % |
| top's Vendetta | 1,251 | 1,956 | 10.6 (S 23.3) | 1,012 | 1.09 | 9 % |
| our Issac | 994 | 1,158 | 3.2 | 110 | 2.63 | 38 % |
| top's Issac | 1,095 | 1,408 | 6.3 | 334 | 1.65 | 12 % |
| our Cassi | 708 | 902 | 4.6 | 162 | 2.16 | 58 % |
| top's Cassi | 656 | 741 | 2.2 | 252 | 0.62 | 57 % |
| our Vesper | 1,511 | 2,608 | 16.1 | 1,891 | 0.88 | 18 % |
| top's Vesper | 1,331 | 2,730 | 17.3 | 1,830 | 1.03 | 8 % |

**The band is also bigger against us** [measured]: 1,902 v 1,773 mean max HP at r600 (they earn 729 v 581 gold a body).
That is denial / income, not this study.

**Splitting the r600 gap** into income ((top spend − ours) x top HP/g) and buy choice (our spend x (top HP/g − ours))
[measured]:

| Body | Gap | Income | Buys | Buys' share |
| --- | --- | --- | --- | --- |
| HoR | 814 | 531 | 284 | 35 % |
| Marcella | 727 | 424 | 299 | 41 % |
| Vendetta | 606 | 647 | −48 | ~0 |
| Issac | 250 | 345 | −96 | ~0 |
| Cassi | ours is bigger | | | |

On HoR, though, the buy lever is larger than its 35 % share. HoR's top possible HP/g is 3.33 (all Health), not the
top's 1.53. All-Health on our HoR's own 222 gold reaches the top's HoR size.

**Why our HoR is small** [code + measured]:
- `item_table 3` gives HoR the `b_ruin` line: Prospector F, Treasure F, Jungle F, then Durability H 4th.
- Our HoR spends 84 / 222 / 450 gold by r300 / 600 / 900 (the median is lower: 60 / 180 / 345). It is still in Focus
  shards at r600.
- Marcella's `b_marcella` line has the same shape. Under eco 2, both get Prospector in the main stat, then families by
  Health share (HoR 0.45).

## (b) Effective HP per gold, and what the top buys

**Per 150 gold (one emblem)** [rules + sdk; EHP = max HP / (1 − damage reduction)]:

| Buy | What it gives | HoR / Ma / Vd (100 HP a shard) | Issac (80) | Cassi (65) |
| --- | --- | --- | --- | --- |
| 5 Health shards (Prospector, Jungle, Treasure ... H) | 5 x growth + the family passive | 500 (3.33 / gold) | 400 | 325 |
| **Power H** | 6 x growth | **600 (4.0 / gold)** | 480 | 390 |
| Bruiser H | 5 x growth + 1 Str + 1 Focus shard | 500 + off-stats | 400 | 325 |
| **Durability H** | 5 x growth, and 10 % less incoming damage from every source [sdk doc] | 500 + 0.111 x max HP: **~670-720 at 1,050-1,500 HP (4.5-4.8 / gold)** | ~570 | ~460 |
| Durability F / S | the passive only: the stat is free | +117-167 EHP, main stat kept | | |
| Focus shard on HoR | +9 Focus: shield +13.5 (1.5 x Focus), dash +15.75 damage | ~14 EHP a shard (v 100) | | |
| Focus shard on Varg | shield +25 (2.5 x Focus) | ~25 EHP a shard | | |

Notes:
- **Durability H is the most EHP per gold** for every support once max HP > 900. That's always true for HoR, Marcella
  and Vendetta.
- **Power H is the most raw HP.**
- **Passives depend on the family, not the stat** [sdk: every family has S / H / F variants with one passive]. So
  Prospector H keeps the +25 % cluster bonus and still gives Health.
- **There is no heal item** [rules: the only consumables are the altar lock and teleport crystal]. Healing comes from
  spawn (full) and Willow's 3 x Focus ally heal. Our bot has no heal-cast code.
- **Shields:** HoR's base shield is 120 (1.5 x 80) and Varg's 250 (2.5 x 100), each once per 8 turns.

**What the top's supports buy** [measured; summaries, emblems completed by r600 and the share with Durability (any
stat) by r600]:

| Team | HoR | Vendetta | Marcella | Issac / Cassi |
| --- | --- | --- | --- | --- |
| Mite (60) | 3.9 emblems, 1.6 Health, **Durability 62 %** (median r447, 2nd) | 4.6, 1.3, **71 %** | 7.7, 3.1, **80 %** | 1.5 / 1.0 emblems, Durability 18 / 17 % |
| Fish (40) | 2.8, 1.2, 0 % (Capture H 74 %, Hunter H 40 %) | 6.7, 2.8, **77 %** | 8.7, 2.8, **68 %** | 0.6 / 0.7 |
| stellar (60) | 1.6, 0.6, 17 % | (15 games) 6.7, 2.2, 33 % | (15) 3.9, 1.4, 60 % (Durability **F**) | 1.6 / 0.7 |
| band (Claudus, QS2isLaw, policy wonk) | — / 1.7, 1.5 / 2.6, 0.9 | 73 / 58 / 20 % | **75 / 92 / 75 %** | |

- **In replays the top's supports hold 31-42 % Health shards at r600** (HoR 8.7 H to 11.3 F) and get Durability around
  r330-460. Ours hold HoR 0.6 H, Marcella 3.0 H, Vendetta 4.5 H, with no Durability before ~r650.
- **The top's twins are bare:** 0.6-1.6 emblems by r600, Cassi 741 HP at r600. The top doesn't size its twins either.

## (c) Draft

**The top's supports now (META_8NOV, 8 Nov 15:30; not re-pulled, it is under a day old):**
- C&I ~100 % for all three teams.
- HoR 54-91 %.
- Vendetta 25-81 %.
- Prism (stellar 76 %), Willow (stellar 50 %, Fish 60 %), Tavi (Mite 72 %).
- Marcella 26-65 %.

**None of these is a tank pick.** Prism, Willow and Tavi have 700-900 base HP. The top's big supports (HoR 1,869,
Vendetta 1,956, Marcella 2,224 at r600) are big because they earn 600-1,000 gold by r600 [measured].

**Simply bigger by the rules [measured base stats]:**
- **Ryth:** 1,200 HP, Strength from Health, area stun, reset. The top's Ryth reaches 2,788 HP at r600 on 532 gold
  (HP/g 3.0, all Health).
- **Varg:** 1,000 HP, and a 250 self-shield every 8 turns.

**Both are measured trades on the band:**
- **Ryth for C&I** (tz-67, tz-69 on n17 and fresh):
  - deaths −1.17 / −0.94 a game;
  - but gold at r300 −55 / −64, and tributed by r750 −30;
  - share 0.00 on both sets.
- **Varg** has only local screens (five_swap 1).
- A Ryth in HoR's slot (five_swap 2) on HoR's income would reach ~1,940 HP at r600. That is the same size the HoR item
  change gives, without losing HoR's dash stun. So the draft doesn't beat the item change [guess].

**The twins are the part items cannot reach** [measured; per game: big contacts / all contacts / deaths within 15 after a
contact]:

| | Cassi | Issac | HoR | Vendetta | Vesper | Marcella |
| --- | --- | --- | --- | --- | --- | --- |
| ours | 5.8 / 10.1 / 0.83 | 4.2 / 11.3 / 0.85 | 3.4 / 8.6 / 0.46 | 2.8 / 8.8 / 0.51 | 2.2 / 12.5 / 0.45 | 1.8 / 8.0 / 0.30 |
| top (per game; twins in 85/119) | 3.0 / 5.2 / 0.37 | 0.7 / 5.8 / 0.30 | 0.8 / 8.7 / 0.15 | 0.6 / 7.1 / 0.12 | 0.4 / 5.4 / 0.04 | 0.4 / 6.3 / 0.15 |

- **Our twins have about twice the top's contacts per twin-game** (Cassi 10.1 v 7.3; Issac 11.3 v 8.1).
- **Our Issac earns a third of the top's** (110 v 334 gold by r600). He already buys all Health. That gap is income.
- **Items barely touch the twins:** spent >= 150 gold by r600 in 35 % (Cassi) and 25 % (Issac) of games.

## Counterfactuals: item plans on our own gold [measured spends; the size effect on deaths is correlational: guess]

Death model, P(die within 15 rounds of a contact) by my max HP / their biggest within 6, from our 8,883 contacts:

| Ratio | < 0.4 | 0.4-0.5 | 0.5-0.6 | 0.6-0.8 | 0.8-1.0 | 1.0-1.25 | > 1.25 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P(die) | 0.109 | 0.089 | 0.062 | 0.057 | 0.048 | 0.034 | 0.021 |

| Plan (everything else as tz-126) | Big contacts a game | HoR / Ma / Vd / Issac / Cassi share | Modelled deaths a game |
| --- | --- | --- | --- |
| tz-126 now | 20.2 | 39 / 22 / 32 / 38 / 58 % | 0 |
| tz-138 (eco 2 default: HoR .45, Ma / Vd .33) | 18.5 | 29 / 15 / 29 | −0.10 |
| tz-140 queued (eco 2: HoR .6, Ma / Vd .5) | 18.1 | 26 / 13 / 29 | −0.15 |
| HoR: Prospector F, then all Health (eco_hr 1 alone on tz) | 18.7 | 22 / 22 / 32 | −0.08 |
| **HoR all Health, Prospector H, Durability 2nd (`_size` eco_hr 1)** | **17.9** | **13** / 22 / 32 | **−0.15** |
| **+ Marcella / Vendetta Health .5 (`_size`)** | **17.0** | 13 / 13 / 29 | **−0.24** |
| + twins Durability 2nd, all Health (`_size` eco 18) | 16.6 | 12 / 13 / 29 / 36 / 56 | −0.27 |
| (HoR Durability 1st instead of Prospector H first) | 17.9 | 12 | −0.16 |
| top, for reference | 8.1 | 9 / 6 / 9 / 12 / 57 | |

**Reading:**
- **Items close about a third of the big-contact gap** (20.2 -> 16.6 of the 12.1 gap). The rest is the twins (6.4) and
  Vesper (1.8), which come down to income and position.
- **HoR is the single largest item piece:** −2.3 big contacts a game. It is the body with the worst gap (39 v 9 %).
- **The cost to HoR [rules arithmetic + measured spends]:**
  - Focus stays 80 instead of ~142 at r600: dash 140 v 249 damage, shield 120 v 213.
  - Before r300 our HoR has spent 84 gold (2.8 Focus shards), so its camp damage changes by about 5 a round. The old
    sup_lines stop (tz-36, mon300 −0.6k in 60 games) covered HoR and Marcella both, on an older bot.

## Built: `bots/_size` (tz-126 + 2 lines in `shop()`'s eco block)

```cpp
const bool all_h = eco_t >= 0.99f;   // a Health target >= 1: every buy Health, Prospector included
const S st = (all_h || (nall > 0 && float(nh) < eco_t * float(nall))) ? S::health : eco_m;
...
next = cambc::get_item_enum(fam, (fam == F::prospector && !all_h) ? eco_m : st, true);
```

- **Defaults:** with eco 0, the wasm is byte-identical to bots/tz's [measured, cmp].
- **Under eco 2 with eco_hr 1.0,** HoR buys Prospector H, Durability H, Jungle H, Monster H, Capture H, Bruiser H,
  then Power H. Checked in one local game summary (04orchard).
- **Under eco 16 with eco_hc / eco_hi 1.0,** the twins buy Prospector H, Durability H, Bruiser H, Jungle H, then
  Power H.
- **Knobs:** `tools/variant.py` overrides eco, eco_hr, eco_hm, eco_hv, eco_hc and eco_hi (all static constexpr; the
  regex matches; checked by building `_sizeh`).
- **Local screen** [measured; crash screen only, local results don't predict the band]: `_sizeh` (eco 2, eco_hr 1.0)
  v tz on the held-out maps, 84 games.
  - win 52.4 % (42-63), median margin +35;
  - deaths 3.6 v tz's 4.2;
  - gold300 1,506 v 1,479; mon300 26.6k; trib750 553;
  - no faults.
  - `bots/_sizeh` was deleted afterwards; `bots/_size` is kept for the queue.

## Ranked changes

1. **HoR all-Health line** (`_size`, eco 2 + eco_hr 1.0):
   - HoR at r600: 1,055 -> ~1,740-1,880 HP (top's 1,869);
   - big-contact share 39 -> 13 %; −2.3 big contacts a game; modelled deaths −0.15 a game [guess].
   - Compare it with tz-113 (eco 2 at the defaults, n37 +0.02): same base, so the difference is HoR's line.

   `??|tz-126 + HoR all-Health line (eco 2, eco_hr 1: Prospector H, Durability H ... Power H)|_size|eco=2 eco_hr=1.0`
2. **HoR all-Health plus Marcella / Vendetta Health share .5** (Durability 2nd under eco 2):
   - 17.0 big contacts a game, modelled −0.24 [guess];
   - Marcella r600 ~2,300 HP (top's 2,224), Vendetta ~1,660 (income-limited).
   - It overlaps tz-140 (queued: HoR .6), but its HoR line is all-Health.

   `??|tz-126 + support sizes (eco 2: HoR all Health, Marcella / Vendetta .5)|_size|eco=2 eco_hr=1.0 eco_hm=0.5 eco_hv=0.5`
3. **(Low) the twins with Durability before Bruiser, and Power H after** (eco 18):
   - only 7-12 % of twin-games reach the second emblem by r600;
   - −0.4 big contacts a game, modelled −0.03. Queue it only stacked on 1-2 if they win.

   `??|tz-126 + all-Health HoR and twins (eco 18)|_size|eco=18 eco_hr=1.0 eco_hc=1.0 eco_hi=1.0 eco_hm=0.5 eco_hv=0.5`

**Not recommended:**
- Ryth / Varg drafts: a measured death-for-income trade, share 0.00 twice.
- Willow: no heal code.
- Durability F on Marcella: superseded by eco 2's Durability-2nd families.

**What items can't fix:** the twins' size and Vendetta's (income), and the band being bigger against us (their 729 v 581
gold a body). Those are the collection / denial levers (yield.md, early_income.md).
