@echo off
setlocal
cd /d "%~dp0"
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" > build-env.log 2>&1
if errorlevel 1 exit /b 1
cl /nologo /W4 /O2 /TC scene_materials_v09.c scene_materials_v09_test.c /Fe:scene_materials_v09_test.exe
if errorlevel 1 exit /b 1
scene_materials_v09_test.exe
exit /b %errorlevel%
