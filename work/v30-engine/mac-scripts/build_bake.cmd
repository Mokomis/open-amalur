@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars32.bat" > "%~dp0bake-env.log" 2>&1
if errorlevel 1 exit /b 1
cl /nologo /O2 /EHsc "%~dp0clip_bake.cpp" /Fe:"%~dp0clip-bake.exe" /Fo:"%~dp0clip-bake.obj" /link /BASE:0x30000000 /DYNAMICBASE:NO /FIXED > "%~dp0bake-build.log" 2>&1
exit /b %errorlevel%
