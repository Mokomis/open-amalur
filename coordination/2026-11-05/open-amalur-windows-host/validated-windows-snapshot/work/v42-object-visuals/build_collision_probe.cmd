@echo off
setlocal
cd /d "%~dp0"
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" > collision-compiler.log 2>&1
if errorlevel 1 exit /b %errorlevel%
cl /nologo /std:c11 /O2 /I..\v19-host prop_collision_probe.c ..\v19-host\opem_collision.c /Fe:prop_collision_probe.exe > collision-build.log 2>&1
exit /b %errorlevel%
