#!/bin/zsh
# Platform A/B of a local bot against the UK band, paired with an earlier label; v93 is restored live afterwards.
#   tools/ab.sh BOT "STAMP: note" LABEL [BASE_LABEL=v93_band]
# Uses 25 scrim groups (24 paired + 1 to bring v93 back live). `cambc submit` makes the upload the selection.
cd "$(dirname "$0")/.."
C=.venv/bin/cambc
BOT=$1; NOTE=$2; LABEL=$3; BASE=${4:-v93_band}
# retried: one HTTP 429 here (6 Nov) read as an empty version and skipped the whole run
ver() {
  local out
  for i in $(seq 1 20); do
    out=$($C submissions list --json 2>/dev/null | python3 -I -c "import json,sys; d=json.load(sys.stdin); print(d['submissions'][0]['version'], d['submissions'][0]['status'])" 2>/dev/null) && [[ -n $out ]] && { echo $out; return; }
    sleep 5
  done
}
read V0 S0 <<< "$(ver)"
NOTE=${NOTE[1,80]}  # the platform rejects notes over 80 characters
$C submit $BOT --note "$NOTE" | tail -1
read V S <<< "$(ver)"
if [[ $V == $V0 ]]; then echo "upload failed: newest is still v$V0; nothing scrimmed"; exit 1; fi
echo "uploaded v$V ($S)"
for i in $(seq 1 240); do read V S <<< "$(ver)"; [[ $S != queued && $S != compiling && $S != building ]] && break; sleep 15; done
echo "v$V status: $S"
if [[ $S == active || $S == inactive || $S == ready ]]; then
  until [[ $($C match-groups quota --json | python3 -I -c "import json,sys; q=json.load(sys.stdin)['quota']; print(q['limit']-q['used'])") -ge 25 ]]; do sleep 60; done
  $C submissions activate $V >/dev/null && echo "pinned v$V"
  python3 -I tools/scrim.py run $LABEL --pair-with $BASE
fi
# the restore must not fail on a rate limit (it did once: v149 stayed live)
for i in $(seq 1 60); do $C submissions activate 93 >/dev/null 2>&1 && { echo "selected 93"; break; }; sleep 10; done
python3 -I tools/scrim.py run restore93 --groups 1 --teams "Team Kungarna=62270180-b974-4f66-9bca-3ff6a25940c3"
sleep 20
$C submissions list --json | python3 -I -c "import json,sys; d=json.load(sys.stdin); print('LIVE', d['active']['version'], 'SELECTED', d['selected']['version'])"
python3 -I tools/scrim.py report $BASE $LABEL
python3 -I tools/scrim.py metrics $BASE $LABEL
