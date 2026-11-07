@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" > helper-build.log 2>&1
if errorlevel 1 exit /b %errorlevel%
cl /nologo /TC /std:c11 /W4 /WX /fp:strict native_light_volume_weights.c test_light_volume_weights.c /Fe:lighting-volume-tests.exe /link /INCREMENTAL:NO > helper-compiler.log 2>&1
if errorlevel 1 exit /b %errorlevel%
lighting-volume-tests.exe
