@echo off
setlocal
cd /d "%~dp0"
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" > compiler.log 2>&1
if errorlevel 1 exit /b %errorlevel%
lib /nologo /def:dependencies\libEGL.def /machine:x64 /out:dependencies\libEGL.lib > imports.log 2>&1
if errorlevel 1 exit /b %errorlevel%
lib /nologo /def:dependencies\libGLESv2.def /machine:x64 /out:dependencies\libGLESv2.lib >> imports.log 2>&1
if errorlevel 1 exit /b %errorlevel%
"C:\Program Files\CMake\bin\cmake.exe" -S . -B build -G Ninja "-DCMAKE_MAKE_PROGRAM=C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe" -DCMAKE_BUILD_TYPE=RelWithDebInfo > configure.log 2>&1
if errorlevel 1 exit /b %errorlevel%
"C:\Program Files\CMake\bin\cmake.exe" --build build --target open-amalur-windows --parallel 8 > build.log 2>&1
exit /b %errorlevel%
