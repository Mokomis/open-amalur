@echo off
setlocal
cd /d "%~dp0"
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" > compiler-setup.log 2>&1
if errorlevel 1 exit /b %errorlevel%
set "ROOT=C:\Users\rwill\Documents\Opem Amalur"
set "HOST=%ROOT%\work\v19-host"
set "WINHOST=%ROOT%\work\v40-windows-host"
lib /nologo /def:"..\materials\libEGL-fixture.def" /machine:x64 /out:libEGL-fixture.lib > imports.log 2>&1
if errorlevel 1 exit /b %errorlevel%
lib /nologo /def:"..\materials\libGLESv2-fixture.def" /machine:x64 /out:libGLESv2-fixture.lib >> imports.log 2>&1
if errorlevel 1 exit /b %errorlevel%
cl /nologo /TC /std:c11 /O2 /Gy /Gw /W4 /D_CRT_SECURE_NO_WARNINGS /DOA_DESKTOP=1 /FI"%WINHOST%\include\desktop_compat.h" /I. /I"..\materials" /I"..\appearance-assets" /I"%HOST%" /I"%WINHOST%\include" /I"%WINHOST%\dependencies\include" test_appearance_actor.c oa_character_appearance.c "..\appearance-assets\oa_appearance.c" "..\appearance-assets\oa_appearance_selection.c" "..\materials\oa_cosmetic_material.c" "..\materials\oa_cosmetic_texture_bank.c" "%HOST%\oa_creation.c" "%HOST%\oa_creation_source_tables.c" "%HOST%\oa_post.c" "%HOST%\oa_render_cache.c" "%HOST%\oa_native_bloom.c" "%HOST%\oa_native_ao.c" "%HOST%\oa_native_filter.c" "%HOST%\oa_native_dof.c" /Fe:test-appearance-actor.exe /link /OPT:REF /OPT:ICF libEGL-fixture.lib libGLESv2-fixture.lib > build.log 2>&1
if errorlevel 1 exit /b %errorlevel%
set "PATH=%WINHOST%\dependencies;%PATH%"
test-appearance-actor.exe > test-output.txt 2> test-errors.txt
exit /b %errorlevel%
