// Exchange rates: what each quantity is worth in tributed gems, the unit of P(win).
// Seeded from the logistic win model fitted on 250 top-3 games on 5.0 (docs/research/LADDER_5_0.md §4.4):
//   1 gold earned ~0.19 gems at r150, 0.16 at r300, 0.12 at r500, 0.05 at r750; a carried gem ~0.6-0.9 of a banked
//   one; a kill ~24-29 gems beyond the bag. These are tuning seeds (SPSA), not truths.
#pragma once
#include "common.h"

namespace value {

// Tunable constants (SPSA): keep them here, one place.
struct Params {
    // Exchange rates (gems per unit)
    float gold_r150 = 0.55f;          // one gold earned, by round (refit on 415 UK-band games, 6 Nov)
    float gold_r300 = 0.32f;
    float gold_r500 = 0.15f;
    float gold_r750 = 0.04f;
    float gold_late = 0.02f;
    float carried_base = 0.85f;       // a carried gem's worth before risk
    float carried_per_gem = 0.0015f;  // bigger bags are worth less per gem (more to lose)
    float carried_danger = 0.25f;     // extra discount when enemies are near
    float kill = 25.0f;               // a kill, beyond the bag it takes (used when kill_curve = 0)
    int kill_curve = 1;               // 1 = the kill (and a death) priced by round, fitted on the UK band (below)
    float kill_r150 = 64.0f;          // logistic P(win) on 415 band games (AUC 0.89 at r300), gems per kill
    float kill_r300 = 40.0f;
    float kill_r500 = 35.0f;
    float kill_r750 = 15.0f;
    float bench_round = 0.6f;         // a round of one of our bodies benched, in gems
    // Farming
    float hit_frac = 0.5435f;         // share of monster Strength that lands per round in range (measured on 4.0)
    float hysteresis = 1.2456f;       // a new goal must beat the current one by this factor
    float shop_gold = 0.0997f;        // value of spending a held gold, per gold, before r700
    int bank_gems = 0;                // > 0: bank once the bag holds this many gems (carries: x bank_carry_k, growing by round)
    float bank_carry_k = 1.5f;
    float bank_k = 0.8117f;           // bank when no farm beats this multiple of the body's long-run rate
    float hp_floor = 0.25f;           // below this share of max HP a body goes home; a farm must leave it above
    float camp_retreat = 0.25f;       // while clearing, below this share of HP and being hit: step out of the camps' reach
    float retreat_rounds = 3.5f;      // ... or when HP covers fewer than this many rounds of last turn's damage
    int opening_end = 144;            // until this round every body follows one pack target (Fish's opening)
    float spread_k = 0.5f;            // spread 2: a group the other squad's leader is on is priced x this
    int spread = 0;                   // a squad leader leaves a group to the other squad's leader already on it (unless it needs more bodies)
    int squad_min = 4;                // squads apply from this team size (smaller teams: carries free, the rest packed)
    int pack_one_max = 0;             // at or below this team size every body is in one squad
    int lead_carry = 0;               // 1 = a squad's carry (highest taker rank) leads, not its lowest slot
    int resp_sticky = 0;              // 0 = no hysteresis / follow bonus for a respawning group we'd wait at (our squads re-took
                                      // the group they had just captured 25 % of the time, the top 3 13 %; supports waited ~10 % of r0-300)
    int resp_idle_max = 0;            // > 0: a respawning target with more idle rounds than this ahead is priced x0.3
    float walk_k = 1.0f;              // each walking round to a target costs this many rounds in its price (our next camp is
                                      // 11.9 walking rounds away, the top 3's 8.7)
    // 9 Nov: we wait 246 body-rounds a game (r<=600) beside respawning own-third groups, the top 153, while free mid groups
    // go to the band (it takes 48-76 % of the value at 40-60 % of the way to its spawn; 20-42 % from the top). Own-third
    // groups are rarely the enemy's (5 %): each idle round beside one costs 1 + this rounds (mid_frac < own_frac).
    float own_wait_pen = 0.0f;
    float own_frac = 0.33f;
    float wait_pen = 0.0f;            // each idle round beside a respawning group (wait beyond the walk) costs 1 + this rounds
                                      // (idle beside respawns: ours 5.2 % of body-rounds, top 3 1.3 %)
    int feed_r = 9;                  // ... a non-carry leaves a cleared group's reward to a carry within this many tiles
    int feed_rank = 4;                // ... carries are taker_rank >= this (6: Vesper only; 5: + Marcella; 4: + Vendetta)
    float deny_cap = 0.0f;            // capture denial: walk onto a group the enemy is capturing (worth >= this, gem equivalents)
    float deny_ratio = 0.7f;          // ... only when our power near is >= this x theirs
    int deny_r = 7;                   // ... within this many tiles
    int gem_runner = 0;               // a gem runner (HoR, else Vendetta) on maps with at least this many pure gem-cluster groups
    float gem_run_k = 2.0f;           // ... its price on gem-only groups x this
    int runner_bank = 20;             // ... banks at this bag
    float fed_k = 1.9f;               // break off from an enemy with this many times my max HP within its reach + 2
    int gem_marcella = 0;             // on maps with at least this many pure gem-cluster groups Marcella is the first taker
    int rally = 0;                    // early clashes: post a rally tile (bytes 6-7), healthy idle bodies within rally_r converge
    int rally_until = 300;
    int rally_r = 15;
    float hunt_k = 0.0f;              // chase an enemy with 1/this of my max HP (unguarded) within hunt_r
    int hunt_r = 8;
    int bank_prox = 0;                // bank with any gems when an altar is within 4, or right after a capture with one within 8
    int cap_recall = 0;               // > 0: recall on the capture tile once our capture runs, if HP < 60 % or gold >= this
    int seed = 0;                     // evaluation only: a 1e-4 tie-break nudge in goal prices, so one build can be sampled several times
    int finish = 0;                   // keep farming a damaged group I'm at until it is cleared (no enemy seen, HP >= finish_hp)
    float finish_hp = 0.3f;
    float engage_k = 0.8f;            // engage_mode 2: before r300 commit at >= 80 % HP when my max HP >= this x their biggest
    int engage_mode = 0;              // 1 = the top 3's commit / break table (k, L, h) instead of the exchange sim
    float fed_pow = 0.0f;             // > 0: fed = max HP x damage >= this x mine (instead of fed_k on max HP)
    int fed_margin = 2;               // the fed break applies within the enemy's reach + this
    float fed_gang = 0.0f;            // no fed break when the bodies within 5 of me have this many times its HP x damage
    float fed_farm = 1.0f;            // farm value x this for a group a fed enemy stood by in the last 10 rounds
    // Dash budget (code audit 2.4, never built before 9 Nov): every dasher spent its dash on travel ~75 times a game (HoR 77
    // travel v 22 landings), so at contact HoR's stun dash and the carries' escape dash were on cooldown. Bits: 1 no travel /
    // camp-landing dash with an enemy seen within dk_r in the last dk_age rounds; 2 HoR (a damage dash) never travel-dashes;
    // 4 the flee dash only when a visible enemy can reach me next turn; 8 Marcella's enhanced (stun) reset kept off camps
    // with an enemy near (as bit 1).
    // Early safety (8 Nov evening): blowouts open before r300 (collected gap -38 / -112 / -156 at r100 / 200 / 300); our
    // Vesper / Vendetta / Marcella die 0.70 a game by r300 v the top's 0.14, 0.57 of it in the middle, 0.30 beside a live
    // group they were working, 0.47 with enemies within 8 already 20 rounds before (n17 / top_v_band decoded). Before
    // early_until: bit 1 the contact hold (WORK / p1) needs more bodies than theirs near and our max HP >= theirs; bit 2
    // groups with enemies seen lately are priced x early_d1 (one) / x early_dm (2+), bit 4 those only for non-twin bodies.
    int early = 0;
    int early_until = 300;
    float early_d1 = 0.6f;
    float early_dm = 0.3f;
    // opn (opening study, 8 Nov [measured] top_v_band 119 games v n17_tz66 150, main bodies Vesper / Vendetta / Marcella /
    // Tavi / HoR, r<=300): after the first champion hit at >= 75 % HP ours die within 10 rounds 15.7 % v the top's 3.9 %;
    // 17.9 % / 30.2 % v 2.1 % / 4.3 % when the enemies within 5 outnumber our bodies by one / two+. The top's bodies open
    // distance at once (nearest attacker 2.7 / 3.5 / 4.1 tiles at +1 / +2 / +3 rounds v our 2.1 / 2.4 / 3.3) while landing as
    // many champion hits (3.3 v 3.1 in 5 rounds); top Vesper ends within 2 of an attacker on 36 % of turns v ours 51 %
    // (deaths 0 / 32 v 10 / 81). Bits (main bodies only, before opn_until, never when a kill lands this round):
    //   1 hit-break: damaged with an enemy in step + hit reach and enemies within opn_r > our bodies within opn_r +
    //     opn_margin: break for opn_hold rounds by a step / dash out of every next-turn reach (find_escape); melee swing
    //     first, ranged shoot after the step (reset); trapped: hit the weakest in reach.
    //   2 ranged spacing: a ranged main body (Vesper, Tavi) that an enemy can step-and-hit next turn steps to the tile with
    //     the fewest such enemies (then fewer next-turn reaches incl. dashes, a target still in range, allies, home), then
    //     shoots with its reset; only when that tile is strictly safer than staying.
    //   4 bit 1 counts only enemies that out-size our bodies near: their max HP within opn_r >= opn_mhp_k x ours.
    //   8 bit 1 with no way out hits the weakest in reach (else the old flee walk, then a hit if one is in reach).
    //  16 bit 2 with an enemy next to me (no step gets out of its reach): shoot, then dash to the safest tile.
    // opn / camp_path / eco and their knobs are static constexpr (merged 8 Nov): at 0 they compile out, so the default build
    // stays byte-for-byte tz-96's in code and data (play is fuel- and layout-sensitive). variant.py edits them as usual.
    static constexpr int opn = 0;
    // Churn (9 Nov, drop-reason log: 210 job drops a game; the en-route ones that come back within 30 rounds are team
    // events: an ally's commit halving my share 16 / game (back 46-68 %), the pack leader's errands and switches 19 / game
    // (back 42-55 %); value flips are ~0). static constexpr: 0 compiles out. Bits: 1 my current job's share counts only
    // committed allies nearer to it than me (first come keeps it; the farther one moves on); 2 a follower keeps working the
    // leader's last farm target (pack-priced) while the leader is on a bank / home errand, up to churn_hold rounds; 4 a pack
    // leader's hold on its job is x (1 + churn_lead x followers): its switch moves the whole pack.
    static constexpr int churn = 6;
    static constexpr int churn_hold = 25;
    static constexpr float churn_lead = 0.1f;
    static constexpr int opn_until = 300;
    static constexpr int opn_r = 5;
    static constexpr int opn_margin = 0;
    static constexpr int opn_hold = 3;
    static constexpr float opn_mhp_k = 1.0f;
    int dash_keep = 0;
    int dk_r = 12;
    int dk_age = 10;
    int champ_dash = 0;               // a melee damage dash (HoR) lands next to the fight target, adjacent or not, then hits
    int stun_first = 0;               // in a fight, stun the target first when an ally is within 3 of it or it is below half HP
    int stun_keep = 0;                // no flee stun above half HP (keep it for kills)
    int fill_late = 2;                // the wait filler may make me arrive this many rounds after the respawn
    int fill_fuel = 45000;            // ... and runs with at least this much fuel left
    int gate = 1;                     // learned engagement gate: 1 = veto commits with advantage < -gate_lo; 2 = + push > gate_hi
    float gate_lam = 1.0f;
    float gate_lo = 0.03f;
    float gate_hi = 0.10f;
    float fed_far_k = 0.0f;           // > 0: break from an enemy with this many times my max HP within fed_far_r (and the posted big one)
    int fed_far_r = 8;
    int camp_leave = 0;               // step out of awake camps' reach (not my farm group; mine when HP < camp_leave_k x last damage)
    float camp_leave_k = 4.0f;
    static constexpr int pathx = 0;                    // pathx.h: 1 draft walks, 2 opening walks, 4 enemy-spawn race, 8 fuel governor
    static constexpr int gov_fuel = 55000;
    static constexpr int hole_gain = 4;                // pathx 32: a hole dash route must save this many rounds over the walk             // pathx 8: keep the goal below this much fuel before the choice
    static constexpr int camp_path = 7;                // camp death study (8 Nov, band): deaths to camps away from farming (walking into an awake
                                      // camp's reach, wandering or standing in it) 0.38 bodies a game v the top's 0.08; farming
                                      // deaths level. A tile is BAD when the awake camps (not my farm group) covering it deal
                                      // >= my HP / cp_k a round. Bits: 1 goal moves (step_to, step_field, dash_field, engine
                                      // pathing) never step from a lighter tile onto a BAD one (wait instead, at most cp_wait
                                      // turns); 2 flee steps / dashes price BAD tiles (-cp_flee); 4 exit first: a body on a BAD
                                      // tile (local v idle: 101 of 107 camp deaths were in reach of a group other than the
                                      // goal's, mostly walking HOME or to the next group out of the golem it just left, along
                                      // the goal's field) first steps to the neighbour with the least damage left on the way
                                      // out (sum of strength x tiles to leave each reach), the goal's field breaking ties
    static constexpr float cp_k = 20.0f;
    static constexpr int cp_wait = 8;
    static constexpr float cp_flee = 6.0f;
    // agF (farming study §4 rule 2): reward handoff by presence. The best taker rank among our bodies within
    // max(hand_r, its attack range) of a cleared group's spawn tiles takes it; nobody walks in from farther (the old
    // feed / feed_r walk-in: 18-19 % of our captures v the top 3's 4 %). An orphan reward (none of ours present, none
    // heading there by comms) is priced as before.
    int handoff = 2;
    int hand_r = 2;
    int hand_carry = 1;               // the feed carry prices an ally-cleared group at the full reward when it arrives before
                                      // the allies finish it (ETA <= their remaining clear + 1); 2: and at 0 when it would be late
    // agF (rule 1): respawn arrival timing. resp_time: don't walk to a respawning target before ready - walk - resp_slack.
    int resp_time = 0;
    int resp_slack = 1;
    int fill2 = 0;                    // wait filler 2: idle >= fill2_idle, start-time aware (respawning fills too); 2: + a bank
    int fill2_idle = 3;               // trip that is back in time
    // Planner (farming study §4, 7 Nov): a farm goal is a plan made on events, not a price re-taken every turn. A body
    // is timed by when it can START work; a respawning target is a reservation whose slack is filled (another job or a
    // bank trip that is back in time); a bank trip is taken when the plan passes near an altar (small detour for the bag)
    // or the bag is at risk; 0 = choose() as tz-38 + the agF switches.
    int planner = 1;
    int plan_every = 4;               // re-plan at least every this many turns (events re-plan at once)
    int plan_k = 10;                  // groups fully priced on a planning turn (cheap bound first)
    int plan_fill = 1;                // fill a reservation's slack: 1 = every body, 2 = leaders and free bodies only
    int plan_idle = 3;                // ... when it leaves at least this many idle rounds
    int plan_late = 2;                // ... the fill may make me start the reservation this many rounds late
    int plan_bank = 1;                // 0 = the old bank_rate offer; 1 = detour banking + the old offer; 2 = detour + urgent only
    float bank_detour = 0.2f;         // a bank trip may delay the next job's start by this many rounds per carried gem
    int bank_detour_max = 14;         // ... at most this many
    int bank_min = 6;                 // ... with at least this many gems carried
    int bank_fill_min = 6;            // ... or this many when the trip fits in a reservation's slack (it costs nothing there)
    float bank_risk = 1.0f;           // ... allowance x (1 + this x min(3, threat near me)): the bag at risk
    int plan_claim = 0;               // skip a group the other squads' bodies with an earlier ETA already cover (need_of)
    float plan_near = 30;           // > 0: score = rate x 2^(-start / this): nearest-ready first (0 = rate only; ~18 moves our
                                      // fitted 4.8-5.5 tiles per value doubling toward the top 3's 3.9)
    int plan_home = 0;                // a reservation's slack with no job in it: a home trip (recall, shop, heal) back in time
    int plan_shop = 100;              // ... when holding this much gold (or below 80 % HP)
    int plan_end = 1;                 // endgame: our score + every bag of ours reaches the winning total: every body with gems banks
                                      // (v idle the team still carries 144 gems in the game's last round, 109 when the score passes 900)
    int end_bag = 30;                 // ... an ally's bag when it is out of sight (seen bags are read; error 97 when not visible) and
                                      // not seen in the last 30 rounds
    int end_pre = 0;                  // ... within this many gems of it: bank detours allowed x3
    int plan_ahead = 1;               // a capturing pack leader posts its next job (comms), so the pack walks on during the capture
    int plan_slip = 3;                // re-plan when the job's start slips by more than this many rounds
    int plan_diag = 0;                // diagnostics: print the planner counters at r300 / r600 (stdout costs fuel: scratch only)
    // Roles (role study + top-v-band study, 7 Nov): one redesign of who does what, built on the planner. roles 1 turns
    // on the parts in role_mask: 1 the crew takes for itself (squads: Vendetta with HoR + the twins, Vesper and Marcella
    // apart; whoever is present takes, Vesper first only when she is there; every body banks at ~25 with an altar on
    // its route, shops from 90 gold, HoR / Vendetta / Marcella heal from 65 % HP); 2 WORK = strike-and-farm (a body
    // within role_work_r of its live group keeps clearing and hitting champions in reach unless a real threat); 4
    // conversion (HoR walk + dash + hit within 4, Cassi walk-in stun then damage, stuns before hits, allies pick up a
    // stunned target from role_assist_r); 8 Marcella pokes with her damage spell at range 4 when not breaking off.
    int roles = 1;
    int role_mask = 6;                 // bits: 1 squads, 16 take rule, 32 banking, 64 early heal, 128 shop from 90 gold (part 1);
                                      // 2 WORK; 4 conversion; 8 Marcella's poke
    int role_work_r = 4;
    int role_sq = 1;                  // squads (bit 1): 1 crew + Vesper + Marcella; 2 crew + Vesper/Marcella; 3 crew with Marcella + Vesper; 4 Vendetta/HoR/Marcella + Vesper/twins
    int role_bag = 25;                // supports: a bank trip on the route is taken from this bag (detour <= role_detour)
    int role_vbag = 40;               // ... Vesper's bag for the same
    int role_detour = 8;
    int role_force = 35;              // supports bank from this bag with an altar within 12 (Vesper: role_vbag + 20)
    int role_gold = 90;               // home trips count gold from this (was 120)
    float role_heal = 0.65f;          // HoR / Vendetta / Marcella: below this HP share the heal term x role_heal_k
    float role_heal_k = 3.0f;
    int role_wassist = 1;             // 1 = a worker still joins a teammate's fight (assist) while holding its group
    int role_assist_r = 6;            // a stunned enemy an ally fights is picked up from this far
    float role_ratio = 0.8f;          // openers (HoR pounce, Cassi stun) need local power >= this x theirs
    // Mid (planloss study, 8 Nov: 88 % of the r600 gem gap in blowouts is mid groups; we take 21 % of the mid groups both
    // sides reach, the top 72 %; we reach first 37 % of cycles, the top 63 %). On top of roles 2 (WORK).
    float work_out_k = 1.15f;          // > 0: a WORK hold ends when their max HP near >= this x ours and we don't have more bodies
    int work_bag_stop = 25;            // > 0: ... or when out-sized while carrying at least this many gems
    float regb_gold = 1.0f;           // != 1: on home-poor (< 25 % of gem value nearer our spawn) compact (spawn distance < 45)
                                      // maps, gold is priced x this before r300 (regime study: the band / top take mid gems first)
    int gold_draft = 0;               // 1 = on maps with total group gold < gold_draft_cut: Marcella carry (4: Ma/Vd/HR/C&I; 5: + Willow); 2 = Prism 5th
    int gold_draft_cut = 1400;
    int ryth_stun = 0;                // Ryth opens fights with its ground area stun on the target tile
    int hunt_brk = 0;                 // break (and stop a WORK hold) when an enemy >= fed_k x my max HP is closing on me within hunt_brk_r
    int hunt_brk_r = 9;
    int p1 = 1;                       // hold and work the group in contact at every layer (parts in p1_mask)
    int p1_mask = 31;                 // 1 planner: a held job is not re-planned on sight / damage; 2 strict stops: the hold ends
                                      // only for HP < work_hp, a fed enemy within reach + 2, damage with an enemy in reach while
                                      // locally smaller, the gate (P(die) > work_pdie) or an execute; 4 stance hygiene: a held
                                      // body keeps no lingering BREAK, a vetoed opener returns to the hold; 8 denial bonus;
                                      // 16 the guards of a cleared reward (handoff 2) hold it as workers do; 32 a held job is
                                      // not traded for a bank / home trip while the enemy is in sight (endgame bank excepted)
    float p1_deny = 0.2f;             // the held job's price x (1 + this) with an enemy seen by it lately (what we hold they lose)
    int p2 = 0;                       // race pricing for mid groups (35-65 % of the way to the enemy spawn), parts in p2_mask
    int p2_mask = 7;                  // 1 race bonus, 2 lost-race cut, 4 packs: big mid jobs are never solo jobs; 8 the bonus only
                                      // against a known enemy (no spawn-distance fallback)
    float race_k = 0.3f;              // score x (1 + this) when my ETA beats the nearest known enemy's (fallback: their spawn's)
    float race_lose = 0.5f;           // score x this when a known enemy's ETA is > race_gap shorter and we'd be outnumbered
    int race_gap = 5;
    int race_gems = 25;               // packs: mid jobs with this many gems (or with elk / strength) are pack jobs
    int p3 = 1;                       // take first in contact: an enemy within 8 of a reward of ours: the nearest present
                                      // eligible body takes it at once; the others guard (hit enemies within 2 of its tiles)
    int p3_r = 8;
    // WORK stance (gap study D1, ported from bots/tz); roles part 2 turns it on as strike-and-farm (work 2 semantics).
    int work = 0;                     // 1 = D1 as in tz; 2 = strike-and-farm: closing / damage is a threat only when our
    int work_r = 2;                   //     local max HP is below theirs, and workers keep their champion shots
    float work_hp = 0.5f;
    float work_ratio = 0.8f;
    float work_pdie = 0.12f;
    int work_paths = 1;
    int work_price = 1;
    int work_shots = 1;               // work 1 only: a ranged worker does not take the free shot at a champion
    int move_guard = 0;               // goal moves: no hop back onto last turn's tile; step_to only strictly nearer; field first
    int recall_guard = 1;             // no recall with an enemy seen in 5 rounds within 7, or in a camp's reach (walk instead)
    int blind_stance = 1;             // a winning sim with no enemy in sight gives no stance (not a 6-round break)
    int assist_fix = 0;               // 1 = no assist during a fed break; 2 = assist only from no stance
    int kite = 1;                     // ranged + attack reset (Vesper, Cassi): 1 = shoot after a move (reset restores the attack
                                      // [measured]); 2 = + in a fight step to a safer tile still in range, reset, shoot; 3 = + while breaking
                                      // (ranged move+attack turns: ours 0 %, the top 3's 6.7 %)
    int kite_exec = 0;                // the execute check counts a ranged step + reset + shot at range + 1
    int kite_camp = 0;                // the same step + reset + shot on camps one tile out of range
    float kite_gain = 0.7f;           // kite 2 steps only when the new tile's danger <= this x staying
    int big = 1;                      // comms bytes 6-7 = the biggest enemy's last sighting (feed on): groups within big_r of it are
    float big_k = 0.5f;               // ... priced x this for bodies it out-sizes (its HP class >= fed_k x my max HP)
    int big_r = 8;
    int big_age = 16;
    int melee_step = 0;               // melee in a fight: after the hit, step to a safer tile still next to the target (kite_gain)
    int break_act = 0;                // a break that gains no tile hits / casts on the weakest in reach
    float flee_sep = 0.0f;            // flee steps: separation weight per tile (was 1.5) and -20 for a tile still in an enemy's reach
    float target_dps = 0.0f;          // target score x (1 + this x the enemy's damage / mine)
    int gem_map_n = 0;                // on maps with at least this many pure gem-cluster groups ...
    float gem_map_k = 1.5f;           // ... gems are priced x this
    int bag_cap = 0;                  // bank at this bag ...
    int bag_near = 25;                // ... or at this bag with an altar within 6
    int five_swap = 0;                // 5-pick maps: HoR replaced by 1 Varg, 2 Ryth, 3 Stellar, 4 Prism, 5 Tavi
    float lookahead = 0.0f;           // farm price = (v + this x next v) / (t + this x next t): the best group after this one
    int feed = 1;                     // feed the carry (top 3, 6 Nov: their Vesper earns 3,456 gold a game to our 996, supports
                                      // 200-900): the highest-ranked carry present takes, non-carries leave rewards to a carry nearby
    int feed_until = 0;               // > 0: feed only before this round
    int feed_shards = 0;              // > 0: stop feeding a carry that owns this many shards (Vesper's line: 6 emblems = 30)
    int cluster_solo = 1;             // groups with no Strength (gem / gold clusters) are one body's job: priced solo, never followed
    float follow_k = 1.5f;            // a pack member's price on its leader's target (x the shared farm rate)
    int squad_table = 1;              // 0 = Vesper / Vendetta / HoR and Marcella / Ryth; 1 = Marcella / HoR / Ryth and Vesper / Vendetta
    int squads = 2;                   // 1 = after the opening, two squads of three each following its own leader; 2 = from r0
    int pack_all = 0;                 // 1 = every body (carries too) follows the pack all game
    int follow_mode = 0;              // (reserved)
    int assign_mode = 0;              // 0 = pack follows a leader (opening, crew); 1 = assignment by arrival and need
    int keep_capture = 0;             // a body already on a capture tile keeps the capture; others move on
    int reward_comms = 1;             // a far capture-ready group an ally targets is not worth walking to
    int wait_fill = 6;                // a respawn wait of this many idle rounds or more is filled with another group (0 = off)
    int null_burn = 0;                // calibration only: burn this much fuel a turn (a null change for measuring noise)
    int first_lite = 0;               // first turn short of fuel after the map setup: step toward the nearest group, nothing else
                                      // (every body of both teams ran out of fuel in round 1: init costs 84-145k of 175k)
    int first_reserve = 70000;        // fuel kept for the first turn's play after the map setup (fields wait)
    int budget_groups = 30;           // the fuel budget on pricing applies only on maps with more groups than this
    int price_reserve = 35000;        // fuel kept back when sizing the full-price list
    int price_cost = 1700;            // fuel per fully priced group
    int price_min = 4;                // groups always fully priced
    int price_top = 16;               // groups given the full farm price each turn (the rest ranked by a cheap bound)
    int tier_shards = 8;              // shards per item tier in the capture-taker rule
    // Fights
    float fight_ratio = 1.5f;         // (legacy ratio thresholds; the exchange simulation decides commits)
    float flee_ratio = 0.8f;
    float commit_ratio = 0.6f;
    float enemy_dps_k = 1.15f;        // enemy damage a round is underestimated by str + foc/4 (resets, items): pad it
    int camp_stun = 1;                // stuns may target camps when no enemy champion is seen within 10 (top-3 Cassi: 18 camp stuns a game)
    float siege = 150.0f;               // > 0: a group walling in an altar is a team objective worth this many extra gems, farmed
                                      // by bodies with max HP >= siege_hp x its strength without the HP-floor check (they rotate out)
    float siege_hp = 5.0f;
    int claim_need = 0;               // skip an alive group when the allies heading there AND nearer to it already number its need
                                      // (half our abandoned walks: an ally nearer took the group first)
    int micro = 0;                    // per-tile micro (XSquare's, copied by most top Battlecode teams): fight and break-off
                                      // steps chosen by comparing danger / lethal / can-hit / allies / distances tile by tile
    int prio_fight = 1;               // set_priority: bodies near enemies act first within our team (turns alternate champion by
                                      // champion between teams; within a team higher priority first [rules]; we never set it)
    int xsq_switch = 0;               // XSquare's anti-oscillation: leave an alive farm target for another only if the new one is
                                      // nearer than the closest I got to the current one (supports switched 7.6-13 times to r300)
    int own_close = 0;                // pricing my current target, count only committed allies nearer to it than me (two bodies on
                                      // one group both saw it halve and both left: 2.8-5 'price' switches each to r300)
    int open_big = 0;                 // until this round every body prices groups as the whole team's job (the top 3 open with ~4
                                      // bodies on one big group near home: elk 46 %, 2,640 HP, first capture r24 with 17.6 gems)
    int late_skip = 0;                // don't head for an alive group the allies on it clear before I arrive (to r300 our supports
                                      // abandoned 4-6.5 walks each because the target died first; arrivals 6-9)
    float assist_ratio = 0.7f;        // assist only when our power near (L.our / L.their) is at least this (band: 123 v 41 deaths in
                                      // fights we outnumbered: their bodies are bigger)
    int assist = 1;                   // join a teammate's fight: its comms target visible within assist_r and my HP >= assist_hp
    int assist_r = 7;
    float assist_hp = 0.5f;
    int free_hit = 2;                 // a melee body hits an adjacent enemy champion first, every turn (melee move and attack in one
                                      // turn [rules]; with an enemy in reach our melee hit 50-66 % of turns, the top 3's 77-89 %, v93's 84-91 %)
    int fight_mode = 0;               // 1 = the top 3's engagement rule (6 Nov, 7,819 contacts): ranged bodies and Marcella always
                                      // fight; melee at HP >= fm_melee_hp with local power ratio >= fm_ratio; anyone below fm_low
                                      // breaks off; no break-off at 5-8 tiles on a losing sim
    float fm_low = 0.4f;
    float fm_melee_hp = 0.6f;
    float fm_ratio = 0.5f;
    float commit_bias = 1.0f;
    float duel_bias = 1.0f;           // ... in an isolated 1v1 (one enemy within 12 over 10 rounds): band replays, we fled 41 % of
                                      // the duels we were >1.6x stronger in (kill 1 % fleeing, 24 % fighting)         // our damage multiplier inside the exchange simulation (>1: commit more)
    float stance_low = 0.3f;          // break below this share of max HP
    int stance_hold = 6;              // rounds a commit/break decision holds without a new event
    int break_closing = 0;            // 1 = break off only from an enemy closing on me or within its reach (else keep farming)
    int flee_linger = 1;              // rounds a breaking body keeps fleeing after the last threat was in reach
    int break_radius = 8;              // a losing fight is broken off at this distance
    float flee_ally = 0.3f;           // fleeing: pull toward allies per tile (a 2v1 the sim commits to beats a chase home)
    int flee_ally_cap = 8;            // ... over allies within this many tiles
    int melee_nearest = 1;            // melee in a fight close on the nearest enemy when the target is out of reach
    int shield_early = 1;             // self-shields fire whenever damage is coming (camps awake in reach, enemies near)
    int commit_outnumber = 0;         // commit whenever we have more bodies in the fight than they do (and not low)
    int fight_team = 0;               // commit when the team wins the exchange (kill them all, lose fewer), not when I survive it
    int flee_hits = 1;                // breaking off: stun the nearest chaser (walk-compatible stuns), swing at anyone in reach
    int spell_aware = 1;              // keep out of (and flee beyond) a visible enemy's ready damage spell that would take 25 % of my HP
    float marc_bank = 2.0f;           // Marcella's bank bonus per carried gem (x gold worth / walk): her tribute passive
    int marcella_taker = 0;           // Marcella is the first-choice capture taker (2 gold per gem tributed; the band's habit)
    int execute = 1;                  // commit on an enemy our bodies in reach can kill this round
    float execute_margin = 1.1f;      // ... when the sum of their bursts is at least this multiple of its HP
    int execute2 = 0;                 // also two-round kills (bursts now + a round of damage) when no enemy near can kill our weakest
    float execute2_safe = 1.0f;       // ... there in two rounds: their two-round damage < this x its HP
    int flee_mode = 0;                // 2 = break off only by a step (or dash + step) out of every enemy's next-turn reach; else hit back
    int spell_first = 1;              // damage spells in reach are cast before walking (they exclude walking), in fights and on camps
    int trapped_fight = 0;            // breaking off but every step stays in an enemy's reach: hit back instead
    int threat_memory = 25;           // rounds an enemy sighting keeps discounting the groups near it
    float deny_k = 0.0f;              // a group nearer the middle is also one the enemy doesn't get: value x (1 + this) from 35 % to
                                      // 50 % of the way to their spawn (the band takes 1,283 middle captures by r300 to our 557)
    int deny_until = 2000;            // ... only before this round
    float danger_multi = 0.6f;        // farm value near 2+ enemies seen in the last 30 rounds (was 0.35)
    float danger_one = 0.85f;          // ... near one enemy (was 0.65)
    int threat_team = 0;              // 1 = the threat discount weighs enemies against my power plus my allies' near (not mine alone)
    float threat_k = 0.2f;            // discount per unit of (enemy strength / mine) near a group
    float bank_threat = 0.01f;        // bank rate per carried gem per unit of nearby enemy strength (bag at risk)
    // Altars and vision
    int lock_race = 850;              // from this enemy score, lock altars their carriers approach
    int together = 1;                 // nothing worth farming alone: price groups as if the whole team joined
    int stuck_rounds = 30;            // a farm target beside me that loses no HP for this long is banned for 200 rounds
    int bank_dig = 1;                 // banking but blocked by camps on the way: hit the blocking camp
    int altar_walk = 1;               // walk to altars around camp tiles when a way exists (02guardians); 0 = through them
    float home_farm = 0.7f;           // farm a group from our own spawn tiles (healed in full each turn) when its total
                                      // strength is under this share of my max HP and every camp is in my reach (0 = off)
    int lock_cost = 10;               // rounds a remembered enemy lock adds to an altar's walk
    int ward_altar_ok = 0;            // 1 = wards may go next to altars again (they block tribute tiles)
    int ward_refresh = 4;
    int pre_recall = 1;               // start a recall at each turn's end, keep it next turn only if going home (the band's habit)             // re-place this body's ward when farther than this (0 = no wards: net negative)
    // Tables
    int item_table = 3;               // 0 = Fish's 5.0 lines, 1 = Mite's tanky carries, 3 = the UK band's consensus
    int monster_early = 0;            // 1 = Monster emblem third for Vesper, Vendetta, Marcella and HoR
    int prospector_first = 1;         // 1 = every champion's first emblem is Prospector (+25 % cluster rewards)
    int cassi_health = 1;             // Cassi buys Health first (she sat at 600 HP all game)
    int mage_hp = 0;                  // Marcella and HoR buy Health shards (top 3 per 100 gold: Marcella 19 Focus / 157 HP, ours
                                      // 28 / 78; HoR 14 / 179, ours 26 / 49)
    float melee_inc = 0.0f;           // a melee body (nearest to the camps, which hit the nearest [rules]) takes this share of the
                                      // pack's incoming on top of its own split (0 = split evenly as before; 1 = all of it)
    int fill_pack = 0;                // wait filler: only the pack leader fills, pricing with the pack (supports' solo price is 0)
    int budget_fuel = 0;              // > 0: the pricing budget also applies when less than this much fuel is left at choose time
    int field_est = 3;                // fuel estimate per tile of a distance field (a field costing more than this ran turns dry on
                                      // 03the-front: 240 exhausted turns a game, all at the end-of-turn field building)
    int twin_half = 1;                // the fight assessment counts each twin's HP at half (one twin's death costs both)
    int twin_tether = 0;              // outside fights a twin > 3 tiles from the other walks back to it; either < 50 % HP: both go
                                      // home (band v tz-28: 27 % of our mid-game deaths were twin collateral, often 8+ tiles off)
    float gem_sup = 1.0f;             // non-Vesper bodies: pure gem-cluster groups x this before r150, fading to x1 at r300
    int sup_lines = 0;                // item_table 3: HoR / Marcella lines with Bruiser + Durability Health, no Treasure
    float gem_open = 1.0f;            // pure gem-cluster groups priced x this before r150 (band: first central gem group r117; ours
                                      // none by r300 in 17 of 32 games; 74 % of our attempts succeed uncontested)
    float twin_home = 1.0f;           // the twins price groups past the middle (nearer the enemy spawn) x this (they die 3.2 times a
                                      // game each v the band, mostly mid-game ganks by 2-3 enemies)
    float gem_k = 1.0f;               // gems in a group's price x this (band v tz-28: our gold is on target, gems 153 v 265 by r300)
    int stun_focus = 0;               // a stunned enemy within my reach + 1: commit to it (top 3: a damage cast follows Cassi's stun
                                      // 30 % of the time, ours 4 %)
    float gem_adapt = 0.0f;           // > 0: gems priced x (1 + (their score - ours) / this, capped 3) when behind (01elk-arena: our
                                      // gold 1,722 v 1,681 by r300, gems 164 v 1,008 all game: the gems sat in contested elk groups)
    float spiral = 0.0f;              // > 0: when recent ally deaths exceed enemy deaths by this (150-round decay), play defensive:
                                      // fight bias x0.75, groups near enemies x0.5, no assist (blowout losses: our deaths 17.7 v 4.8)
    // Tribute denial (8 Nov, win-not-farm lever): we bought 0 altar locks in 600 band games (the shard loop spent gold
    // below 30, the lock wanted 40); the band places 2.1 a game. A lock cancels a tribute channel and blocks their
    // tributes at that altar until 5 basic attacks [rules]; damage does not cancel a tribute. Bits: 1 buy the lock
    // first (10 gold, from td_round); 2 intercept: a body with a lock walks to an altar where a visible enemy channels a
    // td_bag+ tribute (within td_r, at most td_esc other enemies by it, my HP >= 40 %) and locks it (no fighting);
    // 4 pre-emptive: lock an unlocked altar on their side when passing within 2.
    int tdeny = 0;
    int td_round = 30;
    int td_r = 6;
    int td_bag = 15;
    int td_esc = 1;
    int lock_pre = 0;                 // place a held altar lock on any unlocked altar within 2 (enemy-side first); buy from r30 (the
                                      // top 3 place ~2.9 a game, 161 of 177 pre-emptive; a lock blocks only enemy tributes [rules])
    float carry_safe = 1.0f;          // the top carry carrying >= 40 gems: fight sim bias x this (it loses ~40 gems a game in bags)
    float carry_bias = 1.0f;          // the top carry's damage multiplier inside the fight sim (it is fed: Vesper 4.6 kills a game)
    int espawn_ignore = 1;            // enemies on / beside their own spawn don't count as contact unless they just hit me (00reverse-
                                      // spiral B, spawns side by side: our team stayed home in BREAK for 300+ rounds v idle)
    int blind_fix = 1;                // close-but-blind step: only strictly nearer tiles (bush first), else the normal field step
                                      // (02fields B: Vesper swapped between two equal tiles beside an unseen group for 400 rounds)
    int vesper_power = 0;             // Vesper's line: Prospector only, then Power (Strength 2 : Health 1)
    int score_aware = 0;              // after r400: 150+ gems ahead, the fight sim's bias x0.85 (protect the lead); 150+ behind, x1.2
    int choose_every = 1;             // re-decide the goal every k-th turn (staggered by slot) while the current FARM goal stays
                                      // valid and nothing happens (choose costs 9-33k a turn; fuel-starved decisions; flapping)
    int contest_ban = 15;              // our capture contested this many rounds in a row: ban the group 100 rounds (00the-line:
                                      // Vesper stood on a contested reward for 150 rounds; an enemy held the other end of the region)
    int step_fix = 0;                 // step_to: greedy hop failed and the target tile is blocked / occupied: engine pathing to a
                                      // free tile beside it (it gave up: bodies froze beside walls, idle stands 34 body-rounds a game)
    int lead_mem = 0;                 // followers keep the leader's last FARM target this many rounds while it fights / banks
    int retreat_fix = 1;              // camp retreat counts awake camps in reach (not every camp of the group by spawn tile), and
                                      // with no better tile keeps fighting instead of ending the turn idle (code review, 6 Nov)
    int osc_fix = 0;                  // back on the tile of two turns ago: step_field ignores the leave-a-camp's-reach allowance
                                      // (04comb: Vendetta with 83 gems stepped into and out of an awake camp's reach for 756 rounds)
    int approach_field = 2;           // the last steps to a camp follow the group's distance field, not a straight-line hop (a wall
                                      // between froze HoR 2 tiles from its target for 176 rounds: the hop found no nearer tile)
    int farm_avoid_enemy = 1;         // 0 = while farming (no stance), paths avoid awake camps' reach only, not enemies' reach
    int twin_safe = 0;                // Cassi / Issac: camp retreat 0.45 / 6 rounds, clear floor 0.4 (they are 2.7 of our 3.6 deaths a
                                      // game with no enemy near; one twin's death kills both)
    int pw_ratio = 2;                 // Power emblems in the main stat per Power Health emblem
    int power_after = 1;              // after the emblem line: Power emblems (6 shards' worth for 5 [rules]) in the main stat, every
                                      // third one Health (was Bruiser Health forever: our fed Vesper had top-3 HP at r600, 155 v 274 Strength)
    int item_health = 0;              // 1 = every emblem bought with Health shards
    // Support economy (eco study, 8 Nov [measured] tz66_big v top_v_band, per body by r300 / r600: gold earned Vendetta
    // 168 / 400 v 412 / 1,012, HoR 109 / 267 v 260 / 604, Marcella 272 / 584 v 432 / 998; Vesper level 774 / 1,672 v
    // 758 / 1,830. Health share of shards at r600: Vendetta 36 % v 32 %, HoR 10 % v 44 %, Marcella 15 % v 32 %).
    // Bits: 1 fair-share take (a support whose shards are under eco_share x Vesper's + eco_base takes a reward before
    // Vesper, the most starved first; + bit 8: Vesper doesn't walk in to join while a support is starved); 2 support item
    // lines by Health share (Vendetta / HoR / Marcella: Prospector, Durability, Jungle, Monster, Capture, Bruiser, then
    // Power; each emblem's stat is Health while the Health share is under the target); 4 supports go home to shop from
    // eco_gold; 16 the twins' lines by Health share too (Cassi 0.3 Focus, Issac 0.6 Strength: the top's mix).
    static constexpr int eco = 0;
    static constexpr float eco_share = 0.5f;           // Vendetta / Marcella / Prism: starved under this x Vesper's shards (top: 0.53 at r600)
    static constexpr float eco_share_hr = 0.33f;       // HoR (top: 0.32)
    static constexpr int eco_base = 3;                 // + this many shards (the opening: every support's first shards before Vesper's)
    static constexpr int eco_until = 800;              // the fair-share take ends at this round
    static constexpr float eco_hv = 0.33f;             // Health share targets: Vendetta, HoR, Marcella, Cassi, Issac
    static constexpr float eco_hr = 0.45f;
    static constexpr float eco_hm = 0.33f;
    static constexpr float eco_hc = 0.3f;
    static constexpr float eco_hi = 0.6f;
    static constexpr int eco_gold = 60;                // bit 4: a support's home trip counts gold from this (default 120)
    int draft3 = 0;                   // 3-champion teams: 0 = Vesper / Vendetta / HoR, 1 = Vesper / HoR / Marcella
    // Death study (dth, 8 Nov, tz66_big v top_v_band): our excess deaths are bodies killed without hitting back (1.05 v 0.17
    // events a game r <= 600). Bits: 1 = no frozen flee (a breaking body stood still 5-7 tiles from the enemy on 24 % of its
    // FLEE turns: the separation term capped at reach + 3-4 made staying the best tile whenever the enemy sat between it and
    // home); the cap grows by dth_cap and staying costs dth_slack. 4 = the same frozen flee, when out of every enemy's next-turn
    // reach + dth_safe, ends the break and the turn goes to the goal. 2 = recall abort (a channel is cancelled when a visible
    // enemy can reach me next turn) and a stricter start guard (an enemy seen within dth_rg_age rounds within dth_rg_r).
    int dth = 2;  // tz-96 (8 Nov): bit 2 adopted (n17 share +0.04, wins +0.07; n19 share +0.04, wins +0.04)
    int dth_cap = 3;
    float dth_slack = 0.75f;
    int dth_rg_r = 9;
    int dth_rg_age = 8;
    int dth_safe = 2;                 // dth 4: a frozen flee beyond every visible enemy's reach + this resumes the goal
    // Fight brain (merged 8 Nov from bots_8nov/_fb; docs/research/diag_7nov/fb.md; band: tz-76 = fb 1 on tz-66, +0.06 gem
    // share on 150 games). static constexpr: at fb 0 it compiles out (the default build's fuel is unchanged). fb_mask bits:
    // 1 team target (one kill-soonest target every body computes alike from what it sees + the comms FIGHT slots; used for
    // the commit target, act_fight, free hits and every in-reach swing); 2 finish: commit on the team target when the team
    // kills it within fb_fin_t rounds (overrides a break / a WORK hold; not a fed break); 4 burst: stuns only with follow-up
    // damage (fb_stun_mode 0), no damage cast that the basic already covers, a kill frees the attack / reset / cast for the
    // next target; 8 peel: a body hit by 2+ enemies and hurt steps out of reach behind an ally (still hitting if it can);
    // 16 no waste: no commit / chase on an enemy about to heal at its spawn unless it dies now; 32 cast first: a no-stance
    // body with a cast ready and an enemy champion in its reach casts before moving, HoR dashes next to it (hpk R1); 64 the
    // same while breaking off (not fed / low): walk-compatible casts first, walk-excluding ones only out of every enemy's
    // next-turn reach; 128 recall pick: a recalling enemy below 60 % HP is the team target and a finish (hpk R3).
    static constexpr int fb = 1;  // tz-107 (8 Nov 22:00): fight brain C1 adopted (n17 +0.05 / n19 +0.04 share v tz-66; tz-76 = fb alone +0.06 / +0.07)
    static constexpr int fb_mask = 255;
    static constexpr float fb_post = 0.5f;             // team target score x (1 + this) per ally FIGHT slot naming it
    static constexpr float fb_stun_k = 1.5f;           // ... x this for a stunned enemy
    static constexpr int fb_esc_r = 3;                 // an enemy within this of its spawn is escaping (score x 0.15; no chase) unless T <= 1
    static constexpr float fb_fin_t = 1.6f;            // finish: team rounds-to-kill at most this
    static constexpr float fb_fin_hp = 0.35f;          // ... my HP share at least this
    static constexpr float fb_fin_share = 0.4f;        // > 0: also a victim below this HP share that the team kills within fb_fin_t2 rounds (hpk R2)
    static constexpr float fb_fin_t2 = 4.0f;
    static constexpr float fb_fin_ratio = 0.7f;        // ... local power (ours / theirs) at least this
    static constexpr int fb_fin_far = 0;               // finish adoption reach: my reach + a step (+ a dash) + this
    static constexpr float fb_bc_k = 0.0f;             // bit 64: > 0 lets a walk-excluding cast replace a non-urgent break step (incoming < this x my HP; lost)
    static constexpr int fb_stun_mode = 1;             // burst: 0 = stuns need follow-up damage (fb_follow); 1 = every fight stun goes (hpk: ours 6.1 a game v 20.5)
    static constexpr float fb_follow = 0.15f;          // burst: a stun needs the others' damage in reach >= this x the target's HP (or it is below half)
    static constexpr float fb_peel_hp = 0.65f;         // peel: below this HP share
    static constexpr float fb_peel_dmg = 0.10f;        // ... having lost this share of max HP last turn
    static constexpr int fb_dbg = 0;                   // diagnostics: counters printed at r600 (scratch only)
    // Fight quality (fb2, 9 Nov; on fb 1; static constexpr: 0 compiles out). Bits: 1 keep damage / stun casts and HoR's
    // landing dash off camps while a visible enemy champion (off its spawn) is within fb2_keep_r (8-turn cooldowns [rules]:
    // a cast spent on a camp is missing from the fight that follows); 2 the same for attack resets on camps (an extra basic;
    // Marcella's enhanced reset stuns [rules]); 4 no chase: a commit on a target I can't reach this turn (reach + a step,
    // + a dash) that moved away / toward its spawn, isn't stunned or recalling, and that the allies in reach can't kill
    // before it reaches its spawn (their damage x min(spawn distance, fb2_chase_t) x fb2_chase_k < live HP) is dropped
    // (farm instead of being dragged); 8 kill-now focus: the team target score x fb2_now_k when the team's damage in reach
    // covers its live HP this turn.
    static constexpr int fb2 = 3;                      // tz-126 (adopted 9 Nov): bits 1 + 2. Band n29 share +0.04 / wins +0.06, fresh n31 +0.02 / +0.02
    static constexpr int fb2_keep_r = 6;
    static constexpr int fb2_chase_t = 4;
    static constexpr float fb2_chase_k = 1.0f;
    static constexpr float fb2_run_hp = 0.0f;          // bit 4: only runners at or above this HP share are let go (hurt ones are chased)
    static constexpr float fb2_now_k = 2.0f;
    // cap_emb (tz-117, adopted 9 Nov): Vesper's emblem line gets the Capture emblem (3-round captures) at cap_emb_pos (the
    // top's Vesper captures in 3 rounds on 76-89 % of captures, ours 10-13 %). Band: n23 share +0.01, n19 +0.03 (wins +0.04).
    static constexpr int cap_emb = 1;
    static constexpr int cap_emb_pos = 1;              // index of Capture in Vesper's emblem line (0 = first)
    // farmx (farm micro, 9 Nov; BUILD_LOG "Farm micro"): bit 1 hit order (in reach: the highest-Strength camp first, clusters
    // last); 2 a reset never wasted (after a kill it follows another live camp of the group in reach, else it is kept); 4 the
    // approach tile where I tank the least camp Strength; 8 approach the strongest live camp, not the nearest tile; 16 Jungle
    // first on Vendetta / HoR / Marcella (Issac second); 32 capture prep on a dead spawn tile. Local v tz-116: 19 = 54.7 %.
    static constexpr int farmx = 3;
    // openx (L7, 10 Nov; FINDINGS §7 / §12.4: the gap opens by r150; the top's first wave is gem clusters 11 % (ours 2 %),
    // gold clusters 14 % (ours 25 %); it puts 2.33 bodies on a first group (ours 2.71) and 3.67 hitters on mid-strength
    // camps (ours 4.16)). static constexpr: 0 compiles out. Bits, all inside the planner's group price:
    //   1 until open_until, gold counts x open_gold_w of its usual weight against gems (farm_vt, the shortlist bound);
    //   2 until open_cap_until, the bodies on one group are capped by its camp Strength (clusters 1; <= 20: 2; <= 60: 3;
    //     else no cap): a body with cap bodies ahead of it on the group (my pack leader first, then nearer, then lower
    //     slot; the twins count as one) prices it at 0 and takes its next-best group; a pack leader prices a capped group
    //     with cap - 1 helpers; with nothing else worth it the capped leader target stays the fallback.
    //   8 the bit 2 caps for the whole game (open_cap_until ignored).
    //  16 clusters at their real rate, all game: a zero-Strength group is a short job, so the flat danger / threat /
    //     big-enemy discounts are scaled by its exposure (clear + capture rounds / open_exp, at most 1); clusters within
    //     open_clu_r always make the priced shortlist; a follower's cluster within open_clu_reach of its leader's target
    //     gets the follow bonus (squad work).
    //  32 the mid when home is empty, all game: with no group of our own zone (mid_frac < 0.35) alive, groups at
    //     mid_frac >= 0.35 lose the flat danger discount, and the threat discount weighs the enemies against my power plus
    //     my allies' near (threat_team), so a squad prices the mid together.
    //  64 bit 1 for every body but Vesper (her gold buys the carry's items).
    //   (The spec's bit 4, non-takers leaving a dead group at once, is not built: bodies sharing a capture are 1.04 for us,
    //   1.06 for the band and the top [measured, FINDINGS §12.4]; non-takers already re-plan when the group turns REWARD.)
    static constexpr int openx = 48;
    static constexpr int open_until = 100;
    static constexpr float open_gold_w = 0.5f;
    static constexpr int open_cap_until = 150;
    static constexpr int open_cap1 = 20;               // total camp Strength <= this: cap 2
    static constexpr int open_cap2 = 60;               // ... <= this: cap 3
    static constexpr int open_exp = 20;                // bit 16: exposure rounds at which a cluster takes the full discount
    static constexpr int open_clu_r = 16;              // bit 16: reachable clusters within this (Chebyshev; walk <= 1.3 x) are always priced
    static constexpr int open_clu_n = 4;               // ... at most this many a planning turn
    static constexpr int open_clu_reach = 8;           // bit 16: a follower's cluster this near its leader's target gets follow_k
    // Bush wards (bushw, the teammate's _hc): the top places 62-83 % of its wards in bushes (top_tricks.md), ours 8 %; a bush
    // hides the hits in it until warded. The ward score's bush bonus (3) becomes bushw_k: a bush within bushw_k / 4 tiles of
    // the aim beats the aim tile itself. static constexpr: 0 compiles out.
    static constexpr int bushw = 1;
    static constexpr int bushw_k = 12;
    static constexpr int draftx = 2304;                   // map-aware draft on ONE-altar maps: 1 = Vendetta -> Prism (4-5 picks); 2 = + Vesper -> Marcella on 4 picks
                                                       // (HoR/Ma/C&I/Pr); 4 = + Vesper -> Willow on 5 picks; 8 = 3 picks Vesper -> Prism; 16 = only where the map has no gold; 32 = Prism for Vesper
                                                       // 64 = Prism takes Vendetta's taker rank (draftx_rank; Vesper's with 32); 128 = Prism is its own squad
                                                       // 256 = Prism for Vesper on GOLD-POOR maps (any altars, 4-5 picks; draftx_gold); 512 = the same on 3 picks;
                                                       // 1024 = Prism for Vendetta on gold-poor maps (4-5 picks; bit 1 by gold, not altars)
                                                       // 2048 = the gold-poor bits (256 / 512 / 1024) on one-altar maps only
    static constexpr int draftx_rank = 4;              // draftx 64: Prism's taker rank (Vendetta 4, Marcella 5, Vesper 6)
    static constexpr int draftx_dbg = 0;               // diagnostics (scratch only)
    static constexpr int draftx_gold = 16;             // draftx 256 / 512 / 1024: a map is gold-poor below this gold rate (sum of group gold / (respawn + 10), monoliths out)
    int draft_table = 7;              // 0 = Fish's comps, 1 = Mite's (Vesper first), 2 = Mite's with Varg for C&I, 3 = the UK band's (Ryth for C&I)
    // engx (9 Nov, engagement policy; static constexpr: 0 compiles out). One priced decision to engage, hold or leave.
    // Local strength = live HP and damage (Strength + Focus / 4 + a third of the ready burst) of the bodies able to arrive
    // within eng_k turns, both sides. Calibrated on 4,517 decoded band fights (tz107_big + tz126_big, Poisson fits, all
    // deciles within 0.05): E[kills] = exp(-1.81 + 0.40 lnHP + 0.20 lnDPS + 0.71 f), E[deaths] = exp(-1.00 - 0.32 lnHP
    // - 0.14 lnDPS - 0.87 f); f = we land the fight's first hit. EV = E[kills] x (kill + their bag) - E[deaths] x (kill + our bag).
    // Bits: 1 the engage test (contact commit / break, openers, assist: EV > eng_margin); 2 full team commit (every body that
    // can arrive joins a posted fight with EV > eng_margin, over a WORK hold or a non-fed break); 4 team disengage (a commit
    // whose EV < -eng_dis breaks and calls the fight off in comms; committed allies on it break with it); 8 open priced fights
    // (an enemy in my strike reach this turn, EV with our first hit > eng_open, from a hold / no stance / non-fed break).
    static constexpr int engx = 51;
    static constexpr int eng_k = 2;                    // arrival turns counted in the local strength
    static constexpr float eng_margin = 0.0f;          // engage when EV > this (gem equivalents)
    static constexpr float eng_dis = 4.0f;             // disengage when EV < -this
    static constexpr float eng_fk = 1.0f;              // the first-hit term x this (selection bias: < 1 shrinks it to the mean 0.41)
    static constexpr float eng_open = 3.0f;            // bit 8: open on an enemy in my strike reach when EV > this
    static constexpr float eng_open_hp = 0.6f;         // ... at this HP share or more
    // Bits 16 / 32 (rev_decisions_fights E1-E3): 16 the engage test is my HP share >= eng_hs and the local live-HP ratio >=
    // eng_hr (leave: below eng_hs or the ratio below eng_hr_out) in place of the price; 32 answer the opener: an enemy that hit
    // one of us near me this round or the last is committed on by every body that can strike it this turn (the test passes).
    static constexpr float eng_hs = 0.5f;
    static constexpr float eng_hr = 0.8f;
    static constexpr float eng_hr_out = 0.5f;
    static constexpr int eng_leave_ev = 0;             // 1: under bit 16 the leave test stays the price (EV < -eng_dis)
    static constexpr int eng_leave_rule = 0;           // 1: the leave test is the HP rule (eng_hs / eng_hr_out) even with the priced engage test
    static constexpr int eng_fed = 0;                  // 1: a team commit (bit 2) with EV > eng_fed_ev overrides the fed break
    static constexpr float eng_fed_ev = 10.0f;
    static constexpr int eng_gate = 0;                 // 1: the learned gate does not veto engx commits
    static constexpr int eng_dbg = 0;                  // diagnostics (scratch only)
    // robx (10 Nov, robustness; static constexpr: 0 compiles out). Recommended: robx 59 (1+2+8+16+32). Bits: 1 respawn deadlock (a body waiting for a respawn
    // never stands on ANY group's spawn tile: an occupied spawn tile holds that group's respawn [measured]); 2 crowd
    // fuel (decision-identical: a bucketed group x enemy scan in W.update, an incremental focus-fire sim in assess); 4 the fuel governor (pathx bit 8: keep the goal below
    // gov_fuel); 8 the teammate's v278 fuel fixes (one raw camp call, enemies-first group scan; its fuel_guard only with rob_fg 1:
    // it changes play and cost 5-8 local win points);
    // 16 the stand-off breaker (a frozen flee beside an altar tributes; a trailing team in a frozen stand-off resumes its goals);
    // 32 crowd fuel (allies read once a turn: decision-identical); 64 the blocked-bank breaker (our score frozen rob_dig_rounds
    // with a bag: the bank dig ignores its HP guard).
    static constexpr int robx = 59;
    static constexpr int rob_dbg = 0;                  // diagnostics (scratch only)
    static constexpr int rob_frz_k = 4;               // robx 16: frozen-flee turns (no tile gained, no damage) before the breaker acts
    static constexpr int rob_sc_rounds = 40;           // ... with neither score moving for this many rounds
    static constexpr int rob_resume = 25;              // ... a trailing / level team resumes its goals for this many rounds
    static constexpr int rob_min_round = 200;          // ... from this round (the opening's 0-0 is not a stand-off)
    static constexpr int rob_dig_rounds = 150;         // robx 64: our score frozen this long + a bag: the bank dig ignores its HP guard
    static constexpr int rob_fg = 0;                   // robx 8: 1 = include v278's fuel_guard (the two knobs below; it changes play), 0 = reads only
    static constexpr int rob_fg_field = 45000;         // robx 8: the farm action builds a missing field only above this fuel (else 12k)
    static constexpr int rob_fg_ward = 50000;          // robx 8: the ward waits for a turn with this much fuel left
    // bankx (10 Nov, docs/research/diag_10nov/scout.md rules 1-2, bank.md; static constexpr: 0 compiles out). Bits:
    // 1 threat bank (band: with 20+ gems near an altar and an enemy within 12 the top tributes within 10 rounds 0.64 of the
    // time, we 0.31; our carry episodes end in death 12.9 % v 3.5 %): a body with >= bankx_bag gems, an enemy champion seen
    // within bankx_er in the last bankx_age rounds, HP >= bankx_hpmin, and a safe altar (no visible enemy within 2, no recent
    // lock, no visible enemy whose ready stun reaches it) within bankx_walk walk: + bankx_bonus bank rate, the WORK hold and
    // the planner's hold end, and a breaking body banks there (act_bank) when it is nearer that altar than every visible enemy.
    // 2 escape recall (band: finished recalls started 4-6 tiles from the nearest enemy, top 3.5 a game, us 0.6): below
    // bankx_hp HP share with an enemy near lately, recall when no visible enemy can strike me next turn (reach + 1, >= 4
    // tiles), past the 9-tile / 8-round guard of recall_unsafe(). 4: every recall uses that reach test in recall_unsafe().
    // The dth-2 abort stays. 8 (on bit 1): the threat bank needs a survivable channel (bankx_surv).
    static constexpr int bankx = 2;
    static constexpr int bankx_bag = 20;
    static constexpr int bankx_walk = 8;
    static constexpr float bankx_bonus = 20.0f;
    static constexpr int bankx_er = 12;
    static constexpr int bankx_age = 3;
    static constexpr float bankx_hpmin = 0.3f;
    static constexpr int bankx_stun = 1;               // 1: a visible enemy with a ready stun reaching the altar (+ 2) vetoes it
    static constexpr float bankx_hp = 0.5f;
    static constexpr float bankx_surv = 1.0f;           // bit 8: the channel's expected hits must stay below my HP x this
    static constexpr int bankx_dbg = 0;                // diagnostics: BANKDBG counters at r600 / r1000 (scratch only)
    // s2end (session2, 10 Nov; docs/research/diag_10nov/session2.md cause 3): the race end. [measured, 133 near-Elo games]
    // 26 end with both teams past 800 banked and we win 10; in 6 of our 16 close losses our banked + carried gems passed
    // 1,000. We stunned or locked 0 enemy tribute channels in 85 v278 games. 02fields (loss): Vesper with the winning 206
    // gems at 20 % HP looped recall -> land on the spawn -> walk off to bank (the plan_end +1000 offer) -> recall for 175
    // rounds without healing (the spawn heal lands at the turn END). static constexpr: 0 compiles out. Bits:
    //   1 a body that starts its turn on our spawn below s2e_heal of its max HP, with no visible enemy able to strike it
    //     next turn, ends its turn there (hits in reach only): the heal is full at the turn end [sdk; measured surv.md];
    //   2 a ready stun (an is_cc ability that targets enemies; Marcella's attack-reset-attack in melee) goes on a visible
    //     enemy within 6 that is submitting gems with a bag >= s2e_bag, before anything else (a stun cancels the channel
    //     [rules]); never on a body already stunned (a second stun is wasted [measured mech.md]);
    //   4 their finisher: a visible enemy submitting gems whose bag + their score reaches the winning total (or whose bag
    //     >= s2e_hoard) draws every body within s2e_r above 30 % HP that can get in reach before the channel ends
    //     (remaining_channel_time): walk to it, then stun / lock (bit 8) / hit;
    //   8 hold one altar lock from round s2e_lock_round (10 gold); bit 4 places it only on the altar the finisher channels
    //     at and only when no ally of ours channels there (our lock cancels our own ally's channel [measured mech.md]).
    static constexpr int s2end = 1;
    static constexpr float s2e_heal = 0.6f;
    static constexpr int s2e_bag = 20;
    static constexpr int s2e_hoard = 150;
    static constexpr int s2e_r = 10;
    static constexpr int s2e_lock_round = 500;
    // sizex (size agent, 10 Nov; docs/research/diag_10nov/size.md): what each body buys. [measured, 150 games of tz-mega v
    // the band, decoded] By r600 our team buys 108.6 stat shards (30.3 Health / 58.8 Strength / 19.5 Focus) for 3,007 gold;
    // the band 119.6 (47.2 / 38.4 / 34.0) for 3,361: the same shards per gold, but 28 % Health v 39 %. Our Marcella holds
    // 2.0 Health of 17.1 shards (band 13.7 of 40.2), HoR 0.7 of 8.4 (band 5.1 of 13.7). Held gold, earn-to-spend wait
    // (28.6 v 28.1 rounds) and shop visits (31.6 v 24.0) are level or ours ahead: not causes. static constexpr: 0 compiles
    // out. Bits:
    //   1 support size line (Marcella, HoR): Prospector (main stat), Durability Health, Bruiser Health, then Jungle /
    //     Monster / Capture with each new set's stat Health while Health < sz_h x all shards (the band's mix), else the
    //     main stat; no Treasure (+10 % of a support's ~500 gold by r600 does not repay its 150 [measured hp_per_gold]);
    //     a set in progress is finished first. Then the after-line.
    //   2 Greed after-line for every body whose line is done (instead of Power): Greed shards are plain shards and 25
    //     combine into a 40-shard emblem [sdk: engine item dump, mechanics.md] (+15 shards for 750 gold v Power's +5);
    //     sets in the main stat then Health at pw_ratio : 1.
    //   4 Vesper's Greed early: after Prospector and Capture, 25 Greed shards in Strength before the rest of her line.
    //   8 (with 2) the Greed after-line starts in Health and alternates Health / main stat 1 : 1 (team size late).
    //  16 (with 2, without 8) the Greed after-line starts in the main stat and alternates main / Health 1 : 1.
    static constexpr int sizex = 11;
    static constexpr float sz_hm = 0.37f;              // Marcella's Health share target (band r600: 13.7 of 40.2)
    static constexpr float sz_hr = 0.38f;              // HoR's (band r600: 5.1 of 13.7)
    // endx (endg, 10 Nov; docs/research/diag_10nov/endg.md): walled-in altars. rob.md: v idle on 01boss-battle (a monolith
    // holds the only tile beside the only altar) and 02the-pack (the altar inside a ring of wolves) our bodies held winning
    // bags 2-3 tiles off for 1,300+ rounds, or farmed nothing at all (01boss-battle B: all six stood at the monoliths from
    // r320 to r2000 walking to groups beyond them, 1,405 gold). A dead camp stays dead until its whole group is captured
    // [rules; mechanics.md], so one kill opens the way. static constexpr: 0 compiles out. Bits:
    //   1 the breach: when no altar has a free tribute tile (Chebyshev 1) that our spawn reaches without crossing a camp
    //     tile, the cheapest one or two camp tiles joining that open ground to an altar (computed from the map at run
    //     time) are dug first when their camps total at most endx_cap HP: a body digs with HP >= endx_hp of its max and
    //     >= endx_k x the strength of the breach group's camps reaching its stand tile; once open, the walk to the altar
    //     goes through the breach; a body without gems on the only free tribute tile of an altar, or in the opened
    //     breach, steps off it;
    //   2 while the breach stands, groups with no spawn tile beside that open ground are not farmed (their walk ends at a
    //     live camp).
    static constexpr int endx = 3;
    static constexpr float endx_hp = 0.5f;
    static constexpr float endx_k = 6.0f;
    static constexpr float endx_cap = 6000.0f;         // bit 1 digs only a breach of at most this camp HP (02guardians: digging a
                                                       // 20,000-HP monolith cost 4-15 deaths and 650-1,100 gems v idle; the
                                                       // siege farm takes it once bodies are big, and it pays 200 gems)
    static constexpr int endx_dbg = 0;                 // diagnostics: ENDXDBG at r500 / r1000 / r1999 (scratch only)
    // s2b (session2b, 10 Nov; band replays tz184_big v p83_m2): bits
    //   1 no escape recall (bankx 2) while a visible enemy within s2b_er is closing on me: A3 starts 6.3 such recalls a
    //     game, 66-80 % are cancelled a turn later by the dth-2 abort (16-33 % arrive); the body flees instead and may
    //     recall on a later turn. Not closing: 50-61 % arrive (kept).
    //   2 work through: a body holding its live group in contact (work_hold) drops a join / answer / opener / hunt commit
    //     on an enemy beyond its attack range and keeps the hold (finish, stunned target and execute still commit).
    static constexpr int s2b = 1;
    static constexpr int s2b_er = 6;
    // s4x (session4, 10 Nov; v306 band replays: two-tile flips 3.9 runs / 87 body-turns a game v the opponents' 2.2 / 21;
    // runs of 30+ turns 0.61 a game v 0.03; e.g. a body under a wall row flipping 290 rounds). Cause [code]: on a goal walk
    // step_to's greedy hop takes an equal-Chebyshev, smaller-Euclid sideways tile toward the target; when nothing is
    // nearer it falls back to the engine's shortest path (move_towards), which steps around the wall; the next turn the
    // greedy hop steps back. Bits:
    //   1 step_to: back on the tile of two turns ago on a goal walk -> the engine's shortest path for s4_lock turns.
    //   2 step_field: the same guard (its equal-distance sidestep can flip too) -> the engine's path to the fallback tile.
    static constexpr int s4x = 3;
    static constexpr int s4_lock = 8;
};
inline Params P;

inline float lerp(float a, float b, float t) { return a + (b - a) * std::clamp(t, 0.0f, 1.0f); }

// Worth of one gold earned at round r.
inline float gold_mul = 1.0f;  // regime B (set at the first turn): gold priced x regb_gold before r300
inline float gold(int r) {
    if (r < 300 && gold_mul != 1.0f) {
        const float g = r < 150 ? P.gold_r150 : lerp(P.gold_r150, P.gold_r300, (r - 150) / 150.0f);
        return g * gold_mul;
    }
    if (r < 150) return P.gold_r150;
    if (r < 300) return lerp(P.gold_r150, P.gold_r300, (r - 150) / 150.0f);
    if (r < 500) return lerp(P.gold_r300, P.gold_r500, (r - 300) / 200.0f);
    if (r < 750) return lerp(P.gold_r500, P.gold_r750, (r - 500) / 250.0f);
    return lerp(P.gold_r750, P.gold_late, (r - 750) / 500.0f);
}

// openx bit 1: the gold weight in a group's price (gold(r), x open_gold_w until open_until).
inline float gold_px(int r) {
    if constexpr ((Params::openx & 1) != 0)
        if (r < Params::open_until) return gold(r) * Params::open_gold_w;
    return gold(r);
}

// Worth of a kill (and so of a death) at round r, beyond the bag.
inline float kill(int r) {
    if (!P.kill_curve) return P.kill;
    if (r < 150) return P.kill_r150;
    if (r < 300) return lerp(P.kill_r150, P.kill_r300, (r - 150) / 150.0f);
    if (r < 500) return lerp(P.kill_r300, P.kill_r500, (r - 300) / 200.0f);
    if (r < 750) return lerp(P.kill_r500, P.kill_r750, (r - 500) / 250.0f);
    return P.kill_r750;
}

// Worth of one carried gem, given the bag it sits in and whether enemies are near.
inline float carried(int bag, bool danger) {
    float v = P.carried_base - P.carried_per_gem * float(bag) - (danger ? P.carried_danger : 0.0f);
    return std::clamp(v, 0.3f, 0.95f);
}

}  // namespace value
