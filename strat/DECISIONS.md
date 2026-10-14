# Decisions

## 14 Oct 2026

- **Stop building scenario trees.** The action space is too large to script; the decision space is six options
  priced in one currency (team gems per round). Behaviour emerges from prices moving with the state.
- **Roles and modes are multipliers**, never code paths (Vesper: capture cheap with a lock, gold worth more;
  Ryth: hold worth more with a stun).
- **Execution stays dumb**: six executors, each with a timeout; the 10k-line bot died of execution logic.
- **Fix numbers, not rules**, in the learning loop.
- **Map model at draft, labels in the 1,024 bytes, fields rebuilt lazily at play.** `tools/mapmodel.py` is the
  offline reference with an HTML page per map (`runs/mapmodel/index.html`); the in-engine port lives in
  `bots/strat/parts/10_model.py` and must print the same summary on round 1.
- **Regime is counted on altars, not groups** (few / pick / many relative to team size). Group counts are a
  separate richness number.
- **Bodies needed per group from the measured clear model** (monsters die one at a time, hits land on one body),
  not the all-monsters-all-rounds formula (which said 8 bodies for a wolf pack).
- **Reaction distance 8** for ownership: vision 8 + 5-turn recall = 7 rounds of warning. The user accepted the
  interlock reading (all altars contested, wolves safe on each side, elks on the frontier).
- **Recall-or-walk label is travel time only**; heal and shop value go into the price, not the map label.
- **Draft fuel is the constraint (14 Oct, measured on expanse 80x80).** Core labels cost 19.4M of 21.8M on
  draft turn 1 (ownership 4.7M and per-tile margin 6.5M are the two to cut); paths, chokes, wards, blocks and
  the danger grid did not fit in draft turns 2-5 (~1.3M usable each). Decision: cut the two big stages first;
  if the rest still does not fit, the play turns compute chokes/danger lazily in the background (as fields are).
