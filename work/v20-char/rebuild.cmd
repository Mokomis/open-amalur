@echo off
set PYTHONIOENCODING=utf-8:replace
cd /d "C:\Users\rwill\Documents\Opem Amalur"
del work\v22-stress\zone-dal\terrain_H.npy work\v22-stress\zone-dal\terrain_H.json
echo ZONE > work\v20-char\rebuild.log
python work\v20-char\build_zone.py work\v22-stress\zone-dal >> work\v20-char\rebuild.log 2>&1 || goto bad
echo CUTOFFS >> work\v20-char\rebuild.log
python work\v20-char\build_cutoffs.py >> work\v20-char\rebuild.log 2>&1 || goto bad
echo VEGGIE >> work\v20-char\rebuild.log
python work\v20-char\build_veggie.py >> work\v20-char\rebuild.log 2>&1 || goto bad
echo PACK >> work\v20-char\rebuild.log
del /q work\v22-stress\live-pack\*.bin
python work\v20-char\build_world_pack.py work\v22-stress\zone-dal work\v22-stress\live-pack >> work\v20-char\rebuild.log 2>&1 || goto bad
echo TEXTURES >> work\v20-char\rebuild.log
python work\v20-char\build_textures.py work\v22-stress\zone-dal work\v22-stress\live-pack >> work\v20-char\rebuild.log 2>&1 || goto bad
echo CHECK >> work\v20-char\rebuild.log
python work\v20-char\build_route.py >> work\v20-char\rebuild.log 2>&1
python work\v20-char\water_spots.py >> work\v20-char\rebuild.log 2>&1
python work\v20-char\route_probe.py >> work\v20-char\rebuild.log 2>&1
python work\v20-char\hole_map.py >> work\v20-char\rebuild.log 2>&1
echo REBUILD_OK >> work\v20-char\rebuild.log
exit /b 0
:bad
echo REBUILD_FAILED >> work\v20-char\rebuild.log