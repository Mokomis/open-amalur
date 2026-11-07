#!/bin/bash
S="$1"; SER=$(/opt/homebrew/bin/adb devices | awk '$2=="device"{print $1}' | head -1); a(){ /opt/homebrew/bin/adb -s "$SER" "$@"; }; slp(){ python3 -I -c "import time,sys;time.sleep(float(sys.argv[1]))" "$1"; }; P=org.opemamalur.scene
L(){ a logcat -d -s OpemAmalurScene | grep 'PROFILE interval' | tail -1 | sed -E 's/.*PROFILE //' | cut -c1-105; }
start(){ a shell input keyevent KEYCODE_WAKEUP; a shell wm dismiss-keyguard; a shell setprop debug.opem.world town; a shell setprop debug.opem.profile $1; a shell setprop debug.opem.scale $2; a shell setprop debug.opem.crowd $3; a logcat -c; a shell am force-stop $P; a shell monkey -p $P -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1; }
mem(){ a shell dumpsys meminfo $P 2>/dev/null | grep -E 'Graphics:|TOTAL PSS' | tr -s ' ' | cut -c1-34 | tr '\n' ' '; echo; }
grab(){ a exec-out screencap -p > "$S/ui/t/$1.png"; W=$(sips -g pixelWidth "$S/ui/t/$1.png" | tail -1 | awk '{print $2}'); if [ "$W" = 1680 ]; then python3 -I "$S/scripts/pngcrop.py" "$S/ui/t/$1.png" "$S/ui/t/$1-s.png" 1680 1120 840; else sips -Z 840 "$S/ui/t/$1.png" --out "$S/ui/t/$1-s.png" >/dev/null 2>&1; fi; }
ready(){ a logcat -d -s OpemAmalurScene | grep -E 'World switched|collision unavailable|world_load|stopped' | sed -E 's/^.*OpemAmalurScene: //' | tail -3 | cut -c1-110 | tr '\n' ' '; echo; }
for t in r24000 r48000; do a install -r "$S/install/apk-$t.apk" | tail -1; echo "== $t"; start 2 150 1; slp 25; ready; L; mem; grab real-$t; start 1 100 1; slp 18; echo "vsync: $(L | cut -c1-60)"; done
echo "== sustained r48000 uncapped"; start 2 150 1; slp 20; for m in 1 2 3; do for q in 1 2 3 4; do slp 15; a shell input tap 1200 400; done; echo "min $m $(L | cut -c1-60) $(a shell dumpsys battery | grep -m1 temperature | tr -d ' ')"; done
echo "swing"; for q in 1 2 3 4 5 6; do a shell input swipe 1300 300 500 300 900; done; slp 2; L; grab real-swing
echo "== crowd r48000, player view"; for n in 1 5 10 20 40; do start 2 150 $n; slp 20; echo "crowd x$n ($((n*12)) people): $(L | cut -c1-70)"; done
a shell setprop debug.opem.profile 0; a shell setprop debug.opem.scale 100; a shell setprop debug.opem.crowd 1; a shell setprop debug.opem.world off; a shell am force-stop $P; echo finished
