# Scenarios: single questions a price or label depends on

## S6: who takes a group's hits when k bodies clear it? (open, 14 Oct)

The bodies-needed label depends on it. Rules: each awake monster hits the nearest champion every round, ties
to the lowest id [measured A2]. Two models in `bots/strat/parts/10_model.py` (one constant switches):
- **one body takes every hit** (physically exact if nobody moves): generic 50 Str / 1,000 HP champion needs
  1 / 3 / 6 / 5 bodies for wolf / pair / pack / elk;
- **hits shared across the k bodies** (the front body steps out and the next takes over): 1 / 2 / 3 / 3,
  which matches what tzu and core actually did on rows (two bodies per pack).
Measure with the scenario harness: two generic bodies on a wolf pair, does the second body relieve the first
before it drops under 40 % HP, and what is the clear time? Until then the shared model is the default.
