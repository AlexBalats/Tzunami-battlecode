# Team Kungarna: their policy as rules, read from replays only (7 Nov, evening)

Data: 165 decoded games with Kungarna in them: 130 against our builds (big32, tz38/39/40_big = 4 x 25 on the same
maps and sides, tz32b_band, tz32b_s7, tz28_band) and 35 against 7 other UK band teams (ukband_6nov). No team code
was read. Scripts in `scratchpad/diag/kungarna/` (`kg.py` lists games, `cache.py` pickles them in ~20 s, one script
per question, outputs in `*.txt`). Distances are Chebyshev (no wall map), so "nearest" is approximate. "Engage"
means the body hit one of our champions or closed the gap to the nearest one that round. "v tz" means the 130
games against our builds, "v band" the 35 against other teams.

## Headline

Kungarna is **not a fighting team**. They are a **parallel solo-farming team** that (1) takes gem clusters, ours
included, (2) keeps farming while we are in sight, (3) banks big bags, often at altars on our half and without an
escort, and (4) fights only when the local HP count favours them. Against us they collect **+150 gems by r300**
(gold is level: tz-39 earns more gold than they do) and bank 137 gems by r300 to our ~60. We die 10.1 times a game,
they 3.7 [measured].

| v tz (130 games) | Kungarna | Us |
| --- | --- | --- |
| captures by r300 | 19.7 | 14.1 |
| ... of gem-only groups | **5.9 (106 gems)** | **1.8 (16 gems)** |
| ... of gold-only groups | 5.9 | 6.7 |
| captures on the *other* team's half by r300 | **4.4 (2.3 gem-only)** | 1.5 |
| banked by r300 / r600 | 137 / 320 | 60 / 180 |
| deaths per game | 3.7 | 10.1 |
| camp hits per round with an enemy 5-8 tiles away / 3-4 tiles | **14.6 % / 7.1 %** | **6.4 % / 2.9 %** |
| mean max HP r300 / r600 | 1,380 / 2,283 | 1,065 / 1,376 |
| tributes a game, bag at tribute (median) | 19.1, **50** | 12.4, 25 |

Against the other band teams the gem gap disappears: 212 v 213 capture gems by r300, gem-only captures 2.7 v 3.1,
and Kungarna takes only 1.5 groups on their half [measured]. So the gem gap is **specific to how we play**. We leave
our own gem clusters and contested ground to them.

## (a) Draft

- **The draft depends on the map only** [measured]. On every map it is identical across our 4 builds, both sides and
  other opponents. It is not a counter-pick.
- Core: **Marcella in 165/165 games**, HoR 144, Vendetta 133, **Ryth in every 5-pick game** (120). The flex slot is
  Prism (73), Varg (58), Vesper (14) or Willow (13). **They never draft Cassi & Issac** (we always do).
- **Prism** comes in on maps rich in gem clusters: every all-gem map, and most maps with 22+ gem clusters or gem
  clusters at about 40 % or more of the camps. The rule is not clean (03honeycomb, 04butterfly and 04terraces have
  many gem clusters but no Prism), so read it as a score, not a threshold [measured / partly guess]. **Varg** comes
  in on wolf/gold-heavy maps (02the_pack, 00swirl, 04comb, 04wilds, 01fracture). **Vesper** comes in on gold-cluster
  maps with almost no gems (03one_gem, 01elk_arena, 03membrane, 04sunburst, 00split). **Willow** comes in on sparse
  maps (00elkring, 00ribs, 02famine).
- Who carries: **Ryth** (max HP 1,456 at r150, 1,987 at r300, 3,536 at r600; its Strength scales with bonus Health
  [rules]) and **Prism** (3,305 at r600; it carries gems for Focus: 179 gems collected by r300, the most of any body).
  Marcella takes the most gold (553 by r300).

## (b) Opening

- **Deterministic and scripted from the map** [measured]. In the 4 x 25 paired games every Kungarna body's first
  group and first-hit round are identical across our 4 builds. Positions first differ at a median of **r62**
  (quartiles r38 / r62 / r130). In 61 % of cases one of our bodies is within 8 at that moment, so the split is a
  reaction to us; otherwise it follows a camp-state difference. There is no randomness.
- First camp hit at r9 / r15 / r26 (quartiles). Prism hits first (median r11), Willow last (r86).
- **They split at once.** Distinct first groups per game: 1 group in 33 games, 2 in 74, 3 in 42, 4-5 in 16. The
  biggest first stack is 3 bodies (median over 70 map-sides). One or two bodies go alone to a second or third group.
- The first group is the nearest to spawn for 34 % of bodies and among the nearest three for 62 %. The stack goes to
  the nearest big group, the singles to nearby small groups.
- Body-rounds by squad size in r1-100: solo 44 %, pair 21 %, trio 19 %, 4+ 16 %.

## (c) Goal selection after r40 (conditional logit, 9,219 choices)

A decision is a body starting to hit a new group (not adjacent to its last one). The features are taken at its last
hit on the previous group. Candidates are groups alive or respawning within 30 rounds.

| Feature | Coef (se) | Reading |
| --- | --- | --- |
| distance /10 tiles | **-1.28** (0.02) | a group 10 tiles farther needs 3.6x the appeal |
| rounds it would wait after arrival /10 | -0.88 (0.03) | |
| is respawning (back before or as they arrive) | **+0.84** (0.04) | they route to respawns timed for arrival |
| per elk / wolf / gem cluster / gold cluster | +0.39 / +0.03 / **+0.11 / +0.13** | gem and gold clusters are near equal: ~0.4 gem per gold implied (ours 0.55 at r150) |
| per golem / monolith | -0.36 / -0.87 | avoided |
| **our bodies within 6 of the group** | **-0.10** (0.01) | **they barely avoid us** |
| their allies within 3 of the group | +0.22 | they join groups their allies are at (no spread rule) |
| group nearer our spawn (dE-dO)/20 | +0.10 | a slight lean toward our side |
| bag x distance home | +0.16 | a full bag does not pull them home |

The fit beats the null clearly (log-likelihood 19,543 v 26,302), but top-1 accuracy is only 0.33 (nearest group:
0.28) [measured]. So their goal pick is roughly "value / (walk + wait)", with clusters valued about equally and a
bonus for timing a respawn, plus coordination we can't see.

**Squads after the opening: none.** From r100 on, 60-65 % of body-rounds are solo and there are about 3.1 separate
groups of bodies. Every pair of types is within 3 tiles only 13-20 % of the time; no pairs are stable [measured].
Our team's numbers are similar (53-57 % solo).

## (d) Engagement (81,103 Kungarna body-turns with one of ours within 5)

Engage rate (hit or close, out of hit / close / back / recall), by own HP share (rows) and local HP ratio (columns).
The local HP ratio is own HP plus allies' HP within 5, divided by our bodies' HP within 5.

| HP share \ ratio | < 0.6 | 0.6-1 | 1-1.6 | > 1.6 |
| --- | --- | --- | --- | --- |
| < 0.3 | 0.11 | 0.12 | 0.16 | 0.20 |
| 0.3-0.5 | 0.23 | 0.44 | 0.55 | 0.62 |
| 0.5-0.9 | 0.29 | 0.48 | 0.62 | 0.74 |
| > 0.9 | 0.35 | 0.49 | 0.67 | 0.77 |

- **Rule** (depth-3 tree, accuracy 0.70 v base 0.60) [measured]: **engage if ratio > 1.0 and own HP > 30 %; retreat
  below 30 % HP whatever the ratio; below a ratio of 0.62 retreat in about 70 % of turns.** Bag size, the half of the
  map and whether our body is farming barely move it.
- Retreat means walking away. A real recall is rare in contact (1-6 % of turns, more at low HP). Outside fights they
  recall often: 37 recalls a game, at a median 74 % HP [measured].
- **Focus fire: little.** 87 % of target-rounds have a single Kungarna attacker. Kills involve 1 Kungarna body most
  often (1: 662, 2: 291, 3+: 79). When we strike first, **no help comes**: Kungarna bodies within 5 of the body we
  hit are 1.99 at the hit and 1.81 four rounds later [measured].
- **Targets:** basic attacks hit whatever is adjacent. Casts (range 4) hit the nearest target 66 % of the time. When
  two of ours are equally near, they pick the lowest HP 56 % of the time, about chance. So: **no HP-based focus**
  [measured].
- Who leads: fight openers are Marcella 751, HoR 509, Vendetta 389 and Ryth 339 (melee). Prism and Vesper rarely
  open a fight.
- Outcome by max HP ratio (Kungarna body v target) when a Kungarna body starts a fight: below 0.75, the target dies
  16 % and the Kungarna body 20 %; at 2x and above, 54 % v 5 % [measured].

## (e) Recall, shop, bank, altars

- **Tribute:** 19 a game v tz. Bag at tribute (quartiles) 26 / **35-50** / 80, mean 54, at **full HP** (median
  1.00). 92 % complete. 80 % go to the altar nearest the last camp hit, 11 tiles away (median), 21 rounds after that
  hit (ours: 30 rounds). Tributes are spread evenly across the game: 2.3-2.6 per 150 rounds from r150 to r900.
- **Big bags (40+): 8.0 a game, 751 gems a game.** **81 % have at most one escort within 5. 30 % are at an altar on
  OUR half (214 gems a game).** Only 13 % have one of our bodies within 6 at the start. We hit the tributer 8 % of
  the time and never killed one. A 40+ tribute is a stationary body for about 6 turns (median) [measured].
- **Altar locks** (step kind 20): **3.0 a game**, 99 % pre-emptive (1 % cancel a tribute), 60 % on their own half,
  placed from r370 / r594 / r873 (quartiles). The other band teams place 0.6 a game, and **we place 0** (the shop bug
  in the end-race study). Their locks on our half block our tributes there [rules].
- **Shop:** 40 visits a game, gold at shop 76 / 134 / 226 (quartiles). Gold at recall is median 24, so recalls are
  about HP, not shopping.
- **Deaths:** 3.7 a game, the bag lost at death is usually 0 (44 gems lost a game; ours 73).

## (f) Reaction to our bodies: they don't hunt

- A fight start is a Kungarna body hitting one of ours after 10+ rounds without doing so. Walking back from each
  fight start, the gap had been closing from 9+ tiles in 2,170 of 3,840 cases. That is two walkers meeting, not a
  dive. **The Kungarna body was diverted from its own camp in 24 %; our target was farming in 22 %** [measured].
- Their farming choice discounts our presence by only 0.10 per body (see (c)). **They keep farming in contact**:
  14.6 % camp-hit rounds with us 5-8 tiles off, against our 6.4 %. This is the "gap opens at contact" finding again.
- 20 % of their body-rounds v tz are on our half, **48 % of those solo**. That is 1.3 Kungarna deaths a game there,
  a third of all their deaths.
- Our deaths v Kungarna (1,311 bodies; Cassi+Issac count twice): Kungarna struck first in 43 %, we did in 34 %. Our
  HP 5 rounds before death is a median 0.80 (we die from burst). The biggest Kungarna body within 6 had 1.64x our
  max HP (median), and 1.5x or more in 55 %. 39 % of our dead had no ally within 5. Cassi & Issac give 304 linked
  deaths (23 % of our death events).

## Where their policy can be exploited (generic rules)

1. **Unescorted big tributes, many on our half.** They bank in big bags (median 50) at the nearest altar, one body
   alone, stationary for about 6 turns. 214 gems a game go in at altars on our half. A **stun cancels a tribute; a
   lock placed on the altar cancels it too** [rules]. Damage does not.
   - **Locks:** fix the shop (`lock_fix`, bot.cpp:1979 / 2040) and turn `lock_pre 1` on (bot.cpp:2057). The earlier
     lock_pre 1/2/3 tests were void: 0 locks were bought. Order the pre-emptive lock by **the altars where enemy
     tributes were seen** (keep a per-altar `last_enemy_trib` round in W, next to `altar_locked`), then by our half.
     Not "enemy side first": Kungarna tributes 30 % of its big bags on our side. A lock blocks only their tributes
     [rules], so locking our own altars costs us nothing.
   - **deny_trib with a stun first** (bot.cpp:3103-3124): when it fires, a body with a stun or stun-dash ready and
     in reach casts it on the tributer before anything else (Cassi slot 1, the HoR dash, Marcella's enhanced attack
     — check the slots in `cambc.h`). That cancels the channel and costs them another ceil(bag/10) turns. With a
     lock in hand, the body within 2 locks instead (try_lock already covers this). `escorts <= 1` matches their 81 %.
   - **Altar sight:** `maybe_ward` (bot.cpp:2539) could place a ward 3-5 tiles from each own-half altar (not
     adjacent: wards there block tribute tiles, `ward_altar_ok`). Today 87 % of their big tributes are unseen.
2. **They invade our gem clusters alone.** By r300 they take 2.3 gem-only groups on our half, to our own 1.35.
   - **Adaptive own-half price** in `farm_vt` (bot.cpp:554-680, next to the `deny_k` block). When we see a group on
     our half come back from a capture we didn't make (the enemy took it), raise own-half group prices (x1.3-1.5,
     decaying over ~150 rounds). This is generic: it fires only against teams that come to our side, so unlike a flat
     `gem_sup` (band: gold300 -100) it costs nothing against teams that stay home.
   - **2-v-1 on lone invaders:** their engage rule wants a local HP ratio of 1 or more, and when we strike nobody
     comes to help (1.99 → 1.81 bodies). This is the case `gang2` (`_agK`, tz-51/52 queued) targets. Add the
     condition "the enemy body is on our half and no other enemy is seen within 8", and keep the max HP gate:
     Kungarna's Ryth and Prism are 2-3.5k after r300.
3. **The HP threshold.** Below 30 % HP their engage rate is 7-20 % and they walk away; they rarely recall in
   contact. So a damaged Kungarna body is a walking kill. A generic `execute` extension: an enemy below 30 % HP that
   is moving away and has no escort within 5 is a commit target for a body with a stun or slow in reach for 2+
   turns. Kill pricing is already in value.h, so this is about stance, not price.
4. **Their engage rule is local, so pairs deter them.** Their engage rate at full HP falls from 0.77 to 0.35 as the
   local ratio falls below 0.6. One of our bodies within 5 of another halves the ratio they see. Packing rules have
   lost before (rally, one-pack opening), so the only form worth testing is narrow [guess]: on the enemy's half, a
   support whose nearest ally is more than 5 tiles off and with an enemy within 8 prices goals toward its nearest
   ally (in `choose()`, bot.cpp:930). Low priority.
5. **Not exploitable within the rules:** their opening is deterministic per map, but countering it needs map-specific
   knowledge. Their target choice (nearest or adjacent, no HP focus) gives little: our squishies are already kept
   back.

## What to copy

1. **Farm through contact** (14.6 % v 6.4 %): this is the WORK stance, tz-54, queued. Kungarna is a clean case: it
   dies 3.7 times a game while doing it. Their contact rule could be the WORK veto: keep farming unless own HP is
   below 30 % or the local ratio is below 0.6.
2. **Let supports keep their captures.** Capture takers by r300: Marcella 28 %, Vendetta 24 %, Prism 19 %, Ryth 12 %,
   HoR 11 % (ours: Vesper 47 %). Their supports earn 230-550 gold by r300 against our 42-231 (HoR 230 v 68,
   Vendetta 316 v 158). Feed 0 lost on the band, so test a **shorter feed radius** (`feed_r` 9 → 4: a support keeps
   a capture unless the carry is close) [guess].
3. **A gem runner on gem-cluster maps** (Prism collects 179 gems by r300). `gem_runner 3` lost locally (60.9 %) but
   was never sent to the band, and the band is the judge here. It is generic (it counts gem-only groups).
4. **Pre-emptive locks** (3 a game, from about r370): see exploit 1.
5. **Bank big, at full HP, at the nearest altar** (median bag 50, 19 tributes a game; we do 12.4 at 25). Pricing
   already favours this; the gap is mostly upstream (gems collected).
6. **Draft** [guess, low priority]: Marcella + HoR + Vendetta + Ryth + flex, never Cassi & Issac (23 % of our deaths
   v them). Our draft study found every comp within ±10 points, and `five_swap 4` (tz-49) is queued; look at its
   band result against Kungarna specifically.

## Caveats

- Kungarna's behaviour against us is partly a response to tz-32..40. The ukband_6nov set (35 games) checks it
  against others: the engage table and the goal model are pooled over all 165 games.
- Hits are matched to champions by the target tile at the end of the previous or current round. Area spells and
  dashes are missed, so the focus-fire numbers are lower bounds.
- "Engage" counts closing the gap, and that includes walking past toward a camp. The HP and ratio gradients hold
  anyway.
- The `cache/` pickles (865 MB) were deleted at the end; `python3 cache.py` rebuilds them in about 20 s.
