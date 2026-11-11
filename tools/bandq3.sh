#!/bin/zsh
# bandq3.sh QUEUEFILE (10 Nov): band stages one after another via tools/band3.sh. Lines: N|note|SRC|BASE|k=v ...  or  !shell command.
# A line is popped as it starts. Pause for the teammate with a line: !until [[ -f ~/tzunami_data/scrims/RESUME ]]; do sleep 30; done
cd "$(dirname "$0")/.." || exit 1
Q=$1
while pgrep -f 'tools/band(big|3)' > /dev/null; do sleep 20; done
while true; do
  L=$(head -1 $Q 2>/dev/null)
  [[ -z $L ]] && { sleep 30; [[ -f $Q.stop ]] && break; continue; }
  tail -n +2 $Q > $Q.tmp && mv $Q.tmp $Q
  if [[ $L == !* ]]; then echo "$(date -u +%H:%M) run ${L#!}"; eval "${L#!}"; continue; fi
  IFS='|' read N NOTE SRC BASE KV <<< "$L"
  echo "$(date -u +%H:%M) start tz-$N v $BASE ($NOTE) [$SRC $KV]"
  zsh tools/band3.sh $N "$NOTE" $SRC $BASE ${=KV} > /dev/null 2>&1
  echo "$(date -u +%H:%M) done tz-$N: $(grep -E 'stage 1|STOPPED|upload failed|RESTORE' ~/tzunami_data/scrims/res_tz$N.txt | tr '\n' ' ')"
  python3 -I tools/scrim.py metrics $BASE tz${N}_big 2>&1 | grep -E '^  (win|share|deaths|kills|coll300|trib750|their750)' | tr -s ' ' | tr '\n' ';'; echo
done
echo "$(date -u +%H:%M) runner stopped"
