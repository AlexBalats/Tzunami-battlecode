#!/bin/zsh
# bandq.sh QUEUEFILE : run band stages one after another. Each line: N|note|SRC|k=v k=v ...  (popped from the top as it
# starts, so lines can be appended while it runs; stops when the file is empty). Results: ~/tzunami_data/scrims/res_tzN.txt
cd "$(dirname "$0")/.." || exit 1
Q=$1
while true; do
  L=$(head -1 $Q 2>/dev/null)
  [[ -z $L ]] && break
  tail -n +2 $Q > $Q.tmp && mv $Q.tmp $Q
  IFS='|' read N NOTE SRC KV <<< "$L"
  echo "$(date -u +%H:%M) start tz-$N ($NOTE)"
  zsh tools/bandbig.sh $N "$NOTE" $SRC ${=KV} > /dev/null 2>&1
  echo "$(date -u +%H:%M) done tz-$N: $(grep -E 'stage 1|STOPPED' ~/tzunami_data/scrims/res_tz$N.txt | tr '\n' ' ')"
  python3 -I tools/scrim.py metrics tz66_big tz${N}_big 2>&1 | grep -E 'win|share|deaths|gold300|trib750' | tr -s ' ' | tr '\n' ';'; echo
done
echo "$(date -u +%H:%M) queue empty"
