@echo off
setlocal
cd /d "%~dp0"
where cl >nul 2>nul
if errorlevel 1 call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b 1
cl /nologo /W4 /O2 /std:c11 /TC opem_collision.c test_collision.c /Fe:test_collision.exe
if errorlevel 1 exit /b 1
cl /nologo /W4 /O2 /std:c11 /TC /I. opem_collision.c walk_scene.c ..\v07-host\src\amalur_scene_mesh.c /Fe:walk_scene.exe
if errorlevel 1 exit /b 1
test_collision.exe
exit /b %errorlevel%
