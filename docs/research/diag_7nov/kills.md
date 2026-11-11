# Kill anatomy: how the top 3 get kills, and what tz needs to match them (7 Nov)

**Data:**

- **TOP:** the top team's kills in `top3_6nov`, 150 games.
- **OURS:** our kills v the band in `tz32b_band` + `tz32b_s7`, 120 games.
- **BAND:** the band's kills on us, in the same 120 games.
- **VBAND:** the band's usual ladder opponents' kills on the band teams we face (Kungarna, QS2isLaw, policy wonk,
  RLP, :3, Claudus), from `ukband_6nov`. That is 92 decoded games, added as a control on the victims.

Scripts and outputs are in `scratchpad/diag/kills/` (listed at the end). Tags: [measured] = counted from the decoded
replays; [code] = bots/tz source as it is now; [rules] / [sdk] = GameRules.md / cambc.h; [guess] = an inference.

## 0. Headline

1. **Kills a game** [measured]: TOP **7.44**, OURS **3.28**, BAND 4.82, VBAND **5.73**.
   - The band is not hard to kill: its usual opponents kill 5.73 of its bodies a game, and we kill 3.28.
   - Games against us are quiet. Contact episodes (an enemy body within 5) are 57 a game for us, 82 for the band
     against others and 86 for the top team.
2. **The gap is 70 % volume, 30 % conversion** [measured, `persist.py`].
   - **Volume:** a "first hit" is a champion hit on a body that the same hunter had not hit for 10 rounds. TOP lands
     48.7 a game, we land 27.2 (×1.79).
   - **Conversion:** after a first hit, the body dies within 10 rounds 25 % of the time for TOP and 19 % for us
     (×1.32).
   - **What happens after the first hit is the same:**

     | After a first hit | TOP | OURS |
     | --- | --- | --- |
     | The hunter hits again | 57 % | 61 % |
     | Another hunter joins | 48 % | 48 % |
     | The hunter is within 3 three rounds later | 47 % | 49 % |
     | Target HP lost in 2 rounds | 0.22 | 0.19 |

     So the volume gap comes before the first hit, and the conversion gap comes from what lands with it (stuns and
     bursts).
3. **Most of the missing volume is Marcella and HoR.** First hits a game per drafted body [measured]:

   | Body | TOP | OURS |
   | --- | --- | --- |
   | Marcella | 17.0 | 5.3 |
   | HoR | 8.8 | 3.4 |
   | Vendetta | 7.3 | 4.1 |
   | Cassi | 8.5 | 5.3 |
   | Issac | 5.2 | 3.1 |
   | Vesper | 11.4 | 8.3 |

   - Marcella and HoR are 60 % of the first-hit gap in our comp.
   - **Contact rounds** (an enemy within 3) per body a game: Marcella 93 v 37, HoR 71 v 35.
   - Our Vesper takes part in as many kills as theirs (2.38 v 2.36 a game). Our kills are Vesper's.
4. **Their stuns set up kills; ours cover a retreat** [measured]:
   - A stun-type hit (Cassi or Prism stun, Ryth area stun, HoR's landing dash) lands in **4.14 of their 7.44 kills a
     game v 0.95 of our 3.28**.
   - **HoR:** our HoR casts its dash with an enemy within 4 4.9 times per HoR game; **66 % move away and 22 % land on
     a champion**. Theirs: 11.2 per HoR game, **66 % on a champion**, 53 % toward the enemy.
   - **Cassi:** our Cassi stuns while stepping away 66 % of the time (theirs 27 %). Her stuns are followed by an
     ally's hit within 2 rounds 33 % of the time (theirs 42 %), and the target dies within 3 rounds 4 % of the time
     (theirs 11 %).
5. **Four patterns make up 93 % of the top team's extra kills** (exclusive classes, §2):

   | Pattern | TOP v OURS (a game) | Share of the 4.16 gap |
   | --- | --- | --- |
   | Recall pick | 1.69 v 0.31 | 33 % |
   | Converge gang | 2.08 v 1.10 | 24 % |
   | Stun-burst | 0.82 v 0.08 | 18 % |
   | Fed-carry solo one-round kill | 1.81 v 1.04 | 18 % |

   - Chasing down a fleeing body is level (0.80 v 0.68): we chase as well as they do.
   - **The recall pick depends on the victims.** The band keeps a recall near us only 6.1 times a game; the top's
     victims do it 23.2 times. Its real upside against the band is small (§3A).

## 1. Method

**Kill records** (`extract_kills.py`):

- **Death and killer:** a champion alive at snapshot D and dead at D+1 died in round D. The killer is the enemy whose
  gold rose by 100 or more that round [rules: a kill pays 100 gold].
- **Twins:** Cassi and Issac dying together count as one event, with the bags summed [rules].
- **Camp kills** (no champion hit in the last 5 rounds and no killer) are dropped.
- **Hits:** basic attacks, damage, area and stun casts, plus HoR's landing dash (`at` 6 by HoR, radius 1 around the
  landing tile). Each is resolved against live positions step by step.
- **Engagement start (es):** the earliest hit on the victim, chained backwards with gaps of at most 4 rounds.
  **Attackers** are every enemy that hit it from es on, plus the killer.

**Per kill:**

- **Victim:** type, max HP, HP path over the 10 rounds before death, HP at es.
- **Attackers:** their types and max HP; each one's distance to the victim at es−10, es−5 and es; the tiles it walked
  in the 10 rounds before; whether it was hitting camps or other bodies before; when it joined.
- **Opener:** the first hit's kind and type; whether a stun-type hit or a stun buff landed.
- **Duration:** rounds from es to death.
- **Victim state:**
  - **Fled:** at least 2 steps away from the nearest attacker, and more steps away than toward.
  - **Kept recall:** a recall start whose next own turn has no cancel, no action and no stun, excluding the death
    turn (the death study's rule).
  - **Farming:** hit a camp in es−5 … es.
  - **Alone:** no ally within 5.
  - **Tributing.**
- **Context:** the bag, the round, and the map third seen from the victim's spawn.

**Opportunities:** an episode starts when an enemy body (more than 4 tiles off its spawn) enters a state:

- alone with 2+ hunters within 7;
- alone with 1 hunter within 5;
- outnumbered by 2+ within 6;
- below 40 % HP with a hunter within 6;
- starting a kept recall with a hunter within 6;
- hitting a camp with a hunter within 6.

For each episode: how many hunters hit it within 5 rounds, the first-hit delay, whether a stun landed, and whether it
died within 10 rounds.

**Checks:**

- Kills a game minus camp kills match the death study: BAND 4.82 = our 5.42 deaths − 0.61 camp deaths [measured].
- The kept-recall rule was tightened twice, because pre-recall turns and the death turn inflated it. The counts still
  carry the death study's caveat for bots that idle with a recall running.

## 2. The anatomy (kills a game unless marked)

### 2.1 Shape of a kill

| | TOP | OURS | BAND (on us) | VBAND |
|---|---|---|---|---|
| kills | **7.44** | **3.28** | 4.82 | 5.73 |
| median rounds, first hit → death | 3 | 4 | 3 | 5 |
| dead in the first-hit round / the next | **1.35 / 1.03** | 0.48 / 0.28 | 1.23 / 0.72 | 0.96 / 0.61 |
| 1 / 2 / 3 / 4+ attackers | 3.31 / 2.20 / 1.27 / 0.65 | 1.70 / 0.79 / 0.56 / 0.23 | 2.73 / 1.40 / 0.54 / 0.14 | 2.38 / 1.70 / 0.89 / 0.76 |
| victim HP share at first hit (median) | 0.87 | 0.85 | 0.87 | 0.88 |
| victim max HP (median) | 1200 | 1500 | 1000 | 1400 |
| killer / victim max HP (median) | 1.61 | 1.49 | 1.79 | 1.44 |
| attackers' summed max HP / victim's (median) | 2.85 | 2.35 | 3.00 | 2.67 |
| victim alone | 2.83 | 1.83 | 2.01 | 2.00 |
| victim fled | 2.65 | 1.51 | 1.43 | 2.11 |
| victim in a kept recall | 1.69 | 0.31 | 1.73 | 1.13 |
| victim farming | 1.02 | 0.53 | 0.38 | 0.75 |
| **stun-type hit in the engagement** | **3.78** | **0.73** | 2.28 | 2.41 |
| … as the opener | 1.63 | 0.13 | 1.27 | 1.00 |
| ≥ 1 attacker came from ≥ 8 tiles (10 rounds before) | 4.87 | 2.18 | 3.18 | 3.79 |
| attackers hitting camps in the 10 rounds before (share) | **29 %** | **16 %** | 23 % | 27 % |
| bag gems a game | 93 | 42 | 67 | 69 |
| r < 300 / 300–800 / 800+ | **1.83** / 3.65 / 1.95 | 0.54 / 1.80 / 0.94 | 1.05 / 2.11 / 1.66 | 1.11 / 2.64 / 1.98 |
| victim's own third / middle / far third | 1.54 / 5.65 / 0.25 | 0.38 / 2.54 / 0.36 | 0.81 / 3.67 / 0.33 | 0.66 / 4.58 / 0.49 |

The victim's HP path is the same for every group: a median of 0.87 → 0.57 → 0.28 → 0.14 at 10, 4, 1 and 0 rounds
before death.

### 2.2 Who opens a kill (opener, a game)

| | basic melee | basic ranged | damage spell | HoR dash | stun (Cassi) | stun + damage (Prism / Ren / Tavi) | area |
|---|---|---|---|---|---|---|---|
| TOP | 2.18 | 2.13 | 1.11 | **0.74** | 0.44 | 0.37 | 0.38 |
| OURS | 0.84 | 1.74 | 0.56 | **0.05** | 0.08 | 0 | 0 |

Openers by type (a game): their Marcella 1.36 v ours 0.49, HoR 1.03 v 0.23, Cassi 0.92 v 0.28, Vendetta 0.86 v
0.33. Our Vesper opens 1.74 v their 1.52 [measured].

### 2.3 Exclusive patterns (first rule that applies; `patterns.py`)

| Pattern (rule) | TOP | OURS | gap | share | BAND | VBAND | TOP: median dur / attackers / victim HP / bag |
|---|---|---|---|---|---|---|---|
| **A recall pick** (victim in a kept recall in es−3 … D−1) | 1.69 | 0.31 | +1.39 | 33 % | 1.73 | 1.13 | 5 / 2.1 / 0.83 / 17 |
| **B stun-burst** (stun-type hit or stun buff, dead within 2 rounds) | 0.82 | 0.08 | +0.74 | 18 % | 0.46 | 0.37 | 1 / 1.7 / 0.61 / 12 |
| **C converge gang** (2+ attackers, ≥ 1 from ≥ 8 tiles 10 rounds before) | 2.08 | 1.10 | +0.98 | 24 % | 0.85 | 1.82 | 6 / 2.7 / 0.97 / 11 |
| D chase-down (victim fled) | 0.80 | 0.68 | +0.12 | 3 % | 0.31 | 0.74 | 6 / 1.5 / 0.87 / 9 |
| E local gang (2+ attackers, all near) | 0.24 | 0.07 | +0.17 | 4 % | 0.07 | 0.22 | |
| **F solo duel** (1 attacker) | 1.81 | 1.04 | +0.76 | 18 % | 1.40 | 1.46 | 0 / 1.0 / 0.74 / 11 |

**What each pattern looks like for TOP** [measured]:

- **A, recall pick:**
  - The victim is at 0.83 HP; 2.1 attackers, one from 10+ tiles.
  - **The victim is stunned in 79 % of them**, since a stun interrupts a recall [rules].
  - It takes 5 rounds; 46 % of victims flee after the recall breaks.
  - Openers a game: melee 0.40, ranged 0.36, HoR dash 0.34, Cassi stun 0.19 (ours: 0.09 / 0.07 / 0.02 / 0.01).
- **B, stun-burst:**
  - The victim is at 0.61 HP when the stun lands; 1.7 attackers; the second hits 1 round after the first.
  - It is over in 1 round: victims flee in 2 % of them.
- **C, converge gang:**
  - The victim is at full HP (0.97); 2.7 attackers. The farthest was 14 tiles away 10 rounds before the first hit.
    The second attacker hits 1 round after the first.
  - **35 % of the attackers were hitting camps in the 10 rounds before (ours 17 %)**: the top's bodies leave their
    camps to join.
  - Victims are stunned in 66 % of them (ours 48 %). It takes 6 rounds; 51 % of victims flee.
- **F, solo duel:**
  - A fed carry (median 3,200 max HP; killer / victim max HP 2.95) kills a body at 0.74 HP in the round of the first
    hit.
  - Their solo killers: Vesper 143, Marcella 97, Vendetta 59, Prism 53, HoR 32.
  - Ours: **Vesper 150, Marcella 25, Vendetta 16, HoR 1**. Our Vesper does this as often as theirs; our Marcella
    does it 0.25 times per Marcella game to their 1.43.
  - Our solo victims were already at 0.49 HP: we finish damaged bodies, while they one-round healthy ones.

### 2.4 Opportunities and conversion (`opps.py`, `convert.py`)

| State (episodes a game / P(kill within 10)) | TOP | OURS | BAND | VBAND |
|---|---|---|---|---|
| enemy within 5 of a hunter | 85.7 / 7 % | 57.1 / 4 % | 64.4 / 7 % | 82.2 / 4 % |
| alone, 2+ hunters within 7 | 24.4 / **12 %** | 21.9 / **6 %** | 18.1 / 9 % | 24.7 / 8 % |
| outnumbered by 2+ within 6 | 11.5 / **22 %** | 7.1 / **12 %** | 3.5 / 20 % | 9.5 / 17 % |
| below 40 % HP, hunter within 6 | 14.7 / 40 % | 8.8 / 32 % | 9.1 / 40 % | 16.1 / 28 % |
| starts a kept recall, hunter within 6 | 23.2 / 10 % | **6.1** / 6 % | 11.9 / **23 %** | 14.8 / 8 % |
| hits a camp, hunter within 6 | 22.1 / 5 % | 17.8 / 2 % | 6.8 / 4 % | 21.3 / 4 % |

**Inside "alone, 2+ hunters within 7"** (TOP v OURS) [measured]:

| | TOP | OURS |
| --- | --- | --- |
| Episodes a game | 24.4 | 21.9 |
| Hunters hit it at all | 42 % | 35 % |
| P(kill) when 1 hunter hits | 18 % | 11 % |
| P(kill) when 2+ hunters hit | 39 % | 29 % |
| P(kill) when a stun lands | 26 % | 13 % |
| P(kill), first hit in the entry round | 28 % | 23 % |
| P(kill), first hit 1–2 rounds later | 24 % | 13 % |
| P(kill), hunters within 7 sum ≥ 2× its max HP | 17 % | 12 % |
| P(kill), hunters within 7 sum < 1.5× its max HP | 4 % | 1 % |
| Episodes a game with a sum < 1.5× | 4.8 | **8.2** |

So we see as many lone enemies, and more of ours are too small to kill them.

**Inside "outnumbered by 2+"** [measured]:

| | TOP | OURS |
| --- | --- | --- |
| P(kill) when 2+ hunters hit | 43 % | 26 % |
| P(kill), first hit in the entry round | 39 % | 27 % |
| P(kill), first hit 1–2 rounds later | 29 % | 11 % |
| P(kill), first hit 3–5 rounds later | 17 % | 12 % |
| P(kill), its HP < 0.5 | 60 % | 34 % |

**Ability use with an enemy champion within 3** (per body, `convert.py`; per drafted game where marked) [measured]:

| Body | TOP | OURS |
|---|---|---|
| HoR: contact rounds | **71** | **35** |
| HoR: slot ready (shield / dash) | 19 / 19 % | 18 / 21 % |
| HoR: champion-hitting casts per 100 contact rounds | 7.6 | **3.6** |
| HoR: stun-type hits on champions a game | **6.75** | **1.01** |
| HoR: … followed by an ally's hit within 2 rounds / target dead within 3 | 37 % / 19 % | **72 % / 24 %** |
| Cassi: stun casts a game | 8.2 | 5.9 |
| Cassi: … followed / dead within 3 | 42 % / 11 % | 33 % / **4 %** |
| Cassi: damage casts in contact a game | 6.8 | **2.3** |
| Marcella: contact rounds | **93** | **37** |
| Marcella: damage spell in contact, per Marcella game | 18.5 | **5.4** |

Casts with an enemy within 4 (`castctx.py`) [measured]:

| Cast | TOP | OURS |
| --- | --- | --- |
| HoR dash | 66 % land on a champion; 53 % toward / 28 % away | **22 % on a champion; 33 % toward / 66 % away** |
| Cassi stun: caster stepping away | 27 % | **66 %** |
| Vendetta dash | 46 % away | 60 % away |
| Vesper dash | 53 % away | 48 % away |

When our HoR does land on a champion, it converts better than theirs (72 % follow-up, 24 % dead within 3). It lands
1/7 as often.

## 3. The patterns, whether tz does them, and why not

### A. Recall pick (33 % of the gap, but victim-dependent)

- **Measured:**
  - The band starts kept recalls near us 6.1 times a game, near its usual opponents 14.8 and near the top team's
    victims 23.2. We are rarely close enough.
  - When it happens, we hit the recaller 28 % of the time (TOP 40 %, the band on us 66 %). P(kill) is 6 % for us,
    10 % for TOP and 23 % for the band on us.
  - The top's recall picks stun the victim in 79 % of them.
- **[code] tz never looks at an enemy's channel:**
  - `assess()` scores targets by `(kill + gems) / (rounds + gap + 1)`, with focus fire ×3.
  - `EnemyMem` has no recall flag, and nothing reads `champion::is_recalling()` on an enemy. The method exists
    [sdk: cambc.h:3767]; whether it reads true on a visible enemy is [guess, check first].
  - A recalling enemy is priced like any other, so the stance block commits only on `sim_win` / `quick_kill`.
- **[guess] upside v the band:** 6.1 × (0.10 − 0.06) ≈ +0.25 a game at today's contact levels. More if contact rises.

### B. Stun-burst (18 %), and stuns in every other pattern

- **Measured:** see §2.4. Our HoR's dash is mainly a flee tool (66 % away), and our Cassi's stun mainly covers a
  retreat (66 % stepping away).
- **[code] Why the HoR dash rarely hits a champion:**
  - `act_fight` uses a dash only to close the gap when the target is out of reach, picking the tile nearest the
    target.
  - Before that, the "hit whoever is in reach now" loop returns as soon as any enemy is adjacent, so an adjacent HoR
    never casts its 1.75 × Focus + stun landing [rules]. `cast_at` skips dashes.
  - `act_flee` spends any ready dash *away* when an enemy is within 4 ("a dash first, when someone is close"), and HoR
    gets no exception.
  - **`execute_target()` → `burst_on()` counts the landing dash within 3 tiles**, so the execute check commits on
    damage that `act_fight` will not cast when adjacent [code]. It is a bug-shaped inconsistency.
- **[code] Why Cassi's stun covers a retreat:**
  - `act_flee` → `stun_chaser()` (`flee_hits 1`) stuns the nearest chaser while running.
  - In a fight, `cast_at` takes abilities in slot order: Cassi's slot 0 damage spell goes first if ready and she has
    not moved, and the stun only if the damage spell is not available.
  - Nothing picks the stun for the target the team can follow up on.
  - `stun_focus` (commit to a stunned enemy) exists and is off: 52.3 % v v93, not kept, but tried while few stuns
    landed.

### C. Converge gang (24 %)

- **Measured:**
  - Outnumbered-by-2 episodes: 11.5 v 7.1 a game; P(kill) 22 % v 12 %.
  - A delay is costly for us: a first hit 1–2 rounds after the entry gives 11 % (TOP 29 %).
  - The top's joiners leave camps: 35 % of their converge attackers were farming in the 10 rounds before (ours 17 %).
  - We meet 8.2 lone enemies a game with too little near (summed max HP < 1.5×; P(kill) 1 %), and the top only 4.8.
- **[code] What exists:**
  - `assist` joins a teammate's comms FIGHT target only when it is **visible to me this round within `assist_r` 7**.
    The top's converge kills draw from 14 tiles (median farthest 10 rounds before), and vision is not shared [rules],
    so a farming body 9–14 tiles away cannot join.
  - The commit rule is the exchange sim (`L.sim_win`: kill them all, and I am neither the first of us to fall nor
    dead). An even 1v1 never commits, and a 3v1 commits only if every body survives.
  - `commit_outnumber` (one more body than them) lost v v93 (47.7 %). The data favour a stricter trigger (+2 bodies
    and 2× the max HP).
- **Not tried in this form:** a kill beacon in comms; "first hit this round" priority.

### D. Chase-down (3 %)

Level (0.80 v 0.68 a game). Vesper's kiting chases well: 0.54 chase kills a game open with a ranged hit, theirs
0.27. No change [measured].

### F. Fed-carry solo (18 %)

- **Measured:** our Vesper matches theirs (1.25 solo kills a game). The gap is **Marcella (0.25 v 1.43 per Marcella
  game)** and Prism, which we don't draft.
- **[code]:** `feed 1` makes Marcella and HoR supports. The economy study found HoR gold at r300 75 v 229, and
  supports buy Focus, not HP.
- This is economy and draft, not bot.cpp micro. Feeding pays on the band (`feed 0`: gold300 −154), so the lever is
  `feed_until` / supports keeping captures, already on the build-log list. No new micro rule.

### The volume gap behind all of them

- **[measured]** Marcella and HoR are in contact a third to a half as often as the top's (37 v 93, 35 v 71 rounds a
  game).
- **[code]** Two rules keep them out:
  - The fed break: within an enemy's reach + 2 when it has 1.9× my max HP, break.
  - The exchange sim decides the stance: with `break_closing 0`, any contact without a winning sim is a BREAK.
- **[guess]** The supports stay near base HP (HoR ~1,000–1,200), so the sim and `fed_k` keep them away.
- More contact alone has lost every time (`fight_mode 1`, `engage_mode 1`: deaths +3.2 on the band). **So the changes
  below raise what each contact yields; they do not ask for more contact**, except #3, which is narrow.

## 4. Proposed changes (decision rules, thresholds from the data, where in bot.cpp)

| # | Change | Where | Rule | Evidence | Expected [guess] |
|---|---|---|---|---|---|
| 1 | **HoR landing dash as the opener / finisher** (switch `land_fight`) | `act_fight` (new `landing_dash_champ()`, modelled on `landing_dash(const Group&)`); `act_flee`'s "dash first" block | (a) Fight: before `cast_at` / `swing`, if a dash with `modifier > 0` is ready and a visible enemy off its spawn is within `range + radius` (3), take the free landing tile within the dash range that hits the stance target (radius 1). Prefer most enemies hit, then the lowest summed HP, then the least `micro_eval` danger. Cast it, then swing + reset (dash is walk-compatible [rules]). Also when already adjacent: today the in-reach branch never dashes. (b) Flee: a HoR at ≥ 0.4 HP keeps its dash unless a landing hits the nearest chaser (it stuns it [rules]); below 0.4 HP flee as now. | Their HoR lands 7.4 champion dashes per HoR game, ours 1.1. 66 % of ours go away. Ours convert at 72 % follow-up and 24 % dead within 3. Makes `burst_on`'s dash term honest. | +0.3 to +0.6 kills a game; deaths ~0, since HoR's flee loses the 2-tile dash only above 0.4 HP |
| 2 | **Cassi stuns for the kill, not the run** (`stun_setup`) | `stun_chaser()`; `cast_at` (ability order for bodies with both a damage and a cc slot) | (a) `stun_chaser` only when my HP < 0.5, or the chaser is within `reach_of()` of me and `find_escape()` finds no way out. Otherwise keep the stun. (b) In a fight, cast the stun first when another of our bodies is within its range + 1 of the target this turn, or the target is channelling (#4) or below 0.5 HP. Otherwise cast damage. | Our stuns: 66 % cast while stepping away, 33 % followed, 4 % dead within 3 (TOP 27 % / 42 % / 11 %). TOP converts 26 % of lone-enemy episodes with a stun v our 13 %. Cassi damage in contact 2.3 v 6.8 a game. | +0.3 to +0.5 kills a game. Small risk to twin deaths (1.85 a game), so keep (a)'s low-HP exception |
| 3 | **Outnumber-2 commit, hit this round** (`gang2`) | `play_turn` stance block (beside `commit_outnumber`); comms FIGHT post | Commit on a visible enemy off its spawn when all of these hold: our visible bodies within 6 ≥ its side within 6 + 2; our summed max HP within 7 ≥ 2.0× its max HP; my HP ≥ 0.5; and no enemy with ≥ 3× my max HP within 8 (the fed break stays). Hit it this turn if in reach, with spells before steps (`spell_first`). Post FIGHT so `assist` joins. | Outnumbered-2: P(kill) with a first hit in the entry round 39 % (TOP) / 27 % (ours); 1–2 rounds late 29 % / 11 %. Below a 1.5× summed max HP P(kill) is 0–2 %, so the 2× gate. `commit_outnumber` (+1) lost; this is +2 and HP-gated. | +0.3 to +0.6 a game. Deaths: the band's counter-kill risk in 3v1 is low, but judge it on the band, since v93 disagreed before |
| 4 | **Recall-aware target** (`recall_pick`) | `World` / `EnemyMem`: a `recalling` flag set from `e.h.is_recalling()` when seen, kept only if it was also set at the previous sighting on the same tile (the band pre-starts a recall every turn [measured, README]); `assess()` target score; stance block | A kept-recalling enemy within my reach + 1 off its spawn: score ×2. Commit when `!low` and the sim is not a clear loss (ratio ≥ 0.7, like `assist_ratio`), because it gets no action until damaged [rules]. Stun first (#2b). Never walk into its spawn region. | The band keeps 6.1 recalls a game near us; we hit 28 % of them and kill 6 %. TOP hits 40 % and kills 10 %; the band hits 66 % of ours and kills 23 %. 79 % of TOP's recall picks stun the victim. | +0.2 to +0.4 a game. Verify `is_recalling()` on enemies with a one-map probe first [sdk unknown] |
| 5 | (later) **Kill beacon** for far joiners | comms bytes 6-7 (shared with `big`), `assist` | When a body commits under #1–#4 and no ≥ 3× `big` sighting is fresh, write the target tile (x/2, y/2, 2-bit age). Bodies at ≥ 0.6 HP farming within 12 with no fed enemy near walk to it for at most 6 rounds. | TOP's converge attackers came from 14 tiles (median farthest); 35 % were farming before (ours 17 %); the second hits 1 round after the first. Rally (bytes 6-7, early-game only) lost v v93; this fires on a committed kill, not on any sighting. | uncertain; only after #1–#3 hold |

**Order.**

1. **#1 and #2 first.** They change no fight decision, only which tool is used in fights we already take. #1 also
   fixes the `burst_on` / `act_fight` mismatch.
2. **Then #3**, a narrow stance trigger.
3. **#4 needs the SDK check.**
4. **#5 only if #3 shows** that joiners are the limit.

**Thresholds to put in `value.h` for SPSA:**

| Parameter | Value |
| --- | --- |
| `land_hp` | 0.4 |
| `stun_keep_hp` | 0.5 |
| `gang2_n` | 2 |
| `gang2_mhp` | 2.0 |
| `gang2_hp` | 0.5 |
| `recall_k` | 2.0 |

**Targets to check on a band stage** (all [measured] here):

| Metric | Now | Target |
| --- | --- | --- |
| HoR champion-landing dashes per HoR game | 1.1 | ≥ 5 (TOP 7.4) |
| Cassi stun followed by an ally within 2 rounds | 33 % | ≥ 40 % |
| Cassi stun: target dead within 3 rounds | 4 % | ≥ 10 % |
| Outnumbered-2 P(kill) | 12 % | ≥ 18 % |
| Stun-type hit in kills, a game | 0.73 | ≥ 2.0 |
| Kills a game | 3.28 | ≥ 4.5 (VBAND 5.73) |
| Deaths | | must not rise |

`castctx.py`, `convert.py` and `persist.py` measure them from any decoded label.

## 5. Caveats

- **Different victims.** The top team's victims (Ad Astra, Vvvvv, BattleCats and other top teams) are not the band.
  VBAND (the band v its usual opponents: 5.73 a game) shows the band is killable. The pattern shares for TOP mix the
  top's skill with its victims' habits, most of all the recall pick.
- **Hit resolution.** Area hits use radius 1 around the target tile [guess on the radius]. HoR's dash damage is
  resolved at its landing tile. Vesper, Vendetta and Issac dashes do no damage [rules] and are not hits.
- **Stun counts.** The stun buff (type 1) is read from round snapshots. A one-round stun can fall between snapshots,
  so "stunned" undercounts; the stun-type *hit* count does not.
- **Kept recall.** Detection follows the death study and stays noisy for bots that idle with a recall running.
- **Causality.** Conversion rates are conditional, not controlled (e.g. a first hit in the entry round may reflect a
  better spot). The expected gains are [guess]; only band A/B decides.
- **Earlier losses.** More engagement lost v v93 and on the band. The proposals avoid adding contact except #3, whose
  gates come from where P(kill) is high.

## Scripts (`scratchpad/diag/kills/`)

| Script | What it does |
| --- | --- |
| `extract_kills.py LABEL OUT.json` | Kill records (both teams); opportunity episodes with conversion and closing; ability readiness and casts in contact by type; stun-hit follow-up. Run on `top3_6nov`, `tz32b_band`, `tz32b_s7`, `ukband_6nov`. |
| `anatomy.py` | §2.1–2.2 (`out_anatomy.txt`) |
| `patterns.py` | Flags, exclusive patterns and per-pattern detail (`out_patterns.txt`) |
| `opps.py` | Opportunities, conversion and closing (`out_opps.txt`) |
| `convert.py` | Conversion by hitters / stun / timing, ability use in contact, stun follow-up (`out_convert.txt`) |
| `castctx.py` | What HoR's dash, Cassi's stun and damage, Marcella's damage and the dashes are used for with an enemy within 4 (`out_castctx.txt`) |
| `persist.py` | First hits a game, follow-through, first hits by drafted body (`out_persist.txt`) |
