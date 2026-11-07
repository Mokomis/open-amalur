#!/bin/bash
S="$1"
while true; do r=$("$S/scripts/win.sh" <<'E2' 2>&1 | LC_ALL=C grep -v -E '^#< CLIXML|<Objs Version' | tail -1
Get-Content work\v20-char\rebuild_poe.log -ErrorAction SilentlyContinue | Select-String 'REBUILD_' | Select-Object -Last 1 | % { $_.Line }
E2
); case "$r" in *REBUILD_*) echo "$r"; break;; esac; python3 -I -c "import time;time.sleep(60)"; done
"$S/scripts/win.sh" <<'E2' 2>&1 | LC_ALL=C grep -v -E '^#< CLIXML|<Objs Version' | LC_ALL=C cut -c1-240
"--- dal"; Get-Content work\v20-char\rebuild.log -Tail 12
"--- poe"; Get-Content work\v20-char\rebuild_poe.log -Tail 10
E2
