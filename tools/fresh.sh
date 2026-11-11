#!/bin/zsh
# fresh.sh BASEVER BASELABEL CANDVER CANDLABEL SEED : base build on new maps (3 groups per opponent = 90 games), then the
# candidate paired on the same groups; v93 restored. Both versions already compiled (no upload).
cd "$(dirname "$0")/.." || exit 1
C=.venv/bin/cambc
BV=$1; BL=$2; CV=$3; CL=$4; SEED=$5
act() { for i in $(seq 1 40); do $C submissions activate $1 >/dev/null 2>&1 && return 0; sleep 10; done; return 1; }
free() { $C match-groups quota --json 2>/dev/null | python3 -I -c "import json,sys; q=json.load(sys.stdin)['quota']; print(q['limit']-q['used'])" 2>/dev/null || echo 0; }
{
until [[ $(free) -ge 37 ]]; do sleep 60; done
act $BV && echo "pinned $BV $(date -u +%H:%M)"
python3 -I tools/scrim.py run $BL --groups 3 --seed $SEED
act $CV && echo "pinned $CV $(date -u +%H:%M)"
python3 -I tools/scrim.py run $CL --pair-with $BL
zsh tools/restore93.sh
} > ~/tzunami_data/scrims/ab_$CL.log 2>&1
{ grep -E "LIVE|RESTORE|pinned" ~/tzunami_data/scrims/ab_$CL.log; python3 -I tools/scrim.py report $BL $CL; python3 -I tools/scrim.py metrics $BL $CL 2>&1 | tail -13; } > ~/tzunami_data/scrims/res_$CL.txt
cat ~/tzunami_data/scrims/res_$CL.txt
