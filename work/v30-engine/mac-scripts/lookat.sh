#!/bin/bash
# lookat.sh <scratch> <name> "<x y z>" <heading+1>: starts at a place, facing a heading, screenshot plus frame time.
S="$1"; . "$S/scripts/live_tool.sh"; SCALE=100
a shell setprop debug.opem.walk 0; a shell setprop debug.opem.fight 0; a shell setprop debug.opem.slow 0
go 2 15 60 1 0 1000 0; a shell setprop debug.opem.at "'$3'"; a shell setprop debug.opem.heading "$4"; a shell am force-stop $P; a shell monkey -p $P -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
slp 8; a shell input keyevent KEYCODE_WAKEUP; slp 6; grab "$2"
echo "$2: $(a logcat -d -s OpemAmalurScene | grep -E 'Moved to|Move rejected' | tail -1 | sed -E 's/^.*OpemAmalurScene: //' | cut -c1-70) | $(a logcat -d -s OpemAmalurScene | grep -E 'PROFILE interval' | tail -1 | sed -E 's/^.*PROFILE //' | cut -c1-100) | $(a logcat -d -s OpemAmalurScene | grep -E 'STREAM cells' | tail -1 | sed -E 's/^.*STREAM //' | cut -c1-60)"
a shell setprop debug.opem.at "''"; a shell setprop debug.opem.heading 0; a shell setprop debug.opem.profile 0; a shell setprop debug.opem.world off; a shell setprop debug.opem.shadow 0; a shell am force-stop $P
