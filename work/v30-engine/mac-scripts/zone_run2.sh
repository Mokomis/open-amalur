#!/bin/bash
S="$1"; SER=$(/opt/homebrew/bin/adb devices | awk '$2=="device"{print $1}' | head -1); a(){ /opt/homebrew/bin/adb -s "$SER" "$@"; }; slp(){ python3 -I -c "import time,sys;time.sleep(float(sys.argv[1]))" "$1"; }; P=org.opemamalur.scene
grab(){ a exec-out screencap -p > "$S/ui/t/$1.png"; W=$(sips -g pixelWidth "$S/ui/t/$1.png" | tail -1 | awk '{print $2}'); if [ "$W" = 1680 ]; then python3 -I "$S/scripts/pngcrop.py" "$S/ui/t/$1.png" "$S/ui/t/$1-s.png" 1680 1120 840; else sips -Z 840 "$S/ui/t/$1.png" --out "$S/ui/t/$1-s.png" >/dev/null 2>&1; fi; }
set_(){ a shell setprop debug.opem.$1 $2; }
mem(){ a shell dumpsys meminfo $P 2>/dev/null | grep -E 'TOTAL PSS' | tr -s ' ' | cut -d' ' -f4; }
run(){ tag=$1; shift; a shell input keyevent KEYCODE_WAKEUP; slp .5; a shell wm dismiss-keyguard; set_ world town; set_ profile $1; set_ scale $2; set_ shadow 60; set_ walk 0; set_ tour $3; set_ tourr $4; set_ far $5; dur=$6; a logcat -c; a shell am force-stop $P; a shell monkey -p $P -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1; a logcat -s OpemAmalurScene > "$S/ui/t/log-$tag.txt" & LP=$!; MEM=""; for t in $(seq 1 $((dur/15))); do slp 15; a shell input tap 1200 400; [ $((t%4)) = 0 ] && MEM="$MEM $(mem)"; [ $t = $((dur/30)) ] && grab $tag; done; kill $LP; echo "== $tag: mem KB by minute:$MEM temp $(a shell dumpsys battery | grep -m1 temperature | tr -d ' ')";
 python3 -I - "$S/ui/t/log-$tag.txt" <<'PY'
import re,sys
t=open(sys.argv[1],errors='replace').read()
iv=[float(x) for x in re.findall(r'PROFILE interval_ms=([\d.]+)',t)];w=[float(x) for x in re.findall(r'worst_ms=([\d.]+)',t)];g=[float(x) for x in re.findall(r' gpu_ms=([\d.]+)',t)]
d=[int(x) for x in re.findall(r'draws=(\d+)',t)];tr=[int(x) for x in re.findall(r'tris=(\d+)',t)];gm=[float(x) for x in re.findall(r'gpu_mb=([\d.]+)',t)];cm=[float(x) for x in re.findall(r'cpu_mb=([\d.]+)',t)];q=[int(x) for x in re.findall(r'queued=(\d+)',t)];u=[float(x) for x in re.findall(r'update_worst_ms=([\d.]+)',t)]
sw=[float(x) for x in re.findall(r'collision swap.*ms=([\d.]+)',t)]
print(' windows',len(iv),'interval mean %.2f max %.2f | worst frame sorted'%(sum(iv)/max(1,len(iv)),max(iv or [0])),sorted(w)[-5:])
print(' gpu mean %.2f max %.2f | draws max %d tris max %d gpu_mb max %.0f cpu_mb max %.0f queue max %d upload worst ms %.1f'%(sum(g)/max(1,len(g)),max(g or [0]),max(d or [0]),max(tr or [0]),max(gm or [0]),max(cm or [0]),max(q or [0]),max(u or [0])))
print(' swaps',len(sw),'max ms',max(sw or [0]),'nocell',t.count('no collision cells'),'errors',len([l for l in t.splitlines() if ' E OpemAmalur' in l and '0x502' not in l and 'no collision' not in l]),'fatal',t.count('FATAL'))
print(' over 33ms windows',sum(1 for x in w if x>33),'of',len(w))
PY
 }
a install -r "$S/install/apk-zone.apk" | tail -1
run sweep 2 150 3000 600 2200 180
run tour30 1 100 3000 600 1000 300
run tour60 1 100 6000 450 1000 120
a shell setprop debug.opem.tour 0; set_ profile 0; set_ scale 100; set_ shadow 0; set_ far 640; set_ world off; a shell am force-stop $P; echo finished
