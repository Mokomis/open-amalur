$note=@'

V0.19.0 OUTSIDE (2026-10-31): tablet 99cc517a runs versionCode 20 with Gorhart reachable through the shop door both ways. APK outputs/scene-v19/opem-amalur-scene-v0.19-arm64.apk sha256 starts dab141127d19742e. Assets work/v20-town from work/v20-char/build_town.py 6000 (60 m radius around the door, 65304 triangles, Noon lighting of region 431608, single for_terrain_grass01_d ground texture). Doors are object records int_dal_gorhart_alchemistshop_entrance and _exit; prompt radius 260 is authored. Real controller flood test work/v20-char/reach_test.c: shop door and Workbench connect both ways. Test aid: adb shell setprop debug.opem.world town opens Gorhart directly; it is now off.
MISSING OUTSIDE: alpha foliage and tree leaves (no alpha test), grass and veggie layer, terrain paint maps and road textures, sky model, fog, shadows, water, NPCs, town beyond 60 m. Material binding picks the first _d texture by name, not native slot data. Depth precision and Reset both untested in depth at the far edge. Heights above 60000 are treated as holes.
'@
Add-Content -Encoding UTF8 'work\CURRENT_STATE.txt' $note
Add-Content -Encoding UTF8 'outputs\scene-v19\PROGRESS.txt' $note
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'scene_v20_session' } | ForEach-Object { taskkill /PID $_.ProcessId /T /F | Out-Null; 'stopped ghidra worker' }
(Get-FileHash 'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe').Hash.Substring(0,12)
(Get-Process java -ErrorAction SilentlyContinue | Measure-Object).Count
