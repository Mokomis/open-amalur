@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" > "%~dp0build-env.log" 2>&1
if errorlevel 1 exit /b %errorlevel%
cd /d "%~dp0..\.."
set "AMALUR_NINJA=C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe"
set "AMALUR_NDK=%~dp0..\..\tools\android\android-ndk-r30"
cmake -S work\v18-host -B work\v18-host\build-windows -G Ninja "-DCMAKE_MAKE_PROGRAM=%AMALUR_NINJA%" -DCMAKE_BUILD_TYPE=Release > outputs\scene-v18\configure-windows.log 2>&1
if errorlevel 1 exit /b %errorlevel%
cmake --build work\v18-host\build-windows --target amalur-exploration-input-test --parallel 8 > outputs\scene-v18\build-windows.log 2>&1
if errorlevel 1 exit /b %errorlevel%
work\v18-host\build-windows\amalur-exploration-input-test.exe > outputs\scene-v18\input-tests.txt 2>&1
if errorlevel 1 exit /b %errorlevel%
cmake -S work\v18-host -B work\v18-host\build-android-arm64 -G Ninja "-DCMAKE_MAKE_PROGRAM=%AMALUR_NINJA%" -DCMAKE_BUILD_TYPE=Release "-DCMAKE_TOOLCHAIN_FILE=%AMALUR_NDK%\build\cmake\android.toolchain.cmake" -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-26 -DAMALUR_SCENE_SHA256=020c6df9316e33fded0280605deb1bd60f6217a4adb4b5465689422e50e05475 > outputs\scene-v18\configure-android.log 2>&1
if errorlevel 1 exit /b %errorlevel%
cmake --build work\v18-host\build-android-arm64 --target opem_amalur_scene --parallel 8 > outputs\scene-v18\build-android.log 2>&1
exit /b %errorlevel%
