# Where the top's extra early income comes from (r0-300), body by body (9 Nov, agent)

**Question.** By r300 the top teams have collected about twice our gems (BUILD_LOG "Phases": 306 v 156). Which bodies
earn the extra, from which camps, and what is structurally different in their opening?

## Data and method

**Games** (decoded band replays, already on disk; nothing downloaded):
- `top_v_band`: 118 games, the top four v the six band teams (7 Nov).
- `tz107_big`: 148 games, tz-107 v the same six (8 Nov). `tz96_big` (149) is a check and agrees within noise.
- The `n23_tz107` replays are not decoded, so they are not used.

**Same maps.** Unless marked, every figure uses the 51 maps both labels share: 95 top games and 85 of ours, per game.

**Caveat** [guess]: the top played the band's 7 Nov bots and we played its 8 Nov bots.

**Scripts** are in `~/tzunami_data/analysis_9nov/early2/` (`python3 -I`, single process, ~25 s for all three labels):

| Script | What it does |
| --- | --- |
| `bodies.py LABEL...` | per body, r0-300: time use, captures (route), first capture, recalls, walks home, spawn visits, shops (inferred from gold drops and stat changes), gem / gold income at r100 / 150 / 300, distance to Vesper, fuel cuts, and the fate of every camp cycle it hit |
| `summ.py [--shared] [--types ..] LABELS` | the per-champion table |
| `split.py` | team income by taker role, zone and kind |
| `fate.py` | who took the reward of each body's camp work |
| `opening.py` + `osumm.py` | team shape r1-150: clusters of bodies, groups worked, first targets, first-cycle races per group |
| `perteam.py` | robustness per top team |

Outputs: `s_shared.txt`, `sp_shared.txt`, `fate_shared.txt`, `open_shared.txt`, `firstcycle.txt`, `perteam.txt`,
`s_gem.txt`, `sp_gem.txt`, `sp_non.txt`.

**Definitions.**
- Zones by the group centre's share of the way from our spawn to theirs: own < 0.4, mid 0.4-0.6, far > 0.6.
- Kind = the group's strongest monster. "gem" and "gold" are clusters: 120 HP tiles with **0 Strength** [rules: camp
  table; game.py STRK]. They deal no damage.
- Income = positive changes in a living body's carried gems / gold.
- Shops: the decoder's step 13 misses most of the top teams' buys, so every gold drop counts as a buy [measured].

## 1. The gap at r300, split into its causes [measured]

**Collected** (banked + carried): top 75 / 127 / 297 v ours 45 / 69 / 149 at r100 / r150 / r300. **Gap +148**; a fifth
of it is already there at r100.

| Cause | Top | Us | Gap |
| --- | --- | --- | --- |
| **Capture gems, all** | 269 | 148 | **+121** |
| gem clusters | 106 | 32 | **+74** (mid +57, own +14) |
| wolves | 78 | 53 | +25 (mid +23) |
| elk | 71 | 56 | +15 (mid +20, own -5) |
| golems | 13 | 5 | +8 |
| Kill / steal gems | 34 | 14 | +20 |
| Bags lost on death, other | | | ~+7 |

**By zone** (capture gems): own third 108 v 97 (+11), **mid 157 v 50 (+107)**, far 5 v 1.

**By taker** (capture gems):
- **supports 229 v 62 (+167)**;
- Vesper 40 v 86 (−46). The top drafts Vesper in only 56 % of these games.

**Gold income to r300:** top 1,606 v ours 1,327 (+280).
- Supports 1,170 v 486 (+684).
- Vesper 436 v 841.
- Team gold-cluster captures 7.2 v 3.7.

**By map regime.** The rule is general: the number of pure gem-cluster groups on the map, readable at the draft.

| Pure gem groups | Top r300 | Us r300 | Gap | Share of our games | Share of the gap |
| --- | --- | --- | --- | --- | --- |
| 0-1 | 206 | 138 | +68 | 56 % | ~28 % |
| 2-3 | 325 | 169 | +156 | 14 % | ~16 % |
| 4+ | 427 | 174 | +253 | 30 % | **~56 %** |

**On the 17 shared 4+ maps:**
- top supports' capture gems 342 v ours 78;
- top Vesper is drafted in 31 % of those games;
- the top drafts the same Marcella / Vendetta / HoR / C&I as we do, plus Willow, Prism or Tavi instead of Vesper;
- every top team, with or without Vesper, shows it: support solo cluster captures 8.6-11.0 v ours 3.2, r300 collected
  319-482 v 188.

**So:** the gap is **support income from cheap groups, mostly zero-Strength clusters, own and mid**. It is largest on
gem-cluster maps. Vesper is not behind: ours out-earns theirs.

## 2. Body by body (shared maps; top / us) [measured]

Cells read top / us. Rounds are medians; time use is the share of body-rounds in r1-150.

| | Vesper | Vendetta | HoR | Marcella | Cassi | Issac |
| --- | --- | --- | --- | --- | --- | --- |
| Bodies a game | 0.56 / 1.00 | 0.71 / 0.88 | 0.83 / 0.88 | 0.57 / 0.80 | 0.72 / 1.00 | 0.72 / 1.00 |
| Camp-hit time | 29 / 25 % | **27 / 19 %** | 27 / 23 % | 18 / 18 % | 26 / 21 % | 26 / 25 % |
| Capture time | 10 / 9 % | **9 / 4.5 %** | 6 / 4 % | **7 / 3 %** | 3 / 2 % | 5 / 2 % |
| Walk | 51 / 52 % | 53 / 62 % | 53 / 59 % | 63 / 67 % | 56 / 59 % | 51 / 54 % |
| Idle | 7 / 7 % | 8 / 8 % | 6 / 9 % | 7 / 5 % | 4 / 6 % | 6 / 8 % |
| Dead | 1 / 2 % | 1 / 3.5 % | 5 / 2 % | 0 / 3 % | 9 / 9 % | 9 / 9 % |
| First camp hit | r11 / r13 | r12 / r13 | r16 / r13 | r22 / r20 | r18 / r18 | r11 / r12 |
| **First capture** | r29 / r32 | **r53 / r97** (24 % none) | **r70 / r102** (41 % none) | **r38 / r98** | r106 / r116 | **r75 / r116** (55 % none) |
| Captures r0-150 (solo) | 3.8 (3.5) / 3.0 (2.9) | **2.8 (2.5) / 0.9 (0.9)** | 1.7 / 0.8 | **2.3 / 0.9** | 0.9 / 0.6 | 1.3 / 0.4 |
| Captures r150-300 | 3.3 / 2.8 | **3.1 / 1.1** | 2.4 / 0.8 | 2.2 / 1.1 | 1.2 / 0.7 | 1.7 / 0.4 |
| Hitters per capture r0-150 | **2.6 / 3.4** | 2.1 / 1.5 | 1.9 / 1.6 | 2.4 / 2.3 | 1.5 / 1.6 | 1.6 / 1.0 |
| First two captures (top) | gold-gold 30 % | wolf-wolf 22, gold-gold 21 | gold-gold 15, wolf-wolf 14 | wolf-wolf 20, gold-gold 15, gem-gem 13 | gold-gold 16 | **gem-gem 24** |
| First two captures (us) | wolf-wolf 21, wolf-elk 18 | none 24, wolf-wolf 17 | **none 41** | wolf-wolf 16, wolf 15 | none 35 | **none 55** |
| Recalls r<=300 | 3.4 / 2.2 | 3.4 / 3.6 | 2.7 / 3.4 | 3.3 / 2.3 | 1.9 / 1.1 | 2.0 / 2.5 |
| First recall | r91 / r91 | **r79 / r53** | **r93 / r59** | r77 / r108 | r140 / r141 | r127 / r78 |
| HP at recall | 0.69 / 0.67 | 0.55 / 0.55 | 0.61 / 0.49 | 0.72 / 0.53 | | |
| Walks home at < full HP | 0.4 / 1.1 | **0.6 / 1.5** | **0.5 / 1.6** | 0.8 / 1.0 | 0.8 / 1.4 | 0.7 / 1.4 |
| Spawn visits r<=300 | 3.8 / 3.3 | **4.0 / 5.2** | **3.3 / 5.1** | 4.0 / 3.2 | 2.6 / 2.5 | 2.8 / 4.2 |
| Wait per visit (rounds) | 2.6 / 2.7 | 2.0 / 1.8 | 2.0 / 2.0 | 2.3 / 3.2 | 2.7 / 3.4 | 1.9 / 1.9 |
| First shop | r78 / r66 | **r79 / r140** | r122 / r118 | **r78 / r148** | r189 / r172 | r143 / r184 |
| Gold spent r<=300 | 670 / 782 | **371 / 112** | **244 / 76** | **427 / 198** | 98 / 51 | 112 / 29 |
| First buy | Strength 91 / 91 % | Str 60 %, Health 31 % / Str 67 % | Focus 67 % / Focus 48 % | Focus 93 / 74 % | | Health 43 / 29 % |
| Gems r100 / 150 / 300 | 25 / 36 / 77 v 28 / 41 / 93 | **20 / 33 / 75 v 6 / 9 / 20** | **9 / 13 / 44 v 4 / 8 / 15** | **23 / 44 / 97 v 9 / 13 / 28** | 8 / 13 / 29 v 3 / 5 / 10 | 11 / 15 / 33 v 2 / 4 / 6 |
| Gold r100 / 150 / 300 | 221 / 361 / 782 v 245 / 379 / 841 | **120 / 179 / 417 v 27 / 52 / 129** | 62 / 97 / 273 v 25 / 46 / 94 | 132 / 192 / 479 v 62 / 103 / 227 | 25 / 45 / 116 v 13 / 26 / 70 | 30 / 50 / 131 v 12 / 16 / 37 |
| Max HP r300 | 1,332 / 1,555 | 1,245 / 983 | 1,311 / 1,003 | 1,522 / 1,235 | 662 / 710 | 1,119 / 977 |
| Deaths r<=300 | 0.08 / 0.20 | 0.06 / 0.29 | 0.15 / 0.24 | 0.07 / 0.28 | 0.49 / 0.55 | 0.49 / 0.55 |
| Fuel cuts r1-5 | 0.34 / 0.82 | 0.16 / 0.99 | 0.24 / 1.01 | 0.11 / 1.01 | 0.10 / 0.84 | 0.19 / 0.93 |

The top's Prism (0.29 a game) is the biggest gem earner there is: 151 gems by r300, 54 % gem-cluster captures, its first
capture at r42.

**Not the causes** [measured]:
- **Splitting at round 1:** body clusters (Chebyshev <= 4) are 2.10 / 2.85 / 3.00 v 2.01 / 2.94 / 2.97 in r1-50 / 51-100 /
  101-150. Supports within 4 of Vesper: 0.50 / 0.29 / 0.22 v 0.52 / 0.26 / 0.29. The shapes are identical.
- **Fuel cuts:** the first camp hit is level (r11-16 v r12-20), so the round-1 cuts cost at most 1-2 rounds.
- **The Capture emblem early:** Vesper stands 2-3 rounds before a capture in 34 % of the top's captures and 22 % of
  ours. Supports are at 4-5 rounds in both. Few early captures can carry the emblem; the first shop is at r78 and 91 %
  of the buys are Strength.
- **Shop timing:** the supports' later shops follow from their lower gold. Vesper's shop is level.
- **Our Vesper** collects more than theirs.

## 3. What is structurally different [measured]

**(a) The supports' camp work goes into Vesper's captures.** Share of each body's camp-hit rounds whose reward went to
Vesper:

| Body | Top | Us |
| --- | --- | --- |
| Vendetta | 16 % | **51 %** |
| HoR | 17 % | **50 %** |
| Marcella | 5 % | **44 %** |
| Cassi | 21 % | **40 %** |
| Issac | 14 % | **41 %** |

On top games with a Vesper, it is still only 25 %. The top's supports keep their own work: Vendetta 51 % v 29 %, HoR
34 % v 17 %, Marcella 62 % v 37 %.

**(b) The supports' first target is Vesper's target.** Support whose first camp hit is Vesper's first group:

| Body | Top | Us |
| --- | --- | --- |
| Vendetta | 18 % | 68 % |
| HoR | 20 % | 55 % |
| Marcella | **0 %** | **51 %** |
| Cassi | 26 % | 61 % |
| Issac | 31 % | 52 % |

The top's Vesper opens on a gold cluster in 47 % of games; ours opens on wolves in 49 %. Our Vesper's captures r0-150 have
3.44 hitters on average, the top's 2.56.

**(c) The same heavy work, but far less cluster work.** Support camp-hit rounds a game r0-300, top v us:

| Kind | Rounds | Group-cycles | Top: kept by the hitter / to Vesper | Us: kept by the hitter / to Vesper |
| --- | --- | --- | --- | --- |
| Wolves | 187 v 158 | | 38 % / 14 % | 21 % / **45 %** |
| Elk | 90 v 89 | | 19 % / 23 % | 9 % / **54 %** |
| Gem clusters | **27 v 10** | **5.1 v 1.5** | 64 % self | |
| Gold clusters | **29 v 18** | **8.2 v 3.8** | 60 % self | |

The top's supports work **13.3 cluster cycles a game** (about 4 rounds of hitting each, no damage taken) v our **5.3**.
Support cluster captures: **4.6 / 5.2 in r0-150 / r150-300 v 2.0 / 1.8** (solo 4.2 / 4.8 v 2.0 / 1.7). Their value
(gems + 0.5 gold) is 112 / 128 v 48 / 43.

**(d) Our heavy-camp tanking sends the supports home.** Our supports take hits on wolves / elk for Vesper's
captures:
- Vendetta and HoR first recall at r53 / r59 v r79 / r93, at 0.49-0.55 HP;
- they walk home 1.5-1.6 times by r300 v 0.5-0.6;
- they visit spawn 5.1-5.2 times v 3.3-4.0;
- their dead time is 3.5 % / 6.8 % of rounds v 1 %.

Clusters cost no HP [rules: 0 Strength], so the top's cluster loop needs fewer trips home.

**(e) The clusters we leave go to the band, or to nobody.** Share of each group's first cycle taken by r300, top v us:

| Group | Top takes | We take | Band v us | Untaken v us |
| --- | --- | --- | --- | --- |
| Own-third gold clusters | 0.82 | 0.50 | | 0.45 |
| Own-third gem clusters | 0.70 | 0.43 | | 0.48 |
| Mid gold clusters | 0.47 | 0.30 | 0.43 | |
| Mid gem clusters | 0.43 (r61 / r83, quartile / median) | **0.10** | 0.39 | 0.52 |
| Mid wolves | 0.40 | 0.20 | | |
| Mid elk | 0.26 | 0.16 | | |

We reach a mid gem cluster (within 2, by r200) in 30 % of cases; the top in 58 %. This is **new income, not a
transfer**: mid groups go to the band (it takes 135 mid capture gems r0-300 against us, 73 against the top) or sit
untaken.

## 4. In the code (bots/tz/src/bot.cpp, read 9 Nov)

How the code produces (a)-(c) [rules: code]:
- `squad_of()` with `squads 2`, `squad_table 1`: two squads from r0, Vesper + Vendetta and HoR + Marcella + the twins.
  The leader is the lowest slot (`pack_leader`).
- `plan_build()`, follower branch: the leader's target is priced with the pack's DPS (`farm_vt(g, pack_n, pack_dps)`)
  and multiplied by `follow_k` 1.5. A cluster is priced solo, so leaving the pack for one needs a solo rate 1.5x the
  pack share. `plan_near` 30 multiplies every score by 2^(-start / 30), the nearest-ready group first, which works
  against mid clusters 15-25 tiles out. `plan_claim` (spread bodies over different groups) is 0.
- `hand_take_raw()` with `feed 1`: the highest `taker_rank` within `hand_r` takes, so Vesper (6) takes any reward she is
  beside.
- `farm_vt()` with `hand_carry 1`: the carry prices an ally-cleared group at the full reward when it arrives before the
  allies finish, which draws Vesper to the supports' groups.
- The danger and threat discounts (x0.6 / x0.85 for enemies seen in 30 rounds; `threat_k`) hit mid groups.
- `play_draft()` (draft.cpp): Vesper is always the first pick (tables 1-9; the `carry` gold-cluster rule applies only in
  the default table).

**Earlier tries that touched this:**

| Try | Base | Result |
| --- | --- | --- |
| `gem_open`, `gem_sup`, `gem_runner`, `gem_marcella`, `gem_map_n` | tz-30s | local v v93 only, or the band on tz-36 (`gem_sup 1.6`: gold300 −100) |
| `grow2` (support spread) | | pricing tweaks under "covered + quiet" conditions inside the squads; locally a transfer from Vesper |
| `eco 7` (fair-share take) | | took captures from Vesper; lost −0.11 |

None changed who the supports' camp work feeds, or added cluster work.

## 5. What to build first: the support cluster loop

**The rule** (general; no map names). From r1, every zero-Strength group (gem / gold cluster) is a job for one
non-Vesper body, the clearer:
1. **Claims.** Each cluster is claimed by the nearest free support by path ETA; claims are posted in comms.
   `plan_claimed` already exists and could be switched on for clusters only.
2. **Priced on its own.** A support prices its claimed cluster solo against its squad leader's target without the
   `follow_k` bonus. Squads stay for groups with Strength (wolves, elk, golems).
3. **The clearer captures.** Clusters are exempt from `hand_carry` and from the feed rank in `hand_take_raw`.
4. **It cycles.** The claimant comes back when its cluster respawns (gem clusters respawn after 50 rounds, gold after 50
   [game.py RESP]). The mid is in scope: the danger discount is softened to the `danger_one` level for clusters, since
   they deal no damage.

**Where:**
- `plan_build()`: the follower branch and the shortlist push;
- `farm_vt()`: the `hand_carry` share;
- `hand_take_raw()`: the taker key;
- optionally `squad_of()`: on maps with 4+ pure gem groups (counted as `gem_map()` does), every non-Vesper body is its
  own squad.

The draft lever (Willow / Prism instead of Vesper on 4+ gem maps) is the second step [guess]: the top earns there with
the same four supports we draft.

**KPIs** (`bodies.py` + `summ.py` on the build's band replays, on shared maps):

| KPI | Now | Target | Top |
| --- | --- | --- | --- |
| Support cluster captures r0-300 (headline) | 3.8 | >= 7 | 9.8 |
| Support camp-hit rounds whose reward goes to Vesper | 40-51 % | <= 30 % | |
| Mid gem clusters, first cycle taken | 0.10 | >= 0.3 | 0.43 |
| Mid gold clusters, first cycle taken | 0.30 | >= 0.4 | |
| Supports' capture gems r300 | 62 | >= 120 | 229 |
| Team collected r150 | 69 | >= 95 | 127 |

**Guards:**
- Vesper's income r300 (93 gems / 841 gold) must not fall by more than ~10 %, or it is a transfer again (grow2).
- Deaths r<=300 must not rise.
- The band's mid capture gems r0-300 against us (135) should fall.

**Whether it wins on the band is unknown [guess].** The mid holds and denial rules lost there. This one adds
zero-damage jobs the band is not contesting at the moment we would take them: we reach 70 % of the mid gem clusters
not at all by r200.
