#!/bin/bash
# flash.sh <scratch> <label>: 8 frames, a contact image and a change score. Touches no controls.
S="$1"; L="$2"; . "$S/scripts/live_tool.sh"; D="$S/ui/t/$L"; rm -rf "$D"; mkdir -p "$D"
for i in 1 2 3 4 5 6 7 8; do a exec-out screencap -p > "$D/$i.png"; done
for i in 1 2 3 4 5 6 7 8; do sips -Z 320 -s format png "$D/$i.png" --out "$D/s$i.png" >/dev/null 2>&1; done
python3 -I "$S/engine/flash_metric.py" "$D"/s[1-8].png
sips -Z 700 "$D/1.png" --out "$D/view1.png" >/dev/null 2>&1; sips -Z 700 "$D/5.png" --out "$D/view5.png" >/dev/null 2>&1
