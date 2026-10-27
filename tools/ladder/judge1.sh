#!/bin/sh
# One plain arena run A v B (70 maps both sides), decoded, dashboard beside an optional reference set.
#   sh tools/ladder/judge1.sh A B OUT_DIR [REF_NAME=REF_DIR]
python3 -I tools/arena.py $1 $2 --jobs 2 2>&1 | grep -E "Record|Mean|both sides|saved" | tee $3.arena
RUN=$(grep saved $3.arena | sed 's/saved //; s#/summary.json##')
sh tools/replay/arena_dec.sh $RUN $3 3 > /dev/null
python3 -I tools/replay/dash.py $4 run=$3/decu
