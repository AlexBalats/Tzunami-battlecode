#!/bin/zsh
# Platform A/B with the least time live (6 Nov): our Elo drops whenever a test build is live, and ab.sh left them live
# while waiting for compile and quota (tz-19 ~27 minutes, tz-20 ~40 with a failed restore).
#   tools/ab2.sh BOT "STAMP: note" LABEL [BASE_LABEL=tz15_band]
# 1. Waits for enough scrim quota BEFORE uploading, so the scrims start as soon as the compile is done.
# 2. Stage 1: base groups 0,1 against each band team (60 paired games), then v93 straight back (restore93.sh checks
#    LIVE). `scrim.py gate` says STOP when the candidate is clearly worse (share <= -0.015 or wins <= -0.05).
# 3. Stage 2 only on CONTINUE: the build is re-activated (already compiled: no wait), groups 2,3 (60 more), restore.
# Note: activating another version cancels a queued compile, so v93 can't be pinned while the build compiles; a
# selected build only goes live with the next unranked game.
cd "$(dirname "$0")/.."
C=.venv/bin/cambc
BOT=$1; NOTE=$2; LABEL=$3; BASE=${4:-tz15_band}; ONLY1=${5:-}  # 5th arg "stage1": stop after 60 games
ver() {
  local out
  for i in $(seq 1 20); do
    out=$($C submissions list --json 2>/dev/null | python3 -I -c "import json,sys; d=json.load(sys.stdin); print(d['submissions'][0]['version'], d['submissions'][0]['status'])" 2>/dev/null) && [[ -n $out ]] && { echo $out; return; }
    sleep 5
  done
}
free() { $C match-groups quota --json 2>/dev/null | python3 -I -c "import json,sys; q=json.load(sys.stdin)['quota']; print(q['limit']-q['used'])" 2>/dev/null || echo 0; }
wait_quota() { until [[ $(free) -ge $1 ]]; do sleep 60; done; }
activate() { for i in $(seq 1 40); do $C submissions activate $1 >/dev/null 2>&1 && return 0; sleep 10; done; return 1; }

wait_quota 15
read V0 S0 <<< "$(ver)"
NOTE=${NOTE[1,80]}
$C submit $BOT --note "$NOTE" | tail -1
read V S <<< "$(ver)"
if [[ $V == $V0 ]]; then echo "upload failed: newest is still v$V0"; zsh tools/restore93.sh; exit 1; fi
echo "uploaded v$V ($S) $(date -u +%H:%M)"
for i in $(seq 1 240); do read V S <<< "$(ver)"; [[ $S != queued && $S != compiling && $S != building ]] && break; sleep 15; done
echo "v$V status: $S $(date -u +%H:%M)"
if [[ $S == active || $S == inactive || $S == ready ]]; then
  wait_quota 13
  activate $V && echo "pinned v$V $(date -u +%H:%M)"
  python3 -I tools/scrim.py run $LABEL --pair-with $BASE --only-groups 0,1
  zsh tools/restore93.sh; echo "restored $(date -u +%H:%M)"
  G=$(python3 -I tools/scrim.py gate $BASE $LABEL)
  echo "stage 1: $G"
  if [[ $G == CONTINUE* && $ONLY1 != stage1 ]]; then
    wait_quota 13
    activate $V && echo "pinned v$V again $(date -u +%H:%M)"
    python3 -I tools/scrim.py run $LABEL --pair-with $BASE --only-groups 2,3
    zsh tools/restore93.sh; echo "restored $(date -u +%H:%M)"
  fi
else
  zsh tools/restore93.sh
fi
python3 -I tools/scrim.py report $BASE $LABEL
python3 -I tools/scrim.py metrics $BASE $LABEL
