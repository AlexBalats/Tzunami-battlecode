#!/bin/zsh
# bandbig.sh N "note" SRC k=v ... : variant of SRC stamped tz-N, uploaded, paired with big32 in two stages:
# stage 1 = base groups 0,1 (60 games); STOP if v tz66_big (paired) wins <= -0.05 or share <= -0.03; else stage 2 =
# groups 2,3,4 (90 more). v93 restored after. Quota for both stages is reserved before the upload.
cd "$(dirname "$0")/.." || exit 1
C=.venv/bin/cambc
N=$1; NOTE=$2; SRC=$3; shift 3
LOG=~/tzunami_data/scrims/ab_tz$N.log
python3 -I tools/variant.py $SRC _tz$N "$@" >/dev/null || exit 1
sed -i '' "s/#define TZ_STAMP \"[^\"]*\"/#define TZ_STAMP \"tz-$N\"/" bots/_tz$N/src/common.h
ver() { for i in $(seq 1 20); do out=$($C submissions list --json 2>/dev/null | python3 -I -c "import json,sys; d=json.load(sys.stdin); print(d['submissions'][0]['version'], d['submissions'][0]['status'])" 2>/dev/null) && [[ -n $out ]] && { echo $out; return; }; sleep 5; done; }
free() { $C match-groups quota --json 2>/dev/null | python3 -I -c "import json,sys; q=json.load(sys.stdin)['quota']; print(q['limit']-q['used'])" 2>/dev/null || echo 0; }
act() { for i in $(seq 1 40); do $C submissions activate $1 >/dev/null 2>&1 && return 0; sleep 10; done; return 1; }
{
until [[ $(free) -ge 31 ]]; do sleep 60; done
read V0 S0 <<< "$(ver)"
$C submit _tz$N --note "tz-$N: ${NOTE[1,70]}" | tail -1
read V S <<< "$(ver)"
[[ $V == $V0 ]] && { echo "upload failed"; zsh tools/restore93.sh; exit 1; }
for i in $(seq 1 240); do read V S <<< "$(ver)"; [[ $S != queued && $S != compiling && $S != building ]] && break; sleep 15; done
echo "v$V $S $(date -u +%H:%M)"
if [[ $S == active || $S == inactive || $S == ready ]]; then
  act $V && echo "pinned v$V"
  python3 -I tools/scrim.py run tz${N}_big --pair-with big32 --only-groups 0,1
  G=$(python3 -I tools/scrim.py gate tz66_big tz${N}_big)
  echo "stage 1 v tz66_big: $G"
  W=$(echo $G | sed -E 's/.*win ([-+0-9.]+).*/\1/'); SH=$(echo $G | sed -E 's/.*share ([-+0-9.]+).*/\1/')
  if python3 -I -c "import sys; sys.exit(0 if ($W <= -0.05 or $SH <= -0.03) else 1)"; then
    echo "STOPPED after 60"
  else
    act $V
    python3 -I tools/scrim.py run tz${N}_big --pair-with big32 --only-groups 2,3,4
  fi
fi
zsh tools/restore93.sh
} > $LOG 2>&1
rm -rf bots/_tz$N
{ grep -E "LIVE|RESTORE|^v[0-9]|stage 1|STOPPED" $LOG; python3 -I tools/scrim.py report big32 tz${N}_big; python3 -I tools/scrim.py metrics big32 tz${N}_big 2>&1 | tail -13; python3 -I tools/scrim.py metrics tz66_big tz${N}_big 2>&1 | tail -13; } > ~/tzunami_data/scrims/res_tz$N.txt
cat ~/tzunami_data/scrims/res_tz$N.txt
