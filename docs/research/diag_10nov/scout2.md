# scout2: what decides the games v306 still loses (10 Nov, ~18:00)

**Question.** Against the five teams that still beat v306 most (policy wonk, QS2isLaw, Team Kungarna, Claudus Maximus,
Vvvvv), what decides the games now? Where does the banked-gem gap open, what happened in the 30 rounds before, how does
the top beat the same teams, and how do our games v the near-Elo teams (which v306 now beats) differ? Find the 1-2
largest causes not covered today.

**Data** [measured]. v306 = `tz189_big` decoded for the 5 teams (75 games) and the 4 near-Elo teams (60); base v281 =
`p83_m2` on the same opponents / maps / sides (75 + 60); top = `top_v_band` + `uk3band` games v 4 of the 5 (123; none v
Vvvvv: Vvvvv is a top team itself). r1-600 unless stated. v306 v the 5 won 19 of 75 here (Kungarna 6, Vvvvv 5,
QS2isLaw 4, Claudus 2, policy wonk 2); paired v base on the same 75 games: share +0.09 (se 0.04), wins +0.12 (se 0.06)
(`sum2b.py`). Scripts: `~/tzunami_data/analysis_10nov/scout2/` (`ext2.py` makes the compact game pickles from scout's `ext.py`; `parse2b.py` is session2b's parser with the top's rows allowed).

## Short answer

1. **The gap opens from income, not from a fight.** In v306's losses v the 5 (n 56) the last round we were level in
   banked gems is a median **r188** (base r167; the band's losses to the top r167). In the 30 rounds before, the band
   captures 44 gems to our 13 and carries **126 gems to our 25** at that round; it then banks 98 in the next 30. Our
   deaths in that window are 0.29 (the band's in its losses to the top: 0.35). Nothing happens in those 30 rounds that
   does not happen in every window: the income gap is steady from r~100.
2. **What makes the five different: they do not die, and they win the damage race at contact.**

   | r1-600, a game | v306 v the 5 | top v the same 5 | v306 v near-Elo | base v the 5 |
   |---|---|---|---|---|
   | Their deaths (our kills) | **2.67** (se 0.28) | 5.05 | 5.18 | 3.09 |
   | Our deaths | 5.31 | 2.80 | 4.40 | 4.76 |
   | Mid captures, ours / theirs (gems) | **93 / 249** | 250 / 124 | 161 / 204 | 89 / 276 |
   | Their captures in OUR zone | **75** | 21 | 40 | 72 |
   | Kill gems, ours / theirs | 21 / 48 | 69 / 19 | 50 / 30 | 26 / 35 |

   **Per squad engagement** (one of our bodies first comes within 4 of an enemy with an ally within 6; 10 rounds after;
   `dmg.py`, `squadhit3.py`):

   | Per onset | v306 v the 5 (20.3 a game) | top v the 5 (14.0) | v306 v near-Elo (18.3) |
   |---|---|---|---|
   | Enemy HP we remove / our HP lost | **419 / 523** | 606 / 457 | 525 / 430 |
   | Kills / deaths | **0.070 / 0.123** | 0.187 / 0.079 | 0.157 / 0.096 |
   | ... with our live HP >= 1.2x theirs (10.2 a game; 2.2x on average) | 474 / 519; 0.098 / 0.069 | 543 / 388; 0.215 / 0.042 | 557 / 417; 0.199 / 0.069 |
   | Level fights the ENEMY walked into (1.27 a game) | **0.032 kills / 0.474 deaths**; our moves away 3.6 a body in 10 rounds, champion hits 0.24 | 0.330 / 0.099; away 2.7, hits 0.50 | 0.172 / 0.141; away 3.0, hits 0.55 |

   The same holds for every one of the five (per squad onset, enemy HP removed / kills / deaths; `dmg.py`):

   | Opponent | v306 | top v the same team |
   |---|---|---|
   | policy wonk | 330 / 0.083 / 0.100 (20.0 onsets a game) | 593 / 0.152 / 0.090 (13.5) |
   | QS2isLaw | 535 / 0.084 / 0.082 (26.1) | 788 / 0.207 / 0.030 (16.4) |
   | Team Kungarna | 393 / 0.071 / 0.142 (14.1) | 611 / 0.197 / 0.098 (15.6) |
   | Claudus Maximus | 421 / 0.052 / 0.094 (20.6) | 519 / 0.238 / 0.040 (11.5) |
   | Vvvvv | 374 / 0.055 / **0.216** (20.7) | (no top games) |

   Two flavours: v Kungarna and Vvvvv we die (6.5 / 7.0 deaths by r600 for 2.1 / 2.6 kills); v policy wonk and
   QS2isLaw the fights are closer but they take our zone (126 / 97 gems a game) and the mid.

   Everything else follows from this: the five hold the mid (their mid captures 249 v 204 for the near-Elo teams; ours
   fall from 161 to 93) and walk into our zone in packs (**policy wonk 126 gems a game, QS2isLaw 97**; the top concedes
   17 and 11 to the same teams). Of policy wonk's and QS2isLaw's 99 gems a game from our zone, 71 are taken with one of
   our bodies within 8 of the group, outnumbered (48) or with less live HP (60), not hitting anything (52) (`invade.py`).
   deny_k (more mid presence) already lost on the band (tz-80/85, share -0.07): **presence without winning the fights
   loses**, so the fight is the lever, not the map.
3. **Cause 1 (new): our supports are a third of the band's size; the gold goes to one giant Vesper.** At r600 v the 5
   (`ext` stats; summaries for gold):

   | r600 (max HP / Strength / Focus) | v306 | the 5 v v306 | the top v the 5 |
   |---|---|---|---|
   | Vesper | **3,838** / 230 / 107 | 2,739 / 230 / 122 | 2,747 / **264** / 129 |
   | Marcella | 2,203 / 42 / **160** | 2,841 / 52 / **351** | 2,235 / 48 / 279 |
   | Vendetta | 1,475 / **109** / 101 | 2,078 / **174** / 108 | 1,950 / 183 / 108 |
   | HoR | 1,277 / 30 / **118** | 1,595 / 32 / 168 | 1,822 / 33 / 182 |
   | Cassi | 925 / 30 / **105** | 665 / 30 / 175 | 722 / 31 / 169 |
   | Team Focus (r300 / r600) | **548 / 611** | 613 / 842 | 678 / 890 |

   Gold earned by r600 (summaries): our Vesper 1,690 (theirs 1,640), but **Marcella 602 v 1,345, Vendetta 411 v 932,
   HoR 219 v 502**. Our Vesper is the biggest body on the field (sizex 8: Greed after-line in Health; base Vesper 2,497
   HP / 276 Str) while every other body of ours is smaller and weaker than the same champion of the band or the top.
   Team Focus at r600 fell from 661 (base) to 611 with sizex 11; the band has 842, the top 890. [guess: the abilities
   that make the band's and the top's kills scale with Focus; we have measured the damage gap, not its split by source.]
4. **Cause 2 (new, smaller): the fed break is squad-blind.** A body breaks off from any enemy with >= 1.9x its max HP
   within reach + 2, whatever its allies (`fed_k 1.9`, `fed_gang 0`, `eng_fed 0` [code: play_turn, `fed_break`]). When
   the five walk into a squad of ours, 11.0 squad bodies a game are "fed-exposed" (an enemy >= 1.9x within 8: Cassi 4.0,
   Issac 1.8, HoR 1.7, Vendetta 1.5); the top has 5.45, and we have 6.3 v the near-Elo teams. Ours move away 3.5 times in
   10 rounds and land 0.19 champion hits each; the top's fed-exposed bodies land 0.44. Death rate per exposed body is
   the same (0.116 v 0.122), so this costs damage output, not bodies. [measured: `fedsq.py`] Cassi's champion stuns are
   NOT suppressed by it (4.9 a game v the top's Cassi 4.6) [measured].

**Not new / checked and dropped** [measured]: capture standoffs on mid groups (0.56 a game); capture denial at home (the
cases where we had the numbers are 7-16 gems a game; `deny_cap` exists); own-spawn idling (83 v 50 body-rounds); gem
yield per capture is level (1.04 x base for both); teleport crystals (step kind 21 is not the crystal: its targets are
4+ tiles away); fuel-cut phantom recalls (0.15 a game). **Escape-recall measure:** `session2b/escape.py` counts
end-of-turn pre-starts that follow an action as real recall starts (`cht 3` after a move then step 11): 3.5 a game v the
5, all cancelled the next turn. In v306 v the 5 the kept escape recalls are 7.7 a game, 66 % arrive, 6 % die within 15
rounds; "died recalling" is still +0.32 a game v base (sig) but part of it is the same display artifact.

## Where the gap opens (losses v the 5, the 30 rounds up to the last level round) [measured, `gap.py`]

| | v306 lost (56) | base lost (60) | band lost to the top (97) | near-Elo lost to v306 (41) |
|---|---|---|---|---|
| Median last level round | r188 | r167 | r167 | r487 |
| Winner's / loser's captures in the window | 44 / 13 | 52 / 14 | 37 / 23 | 32 / 17 |
| ... winner's in the mid / in the loser's zone | 27 / 5 | 33 / 6 | 15 / 2 | 15 / 0 |
| Winner's / loser's bag at that round | 126 / 25 | 129 / 49 | 133 / 38 | 125 / 40 |
| Winner banks in the next 30 | 98 | 89 | 105 | |
| Loser's deaths in the window | 0.29 | 0.18 | 0.35 | 0.46 |
| Team max HP, winner / loser | 6,058 / 6,663 | 6,869 / 6,386 | 7,359 / 6,963 | 11,127 / 8,082 |

v306 is no longer the smaller team when the gap opens (sizex); it loses the income race anyway.

## What I built: `sqx` (squad answer) for cause 2 (cause 1 has no new lever today)

**Cause 1 has no clean lever left today** [measured + history]: the supports' gold is the feed rule and the shop line.
`feed_shards 25` (supports keep more gold) lost on the band on 8 Nov (tz-43: share -0.05, kills -0.9) and draft changes
are closed for today. The only zero-code hedge, Vesper's after-line Strength-first (`sizex=19`, size.md), **lost
locally: 42.6 % (37-49) v `bots/_v306`** (256 games, seed 0; deaths 6.2 v 6.3). Not sent.

**`sqx` in `bots/_sc3`** (a copy of `bots/_v306`, so its defaults ARE v306's settings; files `src/value.h`, `src/bot.cpp`;
`static constexpr`, 0 compiles out):

```cpp
// value.h, after s2b_er
static constexpr int sqx = 0;          // 1 squad-aware fed break, 2 answer the walker
static constexpr float sqx_k = 1.0f;   // the squad edge: assess()'s L.our >= sqx_k x L.their
// bot.cpp, play_turn, in the fed_break loop just before `fed_break = true;` (bit 1):
//   if (L.their > 0 && L.our >= sqx_k * L.their) continue;          // the squad outweighs them: no solo break
// bot.cpp, play_turn, right after the contact stance block (before the p1 stance hygiene) (bit 2):
//   if (contact && stance == BREAK && me.hp >= stance_low * max_hp && L.their > 0 && L.our >= sqx_k * L.their)
//     commit on the nearest visible enemy within my range + 1 that is nearer me than at its last sighting a round ago.
```

`L.our` / `L.their` are the existing `assess()` sums (our HP x damage within 6 v theirs within 8, enemies seen within 3
rounds), so the bits add no SDK calls. Each bit prints `SQX1` / `SQX2` lines at power-of-two counts (inside the
`if constexpr`).

**cmp** [measured]: `bots/_sc3` at `sqx=0`, release build, is **byte-identical** to `bots/_v306/.cambc/build-release/bot.wasm`
(3,701,340 bytes).

**Local results v `bots/_v306`** (256 games each, all maps x both sides) [measured]:

| Build | Win (95 % CI) | Deaths us v them | gold300 | fuelEx | Held-out maps |
|---|---|---|---|---|---|
| `sqx=3`, seed 0 | **55.5 % (49-61)** | 6.1 v 6.0 | 1,518 v 1,489 | 24.0 | 52.4 % |
| `sqx=3`, seed 1 | **55.9 % (50-62)** | 6.2 v 6.2 | 1,513 v 1,495 | 25.3 | 52.4 % |
| `sqx=1` (bit 1 only), seed 0 | 52.0 % (46-58) | 6.1 v 6.1 | 1,513 v 1,477 | 23.4 | |
| `sqx=2` (bit 2 only), seed 0 | 52.0 % (46-58) | 5.9 v 6.0 | 1,505 v 1,495 | 24.0 | |
| `sizex=19` (zero-code hedge), seed 0 | 42.6 % (37-49) | 6.2 v 6.3 | 1,501 v 1,498 | 24.4 | 46.4 % |

**Fires** [measured, kept seed-0 outputs]: bit 1 skips a fed break >= 50 body-turns a game, bit 2 answers a walker >= 4
times a game (power-of-two counters: lower bounds).

**KPIs** (64 of the seed-0 games decoded; sqx side v the v306 side in the same games) [measured]:

| | sqx=3 | v306 | Top v the 5 (band) | v306 v the 5 (band) |
|---|---|---|---|---|
| Fed-exposed bodies the enemy walked into, champion hits each in 10 rounds | **0.34** | 0.17 | 0.44 | 0.19 |
| ... their death rate within 15 rounds | **0.116** | 0.064 | 0.122 | 0.116 |
| Squad onsets: enemy HP removed / ours lost | 514 / 509 | 506 / 484 | 606 / 457 | 419 / 523 |
| Squad onsets: kills / deaths | 0.081 / 0.085 | 0.107 / 0.065 | 0.187 / 0.079 | 0.070 / 0.123 |

The KPI it was built for moved (fed-exposed hits 0.17 -> 0.34, toward the top's 0.44), and those bodies now die at the
top's rate instead of v306's local rate; per game deaths stay level (6.1-6.2 v 6.0-6.2) and gold by r300 is +18 to +29.
Locally the squad-onset exchange did not improve (mirror v306 is not the band). **What the band should show**: our
kills up (v the 5: 2.7 by r600), deaths not up; read kills and deaths next to share, since every unconditional
"fight more" piece lost on the band. This one fires only with a squad edge (`L.our >= L.their`).

## Band line

`sqx 3: squad answer (no solo fed break, answer the walker when the squad has the edge)|_sc3|robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11 endx=3 s2b=1 sqx=3|all`

(`bots/_sc3` already holds these values as defaults; the overrides are the v306 settings and change nothing but `sqx`.)

## What did not work / what does not transfer

- No lever found for cause 1 (support size): feed rules lost on the band before, `sizex=19` lost locally.
- Home invasions (policy wonk 126, QS2isLaw 97 gems a game from our zone) are a consequence of losing fights: our body
  near the group is outnumbered; `deny_cap` / `deny_k` / `rally` exist and lost or never fired.
- Local wins have not predicted the band; `sqx` is a fight piece measured against a v306 mirror.
