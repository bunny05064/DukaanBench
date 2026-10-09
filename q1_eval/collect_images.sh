#!/bin/zsh
# Collects DukaanBench images saved by the manual kit from ~/Downloads
# (or the Desktop) and moves them into q1_eval/images/ with de-duplication.
set -u
DEST="$HOME/JoshTalks-Eval-Challenge/q1_eval/images"
SRC1="$HOME/Downloads"
SRC2="$HOME/Desktop"
mkdir -p "$DEST"
echo "watching $SRC1 and $SRC2 -> $DEST"
while true; do
  for dir in "$SRC1" "$SRC2"; do
    for f in "$dir"/P*__google__*.png(N); do
      base="${f:t}"
      target="$DEST/$base"
      if [[ -e "$target" ]]; then
        n=2
        stem="${base%.png}"
        while [[ -e "$DEST/${stem} ($n).png" ]]; do (( n++ )); done
        target="$DEST/${stem} ($n).png"
      fi
      mv -n "$f" "$target" && echo "$(date +%H:%M:%S) moved: ${target:t}"
    done
  done
  sleep 2
done
