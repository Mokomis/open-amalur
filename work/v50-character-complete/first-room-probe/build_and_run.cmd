@echo off
setlocal
cd /d "%~dp0"
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" > compiler.log 2>&1
if errorlevel 1 exit /b %errorlevel%
set "ROOT=C:\Users\rwill\Documents\Opem Amalur"
set "M=%ROOT%\work\v50-character-complete\materials"
set "W=%ROOT%\work\v40-windows-host"
cl /nologo /TC /std:c11 /O2 /W4 /D_CRT_SECURE_NO_WARNINGS /I"%W%\dependencies\include" test_probe.c /Fe:test-probe.exe /link "%M%\libEGL-fixture.lib" "%M%\libGLESv2-fixture.lib" > build.log 2>&1
if errorlevel 1 exit /b %errorlevel%
set "PATH=%W%\dependencies;%PATH%"
test-probe.exe > test-output.txt 2> test-errors.txt
exit /b %errorlevel%
