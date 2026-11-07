@echo off
set "OA_CAPTURE_ROOT=C:\Users\rwill\Documents\Opem Amalur\work\v31-native-slice"
set "VK_LAYER_PATH=%OA_CAPTURE_ROOT%\capture-tools\build-x86\layer"
set "VK_INSTANCE_LAYERS=VK_LAYER_LUNARG_gfxreconstruct"
set "GFXRECON_CAPTURE_FILE=%OA_CAPTURE_ROOT%\captures\amalur.gfxr"
set "GFXRECON_CAPTURE_TRIGGER=F10"
set "GFXRECON_CAPTURE_TRIGGER_FRAMES=1"
set "GFXRECON_MEMORY_TRACKING_MODE=unassisted"
set "GFXRECON_LOG_FILE=%OA_CAPTURE_ROOT%\captures\capture.log"
set "GFXRECON_LOG_FILE_FLUSH_AFTER_WRITE=true"
set "SteamAppId=1041720"
set "SteamGameId=1041720"
cd /d "%OA_CAPTURE_ROOT%\run-capture"
start "" koa.exe
