#!/bin/bash
S="$1"; SER=$(/opt/homebrew/bin/adb devices | awk '$2=="device"{print $1}' | head -1); a(){ /opt/homebrew/bin/adb -s "$SER" "$@"; }; slp(){ python3 -I -c "import time,sys;time.sleep(float(sys.argv[1]))" "$1"; }; P=org.opemamalur.scene
grab(){ a exec-out screencap -p > "$S/ui/t/$1.png"; W=$(sips -g pixelWidth "$S/ui/t/$1.png" | tail -1 | awk '{print $2}'); if [ "$W" = 1680 ]; then python3 -I "$S/scripts/pngcrop.py" "$S/ui/t/$1.png" "$S/ui/t/$1-s.png" 1680 1120 840; else sips -Z 840 "$S/ui/t/$1.png" --out "$S/ui/t/$1-s.png" >/dev/null 2>&1; fi; }
set_(){ a shell setprop debug.opem.$1 $2; }
start(){ a shell input keyevent KEYCODE_WAKEUP; a shell wm dismiss-keyguard; set_ world town; set_ profile $1; set_ scale $2; set_ shadow $3; set_ walk $4; set_ tour $5; set_ tourr $6; set_ far $7; a logcat -c; a shell am force-stop $P; a shell monkey -p $P -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1; }
L(){ a logcat -d -s OpemAmalurScene | grep -E 'PROFILE interval|STREAM cells' | tail -2 | sed -E 's/^.*OpemAmalurScene: //;s/PROFILE //;s/gpu_samples.*//' | cut -c1-130; }
mem(){ a shell dumpsys meminfo $P 2>/dev/null | grep -E 'TOTAL PSS' | tr -s ' ' | cut -c1-24; }
W(){ a logcat -d -s OpemAmalurScene | grep 'PROFILE interval' | sed -E 's/.*worst_ms=([0-9.]+).*/\1/' | sort -n | tail -4 | tr '\n' ' '; echo " <- worst frames"; }
E(){ a logcat -d -s OpemAmalurScene | grep -E 'FATAL| E OpemAmalur' | grep -v 0x502 | sed -E 's/^.*OpemAmalurScene: //' | cut -c1-110 | sort | uniq -c | sort -rn | head -4; }
a install -r "$S/install/apk-zone.apk" | tail -1
a shell dumpsys package $P | grep -m1 versionName | tr -d ' '
for f in 640 1000 2200; do echo "== full zone, standing, view $f m, shadows, uncapped full res"; start 2 150 60 0 0 600 $f; slp 22; a logcat -d -s OpemAmalurScene | grep -E 'Stream opened|world_load' | sed -E 's/^.*OpemAmalurScene: //' | tail -2 | cut -c1-90; L; mem; grab z-stand-$f; E; done
echo "== tour 30 m/s, radius 600 m, view 1000 m, shadows, 60 Hz, 5 min, memory watch"; start 1 100 60 0 3000 600 1000; for m in 1 2 3 4 5; do for q in 1 2 3 4; do slp 15; a shell input keyevent KEYCODE_WAKEUP; done; echo "min $m $(L | tail -1 | cut -c1-44) $(mem) $(a shell dumpsys battery | grep -m1 temperature | tr -d ' ')"; done; L | head -1; W; grab z-tour; E; echo "swaps=$(a logcat -d -s OpemAmalurScene | grep -c 'collision swap') nocell=$(a logcat -d -s OpemAmalurScene | grep -c 'no collision cells')"
a shell setprop debug.opem.tour 0
echo "finished"
