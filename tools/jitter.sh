# Judge a bot over fuel jitters (23 Oct, docs/nav/ROUTING.md §2.7). The arena is deterministic but chaotic: any change
# flips about half the games, so one 80-game run moves by ±5 wins. A copy that burns J loop steps at the start of each
# play turn plays the same strategy with different chaos; 8 jitters = 640 games, SE about 2 points of win rate.
# Calibration [measured 23 Oct]: jittered cpp-port vs cpp-port 279W/281L (49.8 %), margin +9.
#   sh tools/jitter.sh BOT [J ...]      (repo root; default J = 0 300 700 1500 100 500 1000 2500; 0 = BOT itself)
# Copies are bots/_BOT_jJ (git-ignored scratch: delete them after). Runs vs cpp-p15 (OPP=... to change; cpp-port was deleted 27 Oct), --jobs 2
# (JOBS=1 while something else runs). Prints each run and the total with tools/jitter_sum.py.
cd "$(dirname "$0")/.." || exit 1
B=$1; shift; JS=${*:-0 300 700 1500 100 500 1000 2500}; OPP=${OPP:-cpp-p15}; RUNS=""
for J in $JS; do
  N=$B
  if [ "$J" != 0 ]; then
    N=_${B}_j$J; rm -rf bots/$N; cp -R bots/$B bots/$N; rm -rf bots/$N/.cambc
    python3 -I - bots/$N/src/main.cpp "$J" <<'PY'
import sys
sys.path.insert(0, 'tools'); from tune import jitter_code   # J >= 100000: a hashed seed (LADDER_P12 §B1)
p, j = sys.argv[1], int(sys.argv[2]); s = open(p).read()
a = "static void turn()\n{\n"; assert s.count(a) == 1, "turn() not found"
open(p, 'w').write(s.replace(a, a + jitter_code(j)))
PY
  fi
  R=$(python3 -I tools/arena.py $N $OPP --jobs ${JOBS:-2} 2>&1 | grep "saved runs" | sed 's/saved //; s#/summary.json##')
  RUNS="$RUNS $R"
done
python3 -I tools/jitter_sum.py $RUNS
