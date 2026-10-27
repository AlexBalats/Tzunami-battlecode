# What to copy from the top teams: the plan for p8 (written 23 Oct, adjusted 24 Oct after p7)

For the main session. It comes from reading **78 wins of three top teams** and setting their numbers beside our own
(cpp-p6's 38 ladder losses, measured with the same scripts). The evidence, game tables and method are in
`docs/archive/TOP_TEAMS.md`; the § numbers below point there. No bot code was changed in this study.

The three teams:
- **Team 1**: a fixed Prism draft (Prism, Vesper, Marcella, Willow, Heart of Ruin);
- **Team 2**: a different draft every game;
- **Team 3**: a fixed draft with no Prism (Vesper, Vendetta, Heart of Ruin, Tavi, Marcella).

The user's constraints:
- We don't run Prism, so nothing that needs Prism is in this plan (Prism's 500-gem hoard is team 1's alone).
- Don't copy any team one-to-one: take the habits all three share.
- Generalise: every rule reads the game state (score, bags, walks, HP, cooldowns), never a map name or a
  coordinate (CLAUDE.md rule 10). The 78 wins span 34 of the 40 pool maps, from 30×30 to 100×100.

Tags as in CLAUDE.md. Our numbers are from losses and theirs from wins, so part of every gap is the result itself. The
items below are the gaps too big to be only that (TOP_TEAMS §11).

**Adjusted after p7 (LADDER_P4 §10.3)**: three of this study's ideas were already tried while it ran.
- Banking every ~15 gems (`_bk`, order size) lost: farm time lost.
- Bank when score + bag ≥ 1,000 (`_bkw`, the closing rule) was level vs cpp-p6 (49.1 %).
- Varg → Marcella without her kit lost (35.3 %).

So the untested items go first. The bar is now **cpp-p7**: a piece goes in only if it beats cpp-p7 head to head (and
holds against spar-meta).

## The plan, in order (untested and cheap first)

### 1. Use every ability on cooldown (all three teams; untested)

**Facts** [measured, §11]:

| Per 100 live rounds | Ours | Theirs |
| --- | --- | --- |
| Vesper, all casts | 6.4 | 12.1–12.7 |
| Vesper's dash | 2.9 | 7.3–7.4 |
| Vendetta, all casts | 7.6 | 10.7–12.7 |
| Ren | 4.1 | 12.0 |
| Ryth | 3.5 | 8.7 |
| Varg | 5.2 | 14.8 |

Vendetta's passive resets all her cooldowns on every kill, monsters included [rules], so hers should fire on almost
every camp.

**Ours**:
- `nav.cpp` L4: the travel dash runs only in `Fast` mode, only after `DASH_QUIET` (8) quiet rounds, and **never for
  Vesper or Ren while carrying** (`!(s.bag > 0 && (my_id == 1 || my_id == 8))`).
- On camps, `beh.cpp` farm: `if (t && !KIT.reset_attack(w, s, *t)) KIT.cast_camp(w, s, *t)`, inside `if (!kit)`.
  Check how often that path runs.

**Rule**:
- Dash on every cooldown while walking. Keep the dash for escape only when an enemy is in sight, not because of the
  bag.
- Reset or cast on camps on every cooldown.

**Measure**: casts per 100 live rounds per champion (the query in TOP_TEAMS §11), trip rounds, deaths while carrying.

### 2. Hit camps more of the time (all three teams; diagnose first)

**Facts** [measured, §11]: camp hits per 100 live body-rounds are **9.3 for us** against 18.3 / 16.2 / 16.5 for the
three teams. Even the opponents who beat us manage 13.4. This is the biggest single gap and the most general one.

**Ours**: p7's idle-crew heal (§10.4) may already close part of it. Measure p7 first (arena run →
`arena_decode.sh` → the §11 query), then trace the rest with `timeuse.py` / `stuck.py`. Candidates:
- standing at a respawning group's Ring (`WAIT_MAX 15`, `prices.h`);
- the crew in Fall with no farm price above 0 (`need_k`);
- long walks.

**Measure**: make camp hits per 100 live body-rounds a standing KPI. The target is ≥ 15.

### 3. Lock the altar yourself just before tributing (teams 1 and 3; untested)

**Facts** [measured]:
- Team 1: 68 locks, about half 0–1 rounds before its own tribute.
- Team 3: 152 locks, 93 within 6 rounds of the same body's own tribute.
- Only 11 of 220 were placed while an enemy was tributing nearby. Team 2 never locks.

[rules/sdk] An altar holds one lock (`invalid_action_altar_lock_already_locked`). Our own lock blocks enemy tributes
there and stops an enemy lock from cancelling our channel; only a stun can still cancel it.

**Ours**: `champs.cpp` `buy_all` buys a lock (`LOCK_GOLD 40`), and nothing ever places it.

**Rule**: in `bank` (`beh.cpp`), within 2 tiles of the altar, holding a lock and the altar unlocked → place it, then
tribute. Use `consumables()[altar_lock]`; check its signature in `cambc.h`.

**Measure**: tributes cancelled; enemy tributes at our altars.

### 4. Start the fights, on the nearest enemy you outweigh (all three teams; check first)

**Facts** [measured]: they start most fights (199 of 290; 361 of 523; 423 of 739) and win the kills 154–72, 331–98,
455–123. At the opening hit:
- the opener's max HP is a median **1.13–1.15×** the target's;
- both sides are near full HP;
- the opener's side is even or ahead within 5 tiles (246 of 277 in team 3);
- the target is the **nearest** enemy 88–92 % of the time; the lowest HP only at chance.

Team 1's fight edge is not Prism's: without Prism nearby it won 91–24 (TOP_TEAMS §3). In p6's losses the enemy opened
more fights than we did (10.0 vs 8.1 a game). This matches HANDOFF next item 4: "fights they start".

**Ours**: the `duel` P(lose) gate and `KILL_PLOSE` 0.6 (`prices.cpp`).

**Check first**: on an arena run, how often does our gate refuse an even 1v1 where we hold ≥ 1.13× the enemy's max HP?
If it refuses often, loosen the gate for that case; if not, the gap is elsewhere (being there, items 1–2).

**Measure**: fights opened a game, kills and deaths (`fights.py`), deaths a game.

### 5. Marcella, with her kit this time (all three teams draft her)

**Facts** [measured]:
- Marcella is in every team-1 game, 14 of team 2's 24, and every 5-body team-3 game.
- In teams 1 and 2 she's the top gold earner (her passive pays 2 gold per gem tributed); she tributes ~10 times a
  game and almost never dies.
- **Heart of Ruin is in 78 of 78 winning drafts.** Varg is in 6 of team 2's 24 and nowhere else.

**Ours**: Varg, Vesper, Ren, Ryth, Vendetta (`draft.h`). `_mv` (Varg → Marcella, `PICKS` only) lost 35.3 % because
nothing in the code plays her.

**Do**: the Marcella spec in TOP_TEAMS §8 (both teams' Marcellas measured; `docs/CHAMPIONS.md` checklist):
- raise her bank weight (`base_row` 0.8 → above average);
- add the tribute-gold term (bag × 2 gold) to her Bank price;
- a Strength-first build (Treasure / Jungle Strength), then Health (team 2: 2,700 max HP at r300) or Bruiser
  Strength (team 1);
- let slot 1 (2 × Focus, range 4) open fights from range 4;
- slot 0 (reset + stunning hit) on camps on every cooldown, as theirs.

Then judge the swap alone. Heart of Ruin already has an `fkit` row (LADDER_P4); it's the next candidate, one swap at a
time.

### 6. Banking: on the way and on the way home, not just more often

**Facts** [measured]:
- They make 29–32 tributes a game at a median bag of 21–26. We make 15 at a median bag of 15.
- Team 3 banks next **93 % of the time once the bag is ≥ 50**.
- But `_bk` (bank every ~15 gems) lost: farm time lost.

The difference [measured, team 1 §2]: 245 of 540 of their capture → tribute trips went **through spawn** (recall,
heal, shop, then the altar), and the rest walked a median of 7 rounds. Their tributes are folded into trips they make
anyway.

**Rule** [guess]: when a body recalls to heal or shop with gems in its bag, its next leg is the altar nearest to spawn
on the way back out (`bank_altar` with the spawn as the start). Plus "bag ≥ ~50 → bank" as a ceiling.

**`_bkw`** (the closing rule) was level vs p6. It fixes ladder-only hoard losses (8 of 38) that self-play rarely
shows, so consider bundling it with a winning piece.

**Unknown**: whether `gem_count()` works on an out-of-vision ally from `cambc::champions(team::ally)` [sdk returns
every handle]; if it does, the closing rule can count the whole team's bags.

### 7. Optional, one team only

- **Teleports** (team 2 only): 218 jumps on 5 wall / river maps, median 78 tiles saved. Teams 1 and 3 won those maps
  without it. It matches HANDOFF next item 2 (the jump fed into the farm walks).
- **Pre-charged recall** (team 1 only): end every turn with a recall started, cancel it next turn. One turn off every
  recall [rules: the starting turn counts].

**Not gaps** [measured, §11]:
- wards (we place 169 a game, they 88–431);
- recall HP (we 0.45, they ~0.40);
- spreading out;
- fuel (team 2 rolls over 21 times a game and still wins).

## Judging

As CLAUDE.md rule 5: each item alone, against **cpp-p7** and **spar-meta**, 8 jitters each (`OPP=cpp-p7 sh
tools/jitter.sh <bot>`, `OPP=spar-meta …`). It goes in only if it beats cpp-p7. On top, track the KPIs from this study:
- camp hits per 100 live body-rounds (item 2);
- casts per 100 live rounds (item 1);
- banks a game and median bag (item 6);
- games lost holding 100+.

Spar bars are self-play, and LADDER_P4 §4 showed self-play hid the fight gap. So when p7's / p8's ladder replays come
back, re-run TOP_TEAMS §11 on them to see whether the gaps closed.
