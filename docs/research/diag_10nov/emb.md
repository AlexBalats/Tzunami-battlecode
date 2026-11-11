# emb: which emblems we buy (`embx`)

Agent `size` (second task), 10 Nov. Copy: `bots/_emb` (base `bots/_stkA5`). Scripts: `~/tzunami_data/analysis_10nov/emb/`:
- `items.mjs` + `run_items.sh`: a decoder that writes every champion's item counts at each shop step. The visualiser
  snapshot carries `items`; the old decodes did not. 419 band replays were re-decoded into `items/LABEL/`.
- `emb.py` (replays) and `lemb.py` (local judge JSONs): emblem families per champion, owned by r600 / by the end,
  median completion round, the commonest lines.
- `recall.py` / `brecall.py` / `lrecall.py`: real recalls (a recall channel that survived a turn start) and how they
  end (home, cancelled, died), on band or local games.
- `dpre.py`: what our bodies did in the 7 rounds before each death.
- `kpi_json.py`: deaths and gems lost per champion.

## The question

Which emblem families do the top and the band complete, in what order and by which round, against ours? Would Home,
Durability or other passives save bodies and bags?

## Short answer

- **What we buy differently [measured, 419 band replays re-decoded with items].** Our lines already hold the
  common passives (Prospector, Capture, Treasure, Jungle, Durability, Bruiser, Monster). We never buy four that the
  top and the band do:
  - **Home** (recall 5 -> 3 turn ends [sdk]): the top's Vesper 52 % by r600 (median r435), the band's Vesper 43 %
    (r250), the band's Marcella 30 % (r471);
  - **Tribute** (33 % shorter tribute channel): the top's Vesper 48 % (r462), the top's Prism 66 %;
  - **Collectors**: the top's Vesper 62 %;
  - Hunter: the top's Vesper 33 %.
  - We are also late on Monster for Vendetta: the top 76 % by r600 (r370), ours 14 % (r680).
- **Built `embx`** in `bots/_emb`. At embx=0 its release wasm is byte-identical to `_stkA5`'s, and at A5's settings
  to `_a5r`'s. **embx=15** gives:
  - Vesper Home after Treasure and Tribute after Home;
  - Home in Health on Marcella, HoR and Vendetta;
  - Durability first on Cassi and Issac.
- **Local v `_a5r` (256 games a seed): 53.1 / 55.9 %.** Deaths are 5.7 v 5.9 and 5.7 v 6.2; supports die less in
  both seeds. Kept recalls reach home in 3.6 rounds v 4.1.
- **Every single bit is neutral alone** (48.0-51.6 %), so the gain is the set and it is small.
- **Recall deaths were never the problem.** Locally 0.2-0.3 a game die inside a recall channel; on the band 0.17
  (tiny / one-altar sets). The band's real cost is 4.1 deaths a game of hurt bodies that never start a recall.
  That is the escape recall's job, and a 3-tick Home recall makes it easier.

## What they buy [measured: items decoded from replays; % of bodies owning the family by r600 / by the end, median completion round]

Ours = A5 (local, `_a5r` side of 256 judge games: our current lines). The old ladder lines (tz-mega v the band) differ only in
Jungle-first on supports. Top = the top teams v the band (`top_v_band`, 119 games). Band = the band v us (`tzmega_big`, 150).

| Champion | Ours (A5) | Top | Band |
|---|---|---|---|
| Vesper | Prospector 97, Capture 93, Treasure 92, Jungle 90, Durability 87, Bruiser 79, Monster 75, Greed 51 | Prospector 92, Monster 89, Treasure 84, Capture 83, Jungle 80, Durability 66, **Collectors 62 (r402)**, Bruiser 59, **Home 52 (r435)**, **Tribute 48 (r462)**, Hunter 33 | Monster 93, Durability 92, Treasure 92, Prospector 92, Jungle 87, Bruiser 67, Capture 49, **Home 43 (r250)**, Skirmish 34, Collectors 34 |
| Vendetta | Prospector 82, Jungle 60, Capture 36, Durability 25, **Monster 14 (r680)** | Jungle 85, **Monster 76 (r370)**, Prospector 72, Durability 66 (r450), Capture 61, Treasure 47, Bruiser 35, Collectors 24, Hunter 20 | Prospector 66, Jungle 63, Treasure 46, Monster 37, Durability 35, Capture 33, Home 9 |
| Marcella | Prospector 88, Durability 74, Bruiser 56, Jungle 40, Monster 25, Capture 17 | Prospector 81, Jungle 65, Durability 57, Capture 57, Monster 51, Bruiser 47, Treasure 44, Hunter 19 | Jungle 82, Prospector 75, Durability 65, Treasure 62, Monster 59, Capture 57, Bruiser 52, **Home 30 (r471)**, Collectors 22 |
| HoR | Prospector 57, Durability 34, Bruiser 13, Jungle 7 | Prospector 72, Jungle 49, Monster 42, Durability 33, Bruiser 33, Capture 27, Treasure 24 | Treasure 55, Prospector 51, Jungle 35, Monster 31, Durability 14 |
| Cassi / Issac | Prospector 43 / 32, Bruiser 17 / 11 | Cassi: Prospector 20, Power 19, Bruiser 18, Durability 12; Issac: Prospector 71, Jungle 19, Durability 14 | (rarely drafted) |
| Prism | (draftx, 30 local games) Prospector 47, Treasure 23 | **Tribute 66 (r438)**, Prospector 66, Jungle 40, Capture 37, Monster 34 | Durability 71, Bruiser 55, Monster 50, Prospector 39, Capture 34, Tribute 18 |

- Every emblem gives the same 5 shards of stats [sdk]; only its passive and its place in the line differ. Choosing a
  family costs nothing in size. Only the delay to the passives behind it costs.
- Passives the top and the band buy and we never do: **Home** (Vesper 43-52 %, the band's Marcella 30 %),
  **Tribute** (the top's Vesper 48 %, Prism 66 %), **Collectors** (the top's Vesper 62 %), Hunter (the top's Vesper
  33 %). Monster on Vendetta: the top 76 % by r600, ours 14 %.

## Recalls and deaths on the band [measured: `brecall.py`, `dpre.py` on `tiny_m2` (120 games) and `a1_m2` (119), mega2 v the band; the only band sets decoded with channel fields]

| Per game | Us | The band |
|---|---|---|
| Real recalls started | 31.1 / 31.6 | 39.1 / 37.1 |
| ... reached home | 26.3 / 26.0 | 27.2 / 26.2 |
| ... cancelled | 4.6 / 5.2 | 11.7 / 10.6 |
| ... died in the channel | 0.17 / 0.16 | 0.11 / 0.10 |
| Deaths | 9.6 / 8.6 | 5.0 / 5.0 |
| Our deaths after 3+ of the last 7 rounds below 50 % HP with no real recall | 4.1 / 4.2 | |
| ... of which the nearest enemy was 4+ tiles away 7 rounds before | 1.9 / 1.7 | |

- Deaths inside a recall channel are rare (0.17 a game). Home cannot save many bodies by finishing a channel sooner.
- The real target is the 4.1 deaths a game of hurt bodies that never start a recall. The escape recall (bankx 2) is
  aimed at them, and a 3-tick recall widens the window it can use.

## What is built: `embx` in `bots/_emb` (base `bots/_stkA5`)

Files touched:
- `bots/_emb/src/value.h`: `embx`, `emx_home_pos` 3, `emx_trib_pos` 4, `emx_home_sup` 2 and `emx_coll_pos` 6, at
  the end of `Params`.
- `bots/_emb/src/bot.cpp`:
  - `EMX()`, `emx_put()` and `emx_lines()` above `shop()`, with one hook after the line is built;
  - a Home step in `sz_next()` (the sizex support line);
  - a Home-aware branch in `recall_unsafe()`.

| Bit | What |
|---|---|
| 1 | Vesper: Home (Strength) at index 3 of her line (after Prospector, Capture, Treasure; locally done at median r247) |
| 2 | Vesper: Tribute (Strength) at index 4 (median r287) |
| 4 | Home (Health) on supports: Marcella / HoR third in the sizex line, after Prospector and Durability; Vendetta at index 2 |
| 8 | Cassi / Issac: Durability (Health) first |
| 16 | A body that owns Home: the recall start guard (an enemy seen within 9 tiles in 8 rounds) shrinks to 3/5 (5 tiles, 5 rounds) |
| 32 | Vendetta: Monster (Strength) third, after Prospector and Jungle |
| 64 | Vesper: Collectors (Strength) at index 6 |

**cmp [measured]:** `_emb` at embx=0 and `_stkA5`: release wasm byte-identical. `_emb` with `robx=59 openx=48
draftx=2304 bankx=2 s2end=1 sizex=11 endx=3 embx=0` and `_a5r`: byte-identical. Rechecked after each code change.
No missing games or bot faults.

## Local results [measured: `judge.py` v `_a5r` (A5 at its settings), 256 games a run; recall KPIs on 64 decoded games a run]

| embx | Seed | Win % (95 % CI) | Held-out | Deaths us v them | Vesper deaths / gems lost (us v them) | Real recalls: rounds to home (us v them), died in channel | Team max HP r600 (us v them) |
|---|---|---|---|---|---|---|---|
| **15** (1+2+4+8) | 0 | **53.1 (47-59)** | 51.2 | 5.7 v 5.9 | 0.49 v 0.50 / 14.4 v 10.5 | 3.6 v 4.1; 0.23 v 0.30 | 5,488 v 5,655 |
| 15 | 1 | **55.9 (50-62)** | 52.4 | **5.7 v 6.2** (Marcella 0.67 v 0.81, HoR 0.74 v 0.94, Vendetta 0.74 v 0.82, twins 1.43 v 1.52) | 0.47 v 0.46 / 13.5 v 10.5 | 3.6 v 4.1; 0.20 v 0.27; real recalls 49.4 v 47.2, home 43.4 v 41.2 | 5,437 v 5,598 |
| 1 Vesper Home | 0 | 49.2 (43-55) | 44.0 | 6.0 v 5.7 | 0.51 v 0.48 / 15.6 v 12.2 | 3.9 v 4.2; 0.25 v 0.17 | |
| 2 Vesper Tribute | 0 | 50.0 (44-56) | 48.8 | 6.1 v 5.9 | 0.49 v 0.50 / 10.3 v 11.4 | 4.2 v 4.1; 0.25 v 0.19 | 5,327 v 5,623 |
| 4 supports' Home | 0 | 48.0 (42-54) | 45.2 | 6.0 v 5.9 | 0.48 v 0.49 / 20.5 v 15.0 | 3.8 v 4.2; 0.30 v 0.22 | 5,872 v 5,644 |
| 8 twins Durability first | 0 | 51.6 (45-58) | 53.6 | 6.1 v 6.4 (twins 1.55 v 1.63) | 0.48 v 0.54 / 16.8 v 24.7 | 4.2 v 4.1; 0.22 v 0.38 | 5,673 v 5,614 |
| 32 Vendetta Monster third | 0 | 51.2 (45-57) | 48.8 | 6.1 v 6.3 | 0.49 v 0.49 / 43.9 v 42.9 | 4.2 v 4.1; 0.23 v 0.28 | 5,637 v 5,655 |
| 64 Vesper Collectors | 0 | 50.8 (45-57) | 48.8 | 6.1 v 5.9 | 0.52 v 0.47 / 11.8 v 13.1 | 4.2 v 4.2; 0.38 v 0.25 | 5,356 v 5,645 |
| 21 (1+4+16: Home + its guard) | 0 | 51.2 (45-57) | 47.6 | 5.8 v 5.8 (Marcella 0.69 v 0.80) | 0.47 v 0.52 / 11.6 v 13.8 | 3.7 v 4.2; 0.27 v 0.28; real recalls 49.8 v 47.8, home 43.3 v 41.9 | 5,574 v 5,697 |

What the numbers say:
- **No emblem choice moves the local judge beyond noise.** One 256-game run swings about +-4 points, and every
  single bit lands at 48-52 %.
- **Home does what the rules say:** a kept recall reaches home in 3.6-3.9 rounds instead of 4.1-4.2. But locally a
  recall almost never ends in death (0.2-0.3 a game, both sides) and cancels are level (5.6-5.9). The time saved is
  about 0.5 round a recall, about 20 body-rounds a game. Deaths do not fall.
- Durability first on the twins cuts their deaths a little (1.55 v 1.63, one run).
- **Together (embx=15) it passes the gate: 53.1 / 55.9 % (mean 54.5 %) with fewer deaths in both seeds (5.7 v 5.9,
  5.7 v 6.2).** In seed 1 every support dies less (Marcella 0.67 v 0.81, HoR 0.74 v 0.94, Vendetta 0.74 v 0.82, twins
  1.43 v 1.52). By map class (seed 0 / 1): one-altar 56 / 45 %, tiny 53 / 54 %, small 57 / 60 %, big multi-altar
  47 / 54 %. Team max HP at r600 is 3 % lower (5,437-5,488 v 5,598-5,655): Home and Tribute push Vesper's Durability
  Health two sets later. Focus is -20 % (Home Health on the supports in place of their Focus sets).
- No single bit carries it, and every one sits inside the noise, so the honest reading is "about +2-5 points from
  the whole set, unproven per bit".

## What the band should show

- Deaths down, mostly on the supports; kept recalls reaching home in 3.6 rather than 4.1 rounds; the band's chases
  ending at our spawn.
- Home's real target on the band is the 4.1 deaths a game of hurt bodies that never start a recall (above). The
  escape recall (bankx 2) can use a 3-tick channel from closer range than a 5-tick one. Locally the opponent rarely
  punishes recalls (0.2-0.3 deaths in a channel a game), so Home's local effect is mostly time. Bit 16 (the guard
  that knows about Home) adds about 2 kept recalls a game, but its local run (embx=21) is level at 51.2 %.
- Not tested: Collectors / Hunter / Skirmish on the carries beyond one run each (64: 50.8 %); Tribute with a
  banking model that knows the channel is shorter. The bot's own timing (plan_home's "recall 5", the threat bank's
  channel estimate) still assumes 5-tick recalls and full-length tributes: conservative, not wrong.

**Band line:**
`emb: Vesper Home+Tribute, support Home, twin Durability 1st (embx 15)|_emb|robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11 endx=3 embx=15|all`
