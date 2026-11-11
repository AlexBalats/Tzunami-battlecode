# Hill-climb of value.h knobs on the teammate's bot (9 Nov, agent)

Base: `bots/_hc` = copy of `bots/_friend` (tz-116 + prio_fight 1 + bushw 1 / bushw_k 12) with the one Latin-1 byte in a
value.h comment (`\xa7` in the tp comment) re-encoded as UTF-8. The default _hc build is byte-identical to _friend's wasm
(debug and release, `cmp`) [measured].

Method: greedy coordinate climb. One knob changed per variant (`tools/variant.py _hc _hcN k=v`), judged with
`tools/judge.py _hcN --opp _hc --jobs 2` (128 maps x 2 sides = 256 games, all maps). Accept only at >= 52 %; an accepted
value is written into `bots/_hc/src/value.h` and becomes the next opponent. Caveat: one 256-game run has a ~3 % SE, so a
52 % gate passes noise about 1 in 4 times per try; the final checks v _friend and v tz-116 are the real test. Each
run takes ~3 min. A value that passes 52 % is re-judged once with `seed=1` (the 1e-4 goal-price tie-break nudge gives a
new sample of the same maps); it is accepted when the two runs average >= 52 %.

| step | knob | value (was) | win % v best | deaths v | accepted? |
| --- | --- | --- | --- | --- | --- |
| 1 | bushw_k | 8 (12) | 50.8 | 4.7 v 4.2 | no |
| 2 | bushw_k | 16 (12) | 47.3 | 4.7 v 4.9 | no |
| 3 | bushw_k | 24 (12) | 48.8 | 4.5 v 4.8 | no |
