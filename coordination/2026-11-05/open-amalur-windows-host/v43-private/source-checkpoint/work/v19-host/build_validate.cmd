@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" > "%~dp0build-env.log" 2>&1
if errorlevel 1 exit /b %errorlevel%
cd /d "%~dp0..\.."
set "AMALUR_NINJA=C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe"
set "AMALUR_NDK=%~dp0..\..\tools\android\android-ndk-r30"
cmake -S work\v19-host -B work\v19-host\build-windows -G Ninja "-DCMAKE_MAKE_PROGRAM=%AMALUR_NINJA%" -DCMAKE_BUILD_TYPE=Release > outputs\scene-v19\configure-windows.log 2>&1
if errorlevel 1 exit /b %errorlevel%
cmake --build work\v19-host\build-windows --target amalur-exploration-input-test oa-character-test oa-menu-test oa-actor-ai-test oa-nav-test oa-adpcm-test --parallel 8 > outputs\scene-v19\build-windows.log 2>&1
if errorlevel 1 exit /b %errorlevel%
work\v19-host\build-windows\amalur-exploration-input-test.exe > outputs\scene-v19\input-tests.txt 2>&1
if errorlevel 1 exit /b %errorlevel%
work\v19-host\build-windows\oa-actor-ai-test.exe > outputs\scene-v19\actor-tests.txt 2>&1
if errorlevel 1 exit /b %errorlevel%
work\v19-host\build-windows\oa-adpcm-test.exe work\v23-audio\s0.bin work\v23-audio\s0.reference.raw > outputs\scene-v19\adpcm-tests.txt 2>&1
if errorlevel 1 exit /b %errorlevel%
work\v19-host\build-windows\oa-nav-test.exe > outputs\scene-v19\nav-tests.txt 2>&1
if errorlevel 1 exit /b %errorlevel%
work\v19-host\build-windows\oa-menu-test.exe work\v19-host\build-windows > outputs\scene-v19\menu-tests.txt 2>&1
if errorlevel 1 exit /b %errorlevel%
work\v19-host\build-windows\oa-character-test.exe work\v20-char\character.bin work\v20-town\town_npcs.bin > outputs\scene-v19\character-tests.txt 2>&1
if errorlevel 1 exit /b %errorlevel%
cmake -S work\v19-host -B work\v19-host\build-android-arm64 -G Ninja "-DCMAKE_MAKE_PROGRAM=%AMALUR_NINJA%" -DCMAKE_BUILD_TYPE=Release "-DCMAKE_TOOLCHAIN_FILE=%AMALUR_NDK%\build\cmake\android.toolchain.cmake" -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-26 -DAMALUR_SCENE_SHA256=020c6df9316e33fded0280605deb1bd60f6217a4adb4b5465689422e50e05475 > outputs\scene-v19\configure-android.log 2>&1
if errorlevel 1 exit /b %errorlevel%
cmake --build work\v19-host\build-android-arm64 --target opem_amalur_scene --parallel 8 > outputs\scene-v19\build-android.log 2>&1
exit /b %errorlevel%
