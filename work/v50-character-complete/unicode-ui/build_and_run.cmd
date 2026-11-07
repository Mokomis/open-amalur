@echo off
setlocal
cd /d "%~dp0"
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" > compiler-setup.log 2>&1
if errorlevel 1 exit /b %errorlevel%
set "WINHOST=C:\Users\rwill\Documents\Opem Amalur\work\v40-windows-host"
lib /nologo /def:libEGL-fixture.def /machine:x64 /out:libEGL-fixture.lib > imports.log 2>&1
lib /nologo /def:libGLESv2-fixture.def /machine:x64 /out:libGLESv2-fixture.lib >> imports.log 2>&1
cl /nologo /TC /std:c11 /O2 /W4 /D_CRT_SECURE_NO_WARNINGS /I. /I"%WINHOST%\include" /I"%WINHOST%\dependencies\include" test_unicode_ui.c legacy_wrap.c oa_ui_text_win32.c /Fe:test-unicode-ui.exe /link libEGL-fixture.lib libGLESv2-fixture.lib gdi32.lib user32.lib > build.log 2>&1
if errorlevel 1 exit /b %errorlevel%
set "PATH=%WINHOST%\dependencies;%PATH%"
test-unicode-ui.exe > test-output.txt 2> test-errors.txt
exit /b %errorlevel%
