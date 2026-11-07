#!/bin/bash
S="$1"; for i in $(seq 1 110); do python3 -I -c "import time;time.sleep(30)"; o=$("$S/scripts/win.sh" <<'W' 2>&1 | LC_ALL=C grep -v -E '^#< CLIXML|<Objs Version' | LC_ALL=C cut -c1-260
if(Test-Path work\v22-stress\live-done.txt){"DONE"}; foreach($n in 1,2,3,4){ if(Test-Path "work\v22-stress\live$n.log"){ "--$n"; Get-Content "work\v22-stress\live$n.log" -Tail 2 } }
W
); if echo "$o" | grep -q DONE; then echo "$o"; exit 0; fi; done; echo "$o"
