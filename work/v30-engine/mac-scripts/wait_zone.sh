#!/bin/bash
S="$1"; for i in $(seq 1 110); do python3 -I -c "import time;time.sleep(30)"; o=$("$S/scripts/win.sh" <<'W' 2>&1 | LC_ALL=C grep -v -E '^#< CLIXML|<Objs Version' | LC_ALL=C cut -c1-300
Get-Content work\v22-stress\zone-build.log -Tail 2; Get-Content work\v22-stress\zone-build.err -Tail 2 -ErrorAction SilentlyContinue; "running=$((Get-CimInstance Win32_Process -Filter "CommandLine like '%build_zone%' and Name='python.exe'" | Measure-Object).Count)"
W
); if echo "$o" | grep -q 'running=0'; then echo "$o"; exit 0; fi; done; echo "$o"
