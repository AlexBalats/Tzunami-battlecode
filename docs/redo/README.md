# The redo (20 Oct onward): design documents

The team-loop line is closed, and so is everything before it. We rebuild from `bots/strat-sw`, the ladder entry and
the bar. Each of these seven documents answers one point from the user's redo brief (19 Oct, end). They are design
only: none of them changes code. Tags are as in `CLAUDE.md`: **[rules] [sdk] [measured] [guess]**, plus
**[pm]** for what a postmortem says it did in its own game (not checked in ours).

**Patch 3.0 first.** [00_PATCH_3_0.md](00_PATCH_3_0.md) came after the seven documents: the 3.0.1 numbers and the
strat-sw items (X1–X10) it breaks, each assigned to a session below. Where a document here quotes a 2.2.4 number,
the patch doc wins.

| # | Document | The point it answers |
| --- | --- | --- |
| 0 | [00_PATCH_3_0.md](00_PATCH_3_0.md) | The 20 Oct balance patch (cambc 3.0.1): what changed, what it breaks, who fixes it. |
| 1 | [01_BLUNDER_PATHFINDING.md](01_BLUNDER_PATHFINDING.md) | "The pathfinding wasn't for the drafting phase at all; it was for our bots playing the game." Checked against our docs, `strat-sw` and `GameRules.md`. |
| 2 | [02_GST_REREAD.md](02_GST_REREAD.md) | A focused, section-by-section re-read of the Generalized Strokes Theorem postmortem (2026, 2nd place). |
| 3 | [03_ARCHITECTURE.md](03_ARCHITECTURE.md) | Their two interfaces, State Updater and Behavior, built for our bot. |
| 4 | [04_COMMS.md](04_COMMS.md) | The 8 bytes: what to keep now, and what to borrow later. |
| 5 | [05_PATHFINDING.md](05_PATHFINDING.md) | In-play pathfinding: Om Nom's Optimal Bug and Gone Fishin's methods, converted to CAMBC. |
| 6 | [06_MACRO.md](06_MACRO.md) | Two carries, opening together, solo captures for the main carry, shopping at 150–300 gold, Home. |
| 7 | [07_MICRO.md](07_MICRO.md) | XSquare micro: an information matrix of the 9 tiles, built from the raycast vision we actually have. |
| 8 | [08_FIGHT.md](08_FIGHT.md) | The fight deep dive: the mechanics per champion, what they imply, R5's fight replays, and the small build (F1–F6). |

## How the seven fit together

```
              ┌─────────────────────── one turn of one champion ───────────────────────┐
  sense ──► Info (07: the matrix, only when a threat is near) ──► StateUpdater (03, roles from 06)
    │                                                                  │ picks one
    │ 8 bytes in (04)                                                  ▼
    │                                     Behavior.execute(): Farm / Bank / Shop / Heal / Micro / Ward ...
    │                                                                  │ every move goes through
    │                                                                  ▼
    │                                     Nav (05): global field + local window + team order
    ▼
  post passes (03: spend any unused attack, cast or ward) ──► 8 bytes out (04) ──► trace
```

- **03 is the frame:** every other piece is a Behavior, a service the Behaviors call (Nav, Info, Comms), or a rule
  inside the State Updater.
- **05 and 07 share one model of danger.** Pathfinding avoids the tiles that micro scores as unsafe, and micro uses
  pathfinding's reachability (no micro through walls). Both need the same "who can hit tile q next round" bitboards.
- **06 decides the roles** (main carry, second carry, crew) that pick a State Updater for each body.
- **04 stays as it is** until 06 or 07 needs a byte it does not have.

## The plan: one file = one session (user, 20 Oct)

Each build session takes **one** document and builds only that, so nothing is half-done and forgotten across context
compactions. A session starts by reading this README, the document, `00_PATCH_3_0.md` (its items for this session), and the top
of `docs/HANDOFF.md`, and ends by ticking its patch items and updating the HANDOFF. 01 and 02 are reference, not sessions.

| Session | Document | What gets built | Gate |
| --- | --- | --- | --- |
| 1 (done 20 Oct) | [03_ARCHITECTURE.md](03_ARCHITECTURE.md) | R0: copy `bots/strat-sw` to `bots/redo`, snapshot `bots/strat` as `bots/_teamloop`. R1: cut strat-sw into Behaviors and State Updaters with the *same* decisions, plus the `fall` overflow fix (04 §2). | Mirror vs strat-sw ≈ 50 %, and per-body traces match on 2 maps. Proves the frame, adds nothing. |
| 2 (done 20 Oct) | [05_PATHFINDING.md](05_PATHFINDING.md) | Nav: global field, local window, team order, danger-aware steps, stall handling. | Rounds per tile on direct trips (ours 1.53, theirs 1.22), stuck/osc traces, crew arrival spread. |
| 3 (done 20 Oct) | [06_MACRO.md](06_MACRO.md) | Roles, opening together, the carry's solo capture, the shopping window, builds (Home first on Vesper), per-body emblems for the crew. The roster grows (Ren, Cassi & Issac) in later sessions on the same doc if 3 runs long. | Full arena; the carry's gold share, round of its first emblem, captured g/r. |
| 4 (done 20 Oct: scrapped) | [07_MICRO.md](07_MICRO.md) | The info matrix and `isBetter`, one engine for fights and camp aggro. Built, lost to R3 (12W/30L), deleted; X4 / X8 / diagnostics kept (07 §14). | Deaths a game, bag lost, kill/death in fights; then the full arena. |
| when needed | [04_COMMS.md](04_COMMS.md) | Comms v3 (typed event byte, finer sighting) only when 06 or 07 needs a byte it doesn't have. | Whatever the feature it serves is gated on. |
| 5 (done 20 Oct) | [06_MACRO.md](06_MACRO.md) §11 | Roster growth: Ren third (the second carry, with its own gold); Cassi & Issac built (body slots), lost, not picked; X8 gate on Hunt / HOLD removed. R5 vs strat-sw 20W/22L, margin +105, deaths 14.2 → 10.8 (06 §11.6). | 06's measures. |
| 6, last (done 20 Oct) | [08_FIGHT.md](08_FIGHT.md) | **Fight deep dive (user, 20 Oct).** Doc from the mechanics first, then F1–F6: fight-turn fuel, `duel` P(lose), heal at the first losing hit, recall out of reach, trapped = melee, `KILL_PRICE` 1. R6 vs strat-sw **28W/14L**, margin +164; zipped `submissions/redo-r6.zip` (08 §8). | Fight trade ratio, kill/death, bags lost, deaths by cause; then the strat-sw bar. |
| 7, hotfix (21 Oct: H1–H3, H5 built, R8 zipped; H4 next) | [09_HOTFIX_R8.md](09_HOTFIX_R8.md) | **R8 from R7's ladder losses (user, 21 Oct).** H1 one turn fuel budget + `need_k` memo (rollovers 791/game on big-world), H2 the heal deadlock (`uhit` tested on the wrong tile), H3 one finish-or-leave test for farm and heal, H4 idle crews (tank share, takeable candidates, Fall heals/escorts, crew gold), H5 delete HOLD. | Rollovers ≈ 0, heal A-B-A ≈ 0, trips per take ≤ 1, crew fall < 5 %; then the strat-sw bar and not worse than R7 (09 §4). |
| 7, next | [08_FIGHT.md](08_FIGHT.md) §9 | **The fix pass before the ladder (user, 20 Oct):** G1 swarm deaths on small maps, G2 fight deaths up, G3 the `SCAN.post` ward error. | Deaths/g, fight deaths/g, worst map, faults 0/0; more W than L vs strat-sw and not worse than R6; then the ladder zip. |

**The redo is finished** (20 Oct, session 6): the fight deep dive was its last session (user, 20 Oct). 07's micro frame (matrix, compare) was built and scrapped (07 §14: it overruled the macro, miscounted ranged reach and ran over fuel in fights). The deep dive starts from those lessons, not from that code.

A partial redo is judged on its own session's measures (the Gate column), not on win rate vs strat-sw (user, 20 Oct:
the pieces need each other, so a half-built redo is expected to be worse). The strat-sw bar (`CLAUDE.md` rule 5)
returns once the pieces that need each other are built. Session 1's mirror showed why: R1 is the same bot as strat-sw
and still lost 00lanes from both sides on fuel timing alone (03 §5.1).

## Unknowns to check when building

There is no register any more (the old one is `docs/archive/ASSUMPTIONS.md`, history only). Each unknown below lives
in the document that needs it and is checked in the session that builds it; once measured, the document says
**[measured]** with the match details.

| Id | Unknown | Where |
| --- | --- | --- |
| P-a | A champion inside a bush cannot be seen, and so cannot be targeted, by an enemy outside it unless a ward sees in. | 07 |
| P-b | A write to `cambc.shared_memory` is visible to allies that act later in the same round. | 04, 05 |
| P-c | Vesper can dash and basic-attack in the same turn (the dash is an ability, not the ordinary move). | 07 |
| P-d | When two champions are equally near an awake monster, the tie rule (lower slot is hit) holds for enemies too. | 07 |
| P-e | `visible_tiles_from(q)` (or `Bitboard.shadow_cast`) is cheap enough to run on 9 candidate tiles a turn. | 07 |
| P-f | Setting priority by distance to the goal (the front acts first) cuts blocked steps in a moving crew. | 05 |
| P-g | The main carry's solo capture after a team clear raises team g/r (via an earlier first emblem and +33 % gold). Supported, not isolated (06 §8, §10). | 06 |
| P-h | The SDK shows a visible enemy's ability cooldowns. | 07 |
| P-i | A visible enemy's state flags (recalling, tributing) are readable. | 07 |

## The user's answers (20 Oct)

1. **"~4–5 emblems a game"** is per individual crew champion (not the carries): the 3rd body in 3v3 (e.g. Cassi &
   Issac), the 3rd and 4th in 4v4 (e.g. Ryth and Cassi & Issac). In 06 §3.1 and §4.6.
2. **Home first on Vesper.** In 06 §4.6.
3. **Ren in the draft:** build support for Vesper *and* Ren, which grows the roster; nobody is dropped. In 06 §3.2, §7.
4. **Order of work:** one file = one session (above).

## Sources

`sources/` holds the text of the three postmortems these documents cite:
- Gone Fishin 2023: https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf
- Om Nom 2025: https://battlecode.org/assets/files/postmortem-2025-om-nom.pdf
- Generalized Strokes Theorem 2026: https://battlecode.org/assets/files/postmortem-2026-generalized-strokes-theorem.pdf
- GST's code (State Updaters and Behaviors): https://github.com/uravt/Battlecode26/tree/main/src/Version40/BabyRatBehaviors
