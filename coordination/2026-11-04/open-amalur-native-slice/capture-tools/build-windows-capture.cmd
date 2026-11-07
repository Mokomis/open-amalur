@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars32.bat"
if errorlevel 1 exit /b %errorlevel%
set "PATH=C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja;%PATH%"
cd /d "%~dp0"
"C:\Program Files\CMake\bin\cmake.exe" -S source\gfxreconstruct-0.9.18 -B build-x86 -G Ninja -DCMAKE_BUILD_TYPE=Release -DD3D12_SUPPORT=OFF -DBUILD_WERROR=OFF -DCMAKE_POLICY_VERSION_MINIMUM=3.5
if errorlevel 1 exit /b %errorlevel%
"C:\Program Files\CMake\bin\cmake.exe" --build build-x86 --target VkLayer_gfxreconstruct VkLayer_gfxreconstruct_json -j 6
exit /b %errorlevel%
