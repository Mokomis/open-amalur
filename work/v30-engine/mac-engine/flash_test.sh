#!/bin/bash
# flash_test.sh <scratch> <label> [option text, %s for space] [menu_open]: exits the game, sets launch options, plays, scores the flashing.
# Stops without further taps if the game did not exit.
S="$1"; L="$2"; O="$3"; OPEN="$4"; . "$S/scripts/live_tool.sh"; D="$S/ui/t"; K=$(printf '67 %.0s' $(seq 1 70))
shot(){ a exec-out screencap -p > "$D/$1.png"; sips -Z 700 "$D/$1.png" --out "$D/$1-s.png" >/dev/null 2>&1; }
running(){ a shell 'ps -A -o ARGS' | grep -E '^S:.*koa\.exe' | grep -v -c grep; }
if [ -z "$OPEN" ]; then a shell input tap 90 1587; slp 3; a shell input tap 1187 1552; slp 8; fi
a shell input tap 88 1587; slp 2; a shell input tap 730 1300; slp 5; shot "$L-exit"; a shell input tap 870 890; slp 15
R=$(running); echo "koa after exit: $R"; if [ "$R" != 0 ]; then echo "STOPPED: game still running"; shot "$L-stuck"; exit 3; fi
a shell input tap 2392 800; slp 2; a shell input tap 1050 965; slp 3; a shell input swipe 1500 1350 1500 500 600; slp 2
a shell input tap 1500 1267; slp 2; a shell input keyevent 123; slp 0.3; a shell input keyevent $K; slp 0.5
[ -n "$O" ] && a shell "input text '$O'"
slp 2; shot "$L-field"; a shell input tap 2407 1618; slp 2; a shell input tap 2410 1628; slp 3; a shell input tap 346 803; slp 75
a shell 'ps -A -o ETIME,RSS,PCPU,ARGS' | grep -E 'steam-launch-wrapper|^ *[0-9:]+ +[0-9]+ +[0-9.]+ S:.*koa' | grep -v -E 'grep|reaper' | cut -c1-110
"$S/engine/flash.sh" "$S" "$L" 2>&1 | tail -3
