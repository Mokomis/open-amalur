#!/bin/bash
# video.sh <scratch> <name> <shots> <crop w:h:x:y> <tile>: screenshots in succession (run the game with debug.opem.slow) into a sheet at ui/t/<name>.png
S="$1"; . "$S/scripts/live_tool.sh"
D="$S/ui/t/$2-frames"; rm -rf "$D"; mkdir -p "$D"
a shell input keyevent KEYCODE_WAKEUP
i=0; while [ $i -lt "$3" ]; do a shell input keyevent KEYCODE_WAKEUP; a exec-out screencap -p > "$D/$(printf %03d $i).png"; i=$((i+1)); done
/opt/homebrew/bin/ffmpeg -y -loglevel error -framerate 10 -i "$D/%03d.png" -vf "crop=$4,scale=300:-1,tile=$5" -frames:v 1 "$S/ui/t/$2.png"; ls "$S/ui/t/$2.png" >/dev/null && echo "sheet $2 ok"
