#!/bin/zsh
# stack.sh DEST SRC1 [SRC2 ...] (10 Nov): DEST = a fresh copy of bots/_m2 with each lever copy bots/SRCi 3-way merged in
# (git merge-file against the untouched base bots/_m2), file by file; new files are copied. Switch values are NOT set
# here: make the final variant with tools/variant.py DEST DEST2 k=v .... Stops on any conflict.
cd "$(dirname "$0")/.." || exit 1
DEST=$1; shift
[[ -e bots/$DEST ]] && { echo "bots/$DEST exists"; exit 1; }
python3 -I tools/variant.py _m2 $DEST >/dev/null || exit 1
for S in "$@"; do
  for f in bots/$S/src/*; do
    b=${f:t}
    if [[ ! -e bots/_m2/src/$b ]]; then
      if [[ -e bots/$DEST/src/$b ]] && ! cmp -s $f bots/$DEST/src/$b; then echo "CONFLICT new file $b from $S"; exit 1; fi
      cp $f bots/$DEST/src/$b; continue
    fi
    cmp -s $f bots/_m2/src/$b && continue
    git merge-file -p bots/$DEST/src/$b bots/_m2/src/$b $f > bots/$DEST/src/$b.m 2>/dev/null
    rc=$?
    if [[ $rc -ne 0 ]]; then echo "CONFLICT ($rc hunks) in $b merging $S"; rm bots/$DEST/src/$b.m; exit 1; fi
    mv bots/$DEST/src/$b.m bots/$DEST/src/$b
    echo "merged $S/$b"
  done
done
wc -c bots/$DEST/src/* | tail -1
