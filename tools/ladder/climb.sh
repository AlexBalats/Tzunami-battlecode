#!/bin/sh
# Sequential paired judges vs cpp-p15 (tools/tune.py full), summary lines appended to LOG, then DONE.
#   sh tools/ladder/climb.sh LOG "NAME [ARGS]" ...
LOG=$1; shift; : > $LOG
for spec in "$@"; do
  echo "== $spec" >> $LOG
  python3 -I tools/tune.py full $spec --opp cpp-p15 2>&1 | grep -E "win delta|rate  |win   |tail:|open |hot  |walled|highneed|holdout" >> $LOG
done
echo DONE >> $LOG
