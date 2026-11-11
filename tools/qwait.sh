#!/bin/zsh
# qwait.sh N : wait until at least N unranked groups of quota are free (rolling hour).
cd "$(dirname "$0")/.." || exit 1
until [[ $(.venv/bin/cambc match-groups quota --json 2>/dev/null | python3 -I -c "import json,sys; q=json.load(sys.stdin)['quota']; print(q['limit']-q['used'])" 2>/dev/null || echo 0) -ge $1 ]]; do sleep 60; done
