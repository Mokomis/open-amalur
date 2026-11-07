@echo off
setlocal
cd /d "%~dp0"
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" > compiler-setup.log 2>&1
if errorlevel 1 exit /b %errorlevel%
set "ROOT=C:\Users\rwill\Documents\Opem Amalur"
set "HOST=%ROOT%\work\v19-host"
set "WINHOST=%ROOT%\work\v40-windows-host"
lib /nologo /def:libEGL-fixture.def /machine:x64 /out:libEGL-fixture.lib > imports.log 2>&1
if errorlevel 1 exit /b %errorlevel%
lib /nologo /def:libGLESv2-fixture.def /machine:x64 /out:libGLESv2-fixture.lib >> imports.log 2>&1
if errorlevel 1 exit /b %errorlevel%
cl /nologo /TC /std:c11 /O2 /Gy /Gw /W4 /D_CRT_SECURE_NO_WARNINGS /DOA_DESKTOP=1 /I. /I"%HOST%" /I"%WINHOST%\include" /I"%WINHOST%\dependencies\include" test_weighted_hardlight.c oa_weighted_hardlight.c "%HOST%\oa_character.c" "%HOST%\oa_character_attributes.c" "%HOST%\oa_post.c" "%HOST%\oa_character_material.c" "%HOST%\oa_render_cache.c" "%HOST%\oa_native_bloom.c" "%HOST%\oa_native_ao.c" "%HOST%\oa_native_filter.c" "%HOST%\oa_native_dof.c" /Fe:test-weighted-hardlight.exe /link /OPT:REF /OPT:ICF libEGL-fixture.lib libGLESv2-fixture.lib > build.log 2>&1
if errorlevel 1 exit /b %errorlevel%
set "PATH=%WINHOST%\dependencies;%PATH%"
test-weighted-hardlight.exe > test-output.txt 2> test-errors.txt
exit /b %errorlevel%
