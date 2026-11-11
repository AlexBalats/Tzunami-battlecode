#!/bin/zsh
# jslot.sh CMD... : run CMD holding one of 3 local-judge slots (10 Nov: the user allows ~3 local judges at once).
# Every agent wraps tools/judge.py (and any other multi-game batch) in this. Slots are dirs in ~/tzunami_data/jslots holding a pid.
D=~/tzunami_data/jslots; mkdir -p $D
while true; do
  for i in 1 2 3; do
    if mkdir $D/s$i 2>/dev/null; then echo $$ > $D/s$i/pid; trap "rm -rf $D/s$i" EXIT INT TERM; "$@"; exit $?; fi
    p=$(cat $D/s$i/pid 2>/dev/null); if [[ -n $p ]] && ! kill -0 $p 2>/dev/null; then rm -rf $D/s$i; fi
  done
  sleep 15
done
