#!/bin/zsh
# seeds.sh NAME k=v ...  : 4 seeds (seed=0..3) of tz + overrides v v93, sequential; prints each run's summary to $S/NAME.s<seed>.txt
cd "$(dirname "$0")/.." || exit 1
S=${JUDGE_TMP:-$HOME/tzunami_data/judge}
mkdir -p $S; export JUDGE_TMP=$S
mkdir -p $JUDGE_TMP
N=$1; shift
for s in ${=SEEDS:-0 1 2 3}; do
  python3 -I tools/variant.py ${SRC:-tz} _${N}_$s seed=$s "$@" >/dev/null
  python3 -I tools/judge.py _${N}_$s --opp v93 --jobs 2 > $S/$N.s$s.txt 2>&1
  rm -rf bots/_${N}_$s
done
