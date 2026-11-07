@echo off
setlocal
cd /d "%~dp0..\.."
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" > "%~dp0compiler.log" 2>&1
if errorlevel 1 exit /b %errorlevel%
"C:\Program Files\CMake\bin\cmake.exe" --build work\v19-host\build-windows --target amalur-exploration-input-test oa-character-test oa-menu-test oa-actor-ai-test oa-nav-test oa-adpcm-test --parallel 8 > "%~dp0build.log" 2>&1
exit /b %errorlevel%
