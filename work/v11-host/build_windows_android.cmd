@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" > "%~dp0build-env.log" 2>&1
if errorlevel 1 exit /b %errorlevel%
set "AMALUR_NINJA=C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe"
set "AMALUR_NDK=%~dp0..\..\tools\android\android-ndk-r30"
cmake -S "%~dp0." -B "%~dp0build-windows" -G Ninja "-DCMAKE_MAKE_PROGRAM=%AMALUR_NINJA%" -DCMAKE_BUILD_TYPE=Release  > "%~dp0configure-windows.log" 2>&1
if errorlevel 1 exit /b %errorlevel%
cmake --build "%~dp0build-windows" --parallel 8 > "%~dp0build-windows.log" 2>&1
if errorlevel 1 exit /b %errorlevel%
cmake -S "%~dp0." -B "%~dp0build-android-arm64" -G Ninja "-DCMAKE_MAKE_PROGRAM=%AMALUR_NINJA%" -DCMAKE_BUILD_TYPE=Release "-DCMAKE_TOOLCHAIN_FILE=%AMALUR_NDK%\build\cmake\android.toolchain.cmake" -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-26 -DAMALUR_SCENE_SHA256=bf89bfe1a5b7d2ee2955dc7972509a7efb68fd027cb36482d25b24f905a97bc2  > "%~dp0configure-android.log" 2>&1
if errorlevel 1 exit /b %errorlevel%
cmake --build "%~dp0build-android-arm64" --parallel 8 > "%~dp0build-android.log" 2>&1
exit /b %errorlevel%
