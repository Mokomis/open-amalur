#!/bin/bash
S="$1"; . "$S/scripts/live_tool.sh"
a install -r "$S/install/opem-amalur-scene-v0.28-arm64.apk" | tail -1; a shell input keyevent KEYCODE_WAKEUP; slp 1; a shell wm dismiss-keyguard; a shell setprop debug.opem.heading 91
SCALE=100; go 2 15 0 1 0 1000 0; slp 9; SCALE=$(FULL); echo "full-res scale $SCALE"
run(){ label="$1"; shift; go "$@"; slp 16; echo "$label: $(L | tail -1 | cut -c1-100) | $(L | head -1 | sed -E 's/.*draws=([0-9]+) tris=([0-9]+) gpu_mb=([0-9]+).*/draws \1 tris \2 gpumb \3/') | $(mem)"; }
run "base no post/maps/lights" 2 0 0 1 0 1000 0; grab m0
run "+bloom" 2 1 0 1 0 1000 0
run "+ao" 2 2 0 1 0 1000 0
run "+normal spec" 2 4 0 1 0 1000 0
run "+lights" 2 8 0 1 0 1000 0
run "all lighting" 2 15 0 1 0 1000 0; grab m1
run "all + shadows" 2 15 60 1 0 1000 0; grab m2
run "all + shadows + crowd 60" 2 15 60 5 0 1000 0; grab m3
run "all + shadows + crowd 60 + fx 1500" 2 15 60 5 1500 1000 0; grab m4
for h in 1 181 271; do a shell setprop debug.opem.heading $h; run "all+shadows heading $((h-1))" 2 15 60 1 0 1000 0; grab mh$h; done
a shell setprop debug.opem.heading 0; a shell setprop debug.opem.crowd 1; a shell setprop debug.opem.fx 0; a shell setprop debug.opem.profile 0; a shell setprop debug.opem.world off; a shell am force-stop $P; echo finished
