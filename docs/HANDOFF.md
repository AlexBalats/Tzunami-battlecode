# Handoff: where we are and what to do next

Older entries are in `docs/archive/`: `HANDOFF_to_19oct.md` (13–19 Oct), `HANDOFF_19oct_teamloop.md` (the team loop,
19 Oct) and `HANDOFF_20oct_redo.md` (the patch and redo sessions 1–6, 20 Oct). Keep this file short: the newest entry
on top, then the standing sections.

## 27 Oct (night), the three ways measured; portals built and lost; next = NEXT_PROMPT_BIGTAKES

**State:** v62 = `bots/cpp-p17` = `bots/cpp` live (unchanged; nothing kept this session). Handed to the teammate: `docs/CATCHUP.md` is the
summary of everything so far; `other_stuff_for_now/NEXT_PROMPT_BIGTAKES.md` is one option, not the plan. Notebook:
`other_stuff_for_now/TEAMFIGHT.md`.
- **The judge (JUDGE.md §8):** local results *do* predict the ladder. Every shipped version since p4 replayed v
  spar-fight and spar-fish against its ladder performance (`tools/ladder/perf.py`): r = 0.96–0.98, slope ~0.3 (a local
  Elo gain shows at a third of its size). Judge locally against fixed references; +20 on the ladder ≈ +70 local Elo.
- **The team fight (§1):** focus, commit and time to kill are level with the top 7; we win fights v our climb band. V the
  top three every body is weaker (HP −16 %, damage a hit −24 %, hits a round −14 %): strength = economy. Not built.
- **The farm (§2–3):** v the A/B band the game is nearly level (the middle converts worse); v the top three their
  captured gems a body-round are 3×. Whole 5+ camp groups we never take: the clear model overstates monster damage
  ~2.3× [measured in our own TRACE clears and in replays]; calibrating it (`MON_HIT`) and an SPSA re-tune both **lost**
  (−3.2, −0.4, −5.7 win pts): the overstatement is the exposure margin. Not kept.
- **The walk (§5, the user's question "why are theirs so much more efficient"):** total waste beyond the shortest walk
  is level; the difference is **dash hops over holes**: same dash frequency, but 17–20 % of Claudus's jumps cross a hole
  (top three 11–13 %, ours 7–8 %); Claudus's dashers skip ~190 walk rounds a game each, ours 20–29. Our L4 spends the
  dash on open ground and our fields are walk-only. Hold-the-dash alone lost (−3.0); patch `P18_hop_hold.diff`.
- **The portal routes, built (TEAMFIGHT §5.1):** the mechanism landed (our hops at Claudus's rate, home exits under the
  shortest walk) but three forms lost v p15 (−5.8, −4.0, −3.3 win pts): the real saving is a few rounds a trip (total
  waste 183 v 189), `jumps.py`'s saved-rounds proxy over-counted. Patch `P18_portals_v2.diff`. Not kept.
- New tools: `tools/ladder/perf.py`, `calib.sh`; `tools/replay/farm/teamfight.py`, `farmeff.py`, `dmgfate.py`,
  `budget.py`, `bankleg.py`, `trips.py`, `bigmap.py`, `campsafe.py`, `visits.py`, `wake.py`, `tusum.py` (TRACE),
  `wander.py` (TRACE choices × replay), `trip.py`, `gaps.py`, `jumps.py`; `grp.claims` (captures mapped by the gaining
  bodies: `engine_groups` mislabels about half the groups). Scrims used: 48 groups (v62 v NEET 9/120, Claudus 8/120).

## 27 Oct (evening), the top three's movement read, four squad forms lost; next = NEXT_PROMPT_TEAMFIGHT

**State:** v62 = `bots/cpp-p17` = `bots/cpp` live (unchanged). **Next session: `other_stuff_for_now/NEXT_PROMPT_TEAMFIGHT.md`.**
- **How the top three move (SQUAD.md §6, 125 ranked games of fish / Mite / Trzy, 150 scrims of v62 against them: 11 wins):**
  a squad is a **shared take**: after r300 49–61 % of their camp hits have an ally on the same group (parallel neighbours
  1–5 %), ours 32 % (59 % before r300, while stack mode runs). They share big groups (5+ camps: 36–44 % of their hits, 60–70 %
  shared; ours 22 %) and farm small ones alone. No fixed leader; one squad at a time; trips home and splits like ours. At
  contact they outnumber the enemy (fewer bodies 17–23 % of the time, ours 31 %) and trade evenly or better; we lose 0.41
  bodies to 0.17 in the 20 rounds after.
- **Built (SQUAD.md §7–8), four forms, plain v p17 locally:** followers take the leader's target outright (38–102), priced
  (64–76, no squad), big takes only (41–99), + squad fight joins (42–98). The forced forms make the squad (same-group 41–47 %)
  and cost ~2 deaths a game for every champion, solos included; with more bodies at contact they still trade worse. **Not
  kept, not proposed for upload.** Patch `docs/redo/patches/P18_squad_v4_bigtake_join.diff`.
- **Next:** the team fight (one target, one commit for the bodies in contact together; fight lab first), then why we take big
  groups half as often, then the squad again on top.
- New tools: `tools/replay/farm/squadmove.py`, `pairs.py`, `sharesize.py`, `timeact.py`; `tools/ladder/ab49.json` (v62's
  A/B opponents, for `requeue.py`); `fetch_matches.py` retries on HTTP 429. Scrim quota used: 30 groups (v62 v the top three),
  49 (the null A/B).
- **Ranks 4–7 are not squad teams** (SQUAD.md §6.2): they share and outnumber like v62; what the top 7 share is lone bodies
  that farm (a lone middle body hits a camp 18–25 % of its rounds, ours 13–15 %). Three ways to the top: the squad, lone
  farming speed, the fights.
- **The null A/B (JUDGE.md §7.1):** v62 v the same 49 teams again: 98 / 245 v 113 the first time. A 245-game A/B can't see
  less than ~±20 wins; interleave 2–3 batches per version.

## 27 Oct (afternoon), the A/B, the top 10, the squad started; next = NEXT_PROMPT_SQUAD

**State:** v62 = `bots/cpp-p17` = `bots/cpp` live. **Next session: `other_stuff_for_now/NEXT_PROMPT_SQUAD.md`** (the user chose a
rebuild: the middle squad as group movement).
- **Scrim A/B v62 v v61, same 49 teams:** 113 v 117 of 245 (−1.6 ± 4.5): level. p17's pieces worked (big-group takes +34 %,
  gems by r300 +14) but the fights slipped (LOSSES_P15 §10).
- **Top 10 v top 10 (355 ranked games):** the winner holds and harvests the middle and wins its fights; our lone middle bodies
  hit camps half as often as theirs and we rarely have a squad there (SQUAD.md §1).
- **The squad, two price-nudge forms:** neither made a squad (the three within 6 tiles 11–14 %, p17 9 %); the zone form
  lost 63–77 to p17. Patch `P18_squad_zone_v2.diff`; what a real squad needs: SQUAD.md §5.
- Also not kept: farm under pressure when paired (`P18_paired_pressure_farm.diff`), the siege (`P16_siege_E7.diff`).
- Cleanup: runs/, the jittered copies and variants deleted; `NEXT_PROMPT_P15_LOSSES` and `NEXT_PROMPT_P16` done and removed.

## 27 Oct (midday), p17 = v62: the need model + the end race; the scrim A/B

**State:** v62 = `bots/cpp-p17` = `submissions/cpp-p17.zip` = `bots/cpp` (live since ~13:00). v61 (p16) read flat on the ranked
ladder (49 % over 290 games v a 1,891 field; 1,852 → 1,857) and 47 % in scrims v ranks 45–99. p17 = p16 + team Strength in
the need model + `TANK_K` 1.3 + the end-race bank: paired v p15 +8.5 ± 2.7 on fresh seeds (p16 +5.5). The A/B (v62 v the
same 50 teams) and every finding: `other_stuff_for_now/LOSSES_P15.md` §9–10. New tools: `bots/spar-idle` (the farm alone),
`tools/replay/opensim.py` + `mapgrid.mjs` (the opening simulator), `tools/replay/farm/pressure.py`, `wasted.py`,
`tools/ladder/requeue.py`, `decset.sh`, `climb.sh`, `judge1.sh` (the scratchpad is wiped at restart: keep scripts in the repo).
The local judge has run out of resolution (every variant +5 to +8 v p15): small pieces need the ladder A/B.

## 27 Oct (night), p15's losses, the judge rethought, the CLI ladder, p16 = the middle first

**State:** `submissions/cpp-p16.zip` = `bots/cpp-p16` = `bots/cpp` (the user uploads it as v61; p15 = v60 was live, rank
~100 at ~1,836). Docs: `other_stuff_for_now/JUDGE.md` (the judge), `other_stuff_for_now/LOSSES_P15.md` (the read, the
plan, every result).
- **The judge (JUDGE.md):** p13 and p15 sit at the same rating though p15 read +6 to +9 locally: local games are a
  mirror. `tools/replay/dash.py` (+ `tools/replay/arena_dec.sh`) reads any set of games on the ladder's KPIs.
- **The CLI ladder (JUDGE.md §7, `tools/ladder/`, memory `cli-ladder-access`):** logged in; scrims (5 games vs any team's
  live bot, seconds, 50 groups / rolling hour) and any team's replays. **Scrims play our live bot**: they calibrate, the
  local paired runs (`tools/tune.py full NAME --opp cpp-p15`, 1,120 games, ~10 min) climb.
- **What the ladder says:** p15 v the top 30 17 %, v ranks 31–48 22 %. Against ranks 31–48 fights are even; the gap is
  **the middle**: by r300 109 v 34 middle gems (own sides equal), 1.45 v 1.0 bodies there from r50. Fish and Mite (#1, #2)
  the same (~1.6 bodies in the middle by r50, ~210 gems by r300).
- **p16 = p15 +** Marcella the nuker-banker (Focus build, gem captures and gold weight to her, the range-4 finisher), the
  ladder's carry builds (Bruiser / Durability), big need-1 groups shared (E1), **contested groups ×1.5 (`MID_X`)**, the
  main's gold weight 3 → 1.5. Paired v p15: **+7.1 ± 3.0 (training seeds), +5.5 ± 2.4 (fresh JSF)**, rate +2.6 to +3.3
  SE; plain v p15 73–67, v p13 90–50, every style bot 57–81 %, sprint 2 14–16. **Weak spot: the open maps (−14.8 ± 3.1 on
  JSF)**: their middle is empty and the top teams win them on their own side.
- Not kept: the provoke guard (code in, `PROVOKE_K` 0: passivity loses to an equal-strength opponent), reach (E6), the
  middle opening seed, `MID_X` 1.25 / 2.0.
- **v61 uploaded (27 Oct ~00:30; rank 87 / 1,852 before it).** Scrims v the same 48 teams: **60 / 240 (25 %) v p15's 45 / 240 (19 %)**; v ranks 31–48 gems by r300 96 → 131, crushed 34 → 23 %, middle gems 34 → 53 (LOSSES_P15 §8). Against the top 30 the middle costs deaths (7.5 → 9.5). Paused here (user: 'continue' resumes).
- **After the upload (done, kept for the next read):** re-run the scrims on v61 (`tools/ladder/queue.py` ranks 1–30 and 31–48, `scrim_dl.py`, decode,
  `dash.py`) and compare with p15's columns in JUDGE.md §7: the middle rows and gems by r300 should move.

## 27 Oct, cleanup for the commit; next = p15's ladder losses + a rethink of the judge

**State:** cpp-p15 is on the ladder (uploaded 26 Oct night). **Next session: `other_stuff_for_now/NEXT_PROMPT_P15_LOSSES.md`**
(Step 0 rethinks the judge and the metrics, user 27 Oct; Step 1 reads p15's ladder losses, which the user adds).
- Bots trimmed to `cpp` (dev = p15), `cpp-p15`, `cpp-p13`, the `spar-*` style bots and `mapdump` (bots/README.md lists what
  was deleted and how to restore it). Tools re-pointed: bar / base `cpp-p15`, pool cpp-p13 + spar-fight + spar-pack +
  spar-fish, held out spar-steal + spar-order. `runs/arena` is empty: every base run is re-played on demand.
- `.gitignore`: replay bundles anywhere (`match-*.zip`, `*.repl26a`), iCloud `* 2` copies, `compile_commands.json`; the
  zips of p10, p13, p15 committed. 14 iCloud duplicate files and 8 empty duplicate folders deleted (`sdk/`, `cmake/`).
- The session's replay and judge scripts moved into the repo (RND_DRAFTS §10, tools/replay/farm/README.md).

## 26 Oct, R&D drafts toward p15: VC passes the ship check, zipped as cpp-p15 (`other_stuff_for_now/RND_DRAFTS.md`)

**Update (26 Oct night): the #1 team's habits (TOP_TEAMS_R5, "fish") tested on p15 (RND_DRAFTS §9).** All judged paired
against p15 itself. The pack (stack mode all game, one or two packs) −7.1 / 0.0 v p15 and **−9.3 ± 4.6 v spar-fish** (a new
style bot that hunts in a pack); Cassi & Issac −12.5 (+6 deaths, the third loss); bank by bag × walk level; Cassi first
level in the lab; F5 items (Durability, then Bruiser Strength) +1.6 to +2.1, deaths −0.5 to −0.8, level v spar-fish.
**The user uploads cpp-p15 (v6) unchanged and plans 20–30 scrims v fish:** next session, decode them and compare with R5's p13-v-fish numbers (deaths alone / walking, contact hits, gems by r150). `bots/rnd-p15b` = p15 + F5 (unproven alternative); `bots/spar-fish`
is a new style bot (not in `tune.POOL`). Patches `docs/redo/patches/R5_*`.

**Update (26 Oct evening):** **`submissions/cpp-p15.zip` = `bots/cpp-p15` = `bots/rnd-vcore` v6 = VC + the parting
shot** (RND_DRAFTS §7: a melee leaving a fight hits the adjacent enemy before it walks). v6 v v5: lab +8.6 SE, pool +5.5 ±
2.0 (JSF) / +8.8 ± 2.1 (J 4–5), deaths −1.6 to −2.0; **plain v p13 88–52 (70 maps; A 46–24, B 42–28), sprint 2 18–12,
ladder maps 21–7**. In contact v6 hits 87 % of adjacent rounds (the top 10 83 %). Upload = the user's call. Tried after:
bolder stance (lab −3 to −4.5 SE) and tributing under pressure (inert); both dropped (RND_DRAFTS §8). Team B: VC gains
equally on both sides; the side bias is p13's own (§6). v5 = v6 minus `docs/redo/patches/RND_parting_shot.diff`.

**State:** the bar is still cpp-p13 (live). **Candidate `submissions/cpp-p15.zip` = `bots/cpp-p15` = `bots/rnd-vcore` v5**
(card VC): the draft by team size, Vesper > Vendetta > Heart of Ruin (3 picks) + Marcella (4) + Varg (5: p13's roster);
on a camp-gated map Varg comes in and the rest of the draft is p13's. Built on `bots/rnd-base` = p13 + p14's bug-class
fixes **with p14's per-kind tank share (`ROT_K`) reverted** (it cost the big open maps; RND_DRAFTS §4).
- **Ship check (the proposed rule, RND_DRAFTS §3 VC):** confirmation seeds JSF +6.1 ± 2.7 win pts (2.2 SE), worst pool
  member spar-pack +1.8, plain head to head vs p13 **76–64** (+57), 0 faults: passes. Also J 100004–7 +4.6 ± 2.3, held-out
  opponents +3.5 ± 2.6. Plain sprint 2 13–17 (jittered level), ladder maps 14–14. **Upload = the user's call.**
- The replay read (46 top-10 games on 4.0, §1): their Vendetta is the killer (94 of our 308 deaths), their gold sits on
  three bodies, our Varg made 0 kills in 46 games. Fight lab: VC +5.1 SE.
- Dropped: rnd-stun (lab level twice), rnd-prism (5-pick Prism team −30 on big maps), rnd-heal (Willow = Marcella on 4
  picks; `Kit::heal_ally` kept there).
- Next: the contact-micro gap (our melee hits 26–35 % of contact rounds, theirs 40–51 %), measured in the lab; the 5-pick
  big-map loss left in the base (s2big −10 ± 6).
- Tools: `decode.mjs` decodes engine 2.0.0 replays; `tune.py` honours `ARENA_MAPS` and reports sprint 2 by size. **Never
  run `tune.py clean`** with the default base: it deletes `bots/_cpp-p13_j*` (p13's base runs go stale).
- iCloud `* 2` copies remain in `bots/_cpp-p13_j100002`, `_j100005` and two `.cambc` caches (outside `src/`; my delete
  was blocked).

## 26 Oct, P14 Part 4: the builds settled, Tavi drafted; p14 not shipped (`docs/archive/P14.md` §4)

**State:** `bots/cpp` = `bots/cpp-p14` (Part 4's build, the evidence copy). **The zip was deleted (user): p14 is level
with p13 head to head and worse on the unseen sprint 2 maps.** The live bar is cpp-p13. **Next session:
NEXT_PROMPT_RND_DRAFTS (a brief, deleted 27 Oct)**: R&D spin-outs (`bots/rnd-*`) from p13 toward p15 with whole new
drafts; the user is adding the top-10 teams' ladder games as `replays_from_others/p13-p3/`. The §4.0 early-fight
scripts are now in the repo: `tools/replay/farm/early_deaths.py`, `focus.py`, `helpfight.py`.
- **Kept:** the main's build Treasure → Capture → Bruiser (race +3.7 win pts over 3 seeds); Prospector by map
  (`cluster_share` ≥ `PROS_SHARE` 0.6: the main opens with it, the crew takes it for Jungle; `rate` +0.016 ± 0.007);
  **Tavi in Marcella's slot** with a Focus build (`PICKS` Heart of Ruin, Tavi, Vesper, Vendetta, Varg, Ren; Marcella
  first in `BACKUP`).
- **The judge (fresh seeds J 100002–3, vs p13's base, the pool):** `rate` +0.044 ± 0.027 (1.6 SE), win +1.9 ± 3.2,
  deaths −0.61, crushed 145 v 197 of 1,120, worst opponent spar-order +1.4. Head to head vs p13 68–72 (+36); ladder
  maps 20–8; **sprint 2 maps 12–18** (the 30×30 and big open maps, both sides; the start-of-day build reads the same).
- **Lost:** Prism as the main (−21.5, the user's idea: 700 HP, no Vesper gold), the crew opening Monster (deaths +0.9),
  Cassi & Issac (deaths +7.6), help any ally in contact (−1.8). Racing's winner's curse: the race's +5 became +1.3 on
  fresh seeds, so confirm every race winner on unseen seeds.
- **The replay read (§4.0, 24 top-team losses):** before r150 we die 40 times to their 8–10 at equal items and with
  allies helping; kills per 1,000 champion hits 3.5 v 13.7; they roam in 3s and burst our lone bodies (14 deaths on our
  side). The opening gap is early fights, not farm speed.
- **After the zip (§4.10–4.11):** Power for Bruiser −6.7 ± 5.4 on sprint 2 over 4 jitter seeds (one run had said +5);
  Ryth for Varg unless an altar is camp-gated −10.8 ± 5.6. Both dropped. The full live 4.0 stat table is now in
  `docs/redo/00_PATCH_4_0.md` §1 (Prism Focus 80, Stellar 70: the patch row's "Focus 140" holds for Willow only); the
  area-spell kit is saved as `docs/redo/patches/P14_area_spell_kit.diff`.
- Kept on disk: p13's 4.0 base runs and their copies `bots/_cpp-p13_j*` (re-creating a copy stales the runs).
  `bots/_b4` (26 Oct 03:37, not this session's, unreferenced) was left alone.
- Races run in the background, small (2–3 variants, 2 seeds, reusing the runs on disk; `_t_mTreCap`'s runs are the
  reference for a variant built on it). Never start a race with a shell `&` (no notice; it outlives the call).

## 26 Oct, P14 Part 3 + patch 4.0 (wrapped; Part 4 = NEXT_PROMPT_P14_PART4 (a brief, deleted 27 Oct), done)

**Where it stopped:** the main-carry build race (`tools/race.py cpp _t_mCapJ _t_mMonJ _t_mCapMon _t_mTreCap _t_mMonCap
--seeds 4 --min 2`, log in the session scratchpad `race_main.log`) was stopped after seed 2 of 4. Its runs are on
disk in `runs/arena/` (and p13's 4.0 base runs vs the pool, training seeds: keep them), so re-running the same command
reuses seeds 1–2 and goes on. **Don't edit `bots/cpp` while a race has `cpp` as a variant** (newer sources make the
harness replay it); edit a copy.
- **Patch 4.0 is installed** (`docs/redo/00_PATCH_4_0.md`): cambc 4.0.0, 70 maps; every `.cambc` build cache was
  wiped (stale release wasm made the bot idle); `fkit_learn` (live abilities; `champion_designs` traps in play); the
  engine's capture countdown; a damaging stun hits camps (`kit.cpp`, Tavi / Ren). p13's 4.0 base vs the pool: p12 53.8,
  spar-fight 57.5, spar-pack 49.8, spar-order 43.9 %.
- **`bots/cpp` now** = p13 + gate news + `MAXCG` 64 + per-kind tank share + `spent()` + Bruiser for Power + the order
  draft (Heart of Ruin, Marcella, Vesper, Vendetta, Varg, Ren) + the 4.0 fixes. vs p13 on the 70 maps: 71 W / 69 L.
  Not zipped (`submissions/cpp-p14a.zip` was deleted with the Ryth draft).
- **The 211-game replay read** (P14 §2): dead time is the swing; we lose fights at equal HP with ~0.6× their items; their
  crew earns 150–390 gold by r300 to ours 47–139 because it captures in parallel (~10–12 groups by r300 vs 5.8);
  the contested elk race decides games. 14 new ladder maps rebuilt into `maps_ladder/`.
- **Lost tonight:** commit lock (lab −9.6 SE), crew damage ×0.6 / ×0.8, Marcella Focus, Durability, first capturer
  (−12.3), the Ryth draft (01boss-battle: Varg opens the gate).
- **4.0 fight lab** (redraft for Marcella's slot): Tavi 0.550 (+3.4 SE), Cassi & Issac 0.536 (+2.6), Ren 0.514, Ryth
  0.491; Tavi for Heart of Ruin 0.481.
- **Queued after the race** (variants built in `bots/_t_*`): the crew race (`_t_cMonJ`, `_t_cJMon` with the race's
  main winner rebuilt in), then Tavi for Marcella (`_t_dTaviM`, rebuild it on the current cpp for the `kit.cpp` fix)
  and Cassi & Issac (`_t_dCIM`) in a pool race; Prospector by map; Vendetta as the clearer. P14 §3 has the plan and the
  emblem reasoning.

## 25 Oct, p14 Part 2: bug fixes kept, the fight lab, round 4's pieces, a draft candidate (`docs/archive/P14.md`)

`bots/cpp-p13` stays live and the bar. **`bots/cpp` = p13 + the kept fixes + an undecided draft candidate** (not
zipped). Next session = NEXT_PROMPT_P14_PART3 (a brief, deleted 27 Oct) (the 26 Oct balance patch first).
- **Kept (P14 §1.1, §1.3, §1.5):** the gate news (`Mem::gate_news`: every altar shut and their score rose → the gates
  count as down; 01boss-battle 70 → 83 % vs the pool, neutral elsewhere); `MAXCG` 64 / `MAXLIVE` 80 (R4-3: on the
  sprint 2 map whose only altar is ringed by a 48-camp group, 0–0 at r2000 → won both sides); the per-kind tank share
  (`hit_share`, `ROT_K` 1.5 on monolith / golem by `camp_type`, R4's measured shares; golem gems 138 → 174 a game on
  golem maps); `spent()` (a fuel delta across a rollover wrapped to 4.29e9 and froze Nav for the game; mostly a TRACE
  artefact, so earlier traced measures on 01big-world / 01islands had a frozen Vesper); Tavi's field shop.
- **The draft candidate in `bots/cpp` (§1.7):** `PICKS` Heart of Ruin, Marcella, Vesper, Vendetta, Ryth (+ Ren), Varg
  for Ryth on maps ≥ `VARG_AREA` 6,500 tiles. Pool +0.0 / −0.6 (training / confirmation), held-out +0.5, crushed −20 %,
  deaths −0.5; head to head vs p13 41–39; open maps −4 to −7; sprint 2 maps 67 v 73 of 120. Undecided: re-judge after
  the patch. Found on the way: `PICKS` only picks the roster; slots come from `world.cpp`'s `ORDER`, so a "draft order"
  matters only on 3- and 4-pick maps (LADDER_P13 §D4 was wrong on that).
- **New tools:** `tools/lab.py A B` (the fight lab, `LAB` in `types.h`: no farming, both sides march to the middle and
  fight; kill share ± map-clustered SE in 31 s; the mirror reads 0.500; Varg and Marcella die most, as on the ladder);
  `ARENA_MAPS=maps_sprint2 python3 -I tools/arena.py …` (the 15 rebuilt sprint 2 maps, in `maps_sprint2/`, outside
  `maps/`); `tune.cells` skips runs older than the variant's sources (it had re-printed a pre-edit result).
- **Lost (§1.2–1.5):** no capture handoff −16.4; hold-when-stuck in the lab 0.354 (−6 SE); NOK-AV, `STANCE_*` in the lab
  level; `OPEN_END` 0 / 50 / 150 (−5.5 / −2.3 / −2.5); Tavi for Varg (lab 0.585 but pool −3.8, farms worse); sessions
  (`docs/redo/patches/P14_R4-1c_sessions.diff`: tail worse); R4-4 Marcella as second capturer −2.7, deaths +0.3.
- **Research:** Cout for Clout 2024, The Kragle 2025, SPAARK 2025 postmortems, Stanescu et al. 2015 (Lanchester combat
  prediction), SparCraft / PGS: summarised in P14 (the lab's tests came from them). Comms: a claim names a group in
  5 bits, so groups past index 30 can't be claimed (sprint 2 maps have 35).
- **Cleaned:** runs/arena (cache too) and every scratch bot. p13's base runs must be re-made after the patch anyway.

## 25 Oct, p14 Part 1: p13's ladder losses read, the scrim plan, the opponent pool (`docs/archive/LADDER_P13.md`)

No bot change: `bots/cpp` = `bots/cpp-p13` = `submissions/cpp-p13.zip` is live and is the bar. Next session =
NEXT_PROMPT_P14_PART2 (a brief, deleted 27 Oct).
- **The read (§1–7):** `replays_from_others/p13/` = 90 losses, no wins, no duplicates.
  - The gap is bigger and earlier than p12's: 48 crushed (p12 27 of 65), median split r302; the opponents look
    stronger (their gold by r300 1,769 vs p12's winners' 1,489) [guess: a higher ladder band].
  - Clusters by gems a game: contested middle ~225 (95 v 483 gems, presence 22 v 35 %), own-side farm early ~162
    (splits at r167; camp hits by r300 256 v 344), fights ~113 (even 76 v 230 kills; our melee out-hit 1.3–3.9× in 1v1;
    commits at HP > 70 % die 26 %, theirs 6 %), **the shut gate ~63: 01boss-battle 6 losses, 5 with 0 tributed**
    (the opponent kills the two gate monoliths and stands on their spawn tiles; `World::altar_open` reads only our
    memory, never the enemy's rising score).
  - p13's 12 moves did what they were tuned for (elk 13 → 19 a game, multi-big 2.4 → 4.4, respawn latency 34 → 27) and
    cost banks (20 → 16 a game; theirs 31) and the bag at death (53 → 74).
  - Families: HMVR (Heart of Ruin, Marcella, Vesper, Ryth, Vendetta) 27 losses, every mechanism: the peer to scrim
    first. Top-team signatures 22 losses, gap median 800.
  - New scripts: `tools/replay/farm/splitmech.py` (LADDER_P12's split rule as code + "shut"), `matchup.py` (fights by
    champion matchup), `early.py` (the first 300 rounds).
- **The judge (§B):** `tools/tune.py --opp pool | holdout | a,b,c` (per opponent, the pool mean with the SE clustered by
  map over all opponents, the worst opponent); `tune.py base --opp LIST [--fresh]`; defaults now `--base / --opp
  cpp-p13`. `tune.POOL` = cpp-p12, spar-fight, spar-pack, spar-order; `tune.HOLDOUT_OPP` = spar-steal, cpp-p10, cpp-p8.
- **The pool (§D):** style bots of our own code (cpp-p13 + `// SPARRING` edits): `spar-fight` (HMVR draft, long
  commits, hunts, HP builds), `spar-pack` (T5 draft, stack mode all game, the middle first), `spar-steal` (T4 draft,
  captures ×3, arrive second), `spar-order` (our five reordered). p13 wins 42–58 % against them (cpp-p12 58 %, cpp-p10
  66 %, cpp-p8 83 %; spar-meta and cpp-port 98 %, dropped). It ranks p10 (−13.3) < p11 (−5.4) = p12 (−5.3) < p13. It
  reproduces p13's ladder commit deaths (24 % vs 26 %), the middle's presence (34 %) and capture split, **not** the 2 : 1
  fights or the 5× middle (every copy runs our micro). spar-packfight (both) added nothing, deleted.
  **spar-order may be +4 over p13** (jittered p13 vs it 41.9 ± 2.9; the other direction +0.5 ± 3.5): Part 2.1.
- **Scrims (§C):** the list for the user: 7 teams by signature (P1 HMVR, P2 Willow, P3 VargRyt, P4 Prism, P5
  HTpre/HMVRpre; T1 T6-like, T2 T5), Bo5 each with p13, every replay into `replays_from_others/scrims_p13_<date>/` with
  `teams.txt`; plus 20–30 of p13's ladder wins. **User: scrims use only the live bot and most teams field the same champions, so scrims are held to the end** (§C3).
- **Cleaned:** runs/arena (cache too) and every scratch bot deleted at the end. Part 2 first regenerates p13's base runs
  against the pool: `python3 -I tools/tune.py base --opp pool,holdout` and the same with `--fresh` (7 × 640 games each,
  ~45 min together). p13 vs cpp-p12 on the confirmation seeds read 56.9 % ± 2.4 before the stop.

## 25 Oct, p13 session: p12's ladder losses read, the judge fixed, p13 = p12 + 12 SPSA constants, shipped `submissions/cpp-p13.zip`

All in `docs/archive/LADDER_P12.md`. **`bots/cpp` = `bots/cpp-p13` = `submissions/cpp-p13.zip`** (builds from a
clean unzip; null 49.7 %). The bar until the user uploads it: `bots/cpp-p12` (uploaded, top 100 overnight).
- **A. p12's 65 ladder losses** (`replays_from_others/p12`, one duplicate dropped; our stdout is empty on the ladder):
  - the gem gap (−497 a game) is mostly the **contested band (−338)**: we stand there 24 % of live rounds (they 34 %)
    and die there almost twice as often; they take small groups there too, so it is not the need model;
  - **fights lost at equal numbers** (even 99 v 184 kills, 1v1 38 v 87), while p12 wins the same fights 60 v 25 vs
    cpp-p10 locally: what we tune against our lineage doesn't transfer;
  - they bank 32 times a game to our 20; 4 losses had 1,000+ in hand (the end race);
  - p12 fixed 01boss-battle (no loss) and walled maps (40 → 18 % of losses); modes A/B/C 41/20/4 (p10 27/17/4 of 48);
  - `tools/replay/farm/gain.py` fixed: it read a death's position from the wrong fields.
- **B1. The judge:**
  - the old fixed jitters were not independent (J 50 replayed J 0 in 63 of 80 cells; the "fresh" set interleaved the
    default one, so confirmations partly replayed the tuning seeds); now **hashed seeds**: training J 100000–100007,
    confirmation 100100–100107 (`--fresh`); they share 4–7 of 80 games (the floor);
  - the SE is **clustered by map** (the iid one was 1.1–1.2× optimistic); the left tail and the 8 **held-out maps**
    (`tune.HOLDOUT`) are in every report; `tune.py --opp` (default cpp-p12), `--base` default cpp-p12;
  - CUPED (−11 to −18 % variance) and an SPRT (10.5 % false accepts, no gain over the 2-SE stop) checked, not adopted;
  - the same build reads `rate` +0.023 higher on the confirmation seeds: read a confirmation against its own base runs.
- **B2. p12's chaos:** 62 % jitter agreement, 10 of 80 map-sides fixed, 29 % of mirror games end 600+ apart. The only
  proven self-made noise: the stance flipping as P(lose) crosses 0.7 (420 flips in a 20-game trace).
- **C1. Every structural piece was neutral or lost** vs cpp-p12: R9's kill exclusion (+0.011 / −0.009 on the two seed
  sets), R9's danger term (−0.006), R9's tank share (+0.018 ± 0.025, undecided), the respawn watch as a map rule
  (−0.002), the win-in-hand bank in two forms (−0.013, −0.007: a winning bag walked through enemies is handed over),
  stance hysteresis (pooled +0.011 ± 0.015, deaths −0.25). The port audit's 5 uncalled functions are dead duplicates.
- **C2. The climb** (`tools/spsa.py`, 12 constants in `tools/spsa_p13.json`, 90 iterations, one hour): **p13 vs
  cpp-p12 +11.4 ± 2.8 win points, `rate` +0.070 ± 0.027 on the confirmation seeds** (+13.4 on the training seeds),
  held-out maps +12.5 ± 3.3, every stratum up, deaths −1; **vs cpp-p10 +7.7 ± 3.1 over p12**. Big moves: `KEEP_HP`
  0.40 → 0.3165, `TANK_K` 1.5 → 1.957, `WAIT_MAX` 15 → 9, `BAG_CAP` 50 → 67, `P_NEAR` 0.5 → 0.3026.
- **Plain head to head** (the user's check, no jitter, the two zips, 80 games, run 3 times, identical): **p13 51 W / 29 L
  (64 %) vs p12**, 16 maps won from both sides, held-out maps 13/16, worst 01starfish. p13 is uploaded; its 90 replay
  bundles are in `replays_from_others/p13/` (the p12 and p10 folders are gone: compare through LADDER_P12 / LOSSES_P10).
- **The plan changed (user discussion, end of session):** self-play climbing overfits to our lineage, so the next climb
  runs against an opponent pool: our frozen builds + our own "style bots" (middle-first pack, fighter, steal) that
  must reproduce the ladder's gaps; scrims against chosen peer teams (the user runs them on the website) are the real
  test; **no outside code, ever** (user). Peer win rate is the target (Bo15: 0.55 a game → 65 %, 0.60 → 79 %). Then
  fight micro, comms v3 (the 8 bytes), in-game opponent reading, counter-drafting. All in
  NEXT_PROMPT_P14 (a brief, deleted 27 Oct) (Part 1: ladder read + scrim plan + pool; Part 2: the rest).
- **Next** (NEXT_PROMPT_P14 (a brief, deleted 27 Oct)): the user uploads p13 → read its ladder losses (bag at death and
  banks: p13 banks later); a second SPSA step on p13 (re-base first); one-at-a-time screens of the 12 moves; a sparring
  opponent built from the winners' replays, since the ladder's two big gaps (the middle, fights) are invisible to a
  judge that is our own lineage.

## 25 Oct, night: R&D on p11 (`docs/nav/RND_P11.md`): the noise measured, a tuning harness, the audit found a dead altar gate; p12 = p11 + the gate fix + SUNK_K 3 + MY_RATE 0.6, 62.7 % vs cpp-p10, shipped `submissions/cpp-p12.zip`

Planned as R&D only; at the end the user asked to ship the candidate. **`bots/cpp` = `bots/cpp-p12` =
`submissions/cpp-p12.zip`** (p11 + `docs/redo/patches/RND_p12c.diff`; builds from a clean unzip; the user uploads it
for an overnight ladder test). **Confirmed on a third seed set** (J 75 … 2100): p12 62.7 % ± 0.7 vs cpp-p10
(margin +151), p11 54.5 % ± 1.7 (+86); paired +8.1 ± 2.2 win points, `rate` +0.042 ± 0.014. **p12's null 49.5 %
± 1.2** (default seeds). Everything below is in RND_P11.
- **Noise (§1)** [measured, 2,560 games: p11 and p10's null over 16 jitters]:
  - **To see +2 win points takes ~6,200 paired games on wins, ~1,300 on `rate`** ((gems − theirs) / rounds) and
    ~600 on `gpr` (ours alone). `rate` is the screen measure: it tracks wins best (r 0.76) and counts the opponent.
  - **`jitter_sum`'s ± is optimistic by about 2×.** A fuel jitter makes less chaos than a code change (two jitters
    agree on 71 % of games, two builds on 56 %). p11 vs p10 paired is **+4.4 ± 1.8** win points (default +2.5 ± 2.6,
    fresh +6.1 ± 2.5).
  - **Never screen on a map subset:** a 16-map subset's delta wanders by ±0.04 `rate`, as much as p11's whole effect.
  - Per-map outcomes are **not** near-fixed per build: only 22 of 80 map-sides keep one result over 8 jitters.
  - **A shared base gives every variant one common offset.** Neutral variants read +0.2 and +3.7 win points vs p11's
    default runs. Read a constant's gain against that, and confirm on fresh seeds.
- **The harness (§3):** `tools/tune.py` (`list`, `build NAME KEY=VAL | FILE:old=>new`, `screen` = 160 paired games
  in ~1 min, `full` = 640 in ~3.5 min, `clean`, `slim`) and `tools/noise.py` (any two jitter sets, paired, all
  measures, `--permap`). Runs keep a slim `stats.json` (~0.12 MB a game, no replays).
- **The audit (§4)** [measured, 80 decoded games + the `tu` time use + fuel logs]:
  - **Bug: `World::gate_init()` was never called** (the X8 altar gate, lost in the port, like `MAXCG`). 01boss-battle's
    only altar sits behind the monolith. Both p10 and p11 carried 2,000–10,000 gems there and tributed none (31 of
    32 games end with a 200+ bag). With the gate built: **01boss-battle 31 → 94 % of cells, margin +991**. 01islands
    and 00collision have altars walled off by holes, not camps, which the first fix wrongly shut (01islands 0.62 →
    0.38–0.50). `gate2` gates only an altar that opens without the camps.
  - **Respawns wait a median 32 rounds for the first hit**; a body is there at only 25 % of respawns (the ladder
    winners: 1 round on 00rows).
  - **127 gems a game are carried into deaths** (15 % of the 838 tributed; Vesper 54).
  - Time: hitting camps 10.0 %, capturing 9.4 %, walking 52.1 %, dead 8.6 %. Elk kills 22.7 a game (no longer a gap).
    Fuel: mean 38k a turn of 100k, p99 77k, 1.0 rollover a game, so the decision has headroom.
- **The screen (§3.3):** 16 constants both ways, 32 × 160 games. Most point one way: commit more (`SUNK_K` 3), value
  my time more in the death cost (`MY_RATE` 0.6), heal later (`HEAL_K` 1.0), exclude a failed target longer (`EXCL`
  35). Flat: `EXEC_RES`, `HYST`, `REWARD_X`, `NEAR6` 8, `WAIT_CAP`, `STANCE_HOLD` 4.
- **Full and fresh runs (§3.4):**
  - p12a (the first gate + `SUNK_K` 3 + `MY_RATE` 0.6): **+7.7 ± 2.2 win points over p11 on fresh seeds** (61.4 % vs
    cpp-p10; p11 53.7, the null 47.7), `rate` +0.032, deaths −1.3 a game.
  - p12b (+ `HEAL_K`, `EXCL`, `BANK_NEAR_BONUS`): +4.2, walled maps −0.061 `rate`. The extra three cost.
  - **p12c = `gate2` + `SUNK_K` 3 + `MY_RATE` 0.6: +9.5 ± 2.1 win points over p11 (default seeds), +7.5 ± 2.2
    (fresh); 61.6 % vs cpp-p10 over 1,280 games (p11 53.0 %, nulls 49.2 / 47.7)**, `rate` +0.03, deaths −1.3 a game.
    Best: 00stampede 0.41 → 0.94, 00lost-world 0.16 → 0.78, 00contest, 00monolith, 01elk-arena, 01boss-battle.
    Worst: 00gemfight 0.69 → 0.41, 01corridors, 01fracture, 01big-world (the open maps are p12c's weakest).
- **Patches:** `docs/redo/patches/RND_gate2.diff` (the gate fix), `RND_p12c.diff` (+ the two constants). The
  web notes are `docs/nav/pm/RND_P11_web.md`.
- **Next (RND_P11 §6):**
  1. Read p12's ladder results (the user's overnight test) beside RND_P11 §4; once uploaded, `bots/cpp-p12` is the
     bar (null 49.5 %).
  2. The port audit: R9's Python against `bots/cpp`, piece by piece.
  3. The respawn watch (U3). `WAIT_MAX` 25 helps few-group maps and costs open ones, so the rule reads the map.
  4. Bank before the risk (U4).

## After round 3: cpp-p10's ladder losses built on; a group bug fixed (`cpp-p11`, zipped, NOT uploaded); N1, N2, N3, N5 lost

All in `docs/archive/LOSSES_P10.md` §8. Judged only vs `bots/cpp-p10` (user: "no point wasting time on any of
the older stuff"); each N piece also head to head vs the build before it.
- **Checked first** [measured]:
  - the two facts N1 rests on hold on cambc 3.0.5: damaged camps never regain HP, and they sleep 2–3 rounds after the
    last champion leaves range;
  - local baseline (p10 vs p9, 16 games): 00stampede 0–0 at r2000 both sides; the contested capture gap doesn't show in
    the mirror;
  - U-L3: none of the 21 ladder monolith deaths followed a hit on the monolith. 11 were a camp the bot couldn't see (next
    item); 10 were bodies in range of an awake monolith of their own farm group (the danger board's `skip_g`).
- **Kept and shipped: the group fix.**
  - `MAXCG = 8` cut every group to 8 camps; 19 of 40 maps have bigger ones, up to 30. The bot under-priced them and
    could think a group was cleared while camps lived.
  - `MAXCG` 32, `MAXLIVE` 48, `sense` reads the current group first.
  - It raised rollovers to 21–24 a game (Varg's `splash_m`, quadratic, called per body count). Fixed: `splash_m` once a
    round per group, `clear_model` sorts only hitters, JOIN priced once a group. Rollovers now 0.9–4.1 a game.
  - **vs cpp-p10: 52.3 % ± 0.8, margin +73 (default; null 49.2); 53.8 % ± 1.2, +84 (fresh; null 47.7).** Walled maps
    63 %, big-group maps 59–60 %, high-need maps 43–45 % (the weak set). Worst: 00expanse, 00monolith, 00great-wall.
  - `bots/cpp-p11` frozen = `submissions/cpp-p11.zip` (p10 + P3c + the fix; builds from a clean unzip). **Not uploaded
    (user): the gain is too small; upload the next build once it is a good couple percent better.** The ladder bar stays
    `bots/cpp-p10`. p11's null: **49.8 % ± 1.7 (default seeds) / 48.3 % ± 1.3 (fresh)**.
- **Not kept** (patches `docs/redo/patches/P12_*`):
  - N1, session takes, 7 forms. Best: 48.8 % head to head vs the fix (null 48.0). It wins 00stampede (0–0 → 480–0 vs
    p10) but gives back 00monolith and 00rows; per-body triggers misfired on every map;
  - N2, hold what you clear (contested price × k²/(k²+e²)): 42.2 %;
  - N3, break by numbers: 46.2 % (with the step toward an ally), 44.2 % (without);
  - N5, cluster gold weight: 43.6 %.
  - N4 not built (it needs N1's sessions).
- **New tools** (`tools/replay/farm/`, README): `deathctx`, `contactact`, `battery_us.sh` (copied from the loss
  session's scratchpad).
- **Next (user):** an R&D session on min-maxing p11 (the user's prompt for it is the next session's brief): tune the
  bot's constants with a low-noise harness, make it leaner, lean toward the top teams' habits; then:
  1. the danger board's `skip_g` hole: don't stand in range of an awake camp of my own farm group that my company can't
     take (01gold-rush monolith deaths);
  2. the high-need maps (43–45 % vs p10): N1g's 00stampede win without its 00monolith / 00rows cost;
  3. read cpp-p11's ladder losses once uploaded;
  4. TOP_P9 §10.6: the planned takeoff + the jump in the prices.

## 26 Oct: round 3 (teams 6 and 7) built on p10; every piece lost head to head except the teleport crystal (P3c, kept in `bots/cpp`, not shipped)

All in `docs/nav/TOP_P9.md` §10 (the plan was written before any code).
- **The round-3 gaps are real locally** [measured, p10 vs cpp-p9, 16 decoded games, §10.1]:
  - ally within 5 at r300–1000: 47 % (T6 64 %);
  - bodies at contact: 1.56 v 1.51 (T6 2.00 v 1.57);
  - solo camp hits: 55 % (T6 33 %);
  - kills before r300: 0.5 a game (T6 3.9);
  - Marcella: 8 % of our tributes (T7's 44 %), the most deaths (2.7 a game) and the most gems carried at death, first
    emblem r560.
- **Everything built from them lost vs cpp-p10** (8 jitters; p10's null 49.2 %, re-run):
  - the overlapped-trip shop gate: 46.7 / 50.3 % (2 / 3 shards);
  - the 3 + 2 sub window on every map: 48.9 / 47.3 / 45.6 / 43.3 % (to r300 / 600 / 1000 / all game);
  - the cohesion term in three forms, and with the window: 43.1–47.0 %;
  - Marcella Health first: 45.3 %; with her taking captures: 34.1 %;
  - team 6's fight builds: 44.7 %.
- **Why the pack lost:** it raised cohesion (47 → 55 %) and cut solo camp hits (55 → 46 %), but bodies at contact
  stayed 1.58 v 1.55. Our contacts happen on lone walks: at a contact our body is farming 8 % of the time, and 47 % are
  outward walks with no ally within 5. It also costs the open maps (01big-world 1 / 16, 00expanse 3 / 16).
- **Kept in `bots/cpp`: P3c, the teleport crystal** (TOP_T4/T6/T7's S4):
  - **The rule:** while walking, with no enemy in sight, jump to a landing within 3 that is ≥ 15 closer to the goal
    after the channel. A crystal is bought on spawn only once a landing has been found on this map.
  - **The TRACE proved the timing:** the channel starts at round R, the body stands at R+1 and R+2, and lands on the
    planned tile at R+3.
  - **Jumps:** 6.5–19.5 a game on the walled maps, 35–111 tiles saved a jump (T6 5.5, 97).
  - **Results:**
    - vs cpp-p10: 49.8 % default (null 49.2), **50.9 % fresh** (null 47.7);
    - vs cpp-p9: **63.0 / 61.6 %** (p10 59.4 / 59.1);
    - vs spar-meta: **95.6 %** (p10 94.4);
    - the walled maps: 59.7 % vs the null's 51.7 %.
  - **Not shipped:** the default-seed margin over p10 is inside one SE. The diff is
    `docs/redo/patches/P11_P3_crystal.diff`; zipping it as `cpp-p11` is the user's call.
- **00pilgrimage gets 0 jumps:** its shortcut needs a planned takeoff, and the prices don't see the jump (U-T10.6).
  Reach on top of P3c: 46.7 %, 16 rollovers a game.
- **New tools** (`tools/replay/farm/`, README):
  - copied from round 3: `cohes`, `contact`, `tbud`, `steal`, `killzone`;
  - `egold`: earned gold by round from stats.json;
  - `banker`: tribute share and gems carried at death;
  - `hot`: the contact rate per map, bimodal: 0–11 % or 19–85 % before r300;
  - `portal_est`, `portal_greedy`: offline crystal savings from the map grids (`tools/mapdump.inc`).
- **Patches of what lost:** `docs/redo/patches/P11_*`.
- **Bars unchanged:** `bots/cpp-p10` (null 49.2 / 47.7 %) and `bots/spar-meta`.
- **Next:**
  1. the planned takeoff + the jump in the farm prices (§10.6 item 1);
  2. the user's p10 ladder read beside §10.1: do ladder opponents make the pack or the banker pay where the mirror
     didn't?
  3. ship p11 once it clearly beats p10.

## 25 Oct: p10 = the capture + recall overlap + Treasure → Jungle builds; 59.1 % vs cpp-p9, 69.4 % vs cpp-p8 (fresh seeds); shipped `submissions/cpp-p10.zip`

All in `docs/nav/TOP_P9.md` §9 (the plan was written before any code).
- **The side session checked against the code** (§9.1) [code, measured on 16 local games]:
  - p9 already shops with 120+ on 78 % of full-HP recalls: its trigger is the gold to finish the emblem, not
    `SHOP_MUST` 300;
  - p9 already banks at 50 (`BAG_CAP`).
  - Neither was a gap, so both were dropped from the plan.
  - Against p8 on open maps the top teams' elk hitters were at ~1,600 HP, so elk doesn't need 2,500 HP; reach is
    still the open-map lever.
- **Kept in `bots/cpp` (= `bots/cpp-p10`, `submissions/cpp-p10.zip`, builds from a clean unzip):**
  - **Q1, the capture + recall overlap** (team 4):
    - on a capture tile with no enemy in sight, the body counts the capture rounds itself;
    - it prices the home trip with a free recall (`s.trip`: Shop with the gold the capture will pay, or Heal) against
      the best farm price after the capture (`s.nxt`), and recalls once the rounds left ≤ the recall turns;
    - on landing it notes the respawn and sends code 4 (`caprec_land`);
    - the trace proved the timing: 58 of 58 paid once a camp an ally finished the same round counts one round later.
  - **Q2, Treasure → Jungle first** on the Vesper (→ Power Strength; Home dropped, level with it kept), Heart of Ruin
    (Treasure Health → Jungle Focus → Durability Health), the Vendetta and the crew (Treasure Health → Jungle Strength →
    Power Strength). Each body added gained: vs cpp-p9 48.9 → 54.4 → 56.9 → 59.4 %.
  - **Default seeds: 59.4 % ± 1.6 vs cpp-p9 (null 45.5), 70.0 % ± 1.9, margin +172 vs cpp-p8 (p9 62.8 %, +124).**
  - **Fresh seeds: 59.1 % ± 2.1 vs cpp-p9 (null 47.2), 69.4 % ± 2.5, +168 vs cpp-p8 (p9 57.7 %).**
  - **vs spar-meta 94.4 %, +532.** Rollovers unchanged (4.6 a game at J0).
  - Locally: deaths 10.4 → 5.5, max HP r1000 2,000 → 2,400, elk gems 381 → 459, earned gold r1000 4,835 → 5,369.
  - Worst maps: 00pilgrimage, 01starfish, 00swirl, 00packs (vs p9); 00rows, 00eight (vs p8).
- **Not kept** (on top of Q1 + Q2): reach by rate (64.1 % vs p8), the carry home on the shop recall (67.0 %), team 5's
  Marcella build (level).
- **New tools** (`tools/replay/farm/`, README): `caprec`, `emb`, `shoptrig` (the side session's), `fuelroll` (rollovers
  from the fuel logs). **The overlap fools three scripts:** the reward pays on the round the body lands, so `caprec`'s
  capture line, `shoptrig` and `goldsrc` under-count. Use earned gold from `stats.json` instead.
- **New bars:** `bots/cpp-p10` (frozen; **uploaded by the user 25 Oct**) and `bots/spar-meta`. p10's null: 49.2 % (default seeds) / 47.7 % (fresh).
- **Next (user, 25 Oct):** the user runs another top-teams side session (round 3, `docs/archive/TOP_TEAMS_R3.md`, teams 6+). The next session implements the picked findings on top of p10, as this one did. Also read cpp-p10's ladder losses when they come in. Then the small maps (the snowball), reach again, and a lower
  shop gate for overlapped trips only (the crew's first buy is still r247–278) (§9.5).

## 24 Oct, night: the top teams on our weak maps read by feature (`docs/nav/TOP_P9.md`); a p10 built and dropped; p9 uploaded

- **The user uploads p9** (`submissions/cpp-p9.zip`) and is running a **side session on the top teams**. p10 is redone
  after it, from TOP_P9 plus that session's findings. The p10 built here (reach by rate) was deleted (`bots/cpp` =
  `bots/cpp-p9` again); its change is `docs/redo/patches/TOP_P9_reach_sticky_p10.diff`.
- **The 35 bundles in `replays_from_others/even_better_p9` are p8 games** (our Heart of Ruin buys Bruiser Health first;
  p9's buys Bruiser Focus) [measured]. All losses.
- **By map feature** [measured]:
  - **open maps** (19: 00expanse, 01big-world, 00lanes, 01fracture, 00rows): gold, max HP and deaths equal, yet they
    bank 1,032 to our 505. The gap is **elk groups**: 677 vs 320 gems a game (wolf groups 251 vs 255). One elk kill
    costs both sides the same (2 hitters, ~10 rounds, ~420 HP). They leave wolves idle 56 % and keep elk busy (33 %);
    we do the reverse. The far rich groups (rank 10–20 by walk) are never priced: only `near6` is.
  - **small maps** (13): the fight snowball (deaths 17 vs 3.3, gold 2,956 vs 7,661).
  - hops 4 vs 15 a game; banking via spawn 53 vs 33 % of tributes (their crew shops on the way).
- **What the builds taught** (TOP_P9 §8, all vs cpp-p9 and cpp-p8 over 8 jitters):
  - **reach by rate** (3 groups my live `need_k` takes with ≤ 2 bodies, not their side, refreshed every 25 rounds):
    48.8 / 51.4 % vs cpp-p9 (nulls 45.5 / 47.2 %), 61.7 / 59.2 % vs cpp-p8 (p9 62.8 / 57.7 %), 00expanse 2 → 16 of 16,
    00packs 2 / 16. A small edge; dropped by the user.
  - reach rebuilt every turn: **48 turn rollovers a game** (p9 1.4): the loss was fuel, not the idea;
  - `DMG_X` 0.6 in `clear_model`: no change in what we take locally, deaths 6.7 → 8.2;
  - the bank by recall (two bugs fixed: a slack loop, the altar tile's FAR home value): neutral;
  - Vesper-only reach, far-only reach (`RATE_FAR` 30), `WAIT_MAX` 8: lost or level.
- **New null for p9:** a jittered cpp-p9 vs cpp-p9 is 45.5 % (default seeds), 47.2 % (fresh). New scripts in
  `tools/replay/farm/` (README): `gaintype`, `elkkill`, `bigtake`, `wake`, `campfocus`, `crewhit`, `clrcap`, `spread`,
  `pergame`, `idle`, `banktrip`, `front` (shared `repcommon.py`).
- **Bars:** `bots/cpp-p9` (frozen, uploaded) and `bots/spar-meta`. `runs/arena` reached 9.1 GB mid-session (deleted).
- **Next:** the side session's findings + TOP_P9 §8.3 → redo p10; read cpp-p9's ladder losses when they come in.

## 24 Oct, late: p9 = the engagement stance + Heart of Ruin's kit; 62.8 % vs cpp-p8, 91.7 % vs spar-meta; shipped `submissions/cpp-p9.zip`

All in `docs/nav/LADDER_P8.md` §9.
- **The trace first (U-P8.2):** a TRACE copy with a per-round contact line (`tools/replay/farm/cx_trace.sh`, `cx.py`),
  4 games [measured]:
  - "mixed" = Kill ↔ Heal flips on P(lose) near 0.5; 205 of 222 Heal entries in contact had P(lose) > 0.5;
  - 71 of 101 deaths came in Heal (the walk away);
  - the chase ban and `NAV.near` were not the cause.
- **Kept in `bots/cpp` (N1 + N2, one piece):**
  - **The stance** (`upd_stance`, upd.cpp): on contact, COMMIT (Kill one target, the ally's C_KILL first) or BREAK
    (Heal), held 6 rounds, re-decided on events. Break above P(lose) 0.7 or below 45 % HP.
  - **Deleted:** `trapped`, `flee_ok`, the in-fight chase hold, `retreat_now` in `upd_decide`, Heal's `pdie = plose`,
    Fall's trapped fight.
  - **Heart of Ruin:** the landing dash on champions (`Nav::dash_land`), the Bruiser / Power Focus build, the shield
    as it closes. `Kit::stun_enemy` has a caller.
  - **62.8 % ± 1.3, margin +124, deaths 6.7 vs kills 11.1 vs cpp-p8; 91.7 % ± 0.5, +456, deaths 4.5 vs spar-meta.**
    On fresh seeds (the selection check): **57.7 % ± 2.3, +100** vs cpp-p8. Worst: 01big-world, 00packs, 01fracture.
  - In contact (vs cpp-p8): melee hit share 32–47 % (p8 22–29), move-away 23–28 % (36–46). Heart of Ruin loses 32 HP
    a contact round (68). Mixed 28 % (37).
- **Not kept:**
  - the design's "commit even at a high P(lose) when the escape fails": 28W/52L. Commits at P(lose) > 0.5 died within
    10 rounds 36 % of the time, breaks 2 %;
  - the constant sweeps in §9.2;
  - BREAK as Fall (55.3 %);
  - contact without passers-by (52.5 %).
- **N3 (dash hops), cheap form, parked:** thin holes let into the dash bodies' fields. 44.8 % and 43.9 % (with
  `HOP_MIN` 10) vs cpp-p9; the hop maps lose (41–57 / 176). A unit field can't price the cooldown or a blocked landing.
  Patch: `docs/redo/patches/P9_N3_hop_fields.diff`.
- **The user's question (weak bodies dying at the altar late):** rare locally outside 01boss-battle (15 of 601 deaths,
  262 gems). The bags handed over die in Heal (2,134 gems). On 01boss-battle, 500–3,700-gem bags channel 50–370 turns
  and are taken. Candidate: abort a doomed tribute (§9.4).
- **New bars:** `bots/cpp-p9` (frozen = `submissions/cpp-p9.zip`, builds from a clean unzip) and `bots/spar-meta`.
  **Not uploaded (user, 24 Oct): improve first, upload p10.** The user put 35 top-team replays on our weak maps in
  `replays_from_others/even_better_p9` (all losses). The next session studies them by map feature, adds web research for
  new ideas, writes `docs/nav/TOP_P9.md`, then builds p10 and judges it vs cpp-p9 and cpp-p8.
- **Next:**
  1. Read cpp-p9's ladder losses when they come in. Did the crushed tier move (deaths 16.6 a game, contact hit share,
     `engage.py` / `flee.py`)? Does the stance over-commit against stronger fighters (U-P8.9)?
  2. N4: the crew's shop priced by the takes it unlocks.
  3. N5: the closing race.
  4. N3 in its portal form (§6 N3; §9.5 says why the cheap form lost).
  5. The tribute abort (§9.4) and a better break for bag carriers (U-P8.10).

## 24 Oct, evening: cpp-p8's 67 ladder losses read (analysis only, no bot code)

All in `docs/nav/LADDER_P8.md`. The 68 bundles in `replays_from_others/cpp-p8` (one duplicate) were decoded, flipped,
tiered by opponent behaviour (no names in the bundles) and measured with the existing scripts plus six new ones.
- **Two kinds of loss, two fixes:**
  - **20 close losses** (19 of them against non-top families) are an economy race. We die less and earn more gold, at
    equal HP. We gain 832 gems a game to their 1,035; contested groups are 153 vs 286 of that.
  - Our crew under-gains (Marcella 80 vs 197). Their crew hits elk (43–60 % of camp hits), ours wolves.
  - Three of the close losses were lost in the last rounds with the win reachable. dd99fc94: 926 banked + 93 in bags,
    no two bags in sight of each other.
  - **33 crushed losses** (every T1 / T3 game) are fights: we die 16.6 a game, they 4.3. The gap opens at a median
    r315, after an even start.
  - We lose the early fights at **equal max HP**: 8.7 hits and 0.6 casts a fight to 15.1 and 1.9.
- **Structural (same in p6's losses):** in contact our melee hit a champion on 16–24 % of rounds and move away on
  38–48 %; theirs 31–48 % and 21–26 %.
  - Our "mixed" responses (a hit or two, then walking that doesn't escape) die 32–84 %.
  - Their healthy melee commits 1.7× as often and trades 4.7:1; ours 0.9:1.
- **Dash hops:** on 13 of the 30 maps a dash over a one-tile hole strip brings 21–100 % of the value 10+ rounds closer.
  Our walk fields ignore it. 25 losses were on maps with ≥ 40 %, and only 4 of those were close.
- **Code found:**
  - `Kit::stun_enemy` has no caller (kit.cpp:122), so Heart of Ruin's stun dash never hits a champion;
  - our Heart of Ruin buys Strength (theirs Focus);
  - our crew first shops at r282–r427 (theirs r87–r202).
- **U8–U10 answered** (LADDER_P8 §4.5–4.7):
  - the bank cap isn't punished: hoards 8 of 38 → 4 of 67;
  - opening fights isn't the lever, answering theirs is (67 kills to 352);
  - the dash's saved rounds became more small takes.
- **Tool fault:** `farm.py`'s capture gems over-count on 18 of 67 games, so a first-pass "their takes are 40 % richer"
  was withdrawn. Use the new `gain.py` (bag increments) for gem totals until it's fixed (U-P8.1).
- **New scripts** (`tools/replay/farm/`, README): `oppsig`, `gain`, `engage`, `flee`, `fightctx`, `hops`, `hopmap`.
- **Next (LADDER_P8 §7):**
  1. N2 + N1 together: Heart of Ruin's stun dash on champions and a Focus build; the engagement stance (commit or
     break once, hold it, flee only when the escape works; team focus).
     - First trace the "mixed" cause with the TRACE `flee` line (U-P8.2).
  2. N3: a dash-hop distance for dash bodies (portals over one-tile hole strips, fed into the prices and the opening).
  3. N4: the crew's shop priced by the takes it unlocks.
  4. N5: the closing race (team mode via byte 7).
  5. N6: contested groups priced as a race.
  - Judge each against cpp-p8 and spar-meta over 8 jitters; any head to head against `cpp` is read against the 43 %
    null.

## 24 Oct, p8: the top teams' habits built; 64.8 % vs cpp-p7, 90.0 % vs spar-meta; shipped `submissions/cpp-p8.zip`

All in `docs/nav/LADDER_P4.md` §11 (the plan: `docs/archive/COPY_PLAN.md`; the evidence: `TOP_TEAMS.md`).
- **Kept in `bots/cpp`**, in order, each judged over 8 jitters:
  1. **The dash on every cooldown** (`nav.cpp` L4): bag or not, Safe walks too; held only while an enemy is in sight;
     never into a camp's or enemy's reach. Plus the reset after a walk onto a hurt camp (`follow_hit`). 61.6 % vs p7.
  2. **Our own altar lock** just before our tribute (`place_lock`, `beh.cpp`): 86.6 → 90.0 % vs spar-meta.
  3. **The top teams' draft core with kits:** Varg, Vesper, Marcella, Heart of Ruin, Vendetta.
     - Marcella: bank 1.3 + 2 gold a gem tributed, Treasure → Jungle Strength → Bruiser, opens from range 4
       (`KIT.fight_rng`).
     - Heart of Ruin: its landing dash on the farmed group every cooldown (`Nav::dash_camp`); a travel dash never lands
       next to a camp.
     - **61.4 % head to head** vs the build before it.
  4. **Bank cap 50 + the win line** (score + the bags in sight ≥ 1,000; `prices.cpp`): 61.6 → 65.0 % vs p7.
  - **Final: 64.8 % ± 1.4, margin +144 vs cpp-p7 (all 8 runs won); 90.0 % ± 1.2, +414 vs spar-meta.**
- **Not kept** (patches in `docs/redo/patches/P8_*`):
  - the fold out of spawn (54.2 %);
  - opening even fights from 6 (level, deaths +1.3; the 1.13×-HP form lost);
  - Marcella alone in Varg's place (55.8 %);
  - Ren for Varg; Marcella's bank 1.0 / 1.6; caps 35 / 80.
- **Found:**
  - **A jittered head to head has a 43 % null** (an exact copy vs `cpp`: 43.1 %, LADDER_P4 §11.2). Read h2h against it.
  - `gem_count()` on an ally out of vision throws (error 97).
  - `duel` is not what stops our fights; the reach was.
  - Walking is 40 % of body-rounds (`tu.py`).
- **KPIs p7 → p8 vs spar-meta** (`kpi.py`):
  - Vesper casts 6.0 → 10.2 a 100 live rounds (dash 2.2 → 6.2);
  - camp hits 12.4 → 12.9 (target 15 not met);
  - banks 30 → 32 a game, median bag 18 → 21;
  - locks 0 → 4.8 a game.
- **Ship:** `submissions/cpp-p8.zip` = `bots/cpp/src` (28 files, `TRACE 0`). It builds from a clean unzip, and
  `.gitignore` keeps it. Uploading is the user's step. **New bar: `bots/cpp-p8`** (frozen) + spar-meta.
- **New tools:** `tools/replay/farm/{kpi.py, arena_kpi.sh, tu.py, duel1.py}` (README); the TRACE-only `tu` line
  (`main.cpp`).
- **Cleanup rule (user, 24 Oct):** delete all of `runs/arena` at every session end, the cache included. It had
  reached ~82,700 files (522 MB) on the iCloud Desktop and crashed the site's upload file picker. `arena.py` rebuilds it.
- **Next:**
  1. Read cpp-p8's ladder losses (`replays_from_others/cpp-p8`) with `kpi.py` plus §10's scripts. Questions: did the
     hoards go (U8), and the fights they start?
  2. Camp-hit time: where the dash's saved rounds go (U10, `tu.py` on a TRACE copy).
  3. The teleport with its jump fed into the farm walks (U6).
  4. Contested openings (01elk-arena, U7).

## 24 Oct: cpp-p6's ladder losses read; recall fix + idle-heal kept (57.8 % vs cpp-p6, 82.3 % vs spar-meta); shipped `submissions/cpp-p7.zip`

All in `docs/nav/LADDER_P4.md` §10.
- **New bars (user):** `bots/cpp-p6` (frozen = `submissions/cpp-p6.zip`) and `bots/spar-meta`. **A piece goes in only if
  it beats cpp-p6 head to head**, even if it gains vs spar-meta. spar-meta's Vesper now farms all game (its hunt
  phase deleted, LADDER_P4 §10.3): `cpp` (= p6) scores 75.5 / 73.4 % (two jitter sets) against it, 87 % before.
- **What moved on the ladder (38 p6 losses vs p5's 19, §10.1):**
  - Vesper deaths 5.9 → 2.6 a game; our Vesper made 181 of their 313 deaths.
  - Gold gap 2.6× → 1.4×.
  - The crew dies more (crew gold sends it to lone clusters).
  - Banked unchanged (360 vs 932).
- **Losses by kind:** hoard 8, economy 14, small-map fights 6, gem-gated 6, 01islands 4.
- **Found (§10.2):**
  - **The hoard:** our Vesper ended 01the-farm holding 980 gems (lost 25–1012), because the Bank rate price caps at
    ~11 and the main counts gold 3×. 8 of 38 losses ended with 100+ carried.
  - **Ren stuck 884 rounds at 10 % HP:** `safe_recall` stepped away from a *sleeping* camp and never recalled.
  - **00pilgrimage:** the ladder's bodies teleport across the hole river, saving 112 tiles a jump.
  - **01islands:** the crew idles at 51–58 % HP.
  - **Draft:** Varg is in 9 of their 38 drafts, Marcella in 23.
- **Kept in `bots/cpp` (§10.3–10.4), each judged against both bars over 8 jitters:**
  1. `_rc`: `safe_recall` fears awake camps only (`beh.cpp`). 51.2 % vs cpp-p6, 74.5 % vs spar-meta.
  2. `_ih`: a hurt body with nothing to take goes home to heal: the no-enemy heal is zeroed only while a take is
     priced (`rawb > 0`, `prices.cpp`). 53.0 % / 81.4 %.
  3. `HEAL_NOENEMY_HP` 0.5 → 0.8 (`prices.h`; 0.4 / 0.5 / 0.65 / 0.8 = 51.9 / 53.0 / 57.7 / 57.8 % vs p6).
     **Final: 57.8 % ± 1.2, margin +71 vs cpp-p6; 82.3 % ± 1.5, +326, deaths 4.2 vs spar-meta.**
- **Tried and not kept** (diffs in `docs/redo/patches/LADDER_P4_*.diff`):
  - bank by order size (EOQ), lost;
  - bank end-aware or when the bag wins (+3–4 vs spar-meta, 48–49 % vs p6);
  - the crew's early shop (47 % vs p6);
  - Varg → Marcella (**35.3 % vs p6**; checklist in `docs/CHAMPIONS.md` "Swapping a champion").
- **Teleport: built and parked.** The takeoff planner works (`docs/redo/patches/LADDER_P4_tp_planner_patch.py`), but the
  farm prices never pick the groups behind a shortcut. Next form: feed the plan's cost into the walk in `price_all`.
- **Ship:** `submissions/cpp-p7.zip` = `bots/cpp/src` (28 files, `TRACE 0`). It builds from a clean unzip, and
  `.gitignore` keeps it. Uploading is the user's step.
- **Watch:** iCloud put `* 2` copies into `bots/cpp/.cambc` and a `cp -R` hung for 23 minutes. Run
  `find bots -name '* 2*' -delete` before jitters.
- **p7 vs p6, head to head** (8 jitters × 80 games): 370W/270L, 57.8 % ± 1.2, margin +71 ± 16. Gems 768 vs 697,
  deaths 6.3. p7 won the majority in all 8 runs (43–50 W of 80), and its margin was positive in 7 of 8 (−12 to +129).
  The per-map table was not kept: re-run `OPP=cpp-p6 sh tools/jitter.sh cpp` (~4 min) if needed.
- **New bar:** `bots/cpp-p7` (frozen = `submissions/cpp-p7.zip` = `bots/cpp`) + spar-meta; a piece must beat cpp-p7.
- **The user's side work (24 Oct)** is to go into p8 next session. Part of it is the top-team study in
  `other_stuff_for_now/` (no code): `COPY_PLAN.md` = the plan, `TOP_TEAMS.md` = the evidence (78 wins of three top
  teams vs cpp-p6's losses). Ask the user what it is and where it lives (files,
  branch, `git status` / `git diff`). Merge it into `bots/cpp` one change at a time. Judge each against cpp-p7 and
  spar-meta over 8 jitters, then ship what wins as `submissions/cpp-p8.zip`.
- **Next:**
  0. The user's side work → p8 (above).
  1. When p7's ladder replays come back, re-run §9/§10's measures plus `bagrisk`, `stuck` and `stall`.
  2. Teleport with the jump fed into the farm walks.
  3. Contested openings (01elk-arena: side A loses the r1 centre fight every time in the mirror).
  4. Fights they start (they kill 226, we kill 58 there; 70 % of our deaths are alone, 82 % while walking).
  5. A Marcella kit before any swap.

## 23 Oct, night: cpp-p5's ladder losses read; Vesper farms all game + ranged hits + crew gold kept (86–87 % vs both bars); shipped `submissions/cpp-p6.zip`

All in `docs/nav/LADDER_P4.md` §9.
- **What moved on the ladder** (19 cpp-p5 losses, mostly to top teams, vs cpp-p4's 23):
  - HP is closed: our max HP matches theirs at r300/600/1000.
  - Deaths 15.5 → 14.2 a game (theirs 7.0); we start half the fights (28 % before); melee move + attack 0 → 9–17 %.
  - Gold is not closed: they earn 2.6× ours, and the gap is already open by r300.
- **Where we still lost (§9.2):**
  1. **Our Vesper hunted alone and died** 5.9 times a game (theirs 1.3), 66 % of those deaths alone. The cause was
     R9's hunt phase. Their Vesper farms: 64k gold vs our 24k, 121 elk takes vs 8.
  2. **Elk**: our hits are as strong as theirs; our bodies weren't there.
  3. **The crew doesn't take gold** (`ROLE_GOLD` 0.05).
  4. **Builds**: they buy Treasure first on almost every body.
  5. **Shop and crystals**: their Vendetta buys at r70, ours at r330; they buy teleport crystals, we don't.
- **The Vesper trace (§9.3)**: the walks were Heal steps through `safe_recall`, Farm standing with the attack
  unused, and Kill walking past an enemy already in reach.
- **Kept in `bots/cpp`**, each judged against both bars over 8 jitters (§9.4):
  1. **Ranged hits**:
     - `kite_shot` (`beh.cpp`): shoot instead of stepping away only when no enemy can hit me this round. The
       "or the step is futile" form lost: deaths +2.
     - `follow_hit` on a body that stood still.
     - `kill_fight` shoots the enemy already in reach.
  2. **Vesper farms all game**: the hunt phase, patrol and `Beh::Hunt` deleted everywhere (`apply_phase` in
     `champs.cpp`).
  - Together: **vs cpp-p4 83.8 % ± 1.7, margin +382, deaths 5.0** (p5: 63.9 %, +221, 9.1); **vs spar-meta
    85.5 % ± 0.8, +377, deaths 6.0** (p5: 69.8 %, +184, 10.8).
  3. **Crew gold** (`ROLE_GOLD` crew 0.05 → 1.0, `champs.h`): **vs cpp-p4 85.8 % ± 1.0, +418, deaths 4.8; vs
     spar-meta 87.0 % ± 2.5, +395, deaths 5.5.** A small edge (~1 SE) but ahead on both bars and on margin.
  - Elk came with it: 22.2 elk takes a game after r300 locally (spar-meta 13.2), so §6's elk piece isn't needed.
- **Tried and lost:** the meta draft with our Str builds (57.8 / 59.4 %).
- **Queued at the session end** (each on `_k` = `bots/cpp`):
  - meta draft with Focus builds: lost (75.0 / 84.7 %);
  - crew gold 1.0: **kept** (85.8 / 87.0 %, margin +418 / +395: `ROLE_GOLD` crew 0.05 → 1.0, `champs.h`);
  - the ladder's builds: lost (81.4 / 84.1 %).
- **New scripts**: `tools/replay/farm/{elk,shop,campdmg,hitshare}.py` (README).
- **Ship:** `submissions/cpp-p6.zip` = `bots/cpp/src` (28 files, `TRACE 0`). It builds from a clean unzip, and
  `.gitignore` keeps it. Uploading is the user's step.
- **Next (LADDER_P4 §6 status):**
  0. **p6 vs p5 head to head** (8 jitters, all 40 maps both sides): **475W/165L, 74.2 % ± 1.4, margin +245**,
     deaths 6.3. So the user uploads p6 and brings back *its* ladder replays (`replays_from_others/cpp-p6`) instead
     of more p5 ones; read them first with §9's measures.
  1. Give `bots/spar-meta` the farming Vesper (it may be edited to play more like the ladder; note it in LADDER_P4),
     and re-judge `cpp` against it.
  2. The teleport shortcut (design in §9.4, API in `cambc.h`: `consumables()[tp_crystal].use(dest)`,
     `is_teleporting()`).
  3. The crew's gold and an early shop (crew gold is in; next its early shop: the ladder Vendetta buys at r70).
  4. Death time, then bank legs.
  5. When cpp-p6's ladder replays come back, re-run §9's measures.

## 23 Oct, late: cpp-p4's ladder losses read; the routing deep dive closed; walk fix + Bruiser builds + fight kits + follow-up hit kept; shipped `submissions/cpp-p5.zip`

All in `docs/nav/LADDER_P4.md`.
- **The ladder said** (23 cpp-p4 losses vs cpp-port's 57):
  - The routing gains showed: 24 % of takes start at a respawn, vs 12 % before and 24 % for them.
  - Routing was not the gap. The gap is the economy chain:
    - they earn ≈2.2× our gold (8.3k vs 3.7k) and spend it on Bruiser items, so they carry ≈2× our max HP;
    - so they win fights, deaths 4.2 vs 15.5;
    - so they farm elk and take the kill gold.
  - We spend 13 % of body-rounds dead, they spend 4 %. Their legs are as long as ours; they just make 55 % more of
    them.
- **The judging lesson:** self-play hid it all (LADDER_P4 §4). The deep dive is closed in `docs/nav/README.md` and
  `POSTMORTEMS.md`. The bars are now `bots/cpp-p4` (frozen) **and** `bots/spar-meta`, which has the ladder's draft
  and Bruiser builds. Judge every change against both.
- **Kept in `bots/cpp`**, each judged over 8 jitters:
  1. **Walk fix** (`walkf`, `beh.cpp`). The stall guard measured straight-line progress, so on bent walks it failed
     every long bank (01shortcut: 115 bank fails, 0 banked; road-of-riches 0–1009 on the ladder). vs cpp-p4: 55.9 %,
     margin +87.
  2. **Bruiser builds** (`champs.cpp`): Bruiser Health on every body beside Power Strength, the main's gold passives
     first. vs spar-meta: 55.6 → 63.8 %.
  3. **Fight kits** for Willow, Tavi and Heart of Ruin in `fkit` (`prices.cpp`; `HOR_DMG_X` is a GUESS). 65.5 %,
     deaths 11.5.
  4. **The follow-up hit** (`follow_hit`, `main.cpp`). Melee may move and attack in one turn [rules]. The ladder's
     melee bodies did it on 25–30 % of their attacks, ours on 0 %; now 15–18 %, and Vesper walks then hits with its
     reset.
- **Final build:** vs spar-meta **69.8 %**, margin +184; vs cpp-p4 **63.9 %**, margin +221, deaths 9.1.
- **Ship:** `submissions/cpp-p5.zip` = `bots/cpp/src` (28 files, source only, `TRACE 0`). It builds from a clean
  unzip, and `.gitignore` keeps it. Uploading is the user's step.
- **RL (asked):** not now (LADDER_P4 §7): too few games, 100k fuel a turn, the generated-binaries rule, 26 days left.
- **Cleaned:** the scratch bots, 24 GB of `runs/arena` run folders (the cache is kept), the trace bundles. There
  are no `* 2*` files.
- **Next:**
  - The user uploads cpp-p5 and brings back the replays (`replays_from_others/cpp-p5`). Re-run LADDER_P4's
    measures on them: gold, max HP by r300, deaths, hit back, move+attack, time dead.
  - Then LADDER_P4 §6 in order: ranged hits (Vesper walks 1,036 times with an enemy in reach: trace why), the meta
    draft, elk farming with the new HP, death time.
  - The measures are scripts now: `tools/replay/farm/{freehit,mvatt,noback,goldsrc,timeuse,takes}.py` (usage in its
    README).

## 23 Oct, end: routing piece 4 (the capture guard) kept in its smallest form (ROUTING §4.6); shipped as `submissions/cpp-p4.zip`

- **Verdict:** kept. The capturer stays on its spawn tile, and a non-carry leaves a cleared group only once an ally
  stands on one of its spawn tiles (`beh.cpp:253`). The lower-slot claim no longer pulls a lone capturer off
  (`lone_capture`, `prices.cpp:235, 358`).
  - **Over 22 jitters vs `cpp-port`:** 59.2 % (1042 of 1760), margin +71. The §2.7 build scores 57.2 %, margin +48.
  - **On every set C is ahead or level:** its own 8 jitters 59.1 = 59.1 % (margin +77 vs +49), 6 fresh jitters
    57.9 vs 56.2 %, 8 new jitters 60.3 vs 56.4 %.
  - **Captures:** delay p90 15 → 9 rounds; captures over 10 rounds 15.5 → 8.0 %; steals 1.62 → 1.82 a game.
  - **Flat or better:** deaths 11.8 → 11.4, rollovers 6.44 → 6.37, faults 0 in 1,760 games.
- **Measured before building (U4.3):** only a spawn tile resets a capture. Enemies 1–3 tiles away never did, and
  our own step-offs were about 2/3 of our resets. That is why the leave rule is what works.
- **Dropped** (diffs in `docs/redo/patches/ROUTING_P4_{A,B,D,E}.diff`):
  - A, as designed: the progress price outbid kill and heal (kills 12.4 → 10.6, deaths +1.8). 49.1 %.
  - B: "a capture needs one body" held capturers for good, so the other team cleared more. 53.3 %.
  - D: REWARD_SEEN steal candidates. 54.6 %, deaths +1.1.
  - E: the GUARD_R guard. 57.1 %.
- **Judging, learned:** per-map outcomes are near-fixed per build and flip on one-line changes. C vs the §2.7 build:
  - Worse: 00packs 5 vs 31 of 44, 01hooks 13 vs 36.
  - Better: 00elkring 40 vs 16, 00fragment 36 vs 22.
  - D wins 00packs-B 14 of 14 where C wins 1 of 22.
  - The 00packs-B game splits at r22 on a capture that is 2 rounds faster, so these maps are snowballs, not a capture
    bug. So 8 jitters under-state the spread: use 14+ jitters on the same sets (ROUTING §9).
- **Ship:** `submissions/cpp-p4.zip` = `bots/cpp/src` (28 files, source only, `TRACE 0`). It builds from a clean
  copy, and `.gitignore` keeps it. It is not uploaded yet: that is the user's step (`cambc` submit or the site).
  `bots/_cpp_j*` copies are deleted, and there are no iCloud `* 2*` files.
- **Next (user, 23 Oct):** the user uploads `cpp-p4.zip` and brings back its ladder replays. The next session reads
  them against cpp-port's 57 losses (`docs/nav/REPLAYS.md`). If cpp-p4 holds up, the session moves on to **items and
  gold** (`docs/redo/10_GOLD_ITEMS.md` §5: gold income, the gold tiebreak, and what items speed up farming). Lesson
  from R9: the gold redesign lost 24W/46L because its premise came from 2–3 games, so measure first, over all 40 maps
  and the top teams' replays, then change one piece at a time.

## 23 Oct, close: routing piece 5 (exposure) built in six forms, all lost, not kept (ROUTING §5.6); `bots/cpp` = the §2.7 build

- **Verdict:** no exposure price beat the kept 59.1 % over 8 jitters, and deaths never fell (11.6 → 12–13 in every
  form). As designed (P_NEAR deleted, risk out of the farm and bank value, EXPO_X 1.0) 37.5 %, margin −148; at 0.3
  49.5 %; the best form (flat P kept, exposure only from out-of-vision memory and sightings on farm legs, death
  cost from the risk-free price) 51.9 %, margin −3. **Null test** (the same code at EXPO_X 0, so the kept play plus
  only the machinery's fuel): also 51.9 %, rollovers 6.5 → 7.4 a game. So the price adds nothing over its own
  machinery. Table in §5.6, diffs in `docs/redo/patches/ROUTING_P5_exposure.diff`.
- **Judging, measured:** the kept build on 8 fresh jitters (J 200 … 4000): J ≤ 2000 56.3 % (vs 59.1 % on its own
  set: some selection luck); a flat burn costs no wins up to J2000 (rollovers 4 → 11), then J3000 37/80, J4000
  19/80. Why G loses 4–7 points with identical play is open (enemy-dependent fuel on fight turns [guess], or 8-jitter
  sets move more than ± 1.4). Judge on the same J set and re-run the kept build fresh when a gap is under ~4.
- **Learned:** the flat `P·bag` veto and the bank's `(1+P)`/`sig(near_e)` do real work (U5.6). Exposure helps spread
  maps (00elkring, 00interlock, 01shortcut, 00expanse) and wrecks contested single-prize maps (00contest 15 → 4/16,
  00stampede 16 → 8, 01hooks, 00ambush): a body hesitating alone breaks the crew's commitment [guess]. Rollovers
  +1 a game in every form.
- **Not run:** the DMG_X 0.6 re-test, which was to sit on a kept piece 5.
- **Restore copy:** `bots/cpp` is untracked in git; the kept source was rebuilt from the cache hash 29c3eca5559fc1d9
  and copied back. Committing `bots/cpp` would make the next restore a `git checkout`.
- **Ladder:** no zip (user: ship once 4 and 5 are done; 5 is now closed as not built).
- **Next:** piece 4, the capture guard (ROUTING §4), judged over 8 jitters against the kept build's runs
  (`runs/arena/cpp-vs-cpp-port-20261023-124218` + `cpp_j*-vs-cpp-port-20261023-124*`). Keep its fuel flat (no new
  work on every `price_all`; rollovers must not rise). Contested prizes may want commitment [guess], so the guard
  should hold the crew on the prize.

## 23 Oct, final: routing piece 3 re-looked, not built (ROUTING §3.6); `bots/cpp` = the §2.7 build

- **Verdict:** the need is right as it is. Every way of moving it lost over 8 jitters against the kept 59.1 %: DMG_X
  0.6 in `clear_model` 55.9 %, DMG_X 0.6 on the live take test only 51.6 % (deaths 11.6 → 12.9, gems lost 103 →
  123), live damage × 1.25 53.9 %, `GROUP_UNTIL` 200 54.2 %, `GROUP_UNTIL` 100 56.1 %. `bots/cpp` is the §2.7
  build (J0 re-run 45W/35L, the same as before), plus TRACE-only fields in the clear trace (`beh.cpp:183`,
  `beh.h:18`).
- **Measured (U3.2):** finished solo clears lose 0.54× the all-awake damage (p75 0.66, n 1,249), but that sample
  holds only clean clears; real takes meet enemies, which is what the margin pays for. Group maps stay 35/40 at
  every DMG_X / TANK_K. Bodies 3–5 collect 12/6/2 by r300 in every build, even with no stack mode: it comes from
  the carry rule, not from the need.
- **Gotcha: iCloud.** The repo is on the iCloud-synced Desktop. It dropped stale copies (`beh 2.cpp` ... 27
  files, 12:05 piece-2b code) into `bots/cpp/src`, which broke two jitter builds, and it brings back deleted
  `bots/_*` folders. They were moved to the session scratchpad. Before any build run `find bots -name '* 2*'`;
  better, move the repo off the Desktop or turn off Desktop sync.
- **Ladder (user, 23 Oct):** ship only once every routing piece we are building is finished; no partial build goes
  up, so there is no zip for the 24 Oct sprint. `cpp-port` stays on the ladder.
- **Next:** piece 5 (exposure, ROUTING §5) before piece 4. Every piece-3 loss ran through deaths. After it, re-test
  DMG_X 0.6.

## 23 Oct, last: routing piece 2 + 2b on `bots/cpp`: the altar choice kept, the leg price and rotation scrapped (ROUTING §2.7)

- **Result (8 jitters = 640 games vs `cpp-port`):** `cpp` **378W/262L (59.1 % ± 1.4), margin +49**. Piece 1 alone
  on the same jitters: 354W/286L (55.3 %), margin +57. Faults 0, `TRACE` 0, rollovers 4.0 → 4.2 a game (0.8 by
  r100). The as-designed build (leg price + rotation) lost 37W/43L, margin −32; its diff is
  `docs/redo/patches/ROUTING_P2_leg_rotation.diff`.
- **Kept:** the runtime AW rows (altar → group-anchor walks, one field a turn, `world.cpp:195`, `main.cpp:210`), and
  `bank_altar` picks the open altar with the least added walk to the held FARM target, else the best FARM candidate
  (`prices.cpp:161`). The detour to the altar fell from a median of 6 to 4 tiles. The BANK price, BANK_NEAR, the farm
  detour term and the carry (main / second / lowest) are unchanged. Piece 1's `Mem::lastcap`/`capgold` (written,
  never read once 2b went) are deleted; after that, J0 went 45W/35L, faults 0
  (`runs/arena/cpp-vs-cpp-port-20261023-125911`), the same as before the deletion.
- **Scrapped:** the price `bag / (added + chan)` made banks rarer and bags bigger (banks 27.3 → 24.5 a game, first
  bank r146 → r162). Rotating the carry gave bodies 3–5 gold but took it from the second, and kills fell (12.8 →
  8.9); concentration wins fights, as in 10_GOLD_ITEMS. Every mix of the two lost to the altar choice alone (table
  in §2.7).
- **The arena gap was smaller than the ladder's:** piece 1 already banks 27 times a game here, and its altar was
  already the best on the way 84 % of the time. Bodies 3–5 still hold few gems by r300 (64/29/11/5/2); that is piece
  3's to fix.
- **New judging method, `tools/jitter.sh` + `tools/jitter_sum.py`:** one 80-game run moves ±5 wins on any change, so
  a build runs as 8 copies that burn J loop steps a play turn (same strategy, different chaos). `sh tools/jitter.sh
  cpp` takes ~6 min, prints win % ± SE, margin and the bank measures; copies are `bots/_cpp_jJ` (delete after).
  Calibration: `cpp-port` vs itself over 7 jitters 49.8 %. ROUTING §9 now says to judge this way.
- **Ladder:** not zipped. `cpp` beats the bar by 9 points over 640 games; a zip for the 24 Oct sprint is the user's
  call.
- **Next:** piece 3's re-look (ROUTING §3.5: RATE_X 3 is refuted; check the damage side DMG_X / TANK_K and the ggems
  test, then build the corrected need), judged over 8 jitters against this build's 8 runs
  (`runs/arena/cpp-vs-cpp-port-20261023-124218` + `cpp_j*-vs-cpp-port-20261023-12*`).

## 23 Oct, later: routing piece 1 (respawn timing) built on `bots/cpp`, kept (`docs/nav/ROUTING.md` §1.6)

- **Result:** `cpp` vs `cpp-port` **46W/34L, margin +72**, g/r 0.39, deaths 10.4, 13/40 maps won from both sides,
  faults 0. Unchanged `cpp` (the noise floor) went 37W/43L, margin +19.
- **Built:** a Resp group is priced at full HP with `wait = until − r − walk` as plain rounds; `WAIT_MAX` 15 [guess]
  prices a longer wait 0. The body waits at the Ring instead of `return Done`. Captures are detected in
  `Mem::update`, because `farm()` never ran on the capture round. **Slot code 4 = CAPT** (+ mi, 2 rounds) with
  `lastcap`/`capgold` for 2b. The handoff's EXCL is gone, and `observe_group`'s +1 is gone (U1.2).
- **The cap mattered:** without it 35W/45L (bodies stood 11 % of rounds, first shop r70 → r88). Every cap from 8 to
  25 wins 44–47 of 80.
- **Measures (base → capped):** body at the respawn 13 → 26 % (theirs 31), first hit 47 → 33 rounds, elk kills
  +7 %, takes/game 60.8 → 64.2, captured gems 1,159 → 1,198, deaths 12.9 → 10.4. Watch: rollovers 3.0 → 4.0 a game.
  Worst map 00eight: an enemy Vesper snowball (42 of our 57 deaths); the traced copy of the same build won it. That
  is piece 5's job.
- **U3.1 and U3.5 (no bot code):** the fitted clear rate is ~1.25× base Str at the start and ~1× `s.S` (median, 3,412
  solo clears), so **RATE_X 3 is refuted**. At the fitted rate the need barely moves (35/40 group maps; 31 at 3.0),
  and maps stay group maps through `ggems ≥ 0.7`. Piece 3's premise needs a re-look (damage side, DMG_X / TANK_K,
  and the ggems test) before it is built (ROUTING §3.5).
- **Tools:** `tools/replay/farm/arena_decode.sh runs/arena/<run> W` decodes an arena run for the farm scripts
  (flip `--arena`, unique ids for `farm.py`; ~30 min for 80 games). `tools/mapdump.inc` now runs `--rounds 40`
  (`--rounds 3` cut the dump).
- **Arena note:** deterministic and cached by source hash, but chaotic: any change flips about half the games. Sweep
  a new constant's neighbours to check that a win is real.
- **Ladder:** not zipped. Piece 1 alone could go up (it beats the bar), but the plan (ROUTING §9) is to ship once
  2 + 2b are in, or sooner if the user wants a 24 Oct sprint entry. `TRACE` is 0 in `bots/cpp`.
- **Next:** piece 2 + 2b (bank leg, every body captures), ROUTING §2, on `bots/cpp`, judged the same way.

## 23 Oct: the routing design (`docs/nav/ROUTING.md`); no bot code changed

- **What it is:** the design for the five pieces in REPLAYS §7's order. Each piece has the facts it rests on (only
  those that held in both halves, §0.1 F1–F9), the current code with file:line, the design, its measures, and
  "Unknowns to check when building". §8 lists every line deleted or redesigned, §9 the build and test plan, §10 all
  unknowns.
- **The pieces:**
  1. **Respawn timing** (P14, P15). A respawning group is priced like a live one, with `wait = until − r − walk`
     counted as rounds. The body waits at the Ring (never on a spawn tile) instead of `return Done`
     (`beh.cpp:207`). Allies learn of a capture from the unused slot code **4 = CAPT** (+ mi, held 2 rounds).
     Deleted: the `return 0` at `prices.cpp:237`, and the EXCL after a handoff.
  2. **Bank leg** (P12). A runtime table of altar → group walks `AW[a][g]` (one altar field per turn). The altar
     is the one with the least `added = ad[a] + AW[a][g_next] − gd[g_next]`, and the BANK price is
     `bag / (added + chan)`. Deleted: BANK_NEAR, and the farm detour term (`prices.cpp:264–265`).
  2b. **Every body captures.** The carry rotates to the slot with the oldest capture (from code 4), with the main
     first until its first emblem (`capgold` from the code-4 captures × static `o.gold`). `ROLE_GOLD` is unchanged
     (10 §4.1 lost).
  3. **Corrected need** (P1, P5). `RATE_X` [guess 3.0, fit first] and `DMG_X` [1.0, test 0.6] go inside
     `clear_model`, which fixes every caller at once. `CHAMP_STR` 50 is deleted. Crews come from the corrected
     need, not the fixed `group_slots` sizes.
  4. **Capture guard** (P13). The Reward price counts progress. Non-carries leave only once an ally is on a spawn
     tile; if an enemy is near, they guard, and the reward value goes into that enemy's kill price. Reward groups
     seen become candidates (steals).
  5. **Exposure** (P3, P8, P9). The flat `P_NEAR` 0.5 is replaced by a leg risk:
     Σ remembered enemies near the me→target segment × decay × duel P(lose) × dcost. It comes out of the value,
     not the rate. No "alone" term.
- **Out on purpose:** a tour planner, arrival-order rules, a cohesion term, an "alone" price, gold valuation, and
  anything per map.
- **Next:** build piece 1 on `bots/cpp`.
  - First run `cpp` vs `cpp-port` unchanged for the noise floor.
  - Judge with `python3 -I tools/arena.py cpp cpp-port --jobs 2` plus §1.4's measures.
  - Two checks need no bot code: U3.5 (re-run `tools/mapstudy.py` with RATE_X 3 and count the group maps left) and
    U3.1 (log solo clears in the trace to fit RATE_X). Both can run in piece 1's session.

## 22 Oct, late night: replay deep dive, half 2 and all 57 (`docs/nav/REPLAYS.md` §6–§9); no bot code changed

- **What it is:**
  - The other 28 losses (20 maps), and all 57 together, run through the same tools. We are team A in all of them.
  - The 9 new maps were dumped with MAPDUMP, and `features_22oct.txt` now covers all 57 games.
  - `halves_22oct.txt` labels H1 / H2.
  - REPLAYS changes:
    - §1 gains half-2 and all-57 columns.
    - §6 checks each fact in both halves.
    - §7 is the plan on the facts that held.
    - §8 is the half-2 and all-57 tables (per label, Q11–Q15, need, crews, opening, deaths).
    - §9 lists what is still open.
- **Login still missing**, so the opponent names are still unknown.
- **Dropped or restated (flipped between halves):**
  - **"We pick nearer"** (H2: 40 vs 43 %; nearer in 8 of 22 rows). Order is about even (all 57: 41 / 39 %).
  - **"Contests go to the second arrival"** (H2: the first hitter took 54 % of theirs). They still capture more:
    57 vs 41 %, and 123 vs 72 steals.
  - **"Stacking gap gone."** They stack a little more in both halves (3+ clusters .26 vs .19), mainly elk crews after
    r100.
  - **"Golems and monoliths from r75":** map- and opponent-dependent (H2: 2 + 2 kills).
  - **"Deaths alone":** in H2 they die alone more often than we do. Walking (82 %) holds.
- **Held in both halves [measured, all 57]:**
  - **Respawn waiting:** a body at the camp at 31 vs 12 % of respawns, and it hits first 92 vs 74 % of the time when
    there.
  - **Elk kills:** 3.8× ours.
  - **Banking:** 30 vs 10.5 banks a game, bags 26 vs 16, detour 2 vs 11 tiles.
  - **Five facts in all 25 rows** (families and buckets): at the respawn more, more banks, more elk, fewer dead trips,
    more bodies out.
  - **Static need too high at every need level.** Clear rate 160 / 194 HP a round, n = 448 / 782.
  - **Opening funnel:** bodies 3–5 capture 6 / 2 / 0 vs 29 / 21 / 8 gems by r300.
  - **Deaths:** 17.5 vs 5.0 a game. Half 2 has half of half 1's deaths in every size bucket, yet its gap opens
    earlier (r265), which points at the funnel and takes rather than deaths.
- **Next:** the routing design, in REPLAYS §7's order, unchanged by half 2:
  respawn timing → banking leg (with every body capturing and shopping) → corrected need → capture guard → exposure
  price. Then build and test on `bots/cpp`.

## 22 Oct, night: replay deep dive, half 1 (`docs/nav/REPLAYS.md`); no bot code changed

- **What it is:** 29 of the 57 C++-port losses in `replays_from_others/new` (22 maps, every opponent family; the
  user's scope: half the folder, losses only). MAPS §7 is redone on them, split by opponent family (by draft; no team
  names in the bundles) and by map feature bucket. Q11–Q15 are answered, plus need in practice (with monolith and
  golem takes), the opening per body to r300, and deaths. §7 says what this changes in MAPS §11's plan, and §8 lists
  the half-2 games.
- **Tools (extended, no new scripts):**
  - `order.py`: Q11, Q12, Q13 leaves, Q15, kills by type.
  - `legs.py`: banks and altars.
  - `hpb.py`: kind × bodies, golem/monolith, by-need with a 2nd arg.
  - `phase.py`: crews by phase, form/split, the opening.
  - `farm.py`: `gtiles`.
  - `report.labels` + `FARM_GROUPS` comma lists, tables per label in `agg`/`cohesion`/`legs`/`order`.
  - Label files: `groups_22oct.txt` and `features_22oct.txt`.
  - `decode.mjs` decodes golems (engine 1.0.3).
  - The README holds the steps.
- **Main findings [measured, 29 games]:**
  - **Order is not the gap.** We pick the nearest live group 42 % of the time, they 36 %; we are nearer in 27/32
    family/bucket rows.
  - **They wait at respawns:** a body within 2 tiles at 31 % of respawns vs our 13 %. They wait ~6 rounds and hit
    first 89 % of the time when they do. They kill 4× our elk.
  - **They bank as a leg:** 29.5 vs 9.4 banks a game, bags 25 vs 15, detour 4 vs 10 tiles (1 vs 11 on big maps).
    Every body banks.
  - **Crews are ad hoc for both teams** (same size per take, 79 % split after). Stacking is only modestly larger.
  - **Our static need is 2–3× too high.** The clear rate is 147–184 HP a round per body, not Str 50. They solo need-2
    groups 68 % of the time and took 153 "untakeable" groups. Golems are taken by 1–5 bodies, monoliths by 2–5, from
    r75/r385.
  - **Contests go to the capturer:** they capture 61 % of contested lives; 78 steals vs 42.
  - **Deaths:** 22 vs 5 a game, 90 % to champions, 82 % while walking.
  - **Opening funnel:** our bodies 3–5 capture 6/2/0 gems by r300, theirs 22/16/11.
- **Next (user): half 2**, the 28 games listed in REPLAYS §8. First, MAPDUMP the 9 maps not yet dumped and extend
  `features_22oct.txt`. Check every §6 fact in both halves. Then the routing design in the new order (REPLAYS §7):
  respawn timing → banking leg → corrected need → capture guard → exposure price.

## 22 Oct, late: the map-and-replay study (`docs/nav/MAPS.md`); no bot code changed

- **What it is:** POSTMORTEMS questions 1–4 from the 40 map files and 11–14 from the 11 ladder losses of R7/R8,
  each tied to `bots/cpp` code, plus a table of map features → routing choice → runtime read (MAPS §9).
- **Tools (new):** `tools/mapdump.inc` (a `map_dump()` to paste into a scratch copy of `bots/cpp`: prints what
  `World::boot` sees as one `MAPDUMP` JSON line; steps in the file), `tools/mapstudy.py` (per-map features, tours,
  a one-crew respawn sim, min cut, margins), `tools/replay/farm/order.py` (next group vs the nearest live one,
  respawn latency). `mapjson.mjs` is dead (needs the deleted `tools/mapgen`); use the MAPDUMP grids for replay maps.
- **Main findings** (tags in MAPS):
  - Respawn is 50–60 rounds on every map; everything else varies 10–100× (size, S 3–5, groups 6–51, altars 1–18,
    spawn gap 1–243, front 2–18 tiles). Fixed constants (OPEN_END, GROUP_UNTIL, crews 3+2/2+2/2+1, near6) can't fit.
  - Greedy nearest order walks +10 % over the best tour (median; max +64 % on 00swirl), all of it in the tail: the
    first 5 picks are already optimal. A naive 2-step walking lookahead is **worse** than greedy on 27/40 maps; with
    value and respawn priced it gains +3 % (median). **A tour planner is not the gap.**
  - The opponents that beat us **react** (next group = nearest live 38 %, top-3 74 %, +2 tiles; ours 28 %, 64 %,
    +4) but **stack** (2.8 bodies per elk, 3.5 per monolith, 35 % of body-rounds in clusters of 3+; ours 1.6, no
    monoliths, 10 %), **reach respawns first** 55 % of the time and 7.5 rounds sooner, and lose fewer trips to recalls
    and deaths (33 % vs 55 %).
  - ≥ 60 % of the value is in groups with need > S on 12 maps; our routing never goes there (need model, Str 50).
  - `group_slots` crews are fixed by S; on a 4-body team neither crew of 2 can take a need-3 group (all of
    01hooks' gems). `rich_group`'s fallback can hand a crew a group it can't clear.
  - The worst maps vs R9 are mostly **shared value and a shared altar** (01hooks, 00swirl, 00split, 00pilgrimage);
    only 01concentrated-wealth is a walking/banking map. No feature correlates with margin beyond |ρ| 0.30.
  - The draft record's `open1`/`open2` are decoded but only traced; on 20/80 map-sides one is a need > S group.
- **Next (user, 22 Oct): a replay deep dive first.** The user downloads more ladder replays, especially against the top teams; that session redoes MAPS §7 on them (Q11–Q15 + Q13's damaged-camp leaves) and checks the verdict below. The design session comes after it. Was: the design session (MAPS §11, closing): the reactive pieces done well and priced as a team: crew sizes
  from the map's needs, head for the next respawn (H4), bank as a route leg, keep the target. Before or alongside it,
  the open measures from our own matches (Q5–Q10, Q15, the need model's real clear times).

## 22 Oct: the bot is C++ now (`bots/cpp`); cambc 3.0.5; the pathfinding/macro deep dive is next

- **The teammate ported R9 to C++** (4k lines, module for module) and it replaced R9 on the ladder. It is
  `submissions/cpp-port.zip` (the uploaded sources, unchanged) and the frozen bar `bots/cpp-port`. The working copy
  is `bots/cpp`: the same sources plus one fix (`kit.cpp`: two references bound into the temporary array that
  `abilities()` returns by value; undefined behaviour, flagged by the compiler).
- **cambc 3.0.2 → 3.0.5** (00_PATCH_3_0.md §1): Prism focus per gem 1.0 → 1.5, `distance_field::copy_from`,
  debug drawings last to the champion's next turn, **5 new maps (40; an arena is 80 games)**. `cambc.toml`
  languages = python, cpp.
- **Baseline [measured, 3.0.5, 40 maps × 2 sides]: `cpp` vs `redo` (R9) 51W/29L**, margin +121, 17/40 maps won from
  both sides, faults 0/0 (`runs/arena/cpp-vs-redo-20261022-175633`). Worst maps: 01hooks (−902 mean, lost from both
  sides), 00swirl, 00split, 01concentrated-wealth, 00pilgrimage (all lost from both sides).
- **The port's `DESIGN.md` / `CONTRACT.md`** aren't in the repo; the user says ignore it (the teammate hasn't pulled).
- **Tooling:** `arena.py` already builds any language (`cambc build --release`). The trace-based navstats columns need
  a `TRACE 1` build (compile-time, `src/types.h`).
- **The deep dive (user): "pathfinding" = ROUTING** (where, when, in what order, with whom); moving a body is
  foundational and done. The user hands over postmortems one at a time; there is no session plan (`docs/nav/README.md`).
- **Done: GST 2026** (`docs/nav/pm/2026-gst.md`, code `github.com/uravt/Battlecode26` v40). Their routing is an
  ordered list of behaviours with a nearest or random target, plus spawn-direction load balancing; good enough for an
  unknown map. Ours is a known-map planning problem (a team orienteering problem with time windows [guess]) that they
  never faced. What we take:
  - Decode the top teams' routes from ladder replays.
  - Measure our greedy one-step camp order against a 2–3 step lookahead.
  - Small leads: a per-group contest memory, choosing the bank altar as part of the route, and Nav loop memory kept
    across goal flips.
- **Done: Gone Fishin' 2023** (`docs/nav/pm/2023-gone-fishin.md`, code `github.com/carlguo866/battlecode23-gonefishin`
  `src/submit26_final`). Also reactive: nearest known well, drop-off at the HQ nearest the well, and **marks on
  targets gone bad**: congested (cleared at the next delivery), dangerous (60 rounds), islands (150/300), each kept as
  a backup, not a ban. Their fixed "centre island" preference overfit the map pool and lost the final to a random
  choice [pm]. Their movement ideas were already taken in R2. What we take:
  - **Our Nav computes a crowding signal no behaviour reads** (`NavRes::Waiting`, `nav.cpp:408`). Measure rounds in
    `Waiting` per camp arrival and bodies on the ring per capture.
  - **Our bad-target memory is only about our own failures** (`EXCL`, `WAIT_EXCL`, `DEATH_EXCL`, `dead_g`). Lead: a
    fading "contested lately" mark per group (with GST's threat memory); check the 8-byte budget first.
  - No fixed side/centre preference that isn't priced from the map (rule 10).
- **Done: Om Nom 2025** (`docs/nav/pm/2025-om-nom.md`, code `github.com/CyrilSharma/Battlecode2025`, real source in
  `templates/*.java.jinja2`). Reactive again: the nearest job in sight, else a random map point ("clever" exploration
  didn't help them). **Their routing gains were job persistence, found in their own replays:** finish what this load
  can finish before refuelling (= our H3), go back to the job afterwards (`returnLoc`), stop flipping targets. Third
  team with a crowding re-pick (skip a ruin for 10 rounds when 2 others are adjacent). Their "Optimal Bug" is already
  R2's L1. What we take:
  - **H3 covers heal, not banking** [code]: a bank replaces a farm when its price beats the farm's × max(1.2,
    1 + 2 × progress) (`upd.cpp:196`). Measure how often a body banks off a camp it could finish.
  - **No "go back to the job"** after a bank or a recall; only the remembered monster HP leans the price back.
    Measure farm goals dropped while the camp was damaged, by cause, and who finished that camp.
  - Our Nav doesn't reset on ring-tile switches (goals keyed by group) [code]; their finals bug can't happen to us.
- **Done: confused 2025** (`docs/nav/pm/2025-confused.md`, code `github.com/mhahn2003/bc25` `java/src/finals`; 2nd,
  top seed). Reactive again; his whole macro came from replays (towers first, **minimise idle time**). New: an **idle
  timer**: 10 turns without an action (walking counts as idle) → go to an unseen candidate enemy base, then across the
  centre. Fourth crowding re-pick (2 builders max, ≥ 8 at a tower), second "back to the job" (`continueBuild`). Lost
  the final to a centre default on a large sparse map with corner ruins: the second finalist of four (Gone Fishin').
  What we take:
  - **Our idle body walks to the bank altar and stands** (`Fall`, `upd.cpp:182`, `beh.cpp:377`), and **a respawning
    camp prices 0 until it is up** (`prices.cpp:237`) [code]. This is H4 (09 §3); on a known map we can predict where
    value appears next.
  - `idle%` in `navstats.py` counts walking as busy; his counter counts it as idle.
- **Done: Just Woke Up 2025** (`docs/nav/pm/2025-just-woke-up.md`, code `github.com/Tim-gubski/BattleCode2025`
  `java/src/v57_Optimaler`, the shipped version by inference; PDF text in `docs/redo/sources/`; **1st place**). The
  winner is reactive too ("Keep it Simple"): ordered state lists, sticky targets, bugnav reset only when the target
  moves > √8, zig-zag exploration. Its finals gains were routing details:
  - remembered empty ruins, gone to **only when the unit has the paint and money to build** (blacklisted 50 rounds
    if crowded or enemy-painted);
  - **a priced refill**: walk on to the next tower if the walk beats the wait at this one; refill at the tower just
    built; `returnLoc` back to the job; "thugging it out" (finish a nearly done build);
  - a narrow, map-derived defense rule (at a central choke, at most 2), the opposite of the broad centre defaults
    that lost two finals;
  - judged on every map, the replays of every lost map, scrims vs the top 20; two features that tied or lost in
    self-play shipped because they beat the opponents' style.
  What we take: **our bank altar is the nearest open one with no wait priced** (`bank_altar`, `prices.cpp:158`);
  idle bodies to the next target (H4) is now backed by the winner and the runner-up; measure altar waits and wins by
  side per map.
- **All five read. "Five postmortems, one picture"** is at the end of `docs/nav/POSTMORTEMS.md`:
  - **They agree:** route reactively and do the simple parts well; macro from replays; keep the target and go back
    to the job; re-pick on crowding (5/5); marks on bad targets with a lifetime that fits the cause; spread units
    without talk; moving is a borrowed, solved part.
  - **They disagree** on positional priors (broad defaults lost, a narrow one won), on judging by self-play, on
    copying code, on the exploration shape, and on memory of targets.
  - **None covers a known map:** visit order (a tour), timing respawns, a joint team assignment for few costly
    bodies, the opponent's route on the same map, banking as part of the route, coordination in 8 bytes.
- **The measures to build before any design** (one arena, `cpp` vs `cpp-port`, all 40 maps; the list in
  POSTMORTEMS "What this means for CAMBC"):
  1. Our camp order against a 2–3 step lookahead (GST).
  2. Target flips per map.
  3. Rounds in `Waiting` per camp arrival; bodies on the ring per capture (Gone Fishin').
  4. Bags and deaths lost per group, and returns there within 60 rounds (Gone Fishin', GST).
  5. Farm goals dropped while the camp was damaged, by cause (bank, heal, flip, partner wait, death), the camp's
     fate, whether our body came back; banks that pull a body off a camp it could finish (Om Nom, Just Woke Up).
  6. The top teams' routes from ladder replays (`tools/replay/`).
  7. Each body's rounds split into productive, walking, waiting, standing; `Fall` rounds with no bag and full HP;
     rounds from each camp respawn to our first body there (and the enemy's); groups never visited (confused).
  8. Rounds a body stands at an altar without channelling, per map (Just Woke Up).
  9. Wins by side per map from each arena run (Just Woke Up).
- **Next (new session): the map-and-replay study** (user, 22 Oct: look at the actual maps alongside replays to
  decide the next step). Its 15 questions are at the end of POSTMORTEMS.md: from the 40 maps (size, groups, altars,
  distances, spawn gaps, greedy order vs a 2–3 step lookahead on walking alone, groups needing two bodies), from our
  matches (where body-rounds go, respawn latency, dropped jobs, crowding, unvisited groups, wins by side) and from the
  top CAMBC replays (circuit or react, respawn timing, banking, bodies per camp, contests). The closing rule: if the
  top teams react camp by camp and our losses are walking, waiting and idle bodies, build the reactive pieces well (H4,
  back to the job, crowding re-pick); if they plan circuits timed to respawns, build a planner. Most of our-match
  measures come from the `TRACE 1` build plus `tools/navstats.py` (extend it, don't add a new tool).

## 21 Oct, session 8: R9 = R8 + the draft fuel fix, zipped (`submissions/redo-r9.zip`); gold design lost

Details are in `docs/redo/10_GOLD_ITEMS.md`.
- **The draft crash is fixed (10 §1).** Before, the 01shortcut ladder game lost its draft: one pick, no memory, the
  team stood still until round 101, lost 0–1019. Now all 35 maps have every pick ours and the memory complete.
  - The nearest altar uses lane arithmetic plus a lazy per-altar field on ties, instead of a step-by-step descent
    (10.9M → 1.65M on 01shortcut).
  - `own`, `altar`, `paths` and `chokes` resume across draft turns under `DRAFT_RESERVE`.
  - The encode runs at the next turn's start.
  - `w.d = {}` when there is no memory.
- **R9 vs strat-sw: 52W/18L**, margin +234, 21/35 maps won from both sides (R8: 51W/19L, +217, 19/35).
  vs `_r8`: 33W/36L (1 CLI error). Faults 0/0.
- **The gold design (10 §3) lost 24W/46L to R8 and is not shipped.** The code is in
  `docs/redo/patches/R9_gold_items.diff`.
  - Its premise was wrong: R8's Vesper holds 36 % of the gold over all 35 maps, not 54–61 % (that was 3–5 games).
  - The build earned 16 % less gold and died more; the build orders are the likely cause.
  - 10 §4.1 lists the ablation (main weight 3.0, Monster, Jungle before Durability).
- **The user's point (10 §5, design notes, not built):** 0–0 games go to gold earned.
  - 01boss-battle was lost on gold from one side.
  - Big maps give us the least camp gold per game.
  - The ladder opponents earn 1.3–3× our gold.
- **R9 vs R8 head to head is a tie (33W/36L):** same play logic, only the draft changed; R9 ships because R8 can
  crash on a heavy unseen map. R9 vs R7 (the ladder entry before R9) is not measured head to head yet; the user runs a
  couple of tests at the next session's start (`python3 -I tools/arena.py redo _r7 --jobs 2`, `_r7` from `8aae86e`).
- **Next session:** gold income and the gold tiebreak (10 §5), measured against the top teams' ladder replays first.
  Then H4 (09 §3; H4.4 is still open). `tools/replay/farm/mapjson.mjs` needs the deleted `tools/mapgen`.
- A newer cambc than 3.0.2 is out (the CLI says so). Not installed; check its changelog at the next session's start.
- Cleaned: `bots/_probe`, `bots/_old`, `bots/_r8` (R8 = git `43e28fc`; its zip `submissions/redo-r8.zip` was deleted: never published, it has the draft crash), the whole `runs/` (arena cache
  included) and the pycache folders.

## 21 Oct, late: R8 built and zipped (`submissions/redo-r8.zip`); H4 is next

- **R8 = R7 + H1 (fuel ledger), H2 (heal deadlock), H3 (finish or leave), H5 (HOLD deleted).** H4 (idle crews) is
  not built. Results are in `docs/redo/09_HOTFIX_R8.md` §7.
- **Results [measured]:**
  - vs strat-sw: **51W/19L**, margin +217, 19/35 maps won from both sides (R7 the same night: 48W/21L, +198, 17/35).
  - vs `_r7`: **37W/32L**, margin +37.
  - Rollovers: 57 a game (R7 236). Deaths 9.0 (R7 11.2). Bags lost 83 (R7 74).
- **Two bugs found and fixed while building H1:**
  1. `s.edps` was read on skipped decides before it was set (AttributeError). It is now set in `sense`.
  2. The decide-cost estimate locked at a cold 1.9M, so 80 % of decides were skipped. Fixed with the `DEC_Q` quantile
     and aging on refusal; skips are now 3–12 %.
- **The `bots/redo` sources** equal the zip byte for byte. `.gitignore` whitelists `redo-r8.zip`. R7 is in git (`8aae86e`) and
  `submissions/redo-r7.zip` (the scratch `bots/_r7` was deleted; recreate it from either for a head to head).
- **Next session:** build H4 from 09 §3 (tank share, the takeable candidate list, Fall heals/escorts, crew gold
  0.3), then ablate in the order H4.4, then H4.1. Add 09 §4's `navstats.py` measures (heal A-B-A, trips per take,
  crew fall %) first, so H2/H3/H4 are measured, not only judged by totals. Read R8's ladder games first; watch
  broken-curve, starfish and bags lost.

## 21 Oct: R7's ladder losses analysed; the R8 hotfix designed (`docs/redo/09_HOTFIX_R8.md`)

- **Input:** 7 ladder losses of R7 in `replays_from_others/redo-r7/` and the user's four observations (zzz, the
  dance, half-done camps, idle crews). No bot code changed this session.
- **Found [measured]:** (1) rollovers up to 791 a game (big-world; the opponent 0). `decide` costs 1.3–2.3M of the
  2.5M budget, `need_k` alone 0.64M, and the F_me rebuild and the first goal build have no fuel check. (2) + (3) A heal
  deadlock: `sense` tests the unseen-hit rule on the tile I moved to, not the tile I was hit on, so `safe_recall`
  steps back into the wolf's range (Varg 84 rounds, Ren 297 A-B-A rounds in one game). Farm's go-line (`SURVIVE` 0.6)
  and heal's line (0.5) disagree, so takes are dropped halfway (Varg: 3 trips, 87 rounds for one take). (4) Crews
  find no takeable group (`TANK_SHARE` 0.6 floor; `near6` holds untakeable groups) and Fall stands at the altar
  (islands: 500–1,084 rounds in fall per crew body). HOLD: up to 623 rounds per body, 0 tributes cancelled.
- **Next session:** build R8 by 09 §6 (H1 first), measure by 09 §4, judge vs strat-sw and vs `_r7`, zip
  `submissions/redo-r8.zip` if it passes. The scratch probe `bots/_r8probe` was deleted; the decoded replays were
  in the session scratchpad only (re-decode with `tools/replay/decode.mjs`; clean the NUL bytes from the stdout first).

## 20 Oct, wrap-up: the codebase cleaned for commit; R7 on the ladder

- **The repo now holds:** `bots/redo` (R7, the ladder entry, = `submissions/redo-r7.zip` byte for byte), `bots/strat-sw`
  (the bar, = `submissions/strat-sw.zip`), `bots/strat` (the closed team-loop line, kept because `strat/MEMORY_LAYOUT.md`,
  `strat/FUEL_MODEL.md` and `tools/mapmodel.py` point into its `parts/`), `bots/starter-python`, `bots/mapdump` (for
  `tools/mapmodel.py`, which the redo's draft code cites). Tools: `arena.py`, `assemble.py`, `navstats.py`,
  `microstats.py`, `champstats.py`, `plog.py`, `mapmodel.py`, `replay/`, `mapgen/` (its `engine.mjs` is used by
  `replay/farm/mapjson.mjs`). Test: `tests/test_comms.py`.
- **Deleted (no code or doc still used them):** the bots `tide` (parked, never committed: only
  `docs/archive/REBUILD.md` describes it), `tzunami444`, `tzunami-lite`, `probe`, `null`; the rollbacks `_r5`, `_r6`; the
  tools built on them or on closed workflows (`bench`, `seeds`, `variant`, `field`, `field_sum`, `belief_fit`,
  `scenario`, `invariants`, `openviz`, `gameviz` + `viz/`, `pair`, `tide_*`, `parity/`, `replay/poc.mjs`,
  `replay/idle.py`, `mapgen/dump.mjs`, `strat/field.txt`); the old zips (`strat`, `strat-imp`, `strat-og`,
  `strat-roles`, `redo-r6`); `maps_old/`; all of `runs/` (the arena runs the `docs/redo/` docs cite are gone; their
  numbers are in the docs) and the caches. Every deleted tracked file is in git history (`git checkout 73c1b76 --
  bots/tzunami444`; the old 2.2 maps are `maps/<name>.map26a` at that commit).
- **`.gitignore`** now commits `submissions/redo-r7.zip` and `submissions/strat-sw.zip` (it used to whitelist the old two).
- **Checks at the wrap-up:** `python3 -I -m pytest -q tests` and `python3 -I tools/assemble.py --bot redo --split --check`
  (results in the wrap-up message); no bot logic changed.
- **Next:** read the ladder results of R7. Open work, in order: X5 (altar locks), tribute denial, the main carry's
  gold share (0.64 vs the top teams' ~0.35); Vesper's kill deaths at P(lose) < 0.1 (08 §9.1); `DUEL_EXP` / `FKIT` are
  guesses, not ablated.

## 20 Oct, end: the fix pass done (08 §9); the ladder entry is `submissions/redo-r7.zip`; last bot session

- **`bots/redo` is R7 = R6 + G3:** `ScanWard.post` returns on a dead body (a rolled-over turn
  ran into the round it died: all 28 ward errors of R6's run) and places no ward while stunned.
- **R7 vs strat-sw: 31W/11L, margin +230, 11/21 maps won from both sides** (R6: 28W/14L, +164). On the 14 maps new
  in cambc 3.0.2: 18W/10L (worst: 01the-farm, 01shortcut, 00quadrants lost from both sides).
- **G1 and G2 were built and dropped** (08 §9.3): G1 + G2 went 20W/21L (passive: fewer kills, lost contested maps);
  G2 alone 29W/13L but lost to R7 head to head 17W/24L (fewer carriers killed). The code is in
  `docs/redo/patches/08_G1_G2.diff`. The cause they targeted stands: Vesper's kill deaths at P(lose) < 0.1 with the
  enemy 5–8 out (08 §9.1).
- **cambc 3.0.2** installed (`.venv`, `cambc init --yes`, `cambc.toml`): SDK identical to 3.0.1, pool 21 → 35 maps.
  A no-`--maps` arena is now 70 games. Rare CLI error `expected at least one module field` fails a game before
  round 1: re-run that map (QUICKSTART_MATCHES).
- **Zipped:** `submissions/redo-r7.zip` = `bots/redo/src` byte for byte (`main.py` + `bot.py`, no bytecode); the
  unpacked zip played 00packs A in `--release` to the arena's result.

## How to run things

```sh
cambc build cpp                                          # C++: every bots/cpp/src/*.cpp (wasi-sdk C++20); warnings are bugs
cambc run cpp cpp-port --map 00collision                 # one game (debug build; the arena plays --release)
python3 -I tools/arena.py cpp cpp-port --jobs 2          # the 40 maps in maps/ x 2 sides, cached; replays in runs/arena/<run>/
python3 -I tools/navstats.py runs/arena/<run>            # Nav numbers; microstats.py: deaths, trade; champstats.py: per champion
python3 -I tools/plog.py <replay or logs dir> [TAG ...]  # read a trace (C++: build with TRACE 1 in src/types.h)
# Python references (redo = R9):
python3 -I tools/assemble.py --bot redo --split          # parts -> bots/redo/src/main.py + bot.py
python3 -I -m pytest -q tests                            # the (Python) comms codec test
```

- Full match usage: `docs/QUICKSTART_MATCHES.md`.
- Ladder replays: download, `tools/replay/fetch-engine.sh` (saves the engine version the visualiser ships;
  `decode.mjs` picks it from the replay header), then `node tools/replay/decode.mjs`; the farm numbers
  from there: `tools/replay/farm/README.md`.
- Keep the laptop cool: `--jobs 2`, one run at a time.

## Gotchas we paid for (all [measured])

C++: `TRACE` is compile-time (`bots/cpp/src/types.h`, 0 on the ladder; a 60-char line costs ~2.9k fuel by the
port's comment). The trace-based `navstats` columns (stuck, osc, idle %, turns/50r, calm deaths) are empty for a
`TRACE 0` build; the replay-based ones (direct, excess, spread, deaths by cause) work on any build.
`abilities()` returns `std::array` by value: never bind a reference to one of its elements.
Items 1–8 below are the Python bots'.

1. **Never `import traceback`.** Its first use froze every champion for ~136 rounds.
2. **`camp_groups()` costs ~0.74M fuel per call.** Call it once and keep the objects. `camp.position()` and
   `camp.health()` raise out of vision; use `spawn_position()` for planning.
3. **Invisible allies are listed** by `cambc.champions(Team.ALLY)`. Reading their name raises out of vision; type and
   team are readable since 2.2.4.
4. **Don't name a module `draft`:** the draft instance dies, and the engine then picks at random.
5. **Fuel:**
   - compile costs ~55k fuel per line of `main.py` (not pre-loaded), so dead code costs boot rounds;
   - strat-sw rolls over ~27 turns a game;
   - a turn that runs out of fuel carries over, and the champion is defenceless meanwhile.
6. **`DistanceField.compute` max distance ≤ 65535.** Since 3.0.1 `move_towards` treats the target as free and
   **raises** if the target tile is known to be blocked (altars, camps) [sdk]; before, it returned False. ~100k per call.
7. **Ship `--split`** (revised 20 Oct, 03 §3): parts 00–89 pre-load before the game, so round 1 starts with ~3.9M fuel
   (single file: ~0.7M) and boot ends 2 rounds earlier. The 19 Oct "split measured worse" was ~2 SE on 2.2.4.
8. **Side B.** In ladder downloads we are team B in about a third of games. In arena runs we are team B in the `-B`
   folders. Replay scripts assume team A is us.

## House rules (for teammates and Claude)

- Tag every claim **[rules]**, **[sdk]**, **[measured]** or **[guess]**. A guess lives in the design doc that needs
  it and in code as a `# GUESS` constant. No register.
- One file = one session: build one `docs/redo/` doc per session, finish it, update this file.
- Update docs in the same change as the code or finding.
- Claude doesn't commit: the user commits.
- Claude doesn't edit `docs/Champions/*.md`.
- No generated binaries or bytecode in a submission.
- No map names or coordinates in code.
- Before stopping, update the top of this file.
