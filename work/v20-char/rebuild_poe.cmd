@echo off
set PYTHONIOENCODING=utf-8:replace
cd /d "C:\Users\rwill\Documents\Opem Amalur"
set L=work\v20-char\rebuild_poe.log
set OA_ZONE=poe
set OA_REGION=454305
set OA_TERRAIN_ID=454620
set OA_TERRAIN_DIR=work\v24-zones\poe
set OA_ZONE_DIR=work\v24-zones\poe-zone
set OA_ACTORS_DIR=work\v24-zones\poe-actors
set OA_WORLD_DIR=work\v24-zones\poe-pack
echo ZONE > %L%
python work\v20-char\build_zone.py %OA_ZONE_DIR% >> %L% 2>&1 || goto bad
echo CUTOFFS >> %L%
python work\v20-char\build_cutoffs.py >> %L% 2>&1 || goto bad
echo VEGGIE >> %L%
python work\v20-char\build_veggie.py >> %L% 2>&1 || goto bad
echo PACK >> %L%
python work\v20-char\build_world_pack.py %OA_ZONE_DIR% %OA_WORLD_DIR% >> %L% 2>&1 || goto bad
echo TEXTURES >> %L%
python work\v20-char\build_textures.py %OA_ZONE_DIR% %OA_WORLD_DIR% >> %L% 2>&1 || goto bad
echo ACTORS >> %L%
python work\v20-char\build_actors.py >> %L% 2>&1 || goto bad
python work\v20-char\zone_start.py %OA_ZONE_DIR% %OA_ACTORS_DIR% "Erathell" "Plains of Erathell" >> %L% 2>&1 || goto bad
echo ROUTE >> %L%
for /f "usebackq delims=" %%s in ("%OA_ZONE_DIR%\zone_start.txt") do set OA_START=%%s
python work\v20-char\build_route.py >> %L% 2>&1 || goto bad
echo REBUILD_OK >> %L%
exit /b 0
:bad
echo REBUILD_FAILED >> %L%
exit /b 1
