#!/bin/bash
# Build and install the Plains of Erathell test package. Dalentarth's generated files go back afterwards.
S="$1"
"$S/scripts/win.sh" <<'E2' 2>&1 | LC_ALL=C grep -v -E '^#< CLIXML|<Objs Version' | LC_ALL=C cut -c1-200
Copy-Item work\v24-zones\poe-zone\town_live.inc work\v19-host\town_live.inc -Force; (Get-Item work\v19-host\town_live.inc).LastWriteTime=Get-Date
Copy-Item work\v24-zones\poe-zone\town_start.inc work\v19-host\town_start.inc -Force; (Get-Item work\v19-host\town_start.inc).LastWriteTime=Get-Date
$env:OA_FX_FILE=(Resolve-Path work\v25-fx\poe\fx.bin).Path;$env:OA_WORLD_DIR=(Resolve-Path work\v24-zones\poe-pack).Path;$env:OA_ACTORS_DIR=(Resolve-Path work\v24-zones\poe-actors).Path
cmd /c "work\v19-host\build_validate.cmd > work\v19-host\bv.txt 2>&1"; "build exit $LASTEXITCODE"
Get-Content outputs\scene-v19\build-android.log | Select-String 'error:|FAILED' | Select-Object -First 6 | % { "$_" }
cmd /c "python work\v19-host\package_android.py > work\v19-host\pk.txt 2>&1"; Get-Content work\v19-host\pk.txt -Tail 1
Copy-Item outputs\scene-v19\opem-amalur-scene-v0.33-arm64.apk outputs\scene-v19\opem-amalur-poe-test.apk -Force
(Get-Item outputs\scene-v19\opem-amalur-poe-test.apk).Length/1MB
Copy-Item work\v22-stress\zone-dal\town_live.inc work\v19-host\town_live.inc -Force; (Get-Item work\v19-host\town_live.inc).LastWriteTime=Get-Date
Copy-Item work\v22-stress\zone-dal\town_start.inc work\v19-host\town_start.inc -Force; (Get-Item work\v19-host\town_start.inc).LastWriteTime=Get-Date
E2
scp -q -o HostName=192.168.68.59 -o HostKeyAlias=192.168.68.52 'open-rune-windows:Documents/Opem Amalur/outputs/scene-v19/opem-amalur-poe-test.apk' "$S/install/"
. "$S/scripts/live_tool.sh"; a install -r "$S/install/opem-amalur-poe-test.apk" 2>&1 | tail -1
