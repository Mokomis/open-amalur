#!/bin/bash
S="$1"; . "$S/scripts/live_tool.sh"
SCALE=100
a shell setprop debug.opem.heading 0
a shell setprop debug.opem.fight 300
phase(){ # name secs profile
  name=$1; secs=$2; prof=$3; go $prof 15 60 1 $4 1000 400; echo "== $name start $(date +%T) batt=$(a shell dumpsys battery | awk '/temperature/{print $2/10}')"
  t=0; : > "$S/ui/t/$name.log"; : > "$S/ui/t/$name.detail"
  while [ $t -lt $secs ]; do slp 15; t=$((t+15)); a shell input keyevent KEYCODE_WAKEUP; a shell input tap 1260 300
    a logcat -d -s OpemAmalurScene > "$S/ui/t/$name.raw"; grep -E 'HITCH|ACTORS|TOUR|STREAM cells|collision swap|No navigation' "$S/ui/t/$name.raw" | sed -E 's/^.*OpemAmalurScene: //' >> "$S/ui/t/$name.detail"; grep -E 'PROFILE interval' "$S/ui/t/$name.raw" | sed -E 's/^.*PROFILE //' > "$S/ui/t/$name.cur"
    a logcat -c
    cat "$S/ui/t/$name.cur" >> "$S/ui/t/$name.log"
    if [ $((t%60)) = 0 ]; then echo "$name t=$t batt=$(a shell dumpsys battery | awk '/temperature/{print $2/10}') thermal=$(a shell dumpsys thermalservice | awk -F': ' '/Thermal Status/{print $2;exit}') last: $(tail -1 "$S/ui/t/$name.cur" | cut -c1-110) | $(mem)"; fi
  done
  grab "$name"
}
phase tour_uncapped 180 2 300
grab t3
phase tour_vsync 600 1 300
a shell setprop debug.opem.fight 0; a shell setprop debug.opem.shadow 0; a shell setprop debug.opem.crowd 1; a shell setprop debug.opem.fx 0; a shell setprop debug.opem.tour 0; a shell setprop debug.opem.profile 0; a shell setprop debug.opem.world off; a shell am force-stop $P
python3 -I - "$S" <<'PY'
import re,sys,statistics as st
S=sys.argv[1]
for n in ("tour_uncapped","tour_vsync"):
    rows=[l for l in open(f"{S}/ui/t/{n}.log")]
    f=lambda k:[float(m.group(1)) for l in rows for m in [re.search(k+r"=([\d.]+)",l)] if m]
    I,W,G=f("interval_ms"),f("worst_ms"),f("gpu_ms")
    if not I: print(n,"no data");continue
    I2=sorted(I);print(n,"samples",len(I),"interval mean",round(st.mean(I),2),"p95",I2[int(.95*len(I2))],"max",I2[-1],"worst-frame max",max(W),"gpu mean",round(st.mean(G),2),"gpu max",max(G),"first-min vs last-min interval",round(st.mean(I[:8]),2),round(st.mean(I[-8:]),2))
PY
for n in tour_uncapped tour_vsync; do echo "$n hitches: $(grep -c HITCH "$S/ui/t/$n.detail")"; grep HITCH "$S/ui/t/$n.detail" | sort -t= -k2 -n | tail -6; grep ACTORS "$S/ui/t/$n.detail" | python3 -I -c "
import sys,re
R=[{k:float(v) for k,v in re.findall(r'(\\w+)=([\\d.]+)',l)} for l in sys.stdin]
if R: print('actors max near',max(r['near'] for r in R),'bodies',max(r['bodies'] for r in R),'drawn',max(r['drawn'] for r in R),'chasing',max(r['chasing'] for r in R),'models',max(r['models'] for r in R),'update_ms max',max(r['update_ms'] for r in R))"; grep 'STREAM cells' "$S/ui/t/$n.detail" | tail -1 | cut -c1-120; grep TOUR "$S/ui/t/$n.detail" | tail -1; done; echo finished
