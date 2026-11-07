#!/bin/bash
# capture_motion.sh <scratch> <name> <tour> <fight> <wait seconds>: starts the game in slow motion and writes a frame sheet.
S="$1"; . "$S/scripts/live_tool.sh"; SCALE=100
a shell setprop debug.opem.walk 0; a shell setprop debug.opem.heading 0; a shell setprop debug.opem.slow 100
go 2 15 60 1 0 1000 "$3"; a shell setprop debug.opem.fight "$4"; a shell am force-stop $P; a shell monkey -p $P -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
t=0; while [ $t -lt "$5" ]; do slp 8; t=$((t+8)); a shell input keyevent KEYCODE_WAKEUP; a shell input tap 1260 200; done
a shell setprop debug.opem.slow 20; a shell setprop debug.opem.fight "$4"; a shell am force-stop $P; a shell monkey -p $P -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1; slp 5; a shell input keyevent KEYCODE_WAKEUP; a shell wm dismiss-keyguard; slp 3
bash "$S/scripts/video.sh" "$S" "$2" 12 760:760:880:380 6x2
a shell setprop debug.opem.fight 0; a shell setprop debug.opem.slow 0; a shell setprop debug.opem.tour 0; a shell setprop debug.opem.profile 0; a shell setprop debug.opem.world off; a shell setprop debug.opem.shadow 0; a shell am force-stop $P
