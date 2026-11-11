# transfer: why the local contact gains do not reach the band (8 Nov)

**Data.**
- Band: `tz55_big` (planner P30), `tz62_big` (+ roles 6: WORK + conversion) and `tz64_big` (+ p1 + p3). All
  150 games of each are decoded.
- Pairing is by (opponent, map, side, group). This matters: (opponent, map, side) alone has 4 duplicate keys.
- Local:
  - the mid study's `cyc_mid_*.pkl` (64 maps, side a, v v93): B0 = `_role` (the tz-62 build), Q13 = p1 + p3 (the tz-64
    build), X3 = p3;
  - older decoded local games v v93 (`loc_27`, 209 to 223 of 256 games usable; `loc_30`, 70 to 73 of 80). Their own
    builds are older, but v93 is frozen, so they show v93's side of a contact. The mid labels' replays were deleted,
    so per-body measures on the local side come only from these.

**Definitions.** As in planloss / mid:
- mid = t 0.33–0.67 by r600;
- a contact is a cycle both sides reach (within 2), at t 0.25–0.75; the contact round is when the second side
  arrives.

**Scripts and outputs** are in `scratchpad/diag/transfer/`:
- extraction: `cycles.py` and `extract2.py`, copied unchanged;
- new: `kpi_opp.py`, `leak.py`, `exchange.py`, `close.py`, `constr.py`, `xlabel.py`, `enemy.py`, `bothstay.py`,
  `acts.py`, `stops.py` + `stoprep.py`, `hprisk.py`, `steal.py`, `fight.py`;
- outputs: `out_*.txt`.

**Rules followed.** No games or judges were run and no bots were edited. I read only `bots/_mid` (our code). Tags:
[measured] = counted from the replays, [code] = read in `bots/_mid/src`, [guess] = inference.

## 0. Answer in five lines

1. **The mechanisms did move on the band, at about half their local size** [measured].
   - WORK took our camp damage at a contact from 63 to 110 per body, the band's own level (108).
   - p1 + p3 raised the contact take by **+3.8 points** (locally +8.8) and cut steals from 35 % to 27 %.
   - Together: mid gems +26 ours, −26 theirs a game.
2. **The gain leaked into the kill / bag exchange** [measured].
   - tz-64 v tz-55 by r600: the capture swing is **+34 gems a game**; the kill / bag exchange is **−26**, so the
     margin moves by only **+8.6 ± 23**.
   - tz-62 v tz-55: the capture swing is +24 and the exchange **−35**, so the margin moves by −10.6.
   - Workers kill less (−0.3 to −0.4 kills a game), pick up fewer bags (kill gems −8 to −11) and die carrying bigger
     bags (+4 to +9 gems).
3. **Why local overstates it** [measured]:
   - v93 loses the fight at a contact: we lose more bodies than v93 at only 13–18 % of contacts, and v93 loses more at
     25–29 %. The band is the reverse: we lose more at 24–26 %, they at 11–13 %.
   - v93's bodies at a contact do half the band's camp damage (50–59 v 103–108 per body) and take 15–40 % more damage
     than ours.
   - So locally a hold is a farm race against a body that doesn't farm and dies. On the band it is a fight against
     bigger bodies (1,440 v our 1,160 max HP at contact; 1,375 v 1,090 per body at r300) that farm at our rate.
4. **The hold's stop conditions are not the main problem** [measured].
   - The fed stop fires for 13.8–15.1 % of our bodies on the band, against 4.3–9.2 % locally. All strict stops together cover
     36–40 % of bodies on the band, against 27–38 % locally.
   - Bodies that hold with no stop stay 78 %.
   - The cost sits in the holds that should stop and don't. When the enemy's max HP nearby is ≥ 1.15× ours, a holder
     dies **8.6–8.9 %** of the time within 5 rounds (tz-55 without the hold: 4.7 %) and hits a camp 0.3–0.5 times.
     This is 27–31 % of body-contacts.
5. **Fix** (§3):
   - let workers assist (`role_wassist 1`);
   - end the hold when we are outsized at the group;
   - don't hold with a big bag while outsized.
   - Judge locally on the kill / bag exchange and the fight balance at contact, not on contact take. Build a sparring
     bot that wins contact fights 2:1 the way the band does.
   - The band A/B on 150 games has 28–37 win flips between near-identical builds, so ± about 12 wins at 95 %.
     "Level" cannot rule out the +1–3 wins that the measured +8.6 margin implies [guess on the mapping].

## 1. Did the mechanisms move? (150 paired games each)

### 1.1 Mid / contact KPIs

[measured; `kpi_opp.py`, `out_kpi.txt`, `steal.py`, `acts.py`]

| KPI | tz-55 | tz-62 | tz-64 | local B0 (tz-62 build) | local Q13 (tz-64 build) |
| --- | --- | --- | --- | --- | --- |
| wins / 150 | 28 | 26 | 27 | (75.7 % v v93) | (78.2 %) |
| contact take % | 27.0 | 28.4 | **32.2** | 51.0 | **59.8** |
| mid gems us / them (r600) | 105 / 309 | 126 / 298 | 131 / 283 | 166 / 171 | 197 / 156 |
| camp hits after contact, us / them | 7.0 / 11.0 | 8.2 / 10.4 | 8.1 / 11.6 | 11.8 / 9.6 | 13.6 / 9.1 |
| our bodies at +5: stay / left / dead % | 67 / 30 / 3.4 | 68 / 28 / 3.7 | **72 / 24 / 4.3** | 73 / 26 / 1.3 | 73 / 26 / 0.9 |
| first arrival % | 41.0 | 42.9 | 43.2 | 50.7 | 51.8 |
| groups we cleared that they took (planloss "lost") % | 11.7 | 12.9 | **10.2** | 7.4 | 4.9 |
| stolen after we out-hit % (`steal.py`) | 30.2 | 34.9 | **27.1** | | |
| our camp damage per body, 8 rounds from contact (`acts.py`) | 63 | **110** | 91 | (loc_30: 59) | |
| band's camp damage per body | 107 | 108 | 103 | (v93: 50–59) | |
| camp-hit rounds of our bodies, % | 8.4 | 12.4 | 13.0 | | |
| camp-hit rounds of the band's bodies, % | 15.1 | 14.7 | 13.6 | (v93: 9–10) | |

How the band moves compare with the local ones:

| Step | Band | Local |
| --- | --- | --- |
| tz-62 → tz-64, contact take | +3.8 | +8.8 |
| tz-62 → tz-64, mid margin | +20 | +46 |
| tz-62 → tz-64, stay | +3.7 | +0.1 |
| tz-62 → tz-64, deaths at contact | **+0.6** | −0.5 |
| tz-55 → tz-62 (WORK), contact take | +1.4 | not measurable: no local tz-55 cycles exist |

- In log-odds the band take moved +0.18 and the local take +0.38: about half [measured].
- Within the same size × numbers bucket, local take rates are about 20 points higher than the band's for every build.
  The bucket mix explains only 3–4 points (`xlabel.py`: tz-62's band rates on the local mix give 31.9 v 28.4; B0's
  local rates on the band mix give 46.3 v 50.5).

### 1.2 Contact take per opponent (tz-55 / tz-62 / tz-64)

[measured; `out_kpi.txt`]

| Opponent | Take % | Wins | Note |
| --- | --- | --- | --- |
| :3 | 34.9 / 29.2 / 39.2 | 6 / 3 / 3 | |
| Claudus Maximus | 22.1 / 29.5 / 34.3 | 6 / 5 / 5 | |
| QS2isLaw | 24.3 / 31.5 / 37.4 | 5 / 6 / 5 | |
| Rogue Lock Pickers | 21.2 / 28.3 / **37.8** | 5 / 6 / **7** | tz-64 margin +68 here |
| Team Kungarna | 34.0 / 28.5 / **22.1** | 3 / 3 / 4 | tz-64 deaths at contact 5.6 %, our bags lost +30 |
| policy wonk | 25.3 / 23.0 / 25.9 | 3 / 3 / 3 | |

Kungarna's comps (HoR, Marcella, Prism, Ryth: area stun and stun) punish the hold [measured outcome; the mechanism is
a guess].

### 1.3 Did the band bring more bodies?

Barely [measured]. Within 4 at contact the band rose from 1.46 to 1.51–1.53, and we rose from 1.48 to 1.53–1.60.
Within 8 the band rose from 2.22 to 2.26–2.35. The band's bots are frozen; they react, but no more than our own
presence grew.

## 2. Where the gain leaked

### 2.1 Margin identity, by r600, paired

[measured; `exchange.py` → `out_exchange.txt`]. The identity is collected = captures + kill gems − bags lost.

| Pair | Collected margin | Capture swing (ours / theirs) | Kill / bag exchange | Kill gems, ours / theirs | Bags lost, ours / theirs |
| --- | --- | --- | --- | --- | --- |
| tz-62 − tz-55 | −10.6 ± 21.5 | **+24.2** (+19.8 / −4.4) | **−35.3 ± 14.7** | −10.6 / +8.3 | +8.7 / −7.7 |
| tz-64 − tz-62 | +19.2 ± 20.0 | +9.8 | +9.3 | +2.3 / −2.4 | −4.6 / +0.1 |
| tz-64 − tz-55 | +8.6 ± 22.8 | **+34.0** (+15.1 / −18.9) | **−26.0 ± 13.8** | −8.3 / +5.9 | +4.1 / −7.6 |

By r300 the pattern is the same: tz-64 − tz-55 is a capture swing of +15.1 against an exchange of −12.0.

**Leak 1: the kill / bag exchange** (the largest; it comes with WORK).
- Kills by r600 fall from 2.4 to 2.0–2.1 a game.
- Our bag at death grows from 6.7 to 7.5–8.4 gems.
- The bags lost at mid groups (`dbag_mid`) grow by +3.6 to +8.6.
- The roles study saw kills fall locally too (8.0 → 6.9) but read it as harmless. v93 dies at contacts anyway, so the
  loss cost little there.
- The cause in code: a holder does not assist, by `!(work_hold && !value::P.role_wassist)` (bot.cpp l.3885) [code].
- Per opponent, the tz-64 exchange is:

  | Opponent | Exchange |
  | --- | --- |
  | QS2isLaw | −61 |
  | Team Kungarna | −61 (our bags) |
  | :3 | −36 |
  | Claudus Maximus | +4 |
  | Rogue Lock Pickers | +2 |
  | policy wonk | −4 |

**Leak 2: our own farming time** (`leak.py`).
- tz-64 has −37 body-rounds a game with no enemy within 8 (by r300), −14 camp hits there, and own-third captures
  −11.6 by r600.
- The hold buys about +26 mid gems with about 23 extra contact body-rounds. That is efficient in gems [measured]. So
  this leak is the smaller one.

**Leak 3: the band moves its farming elsewhere.** The band's uncontested captures rise +13 to +16 by r600, which
offsets about half of its mid loss.

**Not a leak:**
- Deaths: +0.1 to +0.2 a game, n.s.
- Gold: gold300 −40 to −57, n.s.
- Team max HP: unchanged.

### 2.2 Where the change lands

[measured; `close.py`] The classes come from all 26 band labels: never won by any build / rare / often.

| tz-64 − tz-55 | Games | Wins | Margin | Mid gems, ours / theirs | Take % |
| --- | --- | --- | --- | --- | --- |
| Never won | 65 | 0 / 0 | +38 ± 24 | **+41 / −41** | 19.2 → 26.7 |
| Rare (< 25 % of builds) | 53 | 14 → 8 | −94 ± 74 | +21 / −18 | 36.8 → 34.3 |
| Often | 32 | 14 → 19 | +194 ± 104 | | |

- In never-won games the gap is ~600 gems, so these gains cannot win games.
- In rare games deaths rose by +0.66.
- Splitting by tz-55's own margin is biased by regression to the mean (the games are chaotic), so I did not use it.

### 2.3 The band A/B cannot see effects this size

[measured flips; the mapping is a guess]

- Between near-identical builds there are 28–37 win flips in 150 games: 18/19 for tz-64 v tz-55, 13/15 for tz-62 v
  tz-55.
- That gives a win-difference SE of about ±6 wins.
- A uniform +25 final-margin shift would turn about 6–9 close losses into wins on paper, but the shift is not uniform.
- The measured +8.6 r600 margin is worth about +1–3 wins [guess]. **"Level" is consistent with the mechanism being
  real and small.**

## 3. Why the hold does not convert against the band

### 3.1 Contacts are decided by the fight, and the band wins it

[measured; `fight.py`, `bothstay.py`]

**Take rate by who lost more bodies near the group in the cycle:**

| Label | They lost more: share (take) | No deaths: share (take) | We lost more: share (take) |
| --- | --- | --- | --- |
| tz-55 band | 13.0 % (52) | 56.8 % (26) | **26.3 %** (17) |
| tz-64 band | 12.5 % (57) | 58.7 % (32) | **24.0 %** (18) |
| B0 local | **27.4 %** (72) | 54.9 % (42) | 12.9 % (38) |
| Q13 local | **24.9 %** (71) | 56.2 % (60) | 14.3 % (38) |

**Both sides stay** (41–49 % of contacts):

| Label | Hits us / them | They out-hit us | Deaths us / them | Take |
| --- | --- | --- | --- | --- |
| tz-62 band | **11.3 / 11.5** (equal effort) | 49 % | 0.57 / 0.27 | 33 % |
| Q13 local | 14.5 / 9.7 | 33 % | 0.37 / 0.60 | 65 % |

- A capture needs 5 rounds of uncontested occupancy, and an enemy in the region resets it [rules, GameRules l.194].
  So equal farming loses when the other side keeps a body in the region and survives.
- After we out-hit, the band contests and steals 27–35 % of the groups. It does this even when our nearest body was
  nearer or tied (18–24 %). The stolen cycles last 18–28 rounds from the last camp's death [measured, `steal.py`].

### 3.2 v93 is the wrong shape of opponent

[measured; `acts.py`, summaries]

| At mid contacts (bodies within 4, 8 rounds) | Ours (band builds) | Band | v93 (loc_27 / loc_30) |
| --- | --- | --- | --- |
| max HP per body | 1,137–1,165 | **1,411–1,487** | 1,174–1,236 |
| Focus per body | 105–109 | **128–130** | 99–104 |
| camp damage per body | 63–110 | **103–108** | 50–59 |
| damage taken per body | 132–144 | 122–140 | **161–174** |
| per body max HP r300 / r600 (whole team) | 1,088 / 1,400 | **1,375 / 2,030** | 1,225–1,267 / 1,604–1,701 |
| bodies (twins = 2) / gold300 | 5.40 / 1,327–1,405 | 4.46 / 1,447–1,469 | 4.45–4.47 / 930–1,120 |

- The band earns our gold, but its gold goes into 4.5 bodies, not our 5.4. That makes each band body 26 % bigger at
  r300 and 45 % bigger at r600.
- v93 earns 20–35 % less gold, so it is only 13–16 % bigger per body.
- The biggest enemy near us is ≥ 1.9× our max HP for 22–24 % of our body-contacts on the band, against 8.8–13.9 %
  locally [measured, `stoprep.py`].

### 3.3 Stop conditions of the hold

`bots/_mid` l.3641–3662, p1 strict. The table shows the first strict stop within 5 rounds of contact, as a share of
our bodies within 4 [measured; `stops.py` / `stoprep.py` → `out_stops.txt`].

| Label | HP < 50 % | Fed (≥ 1.9× within reach + 2) | Damage while outsized | No stop | Stay % when no stop |
| --- | --- | --- | --- | --- | --- |
| tz-55 band | 12.9 | 14.7 | 7.8 | 64.5 | 70 |
| tz-62 band | 13.3 | 15.1 | 8.5 | 63.1 | 74 |
| tz-64 band | 14.1 | 13.8 | 11.5 | 60.6 | **78** |
| loc_30 (v93) | 10.2 | **6.5** | 10.7 | 72.6 | 75 |
| loc_27 (v93) | 14.9 | 9.2 | 13.6 | 62.3 | 70 |

- The gate (P(die) > 0.12) and the execute stop cannot be rebuilt from replays.
- On the band the fed stop fires 1.5–2.3× more often than locally. The other stops fire at similar rates. So the stops
  fire somewhat more often, but they are not why the band wins contacts.
- The bodies the stops release behave sensibly: a fed stop still stays 59–66 % and dies 4–6 %.
- An HP stop dies 19–21 % within 5 rounds. Those are bodies that were low when they arrived: at HP < 40 % at contact,
  32–34 % die [measured, `hprisk.py`].

**What the stops miss** [measured, `hprisk.py`]:

| Local max HP at contact (ours within 6 v theirs within 8) | Share of body-contacts | Dead within 5 rounds (tz-55 / tz-62 / tz-64) | Camp hits (tz-64) |
| --- | --- | --- | --- |
| Theirs ≥ 1.15× | 27–31 % | 4.7 / **8.9 / 8.6** % | 0.50 (tz-62: 0.26) |
| Level | | 6.3 / 3.3 / 4.0 % | 0.58 |
| Ours ≥ 1.15× | | 2.8 / 2.2 / 2.1 % | 0.93 |

- P1's strict mode dropped "local power < 0.8" and "closing while smaller" [code, l.3644–3652]. A holder that is
  outsized now stops only once it is damaged by an enemy in range. The band's casters (Prism, Tavi, Ren, Marcella, all
  at range 4) hit from just outside that check.
- Take by size bucket, tz-55 → tz-64:

  | Bucket | Take % |
  | --- | --- |
  | Bigger | 44 → 52 |
  | Level | 24 → 30 |
  | Smaller | 14 → 18 |
  | More bodies | 43 → 46 |
  | Fewer bodies | 13 → 20 |

  The hold pays everywhere, but most where we out-size the enemy.

## 4. Recommendations

The code is `bots/_mid/src/bot.cpp`. Every change is a generalisable rule.

1. **Workers assist: `role_wassist = 1`** (value.h l.151; used at bot.cpp l.3885).
   - Why: the kill / bag exchange is the measured leak, −26 to −35 a game. On the band, contacts where the enemy lost
     more bodies are taken 52–57 % of the time, against 17–18 % when we lost more.
   - Locally it was +0.8 points with swing +15 (role_build §2), and it gives the kills back.
   - Watch on the band: kills ≥ 2.4 a game, our kill gems ≥ tz-55's 27, our bag at death ≤ 6.7.
2. **End the hold when outsized at the group**, in the strict block (l.3645–3653):
   `if (strict && L.their_mhp >= value::P.work_out_k * L.our_mhp && int(L.ohp.size()) <= L.n_enemy) real = true;`,
   with `work_out_k` 1.15 (new value.h switch). More bodies than theirs keeps the hold: "more" contacts take 43–46 %
   even on the band.
   - Why: holders in that state die 8.6–8.9 % (4.7 % without the hold), hit 0.3–0.5 camps, and cover 27–31 % of
     body-contacts. Smaller-bucket contacts are taken at only 18 %.
   - Expected size [guess]: about half the bag-loss part of the exchange (+4 to +9 gems), plus the released bodies'
     farming (they go to the planner's next job, so they don't walk home).
3. **Bag-aware hold**, at the same place: when outsized (≥ 1.0×) and `me.gems >= 25`, end the hold. The other option
   is to enable p1 bit 32's inverse, a bank trip.
   - Why: our bag at death rose 6.7 → 7.5–8.4 and `dbag_mid` +3.6 to +8.6 [measured].
4. **Keep p3.** On the band it cut steals after we out-hit from 34.9 % to 27.1 %, and lost cleared groups from 12.9 %
   to 10.2 % [measured]. It is the one part that transferred at full local size.
5. **Raise `work_hp` 0.5 → 0.6**: a small effect.
   - At HP 0.5–0.6 at contact, tz-64 bodies die 9.0 % and tz-62 bodies 6.7 % (tz-55: 5.6 %), and they hit 0.53 camps.
   - The sample is n = 89 [measured]. Ship it only with item 2.
6. **Not recommended: lowering `fed_k` for the hold.** Bodies facing a 1.5–1.9× enemy die 6.9 % (tz-64), 1.9 % (tz-62)
   and 3.9 % (tz-55). That is inconsistent, so the evidence doesn't support it.
7. **Structural, beyond the contact mechanism** [measured sizes; the link is a guess]:
   - Our 6-body comp (twins) spreads the same gold as the band over 5.4 bodies. The band's 4.5 bodies are 26–45 %
     bigger each, and at contact our max HP within 6 is 2,480 against their 2,900.
   - No stance rule closes a 20 % size gap in a 5-round uncontested-capture fight.
   - The draft / feed question (fewer, bigger bodies) is where the remaining contact gap lives. Compare planloss §2.4:
     "size explains 4 points". That figure was bucketed at the group level; per body the band is much bigger.

## 5. A local test that predicts the band better

1. **Gate local runs on the exchange, not on contact take.** Paired v v93, require:
   - the kill / bag exchange (`exchange.py` on local summaries) ≥ 0;
   - kills not below the base;
   - the bag at death not above it.

   tz-62's local kill drop (8.0 → 6.9) was the visible warning.
2. **Report the fight balance at contact** (`fight.py`): the shares of "they lost more" and "we lost more".
   - Locally v93 sits at 25–29 / 13–18, the band at 11–13 / 24–26.
   - A change whose local gain comes from the "they lost more" bucket will not transfer.
3. **Build a band-shaped sparring bot.** It is our own code, not v93; `bots/proxy` may already be intended for this
   (no `diag/proxy.md` exists). Calibrate it against these band targets before trusting it:

   | Target (band) | Value |
   | --- | --- |
   | Bodies (twins = 2) | 4.5, e.g. a HoR / Marcella / Vendetta / Vesper + Ryth comp, the most common band comp |
   | Per-body max HP / ours at r300 | ≈ 1.26 |
   | Camp damage per body in 8 rounds of a contact | ≈ 105 |
   | Bodies staying at a contact | ≥ 83 % |
   | Steals after we out-hit | ≈ 30 % |
   | Deaths per both-stay contact, ours / theirs | ≈ 0.6 / 0.3 |

   Accept it only once tz-55 against it reproduces tz-55's band contact KPIs: take ≈ 27 %, they out-hit us ≈ 50 %
   when both stay, fight balance ≈ 13 / 26.
4. **Until it exists, scale the local contact-take gain by about 0.45** (two points: +8.8 → +3.8; [guess]). Judge band
   A/Bs on the r600 collected margin and its exchange split (`exchange.py`, SE ±21–23 gems), not on wins (SE ±6 wins).

## Files

All under `scratchpad/diag/transfer/`:
- `cyc_*.pkl`, `summ_*.pkl`, `stops_*.pkl`, `acts_*.pkl` (`cyc_mid_*` are symlinks to `scratchpad/mid`);
- `out_kpi.txt`, `out_leak_64.txt`, `out_leak_62.txt`, `out_leak_64v62.txt`, `out_exchange.txt`,
  `out_exchange_opp.txt`, `out_close.txt`, `out_stops.txt`, `out_acts.txt`, `out_steal.txt`, `out_xlabel.txt`.

Nothing under `~/tzunami_data` or `bots/` was changed.
