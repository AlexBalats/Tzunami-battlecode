#!/bin/zsh
# Put the live bot (TARGET_VER, default 315 = the locked v315; 10 Nov: LIVE_VER is ignored, the runner's env carried LIVE_VER=278)
# back live and check it: activate (retried through rate limits), play one unranked game so the selection goes live,
# then read LIVE; repeat until LIVE and SELECTED are TARGET_VER (6 Nov: a restore inside ab.sh left a test build live twice).
cd "$(dirname "$0")/.."
C=.venv/bin/cambc
LV=${TARGET_VER:-315}  # the live bot to restore (10 Nov 22:05: the user locked v315 = v306 + s4x 3 flip breaker; 16:15: v306 = A5 + s2b 1 (panel +0.14 share), per the user's rule 'the best version plays ranked'; 15:10: v305 = stack A5; 14:15: v302 = stack A2, confirmed on two band sets; 10:30: v278 = teammate tz-116-fuel; 9 Nov 20:20: tz-mega = v280; 11:15: tz-116 = v265; 03:40: tz-126 = v249; 01:00: tz-117 = v242; 8 Nov 22:00: tz-107 = v238; before: tz-96 = v231, tz-66 = v208)
live() { for t in $(seq 1 12); do o=$($C submissions list --json 2>/dev/null | python3 -I -c "import json,sys; d=json.load(sys.stdin); print(d['active']['version'], d['selected']['version'])" 2>/dev/null) && [[ -n $o ]] && { echo $o; return; }; sleep 5; done; }  # retried: HTTP 429 from parallel readers (10 Nov)
for round in $(seq 1 8); do
  read L S <<< "$(live)"
  if [[ $L == $LV && $S == $LV ]]; then echo "LIVE $LV SELECTED $LV (check $round)"; exit 0; fi
  if [[ $S != $LV ]]; then
    for i in $(seq 1 40); do $C submissions activate $LV >/dev/null 2>&1 && break; sleep 10; done
  fi
  python3 -I tools/scrim.py run restore93 --groups 1 --teams "Team Kungarna=62270180-b974-4f66-9bca-3ff6a25940c3" >/dev/null 2>&1
  sleep 45
done
read L S <<< "$(live)"
echo "RESTORE FAILED: LIVE $L SELECTED $S"
exit 1
