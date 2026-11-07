#!/bin/bash
S="$1"
while true; do r=$("$S/scripts/win.sh" <<'E2' 2>&1 | LC_ALL=C grep -v -E '^#< CLIXML|<Objs Version' | tail -1
Get-Content work\v20-char\rebuild_poe.log -ErrorAction SilentlyContinue | Select-String 'REBUILD_' | Select-Object -Last 1 | % { $_.Line }
E2
); case "$r" in *REBUILD_*) echo "$r"; break;; esac; python3 -I -c "import time;time.sleep(60)"; done
"$S/scripts/win.sh" <<'E2' 2>&1 | LC_ALL=C grep -v -E '^#< CLIXML|<Objs Version' | LC_ALL=C cut -c1-260
Get-Content work\v20-char\rebuild_poe.log -Tail 14
Get-Content work\v24-zones\poe-zone\town_start.inc -ErrorAction SilentlyContinue
(Get-ChildItem work\v24-zones\poe-pack | Measure-Object Length -Sum).Sum/1MB
E2
