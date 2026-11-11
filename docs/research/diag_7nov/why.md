# Why we lose (7 Nov, afternoon) — working notes

## The chain, as measured
1. **Economy first.** Tributed by r300: ours 73 v top-3 185 (2.5x). Gold per 100 rounds per body: Vesper 274 v 398,
   Marcella 98 v 242, Vendetta 60 v 166, HoR 36 v 108. Band r300 gold (ours) ~1,640; tz-1 era 918 v 1,516.
2. **Size follows economy.** After r300 their fed carries are 2.5-2.8k max HP; our supports 1-1.2k. Our deaths v the
   band ~7-8, theirs ~4. 72 % of kills on us involve 2-5 of them.
3. **Fights follow size.** Our micro is level with v93's; we lose on size and exposure (fed-enemy exposure rounds 95 v 11).

So the fight rules we keep tuning sit at the END of the chain. Avoidance (fed break, big) only trims the loss; the
lever is upstream: farm faster with every body, so supports grow too.

## Why the tuning loop stalls
- The local yardstick (v v93) disagrees with the band both ways (big, SPSA). v93 is a farming-light, fight-heavy bot of
  ours; the band farms faster. Changes that trade farming for safety look good v v93, bad v the band (SPSA weights:
  local +3.4, band gold300 -101).
- 60-game band stages: deaths CI +-0.9, wins +-0.1. Single stages produce false positives.
- Knobs on a structure that is slow by design (pricing loop, packs that follow leaders, feeding everything to Vesper).

## Hypotheses to test (cheap first)
- H1 feeding is net negative v the band (supports never grow; Vesper takes 58 % of tributes v 24 %): feed 0 on band.
- H2 the goal loop wastes ~10 rounds per camp visit (28.4 v 18.3): walking to groups that get taken, waiting,
  switching. Farming agent.
- H3 plain bugs still cost (history: the biggest jumps were bugs). Audit agent.
- H4 our engagement decision disagrees with the top 3's in identifiable states (learning agent: behaviour cloning).

## A better yardstick
- A local opponent closer to the band? We can't use their code. Options: (a) judge v idle for farming speed
  (economy is the upstream lever and idle measures it without noise from fights); (b) band stages confirmed on a 2nd
  group set; (c) a "band proxy" KPI pre-screen: gold/tributes by r300 v idle must not drop.
- Rule for now: a change must (1) not lose farming v idle (end round / gold300), (2) hold on the band on 2 group sets.

## Results
- H1 feed 0 on the band (tz-35a, v178): 13/60 (= tz-32b), gold300 -154 (CI -245..-63), deaths +1.2 (+0.05..+2.4):
  **feeding pays** (Vesper's +33 % gold). Rejected.
- tz-32 v idle baseline (256 games): end r933, gold150 755, gold300 1,756, mon300 30.2k, trib750 732, camp deaths 1.5.
