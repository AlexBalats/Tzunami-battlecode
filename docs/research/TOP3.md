# The top three, champion by champion (4 Nov evening)

User (4 Nov): draft the top three teams' exact comps at 3, 4 and 5 picks; track what every champion does (items, recall
timings, wards, everything at the atomic level); build it into v93, big changes allowed; then SPSA hill-climb. RL on hold.

Ladder top three (4 Nov 19:00): **Intercontinental Fish 2,668, Mite 2,566, Pantheon 2,561**. Source: their 600 newest
ranked games each (3 Nov 20:44 → 4 Nov 18:50, `runs/top3/list_*.json`), 505 replays downloaded, ~450 decoded
(`runs/top3/dec`). Scripts in `tools/replay/top3/`: `atom.py` (one row per body per game), `report.py` (per team, size,
champion), `capsplit.py` (who takes the captures), `budget.py` (body-round budget), `cipair.py` (the twins' gap).
v93's rows for the same measures come from its 215 panel replays (`runs/top/W/decu`, `runs/band/W/decu`); those are
v93 v the top 20 and the 2,000 band, the top three's are v the top ~30, so level-of-opponent confounds every
comparison. All numbers [measured]. Full reports: `runs/top3/rep_<team>_<size>.txt`.

## 1. The drafts (`runs/top3/drafts.py`, `drmap.py`, `tree.py`)

Fish's draft is fixed per map (0 of 86 map-sizes with two drafts); Mite's nearly; Pantheon's varies (likely testing).

| Picks | Fish (#1) | Mite (#2) | Pantheon (#3) |
| --- | --- | --- | --- |
| 5 (354 / 376 / 348 games) | **X > Vendetta > HoR > C&I > Willow**, X = Marcella (181, 83 % won) or Vesper (139, 72 %); Ren for Willow on 3 big sparse maps | Vesper > Vendetta > HoR > Marcella > C&I (360, 61 %) | spread: Vesper > Vendetta > C&I > Ren > HoR (57, 88 %), …C&I + Prism + Marcella lines |
| 4 (123 / 120 / 138) | Marcella > Vendetta > HoR > C&I (91, 73 %); Vesper first on 2 maps | Marcella > Vendetta > HoR > C&I (99, 61 %) | C&I > Prism > Marcella > HoR (39, 62 %), … |
| 3 (123 / 104 / 114) | Vesper > HoR > C&I (64, 61 %); Vesper > Marcella > C&I (43, 70 %); Marcella first on gem-only maps | Vesper > HoR > Vendetta (56) / HoR > Vendetta > Marcella (38) | C&I > Prism > Marcella (36), C&I > Marcella > HoR (35) |

All three draft **Cassi & Issac** on nearly every map; none drafts Varg (ours since p8). Fish's choice of X is
map-derived: **Vesper where the map has ≥ 17 gold clusters** (whole map; 44 of 53 5-pick maps right), else Marcella;
4 picks Vesper where wolves + elk ≥ 26 (2 of 18); 3 picks Marcella first only where there is no gold cluster.
Built as `fish_comp()` (draft.cpp, `bots/lad-t3`), checked on 7 maps locally. The camp-gated Varg rule kept (one map).

## 2. Per champion, Fish 5 picks (r0–300 unless said; v93 in brackets, v the top / band)

| | camp-hit share of body-rounds | dead share | gems taken r0–300 | gold r0–300 | first shop | shop visits | banks (bag median) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Vesper | 21 % (15) | 1 % (8) | 104 (42) | 1,168 (400) | r80 (r155) | 7.8 (6.9) | 6.0 (53) (4.5 (25)) |
| Marcella | 8 % (9) | 3 % (7) | 124 (57) | 707 (291) | r77 (r162) | 10.2 (5.7) | 8.0 (48) (5.6 (22)) |
| Vendetta | 16 % (10) | 4 % (9) | 66 (19) | 413 (101) | r79 (r212) | 8.3 (5.2) | 5.7 (29) (3.9 (16)) |
| Heart of Ruin | 19 % (12) | 5 % (8) | 48 (11) | 189 (48) | r142 (r318) | 5.0 (3.1) | 4.5 (29) (2.5 (8)) |
| Cassi / Issac | 23 / 18 % | 7 % | 19 / 14 | 70 / 58 | r273 / r214 | 2.6 / 2.9 | ~2 (20) |
| Willow | 17 % | 4 % | 8 | 45 | r191 | 1.5 | 1.2 (21) |

- **Who takes** (`capsplit.py`): the same number of capture rounds a game as v93 (22), 89 % alone (ours 96 %), but
  ~35 gems a take to our ~20. Marcella 29 % of the gems, Vendetta 25, Vesper 22, HoR 14, the twins and Willow 11 %
  together: the crew clears, the carries take. Mite and Pantheon the same shape.
- **Items** (emblem order, commonest full line): Vesper Capture S → Treasure S → Jungle S → Monster S → Hunter H →
  Durability H (→ Prospector H), then Bruiser S / H (5.7 + 3.6 emblems); Marcella Prospector F → Capture F → Jungle F →
  Monster F → Bruiser H; Vendetta Capture H → Jungle S → Monster S → Hunter H → Durability H → Collectors S (15 of 42
  bodies exactly); Heart of Ruin Prospector F → Capture H → Jungle F → Monster F → Hunter H; Cassi Power F → Durability
  F; Issac Prospector H → Bruiser H; Willow Prospector H (most buy nothing). v93: Treasure → Jungle → Bruiser/Durability
  everywhere. Their carries' first emblem r116–206; v93's r200–580.
- **Recalls**: every body 650–880 recall starts a game (the spam, TOP_HABITS §1), v93 ~10. Real trips home
  (a jump of ≥ 4 to the spawn): Marcella 9.6 a game at 91 % HP with ~210 gold; Vesper 7.9 at 61 % with ~230; Vendetta
  8.3 at 64 % with ~100; the crew 3.5–5 at 31–59 % HP with 0–40 gold (heals). v93: 6–10 a game, mostly heals (Vendetta
  10 at 52 % with 10 gold).
- **Wards**: 17–34 a game a body (own / middle about half each), first by r11–45: level with v93 (25–27).
- **Altar locks** 0.2–1.3 a body a game, **teleport crystals** 0.4–2.7 (Vesper the most): level or a little above v93.
- **The twins** (`cipair.py`): Cassi–Issac gap median 4 (r0–300) / 6 (r300–1k) for Fish, 6–10 Mite, 9 Pantheon; they
  die 2.3 times a game (Fish), 400 of 460 to champions.
- **Time budget** (`budget.py`, r0–300): their bodies hit camps 16–26 % of rounds, ours 10–15 %; dead 1–7 %, ours
  8–12 %; walking level (36–60 %).

## 3. Built: `bots/lad-t3` (v93 + the copy), BOT_VER t3-b = v145

1. `fish_comp()`: the draft above (T3_GOLDC5 17, T3_MON4 26).
2. The per-champion item lines above (champs.cpp, `build[8]`).
3. The recall spam (main.cpp `spam_start` / `spam_cancel`; a real recall is left alone).
4. `TRIP_GOLD` 300 → 150 (their carries go home with 100–230 gold, first shop ~r80).
5. The twin rule: Cassi lifts Issac's farm group / kill target ×3 while he is > 4 tiles away (upd.cpp).

Local smoke v v93 (crash check only; the mirror is anti-predictive, `judging-changes`): 0 crashes on 5 maps; 4 picks
01hooks 1,019 v 22; 5 picks lost 00quadrants 869 v 1,005 and 00ambush 606 v 1,014; 3 picks 00fragment 221 v 930 with
52 deaths (their Vesper killed our twins 16 times). Ladder judge: §4.

## 4. The ladder judge

**t3-b (v145), band stage 1, 60 games v v93ref: 11 v 24 wins, −13 ± 4.3: lost, stopped.** Gems level to r500
(+13), then deaths +10.4 a game (21.1 v 10.8), kills −2.8, gold −1,381. By size: 3 picks 3 v 3, 4 picks 4 v 7, 5
picks 4 v 14. Decoded (`runs/top3/t3b_dec`, `dctx.py`): the new crew dies: twins 4.7 a game (Fish 1.9), Willow 3.5
(1.1), mostly at full HP to one enemy and alone (58 %); our carries died less than v93's (Vesper 1.2 v 2.1). Fish's
crew is a pack (§2, `pairs.py`: HoR + twins + Willow within 4 of each other 51–67 % of r0–300; ours 18–28 %).

Since (local only, not judged): the slot order puts Willow sixth (no comms byte), the twin rule became a pack rule
(followers lift Heart of Ruin's target, take his opening seed, and close on him when nothing is in reach). Local smoke:
the pack still doesn't hold (alone 48–56 %), crew deaths still high. Stopped here (user: slow down, deeper analysis first).
