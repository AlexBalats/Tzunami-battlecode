#!/bin/zsh
# bandq2.sh QUEUEFILE BASE : band stages one after another, paired with BASE (an unselected base label of the live bot)
# via tools/bandbig2.sh. Lines: N|note|SRC|k=v ...  or  !shell command (run as is). Popped as they start.
cd "$(dirname "$0")/.." || exit 1
Q=$1; BASE=$2
while pgrep -f 'tools/bandbig' > /dev/null; do sleep 20; done
while true; do
  L=$(head -1 $Q 2>/dev/null)
  [[ -z $L ]] && break
  tail -n +2 $Q > $Q.tmp && mv $Q.tmp $Q
  if [[ $L == !* ]]; then
    echo "$(date -u +%H:%M) run ${L#!}"; eval "${L#!}"; echo "$(date -u +%H:%M) done cmd: $(tail -c 300 ~/tzunami_data/scrims/cmd.log 2>/dev/null | tr '\n' ' ')"
    continue
  fi
  IFS='|' read N NOTE SRC KV <<< "$L"
  echo "$(date -u +%H:%M) start tz-$N ($NOTE)"
  zsh tools/bandbig2.sh $N "$NOTE" $SRC $BASE ${=KV} > /dev/null 2>&1
  echo "$(date -u +%H:%M) done tz-$N: $(grep -E 'stage 1|STOPPED' ~/tzunami_data/scrims/res_tz$N.txt | tr '\n' ' ')"
  python3 -I tools/scrim.py metrics $BASE tz${N}_big 2>&1 | grep -E 'win|share|deaths|gold300|kills|trib750|their750' | tr -s ' ' | tr '\n' ';'; echo
done
echo "$(date -u +%H:%M) queue empty"
