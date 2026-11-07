#!/bin/bash
S="$1"; SER=$(/opt/homebrew/bin/adb devices | awk '$2=="device"{print $1}' | head -1); a(){ /opt/homebrew/bin/adb -s "$SER" "$@"; }; slp(){ python3 -I -c "import time,sys;time.sleep(float(sys.argv[1]))" "$1"; }; P=org.opemamalur.scene
a shell cat /proc/meminfo | grep -E 'MemTotal|MemAvailable' | tr -s ' '
L(){ a logcat -d -s OpemAmalurScene | grep 'PROFILE interval' | tail -1 | sed -E 's/.*PROFILE //' | cut -c1-100; }
start(){ a shell input keyevent KEYCODE_WAKEUP; a shell wm dismiss-keyguard; a shell setprop debug.opem.world town; a shell setprop debug.opem.profile $1; a shell setprop debug.opem.scale $2; a shell setprop debug.opem.crowd $3; a logcat -c; a shell am force-stop $P; a shell monkey -p $P -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1; }
mem(){ a shell dumpsys meminfo $P 2>/dev/null | grep -E 'Graphics:|TOTAL PSS' | tr -s ' ' | cut -c1-34 | tr '\n' ' '; echo; }
a install -r "$S/install/apk-r48000.apk" | tail -1
echo "== load time r48000"; start 1 100 1; slp 20; a logcat -d -s OpemAmalurScene | grep -E 'world_load' | sed -E 's/.*PROFILE //'; mem
echo "== sustained, full res, uncapped, screen kept awake"; start 2 150 1; slp 12; for m in 1 2 3 4 5 6; do for q in 1 2 3 4; do slp 15; a shell input tap 1200 400; done; echo "min $m $(L | cut -c1-60) $(a shell dumpsys battery | grep -m1 temperature | tr -d ' ')"; done
echo "swing"; for q in 1 2 3 4 5 6; do a shell input swipe 1300 300 500 300 900; done; slp 2; L; a exec-out screencap -p > "$S/ui/t/stress-swing.png"; a logcat -d -s OpemAmalurScene | grep 'PROFILE interval' | tail -8 | sed -E 's/.*worst_ms=([0-9.]+).*/\1/' | tr '\n' ' '; echo
echo "== crowd"; slp 45; a logcat -d -s OpemAmalurScene | grep -m1 -oE 'Townspeople loaded count=[0-9]+'; for n in 1 5 10 20 40; do start 2 100 $n; slp 16; echo "crowd x$n: $(L | cut -c1-70)"; done
echo "== 1024 textures"; a install -r "$S/install/apk-r12000t.apk" | tail -1; start 2 150 1; slp 22; L; mem; a logcat -d -s OpemAmalurScene | grep -E 'world_load| E OpemAmalur' | sed -E 's/.*OpemAmalurScene: //' | tail -3 | cut -c1-130
a shell setprop debug.opem.profile 0; a shell setprop debug.opem.scale 100; a shell setprop debug.opem.crowd 1; a shell setprop debug.opem.world off; a shell am force-stop $P; echo finished
