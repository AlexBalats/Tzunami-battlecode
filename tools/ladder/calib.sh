#!/bin/sh
# Every shipped version v fixed references, plain (70 maps x 2 sides): the local side of the ladder calibration
# (JUDGE.md §8). Old builds unzipped from submissions/ into bots/_cal_pN first.
#   sh tools/ladder/calib.sh OUT_DIR "REF1 REF2" BOT...
O=$1; REFS=$2; shift 2; mkdir -p $O
for ref in $REFS; do for b in "$@"; do
  [ -s $O/$b-v-$ref.arena ] && continue
  python3 -I tools/arena.py $b $ref --jobs 2 2>&1 | grep -E "Record|Mean|both sides|saved|rror" > $O/$b-v-$ref.arena
done; done
echo DONE > $O/DONE
