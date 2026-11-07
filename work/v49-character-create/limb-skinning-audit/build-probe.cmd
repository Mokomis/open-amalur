@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
cd /d "C:\Users\rwill\Documents\Opem Amalur\work\v49-character-create\limb-skinning-audit"
cl /nologo /O2 /W4 /I"C:\Users\rwill\Documents\Opem Amalur\work\v19-host" skin_pose_probe.c "C:\Users\rwill\Documents\Opem Amalur\work\v19-host\oa_character.c" /Fe:skin_pose_probe.exe
if errorlevel 1 exit /b %errorlevel%
skin_pose_probe.exe "C:\Users\rwill\Documents\Opem Amalur\work\v49-character-create\packs\Almain_Male\character.bin" production-pose-rows.bin
if errorlevel 1 exit /b %errorlevel%
skin_pose_probe.exe "C:\Users\rwill\Documents\Opem Amalur\work\v49-character-create\packs\Almain_Male\character.bin" corrected-palette-pose-rows.bin almain-male-palette-corrections.oacpl
