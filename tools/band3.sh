#!/bin/zsh
# band3.sh N "note" SRC BASE [k=v ...] (10 Nov): variant of SRC stamped tz-N, uploaded, paired game for game with BASE
# (any base label: n47 sets or a map-class set). Stage 1 = base groups 0,1; STOP unless paired share > 0 (and wins > -0.05);
# stage 2 = the base's other groups. The live bot is restored after (tools/restore93.sh).
cd "$(dirname "$0")/.." || exit 1
C=.venv/bin/cambc
N=$1; NOTE=$2; SRC=$3; BASE=$4; shift 4
S=~/tzunami_data/scrims; LOG=$S/ab_tz$N.log
python3 -I tools/variant.py $SRC _tz$N "$@" >/dev/null || exit 1
sed -i '' "s/#define TZ_STAMP \"[^\"]*\"/#define TZ_STAMP \"tz-$N\"/" bots/_tz$N/src/common.h
S1=$(cat $S/$BASE.s1 2>/dev/null || echo 0,1)  # stage-1 groups of this base (10 Nov: the 13-team panel uses 0)
REST=$(python3 -I -c "import json,sys; s1={int(x) for x in '$S1'.split(',')}; print(','.join(str(g) for g in sorted({json.loads(l)['group'] for l in open('$S/$BASE.jsonl')}) if g not in s1))")
ver() { for i in $(seq 1 20); do out=$($C submissions list --json 2>/dev/null | python3 -I -c "import json,sys; d=json.load(sys.stdin); print(d['submissions'][0]['version'], d['submissions'][0]['status'])" 2>/dev/null) && [[ -n $out ]] && { echo $out; return; }; sleep 5; done; }
free() { $C match-groups quota --json 2>/dev/null | python3 -I -c "import json,sys; q=json.load(sys.stdin)['quota']; print(q['limit']-q['used'])" 2>/dev/null || echo 0; }
act() { for i in $(seq 1 40); do $C submissions activate $1 >/dev/null 2>&1 && return 0; sleep 10; done; return 1; }
{
NEED=$(python3 -I -c "import json; g={(json.loads(l)['opp'],json.loads(l)['group']) for l in open('$S/$BASE.jsonl')}; print(len(g)+3)")  # all of this base's groups + restore (10 Nov)
until [[ $(free) -ge $NEED ]]; do sleep 60; done
read V0 S0 <<< "$(ver)"
$C submit _tz$N --note "tz-$N: ${NOTE[1,70]}" | tail -1
read V ST <<< "$(ver)"
[[ $V == $V0 ]] && { echo "upload failed"; zsh tools/restore93.sh; exit 1; }
for i in $(seq 1 240); do read V ST <<< "$(ver)"; [[ $ST != queued && $ST != compiling && $ST != building ]] && break; sleep 15; done
echo "v$V $ST $(date -u +%H:%M)"
if [[ $ST == active || $ST == inactive || $ST == ready ]]; then
  act $V && echo "pinned v$V"
  python3 -I tools/scrim.py run tz${N}_big --pair-with $BASE --only-groups $S1
  G=$(python3 -I tools/scrim.py gate $BASE tz${N}_big)
  echo "stage 1 v $BASE: $G"
  W=$(echo $G | sed -E 's/.*win ([-+0-9.]+).*/\1/'); SH=$(echo $G | sed -E 's/.*share ([-+0-9.]+).*/\1/')
  if python3 -I -c "import sys; sys.exit(0 if ($W <= -0.05 or $SH <= 0.0) else 1)"; then
    echo "STOPPED after stage 1"
  elif [[ -n $REST ]]; then
    act $V
    python3 -I tools/scrim.py run tz${N}_big --pair-with $BASE --only-groups $REST
  fi
fi
# 10 Nov: no restore when the next queue line is another band stage (it replaces the live build anyway; saves quota)
NEXTQ=$(head -1 $S/queue_10nov.txt 2>/dev/null)
if [[ $NEXTQ == [0-9]* ]]; then echo "NO RESTORE: next stage queued ($NEXTQ[1,12])"; else zsh tools/restore93.sh; fi
} > $LOG 2>&1
rm -rf bots/_tz$N
{ grep -E "LIVE|RESTORE|^v[0-9]|stage 1|STOPPED|upload failed" $LOG; python3 -I tools/scrim.py report $BASE tz${N}_big; python3 -I tools/scrim.py metrics $BASE tz${N}_big 2>&1 | tail -13; } > $S/res_tz$N.txt
cat $S/res_tz$N.txt
