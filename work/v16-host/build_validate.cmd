@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" > "%~dp0build-env.log" 2>&1
if errorlevel 1 exit /b %errorlevel%
cd /d "%~dp0..\.."
cmake --build work\v16-host\build-windows --target opem-interaction-test amalur-exploration-input-test opem-workbench-placement-test amalur-collision-test --parallel 8 > outputs\scene-v16\placement-build.log 2>&1
if errorlevel 1 exit /b %errorlevel%
work\v16-host\build-windows\opem-workbench-placement-test.exe outputs\scene-v10\collision-confirmed.bin no-ceiling > outputs\scene-v16\placement-test.json 2>&1
if errorlevel 1 exit /b %errorlevel%
work\v16-host\build-windows\amalur-collision-test.exe > outputs\scene-v16\collision-tests.json 2>&1
if errorlevel 1 exit /b %errorlevel%
work\v16-host\build-windows\opem-interaction-test.exe work\v08-portable\runtime outputs\scene-v16\Workbench.lua outputs\scene-v16\test-inventory.bin > outputs\scene-v16\interaction-tests.txt 2>&1
if errorlevel 1 exit /b %errorlevel%
work\v16-host\build-windows\amalur-exploration-input-test.exe > outputs\scene-v16\input-tests.txt 2>&1
if errorlevel 1 exit /b %errorlevel%
cmake --build work\v16-host\build-android-arm64 --target opem_amalur_scene --parallel 8 > outputs\scene-v16\final-build-android.log 2>&1
exit /b %errorlevel%
