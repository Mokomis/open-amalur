#!/bin/bash
# measure.sh apk label "profile skip scale" ...  Launches Gorhart on the tablet with each setting and prints PROFILE lines.
S="$(dirname "$0")/.."; SER=$(/opt/homebrew/bin/adb devices | awk '$2=="device"{print $1}' | head -1); a(){ /opt/homebrew/bin/adb -s "$SER" "$@"; }; slp(){ python3 -I -c "import time,sys;time.sleep(float(sys.argv[1]))" "$1"; }; P=org.opemamalur.scene
apk="$1"; tag="$2"; shift 2; a install -r "$apk" | tail -1; a shell input keyevent KEYCODE_WAKEUP; slp .5; a shell wm dismiss-keyguard; a shell setprop debug.opem.world town
for cfg in "$@"; do set -- $cfg; a shell setprop debug.opem.profile $1; a shell setprop debug.opem.skip $2; a shell setprop debug.opem.scale $3; a logcat -c; a shell am force-stop $P; a shell monkey -p $P -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
 for w in $(seq 1 60); do slp 2; a logcat -d -s OpemAmalurScene | grep -q 'PROFILE interval' && break; done; slp 9
 echo "== $tag profile=$1 skip=$2 scale=$3"; a logcat -d -s OpemAmalurScene | grep -E 'PROFILE|World switched|Profile on| E OpemAmalur' | sed -E 's/^.*OpemAmalurScene: //' | tail -5 | cut -c1-170
a exec-out screencap -p > "$S/ui/t/stress-$tag-$1-$3.png"; a shell dumpsys meminfo $P 2>/dev/null | grep -E 'TOTAL PSS|Graphics:|Native Heap:' | head -3 | cut -c1-70; a shell dumpsys battery | grep -m1 temperature; done
a shell setprop debug.opem.profile 0; a shell setprop debug.opem.skip 0; a shell setprop debug.opem.scale 100; a shell setprop debug.opem.world off; a shell am force-stop $P
