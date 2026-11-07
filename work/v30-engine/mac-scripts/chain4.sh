#!/bin/bash
S="$1"
"$S/scripts/win.sh" <<'E2' 2>&1 | LC_ALL=C grep -v -E '^#< CLIXML|<Objs Version' | LC_ALL=C cut -c1-200
Remove-Item work\v20-char\rebuild.log -ErrorAction SilentlyContinue
$root=(Resolve-Path .).Path
(Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine="cmd /c `"$root\work\v20-char\rebuild.cmd`""}).ReturnValue
E2
while true; do r=$("$S/scripts/win.sh" <<'E2' 2>&1 | LC_ALL=C grep -v -E '^#< CLIXML|<Objs Version' | tail -1
Get-Content work\v20-char\rebuild.log -ErrorAction SilentlyContinue | Select-String 'REBUILD_' | Select-Object -Last 1 | % { $_.Line }
E2
); case "$r" in *REBUILD_*) echo "$r"; break;; esac; python3 -I -c "import time;time.sleep(30)"; done
"$S/scripts/win.sh" <<'E2' 2>&1 | LC_ALL=C grep -v -E '^#< CLIXML|<Objs Version' | LC_ALL=C cut -c1-200
cmd /c work\v19-host\build_validate.cmd 2>&1 | Select-Object -Last 1 | % { "$_" }
"build exit $LASTEXITCODE"
Get-Content outputs\scene-v19\build-android.log | Select-String 'error:|FAILED' | Select-Object -First 8 | % { "$_" }
python work\v19-host\package_android.py 2>&1 | Select-Object -Last 1 | % { "$_" }
E2
scp -q -o HostName=192.168.68.59 -o HostKeyAlias=192.168.68.52 'open-rune-windows:Documents/Opem Amalur/outputs/scene-v19/opem-amalur-scene-v0.33-arm64.apk' "$S/install/"
. "$S/scripts/live_tool.sh"; a install -r "$S/install/opem-amalur-scene-v0.33-arm64.apk" | tail -1
bash "$S/scripts/lookat.sh" "$S" fall1 "-13121 -9104 4500" 1
bash "$S/scripts/lookat.sh" "$S" riv3 "1560 11326 6200" 91
bash "$S/scripts/lookat.sh" "$S" fall3 "-13121 -9104 4500" 91
bash "$S/scripts/lookat.sh" "$S" door "1575 -62759 5200" 91
bash "$S/scripts/lookat.sh" "$S" north "20000 30000 8000" 1
