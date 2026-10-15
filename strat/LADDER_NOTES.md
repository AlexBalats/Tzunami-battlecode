
## 15 Oct 12:16, ten games on the group-opener build (9e0b3c4): ahead at the last tick in 5, behind in 5

Losses and their failure modes (details: `runs/ladder/<id>-logs.zip`, scratch scripts ladsum / laddetail / ladrace):
- **1a406974, 71x71, 5 picks, solo 0.60**: three of five seeds in the contested centre (34,32 / 34,36 / 34,15); the
  enemy 3-stack held altar A2 from r31; champions 9/0/6 dithered heal / hold / kill / farm at 50-74 % HP with farm
  priced 0.1-1.4 (dcost 24) for 100 rounds; score 0 until r150 (theirs 144 at r50, 250 at r100). Vesper farmed her
  own side well (22 gems + 108 gold by r40, 10 shards by r100) but carried 44-66 gems while SHOP (8-9) beat BANK (1.3).
- **173c26eb, 50x50, 4 picks, solo 0.22 (group game)**: two pairs seeded on 3-wolf packs (need 3): HP 46 / 33 / 48 /
  5 % by r26-70, heals. Handoff worked (Vesper gold 24 -> 402 -> 780 -> 1128) but she never cashed out: bag 66 -> 132
  -> 198 -> 264 while unsplit FARM (49-65) beat BANK (4.5-39), score stuck at 66 from r100 to r240; shop at r245 with
  1128 gold. Non-carries 0 gold all game. Enemy 132 at r100, 330 at r200.
- **afc28f06, 50x50, 5 picks, solo 0.55 but ggems 0.89**: pure farm race, 0 deaths, 1.4 vs 2.0 gems/round. Every bag
  was 22-44: we farmed wolves while 89 % of the gems sit in group camps we never took; 21 % of champion-rounds banking
  22-gem bags. The rematch on the same map (a827bb95) was won on Vesper's kills, not on farming.
- **cbf8e2f1, 40x40, 4 picks, solo 0.75**: enemy 72 at r50 / 180 at r100 (a stack), us 22. Farm only 43 % of
  champion-rounds, bank 20 % (per-wolf trips), Vesper kill 34 % + hunt 20 % with 6-18 gold; she died banking 88 gems
  with one enemy near (r150), Varg died with 94 (r356).
- **e2a86964, 80x80, 3 picks, race**: lost 920-976 at r550. Half the farm targets > 12 tiles; from r307 Vesper spent
  32 % hunting + 13 % killing (hunt phase at 15 shards) on a map with nobody to catch; bank 22 %.

Cross-cutting: (A) the carry hoards (no bank / shop while unsplit farm prices dominate); (B) pairs sent to 3-body
packs; (C) the group gate ignores ggems (afc28f06: solo 0.55, gems 0.89); (D) bank per wolf: 20-22 % of
champion-rounds; (E) Vesper's hunt phase on farm-race maps; (F) centre seeds + heal/hold dither against a stack with
farm priced ~0; (G) deaths banking 88-124 bags with an enemy near.
